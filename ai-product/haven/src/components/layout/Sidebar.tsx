'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { Lightbulb, Home, LogOut } from 'lucide-react';
import { useState } from 'react';

const navItems = [
  { href: '/', label: '首页', icon: Home },
  { href: '/ideas', label: '想法', icon: Lightbulb },
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
    <aside className="w-16 lg:w-56 bg-white border-r border-gray-100 flex flex-col items-center lg:items-stretch py-6 px-2 lg:px-4 gap-2 shrink-0">
      {/* Logo */}
      <Link href="/" className="flex items-center justify-center lg:justify-start gap-2 mb-8 px-2">
        <span className="text-2xl">🏠</span>
        <span className="hidden lg:block text-lg font-semibold text-haven-text">Haven</span>
      </Link>

      {/* 导航 */}
      <nav className="flex flex-col gap-1 flex-1">
        {navItems.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center justify-center lg:justify-start gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                active
                  ? 'bg-haven-primary bg-opacity-10 text-haven-primary'
                  : 'text-haven-muted hover:bg-gray-50 hover:text-haven-text'
              }`}
            >
              <Icon size={20} />
              <span className="hidden lg:inline">{label}</span>
            </Link>
          );
        })}
      </nav>

      {/* 登出 */}
      <button
        onClick={handleLogout}
        disabled={loggingOut}
        className="flex items-center justify-center lg:justify-start gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-haven-muted hover:bg-red-50 hover:text-red-500 transition disabled:opacity-60"
        title="退出登录"
      >
        <LogOut size={20} />
        <span className="hidden lg:inline">{loggingOut ? '退出中...' : '退出'}</span>
      </button>

      {/* 底部装饰 */}
      <div className="hidden lg:block text-xs text-haven-muted text-center py-2">
        个人工作台 v0.2
      </div>
    </aside>
  );
}
