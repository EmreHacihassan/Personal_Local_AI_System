'use client';

import React, { useEffect, useState, useRef } from 'react';
import { motion } from 'framer-motion';
import {
  Brain,
  Target,
  BookOpen,
  Clock,
  CheckCircle,
  Loader2,
  Sparkles,
  Map,
  Package,
  Trophy
} from 'lucide-react';

// ==================== TYPES ====================

interface ThinkingStep {
  step: number;
  agent_name: string;
  action: string;
  reasoning: string;
  output: any;
  timestamp: string;
}

interface AIThinkingViewProps {
  steps: ThinkingStep[];
  isComplete: boolean;
  planSummary?: {
    total_stages: number;
    total_packages: number;
    total_exams: number;
    estimated_days: number;
    total_xp: number;
  };
  onViewPlan?: () => void;
}

// ==================== AGENT ICONS ====================

const AGENT_ICONS: Record<string, { icon: React.ReactNode; color: string }> = {
  'Orchestrator': { icon: <Brain />, color: '#8B5CF6' },
  'Goal Analyzer': { icon: <Target />, color: '#F59E0B' },
  'Curriculum Selector': { icon: <BookOpen />, color: '#3B82F6' },
  'Topic Mapper': { icon: <Map />, color: '#10B981' },
  'Stage Planner': { icon: <Map />, color: '#6366F1' },
  'Package Creator': { icon: <Package />, color: '#EC4899' },
  'Exam Strategist': { icon: <Trophy />, color: '#EF4444' },
  'Timeline Optimizer': { icon: <Clock />, color: '#14B8A6' },
  'Plan Finalizer': { icon: <CheckCircle />, color: '#22C55E' },
  'Content Generator': { icon: <Sparkles />, color: '#F97316' },
};

// ==================== THINKING STEP COMPONENT ====================

const ThinkingStepCard: React.FC<{
  step: ThinkingStep;
  index: number;
  isLatest: boolean;
}> = ({ step, index, isLatest }) => {
  const agentInfo = AGENT_ICONS[step.agent_name] || { icon: <Brain />, color: '#6B7280' };
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ delay: index * 0.1, duration: 0.3 }}
      className={`relative ${isLatest ? 'z-10' : ''}`}
    >
      {/* Connection Line */}
      {index > 0 && (
        <div className="absolute -top-6 left-6 w-0.5 h-6 bg-gradient-to-b from-transparent to-gray-300 dark:to-gray-600" />
      )}
      
      <div
        className={`rounded-xl border-2 p-4 transition-all ${
          isLatest
            ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20 shadow-lg shadow-purple-500/20'
            : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800'
        }`}
      >
        {/* Header */}
        <div className="flex items-start gap-3">
          {/* Agent Icon */}
          <div
            className="p-2 rounded-lg"
            style={{ backgroundColor: `${agentInfo.color}20` }}
          >
            <div
              className="w-5 h-5"
              style={{ color: agentInfo.color }}
            >
              {agentInfo.icon}
            </div>
          </div>
          
          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span
                className="text-xs font-semibold px-2 py-0.5 rounded-full"
                style={{ backgroundColor: `${agentInfo.color}20`, color: agentInfo.color }}
              >
                {step.agent_name}
              </span>
              <span className="text-xs text-gray-500 dark:text-gray-400">
                Adım {step.step}
              </span>
              {isLatest && (
                <motion.span
                  animate={{ opacity: [1, 0.5, 1] }}
                  transition={{ repeat: Infinity, duration: 1.5 }}
                  className="flex items-center gap-1 text-xs text-purple-500"
                >
                  <Loader2 className="w-3 h-3 animate-spin" />
                  İşleniyor
                </motion.span>
              )}
            </div>
            
            <h4 className="font-medium text-gray-900 dark:text-white text-sm mb-1">
              {step.action.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </h4>
            
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {step.reasoning}
            </p>
            
            {/* Output Preview */}
            {step.output && typeof step.output === 'object' && (
              <div className="mt-3 p-2 bg-gray-50 dark:bg-gray-900/50 rounded-lg">
                <div className="text-xs text-gray-500 mb-1">Çıktı:</div>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(step.output).slice(0, 4).map(([key, value]) => (
                    <span
                      key={key}
                      className="inline-flex items-center gap-1 px-2 py-1 bg-white dark:bg-gray-800 rounded text-xs"
                    >
                      <span className="text-gray-500">{key}:</span>
                      <span className="font-medium text-gray-900 dark:text-white">
                        {typeof value === 'number' ? value.toLocaleString() : 
                         Array.isArray(value) ? value.length + ' öğe' :
                         typeof value === 'string' ? value.slice(0, 20) + (value.length > 20 ? '...' : '') :
                         '...'}
                      </span>
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
};

// ==================== PROGRESS INDICATOR ====================

const PlanningProgress: React.FC<{ currentAgent: string; isComplete: boolean }> = ({ currentAgent, isComplete }) => {
  const agents = [
    'Goal Analyzer',
    'Curriculum Selector',
    'Topic Mapper',
    'Stage Planner',
    'Package Creator',
    'Exam Strategist',
    'Timeline Optimizer',
    'Plan Finalizer'
  ];
  
  const currentIndex = agents.findIndex(a => a === currentAgent);
  const progress = isComplete ? 100 : ((currentIndex + 1) / agents.length) * 100;
  
  return (
    <div className="mb-6">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
          Plan Oluşturuluyor
        </span>
        <span className="text-sm text-gray-500">
          {isComplete ? '✓ Tamamlandı' : `${Math.round(progress)}%`}
        </span>
      </div>
      <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <motion.div
          className="h-full bg-gradient-to-r from-purple-500 to-indigo-600"
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.5 }}
        />
      </div>
      <div className="flex justify-between mt-2">
        {agents.map((agent, i) => (
          <div
            key={agent}
            className={`w-2 h-2 rounded-full transition-colors ${
              i <= currentIndex || isComplete
                ? 'bg-purple-500'
                : 'bg-gray-300 dark:bg-gray-600'
            }`}
            title={agent}
          />
        ))}
      </div>
    </div>
  );
};

// ==================== SUMMARY CARD ====================

const PlanSummaryCard: React.FC<{
  summary: AIThinkingViewProps['planSummary'];
  onViewPlan?: () => void;
}> = ({ summary, onViewPlan }) => {
  if (!summary) return null;
  
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 
                 rounded-2xl p-6 border-2 border-green-500"
    >
      <div className="flex items-center gap-3 mb-4">
        <div className="p-2 bg-green-500 rounded-lg">
          <CheckCircle className="w-6 h-6 text-white" />
        </div>
        <div>
          <h3 className="text-lg font-bold text-gray-900 dark:text-white">
            Planın Hazır! 🎉
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            AI senin için özel bir müfredat oluşturdu
          </p>
        </div>
      </div>
      
      <div className="grid grid-cols-5 gap-4 mb-6">
        <div className="text-center p-3 bg-white/50 dark:bg-gray-800/50 rounded-xl">
          <div className="text-2xl font-bold text-purple-600">{summary.total_stages}</div>
          <div className="text-xs text-gray-500">Stage</div>
        </div>
        <div className="text-center p-3 bg-white/50 dark:bg-gray-800/50 rounded-xl">
          <div className="text-2xl font-bold text-blue-600">{summary.total_packages}</div>
          <div className="text-xs text-gray-500">Paket</div>
        </div>
        <div className="text-center p-3 bg-white/50 dark:bg-gray-800/50 rounded-xl">
          <div className="text-2xl font-bold text-amber-600">{summary.total_exams}</div>
          <div className="text-xs text-gray-500">Sınav</div>
        </div>
        <div className="text-center p-3 bg-white/50 dark:bg-gray-800/50 rounded-xl">
          <div className="text-2xl font-bold text-green-600">{summary.estimated_days}</div>
          <div className="text-xs text-gray-500">Gün</div>
        </div>
        <div className="text-center p-3 bg-white/50 dark:bg-gray-800/50 rounded-xl">
          <div className="text-2xl font-bold text-pink-600">{summary.total_xp.toLocaleString()}</div>
          <div className="text-xs text-gray-500">XP</div>
        </div>
      </div>
      
      {onViewPlan && (
        <button
          onClick={onViewPlan}
          className="w-full py-3 bg-gradient-to-r from-green-500 to-emerald-600 text-white font-semibold
                     rounded-xl hover:shadow-lg hover:shadow-green-500/30 transition-all flex items-center justify-center gap-2"
        >
          <Map className="w-5 h-5" />
          Yolculuk Haritasını Gör
        </button>
      )}
    </motion.div>
  );
};

// ==================== MAIN COMPONENT ====================

const AIThinkingView: React.FC<AIThinkingViewProps> = ({
  steps,
  isComplete,
  planSummary,
  onViewPlan
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  
  // Auto scroll to latest step
  useEffect(() => {
    if (autoScroll && containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [steps, autoScroll]);
  
  const currentAgent = steps.length > 0 ? steps[steps.length - 1].agent_name : '';
  
  return (
    <div className="h-full flex flex-col bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="flex-shrink-0 p-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
        <div className="flex items-center gap-3 mb-4">
          <motion.div
            animate={!isComplete ? { rotate: [0, 360] } : {}}
            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
            className="p-2 bg-gradient-to-r from-purple-500 to-indigo-600 rounded-lg"
          >
            <Brain className="w-6 h-6 text-white" />
          </motion.div>
          <div>
            <h2 className="text-lg font-bold text-gray-900 dark:text-white">
              AI Düşünüyor
            </h2>
            <p className="text-sm text-gray-500">
              Multi-Agent Müfredat Planlama
            </p>
          </div>
        </div>
        
        <PlanningProgress currentAgent={currentAgent} isComplete={isComplete} />
      </div>
      
      {/* Thinking Steps */}
      <div
        ref={containerRef}
        className="flex-1 overflow-y-auto p-4 space-y-6"
        onScroll={(e) => {
          const target = e.target as HTMLDivElement;
          const isAtBottom = target.scrollHeight - target.scrollTop <= target.clientHeight + 50;
          setAutoScroll(isAtBottom);
        }}
      >
        {steps.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <motion.div
              animate={{ scale: [1, 1.1, 1] }}
              transition={{ repeat: Infinity, duration: 2 }}
            >
              <Sparkles className="w-12 h-12 text-purple-500 mb-4" />
            </motion.div>
            <p className="text-gray-600 dark:text-gray-400">
              AI hedefini analiz ediyor...
            </p>
          </div>
        ) : (
          <>
            {steps.map((step, index) => (
              <ThinkingStepCard
                key={step.step}
                step={step}
                index={index}
                isLatest={index === steps.length - 1 && !isComplete}
              />
            ))}
            
            {isComplete && planSummary && (
              <PlanSummaryCard summary={planSummary} onViewPlan={onViewPlan} />
            )}
          </>
        )}
      </div>
      
      {/* Footer Status */}
      {!isComplete && (
        <div className="flex-shrink-0 p-4 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
          <div className="flex items-center gap-3">
            <Loader2 className="w-5 h-5 text-purple-500 animate-spin" />
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {currentAgent ? `${currentAgent} çalışıyor...` : 'Hazırlanıyor...'}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default AIThinkingView;
