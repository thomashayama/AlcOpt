'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/components/AuthProvider';
import { api } from '@/lib/api';
import type { ContainerOut } from '@/lib/types';
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

function VesselTab() {
  const [dateAdded, setDateAdded] = useState(
    new Date().toISOString().slice(0, 10),
  );
  const [material, setMaterial] = useState('Glass');
  const [volume, setVolume] = useState(2.0);
  const [emptyMass, setEmptyMass] = useState(792.0);
  const [containerType, setContainerType] = useState('carboy');
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<{
    type: 'success' | 'error';
    text: string;
  } | null>(null);
  const [vessels, setVessels] = useState<ContainerOut[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchVessels = async () => {
    try {
      setLoading(true);
      const data = await api.get<ContainerOut[]>(
        '/api/containers?container_type=carboy',
      );
      setVessels(data);
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVessels();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setMessage(null);
    try {
      await api.post('/api/containers', {
        container_type: containerType,
        volume_liters: volume,
        material,
        empty_mass: emptyMass,
        date_added: dateAdded,
      });
      setMessage({ type: 'success', text: 'Vessel added successfully!' });
      fetchVessels();
    } catch (err) {
      setMessage({
        type: 'error',
        text: err instanceof Error ? err.message : 'Failed to add vessel',
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>New Vessel</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="v_date">Date Added</Label>
                <Input
                  id="v_date"
                  type="date"
                  value={dateAdded}
                  onChange={(e) => setDateAdded(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="v_material">Material</Label>
                <Input
                  id="v_material"
                  type="text"
                  value={material}
                  onChange={(e) => setMaterial(e.target.value)}
                />
              </div>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="v_volume">Volume (L)</Label>
                <Input
                  id="v_volume"
                  type="number"
                  step={0.1}
                  value={volume}
                  onChange={(e) => setVolume(Number(e.target.value))}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="v_mass">Empty Mass (g)</Label>
                <Input
                  id="v_mass"
                  type="number"
                  step={0.1}
                  value={emptyMass}
                  onChange={(e) => setEmptyMass(Number(e.target.value))}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="v_type">Type</Label>
                <Input
                  id="v_type"
                  type="text"
                  value={containerType}
                  onChange={(e) => setContainerType(e.target.value)}
                />
              </div>
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

            <Button type="submit" disabled={submitting}>
              {submitting ? 'Adding...' : 'Add Vessel'}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Vessels</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-sm text-muted-foreground">Loading...</p>
          ) : vessels.length === 0 ? (
            <p className="text-sm text-muted-foreground">No vessels found.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Material</TableHead>
                  <TableHead>Volume (L)</TableHead>
                  <TableHead>Empty Mass (g)</TableHead>
                  <TableHead>Date Added</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {vessels.map((v) => (
                  <TableRow key={v.id}>
                    <TableCell>{v.id}</TableCell>
                    <TableCell>{v.container_type}</TableCell>
                    <TableCell>{v.material ?? '-'}</TableCell>
                    <TableCell>{v.volume_liters ?? '-'}</TableCell>
                    <TableCell>{v.empty_mass ?? '-'}</TableCell>
                    <TableCell>{v.date_added ?? '-'}</TableCell>
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

function BottleTab() {
  const [dateAdded, setDateAdded] = useState(
    new Date().toISOString().slice(0, 10),
  );
  const [volume, setVolume] = useState(0.5);
  const [emptyMass, setEmptyMass] = useState(500.0);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<{
    type: 'success' | 'error';
    text: string;
  } | null>(null);
  const [bottles, setBottles] = useState<ContainerOut[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchBottles = async () => {
    try {
      setLoading(true);
      const data = await api.get<ContainerOut[]>(
        '/api/containers?container_type=bottle',
      );
      setBottles(data);
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBottles();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setMessage(null);
    try {
      await api.post('/api/containers', {
        container_type: 'bottle',
        volume_liters: volume,
        empty_mass: emptyMass,
        date_added: dateAdded,
      });
      setMessage({ type: 'success', text: 'Bottle added successfully!' });
      fetchBottles();
    } catch (err) {
      setMessage({
        type: 'error',
        text: err instanceof Error ? err.message : 'Failed to add bottle',
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>New Bottle</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="b_date">Date Added</Label>
                <Input
                  id="b_date"
                  type="date"
                  value={dateAdded}
                  onChange={(e) => setDateAdded(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="b_volume">Volume (L)</Label>
                <Input
                  id="b_volume"
                  type="number"
                  step={0.1}
                  value={volume}
                  onChange={(e) => setVolume(Number(e.target.value))}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="b_mass">Empty Mass (g)</Label>
                <Input
                  id="b_mass"
                  type="number"
                  step={0.1}
                  value={emptyMass}
                  onChange={(e) => setEmptyMass(Number(e.target.value))}
                />
              </div>
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

            <Button type="submit" disabled={submitting}>
              {submitting ? 'Adding...' : 'Add Bottle'}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Bottles</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-sm text-muted-foreground">Loading...</p>
          ) : bottles.length === 0 ? (
            <p className="text-sm text-muted-foreground">No bottles found.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Volume (L)</TableHead>
                  <TableHead>Empty Mass (g)</TableHead>
                  <TableHead>Date Added</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {bottles.map((b) => (
                  <TableRow key={b.id}>
                    <TableCell>{b.id}</TableCell>
                    <TableCell>{b.volume_liters ?? '-'}</TableCell>
                    <TableCell>{b.empty_mass ?? '-'}</TableCell>
                    <TableCell>{b.date_added ?? '-'}</TableCell>
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

export default function BottlesPage() {
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
      <h1 className="text-2xl font-semibold">Bottle Log</h1>
      <Tabs defaultValue={0}>
        <TabsList>
          <TabsTrigger value={0}>New Vessel</TabsTrigger>
          <TabsTrigger value={1}>New Bottle</TabsTrigger>
        </TabsList>
        <TabsContent value={0}>
          <VesselTab />
        </TabsContent>
        <TabsContent value={1}>
          <BottleTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
