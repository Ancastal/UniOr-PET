'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const [name, setName] = useState('');
  const [surname, setSurname] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    console.log('Attempting login with:', { name, surname });

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, surname, password }),
      });

      console.log('Login response status:', response.status);

      const data = await response.json();

      if (response.ok) {
        console.log('Login successful, redirecting...');
        if (data.role === 'project_manager') {
          window.location.href = 'https://pet-manager.ancastal.com';
        } else {
          router.push('/dashboard');
        }
      } else {
        console.error('Login failed:', data);
        setError(data.error || 'Invalid credentials');
      }
    } catch (err) {
      console.error('Login error:', err);
      setError('Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen noise-overlay flex items-center justify-center" style={{ background: 'var(--background)' }}>
      {/* Gradient background overlay */}
      <div
        className="fixed inset-0 opacity-30 pointer-events-none"
        style={{
          background: 'radial-gradient(circle at 20% 50%, var(--cyan-400) 0%, transparent 50%), radial-gradient(circle at 80% 80%, var(--amber-400) 0%, transparent 50%)',
          filter: 'blur(100px)'
        }}
      />

      <div className="relative z-10 w-full max-w-md px-4">
        {/* Logo */}
        <div className="text-center mb-8 animate-slide-in-up">
          <div
            className="clip-corner inline-flex items-center justify-center w-16 h-16 mb-4"
            style={{
              background: 'var(--gradient-accent)',
              boxShadow: 'var(--shadow-xl)'
            }}
          >
            <svg className="w-10 h-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          <h1
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: '2rem',
              fontWeight: '700',
              color: 'var(--navy-900)',
              letterSpacing: '-0.02em',
              marginBottom: '0.5rem'
            }}
          >
            UniOr-PET
          </h1>
          <p style={{ color: 'var(--navy-600)', fontSize: '0.95rem' }}>
            Project Manager Dashboard
          </p>
        </div>

        {/* Login Form */}
        <div
          className="clip-corner glass animate-scale-in"
          style={{
            padding: '2rem',
            border: '1px solid var(--navy-200)',
            boxShadow: 'var(--shadow-xl)',
            animationDelay: '100ms'
          }}
        >
          <h2
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: '1.5rem',
              fontWeight: '600',
              color: 'var(--navy-900)',
              marginBottom: '1.5rem'
            }}
          >
            Login
          </h2>

          {error && (
            <div
              className="mb-4 p-3 rounded-lg"
              style={{
                background: 'var(--rose-400)',
                color: 'white',
                fontSize: '0.875rem'
              }}
            >
              {error}
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label
                htmlFor="name"
                style={{
                  display: 'block',
                  fontSize: '0.875rem',
                  fontWeight: '600',
                  color: 'var(--navy-700)',
                  marginBottom: '0.5rem',
                  fontFamily: 'var(--font-display)'
                }}
              >
                Name
              </label>
              <input
                id="name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="clip-corner w-full px-4 py-3"
                style={{
                  background: 'white',
                  border: '1px solid var(--navy-300)',
                  color: 'var(--navy-900)',
                  fontSize: '0.95rem',
                  outline: 'none',
                  transition: 'all 0.2s'
                }}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = 'var(--cyan-500)';
                  e.currentTarget.style.boxShadow = '0 0 0 3px rgba(6, 182, 212, 0.1)';
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = 'var(--navy-300)';
                  e.currentTarget.style.boxShadow = 'none';
                }}
              />
            </div>

            <div>
              <label
                htmlFor="surname"
                style={{
                  display: 'block',
                  fontSize: '0.875rem',
                  fontWeight: '600',
                  color: 'var(--navy-700)',
                  marginBottom: '0.5rem',
                  fontFamily: 'var(--font-display)'
                }}
              >
                Surname
              </label>
              <input
                id="surname"
                type="text"
                value={surname}
                onChange={(e) => setSurname(e.target.value)}
                required
                className="clip-corner w-full px-4 py-3"
                style={{
                  background: 'white',
                  border: '1px solid var(--navy-300)',
                  color: 'var(--navy-900)',
                  fontSize: '0.95rem',
                  outline: 'none',
                  transition: 'all 0.2s'
                }}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = 'var(--cyan-500)';
                  e.currentTarget.style.boxShadow = '0 0 0 3px rgba(6, 182, 212, 0.1)';
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = 'var(--navy-300)';
                  e.currentTarget.style.boxShadow = 'none';
                }}
              />
            </div>

            <div>
              <label
                htmlFor="password"
                style={{
                  display: 'block',
                  fontSize: '0.875rem',
                  fontWeight: '600',
                  color: 'var(--navy-700)',
                  marginBottom: '0.5rem',
                  fontFamily: 'var(--font-display)'
                }}
              >
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="clip-corner w-full px-4 py-3"
                style={{
                  background: 'white',
                  border: '1px solid var(--navy-300)',
                  color: 'var(--navy-900)',
                  fontSize: '0.95rem',
                  outline: 'none',
                  transition: 'all 0.2s'
                }}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = 'var(--cyan-500)';
                  e.currentTarget.style.boxShadow = '0 0 0 3px rgba(6, 182, 212, 0.1)';
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = 'var(--navy-300)';
                  e.currentTarget.style.boxShadow = 'none';
                }}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="clip-corner w-full px-6 py-3 font-medium text-white transition-all hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
              style={{
                background: loading ? 'var(--navy-500)' : 'var(--gradient-accent)',
                boxShadow: 'var(--shadow-lg)',
                fontFamily: 'var(--font-display)',
                fontWeight: '600',
                fontSize: '0.95rem'
              }}
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                  Logging in...
                </span>
              ) : (
                'Login'
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
