import IdeaList from '@/features/ideas/components/IdeaList';
import { getDb, Idea } from '@/lib/db';

export const dynamic = 'force-dynamic';

export default async function IdeasPage() {
  const db = getDb();
  const rows = db.prepare(
    `SELECT id, content, is_completed, created_at, completed_at
     FROM ideas
     ORDER BY is_completed ASC, created_at DESC`
  ).all() as unknown[];

  const initialIdeas = JSON.parse(JSON.stringify(rows)) as Idea[];

  return <IdeaList initialIdeas={initialIdeas} />;
}
