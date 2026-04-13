'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/components/AuthProvider';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { StartTab } from './tabs/StartTab';
import { IngredientsTab } from './tabs/IngredientsTab';
import { SgTab } from './tabs/SgTab';
import { MassTab } from './tabs/MassTab';
import { RackTab } from './tabs/RackTab';
import { BottleTab } from './tabs/BottleTab';
import { CalculatorTab } from './tabs/CalculatorTab';

export default function BrewPage() {
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
      <h1 className="text-2xl font-semibold">Brew Log</h1>
      <Tabs defaultValue={0}>
        <TabsList className="flex-wrap">
          <TabsTrigger value={0}>Start</TabsTrigger>
          <TabsTrigger value={1}>Ingredients</TabsTrigger>
          <TabsTrigger value={2}>SG Measurements</TabsTrigger>
          <TabsTrigger value={3}>Mass Measurements</TabsTrigger>
          <TabsTrigger value={4}>Rack</TabsTrigger>
          <TabsTrigger value={5}>Bottle</TabsTrigger>
          <TabsTrigger value={6}>Calculator</TabsTrigger>
        </TabsList>
        <ErrorBoundary>
          <TabsContent value={0}><StartTab /></TabsContent>
          <TabsContent value={1}><IngredientsTab /></TabsContent>
          <TabsContent value={2}><SgTab /></TabsContent>
          <TabsContent value={3}><MassTab /></TabsContent>
          <TabsContent value={4}><RackTab /></TabsContent>
          <TabsContent value={5}><BottleTab /></TabsContent>
          <TabsContent value={6}><CalculatorTab /></TabsContent>
        </ErrorBoundary>
      </Tabs>
    </div>
  );
}
