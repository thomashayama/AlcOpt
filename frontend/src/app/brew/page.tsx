'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/components/AuthProvider';
import { api } from '@/lib/api';
import type {
  ContainerLogOut,
  IngredientOut,
  SgMeasurementOut,
  MassMeasurementOut,
} from '@/lib/types';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
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

// ---------------------------------------------------------------------------
// Shared message component
// ---------------------------------------------------------------------------

function Message({
  message,
}: {
  message: { type: 'success' | 'error'; text: string } | null;
}) {
  if (!message) return null;
  return (
    <p
      className={
        message.type === 'success'
          ? 'text-sm text-green-500'
          : 'text-sm text-destructive'
      }
    >
      {message.text}
    </p>
  );
}

// ---------------------------------------------------------------------------
// Tab 1: Start
// ---------------------------------------------------------------------------

interface AdditionOut {
  id: number;
  container_id: number;
  ingredient_id: number;
  ingredient_name?: string;
  date: string;
  starting_amount?: number | null;
  ending_amount?: number | null;
  unit?: string | null;
}

function StartTab() {
  const [containerId, setContainerId] = useState(1);
  const [startDate, setStartDate] = useState(
    new Date().toISOString().slice(0, 10),
  );
  const [stage, setStage] = useState('primary');
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<{
    type: 'success' | 'error';
    text: string;
  } | null>(null);
  const [logs, setLogs] = useState<ContainerLogOut[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const data = await api.get<ContainerLogOut[]>(
        '/api/brew/fermentations',
      );
      setLogs(data);
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setMessage(null);
    try {
      await api.post('/api/brew/fermentations', {
        container_id: containerId,
        start_date: startDate,
        stage,
      });
      setMessage({
        type: 'success',
        text: 'Fermentation started successfully!',
      });
      fetchLogs();
    } catch (err) {
      setMessage({
        type: 'error',
        text:
          err instanceof Error ? err.message : 'Failed to start fermentation',
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Start Fermentation</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="s_container">Container ID</Label>
                <Input
                  id="s_container"
                  type="number"
                  min={1}
                  value={containerId}
                  onChange={(e) => setContainerId(Number(e.target.value))}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="s_date">Start Date</Label>
                <Input
                  id="s_date"
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="s_stage">Stage</Label>
                <Input
                  id="s_stage"
                  type="text"
                  value={stage}
                  onChange={(e) => setStage(e.target.value)}
                />
              </div>
            </div>
            <Message message={message} />
            <Button type="submit" disabled={submitting}>
              {submitting ? 'Starting...' : 'Start Fermentation'}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Fermentation Logs</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-sm text-muted-foreground">Loading...</p>
          ) : logs.length === 0 ? (
            <p className="text-sm text-muted-foreground">No logs found.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Container</TableHead>
                  <TableHead>Fermentation</TableHead>
                  <TableHead>Start</TableHead>
                  <TableHead>End</TableHead>
                  <TableHead>Stage</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {logs.map((l) => (
                  <TableRow key={l.id}>
                    <TableCell>{l.id}</TableCell>
                    <TableCell>{l.container_id}</TableCell>
                    <TableCell>{l.fermentation_id}</TableCell>
                    <TableCell>{l.start_date}</TableCell>
                    <TableCell>{l.end_date ?? '-'}</TableCell>
                    <TableCell>{l.stage ?? '-'}</TableCell>
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

// ---------------------------------------------------------------------------
// Tab 2: Ingredients
// ---------------------------------------------------------------------------

function IngredientsTab() {
  const [ingredients, setIngredients] = useState<IngredientOut[]>([]);
  const [selectedIngredient, setSelectedIngredient] = useState<string>('new');

  // New ingredient form
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

  // Add addition form
  const [addContainerId, setAddContainerId] = useState(1);
  const [addIngredientName, setAddIngredientName] = useState('');
  const [addDate, setAddDate] = useState(
    new Date().toISOString().slice(0, 10),
  );
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
    } catch {
      // silently fail
    }
  };

  const fetchAdditions = async () => {
    try {
      setLoading(true);
      const data = await api.get<AdditionOut[]>('/api/brew/additions');
      setAdditions(data);
    } catch {
      // silently fail
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
      setCreateMessage({
        type: 'success',
        text: 'Ingredient created successfully!',
      });
      setNewName('');
      setSugarContent('');
      setDensity('');
      setPrice('');
      setNotes('');
      fetchIngredients();
    } catch (err) {
      setCreateMessage({
        type: 'error',
        text:
          err instanceof Error ? err.message : 'Failed to create ingredient',
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
        <CardHeader>
          <CardTitle>Select or Create Ingredient</CardTitle>
        </CardHeader>
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
                  <option key={ing.id} value={ing.name}>
                    {ing.name}
                  </option>
                ))}
              </select>
            </div>

            {selectedIngredient === 'new' && (
              <form onSubmit={handleCreateIngredient} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="ing_name">Name</Label>
                    <Input
                      id="ing_name"
                      type="text"
                      value={newName}
                      onChange={(e) => setNewName(e.target.value)}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="ing_sugar">Sugar Content</Label>
                    <Input
                      id="ing_sugar"
                      type="number"
                      step={0.01}
                      value={sugarContent}
                      onChange={(e) =>
                        setSugarContent(
                          e.target.value === ''
                            ? ''
                            : Number(e.target.value),
                        )
                      }
                    />
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
                    <Input
                      id="ing_density"
                      type="number"
                      step={0.001}
                      value={density}
                      onChange={(e) =>
                        setDensity(
                          e.target.value === ''
                            ? ''
                            : Number(e.target.value),
                        )
                      }
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="ing_price">Price</Label>
                    <Input
                      id="ing_price"
                      type="number"
                      step={0.01}
                      value={price}
                      onChange={(e) =>
                        setPrice(
                          e.target.value === ''
                            ? ''
                            : Number(e.target.value),
                        )
                      }
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="ing_notes">Notes</Label>
                  <Input
                    id="ing_notes"
                    type="text"
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                  />
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
        <CardHeader>
          <CardTitle>Add Ingredient to Container</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleAddAddition} className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="add_container">Container ID</Label>
                <Input
                  id="add_container"
                  type="number"
                  min={1}
                  value={addContainerId}
                  onChange={(e) => setAddContainerId(Number(e.target.value))}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="add_ingredient">Ingredient Name</Label>
                <Input
                  id="add_ingredient"
                  type="text"
                  value={addIngredientName}
                  onChange={(e) => setAddIngredientName(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="add_date">Date</Label>
                <Input
                  id="add_date"
                  type="date"
                  value={addDate}
                  onChange={(e) => setAddDate(e.target.value)}
                  required
                />
              </div>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="add_start">Starting Amount</Label>
                <Input
                  id="add_start"
                  type="number"
                  step={0.01}
                  value={startingAmount}
                  onChange={(e) =>
                    setStartingAmount(
                      e.target.value === '' ? '' : Number(e.target.value),
                    )
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="add_end">Ending Amount</Label>
                <Input
                  id="add_end"
                  type="number"
                  step={0.01}
                  value={endingAmount}
                  onChange={(e) =>
                    setEndingAmount(
                      e.target.value === '' ? '' : Number(e.target.value),
                    )
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="add_unit">Unit</Label>
                <Input
                  id="add_unit"
                  type="text"
                  value={addUnit}
                  onChange={(e) => setAddUnit(e.target.value)}
                />
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
        <CardHeader>
          <CardTitle>Additions</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-sm text-muted-foreground">Loading...</p>
          ) : additions.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No additions found.
            </p>
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
                    <TableCell>
                      {a.ingredient_name ?? a.ingredient_id}
                    </TableCell>
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

// ---------------------------------------------------------------------------
// Tab 3: SG Measurements
// ---------------------------------------------------------------------------

function SgTab() {
  const [containerId, setContainerId] = useState(1);
  const [measurementDate, setMeasurementDate] = useState(
    new Date().toISOString().slice(0, 10),
  );
  const [sg, setSg] = useState(1.0);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<{
    type: 'success' | 'error';
    text: string;
  } | null>(null);
  const [measurements, setMeasurements] = useState<SgMeasurementOut[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchMeasurements = async () => {
    try {
      setLoading(true);
      const data = await api.get<SgMeasurementOut[]>(
        '/api/brew/sg-measurements',
      );
      setMeasurements(data);
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMeasurements();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setMessage(null);
    try {
      await api.post('/api/brew/sg-measurements', {
        container_id: containerId,
        measurement_date: measurementDate,
        specific_gravity: sg,
      });
      setMessage({
        type: 'success',
        text: 'SG measurement recorded!',
      });
      fetchMeasurements();
    } catch (err) {
      setMessage({
        type: 'error',
        text:
          err instanceof Error ? err.message : 'Failed to record measurement',
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Record SG Measurement</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="sg_container">Container ID</Label>
                <Input
                  id="sg_container"
                  type="number"
                  min={1}
                  value={containerId}
                  onChange={(e) => setContainerId(Number(e.target.value))}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="sg_date">Measurement Date</Label>
                <Input
                  id="sg_date"
                  type="date"
                  value={measurementDate}
                  onChange={(e) => setMeasurementDate(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="sg_value">Specific Gravity</Label>
                <Input
                  id="sg_value"
                  type="number"
                  step={0.001}
                  value={sg}
                  onChange={(e) => setSg(Number(e.target.value))}
                  required
                />
              </div>
            </div>
            <Message message={message} />
            <Button type="submit" disabled={submitting}>
              {submitting ? 'Recording...' : 'Record Measurement'}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>SG Measurements</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-sm text-muted-foreground">Loading...</p>
          ) : measurements.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No measurements found.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Fermentation</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>SG</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {measurements.map((m) => (
                  <TableRow key={m.id}>
                    <TableCell>{m.id}</TableCell>
                    <TableCell>{m.fermentation_id}</TableCell>
                    <TableCell>{m.measurement_date}</TableCell>
                    <TableCell>{m.specific_gravity ?? '-'}</TableCell>
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

// ---------------------------------------------------------------------------
// Tab 4: Mass Measurements
// ---------------------------------------------------------------------------

function MassTab() {
  const [containerId, setContainerId] = useState(1);
  const [measurementDate, setMeasurementDate] = useState(
    new Date().toISOString().slice(0, 10),
  );
  const [mass, setMass] = useState<number>(0);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<{
    type: 'success' | 'error';
    text: string;
  } | null>(null);
  const [measurements, setMeasurements] = useState<MassMeasurementOut[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchMeasurements = async () => {
    try {
      setLoading(true);
      const data = await api.get<MassMeasurementOut[]>(
        '/api/brew/mass-measurements',
      );
      setMeasurements(data);
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMeasurements();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setMessage(null);
    try {
      await api.post('/api/brew/mass-measurements', {
        container_id: containerId,
        measurement_date: measurementDate,
        mass,
      });
      setMessage({ type: 'success', text: 'Mass measurement recorded!' });
      fetchMeasurements();
    } catch (err) {
      setMessage({
        type: 'error',
        text:
          err instanceof Error ? err.message : 'Failed to record measurement',
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Record Mass Measurement</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="mass_container">Container ID</Label>
                <Input
                  id="mass_container"
                  type="number"
                  min={1}
                  value={containerId}
                  onChange={(e) => setContainerId(Number(e.target.value))}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="mass_date">Measurement Date</Label>
                <Input
                  id="mass_date"
                  type="date"
                  value={measurementDate}
                  onChange={(e) => setMeasurementDate(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="mass_value">Mass (g)</Label>
                <Input
                  id="mass_value"
                  type="number"
                  step={0.1}
                  value={mass}
                  onChange={(e) => setMass(Number(e.target.value))}
                  required
                />
              </div>
            </div>
            <Message message={message} />
            <Button type="submit" disabled={submitting}>
              {submitting ? 'Recording...' : 'Record Measurement'}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Mass Measurements</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-sm text-muted-foreground">Loading...</p>
          ) : measurements.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No measurements found.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Fermentation</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Mass (g)</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {measurements.map((m) => (
                  <TableRow key={m.id}>
                    <TableCell>{m.id}</TableCell>
                    <TableCell>{m.fermentation_id}</TableCell>
                    <TableCell>{m.measurement_date}</TableCell>
                    <TableCell>{m.mass}</TableCell>
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

// ---------------------------------------------------------------------------
// Tab 5: Rack
// ---------------------------------------------------------------------------

function RackTab() {
  const [fromContainerId, setFromContainerId] = useState(1);
  const [toContainerId, setToContainerId] = useState(1);
  const [rackDate, setRackDate] = useState(
    new Date().toISOString().slice(0, 10),
  );
  const [stage, setStage] = useState('secondary');
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<{
    type: 'success' | 'error';
    text: string;
  } | null>(null);
  const [logs, setLogs] = useState<ContainerLogOut[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const data = await api.get<ContainerLogOut[]>(
        '/api/brew/fermentations',
      );
      setLogs(data);
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setMessage(null);
    try {
      await api.post('/api/brew/rack', {
        from_container_id: fromContainerId,
        to_container_id: toContainerId,
        date: rackDate,
        stage,
      });
      setMessage({ type: 'success', text: 'Racking recorded!' });
      fetchLogs();
    } catch (err) {
      setMessage({
        type: 'error',
        text: err instanceof Error ? err.message : 'Failed to record racking',
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Rack</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="rack_from">From Container ID</Label>
                <Input
                  id="rack_from"
                  type="number"
                  min={1}
                  value={fromContainerId}
                  onChange={(e) => setFromContainerId(Number(e.target.value))}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="rack_to">To Container ID</Label>
                <Input
                  id="rack_to"
                  type="number"
                  min={1}
                  value={toContainerId}
                  onChange={(e) => setToContainerId(Number(e.target.value))}
                  required
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="rack_date">Date</Label>
                <Input
                  id="rack_date"
                  type="date"
                  value={rackDate}
                  onChange={(e) => setRackDate(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="rack_stage">Stage</Label>
                <Input
                  id="rack_stage"
                  type="text"
                  value={stage}
                  onChange={(e) => setStage(e.target.value)}
                />
              </div>
            </div>
            <Message message={message} />
            <Button type="submit" disabled={submitting}>
              {submitting ? 'Recording...' : 'Record Racking'}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Fermentation Logs</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-sm text-muted-foreground">Loading...</p>
          ) : logs.length === 0 ? (
            <p className="text-sm text-muted-foreground">No logs found.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Container</TableHead>
                  <TableHead>Fermentation</TableHead>
                  <TableHead>Start</TableHead>
                  <TableHead>End</TableHead>
                  <TableHead>Stage</TableHead>
                  <TableHead>Source</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {logs.map((l) => (
                  <TableRow key={l.id}>
                    <TableCell>{l.id}</TableCell>
                    <TableCell>{l.container_id}</TableCell>
                    <TableCell>{l.fermentation_id}</TableCell>
                    <TableCell>{l.start_date}</TableCell>
                    <TableCell>{l.end_date ?? '-'}</TableCell>
                    <TableCell>{l.stage ?? '-'}</TableCell>
                    <TableCell>{l.source_container_id ?? '-'}</TableCell>
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

// ---------------------------------------------------------------------------
// Tab 6: Bottle
// ---------------------------------------------------------------------------

function BottleTab() {
  const [fromContainerId, setFromContainerId] = useState(1);
  const [toContainerId, setToContainerId] = useState(1);
  const [bottleDate, setBottleDate] = useState(
    new Date().toISOString().slice(0, 10),
  );
  const [amount, setAmount] = useState<number | ''>('');
  const [unit, setUnit] = useState('mL');
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<{
    type: 'success' | 'error';
    text: string;
  } | null>(null);

  // Empty container
  const [emptyContainerId, setEmptyContainerId] = useState(1);
  const [emptying, setEmptying] = useState(false);
  const [emptyMessage, setEmptyMessage] = useState<{
    type: 'success' | 'error';
    text: string;
  } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setMessage(null);
    try {
      await api.post('/api/brew/bottle', {
        from_container_id: fromContainerId,
        to_container_id: toContainerId,
        date: bottleDate,
        amount: amount === '' ? null : amount,
        unit,
      });
      setMessage({ type: 'success', text: 'Bottling recorded!' });
    } catch (err) {
      setMessage({
        type: 'error',
        text: err instanceof Error ? err.message : 'Failed to record bottling',
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleEmpty = async () => {
    setEmptying(true);
    setEmptyMessage(null);
    try {
      await api.post(`/api/brew/empty/${emptyContainerId}`);
      setEmptyMessage({ type: 'success', text: 'Container emptied!' });
    } catch (err) {
      setEmptyMessage({
        type: 'error',
        text:
          err instanceof Error ? err.message : 'Failed to empty container',
      });
    } finally {
      setEmptying(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Bottle</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="bot_from">From Container ID (vessel)</Label>
                <Input
                  id="bot_from"
                  type="number"
                  min={1}
                  value={fromContainerId}
                  onChange={(e) => setFromContainerId(Number(e.target.value))}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="bot_to">To Container ID (bottle)</Label>
                <Input
                  id="bot_to"
                  type="number"
                  min={1}
                  value={toContainerId}
                  onChange={(e) => setToContainerId(Number(e.target.value))}
                  required
                />
              </div>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="bot_date">Date</Label>
                <Input
                  id="bot_date"
                  type="date"
                  value={bottleDate}
                  onChange={(e) => setBottleDate(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="bot_amount">Amount</Label>
                <Input
                  id="bot_amount"
                  type="number"
                  step={0.01}
                  value={amount}
                  onChange={(e) =>
                    setAmount(
                      e.target.value === '' ? '' : Number(e.target.value),
                    )
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="bot_unit">Unit</Label>
                <Input
                  id="bot_unit"
                  type="text"
                  value={unit}
                  onChange={(e) => setUnit(e.target.value)}
                />
              </div>
            </div>
            <Message message={message} />
            <Button type="submit" disabled={submitting}>
              {submitting ? 'Recording...' : 'Record Bottling'}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Empty Container</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-end gap-4">
            <div className="space-y-2">
              <Label htmlFor="empty_id">Container ID</Label>
              <Input
                id="empty_id"
                type="number"
                min={1}
                value={emptyContainerId}
                onChange={(e) => setEmptyContainerId(Number(e.target.value))}
              />
            </div>
            <Button onClick={handleEmpty} disabled={emptying} variant="destructive">
              {emptying ? 'Emptying...' : 'Empty Container'}
            </Button>
          </div>
          <Message message={emptyMessage} />
        </CardContent>
      </Card>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tab 7: Calculator
// ---------------------------------------------------------------------------

interface AbvResult {
  max_abv?: number;
  sugar_content?: number;
  volume?: number;
}

interface CalculatorIngredient {
  ingredient_id: number;
  name: string;
  amount: number;
  unit: string;
}

function CalculatorTab() {
  const [containerId, setContainerId] = useState(1);
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
      } catch {
        // silently fail
      }
    };
    fetchIngredients();
  }, []);

  const toggleIngredient = (ing: IngredientOut) => {
    setSelected((prev) => {
      const exists = prev.find((s) => s.ingredient_id === ing.id);
      if (exists) {
        return prev.filter((s) => s.ingredient_id !== ing.id);
      }
      return [
        ...prev,
        { ingredient_id: ing.id, name: ing.name, amount: 0, unit: 'g' },
      ];
    });
  };

  const updateSelected = (
    id: number,
    field: 'amount' | 'unit',
    value: number | string,
  ) => {
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
        container_id: containerId,
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
        <CardHeader>
          <CardTitle>ABV Calculator</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="calc_container">Container ID</Label>
              <Input
                id="calc_container"
                type="number"
                min={1}
                value={containerId}
                onChange={(e) => setContainerId(Number(e.target.value))}
              />
            </div>

            <div className="space-y-2">
              <Label>Select Ingredients</Label>
              <div className="space-y-2 rounded-lg border border-input p-3">
                {ingredients.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No ingredients available.
                  </p>
                ) : (
                  ingredients.map((ing) => {
                    const isSelected = selected.some(
                      (s) => s.ingredient_id === ing.id,
                    );
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
                          {ing.ingredient_type
                            ? ` (${ing.ingredient_type})`
                            : ''}
                        </label>
                        {isSelected && (
                          <div className="ml-6 flex gap-2">
                            <Input
                              type="number"
                              step={0.01}
                              placeholder="Amount"
                              value={
                                selected.find(
                                  (s) => s.ingredient_id === ing.id,
                                )?.amount ?? 0
                              }
                              onChange={(e) =>
                                updateSelected(
                                  ing.id,
                                  'amount',
                                  Number(e.target.value),
                                )
                              }
                              className="w-28"
                            />
                            <Input
                              type="text"
                              placeholder="Unit"
                              value={
                                selected.find(
                                  (s) => s.ingredient_id === ing.id,
                                )?.unit ?? 'g'
                              }
                              onChange={(e) =>
                                updateSelected(
                                  ing.id,
                                  'unit',
                                  e.target.value,
                                )
                              }
                              className="w-20"
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

            <Button
              onClick={handleCalculate}
              disabled={submitting || selected.length === 0}
            >
              {submitting ? 'Calculating...' : 'Calculate ABV'}
            </Button>

            {result && (
              <div className="rounded-lg border border-input bg-muted/50 p-4 space-y-2">
                <h3 className="font-medium">Results</h3>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">Max ABV</p>
                    <p className="text-lg font-semibold">
                      {result.max_abv != null
                        ? `${result.max_abv.toFixed(2)}%`
                        : '-'}
                    </p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Sugar Content</p>
                    <p className="text-lg font-semibold">
                      {result.sugar_content != null
                        ? `${result.sugar_content.toFixed(1)} g`
                        : '-'}
                    </p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Volume</p>
                    <p className="text-lg font-semibold">
                      {result.volume != null
                        ? `${result.volume.toFixed(1)} mL`
                        : '-'}
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

// ---------------------------------------------------------------------------
// Main Brew Page
// ---------------------------------------------------------------------------

export default function BrewPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && (!user || !user.is_admin)) {
      router.push('/');
    }
  }, [loading, user, router]);

  if (loading) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  if (!user || !user.is_admin) return null;

  return (
    <div className="mx-auto w-full max-w-4xl space-y-6 px-4 py-8">
      <h1 className="text-2xl font-semibold">Brew Log</h1>
      <Tabs defaultValue={0}>
        <TabsList className="flex-wrap">
          <TabsTrigger value={0}>Start</TabsTrigger>
          <TabsTrigger value={1}>Ingredients</TabsTrigger>
          <TabsTrigger value={2}>SG Measurements</TabsTrigger>
          <TabsTrigger value={3}>Mass Measurements</TabsTrigger>
          <TabsTrigger value={4}>Rack</TabsTrigger>
          <TabsTrigger value={5}>Bottle</TabsTrigger>
          <TabsTrigger value={6}>Calculator</TabsTrigger>
        </TabsList>
        <TabsContent value={0}>
          <StartTab />
        </TabsContent>
        <TabsContent value={1}>
          <IngredientsTab />
        </TabsContent>
        <TabsContent value={2}>
          <SgTab />
        </TabsContent>
        <TabsContent value={3}>
          <MassTab />
        </TabsContent>
        <TabsContent value={4}>
          <RackTab />
        </TabsContent>
        <TabsContent value={5}>
          <BottleTab />
        </TabsContent>
        <TabsContent value={6}>
          <CalculatorTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
