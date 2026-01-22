'use client';

import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  Clock, 
  MessageSquare,
  Code,
  Bot,
  Lightbulb,
  RefreshCw,
  Calendar,
  Zap
} from 'lucide-react';

interface AnalyticsDashboardProps {
  className?: string;
}

interface DashboardData {
  summary_7d: {
    total_events: number;
    success_rate: number;
    events_by_type: Record<string, number>;
    most_active_hour: number;
    daily_activity: Record<string, number>;
    hourly_distribution: Record<string, number>;
  };
  productivity: {
    productivity_score: number;
    tasks: {
      created: number;
      completed: number;
      completion_rate: number;
    };
    chat: {
      total_messages: number;
      avg_per_day: number;
    };
    code: {
      executions: number;
      success_rate: number;
    };
    automation: {
      agent_runs: number;
      workflow_runs: number;
    };
  };
  trends: {
    week_over_week_growth: number;
    top_features: Array<{ feature: string; count: number }>;
    feature_usage: Record<string, number>;
  };
  recent_insights: Array<{
    id: string;
    summary: string;
    highlights: string[];
    recommendations: string[];
    generated_at: string;
  }>;
}

export function AnalyticsDashboard({ className = '' }: AnalyticsDashboardProps) {
  const [data, setData] = useState<DashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isGeneratingInsights, setIsGeneratingInsights] = useState(false);

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('http://localhost:8001/api/analytics/dashboard');
      const dashboardData = await res.json();
      setData(dashboardData);
    } catch (error) {
      console.error('Failed to fetch dashboard:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const generateInsights = async () => {
    setIsGeneratingInsights(true);
    try {
      await fetch('http://localhost:8001/api/analytics/insights/generate?days=7', {
        method: 'POST',
      });
      await fetchDashboard();
    } catch (error) {
      console.error('Failed to generate insights:', error);
    } finally {
      setIsGeneratingInsights(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 75) return 'text-green-400';
    if (score >= 50) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getScoreRing = (score: number) => {
    const circumference = 2 * Math.PI * 45;
    const strokeDashoffset = circumference - (score / 100) * circumference;
    
    let color = '#ef4444';
    if (score >= 75) color = '#22c55e';
    else if (score >= 50) color = '#eab308';
    
    return { strokeDashoffset, color };
  };

  if (isLoading) {
    return (
      <div className={`bg-gradient-to-br from-indigo-900/30 to-purple-900/30 rounded-xl border border-indigo-500/30 p-8 flex items-center justify-center ${className}`}>
        <div className="text-center">
          <RefreshCw className="w-8 h-8 text-indigo-400 animate-spin mx-auto mb-3" />
          <p className="text-gray-400">Yükleniyor...</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className={`bg-gradient-to-br from-indigo-900/30 to-purple-900/30 rounded-xl border border-indigo-500/30 p-8 ${className}`}>
        <p className="text-gray-400 text-center">Veri yüklenemedi</p>
      </div>
    );
  }

  const { summary_7d, productivity, trends, recent_insights } = data;
  const ringStyle = getScoreRing(productivity.productivity_score);

  return (
    <div className={`bg-gradient-to-br from-indigo-900/30 to-purple-900/30 rounded-xl border border-indigo-500/30 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-indigo-500/20 rounded-lg">
            <BarChart3 className="w-6 h-6 text-indigo-400" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">Kişisel Analitik</h2>
            <p className="text-sm text-gray-400">Verimlilik ve kullanım istatistikleri</p>
          </div>
        </div>
        <button
          onClick={fetchDashboard}
          className="p-2 bg-white/5 hover:bg-white/10 rounded-lg transition-colors"
        >
          <RefreshCw className="w-5 h-5 text-gray-400" />
        </button>
      </div>

      {/* Main Stats */}
      <div className="p-4 grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Productivity Score */}
        <div className="bg-white/5 rounded-xl p-4 flex items-center gap-4">
          <div className="relative w-24 h-24">
            <svg className="w-24 h-24 transform -rotate-90">
              <circle
                cx="48"
                cy="48"
                r="45"
                stroke="currentColor"
                strokeWidth="6"
                fill="none"
                className="text-white/10"
              />
              <circle
                cx="48"
                cy="48"
                r="45"
                stroke={ringStyle.color}
                strokeWidth="6"
                fill="none"
                strokeLinecap="round"
                strokeDasharray={2 * Math.PI * 45}
                strokeDashoffset={ringStyle.strokeDashoffset}
                className="transition-all duration-500"
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className={`text-2xl font-bold ${getScoreColor(productivity.productivity_score)}`}>
                {productivity.productivity_score}
              </span>
            </div>
          </div>
          <div>
            <h3 className="text-sm text-gray-400">Verimlilik Skoru</h3>
            <p className={`text-lg font-medium ${getScoreColor(productivity.productivity_score)}`}>
              {productivity.productivity_score >= 75 ? 'Mükemmel' :
               productivity.productivity_score >= 50 ? 'İyi' : 'Geliştirilmeli'}
            </p>
            <div className="flex items-center gap-1 mt-1">
              <TrendingUp className={`w-4 h-4 ${trends.week_over_week_growth >= 0 ? 'text-green-400' : 'text-red-400'}`} />
              <span className={`text-xs ${trends.week_over_week_growth >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {trends.week_over_week_growth >= 0 ? '+' : ''}{trends.week_over_week_growth}% bu hafta
              </span>
            </div>
          </div>
        </div>

        {/* Total Events */}
        <div className="bg-white/5 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <Zap className="w-5 h-5 text-yellow-400" />
            <h3 className="text-sm text-gray-400">Toplam Etkinlik</h3>
          </div>
          <p className="text-3xl font-bold text-white">{summary_7d.total_events}</p>
          <p className="text-xs text-gray-400 mt-1">Son 7 günde</p>
          <div className="flex items-center gap-2 mt-2">
            <span className="text-xs text-green-400">%{summary_7d.success_rate} başarı</span>
          </div>
        </div>

        {/* Most Active Hour */}
        <div className="bg-white/5 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <Clock className="w-5 h-5 text-blue-400" />
            <h3 className="text-sm text-gray-400">En Aktif Saat</h3>
          </div>
          <p className="text-3xl font-bold text-white">
            {summary_7d.most_active_hour !== null ? `${String(summary_7d.most_active_hour).padStart(2, '0')}:00` : '--'}
          </p>
          <p className="text-xs text-gray-400 mt-1">Saatlik dağılıma göre</p>
        </div>
      </div>

      {/* Feature Usage */}
      <div className="p-4 border-t border-white/10">
        <h3 className="text-sm font-medium text-gray-400 mb-3 flex items-center gap-2">
          <BarChart3 className="w-4 h-4" />
          Özellik Kullanımı
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="bg-white/5 rounded-lg p-3 text-center">
            <MessageSquare className="w-5 h-5 text-purple-400 mx-auto mb-2" />
            <p className="text-2xl font-bold text-white">{productivity.chat.total_messages}</p>
            <p className="text-xs text-gray-400">Mesaj</p>
          </div>
          <div className="bg-white/5 rounded-lg p-3 text-center">
            <Code className="w-5 h-5 text-green-400 mx-auto mb-2" />
            <p className="text-2xl font-bold text-white">{productivity.code.executions}</p>
            <p className="text-xs text-gray-400">Kod Çalıştırma</p>
          </div>
          <div className="bg-white/5 rounded-lg p-3 text-center">
            <Bot className="w-5 h-5 text-blue-400 mx-auto mb-2" />
            <p className="text-2xl font-bold text-white">{productivity.automation.agent_runs}</p>
            <p className="text-xs text-gray-400">Agent Çalıştırma</p>
          </div>
          <div className="bg-white/5 rounded-lg p-3 text-center">
            <Calendar className="w-5 h-5 text-yellow-400 mx-auto mb-2" />
            <p className="text-2xl font-bold text-white">{productivity.tasks.completed}</p>
            <p className="text-xs text-gray-400">Görev Tamamlama</p>
          </div>
        </div>
      </div>

      {/* Top Features */}
      {trends.top_features.length > 0 && (
        <div className="p-4 border-t border-white/10">
          <h3 className="text-sm font-medium text-gray-400 mb-3">En Çok Kullanılan Özellikler</h3>
          <div className="space-y-2">
            {trends.top_features.map((feature, idx) => (
              <div key={feature.feature} className="flex items-center gap-3">
                <span className="text-xs text-gray-500 w-4">{idx + 1}.</span>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm text-white">{feature.feature.replace(/_/g, ' ')}</span>
                    <span className="text-xs text-gray-400">{feature.count}</span>
                  </div>
                  <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-indigo-500 rounded-full"
                      style={{
                        width: `${Math.min((feature.count / Math.max(...trends.top_features.map(f => f.count))) * 100, 100)}%`
                      }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* AI Insights */}
      <div className="p-4 border-t border-white/10">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-medium text-gray-400 flex items-center gap-2">
            <Lightbulb className="w-4 h-4 text-yellow-400" />
            AI Önerileri
          </h3>
          <button
            onClick={generateInsights}
            disabled={isGeneratingInsights}
            className="flex items-center gap-2 px-3 py-1 bg-indigo-500/20 hover:bg-indigo-500/30 rounded-lg text-sm text-indigo-400 transition-colors"
          >
            {isGeneratingInsights ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Üretiliyor...
              </>
            ) : (
              <>
                <Lightbulb className="w-4 h-4" />
                Yeni Öneri
              </>
            )}
          </button>
        </div>

        {recent_insights.length > 0 ? (
          <div className="space-y-3">
            {recent_insights.slice(0, 2).map((insight) => (
              <div key={insight.id} className="bg-white/5 rounded-lg p-3">
                <p className="text-sm text-white mb-2">{insight.summary}</p>
                
                {insight.highlights.length > 0 && (
                  <div className="mb-2">
                    {insight.highlights.slice(0, 2).map((h, idx) => (
                      <p key={idx} className="text-xs text-green-400 flex items-center gap-1">
                        ✓ {h}
                      </p>
                    ))}
                  </div>
                )}
                
                {insight.recommendations.length > 0 && (
                  <div>
                    {insight.recommendations.slice(0, 2).map((r, idx) => (
                      <p key={idx} className="text-xs text-yellow-400 flex items-center gap-1">
                        💡 {r}
                      </p>
                    ))}
                  </div>
                )}
                
                <p className="text-xs text-gray-500 mt-2">
                  {new Date(insight.generated_at).toLocaleDateString('tr-TR')}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-4">
            <p className="text-sm text-gray-400">Henüz öneri yok</p>
            <button
              onClick={generateInsights}
              className="mt-2 text-sm text-indigo-400 hover:underline"
            >
              İlk öneriyi oluştur
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
