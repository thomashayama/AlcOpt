'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Drawer } from '@base-ui/react/drawer';
import { LogOut, Menu, X } from 'lucide-react';
import { useAuth } from '@/components/AuthProvider';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { NAV_LINKS, isActivePath } from '@/lib/nav';
import { cn } from '@/lib/utils';

/**
 * Phone navigation: a floating hamburger in the top-left that opens a
 * left-side drawer holding everything the desktop header shows.
 * Swipe left (or tap the backdrop / X) to dismiss.
 */
export function MobileNav() {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();
  const { user, loading, login, logout } = useAuth();

  const links = NAV_LINKS.filter((l) => !l.adminOnly || user?.is_admin);
  const mainLinks = links.filter((l) => !l.adminOnly);
  const adminLinks = links.filter((l) => l.adminOnly);

  const rawName = user?.name || user?.email?.split('@')[0] || '';
  const displayName = rawName.charAt(0).toUpperCase() + rawName.slice(1);

  const close = () => setOpen(false);

  const renderLink = (href: string, label: string) => {
    const active = isActivePath(pathname, href);
    return (
      <Link
        key={href}
        href={href}
        onClick={close}
        aria-current={active ? 'page' : undefined}
        className={cn(
          'flex h-11 items-center rounded-lg px-3 text-base transition-colors',
          active
            ? 'bg-sidebar-accent font-medium text-sidebar-foreground shadow-[inset_3px_0_0_var(--sidebar-primary)]'
            : 'text-muted-foreground hover:bg-sidebar-accent/60 hover:text-sidebar-foreground',
        )}
      >
        {label}
      </Link>
    );
  };

  return (
    // Transparent sticky strip: reserves space at the top on first paint and
    // keeps the button reachable while scrolling, without blocking taps on
    // the content beneath it.
    <div className="pointer-events-none sticky top-0 z-40 flex h-14 items-center px-3 md:hidden">
      <Drawer.Root open={open} onOpenChange={setOpen} swipeDirection="left">
        <Drawer.Trigger
          aria-label="Open menu"
          className="pointer-events-auto inline-flex size-10 items-center justify-center rounded-lg bg-[#262730]/90 text-foreground shadow-md ring-1 ring-foreground/10 backdrop-blur transition-colors hover:bg-[#262730] focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
        >
          <Menu className="size-5" />
        </Drawer.Trigger>

        <Drawer.Portal>
          <Drawer.Backdrop className="fixed inset-0 z-50 bg-black/60 transition-opacity duration-300 data-ending-style:opacity-0 data-starting-style:opacity-0" />
          <Drawer.Viewport className="fixed inset-0 z-50 flex">
            <Drawer.Popup
              className={cn(
                'flex h-full w-72 max-w-[85vw] flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground shadow-2xl outline-none',
                'translate-x-[var(--drawer-swipe-movement-x,0px)] transition-transform duration-300 ease-[cubic-bezier(0.32,0.72,0,1)]',
                'data-swiping:duration-0',
                'data-starting-style:-translate-x-full',
                'data-ending-style:-translate-x-full data-ending-style:duration-[calc(var(--drawer-swipe-strength,1)*300ms)]',
              )}
            >
              <Drawer.Content className="flex min-h-0 flex-1 flex-col">
                {/* Brand + close */}
                <div className="flex h-14 shrink-0 items-center justify-between border-b border-sidebar-border pr-2 pl-4">
                  <Drawer.Title
                    render={
                      <Link href="/" onClick={close} className="text-lg font-bold">
                        AlcOpt
                      </Link>
                    }
                  />
                  <Drawer.Close
                    aria-label="Close menu"
                    className="inline-flex size-10 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-sidebar-accent hover:text-sidebar-foreground"
                  >
                    <X className="size-5" />
                  </Drawer.Close>
                </div>

                {/* Links */}
                <nav className="flex-1 space-y-1 overflow-y-auto p-3">
                  {renderLink('/', 'Dashboard')}
                  {mainLinks.map((l) => renderLink(l.href, l.label))}
                  {adminLinks.length > 0 && (
                    <>
                      <p className="px-3 pt-4 pb-1 text-xs font-medium tracking-wide text-muted-foreground uppercase">
                        Admin
                      </p>
                      {adminLinks.map((l) => renderLink(l.href, l.label))}
                    </>
                  )}
                </nav>

                {/* Account */}
                <div className="shrink-0 border-t border-sidebar-border p-4 pb-[max(1rem,env(safe-area-inset-bottom))]">
                  {loading ? null : user ? (
                    <div className="space-y-3">
                      <div className="flex min-w-0 items-center gap-3">
                        <Avatar className="size-10">
                          <AvatarImage src={user.picture} alt={user.email} />
                          <AvatarFallback>{displayName.slice(0, 2).toUpperCase()}</AvatarFallback>
                        </Avatar>
                        <div className="min-w-0">
                          <p className="truncate text-sm font-medium">{displayName}</p>
                          <p className="truncate text-xs text-muted-foreground">{user.email}</p>
                        </div>
                      </div>
                      <Button
                        variant="outline"
                        className="h-10 w-full"
                        onClick={() => {
                          close();
                          logout();
                        }}
                      >
                        <LogOut className="size-4" />
                        Sign Out
                      </Button>
                    </div>
                  ) : (
                    <Button className="h-10 w-full" onClick={() => login()}>
                      Login
                    </Button>
                  )}
                </div>
              </Drawer.Content>
            </Drawer.Popup>
          </Drawer.Viewport>
        </Drawer.Portal>
      </Drawer.Root>
    </div>
  );
}
