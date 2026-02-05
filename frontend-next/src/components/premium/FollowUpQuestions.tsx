'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MessageSquarePlus,
  Sparkles,
  ChevronRight,
  Lightbulb,
  Search,
  HelpCircle,
  Zap,
  RefreshCw
} from 'lucide-react';

// ============ TYPES ============

export interface FollowUpQuestion {
  text: string;
  category?: 'explore' | 'clarify' | 'compare' | 'example' | 'deep-dive';
  relevance?: number;
  icon?: React.ReactNode;
}

interface FollowUpQuestionsProps {
  questions: FollowUpQuestion[];
  onSelect: (question: string) => void;
  variant?: 'inline' | 'pills' | 'cards' | 'floating';
  title?: string;
  maxVisible?: number;
  isLoading?: boolean;
  onRefresh?: () => void;
}

// ============ HELPER FUNCTIONS ============

const getCategoryIcon = (category: string | undefined) => {
  switch (category) {
    case 'explore':
      return <Search className="w-3.5 h-3.5" />;
    case 'clarify':
      return <HelpCircle className="w-3.5 h-3.5" />;
    case 'compare':
      return <Zap className="w-3.5 h-3.5" />;
    case 'example':
      return <Lightbulb className="w-3.5 h-3.5" />;
    case 'deep-dive':
      return <Sparkles className="w-3.5 h-3.5" />;
    default:
      return <MessageSquarePlus className="w-3.5 h-3.5" />;
  }
};

const getCategoryColor = (category: string | undefined) => {
  switch (category) {
    case 'explore':
      return 'from-blue-500/20 to-blue-600/10 border-blue-500/20 hover:border-blue-500/40 text-blue-400';
    case 'clarify':
      return 'from-purple-500/20 to-purple-600/10 border-purple-500/20 hover:border-purple-500/40 text-purple-400';
    case 'compare':
      return 'from-amber-500/20 to-amber-600/10 border-amber-500/20 hover:border-amber-500/40 text-amber-400';
    case 'example':
      return 'from-green-500/20 to-green-600/10 border-green-500/20 hover:border-green-500/40 text-green-400';
    case 'deep-dive':
      return 'from-pink-500/20 to-pink-600/10 border-pink-500/20 hover:border-pink-500/40 text-pink-400';
    default:
      return 'from-white/10 to-white/5 border-white/10 hover:border-white/20 text-white/80';
  }
};

// ============ PILL VARIANT ============

const PillQuestion: React.FC<{
  question: FollowUpQuestion;
  index: number;
  onSelect: () => void;
}> = ({ question, index, onSelect }) => (
  <motion.button
    initial={{ opacity: 0, scale: 0.9, y: 10 }}
    animate={{ opacity: 1, scale: 1, y: 0 }}
    exit={{ opacity: 0, scale: 0.9 }}
    transition={{ delay: index * 0.05, type: 'spring', stiffness: 200 }}
    whileHover={{ scale: 1.02 }}
    whileTap={{ scale: 0.98 }}
    onClick={onSelect}
    className={`inline-flex items-center gap-2 px-3 py-2 rounded-full text-sm
                bg-gradient-to-r ${getCategoryColor(question.category)} 
                border backdrop-blur-sm transition-all cursor-pointer group`}
  >
    <span className="opacity-70 group-hover:opacity-100 transition-opacity">
      {question.icon || getCategoryIcon(question.category)}
    </span>
    <span className="text-white/90">{question.text}</span>
    <ChevronRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
  </motion.button>
);

// ============ CARD VARIANT ============

const CardQuestion: React.FC<{
  question: FollowUpQuestion;
  index: number;
  onSelect: () => void;
}> = ({ question, index, onSelect }) => (
  <motion.button
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -10 }}
    transition={{ delay: index * 0.08, type: 'spring', stiffness: 100 }}
    whileHover={{ y: -2 }}
    whileTap={{ scale: 0.98 }}
    onClick={onSelect}
    className="group relative p-4 rounded-xl text-left overflow-hidden
               bg-gradient-to-br from-white/[0.05] to-transparent
               border border-white/10 hover:border-white/20 transition-all"
  >
    {/* Background glow */}
    <div className={`absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity
                     bg-gradient-to-br ${getCategoryColor(question.category)}`} 
         style={{ opacity: 0.1 }} />
    
    {/* Content */}
    <div className="relative flex items-start gap-3">
      <div className={`flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center
                       bg-gradient-to-br ${getCategoryColor(question.category)}`}>
        {question.icon || getCategoryIcon(question.category)}
      </div>
      
      <div className="flex-1 min-w-0">
        <p className="text-sm text-white/90 group-hover:text-white transition-colors">
          {question.text}
        </p>
        {question.category && (
          <span className="inline-block mt-1.5 text-xs text-white/40 capitalize">
            {question.category.replace('-', ' ')}
          </span>
        )}
      </div>
      
      <ChevronRight className="w-4 h-4 text-white/30 group-hover:text-white/60 
                               group-hover:translate-x-1 transition-all" />
    </div>
  </motion.button>
);

// ============ INLINE VARIANT ============

const InlineQuestion: React.FC<{
  question: FollowUpQuestion;
  index: number;
  onSelect: () => void;
}> = ({ question, index, onSelect }) => (
  <motion.button
    initial={{ opacity: 0, x: -10 }}
    animate={{ opacity: 1, x: 0 }}
    exit={{ opacity: 0, x: 10 }}
    transition={{ delay: index * 0.05 }}
    onClick={onSelect}
    className="group flex items-center gap-2 w-full p-2 rounded-lg
               hover:bg-white/[0.05] transition-colors text-left"
  >
    <div className={`flex-shrink-0 w-6 h-6 rounded-md flex items-center justify-center
                     ${getCategoryColor(question.category)}`}>
      {question.icon || getCategoryIcon(question.category)}
    </div>
    <span className="flex-1 text-sm text-white/70 group-hover:text-white/90 transition-colors truncate">
      {question.text}
    </span>
    <ChevronRight className="w-4 h-4 text-white/20 group-hover:text-white/50 transition-colors" />
  </motion.button>
);

// ============ FLOATING VARIANT ============

const FloatingQuestion: React.FC<{
  question: FollowUpQuestion;
  index: number;
  total: number;
  onSelect: () => void;
}> = ({ question, index, total, onSelect }) => {
  // Calculate position for floating animation
  const angle = (index / total) * Math.PI - Math.PI / 2;
  const radius = 30;
  
  return (
    <motion.button
      initial={{ 
        opacity: 0, 
        scale: 0,
        x: Math.cos(angle) * radius,
        y: Math.sin(angle) * radius 
      }}
      animate={{ 
        opacity: 1, 
        scale: 1,
        x: 0,
        y: 0
      }}
      exit={{ opacity: 0, scale: 0 }}
      transition={{ 
        delay: index * 0.1, 
        type: 'spring', 
        stiffness: 150,
        damping: 15
      }}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={onSelect}
      className={`relative px-4 py-2.5 rounded-2xl text-sm font-medium
                  bg-gradient-to-r ${getCategoryColor(question.category)}
                  border backdrop-blur-md shadow-lg
                  hover:shadow-xl transition-shadow`}
    >
      <span className="flex items-center gap-2">
        <Sparkles className="w-4 h-4 animate-pulse" />
        {question.text}
      </span>
    </motion.button>
  );
};

// ============ LOADING SKELETON ============

const LoadingSkeleton: React.FC<{ variant: string }> = ({ variant }) => {
  const skeletonClass = "animate-pulse bg-white/10 rounded-full";
  
  if (variant === 'pills') {
    return (
      <div className="flex flex-wrap gap-2">
        {[1, 2, 3].map((i) => (
          <div key={i} className={`${skeletonClass} h-10 w-40`} />
        ))}
      </div>
    );
  }
  
  if (variant === 'cards') {
    return (
      <div className="grid gap-3 sm:grid-cols-2">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="animate-pulse rounded-xl bg-white/5 border border-white/10 p-4">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg bg-white/10" />
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-white/10 rounded w-3/4" />
                <div className="h-3 bg-white/10 rounded w-1/4" />
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }
  
  return (
    <div className="space-y-2">
      {[1, 2, 3].map((i) => (
        <div key={i} className={`${skeletonClass} h-10 w-full max-w-md`} />
      ))}
    </div>
  );
};

// ============ MAIN COMPONENT ============

export const FollowUpQuestions: React.FC<FollowUpQuestionsProps> = ({
  questions,
  onSelect,
  variant = 'pills',
  title = 'Devam Soruları',
  maxVisible = 4,
  isLoading = false,
  onRefresh,
}) => {
  const [showAll, setShowAll] = useState(false);
  
  const visibleQuestions = showAll ? questions : questions.slice(0, maxVisible);
  const hasMore = questions.length > maxVisible;
  
  if (isLoading) {
    return (
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <div className="animate-spin">
            <Sparkles className="w-4 h-4 text-blue-400" />
          </div>
          <span className="text-sm text-white/50">Sorular oluşturuluyor...</span>
        </div>
        <LoadingSkeleton variant={variant} />
      </div>
    );
  }
  
  if (questions.length === 0) {
    return null;
  }
  
  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-blue-400" />
          <h3 className="text-sm font-semibold text-white/80">{title}</h3>
          <span className="px-1.5 py-0.5 rounded-md bg-white/10 text-xs text-white/50">
            {questions.length}
          </span>
        </div>
        
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="p-1.5 rounded-lg hover:bg-white/10 transition-colors group"
            title="Yeni sorular oluştur"
          >
            <RefreshCw className="w-4 h-4 text-white/40 group-hover:text-white/70 
                                  group-hover:rotate-180 transition-all duration-300" />
          </button>
        )}
      </div>
      
      {/* Questions */}
      <AnimatePresence mode="popLayout">
        {variant === 'pills' && (
          <div className="flex flex-wrap gap-2">
            {visibleQuestions.map((q, i) => (
              <PillQuestion
                key={`${q.text}-${i}`}
                question={q}
                index={i}
                onSelect={() => onSelect(q.text)}
              />
            ))}
          </div>
        )}
        
        {variant === 'cards' && (
          <div className="grid gap-3 sm:grid-cols-2">
            {visibleQuestions.map((q, i) => (
              <CardQuestion
                key={`${q.text}-${i}`}
                question={q}
                index={i}
                onSelect={() => onSelect(q.text)}
              />
            ))}
          </div>
        )}
        
        {variant === 'inline' && (
          <div className="space-y-1">
            {visibleQuestions.map((q, i) => (
              <InlineQuestion
                key={`${q.text}-${i}`}
                question={q}
                index={i}
                onSelect={() => onSelect(q.text)}
              />
            ))}
          </div>
        )}
        
        {variant === 'floating' && (
          <div className="flex flex-wrap items-center justify-center gap-3 py-4">
            {visibleQuestions.map((q, i) => (
              <FloatingQuestion
                key={`${q.text}-${i}`}
                question={q}
                index={i}
                total={visibleQuestions.length}
                onSelect={() => onSelect(q.text)}
              />
            ))}
          </div>
        )}
      </AnimatePresence>
      
      {/* Show More */}
      {hasMore && (
        <motion.button
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          onClick={() => setShowAll(!showAll)}
          className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
        >
          {showAll ? 'Daha az göster' : `+${questions.length - maxVisible} soru daha`}
        </motion.button>
      )}
    </div>
  );
};

export default FollowUpQuestions;
