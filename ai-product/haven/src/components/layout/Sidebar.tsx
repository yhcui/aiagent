'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useState } from 'react';

const navItems = [
  { href: '/', label: '首页', icon: '🏠' },
  { href: '/ideas', label: '想法', icon: '🔥' },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [loggingOut, setLoggingOut] = useState(false);

  async function handleLogout() {
    if (loggingOut) return;
    setLoggingOut(true);
    try {
      await fetch('/api/auth/logout', { method: 'POST' });
      router.push('/login');
      router.refresh();
    } catch {
      setLoggingOut(false);
    }
  }

  return (
    <aside className="sidebar-camp">
      {/* 顶部挂灯 */}
      <div className="camp-lantern">
        <div className="camp-lantern-rope" />
        <div className="camp-lantern-bulb" />
      </div>

      {/* Logo */}
      <Link href="/" className="camp-logo">
        <span className="camp-logo-badge">🏠</span>
        <span className="camp-logo-text">Haven</span>
      </Link>

      {/* 导航路标 */}
      <nav className="camp-nav">
        {navItems.map(({ href, label, icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={`camp-nav-item ${active ? 'active' : ''}`}
              title={label}
            >
              <span className="camp-icon">{icon}</span>
              <span className="camp-label">{label}</span>
            </Link>
          );
        })}
      </nav>

      {/* 离营 */}
      <button
        onClick={handleLogout}
        disabled={loggingOut}
        className="camp-exit"
        title="离开营地"
      >
        <span className="camp-icon">🚪</span>
        <span className="camp-label">{loggingOut ? '收拾中…' : '离营'}</span>
      </button>

      <div className="camp-version">避风港 v0.2</div>
    </aside>
  );
}
