/**
 * EvenKeel boat-overview Lovelace card.
 *
 * Renders a top-down sailboat diagram with severity overlays per zone,
 * an animated power-flow line (shore/gen/solar → battery → loads), a
 * Captain's Glance headline strip, and a footer of always-on vitals.
 *
 * Tap a zone → navigate to the zone's drill-down view.
 *
 * Configured by Lovelace YAML; see info.md for the schema.
 */
import { LitElement, html, css, type TemplateResult } from "lit";
import { property, state } from "lit/decorators.js";

import { validateConfig, ConfigError, type BoatCardConfig, type Severity } from "./config.js";
import { renderBoatBody, BOAT_VIEWBOX } from "./boat-svg.js";
import {
  computeZoneSeverities,
  formatVital,
  maxSeverity,
  pickHeadline,
  powerFlowDirection,
  severityFromState,
} from "./utils.js";

/**
 * Minimal subset of the HA front-end runtime API. We avoid pulling in
 * the full `home-assistant-js-websocket` types so this card stays light.
 */
interface HassEntity {
  state: string;
  attributes?: Record<string, unknown>;
}

interface HomeAssistantLike {
  states: Record<string, HassEntity>;
  callService?: (...args: unknown[]) => unknown;
}

export class EvenKeelBoatCard extends LitElement {
  // HA passes hass via a property setter; we re-render on every change.
  @property({ attribute: false }) hass?: HomeAssistantLike;

  @state() private _config?: BoatCardConfig;
  @state() private _configError?: string;

  static styles = css`
    :host {
      display: block;
    }
    ha-card,
    .card {
      box-sizing: border-box;
      padding: 16px;
      border-radius: var(--ha-card-border-radius, 16px);
      background: var(--ha-card-background, var(--card-background-color, #fff));
      color: var(--primary-text-color, #1c1c1e);
      font-family: var(--paper-font-body1_-_font-family, sans-serif);
    }
    .header {
      display: flex;
      align-items: baseline;
      gap: 12px;
      margin-bottom: 8px;
    }
    .header h2 {
      margin: 0;
      font-size: 1.1rem;
      font-weight: 600;
      letter-spacing: -0.01em;
    }
    .glance {
      flex: 1 1 auto;
      font-size: 0.95rem;
      color: var(--primary-text-color);
    }
    .glance.severity-warning {
      color: var(--evenkeel-warn, #f59e0b);
      font-weight: 600;
    }
    .glance.severity-critical {
      color: var(--evenkeel-crit, #ef4444);
      font-weight: 700;
    }
    svg.boat {
      display: block;
      width: 100%;
      height: auto;
      max-height: 360px;
    }
    .zone {
      cursor: pointer;
      transition: transform 0.2s ease;
    }
    .zone:hover {
      transform: scale(1.02);
      transform-origin: center;
    }
    .zone .zone-bg {
      fill: var(--evenkeel-ok, #22c55e);
      fill-opacity: 0.18;
      stroke: var(--primary-text-color, #1c1c1e);
      stroke-opacity: 0.35;
      stroke-width: 1;
    }
    .zone.severity-warning .zone-bg {
      fill: var(--evenkeel-warn, #f59e0b);
      fill-opacity: 0.45;
      animation: pulse-warn 1.5s ease-in-out infinite;
    }
    .zone.severity-critical .zone-bg {
      fill: var(--evenkeel-crit, #ef4444);
      fill-opacity: 0.65;
      animation: pulse-crit 1.0s ease-in-out infinite;
    }
    @keyframes pulse-warn {
      50% { fill-opacity: 0.65; }
    }
    @keyframes pulse-crit {
      50% { fill-opacity: 0.95; }
    }
    .powerflow {
      margin-top: 8px;
      font-size: 0.85rem;
      color: var(--secondary-text-color, #5a5a5e);
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }
    .powerflow svg {
      flex: 1 1 200px;
      height: 24px;
    }
    .powerflow .ant-line {
      stroke: var(--evenkeel-ok, #22c55e);
      stroke-width: 2;
      stroke-dasharray: 4 4;
      fill: none;
    }
    .powerflow.flow-charging .ant-line {
      animation: ants-fwd 0.8s linear infinite;
    }
    .powerflow.flow-discharging .ant-line {
      animation: ants-rev 0.8s linear infinite;
      stroke: var(--evenkeel-warn, #f59e0b);
    }
    @keyframes ants-fwd {
      to { stroke-dashoffset: -8; }
    }
    @keyframes ants-rev {
      to { stroke-dashoffset: 8; }
    }
    .vitals {
      display: flex;
      gap: 18px;
      margin-top: 12px;
      padding-top: 12px;
      border-top: 1px solid var(--divider-color, rgba(0, 0, 0, 0.08));
      font-size: 0.85rem;
      color: var(--secondary-text-color, #5a5a5e);
      flex-wrap: wrap;
    }
    .vital {
      display: inline-flex;
      gap: 6px;
      align-items: baseline;
    }
    .vital .key {
      font-size: 0.7rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .vital .val {
      font-variant-numeric: tabular-nums;
      font-weight: 600;
      color: var(--primary-text-color, #1c1c1e);
    }
    .error {
      color: var(--evenkeel-crit, #ef4444);
      padding: 12px;
      font-family: monospace;
      font-size: 0.85rem;
    }
  `;

  // Lovelace calls this when the user changes config in the GUI editor;
  // we use it for validation on the YAML-config path too.
  setConfig(config: unknown): void {
    try {
      this._config = validateConfig(config);
      this._configError = undefined;
    } catch (e) {
      if (e instanceof ConfigError) {
        this._configError = e.message;
      } else if (e instanceof Error) {
        this._configError = `Unexpected: ${e.message}`;
      } else {
        this._configError = String(e);
      }
    }
  }

  // Lovelace asks for a row size estimate. Card is roughly 5 rows tall.
  getCardSize(): number {
    return 5;
  }

  protected render(): TemplateResult {
    if (this._configError) {
      return html`<div class="card error">EvenKeel boat card config error: ${this._configError}</div>`;
    }
    if (!this._config) {
      return html`<div class="card">Loading…</div>`;
    }
    const cfg = this._config;
    const hass = this.hass;

    // Per-zone severities and overall severity (pure functions; unit-tested)
    const zoneSeverities = computeZoneSeverities(cfg.zones, hass?.states);
    const overall: Severity = cfg.overall_status && hass?.states[cfg.overall_status]
      ? severityFromState(hass.states[cfg.overall_status].state)
      : maxSeverity(Object.values(zoneSeverities));

    // Captain's-glance headline
    const headline = pickHeadline(cfg.overall_status, hass?.states, overall);

    // Power flow direction
    const battA = this._numericState(hass, cfg.power_flow?.battery_a);
    const flowDir = powerFlowDirection(battA);

    return html`
      <ha-card class="card">
        <div class="header">
          <h2>${cfg.boat_name ?? "Boat"}</h2>
          <span class="glance severity-${overall}">${headline}</span>
        </div>
        <svg class="boat" viewBox="${BOAT_VIEWBOX}" role="img" aria-label="Boat overview"
             @click=${this._onSvgClick.bind(this)}>
          ${renderBoatBody(zoneSeverities)}
        </svg>
        ${this._renderPowerFlow(cfg, flowDir)}
        ${this._renderVitals(cfg, hass)}
      </ha-card>
    `;
  }

  private _numericState(hass: HomeAssistantLike | undefined, entityId: string | undefined): number | undefined {
    if (!hass || !entityId) return undefined;
    const ent = hass.states[entityId];
    if (!ent) return undefined;
    const n = parseFloat(ent.state);
    return Number.isNaN(n) ? undefined : n;
  }

  private _onSvgClick(ev: MouseEvent): void {
    const target = ev.target as Element | null;
    if (!target) return;
    const zoneEl = target.closest('.zone');
    if (!zoneEl) return;
    const zoneKey = (zoneEl as SVGElement).dataset.zone;
    if (!zoneKey) return;
    const nav = this._config?.zones?.[zoneKey]?.navigate;
    if (!nav) return;
    history.pushState(null, "", nav);
    window.dispatchEvent(new CustomEvent("location-changed", { composed: true }));
  }

  private _renderPowerFlow(cfg: BoatCardConfig, dir: -1 | 0 | 1): TemplateResult {
    if (!cfg.power_flow) return html``;
    const cls = dir === 1 ? "flow-charging" : dir === -1 ? "flow-discharging" : "";
    const labelLeft = cfg.power_flow.shore && this._isOn(cfg.power_flow.shore)
      ? "SHORE"
      : cfg.power_flow.generator && this._isOn(cfg.power_flow.generator)
      ? "GEN"
      : cfg.power_flow.solar && (this._numericState(this.hass, cfg.power_flow.solar) ?? 0) > 5
      ? "SOLAR"
      : "BATTERY";
    const battV = this._numericState(this.hass, cfg.power_flow.battery_v);
    const battLabel = battV !== undefined ? `${battV.toFixed(1)} V` : "—";
    return html`
      <div class="powerflow ${cls}" aria-label="Power flow ${labelLeft} to battery">
        <span>${labelLeft}</span>
        <svg viewBox="0 0 200 24" preserveAspectRatio="none" aria-hidden="true">
          <path class="ant-line" d="M 5 12 L 195 12"/>
        </svg>
        <span>BATT ${battLabel}</span>
      </div>
    `;
  }

  private _isOn(entityId: string): boolean {
    const ent = this.hass?.states[entityId];
    return ent?.state === "on";
  }

  private _renderVitals(cfg: BoatCardConfig, hass: HomeAssistantLike | undefined): TemplateResult {
    if (!cfg.footer_vitals || cfg.footer_vitals.length === 0) return html``;
    return html`
      <div class="vitals">
        ${cfg.footer_vitals.map((eid) => {
          const ent = hass?.states[eid];
          const friendly = (ent?.attributes?.friendly_name as string) ?? eid;
          const unit = ent?.attributes?.unit_of_measurement as string | undefined;
          const valStr = ent ? formatVital(ent.state, unit) : "—";
          // Compress the friendly name for the footer (last word usually
          // says it: "House battery V" → "V")
          const short = friendly.split(" ").slice(-2).join(" ");
          return html`<span class="vital"><span class="key">${short}</span><span class="val">${valStr}</span></span>`;
        })}
      </div>
    `;
  }
}

// Register the element. Both the custom card name AND the camelCase
// alias HA's GUI editor scans for.
if (!customElements.get("evenkeel-boat-card")) {
  customElements.define("evenkeel-boat-card", EvenKeelBoatCard);
}

// Tell HA's card-picker about us. This populates the GUI editor's "+" menu.
type WindowWithCustomCards = typeof window & { customCards?: unknown[] };
const w = window as WindowWithCustomCards;
w.customCards = w.customCards || [];
(w.customCards as unknown[]).push({
  type: "evenkeel-boat-card",
  name: "EvenKeel Boat Card",
  description: "Top-down sailboat diagram with severity overlays + animated power flow",
  preview: false,
});

// Also export the class for tests.
export default EvenKeelBoatCard;
