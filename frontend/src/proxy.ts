import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const backendUrl = process.env.BACKEND_URL ?? 'http://localhost:8000';

const protectedPaths = ['/tasting', '/brew', '/bottles', '/labels'];

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Proxy /api/* and /auth/* to the backend at runtime
  if (pathname.startsWith('/api/') || pathname.startsWith('/auth/')) {
    const url = new URL(
      `${pathname}${request.nextUrl.search}`,
      backendUrl,
    );
    return NextResponse.rewrite(url);
  }

  // Redirect unauthenticated users away from protected pages
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
  matcher: [
    '/api/:path*',
    '/auth/:path*',
    '/tasting/:path*',
    '/brew/:path*',
    '/bottles/:path*',
    '/labels/:path*',
  ],
};
