'use client';

import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Clock,
  Brain,
  CheckCircle,
  ChevronLeft,
  RotateCcw,
  Zap,
  Trophy,
  Target
} from 'lucide-react';

// ==================== TYPES ====================

interface ReviewItem {
  id: string;
  topic_id: string;
  type: string;
  retention: number;
  interval: number;
  next_review?: string;
  front?: string;
  back?: string;
  question?: string;
  answer?: string;
}

interface ReviewSessionProps {
  onComplete?: (stats: ReviewStats) => void;
  onClose?: () => void;
}

interface ReviewStats {
  total_reviewed: number;
  correct: number;
  incorrect: number;
  average_quality: number;
  xp_earned: number;
  time_spent_seconds: number;
}

// ==================== QUALITY BUTTONS ====================

const QUALITY_OPTIONS = [
  { value: 0, label: 'Hiç', emoji: '😫', color: '#EF4444', description: 'Hatırlanmadı' },
  { value: 1, label: 'Yanlış', emoji: '😕', color: '#F97316', description: 'Yanlış cevap' },
  { value: 2, label: 'Zor', emoji: '😐', color: '#F59E0B', description: 'Zorlanarak hatırlandı' },
  { value: 3, label: 'İyi', emoji: '🙂', color: '#84CC16', description: 'Doğru ama zordu' },
  { value: 4, label: 'Kolay', emoji: '😊', color: '#22C55E', description: 'Kolayca hatırlandı' },
  { value: 5, label: 'Mükemmel', emoji: '🤩', color: '#8B5CF6', description: 'Çok kolay' }
];

// ==================== CARD COMPONENT ====================

const ReviewCard: React.FC<{
  item: ReviewItem;
  showAnswer: boolean;
  onFlip: () => void;
}> = ({ item, showAnswer, onFlip }) => {
  return (
    <motion.div
      className="w-full max-w-xl mx-auto perspective-1000"
      style={{ perspective: '1000px' }}
    >
      <motion.div
        className="relative w-full min-h-[300px] cursor-pointer"
        onClick={onFlip}
        animate={{ rotateY: showAnswer ? 180 : 0 }}
        transition={{ duration: 0.6, type: 'spring', stiffness: 100 }}
        style={{ transformStyle: 'preserve-3d' }}
      >
        {/* Front */}
        <div
          className={`absolute inset-0 rounded-2xl p-8 flex flex-col items-center justify-center
            bg-gradient-to-br from-purple-500 to-pink-500 text-white shadow-xl
            ${showAnswer ? 'backface-hidden' : ''}`}
          style={{ backfaceVisibility: 'hidden' }}
        >
          <div className="text-sm uppercase tracking-wide opacity-70 mb-4">
            {item.topic_id}
          </div>
          <div className="text-2xl font-bold text-center">
            {item.front || item.question || 'Soru yükleniyor...'}
          </div>
          <div className="mt-8 text-sm opacity-70 flex items-center gap-2">
            <RotateCcw className="w-4 h-4" />
            Cevabı görmek için tıkla
          </div>
        </div>
        
        {/* Back */}
        <div
          className="absolute inset-0 rounded-2xl p-8 flex flex-col items-center justify-center
            bg-gradient-to-br from-emerald-500 to-teal-500 text-white shadow-xl"
          style={{ backfaceVisibility: 'hidden', transform: 'rotateY(180deg)' }}
        >
          <div className="text-sm uppercase tracking-wide opacity-70 mb-4">
            Cevap
          </div>
          <div className="text-xl font-medium text-center">
            {item.back || item.answer || 'Cevap yükleniyor...'}
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};

// ==================== QUALITY SELECTOR ====================

const QualitySelector: React.FC<{
  onSelect: (quality: number) => void;
  disabled: boolean;
}> = ({ onSelect, disabled }) => {
  return (
    <div className="w-full max-w-xl mx-auto">
      <div className="text-center mb-4 text-gray-600 dark:text-gray-400">
        Hatırlamak ne kadar kolaydı?
      </div>
      <div className="grid grid-cols-6 gap-2">
        {QUALITY_OPTIONS.map((opt) => (
          <motion.button
            key={opt.value}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            disabled={disabled}
            onClick={() => onSelect(opt.value)}
            className="flex flex-col items-center p-3 rounded-xl border-2 transition-all
              hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
            style={{
              borderColor: opt.color,
              backgroundColor: `${opt.color}10`
            }}
          >
            <span className="text-2xl mb-1">{opt.emoji}</span>
            <span className="text-xs font-medium" style={{ color: opt.color }}>
              {opt.label}
            </span>
          </motion.button>
        ))}
      </div>
    </div>
  );
};

// ==================== PROGRESS BAR ====================

const SessionProgress: React.FC<{
  current: number;
  total: number;
  correct: number;
}> = ({ current, total, correct }) => {
  const percentage = (current / total) * 100;
  
  return (
    <div className="w-full max-w-xl mx-auto mb-6">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-gray-500">
          {current} / {total} kart
        </span>
        <span className="text-sm text-green-600 flex items-center gap-1">
          <CheckCircle className="w-4 h-4" />
          {correct} doğru
        </span>
      </div>
      <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <motion.div
          className="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.3 }}
        />
      </div>
    </div>
  );
};

// ==================== STATS SUMMARY ====================

const StatsSummary: React.FC<{
  stats: ReviewStats;
  onClose: () => void;
}> = ({ stats, onClose }) => {
  const accuracy = stats.total_reviewed > 0 
    ? (stats.correct / stats.total_reviewed) * 100 
    : 0;
  
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="w-full max-w-md mx-auto p-8 rounded-2xl bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/30 dark:to-pink-900/30 border border-purple-200 dark:border-purple-800"
    >
      <div className="text-center mb-6">
        <Trophy className="w-16 h-16 mx-auto text-amber-500 mb-4" />
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          Tekrar Tamamlandı!
        </h2>
      </div>
      
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="text-center p-4 bg-white dark:bg-gray-800 rounded-xl">
          <div className="text-3xl font-bold text-purple-600">{stats.total_reviewed}</div>
          <div className="text-sm text-gray-500">Kart</div>
        </div>
        <div className="text-center p-4 bg-white dark:bg-gray-800 rounded-xl">
          <div className="text-3xl font-bold text-green-600">{Math.round(accuracy)}%</div>
          <div className="text-sm text-gray-500">Doğruluk</div>
        </div>
        <div className="text-center p-4 bg-white dark:bg-gray-800 rounded-xl">
          <div className="text-3xl font-bold text-amber-600">{stats.xp_earned}</div>
          <div className="text-sm text-gray-500">XP</div>
        </div>
        <div className="text-center p-4 bg-white dark:bg-gray-800 rounded-xl">
          <div className="text-3xl font-bold text-blue-600">
            {Math.round(stats.time_spent_seconds / 60)}dk
          </div>
          <div className="text-sm text-gray-500">Süre</div>
        </div>
      </div>
      
      <button
        onClick={onClose}
        className="w-full py-3 px-6 rounded-xl bg-purple-600 hover:bg-purple-700 text-white font-semibold transition-colors"
      >
        Tamamla
      </button>
    </motion.div>
  );
};

// ==================== MAIN COMPONENT ====================

export const SpacedRepetitionReview: React.FC<ReviewSessionProps> = ({
  onComplete,
  onClose
}) => {
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showAnswer, setShowAnswer] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [sessionComplete, setSessionComplete] = useState(false);
  const [stats, setStats] = useState<ReviewStats>({
    total_reviewed: 0,
    correct: 0,
    incorrect: 0,
    average_quality: 0,
    xp_earned: 0,
    time_spent_seconds: 0
  });
  const [startTime] = useState(Date.now());
  const [qualities, setQualities] = useState<number[]>([]);
  
  // Fetch due items
  useEffect(() => {
    const fetchItems = async () => {
      try {
        const res = await fetch('/api/journey/v2/premium/reviews/due?max_items=20');
        if (res.ok) {
          const data = await res.json();
          setItems(data.items || []);
        }
      } catch (err) {
        console.error('Failed to fetch reviews:', err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchItems();
  }, []);
  
  const currentItem = items[currentIndex];
  
  const handleQualitySelect = async (quality: number) => {
    if (!currentItem || submitting) return;
    
    setSubmitting(true);
    
    try {
      // Submit review
      const res = await fetch(`/api/journey/v2/premium/reviews/${currentItem.id}/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ quality })
      });
      
      if (res.ok) {
        // Update stats
        const newQualities = [...qualities, quality];
        setQualities(newQualities);
        
        const newStats = {
          ...stats,
          total_reviewed: stats.total_reviewed + 1,
          correct: stats.correct + (quality >= 3 ? 1 : 0),
          incorrect: stats.incorrect + (quality < 3 ? 1 : 0),
          average_quality: newQualities.reduce((a, b) => a + b, 0) / newQualities.length,
          xp_earned: stats.xp_earned + (quality >= 3 ? 10 : 5),
          time_spent_seconds: Math.round((Date.now() - startTime) / 1000)
        };
        setStats(newStats);
        
        // Next card or complete
        if (currentIndex < items.length - 1) {
          setCurrentIndex(currentIndex + 1);
          setShowAnswer(false);
        } else {
          setSessionComplete(true);
          onComplete?.(newStats);
        }
      }
    } catch (err) {
      console.error('Failed to submit review:', err);
    } finally {
      setSubmitting(false);
    }
  };
  
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px]">
        <Brain className="w-12 h-12 text-purple-500 animate-pulse" />
        <p className="mt-4 text-gray-600 dark:text-gray-400">Tekrar kartları yükleniyor...</p>
      </div>
    );
  }
  
  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] text-center">
        <CheckCircle className="w-16 h-16 text-green-500 mb-4" />
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          Tebrikler!
        </h2>
        <p className="text-gray-600 dark:text-gray-400 mb-6">
          Bugün için tekrar edilecek kart yok.
        </p>
        <button
          onClick={onClose}
          className="px-6 py-3 rounded-xl bg-purple-600 hover:bg-purple-700 text-white font-semibold transition-colors"
        >
          Geri Dön
        </button>
      </div>
    );
  }
  
  if (sessionComplete) {
    return <StatsSummary stats={stats} onClose={() => onClose?.()} />;
  }
  
  return (
    <div className="w-full max-w-2xl mx-auto p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <button
          onClick={onClose}
          className="flex items-center gap-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
        >
          <ChevronLeft className="w-5 h-5" />
          Çık
        </button>
        <div className="flex items-center gap-2 text-purple-600">
          <Brain className="w-5 h-5" />
          <span className="font-medium">Aralıklı Tekrar</span>
        </div>
        <div className="flex items-center gap-2 text-amber-600">
          <Zap className="w-5 h-5" />
          <span className="font-medium">{stats.xp_earned} XP</span>
        </div>
      </div>
      
      {/* Progress */}
      <SessionProgress
        current={currentIndex + 1}
        total={items.length}
        correct={stats.correct}
      />
      
      {/* Card */}
      <div className="mb-8">
        <ReviewCard
          item={currentItem}
          showAnswer={showAnswer}
          onFlip={() => setShowAnswer(!showAnswer)}
        />
      </div>
      
      {/* Retention Info */}
      <div className="flex items-center justify-center gap-4 mb-6 text-sm text-gray-500">
        <span className="flex items-center gap-1">
          <Target className="w-4 h-4" />
          Hafıza: %{Math.round(currentItem.retention * 100)}
        </span>
        <span className="flex items-center gap-1">
          <Clock className="w-4 h-4" />
          Interval: {currentItem.interval} gün
        </span>
      </div>
      
      {/* Quality Selector (show only when answer is visible) */}
      <AnimatePresence>
        {showAnswer && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
          >
            <QualitySelector
              onSelect={handleQualitySelect}
              disabled={submitting}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default SpacedRepetitionReview;
