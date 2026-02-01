'use client';

/**
 * 🏆 Gamification Widget
 * Writing streaks, badges, levels, and daily digest
 */

import React, { useState, useEffect } from 'react';
import { 
  Flame, 
  Trophy, 
  Star, 
  TrendingUp,
  Calendar,
  Target,
  Zap,
  Award,
  ChevronRight,
  Sparkles,
  RefreshCw,
  X
} from 'lucide-react';

interface Badge {
  id: string;
  title: string;
  description: string;
  points: number;
}

interface UserStats {
  total_notes: number;
  total_words: number;
  total_folders: number;
  total_links: number;
  total_pomodoros: number;
  total_focus_minutes: number;
  points: number;
  level: number;
  level_progress: number;
  badges: Badge[];
  streak: {
    current_streak: number;
    longest_streak: number;
    last_activity: string | null;
    total_writing_days: number;
    streak_status: {
      emoji: string;
      message: string;
      level: string;
    };
    next_milestone: {
      target: number;
      remaining: number;
    };
  };
}

interface DailyDigest {
  date: string;
  greeting: string;
  motivation: string;
  today_stats: {
    notes_created: number;
    notes_edited: number;
    words_today: number;
  };
  week_stats: {
    total_notes: number;
    total_words: number;
    most_active_day: string;
  };
  streak: {
    current_streak: number;
    streak_status: {
      emoji: string;
      message: string;
    };
  };
  level_info: {
    level: number;
    points: number;
    progress: number;
  };
  suggestions: Array<{
    type: string;
    title: string;
    message: string;
    notes?: Array<{ id: string; title: string }>;
  }>;
  achievements: {
    badges_count: number;
    total_pomodoros: number;
    focus_hours: number;
  };
}

interface GamificationWidgetProps {
  compact?: boolean;
  showDigest?: boolean;
  onNoteClick?: (noteId: string) => void;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export function GamificationWidget({ compact = false, showDigest = false, onNoteClick }: GamificationWidgetProps) {
  const [stats, setStats] = useState<UserStats | null>(null);
  const [digest, setDigest] = useState<DailyDigest | null>(null);
  const [loading, setLoading] = useState(true);
  const [showBadges, setShowBadges] = useState(false);

  const fetchStats = async () => {
    setLoading(true);
    try {
      const [statsRes, digestRes] = await Promise.all([
        fetch(`${API_URL}/api/notes/premium/stats`),
        showDigest ? fetch(`${API_URL}/api/notes/premium/digest`) : Promise.resolve(null),
      ]);

      if (statsRes.ok) {
        const statsData = await statsRes.json();
        if (statsData.success) setStats(statsData);
      }

      if (digestRes && digestRes.ok) {
        const digestData = await digestRes.json();
        if (digestData.success) setDigest(digestData);
      }
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, [showDigest]);

  if (loading) {
    return (
      <div className="p-4 flex items-center justify-center">
        <RefreshCw className="w-5 h-5 animate-spin text-purple-500" />
      </div>
    );
  }

  if (!stats) return null;

  // Compact Mode - Just streak flame
  if (compact) {
    return (
      <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-orange-100 to-red-100 dark:from-orange-900/30 dark:to-red-900/30 rounded-full">
        <span className="text-lg">{stats.streak.streak_status.emoji}</span>
        <span className="font-bold text-orange-600 dark:text-orange-400">
          {stats.streak.current_streak}
        </span>
        <Flame className="w-4 h-4 text-orange-500" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Daily Greeting & Motivation */}
      {digest && (
        <div className="bg-gradient-to-br from-purple-500 to-indigo-600 rounded-2xl p-6 text-white">
          <h2 className="text-2xl font-bold mb-1">{digest.greeting}</h2>
          <p className="text-white/80 text-sm">{digest.motivation}</p>
          
          <div className="grid grid-cols-3 gap-4 mt-4">
            <div className="text-center">
              <div className="text-2xl font-bold">{digest.today_stats.notes_created}</div>
              <div className="text-xs text-white/70">Yeni Not</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold">{digest.today_stats.words_today}</div>
              <div className="text-xs text-white/70">Kelime</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold">{digest.achievements.total_pomodoros}</div>
              <div className="text-xs text-white/70">Pomodoro</div>
            </div>
          </div>
        </div>
      )}

      {/* Streak Card */}
      <div className="bg-gradient-to-br from-orange-50 to-red-50 dark:from-orange-900/20 dark:to-red-900/20 rounded-2xl p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-800 dark:text-white flex items-center gap-2">
            <Flame className="w-5 h-5 text-orange-500" />
            Yazma Serisi
          </h3>
          <span className="text-3xl">{stats.streak.streak_status.emoji}</span>
        </div>
        
        <div className="flex items-end gap-4 mb-3">
          <div>
            <div className="text-5xl font-bold text-orange-600 dark:text-orange-400">
              {stats.streak.current_streak}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">gün seri</div>
          </div>
          <div className="text-sm text-gray-500 dark:text-gray-400">
            En uzun: <strong>{stats.streak.longest_streak}</strong> gün
          </div>
        </div>
        
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
          {stats.streak.streak_status.message}
        </p>
        
        {/* Progress to next milestone */}
        <div className="bg-white/50 dark:bg-black/20 rounded-lg p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-gray-500">Sonraki hedef</span>
            <span className="text-xs font-medium text-orange-600">
              {stats.streak.next_milestone.target} gün
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div
              className="h-2 rounded-full bg-gradient-to-r from-orange-400 to-red-500"
              style={{ 
                width: `${Math.min(100, (stats.streak.current_streak / stats.streak.next_milestone.target) * 100)}%` 
              }}
            />
          </div>
          <div className="text-xs text-gray-500 mt-1 text-center">
            {stats.streak.next_milestone.remaining} gün kaldı
          </div>
        </div>
      </div>

      {/* Level & Points */}
      <div className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-2xl p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-800 dark:text-white flex items-center gap-2">
            <Star className="w-5 h-5 text-yellow-500" />
            Seviye & Puan
          </h3>
          <div className="flex items-center gap-1 px-3 py-1 bg-yellow-100 dark:bg-yellow-900/30 rounded-full">
            <Zap className="w-4 h-4 text-yellow-600" />
            <span className="font-bold text-yellow-700 dark:text-yellow-400">
              {stats.points} XP
            </span>
          </div>
        </div>

        <div className="flex items-center gap-4 mb-3">
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white text-2xl font-bold shadow-lg">
            {stats.level}
          </div>
          <div>
            <div className="text-lg font-semibold text-gray-800 dark:text-white">
              Seviye {stats.level}
            </div>
            <div className="text-sm text-gray-500">
              {100 - stats.level_progress} XP sonraki seviyeye
            </div>
          </div>
        </div>

        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
          <div
            className="h-3 rounded-full bg-gradient-to-r from-blue-500 to-indigo-500 transition-all"
            style={{ width: `${stats.level_progress}%` }}
          />
        </div>
      </div>

      {/* Badges */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
        <div 
          className="flex items-center justify-between cursor-pointer"
          onClick={() => setShowBadges(!showBadges)}
        >
          <h3 className="font-semibold text-gray-800 dark:text-white flex items-center gap-2">
            <Trophy className="w-5 h-5 text-amber-500" />
            Rozetler
            <span className="text-sm font-normal text-gray-500">
              ({stats.badges.length} kazanıldı)
            </span>
          </h3>
          <ChevronRight className={`w-5 h-5 text-gray-400 transition-transform ${showBadges ? 'rotate-90' : ''}`} />
        </div>

        {showBadges && (
          <div className="mt-4 grid grid-cols-2 gap-3">
            {stats.badges.length > 0 ? (
              stats.badges.map((badge) => (
                <div
                  key={badge.id}
                  className="p-3 bg-gradient-to-br from-amber-50 to-yellow-50 dark:from-amber-900/20 dark:to-yellow-900/20 rounded-xl"
                >
                  <div className="text-lg mb-1">{badge.title}</div>
                  <div className="text-xs text-gray-600 dark:text-gray-400">{badge.description}</div>
                  <div className="text-xs text-amber-600 mt-1">+{badge.points} XP</div>
                </div>
              ))
            ) : (
              <div className="col-span-2 text-center py-4 text-gray-500">
                <Award className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>Henüz rozet kazanılmadı</p>
                <p className="text-xs mt-1">Not yazarak rozet kazan!</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 gap-3">
        <StatCard
          icon={<Sparkles className="w-5 h-5 text-purple-500" />}
          value={stats.total_notes}
          label="Toplam Not"
          color="purple"
        />
        <StatCard
          icon={<TrendingUp className="w-5 h-5 text-green-500" />}
          value={`${Math.round(stats.total_words / 1000)}k`}
          label="Kelime Yazıldı"
          color="green"
        />
        <StatCard
          icon={<Target className="w-5 h-5 text-red-500" />}
          value={stats.total_pomodoros}
          label="Pomodoro"
          color="red"
        />
        <StatCard
          icon={<Calendar className="w-5 h-5 text-blue-500" />}
          value={stats.streak.total_writing_days}
          label="Aktif Gün"
          color="blue"
        />
      </div>

      {/* Suggestions from Digest */}
      {digest && digest.suggestions.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-2xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
          <h3 className="font-semibold text-gray-800 dark:text-white mb-3">
            💡 Öneriler
          </h3>
          {digest.suggestions.map((suggestion, idx) => (
            <div key={idx} className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg mb-2">
              <div className="font-medium text-sm">{suggestion.title}</div>
              <div className="text-xs text-gray-500 mt-1">{suggestion.message}</div>
              {suggestion.notes && (
                <div className="mt-2 space-y-1">
                  {suggestion.notes.map((note) => (
                    <button
                      key={note.id}
                      onClick={() => onNoteClick?.(note.id)}
                      className="block w-full text-left text-xs text-blue-600 hover:underline"
                    >
                      → {note.title}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function StatCard({ 
  icon, 
  value, 
  label, 
  color 
}: { 
  icon: React.ReactNode; 
  value: number | string; 
  label: string; 
  color: string 
}) {
  const bgColors: Record<string, string> = {
    purple: 'from-purple-50 to-indigo-50 dark:from-purple-900/20 dark:to-indigo-900/20',
    green: 'from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20',
    red: 'from-red-50 to-rose-50 dark:from-red-900/20 dark:to-rose-900/20',
    blue: 'from-blue-50 to-cyan-50 dark:from-blue-900/20 dark:to-cyan-900/20',
  };

  return (
    <div className={`bg-gradient-to-br ${bgColors[color]} rounded-xl p-4`}>
      <div className="flex items-center gap-2 mb-2">
        {icon}
      </div>
      <div className="text-2xl font-bold text-gray-800 dark:text-white">{value}</div>
      <div className="text-xs text-gray-500">{label}</div>
    </div>
  );
}

export default GamificationWidget;
