'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/components/AuthProvider';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? '';

export default function LabelsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  const [minId, setMinId] = useState(1);
  const [maxId, setMaxId] = useState(12);
  const [baseUrl, setBaseUrl] = useState('');
  const [generating, setGenerating] = useState(false);
  const [message, setMessage] = useState<{
    type: 'success' | 'error';
    text: string;
  } | null>(null);

  useEffect(() => {
    if (!loading && (!user || !user.is_admin)) {
      router.push('/');
    }
  }, [loading, user, router]);

  useEffect(() => {
    setBaseUrl(window.location.origin);
  }, []);

  const handleGenerate = async () => {
    setGenerating(true);
    setMessage(null);
    try {
      const params = new URLSearchParams({
        min_id: String(minId),
        max_id: String(maxId),
        base_url: baseUrl,
      });
      const res = await fetch(
        `${API_BASE}/api/labels/pdf?${params.toString()}`,
        { credentials: 'include' },
      );
      if (!res.ok) {
        let errMsg = res.statusText;
        try {
          const body = await res.json();
          errMsg = body.detail ?? body.message ?? errMsg;
        } catch {
          // use statusText
        }
        throw new Error(errMsg);
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `labels_${minId}-${maxId}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      const count = maxId - minId + 1;
      setMessage({
        type: 'success',
        text: `Generated PDF with ${count} label(s).`,
      });
    } catch (err) {
      setMessage({
        type: 'error',
        text: err instanceof Error ? err.message : 'Failed to generate PDF',
      });
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  if (!user || !user.is_admin) return null;

  return (
    <div className="mx-auto w-full max-w-2xl space-y-8 px-4 py-8">
      <Card>
        <CardHeader>
          <CardTitle>Generate Container Labels</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="min_id">Min Container ID</Label>
                <Input
                  id="min_id"
                  type="number"
                  min={1}
                  value={minId}
                  onChange={(e) => setMinId(Number(e.target.value))}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="max_id">Max Container ID</Label>
                <Input
                  id="max_id"
                  type="number"
                  min={1}
                  value={maxId}
                  onChange={(e) => setMaxId(Number(e.target.value))}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="base_url">Base URL</Label>
              <Input
                id="base_url"
                type="text"
                value={baseUrl}
                onChange={(e) => setBaseUrl(e.target.value)}
              />
            </div>

            {message && (
              <p
                className={
                  message.type === 'success'
                    ? 'text-sm text-green-500'
                    : 'text-sm text-destructive'
                }
              >
                {message.text}
              </p>
            )}

            <Button onClick={handleGenerate} disabled={generating}>
              {generating ? 'Generating...' : 'Generate PDF'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
