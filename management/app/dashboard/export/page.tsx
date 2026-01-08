'use client';

import { useState } from 'react';

interface ExportOption {
  id: string;
  title: string;
  description: string;
  format: string;
  icon: string;
}

export default function ExportPage() {
  const [exporting, setExporting] = useState<string | null>(null);

  const exportOptions: ExportOption[] = [
    {
      id: 'translations',
      title: 'Translation Data',
      description: 'Export all completed translations with source and target text',
      format: 'CSV/JSON',
      icon: 'document'
    },
    {
      id: 'metrics',
      title: 'Performance Metrics',
      description: 'Export detailed editing metrics for all translators',
      format: 'CSV/Excel',
      icon: 'chart'
    },
    {
      id: 'activity',
      title: 'Activity Log',
      description: 'Export complete activity history with timestamps',
      format: 'CSV/JSON',
      icon: 'clock'
    },
    {
      id: 'summary',
      title: 'Project Summary',
      description: 'Export comprehensive project report with statistics',
      format: 'PDF/Excel',
      icon: 'report'
    }
  ];

  const handleExport = async (optionId: string) => {
    setExporting(optionId);

    try {
      const response = await fetch(`/api/dashboard/export/${optionId}`, {
        method: 'POST'
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${optionId}-export-${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        alert('Export failed. Please try again.');
      }
    } catch (err) {
      alert('Export error. Please try again.');
    } finally {
      setExporting(null);
    }
  };

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
          Export Data
        </h1>
        <p style={{ color: 'var(--navy-600)', fontSize: '0.95rem' }}>
          Download project data in various formats
        </p>
      </div>

      {/* Export Options Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5 animate-slide-in-up" style={{ animationDelay: '100ms' }}>
        {exportOptions.map((option, idx) => (
          <div
            key={option.id}
            className="clip-corner relative overflow-hidden"
            style={{
              background: 'white',
              border: '1px solid var(--navy-200)',
              padding: '2rem',
              boxShadow: 'var(--shadow-md)',
              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              animationDelay: `${idx * 100}ms`
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
            <div className="flex items-start gap-4 mb-6">
              <div
                className="w-14 h-14 rounded-lg flex items-center justify-center flex-shrink-0"
                style={{ background: 'var(--gradient-accent)', boxShadow: 'var(--shadow-lg)' }}
              >
                {option.icon === 'document' && (
                  <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                )}
                {option.icon === 'chart' && (
                  <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                )}
                {option.icon === 'clock' && (
                  <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                )}
                {option.icon === 'report' && (
                  <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                )}
              </div>

              <div className="flex-1">
                <h3 style={{
                  fontFamily: 'var(--font-display)',
                  fontSize: '1.25rem',
                  fontWeight: '600',
                  color: 'var(--navy-900)',
                  marginBottom: '0.5rem'
                }}>
                  {option.title}
                </h3>
                <p style={{
                  fontSize: '0.875rem',
                  color: 'var(--navy-600)',
                  marginBottom: '0.75rem'
                }}>
                  {option.description}
                </p>
                <div
                  className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold"
                  style={{
                    background: 'var(--navy-100)',
                    color: 'var(--navy-700)',
                    fontFamily: 'var(--font-display)'
                  }}
                >
                  {option.format}
                </div>
              </div>
            </div>

            <button
              onClick={() => handleExport(option.id)}
              disabled={exporting !== null}
              className="clip-corner w-full px-6 py-3 font-medium text-white transition-all hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
              style={{
                background: exporting === option.id ? 'var(--navy-500)' : 'var(--gradient-accent)',
                boxShadow: 'var(--shadow-lg)',
                fontFamily: 'var(--font-display)',
                fontWeight: '600',
                fontSize: '0.95rem'
              }}
            >
              {exporting === option.id ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                  Exporting...
                </span>
              ) : (
                <span className="flex items-center justify-center gap-2">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  Export
                </span>
              )}
            </button>
          </div>
        ))}
      </div>

      {/* Info Card */}
      <div
        className="clip-corner animate-slide-in-up"
        style={{
          background: 'var(--gradient-overlay)',
          border: '1px solid var(--navy-200)',
          padding: '1.5rem',
          boxShadow: 'var(--shadow-sm)',
          animationDelay: '400ms'
        }}
      >
        <div className="flex items-start gap-3">
          <svg className="w-5 h-5 flex-shrink-0 mt-0.5" style={{ color: 'var(--cyan-600)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <h4 style={{
              fontFamily: 'var(--font-display)',
              fontSize: '0.95rem',
              fontWeight: '600',
              color: 'var(--navy-900)',
              marginBottom: '0.5rem'
            }}>
              Export Information
            </h4>
            <p style={{ fontSize: '0.875rem', color: 'var(--navy-600)', lineHeight: '1.6' }}>
              Exports include data from all translators in your project. Large exports may take a few moments to prepare.
              Downloaded files will include timestamps and can be opened with spreadsheet applications or text editors.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
