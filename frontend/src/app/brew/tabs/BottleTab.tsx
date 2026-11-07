'use client';

import { useCallback, useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type {
  ContainerInfoResponse,
  ContainerLogOut,
  FermentationActiveOut,
  FermentationOut,
} from '@/lib/types';
import { Message } from '@/components/Message';
import { ConfirmDialog } from '@/components/ConfirmDialog';
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

type AmountMode = 'contents' | 'filledMass';

function formatGram(value: number) {
  return Number.isInteger(value)
    ? value.toFixed(0)
    : value.toFixed(2).replace(/0+$/, '').replace(/\.$/, '');
}

export function BottleTab() {
  const [fromContainerId, setFromContainerId] = useState<ContainerIdValue>('');
  const [toContainerId, setToContainerId] = useState<ContainerIdValue>('');
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
  const [finishContainerId, setFinishContainerId] = useState<ContainerIdValue>('');
  const [finishFermentationId, setFinishFermentationId] = useState<number | ''>('');
  const [finishDate, setFinishDate] = useState(
    new Date().toISOString().slice(0, 10),
  );
  const [finishEndMass, setFinishEndMass] = useState<number | ''>('');
  const [finishing, setFinishing] = useState(false);
  const [finishMessage, setFinishMessage] = useState<{
    type: 'success' | 'error';
    text: string;
  } | null>(null);

  const handleFinishActiveChange = useCallback((
    active: FermentationActiveOut | null,
  ) => {
    setFinishFermentationId(active?.fermentation_id ?? '');
  }, []);

  useEffect(() => {
    if (amountMode !== 'filledMass') {
      setTargetBottleEmptyMass(null);
      setTargetBottleMessage(null);
      return;
    }
    if (toContainerId === '') {
      setTargetBottleEmptyMass(null);
      setTargetBottleMessage(null);
      return;
    }

    let cancelled = false;
    setTargetBottleEmptyMass(null);
    setTargetBottleMessage({ type: 'success', text: 'Loading bottle mass...' });

    api.get<ContainerInfoResponse>(`/api/containers/${Number(toContainerId)}`)
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

  const hasContainers = fromContainerId !== '' && toContainerId !== '';
  const canSubmit = !submitting && hasContainers && (
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
          from_container_id: Number(fromContainerId),
          to_container_id: Number(toContainerId),
          date: bottleDate,
          filled_mass_g: filledMass === '' ? null : filledMass,
        }
        : {
          from_container_id: Number(fromContainerId),
          to_container_id: Number(toContainerId),
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
      const nextBottleId = Number(toContainerId) + 1;
      setLastBottlingLog(log);
      setToContainerId(nextBottleId);
      setAmount('');
      setFilledMass('');
      setMessage({
        type: 'success',
        text: `Bottling recorded for container ${log.container_id}. Next bottle should be ${nextBottleId}.`,
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

  const handleFinishFermentation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (finishFermentationId === '') return;
    setFinishing(true);
    setFinishMessage(null);
    try {
      const fermentation = await api.patch<FermentationOut>(
        `/api/brew/fermentations/${finishFermentationId}`,
        {
          end_date: finishDate,
          end_mass: finishEndMass === '' ? null : finishEndMass,
        },
      );
      setFinishMessage({
        type: 'success',
        text: `Fermentation ${fermentation.id} finished.`,
      });
    } catch (err) {
      setFinishMessage({
        type: 'error',
        text: err instanceof Error ? err.message : 'Failed to finish fermentation',
      });
    } finally {
      setFinishing(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader><CardTitle>Bottle</CardTitle></CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <ActiveFermentationSelect
              id="bottle_active_fermentation"
              value={fromContainerId}
              onChange={setFromContainerId}
            />
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="bot_from">From Container ID (vessel)</Label>
                <Input
                  id="bot_from"
                  type="number"
                  min={1}
                  value={fromContainerId}
                  onChange={(e) => setFromContainerId(e.target.value === '' ? '' : Number(e.target.value))}
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
                  onChange={(e) => setToContainerId(e.target.value === '' ? '' : Number(e.target.value))}
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

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
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
                  <UnitSelect
                    id="bot_unit"
                    label="Unit"
                    value={unit}
                    onChange={setUnit}
                  />
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
            {lastBottlingLog && toContainerId !== '' && (
              <p className="text-sm text-muted-foreground">
                {`Next bottle should be ${toContainerId}`}
              </p>
            )}
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
        <CardHeader><CardTitle>Finish Fermentation</CardTitle></CardHeader>
        <CardContent>
          <form onSubmit={handleFinishFermentation} className="space-y-4">
            <ActiveFermentationSelect
              id="finish_active_fermentation"
              label="Active Fermentation to Finish"
              value={finishContainerId}
              onChange={setFinishContainerId}
              onActiveChange={handleFinishActiveChange}
            />
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="finish_date">End Date</Label>
                <Input
                  id="finish_date"
                  type="date"
                  value={finishDate}
                  onChange={(event) => setFinishDate(event.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="finish_end_mass">End Mass (g)</Label>
                <Input
                  id="finish_end_mass"
                  type="number"
                  step={0.1}
                  value={finishEndMass}
                  onChange={(event) => setFinishEndMass(
                    event.target.value === '' ? '' : Number(event.target.value),
                  )}
                />
              </div>
            </div>
            <Message message={finishMessage} />
            <Button
              type="submit"
              disabled={finishing || finishFermentationId === ''}
            >
              {finishing ? 'Finishing...' : 'Finish Fermentation'}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Empty Container</CardTitle></CardHeader>
        <CardContent>
          <div className="flex items-end gap-4">
            <div className="min-w-0 flex-1 space-y-2 sm:flex-none">
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
