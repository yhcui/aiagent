import { NextRequest, NextResponse } from 'next/server';
import { verifyCredentials, createToken } from '@/lib/auth';

export const dynamic = 'force-dynamic';

/** POST: 登录 */
export async function POST(req: NextRequest) {
  try {
    const { username, password } = await req.json();

    if (verifyCredentials(username, password)) {
      const token = createToken();

      const res = NextResponse.json({ ok: true });
      res.cookies.set('session', token, {
        httpOnly: true,
        sameSite: 'lax',
        maxAge: 7 * 24 * 60 * 60,
        path: '/',
      });
      return res;
    }

    return NextResponse.json({ error: '用户名或密码错误' }, { status: 401 });
  } catch (err) {
    console.error('[API] POST /api/auth/login error:', err);
    return NextResponse.json({ error: String(err) }, { status: 500 });
  }
}
