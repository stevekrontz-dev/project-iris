'use client';

import { useState, FormEvent } from 'react';
import { useAuth } from './AuthProvider';

export function LoginPage() {
  const [password, setPassword] = useState('');
  const [error, setError] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(false);
    setIsLoading(true);

    const success = await login(password);

    if (!success) {
      setError(true);
      setPassword('');
    }
    setIsLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-gray-900 to-black flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        {/* Subtle ambient glow */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-gray-800/20 rounded-full blur-3xl" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-gray-800/10 rounded-full blur-3xl" />
        </div>

        <form onSubmit={handleSubmit} className="relative space-y-8">
          {/* Greeting */}
          <div className="text-center space-y-2">
            <h1 className="text-2xl font-light text-white tracking-wide">
              Welcome back, Steve
            </h1>
            <div className="w-12 h-px bg-gradient-to-r from-transparent via-gray-600 to-transparent mx-auto" />
          </div>

          {/* Password Input */}
          <div className="space-y-4">
            <div className="relative">
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
                autoFocus
                autoComplete="current-password"
                className={`w-full px-4 py-3 bg-white/5 border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-1 transition-all ${
                  error
                    ? 'border-red-500/50 focus:ring-red-500/50 focus:border-red-500/50'
                    : 'border-gray-800 focus:ring-gray-600 focus:border-gray-600'
                }`}
              />
              {error && (
                <p className="absolute -bottom-6 left-0 text-xs text-red-400">
                  Incorrect password
                </p>
              )}
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isLoading || !password}
            className="w-full py-3 bg-white/10 hover:bg-white/15 disabled:bg-white/5 disabled:cursor-not-allowed border border-gray-800 rounded-lg text-white font-medium transition-all focus:outline-none focus:ring-1 focus:ring-gray-600"
          >
            {isLoading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="none"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                Verifying...
              </span>
            ) : (
              'Continue'
            )}
          </button>
        </form>

        {/* Minimal footer */}
        <div className="mt-16 text-center">
          <div className="w-8 h-8 mx-auto rounded-full bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-800 flex items-center justify-center">
            <div className="w-2 h-2 rounded-full bg-gray-600" />
          </div>
        </div>
      </div>
    </div>
  );
}
