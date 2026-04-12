'use client';

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  type ReactNode,
} from 'react';
import type { UserInfo } from '@/lib/types';

interface AuthContextValue {
  user: UserInfo | null;
  loading: boolean;
  login: () => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/auth/me', { credentials: 'include' })
      .then((res) => {
        if (res.ok) return res.json();
        return null;
      })
      .then((data) => {
        setUser(data as UserInfo | null);
      })
      .catch(() => {
        setUser(null);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const login = useCallback(async () => {
    const res = await fetch('/auth/login', { credentials: 'include' });
    if (res.ok) {
      const data = await res.json();
      window.location.href = data.url ?? data.authorization_url;
    }
  }, []);

  const logout = useCallback(async () => {
    await fetch('/auth/logout', {
      method: 'POST',
      credentials: 'include',
    });
    setUser(null);
    window.location.reload();
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (ctx === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
}
