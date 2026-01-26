'use client';

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  TrendingUp,
  Target,
  Clock,
  Brain,
  Zap,
  ChevronRight,
  AlertTriangle
} from 'lucide-react';

// ==================== TYPES ====================

interface TopicMastery {
  topic_id: string;
  topic_name: string;
  score: number;
  level: 'novice' | 'learning' | 'developing' | 'proficient' | 'mastered';
  confidence: number;
  total_attempts: number;
  correct_attempts: number;
  average_score: number;
  xp_earned: number;
  retention_rate: number;
}

interface MasterySummary {
  user: {
    total_xp: number;
    level: number;
    next_level_xp: number;
  };
  topics: {
    total: number;
    mastered: number;
    percentage: number;
  };
  packages: {
    total: number;
    completed: number;
    percentage: number;
  };
  stages: {
    total: number;
    completed: number;
    percentage: number;
  };
  spaced_repetition: {
    total_items: number;
    mastered_count: number;
    due_today: number;
    overdue_count: number;
    average_retention: number;
  };
}

interface WeaknessSummary {
  total_signals: number;
  by_severity: {
    critical: number;
    moderate: number;
    mild: number;
  };
  affected_topics: number;
  clusters: Array<{
    id: string;
    name: string;
    priority: number;
    severity: number;
    topic_count: number;
    recommendations: string[];
  }>;
  top_priority_topics: Array<{
    topic_id: string;
    severity: number;
    signal_count: number;
  }>;
}

interface MasteryProgressProps {
  onTopicClick?: (topicId: string) => void;
  showWeakness?: boolean;
  compact?: boolean;
}

// ==================== LEVEL CONFIG ====================

const LEVEL_CONFIG = {
  novice: { color: '#6B7280', label: 'Başlangıç', icon: '🌱' },
  learning: { color: '#3B82F6', label: 'Öğreniyor', icon: '📚' },
  developing: { color: '#F59E0B', label: 'Gelişiyor', icon: '🚀' },
  proficient: { color: '#10B981', label: 'Yetkin', icon: '⭐' },
  mastered: { color: '#8B5CF6', label: 'Usta', icon: '🏆' }
};

// ==================== XP PROGRESS BAR ====================

const XPProgressBar: React.FC<{
  currentXP: number;
  level: number;
  nextLevelXP: number;
}> = ({ currentXP, level, nextLevelXP }) => {
  const _levelXP = level * 1000; // Used for future calculations
  const progressInLevel = currentXP - (level - 1) * 1000;
  const percentage = Math.min((progressInLevel / 1000) * 100, 100);
  void _levelXP; // Suppress unused warning
  
  return (
    <div className="bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl p-4 text-white">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center">
            <span className="text-xl font-bold">{level}</span>
          </div>
          <div>
            <div className="font-semibold">Seviye {level}</div>
            <div className="text-sm text-white/70">{currentXP.toLocaleString()} XP</div>
          </div>
        </div>
        <div className="text-right">
          <div className="text-sm text-white/70">Sonraki seviye</div>
          <div className="font-semibold">{nextLevelXP.toLocaleString()} XP</div>
        </div>
      </div>
      
      <div className="relative h-3 bg-white/20 rounded-full overflow-hidden">
        <motion.div
          className="absolute inset-y-0 left-0 bg-white rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 1, ease: 'easeOut' }}
        />
      </div>
    </div>
  );
};

// ==================== MASTERY RING ====================

const MasteryRing: React.FC<{
  percentage: number;
  size?: number;
  strokeWidth?: number;
  color?: string;
  label?: string;
}> = ({ percentage, size = 80, strokeWidth = 8, color = '#8B5CF6', label }) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (percentage / 100) * circumference;
  
  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-gray-200 dark:text-gray-700"
        />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1, ease: 'easeOut' }}
          style={{ strokeDasharray: circumference }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-lg font-bold" style={{ color }}>{Math.round(percentage)}%</span>
        {label && <span className="text-xs text-gray-500">{label}</span>}
      </div>
    </div>
  );
};

// ==================== TOPIC CARD ====================

const TopicMasteryCard: React.FC<{
  topic: TopicMastery;
  onClick?: () => void;
}> = ({ topic, onClick }) => {
  const config = LEVEL_CONFIG[topic.level];
  
  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 cursor-pointer hover:shadow-md transition-shadow"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{config.icon}</span>
          <div>
            <div className="font-medium text-gray-900 dark:text-white">
              {topic.topic_name || topic.topic_id}
            </div>
            <div className="text-sm" style={{ color: config.color }}>
              {config.label}
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          {/* Mastery Score */}
          <div className="text-right">
            <div className="text-xl font-bold" style={{ color: config.color }}>
              {Math.round(topic.score * 100)}%
            </div>
            <div className="text-xs text-gray-500">
              {topic.total_attempts} deneme
            </div>
          </div>
          
          {/* Retention Indicator */}
          <div className="w-12 h-12 rounded-full border-4 flex items-center justify-center"
            style={{ borderColor: topic.retention_rate > 0.7 ? '#10B981' : topic.retention_rate > 0.4 ? '#F59E0B' : '#EF4444' }}
          >
            <Brain className="w-5 h-5 text-gray-400" />
          </div>
          
          <ChevronRight className="w-5 h-5 text-gray-400" />
        </div>
      </div>
      
      {/* Progress Bar */}
      <div className="mt-3 h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
        <motion.div
          className="h-full rounded-full"
          style={{ backgroundColor: config.color }}
          initial={{ width: 0 }}
          animate={{ width: `${topic.score * 100}%` }}
          transition={{ duration: 0.5 }}
        />
      </div>
      
      {/* Stats */}
      <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
        <span className="flex items-center gap-1">
          <Target className="w-3 h-3" />
          {topic.correct_attempts}/{topic.total_attempts} doğru
        </span>
        <span className="flex items-center gap-1">
          <Zap className="w-3 h-3 text-amber-500" />
          {topic.xp_earned} XP
        </span>
        <span className="flex items-center gap-1">
          <TrendingUp className="w-3 h-3" />
          %{Math.round(topic.retention_rate * 100)} hafıza
        </span>
      </div>
    </motion.div>
  );
};

// ==================== WEAKNESS ALERT ====================

const WeaknessAlert: React.FC<{
  weakness: WeaknessSummary;
  onViewDetails?: () => void;
}> = ({ weakness, onViewDetails }) => {
  if (weakness.total_signals === 0) return null;
  
  const hasCritical = weakness.by_severity.critical > 0;
  
  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`p-4 rounded-xl border-2 ${
        hasCritical
          ? 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
          : 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800'
      }`}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          <AlertTriangle className={`w-6 h-6 ${hasCritical ? 'text-red-500' : 'text-amber-500'}`} />
          <div>
            <div className="font-semibold text-gray-900 dark:text-white">
              {weakness.total_signals} Zayıf Nokta Tespit Edildi
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              {weakness.affected_topics} konuda iyileştirme önerileri var
            </div>
            
            {/* Top Clusters */}
            {weakness.clusters.slice(0, 2).map((cluster, i) => (
              <div key={i} className="mt-2 p-2 rounded-lg bg-white/50 dark:bg-gray-800/50">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">{cluster.name}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    cluster.priority === 1 ? 'bg-red-100 text-red-600' :
                    cluster.priority === 2 ? 'bg-amber-100 text-amber-600' :
                    'bg-gray-100 text-gray-600'
                  }`}>
                    Öncelik {cluster.priority}
                  </span>
                </div>
                {cluster.recommendations[0] && (
                  <p className="text-xs text-gray-500 mt-1">
                    💡 {cluster.recommendations[0]}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
        
        <button
          onClick={onViewDetails}
          className="px-3 py-1.5 text-sm font-medium rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
        >
          Detaylar
        </button>
      </div>
    </motion.div>
  );
};

// ==================== MAIN COMPONENT ====================

export const MasteryProgress: React.FC<MasteryProgressProps> = ({
  onTopicClick,
  showWeakness = true,
  compact = false
}) => {
  const [summary, setSummary] = useState<MasterySummary | null>(null);
  const [weakness, setWeakness] = useState<WeaknessSummary | null>(null);
  const [topics, _setTopics] = useState<TopicMastery[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  void _setTopics; // For future topic updates
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Fetch mastery summary
        const summaryRes = await fetch('/api/journey/v2/premium/mastery/summary');
        if (summaryRes.ok) {
          const data = await summaryRes.json();
          setSummary(data.summary);
        }
        
        // Fetch weakness summary
        if (showWeakness) {
          const weaknessRes = await fetch('/api/journey/v2/premium/weakness/summary');
          if (weaknessRes.ok) {
            const data = await weaknessRes.json();
            setWeakness(data.summary);
          }
        }
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [showWeakness]);
  
  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500" />
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="p-4 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600">
        Veri yüklenirken hata: {error}
      </div>
    );
  }
  
  if (!summary) {
    return (
      <div className="p-8 text-center text-gray-500">
        Henüz ilerleme verisi yok. Öğrenmeye başlayın!
      </div>
    );
  }
  
  return (
    <div className="space-y-6">
      {/* XP & Level */}
      <XPProgressBar
        currentXP={summary.user.total_xp}
        level={summary.user.level}
        nextLevelXP={summary.user.next_level_xp}
      />
      
      {/* Weakness Alert */}
      {showWeakness && weakness && (
        <WeaknessAlert
          weakness={weakness}
          onViewDetails={() => {}}
        />
      )}
      
      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Topics Mastered */}
        <div className="p-4 rounded-xl bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-purple-600">
                {summary.topics.mastered}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Ustalaşılan Konu
              </div>
            </div>
            <MasteryRing
              percentage={summary.topics.percentage}
              size={50}
              strokeWidth={4}
              color="#8B5CF6"
            />
          </div>
        </div>
        
        {/* Packages Completed */}
        <div className="p-4 rounded-xl bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-blue-600">
                {summary.packages.completed}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Tamamlanan Paket
              </div>
            </div>
            <MasteryRing
              percentage={summary.packages.percentage}
              size={50}
              strokeWidth={4}
              color="#3B82F6"
            />
          </div>
        </div>
        
        {/* Stages */}
        <div className="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-emerald-600">
                {summary.stages.completed}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Geçilen Aşama
              </div>
            </div>
            <MasteryRing
              percentage={summary.stages.percentage}
              size={50}
              strokeWidth={4}
              color="#10B981"
            />
          </div>
        </div>
        
        {/* Due Reviews */}
        <div className="p-4 rounded-xl bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-amber-600">
                {summary.spaced_repetition.due_today}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Bugün Tekrar
              </div>
            </div>
            <div className="p-2 rounded-full bg-amber-100 dark:bg-amber-900/50">
              <Clock className="w-6 h-6 text-amber-600" />
            </div>
          </div>
          {summary.spaced_repetition.overdue_count > 0 && (
            <div className="mt-2 text-xs text-red-500">
              ⚠️ {summary.spaced_repetition.overdue_count} gecikmiş
            </div>
          )}
        </div>
      </div>
      
      {/* Retention Chart */}
      {!compact && (
        <div className="p-4 rounded-xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Brain className="w-5 h-5 text-purple-500" />
              <span className="font-semibold text-gray-900 dark:text-white">
                Hafıza Durumu
              </span>
            </div>
            <span className="text-sm text-gray-500">
              SM-2 Algoritması
            </span>
          </div>
          
          <div className="flex items-center gap-6">
            <MasteryRing
              percentage={summary.spaced_repetition.average_retention * 100}
              size={100}
              strokeWidth={10}
              color="#8B5CF6"
              label="Ortalama"
            />
            
            <div className="flex-1 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Toplam Öğe</span>
                <span className="font-medium">{summary.spaced_repetition.total_items}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Ustalaşılan</span>
                <span className="font-medium text-green-600">{summary.spaced_repetition.mastered_count}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Bugün Tekrar</span>
                <span className="font-medium text-amber-600">{summary.spaced_repetition.due_today}</span>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Topic List */}
      {!compact && topics.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-gray-900 dark:text-white">
              Konu Hakimiyeti
            </h3>
            <button className="text-sm text-purple-600 hover:underline">
              Tümünü Gör
            </button>
          </div>
          
          {topics.slice(0, 5).map((topic) => (
            <TopicMasteryCard
              key={topic.topic_id}
              topic={topic}
              onClick={() => onTopicClick?.(topic.topic_id)}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default MasteryProgress;
