import { useRef, useState } from 'react';
import { createIdea } from '../../../api/ideas';

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
    <div className="ideas-input-wrap">
      <input
        ref={inputRef}
        className="ideas-input"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
        placeholder="篝火旁记点什么…"
        disabled={busy}
        maxLength={200}
      />
      <div className="ideas-input-lines" />
      <button
        className="ideas-submit"
        onClick={handleSubmit}
        disabled={busy || !value.trim()}
        title="钉上去"
      >
        {busy ? '…' : '✎'}
      </button>
    </div>
  );
}
