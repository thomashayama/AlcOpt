'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import { Message } from '@/components/Message';
import { ConfirmDialog } from '@/components/ConfirmDialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Card, CardContent, CardHeader, CardTitle,
} from '@/components/ui/card';

export function BottleTab() {
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

  const [emptyContainerId, setEmptyContainerId] = useState(1);
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
    setEmptyMessage(null);
    try {
      await api.post(`/api/brew/empty/${emptyContainerId}`);
      setEmptyMessage({ type: 'success', text: 'Container emptied!' });
    } catch (err) {
      setEmptyMessage({
        type: 'error',
        text: err instanceof Error ? err.message : 'Failed to empty container',
      });
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader><CardTitle>Bottle</CardTitle></CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="bot_from">From Container ID (vessel)</Label>
                <Input id="bot_from" type="number" min={1} value={fromContainerId} onChange={(e) => setFromContainerId(Number(e.target.value))} required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="bot_to">To Container ID (bottle)</Label>
                <Input id="bot_to" type="number" min={1} value={toContainerId} onChange={(e) => setToContainerId(Number(e.target.value))} required />
              </div>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="bot_date">Date</Label>
                <Input id="bot_date" type="date" value={bottleDate} onChange={(e) => setBottleDate(e.target.value)} required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="bot_amount">Amount</Label>
                <Input id="bot_amount" type="number" step={0.01} value={amount} onChange={(e) => setAmount(e.target.value === '' ? '' : Number(e.target.value))} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="bot_unit">Unit</Label>
                <Input id="bot_unit" type="text" value={unit} onChange={(e) => setUnit(e.target.value)} />
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
        <CardHeader><CardTitle>Empty Container</CardTitle></CardHeader>
        <CardContent>
          <div className="flex items-end gap-4">
            <div className="space-y-2">
              <Label htmlFor="empty_id">Container ID</Label>
              <Input id="empty_id" type="number" min={1} value={emptyContainerId} onChange={(e) => setEmptyContainerId(Number(e.target.value))} />
            </div>
            <ConfirmDialog
              title="Empty Container"
              description={`Are you sure you want to mark container ${emptyContainerId} as empty? This will close its active fermentation log.`}
              confirmLabel="Empty"
              variant="destructive"
              onConfirm={handleEmpty}
              trigger="Empty Container"
            />
          </div>
          <Message message={emptyMessage} />
        </CardContent>
      </Card>
    </div>
  );
}
