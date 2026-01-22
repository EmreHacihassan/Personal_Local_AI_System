'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Target,
  Brain,
  Clock,
  Calendar,
  BookOpen,
  Zap,
  ChevronRight,
  ChevronLeft,
  Sparkles,
  GraduationCap,
  Trophy,
  Star,
  Check,
  AlertCircle
} from 'lucide-react';

// ==================== TYPES ====================

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

interface JourneyWizardProps {
  onComplete: (goal: LearningGoal) => void;
  onCancel: () => void;
}

// ==================== CONSTANTS ====================

const SUBJECTS = [
  { id: 'matematik', name: 'Matematik', icon: '📐', color: '#3B82F6' },
  { id: 'fizik', name: 'Fizik', icon: '⚛️', color: '#8B5CF6' },
  { id: 'kimya', name: 'Kimya', icon: '🧪', color: '#10B981' },
  { id: 'biyoloji', name: 'Biyoloji', icon: '🧬', color: '#22C55E' },
  { id: 'türkçe', name: 'Türkçe', icon: '📚', color: '#EF4444' },
  { id: 'tarih', name: 'Tarih', icon: '📜', color: '#F59E0B' },
  { id: 'coğrafya', name: 'Coğrafya', icon: '🌍', color: '#06B6D4' },
  { id: 'programlama', name: 'Programlama', icon: '💻', color: '#EC4899' },
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

const MATH_TOPICS = [
  'Temel Matematik', 'Cebir', 'Fonksiyonlar', 'Trigonometri',
  'Üstel ve Logaritmik Fonksiyonlar', 'Diziler', 'Limit ve Süreklilik',
  'Türev', 'İntegral', 'Analitik Geometri', 'Geometri', 'Olasılık ve İstatistik'
];

// ==================== STEP COMPONENTS ====================

const StepIndicator: React.FC<{ currentStep: number; totalSteps: number }> = ({ currentStep, totalSteps }) => {
  return (
    <div className="flex items-center justify-center gap-2 mb-8">
      {Array.from({ length: totalSteps }).map((_, index) => (
        <motion.div
          key={index}
          className={`h-2 rounded-full transition-all duration-300 ${
            index <= currentStep 
              ? 'bg-gradient-to-r from-purple-500 to-indigo-600' 
              : 'bg-gray-200 dark:bg-gray-700'
          }`}
          initial={{ width: 24 }}
          animate={{ width: index === currentStep ? 48 : 24 }}
        />
      ))}
    </div>
  );
};

// Step 1: Konu Seçimi
const SubjectStep: React.FC<{
  selected: string;
  onSelect: (subject: string) => void;
}> = ({ selected, onSelect }) => {
  return (
    <div className="space-y-6">
      <div className="text-center">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          className="inline-flex p-4 bg-gradient-to-r from-purple-500/20 to-indigo-500/20 rounded-full mb-4"
        >
          <BookOpen className="w-8 h-8 text-purple-500" />
        </motion.div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          Ne Öğrenmek İstiyorsun?
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Hangi konuda ustalaşmak istediğini seç
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {SUBJECTS.map((subject) => (
          <motion.button
            key={subject.id}
            onClick={() => onSelect(subject.id)}
            className={`p-4 rounded-xl border-2 transition-all ${
              selected === subject.id
                ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20'
                : 'border-gray-200 dark:border-gray-700 hover:border-purple-300'
            }`}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <div className="text-3xl mb-2">{subject.icon}</div>
            <div className="font-semibold text-gray-900 dark:text-white">{subject.name}</div>
            {selected === subject.id && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="mt-2"
              >
                <Check className="w-5 h-5 text-purple-500 mx-auto" />
              </motion.div>
            )}
          </motion.button>
        ))}
      </div>
    </div>
  );
};

// Step 2: Hedef Belirleme
const GoalStep: React.FC<{
  title: string;
  target: string;
  motivation: string;
  onChange: (field: string, value: string) => void;
}> = ({ title, target, motivation, onChange }) => {
  return (
    <div className="space-y-6">
      <div className="text-center">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          className="inline-flex p-4 bg-gradient-to-r from-amber-500/20 to-orange-500/20 rounded-full mb-4"
        >
          <Target className="w-8 h-8 text-amber-500" />
        </motion.div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          Hedefin Ne?
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Net bir hedef belirle - bu yolculuğun pusulası olacak
        </p>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            📌 Çalışma Planı Başlığı
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => onChange('title', e.target.value)}
            placeholder="Örn: AYT Matematik Çalışma Planı"
            className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-xl 
                       bg-white dark:bg-gray-800 text-gray-900 dark:text-white
                       focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            🎯 Ana Hedefe
          </label>
          <input
            type="text"
            value={target}
            onChange={(e) => onChange('target', e.target.value)}
            placeholder="Örn: AYT'de 35+ net yapmak"
            className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-xl 
                       bg-white dark:bg-gray-800 text-gray-900 dark:text-white
                       focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            💪 Motivasyonun
          </label>
          <textarea
            value={motivation}
            onChange={(e) => onChange('motivation', e.target.value)}
            placeholder="Bu hedefi neden istiyorsun? Seni ne motive ediyor?"
            rows={3}
            className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-xl 
                       bg-white dark:bg-gray-800 text-gray-900 dark:text-white
                       focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
          />
        </div>
      </div>
    </div>
  );
};

// Step 3: Ön Bilgi & Zayıf Alanlar
const KnowledgeStep: React.FC<{
  priorKnowledge: string;
  weakAreas: string[];
  focusAreas: string[];
  subject: string;
  onChange: (field: string, value: any) => void;
}> = ({ priorKnowledge, weakAreas, focusAreas, subject, onChange }) => {
  const topics = subject === 'matematik' ? MATH_TOPICS : [];

  const toggleWeakArea = (topic: string) => {
    if (weakAreas.includes(topic)) {
      onChange('weakAreas', weakAreas.filter(t => t !== topic));
    } else {
      onChange('weakAreas', [...weakAreas, topic]);
    }
  };

  const toggleFocusArea = (topic: string) => {
    if (focusAreas.includes(topic)) {
      onChange('focusAreas', focusAreas.filter(t => t !== topic));
    } else {
      onChange('focusAreas', [...focusAreas, topic]);
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          className="inline-flex p-4 bg-gradient-to-r from-blue-500/20 to-cyan-500/20 rounded-full mb-4"
        >
          <Brain className="w-8 h-8 text-blue-500" />
        </motion.div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          Nereden Başlıyorsun?
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Ön bilgini ve zayıf yönlerini paylaş - sana özel plan oluşturalım
        </p>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            📚 Ön Bilgi Seviyen
          </label>
          <select
            value={priorKnowledge}
            onChange={(e) => onChange('priorKnowledge', e.target.value)}
            className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-xl 
                       bg-white dark:bg-gray-800 text-gray-900 dark:text-white
                       focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          >
            <option value="">Seç...</option>
            <option value="beginner">Başlangıç - Konuları yeni öğreniyorum</option>
            <option value="intermediate">Orta - Temel bilgilerim var</option>
            <option value="advanced">İleri - Çoğu konuya hakimim</option>
            <option value="refresher">Tazeleme - Bildiklerimi pekiştirmek istiyorum</option>
          </select>
        </div>

        {topics.length > 0 && (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                ⚠️ Zayıf Olduğun Konular
                <span className="text-gray-500 text-xs ml-2">(Bunlara daha fazla zaman ayıracağız)</span>
              </label>
              <div className="flex flex-wrap gap-2">
                {topics.map(topic => (
                  <button
                    key={`weak-${topic}`}
                    onClick={() => toggleWeakArea(topic)}
                    className={`px-3 py-1.5 rounded-full text-sm transition-all ${
                      weakAreas.includes(topic)
                        ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400 border-2 border-red-500'
                        : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400 border-2 border-transparent hover:border-red-300'
                    }`}
                  >
                    {topic}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                ⭐ Odaklanmak İstediğin Konular
                <span className="text-gray-500 text-xs ml-2">(Özel ilgi alanların)</span>
              </label>
              <div className="flex flex-wrap gap-2">
                {topics.map(topic => (
                  <button
                    key={`focus-${topic}`}
                    onClick={() => toggleFocusArea(topic)}
                    className={`px-3 py-1.5 rounded-full text-sm transition-all ${
                      focusAreas.includes(topic)
                        ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 border-2 border-green-500'
                        : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400 border-2 border-transparent hover:border-green-300'
                    }`}
                  >
                    {topic}
                  </button>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

// Step 4: Zaman Planı
const TimeStep: React.FC<{
  dailyHours: number;
  deadline: string;
  onChange: (field: string, value: any) => void;
}> = ({ dailyHours, deadline, onChange }) => {
  return (
    <div className="space-y-6">
      <div className="text-center">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          className="inline-flex p-4 bg-gradient-to-r from-green-500/20 to-emerald-500/20 rounded-full mb-4"
        >
          <Clock className="w-8 h-8 text-green-500" />
        </motion.div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          Zaman Planın
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Günlük ne kadar zaman ayırabilirsin?
        </p>
      </div>

      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">
            ⏰ Günlük Çalışma Süresi: <span className="text-purple-500 font-bold">{dailyHours} saat</span>
          </label>
          <input
            type="range"
            min="0.5"
            max="8"
            step="0.5"
            value={dailyHours}
            onChange={(e) => onChange('dailyHours', parseFloat(e.target.value))}
            className="w-full h-3 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer
                       accent-purple-500"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>30 dk</span>
            <span>4 saat</span>
            <span>8 saat</span>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            📅 Hedef Tarih (Opsiyonel)
          </label>
          <input
            type="date"
            value={deadline}
            onChange={(e) => onChange('deadline', e.target.value)}
            min={new Date().toISOString().split('T')[0]}
            className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-xl 
                       bg-white dark:bg-gray-800 text-gray-900 dark:text-white
                       focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
          <p className="text-sm text-gray-500 mt-1">
            Örn: Sınav tarihi, proje teslimi vb.
          </p>
        </div>

        {dailyHours > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-4 bg-gradient-to-r from-purple-50 to-indigo-50 dark:from-purple-900/20 dark:to-indigo-900/20 rounded-xl"
          >
            <div className="flex items-center gap-3">
              <Sparkles className="w-5 h-5 text-purple-500" />
              <div>
                <div className="font-medium text-gray-900 dark:text-white">Tahmini Süre</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  Günde {dailyHours} saat ile yaklaşık {Math.ceil(100 / dailyHours)} günde tamamlayabilirsin
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
};

// Step 5: Tercihler
const PreferencesStep: React.FC<{
  contentPrefs: string[];
  examPrefs: string[];
  onChange: (field: string, value: string[]) => void;
}> = ({ contentPrefs, examPrefs, onChange }) => {
  const toggleContent = (id: string) => {
    if (contentPrefs.includes(id)) {
      onChange('contentPrefs', contentPrefs.filter(c => c !== id));
    } else {
      onChange('contentPrefs', [...contentPrefs, id]);
    }
  };

  const toggleExam = (id: string) => {
    if (examPrefs.includes(id)) {
      onChange('examPrefs', examPrefs.filter(e => e !== id));
    } else {
      onChange('examPrefs', [...examPrefs, id]);
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          className="inline-flex p-4 bg-gradient-to-r from-pink-500/20 to-rose-500/20 rounded-full mb-4"
        >
          <Zap className="w-8 h-8 text-pink-500" />
        </motion.div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          Öğrenme Tercihlerin
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Sana en uygun içerik ve sınav türlerini seç
        </p>
      </div>

      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            📚 İçerik Türleri
          </label>
          <div className="grid grid-cols-2 gap-3">
            {CONTENT_TYPES.map(type => (
              <button
                key={type.id}
                onClick={() => toggleContent(type.id)}
                className={`p-3 rounded-xl border-2 text-left transition-all ${
                  contentPrefs.includes(type.id)
                    ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:border-purple-300'
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className="text-xl">{type.icon}</span>
                  <span className="font-medium text-gray-900 dark:text-white">{type.name}</span>
                </div>
                <div className="text-xs text-gray-500 mt-1">{type.desc}</div>
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            📝 Sınav Türleri
          </label>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {EXAM_TYPES.map(type => (
              <button
                key={type.id}
                onClick={() => toggleExam(type.id)}
                className={`p-3 rounded-xl border-2 text-left transition-all ${
                  examPrefs.includes(type.id)
                    ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:border-indigo-300'
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className="text-xl">{type.icon}</span>
                  <span className="font-medium text-gray-900 dark:text-white text-sm">{type.name}</span>
                </div>
                <div className="text-xs text-gray-500 mt-1">{type.desc}</div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// Step 6: Özet
const SummaryStep: React.FC<{
  goal: LearningGoal;
}> = ({ goal }) => {
  const subject = SUBJECTS.find(s => s.id === goal.subject);

  return (
    <div className="space-y-6">
      <div className="text-center">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1, rotate: [0, 10, -10, 0] }}
          transition={{ duration: 0.5 }}
          className="inline-flex p-4 bg-gradient-to-r from-yellow-500/20 to-amber-500/20 rounded-full mb-4"
        >
          <Trophy className="w-8 h-8 text-yellow-500" />
        </motion.div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          Hazırsın! 🎉
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Öğrenme yolculuğun için her şey hazır
        </p>
      </div>

      <div className="bg-gradient-to-r from-purple-50 to-indigo-50 dark:from-purple-900/20 dark:to-indigo-900/20 rounded-2xl p-6 space-y-4">
        <div className="flex items-center gap-4">
          <div className="text-4xl">{subject?.icon}</div>
          <div>
            <h3 className="text-xl font-bold text-gray-900 dark:text-white">{goal.title}</h3>
            <p className="text-gray-600 dark:text-gray-400">{goal.target_outcome}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="text-center p-3 bg-white/50 dark:bg-gray-800/50 rounded-xl">
            <Clock className="w-5 h-5 text-purple-500 mx-auto mb-1" />
            <div className="text-sm text-gray-500">Günlük</div>
            <div className="font-bold text-gray-900 dark:text-white">{goal.daily_hours} saat</div>
          </div>
          <div className="text-center p-3 bg-white/50 dark:bg-gray-800/50 rounded-xl">
            <Star className="w-5 h-5 text-amber-500 mx-auto mb-1" />
            <div className="text-sm text-gray-500">Zayıf Alanlar</div>
            <div className="font-bold text-gray-900 dark:text-white">{goal.weak_areas.length} konu</div>
          </div>
        </div>

        {goal.motivation && (
          <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
            <div className="text-sm text-gray-500 mb-1">💪 Motivasyonun</div>
            <div className="text-gray-700 dark:text-gray-300 italic">"{goal.motivation}"</div>
          </div>
        )}
      </div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="flex items-center gap-3 p-4 bg-green-50 dark:bg-green-900/20 rounded-xl"
      >
        <GraduationCap className="w-6 h-6 text-green-600" />
        <div className="text-sm text-green-800 dark:text-green-300">
          AI, senin için özel bir müfredat oluşturacak. Stage'ler, paketler, sınavlar ve sertifika hazır olacak!
        </div>
      </motion.div>
    </div>
  );
};

// ==================== MAIN WIZARD COMPONENT ====================

const JourneyCreationWizard: React.FC<JourneyWizardProps> = ({ onComplete, onCancel }) => {
  const [step, setStep] = useState(0);
  const [goal, setGoal] = useState<LearningGoal>({
    title: '',
    subject: '',
    target_outcome: '',
    motivation: '',
    prior_knowledge: '',
    weak_areas: [],
    focus_areas: [],
    daily_hours: 2,
    deadline: null,
    content_preferences: ['text', 'video'],
    exam_preferences: ['multiple_choice', 'feynman'],
    topics_to_include: null,
    topics_to_exclude: null,
  });

  const TOTAL_STEPS = 6;

  const updateGoal = (field: string, value: any) => {
    setGoal(prev => ({ ...prev, [field]: value }));
  };

  const canProceed = () => {
    switch (step) {
      case 0: return !!goal.subject;
      case 1: return !!goal.title && !!goal.target_outcome;
      case 2: return true; // Optional
      case 3: return goal.daily_hours > 0;
      case 4: return goal.content_preferences.length > 0;
      case 5: return true;
      default: return false;
    }
  };

  const handleNext = () => {
    if (step < TOTAL_STEPS - 1) {
      setStep(step + 1);
    } else {
      onComplete(goal);
    }
  };

  const handleBack = () => {
    if (step > 0) {
      setStep(step - 1);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4"
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="w-full max-w-2xl bg-white dark:bg-gray-900 rounded-2xl shadow-2xl overflow-hidden"
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-600 to-indigo-600 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <GraduationCap className="w-6 h-6 text-white" />
              <span className="text-white font-semibold">Öğrenme Yolculuğu Oluştur</span>
            </div>
            <button
              onClick={onCancel}
              className="text-white/70 hover:text-white transition-colors"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          <StepIndicator currentStep={step} totalSteps={TOTAL_STEPS} />

          <AnimatePresence mode="wait">
            <motion.div
              key={step}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
            >
              {step === 0 && (
                <SubjectStep
                  selected={goal.subject}
                  onSelect={(subject) => updateGoal('subject', subject)}
                />
              )}
              {step === 1 && (
                <GoalStep
                  title={goal.title}
                  target={goal.target_outcome}
                  motivation={goal.motivation}
                  onChange={updateGoal}
                />
              )}
              {step === 2 && (
                <KnowledgeStep
                  priorKnowledge={goal.prior_knowledge}
                  weakAreas={goal.weak_areas}
                  focusAreas={goal.focus_areas}
                  subject={goal.subject}
                  onChange={updateGoal}
                />
              )}
              {step === 3 && (
                <TimeStep
                  dailyHours={goal.daily_hours}
                  deadline={goal.deadline || ''}
                  onChange={updateGoal}
                />
              )}
              {step === 4 && (
                <PreferencesStep
                  contentPrefs={goal.content_preferences}
                  examPrefs={goal.exam_preferences}
                  onChange={updateGoal}
                />
              )}
              {step === 5 && <SummaryStep goal={goal} />}
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 dark:border-gray-700 p-4 flex justify-between">
          <button
            onClick={step === 0 ? onCancel : handleBack}
            className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white
                       flex items-center gap-2 transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
            {step === 0 ? 'İptal' : 'Geri'}
          </button>

          <button
            onClick={handleNext}
            disabled={!canProceed()}
            className={`px-6 py-2 rounded-xl font-semibold flex items-center gap-2 transition-all
              ${canProceed()
                ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white hover:shadow-lg'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
              }`}
          >
            {step === TOTAL_STEPS - 1 ? (
              <>
                <Sparkles className="w-4 h-4" />
                Yolculuğu Başlat
              </>
            ) : (
              <>
                Devam
                <ChevronRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default JourneyCreationWizard;
