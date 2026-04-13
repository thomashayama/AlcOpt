'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { ContainerLogOut } from '@/lib/types';
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

export function RackTab() {
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
      const data = await api.get<ContainerLogOut[]>('/api/brew/fermentations');
      setLogs(data);
    } catch (err) {
      setMessage({ type: 'error', text: err instanceof Error ? err.message : 'Failed to load logs' });
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
        <CardHeader><CardTitle>Rack</CardTitle></CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="rack_from">From Container ID</Label>
                <Input id="rack_from" type="number" min={1} value={fromContainerId} onChange={(e) => setFromContainerId(Number(e.target.value))} required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="rack_to">To Container ID</Label>
                <Input id="rack_to" type="number" min={1} value={toContainerId} onChange={(e) => setToContainerId(Number(e.target.value))} required />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="rack_date">Date</Label>
                <Input id="rack_date" type="date" value={rackDate} onChange={(e) => setRackDate(e.target.value)} required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="rack_stage">Stage</Label>
                <Input id="rack_stage" type="text" value={stage} onChange={(e) => setStage(e.target.value)} />
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
        <CardHeader><CardTitle>Fermentation Logs</CardTitle></CardHeader>
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
