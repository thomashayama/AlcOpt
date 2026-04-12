'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function AuthCallbackPage() {
  const router = useRouter();

  useEffect(() => {
    const timer = setTimeout(() => {
      router.replace('/');
    }, 1000);
    return () => clearTimeout(timer);
  }, [router]);

  return (
    <div className="flex flex-1 items-center justify-center">
      <p className="text-lg text-muted-foreground">Completing login...</p>
    </div>
  );
}
