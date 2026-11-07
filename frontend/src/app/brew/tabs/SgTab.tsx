'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { SgMeasurementOut } from '@/lib/types';
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
  type ContainerIdValue,
} from './brewFormHelpers';

export function SgTab() {
  const [containerId, setContainerId] = useState<ContainerIdValue>('');
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
  const [lastMeasurement, setLastMeasurement] = useState<SgMeasurementOut | null>(
    null,
  );
  const [undoing, setUndoing] = useState(false);

  const fetchMeasurements = async () => {
    try {
      setLoading(true);
      const data = await api.get<SgMeasurementOut[]>('/api/brew/sg-measurements');
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
      const measurement = await api.post<SgMeasurementOut>('/api/brew/sg-measurements', {
        container_id: Number(containerId),
        measurement_date: measurementDate,
        specific_gravity: sg,
      });
      setLastMeasurement(measurement);
      setMessage({
        type: 'success',
        text: `SG measurement ${measurement.id} recorded for fermentation ${measurement.fermentation_id}: ${measurement.specific_gravity}.`,
      });
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

  const handleUndo = async () => {
    if (!lastMeasurement) return;
    setUndoing(true);
    setMessage(null);
    try {
      const result = await api.post<{ message: string }>(
        `/api/brew/sg-measurements/${lastMeasurement.id}/undo`,
      );
      setLastMeasurement(null);
      setMessage({ type: 'success', text: result.message });
      fetchMeasurements();
    } catch (err) {
      setMessage({
        type: 'error',
        text: err instanceof Error ? err.message : 'Failed to undo measurement',
      });
    } finally {
      setUndoing(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader><CardTitle>Record SG Measurement</CardTitle></CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <ActiveFermentationSelect
              id="sg_active_fermentation"
              value={containerId}
              onChange={setContainerId}
            />
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div className="space-y-2">
                <Label htmlFor="sg_container">Container ID</Label>
                <Input
                  id="sg_container"
                  type="number"
                  min={1}
                  value={containerId}
                  onChange={(e) => setContainerId(e.target.value === '' ? '' : Number(e.target.value))}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="sg_date">Measurement Date</Label>
                <Input id="sg_date" type="date" value={measurementDate} onChange={(e) => setMeasurementDate(e.target.value)} required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="sg_value">Specific Gravity</Label>
                <Input id="sg_value" type="number" step={0.001} value={sg} onChange={(e) => setSg(Number(e.target.value))} required />
              </div>
            </div>
            <Message message={message} />
            <div className="flex flex-wrap gap-3">
              <Button type="submit" disabled={submitting || containerId === ''}>
                {submitting ? 'Recording...' : 'Record Measurement'}
              </Button>
              {lastMeasurement && (
                <Button
                  type="button"
                  variant="destructive"
                  onClick={handleUndo}
                  disabled={undoing}
                >
                  {undoing ? 'Undoing...' : 'Undo Last SG Measurement'}
                </Button>
              )}
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>SG Measurements</CardTitle></CardHeader>
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
                  <TableHead>
                    <span className="sm:hidden">Ferm.</span>
                    <span className="hidden sm:inline">Fermentation</span>
                  </TableHead>
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
