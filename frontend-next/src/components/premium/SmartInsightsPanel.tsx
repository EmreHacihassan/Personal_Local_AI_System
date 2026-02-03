'use client';

/**
 * 🧠 Smart Insights Panel
 * AI-powered note analysis with readability, sentiment, and suggestions
 */

import React, { useState, useEffect } from 'react';
import { 
  Brain, 
  Clock, 
  FileText, 
  TrendingUp, 
  Lightbulb,
  Hash,
  Link2,
  Code,
  Image as ImageIcon,
  X,
  RefreshCw,
  BarChart3,
  Smile,
  Meh,
  Frown
} from 'lucide-react';

interface NoteInsights {
  word_count: number;
  character_count: number;
  sentence_count: number;
  paragraph_count: number;
  reading_time_minutes: number;
  readability_score: number;
  sentiment: 'positive' | 'negative' | 'neutral';
  suggestions: string[];
  has_links: boolean;
  has_images: boolean;
  has_code: boolean;
  has_latex: boolean;
  markdown_elements: {
    headers: number;
    bold: number;
    italic: number;
    links: number;
    code_blocks: number;
    inline_code: number;
    lists: number;
    checkboxes: number;
    images: number;
    latex: number;
  };
}

interface SmartInsightsPanelProps {
  noteId: string;
  noteTitle?: string;
  isOpen: boolean;
  onClose: () => void;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function SmartInsightsPanel({ noteId, noteTitle, isOpen, onClose }: SmartInsightsPanelProps) {
  const [insights, setInsights] = useState<NoteInsights | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchInsights = async () => {
    if (!noteId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_URL}/api/notes/premium/insights/${noteId}`);
      if (!response.ok) throw new Error('Failed to fetch insights');
      
      const data = await response.json();
      if (data.success) {
        setInsights(data.insights);
      } else {
        throw new Error(data.error || 'Unknown error');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error fetching insights');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && noteId) {
      fetchInsights();
    }
  }, [isOpen, noteId]);

  if (!isOpen) return null;

  const getSentimentIcon = () => {
    if (!insights) return <Meh className="w-5 h-5 text-gray-400" />;
    switch (insights.sentiment) {
      case 'positive': return <Smile className="w-5 h-5 text-green-500" />;
      case 'negative': return <Frown className="w-5 h-5 text-red-500" />;
      default: return <Meh className="w-5 h-5 text-yellow-500" />;
    }
  };

  const getReadabilityColor = (score: number) => {
    if (score >= 70) return 'text-green-500';
    if (score >= 50) return 'text-yellow-500';
    return 'text-red-500';
  };

  const getReadabilityLabel = (score: number) => {
    if (score >= 80) return 'Çok Kolay';
    if (score >= 60) return 'Kolay';
    if (score >= 40) return 'Orta';
    if (score >= 20) return 'Zor';
    return 'Çok Zor';
  };

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-white dark:bg-gray-900 shadow-2xl z-50 flex flex-col border-l border-gray-200 dark:border-gray-700">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-purple-500 to-indigo-600">
        <div className="flex items-center gap-2 text-white">
          <Brain className="w-6 h-6" />
          <span className="font-semibold">Smart Insights</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchInsights}
            disabled={loading}
            className="p-1.5 hover:bg-white/20 rounded-lg text-white transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-white/20 rounded-lg text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {loading && (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin w-8 h-8 border-4 border-purple-500 border-t-transparent rounded-full" />
          </div>
        )}

        {error && (
          <div className="p-4 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg">
            {error}
          </div>
        )}

        {insights && !loading && (
          <>
            {/* Quick Stats */}
            <div className="grid grid-cols-2 gap-3">
              <StatCard
                icon={<FileText className="w-4 h-4 text-blue-500" />}
                label="Kelime"
                value={insights.word_count.toLocaleString()}
              />
              <StatCard
                icon={<Clock className="w-4 h-4 text-green-500" />}
                label="Okuma Süresi"
                value={`${insights.reading_time_minutes} dk`}
              />
              <StatCard
                icon={<Hash className="w-4 h-4 text-purple-500" />}
                label="Paragraf"
                value={insights.paragraph_count.toString()}
              />
              <StatCard
                icon={<FileText className="w-4 h-4 text-orange-500" />}
                label="Cümle"
                value={insights.sentence_count.toString()}
              />
            </div>

            {/* Readability Score */}
            <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-4">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Okunabilirlik Skoru
                </span>
                <span className={`text-lg font-bold ${getReadabilityColor(insights.readability_score)}`}>
                  {insights.readability_score}%
                </span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5 mb-2">
                <div
                  className={`h-2.5 rounded-full transition-all ${
                    insights.readability_score >= 70 ? 'bg-green-500' :
                    insights.readability_score >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${insights.readability_score}%` }}
                />
              </div>
              <span className="text-xs text-gray-500">
                {getReadabilityLabel(insights.readability_score)}
              </span>
            </div>

            {/* Sentiment */}
            <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Duygu Analizi
                </span>
                <div className="flex items-center gap-2">
                  {getSentimentIcon()}
                  <span className="text-sm capitalize">
                    {insights.sentiment === 'positive' ? 'Pozitif' :
                     insights.sentiment === 'negative' ? 'Negatif' : 'Nötr'}
                  </span>
                </div>
              </div>
            </div>

            {/* Content Features */}
            <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-4">
              <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">
                İçerik Özellikleri
              </h3>
              <div className="flex flex-wrap gap-2">
                {insights.has_links && (
                  <FeatureBadge icon={<Link2 className="w-3 h-3" />} label="Bağlantılar" />
                )}
                {insights.has_images && (
                  <FeatureBadge icon={<ImageIcon className="w-3 h-3" />} label="Görseller" />
                )}
                {insights.has_code && (
                  <FeatureBadge icon={<Code className="w-3 h-3" />} label="Kod" />
                )}
                {insights.has_latex && (
                  <FeatureBadge icon={<span className="text-xs">∑</span>} label="LaTeX" />
                )}
                {insights.markdown_elements.headers > 0 && (
                  <FeatureBadge icon={<span className="text-xs font-bold">H</span>} label={`${insights.markdown_elements.headers} Başlık`} />
                )}
                {insights.markdown_elements.lists > 0 && (
                  <FeatureBadge icon={<span className="text-xs">•</span>} label={`${insights.markdown_elements.lists} Liste`} />
                )}
                {insights.markdown_elements.checkboxes > 0 && (
                  <FeatureBadge icon={<span className="text-xs">☑</span>} label={`${insights.markdown_elements.checkboxes} Görev`} />
                )}
              </div>
            </div>

            {/* AI Suggestions */}
            {insights.suggestions.length > 0 && (
              <div className="bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-900/20 dark:to-orange-900/20 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Lightbulb className="w-5 h-5 text-amber-500" />
                  <h3 className="text-sm font-medium text-gray-800 dark:text-gray-200">
                    AI Önerileri
                  </h3>
                </div>
                <ul className="space-y-2">
                  {insights.suggestions.map((suggestion, idx) => (
                    <li key={idx} className="text-sm text-gray-600 dark:text-gray-400">
                      {suggestion}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Markdown Stats */}
            <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-4">
              <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3 flex items-center gap-2">
                <BarChart3 className="w-4 h-4" />
                Markdown İstatistikleri
              </h3>
              <div className="grid grid-cols-3 gap-2 text-center text-xs">
                <div className="bg-white dark:bg-gray-700 p-2 rounded-lg">
                  <div className="font-bold text-purple-500">{insights.markdown_elements.bold}</div>
                  <div className="text-gray-500">Kalın</div>
                </div>
                <div className="bg-white dark:bg-gray-700 p-2 rounded-lg">
                  <div className="font-bold text-blue-500">{insights.markdown_elements.italic}</div>
                  <div className="text-gray-500">İtalik</div>
                </div>
                <div className="bg-white dark:bg-gray-700 p-2 rounded-lg">
                  <div className="font-bold text-green-500">{insights.markdown_elements.code_blocks}</div>
                  <div className="text-gray-500">Kod Blok</div>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function StatCard({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-3 flex items-center gap-3">
      <div className="p-2 bg-white dark:bg-gray-700 rounded-lg shadow-sm">
        {icon}
      </div>
      <div>
        <div className="text-lg font-bold text-gray-800 dark:text-white">{value}</div>
        <div className="text-xs text-gray-500">{label}</div>
      </div>
    </div>
  );
}

function FeatureBadge({ icon, label }: { icon: React.ReactNode; label: string }) {
  return (
    <span className="inline-flex items-center gap-1 px-2 py-1 bg-white dark:bg-gray-700 rounded-full text-xs text-gray-600 dark:text-gray-300 shadow-sm">
      {icon}
      {label}
    </span>
  );
}

export default SmartInsightsPanel;
