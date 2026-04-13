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

export function StartTab() {
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
      await api.post('/api/brew/fermentations', {
        container_id: containerId,
        start_date: startDate,
        stage,
      });
      setMessage({ type: 'success', text: 'Fermentation started successfully!' });
      fetchLogs();
    } catch (err) {
      setMessage({
        type: 'error',
        text: err instanceof Error ? err.message : 'Failed to start fermentation',
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader><CardTitle>Start Fermentation</CardTitle></CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="s_container">Container ID</Label>
                <Input id="s_container" type="number" min={1} value={containerId} onChange={(e) => setContainerId(Number(e.target.value))} required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="s_date">Start Date</Label>
                <Input id="s_date" type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="s_stage">Stage</Label>
                <Input id="s_stage" type="text" value={stage} onChange={(e) => setStage(e.target.value)} />
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
