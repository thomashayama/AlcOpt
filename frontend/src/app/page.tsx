'use client';

import { useEffect, useState, useMemo } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { theme } from '@/lib/theme';
import type { LeaderboardEntry, ReviewOut } from '@/lib/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
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
  fermentation_id: number;
  avg_rating: number;
  abv: number;
}

interface RatingRsPoint {
  fermentation_id: number;
  avg_rating: number;
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
    () => ratingsAbv.map((p) => ({ x: p.abv, y: p.avg_rating })),
    [ratingsAbv],
  );
  const abvReg = useMemo(() => linearRegression(abvScatter), [abvScatter]);
  const abvTrend = useMemo(
    () => (abvReg ? buildTrendlineData(abvScatter, abvReg) : []),
    [abvScatter, abvReg],
  );

  const rsScatter = useMemo(
    () => ratingsRs.map((p) => ({ x: p.residual_sugar, y: p.avg_rating })),
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

  return (
    <div className="mx-auto w-full max-w-7xl space-y-8 px-4 py-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">AlcOpt Dashboard</h1>
        <Link href="/tasting">
          <Button>Submit Tasting</Button>
        </Link>
      </div>

      {/* Leaderboard */}
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
                  <TableHead className="w-16">Rank</TableHead>
                  <TableHead>Fermentation</TableHead>
                  <TableHead>Avg Rating</TableHead>
                  <TableHead className="w-24 text-right">Reviews</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {leaderboard.map((entry) => (
                  <TableRow key={entry.fermentation_id}>
                    <TableCell className="font-medium">{entry.rank}</TableCell>
                    <TableCell>Fermentation #{entry.fermentation_id}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="h-2.5 w-32 rounded-full bg-muted overflow-hidden">
                          <div
                            className="h-full rounded-full transition-all"
                            style={{
                              width: `${(entry.avg_rating / maxRating) * 100}%`,
                              backgroundColor: theme.primary,
                            }}
                          />
                        </div>
                        <span className="text-sm tabular-nums">
                          {entry.avg_rating.toFixed(2)}
                        </span>
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
              <div className="h-[400px]">
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
                  colors={{
                    type: 'diverging',
                    scheme: 'red_yellow_green',
                    minValue: -1,
                    maxValue: 1,
                  }}
                  emptyColor="#3A2F2A"
                  borderWidth={1}
                  borderColor="#1A1410"
                  theme={{
                    text: { fill: theme.text },
                    axis: {
                      ticks: { text: { fill: theme.text, fontSize: 11 } },
                    },
                    tooltip: {
                      container: {
                        background: theme.surface,
                        color: theme.text,
                      },
                    },
                  }}
                  labelTextColor={{ from: 'color', modifiers: [['darker', 3]] }}
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
              <div className="h-[400px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={ratingDistribution}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(245,240,232,0.1)" />
                    <XAxis
                      dataKey="rating"
                      label={{ value: 'Rating', position: 'insideBottom', offset: -5, fill: theme.text }}
                      tick={{ fill: theme.text }}
                    />
                    <YAxis
                      allowDecimals={false}
                      label={{
                        value: 'Count',
                        angle: -90,
                        position: 'insideLeft',
                        fill: theme.text,
                      }}
                      tick={{ fill: theme.text }}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: theme.surface,
                        border: `1px solid ${theme.primary}`,
                        color: theme.text,
                        borderRadius: 8,
                      }}
                    />
                    <Bar dataKey="count" fill={theme.primary} radius={[4, 4, 0, 0]} />
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
              <div className="h-[400px]">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(245,240,232,0.1)" />
                    <XAxis
                      dataKey="x"
                      type="number"
                      name="ABV"
                      unit="%"
                      label={{ value: 'ABV %', position: 'insideBottom', offset: -5, fill: theme.text }}
                      tick={{ fill: theme.text }}
                    />
                    <YAxis
                      dataKey="y"
                      type="number"
                      name="Rating"
                      domain={[0, 5]}
                      label={{
                        value: 'Overall Rating',
                        angle: -90,
                        position: 'insideLeft',
                        fill: theme.text,
                      }}
                      tick={{ fill: theme.text }}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: theme.surface,
                        border: `1px solid ${theme.primary}`,
                        color: theme.text,
                        borderRadius: 8,
                      }}
                    />
                    <Scatter data={abvScatter} fill={theme.accent} />
                    {abvTrend.length > 0 && (
                      <Line
                        data={abvTrend}
                        dataKey="y"
                        stroke={theme.primary}
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
              <div className="h-[400px]">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(245,240,232,0.1)" />
                    <XAxis
                      dataKey="x"
                      type="number"
                      name="Residual Sugar"
                      label={{
                        value: 'Residual Sugar (g/L)',
                        position: 'insideBottom',
                        offset: -5,
                        fill: theme.text,
                      }}
                      tick={{ fill: theme.text }}
                    />
                    <YAxis
                      dataKey="y"
                      type="number"
                      name="Rating"
                      domain={[0, 5]}
                      label={{
                        value: 'Overall Rating',
                        angle: -90,
                        position: 'insideLeft',
                        fill: theme.text,
                      }}
                      tick={{ fill: theme.text }}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: theme.surface,
                        border: `1px solid ${theme.primary}`,
                        color: theme.text,
                        borderRadius: 8,
                      }}
                    />
                    <Scatter data={rsScatter} fill={theme.accent} />
                    {rsTrend.length > 0 && (
                      <Line
                        data={rsTrend}
                        dataKey="y"
                        stroke={theme.primary}
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
