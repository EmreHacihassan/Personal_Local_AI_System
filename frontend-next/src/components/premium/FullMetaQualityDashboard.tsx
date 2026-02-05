'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Brain,
  Zap,
  Timer,
  Target,
  TrendingUp,
  Flame,
  Eye,
  Layers,
  Activity,
  Sparkles,
  Clock,
  AlertCircle,
  Check,
  Play,
  Pause,
  RefreshCw,
  ChevronRight,
  Star,
  Trophy,
  Heart,
  Volume2,
  Gauge,
  Focus,
  Waves,
  Battery,
  BatteryLow,
  BatteryMedium,
  BatteryFull,
  Rocket,
  Award,
  Calendar,
  BarChart3,
  PieChart,
  X,
} from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

// ==================== TYPES ====================
interface AttentionMetrics {
  flow_state: 'building' | 'in_flow' | 'declining' | 'lost';
  attention_score: number;
  focus_duration: number;
  distraction_count: number;
  optimal_break_in: number;
  session_quality: 'excellent' | 'good' | 'average' | 'poor';
}

interface MicroContent {
  chunk_id: string;
  title: string;
  duration_seconds: number;
  content_type: 'video' | 'text' | 'quiz' | 'practice';
  difficulty: number;
  engagement_score: number;
  tags: string[];
}

interface FeedbackEvent {
  type: 'achievement' | 'progress' | 'streak' | 'milestone' | 'mastery';
  message: string;
  xp_earned: number;
  animation: string;
  sound_effect?: string;
  timestamp: string;
}

interface CognitiveLoad {
  intrinsic_load: number;
  extraneous_load: number;
  germane_load: number;
  total_load: number;
  zone: 'optimal' | 'underload' | 'overload';
  recommendation: string;
}

interface MomentumData {
  current_streak: number;
  best_streak: number;
  total_days_active: number;
  momentum_score: number;
  velocity: 'accelerating' | 'steady' | 'slowing' | 'stalled';
  next_milestone: number;
  streak_protected: boolean;
}

interface QualityDashboard {
  attention: AttentionMetrics;
  cognitive: CognitiveLoad;
  momentum: MomentumData;
  recent_feedback: FeedbackEvent[];
  micro_feed: MicroContent[];
  overall_quality_score: number;
}

// ==================== QUALITY DASHBOARD TABS ====================
type TabType = 'attention' | 'micro' | 'feedback' | 'cognitive' | 'momentum';

const QUALITY_TABS: { id: TabType; label: string; icon: React.ReactNode; color: string }[] = [
  { id: 'attention', label: 'Dikkat Akışı', icon: <Eye className="w-4 h-4" />, color: 'from-purple-500 to-violet-600' },
  { id: 'micro', label: 'Mikro Öğrenme', icon: <Zap className="w-4 h-4" />, color: 'from-blue-500 to-cyan-600' },
  { id: 'feedback', label: 'Anlık Geri Bildirim', icon: <Sparkles className="w-4 h-4" />, color: 'from-amber-500 to-orange-600' },
  { id: 'cognitive', label: 'Zihinsel Yük', icon: <Brain className="w-4 h-4" />, color: 'from-green-500 to-emerald-600' },
  { id: 'momentum', label: 'Momentum', icon: <Rocket className="w-4 h-4" />, color: 'from-pink-500 to-rose-600' },
];

// ==================== HELPER COMPONENTS ====================
const ProgressRing: React.FC<{ value: number; max?: number; size?: number; color?: string }> = ({
  value,
  max = 100,
  size = 120,
  color = '#8B5CF6',
}) => {
  const percentage = Math.min(100, (value / max) * 100);
  const strokeWidth = size * 0.08;
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (percentage / 100) * circumference;

  return (
    <svg width={size} height={size} className="transform -rotate-90">
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        strokeWidth={strokeWidth}
        fill="none"
        className="stroke-gray-700"
      />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        strokeWidth={strokeWidth}
        fill="none"
        stroke={color}
        strokeLinecap="round"
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        className="transition-all duration-500"
      />
    </svg>
  );
};

const FlowStateIndicator: React.FC<{ state: string; score: number }> = ({ state, score }) => {
  const stateConfig: Record<string, { color: string; label: string; icon: React.ReactNode; animation: string }> = {
    in_flow: { 
      color: 'from-green-400 to-emerald-500', 
      label: 'Flow Durumunda', 
      icon: <Waves className="w-6 h-6" />,
      animation: 'animate-pulse'
    },
    building: { 
      color: 'from-blue-400 to-cyan-500', 
      label: 'Flow Oluşuyor', 
      icon: <TrendingUp className="w-6 h-6" />,
      animation: ''
    },
    declining: { 
      color: 'from-amber-400 to-orange-500', 
      label: 'Dikkat Düşüyor', 
      icon: <AlertCircle className="w-6 h-6" />,
      animation: ''
    },
    lost: { 
      color: 'from-red-400 to-rose-500', 
      label: 'Mola Zamanı', 
      icon: <Pause className="w-6 h-6" />,
      animation: ''
    },
  };

  const config = stateConfig[state] || stateConfig.building;

  return (
    <motion.div
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      className={`flex items-center gap-4 p-6 rounded-2xl bg-gradient-to-r ${config.color} ${config.animation}`}
    >
      <div className="p-3 bg-white/20 rounded-xl backdrop-blur-sm">
        {config.icon}
      </div>
      <div>
        <h3 className="text-xl font-bold text-white">{config.label}</h3>
        <p className="text-white/80">Dikkat Skoru: %{score}</p>
      </div>
    </motion.div>
  );
};

const MicroContentCard: React.FC<{ content: MicroContent; onPlay: () => void }> = ({ content, onPlay }) => {
  const typeIcons: Record<string, React.ReactNode> = {
    video: <Play className="w-4 h-4" />,
    text: <Layers className="w-4 h-4" />,
    quiz: <Target className="w-4 h-4" />,
    practice: <Activity className="w-4 h-4" />,
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
  };

  return (
    <motion.div
      whileHover={{ scale: 1.02, y: -2 }}
      whileTap={{ scale: 0.98 }}
      onClick={onPlay}
      className="p-4 bg-gray-800/50 rounded-xl border border-gray-700 hover:border-blue-500 cursor-pointer transition-all"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-blue-500/20 rounded-lg">
            {typeIcons[content.content_type]}
          </div>
          <span className="text-xs text-gray-400 uppercase">{content.content_type}</span>
        </div>
        <span className="flex items-center gap-1 text-xs text-gray-500">
          <Clock className="w-3 h-3" />
          {formatDuration(content.duration_seconds)}
        </span>
      </div>
      
      <h4 className="text-white font-medium mb-2 line-clamp-2">{content.title}</h4>
      
      <div className="flex items-center justify-between">
        <div className="flex gap-1">
          {content.tags.slice(0, 3).map((tag) => (
            <span key={tag} className="text-xs px-2 py-0.5 bg-gray-700 rounded-full text-gray-400">
              {tag}
            </span>
          ))}
        </div>
        <div className="flex items-center gap-1">
          <Star className="w-3 h-3 text-amber-400" />
          <span className="text-xs text-amber-400">{content.engagement_score}</span>
        </div>
      </div>
    </motion.div>
  );
};

const FeedbackPopup: React.FC<{ event: FeedbackEvent; onClose: () => void }> = ({ event, onClose }) => {
  const typeConfig: Record<string, { color: string; icon: React.ReactNode }> = {
    achievement: { color: 'from-amber-500 to-yellow-500', icon: <Trophy className="w-8 h-8" /> },
    progress: { color: 'from-blue-500 to-cyan-500', icon: <TrendingUp className="w-8 h-8" /> },
    streak: { color: 'from-orange-500 to-red-500', icon: <Flame className="w-8 h-8" /> },
    milestone: { color: 'from-purple-500 to-pink-500', icon: <Star className="w-8 h-8" /> },
    mastery: { color: 'from-green-500 to-emerald-500', icon: <Award className="w-8 h-8" /> },
  };

  const config = typeConfig[event.type] || typeConfig.progress;

  return (
    <motion.div
      initial={{ scale: 0, opacity: 0, y: 50 }}
      animate={{ scale: 1, opacity: 1, y: 0 }}
      exit={{ scale: 0, opacity: 0, y: -50 }}
      className="fixed bottom-8 right-8 z-50"
    >
      <div className={`p-6 rounded-2xl bg-gradient-to-r ${config.color} shadow-2xl`}>
        <button onClick={onClose} className="absolute top-2 right-2 text-white/60 hover:text-white">
          <X className="w-4 h-4" />
        </button>
        
        <div className="flex items-center gap-4">
          <motion.div
            animate={{ rotate: [0, 10, -10, 0], scale: [1, 1.1, 1] }}
            transition={{ duration: 0.5, repeat: 2 }}
            className="p-3 bg-white/20 rounded-xl"
          >
            {config.icon}
          </motion.div>
          
          <div>
            <h3 className="text-lg font-bold text-white">{event.message}</h3>
            <p className="text-white/80 flex items-center gap-1">
              <Sparkles className="w-4 h-4" />
              +{event.xp_earned} XP
            </p>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

const CognitiveLoadMeter: React.FC<{ load: CognitiveLoad }> = ({ load }) => {
  const zoneColors: Record<string, string> = {
    optimal: 'bg-green-500',
    underload: 'bg-blue-500',
    overload: 'bg-red-500',
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white">Zihinsel Yük Analizi</h3>
        <span className={`px-3 py-1 rounded-full text-sm text-white ${zoneColors[load.zone]}`}>
          {load.zone === 'optimal' ? 'Optimal Bölge' : load.zone === 'underload' ? 'Düşük Yük' : 'Aşırı Yük'}
        </span>
      </div>

      {/* Load Breakdown */}
      <div className="space-y-4">
        <div>
          <div className="flex justify-between text-sm mb-1">
            <span className="text-gray-400">İçsel Yük (Zorluk)</span>
            <span className="text-purple-400">{load.intrinsic_load}%</span>
          </div>
          <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${load.intrinsic_load}%` }}
              className="h-full bg-gradient-to-r from-purple-500 to-violet-500 rounded-full"
            />
          </div>
        </div>

        <div>
          <div className="flex justify-between text-sm mb-1">
            <span className="text-gray-400">Dışsal Yük (Tasarım)</span>
            <span className="text-blue-400">{load.extraneous_load}%</span>
          </div>
          <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${load.extraneous_load}%` }}
              className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full"
            />
          </div>
        </div>

        <div>
          <div className="flex justify-between text-sm mb-1">
            <span className="text-gray-400">Üretken Yük (Öğrenme)</span>
            <span className="text-green-400">{load.germane_load}%</span>
          </div>
          <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${load.germane_load}%` }}
              className="h-full bg-gradient-to-r from-green-500 to-emerald-500 rounded-full"
            />
          </div>
        </div>
      </div>

      {/* Total Load Gauge */}
      <div className="flex items-center justify-center">
        <div className="relative">
          <ProgressRing value={load.total_load} size={140} color={load.zone === 'optimal' ? '#22C55E' : load.zone === 'underload' ? '#3B82F6' : '#EF4444'} />
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-3xl font-bold text-white">{load.total_load}%</span>
            <span className="text-xs text-gray-400">Toplam Yük</span>
          </div>
        </div>
      </div>

      {/* Recommendation */}
      <div className="p-4 bg-gray-800/50 rounded-xl border border-gray-700">
        <p className="text-gray-300 text-sm">{load.recommendation}</p>
      </div>
    </div>
  );
};

const MomentumPanel: React.FC<{ momentum: MomentumData }> = ({ momentum }) => {
  const velocityConfig: Record<string, { color: string; label: string; icon: React.ReactNode }> = {
    accelerating: { color: 'text-green-400', label: 'Hızlanıyor', icon: <Rocket className="w-5 h-5" /> },
    steady: { color: 'text-blue-400', label: 'Kararlı', icon: <Target className="w-5 h-5" /> },
    slowing: { color: 'text-amber-400', label: 'Yavaşlıyor', icon: <AlertCircle className="w-5 h-5" /> },
    stalled: { color: 'text-red-400', label: 'Durağan', icon: <Pause className="w-5 h-5" /> },
  };

  const config = velocityConfig[momentum.velocity] || velocityConfig.steady;

  return (
    <div className="space-y-6">
      {/* Streak Display */}
      <div className="flex items-center justify-center">
        <motion.div
          animate={{ scale: [1, 1.05, 1] }}
          transition={{ duration: 2, repeat: Infinity }}
          className="relative"
        >
          <div className="w-32 h-32 rounded-full bg-gradient-to-br from-orange-500 to-red-600 flex items-center justify-center">
            <Flame className="w-16 h-16 text-white" />
          </div>
          <div className="absolute -bottom-2 left-1/2 transform -translate-x-1/2 bg-gray-900 px-4 py-1 rounded-full border border-orange-500">
            <span className="text-2xl font-bold text-orange-400">{momentum.current_streak}</span>
            <span className="text-sm text-gray-400 ml-1">gün</span>
          </div>
          {momentum.streak_protected && (
            <div className="absolute -top-2 -right-2 bg-green-500 p-1 rounded-full">
              <Check className="w-4 h-4 text-white" />
            </div>
          )}
        </motion.div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-3 gap-4">
        <div className="text-center p-4 bg-gray-800/50 rounded-xl">
          <Trophy className="w-6 h-6 text-amber-400 mx-auto mb-2" />
          <p className="text-2xl font-bold text-white">{momentum.best_streak}</p>
          <p className="text-xs text-gray-400">En İyi Seri</p>
        </div>
        <div className="text-center p-4 bg-gray-800/50 rounded-xl">
          <Calendar className="w-6 h-6 text-blue-400 mx-auto mb-2" />
          <p className="text-2xl font-bold text-white">{momentum.total_days_active}</p>
          <p className="text-xs text-gray-400">Toplam Gün</p>
        </div>
        <div className="text-center p-4 bg-gray-800/50 rounded-xl">
          <Star className="w-6 h-6 text-purple-400 mx-auto mb-2" />
          <p className="text-2xl font-bold text-white">{momentum.next_milestone}</p>
          <p className="text-xs text-gray-400">Sonraki Hedef</p>
        </div>
      </div>

      {/* Momentum Score */}
      <div className="p-4 bg-gray-800/50 rounded-xl">
        <div className="flex items-center justify-between mb-3">
          <span className="text-gray-400">Momentum Skoru</span>
          <span className={`flex items-center gap-1 ${config.color}`}>
            {config.icon}
            {config.label}
          </span>
        </div>
        <div className="h-3 bg-gray-700 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${momentum.momentum_score}%` }}
            className="h-full bg-gradient-to-r from-pink-500 to-rose-500 rounded-full"
          />
        </div>
        <div className="flex justify-between mt-1">
          <span className="text-xs text-gray-500">0</span>
          <span className="text-sm font-bold text-pink-400">{momentum.momentum_score}%</span>
          <span className="text-xs text-gray-500">100</span>
        </div>
      </div>
    </div>
  );
};

// ==================== MAIN COMPONENT ====================
export default function FullMetaQualityDashboard() {
  const [activeTab, setActiveTab] = useState<TabType>('attention');
  const [isLoading, setIsLoading] = useState(true);
  const [userId] = useState('user_123'); // TODO: Get from auth
  const [sessionId, setSessionId] = useState<string | null>(null);
  
  // Data states
  const [attentionMetrics, setAttentionMetrics] = useState<AttentionMetrics | null>(null);
  const [microFeed, setMicroFeed] = useState<MicroContent[]>([]);
  const [feedbackEvents, setFeedbackEvents] = useState<FeedbackEvent[]>([]);
  const [cognitiveLoad, setCognitiveLoad] = useState<CognitiveLoad | null>(null);
  const [momentum, setMomentum] = useState<MomentumData | null>(null);
  const [activeFeedback, setActiveFeedback] = useState<FeedbackEvent | null>(null);

  // Attention tracking interval
  const attentionIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // ==================== API CALLS ====================
  const startAttentionSession = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/full-meta/quality/attention/start-session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          content_difficulty: 0.5,
        }),
      });
      const data = await res.json();
      setSessionId(data.session_id);
      return data.session_id;
    } catch (error) {
      console.error('Failed to start attention session:', error);
    }
  };

  const sendAttentionSignal = async (signalType: string, value: number) => {
    if (!sessionId) return;
    try {
      const res = await fetch(`${API_BASE}/api/full-meta/quality/attention/signal`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          signal_type: signalType,
          signal_data: { value },
        }),
      });
      const data = await res.json();
      setAttentionMetrics(data);
    } catch (error) {
      console.error('Failed to send attention signal:', error);
    }
  };

  const fetchMicroFeed = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/full-meta/quality/micro/feed/${userId}`);
      const data = await res.json();
      setMicroFeed(data.feed || []);
    } catch (error) {
      console.error('Failed to fetch micro feed:', error);
    }
  };

  const fetchMomentum = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/full-meta/quality/momentum/${userId}`);
      const data = await res.json();
      setMomentum(data);
    } catch (error) {
      console.error('Failed to fetch momentum:', error);
    }
  };

  const analyzeContent = async (contentText: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/full-meta/quality/cognitive/analyze-content`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: {
            text: contentText,
            type: 'text',
            concepts: [],
            difficulty: 50,
            dependencies: []
          },
          user_id: userId,
          session_duration_minutes: 0
        }),
      });
      const data = await res.json();
      setCognitiveLoad(data);
    } catch (error) {
      console.error('Failed to analyze cognitive load:', error);
    }
  };

  const generateFeedback = async (eventType: string, context: object) => {
    try {
      const res = await fetch(`${API_BASE}/api/full-meta/quality/feedback/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          event_type: eventType,
          context,
        }),
      });
      const data = await res.json();
      setActiveFeedback(data);
      setFeedbackEvents((prev) => [data, ...prev].slice(0, 10));
      
      // Auto-dismiss after 5 seconds
      setTimeout(() => setActiveFeedback(null), 5000);
    } catch (error) {
      console.error('Failed to generate feedback:', error);
    }
  };

  // ==================== EFFECTS ====================
  useEffect(() => {
    const initDashboard = async () => {
      setIsLoading(true);
      await Promise.all([
        startAttentionSession(),
        fetchMicroFeed(),
        fetchMomentum(),
        analyzeContent('Örnek öğrenme içeriği - makine öğrenmesi temelleri'),
      ]);
      setIsLoading(false);
    };

    initDashboard();

    return () => {
      if (attentionIntervalRef.current) {
        clearInterval(attentionIntervalRef.current);
      }
    };
  }, []);

  // Periodic attention check
  useEffect(() => {
    if (sessionId) {
      attentionIntervalRef.current = setInterval(() => {
        sendAttentionSignal('focus_check', Math.random() > 0.3 ? 1 : 0);
      }, 30000); // Check every 30 seconds
    }

    return () => {
      if (attentionIntervalRef.current) {
        clearInterval(attentionIntervalRef.current);
      }
    };
  }, [sessionId]);

  // ==================== RENDER TAB CONTENT ====================
  const renderTabContent = () => {
    switch (activeTab) {
      case 'attention':
        return (
          <div className="space-y-6">
            {attentionMetrics && (
              <>
                <FlowStateIndicator state={attentionMetrics.flow_state} score={attentionMetrics.attention_score} />
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-gray-800/50 rounded-xl">
                    <div className="flex items-center gap-2 mb-2">
                      <Clock className="w-4 h-4 text-blue-400" />
                      <span className="text-gray-400 text-sm">Odaklanma Süresi</span>
                    </div>
                    <p className="text-2xl font-bold text-white">
                      {Math.floor(attentionMetrics.focus_duration / 60)}m {attentionMetrics.focus_duration % 60}s
                    </p>
                  </div>
                  
                  <div className="p-4 bg-gray-800/50 rounded-xl">
                    <div className="flex items-center gap-2 mb-2">
                      <AlertCircle className="w-4 h-4 text-amber-400" />
                      <span className="text-gray-400 text-sm">Dikkat Dağınıklığı</span>
                    </div>
                    <p className="text-2xl font-bold text-white">{attentionMetrics.distraction_count}</p>
                  </div>
                </div>

                <div className="p-4 bg-gray-800/50 rounded-xl">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-gray-400">Mola Önerisi</span>
                    <span className="text-blue-400">{attentionMetrics.optimal_break_in} dk sonra</span>
                  </div>
                  <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: '100%' }}
                      animate={{ width: `${(attentionMetrics.optimal_break_in / 25) * 100}%` }}
                      className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full"
                    />
                  </div>
                </div>

                <div className="flex gap-3">
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => sendAttentionSignal('focus', 1)}
                    className="flex-1 p-3 bg-green-500/20 text-green-400 rounded-xl flex items-center justify-center gap-2"
                  >
                    <Eye className="w-5 h-5" />
                    Odaklanıyorum
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => sendAttentionSignal('break', 1)}
                    className="flex-1 p-3 bg-amber-500/20 text-amber-400 rounded-xl flex items-center justify-center gap-2"
                  >
                    <Pause className="w-5 h-5" />
                    Mola Veriyorum
                  </motion.button>
                </div>
              </>
            )}
          </div>
        );

      case 'micro':
        return (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-white">Kişisel Feed</h3>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={fetchMicroFeed}
                className="p-2 bg-blue-500/20 text-blue-400 rounded-lg"
              >
                <RefreshCw className="w-4 h-4" />
              </motion.button>
            </div>

            <div className="grid gap-4">
              {microFeed.length > 0 ? (
                microFeed.map((content) => (
                  <MicroContentCard
                    key={content.chunk_id}
                    content={content}
                    onPlay={() => generateFeedback('content_started', { content_id: content.chunk_id })}
                  />
                ))
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <Zap className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>Henüz içerik yok</p>
                </div>
              )}
            </div>
          </div>
        );

      case 'feedback':
        return (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-white">Son Geri Bildirimler</h3>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => generateFeedback('test', { message: 'Test feedback' })}
                className="px-4 py-2 bg-amber-500/20 text-amber-400 rounded-lg text-sm"
              >
                Test Et
              </motion.button>
            </div>

            <div className="space-y-3">
              {feedbackEvents.length > 0 ? (
                feedbackEvents.map((event, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="p-4 bg-gray-800/50 rounded-xl border border-gray-700"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-amber-500/20 rounded-lg">
                          <Sparkles className="w-4 h-4 text-amber-400" />
                        </div>
                        <div>
                          <p className="text-white">{event.message}</p>
                          <p className="text-xs text-gray-500">{event.timestamp}</p>
                        </div>
                      </div>
                      <span className="text-amber-400 font-medium">+{event.xp_earned} XP</span>
                    </div>
                  </motion.div>
                ))
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <Sparkles className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>Henüz geri bildirim yok</p>
                </div>
              )}
            </div>
          </div>
        );

      case 'cognitive':
        return cognitiveLoad ? (
          <CognitiveLoadMeter load={cognitiveLoad} />
        ) : (
          <div className="text-center py-12 text-gray-500">
            <Brain className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>Yükleniyor...</p>
          </div>
        );

      case 'momentum':
        return momentum ? (
          <MomentumPanel momentum={momentum} />
        ) : (
          <div className="text-center py-12 text-gray-500">
            <Rocket className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>Yükleniyor...</p>
          </div>
        );

      default:
        return null;
    }
  };

  // ==================== MAIN RENDER ====================
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
        >
          <Sparkles className="w-8 h-8 text-purple-500" />
        </motion.div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-gray-900">
      {/* Header */}
      <div className="p-6 border-b border-gray-800">
        <div className="flex items-center gap-4 mb-4">
          <div className="p-3 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl">
            <Activity className="w-7 h-7 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Kalite Dashboard</h1>
            <p className="text-sm text-gray-400">2026 Nesil Öğrenme Optimizasyonu</p>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-2 overflow-x-auto pb-2">
          {QUALITY_TABS.map((tab) => (
            <motion.button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl whitespace-nowrap transition-all ${
                activeTab === tab.id
                  ? `bg-gradient-to-r ${tab.color} text-white`
                  : 'bg-gray-800 text-gray-400 hover:text-white'
              }`}
            >
              {tab.icon}
              <span className="text-sm font-medium">{tab.label}</span>
            </motion.button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.2 }}
          >
            {renderTabContent()}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Feedback Popup */}
      <AnimatePresence>
        {activeFeedback && (
          <FeedbackPopup event={activeFeedback} onClose={() => setActiveFeedback(null)} />
        )}
      </AnimatePresence>
    </div>
  );
}
