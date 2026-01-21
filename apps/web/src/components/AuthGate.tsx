'use client';

import { ReactNode } from 'react';
import { useAuth } from './AuthProvider';
import { LoginPage } from './LoginPage';

export function AuthGate({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  // Show loading state while checking auth
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-black via-gray-900 to-black flex items-center justify-center">
        <div className="w-8 h-8 rounded-full border-2 border-gray-700 border-t-gray-400 animate-spin" />
      </div>
    );
  }

  // Show login page if not authenticated
  if (!isAuthenticated) {
    return <LoginPage />;
  }

  // Show the actual app content
  return <>{children}</>;
}
