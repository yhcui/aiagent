'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';

// 生成星星
function useStars(count: number) {
  const [stars, setStars] = useState<{ top: number; left: number; size: number; delay: number }[]>([]);
  useEffect(() => {
    setStars(
      Array.from({ length: count }, () => ({
        top: Math.random() * 60,
        left: Math.random() * 100,
        size: Math.random() * 2 + 1,
        delay: Math.random() * 3,
      }))
    );
  }, [count]);
  return stars;
}

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [opening, setOpening] = useState(false);
  const [shake, setShake] = useState(false);
  const houseRef = useRef<HTMLDivElement>(null);

  const stars = useStars(40);
  const fireflies = useStars(12);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();
      if (res.ok && data.ok) {
        // 门打开动画，再跳转
        setLoading(false);
        setOpening(true);
        setTimeout(() => {
          router.push('/');
          router.refresh();
        }, 900);
      } else {
        setError(data.error || '敲错门啦');
        triggerShake();
      }
    } catch {
      setError('门外风太大，没听见');
      triggerShake();
    } finally {
      setLoading(false);
    }
  }

  function triggerShake() {
    setShake(true);
    setTimeout(() => setShake(false), 500);
  }

  return (
    <div className="login-scene">
      {/* 星空 */}
      {stars.map((s, i) => (
        <span
          key={`star-${i}`}
          className="login-star"
          style={{ top: `${s.top}%`, left: `${s.left}%`, width: s.size, height: s.size, animationDelay: `${s.delay}s` }}
        />
      ))}

      {/* 月亮 */}
      <div className="login-moon" />

      {/* 萤火虫 */}
      {fireflies.map((f, i) => (
        <span
          key={`fly-${i}`}
          className="login-firefly"
          style={{ top: `${40 + f.top / 3}%`, left: `${f.left}%`, animationDelay: `${f.delay}s`, animationDuration: `${6 + f.delay}s` }}
        />
      ))}

      {/* 草地 */}
      <div className="login-grass" />

      {/* 小屋 */}
      <div className={`login-house ${shake ? 'login-shake' : ''}`} ref={houseRef}>
        <div className="login-roof">
          <div className="login-chimney">
            <div className="login-smoke">
              <span /><span /><span />
            </div>
          </div>
        </div>

        <div className="login-wall">
          <div className="login-window">
            <div className="login-cat">
              <div className="login-cat-eye left" />
              <div className="login-cat-eye right" />
            </div>
          </div>
          <div className="login-window" />
        </div>

        {/* 门 = 登录表单 */}
        <div
          className="login-door-wrap"
          style={{
            transform: opening ? 'perspective(800px) rotateY(-105deg)' : 'perspective(800px) rotateY(0deg)',
            transition: 'transform 0.9s cubic-bezier(0.4, 0, 0.2, 1)',
            transformOrigin: 'left center',
          }}
        >
          <div className="login-door">
            <div className="login-sign">Haven · 避风港</div>
            <div className="login-knob" />

            <h1>Haven</h1>
            <p className="tagline">咚咚咚 — 敲敲门，回家 🚪</p>

            <form onSubmit={handleLogin}>
              <div style={{ marginBottom: 14 }}>
                <label>访客姓名</label>
                <input
                  type="text"
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                  placeholder="谁在外面呀？"
                  autoComplete="username"
                />
              </div>

              <div>
                <label>暗号</label>
                <input
                  type="password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="说对了门才开"
                  autoComplete="current-password"
                />
              </div>

              {error && <div className="login-error">{error}</div>}

              <button type="submit" disabled={loading || opening}>
                {loading ? (
                  <>
                    <svg className="animate-spin" width="18" height="18" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    正在开门…
                  </>
                ) : opening ? (
                  '欢迎回家 ✨'
                ) : (
                  '敲门进屋'
                )}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
