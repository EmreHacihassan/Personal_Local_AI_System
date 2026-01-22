'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Trophy,
  Clock,
  CheckCircle,
  XCircle,
  Star,
  ChevronLeft,
  ChevronRight,
  MessageCircle,
  Brain,
  Mic,
  MicOff,
  Send,
  AlertTriangle,
  Award,
  Target,
  Sparkles,
  BookOpen,
  Lightbulb
} from 'lucide-react';

// ==================== TYPES ====================

type ExamType = 
  | 'multiple_choice'
  | 'fill_blank'
  | 'essay'
  | 'code_practice'
  | 'feynman'
  | 'teach_back'
  | 'oral_presentation'
  | 'concept_map'
  | 'case_study'
  | 'problem_solving';

interface Question {
  id: string;
  type: 'multiple_choice' | 'fill_blank' | 'essay' | 'code';
  question: string;
  options?: string[];
  code_template?: string;
  hints?: string[];
  points: number;
}

interface FeynmanCriteria {
  accuracy: number;
  depth: number;
  clarity: number;
  examples: number;
  completeness: number;
}

interface ExamData {
  id: string;
  title: string;
  type: ExamType;
  topic: string;
  description: string;
  instructions: string;
  questions?: Question[];
  feynman_prompt?: string;
  time_limit_minutes?: number;
  passing_score: number;
  max_attempts: number;
  current_attempt: number;
}

interface ExamResult {
  passed: boolean;
  score: number;
  total_points: number;
  percentage: number;
  feedback: string;
  detailed_feedback?: FeynmanCriteria;
  xp_earned: number;
  time_taken: number;
}

interface ExamViewProps {
  exam: ExamData;
  onComplete: (result: ExamResult) => void;
  onBack: () => void;
}

// ==================== TIMER COMPONENT ====================

const Timer: React.FC<{ minutes: number; onExpire: () => void }> = ({ minutes, onExpire }) => {
  const [seconds, setSeconds] = useState(minutes * 60);
  
  useEffect(() => {
    const interval = setInterval(() => {
      setSeconds(prev => {
        if (prev <= 1) {
          clearInterval(interval);
          onExpire();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    
    return () => clearInterval(interval);
  }, [onExpire]);
  
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  const isWarning = seconds <= 60;
  
  return (
    <div className={`flex items-center gap-2 px-3 py-2 rounded-lg font-mono text-lg
                    ${isWarning 
                      ? 'bg-red-100 dark:bg-red-900/30 text-red-600 animate-pulse' 
                      : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300'}`}>
      <Clock className="w-5 h-5" />
      <span>{String(mins).padStart(2, '0')}:{String(secs).padStart(2, '0')}</span>
    </div>
  );
};

// ==================== MULTIPLE CHOICE QUESTION ====================

const MultipleChoiceQuestion: React.FC<{
  question: Question;
  selectedAnswer: number | null;
  onSelect: (index: number) => void;
  showHint: boolean;
}> = ({ question, selectedAnswer, onSelect, showHint }) => {
  return (
    <div className="space-y-4">
      <div className="text-lg font-medium text-gray-900 dark:text-white">
        {question.question}
      </div>
      
      <div className="space-y-2">
        {question.options?.map((option, i) => (
          <button
            key={i}
            onClick={() => onSelect(i)}
            className={`w-full p-4 text-left rounded-xl border-2 transition-all ${
              selectedAnswer === i
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/30'
                : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
            }`}
          >
            <div className="flex items-center gap-3">
              <div className={`w-8 h-8 rounded-full border-2 flex items-center justify-center font-medium
                             ${selectedAnswer === i
                               ? 'border-blue-500 bg-blue-500 text-white'
                               : 'border-gray-300 dark:border-gray-600 text-gray-500'}`}>
                {String.fromCharCode(65 + i)}
              </div>
              <span className="text-gray-800 dark:text-gray-200">{option}</span>
            </div>
          </button>
        ))}
      </div>
      
      {showHint && question.hints && question.hints.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800"
        >
          <div className="flex items-start gap-2">
            <Lightbulb className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
            <span className="text-sm text-amber-800 dark:text-amber-300">
              {question.hints[0]}
            </span>
          </div>
        </motion.div>
      )}
    </div>
  );
};

// ==================== FEYNMAN TECHNIQUE EXAM ====================

const FeynmanExam: React.FC<{
  topic: string;
  prompt: string;
  onSubmit: (explanation: string) => Promise<ExamResult>;
  isSubmitting: boolean;
}> = ({ topic, prompt, onSubmit, isSubmitting }) => {
  const [explanation, setExplanation] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [tips, setTips] = useState<string[]>([
    'Basit bir dille açıkla, karmaşık terimlerden kaçın',
    'Günlük hayattan örnekler ver',
    'Adım adım açıkla',
    'Analojiler kullan',
    'Temel kavramlardan başla'
  ]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  const handleSubmit = () => {
    if (explanation.trim().length > 50) {
      onSubmit(explanation);
    }
  };
  
  const wordCount = explanation.trim().split(/\s+/).filter(Boolean).length;
  const minWords = 100;
  const progress = Math.min((wordCount / minWords) * 100, 100);
  
  return (
    <div className="space-y-6">
      {/* Feynman Info */}
      <div className="p-6 bg-gradient-to-br from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20
                      rounded-2xl border border-indigo-200 dark:border-indigo-800">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-indigo-500 rounded-xl">
            <Brain className="w-8 h-8 text-white" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-indigo-900 dark:text-indigo-300">
              Feynman Tekniği ile Öğren
            </h3>
            <p className="text-indigo-700 dark:text-indigo-400 mt-2">
              Richard Feynman'ın geliştirdiği bu teknikte, öğrendiğin konuyu basit bir dille
              birisine anlatıyormuş gibi açıklarsın. Bu yöntem, gerçekten ne kadar anladığını ortaya çıkarır.
            </p>
          </div>
        </div>
      </div>
      
      {/* Topic */}
      <div className="text-center py-4">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          Şu konuyu anlat: <span className="text-indigo-600">{topic}</span>
        </h2>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          {prompt}
        </p>
      </div>
      
      {/* Tips */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
        {tips.map((tip, i) => (
          <div key={i} className="p-2 bg-gray-100 dark:bg-gray-800 rounded-lg text-center text-xs text-gray-600 dark:text-gray-400">
            {tip}
          </div>
        ))}
      </div>
      
      {/* Explanation Input */}
      <div className="relative">
        <textarea
          ref={textareaRef}
          value={explanation}
          onChange={(e) => setExplanation(e.target.value)}
          placeholder="Konuyu burada kendi kelimelerinle açıkla... 

Örneğin: 'Bu konu şöyle çalışıyor. Bunu şuna benzetebiliriz...' şeklinde başlayabilirsin.

Karmaşık terimleri kullanma, 10 yaşındaki birine anlatıyormuş gibi yaz."
          className="w-full h-64 p-4 border-2 border-gray-200 dark:border-gray-700 rounded-xl
                     bg-white dark:bg-gray-800 text-gray-900 dark:text-white
                     focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 outline-none
                     resize-none"
        />
        
        {/* Recording Button */}
        <button
          onClick={() => setIsRecording(!isRecording)}
          className={`absolute bottom-4 right-4 p-3 rounded-full transition-all ${
            isRecording
              ? 'bg-red-500 text-white animate-pulse'
              : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200'
          }`}
        >
          {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
        </button>
      </div>
      
      {/* Progress */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-gray-600 dark:text-gray-400">
            {wordCount} / {minWords} kelime (minimum)
          </span>
          <span className={wordCount >= minWords ? 'text-green-500' : 'text-amber-500'}>
            {wordCount >= minWords ? '✓ Yeterli' : 'Biraz daha yaz'}
          </span>
        </div>
        <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <motion.div
            className={`h-full ${wordCount >= minWords ? 'bg-green-500' : 'bg-amber-500'}`}
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
          />
        </div>
      </div>
      
      {/* Submit */}
      <button
        onClick={handleSubmit}
        disabled={wordCount < 50 || isSubmitting}
        className={`w-full py-4 rounded-xl font-bold text-lg flex items-center justify-center gap-3 transition-all
                   ${wordCount >= 50 && !isSubmitting
                     ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white hover:shadow-lg hover:shadow-indigo-500/30'
                     : 'bg-gray-200 dark:bg-gray-700 text-gray-400 cursor-not-allowed'}`}
      >
        {isSubmitting ? (
          <>
            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            AI Değerlendiriyor...
          </>
        ) : (
          <>
            <Send className="w-5 h-5" />
            Açıklamayı Gönder
          </>
        )}
      </button>
    </div>
  );
};

// ==================== EXAM RESULT SCREEN ====================

const ExamResultScreen: React.FC<{
  result: ExamResult;
  examType: ExamType;
  onContinue: () => void;
}> = ({ result, examType, onContinue }) => {
  const isFeynman = examType === 'feynman' || examType === 'teach_back';
  
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="max-w-2xl mx-auto p-8"
    >
      {/* Result Header */}
      <div className={`text-center mb-8 p-8 rounded-3xl ${
        result.passed
          ? 'bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20'
          : 'bg-gradient-to-br from-red-50 to-orange-50 dark:from-red-900/20 dark:to-orange-900/20'
      }`}>
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', delay: 0.2 }}
          className={`w-24 h-24 mx-auto mb-4 rounded-full flex items-center justify-center ${
            result.passed ? 'bg-green-500' : 'bg-red-500'
          }`}
        >
          {result.passed ? (
            <Trophy className="w-12 h-12 text-white" />
          ) : (
            <XCircle className="w-12 h-12 text-white" />
          )}
        </motion.div>
        
        <h2 className={`text-3xl font-bold ${
          result.passed ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
        }`}>
          {result.passed ? 'Tebrikler! Başardın! 🎉' : 'Tekrar Dene 💪'}
        </h2>
        
        <div className="mt-4 flex items-center justify-center gap-6">
          <div className="text-center">
            <div className={`text-4xl font-bold ${
              result.passed ? 'text-green-600' : 'text-red-600'
            }`}>
              %{result.percentage}
            </div>
            <div className="text-sm text-gray-500">Başarı</div>
          </div>
          
          <div className="w-px h-12 bg-gray-300 dark:bg-gray-600" />
          
          <div className="text-center">
            <div className="text-4xl font-bold text-amber-500 flex items-center gap-1">
              <Star className="w-8 h-8" />
              {result.xp_earned}
            </div>
            <div className="text-sm text-gray-500">XP Kazandın</div>
          </div>
        </div>
      </div>
      
      {/* Feynman Detailed Feedback */}
      {isFeynman && result.detailed_feedback && (
        <div className="mb-8 p-6 bg-indigo-50 dark:bg-indigo-900/20 rounded-2xl border border-indigo-200 dark:border-indigo-800">
          <h3 className="font-bold text-indigo-900 dark:text-indigo-300 mb-4 flex items-center gap-2">
            <Brain className="w-5 h-5" />
            Detaylı Değerlendirme
          </h3>
          
          <div className="space-y-3">
            {[
              { key: 'accuracy', label: 'Doğruluk', icon: '✓' },
              { key: 'depth', label: 'Derinlik', icon: '📊' },
              { key: 'clarity', label: 'Açıklık', icon: '💡' },
              { key: 'examples', label: 'Örnekler', icon: '📝' },
              { key: 'completeness', label: 'Bütünlük', icon: '🎯' },
            ].map(({ key, label, icon }) => {
              const value = result.detailed_feedback![key as keyof FeynmanCriteria];
              return (
                <div key={key}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="flex items-center gap-1">
                      <span>{icon}</span> {label}
                    </span>
                    <span className="font-medium">{value}/100</span>
                  </div>
                  <div className="h-2 bg-indigo-200 dark:bg-indigo-800 rounded-full overflow-hidden">
                    <motion.div
                      className="h-full bg-indigo-500"
                      initial={{ width: 0 }}
                      animate={{ width: `${value}%` }}
                      transition={{ delay: 0.5 }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
      
      {/* General Feedback */}
      <div className="mb-8 p-6 bg-gray-50 dark:bg-gray-800 rounded-2xl">
        <h3 className="font-bold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
          <MessageCircle className="w-5 h-5" />
          AI Geri Bildirimi
        </h3>
        <p className="text-gray-700 dark:text-gray-300 whitespace-pre-line">
          {result.feedback}
        </p>
      </div>
      
      {/* Continue Button */}
      <button
        onClick={onContinue}
        className={`w-full py-4 rounded-xl font-bold text-lg ${
          result.passed
            ? 'bg-gradient-to-r from-green-500 to-emerald-600 text-white hover:shadow-lg hover:shadow-green-500/30'
            : 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white hover:shadow-lg hover:shadow-blue-500/30'
        } transition-all`}
      >
        {result.passed ? 'Devam Et' : 'Tekrar Dene'}
      </button>
    </motion.div>
  );
};

// ==================== MAIN EXAM VIEW ====================

const ExamView: React.FC<ExamViewProps> = ({ exam, onComplete, onBack }) => {
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<Map<string, any>>(new Map());
  const [showHints, setShowHints] = useState<Set<string>>(new Set());
  const [result, setResult] = useState<ExamResult | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [startTime] = useState(Date.now());
  
  const isFeynmanType = exam.type === 'feynman' || exam.type === 'teach_back';
  
  const handleSubmitExam = async () => {
    setIsSubmitting(true);
    
    const timeTaken = Math.floor((Date.now() - startTime) / 1000);
    
    // API call would go here
    // Simulating API response
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    const mockResult: ExamResult = {
      passed: true,
      score: 85,
      total_points: 100,
      percentage: 85,
      feedback: 'Harika bir açıklama yaptın! Konuyu basit ve anlaşılır şekilde ifade etmişsin.',
      detailed_feedback: isFeynmanType ? {
        accuracy: 88,
        depth: 82,
        clarity: 90,
        examples: 78,
        completeness: 85
      } : undefined,
      xp_earned: 150,
      time_taken: timeTaken
    };
    
    setResult(mockResult);
    setIsSubmitting(false);
  };
  
  const handleFeynmanSubmit = async (explanation: string): Promise<ExamResult> => {
    setIsSubmitting(true);
    
    try {
      const response = await fetch('/api/journey/v2/exam/feynman/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          exam_id: exam.id,
          explanation: explanation
        })
      });
      
      const data = await response.json();
      setResult(data);
      return data;
    } catch (error) {
      // Mock response for demo
      const mockResult: ExamResult = {
        passed: true,
        score: 85,
        total_points: 100,
        percentage: 85,
        feedback: 'Harika bir açıklama! Konuyu basit bir dille ifade etmişsin ve günlük hayattan güzel örnekler vermişsin.',
        detailed_feedback: {
          accuracy: 88,
          depth: 82,
          clarity: 90,
          examples: 78,
          completeness: 85
        },
        xp_earned: 150,
        time_taken: Math.floor((Date.now() - startTime) / 1000)
      };
      setResult(mockResult);
      return mockResult;
    } finally {
      setIsSubmitting(false);
    }
  };
  
  const handleTimeExpire = () => {
    handleSubmitExam();
  };
  
  if (result) {
    return (
      <ExamResultScreen
        result={result}
        examType={exam.type}
        onContinue={() => onComplete(result)}
      />
    );
  }
  
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={onBack}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            
            <div>
              <h1 className="text-lg font-bold text-gray-900 dark:text-white">
                {exam.title}
              </h1>
              <p className="text-sm text-gray-500">
                {exam.type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </p>
            </div>
          </div>
          
          {exam.time_limit_minutes && (
            <Timer minutes={exam.time_limit_minutes} onExpire={handleTimeExpire} />
          )}
        </div>
      </div>
      
      {/* Content */}
      <div className="max-w-4xl mx-auto p-4">
        {/* Instructions */}
        <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl border border-blue-200 dark:border-blue-800">
          <h3 className="font-medium text-blue-800 dark:text-blue-300 mb-1">
            📋 Talimatlar
          </h3>
          <p className="text-sm text-blue-700 dark:text-blue-400">
            {exam.instructions}
          </p>
        </div>
        
        {/* Feynman Exam */}
        {isFeynmanType && (
          <FeynmanExam
            topic={exam.topic}
            prompt={exam.feynman_prompt || 'Bu konuyu basit bir dille açıkla.'}
            onSubmit={handleFeynmanSubmit}
            isSubmitting={isSubmitting}
          />
        )}
        
        {/* Multiple Choice Questions */}
        {exam.questions && exam.questions.length > 0 && !isFeynmanType && (
          <>
            {/* Question Navigation */}
            <div className="flex items-center gap-2 mb-6 overflow-x-auto pb-2">
              {exam.questions.map((q, i) => (
                <button
                  key={q.id}
                  onClick={() => setCurrentQuestion(i)}
                  className={`w-10 h-10 rounded-full flex items-center justify-center font-medium transition-all ${
                    i === currentQuestion
                      ? 'bg-blue-500 text-white scale-110'
                      : answers.has(q.id)
                        ? 'bg-green-500 text-white'
                        : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                  }`}
                >
                  {i + 1}
                </button>
              ))}
            </div>
            
            {/* Current Question */}
            <MultipleChoiceQuestion
              question={exam.questions[currentQuestion]}
              selectedAnswer={answers.get(exam.questions[currentQuestion].id) ?? null}
              onSelect={(index) => {
                const newAnswers = new Map(answers);
                newAnswers.set(exam.questions![currentQuestion].id, index);
                setAnswers(newAnswers);
              }}
              showHint={showHints.has(exam.questions[currentQuestion].id)}
            />
            
            {/* Navigation Buttons */}
            <div className="flex justify-between mt-8">
              <button
                onClick={() => setCurrentQuestion(prev => Math.max(0, prev - 1))}
                disabled={currentQuestion === 0}
                className="px-6 py-3 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 
                           rounded-xl disabled:opacity-50 flex items-center gap-2"
              >
                <ChevronLeft className="w-5 h-5" />
                Önceki
              </button>
              
              {currentQuestion === exam.questions.length - 1 ? (
                <button
                  onClick={handleSubmitExam}
                  disabled={isSubmitting || answers.size < exam.questions.length}
                  className="px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-600 text-white
                             rounded-xl font-bold disabled:opacity-50 flex items-center gap-2"
                >
                  {isSubmitting ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Değerlendiriliyor...
                    </>
                  ) : (
                    <>
                      <CheckCircle className="w-5 h-5" />
                      Sınavı Bitir
                    </>
                  )}
                </button>
              ) : (
                <button
                  onClick={() => setCurrentQuestion(prev => Math.min(exam.questions!.length - 1, prev + 1))}
                  className="px-6 py-3 bg-blue-500 text-white rounded-xl flex items-center gap-2"
                >
                  Sonraki
                  <ChevronRight className="w-5 h-5" />
                </button>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default ExamView;
