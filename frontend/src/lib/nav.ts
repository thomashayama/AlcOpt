export interface NavLink {
  href: string;
  label: string;
  adminOnly?: boolean;
}

export const NAV_LINKS: NavLink[] = [
  { href: '/tasting', label: 'Tasting' },
  { href: '/info', label: 'Info' },
  { href: '/brew', label: 'Brew', adminOnly: true },
  { href: '/bottles', label: 'Bottles', adminOnly: true },
  { href: '/labels', label: 'Labels', adminOnly: true },
];

export function isActivePath(pathname: string, href: string): boolean {
  return pathname === href || pathname.startsWith(`${href}/`);
}
