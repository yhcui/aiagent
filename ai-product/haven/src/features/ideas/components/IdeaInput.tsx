'use client';

import { useState, useRef } from 'react';
import { Plus, Sparkles } from 'lucide-react';
import { createIdea } from '../api';

interface Props {
  onAdded: () => void;
}

export default function IdeaInput({ onAdded }: Props) {
  const [value, setValue] = useState('');
  const [busy, setBusy] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = async () => {
    const content = value.trim();
    if (!content || busy) return;
    setBusy(true);
    try {
      await createIdea(content);
      setValue('');
      onAdded();
    } catch (e) {
      console.error('添加失败', e);
    } finally {
      setBusy(false);
      inputRef.current?.focus();
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm p-4 flex gap-3 items-center">
      <input
        ref={inputRef}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
        placeholder="记下你的想法..."
        disabled={busy}
        className="flex-1 bg-transparent outline-none text-haven-text placeholder:text-haven-muted text-base"
      />
      <button
        onClick={handleSubmit}
        disabled={busy || !value.trim()}
        className="flex-shrink-0 w-10 h-10 rounded-xl bg-haven-primary hover:bg-opacity-80 text-white flex items-center justify-center transition-all disabled:opacity-40"
      >
        {busy ? (
          <Sparkles size={18} className="animate-spin" />
        ) : (
          <Plus size={18} />
        )}
      </button>
    </div>
  );
}
