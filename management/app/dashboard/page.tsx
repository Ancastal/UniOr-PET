'use client';

import { useEffect, useState } from 'react';

interface ProjectStats {
  totalTranslators: number;
  totalSegments: number;
  completedSegments: number;
  projectCreated: string;
  sourceFile: string;
  translationFile: string;
  dbType: string;
}

interface TranslatorActivity {
  name: string;
  surname: string;
  segmentsCompleted: number;
  totalEditTime: number;
  insertions: number;
  deletions: number;
  status: string;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<ProjectStats | null>(null);
  const [activity, setActivity] = useState<TranslatorActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await fetch('/api/dashboard/stats');
      if (response.ok) {
        const data = await response.json();
        setStats(data.stats);
        setActivity(data.activity);
      } else {
        setError('Failed to load dashboard data');
      }
    } catch (err) {
      setError('Error loading dashboard');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-[var(--navy-200)] border-t-[var(--cyan-500)] rounded-full animate-spin mx-auto mb-4"></div>
          <p style={{ color: 'var(--navy-600)' }} className="text-sm font-medium">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-24">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-lg" style={{ background: 'var(--rose-400)', color: 'white' }}>
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {error}
        </div>
      </div>
    );
  }

  const statsCards = [
    { title: 'Total Translators', value: stats?.totalTranslators.toString() || '0', icon: 'users', color: 'cyan', delay: '0ms' },
    { title: 'Total Segments', value: stats?.totalSegments.toString() || '0', icon: 'document', color: 'amber', delay: '100ms' },
    { title: 'Completed Segments', value: stats?.completedSegments.toString() || '0', icon: 'check', color: 'emerald', delay: '200ms' },
    { title: 'Progress', value: stats ? `${Math.round((stats.completedSegments / stats.totalSegments) * 100)}%` : '0%', icon: 'chart', color: 'cyan', delay: '300ms' },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="animate-slide-in-up">
        <h1 style={{
          fontFamily: 'var(--font-display)',
          color: 'var(--navy-900)',
          fontSize: '2.5rem',
          fontWeight: '700',
          letterSpacing: '-0.02em',
          marginBottom: '0.5rem'
        }}>
          Dashboard
        </h1>
        <p style={{ color: 'var(--navy-600)', fontSize: '0.95rem' }}>
          Real-time overview of your translation project
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        {statsCards.map((stat) => (
          <StatCard
            key={stat.title}
            title={stat.title}
            value={stat.value}
            icon={stat.icon}
            color={stat.color}
            delay={stat.delay}
          />
        ))}
      </div>

      {/* Project Information */}
      {stats && (
        <div
          className="clip-corner-lg noise-overlay animate-scale-in relative overflow-hidden"
          style={{
            background: 'var(--gradient-primary)',
            padding: '2rem',
            boxShadow: 'var(--shadow-xl)',
            animationDelay: '100ms'
          }}
        >
          <div
            className="absolute inset-0 opacity-20 animate-gradient"
            style={{
              background: 'linear-gradient(135deg, var(--cyan-400) 0%, var(--amber-400) 100%)',
              pointerEvents: 'none'
            }}
          />

          <div className="relative z-10">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ background: 'var(--cyan-500)' }}>
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div>
                <h2 style={{
                  fontFamily: 'var(--font-display)',
                  color: 'var(--navy-50)',
                  fontSize: '1.5rem',
                  fontWeight: '600'
                }}>
                  Project Information
                </h2>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <div style={{ color: 'var(--navy-300)', fontSize: '0.875rem', marginBottom: '0.5rem' }}>Source File</div>
                <div style={{ color: 'var(--navy-50)', fontSize: '1rem', fontWeight: '600', fontFamily: 'monospace' }}>{stats.sourceFile}</div>
              </div>
              <div>
                <div style={{ color: 'var(--navy-300)', fontSize: '0.875rem', marginBottom: '0.5rem' }}>Translation File</div>
                <div style={{ color: 'var(--navy-50)', fontSize: '1rem', fontWeight: '600', fontFamily: 'monospace' }}>{stats.translationFile}</div>
              </div>
              <div>
                <div style={{ color: 'var(--navy-300)', fontSize: '0.875rem', marginBottom: '0.5rem' }}>Created</div>
                <div style={{ color: 'var(--navy-50)', fontSize: '1rem', fontWeight: '600' }}>{stats.projectCreated}</div>
              </div>
              <div>
                <div style={{ color: 'var(--navy-300)', fontSize: '0.875rem', marginBottom: '0.5rem' }}>Database</div>
                <div style={{ color: 'var(--navy-50)', fontSize: '1rem', fontWeight: '600' }}>{stats.dbType}</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Translator Activity */}
      <div
        className="clip-corner overflow-hidden animate-slide-in-up"
        style={{
          background: 'white',
          border: '1px solid var(--navy-200)',
          boxShadow: 'var(--shadow-md)',
          animationDelay: '200ms'
        }}
      >
        <div className="p-6" style={{ borderBottom: '1px solid var(--navy-100)', background: 'var(--gradient-overlay)' }}>
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'var(--amber-400)' }}>
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div>
              <h2 style={{
                fontFamily: 'var(--font-display)',
                color: 'var(--navy-900)',
                fontSize: '1.25rem',
                fontWeight: '600'
              }}>
                Recent Activity
              </h2>
              <p style={{ color: 'var(--navy-600)', fontSize: '0.875rem' }}>
                Translator performance overview
              </p>
            </div>
          </div>
        </div>
        <div className="overflow-x-auto">
          {activity.length > 0 ? (
            <table className="w-full">
              <thead style={{ background: 'var(--navy-50)' }}>
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--navy-700)', fontFamily: 'var(--font-display)' }}>Translator</th>
                  <th className="px-6 py-4 text-right text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--navy-700)', fontFamily: 'var(--font-display)' }}>Segments</th>
                  <th className="px-6 py-4 text-right text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--navy-700)', fontFamily: 'var(--font-display)' }}>Edit Time (s)</th>
                  <th className="px-6 py-4 text-right text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--navy-700)', fontFamily: 'var(--font-display)' }}>Insertions</th>
                  <th className="px-6 py-4 text-right text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--navy-700)', fontFamily: 'var(--font-display)' }}>Deletions</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--navy-700)', fontFamily: 'var(--font-display)' }}>Status</th>
                </tr>
              </thead>
              <tbody style={{ background: 'white' }}>
                {activity.map((translator, idx) => (
                  <tr
                    key={`${translator.name}-${translator.surname}`}
                    className="transition-colors hover:bg-opacity-50"
                    style={{
                      borderBottom: '1px solid var(--navy-100)',
                      background: idx % 2 === 0 ? 'transparent' : 'var(--navy-50)'
                    }}
                  >
                    <td className="px-6 py-4">
                      <div style={{
                        fontSize: '0.9rem',
                        fontWeight: '600',
                        color: 'var(--navy-900)',
                        fontFamily: 'var(--font-display)'
                      }}>
                        {translator.name} {translator.surname}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right" style={{
                      fontSize: '0.95rem',
                      fontWeight: '700',
                      color: 'var(--navy-900)',
                      fontFamily: 'var(--font-display)'
                    }}>
                      {translator.segmentsCompleted}
                    </td>
                    <td className="px-6 py-4 text-right" style={{
                      fontSize: '0.95rem',
                      fontWeight: '600',
                      color: 'var(--navy-700)'
                    }}>
                      {translator.totalEditTime.toFixed(1)}
                    </td>
                    <td className="px-6 py-4 text-right" style={{
                      fontSize: '0.95rem',
                      fontWeight: '700',
                      color: 'var(--emerald-500)'
                    }}>
                      {translator.insertions}
                    </td>
                    <td className="px-6 py-4 text-right" style={{
                      fontSize: '0.95rem',
                      fontWeight: '700',
                      color: 'var(--rose-500)'
                    }}>
                      {translator.deletions}
                    </td>
                    <td className="px-6 py-4">
                      <span style={{
                        fontSize: '0.875rem',
                        fontWeight: '600',
                        color: translator.status === 'Active' ? 'var(--emerald-500)' : 'var(--navy-500)'
                      }}>
                        {translator.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="p-12 text-center">
              <p style={{ color: 'var(--navy-500)', fontSize: '0.95rem' }}>
                No translator activity yet. Share your project key to get started!
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, icon, color, delay }: { title: string; value: string; icon: string; color: string; delay: string }) {
  const colorMap: Record<string, { bg: string; icon: string; accent: string }> = {
    cyan: { bg: 'var(--cyan-500)', icon: 'var(--cyan-600)', accent: 'var(--cyan-400)' },
    amber: { bg: 'var(--amber-500)', icon: 'var(--amber-600)', accent: 'var(--amber-400)' },
    emerald: { bg: 'var(--emerald-500)', icon: 'var(--emerald-500)', accent: 'var(--emerald-400)' },
  };

  const colors = colorMap[color];

  return (
    <div
      className="clip-corner relative overflow-hidden animate-slide-in-up group"
      style={{
        background: 'white',
        border: '1px solid var(--navy-200)',
        padding: '1.5rem',
        boxShadow: 'var(--shadow-md)',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        animationDelay: delay
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateY(-4px)';
        e.currentTarget.style.boxShadow = 'var(--shadow-xl)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0)';
        e.currentTarget.style.boxShadow = 'var(--shadow-md)';
      }}
    >
      <div
        className="absolute top-0 right-0 w-12 h-12 opacity-10"
        style={{ background: colors.bg }}
      />

      <div className="flex items-start justify-between relative z-10">
        <div className="flex-1">
          <p style={{
            color: 'var(--navy-600)',
            fontSize: '0.8rem',
            fontWeight: '600',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            marginBottom: '0.75rem',
            fontFamily: 'var(--font-display)'
          }}>
            {title}
          </p>
          <p style={{
            fontSize: '2.5rem',
            fontWeight: '700',
            color: 'var(--navy-900)',
            lineHeight: '1',
            fontFamily: 'var(--font-display)',
            letterSpacing: '-0.02em'
          }}>
            {value}
          </p>
        </div>

        <div
          className="w-12 h-12 rounded-lg flex items-center justify-center transition-transform group-hover:scale-110"
          style={{ background: colors.bg, boxShadow: 'var(--shadow-sm)' }}
        >
          {icon === 'users' && (
            <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          )}
          {icon === 'document' && (
            <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          )}
          {icon === 'check' && (
            <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          )}
          {icon === 'chart' && (
            <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          )}
        </div>
      </div>

      <div
        className="absolute bottom-0 left-0 right-0 h-1 transition-all group-hover:h-2"
        style={{ background: colors.bg }}
      />
    </div>
  );
}
