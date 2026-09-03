import { NextRequest, NextResponse } from 'next/server';
import { verifyToken } from '@/lib/auth';

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  // 放行登录相关路径
  if (pathname === '/login' || pathname.startsWith('/api/auth/')) {
    return NextResponse.next();
  }

  // 其余页面验证 session
  const token = req.cookies.get('session')?.value ?? '';
  if (verifyToken(token)) {
    return NextResponse.next();
  }

  // 未登录
  if (req.method === 'GET') {
    return NextResponse.redirect(new URL('/login', req.url));
  }
  return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
}
