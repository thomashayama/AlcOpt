import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const protectedPaths = ['/tasting', '/brew', '/bottles', '/labels'];

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const token = request.cookies.get('token');

  const isProtected = protectedPaths.some(
    (p) => pathname === p || pathname.startsWith(`${p}/`),
  );

  if (isProtected && !token) {
    return NextResponse.redirect(new URL('/', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/tasting/:path*', '/brew/:path*', '/bottles/:path*', '/labels/:path*'],
};
