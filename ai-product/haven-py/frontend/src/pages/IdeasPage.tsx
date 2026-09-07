import { useCallback, useEffect, useMemo, useState } from 'react';
import { AnimatePresence } from 'framer-motion';
import IdeaInput from '../features/ideas/components/IdeaInput';
import IdeaItem from '../features/ideas/components/IdeaItem';
import { fetchIdeas, type Idea } from '../api/ideas';
import { ApiError } from '../api/client';

export default function IdeasPage() {
  const [ideas, setIdeas] = useState<Idea[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const stars = useMemo(
    () =>
      Array.from({ length: 25 }, () => ({
        top: Math.random() * 50,
        left: Math.random() * 100,
        size: Math.random() * 2 + 1,
        delay: Math.random() * 4,
      })),
    []
  );

  const refresh = useCallback(async () => {
    try {
      const data = await fetchIdeas();
      setIdeas(data);
      setError('');
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) {
        setError('登录已失效，请重新登录');
      } else {
        console.error('刷新失败', e);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return (
    <div className="ideas-page">
      {stars.map((s, i) => (
        <span
          key={`s-${i}`}
          className="ideas-star"
          style={{
            top: `${s.top}%`,
            left: `${s.left}%`,
            width: s.size,
            height: s.size,
            animationDelay: `${s.delay}s`,
          }}
        />
      ))}

      <div className="ideas-fire-glow" />

      <div className="ideas-board">
        <h1 className="ideas-title">
          <span className="flame">🔥</span>
          灵感营火
        </h1>
        <p className="ideas-subtitle">围炉夜话，记下每一闪而过的念头</p>

        <IdeaInput onAdded={refresh} />

        {error && <div className="login-error">{error}</div>}

        {!loading && ideas.length === 0 && !error ? (
          <div className="ideas-empty">
            <span className="lantern">🏮</span>
            <p style={{ marginTop: 16, fontSize: 17, fontWeight: 600 }}>
              夜空很静，还没人留下想法
            </p>
            <p style={{ marginTop: 4, fontSize: 13, opacity: 0.6 }}>在上方写下第一个念头吧</p>
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
