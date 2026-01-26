'use client';

import React, { useEffect, useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Brain,
  BookOpen,
  Search,
  Palette,
  ClipboardCheck,
  Microscope,
  Loader2,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Clock,
  AlertTriangle
} from 'lucide-react';

// ==================== TYPES ====================

interface AgentThought {
  agent: string;
  icon: string;
  step: string;
  phase: string;
  thinking: string;
  reasoning?: string;
  evidence?: string[];
  conclusion?: string;
  confidence?: number;
  is_complete: boolean;
  timestamp: string;
}

interface AgentProgress {
  total_agents: number;
  completed_agents: number;
  current_agent: string;
  current_step: string;
  elapsed_seconds: number;
}

interface CurriculumResult {
  success: boolean;
  curriculum_plan: any;
  quality_score: number;
  total_thinking_time: number;
  agent_contributions: Record<string, any>;
  recommendations: string[];
}

interface AgentThinkingStreamProps {
  topic: string;
  onComplete?: (result: CurriculumResult) => void;
  onError?: (error: string) => void;
  autoStart?: boolean;
}

// ==================== AGENT CONFIG ====================

const AGENT_CONFIG: Record<string, {
  icon: React.ReactNode;
  color: string;
  bgColor: string;
  label: string;
  description: string;
}> = {
  'Pedagoji Uzmanı': {
    icon: <BookOpen className="w-5 h-5" />,
    color: '#8B5CF6',
    bgColor: 'bg-purple-100 dark:bg-purple-900/30',
    label: 'Pedagoji',
    description: 'Bloom taksonomisi ve öğrenme stilleri analizi'
  },
  'Araştırma Uzmanı': {
    icon: <Search className="w-5 h-5" />,
    color: '#3B82F6',
    bgColor: 'bg-blue-100 dark:bg-blue-900/30',
    label: 'Araştırma',
    description: 'RAG ve kaynak araştırması'
  },
  'İçerik Stratejisti': {
    icon: <Palette className="w-5 h-5" />,
    color: '#EC4899',
    bgColor: 'bg-pink-100 dark:bg-pink-900/30',
    label: 'İçerik',
    description: 'Multimedya ve AI video planlama'
  },
  'Sınav Tasarımcısı': {
    icon: <ClipboardCheck className="w-5 h-5" />,
    color: '#F59E0B',
    bgColor: 'bg-amber-100 dark:bg-amber-900/30',
    label: 'Sınav',
    description: 'Değerlendirme stratejisi ve aralıklı tekrar'
  },
  'Kalite Kontrol Uzmanı': {
    icon: <Microscope className="w-5 h-5" />,
    color: '#10B981',
    bgColor: 'bg-emerald-100 dark:bg-emerald-900/30',
    label: 'Kalite',
    description: 'Final kontrol ve optimizasyon'
  },
  'Curriculum Studio': {
    icon: <Brain className="w-5 h-5" />,
    color: '#6366F1',
    bgColor: 'bg-indigo-100 dark:bg-indigo-900/30',
    label: 'Orkestratör',
    description: 'Multi-agent koordinasyonu'
  }
};

const PHASE_LABELS: Record<string, string> = {
  'analyzing': '🔍 Analiz ediliyor...',
  'reasoning': '💭 Düşünüyor...',
  'deciding': '⚖️ Karar veriyor...',
  'concluding': '✅ Sonuçlandırıyor...'
};

// ==================== THOUGHT CARD ====================

const ThoughtCard: React.FC<{
  thought: AgentThought;
  isLatest: boolean;
  isExpanded: boolean;
  onToggle: () => void;
}> = ({ thought, isLatest, isExpanded, onToggle }) => {
  const config = AGENT_CONFIG[thought.agent] || AGENT_CONFIG['Curriculum Studio'];
  
  return (
    <motion.div
      initial={{ opacity: 0, x: -20, scale: 0.95 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className={`relative rounded-xl border-2 overflow-hidden transition-all duration-300 ${
        isLatest
          ? 'border-purple-500 shadow-lg shadow-purple-500/20'
          : 'border-gray-200 dark:border-gray-700'
      }`}
    >
      {/* Header */}
      <div
        className={`p-4 cursor-pointer ${config.bgColor}`}
        onClick={onToggle}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Agent Icon */}
            <div
              className="p-2 rounded-lg bg-white dark:bg-gray-800 shadow-sm"
              style={{ color: config.color }}
            >
              {config.icon}
            </div>
            
            {/* Agent Info */}
            <div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-gray-900 dark:text-white">
                  {thought.icon} {config.label}
                </span>
                {isLatest && !thought.is_complete && (
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                  >
                    <Loader2 className="w-4 h-4 text-purple-500" />
                  </motion.div>
                )}
                {thought.is_complete && (
                  <CheckCircle className="w-4 h-4 text-green-500" />
                )}
              </div>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                {PHASE_LABELS[thought.phase] || thought.phase}
              </span>
            </div>
          </div>
          
          {/* Confidence & Expand */}
          <div className="flex items-center gap-3">
            {thought.confidence !== undefined && thought.confidence > 0 && (
              <div className="flex items-center gap-1">
                <div className="w-16 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${thought.confidence * 100}%` }}
                    transition={{ duration: 0.5 }}
                    className="h-full rounded-full"
                    style={{ backgroundColor: config.color }}
                  />
                </div>
                <span className="text-xs text-gray-500">
                  {Math.round(thought.confidence * 100)}%
                </span>
              </div>
            )}
            {isExpanded ? (
              <ChevronUp className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-400" />
            )}
          </div>
        </div>
        
        {/* Main Thinking */}
        <motion.p
          className="mt-2 text-gray-700 dark:text-gray-300"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          {thought.thinking}
        </motion.p>
      </div>
      
      {/* Expanded Content */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700"
          >
            <div className="p-4 space-y-3">
              {/* Reasoning */}
              {thought.reasoning && (
                <div>
                  <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                    Düşünce Süreci
                  </span>
                  <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                    {thought.reasoning}
                  </p>
                </div>
              )}
              
              {/* Evidence */}
              {thought.evidence && thought.evidence.length > 0 && (
                <div>
                  <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                    Bulgular
                  </span>
                  <ul className="mt-1 space-y-1">
                    {thought.evidence.map((item, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400">
                        <span className="text-purple-500">•</span>
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              
              {/* Conclusion */}
              {thought.conclusion && (
                <div className="p-3 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
                  <span className="text-xs font-semibold text-green-600 dark:text-green-400 uppercase tracking-wide">
                    Sonuç
                  </span>
                  <p className="mt-1 text-sm text-green-700 dark:text-green-300">
                    {thought.conclusion}
                  </p>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

// ==================== PROGRESS BAR ====================

const AgentProgressBar: React.FC<{ progress: AgentProgress | null }> = ({ progress }) => {
  if (!progress) return null;
  
  const percentage = (progress.completed_agents / progress.total_agents) * 100;
  
  return (
    <div className="mb-6">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
          Agent İlerlemesi
        </span>
        <span className="text-sm text-gray-500">
          {progress.completed_agents} / {progress.total_agents} tamamlandı
        </span>
      </div>
      <div className="relative h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <motion.div
          className="absolute inset-y-0 left-0 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
        />
      </div>
      <div className="flex items-center justify-between mt-2">
        <span className="text-xs text-gray-500 flex items-center gap-1">
          <Clock className="w-3 h-3" />
          {Math.round(progress.elapsed_seconds)}s
        </span>
        <span className="text-xs text-purple-600 dark:text-purple-400">
          {progress.current_agent && `${progress.current_agent} çalışıyor...`}
        </span>
      </div>
    </div>
  );
};

// ==================== MAIN COMPONENT ====================

export const AgentThinkingStream: React.FC<AgentThinkingStreamProps> = ({
  topic,
  onComplete,
  onError,
  autoStart = true
}) => {
  const [thoughts, setThoughts] = useState<AgentThought[]>([]);
  const [progress, setProgress] = useState<AgentProgress | null>(null);
  const [result, setResult] = useState<CurriculumResult | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);
  
  const containerRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  
  // Auto-expand latest thought
  useEffect(() => {
    if (thoughts.length > 0) {
      setExpandedIndex(thoughts.length - 1);
    }
  }, [thoughts.length]);
  
  // Auto-scroll to bottom
  useEffect(() => {
    if (containerRef.current && isStreaming) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [thoughts, isStreaming]);
  
  const startStreaming = useCallback(async () => {
    setIsStreaming(true);
    setError(null);
    setThoughts([]);
    setResult(null);
    
    try {
      const response = await fetch('/api/journey/v2/premium/curriculum/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic,
          target_level: 'intermediate',
          daily_hours: 2.0,
          duration_weeks: 4,
          learning_style: 'multimodal',
          custom_instructions: ''
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      
      if (!reader) {
        throw new Error('Stream not available');
      }
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.type === 'thought') {
                setThoughts(prev => [...prev, data]);
              } else if (data.type === 'progress') {
                setProgress(data);
              } else if (data.type === 'result') {
                setResult(data);
                onComplete?.(data);
              } else if (data.type === 'error') {
                setError(data.message);
                onError?.(data.message);
              } else if (data.type === 'done') {
                setIsStreaming(false);
              }
            } catch (_e) {
              // Skip parse errors
            }
          }
        }
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      onError?.(message);
    } finally {
      setIsStreaming(false);
    }
  }, [topic, onComplete, onError]);
  
  useEffect(() => {
    if (autoStart && topic) {
      startStreaming();
    }
    const eventSource = eventSourceRef.current;
    return () => {
      eventSource?.close();
    };
  }, [autoStart, topic, startStreaming]);
  
  return (
    <div className="w-full max-w-3xl mx-auto">
      {/* Header */}
      <div className="mb-6 text-center">
        <div className="flex items-center justify-center gap-2 mb-2">
          <Brain className="w-8 h-8 text-purple-500" />
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Multi-Agent Curriculum Studio
          </h2>
        </div>
        <p className="text-gray-600 dark:text-gray-400">
          5 uzman agent &ldquo;{topic}&rdquo; için müfredat oluşturuyor...
        </p>
      </div>
      
      {/* Progress Bar */}
      <AgentProgressBar progress={progress} />
      
      {/* Error */}
      {error && (
        <div className="mb-4 p-4 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
          <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
            <AlertTriangle className="w-5 h-5" />
            <span>{error}</span>
          </div>
        </div>
      )}
      
      {/* Thoughts Container */}
      <div
        ref={containerRef}
        className="space-y-4 max-h-[600px] overflow-y-auto pr-2"
      >
        {thoughts.map((thought, index) => (
          <ThoughtCard
            key={`${thought.agent}-${thought.step}-${index}`}
            thought={thought}
            isLatest={index === thoughts.length - 1 && isStreaming}
            isExpanded={expandedIndex === index}
            onToggle={() => setExpandedIndex(expandedIndex === index ? null : index)}
          />
        ))}
        
        {/* Loading State */}
        {isStreaming && thoughts.length === 0 && (
          <div className="flex items-center justify-center p-8">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
            >
              <Sparkles className="w-8 h-8 text-purple-500" />
            </motion.div>
            <span className="ml-3 text-gray-600 dark:text-gray-400">
              Agent&apos;lar başlatılıyor...
            </span>
          </div>
        )}
      </div>
      
      {/* Result */}
      {result && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-6 p-6 rounded-xl bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 border border-green-200 dark:border-green-800"
        >
          <div className="flex items-center gap-3 mb-4">
            <CheckCircle className="w-8 h-8 text-green-500" />
            <div>
              <h3 className="text-xl font-bold text-green-700 dark:text-green-300">
                Müfredat Hazır!
              </h3>
              <p className="text-sm text-green-600 dark:text-green-400">
                Kalite Skoru: %{Math.round(result.quality_score * 100)} • 
                Süre: {Math.round(result.total_thinking_time)}s
              </p>
            </div>
          </div>
          
          {result.curriculum_plan && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
              <div className="text-center p-3 bg-white dark:bg-gray-800 rounded-lg">
                <div className="text-2xl font-bold text-purple-600">
                  {result.curriculum_plan.stage_count || 0}
                </div>
                <div className="text-xs text-gray-500">Aşama</div>
              </div>
              <div className="text-center p-3 bg-white dark:bg-gray-800 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {result.curriculum_plan.total_packages || 0}
                </div>
                <div className="text-xs text-gray-500">Paket</div>
              </div>
              <div className="text-center p-3 bg-white dark:bg-gray-800 rounded-lg">
                <div className="text-2xl font-bold text-pink-600">
                  {result.curriculum_plan.bloom_level || 'N/A'}
                </div>
                <div className="text-xs text-gray-500">Bloom Seviye</div>
              </div>
              <div className="text-center p-3 bg-white dark:bg-gray-800 rounded-lg">
                <div className="text-2xl font-bold text-amber-600">
                  {result.curriculum_plan.daily_hours || 0}s
                </div>
                <div className="text-xs text-gray-500">Günlük</div>
              </div>
            </div>
          )}
          
          {result.recommendations && result.recommendations.length > 0 && (
            <div className="mt-4 p-3 bg-white dark:bg-gray-800 rounded-lg">
              <span className="text-xs font-semibold text-gray-500 uppercase">Öneriler</span>
              <ul className="mt-2 space-y-1">
                {result.recommendations.map((rec, i) => (
                  <li key={i} className="text-sm text-gray-600 dark:text-gray-400 flex items-start gap-2">
                    <span className="text-amber-500">💡</span>
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
};

export default AgentThinkingStream;
