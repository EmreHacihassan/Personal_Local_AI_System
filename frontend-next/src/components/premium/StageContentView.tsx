'use client';

/**
 * 🎓 StageContentView - Stage İçerik Görüntüleyici
 * 
 * Stage'deki tüm içerikleri (ders, formül, video, alıştırma, quiz) gösterir.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Book,
  FileText,
  Video,
  PenTool,
  ClipboardCheck,
  ChevronLeft,
  ChevronRight,
  CheckCircle,
  Star,
  Zap,
  Play,
  Clock,
  ArrowLeft,
  Lightbulb,
  Calculator,
  X,
  Send,
  RefreshCw
} from 'lucide-react';

// Types
interface ContentItem {
  id: string;
  type: 'lesson' | 'formula' | 'video' | 'practice' | 'quiz' | 'challenge';
  title: string;
  description: string;
  content: any;
  duration_minutes: number;
  xp_reward: number;
  is_completed: boolean;
  completion_date: string | null;
  source: string;
}

interface StageData {
  id: string;
  number: number;
  title: string;
  topic: string;
  subtopics: string[];
  difficulty: string;
  contents: ContentItem[];
  status: string;
  stars: number;
  xp_total: number;
  xp_earned: number;
}

interface StageContentViewProps {
  userId: string;
  stageId: string;
  onBack: () => void;
  onComplete?: (stageId: string) => void;
  language?: 'tr' | 'en' | 'de';
}

const translations = {
  tr: {
    loading: 'Yükleniyor...',
    lesson: 'Konu Anlatımı',
    formula: 'Formüller',
    video: 'Video Ders',
    practice: 'Alıştırma',
    quiz: 'Mini Sınav',
    challenge: 'Challenge',
    complete: 'Tamamla',
    completed: 'Tamamlandı',
    next: 'Sonraki',
    previous: 'Önceki',
    back: 'Geri',
    xp: 'XP',
    minutes: 'dakika',
    progress: 'İlerleme',
    stage: 'Aşama',
    congratulations: 'Tebrikler!',
    stageComplete: 'Aşamayı tamamladın!',
    earnedXP: 'Kazanılan XP',
    earnedStars: 'Kazanılan Yıldız',
    continue: 'Devam Et',
    hint: 'İpucu',
    submit: 'Gönder',
    correct: 'Doğru!',
    incorrect: 'Yanlış',
    tryAgain: 'Tekrar Dene',
    yourAnswer: 'Cevabın',
    correctAnswer: 'Doğru Cevap',
    explanation: 'Açıklama',
    summary: 'Özet',
    keyPoints: 'Önemli Noktalar',
    examples: 'Örnekler'
  },
  en: {
    loading: 'Loading...',
    lesson: 'Lesson',
    formula: 'Formulas',
    video: 'Video Lesson',
    practice: 'Practice',
    quiz: 'Mini Quiz',
    challenge: 'Challenge',
    complete: 'Complete',
    completed: 'Completed',
    next: 'Next',
    previous: 'Previous',
    back: 'Back',
    xp: 'XP',
    minutes: 'minutes',
    progress: 'Progress',
    stage: 'Stage',
    congratulations: 'Congratulations!',
    stageComplete: 'You completed the stage!',
    earnedXP: 'Earned XP',
    earnedStars: 'Earned Stars',
    continue: 'Continue',
    hint: 'Hint',
    submit: 'Submit',
    correct: 'Correct!',
    incorrect: 'Incorrect',
    tryAgain: 'Try Again',
    yourAnswer: 'Your Answer',
    correctAnswer: 'Correct Answer',
    explanation: 'Explanation',
    summary: 'Summary',
    keyPoints: 'Key Points',
    examples: 'Examples'
  },
  de: {
    loading: 'Laden...',
    lesson: 'Lektion',
    formula: 'Formeln',
    video: 'Videolektion',
    practice: 'Übung',
    quiz: 'Mini-Quiz',
    challenge: 'Herausforderung',
    complete: 'Abschließen',
    completed: 'Abgeschlossen',
    next: 'Weiter',
    previous: 'Zurück',
    back: 'Zurück',
    xp: 'XP',
    minutes: 'Minuten',
    progress: 'Fortschritt',
    stage: 'Stufe',
    congratulations: 'Gratulation!',
    stageComplete: 'Du hast die Stufe abgeschlossen!',
    earnedXP: 'Verdiente XP',
    earnedStars: 'Verdiente Sterne',
    continue: 'Weiter',
    hint: 'Hinweis',
    submit: 'Absenden',
    correct: 'Richtig!',
    incorrect: 'Falsch',
    tryAgain: 'Nochmal versuchen',
    yourAnswer: 'Deine Antwort',
    correctAnswer: 'Richtige Antwort',
    explanation: 'Erklärung',
    summary: 'Zusammenfassung',
    keyPoints: 'Wichtige Punkte',
    examples: 'Beispiele'
  }
};

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

// Content Type Icons
const getContentIcon = (type: string) => {
  switch (type) {
    case 'lesson': return Book;
    case 'formula': return Calculator;
    case 'video': return Video;
    case 'practice': return PenTool;
    case 'quiz': return ClipboardCheck;
    case 'challenge': return Zap;
    default: return Book;
  }
};

// Lesson Content Component
const LessonContent: React.FC<{
  content: any;
  t: typeof translations.tr;
}> = ({ content, t }) => {
  const [activeSection, setActiveSection] = useState(0);
  
  const sections = content.sections || [];
  
  return (
    <div className="space-y-6">
      {/* Section Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {sections.map((section: any, idx: number) => (
          <button
            key={idx}
            onClick={() => setActiveSection(idx)}
            className={`px-4 py-2 rounded-lg whitespace-nowrap transition-all ${
              activeSection === idx
                ? 'bg-purple-600 text-white'
                : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
            }`}
          >
            {section.title}
          </button>
        ))}
      </div>
      
      {/* Active Section Content */}
      {sections[activeSection] && (
        <motion.div
          key={activeSection}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gray-800/50 rounded-xl p-6"
        >
          <h3 className="text-xl font-bold mb-4">{sections[activeSection].title}</h3>
          <p className="text-gray-300 mb-4">{sections[activeSection].text}</p>
          
          {/* Key Points */}
          {sections[activeSection].key_points && (
            <div className="mt-4">
              <h4 className="font-semibold mb-2 flex items-center gap-2">
                <Lightbulb size={18} className="text-yellow-400" />
                {t.keyPoints}
              </h4>
              <ul className="space-y-2">
                {sections[activeSection].key_points.map((point: string, idx: number) => (
                  <li key={idx} className="flex items-start gap-2 text-gray-300">
                    <CheckCircle size={16} className="text-green-400 mt-1 flex-shrink-0" />
                    {point}
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {/* Examples */}
          {sections[activeSection].problems && (
            <div className="mt-6 space-y-4">
              <h4 className="font-semibold flex items-center gap-2">
                <PenTool size={18} className="text-blue-400" />
                {t.examples}
              </h4>
              {sections[activeSection].problems.map((problem: any, idx: number) => (
                <div key={idx} className="bg-gray-900/50 rounded-lg p-4">
                  <p className="font-medium mb-2">{problem.question}</p>
                  <div className="text-sm text-gray-400 border-l-2 border-purple-500 pl-3 mt-2">
                    {problem.solution}
                  </div>
                  <div className="mt-2 text-green-400 font-semibold">
                    Cevap: {problem.answer}
                  </div>
                </div>
              ))}
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
};

// Formula Content Component
const FormulaContent: React.FC<{
  content: any;
  t: typeof translations.tr;
}> = ({ content, t }) => {
  const formulas = content.formulas || [];
  
  return (
    <div className="space-y-6">
      {formulas.map((formula: any, idx: number) => (
        <motion.div
          key={idx}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: idx * 0.1 }}
          className="bg-gradient-to-r from-purple-900/50 to-blue-900/50 rounded-xl p-6 border border-purple-500/30"
        >
          <h3 className="text-lg font-bold mb-3 text-purple-300">{formula.name}</h3>
          
          {/* Formula Display */}
          <div className="bg-black/30 rounded-lg p-4 text-center text-2xl font-mono text-white mb-4">
            {formula.latex}
          </div>
          
          {/* Description */}
          <p className="text-gray-300 mb-4">{formula.description}</p>
          
          {/* Variables */}
          {formula.variables && (
            <div className="bg-gray-900/50 rounded-lg p-4">
              <h4 className="font-semibold mb-2 text-sm text-gray-400">Değişkenler:</h4>
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(formula.variables).map(([key, value]) => (
                  <div key={key} className="flex items-center gap-2">
                    <span className="font-mono text-purple-400">{key}</span>
                    <span className="text-gray-400">→</span>
                    <span className="text-gray-300">{value as string}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </motion.div>
      ))}
      
      {/* Cheat Sheet */}
      {content.cheat_sheet && (
        <div className="bg-yellow-500/10 rounded-xl p-6 border border-yellow-500/30">
          <h3 className="font-bold mb-4 flex items-center gap-2 text-yellow-400">
            <Lightbulb size={20} />
            Hızlı Referans
          </h3>
          {content.cheat_sheet.tips?.length > 0 && (
            <ul className="space-y-2">
              {content.cheat_sheet.tips.map((tip: string, idx: number) => (
                <li key={idx} className="text-gray-300 flex items-start gap-2">
                  <Star size={14} className="text-yellow-400 mt-1" />
                  {tip}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
};

// Video Content Component
const VideoContent: React.FC<{
  content: any;
  t: typeof translations.tr;
}> = ({ content, t }) => {
  const videos = content.videos || [];
  
  return (
    <div className="space-y-6">
      {videos.map((video: any, idx: number) => (
        <div key={idx} className="bg-gray-800/50 rounded-xl overflow-hidden">
          {/* Video Placeholder */}
          <div className="aspect-video bg-gradient-to-br from-gray-900 to-gray-800 flex items-center justify-center">
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              className="w-20 h-20 bg-red-600 rounded-full flex items-center justify-center"
            >
              <Play size={32} className="text-white ml-1" />
            </motion.button>
          </div>
          
          {/* Video Info */}
          <div className="p-4">
            <h3 className="font-bold text-lg mb-2">{video.title}</h3>
            <div className="flex items-center gap-4 text-sm text-gray-400">
              <span className="flex items-center gap-1">
                <Clock size={14} />
                {video.duration}
              </span>
              <span>{video.source}</span>
            </div>
            
            {/* Chapters */}
            {video.chapters && video.chapters.length > 0 && (
              <div className="mt-4 space-y-2">
                <h4 className="font-semibold text-sm text-gray-400">Bölümler:</h4>
                {video.chapters.map((chapter: any, cIdx: number) => (
                  <button
                    key={cIdx}
                    className="w-full flex items-center gap-3 p-2 rounded-lg bg-gray-900/50 hover:bg-gray-900 transition-colors text-left"
                  >
                    <span className="text-xs text-purple-400 font-mono">{chapter.time}</span>
                    <span className="text-sm">{chapter.title}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

// Practice/Quiz Content Component
const QuizContent: React.FC<{
  content: any;
  onComplete: (score: number) => void;
  t: typeof translations.tr;
}> = ({ content, onComplete, t }) => {
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [showResult, setShowResult] = useState(false);
  const [score, setScore] = useState(0);
  const [answeredQuestions, setAnsweredQuestions] = useState<number[]>([]);
  
  const questions = content.questions || [];
  const question = questions[currentQuestion];
  
  const handleSubmit = () => {
    if (!selectedAnswer || !question) return;
    
    const isCorrect = selectedAnswer === question.correct_answer;
    if (isCorrect) {
      setScore(prev => prev + (question.points || 10));
    }
    
    setShowResult(true);
    setAnsweredQuestions(prev => [...prev, currentQuestion]);
  };
  
  const handleNext = () => {
    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(prev => prev + 1);
      setSelectedAnswer(null);
      setShowResult(false);
    } else {
      // Quiz complete
      const finalScore = (score / (questions.length * 20)) * 100;
      onComplete(finalScore);
    }
  };
  
  if (!question) {
    return <div className="text-center py-8">{t.loading}</div>;
  }
  
  return (
    <div className="space-y-6">
      {/* Progress Bar */}
      <div className="flex items-center gap-4">
        <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-purple-500 to-pink-500"
            initial={{ width: 0 }}
            animate={{ width: `${((currentQuestion + 1) / questions.length) * 100}%` }}
          />
        </div>
        <span className="text-sm text-gray-400">
          {currentQuestion + 1}/{questions.length}
        </span>
      </div>
      
      {/* Question */}
      <motion.div
        key={currentQuestion}
        initial={{ opacity: 0, x: 50 }}
        animate={{ opacity: 1, x: 0 }}
        className="bg-gray-800/50 rounded-xl p-6"
      >
        <h3 className="text-lg font-medium mb-6">{question.question}</h3>
        
        {/* Options */}
        {question.options && (
          <div className="space-y-3">
            {question.options.map((option: string, idx: number) => (
              <button
                key={idx}
                onClick={() => !showResult && setSelectedAnswer(option)}
                disabled={showResult}
                className={`w-full p-4 rounded-lg text-left transition-all ${
                  showResult
                    ? option === question.correct_answer
                      ? 'bg-green-500/20 border-2 border-green-500'
                      : option === selectedAnswer
                        ? 'bg-red-500/20 border-2 border-red-500'
                        : 'bg-gray-800 border-2 border-transparent'
                    : selectedAnswer === option
                      ? 'bg-purple-500/20 border-2 border-purple-500'
                      : 'bg-gray-800 border-2 border-transparent hover:bg-gray-700'
                }`}
              >
                <span className="font-medium">{option}</span>
              </button>
            ))}
          </div>
        )}
        
        {/* Result Feedback */}
        {showResult && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`mt-4 p-4 rounded-lg ${
              selectedAnswer === question.correct_answer
                ? 'bg-green-500/20 border border-green-500'
                : 'bg-red-500/20 border border-red-500'
            }`}
          >
            <div className="flex items-center gap-2 font-bold">
              {selectedAnswer === question.correct_answer ? (
                <>
                  <CheckCircle className="text-green-400" />
                  {t.correct}
                </>
              ) : (
                <>
                  <X className="text-red-400" />
                  {t.incorrect}
                </>
              )}
            </div>
            {question.explanation && (
              <p className="mt-2 text-sm text-gray-300">{question.explanation}</p>
            )}
          </motion.div>
        )}
      </motion.div>
      
      {/* Actions */}
      <div className="flex justify-between">
        <div className="flex items-center gap-2 text-yellow-400">
          <Zap size={18} />
          <span className="font-bold">{score} {t.xp}</span>
        </div>
        
        {!showResult ? (
          <motion.button
            onClick={handleSubmit}
            disabled={!selectedAnswer}
            className={`px-6 py-3 rounded-lg font-bold flex items-center gap-2 ${
              selectedAnswer
                ? 'bg-purple-600 hover:bg-purple-700'
                : 'bg-gray-700 cursor-not-allowed'
            }`}
            whileHover={selectedAnswer ? { scale: 1.02 } : {}}
            whileTap={selectedAnswer ? { scale: 0.98 } : {}}
          >
            <Send size={18} />
            {t.submit}
          </motion.button>
        ) : (
          <motion.button
            onClick={handleNext}
            className="px-6 py-3 rounded-lg font-bold bg-green-600 hover:bg-green-700 flex items-center gap-2"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            {currentQuestion < questions.length - 1 ? t.next : t.complete}
            <ChevronRight size={18} />
          </motion.button>
        )}
      </div>
    </div>
  );
};

// Stage Completion Modal
const CompletionModal: React.FC<{
  xp: number;
  stars: number;
  onContinue: () => void;
  t: typeof translations.tr;
}> = ({ xp, stars, onContinue, t }) => (
  <motion.div
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
  >
    <motion.div
      initial={{ scale: 0.5, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      className="bg-gradient-to-br from-purple-900 to-pink-900 rounded-2xl p-8 text-center max-w-md w-full"
    >
      <motion.div
        initial={{ rotate: 0 }}
        animate={{ rotate: 360 }}
        transition={{ duration: 0.5 }}
      >
        <Star className="w-20 h-20 mx-auto text-yellow-400 fill-yellow-400" />
      </motion.div>
      
      <h2 className="text-3xl font-bold mt-4">{t.congratulations}</h2>
      <p className="text-gray-300 mt-2">{t.stageComplete}</p>
      
      <div className="flex justify-center gap-8 mt-6">
        <div className="text-center">
          <div className="text-3xl font-bold text-yellow-400">+{xp}</div>
          <div className="text-sm text-gray-400">{t.earnedXP}</div>
        </div>
        <div className="text-center">
          <div className="flex justify-center">
            {[1, 2, 3].map(i => (
              <motion.div
                key={i}
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: i * 0.2 }}
              >
                <Star
                  size={28}
                  className={i <= stars ? 'text-yellow-400 fill-yellow-400' : 'text-gray-600'}
                />
              </motion.div>
            ))}
          </div>
          <div className="text-sm text-gray-400">{t.earnedStars}</div>
        </div>
      </div>
      
      <motion.button
        onClick={onContinue}
        className="mt-8 px-8 py-3 bg-gradient-to-r from-green-500 to-emerald-600 rounded-lg font-bold"
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        {t.continue}
      </motion.button>
    </motion.div>
  </motion.div>
);

// Main Component
export const StageContentView: React.FC<StageContentViewProps> = ({
  userId,
  stageId,
  onBack,
  onComplete,
  language = 'tr'
}) => {
  const t = translations[language];
  
  const [loading, setLoading] = useState(true);
  const [stage, setStage] = useState<StageData | null>(null);
  const [currentContentIndex, setCurrentContentIndex] = useState(0);
  const [showCompletion, setShowCompletion] = useState(false);
  const [earnedXP, setEarnedXP] = useState(0);
  const [earnedStars, setEarnedStars] = useState(0);
  
  // Load stage data
  useEffect(() => {
    const loadStage = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/learning-journey/stage/${userId}/${stageId}`);
        if (res.ok) {
          const data = await res.json();
          setStage(data.stage);
          
          // Find first incomplete content
          const firstIncomplete = data.stage.contents.findIndex((c: ContentItem) => !c.is_completed);
          if (firstIncomplete !== -1) {
            setCurrentContentIndex(firstIncomplete);
          }
        }
      } catch (error) {
        console.error('Failed to load stage:', error);
      } finally {
        setLoading(false);
      }
    };
    
    loadStage();
  }, [userId, stageId]);
  
  // Complete content
  const completeContent = async (score: number = 100) => {
    if (!stage) return;
    
    const content = stage.contents[currentContentIndex];
    
    try {
      await fetch(`${API_BASE}/api/learning-journey/stage/complete-content`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          stage_id: stageId,
          content_id: content.id,
          time_spent_seconds: content.duration_minutes * 60
        })
      });
      
      // Update local state
      const updatedContents = [...stage.contents];
      updatedContents[currentContentIndex].is_completed = true;
      setStage({ ...stage, contents: updatedContents });
      setEarnedXP(prev => prev + content.xp_reward);
      
      // Check if all contents are complete
      const allComplete = updatedContents.every(c => c.is_completed);
      if (allComplete) {
        setEarnedStars(score >= 95 ? 3 : score >= 80 ? 2 : 1);
        setShowCompletion(true);
      } else {
        // Move to next content
        const nextIncomplete = updatedContents.findIndex((c, i) => i > currentContentIndex && !c.is_completed);
        if (nextIncomplete !== -1) {
          setCurrentContentIndex(nextIncomplete);
        }
      }
    } catch (error) {
      console.error('Failed to complete content:', error);
    }
  };
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <RefreshCw className="w-8 h-8 animate-spin text-purple-500" />
      </div>
    );
  }
  
  if (!stage) {
    return <div className="text-center py-8">Stage not found</div>;
  }
  
  const currentContent = stage.contents[currentContentIndex];
  const ContentIcon = getContentIcon(currentContent?.type || 'lesson');
  const completedCount = stage.contents.filter(c => c.is_completed).length;
  
  return (
    <div className="min-h-screen bg-gray-900 text-white pb-24">
      {/* Header */}
      <div className="sticky top-0 bg-gray-900/95 backdrop-blur-sm border-b border-gray-800 p-4 z-40">
        <div className="flex items-center gap-4">
          <button
            onClick={onBack}
            className="p-2 hover:bg-gray-800 rounded-lg"
          >
            <ArrowLeft size={24} />
          </button>
          <div className="flex-1">
            <h1 className="font-bold text-lg">{stage.title}</h1>
            <div className="flex items-center gap-3 text-sm text-gray-400">
              <span>{t.stage} {stage.number}</span>
              <span>•</span>
              <span>{completedCount}/{stage.contents.length}</span>
            </div>
          </div>
          <div className="flex items-center gap-2 text-yellow-400">
            <Zap size={18} />
            <span className="font-bold">{earnedXP} {t.xp}</span>
          </div>
        </div>
        
        {/* Content Navigation */}
        <div className="flex gap-2 mt-4 overflow-x-auto pb-2">
          {stage.contents.map((content, idx) => {
            const Icon = getContentIcon(content.type);
            return (
              <button
                key={content.id}
                onClick={() => setCurrentContentIndex(idx)}
                className={`flex-shrink-0 px-3 py-2 rounded-lg flex items-center gap-2 transition-all ${
                  idx === currentContentIndex
                    ? 'bg-purple-600 text-white'
                    : content.is_completed
                      ? 'bg-green-600/20 text-green-400'
                      : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                }`}
              >
                {content.is_completed ? (
                  <CheckCircle size={16} />
                ) : (
                  <Icon size={16} />
                )}
                <span className="text-sm whitespace-nowrap">
                  {t[content.type as keyof typeof t] || content.type}
                </span>
              </button>
            );
          })}
        </div>
      </div>
      
      {/* Content Area */}
      <div className="p-4 max-w-4xl mx-auto">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentContentIndex}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            {/* Content Header */}
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-purple-600/20 rounded-xl flex items-center justify-center">
                  <ContentIcon size={24} className="text-purple-400" />
                </div>
                <div>
                  <h2 className="text-xl font-bold">{currentContent.title}</h2>
                  <div className="flex items-center gap-3 text-sm text-gray-400">
                    <span className="flex items-center gap-1">
                      <Clock size={14} />
                      {currentContent.duration_minutes} {t.minutes}
                    </span>
                    <span className="flex items-center gap-1">
                      <Zap size={14} className="text-yellow-400" />
                      +{currentContent.xp_reward} {t.xp}
                    </span>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Content based on type */}
            {currentContent.type === 'lesson' && (
              <LessonContent content={currentContent.content} t={t} />
            )}
            {currentContent.type === 'formula' && (
              <FormulaContent content={currentContent.content} t={t} />
            )}
            {currentContent.type === 'video' && (
              <VideoContent content={currentContent.content} t={t} />
            )}
            {(currentContent.type === 'practice' || currentContent.type === 'quiz') && (
              <QuizContent
                content={currentContent.content}
                onComplete={(score) => completeContent(score)}
                t={t}
              />
            )}
            
            {/* Complete Button (for non-quiz content) */}
            {currentContent.type !== 'practice' && currentContent.type !== 'quiz' && !currentContent.is_completed && (
              <motion.button
                onClick={() => completeContent(100)}
                className="w-full mt-8 py-4 bg-gradient-to-r from-green-500 to-emerald-600 rounded-xl font-bold text-lg flex items-center justify-center gap-2"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <CheckCircle size={24} />
                {t.complete}
              </motion.button>
            )}
            
            {currentContent.is_completed && (
              <div className="mt-8 p-4 bg-green-500/20 rounded-xl text-center text-green-400 font-medium flex items-center justify-center gap-2">
                <CheckCircle size={20} />
                {t.completed}
              </div>
            )}
          </motion.div>
        </AnimatePresence>
      </div>
      
      {/* Completion Modal */}
      {showCompletion && (
        <CompletionModal
          xp={earnedXP}
          stars={earnedStars}
          onContinue={() => {
            setShowCompletion(false);
            onComplete?.(stageId);
            onBack();
          }}
          t={t}
        />
      )}
    </div>
  );
};

export default StageContentView;
