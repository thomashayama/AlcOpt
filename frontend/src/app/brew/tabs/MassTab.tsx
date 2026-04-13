'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { MassMeasurementOut } from '@/lib/types';
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

export function MassTab() {
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
      const data = await api.get<MassMeasurementOut[]>('/api/brew/mass-measurements');
      setMeasurements(data);
    } catch (err) {
      setMessage({ type: 'error', text: err instanceof Error ? err.message : 'Failed to load measurements' });
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
        text: err instanceof Error ? err.message : 'Failed to record measurement',
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader><CardTitle>Record Mass Measurement</CardTitle></CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="mass_container">Container ID</Label>
                <Input id="mass_container" type="number" min={1} value={containerId} onChange={(e) => setContainerId(Number(e.target.value))} required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="mass_date">Measurement Date</Label>
                <Input id="mass_date" type="date" value={measurementDate} onChange={(e) => setMeasurementDate(e.target.value)} required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="mass_value">Mass (g)</Label>
                <Input id="mass_value" type="number" step={0.1} value={mass} onChange={(e) => setMass(Number(e.target.value))} required />
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
        <CardHeader><CardTitle>Mass Measurements</CardTitle></CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-sm text-muted-foreground">Loading...</p>
          ) : measurements.length === 0 ? (
            <p className="text-sm text-muted-foreground">No measurements found.</p>
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
