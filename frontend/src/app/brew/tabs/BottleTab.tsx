'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { ContainerInfoResponse, ContainerLogOut } from '@/lib/types';
import { Message } from '@/components/Message';
import { ConfirmDialog } from '@/components/ConfirmDialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Card, CardContent, CardHeader, CardTitle,
} from '@/components/ui/card';

type AmountMode = 'contents' | 'filledMass';

function formatGram(value: number) {
  return Number.isInteger(value)
    ? value.toFixed(0)
    : value.toFixed(2).replace(/0+$/, '').replace(/\.$/, '');
}

export function BottleTab() {
  const [fromContainerId, setFromContainerId] = useState(1);
  const [toContainerId, setToContainerId] = useState(1);
  const [bottleDate, setBottleDate] = useState(
    new Date().toISOString().slice(0, 10),
  );
  const [amountMode, setAmountMode] = useState<AmountMode>('contents');
  const [amount, setAmount] = useState<number | ''>('');
  const [unit, setUnit] = useState('mL');
  const [filledMass, setFilledMass] = useState<number | ''>('');
  const [targetBottleEmptyMass, setTargetBottleEmptyMass] = useState<number | null>(
    null,
  );
  const [targetBottleMessage, setTargetBottleMessage] = useState<{
    type: 'success' | 'error';
    text: string;
  } | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<{
    type: 'success' | 'error';
    text: string;
  } | null>(null);
  const [lastBottlingLog, setLastBottlingLog] = useState<ContainerLogOut | null>(
    null,
  );
  const [undoing, setUndoing] = useState(false);

  const [emptyContainerId, setEmptyContainerId] = useState(1);
  const [emptyMessage, setEmptyMessage] = useState<{
    type: 'success' | 'error';
    text: string;
  } | null>(null);

  useEffect(() => {
    if (amountMode !== 'filledMass') {
      setTargetBottleEmptyMass(null);
      setTargetBottleMessage(null);
      return;
    }

    let cancelled = false;
    setTargetBottleEmptyMass(null);
    setTargetBottleMessage({ type: 'success', text: 'Loading bottle mass...' });

    api.get<ContainerInfoResponse>(`/api/containers/${toContainerId}`)
      .then((data) => {
        if (cancelled) return;
        const emptyMass = data.container.empty_mass;
        if (emptyMass === null || emptyMass === undefined) {
          setTargetBottleMessage({
            type: 'error',
            text: `Container ${toContainerId} does not have an empty mass.`,
          });
          return;
        }
        setTargetBottleEmptyMass(emptyMass);
        setTargetBottleMessage({
          type: 'success',
          text: `Empty mass: ${formatGram(emptyMass)}g`,
        });
      })
      .catch((err) => {
        if (cancelled) return;
        setTargetBottleMessage({
          type: 'error',
          text: err instanceof Error ? err.message : 'Failed to load bottle mass',
        });
      });

    return () => {
      cancelled = true;
    };
  }, [amountMode, toContainerId]);

  const calculatedBottleAmount =
    amountMode === 'filledMass'
    && filledMass !== ''
    && targetBottleEmptyMass !== null
      ? filledMass - targetBottleEmptyMass
      : null;

  const canSubmit = !submitting && (
    amountMode === 'contents'
    || (
      filledMass !== ''
      && targetBottleEmptyMass !== null
      && calculatedBottleAmount !== null
      && calculatedBottleAmount > 0
    )
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setMessage(null);
    try {
      const payload = amountMode === 'filledMass'
        ? {
          from_container_id: fromContainerId,
          to_container_id: toContainerId,
          date: bottleDate,
          filled_mass_g: filledMass === '' ? null : filledMass,
        }
        : {
          from_container_id: fromContainerId,
          to_container_id: toContainerId,
          date: bottleDate,
          amount: amount === '' ? null : amount,
          unit,
        };

      if (amountMode === 'filledMass') {
        if (calculatedBottleAmount === null) {
          setMessage({ type: 'error', text: 'Enter a filled bottle mass.' });
          return;
        }
        if (calculatedBottleAmount <= 0) {
          setMessage({
            type: 'error',
            text: 'Filled bottle mass must be greater than empty mass.',
          });
          return;
        }
      }

      const log = await api.post<ContainerLogOut>('/api/brew/bottle', payload);
      setLastBottlingLog(log);
      setMessage({
        type: 'success',
        text: `Bottling recorded for container ${log.container_id}.`,
      });
    } catch (err) {
      setMessage({
        type: 'error',
        text: err instanceof Error ? err.message : 'Failed to record bottling',
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleUndo = async () => {
    if (!lastBottlingLog) return;
    setUndoing(true);
    setMessage(null);
    try {
      const result = await api.post<{ message: string }>(
        `/api/brew/bottle/${lastBottlingLog.id}/undo`,
      );
      setLastBottlingLog(null);
      setMessage({ type: 'success', text: result.message });
    } catch (err) {
      setMessage({
        type: 'error',
        text: err instanceof Error ? err.message : 'Failed to undo bottling',
      });
    } finally {
      setUndoing(false);
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

            <fieldset className="space-y-2">
              <legend className="text-sm font-medium">Amount entry</legend>
              <div className="flex flex-wrap gap-3">
                <label
                  htmlFor="amount_contents"
                  className="flex items-center gap-2 text-sm"
                >
                  <input
                    id="amount_contents"
                    type="radio"
                    name="amount_mode"
                    checked={amountMode === 'contents'}
                    onChange={() => setAmountMode('contents')}
                  />
                  Contents amount
                </label>
                <label
                  htmlFor="amount_filled_mass"
                  className="flex items-center gap-2 text-sm"
                >
                  <input
                    id="amount_filled_mass"
                    type="radio"
                    name="amount_mode"
                    checked={amountMode === 'filledMass'}
                    onChange={() => setAmountMode('filledMass')}
                  />
                  Filled bottle mass
                </label>
              </div>
            </fieldset>

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
              {amountMode === 'contents' ? (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="bot_amount">Amount</Label>
                    <Input
                      id="bot_amount"
                      type="number"
                      step={0.01}
                      value={amount}
                      onChange={(e) => setAmount(
                        e.target.value === '' ? '' : Number(e.target.value),
                      )}
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
                </>
              ) : (
                <div className="space-y-2 md:col-span-2">
                  <Label htmlFor="bot_filled_mass">Filled Bottle Mass (g)</Label>
                  <Input
                    id="bot_filled_mass"
                    type="number"
                    step={0.01}
                    value={filledMass}
                    onChange={(e) => setFilledMass(
                      e.target.value === '' ? '' : Number(e.target.value),
                    )}
                  />
                </div>
              )}
            </div>

            {amountMode === 'filledMass' && (
              <div className="space-y-1 text-sm">
                <Message message={targetBottleMessage} />
                {calculatedBottleAmount !== null
                  && targetBottleEmptyMass !== null && (
                    <p
                      className={
                        calculatedBottleAmount > 0
                          ? 'text-muted-foreground'
                          : 'text-destructive'
                      }
                    >
                      {`${formatGram(filledMass as number)}g - ${formatGram(targetBottleEmptyMass)}g = ${formatGram(calculatedBottleAmount)}g contents`}
                    </p>
                )}
              </div>
            )}

            <Message message={message} />
            <div className="flex flex-wrap gap-3">
              <Button type="submit" disabled={!canSubmit}>
                {submitting ? 'Recording...' : 'Record Bottling'}
              </Button>
              {lastBottlingLog && (
                <Button
                  type="button"
                  variant="destructive"
                  onClick={handleUndo}
                  disabled={undoing}
                >
                  {undoing ? 'Undoing...' : 'Undo Last Bottling'}
                </Button>
              )}
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Empty Container</CardTitle></CardHeader>
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
