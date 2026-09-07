import { api } from './client';

export const login = (username: string, password: string) =>
  api.post<{ ok: boolean }>('/auth/login', { username, password });

export const logout = () => api.post<{ ok: boolean }>('/auth/logout');
