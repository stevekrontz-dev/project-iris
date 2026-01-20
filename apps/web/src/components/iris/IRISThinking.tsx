'use client';

import { useState, useEffect } from 'react';

interface IRISThinkingProps {
  isActive: boolean;
  stage?: 'analyzing' | 'matching' | 'explaining' | 'complete';
  researcherName?: string;
}

const STAGES = {
  analyzing: {
    title: 'Analyzing Profile',
    steps: [
      'Reading research publications...',
      'Extracting key methodologies...',
      'Identifying research themes...',
      'Building semantic fingerprint...',
    ],
  },
  matching: {
    title: 'Finding Connections',
    steps: [
      'Scanning 1,289 researcher profiles...',
      'Computing similarity scores...',
      'Identifying cross-disciplinary overlaps...',
      'Ranking potential collaborators...',
    ],
  },
  explaining: {
    title: 'Generating Insights',
    steps: [
      'Analyzing shared research areas...',
      'Identifying complementary expertise...',
      'Drafting collaboration rationale...',
      'Preparing recommendations...',
    ],
  },
  complete: {
    title: 'Analysis Complete',
    steps: ['Found 12 potential connections'],
  },
};

export function IRISThinking({ isActive, stage = 'analyzing', researcherName }: IRISThinkingProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [dots, setDots] = useState('');
  const stageData = STAGES[stage];

  useEffect(() => {
    if (!isActive || stage === 'complete') return;

    const stepInterval = setInterval(() => {
      setCurrentStep((prev) => (prev + 1) % stageData.steps.length);
    }, 2000);

    const dotsInterval = setInterval(() => {
      setDots((prev) => (prev.length >= 3 ? '' : prev + '.'));
    }, 500);

    return () => {
      clearInterval(stepInterval);
      clearInterval(dotsInterval);
    };
  }, [isActive, stage, stageData.steps.length]);

  if (!isActive) return null;

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6 pb-4 border-b border-gray-100">
        <div className="relative">
          <div className="w-12 h-12 bg-[#0B1315] rounded flex items-center justify-center">
            <div className="w-6 h-6 bg-[#FDBB30] rounded-sm animate-pulse" />
          </div>
        </div>
        <div>
          <h3 className="text-lg font-semibold text-[#0B1315]">IRIS Analysis</h3>
          <p className="text-sm text-gray-500">Processing researcher profile</p>
        </div>
      </div>

      {/* Stage indicator */}
      <div className="mb-4">
        <div className="flex items-center gap-2 text-base font-medium text-[#0B1315]">
          <span>{stageData.title}</span>
          {stage !== 'complete' && <span className="text-gray-400">{dots}</span>}
        </div>
        {researcherName && (
          <p className="text-sm text-gray-500 mt-1">
            Analyzing profile for <span className="text-[#0B1315] font-medium">{researcherName}</span>
          </p>
        )}
      </div>

      {/* Processing steps */}
      <div className="space-y-3">
        {stageData.steps.map((step, index) => (
          <div
            key={step}
            className={`flex items-center gap-3 transition-all duration-300 ${
              index === currentStep
                ? 'opacity-100'
                : index < currentStep
                ? 'opacity-60'
                : 'opacity-40'
            }`}
          >
            <div
              className={`w-5 h-5 rounded flex items-center justify-center text-xs ${
                index < currentStep
                  ? 'bg-green-100 text-green-600'
                  : index === currentStep
                  ? 'bg-[#FDBB30] text-[#0B1315]'
                  : 'bg-gray-100 text-gray-400'
              }`}
            >
              {index < currentStep ? '✓' : index + 1}
            </div>
            <span className="text-sm text-gray-700">{step}</span>
          </div>
        ))}
      </div>

      {/* Progress bar */}
      {stage !== 'complete' && (
        <div className="mt-6 pt-4 border-t border-gray-100">
          <div className="flex justify-between text-xs text-gray-500 mb-2">
            <span>Processing</span>
            <span>{Math.round((currentStep / stageData.steps.length) * 100)}%</span>
          </div>
          <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-[#FDBB30] rounded-full transition-all duration-500"
              style={{ width: `${(currentStep / stageData.steps.length) * 100}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
}

export default IRISThinking;
