/**
 * Lit/HTML rendering smoke tests via happy-dom.
 *
 * These are minimal — they confirm the element registers, accepts
 * config, and renders without throwing. Heavier visual-regression
 * testing is deferred to the Playwright pass in tests/.
 */
import { describe, expect, it, beforeEach } from "vitest";

import "../src/evenkeel-boat-card";

interface MinimalHass {
  states: Record<string, { state: string; attributes?: Record<string, unknown> }>;
}

function makeCard() {
  const el = document.createElement("evenkeel-boat-card") as HTMLElement & {
    setConfig: (c: unknown) => void;
    hass?: MinimalHass;
    shadowRoot: ShadowRoot | null;
  };
  document.body.appendChild(el);
  return el;
}

describe("evenkeel-boat-card element", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
  });

  it("registers as a custom element", () => {
    expect(customElements.get("evenkeel-boat-card")).toBeDefined();
  });

  it("renders an error card on bad config without throwing", async () => {
    const card = makeCard();
    card.setConfig({ type: "wrong" });
    await new Promise((r) => setTimeout(r, 10));
    const html = card.shadowRoot!.innerHTML;
    expect(html).toContain("config error");
    expect(html.toLowerCase()).toContain("type");
  });

  it("renders the boat SVG with config but no hass", async () => {
    const card = makeCard();
    card.setConfig({
      type: "custom:evenkeel-boat-card",
      boat_name: "Test Vessel",
    });
    await new Promise((r) => setTimeout(r, 10));
    const html = card.shadowRoot!.innerHTML;
    expect(html).toContain("Test Vessel");
    expect(html).toContain("svg");
    expect(html).toContain('class="boat"');
  });

  it("falls back to All good when no overall_status entity is configured", async () => {
    const card = makeCard();
    card.setConfig({ type: "custom:evenkeel-boat-card" });
    await new Promise((r) => setTimeout(r, 10));
    expect(card.shadowRoot!.innerHTML).toContain("All good");
  });

  it("uses overall_status entity headline when provided", async () => {
    const card = makeCard();
    card.hass = {
      states: {
        "sensor.boat_primary_alert": {
          state: "critical",
          attributes: { headline: "Water in the bilge — Pete needs to check now" },
        },
      },
    };
    card.setConfig({
      type: "custom:evenkeel-boat-card",
      overall_status: "sensor.boat_primary_alert",
    });
    await new Promise((r) => setTimeout(r, 10));
    expect(card.shadowRoot!.innerHTML).toContain("Water in the bilge");
  });

  // Note: zone severity painting (CSS class swap based on rollup state) is
  // verified by `computeZoneSeverities` unit tests in utils.test.ts. The
  // SVG-namespace rendering doesn't survive happy-dom's parser cleanly;
  // visual regression of zone painting is left to the Playwright pass
  // running against a real HA instance (tests/e2e/).

  it("renders without throwing when an overall_status entity is critical", async () => {
    const card = makeCard();
    card.hass = {
      states: {
        "sensor.boat_primary_alert": {
          state: "critical",
          attributes: { headline: "Water in the bilge — Pete needs to check now" },
        },
      },
    };
    card.setConfig({
      type: "custom:evenkeel-boat-card",
      overall_status: "sensor.boat_primary_alert",
      zones: { engine_bay: { rollup: "sensor.boat_engine_tanks_status" } },
    });
    await new Promise((r) => setTimeout(r, 10));
    const html = card.shadowRoot!.innerHTML;
    // Headline appears
    expect(html).toContain("Water in the bilge");
    // Severity class is applied to the glance row
    expect(html).toContain("severity-critical");
  });

  it("getCardSize returns a sensible row estimate", () => {
    const card = makeCard() as unknown as { getCardSize: () => number };
    expect(card.getCardSize()).toBeGreaterThan(0);
  });

  it("registers itself with HA's custom-card picker", () => {
    type W = typeof window & { customCards?: { type: string }[] };
    const cards = (window as W).customCards;
    expect(Array.isArray(cards)).toBe(true);
    expect(cards!.find((c) => c.type === "evenkeel-boat-card")).toBeDefined();
  });
});
