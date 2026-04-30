/**
 * Severity helpers + entity-state utilities used by the card.
 */

import type { Severity } from "./config.js";

/**
 * Map an entity state string to one of the canonical severity tokens.
 * Defaults to "ok" so an unavailable / unknown rollup never paints the
 * boat red. Captain's-glance is the place to surface "something wrong."
 */
export function severityFromState(state: string | undefined): Severity {
  if (state === "warning") return "warning";
  if (state === "critical") return "critical";
  return "ok";
}

/**
 * Severity from a plain numeric value + thresholds.
 *
 * Use `direction = "high"` when high values are bad (e.g., temperature).
 * Use `direction = "low"` when low values are bad (e.g., voltage).
 */
export function severityFromNumeric(
  value: number | undefined,
  thresholds: { warn: number; crit: number },
  direction: "high" | "low" = "high",
): Severity {
  if (value === undefined || Number.isNaN(value)) return "ok";
  if (direction === "high") {
    if (value >= thresholds.crit) return "critical";
    if (value >= thresholds.warn) return "warning";
    return "ok";
  }
  if (value <= thresholds.crit) return "critical";
  if (value <= thresholds.warn) return "warning";
  return "ok";
}

export function severityCssVar(s: Severity): string {
  switch (s) {
    case "critical":
      return "var(--evenkeel-crit, #ef4444)";
    case "warning":
      return "var(--evenkeel-warn, #f59e0b)";
    default:
      return "var(--evenkeel-ok, #22c55e)";
  }
}

/**
 * Pulse animation rate in seconds. Critical pulses faster than warning
 * so the eye is drawn to the most urgent issue first.
 */
export function severityPulseSeconds(s: Severity): number {
  switch (s) {
    case "critical":
      return 1.0;
    case "warning":
      return 1.5;
    default:
      return 0;
  }
}

/**
 * Highest of a list of severities — used for the overall card border /
 * captain's-glance fallback when no `overall_status` entity is configured.
 */
export function maxSeverity(items: Severity[]): Severity {
  if (items.includes("critical")) return "critical";
  if (items.includes("warning")) return "warning";
  return "ok";
}

/**
 * Format a numeric value for the footer vitals row. Strips trailing
 * zeros; appends unit if provided.
 */
export function formatVital(value: string | number | undefined, unit?: string): string {
  if (value === undefined || value === null || value === "") return "—";
  const n = typeof value === "string" ? parseFloat(value) : value;
  if (Number.isNaN(n)) return String(value);
  const rounded = Math.abs(n) >= 100 ? Math.round(n) : Math.round(n * 10) / 10;
  return unit ? `${rounded} ${unit}` : `${rounded}`;
}

/**
 * Compute power-flow direction. Negative current = battery discharging
 * to loads. Positive = battery charging from shore/gen/solar.
 *
 * Returns `+1` for charging-flow (animate from source toward battery),
 * `-1` for discharging (battery toward loads),
 * `0` for steady-state (no animation).
 */
export function powerFlowDirection(batteryAmps: number | undefined): -1 | 0 | 1 {
  if (batteryAmps === undefined || Number.isNaN(batteryAmps)) return 0;
  if (Math.abs(batteryAmps) < 0.5) return 0;
  return batteryAmps > 0 ? 1 : -1;
}

/**
 * Minimal subset of HA's hass.states map needed for severity computation.
 * Defined here so it can be imported by tests without pulling in the full
 * card module.
 */
export interface HassStateLike {
  state: string;
  attributes?: Record<string, unknown>;
}

export interface ZoneCfgLike {
  rollup: string;
}

/**
 * Pure function that maps zone configurations + HA state map → per-zone
 * severity. Defaults to "ok" when an entity is missing or its state is
 * not in the canonical {ok, warning, critical} set.
 *
 * Extracted as a free function so it can be unit-tested without
 * spinning up the LitElement / happy-dom.
 */
export function computeZoneSeverities(
  zones: Record<string, ZoneCfgLike> | undefined,
  states: Record<string, HassStateLike> | undefined,
): Record<string, Severity> {
  const out: Record<string, Severity> = {};
  if (!zones) return out;
  for (const [zoneKey, zoneCfg] of Object.entries(zones)) {
    const ent = states?.[zoneCfg.rollup];
    out[zoneKey] = ent ? severityFromState(ent.state) : "ok";
  }
  return out;
}

/**
 * Pure function: pick the headline string the card shows in its header.
 *
 * Priority:
 *   1. `overall_status` entity's `headline` attribute (Captain's Glance)
 *   2. fallback to a generic message keyed by overall severity.
 */
export function pickHeadline(
  overallEntityId: string | undefined,
  states: Record<string, HassStateLike> | undefined,
  fallbackSeverity: Severity,
): string {
  if (overallEntityId && states) {
    const ent = states[overallEntityId];
    if (ent) {
      const h = ent.attributes?.headline;
      if (typeof h === "string" && h.length > 0) return h;
    }
  }
  if (fallbackSeverity === "critical") return "Action needed.";
  if (fallbackSeverity === "warning") return "Heads up.";
  return "All good.";
}
