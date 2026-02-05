'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Brain,
  Lightbulb,
  GitBranch,
  Target,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  Clock,
  Sparkles,
  ArrowRight,
  MessageSquare,
  AlertCircle,
  Info
} from 'lucide-react';

// ============ TYPES ============

export type ThinkingPhase = 
  | 'understanding'
  | 'planning'
  | 'decomposing'
  | 'analyzing'
  | 'synthesizing'
  | 'verifying'
  | 'reflecting'
  | 'concluding';

export interface ThinkingStep {
  phase: ThinkingPhase;
  content: string;
  confidence?: number;
  durationMs?: number;
  subSteps?: ThinkingStep[];
  sources?: string[];
}

export interface ChainOfThought {
  question: string;
  steps: ThinkingStep[];
  finalAnswer: string;
  overallConfidence: number;
  totalTimeMs: number;
}

interface ThinkingStepsProps {
  chainOfThought: ChainOfThought;
  variant?: 'timeline' | 'cards' | 'tree' | 'minimal';
  isStreaming?: boolean;
  showConfidence?: boolean;
  onStepClick?: (step: ThinkingStep, index: number) => void;
}

// ============ HELPER FUNCTIONS ============

const getPhaseIcon = (phase: ThinkingPhase) => {
  const icons: Record<ThinkingPhase, React.ReactNode> = {
    understanding: <MessageSquare className="w-4 h-4" />,
    planning: <Target className="w-4 h-4" />,
    decomposing: <GitBranch className="w-4 h-4" />,
    analyzing: <Brain className="w-4 h-4" />,
    synthesizing: <Sparkles className="w-4 h-4" />,
    verifying: <CheckCircle className="w-4 h-4" />,
    reflecting: <Info className="w-4 h-4" />,
    concluding: <Lightbulb className="w-4 h-4" />
  };
  return icons[phase];
};

const getPhaseLabel = (phase: ThinkingPhase): string => {
  const labels: Record<ThinkingPhase, string> = {
    understanding: 'Anlama',
    planning: 'Planlama',
    decomposing: 'Ayrıştırma',
    analyzing: 'Analiz',
    synthesizing: 'Sentez',
    verifying: 'Doğrulama',
    reflecting: 'Değerlendirme',
    concluding: 'Sonuçlandırma'
  };
  return labels[phase];
};

const getPhaseColor = (phase: ThinkingPhase): string => {
  const colors: Record<ThinkingPhase, string> = {
    understanding: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    planning: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    decomposing: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
    analyzing: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    synthesizing: 'bg-pink-500/20 text-pink-400 border-pink-500/30',
    verifying: 'bg-green-500/20 text-green-400 border-green-500/30',
    reflecting: 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30',
    concluding: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
  };
  return colors[phase];
};

const getConfidenceColor = (confidence: number): string => {
  if (confidence >= 0.8) return 'text-green-400';
  if (confidence >= 0.6) return 'text-yellow-400';
  if (confidence >= 0.4) return 'text-orange-400';
  return 'text-red-400';
};

// ============ TIMELINE VARIANT ============

const TimelineStep: React.FC<{
  step: ThinkingStep;
  index: number;
  isLast: boolean;
  isStreaming: boolean;
  showConfidence: boolean;
  onClick?: () => void;
}> = ({ step, index, isLast, isStreaming, showConfidence, onClick }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const hasSubSteps = step.subSteps && step.subSteps.length > 0;
  
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.1 }}
      className="relative"
    >
      {/* Timeline line */}
      {!isLast && (
        <div className="absolute left-5 top-10 w-0.5 h-[calc(100%-2rem)] bg-gradient-to-b from-white/20 to-transparent" />
      )}
      
      {/* Step content */}
      <div 
        className="flex gap-4 cursor-pointer group"
        onClick={() => {
          setIsExpanded(!isExpanded);
          onClick?.();
        }}
      >
        {/* Icon */}
        <div className={`relative flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center
                        ${getPhaseColor(step.phase)} border`}>
          {getPhaseIcon(step.phase)}
          {isStreaming && isLast && (
            <motion.div
              className="absolute inset-0 rounded-xl border-2 border-current"
              animate={{ scale: [1, 1.3, 1], opacity: [0.5, 0, 0.5] }}
              transition={{ duration: 1.5, repeat: Infinity }}
            />
          )}
        </div>
        
        {/* Content */}
        <div className="flex-1 pb-6">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-medium text-white/90">
              {getPhaseLabel(step.phase)}
            </span>
            {showConfidence && step.confidence !== undefined && (
              <span className={`text-xs ${getConfidenceColor(step.confidence)}`}>
                {Math.round(step.confidence * 100)}%
              </span>
            )}
            {step.durationMs !== undefined && (
              <span className="text-xs text-white/40 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {step.durationMs}ms
              </span>
            )}
            {hasSubSteps && (
              <button className="ml-auto p-1 rounded hover:bg-white/10 transition-colors">
                {isExpanded ? (
                  <ChevronUp className="w-4 h-4 text-white/50" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-white/50" />
                )}
              </button>
            )}
          </div>
          
          <p className="text-sm text-white/70 leading-relaxed">
            {step.content}
          </p>
          
          {/* Sub-steps */}
          <AnimatePresence>
            {isExpanded && hasSubSteps && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="mt-3 ml-4 border-l-2 border-white/10 pl-4 space-y-3"
              >
                {step.subSteps!.map((subStep, subIndex) => (
                  <div key={subIndex} className="flex items-start gap-2">
                    <ArrowRight className="w-4 h-4 text-white/30 flex-shrink-0 mt-0.5" />
                    <p className="text-xs text-white/60">{subStep.content}</p>
                  </div>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  );
};

const TimelineView: React.FC<ThinkingStepsProps> = ({
  chainOfThought,
  isStreaming = false,
  showConfidence = true,
  onStepClick
}) => {
  const scrollRef = useRef<HTMLDivElement>(null);
  
  // Auto-scroll to latest step when streaming
  useEffect(() => {
    if (isStreaming && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [chainOfThought.steps.length, isStreaming]);
  
  return (
    <div className="space-y-4">
      {/* Question */}
      <div className="p-4 rounded-xl bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-white/10">
        <div className="flex items-center gap-2 mb-2">
          <MessageSquare className="w-4 h-4 text-blue-400" />
          <span className="text-sm font-medium text-white/80">Soru</span>
        </div>
        <p className="text-white/90">{chainOfThought.question}</p>
      </div>
      
      {/* Steps */}
      <div ref={scrollRef} className="max-h-[500px] overflow-y-auto pr-2 space-y-1">
        {chainOfThought.steps.map((step, index) => (
          <TimelineStep
            key={`${step.phase}-${index}`}
            step={step}
            index={index}
            isLast={index === chainOfThought.steps.length - 1}
            isStreaming={isStreaming}
            showConfidence={showConfidence}
            onClick={() => onStepClick?.(step, index)}
          />
        ))}
      </div>
      
      {/* Final Answer */}
      {chainOfThought.finalAnswer && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 rounded-xl bg-gradient-to-r from-emerald-500/10 to-green-500/10 
                     border border-emerald-500/20"
        >
          <div className="flex items-center gap-2 mb-2">
            <Lightbulb className="w-4 h-4 text-emerald-400" />
            <span className="text-sm font-medium text-emerald-300">Sonuç</span>
            {showConfidence && (
              <span className={`ml-auto text-xs ${getConfidenceColor(chainOfThought.overallConfidence)}`}>
                Güven: {Math.round(chainOfThought.overallConfidence * 100)}%
              </span>
            )}
          </div>
          <p className="text-white/90">{chainOfThought.finalAnswer}</p>
          
          <div className="mt-3 pt-3 border-t border-white/10 flex items-center gap-4 text-xs text-white/40">
            <span className="flex items-center gap-1">
              <Brain className="w-3 h-3" />
              {chainOfThought.steps.length} adım
            </span>
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {Math.round(chainOfThought.totalTimeMs / 1000)}s
            </span>
          </div>
        </motion.div>
      )}
    </div>
  );
};

// ============ CARDS VARIANT ============

const CardsView: React.FC<ThinkingStepsProps> = ({
  chainOfThought,
  isStreaming = false,
  showConfidence = true,
  onStepClick
}) => {
  return (
    <div className="space-y-4">
      {/* Question */}
      <div className="text-center p-4 rounded-xl bg-white/[0.03] border border-white/10">
        <p className="text-white/90">{chainOfThought.question}</p>
      </div>
      
      {/* Steps as cards */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {chainOfThought.steps.map((step, index) => (
          <motion.div
            key={`${step.phase}-${index}`}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.1 }}
            onClick={() => onStepClick?.(step, index)}
            className={`group p-4 rounded-xl cursor-pointer
                       bg-gradient-to-br from-white/[0.05] to-transparent
                       border transition-all hover:scale-[1.02]
                       ${getPhaseColor(step.phase)}`}
          >
            <div className="flex items-center gap-2 mb-2">
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${getPhaseColor(step.phase)}`}>
                {getPhaseIcon(step.phase)}
              </div>
              <span className="font-medium text-white/90 text-sm">
                {getPhaseLabel(step.phase)}
              </span>
              {isStreaming && index === chainOfThought.steps.length - 1 && (
                <motion.div
                  className="ml-auto w-2 h-2 rounded-full bg-blue-400"
                  animate={{ opacity: [1, 0.3, 1] }}
                  transition={{ duration: 1, repeat: Infinity }}
                />
              )}
            </div>
            
            <p className="text-xs text-white/60 line-clamp-3">
              {step.content}
            </p>
            
            {showConfidence && step.confidence !== undefined && (
              <div className="mt-2 flex items-center gap-1">
                <div className="flex-1 h-1 rounded-full bg-white/10 overflow-hidden">
                  <motion.div
                    className="h-full bg-current"
                    initial={{ width: 0 }}
                    animate={{ width: `${step.confidence * 100}%` }}
                  />
                </div>
                <span className={`text-xs ${getConfidenceColor(step.confidence)}`}>
                  {Math.round(step.confidence * 100)}%
                </span>
              </div>
            )}
          </motion.div>
        ))}
      </div>
      
      {/* Final Answer */}
      {chainOfThought.finalAnswer && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 rounded-xl bg-gradient-to-r from-emerald-500/20 to-green-500/10 
                     border border-emerald-500/20"
        >
          <div className="flex items-center gap-2 mb-2">
            <Lightbulb className="w-5 h-5 text-emerald-400" />
            <span className="font-medium text-emerald-300">Sonuç</span>
          </div>
          <p className="text-white/90">{chainOfThought.finalAnswer}</p>
        </motion.div>
      )}
    </div>
  );
};

// ============ MINIMAL VARIANT ============

const MinimalView: React.FC<ThinkingStepsProps> = ({
  chainOfThought,
  isStreaming = false,
  showConfidence = true
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  return (
    <div className="space-y-2">
      {/* Collapsed header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-3 rounded-lg 
                   bg-white/[0.03] hover:bg-white/[0.05] transition-colors"
      >
        <div className="flex items-center gap-2">
          <Brain className="w-4 h-4 text-purple-400" />
          <span className="text-sm text-white/70">
            {isStreaming ? 'Düşünüyor...' : `${chainOfThought.steps.length} düşünme adımı`}
          </span>
          {isStreaming && (
            <motion.div
              className="w-2 h-2 rounded-full bg-purple-400"
              animate={{ opacity: [1, 0.3, 1] }}
              transition={{ duration: 1, repeat: Infinity }}
            />
          )}
        </div>
        
        <div className="flex items-center gap-2">
          {showConfidence && chainOfThought.overallConfidence > 0 && (
            <span className={`text-xs ${getConfidenceColor(chainOfThought.overallConfidence)}`}>
              {Math.round(chainOfThought.overallConfidence * 100)}% güven
            </span>
          )}
          {isExpanded ? (
            <ChevronUp className="w-4 h-4 text-white/50" />
          ) : (
            <ChevronDown className="w-4 h-4 text-white/50" />
          )}
        </div>
      </button>
      
      {/* Expanded content */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="space-y-2 pl-6 border-l-2 border-purple-500/30">
              {chainOfThought.steps.map((step, index) => (
                <div key={index} className="flex items-start gap-2">
                  <span className={`text-xs font-medium ${getPhaseColor(step.phase).split(' ')[1]}`}>
                    {getPhaseLabel(step.phase)}:
                  </span>
                  <span className="text-xs text-white/60 line-clamp-2">
                    {step.content}
                  </span>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

// ============ MAIN COMPONENT ============

export const ThinkingSteps: React.FC<ThinkingStepsProps> = (props) => {
  const { variant = 'timeline' } = props;
  
  switch (variant) {
    case 'cards':
      return <CardsView {...props} />;
    case 'minimal':
      return <MinimalView {...props} />;
    default:
      return <TimelineView {...props} />;
  }
};

export default ThinkingSteps;
