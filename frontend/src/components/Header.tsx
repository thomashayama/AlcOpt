'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/components/AuthProvider';
import { MobileNav } from '@/components/MobileNav';
import { Button } from '@/components/ui/button';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { NAV_LINKS, isActivePath } from '@/lib/nav';
import { cn } from '@/lib/utils';

export function Header() {
  const { user, loading, login, logout } = useAuth();
  const pathname = usePathname();

  const rawName = user?.name || user?.email?.split('@')[0] || '';
  const displayName = rawName.charAt(0).toUpperCase() + rawName.slice(1);

  const links = NAV_LINKS.filter((l) => !l.adminOnly || user?.is_admin);

  return (
    <>
      {/* Phones: hamburger + side drawer */}
      <MobileNav />

      {/* Tablet / desktop: full header bar */}
      <header className="sticky top-0 z-50 hidden border-b border-border bg-background md:block">
        <div className="mx-auto flex h-[62px] max-w-7xl items-center justify-between px-5">
          {/* Left: brand + nav */}
          <div className="flex items-center gap-8">
            <Link
              href="/"
              className="font-heading text-3xl leading-none font-semibold text-foreground"
            >
              AlcOpt
            </Link>

            <nav className="flex items-center gap-6 text-[0.9375rem]">
              {links.map((l) => {
                const active = isActivePath(pathname, l.href);
                return (
                  <Link
                    key={l.href}
                    href={l.href}
                    aria-current={active ? 'page' : undefined}
                    className={cn(
                      // Full-height link so the gold underline sits on the header rule.
                      '-mb-px flex h-[62px] items-center border-b-2 transition-colors hover:text-foreground',
                      active
                        ? 'border-accent text-foreground'
                        : 'border-transparent text-muted-foreground',
                    )}
                  >
                    {l.label}
                  </Link>
                );
              })}
            </nav>
          </div>

          {/* Right: auth */}
          <div className="flex items-center">
            {loading ? null : user ? (
              <Popover>
                <PopoverTrigger
                  className="inline-flex items-center gap-2 rounded-md px-2.5 py-1.5 text-sm text-muted-foreground hover:bg-muted hover:text-foreground transition-colors cursor-pointer"
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
              <Button onClick={() => login()}>Login</Button>
            )}
          </div>
        </div>
      </header>
    </>
  );
}
