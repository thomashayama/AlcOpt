'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { AdditionOut, IngredientOut } from '@/lib/types';
import { Message } from '@/components/Message';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Card, CardContent, CardHeader, CardTitle,
} from '@/components/ui/card';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import {
  ActiveFermentationSelect,
  UnitSelect,
  type ContainerIdValue,
} from './brewFormHelpers';

interface IngredientAdditionResponse {
  id: number;
  fermentation_id?: number | null;
  message: string;
}

function formatAmount(value: number) {
  return Number.isInteger(value)
    ? value.toFixed(0)
    : value.toFixed(2).replace(/0+$/, '').replace(/\.$/, '');
}

export function IngredientsTab() {
  const [ingredients, setIngredients] = useState<IngredientOut[]>([]);
  const [selectedIngredient, setSelectedIngredient] = useState<string>('new');

  const [newName, setNewName] = useState('');
  const [sugarContent, setSugarContent] = useState<number | ''>('');
  const [ingredientType, setIngredientType] = useState('Liquid');
  const [density, setDensity] = useState<number | ''>('');
  const [price, setPrice] = useState<number | ''>('');
  const [notes, setNotes] = useState('');
  const [creatingIngredient, setCreatingIngredient] = useState(false);
  const [createMessage, setCreateMessage] = useState<{
    type: 'success' | 'error';
    text: string;
  } | null>(null);

  const [addContainerId, setAddContainerId] = useState<ContainerIdValue>('');
  const [addIngredientName, setAddIngredientName] = useState('');
  const [addDate, setAddDate] = useState(new Date().toISOString().slice(0, 10));
  const [startingAmount, setStartingAmount] = useState<number | ''>('');
  const [endingAmount, setEndingAmount] = useState<number | ''>('');
  const [addUnit, setAddUnit] = useState('g');
  const [addingAddition, setAddingAddition] = useState(false);
  const [addMessage, setAddMessage] = useState<{
    type: 'success' | 'error';
    text: string;
  } | null>(null);

  const [additions, setAdditions] = useState<AdditionOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastAddition, setLastAddition] = useState<IngredientAdditionResponse | null>(
    null,
  );
  const [undoingAddition, setUndoingAddition] = useState(false);

  const fetchIngredients = async () => {
    try {
      const data = await api.get<IngredientOut[]>('/api/brew/ingredients');
      setIngredients(data);
    } catch (err) {
      setCreateMessage({ type: 'error', text: err instanceof Error ? err.message : 'Failed to load ingredients' });
    }
  };

  const fetchAdditions = async () => {
    try {
      setLoading(true);
      const data = await api.get<AdditionOut[]>('/api/brew/additions');
      setAdditions(data);
    } catch (err) {
      setAddMessage({ type: 'error', text: err instanceof Error ? err.message : 'Failed to load additions' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIngredients();
    fetchAdditions();
  }, []);

  const handleCreateIngredient = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreatingIngredient(true);
    setCreateMessage(null);
    try {
      const ingredient = await api.post<IngredientOut>('/api/brew/ingredients', {
        name: newName,
        sugar_content: sugarContent === '' ? 0 : sugarContent,
        ingredient_type: ingredientType,
        density: density === '' ? 1 : density,
        price: price === '' ? 0 : price,
        notes,
      });
      setIngredients((prev) => [
        ...prev.filter((existing) => existing.id !== ingredient.id),
        ingredient,
      ].sort((a, b) => a.name.localeCompare(b.name)));
      setSelectedIngredient(ingredient.name);
      setAddIngredientName(ingredient.name);
      setCreateMessage({
        type: 'success',
        text: `Ingredient ${ingredient.id} created: ${ingredient.name}. It is selected below.`,
      });
      setNewName('');
      setSugarContent('');
      setDensity('');
      setPrice('');
      setNotes('');
    } catch (err) {
      setCreateMessage({
        type: 'error',
        text: err instanceof Error ? err.message : 'Failed to create ingredient',
      });
    } finally {
      setCreatingIngredient(false);
    }
  };

  const handleAddAddition = async (e: React.FormEvent) => {
    e.preventDefault();
    setAddingAddition(true);
    setAddMessage(null);
    try {
      const startValue = startingAmount === '' ? 0 : startingAmount;
      const endValue = endingAmount === '' ? 0 : endingAmount;
      const amount = endValue - startValue;
      const result = await api.post<IngredientAdditionResponse>('/api/brew/additions', {
        container_id: Number(addContainerId),
        ingredient_name: addIngredientName,
        date: addDate,
        starting_amount: startValue,
        ending_amount: endValue,
        unit: addUnit,
      });
      setLastAddition(result);
      setAddMessage({
        type: 'success',
        text: `Addition ${result.id} recorded for container ${Number(addContainerId)}: ${addIngredientName} ${formatAmount(amount)} ${addUnit} (${result.fermentation_id == null ? 'no active fermentation' : `fermentation ${result.fermentation_id}`}).`,
      });
      fetchAdditions();
    } catch (err) {
      setAddMessage({
        type: 'error',
        text: err instanceof Error ? err.message : 'Failed to add addition',
      });
    } finally {
      setAddingAddition(false);
    }
  };

  const handleUndoAddition = async () => {
    if (!lastAddition) return;
    setUndoingAddition(true);
    setAddMessage(null);
    try {
      const result = await api.post<{ message: string }>(
        `/api/brew/additions/${lastAddition.id}/undo`,
      );
      setLastAddition(null);
      setAddMessage({ type: 'success', text: result.message });
      fetchAdditions();
    } catch (err) {
      setAddMessage({
        type: 'error',
        text: err instanceof Error ? err.message : 'Failed to undo addition',
      });
    } finally {
      setUndoingAddition(false);
    }
  };

  const calculatedAdditionAmount =
    startingAmount !== '' && endingAmount !== ''
      ? endingAmount - startingAmount
      : null;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader><CardTitle>Select or Create Ingredient</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="ingredient_select">Ingredient</Label>
              <select
                id="ingredient_select"
                className="flex h-8 w-full rounded-lg border border-input bg-transparent px-2.5 py-1 text-base transition-colors md:text-sm focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
                value={selectedIngredient}
                onChange={(e) => {
                  setSelectedIngredient(e.target.value);
                  if (e.target.value !== 'new') {
                    setAddIngredientName(e.target.value);
                  }
                }}
              >
                <option value="new">New Ingredient</option>
                {ingredients.map((ing) => (
                  <option key={ing.id} value={ing.name}>{ing.name}</option>
                ))}
              </select>
            </div>

            {selectedIngredient === 'new' && (
              <form onSubmit={handleCreateIngredient} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="ing_name">Name</Label>
                    <Input id="ing_name" type="text" value={newName} onChange={(e) => setNewName(e.target.value)} required />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="ing_sugar">Sugar Content</Label>
                    <Input id="ing_sugar" type="number" step={0.01} value={sugarContent} onChange={(e) => setSugarContent(e.target.value === '' ? '' : Number(e.target.value))} />
                  </div>
                </div>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                  <div className="space-y-2">
                    <Label htmlFor="ing_type">Type</Label>
                    <select
                      id="ing_type"
                      className="flex h-8 w-full rounded-lg border border-input bg-transparent px-2.5 py-1 text-base transition-colors md:text-sm focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
                      value={ingredientType}
                      onChange={(e) => setIngredientType(e.target.value)}
                    >
                      <option value="Liquid">Liquid</option>
                      <option value="Solute">Solute</option>
                      <option value="Solid">Solid</option>
                    </select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="ing_density">Density</Label>
                    <Input id="ing_density" type="number" step={0.001} value={density} onChange={(e) => setDensity(e.target.value === '' ? '' : Number(e.target.value))} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="ing_price">Price</Label>
                    <Input id="ing_price" type="number" step={0.01} value={price} onChange={(e) => setPrice(e.target.value === '' ? '' : Number(e.target.value))} />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="ing_notes">Notes</Label>
                  <Input id="ing_notes" type="text" value={notes} onChange={(e) => setNotes(e.target.value)} />
                </div>
                <Button type="submit" disabled={creatingIngredient}>
                  {creatingIngredient ? 'Creating...' : 'Create Ingredient'}
                </Button>
              </form>
            )}
            <Message message={createMessage} />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Add Ingredient to Container</CardTitle></CardHeader>
        <CardContent>
          <form onSubmit={handleAddAddition} className="space-y-4">
            <ActiveFermentationSelect
              id="add_active_fermentation"
              value={addContainerId}
              onChange={setAddContainerId}
            />
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div className="space-y-2">
                <Label htmlFor="add_container">Container ID</Label>
                <Input
                  id="add_container"
                  type="number"
                  min={1}
                  value={addContainerId}
                  onChange={(e) => setAddContainerId(e.target.value === '' ? '' : Number(e.target.value))}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="add_ingredient">Ingredient Name</Label>
                <Input id="add_ingredient" type="text" value={addIngredientName} onChange={(e) => setAddIngredientName(e.target.value)} required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="add_date">Date</Label>
                <Input id="add_date" type="date" value={addDate} onChange={(e) => setAddDate(e.target.value)} required />
              </div>
            </div>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div className="space-y-2">
                <Label htmlFor="add_start">Starting Amount</Label>
                <Input id="add_start" type="number" step={0.01} value={startingAmount} onChange={(e) => setStartingAmount(e.target.value === '' ? '' : Number(e.target.value))} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="add_end">Ending Amount</Label>
                <Input id="add_end" type="number" step={0.01} value={endingAmount} onChange={(e) => setEndingAmount(e.target.value === '' ? '' : Number(e.target.value))} />
              </div>
              <UnitSelect
                id="add_unit"
                label="Unit"
                value={addUnit}
                onChange={setAddUnit}
              />
            </div>
            {calculatedAdditionAmount !== null && (
              <p className="text-sm text-muted-foreground">
                {`${formatAmount(endingAmount as number)} - ${formatAmount(startingAmount as number)} = ${formatAmount(calculatedAdditionAmount)} ${addUnit} amount change`}
              </p>
            )}
            <Message message={addMessage} />
            <div className="flex flex-wrap gap-3">
              <Button type="submit" disabled={addingAddition || addContainerId === ''}>
                {addingAddition ? 'Adding...' : 'Add to Container'}
              </Button>
              {lastAddition && (
                <Button
                  type="button"
                  variant="destructive"
                  onClick={handleUndoAddition}
                  disabled={undoingAddition}
                >
                  {undoingAddition ? 'Undoing...' : 'Undo Last Addition'}
                </Button>
              )}
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Additions</CardTitle></CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-sm text-muted-foreground">Loading...</p>
          ) : additions.length === 0 ? (
            <p className="text-sm text-muted-foreground">No additions found.</p>
          ) : (
            <Table stack>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Container</TableHead>
                  <TableHead>Ingredient</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Amount</TableHead>
                  <TableHead>Unit</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {additions.map((a) => (
                  <TableRow key={a.id}>
                    <TableCell data-label="ID">{a.id}</TableCell>
                    <TableCell data-label="Container">{a.container_id}</TableCell>
                    <TableCell
                      data-label="Ingredient"
                      className="max-sm:order-first max-sm:col-span-full max-sm:font-medium"
                    >
                      {a.ingredient_name ?? a.ingredient_id}
                    </TableCell>
                    <TableCell data-label="Date">{a.added_at?.slice(0, 10) ?? '-'}</TableCell>
                    <TableCell data-label="Amount">{a.amount ?? '-'}</TableCell>
                    <TableCell data-label="Unit">{a.unit ?? '-'}</TableCell>
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
