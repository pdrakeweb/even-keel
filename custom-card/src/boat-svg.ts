/**
 * Hunter 41DS top-down profile, simplified.
 *
 * Each named compartment is a `<g class="zone" data-zone="<key>">`.
 * The card sets `data-severity="<severity>"` at runtime; CSS in
 * evenkeel-boat-card.ts colors the fill accordingly.
 *
 * v0.1 uses simple polygon shapes — accurate enough to read at-a-glance
 * but not a precise replica. v0.2 will refine with vendor drawings.
 *
 * Coordinate system: 800 × 320, bow at right, stern at left.
 */

import { svg, type SVGTemplateResult } from "lit";

export const BOAT_VIEWBOX = "0 0 800 320";

/**
 * The boat hull outline. Drawn separately so the card can apply
 * a different stroke for theme variants without re-rendering zones.
 */
export const HULL_PATH = svg`
  <path
    d="M 30 160
       Q 30 100, 90 80
       L 700 80
       Q 770 80, 770 160
       Q 770 240, 700 260
       L 90 260
       Q 30 220, 30 160 Z"
    fill="var(--card-background-color, #ffffff)"
    stroke="var(--primary-text-color, #1c1c1e)"
    stroke-width="2"
  />`;

interface Zone {
  key: string;
  label: string;
  x: number;
  y: number;
  w: number;
  h: number;
  /** Rounded-rect radius. */
  r?: number;
}

export const ZONES: Zone[] = [
  { key: "lazarette", label: "LAZ", x: 50, y: 100, w: 90, h: 120, r: 12 },
  { key: "cockpit", label: "COCKPIT", x: 145, y: 95, w: 110, h: 130, r: 10 },
  { key: "engine_bay", label: "ENGINE", x: 260, y: 110, w: 90, h: 100, r: 8 },
  { key: "galley", label: "GALLEY", x: 355, y: 95, w: 80, h: 60, r: 6 },
  { key: "nav_station", label: "NAV", x: 355, y: 165, w: 80, h: 60, r: 6 },
  { key: "head", label: "HEAD", x: 440, y: 95, w: 60, h: 60, r: 6 },
  { key: "salon", label: "SALON", x: 440, y: 165, w: 110, h: 60, r: 6 },
  { key: "v_berth", label: "V-BERTH", x: 555, y: 95, w: 130, h: 130, r: 12 },
  { key: "forepeak", label: "FOREPEAK", x: 690, y: 110, w: 70, h: 100, r: 14 },
];

/**
 * The bilge crosses several compartments at the bottom of the hull.
 * Drawn as a separate translucent strip overlaid on the keel line.
 *
 * Built as a function so the severity attribute is set at render time.
 */
export function bilgeOverlay(severity: string): SVGTemplateResult {
  const cls = `zone bilge-strip severity-${severity}`;
  return svg`
    <g class=${cls} data-zone="bilge">
      <rect x="100" y="220" width="600" height="20"
            rx="6" ry="6"
            class="zone-bg"/>
    </g>`;
}

/**
 * Keel hint — purely cosmetic.
 */
export const KEEL_HINT = svg`
  <path d="M 350 260 Q 400 285, 450 260" fill="none"
        stroke="var(--secondary-text-color, #5a5a5e)"
        stroke-width="2" stroke-linecap="round" opacity="0.4"/>`;

/**
 * Mast indicator — small dot near salon center.
 */
export const MAST_DOT = svg`<circle cx="495" cy="195" r="4"
  fill="var(--secondary-text-color, #5a5a5e)" opacity="0.6"/>`;

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
    ${ZONES.map((z) => {
      const sev = zoneSeverities[z.key] ?? "ok";
      const cls = `zone severity-${sev}`;
      return svg`
        <g class=${cls} data-zone=${z.key}>
          <rect x=${z.x} y=${z.y} width=${z.w} height=${z.h}
                rx=${z.r ?? 6} ry=${z.r ?? 6}
                class="zone-bg"/>
          <text x=${z.x + z.w / 2} y=${z.y + z.h / 2 + 4}
                text-anchor="middle"
                class="zone-label"
                font-size="11"
                fill="var(--primary-text-color, #1c1c1e)"
                opacity="0.75">
            ${z.label}
          </text>
        </g>
      `;
    })}
    ${bilgeOverlay(zoneSeverities["bilge"] ?? "ok")}
    ${KEEL_HINT}
    ${MAST_DOT}
  `;
}
