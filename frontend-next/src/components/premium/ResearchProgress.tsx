'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search,
  BookOpen,
  CheckCircle,
  Loader2,
  AlertCircle,
  FileSearch,
  Brain,
  FlaskConical,
  FileText,
  Clock,
  Sparkles,
  ChevronDown,
  ChevronUp,
  Shield,
  TrendingUp
} from 'lucide-react';

// ============ TYPES ============

export type ResearchPhase = 
  | 'planning'
  | 'searching'
  | 'extracting'
  | 'analyzing'
  | 'verifying'
  | 'synthesizing'
  | 'refining'
  | 'complete';

export interface ResearchProgressData {
  phase: ResearchPhase;
  iteration: number;
  totalIterations: number;
  message: string;
  sourcesFound?: number;
  evidenceCollected?: number;
  findingsCount?: number;
  confidence?: number;
  elapsedSeconds?: number;
  estimatedRemaining?: number;
  progressPercent?: number;
}

interface ResearchProgressProps {
  progress: ResearchProgressData;
  variant?: 'minimal' | 'compact' | 'detailed';
  showStats?: boolean;
  onCancel?: () => void;
}

// ============ HELPER FUNCTIONS ============

const getPhaseIcon = (phase: ResearchPhase) => {
  const iconProps = { className: "w-5 h-5" };
  
  switch (phase) {
    case 'planning':
      return <Brain {...iconProps} />;
    case 'searching':
      return <Search {...iconProps} />;
    case 'extracting':
      return <FileSearch {...iconProps} />;
    case 'analyzing':
      return <FlaskConical {...iconProps} />;
    case 'verifying':
      return <Shield {...iconProps} />;
    case 'synthesizing':
      return <FileText {...iconProps} />;
    case 'refining':
      return <Sparkles {...iconProps} />;
    case 'complete':
      return <CheckCircle {...iconProps} />;
    default:
      return <Loader2 {...iconProps} className="animate-spin" />;
  }
};

const getPhaseLabel = (phase: ResearchPhase): string => {
  const labels: Record<ResearchPhase, string> = {
    planning: 'Planlama',
    searching: 'Arama',
    extracting: 'Çıkarım',
    analyzing: 'Analiz',
    verifying: 'Doğrulama',
    synthesizing: 'Sentez',
    refining: 'İyileştirme',
    complete: 'Tamamlandı'
  };
  return labels[phase] || phase;
};

const getPhaseColor = (phase: ResearchPhase): string => {
  const colors: Record<ResearchPhase, string> = {
    planning: 'text-purple-400 bg-purple-500/20',
    searching: 'text-blue-400 bg-blue-500/20',
    extracting: 'text-cyan-400 bg-cyan-500/20',
    analyzing: 'text-amber-400 bg-amber-500/20',
    verifying: 'text-green-400 bg-green-500/20',
    synthesizing: 'text-pink-400 bg-pink-500/20',
    refining: 'text-indigo-400 bg-indigo-500/20',
    complete: 'text-emerald-400 bg-emerald-500/20'
  };
  return colors[phase] || 'text-gray-400 bg-gray-500/20';
};

const formatTime = (seconds: number): string => {
  if (seconds < 60) return `${Math.round(seconds)}s`;
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.round(seconds % 60);
  return `${minutes}m ${remainingSeconds}s`;
};

// ============ PHASE STEPS INDICATOR ============

const PhaseSteps: React.FC<{ currentPhase: ResearchPhase }> = ({ currentPhase }) => {
  const phases: ResearchPhase[] = [
    'planning', 'searching', 'extracting', 'analyzing', 
    'verifying', 'synthesizing', 'complete'
  ];
  
  const currentIndex = phases.indexOf(currentPhase);
  
  return (
    <div className="flex items-center gap-1">
      {phases.map((phase, index) => {
        const isActive = index === currentIndex;
        const isComplete = index < currentIndex;
        
        return (
          <React.Fragment key={phase}>
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ 
                scale: isActive ? 1.1 : 1, 
                opacity: 1,
                backgroundColor: isComplete 
                  ? 'rgb(34, 197, 94)' 
                  : isActive 
                    ? 'rgb(59, 130, 246)' 
                    : 'rgba(255, 255, 255, 0.1)'
              }}
              className={`w-2 h-2 rounded-full ${isActive ? 'ring-2 ring-blue-500/30' : ''}`}
              title={getPhaseLabel(phase)}
            />
            {index < phases.length - 1 && (
              <div className={`w-4 h-0.5 ${
                isComplete ? 'bg-green-500' : 'bg-white/10'
              }`} />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
};

// ============ STATS CARD ============

const StatsCard: React.FC<{
  icon: React.ReactNode;
  label: string;
  value: string | number;
  trend?: 'up' | 'down' | 'neutral';
}> = ({ icon, label, value, trend }) => (
  <div className="flex items-center gap-3 p-3 rounded-lg bg-white/[0.03] border border-white/5">
    <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center text-white/60">
      {icon}
    </div>
    <div>
      <div className="text-lg font-semibold text-white/90 flex items-center gap-1">
        {value}
        {trend === 'up' && <TrendingUp className="w-3 h-3 text-green-400" />}
      </div>
      <div className="text-xs text-white/40">{label}</div>
    </div>
  </div>
);

// ============ MINIMAL VARIANT ============

const MinimalProgress: React.FC<ResearchProgressProps> = ({ progress }) => (
  <motion.div
    initial={{ opacity: 0, y: -10 }}
    animate={{ opacity: 1, y: 0 }}
    className="flex items-center gap-3"
  >
    <div className={`p-1.5 rounded-lg ${getPhaseColor(progress.phase)}`}>
      {progress.phase === 'complete' ? (
        getPhaseIcon(progress.phase)
      ) : (
        <Loader2 className="w-4 h-4 animate-spin" />
      )}
    </div>
    <span className="text-sm text-white/70">{progress.message}</span>
    {progress.confidence !== undefined && progress.confidence > 0 && (
      <span className="text-xs text-white/50 px-2 py-0.5 rounded-full bg-white/10">
        {Math.round(progress.confidence * 100)}% güven
      </span>
    )}
  </motion.div>
);

// ============ COMPACT VARIANT ============

const CompactProgress: React.FC<ResearchProgressProps> = ({ progress, showStats }) => {
  const percent = progress.progressPercent || 
    Math.round((progress.iteration / Math.max(1, progress.totalIterations)) * 100);
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-3 p-4 rounded-xl bg-white/[0.02] border border-white/5"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${getPhaseColor(progress.phase)}`}>
            {progress.phase === 'complete' ? (
              getPhaseIcon(progress.phase)
            ) : (
              <Loader2 className="w-5 h-5 animate-spin" />
            )}
          </div>
          <div>
            <div className="font-medium text-white/90">
              {getPhaseLabel(progress.phase)}
            </div>
            <div className="text-xs text-white/50">
              İterasyon {progress.iteration}/{progress.totalIterations}
            </div>
          </div>
        </div>
        
        <div className="text-right">
          <div className="text-2xl font-bold text-white/90">{percent}%</div>
          {progress.elapsedSeconds !== undefined && (
            <div className="text-xs text-white/40 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {formatTime(progress.elapsedSeconds)}
            </div>
          )}
        </div>
      </div>
      
      {/* Progress Bar */}
      <div className="relative h-2 rounded-full bg-white/10 overflow-hidden">
        <motion.div
          className="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-blue-500 to-purple-500"
          initial={{ width: 0 }}
          animate={{ width: `${percent}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
        />
        {progress.phase !== 'complete' && (
          <motion.div
            className="absolute inset-y-0 w-20 bg-gradient-to-r from-transparent via-white/30 to-transparent"
            animate={{ x: ['0%', '500%'] }}
            transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
          />
        )}
      </div>
      
      {/* Message */}
      <div className="text-sm text-white/60">{progress.message}</div>
      
      {/* Mini Stats */}
      {showStats && (
        <div className="flex items-center gap-4 text-xs text-white/40">
          {progress.sourcesFound !== undefined && progress.sourcesFound > 0 && (
            <span className="flex items-center gap-1">
              <Search className="w-3 h-3" />
              {progress.sourcesFound} kaynak
            </span>
          )}
          {progress.evidenceCollected !== undefined && progress.evidenceCollected > 0 && (
            <span className="flex items-center gap-1">
              <FileSearch className="w-3 h-3" />
              {progress.evidenceCollected} kanıt
            </span>
          )}
          {progress.findingsCount !== undefined && progress.findingsCount > 0 && (
            <span className="flex items-center gap-1">
              <CheckCircle className="w-3 h-3" />
              {progress.findingsCount} bulgu
            </span>
          )}
        </div>
      )}
    </motion.div>
  );
};

// ============ DETAILED VARIANT ============

const DetailedProgress: React.FC<ResearchProgressProps> = ({ 
  progress, 
  showStats = true,
  onCancel 
}) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const percent = progress.progressPercent || 
    Math.round((progress.iteration / Math.max(1, progress.totalIterations)) * 100);
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl bg-gradient-to-br from-white/[0.05] to-white/[0.02] 
                 border border-white/10 overflow-hidden"
    >
      {/* Header */}
      <div className="p-4 border-b border-white/5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`relative p-3 rounded-xl ${getPhaseColor(progress.phase)}`}>
              {progress.phase === 'complete' ? (
                <CheckCircle className="w-6 h-6" />
              ) : (
                <>
                  {getPhaseIcon(progress.phase)}
                  <motion.div
                    className="absolute inset-0 rounded-xl border-2 border-current"
                    animate={{ scale: [1, 1.2, 1], opacity: [0.5, 0, 0.5] }}
                    transition={{ duration: 2, repeat: Infinity }}
                  />
                </>
              )}
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white/90">
                {progress.phase === 'complete' ? 'Araştırma Tamamlandı' : 'Araştırma Devam Ediyor'}
              </h3>
              <p className="text-sm text-white/50">
                {getPhaseLabel(progress.phase)} • İterasyon {progress.iteration}/{progress.totalIterations}
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            {progress.confidence !== undefined && progress.confidence > 0 && (
              <div className="text-center">
                <div className="text-2xl font-bold text-white/90">
                  {Math.round(progress.confidence * 100)}%
                </div>
                <div className="text-xs text-white/40">Güven</div>
              </div>
            )}
            
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-2 rounded-lg hover:bg-white/10 transition-colors"
            >
              {isExpanded ? (
                <ChevronUp className="w-5 h-5 text-white/50" />
              ) : (
                <ChevronDown className="w-5 h-5 text-white/50" />
              )}
            </button>
          </div>
        </div>
        
        {/* Phase indicators */}
        <div className="mt-4">
          <PhaseSteps currentPhase={progress.phase} />
        </div>
      </div>
      
      {/* Expandable content */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
          >
            {/* Progress bar */}
            <div className="px-4 pt-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-white/60">İlerleme</span>
                <span className="text-sm font-medium text-white/80">{percent}%</span>
              </div>
              <div className="relative h-3 rounded-full bg-white/10 overflow-hidden">
                <motion.div
                  className="absolute inset-y-0 left-0 rounded-full"
                  style={{
                    background: 'linear-gradient(90deg, #3B82F6, #8B5CF6, #EC4899)'
                  }}
                  initial={{ width: 0 }}
                  animate={{ width: `${percent}%` }}
                  transition={{ duration: 0.5, ease: 'easeOut' }}
                />
                {progress.phase !== 'complete' && (
                  <motion.div
                    className="absolute inset-y-0 w-32 bg-gradient-to-r from-transparent via-white/40 to-transparent"
                    animate={{ x: ['-100%', '400%'] }}
                    transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                  />
                )}
              </div>
            </div>
            
            {/* Current message */}
            <div className="px-4 py-3">
              <div className="flex items-start gap-3 p-3 rounded-lg bg-white/[0.03]">
                {progress.phase === 'complete' ? (
                  <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                ) : (
                  <Loader2 className="w-5 h-5 text-blue-400 animate-spin flex-shrink-0 mt-0.5" />
                )}
                <p className="text-sm text-white/70">{progress.message}</p>
              </div>
            </div>
            
            {/* Stats */}
            {showStats && (
              <div className="px-4 pb-4 grid grid-cols-2 sm:grid-cols-4 gap-3">
                <StatsCard
                  icon={<Search className="w-4 h-4" />}
                  label="Kaynaklar"
                  value={progress.sourcesFound || 0}
                  trend={progress.sourcesFound && progress.sourcesFound > 0 ? 'up' : 'neutral'}
                />
                <StatsCard
                  icon={<FileSearch className="w-4 h-4" />}
                  label="Kanıtlar"
                  value={progress.evidenceCollected || 0}
                />
                <StatsCard
                  icon={<CheckCircle className="w-4 h-4" />}
                  label="Bulgular"
                  value={progress.findingsCount || 0}
                />
                <StatsCard
                  icon={<Clock className="w-4 h-4" />}
                  label="Süre"
                  value={formatTime(progress.elapsedSeconds || 0)}
                />
              </div>
            )}
            
            {/* Estimated time */}
            {progress.estimatedRemaining !== undefined && progress.estimatedRemaining > 0 && (
              <div className="px-4 pb-4">
                <div className="flex items-center justify-center gap-2 text-xs text-white/40">
                  <Clock className="w-3 h-3" />
                  Tahmini kalan süre: {formatTime(progress.estimatedRemaining)}
                </div>
              </div>
            )}
            
            {/* Cancel button */}
            {onCancel && progress.phase !== 'complete' && (
              <div className="px-4 pb-4">
                <button
                  onClick={onCancel}
                  className="w-full py-2 rounded-lg border border-red-500/30 text-red-400 
                             hover:bg-red-500/10 transition-colors text-sm"
                >
                  Araştırmayı İptal Et
                </button>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

// ============ MAIN COMPONENT ============

export const ResearchProgress: React.FC<ResearchProgressProps> = (props) => {
  const { variant = 'compact' } = props;
  
  switch (variant) {
    case 'minimal':
      return <MinimalProgress {...props} />;
    case 'detailed':
      return <DetailedProgress {...props} />;
    default:
      return <CompactProgress {...props} />;
  }
};

export default ResearchProgress;
