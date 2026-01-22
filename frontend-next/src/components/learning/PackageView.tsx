'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Package,
  Play,
  CheckCircle,
  Lock,
  Clock,
  Star,
  ChevronRight,
  BookOpen,
  Video,
  FileText,
  Sparkles,
  Trophy,
  AlertCircle,
  X,
  ChevronLeft
} from 'lucide-react';

// ==================== TYPES ====================

interface ContentBlock {
  id: string;
  type: 'text' | 'video' | 'interactive' | 'formula' | 'quiz';
  title: string;
  content: string;
  estimated_read_time: number;
  completed?: boolean;
}

interface Exercise {
  id: string;
  type: string;
  title: string;
  instructions: string;
  duration_minutes: number;
  xp_reward: number;
  completed?: boolean;
}

interface Exam {
  id: string;
  title: string;
  type: string;
  passing_score: number;
  time_limit_minutes?: number;
  attempts: number;
  max_attempts: number;
  best_score?: number;
}

interface PackageData {
  id: string;
  number: number;
  title: string;
  description: string;
  type: 'intro' | 'learning' | 'practice' | 'review' | 'exam' | 'closure';
  status: 'locked' | 'available' | 'in_progress' | 'completed';
  topics: string[];
  learning_objectives: string[];
  content_blocks: ContentBlock[];
  exercises: Exercise[];
  exams: Exam[];
  xp_reward: number;
  xp_earned?: number;
  estimated_duration_minutes: number;
  theme_color: string;
  icon: string;
}

interface PackageViewProps {
  package_data: PackageData;
  onComplete: () => void;
  onBack: () => void;
  onStartExam: (examId: string) => void;
}

// ==================== CONTENT TYPE ICONS ====================

const CONTENT_ICONS: Record<string, React.ReactNode> = {
  text: <FileText className="w-4 h-4" />,
  video: <Video className="w-4 h-4" />,
  interactive: <Sparkles className="w-4 h-4" />,
  formula: <span className="text-sm">∑</span>,
  quiz: <Trophy className="w-4 h-4" />,
};

const PACKAGE_TYPE_INFO: Record<string, { label: string; color: string; icon: string }> = {
  intro: { label: 'Giriş', color: '#6366F1', icon: '🎯' },
  learning: { label: 'Öğrenme', color: '#3B82F6', icon: '📚' },
  practice: { label: 'Pratik', color: '#F59E0B', icon: '✏️' },
  review: { label: 'Tekrar', color: '#8B5CF6', icon: '🔄' },
  exam: { label: 'Sınav', color: '#EF4444', icon: '📝' },
  closure: { label: 'Final', color: '#10B981', icon: '🏆' },
};

// ==================== CONTENT BLOCK COMPONENT ====================

const ContentBlockCard: React.FC<{
  block: ContentBlock;
  isExpanded: boolean;
  onToggle: () => void;
  onComplete: () => void;
}> = ({ block, isExpanded, onToggle, onComplete }) => {
  return (
    <motion.div
      layout
      className={`rounded-xl border-2 overflow-hidden transition-all ${
        block.completed
          ? 'border-green-500 bg-green-50 dark:bg-green-900/20'
          : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800'
      }`}
    >
      {/* Header */}
      <button
        onClick={onToggle}
        className="w-full p-4 flex items-center gap-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
      >
        <div className={`p-2 rounded-lg ${
          block.completed ? 'bg-green-500 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
        }`}>
          {block.completed ? <CheckCircle className="w-4 h-4" /> : CONTENT_ICONS[block.type]}
        </div>
        
        <div className="flex-1 min-w-0">
          <h4 className="font-medium text-gray-900 dark:text-white truncate">
            {block.title}
          </h4>
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <Clock className="w-3 h-3" />
            <span>{block.estimated_read_time} dk</span>
          </div>
        </div>
        
        <ChevronRight className={`w-5 h-5 text-gray-400 transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
      </button>
      
      {/* Content */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t border-gray-200 dark:border-gray-700"
          >
            <div className="p-4">
              {/* Markdown content */}
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <div dangerouslySetInnerHTML={{ __html: block.content.replace(/\n/g, '<br/>') }} />
              </div>
              
              {!block.completed && (
                <button
                  onClick={onComplete}
                  className="mt-4 w-full py-2 bg-gradient-to-r from-green-500 to-emerald-600 text-white font-semibold
                             rounded-lg hover:shadow-lg transition-all flex items-center justify-center gap-2"
                >
                  <CheckCircle className="w-4 h-4" />
                  Tamamlandı
                </button>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

// ==================== EXERCISE CARD ====================

const ExerciseCard: React.FC<{
  exercise: Exercise;
  onStart: () => void;
}> = ({ exercise, onStart }) => {
  return (
    <div className={`p-4 rounded-xl border-2 ${
      exercise.completed
        ? 'border-green-500 bg-green-50 dark:bg-green-900/20'
        : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800'
    }`}>
      <div className="flex items-start gap-3">
        <div className={`p-2 rounded-lg ${
          exercise.completed ? 'bg-green-500 text-white' : 'bg-amber-100 dark:bg-amber-900/30 text-amber-600'
        }`}>
          {exercise.completed ? <CheckCircle className="w-5 h-5" /> : <Sparkles className="w-5 h-5" />}
        </div>
        
        <div className="flex-1">
          <h4 className="font-medium text-gray-900 dark:text-white">{exercise.title}</h4>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{exercise.instructions}</p>
          
          <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {exercise.duration_minutes} dk
            </span>
            <span className="flex items-center gap-1">
              <Star className="w-3 h-3 text-amber-500" />
              +{exercise.xp_reward} XP
            </span>
          </div>
        </div>
        
        {!exercise.completed && (
          <button
            onClick={onStart}
            className="px-4 py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600 transition-colors"
          >
            Başla
          </button>
        )}
      </div>
    </div>
  );
};

// ==================== EXAM CARD ====================

const ExamCard: React.FC<{
  exam: Exam;
  onStart: () => void;
}> = ({ exam, onStart }) => {
  const passed = exam.best_score && exam.best_score >= exam.passing_score;
  
  return (
    <div className={`p-4 rounded-xl border-2 ${
      passed
        ? 'border-green-500 bg-green-50 dark:bg-green-900/20'
        : 'border-purple-200 dark:border-purple-700 bg-purple-50 dark:bg-purple-900/20'
    }`}>
      <div className="flex items-start gap-3">
        <div className={`p-2 rounded-lg ${
          passed ? 'bg-green-500 text-white' : 'bg-purple-500 text-white'
        }`}>
          {passed ? <CheckCircle className="w-5 h-5" /> : <Trophy className="w-5 h-5" />}
        </div>
        
        <div className="flex-1">
          <h4 className="font-medium text-gray-900 dark:text-white">{exam.title}</h4>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Tür: {exam.type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
          </p>
          
          <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
            {exam.time_limit_minutes && (
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {exam.time_limit_minutes} dk
              </span>
            )}
            <span>Geçme: %{exam.passing_score}</span>
            <span>Deneme: {exam.attempts}/{exam.max_attempts}</span>
          </div>
          
          {exam.best_score !== undefined && (
            <div className="mt-2 flex items-center gap-2">
              <span className="text-sm">En iyi skor:</span>
              <span className={`font-bold ${passed ? 'text-green-600' : 'text-red-600'}`}>
                %{exam.best_score}
              </span>
            </div>
          )}
        </div>
        
        {(!passed && exam.attempts < exam.max_attempts) && (
          <button
            onClick={onStart}
            className="px-4 py-2 bg-gradient-to-r from-purple-500 to-indigo-600 text-white rounded-lg 
                       hover:shadow-lg transition-all"
          >
            {exam.attempts > 0 ? 'Tekrar Dene' : 'Başla'}
          </button>
        )}
      </div>
    </div>
  );
};

// ==================== MAIN PACKAGE VIEW ====================

const PackageView: React.FC<PackageViewProps> = ({
  package_data,
  onComplete,
  onBack,
  onStartExam
}) => {
  const [expandedBlock, setExpandedBlock] = useState<string | null>(null);
  const [completedBlocks, setCompletedBlocks] = useState<Set<string>>(new Set());
  
  const typeInfo = PACKAGE_TYPE_INFO[package_data.type] || PACKAGE_TYPE_INFO.learning;
  
  const allBlocksCompleted = package_data.content_blocks.every(
    b => completedBlocks.has(b.id) || b.completed
  );
  
  const allExamsPassed = package_data.exams.every(
    e => e.best_score && e.best_score >= e.passing_score
  );
  
  const canComplete = allBlocksCompleted && (package_data.exams.length === 0 || allExamsPassed);
  
  const handleBlockComplete = (blockId: string) => {
    setCompletedBlocks(prev => new Set([...prev, blockId]));
    setExpandedBlock(null);
  };
  
  const progress = () => {
    const totalItems = package_data.content_blocks.length + package_data.exams.length;
    const completedItems = completedBlocks.size + 
      package_data.exams.filter(e => e.best_score && e.best_score >= e.passing_score).length;
    return totalItems > 0 ? Math.round((completedItems / totalItems) * 100) : 0;
  };
  
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div 
        className="sticky top-0 z-10 p-4 border-b border-gray-200 dark:border-gray-700"
        style={{ backgroundColor: `${typeInfo.color}15` }}
      >
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center gap-4 mb-4">
            <button
              onClick={onBack}
              className="p-2 hover:bg-white/50 dark:hover:bg-gray-800/50 rounded-lg transition-colors"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className="text-2xl">{package_data.icon}</span>
                <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                  {package_data.title}
                </h1>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                {package_data.description}
              </p>
            </div>
            
            <div className="text-right">
              <div className="flex items-center gap-1 text-amber-500">
                <Star className="w-4 h-4" />
                <span className="font-bold">{package_data.xp_reward} XP</span>
              </div>
              <div className="text-xs text-gray-500">
                {package_data.estimated_duration_minutes} dk
              </div>
            </div>
          </div>
          
          {/* Progress Bar */}
          <div className="flex items-center gap-3">
            <div className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <motion.div
                className="h-full rounded-full"
                style={{ backgroundColor: typeInfo.color }}
                initial={{ width: 0 }}
                animate={{ width: `${progress()}%` }}
              />
            </div>
            <span className="text-sm font-medium" style={{ color: typeInfo.color }}>
              {progress()}%
            </span>
          </div>
        </div>
      </div>
      
      {/* Content */}
      <div className="max-w-4xl mx-auto p-4 space-y-8">
        {/* Learning Objectives */}
        {package_data.learning_objectives.length > 0 && (
          <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl border border-blue-200 dark:border-blue-800">
            <h3 className="font-semibold text-blue-800 dark:text-blue-300 mb-2">
              🎯 Öğrenme Hedefleri
            </h3>
            <ul className="space-y-1">
              {package_data.learning_objectives.map((obj, i) => (
                <li key={i} className="text-sm text-blue-700 dark:text-blue-400 flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  {obj}
                </li>
              ))}
            </ul>
          </div>
        )}
        
        {/* Content Blocks */}
        {package_data.content_blocks.length > 0 && (
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <BookOpen className="w-5 h-5" />
              İçerikler
            </h3>
            <div className="space-y-3">
              {package_data.content_blocks.map(block => (
                <ContentBlockCard
                  key={block.id}
                  block={{ ...block, completed: completedBlocks.has(block.id) || block.completed }}
                  isExpanded={expandedBlock === block.id}
                  onToggle={() => setExpandedBlock(expandedBlock === block.id ? null : block.id)}
                  onComplete={() => handleBlockComplete(block.id)}
                />
              ))}
            </div>
          </div>
        )}
        
        {/* Exercises */}
        {package_data.exercises.length > 0 && (
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-amber-500" />
              Egzersizler
            </h3>
            <div className="space-y-3">
              {package_data.exercises.map(exercise => (
                <ExerciseCard
                  key={exercise.id}
                  exercise={exercise}
                  onStart={() => {}}
                />
              ))}
            </div>
          </div>
        )}
        
        {/* Exams */}
        {package_data.exams.length > 0 && (
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <Trophy className="w-5 h-5 text-purple-500" />
              Sınavlar
            </h3>
            <div className="space-y-3">
              {package_data.exams.map(exam => (
                <ExamCard
                  key={exam.id}
                  exam={exam}
                  onStart={() => onStartExam(exam.id)}
                />
              ))}
            </div>
          </div>
        )}
        
        {/* Complete Button */}
        <div className="pt-6 pb-12">
          {canComplete ? (
            <button
              onClick={onComplete}
              className="w-full py-4 bg-gradient-to-r from-green-500 to-emerald-600 text-white font-bold text-lg
                         rounded-xl hover:shadow-lg hover:shadow-green-500/30 transition-all flex items-center justify-center gap-3"
            >
              <CheckCircle className="w-6 h-6" />
              Paketi Tamamla (+{package_data.xp_reward} XP)
            </button>
          ) : (
            <div className="p-4 bg-amber-50 dark:bg-amber-900/20 rounded-xl border border-amber-200 dark:border-amber-800
                            flex items-center gap-3">
              <AlertCircle className="w-6 h-6 text-amber-500 flex-shrink-0" />
              <div>
                <div className="font-medium text-amber-800 dark:text-amber-300">
                  Paketi tamamlamak için:
                </div>
                <div className="text-sm text-amber-700 dark:text-amber-400">
                  {!allBlocksCompleted && '• Tüm içerikleri oku '}
                  {package_data.exams.length > 0 && !allExamsPassed && '• Sınavlardan geçme puanı al'}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PackageView;
