'use client';

import { useState, useRef, useEffect } from 'react';

interface Scientist {
  id: string;
  name: string;
  field: string;
  era: string;
  image: string;
  color: string;
  systemPrompt: string;
  greeting: string;
  facts: string[];
}

// Historical scientists temporarily disabled - need proper knowledge bases
const HISTORICAL_SCIENTISTS: Scientist[] = [
  // Coming soon - Einstein, Hawking, Feynman, Curie, Turing, Darwin
  // Will be re-enabled once we have RAG with their papers, lectures, and interviews
];

interface Message {
  role: 'user' | 'scientist';
  content: string;
  timestamp: Date;
}

interface ResearchPersonaModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialScientist?: string;
}

export default function ResearchPersonaModal({ isOpen, onClose, initialScientist }: ResearchPersonaModalProps) {
  const [selectedScientist, setSelectedScientist] = useState<Scientist | null>(
    initialScientist ? HISTORICAL_SCIENTISTS.find(s => s.id === initialScientist) || null : null
  );
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [isVideoOn, setIsVideoOn] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Reset when scientist changes
  useEffect(() => {
    if (selectedScientist) {
      setMessages([{
        role: 'scientist',
        content: selectedScientist.greeting,
        timestamp: new Date()
      }]);
    }
  }, [selectedScientist]);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input when scientist selected
  useEffect(() => {
    if (selectedScientist) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [selectedScientist]);

  const handleSend = async () => {
    if (!inputValue.trim() || !selectedScientist || isThinking) return;

    const userMessage: Message = {
      role: 'user',
      content: inputValue.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = inputValue.trim();
    setInputValue('');
    setIsThinking(true);

    try {
      // Build conversation history (excluding the greeting)
      const history = messages.slice(1).map(msg => ({
        role: msg.role,
        content: msg.content
      }));

      const response = await fetch('/api/persona/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          personaId: selectedScientist.id,
          message: currentInput,
          history: history
        })
      });

      if (!response.ok) {
        throw new Error('Failed to get response');
      }

      const data = await response.json();

      setMessages(prev => [...prev, {
        role: 'scientist',
        content: data.response,
        timestamp: new Date()
      }]);
    } catch (error) {
      console.error('Persona chat error:', error);
      // Fallback to a contextual error message in character
      const fallbackResponses: Record<string, string> = {
        einstein: "Ah, it seems the connection through space-time has become turbulent. Perhaps we could try again?",
        hawking: "Even black holes have information paradoxes. It seems our communication has encountered one. Please try again.",
        feynman: "Well, that's strange! Something went wrong with the communication. Let's try that again - nature shouldn't be this uncooperative!",
        curie: "It appears our experiment has encountered an unexpected variable. Shall we try once more?",
        turing: "An unexpected halt in our computation. The machine needs another attempt to process your query.",
        darwin: "Nature, it seems, has thrown us a curious obstacle. Perhaps we should adapt and try again?"
      };

      setMessages(prev => [...prev, {
        role: 'scientist',
        content: fallbackResponses[selectedScientist.id] || "I apologize, but I cannot formulate a response at this moment. Please try again.",
        timestamp: new Date()
      }]);
    } finally {
      setIsThinking(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/90 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[#1a1a1f] rounded-2xl w-full max-w-5xl max-h-[90vh] overflow-hidden shadow-2xl border border-white/10">
        {!selectedScientist ? (
          // Scientist Selection View
          <div className="p-8">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 via-fuchsia-400 to-yellow-400 bg-clip-text text-transparent mb-2">
                Research Persona Lab
              </h2>
              <p className="text-gray-400">
                Consult with the greatest minds in history. Powered by AI.
              </p>
            </div>

            {HISTORICAL_SCIENTISTS.length > 0 ? (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {HISTORICAL_SCIENTISTS.map((scientist) => (
                  <button
                    key={scientist.id}
                    onClick={() => setSelectedScientist(scientist)}
                    className="group relative bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/30 rounded-xl p-6 text-left transition-all duration-300 hover:scale-105"
                  >
                    {/* Avatar placeholder */}
                    <div
                      className="w-20 h-20 rounded-full mx-auto mb-4 flex items-center justify-center text-3xl font-bold text-white"
                      style={{ backgroundColor: scientist.color + '40', borderColor: scientist.color, borderWidth: 2 }}
                    >
                      {scientist.name.split(' ').map(n => n[0]).join('')}
                    </div>

                    <h3 className="text-lg font-semibold text-white text-center mb-1">
                      {scientist.name}
                    </h3>
                    <p className="text-sm text-gray-400 text-center mb-2">
                      {scientist.field}
                    </p>
                    <p className="text-xs text-gray-500 text-center">
                      {scientist.era}
                    </p>

                    {/* Facts */}
                    <div className="mt-4 flex flex-wrap gap-1 justify-center">
                      {scientist.facts.map((fact, i) => (
                        <span
                          key={i}
                          className="px-2 py-0.5 rounded text-xs"
                          style={{ backgroundColor: scientist.color + '20', color: scientist.color }}
                        >
                          {fact}
                        </span>
                      ))}
                    </div>

                    {/* Hover effect */}
                    <div
                      className="absolute inset-0 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"
                      style={{ boxShadow: `0 0 30px ${scientist.color}30` }}
                    />
                  </button>
                ))}
              </div>
            ) : (
              /* Coming Soon State */
              <div className="text-center py-16">
                <div className="w-32 h-32 mx-auto mb-6 rounded-full bg-gradient-to-br from-cyan-500/20 to-fuchsia-500/20 flex items-center justify-center">
                  <svg className="w-16 h-16 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                </div>
                <h3 className="text-2xl font-bold text-white mb-2">Personas Coming Soon</h3>
                <p className="text-gray-400 max-w-md mx-auto mb-6">
                  We're building AI personas powered by real research data - papers, lectures, interviews, and more.
                  Soon you'll be able to have meaningful conversations with history's greatest minds.
                </p>
                <div className="flex flex-wrap justify-center gap-3">
                  {['Einstein', 'Hawking', 'Feynman', 'Curie', 'Turing', 'Darwin'].map((name) => (
                    <span key={name} className="px-3 py-1 bg-white/5 border border-white/10 rounded-full text-sm text-gray-500">
                      {name}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="mt-8 text-center">
              <button
                onClick={onClose}
                className="px-6 py-2 bg-white/10 hover:bg-white/20 text-gray-300 rounded-lg transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        ) : (
          // Video Call View
          <div className="flex flex-col h-[85vh]">
            {/* Top Bar - Zoom style */}
            <div className="bg-[#232329] px-4 py-3 flex items-center justify-between border-b border-white/10">
              <div className="flex items-center gap-3">
                <div className="flex gap-1.5">
                  <div className="w-3 h-3 rounded-full bg-red-500 hover:bg-red-400 cursor-pointer" onClick={onClose}></div>
                  <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                  <div className="w-3 h-3 rounded-full bg-green-500"></div>
                </div>
                <span className="text-sm text-gray-400 ml-2">
                  IRIS Research Call • {selectedScientist.name}
                </span>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-xs text-gray-500 font-mono">
                  {new Date().toLocaleTimeString()}
                </span>
                <div className="flex items-center gap-1 text-green-400 text-xs">
                  <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
                  Connected
                </div>
              </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex">
              {/* Video Panel */}
              <div className="w-1/2 p-4 flex flex-col">
                {/* Main Video (Scientist) */}
                <div
                  className="flex-1 rounded-xl overflow-hidden relative"
                  style={{ backgroundColor: selectedScientist.color + '10' }}
                >
                  {isVideoOn ? (
                    <div className="absolute inset-0 flex items-center justify-center">
                      {/* Scientist Avatar */}
                      <div className="text-center">
                        <div
                          className={`w-32 h-32 rounded-full mx-auto mb-4 flex items-center justify-center text-5xl font-bold text-white border-4 transition-all duration-500 ${
                            isThinking ? 'animate-pulse' : ''
                          }`}
                          style={{ backgroundColor: selectedScientist.color + '60', borderColor: selectedScientist.color }}
                        >
                          {selectedScientist.name.split(' ').map(n => n[0]).join('')}
                        </div>
                        <h3 className="text-xl font-semibold text-white">{selectedScientist.name}</h3>
                        <p className="text-sm text-gray-400">{selectedScientist.field}</p>
                        {isThinking && (
                          <p className="text-xs text-cyan-400 mt-2 animate-pulse">
                            Contemplating...
                          </p>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
                      <span className="text-gray-500">Video Off</span>
                    </div>
                  )}

                  {/* Scientist name tag */}
                  <div className="absolute bottom-4 left-4 px-3 py-1 bg-black/60 rounded text-sm text-white">
                    {selectedScientist.name}
                  </div>

                  {/* Speaking indicator */}
                  {isThinking && (
                    <div className="absolute bottom-4 right-4 flex items-center gap-1">
                      <div className="w-1 h-3 bg-cyan-400 rounded animate-pulse" style={{ animationDelay: '0ms' }}></div>
                      <div className="w-1 h-4 bg-cyan-400 rounded animate-pulse" style={{ animationDelay: '150ms' }}></div>
                      <div className="w-1 h-2 bg-cyan-400 rounded animate-pulse" style={{ animationDelay: '300ms' }}></div>
                      <div className="w-1 h-5 bg-cyan-400 rounded animate-pulse" style={{ animationDelay: '450ms' }}></div>
                    </div>
                  )}
                </div>

                {/* Self View (small) */}
                <div className="mt-4 h-24 bg-gray-800 rounded-lg overflow-hidden relative">
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="w-12 h-12 bg-gray-700 rounded-full flex items-center justify-center">
                      <svg className="w-6 h-6 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                    </div>
                  </div>
                  <div className="absolute bottom-2 left-2 px-2 py-0.5 bg-black/60 rounded text-xs text-white">
                    You
                  </div>
                </div>

                {/* Call Controls */}
                <div className="mt-4 flex items-center justify-center gap-4">
                  <button className="p-3 bg-white/10 hover:bg-white/20 rounded-full transition-colors">
                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                    </svg>
                  </button>
                  <button
                    onClick={() => setIsVideoOn(!isVideoOn)}
                    className={`p-3 rounded-full transition-colors ${isVideoOn ? 'bg-white/10 hover:bg-white/20' : 'bg-red-500/20 text-red-400'}`}
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                  </button>
                  <button
                    onClick={onClose}
                    className="p-3 bg-red-500 hover:bg-red-600 rounded-full transition-colors"
                  >
                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 8l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2M5 3a2 2 0 00-2 2v1c0 8.284 6.716 15 15 15h1a2 2 0 002-2v-3.28a1 1 0 00-.684-.948l-4.493-1.498a1 1 0 00-1.21.502l-1.13 2.257a11.042 11.042 0 01-5.516-5.517l2.257-1.128a1 1 0 00.502-1.21L9.228 3.683A1 1 0 008.279 3H5z" />
                    </svg>
                  </button>
                  <button
                    onClick={() => setSelectedScientist(null)}
                    className="p-3 bg-white/10 hover:bg-white/20 rounded-full transition-colors"
                    title="Switch Scientist"
                  >
                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                    </svg>
                  </button>
                </div>
              </div>

              {/* Chat Panel */}
              <div className="w-1/2 border-l border-white/10 flex flex-col bg-[#0d0d0f]">
                {/* Chat Header */}
                <div className="px-4 py-3 border-b border-white/10">
                  <h3 className="font-semibold text-white">Conversation</h3>
                  <p className="text-xs text-gray-500">
                    Ask questions, debate ideas, or explore theories
                  </p>
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                  {messages.map((message, i) => (
                    <div
                      key={i}
                      className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                          message.role === 'user'
                            ? 'bg-cyan-500/20 text-cyan-100'
                            : 'bg-white/10 text-gray-200'
                        }`}
                      >
                        {message.role === 'scientist' && (
                          <div className="flex items-center gap-2 mb-1">
                            <div
                              className="w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold"
                              style={{ backgroundColor: selectedScientist.color }}
                            >
                              {selectedScientist.name[0]}
                            </div>
                            <span className="text-xs font-semibold" style={{ color: selectedScientist.color }}>
                              {selectedScientist.name.split(' ')[1]}
                            </span>
                          </div>
                        )}
                        <p className="text-sm leading-relaxed">{message.content}</p>
                        <p className="text-xs text-gray-500 mt-1">
                          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </p>
                      </div>
                    </div>
                  ))}

                  {isThinking && (
                    <div className="flex justify-start">
                      <div className="bg-white/10 rounded-2xl px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="flex gap-1">
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  <div ref={messagesEndRef} />
                </div>

                {/* Input */}
                <div className="p-4 border-t border-white/10">
                  <div className="flex gap-2">
                    <input
                      ref={inputRef}
                      type="text"
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                      placeholder={`Ask ${selectedScientist.name.split(' ')[0]} a question...`}
                      className="flex-1 bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
                      disabled={isThinking}
                    />
                    <button
                      onClick={handleSend}
                      disabled={!inputValue.trim() || isThinking}
                      className="px-4 py-3 bg-gradient-to-r from-cyan-500 to-fuchsia-500 text-white rounded-xl font-medium hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Send
                    </button>
                  </div>
                  <p className="text-xs text-gray-600 mt-2 text-center">
                    AI-generated responses based on historical writings and known perspectives
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
