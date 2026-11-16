'use client';

import { useEffect, useState, useMemo } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import {
  chartAxisLine,
  chartAxisTitle,
  chartTick,
  chartTooltipStyle,
  correlationColor,
  theme,
} from '@/lib/theme';
import { cn } from '@/lib/utils';
import type { LeaderboardEntry, ReviewOut } from '@/lib/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { buttonVariants } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Line,
  ComposedChart,
} from 'recharts';
import { ResponsiveHeatMap } from '@nivo/heatmap';

interface RatingAbvPoint {
  overall_rating: number;
  abv: number;
}

interface RatingRsPoint {
  overall_rating: number;
  residual_sugar: number;
}

const RATING_ATTRS = [
  'overall_rating',
  'boldness',
  'tannicity',
  'sweetness',
  'acidity',
  'complexity',
] as const;

const ATTR_LABELS: Record<string, string> = {
  overall_rating: 'Overall',
  boldness: 'Boldness',
  tannicity: 'Tannicity',
  sweetness: 'Sweetness',
  acidity: 'Acidity',
  complexity: 'Complexity',
};

function computeCorrelationMatrix(reviews: ReviewOut[]) {
  if (reviews.length < 2) return [];

  const means: Record<string, number> = {};
  for (const attr of RATING_ATTRS) {
    means[attr] = reviews.reduce((s, r) => s + r[attr], 0) / reviews.length;
  }

  function pearson(a: (typeof RATING_ATTRS)[number], b: (typeof RATING_ATTRS)[number]) {
    let sumAB = 0;
    let sumA2 = 0;
    let sumB2 = 0;
    for (const r of reviews) {
      const da = r[a] - means[a];
      const db = r[b] - means[b];
      sumAB += da * db;
      sumA2 += da * da;
      sumB2 += db * db;
    }
    const denom = Math.sqrt(sumA2 * sumB2);
    return denom === 0 ? 0 : sumAB / denom;
  }

  return RATING_ATTRS.map((row) => ({
    id: ATTR_LABELS[row],
    data: RATING_ATTRS.map((col) => ({
      x: ATTR_LABELS[col],
      y: Math.round(pearson(row, col) * 100) / 100,
    })),
  }));
}

function linearRegression(points: { x: number; y: number }[]) {
  if (points.length < 2) return null;
  const n = points.length;
  const sumX = points.reduce((s, p) => s + p.x, 0);
  const sumY = points.reduce((s, p) => s + p.y, 0);
  const sumXY = points.reduce((s, p) => s + p.x * p.y, 0);
  const sumX2 = points.reduce((s, p) => s + p.x * p.x, 0);
  const denom = n * sumX2 - sumX * sumX;
  if (denom === 0) return null;
  const slope = (n * sumXY - sumX * sumY) / denom;
  const intercept = (sumY - slope * sumX) / n;
  return { slope, intercept };
}

function buildTrendlineData(
  points: { x: number; y: number }[],
  reg: { slope: number; intercept: number },
) {
  if (points.length === 0) return [];
  const xs = points.map((p) => p.x);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  return [
    { x: minX, y: reg.slope * minX + reg.intercept },
    { x: maxX, y: reg.slope * maxX + reg.intercept },
  ];
}

function count(n: number, noun: string) {
  return `${n} ${noun}${n === 1 ? '' : 's'}`;
}

/** Thin rule with a diamond, as on a printed wine label. */
function LabelRule() {
  return (
    <div aria-hidden className="mx-auto my-3.5 flex w-2/3 items-center gap-2.5">
      <span className="h-px flex-1 bg-current opacity-45" />
      <span className="size-1.5 rotate-45 bg-primary" />
      <span className="h-px flex-1 bg-current opacity-45" />
    </div>
  );
}

/** The top-ranked fermentation, set as a bottle label. */
function TopRatedLabel({ entry }: { entry: LeaderboardEntry }) {
  return (
    <aside
      aria-label="Top rated fermentation"
      className="flex flex-col justify-center rounded-xs bg-label px-6 py-9 text-center text-label-foreground outline-1 outline-offset-[-10px] outline-label-foreground/50"
    >
      <p className="font-heading text-[1.3125rem] leading-none font-medium italic">Top rated</p>
      <LabelRule />
      <p className="font-heading text-xl leading-none font-medium tracking-[0.08em]">
        Fermentation
      </p>
      <p className="font-heading text-7xl leading-none font-bold">Nº {entry.fermentation_id}</p>
      <LabelRule />
      <p className="font-heading text-[2.875rem] leading-none font-semibold text-primary">
        {entry.avg_rating.toFixed(2)}
      </p>
      <p className="mt-1.5 text-[0.8125rem]">
        average of {count(entry.num_ratings, 'tasting')}
      </p>
    </aside>
  );
}

export default function HomePage() {
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [reviews, setReviews] = useState<ReviewOut[]>([]);
  const [ratingsAbv, setRatingsAbv] = useState<RatingAbvPoint[]>([]);
  const [ratingsRs, setRatingsRs] = useState<RatingRsPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get<LeaderboardEntry[]>('/api/leaderboard'),
      api.get<ReviewOut[]>('/api/analytics/reviews'),
      api.get<RatingAbvPoint[]>('/api/analytics/ratings-abv'),
      api.get<RatingRsPoint[]>('/api/analytics/ratings-rs'),
    ])
      .then(([lb, rev, abv, rs]) => {
        setLeaderboard(lb);
        setReviews(rev);
        setRatingsAbv(abv);
        setRatingsRs(rs);
      })
      .catch((err) => {
        console.error('Failed to fetch home data:', err);
      })
      .finally(() => setLoading(false));
  }, []);

  const heatmapData = useMemo(() => computeCorrelationMatrix(reviews), [reviews]);

  const ratingDistribution = useMemo(() => {
    const bins = [
      { rating: '1', count: 0 },
      { rating: '2', count: 0 },
      { rating: '3', count: 0 },
      { rating: '4', count: 0 },
      { rating: '5', count: 0 },
    ];
    for (const r of reviews) {
      const bucket = Math.max(1, Math.min(5, Math.round(r.overall_rating)));
      bins[bucket - 1].count += 1;
    }
    return bins;
  }, [reviews]);

  const abvScatter = useMemo(
    () => ratingsAbv.map((p) => ({ x: p.abv, y: p.overall_rating })),
    [ratingsAbv],
  );
  const abvReg = useMemo(() => linearRegression(abvScatter), [abvScatter]);
  const abvTrend = useMemo(
    () => (abvReg ? buildTrendlineData(abvScatter, abvReg) : []),
    [abvScatter, abvReg],
  );

  const rsScatter = useMemo(
    () => ratingsRs.map((p) => ({ x: p.residual_sugar, y: p.overall_rating })),
    [ratingsRs],
  );
  const rsReg = useMemo(() => linearRegression(rsScatter), [rsScatter]);
  const rsTrend = useMemo(
    () => (rsReg ? buildTrendlineData(rsScatter, rsReg) : []),
    [rsScatter, rsReg],
  );

  const maxRating = useMemo(() => {
    if (leaderboard.length === 0) return 5;
    return Math.max(...leaderboard.map((e) => e.avg_rating), 5);
  }, [leaderboard]);

  if (loading) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  const topRated = leaderboard[0];

  return (
    <div className="mx-auto w-full max-w-7xl space-y-6 px-4 pt-2 pb-12 md:px-5 md:pt-11 md:pb-16">
      <div className="flex flex-wrap items-end justify-between gap-4 pb-1">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="mt-2.5 text-muted-foreground">
            {reviews.length === 0
              ? 'No tastings yet.'
              : `${count(reviews.length, 'tasting')} across ${count(leaderboard.length, 'fermentation')}.`}
          </p>
        </div>
        <Link href="/tasting" className={cn(buttonVariants(), 'max-sm:w-full')}>
          Submit Tasting
        </Link>
      </div>

      {/* Top-rated label + leaderboard */}
      <div className={cn('grid gap-6', topRated && 'md:grid-cols-[280px_1fr] lg:grid-cols-[300px_1fr]')}>
        {topRated && <TopRatedLabel entry={topRated} />}
        <Card>
          <CardHeader>
            <CardTitle>Leaderboard</CardTitle>
          </CardHeader>
          <CardContent>
            {leaderboard.length === 0 ? (
              <p className="text-muted-foreground">No ratings yet.</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-10 sm:w-16">
                      <span className="sm:hidden">#</span>
                      <span className="hidden sm:inline">Rank</span>
                    </TableHead>
                    <TableHead>
                      <span className="sm:hidden">Ferm.</span>
                      <span className="hidden sm:inline">Fermentation</span>
                    </TableHead>
                    <TableHead>Avg Rating</TableHead>
                    <TableHead className="text-right sm:w-24">Reviews</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {leaderboard.map((entry, i) => (
                    <TableRow key={entry.fermentation_id}>
                      <TableCell
                        className={cn(
                          'font-heading text-2xl leading-none font-semibold',
                          i === 0 ? 'text-accent' : 'text-muted-foreground',
                        )}
                      >
                        {entry.rank}
                      </TableCell>
                      <TableCell>
                        <span className="hidden sm:inline">Fermentation </span>#
                        {entry.fermentation_id}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2 sm:gap-3">
                          <div className="h-1.5 w-14 shrink-0 overflow-hidden rounded-full bg-well sm:w-28 lg:w-48">
                            <div
                              className={cn(
                                'h-full rounded-full',
                                i === 0 ? 'bg-accent' : 'bg-chart-1',
                              )}
                              style={{ width: `${(entry.avg_rating / maxRating) * 100}%` }}
                            />
                          </div>
                          <span>{entry.avg_rating.toFixed(2)}</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-right">{entry.num_ratings}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Charts grid */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Correlation Heatmap */}
        <Card>
          <CardHeader>
            <CardTitle>Rating Attribute Correlations</CardTitle>
          </CardHeader>
          <CardContent>
            {heatmapData.length === 0 ? (
              <p className="text-muted-foreground">Not enough reviews for correlation data.</p>
            ) : (
              <div className="h-[300px] sm:h-[400px]">
                <ResponsiveHeatMap
                  data={heatmapData}
                  margin={{ top: 60, right: 30, bottom: 30, left: 80 }}
                  axisTop={{
                    tickSize: 0,
                    tickPadding: 5,
                    tickRotation: -45,
                  }}
                  axisLeft={{
                    tickSize: 0,
                    tickPadding: 5,
                  }}
                  colors={(cell) => correlationColor(cell.value)}
                  emptyColor={theme.surface}
                  borderWidth={2}
                  borderColor={theme.card}
                  theme={{
                    text: { fill: theme.text },
                    axis: {
                      ticks: { text: { fill: theme.muted, fontSize: 11 } },
                    },
                    tooltip: {
                      container: {
                        background: theme.surface,
                        color: theme.text,
                        borderRadius: 4,
                      },
                    },
                  }}
                  labelTextColor={theme.text}
                  hoverTarget="cell"
                />
              </div>
            )}
          </CardContent>
        </Card>

        {/* Rating Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Overall Rating Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            {reviews.length === 0 ? (
              <p className="text-muted-foreground">No reviews yet.</p>
            ) : (
              <div className="h-[300px] sm:h-[400px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={ratingDistribution}>
                    <CartesianGrid vertical={false} stroke={theme.grid} />
                    <XAxis
                      dataKey="rating"
                      label={chartAxisTitle('Rating', 'bottom')}
                      tick={chartTick}
                      axisLine={chartAxisLine}
                      tickLine={false}
                    />
                    <YAxis
                      allowDecimals={false}
                      label={chartAxisTitle('Count', 'left')}
                      tick={chartTick}
                      axisLine={false}
                      tickLine={false}
                    />
                    <Tooltip contentStyle={chartTooltipStyle} cursor={{ fill: theme.grid }} />
                    <Bar dataKey="count" fill={theme.wine} radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Rating vs ABV */}
        <Card>
          <CardHeader>
            <CardTitle>Overall Rating vs ABV</CardTitle>
          </CardHeader>
          <CardContent>
            {abvScatter.length === 0 ? (
              <p className="text-muted-foreground">No ABV data available.</p>
            ) : (
              <div className="h-[300px] sm:h-[400px]">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart>
                    <CartesianGrid stroke={theme.grid} />
                    <XAxis
                      dataKey="x"
                      type="number"
                      name="ABV"
                      unit="%"
                      label={chartAxisTitle('ABV %', 'bottom')}
                      tick={chartTick}
                      axisLine={chartAxisLine}
                      tickLine={false}
                    />
                    <YAxis
                      dataKey="y"
                      type="number"
                      name="Rating"
                      domain={[0, 5]}
                      label={chartAxisTitle('Overall Rating', 'left')}
                      tick={chartTick}
                      axisLine={false}
                      tickLine={false}
                    />
                    <Tooltip contentStyle={chartTooltipStyle} cursor={{ stroke: theme.axis }} />
                    <Scatter
                      data={abvScatter}
                      fill={theme.gold}
                      stroke={theme.card}
                      strokeWidth={1.5}
                    />
                    {abvTrend.length > 0 && (
                      <Line
                        data={abvTrend}
                        dataKey="y"
                        stroke={theme.wine}
                        strokeWidth={2}
                        dot={false}
                        legendType="none"
                      />
                    )}
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Rating vs Residual Sugar */}
        <Card>
          <CardHeader>
            <CardTitle>Overall Rating vs Residual Sugar</CardTitle>
          </CardHeader>
          <CardContent>
            {rsScatter.length === 0 ? (
              <p className="text-muted-foreground">No residual sugar data available.</p>
            ) : (
              <div className="h-[300px] sm:h-[400px]">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart>
                    <CartesianGrid stroke={theme.grid} />
                    <XAxis
                      dataKey="x"
                      type="number"
                      name="Residual Sugar"
                      label={chartAxisTitle('Residual Sugar (g/L)', 'bottom')}
                      tick={chartTick}
                      axisLine={chartAxisLine}
                      tickLine={false}
                    />
                    <YAxis
                      dataKey="y"
                      type="number"
                      name="Rating"
                      domain={[0, 5]}
                      label={chartAxisTitle('Overall Rating', 'left')}
                      tick={chartTick}
                      axisLine={false}
                      tickLine={false}
                    />
                    <Tooltip contentStyle={chartTooltipStyle} cursor={{ stroke: theme.axis }} />
                    <Scatter
                      data={rsScatter}
                      fill={theme.gold}
                      stroke={theme.card}
                      strokeWidth={1.5}
                    />
                    {rsTrend.length > 0 && (
                      <Line
                        data={rsTrend}
                        dataKey="y"
                        stroke={theme.wine}
                        strokeWidth={2}
                        dot={false}
                        legendType="none"
                      />
                    )}
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
