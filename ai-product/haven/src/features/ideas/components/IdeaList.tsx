'use client';

import { useState, useEffect, useCallback } from 'react';
import { AnimatePresence } from 'framer-motion';
import { Lightbulb } from 'lucide-react';
import IdeaInput from './IdeaInput';
import IdeaItem from './IdeaItem';
import { fetchIdeas } from '../api';
import type { Idea } from '@/lib/db';

interface Props {
  initialIdeas: Idea[];
}

export default function IdeaList({ initialIdeas }: Props) {
  const [ideas, setIdeas] = useState<Idea[]>(initialIdeas);

  const refresh = useCallback(async () => {
    try {
      const latest = await fetchIdeas();
      setIdeas(latest);
    } catch (e) {
      console.error('刷新失败', e);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const isEmpty = ideas.length === 0;

  return (
    <div className="space-y-3">
      <IdeaInput onAdded={refresh} />

      {isEmpty && (
        <div className="text-center py-16">
          <Lightbulb size={48} className="mx-auto mb-4 text-haven-primary opacity-50" />
          <p className="text-haven-muted text-lg">记下第一个想法吧 ✨</p>
        </div>
      )}

      <AnimatePresence>
        {ideas.map((idea) => (
          <IdeaItem key={idea.id} idea={idea} onChanged={refresh} />
        ))}
      </AnimatePresence>
    </div>
  );
}
