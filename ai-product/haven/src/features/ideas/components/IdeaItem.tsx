'use client';

import { motion } from 'framer-motion';
import { Check, Trash2, Circle } from 'lucide-react';
import { toggleIdea, deleteIdea } from '../api';
import type { Idea } from '@/lib/db';

interface Props {
  idea: Idea;
  onChanged: () => void;
}

export default function IdeaItem({ idea, onChanged }: Props) {
  const handleToggle = async () => {
    try {
      await toggleIdea(idea.id);
      onChanged();
    } catch (e) {
      console.error('操作失败', e);
    }
  };

  const handleDelete = async () => {
    try {
      await deleteIdea(idea.id);
      onChanged();
    } catch (e) {
      console.error('删除失败', e);
    }
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: -40 }}
      transition={{ duration: 0.2 }}
      className={`group bg-white rounded-2xl shadow-sm p-4 flex gap-3 items-start transition-shadow hover:shadow-md ${
        idea.is_completed ? 'opacity-60' : ''
      }`}
    >
      {/* 完成按钮 */}
      <button
        onClick={handleToggle}
        className={`flex-shrink-0 mt-0.5 w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all ${
          idea.is_completed
            ? 'border-haven-success bg-haven-success text-white'
            : 'border-haven-muted hover:border-haven-primary'
        }`}
      >
        {idea.is_completed ? <Check size={14} /> : <Circle size={14} className="fill-transparent" />}
      </button>

      {/* 内容 */}
      <p
        className={`flex-1 text-base leading-relaxed break-words ${
          idea.is_completed ? 'line-through text-haven-muted' : 'text-haven-text'
        }`}
      >
        {idea.content}
      </p>

      {/* 删除按钮 */}
      <button
        onClick={handleDelete}
        className="flex-shrink-0 opacity-0 group-hover:opacity-100 p-1.5 rounded-lg text-haven-muted hover:text-red-500 hover:bg-red-50 transition-all"
      >
        <Trash2 size={16} />
      </button>
    </motion.div>
  );
}
