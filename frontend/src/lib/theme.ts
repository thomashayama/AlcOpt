/**
 * Cellar palette for code that can't read CSS variables (Recharts and Nivo
 * props). Keep in sync with the `.dark` block in app/globals.css.
 */
export const theme = {
  primary: '#A4243B',
  accent: '#D4A24C',
  background: '#1A1410',
  card: '#231914',
  surface: '#2E221B',
  text: '#F5F0E8',
  muted: '#B8A996',
  grid: 'rgba(245,240,232,0.11)',
  axis: 'rgba(245,240,232,0.24)',
  // Chart marks: the burgundy and gold stepped so both clear 3:1 on `card`
  // and stay apart under colour-vision deficiency. Use these for bars, lines
  // and points, not `primary` / `accent`.
  wine: '#BE3F5A',
  gold: '#B98A36',
} as const;

/** Shared look for chart axes and tooltips. */
export const chartTick = { fill: theme.muted, fontSize: 12 } as const;

export const chartAxisLine = { stroke: theme.axis } as const;

export const chartTooltipStyle = {
  backgroundColor: theme.surface,
  border: `1px solid ${theme.axis}`,
  borderRadius: 4,
  color: theme.text,
} as const;

/** Axis title props for Recharts `label`. */
export function chartAxisTitle(value: string, side: 'bottom' | 'left' | 'right') {
  if (side === 'bottom') {
    return { value, position: 'insideBottom' as const, offset: -5, fill: theme.muted, fontSize: 12 };
  }
  return {
    value,
    angle: side === 'left' ? -90 : 90,
    position: side === 'left' ? ('insideLeft' as const) : ('insideRight' as const),
    fill: theme.muted,
    fontSize: 12,
  };
}

// Correlation runs from -1 to 1: cool pole, neutral midpoint, warm pole.
const CORRELATION_STOPS = {
  negative: [56, 111, 160],
  zero: [51, 46, 43],
  positive: [176, 58, 85],
} as const;

/** Diverging colour for a correlation coefficient in [-1, 1]. */
export function correlationColor(value: number | null): string {
  if (value == null || Number.isNaN(value)) return theme.surface;
  const t = Math.max(-1, Math.min(1, value));
  const pole = t < 0 ? CORRELATION_STOPS.negative : CORRELATION_STOPS.positive;
  const mix = Math.abs(t);
  const [r, g, b] = CORRELATION_STOPS.zero.map((c, i) =>
    Math.round(c + (pole[i] - c) * mix),
  );
  return `rgb(${r}, ${g}, ${b})`;
}
