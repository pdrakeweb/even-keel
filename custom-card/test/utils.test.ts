import { describe, expect, it } from "vitest";

import {
  computeZoneSeverities,
  formatVital,
  maxSeverity,
  pickHeadline,
  powerFlowDirection,
  severityCssVar,
  severityFromNumeric,
  severityFromState,
  severityPulseSeconds,
} from "../src/utils";

describe("severityFromState", () => {
  it("maps the canonical strings", () => {
    expect(severityFromState("ok")).toBe("ok");
    expect(severityFromState("warning")).toBe("warning");
    expect(severityFromState("critical")).toBe("critical");
  });

  it("defaults to ok for unknown / missing state", () => {
    // Fail-open: a missing rollup should NEVER paint red.
    expect(severityFromState(undefined)).toBe("ok");
    expect(severityFromState("unknown")).toBe("ok");
    expect(severityFromState("unavailable")).toBe("ok");
  });
});

describe("severityFromNumeric (high-bad)", () => {
  it("ok below warn", () => {
    expect(severityFromNumeric(50, { warn: 60, crit: 80 })).toBe("ok");
  });
  it("warning at warn threshold", () => {
    expect(severityFromNumeric(60, { warn: 60, crit: 80 })).toBe("warning");
  });
  it("critical at crit threshold", () => {
    expect(severityFromNumeric(80, { warn: 60, crit: 80 })).toBe("critical");
  });
  it("ok for undefined / NaN", () => {
    expect(severityFromNumeric(undefined, { warn: 1, crit: 2 })).toBe("ok");
    expect(severityFromNumeric(NaN, { warn: 1, crit: 2 })).toBe("ok");
  });
});

describe("severityFromNumeric (low-bad)", () => {
  it("ok above warn", () => {
    expect(severityFromNumeric(13.0, { warn: 12.0, crit: 11.5 }, "low")).toBe("ok");
  });
  it("warning at warn threshold", () => {
    expect(severityFromNumeric(12.0, { warn: 12.0, crit: 11.5 }, "low")).toBe("warning");
  });
  it("critical at crit threshold", () => {
    expect(severityFromNumeric(11.5, { warn: 12.0, crit: 11.5 }, "low")).toBe("critical");
  });
});

describe("severityCssVar", () => {
  it("renders ok green", () => {
    expect(severityCssVar("ok")).toContain("evenkeel-ok");
  });
  it("renders warn amber", () => {
    expect(severityCssVar("warning")).toContain("evenkeel-warn");
  });
  it("renders crit red", () => {
    expect(severityCssVar("critical")).toContain("evenkeel-crit");
  });
  it("includes a CSS fallback color outside the var()", () => {
    // Without theme tokens the card must still be readable.
    expect(severityCssVar("ok")).toMatch(/#22c55e|#[0-9a-fA-F]{6}/);
  });
});

describe("severityPulseSeconds", () => {
  it("ok = 0 (no animation)", () => {
    expect(severityPulseSeconds("ok")).toBe(0);
  });
  it("critical pulses faster than warning", () => {
    expect(severityPulseSeconds("critical")).toBeLessThan(severityPulseSeconds("warning"));
  });
});

describe("maxSeverity", () => {
  it("empty defaults to ok", () => {
    expect(maxSeverity([])).toBe("ok");
  });
  it("any critical wins", () => {
    expect(maxSeverity(["ok", "warning", "critical", "ok"])).toBe("critical");
  });
  it("warning beats ok", () => {
    expect(maxSeverity(["ok", "ok", "warning"])).toBe("warning");
  });
  it("all ok stays ok", () => {
    expect(maxSeverity(["ok", "ok", "ok"])).toBe("ok");
  });
});

describe("formatVital", () => {
  it("undefined / null / empty -> em-dash", () => {
    expect(formatVital(undefined)).toBe("—");
    expect(formatVital("")).toBe("—");
  });
  it("rounds floats to one decimal under 100", () => {
    expect(formatVital(12.345, "V")).toBe("12.3 V");
  });
  it("rounds to integer over 100", () => {
    expect(formatVital(12345)).toBe("12345");
  });
  it("strips zeros via roundtrip but leaves clean integer", () => {
    expect(formatVital(7)).toBe("7");
  });
  it("propagates non-numeric strings as-is", () => {
    expect(formatVital("battery")).toBe("battery");
  });
  it("handles unit suffix", () => {
    expect(formatVital("12.5", "V")).toBe("12.5 V");
  });
});

describe("powerFlowDirection", () => {
  it("undefined / NaN -> 0", () => {
    expect(powerFlowDirection(undefined)).toBe(0);
    expect(powerFlowDirection(NaN)).toBe(0);
  });
  it("positive amps = charging (+1)", () => {
    expect(powerFlowDirection(2.5)).toBe(1);
  });
  it("negative amps = discharging (-1)", () => {
    expect(powerFlowDirection(-3.0)).toBe(-1);
  });
  it("near-zero is treated as steady (0)", () => {
    // Threshold is 0.5 A — below that is noise floor on most shunts.
    expect(powerFlowDirection(0.2)).toBe(0);
    expect(powerFlowDirection(-0.4)).toBe(0);
  });
});

describe("computeZoneSeverities", () => {
  it("undefined zones -> empty record", () => {
    expect(computeZoneSeverities(undefined, {})).toEqual({});
  });

  it("entity present -> mapped severity", () => {
    const out = computeZoneSeverities(
      {
        bilge: { rollup: "sensor.boat_bilge_status" },
        engine: { rollup: "sensor.boat_engine_tanks_status" },
      },
      {
        "sensor.boat_bilge_status": { state: "critical" },
        "sensor.boat_engine_tanks_status": { state: "ok" },
      },
    );
    expect(out).toEqual({ bilge: "critical", engine: "ok" });
  });

  it("missing entity -> ok (fail-open)", () => {
    const out = computeZoneSeverities(
      { bilge: { rollup: "sensor.missing" } },
      {},
    );
    expect(out).toEqual({ bilge: "ok" });
  });

  it("unknown state string -> ok", () => {
    const out = computeZoneSeverities(
      { bilge: { rollup: "sensor.boat_bilge_status" } },
      { "sensor.boat_bilge_status": { state: "exploding" } },
    );
    expect(out).toEqual({ bilge: "ok" });
  });
});

describe("pickHeadline", () => {
  it("uses entity headline attribute when present", () => {
    const out = pickHeadline(
      "sensor.boat_primary_alert",
      {
        "sensor.boat_primary_alert": {
          state: "critical",
          attributes: { headline: "Water in the bilge — Pete needs to check" },
        },
      },
      "critical",
    );
    expect(out).toBe("Water in the bilge — Pete needs to check");
  });

  it("falls back to generic on missing entity", () => {
    expect(pickHeadline("sensor.x", {}, "critical")).toBe("Action needed.");
    expect(pickHeadline("sensor.x", {}, "warning")).toBe("Heads up.");
    expect(pickHeadline("sensor.x", {}, "ok")).toBe("All good.");
  });

  it("falls back when no overall_status configured", () => {
    expect(pickHeadline(undefined, undefined, "ok")).toBe("All good.");
  });

  it("falls back when entity has no headline attribute", () => {
    const out = pickHeadline(
      "sensor.x",
      { "sensor.x": { state: "warning" } },
      "warning",
    );
    expect(out).toBe("Heads up.");
  });
});
