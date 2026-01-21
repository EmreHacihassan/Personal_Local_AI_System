'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ThumbsUp, 
  ArrowDownCircle, 
  ArrowUpCircle,
  CheckCircle,
  XCircle,
  RefreshCw,
  Info,
  Sparkles,
} from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * Model bilgisi arayüzü
 */
export interface ModelInfo {
  model_size: 'small' | 'large';
  model_name: string;
  model_icon: string;
  model_display_name: string;
  confidence: number;
  decision_source: string;
  response_id: string;
  attempt_number: number;
}

/**
 * Feedback tipi
 */
export type FeedbackType = 'correct' | 'downgrade' | 'upgrade';

/**
 * ModelBadge Props
 */
interface ModelBadgeProps {
  modelInfo: ModelInfo;
  onFeedback?: (type: FeedbackType, responseId: string) => void;
  onCompare?: (responseId: string) => void;
  showFeedback?: boolean;
  compact?: boolean;
  language?: 'tr' | 'en' | 'de';
}

/**
 * Model Badge - Her yanıtta model bilgisini gösteren badge
 * 
 * Features:
 * - Model ikonu ve adı (🟢 4B veya 🔵 8B)
 * - Güven skoru
 * - Feedback butonları
 * - Karşılaştırma butonu
 * - Attempt sayısı [1] [2]
 */
export function ModelBadge({
  modelInfo,
  onFeedback,
  onCompare,
  showFeedback = true,
  compact = false,
  language = 'tr',
}: ModelBadgeProps) {
  const [showTooltip, setShowTooltip] = useState(false);
  const [feedbackGiven, setFeedbackGiven] = useState<FeedbackType | null>(null);
  const [isHovered, setIsHovered] = useState(false);

  const isSmall = modelInfo.model_size === 'small';
  
  const labels = {
    tr: {
      confidence: 'Güven',
      correct: 'Doğru model',
      downgrade: 'Küçük yeterliydi',
      upgrade: 'Büyük lazımdı',
      compare: 'Diğerini dene',
      attempt: 'Deneme',
      sources: {
        rule_based: 'Kural tabanlı',
        ai_router: 'AI yönlendirme',
        learned: 'Öğrenilmiş',
        similarity: 'Benzerlik',
        default: 'Varsayılan',
      },
    },
    en: {
      confidence: 'Confidence',
      correct: 'Correct model',
      downgrade: 'Small was enough',
      upgrade: 'Large was needed',
      compare: 'Try other',
      attempt: 'Attempt',
      sources: {
        rule_based: 'Rule-based',
        ai_router: 'AI routing',
        learned: 'Learned',
        similarity: 'Similarity',
        default: 'Default',
      },
    },
    de: {
      confidence: 'Vertrauen',
      correct: 'Richtiges Modell',
      downgrade: 'Klein war genug',
      upgrade: 'Groß war nötig',
      compare: 'Andere testen',
      attempt: 'Versuch',
      sources: {
        rule_based: 'Regelbasiert',
        ai_router: 'KI-Routing',
        learned: 'Gelernt',
        similarity: 'Ähnlichkeit',
        default: 'Standard',
      },
    },
  };

  const t = labels[language];

  const handleFeedback = (type: FeedbackType) => {
    setFeedbackGiven(type);
    onFeedback?.(type, modelInfo.response_id);
  };

  // Compact mode - sadece ikon göster
  if (compact) {
    return (
      <div 
        className="inline-flex items-center gap-1"
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
      >
        <span className="text-sm" title={modelInfo.model_display_name}>
          {modelInfo.model_icon}
        </span>
        {modelInfo.attempt_number > 1 && (
          <span className="text-xs text-muted-foreground">
            [{modelInfo.attempt_number}]
          </span>
        )}
      </div>
    );
  }

  return (
    <div 
      className="relative inline-flex items-center"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Main Badge */}
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className={cn(
          "flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium",
          "border transition-all duration-200",
          isSmall 
            ? "bg-green-50 dark:bg-green-950/30 border-green-200 dark:border-green-800 text-green-700 dark:text-green-300"
            : "bg-blue-50 dark:bg-blue-950/30 border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-300",
          isHovered && "shadow-md"
        )}
      >
        {/* Model Icon */}
        <span className="text-base">{modelInfo.model_icon}</span>
        
        {/* Model Name */}
        <span className="font-semibold">{modelInfo.model_display_name}</span>
        
        {/* Confidence Indicator */}
        <div 
          className={cn(
            "w-1.5 h-1.5 rounded-full",
            modelInfo.confidence >= 0.8 ? "bg-green-500" :
            modelInfo.confidence >= 0.6 ? "bg-yellow-500" : "bg-orange-500"
          )}
          title={`${t.confidence}: ${Math.round(modelInfo.confidence * 100)}%`}
        />
        
        {/* Attempt Number */}
        {modelInfo.attempt_number > 1 && (
          <span className="px-1.5 py-0.5 bg-white/50 dark:bg-black/20 rounded-full text-[10px]">
            [{modelInfo.attempt_number}]
          </span>
        )}
        
        {/* Info Button */}
        <button
          onClick={() => setShowTooltip(!showTooltip)}
          className="p-0.5 hover:bg-white/50 dark:hover:bg-black/20 rounded-full transition-colors"
        >
          <Info className="w-3 h-3" />
        </button>
      </motion.div>

      {/* Tooltip with Details */}
      <AnimatePresence>
        {showTooltip && (
          <motion.div
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 5 }}
            className={cn(
              "absolute bottom-full left-0 mb-2 p-3 rounded-lg shadow-xl z-50",
              "bg-card border border-border min-w-[200px]"
            )}
          >
            <div className="space-y-2 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Model:</span>
                <span className="font-medium">{modelInfo.model_name}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">{t.confidence}:</span>
                <span className="font-medium">{Math.round(modelInfo.confidence * 100)}%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Kaynak:</span>
                <span className="font-medium text-xs">
                  {t.sources[modelInfo.decision_source as keyof typeof t.sources] || modelInfo.decision_source}
                </span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Feedback Buttons - Show on hover or when no feedback given */}
      <AnimatePresence>
        {showFeedback && isHovered && !feedbackGiven && (
          <motion.div
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -10 }}
            className="ml-2 flex items-center gap-1"
          >
            {/* Correct - Doğru model */}
            <button
              onClick={() => handleFeedback('correct')}
              className={cn(
                "p-1.5 rounded-full transition-all",
                "hover:bg-green-100 dark:hover:bg-green-900/30 text-muted-foreground hover:text-green-600"
              )}
              title={t.correct}
            >
              <ThumbsUp className="w-3.5 h-3.5" />
            </button>

            {/* Downgrade - Küçük yeterliydi (sadece büyük modelde) */}
            {!isSmall && (
              <button
                onClick={() => handleFeedback('downgrade')}
                className={cn(
                  "p-1.5 rounded-full transition-all",
                  "hover:bg-yellow-100 dark:hover:bg-yellow-900/30 text-muted-foreground hover:text-yellow-600"
                )}
                title={t.downgrade}
              >
                <ArrowDownCircle className="w-3.5 h-3.5" />
              </button>
            )}

            {/* Upgrade - Büyük lazımdı (sadece küçük modelde) */}
            {isSmall && (
              <button
                onClick={() => handleFeedback('upgrade')}
                className={cn(
                  "p-1.5 rounded-full transition-all",
                  "hover:bg-orange-100 dark:hover:bg-orange-900/30 text-muted-foreground hover:text-orange-600"
                )}
                title={t.upgrade}
              >
                <ArrowUpCircle className="w-3.5 h-3.5" />
              </button>
            )}

            {/* Compare - Diğerini dene */}
            <button
              onClick={() => onCompare?.(modelInfo.response_id)}
              className={cn(
                "p-1.5 rounded-full transition-all",
                "hover:bg-purple-100 dark:hover:bg-purple-900/30 text-muted-foreground hover:text-purple-600"
              )}
              title={t.compare}
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </motion.div>
        )}

        {/* Feedback Given Indicator */}
        {feedbackGiven && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            className={cn(
              "ml-2 flex items-center gap-1 px-2 py-1 rounded-full text-xs",
              feedbackGiven === 'correct' && "bg-green-100 dark:bg-green-900/30 text-green-600",
              feedbackGiven === 'downgrade' && "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-600",
              feedbackGiven === 'upgrade' && "bg-orange-100 dark:bg-orange-900/30 text-orange-600"
            )}
          >
            <CheckCircle className="w-3 h-3" />
            <span>
              {feedbackGiven === 'correct' ? '✓' : 
               feedbackGiven === 'downgrade' ? '↓' : '↑'}
            </span>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/**
 * Comparison View - İki model yanıtını yan yana göster
 */
interface ComparisonViewProps {
  originalResponse: string;
  comparisonResponse: string;
  originalModel: {
    name: string;
    icon: string;
    displayName: string;
  };
  comparisonModel: {
    name: string;
    icon: string;
    displayName: string;
  };
  isLoading?: boolean;
  onSelect: (selectedModel: 'small' | 'large') => void;
  onClose: () => void;
  language?: 'tr' | 'en' | 'de';
}

export function ComparisonView({
  originalResponse,
  comparisonResponse,
  originalModel,
  comparisonModel,
  isLoading = false,
  onSelect,
  onClose,
  language = 'tr',
}: ComparisonViewProps) {
  const labels = {
    tr: {
      title: 'Model Karşılaştırması',
      original: 'Orijinal Yanıt',
      comparison: 'Alternatif Yanıt',
      select: 'Bu modeli seç',
      cancel: 'İptal',
      loading: 'Alternatif yanıt yükleniyor...',
    },
    en: {
      title: 'Model Comparison',
      original: 'Original Response',
      comparison: 'Alternative Response',
      select: 'Select this model',
      cancel: 'Cancel',
      loading: 'Loading alternative response...',
    },
    de: {
      title: 'Modellvergleich',
      original: 'Ursprüngliche Antwort',
      comparison: 'Alternative Antwort',
      select: 'Dieses Modell wählen',
      cancel: 'Abbrechen',
      loading: 'Alternative Antwort wird geladen...',
    },
  };

  const t = labels[language];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
    >
      <div className="w-full max-w-4xl bg-card rounded-2xl shadow-2xl border border-border overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border bg-muted/50">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-primary" />
            {t.title}
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-accent rounded-lg transition-colors"
          >
            <XCircle className="w-5 h-5" />
          </button>
        </div>

        {/* Comparison Grid */}
        <div className="grid grid-cols-2 gap-4 p-4 max-h-[60vh] overflow-y-auto">
          {/* Original Response */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-muted-foreground">{t.original}</span>
              <div className="flex items-center gap-1.5 px-2 py-1 bg-blue-100 dark:bg-blue-900/30 rounded-full">
                <span>{originalModel.icon}</span>
                <span className="text-xs font-medium text-blue-700 dark:text-blue-400">
                  {originalModel.displayName}
                </span>
              </div>
            </div>
            <div className="p-3 bg-muted/50 rounded-xl min-h-[200px] text-sm whitespace-pre-wrap">
              {originalResponse}
            </div>
            <button
              onClick={() => onSelect('small')}
              className="w-full py-2 px-4 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              <CheckCircle className="w-4 h-4" />
              {t.select}
            </button>
          </div>

          {/* Comparison Response */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-muted-foreground">{t.comparison}</span>
              <div className="flex items-center gap-1.5 px-2 py-1 bg-purple-100 dark:bg-purple-900/30 rounded-full">
                <span>{comparisonModel.icon}</span>
                <span className="text-xs font-medium text-purple-700 dark:text-purple-400">
                  {comparisonModel.displayName}
                </span>
              </div>
            </div>
            <div className="p-3 bg-muted/50 rounded-xl min-h-[200px] text-sm whitespace-pre-wrap">
              {isLoading ? (
                <div className="flex items-center gap-2 text-muted-foreground">
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  {t.loading}
                </div>
              ) : (
                comparisonResponse
              )}
            </div>
            <button
              onClick={() => onSelect('large')}
              disabled={isLoading}
              className={cn(
                "w-full py-2 px-4 rounded-lg transition-colors flex items-center justify-center gap-2",
                isLoading 
                  ? "bg-muted text-muted-foreground cursor-not-allowed"
                  : "bg-purple-500 hover:bg-purple-600 text-white"
              )}
            >
              <CheckCircle className="w-4 h-4" />
              {t.select}
            </button>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-border bg-muted/30 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-muted-foreground hover:text-foreground transition-colors"
          >
            {t.cancel}
          </button>
        </div>
      </div>
    </motion.div>
  );
}

export default ModelBadge;
