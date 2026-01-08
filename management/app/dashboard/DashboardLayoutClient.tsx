'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { AuthenticatedUser } from '@/lib/auth';

export default function DashboardLayoutClient({
  children,
  pm
}: {
  children: React.ReactNode;
  pm: AuthenticatedUser;
}) {
  const pathname = usePathname();
  const router = useRouter();

  const handleLogout = async () => {
    await fetch('/api/auth/logout', { method: 'POST' });
    router.push('/');
  };

  return (
    <div className="min-h-screen noise-overlay" style={{ background: 'var(--background)' }}>
      {/* Gradient background overlay */}
      <div
        className="fixed inset-0 opacity-30 pointer-events-none"
        style={{
          background: 'radial-gradient(circle at 20% 50%, var(--cyan-400) 0%, transparent 50%), radial-gradient(circle at 80% 80%, var(--amber-400) 0%, transparent 50%)',
          filter: 'blur(100px)'
        }}
      />

      {/* Header */}
      <header
        className="glass sticky top-0 z-50 animate-slide-in-up"
        style={{
          borderBottom: '1px solid var(--navy-200)',
          boxShadow: 'var(--shadow-md)'
        }}
      >
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              {/* Logo */}
              <div
                className="clip-corner flex items-center justify-center w-12 h-12"
                style={{
                  background: 'var(--gradient-accent)',
                  boxShadow: 'var(--shadow-lg)'
                }}
              >
                <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <div>
                <h1
                  style={{
                    fontFamily: 'var(--font-display)',
                    fontSize: '1.35rem',
                    fontWeight: '700',
                    color: 'var(--navy-900)',
                    letterSpacing: '-0.02em'
                  }}
                >
                  Project Manager Dashboard
                </h1>
                <p
                  style={{
                    fontSize: '0.8rem',
                    color: 'var(--navy-600)',
                    fontWeight: '500'
                  }}
                >
                  UniOr-PET Translation Management
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div
                className="pl-4"
                style={{ borderLeft: '2px solid var(--cyan-500)' }}
              >
                <div
                  style={{
                    fontSize: '0.7rem',
                    color: 'var(--navy-500)',
                    textTransform: 'uppercase',
                    letterSpacing: '0.08em',
                    fontWeight: '700',
                    fontFamily: 'var(--font-display)'
                  }}
                >
                  Project Manager
                </div>
                <div
                  style={{
                    fontWeight: '600',
                    color: 'var(--navy-900)',
                    fontSize: '0.95rem',
                    fontFamily: 'var(--font-display)'
                  }}
                >
                  {pm.name} {pm.surname}
                </div>
                <div
                  style={{
                    fontSize: '0.7rem',
                    color: 'var(--navy-500)',
                    fontFamily: 'monospace'
                  }}
                >
                  {pm.projectKey}
                </div>
              </div>
              <button
                onClick={handleLogout}
                className="clip-corner px-4 py-2 text-sm font-medium transition-all hover:scale-105"
                style={{
                  color: 'var(--navy-700)',
                  border: '1px solid var(--navy-300)',
                  background: 'white',
                  fontFamily: 'var(--font-display)',
                  fontWeight: '600'
                }}
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="flex relative">
        {/* Sidebar Navigation */}
        <aside
          className="w-72 min-h-[calc(100vh-5rem)] sticky top-20 glass animate-slide-in-right"
          style={{
            borderRight: '1px solid var(--navy-200)',
            boxShadow: 'var(--shadow-sm)'
          }}
        >
          <nav className="p-6 space-y-2">
            <div
              className="mb-6 pb-4"
              style={{ borderBottom: '2px solid var(--navy-100)' }}
            >
              <h3
                style={{
                  fontFamily: 'var(--font-display)',
                  fontSize: '0.75rem',
                  fontWeight: '700',
                  color: 'var(--navy-500)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.1em'
                }}
              >
                Navigation
              </h3>
            </div>

            <NavLink href="/dashboard" icon="chart" active={pathname === '/dashboard'}>
              Dashboard
            </NavLink>
            <NavLink href="/dashboard/users" icon="users" active={pathname === '/dashboard/users'}>
              User Management
            </NavLink>
            <NavLink href="/dashboard/analytics" icon="analytics" active={pathname === '/dashboard/analytics'}>
              Analytics
            </NavLink>
            <NavLink href="/dashboard/export" icon="download" active={pathname === '/dashboard/export'}>
              Export Data
            </NavLink>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-8 relative z-10 animate-slide-in-up" style={{ animationDelay: '100ms' }}>
          {children}
        </main>
      </div>
    </div>
  );
}

function NavLink({ href, icon, children, active }: { href: string; icon: string; children: React.ReactNode; active: boolean }) {
  return (
    <Link
      href={href}
      className="clip-corner flex items-center gap-3 px-4 py-3 text-sm font-medium transition-all group relative overflow-hidden"
      style={{
        color: active ? 'white' : 'var(--navy-700)',
        background: active ? 'var(--gradient-accent)' : 'transparent',
        fontFamily: 'var(--font-display)',
        fontWeight: '600',
        boxShadow: active ? 'var(--shadow-md)' : 'none'
      }}
      onMouseEnter={(e) => {
        if (!active) {
          e.currentTarget.style.background = 'var(--navy-50)';
          e.currentTarget.style.transform = 'translateX(4px)';
        }
      }}
      onMouseLeave={(e) => {
        if (!active) {
          e.currentTarget.style.background = 'transparent';
          e.currentTarget.style.transform = 'translateX(0)';
        }
      }}
    >
      {/* Active indicator */}
      {active && (
        <div
          className="absolute left-0 top-0 bottom-0 w-1"
          style={{ background: 'var(--amber-400)' }}
        />
      )}

      <div className={active ? 'text-white' : 'transition-colors'} style={{ color: active ? 'white' : 'var(--cyan-600)' }}>
        {icon === 'chart' && (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        )}
        {icon === 'users' && (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
        )}
        {icon === 'analytics' && (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        )}
        {icon === 'download' && (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
        )}
      </div>
      <span>{children}</span>
    </Link>
  );
}
