import { NextRequest, NextResponse } from 'next/server';
import { getDb, Idea } from '@/lib/db';

export const dynamic = 'force-dynamic';

function toPlain(rows: unknown[]): Idea[] {
  return JSON.parse(JSON.stringify(rows)) as Idea[];
}

/** GET: 获取所有 idea（未完成在前，已完成在后） */
export async function GET() {
  try {
    const db = getDb();
    const rows = db.prepare(
      `SELECT id, content, is_completed, created_at, completed_at
       FROM ideas
       ORDER BY is_completed ASC, created_at DESC`
    ).all() as unknown[];
    return NextResponse.json(toPlain(rows));
  } catch (err) {
    console.error('[API] GET /api/ideas error:', err);
    return NextResponse.json({ error: String(err) }, { status: 500 });
  }
}

/** POST: 创建新 idea */
export async function POST(req: NextRequest) {
  try {
    const { content } = await req.json();
    if (!content?.trim()) {
      return NextResponse.json({ error: '内容不能为空' }, { status: 400 });
    }
    const db = getDb();
    db.prepare(
      'INSERT INTO ideas (content, created_at) VALUES (?, ?)'
    ).run(content.trim(), new Date().toISOString());
    return NextResponse.json({ ok: true });
  } catch (err) {
    console.error('[API] POST /api/ideas error:', err);
    return NextResponse.json({ error: String(err) }, { status: 500 });
  }
}

/** PATCH: 切换完成状态 */
export async function PATCH(req: NextRequest) {
  try {
    const { id } = await req.json();
    if (!id) return NextResponse.json({ error: '缺少 id' }, { status: 400 });

    const db = getDb();
    const row = db.prepare('SELECT * FROM ideas WHERE id = ?').get(id) as Idea | undefined;
    if (!row) return NextResponse.json({ error: 'Idea 不存在' }, { status: 404 });

    const newCompleted = !row.is_completed;
    db.prepare(
      'UPDATE ideas SET is_completed = ?, completed_at = ? WHERE id = ?'
    ).run(newCompleted ? 1 : 0, newCompleted ? new Date().toISOString() : null, id);

    return NextResponse.json({ ok: true });
  } catch (err) {
    console.error('[API] PATCH /api/ideas error:', err);
    return NextResponse.json({ error: String(err) }, { status: 500 });
  }
}

/** DELETE: 删除 idea */
export async function DELETE(req: NextRequest) {
  try {
    const { id } = await req.json();
    if (!id) return NextResponse.json({ error: '缺少 id' }, { status: 400 });

    const db = getDb();
    db.prepare('DELETE FROM ideas WHERE id = ?').run(id);
    return NextResponse.json({ ok: true });
  } catch (err) {
    console.error('[API] DELETE /api/ideas error:', err);
    return NextResponse.json({ error: String(err) }, { status: 500 });
  }
}
