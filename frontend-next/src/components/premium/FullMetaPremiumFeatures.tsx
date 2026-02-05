'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Brain,
  Gamepad2,
  Target,
  Palette,
  Timer,
  Lightbulb,
  BarChart3,
  Award,
  Waves,
  Castle,
  Layers,
  Eye,
  Flame,
  Trophy,
  Swords,
  Calendar,
  Sparkles,
  TrendingUp,
  Clock,
  Heart,
  Link,
  MessageCircle,
  GitBranch,
  Map,
  AlertCircle,
  User,
  RotateCcw,
  FileText,
  GraduationCap,
  Zap,
  Activity,
  Shield,
  Star,
  ChevronRight,
  Play,
  Pause,
  RefreshCw,
  X,
  Check,
  Volume2,
  Code,
  PenTool,
  Network,
  BookOpen,
} from 'lucide-react';

// ============================================================================
// TYPES
// ============================================================================

type FeatureTab = 
  | 'neuroscience' 
  | 'gamification' 
  | 'adaptive' 
  | 'multimodal' 
  | 'spaced-rep' 
  | 'feynman' 
  | 'analytics' 
  | 'premium';

interface ThetaSession {
  session_id: string;
  state: string;
  duration: number;
}

interface DailyQuest {
  id: string;
  title: string;
  description: string;
  xp_reward: number;
  completed: boolean;
  progress: number;
  target: number;
}

interface BossBattle {
  battle_id: string;
  difficulty: string;
  questions: number;
  passing_score: number;
}

interface StrengthMapTopic {
  topic: string;
  score: number;
  trend: string;
}

interface BurnoutAssessment {
  risk_level: string;
  score: number;
  recommendations: string[];
}

// ============================================================================
// CONSTANTS
// ============================================================================

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

const FEATURE_TABS: { id: FeatureTab; label: string; icon: React.ReactNode; color: string }[] = [
  { id: 'neuroscience', label: 'Nörobilim', icon: <Brain className="w-5 h-5" />, color: 'from-purple-500 to-violet-500' },
  { id: 'gamification', label: 'Gamification', icon: <Gamepad2 className="w-5 h-5" />, color: 'from-yellow-500 to-orange-500' },
  { id: 'adaptive', label: 'Adaptif AI', icon: <Target className="w-5 h-5" />, color: 'from-blue-500 to-cyan-500' },
  { id: 'multimodal', label: 'Multi-Modal', icon: <Palette className="w-5 h-5" />, color: 'from-pink-500 to-rose-500' },
  { id: 'spaced-rep', label: 'Spaced Rep 3.0', icon: <Timer className="w-5 h-5" />, color: 'from-green-500 to-emerald-500' },
  { id: 'feynman', label: 'Feynman 2.0', icon: <Lightbulb className="w-5 h-5" />, color: 'from-amber-500 to-yellow-500' },
  { id: 'analytics', label: 'Analytics', icon: <BarChart3 className="w-5 h-5" />, color: 'from-indigo-500 to-blue-500' },
  { id: 'premium', label: 'Premium', icon: <Award className="w-5 h-5" />, color: 'from-red-500 to-pink-500' },
];

// ============================================================================
// API FUNCTIONS
// ============================================================================

async function startThetaSession(userId: string, topic: string, duration: number): Promise<ThetaSession> {
  const res = await fetch(`${API_BASE}/api/full-meta/premium/neuroscience/theta-session`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, topic, duration_minutes: duration }),
  });
  return await res.json();
}

async function getDailyQuests(userId: string): Promise<{ quests: DailyQuest[]; streak: number }> {
  const res = await fetch(`${API_BASE}/api/full-meta/premium/gamification/daily-quests/${userId}`);
  return await res.json();
}

async function createBossBattle(difficulty: string, contentItems: any[]): Promise<BossBattle> {
  const res = await fetch(`${API_BASE}/api/full-meta/premium/gamification/boss-battle`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ difficulty, content_items: contentItems }),
  });
  return await res.json();
}

async function getLearningStyle(userId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/api/full-meta/premium/adaptive/learning-style/${userId}`);
  return await res.json();
}

async function getOptimalTimes(userId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/api/full-meta/premium/adaptive/optimal-time/${userId}`);
  return await res.json();
}

async function getVelocityGraph(userId: string, days: number = 30): Promise<any> {
  const res = await fetch(`${API_BASE}/api/full-meta/premium/analytics/velocity/${userId}?days=${days}`);
  return await res.json();
}

async function getStrengthMap(userId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/api/full-meta/premium/analytics/strength-map/${userId}`);
  return await res.json();
}

async function getBurnoutAssessment(userId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/api/full-meta/premium/analytics/burnout/${userId}`);
  return await res.json();
}

async function getPremiumDashboard(userId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/api/full-meta/premium/dashboard/${userId}`);
  return await res.json();
}

async function startRubberDuckSession(userId: string, topic: string): Promise<any> {
  const res = await fetch(`${API_BASE}/api/full-meta/premium/feynman/rubber-duck`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, topic, level: 'beginner' }),
  });
  return await res.json();
}

async function generateAnalogy(concept: string, domain: string = 'everyday'): Promise<any> {
  const res = await fetch(`${API_BASE}/api/full-meta/premium/feynman/analogy`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ concept, domain }),
  });
  return await res.json();
}

async function createTutorAvatar(userId: string, name: string, personality: string): Promise<any> {
  const res = await fetch(`${API_BASE}/api/full-meta/premium/tutor/avatar`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, name, personality }),
  });
  return await res.json();
}

// ============================================================================
// SUBCOMPONENTS
// ============================================================================

// Neuroscience Tab
const NeuroscienceTab: React.FC<{ userId: string }> = ({ userId }) => {
  const [thetaSession, setThetaSession] = useState<ThetaSession | null>(null);
  const [topic, setTopic] = useState('');
  const [duration, setDuration] = useState(25);
  const [isActive, setIsActive] = useState(false);

  const handleStartSession = async () => {
    if (!topic) return;
    const session = await startThetaSession(userId, topic, duration);
    setThetaSession(session);
    setIsActive(true);
  };

  return (
    <div className="space-y-6">
      {/* Theta Wave Sync */}
      <div className="bg-gray-800/50 rounded-2xl p-6 border border-purple-500/30">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 rounded-xl bg-gradient-to-br from-purple-500 to-violet-500">
            <Waves className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Theta Wave Sync</h3>
            <p className="text-sm text-gray-400">Beyin dalgası senkronizasyonu ile derin öğrenme</p>
          </div>
        </div>

        {!isActive ? (
          <div className="space-y-4">
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="Odaklanacağın konu..."
              className="w-full bg-gray-900 border border-gray-600 rounded-xl p-3 text-white"
            />
            <div className="flex items-center gap-4">
              <label className="text-sm text-gray-400">Süre:</label>
              {[15, 25, 45].map((d) => (
                <button
                  key={d}
                  onClick={() => setDuration(d)}
                  className={`px-4 py-2 rounded-xl ${
                    duration === d
                      ? 'bg-purple-500 text-white'
                      : 'bg-gray-700 text-gray-300'
                  }`}
                >
                  {d} dk
                </button>
              ))}
            </div>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleStartSession}
              disabled={!topic}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-purple-500 to-violet-500 text-white font-medium disabled:opacity-50"
            >
              <Play className="w-5 h-5 inline mr-2" />
              Oturumu Başlat
            </motion.button>
          </div>
        ) : (
          <div className="text-center py-8">
            <motion.div
              animate={{ scale: [1, 1.1, 1], opacity: [0.5, 1, 0.5] }}
              transition={{ repeat: Infinity, duration: 4 }}
              className="w-32 h-32 mx-auto rounded-full bg-gradient-to-br from-purple-500/30 to-violet-500/30 flex items-center justify-center mb-4"
            >
              <Brain className="w-16 h-16 text-purple-400" />
            </motion.div>
            <p className="text-purple-300 text-lg">Theta dalga modunda...</p>
            <p className="text-gray-400 mt-2">Derin öğrenme için hazırsın</p>
            <button
              onClick={() => setIsActive(false)}
              className="mt-4 px-6 py-2 bg-gray-700 text-gray-300 rounded-xl"
            >
              Bitir
            </button>
          </div>
        )}
      </div>

      {/* Memory Palace */}
      <div className="bg-gray-800/50 rounded-2xl p-6 border border-indigo-500/30">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 rounded-xl bg-gradient-to-br from-indigo-500 to-blue-500">
            <Castle className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Memory Palace</h3>
            <p className="text-sm text-gray-400">Mekansal hafıza teknikleri ile hatırlama</p>
          </div>
        </div>
        <p className="text-gray-300 mb-4">
          Öğrendiklerini sanal bir sarayda konumlandır. Hatırlamak istediğinde sarayda gezin.
        </p>
        <button className="px-4 py-2 bg-indigo-500/20 border border-indigo-500/50 text-indigo-300 rounded-xl">
          Saray Oluştur
        </button>
      </div>

      {/* Dual Coding */}
      <div className="bg-gray-800/50 rounded-2xl p-6 border border-cyan-500/30">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-500">
            <Eye className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Dual Coding</h3>
            <p className="text-sm text-gray-400">Görsel + Sözel ikili kodlama</p>
          </div>
        </div>
        <p className="text-gray-300">
          Her kavram için hem görsel hem sözel temsiller oluşturarak hafızayı güçlendir.
        </p>
      </div>
    </div>
  );
};

// Gamification Tab
const GamificationTab: React.FC<{ userId: string }> = ({ userId }) => {
  const [quests, setQuests] = useState<DailyQuest[]>([]);
  const [streak, setStreak] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadQuests();
  }, []);

  const loadQuests = async () => {
    setLoading(true);
    try {
      const data = await getDailyQuests(userId);
      setQuests(data.quests || []);
      setStreak(data.streak || 0);
    } catch (error) {
      console.error('Failed to load quests:', error);
    }
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      {/* Streak Banner */}
      <div className="bg-gradient-to-r from-orange-900/50 to-red-900/50 rounded-2xl p-6 border border-orange-500/30">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <motion.div
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ repeat: Infinity, duration: 1.5 }}
            >
              <Flame className="w-12 h-12 text-orange-400" />
            </motion.div>
            <div>
              <div className="text-3xl font-bold text-orange-400">{streak}</div>
              <div className="text-orange-200">Gün Streak 🔥</div>
            </div>
          </div>
          <Trophy className="w-16 h-16 text-amber-400/30" />
        </div>
      </div>

      {/* Daily Quests */}
      <div className="bg-gray-800/50 rounded-2xl p-6 border border-yellow-500/30">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 rounded-xl bg-gradient-to-br from-yellow-500 to-amber-500">
            <Calendar className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Günlük Görevler</h3>
            <p className="text-sm text-gray-400">Bugünkü hedeflerini tamamla</p>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-8">
            <RefreshCw className="w-8 h-8 text-yellow-400 animate-spin mx-auto" />
          </div>
        ) : quests.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            Henüz görev yok. Öğrenmeye başla!
          </div>
        ) : (
          <div className="space-y-3">
            {quests.map((quest) => (
              <div
                key={quest.id}
                className={`p-4 rounded-xl border ${
                  quest.completed
                    ? 'bg-green-900/20 border-green-500/30'
                    : 'bg-gray-900/50 border-gray-700/50'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-white">{quest.title}</span>
                  <span className="text-amber-400 text-sm">+{quest.xp_reward} XP</span>
                </div>
                <p className="text-sm text-gray-400 mb-2">{quest.description}</p>
                <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-gradient-to-r from-yellow-400 to-amber-500"
                    initial={{ width: 0 }}
                    animate={{ width: `${(quest.progress / quest.target) * 100}%` }}
                  />
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {quest.progress}/{quest.target}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Boss Battle */}
      <div className="bg-gray-800/50 rounded-2xl p-6 border border-red-500/30">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 rounded-xl bg-gradient-to-br from-red-500 to-pink-500">
            <Swords className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Boss Battle</h3>
            <p className="text-sm text-gray-400">Bölüm sonu sınavları</p>
          </div>
        </div>
        <p className="text-gray-300 mb-4">
          Paket sonunda boss battle&apos;ı geçmeden ilerleyemezsin. Hazır mısın?
        </p>
        <button className="px-4 py-2 bg-red-500/20 border border-red-500/50 text-red-300 rounded-xl">
          Mücadeleye Başla
        </button>
      </div>
    </div>
  );
};

// Adaptive Tab
const AdaptiveTab: React.FC<{ userId: string }> = ({ userId }) => {
  const [learningStyle, setLearningStyle] = useState<any>(null);
  const [optimalTimes, setOptimalTimes] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [style, times] = await Promise.all([
        getLearningStyle(userId),
        getOptimalTimes(userId),
      ]);
      setLearningStyle(style);
      setOptimalTimes(times);
    } catch (error) {
      console.error('Failed to load adaptive data:', error);
    }
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      {/* Learning Style */}
      <div className="bg-gray-800/50 rounded-2xl p-6 border border-blue-500/30">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500">
            <User className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Öğrenme Stilin</h3>
            <p className="text-sm text-gray-400">AI&apos;nin senin için belirlediği stil</p>
          </div>
        </div>
        
        {loading ? (
          <div className="text-center py-8">
            <RefreshCw className="w-8 h-8 text-blue-400 animate-spin mx-auto" />
          </div>
        ) : learningStyle?.has_profile ? (
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-blue-900/30 rounded-xl p-4">
              <div className="text-blue-300 text-sm">Birincil Stil</div>
              <div className="text-white font-medium">{learningStyle.profile.primary_style}</div>
            </div>
            <div className="bg-cyan-900/30 rounded-xl p-4">
              <div className="text-cyan-300 text-sm">İkincil Stil</div>
              <div className="text-white font-medium">{learningStyle.profile.secondary_style}</div>
            </div>
          </div>
        ) : (
          <p className="text-gray-400">Henüz yeterli veri yok. Öğrenmeye devam et!</p>
        )}
      </div>

      {/* Optimal Times */}
      <div className="bg-gray-800/50 rounded-2xl p-6 border border-green-500/30">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 rounded-xl bg-gradient-to-br from-green-500 to-emerald-500">
            <Clock className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Optimal Çalışma Zamanları</h3>
            <p className="text-sm text-gray-400">En verimli olduğun saatler</p>
          </div>
        </div>
        
        {optimalTimes?.optimal_hours ? (
          <div className="flex flex-wrap gap-2">
            {optimalTimes.optimal_hours.map((hour: number) => (
              <span
                key={hour}
                className="px-3 py-1 bg-green-900/30 text-green-300 rounded-lg text-sm"
              >
                {hour}:00
              </span>
            ))}
          </div>
        ) : (
          <p className="text-gray-400">Analiz devam ediyor...</p>
        )}
      </div>

      {/* Struggle Detection */}
      <div className="bg-gray-800/50 rounded-2xl p-6 border border-amber-500/30">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 rounded-xl bg-gradient-to-br from-amber-500 to-orange-500">
            <AlertCircle className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Zorlanma Tespiti</h3>
            <p className="text-sm text-gray-400">AI anında müdahale eder</p>
          </div>
        </div>
        <p className="text-gray-300">
          Zorlandığın anları tespit edip otomatik destek sunar, farklı açıklamalar önerir.
        </p>
      </div>
    </div>
  );
};

// Analytics Tab
const AnalyticsTab: React.FC<{ userId: string }> = ({ userId }) => {
  const [strengthMap, setStrengthMap] = useState<any>(null);
  const [burnout, setBurnout] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [strength, burn] = await Promise.all([
        getStrengthMap(userId),
        getBurnoutAssessment(userId),
      ]);
      setStrengthMap(strength);
      setBurnout(burn);
    } catch (error) {
      console.error('Failed to load analytics:', error);
    }
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      {/* Strength Map */}
      <div className="bg-gray-800/50 rounded-2xl p-6 border border-indigo-500/30">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-500">
            <Map className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Güç Haritası</h3>
            <p className="text-sm text-gray-400">Konu bazında güçlü/zayıf yönlerin</p>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-8">
            <RefreshCw className="w-8 h-8 text-indigo-400 animate-spin mx-auto" />
          </div>
        ) : strengthMap?.has_data ? (
          <div className="space-y-3">
            {strengthMap.topics?.slice(0, 5).map((topic: StrengthMapTopic) => (
              <div key={topic.topic}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-300">{topic.topic}</span>
                  <span className={topic.score >= 70 ? 'text-green-400' : 'text-amber-400'}>
                    {topic.score}%
                  </span>
                </div>
                <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                  <motion.div
                    className={`h-full ${
                      topic.score >= 70
                        ? 'bg-gradient-to-r from-green-400 to-emerald-500'
                        : 'bg-gradient-to-r from-amber-400 to-orange-500'
                    }`}
                    initial={{ width: 0 }}
                    animate={{ width: `${topic.score}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-400">Henüz yeterli veri yok.</p>
        )}
      </div>

      {/* Learning Velocity */}
      <div className="bg-gray-800/50 rounded-2xl p-6 border border-blue-500/30">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500">
            <TrendingUp className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Öğrenme Hızı</h3>
            <p className="text-sm text-gray-400">Günlük öğrenme trendlerin</p>
          </div>
        </div>
        <div className="h-32 flex items-end justify-between gap-1">
          {[65, 72, 58, 80, 75, 88, 92].map((val, i) => (
            <motion.div
              key={i}
              className="flex-1 bg-gradient-to-t from-blue-500 to-cyan-400 rounded-t"
              initial={{ height: 0 }}
              animate={{ height: `${val}%` }}
              transition={{ delay: i * 0.1 }}
            />
          ))}
        </div>
        <div className="flex justify-between text-xs text-gray-500 mt-2">
          <span>Pzt</span>
          <span>Sal</span>
          <span>Çar</span>
          <span>Per</span>
          <span>Cum</span>
          <span>Cmt</span>
          <span>Paz</span>
        </div>
      </div>

      {/* Burnout Detector */}
      <div className="bg-gray-800/50 rounded-2xl p-6 border border-red-500/30">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 rounded-xl bg-gradient-to-br from-red-500 to-pink-500">
            <Heart className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Tükenmişlik Dedektörü</h3>
            <p className="text-sm text-gray-400">Sağlığını korumak için izleme</p>
          </div>
        </div>
        
        {burnout?.has_data ? (
          <div className="space-y-4">
            <div className={`p-4 rounded-xl ${
              burnout.risk_level === 'low'
                ? 'bg-green-900/30 border border-green-500/30'
                : burnout.risk_level === 'medium'
                ? 'bg-amber-900/30 border border-amber-500/30'
                : 'bg-red-900/30 border border-red-500/30'
            }`}>
              <div className="text-sm text-gray-400">Risk Seviyesi</div>
              <div className={`text-lg font-semibold ${
                burnout.risk_level === 'low'
                  ? 'text-green-400'
                  : burnout.risk_level === 'medium'
                  ? 'text-amber-400'
                  : 'text-red-400'
              }`}>
                {burnout.risk_level === 'low' ? 'Düşük ✓' : burnout.risk_level === 'medium' ? 'Orta ⚠️' : 'Yüksek ⚠️'}
              </div>
            </div>
          </div>
        ) : (
          <p className="text-gray-400">Analiz için daha fazla veri gerekiyor.</p>
        )}
      </div>
    </div>
  );
};

// Feynman Tab
const FeynmanTab: React.FC<{ userId: string }> = ({ userId }) => {
  const [topic, setTopic] = useState('');
  const [concept, setConcept] = useState('');
  const [analogy, setAnalogy] = useState<any>(null);
  const [session, setSession] = useState<any>(null);

  const handleStartDuck = async () => {
    if (!topic) return;
    const data = await startRubberDuckSession(userId, topic);
    setSession(data);
  };

  const handleGenerateAnalogy = async () => {
    if (!concept) return;
    const data = await generateAnalogy(concept);
    setAnalogy(data);
  };

  return (
    <div className="space-y-6">
      {/* Rubber Duck AI */}
      <div className="bg-gray-800/50 rounded-2xl p-6 border border-yellow-500/30">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 rounded-xl bg-gradient-to-br from-yellow-500 to-amber-500">
            <MessageCircle className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Rubber Duck AI</h3>
            <p className="text-sm text-gray-400">Anlattıkça öğren, AI soru sorar</p>
          </div>
        </div>

        {!session ? (
          <div className="space-y-4">
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="Hangi konuyu anlatmak istiyorsun?"
              className="w-full bg-gray-900 border border-gray-600 rounded-xl p-3 text-white"
            />
            <button
              onClick={handleStartDuck}
              disabled={!topic}
              className="w-full py-3 bg-yellow-500/20 border border-yellow-500/50 text-yellow-300 rounded-xl disabled:opacity-50"
            >
              🦆 Oturumu Başlat
            </button>
          </div>
        ) : (
          <div className="bg-yellow-900/20 rounded-xl p-4">
            <p className="text-yellow-200">Oturum başladı! Konuyu açıklamaya başla...</p>
            <button
              onClick={() => setSession(null)}
              className="mt-3 text-sm text-gray-400 hover:text-white"
            >
              Bitir
            </button>
          </div>
        )}
      </div>

      {/* Analogy Generator */}
      <div className="bg-gray-800/50 rounded-2xl p-6 border border-orange-500/30">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 rounded-xl bg-gradient-to-br from-orange-500 to-red-500">
            <Lightbulb className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Analoji Üretici</h3>
            <p className="text-sm text-gray-400">Karmaşık kavramları basitleştir</p>
          </div>
        </div>

        <div className="space-y-4">
          <input
            type="text"
            value={concept}
            onChange={(e) => setConcept(e.target.value)}
            placeholder="Bir kavram gir (ör: Neural Network)"
            className="w-full bg-gray-900 border border-gray-600 rounded-xl p-3 text-white"
          />
          <button
            onClick={handleGenerateAnalogy}
            disabled={!concept}
            className="px-4 py-2 bg-orange-500/20 border border-orange-500/50 text-orange-300 rounded-xl disabled:opacity-50"
          >
            Analoji Oluştur
          </button>

          {analogy && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-orange-900/20 rounded-xl p-4"
            >
              <p className="text-orange-200">{analogy.analogy}</p>
            </motion.div>
          )}
        </div>
      </div>

      {/* Concept Map */}
      <div className="bg-gray-800/50 rounded-2xl p-6 border border-pink-500/30">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 rounded-xl bg-gradient-to-br from-pink-500 to-rose-500">
            <Network className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Kavram Haritası</h3>
            <p className="text-sm text-gray-400">Bağlantıları görselleştir</p>
          </div>
        </div>
        <p className="text-gray-300 mb-4">
          Kavramlar arası ilişkileri otomatik haritala ve görselleştir.
        </p>
        <button className="px-4 py-2 bg-pink-500/20 border border-pink-500/50 text-pink-300 rounded-xl">
          Harita Oluştur
        </button>
      </div>
    </div>
  );
};

// Premium Tab
const PremiumTab: React.FC<{ userId: string }> = ({ userId }) => {
  const [tutorName, setTutorName] = useState('Atlas');
  const [tutorPersonality, setTutorPersonality] = useState('mentor');

  const handleCreateTutor = async () => {
    await createTutorAvatar(userId, tutorName, tutorPersonality);
  };

  return (
    <div className="space-y-6">
      {/* AI Tutor Avatar */}
      <div className="bg-gradient-to-br from-purple-900/50 to-indigo-900/50 rounded-2xl p-6 border border-purple-500/30">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500">
            <User className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">AI Tutor Avatar</h3>
            <p className="text-sm text-purple-200">Kişiselleştirilmiş öğretmenin</p>
          </div>
        </div>

        <div className="space-y-4">
          <input
            type="text"
            value={tutorName}
            onChange={(e) => setTutorName(e.target.value)}
            placeholder="Tutor adı"
            className="w-full bg-gray-900 border border-purple-500/30 rounded-xl p-3 text-white"
          />
          <div className="flex gap-2">
            {['mentor', 'coach', 'friend', 'professor'].map((p) => (
              <button
                key={p}
                onClick={() => setTutorPersonality(p)}
                className={`px-3 py-2 rounded-xl text-sm ${
                  tutorPersonality === p
                    ? 'bg-purple-500 text-white'
                    : 'bg-gray-800 text-gray-300'
                }`}
              >
                {p}
              </button>
            ))}
          </div>
          <button
            onClick={handleCreateTutor}
            className="w-full py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white font-medium rounded-xl"
          >
            Tutor Oluştur
          </button>
        </div>
      </div>

      {/* Reverse Engineering */}
      <div className="bg-gray-800/50 rounded-2xl p-6 border border-cyan-500/30">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-500">
            <RotateCcw className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Reverse Engineering</h3>
            <p className="text-sm text-gray-400">Sonuçtan geriye doğru öğren</p>
          </div>
        </div>
        <p className="text-gray-300 mb-4">
          Bir sonuç gir (ör: &quot;bir web sitesi yapabilmek&quot;), AI geriye doğru öğrenme yolunu çıkarsın.
        </p>
        <button className="px-4 py-2 bg-cyan-500/20 border border-cyan-500/50 text-cyan-300 rounded-xl">
          Tersine Mühendislik Başlat
        </button>
      </div>

      {/* Mastery Certification */}
      <div className="bg-gray-800/50 rounded-2xl p-6 border border-amber-500/30">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 rounded-xl bg-gradient-to-br from-amber-500 to-yellow-500">
            <Award className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Mastery Sertifika</h3>
            <p className="text-sm text-gray-400">Uzmanlığını belgele</p>
          </div>
        </div>
        <p className="text-gray-300 mb-4">
          Konuda yeterli seviyeye ulaştığında sertifika kazan ve paylaş.
        </p>
        <button className="px-4 py-2 bg-amber-500/20 border border-amber-500/50 text-amber-300 rounded-xl">
          Sertifika Yollarını Gör
        </button>
      </div>

      {/* Learning Notes */}
      <div className="bg-gray-800/50 rounded-2xl p-6 border border-green-500/30">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 rounded-xl bg-gradient-to-br from-green-500 to-emerald-500">
            <FileText className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Premium Notlar</h3>
            <p className="text-sm text-gray-400">AI destekli not oluşturma</p>
          </div>
        </div>
        <p className="text-gray-300 mb-4">
          Özet, mind-map, cornell veya flashcard formatında otomatik notlar oluştur.
        </p>
        <button className="px-4 py-2 bg-green-500/20 border border-green-500/50 text-green-300 rounded-xl">
          Not Oluştur
        </button>
      </div>
    </div>
  );
};

// Multimodal Tab - Placeholder
const MultimodalTab: React.FC = () => (
  <div className="space-y-6">
    <div className="bg-gray-800/50 rounded-2xl p-6 border border-pink-500/30">
      <div className="flex items-center gap-3 mb-4">
        <div className="p-3 rounded-xl bg-gradient-to-br from-pink-500 to-rose-500">
          <PenTool className="w-6 h-6 text-white" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-white">Görsel Dersler</h3>
          <p className="text-sm text-gray-400">İnteraktif görsellerle öğren</p>
        </div>
      </div>
      <p className="text-gray-300">Her kavram için otomatik infografik ve diyagram oluşturulur.</p>
    </div>

    <div className="bg-gray-800/50 rounded-2xl p-6 border border-violet-500/30">
      <div className="flex items-center gap-3 mb-4">
        <div className="p-3 rounded-xl bg-gradient-to-br from-violet-500 to-purple-500">
          <Code className="w-6 h-6 text-white" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-white">Code Playground</h3>
          <p className="text-sm text-gray-400">Kodla pratik yap</p>
        </div>
      </div>
      <p className="text-gray-300">Kavramları kod yazarak öğren. Anında feedback al.</p>
    </div>
  </div>
);

// Spaced Rep Tab - Placeholder
const SpacedRepTab: React.FC = () => (
  <div className="space-y-6">
    <div className="bg-gray-800/50 rounded-2xl p-6 border border-green-500/30">
      <div className="flex items-center gap-3 mb-4">
        <div className="p-3 rounded-xl bg-gradient-to-br from-green-500 to-emerald-500">
          <Timer className="w-6 h-6 text-white" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-white">Context-Aware Spacing</h3>
          <p className="text-sm text-gray-400">Bağlama göre tekrar aralıkları</p>
        </div>
      </div>
      <p className="text-gray-300">Sadece zamana değil, bağlama ve duygu durumuna göre akıllı tekrar.</p>
    </div>

    <div className="bg-gray-800/50 rounded-2xl p-6 border border-rose-500/30">
      <div className="flex items-center gap-3 mb-4">
        <div className="p-3 rounded-xl bg-gradient-to-br from-rose-500 to-pink-500">
          <Heart className="w-6 h-6 text-white" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-white">Emotional Tagging</h3>
          <p className="text-sm text-gray-400">Duygusal bağlam</p>
        </div>
      </div>
      <p className="text-gray-300">Kartları duygusal etiketlerle işaretle, daha iyi hatırla.</p>
    </div>

    <div className="bg-gray-800/50 rounded-2xl p-6 border border-cyan-500/30">
      <div className="flex items-center gap-3 mb-4">
        <div className="p-3 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-500">
          <Link className="w-6 h-6 text-white" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-white">Related Recall</h3>
          <p className="text-sm text-gray-400">İlişkili kavramları birlikte</p>
        </div>
      </div>
      <p className="text-gray-300">Bir kartı tekrar ederken ilişkili kavramları da hatırlat.</p>
    </div>
  </div>
);

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function FullMetaPremiumFeatures() {
  const [activeTab, setActiveTab] = useState<FeatureTab>('neuroscience');
  const userId = 'default_user';

  const renderTabContent = () => {
    switch (activeTab) {
      case 'neuroscience':
        return <NeuroscienceTab userId={userId} />;
      case 'gamification':
        return <GamificationTab userId={userId} />;
      case 'adaptive':
        return <AdaptiveTab userId={userId} />;
      case 'multimodal':
        return <MultimodalTab />;
      case 'spaced-rep':
        return <SpacedRepTab />;
      case 'feynman':
        return <FeynmanTab userId={userId} />;
      case 'analytics':
        return <AnalyticsTab userId={userId} />;
      case 'premium':
        return <PremiumTab userId={userId} />;
      default:
        return null;
    }
  };

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-gray-900 via-gray-900 to-gray-800">
      {/* Header */}
      <div className="p-6 border-b border-gray-700/50">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500">
            <Sparkles className="w-7 h-7 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Premium Öğrenme Özellikleri</h1>
            <p className="text-sm text-gray-400">Full Meta Learning - Gelişmiş Modüller</p>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-2 overflow-x-auto pb-2">
          {FEATURE_TABS.map((tab) => (
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
    </div>
  );
}
