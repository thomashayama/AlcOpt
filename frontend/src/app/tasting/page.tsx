'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/components/AuthProvider';
import { api } from '@/lib/api';
import type { ReviewOut } from '@/lib/types';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';

const RATING_FIELDS = [
  { key: 'overall_rating', label: 'Overall Rating', low: '1', high: '5' },
  { key: 'boldness', label: 'Boldness', low: 'Light', high: 'Bold' },
  { key: 'tannicity', label: 'Tannicity', low: 'Smooth', high: 'Tannic' },
  { key: 'sweetness', label: 'Sweetness', low: 'Dry', high: 'Sweet' },
  { key: 'acidity', label: 'Acidity', low: 'Soft', high: 'Acidic' },
  { key: 'complexity', label: 'Complexity', low: 'Simple', high: 'Complex' },
] as const;

type RatingKey = (typeof RATING_FIELDS)[number]['key'];

export default function TastingPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  const [containerId, setContainerId] = useState<number>(1);
  const [tastingDate, setTastingDate] = useState(
    new Date().toISOString().slice(0, 10),
  );
  const [ratings, setRatings] = useState<Record<RatingKey, number>>({
    overall_rating: 3.0,
    boldness: 3.0,
    tannicity: 3.0,
    sweetness: 3.0,
    acidity: 3.0,
    complexity: 3.0,
  });
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<{
    type: 'success' | 'error';
    text: string;
  } | null>(null);

  const [reviews, setReviews] = useState<ReviewOut[]>([]);
  const [reviewsLoading, setReviewsLoading] = useState(true);

  useEffect(() => {
    if (!loading && !user) {
      router.push('/');
    }
  }, [loading, user, router]);

  const fetchReviews = async () => {
    try {
      setReviewsLoading(true);
      const data = await api.get<ReviewOut[]>('/api/reviews/mine');
      setReviews(data);
    } catch {
      // silently fail
    } finally {
      setReviewsLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      fetchReviews();
    }
  }, [user]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setMessage(null);
    try {
      await api.post('/api/reviews', {
        container_id: containerId,
        tasting_date: tastingDate,
        ...ratings,
      });
      setMessage({ type: 'success', text: 'Review submitted successfully!' });
      fetchReviews();
    } catch (err) {
      setMessage({
        type: 'error',
        text: err instanceof Error ? err.message : 'Failed to submit review',
      });
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="mx-auto w-full max-w-3xl space-y-8 px-4 py-8">
      <Card>
        <CardHeader>
          <CardTitle>Tasting Form</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="container_id">Container ID</Label>
                <Input
                  id="container_id"
                  type="number"
                  min={1}
                  value={containerId}
                  onChange={(e) => setContainerId(Number(e.target.value))}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="tasting_date">Tasting Date</Label>
                <Input
                  id="tasting_date"
                  type="date"
                  value={tastingDate}
                  onChange={(e) => setTastingDate(e.target.value)}
                  required
                />
              </div>
            </div>

            {RATING_FIELDS.map(({ key, label, low, high }) => (
              <div key={key} className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>{label}</Label>
                  <span className="text-sm font-medium tabular-nums">
                    {ratings[key].toFixed(1)}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="w-16 text-xs text-muted-foreground">
                    {low}
                  </span>
                  <Slider
                    min={1}
                    max={5}
                    step={0.1}
                    value={[ratings[key]]}
                    onValueChange={(val) => {
                      const v = typeof val === 'number' ? val : val[0];
                      setRatings((prev) => ({ ...prev, [key]: v }));
                    }}
                  />
                  <span className="w-16 text-right text-xs text-muted-foreground">
                    {high}
                  </span>
                </div>
              </div>
            ))}

            {message && (
              <p
                className={
                  message.type === 'success'
                    ? 'text-sm text-green-500'
                    : 'text-sm text-destructive'
                }
              >
                {message.text}
              </p>
            )}

            <Button type="submit" disabled={submitting}>
              {submitting ? 'Submitting...' : 'Submit Review'}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Your Review History</CardTitle>
        </CardHeader>
        <CardContent>
          {reviewsLoading ? (
            <p className="text-sm text-muted-foreground">Loading reviews...</p>
          ) : reviews.length === 0 ? (
            <p className="text-sm text-muted-foreground">No reviews yet.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Container</TableHead>
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
                {reviews.map((r) => (
                  <TableRow key={r.id}>
                    <TableCell>{r.container_id}</TableCell>
                    <TableCell>{r.review_date}</TableCell>
                    <TableCell>{r.overall_rating.toFixed(1)}</TableCell>
                    <TableCell>{r.boldness.toFixed(1)}</TableCell>
                    <TableCell>{r.tannicity.toFixed(1)}</TableCell>
                    <TableCell>{r.sweetness.toFixed(1)}</TableCell>
                    <TableCell>{r.acidity.toFixed(1)}</TableCell>
                    <TableCell>{r.complexity.toFixed(1)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
