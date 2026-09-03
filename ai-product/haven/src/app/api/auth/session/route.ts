import { NextRequest, NextResponse } from 'next/server';
import { getDb } from '@/lib/db';

export const dynamic = 'force-dynamic';

/** GET: 验证 session 是否有效 */
export async function GET(req: NextRequest) {
  const token = req.cookies.get('session')?.value;
  if (!token) {
    return NextResponse.json({ authenticated: false });
  }

  const db = getDb();
  const row = db.prepare('SELECT * FROM sessions WHERE id = ?').get(token) as { expires_at: string } | undefined;

  if (!row || new Date(row.expires_at) < new Date()) {
    if (row) {
      db.prepare('DELETE FROM sessions WHERE id = ?').run(token);
    }
    return NextResponse.json({ authenticated: false });
  }

  return NextResponse.json({ authenticated: true });
}
