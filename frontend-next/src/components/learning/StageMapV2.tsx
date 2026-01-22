'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Map,
  Star,
  Lock,
  CheckCircle,
  Play,
  Clock,
  Trophy,
  Package,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Target,
  BookOpen,
  Zap,
  Award,
  AlertCircle
} from 'lucide-react';

// ==================== TYPES ====================

type PackageType = 'intro' | 'learning' | 'practice' | 'review' | 'exam' | 'closure';
type PackageStatus = 'locked' | 'available' | 'in_progress' | 'completed';
type StageStatus = 'locked' | 'available' | 'in_progress' | 'completed';

interface PackagePreview {
  id: string;
  number: number;
  title: string;
  type: PackageType;
  status: PackageStatus;
  xp_reward: number;
  estimated_minutes: number;
  topics: string[];
}

interface StageData {
  id: string;
  number: number;
  title: string;
  description: string;
  status: StageStatus;
  theme_color: string;
  icon: string;
  packages: PackagePreview[];
  xp_total: number;
  xp_earned: number;
  completion_percentage: number;
}

interface JourneyProgressData {
  journey_id: string;
  title: string;
  current_stage: number;
  total_stages: number;
  total_xp: number;
  earned_xp: number;
  stages: StageData[];
}

interface StageMapV2Props {
  journey: JourneyProgressData;
  onPackageClick: (stageId: string, packageId: string) => void;
  onStageClick?: (stageId: string) => void;
}

// ==================== PACKAGE TYPE INFO ====================

const PACKAGE_TYPE_INFO: Record<PackageType, { icon: string; label: string; color: string }> = {
  intro: { icon: '🎯', label: 'Giriş', color: '#6366F1' },
  learning: { icon: '📚', label: 'Öğrenme', color: '#3B82F6' },
  practice: { icon: '✏️', label: 'Pratik', color: '#F59E0B' },
  review: { icon: '🔄', label: 'Tekrar', color: '#8B5CF6' },
  exam: { icon: '📝', label: 'Sınav', color: '#EF4444' },
  closure: { icon: '🏆', label: 'Final', color: '#10B981' },
};

const STATUS_COLORS = {
  locked: 'bg-gray-400',
  available: 'bg-blue-500',
  in_progress: 'bg-amber-500',
  completed: 'bg-green-500',
};

// ==================== PACKAGE CARD ====================

const PackageCard: React.FC<{
  pkg: PackagePreview;
  stageColor: string;
  onClick: () => void;
}> = ({ pkg, stageColor, onClick }) => {
  const typeInfo = PACKAGE_TYPE_INFO[pkg.type];
  const isLocked = pkg.status === 'locked';
  const isCompleted = pkg.status === 'completed';
  
  return (
    <motion.button
      onClick={onClick}
      disabled={isLocked}
      whileHover={!isLocked ? { scale: 1.02, y: -2 } : undefined}
      whileTap={!isLocked ? { scale: 0.98 } : undefined}
      className={`w-full p-4 rounded-xl text-left transition-all ${
        isLocked
          ? 'bg-gray-100 dark:bg-gray-800 opacity-60 cursor-not-allowed'
          : isCompleted
            ? 'bg-green-50 dark:bg-green-900/20 border-2 border-green-500'
            : 'bg-white dark:bg-gray-800 border-2 border-gray-200 dark:border-gray-700 hover:border-blue-500 dark:hover:border-blue-500 hover:shadow-lg'
      }`}
    >
      <div className="flex items-start gap-3">
        {/* Status Icon */}
        <div className={`relative flex-shrink-0`}>
          <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-2xl
                          ${isLocked 
                            ? 'bg-gray-200 dark:bg-gray-700' 
                            : isCompleted 
                              ? 'bg-green-100 dark:bg-green-900/30' 
                              : 'bg-blue-50 dark:bg-blue-900/30'}`}>
            {isLocked ? (
              <Lock className="w-5 h-5 text-gray-400" />
            ) : (
              typeInfo.icon
            )}
          </div>
          
          {/* Status Badge */}
          {!isLocked && (
            <div className={`absolute -bottom-1 -right-1 w-5 h-5 rounded-full flex items-center justify-center
                            ${isCompleted ? 'bg-green-500' : pkg.status === 'in_progress' ? 'bg-amber-500' : 'bg-blue-500'}`}>
              {isCompleted ? (
                <CheckCircle className="w-3 h-3 text-white" />
              ) : pkg.status === 'in_progress' ? (
                <Play className="w-3 h-3 text-white fill-white" />
              ) : (
                <ChevronDown className="w-3 h-3 text-white" />
              )}
            </div>
          )}
        </div>
        
        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium px-2 py-0.5 rounded-full"
                  style={{ backgroundColor: `${typeInfo.color}20`, color: typeInfo.color }}>
              {typeInfo.label}
            </span>
            <span className="text-xs text-gray-500">#{pkg.number}</span>
          </div>
          
          <h4 className="font-medium text-gray-900 dark:text-white mt-1 truncate">
            {pkg.title}
          </h4>
          
          <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {pkg.estimated_minutes} dk
            </span>
            <span className="flex items-center gap-1">
              <Star className="w-3 h-3 text-amber-500" />
              {pkg.xp_reward} XP
            </span>
          </div>
        </div>
      </div>
    </motion.button>
  );
};

// ==================== STAGE CARD ====================

const StageCard: React.FC<{
  stage: StageData;
  isExpanded: boolean;
  onToggle: () => void;
  onPackageClick: (packageId: string) => void;
}> = ({ stage, isExpanded, onToggle, onPackageClick }) => {
  const isLocked = stage.status === 'locked';
  const isCompleted = stage.status === 'completed';
  const completedPackages = stage.packages.filter(p => p.status === 'completed').length;
  
  return (
    <motion.div
      layout
      className={`rounded-2xl overflow-hidden border-2 transition-all ${
        isLocked
          ? 'border-gray-300 dark:border-gray-700 opacity-60'
          : isCompleted
            ? 'border-green-500 shadow-lg shadow-green-500/20'
            : stage.status === 'in_progress'
              ? 'border-amber-500 shadow-lg shadow-amber-500/20'
              : 'border-blue-500 shadow-lg shadow-blue-500/20'
      }`}
    >
      {/* Header */}
      <button
        onClick={onToggle}
        disabled={isLocked}
        className={`w-full p-4 flex items-center gap-4 text-left ${
          isLocked
            ? 'bg-gray-50 dark:bg-gray-800 cursor-not-allowed'
            : 'bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700/50'
        }`}
        style={{
          borderLeft: !isLocked ? `4px solid ${stage.theme_color}` : undefined
        }}
      >
        {/* Stage Icon */}
        <div className={`w-16 h-16 rounded-2xl flex items-center justify-center text-3xl
                        ${isLocked ? 'bg-gray-200 dark:bg-gray-700' : ''}`}
             style={{ backgroundColor: !isLocked ? `${stage.theme_color}20` : undefined }}>
          {isLocked ? (
            <Lock className="w-6 h-6 text-gray-400" />
          ) : (
            stage.icon
          )}
        </div>
        
        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold px-2 py-0.5 rounded-full text-white"
                  style={{ backgroundColor: isLocked ? '#9CA3AF' : stage.theme_color }}>
              AŞAMA {stage.number}
            </span>
            {isCompleted && (
              <span className="flex items-center gap-1 text-xs text-green-500">
                <CheckCircle className="w-3 h-3" />
                Tamamlandı
              </span>
            )}
          </div>
          
          <h3 className="text-lg font-bold text-gray-900 dark:text-white mt-1 truncate">
            {stage.title}
          </h3>
          
          <p className="text-sm text-gray-500 truncate">
            {stage.description}
          </p>
          
          {/* Progress */}
          <div className="flex items-center gap-4 mt-2">
            <div className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <motion.div
                className="h-full rounded-full"
                style={{ backgroundColor: stage.theme_color }}
                initial={{ width: 0 }}
                animate={{ width: `${stage.completion_percentage}%` }}
              />
            </div>
            <span className="text-sm font-medium" style={{ color: stage.theme_color }}>
              {stage.completion_percentage}%
            </span>
          </div>
          
          {/* Stats */}
          <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
            <span>{completedPackages}/{stage.packages.length} paket</span>
            <span className="flex items-center gap-1">
              <Star className="w-3 h-3 text-amber-500" />
              {stage.xp_earned}/{stage.xp_total} XP
            </span>
          </div>
        </div>
        
        {/* Expand Button */}
        {!isLocked && (
          <div className={`p-2 rounded-full transition-colors ${
            isExpanded ? 'bg-gray-200 dark:bg-gray-700' : 'hover:bg-gray-100 dark:hover:bg-gray-700'
          }`}>
            {isExpanded ? (
              <ChevronUp className="w-5 h-5 text-gray-500" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-500" />
            )}
          </div>
        )}
      </button>
      
      {/* Packages */}
      <AnimatePresence>
        {isExpanded && !isLocked && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t border-gray-200 dark:border-gray-700"
          >
            <div className="p-4 grid gap-3">
              {stage.packages.map(pkg => (
                <PackageCard
                  key={pkg.id}
                  pkg={pkg}
                  stageColor={stage.theme_color}
                  onClick={() => onPackageClick(pkg.id)}
                />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

// ==================== JOURNEY HEADER ====================

const JourneyHeader: React.FC<{
  journey: JourneyProgressData;
}> = ({ journey }) => {
  const progressPercentage = Math.round((journey.earned_xp / journey.total_xp) * 100);
  
  return (
    <div className="bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 rounded-3xl p-6 text-white">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold">{journey.title}</h1>
          <p className="text-white/80 mt-1">
            Aşama {journey.current_stage}/{journey.total_stages}
          </p>
        </div>
        
        <div className="text-right">
          <div className="flex items-center gap-1 text-amber-300">
            <Star className="w-5 h-5 fill-amber-300" />
            <span className="text-xl font-bold">{journey.earned_xp}</span>
          </div>
          <p className="text-xs text-white/60">/ {journey.total_xp} XP</p>
        </div>
      </div>
      
      {/* Progress Bar */}
      <div className="mt-4">
        <div className="flex justify-between text-sm mb-1">
          <span className="text-white/80">Genel İlerleme</span>
          <span className="font-bold">{progressPercentage}%</span>
        </div>
        <div className="h-3 bg-white/20 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-white rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${progressPercentage}%` }}
          />
        </div>
      </div>
      
      {/* Quick Stats */}
      <div className="mt-4 grid grid-cols-3 gap-4">
        {[
          { icon: <Target className="w-4 h-4" />, value: journey.total_stages, label: 'Aşama' },
          { icon: <Package className="w-4 h-4" />, value: journey.stages.reduce((acc, s) => acc + s.packages.length, 0), label: 'Paket' },
          { icon: <Trophy className="w-4 h-4" />, value: journey.stages.reduce((acc, s) => acc + s.packages.filter(p => p.type === 'exam').length, 0), label: 'Sınav' },
        ].map((stat, i) => (
          <div key={i} className="text-center bg-white/10 rounded-xl p-2">
            <div className="flex justify-center">{stat.icon}</div>
            <div className="font-bold">{stat.value}</div>
            <div className="text-xs text-white/60">{stat.label}</div>
          </div>
        ))}
      </div>
    </div>
  );
};

// ==================== MAIN STAGE MAP V2 ====================

const StageMapV2: React.FC<StageMapV2Props> = ({
  journey,
  onPackageClick,
  onStageClick
}) => {
  const [expandedStage, setExpandedStage] = useState<string | null>(null);
  
  // Auto-expand current stage
  useEffect(() => {
    const currentStage = journey.stages.find(s => s.status === 'in_progress' || s.status === 'available');
    if (currentStage && !expandedStage) {
      setExpandedStage(currentStage.id);
    }
  }, [journey.stages, expandedStage]);
  
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 pb-8">
      {/* Header */}
      <div className="p-4">
        <JourneyHeader journey={journey} />
      </div>
      
      {/* Stage List */}
      <div className="px-4 space-y-4 mt-4">
        {journey.stages.map((stage, index) => (
          <React.Fragment key={stage.id}>
            {/* Connection Line */}
            {index > 0 && (
              <div className="flex justify-center">
                <div className={`w-1 h-8 rounded-full ${
                  stage.status === 'locked' ? 'bg-gray-300 dark:bg-gray-700' : 'bg-gradient-to-b from-green-500 to-blue-500'
                }`} />
              </div>
            )}
            
            <StageCard
              stage={stage}
              isExpanded={expandedStage === stage.id}
              onToggle={() => {
                setExpandedStage(expandedStage === stage.id ? null : stage.id);
                onStageClick?.(stage.id);
              }}
              onPackageClick={(packageId) => onPackageClick(stage.id, packageId)}
            />
          </React.Fragment>
        ))}
      </div>
      
      {/* Completion Banner (if all completed) */}
      {journey.stages.every(s => s.status === 'completed') && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mx-4 mt-8 p-6 bg-gradient-to-r from-green-500 to-emerald-600 rounded-2xl text-white text-center"
        >
          <Award className="w-12 h-12 mx-auto mb-2" />
          <h3 className="text-xl font-bold">🎉 Tebrikler! Yolculuğu Tamamladın!</h3>
          <p className="text-white/80 mt-1">Sertifikanı almak için tıkla</p>
        </motion.div>
      )}
    </div>
  );
};

export default StageMapV2;
