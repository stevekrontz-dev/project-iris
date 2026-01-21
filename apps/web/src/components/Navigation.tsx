'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from './AuthProvider';

// KSU Brand Colors
const KSU_GOLD = '#FDBB30';
const KSU_BLACK = '#0B1315';

interface NavLink {
  href: string;
  label: string;
  description?: string;
}

const NAV_LINKS: NavLink[] = [
  { href: '/discover', label: 'Discover', description: 'KSU Collaborator Search' },
  { href: '/consortium', label: 'Consortium', description: 'Southeast Research Network' },
  { href: '/grants', label: 'Grants', description: 'Team Builder' },
  { href: '/network', label: 'Network', description: 'Collaboration Graph' },
];

interface NavigationProps {
  variant?: 'light' | 'dark';
}

export function Navigation({ variant = 'dark' }: NavigationProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const pathname = usePathname();
  const { logout } = useAuth();

  const isActive = (href: string) => pathname === href;

  const bgClass = variant === 'dark' ? 'bg-[#0B1315]' : 'bg-white';
  const borderClass = variant === 'dark' ? 'border-gray-800' : 'border-gray-200';
  const textClass = variant === 'dark' ? 'text-white' : 'text-[#0B1315]';
  const mutedTextClass = variant === 'dark' ? 'text-gray-400' : 'text-gray-600';
  const hoverClass = variant === 'dark' ? 'hover:text-white' : 'hover:text-[#0B1315]';

  return (
    <header className={`${bgClass} border-b ${borderClass}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="py-4 flex items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-3 flex-shrink-0">
            <div className="w-10 h-10 bg-[#FDBB30] rounded flex items-center justify-center">
              <span className="text-[#0B1315] font-bold text-sm">KSU</span>
            </div>
            <div className="hidden sm:block">
              <h1 className={`${textClass} text-lg font-semibold tracking-tight`}>
                IRIS
              </h1>
              <p className={`text-xs ${mutedTextClass}`}>
                Research Collaborator Finder
              </p>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-1">
            {NAV_LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive(link.href)
                    ? 'bg-[#FDBB30]/10 text-[#FDBB30]'
                    : `${mutedTextClass} ${hoverClass}`
                }`}
              >
                {link.label}
              </Link>
            ))}
          </nav>

          {/* Logout Button - Desktop */}
          <div className="hidden md:flex items-center space-x-4">
            <button
              onClick={logout}
              className="text-gray-400 hover:text-white px-3 py-2 text-sm transition-colors"
            >
              Logout
            </button>
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 rounded-lg hover:bg-gray-800/50 transition-colors"
            aria-label="Toggle menu"
          >
            <svg
              className={`w-6 h-6 ${textClass}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              {mobileMenuOpen ? (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              ) : (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              )}
            </svg>
          </button>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden pb-4 border-t border-gray-800 pt-4">
            <nav className="space-y-1">
              {NAV_LINKS.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`block px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                    isActive(link.href)
                      ? 'bg-[#FDBB30]/10 text-[#FDBB30]'
                      : `${mutedTextClass} ${hoverClass}`
                  }`}
                >
                  <div>{link.label}</div>
                  {link.description && (
                    <div className="text-xs text-gray-500 mt-0.5">{link.description}</div>
                  )}
                </Link>
              ))}
            </nav>
            <div className="mt-4 px-4">
              <button
                onClick={logout}
                className="w-full text-gray-400 hover:text-white px-4 py-3 rounded-lg font-medium text-sm border border-gray-700 hover:border-gray-600 transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        )}
      </div>
    </header>
  );
}

export default Navigation;
