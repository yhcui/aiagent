import { api } from './client';

export interface Idea {
  id: number;
  content: string;
  is_completed: number;
  created_at: string;
  completed_at: string | null;
}

export const fetchIdeas = () => api.get<Idea[]>('/ideas');

export const createIdea = (content: string) =>
  api.post<Idea>('/ideas', { content });

export const toggleIdea = (id: number) => api.patch<{ ok: boolean }>(`/ideas/${id}`);

export const deleteIdea = (id: number) => api.del<{ ok: boolean }>(`/ideas/${id}`);
