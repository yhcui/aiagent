'use server';

import { getDb, persist } from '@/lib/db';
import { ideas } from '@/lib/db/schema';
import { eq, desc } from 'drizzle-orm';
import type { NewIdea } from '@/lib/db/schema';

/** 查询所有 idea（未完成在前，已完成在后） */
export async function getIdeas() {
  try {
    const db = await getDb();
    const rows = db.select().from(ideas).orderBy(
      ideas.isCompleted,
      desc(ideas.createdAt)
    );
    console.log('[ACTION] getIdeas count:', rows.length);
    return rows;
  } catch (err) {
    console.error('[ACTION] getIdeas ERROR:', err);
    throw err;
  }
}

/** 创建新 idea */
export async function addIdea(content: string) {
  if (!content.trim()) throw new Error('内容不能为空');
  try {
    console.log('[ACTION] addIdea start:', content);
    const db = await getDb();
    console.log('[ACTION] db ready');
    const data: NewIdea = { content: content.trim() };
    await db.insert(ideas).values(data);
    console.log('[ACTION] insert done');
    persist();
    console.log('[ACTION] persist done');
  } catch (err) {
    console.error('[ACTION] addIdea ERROR:', err);
    throw err;
  }
}

/** 切换完成状态 */
export async function toggleIdeaComplete(id: number) {
  const db = await getDb();
  const rows = db.select().from(ideas).where(eq(ideas.id, id));
  if (!rows.length) throw new Error(`Idea ${id} not found`);

  const existing = rows[0];
  const now = new Date().toISOString();
  const newCompleted = !existing.isCompleted;

  await db.update(ideas)
    .set({
      isCompleted: newCompleted,
      completedAt: newCompleted ? now : null,
    })
    .where(eq(ideas.id, id));

  persist();
}

/** 删除 idea */
export async function removeIdea(id: number) {
  const db = await getDb();
  await db.delete(ideas).where(eq(ideas.id, id));
  persist();
}
