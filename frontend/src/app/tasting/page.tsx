'use client';

import { Suspense, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
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

const RUBRIC = [
  {
    attribute: 'Overall Rating',
    description: 'Your overall enjoyment and quality assessment.',
    levels: [
      {
        score: '1',
        label: 'Poor',
        detail: 'Significant flaws, unpleasant to drink.',
        wines: 'Corked or oxidized wine, cooking wine',
        foods: 'Burnt toast, spoiled fruit',
      },
      {
        score: '2',
        label: 'Below average',
        detail: 'Drinkable but unremarkable, some off-notes or imbalance.',
        wines: 'Generic box wine, bulk jug wine',
        foods: 'Stale crackers, watered-down juice',
      },
      {
        score: '3',
        label: 'Average',
        detail: 'Pleasant, no major flaws. Would drink again casually.',
        wines: 'Decent house wine, mid-range supermarket bottle',
        foods: 'A solid home-cooked meal, fresh bread with butter',
      },
      {
        score: '4',
        label: 'Very good',
        detail: 'Notably enjoyable, well-balanced. Would seek out again.',
        wines: 'Village-level Burgundy, quality Chianti Classico Riserva',
        foods: 'A well-prepared restaurant dish, artisan cheese',
      },
      {
        score: '5',
        label: 'Exceptional',
        detail: 'Outstanding quality, memorable and thought-provoking.',
        wines: 'Grand Cru Burgundy, top Barolo, first-growth Bordeaux',
        foods: 'A once-in-a-lifetime tasting-menu experience',
      },
    ],
  },
  {
    attribute: 'Boldness',
    description:
      'How heavy or full the wine feels in your mouth — its weight and intensity.',
    levels: [
      {
        score: '1',
        label: 'Very light',
        detail: 'Barely-there body, almost water-like.',
        wines: 'Vinho Verde, light Pinot Grigio, Muscadet',
        foods: 'Skim milk, clear broth, cucumber water',
      },
      {
        score: '2',
        label: 'Light',
        detail: 'Delicate, refreshing, easy-drinking.',
        wines: 'Riesling, Beaujolais Nouveau, Albariño',
        foods: 'Green tea, sparkling water with lemon, melon',
      },
      {
        score: '3',
        label: 'Medium',
        detail: 'Balanced weight, neither thin nor heavy.',
        wines: 'Merlot, Chianti, unoaked Chardonnay, Côtes du Rhône',
        foods: 'Whole milk, apple juice, a bowl of risotto',
      },
      {
        score: '4',
        label: 'Full',
        detail: 'Rich, weighty, coats the palate.',
        wines: 'Cabernet Sauvignon, Malbec, oaked Chardonnay',
        foods: 'Heavy cream, dark chocolate, grilled steak',
      },
      {
        score: '5',
        label: 'Very full / intense',
        detail: 'Massive body, viscous, almost chewy.',
        wines: 'Amarone, Barossa Shiraz, vintage Port',
        foods: 'Molasses, espresso, melted butter, braised short ribs',
      },
    ],
  },
  {
    attribute: 'Tannicity',
    description:
      'The drying, astringent, slightly bitter sensation on your tongue, gums, and inner cheeks. Caused by polyphenols from grape skins, seeds, and oak.',
    levels: [
      {
        score: '1',
        label: 'None / silky',
        detail: 'No drying sensation at all. Smooth and slippery.',
        wines: 'White wines (Sauvignon Blanc, Moscato), rosé',
        foods: 'Yogurt, custard, ripe banana',
      },
      {
        score: '2',
        label: 'Soft',
        detail: 'Barely perceptible grip, gentle texture.',
        wines: 'Pinot Noir, Gamay (Beaujolais), light Grenache',
        foods: 'Lightly brewed green tea, peeled almonds',
      },
      {
        score: '3',
        label: 'Moderate',
        detail: 'Noticeable drying but not aggressive. Well-integrated.',
        wines: 'Sangiovese (Chianti), Tempranillo (Rioja Crianza), Zinfandel',
        foods: 'Black tea steeped 3 min, milk chocolate, cranberries',
      },
      {
        score: '4',
        label: 'Firm',
        detail: 'Strong grip, pronounced drying. Wants food to soften it.',
        wines: 'Cabernet Sauvignon, Nebbiolo (Barbaresco), Mourvèdre',
        foods: 'Over-steeped black tea, walnut skins, dark chocolate (80%+)',
      },
      {
        score: '5',
        label: 'Very astringent',
        detail:
          'Intensely drying, mouth-puckering. Often in young, unevolved wines.',
        wines: 'Young Barolo, Tannat, Petite Sirah, young Bordeaux',
        foods: 'Unripe persimmon, raw pomegranate pith, grape seeds',
      },
    ],
  },
  {
    attribute: 'Sweetness',
    description:
      'Perception of residual sugar — how sweet vs. dry the wine tastes.',
    levels: [
      {
        score: '1',
        label: 'Bone dry',
        detail: 'Zero sweetness. All sugar has been fermented out.',
        wines: 'Muscadet, Chablis, Brut Nature Champagne, dry Fino Sherry',
        foods: 'Unsweetened espresso, raw lemon juice, dry sourdough',
      },
      {
        score: '2',
        label: 'Dry',
        detail: 'Little to no perceptible sweetness. Standard for most reds.',
        wines: 'Most red table wines, Sauvignon Blanc, Grüner Veltliner',
        foods: 'Unsweetened iced tea, grapefruit, toasted nuts',
      },
      {
        score: '3',
        label: 'Off-dry',
        detail: 'Hint of sweetness that rounds out the palate.',
        wines: 'Riesling Kabinett, Gewürztraminer, demi-sec Vouvray',
        foods: 'Green apple, carrot juice, honey-drizzled goat cheese',
      },
      {
        score: '4',
        label: 'Sweet',
        detail: 'Clearly sweet, dessert-leaning.',
        wines: 'Sauternes, late-harvest Riesling, Banyuls',
        foods: 'Honey, ripe mango, caramel, crème brûlée',
      },
      {
        score: '5',
        label: 'Very sweet',
        detail: 'Lusciously sweet, syrupy richness.',
        wines: 'Tokaji Aszú (5+ puttonyos), Ice Wine, Pedro Ximénez Sherry',
        foods: 'Maple syrup, dried figs, candied fruit, toffee',
      },
    ],
  },
  {
    attribute: 'Acidity',
    description:
      'Tartness and crispness — the mouth-watering, lip-smacking quality that gives wine freshness and structure.',
    levels: [
      {
        score: '1',
        label: 'Very soft / flat',
        detail: 'Almost no acidity. Can feel flabby or dull.',
        wines: 'Over-ripe warm-climate reds, some oaked Chardonnays',
        foods: 'Ripe banana, heavy cream, avocado',
      },
      {
        score: '2',
        label: 'Low',
        detail: 'Gentle, rounded. Smooth but not sharp.',
        wines: 'Viognier, warm-climate Merlot, Amarone',
        foods: 'Cantaloupe, roasted sweet potato, brie',
      },
      {
        score: '3',
        label: 'Medium',
        detail: 'Balanced tartness — refreshing without being biting.',
        wines: 'Pinot Noir, Chardonnay (Burgundy), Grenache',
        foods: 'Green apple, plain yogurt, fresh tomato',
      },
      {
        score: '4',
        label: 'High',
        detail: 'Bright, zesty, makes your mouth water noticeably.',
        wines: 'Sauvignon Blanc, Barbera, Assyrtiko, Sancerre',
        foods: 'Grapefruit, sour cherry, kombucha, goat cheese',
      },
      {
        score: '5',
        label: 'Very high / searing',
        detail: 'Razor-sharp, electric acidity. Piercing freshness.',
        wines: 'Champagne, young Riesling (Mosel), Vinho Verde, Txakoli',
        foods: 'Straight lemon juice, cranberry, pickle brine, green mango',
      },
    ],
  },
  {
    attribute: 'Complexity',
    description:
      'The number and interplay of distinct flavors, aromas, and textures — and how they evolve in the glass and on the palate over time.',
    levels: [
      {
        score: '1',
        label: 'Very simple',
        detail: 'One-note, straightforward. What you smell is what you get.',
        wines: 'Basic table wine, bulk wine, wine coolers',
        foods: 'Plain white rice, boiled potato, white bread',
      },
      {
        score: '2',
        label: 'Simple',
        detail: 'Two or three identifiable notes, pleasant but predictable.',
        wines: 'Young Beaujolais, basic Pinot Grigio, simple rosé',
        foods: 'Grilled cheese, buttered toast, a ripe pear',
      },
      {
        score: '3',
        label: 'Moderate',
        detail:
          'Several distinct layers — fruit, spice, earth — that hold your interest.',
        wines: 'Chianti Classico, Côtes du Rhône, New Zealand Sauvignon Blanc',
        foods: 'Well-seasoned stew, a mixed cheese board, pad thai',
      },
      {
        score: '4',
        label: 'Complex',
        detail:
          'Many interwoven aromas and flavors that shift and reveal new facets with each sip.',
        wines:
          'Grand Cru Burgundy, aged Rioja Gran Reserva, Châteauneuf-du-Pape',
        foods:
          'Multi-course tasting menu, mole sauce, truffle risotto, aged Comté',
      },
      {
        score: '5',
        label: 'Extremely complex',
        detail:
          'Kaleidoscopic — constantly evolving in the glass. Layers upon layers of aroma, flavor, and texture.',
        wines:
          'Top Barolo (10+ years), classified Bordeaux at peak, vintage Port (20+ years), aged Riesling Spätlese',
        foods:
          'Elaborate curry with 15+ spices, high-end omakase, aged balsamic on Parmigiano',
      },
    ],
  },
] as const;

type RatingKey = (typeof RATING_FIELDS)[number]['key'];

export default function TastingPageWrapper() {
  return (
    <Suspense fallback={<div className="p-8 text-center">Loading...</div>}>
      <TastingPage />
    </Suspense>
  );
}

function TastingPage() {
  const { user, loading } = useAuth();
  const searchParams = useSearchParams();
  const prefilledId = searchParams.get('container_id');

  const [containerId, setContainerId] = useState<number>(
    prefilledId ? parseInt(prefilledId, 10) : 1,
  );
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
  const [email, setEmail] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<{
    type: 'success' | 'error';
    text: string;
  } | null>(null);

  const [rubricOpen, setRubricOpen] = useState(false);
  const [reviews, setReviews] = useState<ReviewOut[]>([]);
  const [reviewsLoading, setReviewsLoading] = useState(true);

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
        ...(user ? {} : { email }),
      });
      setMessage({ type: 'success', text: 'Review submitted successfully!' });
      if (user) fetchReviews();
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

  return (
    <div className="mx-auto w-full max-w-3xl space-y-8 px-4 py-8">
      <Card>
        <CardHeader>
          <button
            type="button"
            onClick={() => setRubricOpen((o) => !o)}
            className="flex w-full items-center justify-between text-left"
          >
            <CardTitle>Tasting Rubric</CardTitle>
            <span className="text-muted-foreground text-sm">
              {rubricOpen ? '▲ Hide' : '▼ Show guide'}
            </span>
          </button>
          <p className="text-sm text-muted-foreground">
            Reference guide for rating each attribute — with wine &amp; food
            comparisons at every level.
          </p>
        </CardHeader>
        {rubricOpen && (
          <CardContent className="space-y-6">
            {RUBRIC.map((attr) => (
              <div key={attr.attribute}>
                <h3 className="mb-1 text-base font-semibold text-[#D4A24C]">
                  {attr.attribute}
                </h3>
                <p className="mb-3 text-sm text-muted-foreground">
                  {attr.description}
                </p>
                <div className="space-y-2">
                  {attr.levels.map((lvl) => (
                    <div
                      key={lvl.score}
                      className="rounded-md border border-border/50 bg-card/50 p-3"
                    >
                      <div className="mb-1 flex items-baseline gap-2">
                        <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-[#A4243B] text-xs font-bold text-white">
                          {lvl.score}
                        </span>
                        <span className="font-medium">{lvl.label}</span>
                      </div>
                      <p className="mb-1 text-sm">{lvl.detail}</p>
                      <div className="grid grid-cols-2 gap-x-4 text-xs text-muted-foreground">
                        <p>
                          <span className="font-medium text-[#D4A24C]">
                            Wines:{' '}
                          </span>
                          {lvl.wines}
                        </p>
                        <p>
                          <span className="font-medium text-[#D4A24C]">
                            Tastes like:{' '}
                          </span>
                          {lvl.foods}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </CardContent>
        )}
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Tasting Form</CardTitle>
          {!user && (
            <p className="text-sm text-muted-foreground">
              You&apos;re not logged in. Enter your email below to submit a review.
              Log in with Google to see your review history.
            </p>
          )}
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {!user && (
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="your@email.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
            )}
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

      {user && (
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
      )}
    </div>
  );
}
