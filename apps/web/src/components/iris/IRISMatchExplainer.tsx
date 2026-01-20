'use client';

import { useState } from 'react';

interface MatchFactor {
  factor: string;
  weight: number;
  description: string;
  icon: string;
}

interface IRISMatchExplainerProps {
  matchScore: number;
  matchedResearcher: {
    name: string;
    department: string;
    photoUrl?: string;
  };
  factors: MatchFactor[];
  explanation: string;
}

export function IRISMatchExplainer({
  matchScore,
  matchedResearcher,
  factors,
  explanation,
}: IRISMatchExplainerProps) {
  const [showDetails, setShowDetails] = useState(false);
  const scorePercent = Math.round(matchScore * 100);

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="p-5 border-b border-gray-100">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded bg-gray-100 flex items-center justify-center">
              {matchedResearcher.photoUrl ? (
                <img
                  src={matchedResearcher.photoUrl}
                  alt={matchedResearcher.name}
                  className="w-14 h-14 rounded object-cover"
                />
              ) : (
                <span className="text-lg font-semibold text-gray-600">
                  {matchedResearcher.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
                </span>
              )}
            </div>
            <div>
              <h3 className="text-lg font-semibold text-[#0B1315]">{matchedResearcher.name}</h3>
              <p className="text-sm text-gray-600">{matchedResearcher.department}</p>
            </div>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-[#0B1315]">{scorePercent}%</div>
            <div className="text-xs text-gray-500 uppercase tracking-wide">Match</div>
          </div>
        </div>
      </div>

      {/* IRIS Analysis */}
      <div className="p-5 bg-gray-50 border-b border-gray-100">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 bg-[#0B1315] rounded flex items-center justify-center flex-shrink-0">
            <div className="w-4 h-4 bg-[#FDBB30] rounded-sm" />
          </div>
          <div>
            <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">IRIS Analysis</div>
            <p className="text-sm text-gray-700 leading-relaxed">{explanation}</p>
          </div>
        </div>
      </div>

      {/* Methodology Toggle */}
      <button
        onClick={() => setShowDetails(!showDetails)}
        className="w-full px-5 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors text-left"
      >
        <span className="text-sm font-medium text-[#0B1315]">
          View matching methodology
        </span>
        <svg
          className={`w-4 h-4 text-gray-400 transform transition-transform ${showDetails ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Detailed Breakdown */}
      {showDetails && (
        <div className="p-5 border-t border-gray-100 space-y-5">
          <div>
            <div className="text-xs text-gray-500 uppercase tracking-wide mb-4">
              Match Factors
            </div>

            <div className="space-y-4">
              {factors.map((factor, index) => (
                <div key={index} className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded bg-gray-100 flex items-center justify-center flex-shrink-0 text-xs font-medium text-gray-600">
                    {factor.icon}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-[#0B1315]">{factor.factor}</span>
                      <span className="text-xs text-gray-500">
                        {Math.round(factor.weight * 100)}%
                      </span>
                    </div>
                    <p className="text-xs text-gray-600 mb-2">{factor.description}</p>
                    <div className="h-1 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-[#FDBB30] rounded-full"
                        style={{ width: `${factor.weight * 100}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Data sources */}
          <div className="pt-4 border-t border-gray-100">
            <div className="text-xs text-gray-500 uppercase tracking-wide mb-3">Data Sources</div>
            <div className="flex flex-wrap gap-2">
              {['Publications', 'Research Areas', 'Grant History', 'Methodology'].map((source) => (
                <span
                  key={source}
                  className="px-3 py-1 bg-gray-100 rounded text-xs text-gray-600"
                >
                  {source}
                </span>
              ))}
            </div>
          </div>

          {/* Privacy notice */}
          <div className="p-3 bg-gray-50 rounded border border-gray-200">
            <div className="flex items-center gap-2 text-gray-600">
              <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              <span className="text-xs">
                Analysis performed locally on KSU infrastructure
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default IRISMatchExplainer;
