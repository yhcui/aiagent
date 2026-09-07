import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { logout } from '../../api/auth';

const navItems = [
  { href: '/ideas', label: '想法', icon: '🔥' },
];

export default function Sidebar() {
  const location = useLocation();
  const navigate = useNavigate();
  const [loggingOut, setLoggingOut] = useState(false);

  const handleLogout = async () => {
    if (loggingOut) return;
    setLoggingOut(true);
    try {
      await logout();
    } catch (e) {
      console.error('登出失败', e);
    } finally {
      navigate('/login', { replace: true });
    }
  };

  return (
    <aside className="sidebar-camp">
      <div className="camp-lantern">
        <div className="camp-lantern-rope" />
        <div className="camp-lantern-bulb" />
      </div>

      <a href="/ideas" className="camp-logo">
        <span className="camp-logo-badge">🏠</span>
        <span className="camp-logo-text">Haven</span>
      </a>

      <nav className="camp-nav">
        {navItems.map(({ href, label, icon }) => {
          const active = location.pathname === href;
          return (
            <a
              key={href}
              href={href}
              className={`camp-nav-item ${active ? 'active' : ''}`}
              title={label}
              onClick={(e) => {
                e.preventDefault();
                navigate(href);
              }}
            >
              <span className="camp-icon">{icon}</span>
              <span className="camp-label">{label}</span>
            </a>
          );
        })}
      </nav>

      <button onClick={handleLogout} disabled={loggingOut} className="camp-exit" title="离开营地">
        <span className="camp-icon">🚪</span>
        <span className="camp-label">{loggingOut ? '收拾中…' : '离营'}</span>
      </button>

      <div className="camp-version">避风港 v1.0</div>
    </aside>
  );
}
