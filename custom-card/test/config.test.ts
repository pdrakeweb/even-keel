/**
 * Config validation contract.
 *
 * The card MUST throw a clear ConfigError on every malformed config and
 * MUST accept the documented schema verbatim.
 */
import { describe, expect, it } from "vitest";

import { validateConfig, ConfigError, KNOWN_ZONE_KEYS } from "../src/config";

describe("validateConfig", () => {
  describe("type field", () => {
    it("accepts the canonical custom: type", () => {
      const cfg = validateConfig({ type: "custom:evenkeel-boat-card" });
      expect(cfg.type).toBe("custom:evenkeel-boat-card");
    });

    it("rejects missing type", () => {
      expect(() => validateConfig({})).toThrow(ConfigError);
    });

    it("rejects wrong type", () => {
      expect(() => validateConfig({ type: "custom:not-our-card" })).toThrow(ConfigError);
    });

    it("rejects non-string type", () => {
      expect(() => validateConfig({ type: 42 })).toThrow(ConfigError);
    });

    it("rejects non-object input", () => {
      expect(() => validateConfig(null)).toThrow(ConfigError);
      expect(() => validateConfig(undefined)).toThrow(ConfigError);
      expect(() => validateConfig("nope")).toThrow(ConfigError);
    });
  });

  describe("boat_name", () => {
    it("optional", () => {
      const cfg = validateConfig({ type: "custom:evenkeel-boat-card" });
      expect(cfg.boat_name).toBeUndefined();
    });

    it("string passes through", () => {
      const cfg = validateConfig({ type: "custom:evenkeel-boat-card", boat_name: "Hunter 41DS" });
      expect(cfg.boat_name).toBe("Hunter 41DS");
    });

    it("non-string rejected", () => {
      expect(() => validateConfig({ type: "custom:evenkeel-boat-card", boat_name: 42 })).toThrow(ConfigError);
    });
  });

  describe("overall_status", () => {
    it("accepts valid entity_id", () => {
      const cfg = validateConfig({ type: "custom:evenkeel-boat-card", overall_status: "sensor.boat_primary_alert" });
      expect(cfg.overall_status).toBe("sensor.boat_primary_alert");
    });

    it("rejects invalid entity_id format", () => {
      expect(() =>
        validateConfig({ type: "custom:evenkeel-boat-card", overall_status: "Not An Entity" }),
      ).toThrow(ConfigError);
    });

    it("rejects entity_id with capitals", () => {
      expect(() =>
        validateConfig({ type: "custom:evenkeel-boat-card", overall_status: "Sensor.Boat" }),
      ).toThrow(ConfigError);
    });
  });

  describe("zones", () => {
    it("optional", () => {
      const cfg = validateConfig({ type: "custom:evenkeel-boat-card" });
      expect(cfg.zones).toBeUndefined();
    });

    it("accepts well-formed zones", () => {
      const cfg = validateConfig({
        type: "custom:evenkeel-boat-card",
        zones: {
          bilge: {
            rollup: "sensor.boat_bilge_status",
            navigate: "/lovelace/boat-kelly/bilge",
          },
          engine: {
            rollup: "sensor.boat_engine_tanks_status",
          },
        },
      });
      expect(Object.keys(cfg.zones!)).toEqual(["bilge", "engine"]);
      expect(cfg.zones!.bilge.rollup).toBe("sensor.boat_bilge_status");
      expect(cfg.zones!.bilge.navigate).toBe("/lovelace/boat-kelly/bilge");
    });

    it("rejects zones not an object", () => {
      expect(() =>
        validateConfig({ type: "custom:evenkeel-boat-card", zones: ["not", "a", "map"] }),
      ).toThrow(ConfigError);
    });

    it("rejects zone with missing rollup", () => {
      expect(() =>
        validateConfig({
          type: "custom:evenkeel-boat-card",
          zones: { bilge: { navigate: "/x" } },
        }),
      ).toThrow(/rollup/);
    });

    it("rejects zone with bad rollup entity_id", () => {
      expect(() =>
        validateConfig({
          type: "custom:evenkeel-boat-card",
          zones: { bilge: { rollup: "not-a-valid-id" } },
        }),
      ).toThrow(/rollup/);
    });

    it("rejects zone with non-string navigate", () => {
      expect(() =>
        validateConfig({
          type: "custom:evenkeel-boat-card",
          zones: { bilge: { rollup: "sensor.x", navigate: 42 } },
        }),
      ).toThrow(/navigate/);
    });

    it("KNOWN_ZONE_KEYS catalog exposes every zone the card draws", () => {
      // This locks down the public list — the card's SVG ZONES array
      // and this catalog must agree. Adding a new zone in boat-svg.ts
      // requires updating KNOWN_ZONE_KEYS too.
      expect(KNOWN_ZONE_KEYS.length).toBeGreaterThanOrEqual(8);
      expect(KNOWN_ZONE_KEYS).toContain("bilge");
      expect(KNOWN_ZONE_KEYS).toContain("engine");
    });
  });

  describe("power_flow", () => {
    it("optional", () => {
      const cfg = validateConfig({ type: "custom:evenkeel-boat-card" });
      expect(cfg.power_flow).toBeUndefined();
    });

    it("accepts partial config", () => {
      const cfg = validateConfig({
        type: "custom:evenkeel-boat-card",
        power_flow: {
          shore: "binary_sensor.boat_shore_power",
          battery_v: "sensor.boat_house_battery_v",
        },
      });
      expect(cfg.power_flow).toEqual({
        shore: "binary_sensor.boat_shore_power",
        battery_v: "sensor.boat_house_battery_v",
      });
    });

    it("rejects malformed entity in power_flow", () => {
      expect(() =>
        validateConfig({
          type: "custom:evenkeel-boat-card",
          power_flow: { shore: "BadCaps" },
        }),
      ).toThrow(/shore/);
    });

    it("ignores extraneous keys in power_flow", () => {
      // Defensive: we don't reject extras, we just don't propagate them.
      const cfg = validateConfig({
        type: "custom:evenkeel-boat-card",
        power_flow: {
          shore: "binary_sensor.boat_shore_power",
          extraneous_key: "sensor.x",
        },
      });
      expect(cfg.power_flow).toEqual({ shore: "binary_sensor.boat_shore_power" });
    });
  });

  describe("footer_vitals", () => {
    it("optional", () => {
      const cfg = validateConfig({ type: "custom:evenkeel-boat-card" });
      expect(cfg.footer_vitals).toBeUndefined();
    });

    it("accepts up to 6 entities", () => {
      const cfg = validateConfig({
        type: "custom:evenkeel-boat-card",
        footer_vitals: [
          "sensor.a",
          "sensor.b",
          "sensor.c",
          "sensor.d",
          "sensor.e",
          "sensor.f",
        ],
      });
      expect(cfg.footer_vitals).toHaveLength(6);
    });

    it("rejects more than 6 entries", () => {
      expect(() =>
        validateConfig({
          type: "custom:evenkeel-boat-card",
          footer_vitals: Array(7).fill("sensor.a"),
        }),
      ).toThrow(/at most 6/);
    });

    it("rejects non-array", () => {
      expect(() =>
        validateConfig({ type: "custom:evenkeel-boat-card", footer_vitals: "sensor.a" }),
      ).toThrow(ConfigError);
    });

    it("rejects bad entity_id within array", () => {
      expect(() =>
        validateConfig({ type: "custom:evenkeel-boat-card", footer_vitals: ["sensor.a", "Bad ID"] }),
      ).toThrow(/footer_vitals/);
    });
  });

  describe("ConfigError", () => {
    it("is an Error subclass with .name", () => {
      try {
        validateConfig({});
      } catch (e) {
        expect(e).toBeInstanceOf(ConfigError);
        expect(e).toBeInstanceOf(Error);
        expect((e as Error).name).toBe("ConfigError");
      }
    });
  });
});
