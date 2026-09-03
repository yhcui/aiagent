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

  // node:sqlite 返回的对象带特殊原型，需序列化为纯对象才能传给 Client Component
  const initialIdeas = JSON.parse(JSON.stringify(rows)) as Idea[];

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-haven-text">💡 想法</h1>
        <p className="text-haven-muted mt-1">捕捉灵感，让想法不再溜走</p>
      </header>
      <IdeaList initialIdeas={initialIdeas} />
    </div>
  );
}
