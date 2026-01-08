'use client';

import { useEffect, useState } from 'react';

interface Translator {
  name: string;
  surname: string;
  segmentsCompleted: number;
  progress: number;
  totalEditTime: number;
  insertions: number;
  deletions: number;
  status: string;
}

export default function UsersPage() {
  const [translators, setTranslators] = useState<Translator[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchTranslators();
  }, []);

  const fetchTranslators = async () => {
    try {
      const response = await fetch('/api/dashboard/users');
      if (response.ok) {
        const data = await response.json();
        setTranslators(data.translators);
      } else {
        setError('Failed to load translators');
      }
    } catch (err) {
      setError('Error loading translators');
    } finally {
      setLoading(false);
    }
  };

  const filteredTranslators = translators.filter(t =>
    searchQuery === '' ||
    t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.surname.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-[var(--navy-200)] border-t-[var(--cyan-500)] rounded-full animate-spin mx-auto mb-4"></div>
          <p style={{ color: 'var(--navy-600)' }} className="text-sm font-medium">Loading translators...</p>
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
          User Management
        </h1>
        <p style={{ color: 'var(--navy-600)', fontSize: '0.95rem' }}>
          View and manage translators in your project
        </p>
      </div>

      {/* Search bar */}
      <div className="animate-slide-in-up" style={{ animationDelay: '100ms' }}>
        <input
          type="text"
          placeholder="Search translators..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="clip-corner w-full max-w-md px-4 py-3"
          style={{
            background: 'white',
            border: '1px solid var(--navy-300)',
            color: 'var(--navy-900)',
            fontSize: '0.95rem',
            outline: 'none',
            transition: 'all 0.2s',
            boxShadow: 'var(--shadow-sm)'
          }}
          onFocus={(e) => {
            e.currentTarget.style.borderColor = 'var(--cyan-500)';
            e.currentTarget.style.boxShadow = '0 0 0 3px rgba(6, 182, 212, 0.1)';
          }}
          onBlur={(e) => {
            e.currentTarget.style.borderColor = 'var(--navy-300)';
            e.currentTarget.style.boxShadow = 'var(--shadow-sm)';
          }}
        />
      </div>

      {/* Translators Grid */}
      {filteredTranslators.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 animate-slide-in-up" style={{ animationDelay: '200ms' }}>
          {filteredTranslators.map((translator) => (
            <div
              key={`${translator.name}-${translator.surname}`}
              className="clip-corner relative overflow-hidden"
              style={{
                background: 'white',
                border: '1px solid var(--navy-200)',
                padding: '1.5rem',
                boxShadow: 'var(--shadow-md)',
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
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
              {/* Status indicator */}
              <div
                className="absolute top-0 right-0 w-2 h-full"
                style={{ background: translator.status === 'Active' ? 'var(--emerald-500)' : 'var(--navy-300)' }}
              />

              <div className="flex items-start gap-4">
                <div
                  className="w-12 h-12 rounded-lg flex items-center justify-center"
                  style={{ background: 'var(--gradient-accent)', boxShadow: 'var(--shadow-sm)' }}
                >
                  <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>

                <div className="flex-1">
                  <h3 style={{
                    fontFamily: 'var(--font-display)',
                    fontSize: '1.25rem',
                    fontWeight: '600',
                    color: 'var(--navy-900)',
                    marginBottom: '0.5rem'
                  }}>
                    {translator.name} {translator.surname}
                  </h3>

                  <div className="grid grid-cols-2 gap-3 mt-4">
                    <div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--navy-500)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: '600' }}>
                        Segments
                      </div>
                      <div style={{ fontSize: '1.5rem', fontWeight: '700', color: 'var(--navy-900)', fontFamily: 'var(--font-display)' }}>
                        {translator.segmentsCompleted}
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--navy-500)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: '600' }}>
                        Progress
                      </div>
                      <div style={{ fontSize: '1.5rem', fontWeight: '700', color: 'var(--cyan-500)', fontFamily: 'var(--font-display)' }}>
                        {translator.progress}%
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--navy-500)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: '600' }}>
                        Edit Time
                      </div>
                      <div style={{ fontSize: '1rem', fontWeight: '600', color: 'var(--navy-700)' }}>
                        {translator.totalEditTime.toFixed(1)}s
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--navy-500)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: '600' }}>
                        Status
                      </div>
                      <div style={{
                        fontSize: '0.875rem',
                        fontWeight: '600',
                        color: translator.status === 'Active' ? 'var(--emerald-500)' : 'var(--navy-500)'
                      }}>
                        {translator.status}
                      </div>
                    </div>
                  </div>

                  {/* Progress bar */}
                  <div className="mt-4">
                    <div
                      className="h-2 rounded-full overflow-hidden"
                      style={{ background: 'var(--navy-100)' }}
                    >
                      <div
                        className="h-full transition-all duration-500"
                        style={{
                          background: 'var(--gradient-accent)',
                          width: `${translator.progress}%`
                        }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-24">
          <p style={{ color: 'var(--navy-500)', fontSize: '0.95rem' }}>
            {searchQuery ? `No translators found matching "${searchQuery}"` : 'No translators have joined yet.'}
          </p>
        </div>
      )}
    </div>
  );
}
