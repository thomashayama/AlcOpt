'use client';

import Link from 'next/link';
import { useAuth } from '@/components/AuthProvider';
import { Button } from '@/components/ui/button';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';

export function Header() {
  const { user, loading, login, logout } = useAuth();

  const rawName = user?.name || user?.email?.split('@')[0] || '';
  const displayName = rawName.charAt(0).toUpperCase() + rawName.slice(1);

  return (
    <header className="sticky top-0 z-50 border-b" style={{ backgroundColor: '#262730' }}>
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4">
        {/* Left: brand + nav */}
        <div className="flex items-center gap-6">
          <Link href="/" className="text-lg font-bold text-foreground">
            AlcOpt
          </Link>

          <nav className="flex items-center gap-4 text-sm">
            <Link href="/tasting" className="text-muted-foreground hover:text-foreground transition-colors">
              Tasting
            </Link>
            <Link href="/info" className="text-muted-foreground hover:text-foreground transition-colors">
              Info
            </Link>

            {user?.is_admin && (
              <>
                <Link href="/brew" className="text-muted-foreground hover:text-foreground transition-colors">
                  Brew
                </Link>
                <Link href="/bottles" className="text-muted-foreground hover:text-foreground transition-colors">
                  Bottles
                </Link>
                <Link href="/labels" className="text-muted-foreground hover:text-foreground transition-colors">
                  Labels
                </Link>
              </>
            )}
          </nav>
        </div>

        {/* Right: auth */}
        <div className="flex items-center">
          {loading ? null : user ? (
            <Popover>
              <PopoverTrigger
                className="inline-flex items-center gap-2 rounded-lg px-2.5 py-1.5 text-sm text-foreground hover:bg-muted transition-colors cursor-pointer"
              >
                {displayName}
              </PopoverTrigger>
              <PopoverContent className="w-64" align="end">
                <div className="flex flex-col items-center gap-3 py-2">
                  <Avatar className="h-16 w-16" size="lg">
                    <AvatarImage src={user.picture} alt={user.email} />
                    <AvatarFallback>
                      {displayName.slice(0, 2).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <p className="text-sm text-muted-foreground">{user.email}</p>
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => logout()}
                  >
                    Sign Out
                  </Button>
                </div>
              </PopoverContent>
            </Popover>
          ) : (
            <Button
              onClick={() => login()}
              className="bg-primary text-primary-foreground hover:bg-primary/90"
            >
              Login
            </Button>
          )}
        </div>
      </div>
    </header>
  );
}
