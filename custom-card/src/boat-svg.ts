/**
 * Hunter 41DS top-down profile.
 *
 * Each named compartment is a `<g class="zone severity-…" data-zone="<key>">`.
 * The card's stylesheet colors the fill based on the severity class.
 *
 * v0.2 (Iteration 2E): tightened hull silhouette to a recognisable
 * sloop — pointed bow at the right, transom-stern at the left, beam
 * widest amidships. Compartments now match the typical Hunter 41DS
 * layout (cockpit aft of engine, galley + nav station port/starboard
 * of companionway, salon centerline, head + V-berth forward) and
 * taper at both ends so they don't visually bleed past the hull.
 *
 * Coordinate system: 800 × 320, bow on the right, stern on the left.
 *   Stern transom: x = 30
 *   Bow tip:       x = 780
 *   Centerline:    y = 160
 *   Beam max:      y ∈ [70, 250]  (180 px tall ≈ Hunter's 14′ beam)
 */

import { svg, type SVGTemplateResult } from "lit";

export const BOAT_VIEWBOX = "0 0 800 320";

/**
 * The boat hull outline: transom-stern at the left, sweet sweep up to
 * a pointed bow on the right. Drawn first so zones overlay it.
 *
 * Path beats:
 *   - flat-ish transom across the stern from (30, 70) to (30, 250)
 *   - smooth chine up to the widest beam at amidships (~ x 380)
 *   - gentle taper toward the bow
 *   - sharp point at the bow tip (780, 160)
 *   - symmetric chine back down
 */
export const HULL_PATH = svg`
  <path
    d="M 30 90
       Q 25 70, 60 65
       Q 220 50, 380 60
       Q 560 60, 700 100
       Q 760 130, 780 160
       Q 760 190, 700 220
       Q 560 260, 380 260
       Q 220 270, 60 255
       Q 25 250, 30 230
       Z"
    fill="var(--card-background-color, #ffffff)"
    stroke="var(--primary-text-color, #1c1c1e)"
    stroke-width="2"
    stroke-linejoin="round"
  />`;

/**
 * Toe rail — a thin inner line that hints at deck edge and reinforces
 * the hull silhouette without competing with zone color.
 */
export const TOE_RAIL = svg`
  <path
    d="M 50 95
       Q 220 75, 380 80
       Q 560 80, 690 115
       Q 740 140, 760 160
       Q 740 180, 690 205
       Q 560 240, 380 240
       Q 220 245, 50 225"
    fill="none"
    stroke="var(--primary-text-color, #1c1c1e)"
    stroke-width="1"
    stroke-opacity="0.25"
  />`;

interface Zone {
  key: string;
  label: string;
  /**
   * SVG path describing the zone's interior shape. Taking shapes as
   * paths (instead of x/y/w/h rectangles) lets the V-berth and forepeak
   * taper into the bow rather than ending in unrealistic right angles.
   */
  d: string;
  /** Label x,y in viewBox coords. */
  lx: number;
  ly: number;
}

export const ZONES: Zone[] = [
  // Stern → bow.
  {
    key: "lazarette",
    label: "LAZ",
    // Just inside the transom — shallow, full-beam.
    d: "M 45 95 L 110 90 L 110 230 L 45 225 Z",
    lx: 78,
    ly: 165,
  },
  {
    key: "cockpit",
    label: "COCKPIT",
    // Slightly trapezoidal — narrower at the companionway end.
    d: "M 115 90 L 115 230 L 235 220 L 235 100 Z",
    lx: 175,
    ly: 165,
  },
  {
    key: "engine_bay",
    label: "ENGINE",
    // Under the cockpit sole — narrower, centerline-biased.
    d: "M 240 110 L 240 210 L 320 205 L 320 115 Z",
    lx: 280,
    ly: 165,
  },
  {
    key: "galley",
    label: "GALLEY",
    // Port side, just forward of the engine.
    d: "M 325 80 L 325 155 L 410 155 L 410 78 Z",
    lx: 367,
    ly: 122,
  },
  {
    key: "nav_station",
    label: "NAV",
    // Starboard, mirror of galley.
    d: "M 325 165 L 325 240 L 410 242 L 410 165 Z",
    lx: 367,
    ly: 207,
  },
  {
    key: "salon",
    label: "SALON",
    // Centerline mid — large, slightly tapered toward the bow.
    d: "M 415 90 L 415 230 L 555 220 L 555 100 Z",
    lx: 485,
    ly: 165,
  },
  {
    key: "head",
    label: "HEAD",
    // Port-side mid-forward, between salon and V-berth.
    d: "M 560 95 L 560 155 L 640 145 L 640 100 Z",
    lx: 600,
    ly: 127,
  },
  {
    key: "v_berth",
    label: "V-BERTH",
    // Forward — tapering toward the bow.
    d: "M 560 165 L 560 220 L 640 210 L 645 165 Z",
    lx: 600,
    ly: 192,
  },
  {
    key: "forepeak",
    label: "FOREPEAK",
    // The pointy bow itself.
    d: "M 650 110 L 745 158 L 745 162 L 650 210 Z",
    lx: 690,
    ly: 165,
  },
];

/**
 * The bilge crosses several compartments at the bottom of the hull.
 * Drawn as a separate translucent strip overlaid on the keel line.
 *
 * Built as a function so the severity class is set at render time.
 */
export function bilgeOverlay(severity: string): SVGTemplateResult {
  const cls = `zone bilge-strip severity-${severity}`;
  return svg`
    <g class=${cls} data-zone="bilge">
      <rect x="120" y="155" width="430" height="10"
            rx="4" ry="4"
            class="zone-bg"/>
    </g>`;
}

/**
 * Mast — concentric circles at the deck step. The Hunter 41DS mast is
 * stepped on the cabin top roughly above the head/forward salon, so we
 * place it on centerline at ~ x 530.
 */
export const MAST_DOT = svg`
  <g aria-label="Mast" opacity="0.85">
    <circle cx="530" cy="160" r="6"
            fill="var(--card-background-color, #fff)"
            stroke="var(--primary-text-color, #1c1c1e)"
            stroke-width="1.5"/>
    <circle cx="530" cy="160" r="2.5"
            fill="var(--primary-text-color, #1c1c1e)"
            opacity="0.7"/>
  </g>`;

/**
 * Helm wheel inside the cockpit. Hunter 41DS has a single pedestal
 * roughly amidships of the cockpit footwell.
 */
export const HELM = svg`
  <g aria-label="Helm" opacity="0.7">
    <circle cx="170" cy="160" r="9"
            fill="none"
            stroke="var(--primary-text-color, #1c1c1e)"
            stroke-width="1.2"/>
    <line x1="161" y1="160" x2="179" y2="160"
          stroke="var(--primary-text-color, #1c1c1e)"
          stroke-width="1.2"/>
    <line x1="170" y1="151" x2="170" y2="169"
          stroke="var(--primary-text-color, #1c1c1e)"
          stroke-width="1.2"/>
  </g>`;

/**
 * Bow pulpit — open V at the very tip of the bow, hinting at the
 * stainless rail without rendering every stanchion.
 */
export const BOW_PULPIT = svg`
  <path d="M 720 145 L 770 160 L 720 175"
        fill="none"
        stroke="var(--primary-text-color, #1c1c1e)"
        stroke-width="1.2"
        opacity="0.55"/>`;

/**
 * Stern rail — short bracket at the transom corners.
 */
export const STERN_RAIL = svg`
  <g opacity="0.55">
    <path d="M 35 78 L 50 92"
          stroke="var(--primary-text-color, #1c1c1e)"
          stroke-width="1.2" fill="none"/>
    <path d="M 35 242 L 50 228"
          stroke="var(--primary-text-color, #1c1c1e)"
          stroke-width="1.2" fill="none"/>
  </g>`;

/**
 * Navigation lights: red (port, y > 160), green (starboard, y < 160),
 * white stern light. Always rendered — independent of severity since
 * they're a cosmetic landmark.
 */
export const NAV_LIGHTS = svg`
  <g aria-label="Nav lights" opacity="0.85">
    <circle cx="745" cy="155" r="2.5" fill="#22c55e"/>   <!-- starboard green -->
    <circle cx="745" cy="165" r="2.5" fill="#ef4444"/>   <!-- port red -->
    <circle cx="40"  cy="160" r="2.5" fill="#f8fafc"
            stroke="var(--primary-text-color, #1c1c1e)"
            stroke-width="0.8"/>                          <!-- stern white -->
  </g>`;

/**
 * Render the SVG body. Each zone gets a CSS class indicating its
 * current severity so the card's stylesheet can color it.
 *
 * We use class-based severity rather than `data-severity` because
 * Lit's attribute binding inside `svg` templates is unreliable on
 * happy-dom (test runner) and on some browsers' SVG namespace
 * handling. CSS classes are universally honored.
 */
export function renderBoatBody(zoneSeverities: Record<string, string>): SVGTemplateResult {
  return svg`
    ${HULL_PATH}
    ${TOE_RAIL}
    ${ZONES.map((z) => {
      const sev = zoneSeverities[z.key] ?? "ok";
      const cls = `zone severity-${sev}`;
      return svg`
        <g class=${cls} data-zone=${z.key}>
          <path d=${z.d} class="zone-bg"/>
          <text x=${z.lx} y=${z.ly + 4}
                text-anchor="middle"
                class="zone-label"
                font-size="11"
                fill="var(--primary-text-color, #1c1c1e)"
                opacity="0.8">
            ${z.label}
          </text>
        </g>
      `;
    })}
    ${bilgeOverlay(zoneSeverities["bilge"] ?? "ok")}
    ${HELM}
    ${MAST_DOT}
    ${BOW_PULPIT}
    ${STERN_RAIL}
    ${NAV_LIGHTS}
  `;
}
