'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  GraduationCap,
  Plus,
  RefreshCw,
  Sparkles,
  Flame,
  Star,
  Clock,
  Zap,
  ArrowLeft,
  Map,
  Layers,
  ChevronRight,
  ChevronDown,
  Play,
  CheckCircle,
  Lock,
  BookOpen,
  Target,
  Trophy,
  Brain,
  Award,
  Mic,
  FileText,
  Video,
  HelpCircle,
  AlertCircle,
  TrendingUp,
  Send,
  Timer,
  Check,
  X
} from 'lucide-react';

// ============================================================================
// TYPES
// ============================================================================

interface LearningGoal {
  title: string;
  subject: string;
  target_outcome: string;
  motivation: string;
  prior_knowledge: string;
  weak_areas: string[];
  focus_areas: string[];
  daily_hours: number;
  deadline: string | null;
  content_preferences: string[];
  exam_preferences: string[];
  topics_to_include: string[] | null;
  topics_to_exclude: string[] | null;
}

interface JourneyV2 {
  journey_id: string;
  title: string;
  subject: string;
  target_outcome: string;
  total_stages: number;
  total_packages: number;
  total_exams: number;
  total_exercises: number;
  estimated_total_hours: number;
  total_xp_possible: number;
  created_at: string;
  stages?: StageV2[];
  progress?: JourneyProgress;
}

interface StageV2 {
  id: string;           // Backend uses 'id'
  stage_id?: string;    // Alias for compatibility
  title: string;        // Backend uses 'title'
  name?: string;        // Alias for compatibility
  description: string;
  number: number;       // Backend uses 'number' not 'order'
  order?: number;       // Alias for compatibility
  packages: PackageV2[];
  status: 'locked' | 'available' | 'in_progress' | 'completed';
  progress_percentage: number;
  xp_earned: number;
  xp_total: number;
}

interface PackageV2 {
  id: string;           // Backend uses 'id'
  package_id?: string;  // Alias for compatibility
  title: string;        // Backend uses 'title'
  name?: string;        // Alias for compatibility
  description: string;
  type: string;         // Backend uses 'type'
  package_type?: string; // Alias for compatibility
  number: number;       // Backend uses 'number'
  order?: number;       // Alias for compatibility
  status: 'locked' | 'available' | 'in_progress' | 'passed' | 'completed';
  progress_percentage: number;
  xp_earned: number;
  xp_total: number;
  xp_reward?: number;   // Backend field
  content_blocks: ContentBlock[];
  exercises: Exercise[];
  exams: ExamV2[];
}

interface ContentBlock {
  id: string;
  type?: string;        // Backend uses 'type'
  block_type?: string;  // Alias for compatibility
  title: string;
  content: string;
  media_url?: string;
  completed: boolean;
}

interface Exercise {
  id: string;
  type?: string;           // Backend uses 'type'
  exercise_type?: string;  // Alias for compatibility
  title: string;
  description: string;
  instructions: string;
  completed: boolean;
  score?: number;
}

interface ExamV2 {
  id: string;
  type: string;         // Backend uses 'type'
  exam_type?: string;   // Alias for compatibility
  title: string;
  description: string;
  topic: string;
  time_limit_minutes: number;
  passing_score: number;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  score?: number;
  questions?: ExamQuestion[];
}

interface ExamQuestion {
  id: string;
  question: string;
  type: string;
  options?: string[];
  correct_answer?: string;
}

interface JourneyProgress {
  completed_packages: number;
  total_packages: number;
  completed_exams: number;
  total_exams: number;
  xp_earned: number;
  xp_total: number;
  streak_days: number;
  level: number;
}

interface AIThinkingStep {
  step: string;
  status: 'pending' | 'processing' | 'completed';
  message: string;
  details?: Record<string, unknown>;
}

interface Certificate {
  id: string;
  certificate_code?: string;   // Alias
  verification_code: string;   // Backend field
  user_name: string;
  journey_title: string;
  title?: string;              // Backend field
  subject?: string;
  issued_at?: string;
  completion_date: string;     // Backend field
  grade: string;
  total_xp: number;
  total_xp_earned?: number;    // Backend field alias
  average_score?: number;
}

type ViewState = 'list' | 'wizard' | 'thinking' | 'journey' | 'package' | 'exam' | 'certificate';

// ============================================================================
// CONSTANTS
// ============================================================================

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const SUBJECTS = [
  { id: 'matematik', name: 'Matematik', icon: '📐', color: '#3B82F6' },
  { id: 'fizik', name: 'Fizik', icon: '⚛️', color: '#8B5CF6' },
  { id: 'kimya', name: 'Kimya', icon: '🧪', color: '#10B981' },
  { id: 'biyoloji', name: 'Biyoloji', icon: '🧬', color: '#22C55E' },
  { id: 'programlama', name: 'Programlama', icon: '💻', color: '#EC4899' },
  { id: 'ingilizce', name: 'İngilizce', icon: '🌍', color: '#06B6D4' },
  { id: 'tarih', name: 'Tarih', icon: '📜', color: '#F59E0B' },
  { id: 'felsefe', name: 'Felsefe', icon: '🤔', color: '#6366F1' },
];

const CONTENT_TYPES = [
  { id: 'text', name: 'Metin', icon: '📖', desc: 'Yazılı açıklamalar' },
  { id: 'video', name: 'Video', icon: '🎬', desc: 'Video dersler' },
  { id: 'interactive', name: 'İnteraktif', icon: '🎮', desc: 'Etkileşimli içerik' },
  { id: 'audio', name: 'Sesli', icon: '🎧', desc: 'Podcast tarzı' },
];

const EXAM_TYPES = [
  { id: 'multiple_choice', name: 'Çoktan Seçmeli', icon: '📝', desc: 'Klasik test' },
  { id: 'feynman', name: 'Feynman Tekniği', icon: '🎤', desc: 'Anlat & Öğren' },
  { id: 'problem_solving', name: 'Problem Çözme', icon: '🧩', desc: 'Adım adım çözüm' },
  { id: 'concept_map', name: 'Kavram Haritası', icon: '🕸️', desc: 'Görsel bağlantı' },
  { id: 'teach_back', name: 'Öğreterek Öğren', icon: '👨‍🏫', desc: 'Birine anlatır gibi' },
];

const PACKAGE_TYPE_ICONS: Record<string, { icon: React.ReactNode; color: string }> = {
  intro: { icon: <Target className="w-5 h-5" />, color: 'from-blue-500 to-cyan-500' },
  learning: { icon: <BookOpen className="w-5 h-5" />, color: 'from-indigo-500 to-purple-500' },
  practice: { icon: <Brain className="w-5 h-5" />, color: 'from-green-500 to-emerald-500' },
  review: { icon: <RefreshCw className="w-5 h-5" />, color: 'from-yellow-500 to-orange-500' },
  exam: { icon: <FileText className="w-5 h-5" />, color: 'from-red-500 to-pink-500' },
  closure: { icon: <Trophy className="w-5 h-5" />, color: 'from-amber-500 to-yellow-500' },
};

const THINKING_STEPS = [
  { step: 'goal_analysis', icon: <Target className="w-5 h-5" />, label: 'Hedef Analizi' },
  { step: 'curriculum_selection', icon: <BookOpen className="w-5 h-5" />, label: 'Müfredat Seçimi' },
  { step: 'topic_mapping', icon: <Map className="w-5 h-5" />, label: 'Konu Haritalama' },
  { step: 'stage_planning', icon: <Layers className="w-5 h-5" />, label: 'Aşama Planlama' },
  { step: 'package_design', icon: <Award className="w-5 h-5" />, label: 'Paket Tasarımı' },
  { step: 'exam_generation', icon: <FileText className="w-5 h-5" />, label: 'Sınav Oluşturma' },
  { step: 'exercise_creation', icon: <Brain className="w-5 h-5" />, label: 'Egzersiz Hazırlama' },
  { step: 'content_structuring', icon: <Sparkles className="w-5 h-5" />, label: 'İçerik Yapılandırma' },
];

// ============================================================================
// API FUNCTIONS
// ============================================================================

async function fetchJourneys(userId: string = 'default_user'): Promise<JourneyV2[]> {
  try {
    const res = await fetch(`${API_BASE}/api/journey/v2/list?user_id=${userId}`);
    if (!res.ok) return [];
    const data = await res.json();
    return data.journeys || [];
  } catch (error) {
    console.error('Failed to fetch journeys:', error);
    return [];
  }
}

async function fetchJourneyMap(journeyId: string): Promise<JourneyV2 | null> {
  try {
    const res = await fetch(`${API_BASE}/api/journey/v2/${journeyId}/map`);
    if (!res.ok) return null;
    const data = await res.json();
    return data;
  } catch (error) {
    console.error('Failed to fetch journey map:', error);
    return null;
  }
}

async function createJourneyV2(goal: LearningGoal): Promise<{
  success: boolean;
  journey_id?: string;
  thinking_steps?: AIThinkingStep[];
  curriculum?: JourneyV2;
  error?: string;
}> {
  try {
    const res = await fetch(`${API_BASE}/api/journey/v2/create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(goal)
    });
    return await res.json();
  } catch (error) {
    return { success: false, error: String(error) };
  }
}

async function submitExamV2(
  journeyId: string, 
  examId: string, 
  submission: {
    exam_type: string;
    explanation?: string;
    answers?: Record<string, string>;
    time_taken_seconds: number;
  }
): Promise<{
  success: boolean;
  score?: number;
  passed?: boolean;
  feedback?: {
    accuracy: number;
    depth: number;
    clarity: number;
    examples: number;
    completeness: number;
    overall_feedback: string;
  };
}> {
  try {
    const res = await fetch(`${API_BASE}/api/journey/v2/${journeyId}/exams/${examId}/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(submission)
    });
    return await res.json();
  } catch (error) {
    return { success: false };
  }
}

async function startPackageV2(
  journeyId: string,
  packageId: string
): Promise<{
  success: boolean;
  package?: PackageV2;
  events?: unknown[];
  error?: string;
}> {
  try {
    const res = await fetch(`${API_BASE}/api/journey/v2/${journeyId}/packages/${packageId}/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    return await res.json();
  } catch (error) {
    return { success: false, error: String(error) };
  }
}

async function completePackageV2(
  journeyId: string,
  packageId: string
): Promise<{
  success: boolean;
  events?: unknown[];
  error?: string;
}> {
  try {
    const res = await fetch(`${API_BASE}/api/journey/v2/${journeyId}/packages/${packageId}/complete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    return await res.json();
  } catch (error) {
    return { success: false, error: String(error) };
  }
}

async function completeJourneyV2(
  journeyId: string,
  userName: string
): Promise<{
  success: boolean;
  certificate?: Certificate;
  events?: unknown[];
  error?: string;
}> {
  try {
    const res = await fetch(`${API_BASE}/api/journey/v2/${journeyId}/complete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_name: userName })
    });
    return await res.json();
  } catch (error) {
    return { success: false, error: String(error) };
  }
}

// ============================================================================
// SUB COMPONENTS
// ============================================================================

// XP Indicator
const XPIndicator: React.FC<{ xp: number; level: number }> = ({ xp, level }) => {
  const xpForNextLevel = ((level + 1) ** 2) * 100;
  const currentLevelXp = (level ** 2) * 100;
  const progress = Math.min(((xp - currentLevelXp) / (xpForNextLevel - currentLevelXp)) * 100, 100);

  return (
    <div className="flex items-center gap-3 bg-gradient-to-r from-purple-900/50 to-indigo-900/50 rounded-xl p-3 border border-purple-500/30">
      <div className="w-12 h-12 rounded-full bg-gradient-to-br from-yellow-400 to-amber-500 flex items-center justify-center font-bold text-lg text-black">
        {level}
      </div>
      <div className="flex-1">
        <div className="flex justify-between text-sm mb-1">
          <span className="text-purple-200">Level {level}</span>
          <span className="text-amber-400">{xp.toLocaleString()} XP</span>
        </div>
        <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-yellow-400 to-amber-500"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
          />
        </div>
      </div>
    </div>
  );
};

// Streak Indicator
const StreakIndicator: React.FC<{ days: number }> = ({ days }) => (
  <div className="flex items-center gap-2 bg-gradient-to-r from-orange-900/50 to-red-900/50 rounded-xl p-3 border border-orange-500/30">
    <Flame className="w-8 h-8 text-orange-400" />
    <div>
      <div className="text-2xl font-bold text-orange-400">{days}</div>
      <div className="text-xs text-orange-200">gün streak 🔥</div>
    </div>
  </div>
);

// Journey Card
const JourneyCard: React.FC<{
  journey: JourneyV2;
  onSelect: (journey: JourneyV2) => void;
}> = ({ journey, onSelect }) => {
  const progressPercent = journey.progress 
    ? (journey.progress.completed_packages / Math.max(journey.progress.total_packages, 1)) * 100 
    : 0;

  return (
    <motion.div
      whileHover={{ scale: 1.02, y: -4 }}
      whileTap={{ scale: 0.98 }}
      onClick={() => onSelect(journey)}
      className="cursor-pointer bg-gradient-to-br from-gray-800/80 to-gray-900/80 rounded-2xl p-6 border border-gray-700/50 hover:border-purple-500/50 transition-all"
    >
      <div className="flex items-start justify-between mb-4">
        <div className="p-3 rounded-xl bg-gradient-to-br from-purple-500 to-indigo-500">
          <GraduationCap className="w-6 h-6 text-white" />
        </div>
        <div className="flex items-center gap-1 text-amber-400">
          <Star className="w-4 h-4 fill-current" />
          <span className="text-sm font-medium">Lvl {journey.progress?.level || 1}</span>
        </div>
      </div>
      
      <h3 className="text-lg font-semibold text-white mb-1">{journey.title}</h3>
      <p className="text-sm text-gray-400 mb-4 line-clamp-2">{journey.target_outcome}</p>
      
      <div className="flex items-center justify-between text-sm text-gray-400 mb-3">
        <span>{journey.total_stages} aşama</span>
        <span>{journey.total_packages} paket</span>
        <span>{journey.total_exams} sınav</span>
      </div>
      
      <div className="h-2 bg-gray-700 rounded-full overflow-hidden mb-2">
        <motion.div
          className="h-full bg-gradient-to-r from-green-400 to-emerald-500"
          initial={{ width: 0 }}
          animate={{ width: `${progressPercent}%` }}
        />
      </div>
      <div className="flex justify-between text-xs">
        <span className="text-gray-500">İlerleme</span>
        <span className="text-green-400">{progressPercent.toFixed(1)}%</span>
      </div>

      <div className="mt-4 flex items-center justify-between text-xs text-gray-500">
        <span className="flex items-center gap-1">
          <Clock className="w-3 h-3" />
          ~{journey.estimated_total_hours?.toFixed(0) || 0} saat
        </span>
        <span className="flex items-center gap-1">
          <Zap className="w-3 h-3 text-amber-400" />
          {(journey.total_xp_possible || 0).toLocaleString()} XP
        </span>
      </div>
    </motion.div>
  );
};

// Step Indicator for Wizard
const StepIndicator: React.FC<{ currentStep: number; totalSteps: number }> = ({ currentStep, totalSteps }) => (
  <div className="flex items-center justify-center gap-2 mb-8">
    {Array.from({ length: totalSteps }).map((_, index) => (
      <motion.div
        key={index}
        className={`h-2 rounded-full transition-all duration-300 ${
          index <= currentStep 
            ? 'bg-gradient-to-r from-purple-500 to-indigo-600' 
            : 'bg-gray-700'
        }`}
        initial={{ width: 24 }}
        animate={{ width: index === currentStep ? 48 : 24 }}
      />
    ))}
  </div>
);

// ============================================================================
// WIZARD COMPONENT
// ============================================================================

const JourneyWizard: React.FC<{
  onComplete: (goal: LearningGoal) => void;
  onCancel: () => void;
}> = ({ onComplete, onCancel }) => {
  const [step, setStep] = useState(0);
  const [goal, setGoal] = useState<LearningGoal>({
    title: '',
    subject: '',
    target_outcome: '',
    motivation: '',
    prior_knowledge: 'beginner',
    weak_areas: [],
    focus_areas: [],
    daily_hours: 2,
    deadline: null,
    content_preferences: ['text', 'video'],
    exam_preferences: ['multiple_choice', 'feynman'],
    topics_to_include: null,
    topics_to_exclude: null,
  });

  const updateGoal = (updates: Partial<LearningGoal>) => {
    setGoal(prev => ({ ...prev, ...updates }));
  };

  const canProceed = () => {
    switch (step) {
      case 0: return goal.subject !== '';
      case 1: return goal.title !== '' && goal.target_outcome !== '';
      case 2: return goal.prior_knowledge !== '';
      case 3: return goal.daily_hours > 0;
      case 4: return goal.content_preferences.length > 0;
      default: return true;
    }
  };

  const handleNext = () => {
    if (step < 4) {
      setStep(step + 1);
    } else {
      onComplete(goal);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <StepIndicator currentStep={step} totalSteps={5} />

      <AnimatePresence mode="wait">
        {/* Step 0: Subject Selection */}
        {step === 0 && (
          <motion.div
            key="step0"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-white mb-2">Ne öğrenmek istiyorsun?</h2>
              <p className="text-gray-400">Bir konu alanı seç</p>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {SUBJECTS.map((subject) => (
                <motion.button
                  key={subject.id}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => updateGoal({ subject: subject.id })}
                  className={`p-6 rounded-2xl border-2 transition-all ${
                    goal.subject === subject.id
                      ? 'border-purple-500 bg-purple-500/20'
                      : 'border-gray-700 bg-gray-800/50 hover:border-gray-600'
                  }`}
                >
                  <div className="text-4xl mb-3">{subject.icon}</div>
                  <div className="font-medium text-white">{subject.name}</div>
                </motion.button>
              ))}
            </div>
          </motion.div>
        )}

        {/* Step 1: Goal Details */}
        {step === 1 && (
          <motion.div
            key="step1"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-white mb-2">Hedefini tanımla</h2>
              <p className="text-gray-400">Ne başarmak istiyorsun?</p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Yolculuk Başlığı
                </label>
                <input
                  type="text"
                  value={goal.title}
                  onChange={(e) => updateGoal({ title: e.target.value })}
                  placeholder="Örn: AYT Matematik Hazırlık"
                  className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-white focus:border-purple-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Hedef Sonuç
                </label>
                <textarea
                  value={goal.target_outcome}
                  onChange={(e) => updateGoal({ target_outcome: e.target.value })}
                  placeholder="Örn: AYT'de 35+ net yaparak istediğim bölüme girmek"
                  rows={3}
                  className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-white resize-none focus:border-purple-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Motivasyonun
                </label>
                <textarea
                  value={goal.motivation}
                  onChange={(e) => updateGoal({ motivation: e.target.value })}
                  placeholder="Bu hedef seni neden motive ediyor?"
                  rows={2}
                  className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-white resize-none focus:border-purple-500 focus:outline-none"
                />
              </div>
            </div>
          </motion.div>
        )}

        {/* Step 2: Prior Knowledge */}
        {step === 2 && (
          <motion.div
            key="step2"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-white mb-2">Mevcut seviyeni belirle</h2>
              <p className="text-gray-400">Bu konudaki bilgi düzeyin nedir?</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {[
                { id: 'beginner', label: 'Başlangıç', icon: '🌱', desc: 'Konuya yeni başlıyorum' },
                { id: 'intermediate', label: 'Orta', icon: '📚', desc: 'Temel bilgilerim var' },
                { id: 'advanced', label: 'İleri', icon: '🎯', desc: 'Çoğu konuyu biliyorum' },
              ].map((level) => (
                <motion.button
                  key={level.id}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => updateGoal({ prior_knowledge: level.id })}
                  className={`p-6 rounded-2xl border-2 text-left transition-all ${
                    goal.prior_knowledge === level.id
                      ? 'border-purple-500 bg-purple-500/20'
                      : 'border-gray-700 bg-gray-800/50 hover:border-gray-600'
                  }`}
                >
                  <div className="text-3xl mb-3">{level.icon}</div>
                  <div className="font-medium text-white mb-1">{level.label}</div>
                  <div className="text-sm text-gray-400">{level.desc}</div>
                </motion.button>
              ))}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Zayıf olduğun alanlar (opsiyonel)
              </label>
              <input
                type="text"
                value={goal.weak_areas.join(', ')}
                onChange={(e) => updateGoal({ weak_areas: e.target.value.split(',').map(s => s.trim()).filter(Boolean) })}
                placeholder="Örn: Türev, İntegral, Limit"
                className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-white focus:border-purple-500 focus:outline-none"
              />
            </div>
          </motion.div>
        )}

        {/* Step 3: Time Planning */}
        {step === 3 && (
          <motion.div
            key="step3"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-white mb-2">Zaman planı</h2>
              <p className="text-gray-400">Günlük ne kadar çalışabilirsin?</p>
            </div>

            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-4">
                  Günlük Çalışma Süresi: <span className="text-purple-400">{goal.daily_hours} saat</span>
                </label>
                <input
                  type="range"
                  min={0.5}
                  max={8}
                  step={0.5}
                  value={goal.daily_hours}
                  onChange={(e) => updateGoal({ daily_hours: parseFloat(e.target.value) })}
                  className="w-full accent-purple-500"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-2">
                  <span>30 dk</span>
                  <span>4 saat</span>
                  <span>8 saat</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Hedef Tarih (opsiyonel)
                </label>
                <input
                  type="date"
                  value={goal.deadline || ''}
                  onChange={(e) => updateGoal({ deadline: e.target.value || null })}
                  className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-white focus:border-purple-500 focus:outline-none"
                />
              </div>
            </div>
          </motion.div>
        )}

        {/* Step 4: Preferences */}
        {step === 4 && (
          <motion.div
            key="step4"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-white mb-2">Tercihlerini belirle</h2>
              <p className="text-gray-400">Nasıl öğrenmek istiyorsun?</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-3">
                İçerik Türleri
              </label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {CONTENT_TYPES.map((type) => (
                  <button
                    key={type.id}
                    onClick={() => {
                      const prefs = goal.content_preferences.includes(type.id)
                        ? goal.content_preferences.filter(p => p !== type.id)
                        : [...goal.content_preferences, type.id];
                      updateGoal({ content_preferences: prefs });
                    }}
                    className={`p-4 rounded-xl border-2 text-center transition-all ${
                      goal.content_preferences.includes(type.id)
                        ? 'border-purple-500 bg-purple-500/20'
                        : 'border-gray-700 bg-gray-800/50'
                    }`}
                  >
                    <div className="text-2xl mb-2">{type.icon}</div>
                    <div className="text-sm font-medium text-white">{type.name}</div>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-3">
                Sınav Türleri
              </label>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {EXAM_TYPES.map((type) => (
                  <button
                    key={type.id}
                    onClick={() => {
                      const prefs = goal.exam_preferences.includes(type.id)
                        ? goal.exam_preferences.filter(p => p !== type.id)
                        : [...goal.exam_preferences, type.id];
                      updateGoal({ exam_preferences: prefs });
                    }}
                    className={`p-4 rounded-xl border-2 text-left transition-all ${
                      goal.exam_preferences.includes(type.id)
                        ? 'border-purple-500 bg-purple-500/20'
                        : 'border-gray-700 bg-gray-800/50'
                    }`}
                  >
                    <div className="text-2xl mb-2">{type.icon}</div>
                    <div className="text-sm font-medium text-white">{type.name}</div>
                    <div className="text-xs text-gray-400">{type.desc}</div>
                  </button>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Navigation Buttons */}
      <div className="flex items-center justify-between mt-8">
        <button
          onClick={() => step > 0 ? setStep(step - 1) : onCancel()}
          className="px-6 py-3 rounded-xl bg-gray-800 text-gray-300 hover:bg-gray-700 transition-colors"
        >
          {step > 0 ? 'Geri' : 'İptal'}
        </button>

        <button
          onClick={handleNext}
          disabled={!canProceed()}
          className={`px-8 py-3 rounded-xl font-medium flex items-center gap-2 transition-all ${
            canProceed()
              ? 'bg-gradient-to-r from-purple-500 to-indigo-500 text-white hover:opacity-90'
              : 'bg-gray-700 text-gray-500 cursor-not-allowed'
          }`}
        >
          {step < 4 ? (
            <>
              İleri
              <ChevronRight className="w-5 h-5" />
            </>
          ) : (
            <>
              <Sparkles className="w-5 h-5" />
              Yolculuğu Başlat
            </>
          )}
        </button>
      </div>
    </div>
  );
};

// ============================================================================
// AI THINKING VIEW COMPONENT
// ============================================================================

const AIThinkingViewComponent: React.FC<{
  steps: AIThinkingStep[];
  curriculum?: JourneyV2 | null;
  onComplete: () => void;
  isLoading?: boolean;
}> = ({ steps, curriculum, onComplete, isLoading = false }) => {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [hasCalledComplete, setHasCalledComplete] = useState(false);

  // Adım sayısı olarak THINKING_STEPS kullan
  const totalSteps = THINKING_STEPS.length;

  useEffect(() => {
    // Adım animasyonu - her 800ms bir adım ilerlet
    const timer = setInterval(() => {
      setCurrentStepIndex(prev => {
        if (prev < totalSteps - 1) return prev + 1;
        clearInterval(timer);
        return prev;
      });
    }, 800);

    return () => clearInterval(timer);
  }, [totalSteps]);

  // Animasyon bitti VE curriculum hazır olduğunda onComplete'i çağır
  useEffect(() => {
    if (currentStepIndex >= totalSteps - 1 && curriculum && !isLoading && !hasCalledComplete) {
      setHasCalledComplete(true);
      setTimeout(onComplete, 1500);
    }
  }, [currentStepIndex, totalSteps, curriculum, isLoading, onComplete, hasCalledComplete]);

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 2, ease: 'linear' }}
          className="w-20 h-20 mx-auto mb-6 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center"
        >
          <Brain className="w-10 h-10 text-white" />
        </motion.div>
        <h2 className="text-2xl font-bold text-white mb-2">AI Müfredatı Hazırlıyor</h2>
        <p className="text-gray-400">Kişiselleştirilmiş öğrenme yolculuğun oluşturuluyor...</p>
      </div>

      {/* Steps */}
      <div className="space-y-3">
        {THINKING_STEPS.map((stepInfo, index) => {
          const isCompleted = index < currentStepIndex;
          const isProcessing = index === currentStepIndex;
          const isPending = index > currentStepIndex;

          return (
            <motion.div
              key={stepInfo.step}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className={`flex items-center gap-4 p-4 rounded-xl border transition-all ${
                isCompleted
                  ? 'border-green-500/50 bg-green-900/20'
                  : isProcessing
                  ? 'border-purple-500/50 bg-purple-900/20'
                  : 'border-gray-700 bg-gray-800/30'
              }`}
            >
              <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                isCompleted
                  ? 'bg-green-500 text-white'
                  : isProcessing
                  ? 'bg-purple-500 text-white animate-pulse'
                  : 'bg-gray-700 text-gray-400'
              }`}>
                {isCompleted ? (
                  <CheckCircle className="w-5 h-5" />
                ) : isProcessing ? (
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}
                  >
                    {stepInfo.icon}
                  </motion.div>
                ) : (
                  stepInfo.icon
                )}
              </div>

              <div className="flex-1">
                <div className={`font-medium ${
                  isCompleted ? 'text-green-400' : isProcessing ? 'text-purple-300' : 'text-gray-500'
                }`}>
                  {stepInfo.label}
                </div>
                {isProcessing && (
                  <div className="text-sm text-purple-400 animate-pulse">İşleniyor...</div>
                )}
              </div>

              {isCompleted && (
                <CheckCircle className="w-5 h-5 text-green-400" />
              )}
            </motion.div>
          );
        })}
      </div>

      {/* Curriculum Preview */}
      {curriculum && currentStepIndex >= THINKING_STEPS.length - 1 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-8 p-6 rounded-2xl bg-gradient-to-br from-purple-900/50 to-indigo-900/50 border border-purple-500/30"
        >
          <h3 className="text-lg font-semibold text-white mb-4">Müfredat Özeti</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-purple-400">{curriculum.total_stages}</div>
              <div className="text-sm text-gray-400">Aşama</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-blue-400">{curriculum.total_packages}</div>
              <div className="text-sm text-gray-400">Paket</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-400">{curriculum.total_exams}</div>
              <div className="text-sm text-gray-400">Sınav</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-amber-400">{(curriculum.total_xp_possible || 0).toLocaleString()}</div>
              <div className="text-sm text-gray-400">XP</div>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
};

// ============================================================================
// STAGE MAP COMPONENT
// ============================================================================

const StageMapComponent: React.FC<{
  stages: StageV2[];
  onSelectPackage: (pkg: PackageV2) => void;
}> = ({ stages, onSelectPackage }) => {
  const [expandedStages, setExpandedStages] = useState<Set<string>>(new Set());

  const toggleStage = (stageId: string) => {
    const newExpanded = new Set(expandedStages);
    if (newExpanded.has(stageId)) {
      newExpanded.delete(stageId);
    } else {
      newExpanded.add(stageId);
    }
    setExpandedStages(newExpanded);
  };

  useEffect(() => {
    // Auto-expand first available stage
    const firstAvailable = stages.find(s => s.status !== 'locked');
    if (firstAvailable) {
      const stageId = firstAvailable.id || firstAvailable.stage_id || '';
      setExpandedStages(new Set([stageId]));
    }
  }, [stages]);

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-white flex items-center gap-2">
        <Map className="w-5 h-5 text-indigo-400" />
        Öğrenme Yol Haritası
      </h3>

      {stages.map((stage, index) => {
        const stageId = stage.id || stage.stage_id || `stage-${index}`;
        const stageName = stage.title || stage.name || `Aşama ${index + 1}`;
        const isLocked = stage.status === 'locked';
        const isExpanded = expandedStages.has(stageId);
        const completedPackages = stage.packages.filter(p => p.status === 'passed' || p.status === 'completed').length;
        const progress = stage.packages.length > 0 ? (completedPackages / stage.packages.length) * 100 : 0;

        return (
          <div
            key={stageId}
            className={`rounded-2xl border overflow-hidden ${
              isLocked ? 'border-gray-700 opacity-60' : 'border-gray-700/50'
            }`}
          >
            {/* Stage Header */}
            <div
              onClick={() => !isLocked && toggleStage(stageId)}
              className={`p-4 flex items-center justify-between ${
                !isLocked ? 'cursor-pointer hover:bg-gray-800/50' : ''
              } transition-colors`}
            >
              <div className="flex items-center gap-4">
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                  isLocked
                    ? 'bg-gray-700'
                    : stage.status === 'completed'
                    ? 'bg-green-500'
                    : 'bg-gradient-to-br from-indigo-500 to-purple-500'
                }`}>
                  {isLocked ? (
                    <Lock className="w-6 h-6 text-gray-500" />
                  ) : stage.status === 'completed' ? (
                    <CheckCircle className="w-6 h-6 text-white" />
                  ) : (
                    <span className="text-white font-bold">{(stage.number || index) + 1}</span>
                  )}
                </div>
                <div>
                  <h4 className="font-semibold text-white">{stageName}</h4>
                  <p className="text-sm text-gray-400">{stage.packages.length} paket • {stage.description}</p>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <div className="text-right">
                  <div className="text-sm text-gray-400">{completedPackages}/{stage.packages.length}</div>
                  <div className="w-24 h-2 bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-green-400 to-emerald-500"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                </div>
                {!isLocked && (
                  <motion.div
                    animate={{ rotate: isExpanded ? 90 : 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    <ChevronRight className="w-5 h-5 text-gray-400" />
                  </motion.div>
                )}
              </div>
            </div>

            {/* Packages */}
            <AnimatePresence>
              {isExpanded && !isLocked && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.3 }}
                  className="border-t border-gray-700/50"
                >
                  <div className="p-4 grid gap-3">
                    {stage.packages.map((pkg) => {
                      const pkgType = pkg.type || pkg.package_type || 'learning';
                      const pkgTypeInfo = PACKAGE_TYPE_ICONS[pkgType] || PACKAGE_TYPE_ICONS.learning;
                      const pkgId = pkg.id || pkg.package_id || '';
                      const pkgName = pkg.title || pkg.name || 'Paket';
                      const isPackageLocked = pkg.status === 'locked';
                      const isPackageCompleted = pkg.status === 'passed' || pkg.status === 'completed';

                      return (
                        <motion.div
                          key={pkgId}
                          whileHover={!isPackageLocked ? { scale: 1.01, x: 4 } : {}}
                          onClick={() => !isPackageLocked && onSelectPackage(pkg)}
                          className={`p-4 rounded-xl border transition-all ${
                            isPackageLocked
                              ? 'border-gray-700 bg-gray-800/30 opacity-50 cursor-not-allowed'
                              : isPackageCompleted
                              ? 'border-green-500/50 bg-green-900/20 cursor-pointer'
                              : 'border-gray-700/50 bg-gray-800/50 cursor-pointer hover:border-purple-500/50'
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                              <div className={`w-10 h-10 rounded-lg flex items-center justify-center bg-gradient-to-br ${pkgTypeInfo.color} text-white`}>
                                {isPackageLocked ? <Lock className="w-5 h-5" /> : pkgTypeInfo.icon}
                              </div>
                              <div>
                                <h5 className="font-medium text-white">{pkgName}</h5>
                                <p className="text-xs text-gray-400">
                                  {pkg.content_blocks?.length || 0} içerik • {pkg.exams?.length || 0} sınav
                                </p>
                              </div>
                            </div>

                            <div className="flex items-center gap-3">
                              {(pkg.xp_total || pkg.xp_reward || 0) > 0 && (
                                <div className="flex items-center gap-1 text-amber-400 text-sm">
                                  <Star className="w-4 h-4" />
                                  <span>{pkg.xp_earned || 0}/{pkg.xp_total || pkg.xp_reward || 0}</span>
                                </div>
                              )}

                              {isPackageCompleted && (
                                <CheckCircle className="w-5 h-5 text-green-400" />
                              )}
                              
                              {!isPackageLocked && !isPackageCompleted && (
                                <Play className="w-5 h-5 text-purple-400" />
                              )}
                            </div>
                          </div>
                        </motion.div>
                      );
                    })}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        );
      })}
    </div>
  );
};

// ============================================================================
// PACKAGE VIEW COMPONENT
// ============================================================================

const PackageViewComponent: React.FC<{
  pkg: PackageV2;
  journeyId: string;
  onStartExam: (exam: ExamV2) => void;
  onBack: () => void;
  onPackageLoaded: (pkg: PackageV2) => void;
}> = ({ pkg, journeyId, onStartExam, onBack, onPackageLoaded }) => {
  const [activeTab, setActiveTab] = useState<'content' | 'exercises' | 'exams'>('content');
  const [loading, setLoading] = useState(false);
  const [currentPackage, setCurrentPackage] = useState(pkg);

  const pkgType = currentPackage.type || currentPackage.package_type || 'learning';
  const pkgTypeInfo = PACKAGE_TYPE_ICONS[pkgType] || PACKAGE_TYPE_ICONS.learning;
  const pkgName = currentPackage.title || currentPackage.name || 'Paket';

  // Package'ı başlat ve içerikleri yükle
  useEffect(() => {
    const loadPackage = async () => {
      if (currentPackage.content_blocks?.length === 0 && journeyId) {
        setLoading(true);
        const pkgId = currentPackage.id || currentPackage.package_id || '';
        const result = await startPackageV2(journeyId, pkgId);
        if (result.success && result.package) {
          setCurrentPackage(result.package);
          onPackageLoaded(result.package);
        }
        setLoading(false);
      }
    };
    loadPackage();
  }, [journeyId, currentPackage.id, currentPackage.package_id]);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto flex items-center justify-center py-20">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 text-purple-400 animate-spin mx-auto mb-4" />
          <p className="text-gray-400">İçerikler hazırlanıyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className={`p-6 rounded-2xl bg-gradient-to-r ${pkgTypeInfo.color}`}>
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-xl bg-white/20 flex items-center justify-center">
            {pkgTypeInfo.icon}
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">{pkgName}</h2>
            <p className="text-white/80">{currentPackage.description}</p>
          </div>
        </div>
        <div className="flex items-center gap-6 mt-4 text-white/70 text-sm">
          <span className="flex items-center gap-1">
            <BookOpen className="w-4 h-4" />
            {currentPackage.content_blocks?.length || 0} içerik
          </span>
          <span className="flex items-center gap-1">
            <Brain className="w-4 h-4" />
            {currentPackage.exercises?.length || 0} egzersiz
          </span>
          <span className="flex items-center gap-1">
            <FileText className="w-4 h-4" />
            {currentPackage.exams?.length || 0} sınav
          </span>
          <span className="flex items-center gap-1">
            <Zap className="w-4 h-4 text-amber-300" />
            {currentPackage.xp_total || currentPackage.xp_reward || 0} XP
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2">
        {[
          { id: 'content', label: 'İçerik', icon: <BookOpen className="w-4 h-4" /> },
          { id: 'exercises', label: 'Egzersizler', icon: <Brain className="w-4 h-4" /> },
          { id: 'exams', label: 'Sınavlar', icon: <FileText className="w-4 h-4" /> },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as typeof activeTab)}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl transition-all ${
              activeTab === tab.id
                ? 'bg-purple-500 text-white'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
            }`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="space-y-4">
        {activeTab === 'content' && (
          <>
            {(currentPackage.content_blocks || []).length === 0 ? (
              <div className="text-center py-12 text-gray-400">
                <BookOpen className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>Bu pakette henüz içerik yok</p>
              </div>
            ) : (
              currentPackage.content_blocks.map((block) => {
                const blockType = block.block_type || block.type || 'text';
                return (
                  <div
                    key={block.id}
                    className={`p-4 rounded-xl border transition-all ${
                      block.completed
                        ? 'border-green-500/50 bg-green-900/20'
                        : 'border-gray-700/50 bg-gray-800/50'
                    }`}
                  >
                    <div className="flex items-start gap-4">
                      <div className={`p-2 rounded-lg ${
                        blockType === 'video' ? 'bg-red-500/20 text-red-400' :
                        blockType === 'interactive' ? 'bg-green-500/20 text-green-400' :
                        blockType === 'formula_sheet' ? 'bg-purple-500/20 text-purple-400' :
                        blockType === 'example' ? 'bg-orange-500/20 text-orange-400' :
                        blockType === 'summary' ? 'bg-cyan-500/20 text-cyan-400' :
                        'bg-blue-500/20 text-blue-400'
                      }`}>
                        {blockType === 'video' ? <Video className="w-5 h-5" /> :
                         blockType === 'interactive' ? <Target className="w-5 h-5" /> :
                         blockType === 'formula_sheet' ? <BookOpen className="w-5 h-5" /> :
                         <FileText className="w-5 h-5" />}
                      </div>
                      <div className="flex-1">
                        <h4 className="font-medium text-white">{block.title}</h4>
                        <p className="text-sm text-gray-400 mt-1 whitespace-pre-wrap">{block.content}</p>
                      </div>
                      {block.completed && (
                        <CheckCircle className="w-5 h-5 text-green-400" />
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </>
        )}

        {activeTab === 'exercises' && (
          <>
            {(currentPackage.exercises || []).length === 0 ? (
              <div className="text-center py-12 text-gray-400">
                <Brain className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>Bu pakette henüz egzersiz yok</p>
              </div>
            ) : (
              currentPackage.exercises.map((exercise) => (
                <div
                  key={exercise.id}
                  className={`p-4 rounded-xl border transition-all ${
                    exercise.completed
                      ? 'border-green-500/50 bg-green-900/20'
                      : 'border-gray-700/50 bg-gray-800/50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-lg bg-purple-500/20 text-purple-400">
                        <Brain className="w-5 h-5" />
                      </div>
                      <div>
                        <h4 className="font-medium text-white">{exercise.title}</h4>
                        <p className="text-sm text-gray-400">{exercise.exercise_type || exercise.type}</p>
                      </div>
                    </div>
                    {exercise.completed ? (
                      <div className="flex items-center gap-2">
                        <span className="text-green-400">{exercise.score}%</span>
                        <CheckCircle className="w-5 h-5 text-green-400" />
                      </div>
                    ) : (
                      <button className="px-4 py-2 rounded-lg bg-purple-500 text-white text-sm hover:bg-purple-600">
                        Başla
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}
          </>
        )}

        {activeTab === 'exams' && (
          <>
            {(currentPackage.exams || []).length === 0 ? (
              <div className="text-center py-12 text-gray-400">
                <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>Bu pakette henüz sınav yok</p>
              </div>
            ) : (
              currentPackage.exams.map((exam) => {
                const examType = exam.type || exam.exam_type || 'multiple_choice';
                return (
                  <div
                    key={exam.id}
                    className={`p-4 rounded-xl border transition-all ${
                      exam.status === 'completed'
                        ? 'border-green-500/50 bg-green-900/20'
                        : exam.status === 'failed'
                        ? 'border-red-500/50 bg-red-900/20'
                        : 'border-gray-700/50 bg-gray-800/50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${
                          examType === 'feynman' ? 'bg-pink-500/20 text-pink-400' :
                          examType === 'problem_solving' ? 'bg-orange-500/20 text-orange-400' :
                          'bg-blue-500/20 text-blue-400'
                        }`}>
                          {examType === 'feynman' ? <Mic className="w-5 h-5" /> :
                           examType === 'problem_solving' ? <Target className="w-5 h-5" /> :
                           <FileText className="w-5 h-5" />}
                        </div>
                        <div>
                          <h4 className="font-medium text-white">{exam.title}</h4>
                          <p className="text-sm text-gray-400">
                            {examType === 'feynman' ? 'Feynman Tekniği' :
                             examType === 'multiple_choice' ? 'Çoktan Seçmeli' :
                             examType} • {exam.time_limit_minutes} dk
                          </p>
                        </div>
                      </div>
                      
                      {exam.status === 'completed' ? (
                        <div className="flex items-center gap-2">
                          <span className="text-green-400 font-medium">{exam.score}%</span>
                          <CheckCircle className="w-5 h-5 text-green-400" />
                        </div>
                      ) : exam.status === 'failed' ? (
                        <div className="flex items-center gap-2">
                          <span className="text-red-400 font-medium">{exam.score}%</span>
                          <X className="w-5 h-5 text-red-400" />
                        </div>
                      ) : (
                        <button
                          onClick={() => onStartExam(exam)}
                          className="px-4 py-2 rounded-lg bg-gradient-to-r from-purple-500 to-indigo-500 text-white text-sm hover:opacity-90 flex items-center gap-2"
                        >
                          <Play className="w-4 h-4" />
                          Sınava Başla
                        </button>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </>
        )}
      </div>
    </div>
  );
};

// ============================================================================
// EXAM VIEW COMPONENT (FEYNMAN)
// ============================================================================

const ExamViewComponent: React.FC<{
  exam: ExamV2;
  journeyId: string;
  onSubmit: (result: { score: number; passed: boolean }) => void;
  onBack: () => void;
}> = ({ exam, journeyId, onSubmit, onBack }) => {
  const [explanation, setExplanation] = useState('');
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [timeRemaining, setTimeRemaining] = useState((exam.time_limit_minutes || 30) * 60);
  const [result, setResult] = useState<{
    score: number;
    passed: boolean;
    feedback?: {
      accuracy: number;
      depth: number;
      clarity: number;
      examples: number;
      completeness: number;
      overall_feedback: string;
    };
  } | null>(null);

  const examType = exam.type || exam.exam_type || 'multiple_choice';
  const examTopic = exam.topic || exam.title || '';

  // Timer
  useEffect(() => {
    if (timeRemaining <= 0 || result) return;
    
    const timer = setInterval(() => {
      setTimeRemaining(prev => {
        if (prev <= 1) {
          clearInterval(timer);
          handleSubmit();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [timeRemaining, result]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    
    const res = await submitExamV2(journeyId, exam.id, {
      exam_type: examType,
      explanation: examType === 'feynman' ? explanation : undefined,
      answers: examType === 'multiple_choice' ? answers : undefined,
      time_taken_seconds: ((exam.time_limit_minutes || 30) * 60) - timeRemaining
    });

    if (res.success) {
      setResult({
        score: res.score || 0,
        passed: res.passed || false,
        feedback: res.feedback
      });
    }
    
    setSubmitting(false);
  };

  if (result) {
    return (
      <div className="max-w-2xl mx-auto space-y-6">
        <div className={`p-8 rounded-2xl text-center ${
          result.passed
            ? 'bg-gradient-to-br from-green-900/50 to-emerald-900/50 border border-green-500/50'
            : 'bg-gradient-to-br from-red-900/50 to-orange-900/50 border border-red-500/50'
        }`}>
          <div className={`w-20 h-20 mx-auto mb-4 rounded-full flex items-center justify-center ${
            result.passed ? 'bg-green-500' : 'bg-red-500'
          }`}>
            {result.passed ? <Trophy className="w-10 h-10 text-white" /> : <AlertCircle className="w-10 h-10 text-white" />}
          </div>
          <h2 className="text-2xl font-bold text-white mb-2">
            {result.passed ? 'Tebrikler! 🎉' : 'Tekrar Dene'}
          </h2>
          <div className="text-4xl font-bold text-white mb-4">{result.score}%</div>
          <p className="text-gray-300">
            {result.passed ? 'Sınavı başarıyla geçtin!' : `Geçme notu: ${exam.passing_score}%`}
          </p>
        </div>

        {/* Feynman Feedback */}
        {result.feedback && (
          <div className="p-6 rounded-2xl bg-gray-800/50 border border-gray-700/50 space-y-4">
            <h3 className="font-semibold text-white">Değerlendirme Detayları</h3>
            
            {['accuracy', 'depth', 'clarity', 'examples', 'completeness'].map((criterion) => {
              const value = result.feedback?.[criterion as keyof typeof result.feedback] as number;
              const labels: Record<string, string> = {
                accuracy: 'Doğruluk',
                depth: 'Derinlik',
                clarity: 'Açıklık',
                examples: 'Örnekler',
                completeness: 'Bütünlük'
              };
              
              return (
                <div key={criterion}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-400">{labels[criterion]}</span>
                    <span className="text-white">{value}%</span>
                  </div>
                  <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        value >= 80 ? 'bg-green-500' : value >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${value}%` }}
                    />
                  </div>
                </div>
              );
            })}

            {result.feedback.overall_feedback && (
              <div className="mt-4 p-4 rounded-xl bg-gray-900/50 border border-gray-600/50">
                <h4 className="text-sm font-medium text-gray-400 mb-2">Genel Değerlendirme</h4>
                <p className="text-gray-300">{result.feedback.overall_feedback}</p>
              </div>
            )}
          </div>
        )}

        <button
          onClick={() => onSubmit(result)}
          className="w-full py-3 rounded-xl bg-gradient-to-r from-purple-500 to-indigo-500 text-white font-medium"
        >
          Devam Et
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">{exam.title}</h2>
          <p className="text-gray-400">{exam.description}</p>
        </div>
        <div className={`px-4 py-2 rounded-xl font-mono text-lg ${
          timeRemaining < 60 ? 'bg-red-500/20 text-red-400' : 'bg-gray-800 text-white'
        }`}>
          <Timer className="w-5 h-5 inline mr-2" />
          {formatTime(timeRemaining)}
        </div>
      </div>

      {/* Feynman Exam */}
      {examType === 'feynman' && (
        <div className="space-y-4">
          <div className="p-6 rounded-2xl bg-gradient-to-br from-pink-900/30 to-rose-900/30 border border-pink-500/30">
            <div className="flex items-center gap-3 mb-4">
              <Mic className="w-8 h-8 text-pink-400" />
              <div>
                <h3 className="font-semibold text-white">Feynman Tekniği</h3>
                <p className="text-sm text-gray-400">Bu konuyu bir çocuğa anlatır gibi açıkla</p>
              </div>
            </div>
            <div className="p-4 rounded-xl bg-gray-900/50 border border-gray-700/50">
              <p className="text-gray-300 font-medium">{examTopic}</p>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Açıklaman
            </label>
            <textarea
              value={explanation}
              onChange={(e) => setExplanation(e.target.value)}
              rows={10}
              placeholder="Bu konuyu basit kelimelerle, örneklerle açıkla..."
              className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-white resize-none focus:border-pink-500 focus:outline-none"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-2">
              <span>Minimum 100 karakter</span>
              <span>{explanation.length} karakter</span>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-amber-900/20 border border-amber-500/30">
            <h4 className="font-medium text-amber-300 mb-2">💡 İpuçları</h4>
            <ul className="text-sm text-amber-200/80 space-y-1">
              <li>• Basit kelimeler kullan</li>
              <li>• Günlük hayattan örnekler ver</li>
              <li>• Karmaşık terimleri açıkla</li>
              <li>• Benzetmeler yap</li>
            </ul>
          </div>
        </div>
      )}

      {/* Multiple Choice Exam */}
      {examType === 'multiple_choice' && exam.questions && (
        <div className="space-y-6">
          {exam.questions.map((q, index) => (
            <div key={q.id} className="p-4 rounded-xl bg-gray-800/50 border border-gray-700/50">
              <p className="font-medium text-white mb-4">
                {index + 1}. {q.question}
              </p>
              <div className="space-y-2">
                {q.options?.map((option, optIndex) => (
                  <button
                    key={optIndex}
                    onClick={() => setAnswers({ ...answers, [q.id]: option })}
                    className={`w-full p-3 rounded-lg text-left transition-all ${
                      answers[q.id] === option
                        ? 'bg-purple-500 text-white'
                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    }`}
                  >
                    {String.fromCharCode(65 + optIndex)}. {option}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Submit Button */}
      <button
        onClick={handleSubmit}
        disabled={submitting || (examType === 'feynman' && explanation.length < 100)}
        className={`w-full py-4 rounded-xl font-medium flex items-center justify-center gap-2 ${
          submitting || (examType === 'feynman' && explanation.length < 100)
            ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
            : 'bg-gradient-to-r from-green-500 to-emerald-500 text-white hover:opacity-90'
        }`}
      >
        {submitting ? (
          <>
            <RefreshCw className="w-5 h-5 animate-spin" />
            Değerlendiriliyor...
          </>
        ) : (
          <>
            <Send className="w-5 h-5" />
            Gönder
          </>
        )}
      </button>
    </div>
  );
};

// ============================================================================
// CERTIFICATE VIEW COMPONENT
// ============================================================================

const CertificateViewComponent: React.FC<{
  certificate: Certificate;
  onClose: () => void;
}> = ({ certificate, onClose }) => {
  const gradeColors: Record<string, string> = {
    'platinum': 'from-purple-400 via-pink-400 to-purple-400',
    'gold': 'from-yellow-400 via-amber-300 to-yellow-400',
    'silver': 'from-gray-300 via-gray-100 to-gray-300',
    'bronze': 'from-orange-400 via-orange-300 to-orange-400',
  };

  const certCode = certificate.verification_code || certificate.certificate_code || '';
  const certTitle = certificate.journey_title || certificate.title || '';
  const certDate = certificate.completion_date || certificate.issued_at || new Date().toISOString();
  const certXP = certificate.total_xp || certificate.total_xp_earned || 0;

  return (
    <div className="max-w-2xl mx-auto">
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className={`p-8 rounded-3xl bg-gradient-to-br ${gradeColors[certificate.grade] || gradeColors.gold} shadow-2xl`}
      >
        <div className="bg-white rounded-2xl p-8 text-center">
          <div className="text-6xl mb-4">🎓</div>
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Başarı Sertifikası</h1>
          <p className="text-gray-600 mb-6">Bu sertifika</p>
          
          <div className="text-2xl font-bold text-gray-800 mb-2">{certificate.user_name}</div>
          <p className="text-gray-600 mb-6">adına aşağıdaki yolculuğu başarıyla tamamladığı için verilmiştir:</p>
          
          <div className="p-4 rounded-xl bg-gradient-to-r from-purple-100 to-indigo-100 mb-6">
            <div className="text-xl font-semibold text-purple-800">{certTitle}</div>
          </div>

          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="p-3 rounded-lg bg-gray-50">
              <div className="text-sm text-gray-500">Derece</div>
              <div className="font-bold text-gray-800 capitalize">{certificate.grade}</div>
            </div>
            <div className="p-3 rounded-lg bg-gray-50">
              <div className="text-sm text-gray-500">Toplam XP</div>
              <div className="font-bold text-gray-800">{certXP.toLocaleString()}</div>
            </div>
          </div>

          <div className="text-xs text-gray-400">
            <div>Sertifika Kodu: {certCode}</div>
            <div>Tarih: {new Date(certDate).toLocaleDateString('tr-TR')}</div>
          </div>
        </div>
      </motion.div>

      <div className="flex justify-center gap-4 mt-6">
        <button
          onClick={onClose}
          className="px-6 py-3 rounded-xl bg-gradient-to-r from-purple-500 to-indigo-500 text-white font-medium"
        >
          Tamam
        </button>
      </div>
    </div>
  );
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function FullMetaPanel() {
  const [view, setView] = useState<ViewState>('list');
  const [journeys, setJourneys] = useState<JourneyV2[]>([]);
  const [selectedJourney, setSelectedJourney] = useState<JourneyV2 | null>(null);
  const [selectedPackage, setSelectedPackage] = useState<PackageV2 | null>(null);
  const [selectedExam, setSelectedExam] = useState<ExamV2 | null>(null);
  const [loading, setLoading] = useState(true);
  const [isCreatingJourney, setIsCreatingJourney] = useState(false);
  const [thinkingSteps, setThinkingSteps] = useState<AIThinkingStep[]>([]);
  const [createdCurriculum, setCreatedCurriculum] = useState<JourneyV2 | null>(null);
  const [certificate, setCertificate] = useState<Certificate | null>(null);
  const [createError, setCreateError] = useState<string | null>(null);

  useEffect(() => {
    loadJourneys();
  }, []);

  const loadJourneys = async () => {
    setLoading(true);
    const data = await fetchJourneys();
    setJourneys(data);
    setLoading(false);
  };

  const handleWizardComplete = async (goal: LearningGoal) => {
    setView('thinking');
    setThinkingSteps([]);
    setCreatedCurriculum(null);
    setCreateError(null);
    setIsCreatingJourney(true);

    try {
      const result = await createJourneyV2(goal);
      
      if (result.success && result.curriculum) {
        if (result.thinking_steps) {
          setThinkingSteps(result.thinking_steps);
        }
        setCreatedCurriculum(result.curriculum);
      } else {
        console.error('Journey creation failed:', result.error);
        setCreateError(result.error || 'Yolculuk oluşturulurken bir hata oluştu');
      }
    } catch (error) {
      console.error('Journey creation error:', error);
      setCreateError('Bağlantı hatası oluştu');
    } finally {
      setIsCreatingJourney(false);
    }
  };

  const handleSelectJourney = async (journey: JourneyV2) => {
    setLoading(true);
    const fullJourney = await fetchJourneyMap(journey.journey_id);
    if (fullJourney) {
      setSelectedJourney(fullJourney);
      setView('journey');
    }
    setLoading(false);
  };

  const handleSelectPackage = (pkg: PackageV2) => {
    if (pkg.status === 'locked') return;
    setSelectedPackage(pkg);
    setView('package');
  };

  const handleStartExam = (exam: ExamV2) => {
    setSelectedExam(exam);
    setView('exam');
  };

  const handleExamComplete = () => {
    setSelectedExam(null);
    setView('package');
  };

  const handleBack = () => {
    switch (view) {
      case 'wizard':
      case 'thinking':
        setView('list');
        break;
      case 'journey':
        setSelectedJourney(null);
        setView('list');
        break;
      case 'package':
        setSelectedPackage(null);
        setView('journey');
        break;
      case 'exam':
        setSelectedExam(null);
        setView('package');
        break;
      case 'certificate':
        setCertificate(null);
        setView('list');
        loadJourneys();
        break;
      default:
        setView('list');
    }
  };

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-gray-900 via-gray-900 to-gray-800">
      {/* Header */}
      <div className="p-6 border-b border-gray-700/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {view !== 'list' && (
              <button
                onClick={handleBack}
                className="p-2 rounded-xl bg-gray-800 hover:bg-gray-700 transition-colors"
              >
                <ArrowLeft className="w-5 h-5 text-gray-400" />
              </button>
            )}
            <div>
              <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                <GraduationCap className="w-7 h-7 text-purple-400" />
                Full Meta - AI ile Öğren
              </h1>
              <p className="text-sm text-gray-400">
                {view === 'list' && 'Kişiselleştirilmiş öğrenme yolculukları'}
                {view === 'wizard' && 'Yeni öğrenme yolculuğu oluştur'}
                {view === 'thinking' && 'AI müfredatı hazırlıyor...'}
                {view === 'journey' && selectedJourney?.title}
                {view === 'package' && (selectedPackage?.title || selectedPackage?.name)}
                {view === 'exam' && selectedExam?.title}
                {view === 'certificate' && 'Tebrikler! 🎉'}
              </p>
            </div>
          </div>
          
          {view === 'list' && (
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setView('wizard')}
              className="px-4 py-2 rounded-xl bg-gradient-to-r from-purple-500 to-indigo-500 text-white font-medium flex items-center gap-2"
            >
              <Plus className="w-5 h-5" />
              Yeni Yolculuk
            </motion.button>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6">
        {loading && view === 'list' ? (
          <div className="flex items-center justify-center h-full">
            <RefreshCw className="w-8 h-8 text-purple-400 animate-spin" />
          </div>
        ) : (
          <AnimatePresence mode="wait">
            {/* Journey List */}
            {view === 'list' && (
              <motion.div
                key="list"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
              >
                {journeys.length === 0 ? (
                  <div className="text-center py-16">
                    <GraduationCap className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                    <h2 className="text-xl font-semibold text-white mb-2">
                      Henüz bir öğrenme yolculuğun yok
                    </h2>
                    <p className="text-gray-400 mb-6">
                      Full Meta ile kişiselleştirilmiş bir yolculuk oluştur
                    </p>
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => setView('wizard')}
                      className="px-6 py-3 rounded-xl bg-gradient-to-r from-purple-500 to-indigo-500 text-white font-medium inline-flex items-center gap-2"
                    >
                      <Sparkles className="w-5 h-5" />
                      İlk Yolculuğunu Başlat
                    </motion.button>
                  </div>
                ) : (
                  <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {journeys.map((j) => (
                      <JourneyCard key={j.journey_id} journey={j} onSelect={handleSelectJourney} />
                    ))}
                  </div>
                )}
              </motion.div>
            )}

            {/* Wizard */}
            {view === 'wizard' && (
              <motion.div
                key="wizard"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
              >
                <JourneyWizard
                  onComplete={handleWizardComplete}
                  onCancel={() => setView('list')}
                />
              </motion.div>
            )}

            {/* AI Thinking */}
            {view === 'thinking' && (
              <motion.div
                key="thinking"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
              >
                {createError ? (
                  <div className="max-w-xl mx-auto p-6 rounded-xl bg-red-900/30 border border-red-500/50 text-center">
                    <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-white mb-2">Bir Hata Oluştu</h3>
                    <p className="text-gray-300 mb-4">{createError}</p>
                    <button
                      onClick={() => { setView('list'); setCreateError(null); }}
                      className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-white transition-colors"
                    >
                      Geri Dön
                    </button>
                  </div>
                ) : (
                  <AIThinkingViewComponent
                    steps={thinkingSteps}
                    curriculum={createdCurriculum}
                    isLoading={isCreatingJourney}
                    onComplete={() => {
                      if (createdCurriculum) {
                        setSelectedJourney(createdCurriculum);
                        setView('journey');
                        loadJourneys();
                      }
                    }}
                  />
                )}
              </motion.div>
            )}

            {/* Stage Map */}
            {view === 'journey' && selectedJourney && (
              <motion.div
                key="journey"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-6"
              >
                {selectedJourney.progress && (
                  <div className="grid md:grid-cols-3 gap-4">
                    <XPIndicator
                      xp={selectedJourney.progress.xp_earned}
                      level={selectedJourney.progress.level}
                    />
                    <StreakIndicator days={selectedJourney.progress.streak_days} />
                    <div className="bg-gradient-to-r from-green-900/50 to-emerald-900/50 rounded-xl p-4 border border-green-500/30">
                      <div className="text-2xl font-bold text-green-400">
                        {((selectedJourney.progress.completed_packages / Math.max(selectedJourney.progress.total_packages, 1)) * 100).toFixed(1)}%
                      </div>
                      <div className="text-sm text-green-200">Genel İlerleme</div>
                    </div>
                  </div>
                )}

                <StageMapComponent
                  stages={selectedJourney.stages || []}
                  onSelectPackage={handleSelectPackage}
                />
              </motion.div>
            )}

            {/* Package View */}
            {view === 'package' && selectedPackage && selectedJourney && (
              <motion.div
                key="package"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
              >
                <PackageViewComponent
                  pkg={selectedPackage}
                  journeyId={selectedJourney.journey_id}
                  onStartExam={handleStartExam}
                  onBack={handleBack}
                  onPackageLoaded={(pkg) => setSelectedPackage(pkg)}
                />
              </motion.div>
            )}

            {/* Exam View */}
            {view === 'exam' && selectedExam && selectedJourney && (
              <motion.div
                key="exam"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
              >
                <ExamViewComponent
                  exam={selectedExam}
                  journeyId={selectedJourney.journey_id}
                  onSubmit={handleExamComplete}
                  onBack={handleBack}
                />
              </motion.div>
            )}

            {/* Certificate */}
            {view === 'certificate' && certificate && (
              <motion.div
                key="certificate"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
              >
                <CertificateViewComponent
                  certificate={certificate}
                  onClose={() => {
                    setCertificate(null);
                    setView('list');
                    loadJourneys();
                  }}
                />
              </motion.div>
            )}
          </AnimatePresence>
        )}
      </div>
    </div>
  );
}

