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

  const [addContainerId, setAddContainerId] = useState(1);
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
      await api.post('/api/brew/ingredients', {
        name: newName,
        sugar_content: sugarContent === '' ? null : sugarContent,
        ingredient_type: ingredientType,
        density: density === '' ? null : density,
        price: price === '' ? null : price,
        notes: notes || null,
      });
      setCreateMessage({ type: 'success', text: 'Ingredient created successfully!' });
      setNewName('');
      setSugarContent('');
      setDensity('');
      setPrice('');
      setNotes('');
      fetchIngredients();
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
      await api.post('/api/brew/additions', {
        container_id: addContainerId,
        ingredient_name: addIngredientName,
        date: addDate,
        starting_amount: startingAmount === '' ? null : startingAmount,
        ending_amount: endingAmount === '' ? null : endingAmount,
        unit: addUnit,
      });
      setAddMessage({ type: 'success', text: 'Addition recorded!' });
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
                className="flex h-8 w-full rounded-lg border border-input bg-transparent px-2.5 py-1 text-sm transition-colors focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
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
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="ing_type">Type</Label>
                    <select
                      id="ing_type"
                      className="flex h-8 w-full rounded-lg border border-input bg-transparent px-2.5 py-1 text-sm transition-colors focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
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
                <Message message={createMessage} />
                <Button type="submit" disabled={creatingIngredient}>
                  {creatingIngredient ? 'Creating...' : 'Create Ingredient'}
                </Button>
              </form>
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Add Ingredient to Container</CardTitle></CardHeader>
        <CardContent>
          <form onSubmit={handleAddAddition} className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="add_container">Container ID</Label>
                <Input id="add_container" type="number" min={1} value={addContainerId} onChange={(e) => setAddContainerId(Number(e.target.value))} required />
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
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="add_start">Starting Amount</Label>
                <Input id="add_start" type="number" step={0.01} value={startingAmount} onChange={(e) => setStartingAmount(e.target.value === '' ? '' : Number(e.target.value))} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="add_end">Ending Amount</Label>
                <Input id="add_end" type="number" step={0.01} value={endingAmount} onChange={(e) => setEndingAmount(e.target.value === '' ? '' : Number(e.target.value))} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="add_unit">Unit</Label>
                <Input id="add_unit" type="text" value={addUnit} onChange={(e) => setAddUnit(e.target.value)} />
              </div>
            </div>
            <Message message={addMessage} />
            <Button type="submit" disabled={addingAddition}>
              {addingAddition ? 'Adding...' : 'Add to Container'}
            </Button>
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
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Container</TableHead>
                  <TableHead>Ingredient</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Start Amt</TableHead>
                  <TableHead>End Amt</TableHead>
                  <TableHead>Unit</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {additions.map((a) => (
                  <TableRow key={a.id}>
                    <TableCell>{a.id}</TableCell>
                    <TableCell>{a.container_id}</TableCell>
                    <TableCell>{a.ingredient_name ?? a.ingredient_id}</TableCell>
                    <TableCell>{a.date}</TableCell>
                    <TableCell>{a.starting_amount ?? '-'}</TableCell>
                    <TableCell>{a.ending_amount ?? '-'}</TableCell>
                    <TableCell>{a.unit ?? '-'}</TableCell>
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
