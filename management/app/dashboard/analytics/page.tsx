'use client';

import { useEffect, useState } from 'react';

interface Analytics {
  overview: {
    totalSegments: number;
    completedSegments: number;
    avgEditTimePerSegment: number;
    totalTranslators: number;
  };
  translatorMetrics: {
    name: string;
    surname: string;
    avgEditTime: number;
    avgInsertions: number;
    avgDeletions: number;
    efficiency: number;
  }[];
  segmentDistribution: {
    range: string;
    count: number;
  }[];
}

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      const response = await fetch('/api/dashboard/analytics');
      if (response.ok) {
        const data = await response.json();
        setAnalytics(data);
      } else {
        setError('Failed to load analytics');
      }
    } catch (err) {
      setError('Error loading analytics');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-[var(--navy-200)] border-t-[var(--cyan-500)] rounded-full animate-spin mx-auto mb-4"></div>
          <p style={{ color: 'var(--navy-600)' }} className="text-sm font-medium">Loading analytics...</p>
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

  if (!analytics) return null;

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
          Analytics
        </h1>
        <p style={{ color: 'var(--navy-600)', fontSize: '0.95rem' }}>
          Detailed performance metrics and insights
        </p>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        <MetricCard
          title="Total Segments"
          value={analytics.overview.totalSegments.toString()}
          icon="document"
          color="cyan"
          delay="0ms"
        />
        <MetricCard
          title="Completed"
          value={analytics.overview.completedSegments.toString()}
          icon="check"
          color="emerald"
          delay="100ms"
        />
        <MetricCard
          title="Avg Edit Time"
          value={`${analytics.overview.avgEditTimePerSegment.toFixed(1)}s`}
          icon="clock"
          color="amber"
          delay="200ms"
        />
        <MetricCard
          title="Translators"
          value={analytics.overview.totalTranslators.toString()}
          icon="users"
          color="cyan"
          delay="300ms"
        />
      </div>

      {/* Translator Efficiency Table */}
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
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div>
              <h2 style={{
                fontFamily: 'var(--font-display)',
                color: 'var(--navy-900)',
                fontSize: '1.25rem',
                fontWeight: '600'
              }}>
                Translator Efficiency
              </h2>
              <p style={{ color: 'var(--navy-600)', fontSize: '0.875rem' }}>
                Performance metrics per translator
              </p>
            </div>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead style={{ background: 'var(--navy-50)' }}>
              <tr>
                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--navy-700)', fontFamily: 'var(--font-display)' }}>Translator</th>
                <th className="px-6 py-4 text-right text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--navy-700)', fontFamily: 'var(--font-display)' }}>Avg Edit Time</th>
                <th className="px-6 py-4 text-right text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--navy-700)', fontFamily: 'var(--font-display)' }}>Avg Insertions</th>
                <th className="px-6 py-4 text-right text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--navy-700)', fontFamily: 'var(--font-display)' }}>Avg Deletions</th>
                <th className="px-6 py-4 text-right text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--navy-700)', fontFamily: 'var(--font-display)' }}>Efficiency</th>
              </tr>
            </thead>
            <tbody style={{ background: 'white' }}>
              {analytics.translatorMetrics.map((metric, idx) => (
                <tr
                  key={`${metric.name}-${metric.surname}`}
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
                      {metric.name} {metric.surname}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right" style={{
                    fontSize: '0.95rem',
                    fontWeight: '600',
                    color: 'var(--navy-700)'
                  }}>
                    {metric.avgEditTime.toFixed(1)}s
                  </td>
                  <td className="px-6 py-4 text-right" style={{
                    fontSize: '0.95rem',
                    fontWeight: '700',
                    color: 'var(--emerald-500)'
                  }}>
                    {metric.avgInsertions.toFixed(1)}
                  </td>
                  <td className="px-6 py-4 text-right" style={{
                    fontSize: '0.95rem',
                    fontWeight: '700',
                    color: 'var(--rose-500)'
                  }}>
                    {metric.avgDeletions.toFixed(1)}
                  </td>
                  <td className="px-6 py-4 text-right" style={{
                    fontSize: '0.95rem',
                    fontWeight: '700',
                    color: 'var(--cyan-500)'
                  }}>
                    {metric.efficiency.toFixed(1)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Segment Distribution */}
      <div
        className="clip-corner overflow-hidden animate-slide-in-up"
        style={{
          background: 'white',
          border: '1px solid var(--navy-200)',
          boxShadow: 'var(--shadow-md)',
          padding: '2rem',
          animationDelay: '300ms'
        }}
      >
        <div className="flex items-center gap-3 mb-6">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'var(--cyan-500)' }}>
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
          <div>
            <h2 style={{
              fontFamily: 'var(--font-display)',
              color: 'var(--navy-900)',
              fontSize: '1.25rem',
              fontWeight: '600'
            }}>
              Edit Time Distribution
            </h2>
            <p style={{ color: 'var(--navy-600)', fontSize: '0.875rem' }}>
              Segments grouped by edit time ranges
            </p>
          </div>
        </div>

        <div className="space-y-4">
          {analytics.segmentDistribution.map((dist, idx) => {
            const maxCount = Math.max(...analytics.segmentDistribution.map(d => d.count));
            const percentage = (dist.count / maxCount) * 100;

            return (
              <div key={idx}>
                <div className="flex items-center justify-between mb-2">
                  <span style={{
                    fontSize: '0.875rem',
                    fontWeight: '600',
                    color: 'var(--navy-700)',
                    fontFamily: 'var(--font-display)'
                  }}>
                    {dist.range}
                  </span>
                  <span style={{
                    fontSize: '0.875rem',
                    fontWeight: '700',
                    color: 'var(--navy-900)',
                    fontFamily: 'var(--font-display)'
                  }}>
                    {dist.count} segments
                  </span>
                </div>
                <div
                  className="h-3 rounded-full overflow-hidden"
                  style={{ background: 'var(--navy-100)' }}
                >
                  <div
                    className="h-full transition-all duration-500"
                    style={{
                      background: 'var(--gradient-accent)',
                      width: `${percentage}%`
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function MetricCard({ title, value, icon, color, delay }: { title: string; value: string; icon: string; color: string; delay: string }) {
  const colorMap: Record<string, { bg: string }> = {
    cyan: { bg: 'var(--cyan-500)' },
    amber: { bg: 'var(--amber-500)' },
    emerald: { bg: 'var(--emerald-500)' },
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
          {icon === 'clock' && (
            <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          )}
          {icon === 'users' && (
            <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
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
