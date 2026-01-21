'use client';

import { useState } from 'react';
import { IRISThinking } from '@/components/iris/IRISThinking';
import { IRISMatchExplainer } from '@/components/iris/IRISMatchExplainer';
import { Navigation } from '@/components/Navigation';

const DEMO_MATCH = {
  matchScore: 0.87,
  matchedResearcher: {
    name: 'Dr. Sarah Chen',
    department: 'Computer Science',
  },
  factors: [
    {
      factor: 'Research Overlap',
      weight: 0.35,
      description: 'Both work on machine learning applications in healthcare diagnostics',
      icon: 'RO',
    },
    {
      factor: 'Complementary Methods',
      weight: 0.28,
      description: 'Your statistical modeling pairs well with their deep learning expertise',
      icon: 'CM',
    },
    {
      factor: 'Grant Synergy',
      weight: 0.22,
      description: 'Active NSF funding in related areas increases collaboration potential',
      icon: 'GS',
    },
    {
      factor: 'Publication Network',
      weight: 0.15,
      description: 'Co-cited 12 times in recent literature',
      icon: 'PN',
    },
  ],
  explanation:
    'Dr. Chen\'s expertise in neural network architectures for medical imaging complements your work on predictive modeling for patient outcomes. Together, you could develop end-to-end diagnostic systems that combine imaging analysis with clinical data prediction.',
};

export default function Home() {
  const [showDemo, setShowDemo] = useState(false);
  const [demoStage, setDemoStage] = useState<'analyzing' | 'matching' | 'explaining' | 'complete'>('analyzing');
  const [showResult, setShowResult] = useState(false);

  const runDemo = () => {
    setShowDemo(true);
    setShowResult(false);
    setDemoStage('analyzing');

    setTimeout(() => setDemoStage('matching'), 3000);
    setTimeout(() => setDemoStage('explaining'), 6000);
    setTimeout(() => {
      setDemoStage('complete');
      setTimeout(() => {
        setShowDemo(false);
        setShowResult(true);
      }, 1500);
    }, 9000);
  };

  return (
    <div className="min-h-screen bg-white">
      <Navigation variant="dark" />

      {/* Hero Section */}
      <section className="bg-gray-50 border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-6 lg:px-8 py-16 lg:py-20">
          <div className="max-w-3xl">
            <p className="text-sm font-medium text-[#FDBB30] uppercase tracking-wide mb-3">
              Kennesaw State University
            </p>
            <h2 className="text-4xl lg:text-5xl font-serif font-bold text-[#0B1315] leading-tight">
              Discover Research Collaborators Through Intelligent Matching
            </h2>
            <p className="mt-6 text-lg text-gray-600 leading-relaxed">
              IRIS analyzes research profiles, publications, and academic backgrounds to
              identify meaningful collaboration opportunities across KSU's research community.
            </p>
            <div className="mt-8 flex gap-4">
              <a
                href="/discover"
                className="bg-[#0B1315] text-white px-6 py-3 rounded font-medium hover:bg-[#1a2428] transition-colors border-2 border-[#0B1315] inline-block"
              >
                Find Collaborators
              </a>
              <button
                onClick={runDemo}
                className="bg-white text-[#0B1315] px-6 py-3 rounded font-medium hover:bg-gray-50 transition-colors border-2 border-[#0B1315]"
              >
                View Demo
              </button>
            </div>
          </div>
        </div>
      </section>

      <main className="max-w-6xl mx-auto px-6 lg:px-8 py-12 lg:py-16">
        {/* Demo Section */}
        <div className="max-w-2xl mx-auto">
          {showDemo && (
            <div className="mb-12">
              <IRISThinking
                isActive={showDemo}
                stage={demoStage}
                researcherName="Dr. Michael Torres"
              />
            </div>
          )}

          {showResult && (
            <div className="mb-12">
              <IRISMatchExplainer {...DEMO_MATCH} />
            </div>
          )}

          {!showDemo && !showResult && (
            <div className="bg-white border border-gray-200 rounded-lg p-8 text-center shadow-sm mb-12">
              <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-lg flex items-center justify-center">
                <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-[#0B1315] mb-2">
                See How IRIS Works
              </h3>
              <p className="text-gray-600 text-sm mb-6">
                Click "View Demo" above to see how IRIS analyzes researcher profiles and identifies collaboration opportunities.
              </p>
              <button
                onClick={runDemo}
                className="text-sm text-[#0B1315] font-medium border border-gray-300 px-4 py-2 rounded hover:bg-gray-50 transition-colors"
              >
                Start Demo
              </button>
            </div>
          )}
        </div>

        {/* Features Section */}
        <section className="border-t border-gray-200 pt-16">
          <div className="text-center mb-12">
            <h3 className="text-2xl font-serif font-semibold text-[#0B1315]">
              Platform Principles
            </h3>
            <p className="mt-2 text-gray-600">
              Built for academic research with privacy and transparency at the core.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
              <div className="w-10 h-10 bg-gray-100 rounded flex items-center justify-center mb-4">
                <svg className="w-5 h-5 text-[#0B1315]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <h4 className="text-base font-semibold text-[#0B1315] mb-2">
                On-Premise Processing
              </h4>
              <p className="text-sm text-gray-600 leading-relaxed">
                All AI analysis runs locally on KSU infrastructure. Research data never leaves university servers.
              </p>
            </div>

            <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
              <div className="w-10 h-10 bg-gray-100 rounded flex items-center justify-center mb-4">
                <svg className="w-5 h-5 text-[#0B1315]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h4 className="text-base font-semibold text-[#0B1315] mb-2">
                Transparent Methodology
              </h4>
              <p className="text-sm text-gray-600 leading-relaxed">
                Full visibility into matching algorithms. Every recommendation includes detailed attribution and reasoning.
              </p>
            </div>

            <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
              <div className="w-10 h-10 bg-gray-100 rounded flex items-center justify-center mb-4">
                <svg className="w-5 h-5 text-[#0B1315]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <h4 className="text-base font-semibold text-[#0B1315] mb-2">
                Researcher IP Rights
              </h4>
              <p className="text-sm text-gray-600 leading-relaxed">
                Researchers and institutions retain all intellectual property. No platform claims on discoveries.
              </p>
            </div>
          </div>
        </section>

        {/* Stats Section */}
        <section className="mt-16 bg-gray-50 border border-gray-200 rounded-lg p-8">
          <div className="grid md:grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-3xl font-semibold text-[#0B1315]">1,289</div>
              <div className="text-sm text-gray-600 mt-1">Faculty Profiles</div>
            </div>
            <div>
              <div className="text-3xl font-semibold text-[#0B1315]">12</div>
              <div className="text-sm text-gray-600 mt-1">Colleges</div>
            </div>
            <div>
              <div className="text-3xl font-semibold text-[#0B1315]">100%</div>
              <div className="text-sm text-gray-600 mt-1">On-Premise AI</div>
            </div>
            <div>
              <div className="text-3xl font-semibold text-[#0B1315]">0</div>
              <div className="text-sm text-gray-600 mt-1">External Data Sharing</div>
            </div>
          </div>
        </section>
      </main>

      {/* Academic Footer */}
      <footer className="bg-[#0B1315] border-t border-gray-800 mt-16">
        <div className="max-w-6xl mx-auto px-6 lg:px-8 py-10">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div className="col-span-1 md:col-span-2">
              <div className="flex items-center space-x-3 mb-4">
                <div className="w-8 h-8 bg-[#FDBB30] rounded flex items-center justify-center">
                  <span className="text-[#0B1315] font-bold text-xs">KSU</span>
                </div>
                <span className="text-white font-semibold">IRIS</span>
              </div>
              <p className="text-gray-400 text-sm leading-relaxed max-w-md">
                Intelligent Research Information System facilitates scholarly collaboration
                across Kennesaw State University through AI-powered matching and discovery.
              </p>
            </div>
            <div>
              <h5 className="text-white font-medium mb-4 text-sm">Platform</h5>
              <ul className="space-y-2 text-sm">
                <li><a href="/discover" className="text-gray-400 hover:text-white transition-colors">Discover Collaborators</a></li>
                <li><a href="#" className="text-gray-400 hover:text-white transition-colors">Privacy Policy</a></li>
                <li><a href="#" className="text-gray-400 hover:text-white transition-colors">Terms of Service</a></li>
              </ul>
            </div>
            <div>
              <h5 className="text-white font-medium mb-4 text-sm">Support</h5>
              <ul className="space-y-2 text-sm">
                <li><a href="#" className="text-gray-400 hover:text-white transition-colors">Contact</a></li>
                <li><a href="#" className="text-gray-400 hover:text-white transition-colors">Help Center</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 flex justify-between items-center text-sm text-gray-500">
            <p>&copy; 2025 Kennesaw State University</p>
            <p>Pilot Program</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
