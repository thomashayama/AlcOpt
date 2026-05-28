'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { IngredientOut } from '@/lib/types';
import { Message } from '@/components/Message';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Card, CardContent, CardHeader, CardTitle,
} from '@/components/ui/card';
import {
  ActiveFermentationSelect,
  UnitSelect,
  type ContainerIdValue,
} from './brewFormHelpers';

interface AbvResult {
  max_abv?: number;
  sugar_content_g_per_l?: number;
  volume_l?: number;
  container_volume_l?: number | null;
}

interface CalculatorIngredient {
  ingredient_id: number;
  name: string;
  amount: number;
  unit: string;
}

export function CalculatorTab() {
  const [containerId, setContainerId] = useState<ContainerIdValue>('');
  const [ingredients, setIngredients] = useState<IngredientOut[]>([]);
  const [selected, setSelected] = useState<CalculatorIngredient[]>([]);
  const [result, setResult] = useState<AbvResult | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<{
    type: 'success' | 'error';
    text: string;
  } | null>(null);

  useEffect(() => {
    const fetchIngredients = async () => {
      try {
        const data = await api.get<IngredientOut[]>('/api/brew/ingredients');
        setIngredients(data);
      } catch (err) {
        setMessage({ type: 'error', text: err instanceof Error ? err.message : 'Failed to load ingredients' });
      }
    };
    fetchIngredients();
  }, []);

  const toggleIngredient = (ing: IngredientOut) => {
    setSelected((prev) => {
      const exists = prev.find((s) => s.ingredient_id === ing.id);
      if (exists) return prev.filter((s) => s.ingredient_id !== ing.id);
      return [...prev, { ingredient_id: ing.id, name: ing.name, amount: 0, unit: 'g' }];
    });
  };

  const updateSelected = (id: number, field: 'amount' | 'unit', value: number | string) => {
    setSelected((prev) =>
      prev.map((s) => (s.ingredient_id === id ? { ...s, [field]: value } : s)),
    );
  };

  const handleCalculate = async () => {
    setSubmitting(true);
    setMessage(null);
    setResult(null);
    try {
      const data = await api.post<AbvResult>('/api/brew/calculate-abv', {
        container_id: Number(containerId),
        ingredients: selected.map((s) => ({
          ingredient_id: s.ingredient_id,
          amount: s.amount,
          unit: s.unit,
        })),
      });
      setResult(data);
    } catch (err) {
      setMessage({
        type: 'error',
        text: err instanceof Error ? err.message : 'Calculation failed',
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader><CardTitle>ABV Calculator</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-4">
            <ActiveFermentationSelect
              id="calc_active_fermentation"
              value={containerId}
              onChange={setContainerId}
            />
            <div className="space-y-2">
              <Label htmlFor="calc_container">Container ID</Label>
              <Input
                id="calc_container"
                type="number"
                min={1}
                value={containerId}
                onChange={(e) => setContainerId(e.target.value === '' ? '' : Number(e.target.value))}
              />
            </div>

            <div className="space-y-2">
              <Label>Select Ingredients</Label>
              <div className="space-y-2 rounded-lg border border-input p-3">
                {ingredients.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No ingredients available.</p>
                ) : (
                  ingredients.map((ing) => {
                    const isSelected = selected.some((s) => s.ingredient_id === ing.id);
                    return (
                      <div key={ing.id} className="space-y-2">
                        <label className="flex items-center gap-2 text-sm cursor-pointer">
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => toggleIngredient(ing)}
                            className="accent-primary"
                          />
                          {ing.name}
                          {ing.ingredient_type ? ` (${ing.ingredient_type})` : ''}
                        </label>
                        {isSelected && (
                          <div className="ml-6 flex gap-2">
                            <Input
                              type="number"
                              step={0.01}
                              placeholder="Amount"
                              value={selected.find((s) => s.ingredient_id === ing.id)?.amount ?? 0}
                              onChange={(e) => updateSelected(ing.id, 'amount', Number(e.target.value))}
                              className="w-28"
                            />
                            <UnitSelect
                              id={`calc_unit_${ing.id}`}
                              label={`Unit for ${ing.name}`}
                              labelClassName="sr-only"
                              value={selected.find((s) => s.ingredient_id === ing.id)?.unit ?? 'g'}
                              onChange={(value) => updateSelected(ing.id, 'unit', value)}
                              className="w-24"
                            />
                          </div>
                        )}
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            <Message message={message} />

            <Button onClick={handleCalculate} disabled={submitting || selected.length === 0 || containerId === ''}>
              {submitting ? 'Calculating...' : 'Calculate ABV'}
            </Button>

            {result && (
              <div className="rounded-lg border border-input bg-muted/50 p-4 space-y-2">
                <h3 className="font-medium">Results</h3>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">Max ABV</p>
                    <p className="text-lg font-semibold">
                      {result.max_abv != null ? `${result.max_abv.toFixed(2)}%` : '-'}
                    </p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Sugar Concentration</p>
                    <p className="text-lg font-semibold">
                      {result.sugar_content_g_per_l != null ? `${result.sugar_content_g_per_l.toFixed(1)} g/L` : '-'}
                    </p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Volume</p>
                    <p className="text-lg font-semibold">
                      {result.volume_l != null ? `${result.volume_l.toFixed(2)} L` : '-'}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
