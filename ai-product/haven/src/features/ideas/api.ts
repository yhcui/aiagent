import type { Idea } from '@/lib/db';

export async function fetchIdeas(): Promise<Idea[]> {
  const res = await fetch('/api/ideas', { cache: 'no-store' });
  if (!res.ok) throw new Error('获取失败');
  return res.json();
}

export async function createIdea(content: string): Promise<void> {
  const res = await fetch('/api/ideas', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content }),
  });
  if (!res.ok) throw new Error('创建失败');
}

export async function toggleIdea(id: number): Promise<void> {
  const res = await fetch('/api/ideas', {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id }),
  });
  if (!res.ok) throw new Error('操作失败');
}

export async function deleteIdea(id: number): Promise<void> {
  const res = await fetch('/api/ideas', {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id }),
  });
  if (!res.ok) throw new Error('删除失败');
}
