'use client';

import { Suspense, useEffect, useState, useMemo, useCallback } from 'react';
import { useSearchParams } from 'next/navigation';
import { api } from '@/lib/api';
import { theme } from '@/lib/theme';
import type { ContainerInfoResponse, IngredientAdditionOut } from '@/lib/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

function daysBetween(start: string, date: string): number {
  const s = new Date(start);
  const d = new Date(date);
  return Math.round((d.getTime() - s.getTime()) / (1000 * 60 * 60 * 24));
}

export default function InfoPageWrapper() {
  return (
    <Suspense fallback={<div className="p-8 text-center">Loading...</div>}>
      <InfoPage />
    </Suspense>
  );
}

function InfoPage() {
  const searchParams = useSearchParams();
  const deepLinkId = searchParams.get('container_id');

  const [containerId, setContainerId] = useState(deepLinkId ?? '');
  const [data, setData] = useState<ContainerInfoResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchContainer = useCallback(async (id: string) => {
    if (!id) return;
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const result = await api.get<ContainerInfoResponse>(`/api/containers/${id}`);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch container');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (deepLinkId) {
      setContainerId(deepLinkId);
      fetchContainer(deepLinkId);
    }
  }, [deepLinkId, fetchContainer]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchContainer(containerId);
  };

  const sgChartData = useMemo(() => {
    if (!data || !data.sg_measurements.length || !data.fermentation) return [];
    const startDate = data.fermentation.start_date;
    const initialSg = data.sg_measurements[0]?.specific_gravity ?? null;

    return data.sg_measurements
      .filter((m) => m.specific_gravity != null)
      .map((m) => {
        const days = daysBetween(startDate, m.measurement_date);
        const sg = m.specific_gravity!;
        const abv = initialSg != null ? (initialSg - sg) * 131.25 : null;
        return { days, sg, abv: abv != null ? Math.round(abv * 100) / 100 : null };
      })
      .sort((a, b) => a.days - b.days);
  }, [data]);

  const ingredientsWithDays = useMemo<
    (IngredientAdditionOut & { daysFromStart: number | null })[]
  >(() => {
    if (!data || !data.fermentation) return [];
    const startDate = data.fermentation.start_date;
    return data.ingredients.map((ing) => ({
      ...ing,
      daysFromStart: ing.date_added ? daysBetween(startDate, ing.date_added) : null,
    }));
  }, [data]);

  return (
    <div className="mx-auto w-full max-w-4xl space-y-8 px-4 py-8">
      <h1 className="text-3xl font-bold">Container Information</h1>

      {/* Lookup form */}
      <Card>
        <CardContent className="pt-6">
          <form onSubmit={handleSubmit} className="flex items-end gap-4">
            <div className="flex flex-col gap-2">
              <Label htmlFor="container-id">Container ID</Label>
              <Input
                id="container-id"
                type="number"
                min={1}
                placeholder="Enter container ID"
                value={containerId}
                onChange={(e) => setContainerId(e.target.value)}
                className="w-48"
              />
            </div>
            <Button type="submit" disabled={!containerId || loading}>
              {loading ? 'Loading...' : 'Look Up'}
            </Button>
          </form>
        </CardContent>
      </Card>

      {error && (
        <Card>
          <CardContent className="pt-6">
            <p className="text-destructive">{error}</p>
          </CardContent>
        </Card>
      )}

      {data && (
        <>
          {/* Container Details */}
          <Card>
            <CardHeader>
              <CardTitle>Container #{data.container.id}</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="grid grid-cols-2 gap-x-8 gap-y-3 sm:grid-cols-3">
                <div>
                  <dt className="text-sm text-muted-foreground">Type</dt>
                  <dd className="font-medium capitalize">{data.container.container_type}</dd>
                </div>
                {data.container.volume_liters != null && (
                  <div>
                    <dt className="text-sm text-muted-foreground">Volume</dt>
                    <dd className="font-medium">{data.container.volume_liters} L</dd>
                  </div>
                )}
                {data.container.material && (
                  <div>
                    <dt className="text-sm text-muted-foreground">Material</dt>
                    <dd className="font-medium capitalize">{data.container.material}</dd>
                  </div>
                )}
                {data.container.empty_mass != null && (
                  <div>
                    <dt className="text-sm text-muted-foreground">Empty Mass</dt>
                    <dd className="font-medium">{data.container.empty_mass} g</dd>
                  </div>
                )}
                {data.container.date_added && (
                  <div>
                    <dt className="text-sm text-muted-foreground">Date Added</dt>
                    <dd className="font-medium">{data.container.date_added}</dd>
                  </div>
                )}
              </dl>
            </CardContent>
          </Card>

          {/* Fermentation Info */}
          {data.fermentation && (
            <Card>
              <CardHeader>
                <CardTitle>Fermentation #{data.fermentation.id}</CardTitle>
              </CardHeader>
              <CardContent>
                <dl className="grid grid-cols-2 gap-x-8 gap-y-3 sm:grid-cols-3">
                  <div>
                    <dt className="text-sm text-muted-foreground">Start Date</dt>
                    <dd className="font-medium">{data.fermentation.start_date}</dd>
                  </div>
                  {data.fermentation.end_date && (
                    <div>
                      <dt className="text-sm text-muted-foreground">End Date</dt>
                      <dd className="font-medium">{data.fermentation.end_date}</dd>
                    </div>
                  )}
                  {data.abv != null && (
                    <div>
                      <dt className="text-sm text-muted-foreground">ABV</dt>
                      <dd className="font-medium">{data.abv.toFixed(2)}%</dd>
                    </div>
                  )}
                  {data.residual_sugar != null && (
                    <div>
                      <dt className="text-sm text-muted-foreground">Residual Sugar</dt>
                      <dd className="font-medium">{data.residual_sugar.toFixed(1)} g/L</dd>
                    </div>
                  )}
                </dl>
              </CardContent>
            </Card>
          )}

          {/* SG Chart */}
          {sgChartData.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Specific Gravity &amp; ABV over Time</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-[400px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={sgChartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(245,240,232,0.1)" />
                      <XAxis
                        dataKey="days"
                        label={{
                          value: 'Days from Start',
                          position: 'insideBottom',
                          offset: -5,
                          fill: theme.text,
                        }}
                        tick={{ fill: theme.text }}
                      />
                      <YAxis
                        yAxisId="sg"
                        domain={['auto', 'auto']}
                        label={{
                          value: 'Specific Gravity',
                          angle: -90,
                          position: 'insideLeft',
                          fill: '#6B9BD2',
                        }}
                        tick={{ fill: '#6B9BD2' }}
                      />
                      <YAxis
                        yAxisId="abv"
                        orientation="right"
                        domain={[0, 'auto']}
                        label={{
                          value: 'ABV %',
                          angle: 90,
                          position: 'insideRight',
                          fill: theme.primary,
                        }}
                        tick={{ fill: theme.primary }}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: theme.surface,
                          border: `1px solid ${theme.primary}`,
                          color: theme.text,
                          borderRadius: 8,
                        }}
                      />
                      <Line
                        yAxisId="sg"
                        type="monotone"
                        dataKey="sg"
                        stroke="#6B9BD2"
                        strokeWidth={2}
                        name="Specific Gravity"
                        dot={{ fill: '#6B9BD2', r: 4 }}
                      />
                      <Line
                        yAxisId="abv"
                        type="monotone"
                        dataKey="abv"
                        stroke={theme.primary}
                        strokeWidth={2}
                        name="ABV %"
                        dot={{ fill: theme.primary, r: 4 }}
                      />
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Ingredients Table */}
          {data.ingredients.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Ingredients</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Ingredient</TableHead>
                      <TableHead>Amount</TableHead>
                      <TableHead>Unit</TableHead>
                      <TableHead>Days from Start</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {ingredientsWithDays.map((ing, i) => (
                      <TableRow key={ing.id ?? i}>
                        <TableCell>{ing.name}</TableCell>
                        <TableCell>{ing.amount ?? '-'}</TableCell>
                        <TableCell>{ing.unit ?? '-'}</TableCell>
                        <TableCell>{ing.daysFromStart ?? '-'}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}

          {/* Reviews Table */}
          {data.reviews.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Reviews</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date</TableHead>
                      <TableHead>Overall</TableHead>
                      <TableHead>Boldness</TableHead>
                      <TableHead>Tannicity</TableHead>
                      <TableHead>Sweetness</TableHead>
                      <TableHead>Acidity</TableHead>
                      <TableHead>Complexity</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data.reviews.map((review) => (
                      <TableRow key={review.id}>
                        <TableCell>{review.review_date}</TableCell>
                        <TableCell>{review.overall_rating}</TableCell>
                        <TableCell>{review.boldness}</TableCell>
                        <TableCell>{review.tannicity}</TableCell>
                        <TableCell>{review.sweetness}</TableCell>
                        <TableCell>{review.acidity}</TableCell>
                        <TableCell>{review.complexity}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
