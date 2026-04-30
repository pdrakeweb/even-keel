/**
 * Card config schema + validation.
 *
 * The card YAML format (see info.md) maps cleanly to BoatCardConfig.
 * Anything that isn't structurally correct should be caught here so
 * users see a clear error rather than a blank card.
 */

export type Severity = "ok" | "warning" | "critical";

export interface ZoneConfig {
  /** Entity ID of a sensor whose state ∈ {ok, warning, critical}. */
  rollup: string;
  /** Optional override headline; otherwise pulls from rollup attribute. */
  headline?: string;
  /** Lovelace navigation path triggered on tap. */
  navigate?: string;
}

export interface PowerFlowConfig {
  shore?: string; // binary_sensor
  generator?: string; // binary_sensor
  solar?: string; // sensor (W)
  battery_v?: string; // sensor (V)
  battery_a?: string; // sensor (A — negative = discharge)
}

export interface BoatCardConfig {
  type: string; // always "custom:evenkeel-boat-card"
  boat_name?: string;
  /** Entity for the Captain's Glance headline at the top of the card. */
  overall_status?: string;
  zones?: Record<string, ZoneConfig>;
  power_flow?: PowerFlowConfig;
  /** Up to 4 entity IDs displayed in the bottom strip. */
  footer_vitals?: string[];
}

export class ConfigError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ConfigError";
  }
}

export const KNOWN_ZONE_KEYS = [
  "bilge",
  "engine",
  "climate",
  "electrical",
  "weather",
  "position",
  "safety",
  "system",
  "v_berth",
  "head",
  "galley",
  "nav_station",
  "lazarette",
  "forepeak",
  "cockpit",
] as const;

export type KnownZoneKey = (typeof KNOWN_ZONE_KEYS)[number];

const ENTITY_ID_RE = /^[a-z_][a-z0-9_]*\.[a-z0-9_]+$/;

/**
 * Validate user-supplied card config. Throws ConfigError on any structural
 * problem. Returns a defensively-copied, normalized config.
 */
export function validateConfig(raw: unknown): BoatCardConfig {
  if (!raw || typeof raw !== "object") {
    throw new ConfigError("Card config must be an object.");
  }
  const cfg = raw as Record<string, unknown>;

  if (typeof cfg.type !== "string" || !cfg.type.includes("evenkeel-boat-card")) {
    throw new ConfigError(`Bad or missing 'type' (got ${JSON.stringify(cfg.type)}).`);
  }

  if (cfg.boat_name !== undefined && typeof cfg.boat_name !== "string") {
    throw new ConfigError("'boat_name' must be a string.");
  }

  if (cfg.overall_status !== undefined) {
    if (typeof cfg.overall_status !== "string" || !ENTITY_ID_RE.test(cfg.overall_status)) {
      throw new ConfigError(`'overall_status' must be a valid entity_id, got ${JSON.stringify(cfg.overall_status)}.`);
    }
  }

  const zones: Record<string, ZoneConfig> = {};
  if (cfg.zones !== undefined) {
    if (!cfg.zones || typeof cfg.zones !== "object" || Array.isArray(cfg.zones)) {
      throw new ConfigError("'zones' must be a mapping of zone-name → zone config.");
    }
    for (const [key, val] of Object.entries(cfg.zones as Record<string, unknown>)) {
      if (!val || typeof val !== "object") {
        throw new ConfigError(`Zone '${key}' must be an object.`);
      }
      const zone = val as Record<string, unknown>;
      if (typeof zone.rollup !== "string" || !ENTITY_ID_RE.test(zone.rollup)) {
        throw new ConfigError(`Zone '${key}': 'rollup' must be a valid entity_id, got ${JSON.stringify(zone.rollup)}.`);
      }
      if (zone.navigate !== undefined && typeof zone.navigate !== "string") {
        throw new ConfigError(`Zone '${key}': 'navigate' must be a string path.`);
      }
      if (zone.headline !== undefined && typeof zone.headline !== "string") {
        throw new ConfigError(`Zone '${key}': 'headline' must be a string.`);
      }
      zones[key] = {
        rollup: zone.rollup,
        headline: zone.headline as string | undefined,
        navigate: zone.navigate as string | undefined,
      };
    }
  }

  let powerFlow: PowerFlowConfig | undefined;
  if (cfg.power_flow !== undefined) {
    if (!cfg.power_flow || typeof cfg.power_flow !== "object") {
      throw new ConfigError("'power_flow' must be an object.");
    }
    const pf = cfg.power_flow as Record<string, unknown>;
    powerFlow = {};
    for (const k of ["shore", "generator", "solar", "battery_v", "battery_a"] as const) {
      const v = pf[k];
      if (v === undefined) continue;
      if (typeof v !== "string" || !ENTITY_ID_RE.test(v)) {
        throw new ConfigError(`'power_flow.${k}' must be a valid entity_id.`);
      }
      powerFlow[k] = v;
    }
  }

  let footerVitals: string[] | undefined;
  if (cfg.footer_vitals !== undefined) {
    if (!Array.isArray(cfg.footer_vitals)) {
      throw new ConfigError("'footer_vitals' must be a list of entity_ids.");
    }
    if (cfg.footer_vitals.length > 6) {
      throw new ConfigError("'footer_vitals' supports at most 6 entries.");
    }
    footerVitals = [];
    for (const e of cfg.footer_vitals) {
      if (typeof e !== "string" || !ENTITY_ID_RE.test(e)) {
        throw new ConfigError(`'footer_vitals' entry ${JSON.stringify(e)} is not a valid entity_id.`);
      }
      footerVitals.push(e);
    }
  }

  return {
    type: cfg.type,
    boat_name: cfg.boat_name as string | undefined,
    overall_status: cfg.overall_status as string | undefined,
    zones: Object.keys(zones).length > 0 ? zones : undefined,
    power_flow: powerFlow,
    footer_vitals: footerVitals,
  };
}
