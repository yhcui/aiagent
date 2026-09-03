import { getDb } from '@/lib/db';
import { ideas } from '@/lib/db/schema';
import { eq, desc } from 'drizzle-orm';
import type { NewIdea } from '@/lib/db/schema';

/** 查询所有 idea（未完成在前，已完成在后） */
export async function getAllIdeas() {
  const { db } = await getDb();
  return db.select().from(ideas).orderBy(
    ideas.isCompleted,
    desc(ideas.createdAt)
  );
}

/** 创建新 idea */
export async function createIdea(data: NewIdea) {
  const { db } = await getDb();
  const [row] = await db.insert(ideas).values(data).returning();
  return row;
}

/** 切换完成状态 */
export async function toggleIdeaComplete(id: number) {
  const { db } = await getDb();
  const rows = await db.select().from(ideas).where(eq(ideas.id, id));
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

  return { ...existing, isCompleted: newCompleted, completedAt: newCompleted ? now : null };
}

/** 删除 idea */
export async function deleteIdea(id: number) {
  const { db } = await getDb();
  await db.delete(ideas).where(eq(ideas.id, id));
}
