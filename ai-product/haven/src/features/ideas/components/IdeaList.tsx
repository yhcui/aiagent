'use client';

import { useState, useEffect, useCallback } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import IdeaInput from './IdeaInput';
import IdeaItem from './IdeaItem';
import { fetchIdeas } from '../api';
import type { Idea } from '@/lib/db';

interface Props {
  initialIdeas: Idea[];
}

// 稀疏背景星星
const STARS = Array.from({ length: 25 }, () => ({
  top: Math.random() * 50,
  left: Math.random() * 100,
  size: Math.random() * 2 + 1,
  delay: Math.random() * 4,
}));

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
    <div className="ideas-page">
      {/* 星空 */}
      {STARS.map((s, i) => (
        <span
          key={`s-${i}`}
          className="ideas-star"
          style={{ top: `${s.top}%`, left: `${s.left}%`, width: s.size, height: s.size, animationDelay: `${s.delay}s` }}
        />
      ))}
      {/* 篝火光晕 */}
      <div className="ideas-fire-glow" />

      <div className="ideas-board">
        <h1 className="ideas-title">
          <span className="flame">🔥</span>
          灵感营火
        </h1>
        <p className="ideas-subtitle">围炉夜话，记下每一闪而过的念头</p>

        <IdeaInput onAdded={refresh} />

        {isEmpty ? (
          <div className="ideas-empty">
            <span className="lantern">🏮</span>
            <p style={{ marginTop: 16, fontSize: 17, fontWeight: 600 }}>
              夜空很静，还没人留下想法
            </p>
            <p style={{ marginTop: 4, fontSize: 13, opacity: 0.6 }}>
              在上方写下第一个念头吧
            </p>
          </div>
        ) : (
          <AnimatePresence>
            {ideas.map((idea, i) => (
              <IdeaItem key={idea.id} idea={idea} index={i} onChanged={refresh} />
            ))}
          </AnimatePresence>
        )}
      </div>
    </div>
  );
}
