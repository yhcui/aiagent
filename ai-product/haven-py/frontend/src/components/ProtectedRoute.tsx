import { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { fetchIdeas } from '../api/ideas';
import { ApiError } from '../api/client';

/**
 * 路由守卫：用一次轻量接口探测 Cookie 登录态是否有效。
 * 未登录则重定向到 /login。
 */
export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const [state, setState] = useState<'checking' | 'ok' | 'expired'>('checking');

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        await fetchIdeas();
        if (!cancelled) setState('ok');
      } catch (e) {
        if (cancelled) return;
        // 401 表示未登录/已过期；网络错误则放行，交由页面自行报错
        setState(e instanceof ApiError && e.status === 401 ? 'expired' : 'ok');
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (state === 'checking') {
    return (
      <div className="login-scene">
        <div style={{ color: 'rgba(244,228,193,0.6)', fontSize: 15 }}>正在确认身份…</div>
      </div>
    );
  }

  if (state === 'expired') {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return <>{children}</>;
}
