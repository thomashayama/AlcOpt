'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { FermentationActiveOut } from '@/lib/types';
import { Label } from '@/components/ui/label';

export type ContainerIdValue = number | '';

export const VALID_UNITS = ['g', 'kg', 'mL', 'L', 'tsp', 'tbsp'] as const;

const selectClassName = 'flex h-8 w-full rounded-lg border border-input bg-transparent px-2.5 py-1 text-sm transition-colors focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50';

function toDate(value: string) {
  return value.slice(0, 10);
}

export function formatActiveFermentation(active: FermentationActiveOut) {
  return `Container ${active.container_id} - fermentation ${active.fermentation_id} - ${active.stage ?? 'active'} - ${active.container_type} - started ${toDate(active.start_date)}`;
}

export function formatActiveFermentationSummary(active: FermentationActiveOut) {
  return `Active: container ${active.container_id}, fermentation ${active.fermentation_id}, ${active.stage ?? 'active'}, started ${toDate(active.start_date)}`;
}

function useActiveFermentations() {
  const [active, setActive] = useState<FermentationActiveOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api.get<FermentationActiveOut[]>('/api/brew/fermentations/active')
      .then((data) => {
        if (!cancelled) setActive(Array.isArray(data) ? data : []);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load active fermentations');
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return { active, loading, error };
}

export function ActiveFermentationSummary() {
  const { active, loading, error } = useActiveFermentations();

  if (loading) {
    return <p className="text-sm text-muted-foreground">Loading active fermentations...</p>;
  }
  if (error) {
    return <p className="text-sm text-destructive">{error}</p>;
  }
  if (active.length === 0) {
    return <p className="text-sm text-muted-foreground">No active fermentations.</p>;
  }

  return (
    <div className="space-y-1 text-sm text-muted-foreground">
      {active.map((item) => (
        <p key={`${item.fermentation_id}-${item.container_id}`}>
          {formatActiveFermentationSummary(item)}
        </p>
      ))}
    </div>
  );
}

export function ActiveFermentationSelect({
  id,
  label = 'Active Fermentation',
  value,
  onChange,
}: {
  id: string;
  label?: string;
  value: ContainerIdValue;
  onChange: (value: ContainerIdValue) => void;
}) {
  const { active, loading, error } = useActiveFermentations();

  useEffect(() => {
    if (value === '' && active.length > 0) {
      onChange(active[0].container_id);
    }
  }, [active, onChange, value]);

  const selectedValue = active.some((item) => item.container_id === value)
    ? String(value)
    : '';
  const selectedActive = active.find((item) => item.container_id === value);

  return (
    <div className="space-y-2">
      <Label htmlFor={id}>{label}</Label>
      <select
        id={id}
        className={selectClassName}
        value={selectedValue}
        onChange={(e) => onChange(e.target.value === '' ? '' : Number(e.target.value))}
        disabled={loading || active.length === 0}
      >
        <option value="">
          {loading ? 'Loading active fermentations...' : 'Manual container ID'}
        </option>
        {active.map((item) => (
          <option key={`${item.fermentation_id}-${item.container_id}`} value={item.container_id}>
            {formatActiveFermentation(item)}
          </option>
        ))}
      </select>
      {selectedActive && (
        <p className="text-sm text-muted-foreground">
          {formatActiveFermentation(selectedActive)}
        </p>
      )}
      {error && <p className="text-sm text-destructive">{error}</p>}
      {!loading && !error && active.length === 0 && (
        <p className="text-sm text-muted-foreground">No active fermentations.</p>
      )}
    </div>
  );
}

export function UnitSelect({
  id,
  label,
  value,
  onChange,
  labelClassName,
  className = '',
}: {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  labelClassName?: string;
  className?: string;
}) {
  return (
    <div className={className || 'space-y-2'}>
      <Label htmlFor={id} className={labelClassName}>{label}</Label>
      <select
        id={id}
        className={selectClassName}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {VALID_UNITS.map((unit) => (
          <option key={unit} value={unit}>
            {unit}
          </option>
        ))}
      </select>
    </div>
  );
}
