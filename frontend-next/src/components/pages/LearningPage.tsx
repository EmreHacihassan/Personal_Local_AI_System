'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  GraduationCap,
  BookOpen,
  Trophy,
  Target,
  Clock,
  Flame,
  ChevronRight,
  Play,
  CheckCircle2,
  Lock,
  Star
} from 'lucide-react';
import { useStore } from '@/store/useStore';
import { cn } from '@/lib/utils';

interface Course {
  id: string;
  title: string;
  titleEn: string;
  description: string;
  descriptionEn: string;
  lessons: number;
  duration: string;
  progress: number;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  locked?: boolean;
}

const courses: Course[] = [
  {
    id: '1',
    title: 'AI Asistanı Kullanımı',
    titleEn: 'Using AI Assistant',
    description: 'Temel özellikler ve etkili kullanım yöntemleri',
    descriptionEn: 'Basic features and effective usage methods',
    lessons: 5,
    duration: '15 dk',
    progress: 100,
    difficulty: 'beginner'
  },
  {
    id: '2',
    title: 'Belge Yönetimi',
    titleEn: 'Document Management',
    description: 'Belge yükleme, arama ve RAG sistemi kullanımı',
    descriptionEn: 'Document upload, search and RAG system usage',
    lessons: 4,
    duration: '20 dk',
    progress: 75,
    difficulty: 'beginner'
  },
  {
    id: '3',
    title: 'Gelişmiş Sohbet Teknikleri',
    titleEn: 'Advanced Chat Techniques',
    description: 'Prompt mühendisliği ve verimli sorgulama',
    descriptionEn: 'Prompt engineering and efficient querying',
    lessons: 6,
    duration: '30 dk',
    progress: 25,
    difficulty: 'intermediate'
  },
  {
    id: '4',
    title: 'Web Araması ve Entegrasyon',
    titleEn: 'Web Search & Integration',
    description: 'Web araması, API entegrasyonları',
    descriptionEn: 'Web search and API integrations',
    lessons: 4,
    duration: '25 dk',
    progress: 0,
    difficulty: 'intermediate'
  },
  {
    id: '5',
    title: 'Kurumsal Kullanım',
    titleEn: 'Enterprise Usage',
    description: 'Takım yönetimi, raporlama ve analitik',
    descriptionEn: 'Team management, reporting and analytics',
    lessons: 8,
    duration: '45 dk',
    progress: 0,
    difficulty: 'advanced',
    locked: true
  }
];

const achievements = [
  { id: '1', name: 'İlk Adım', nameEn: 'First Step', icon: Star, unlocked: true },
  { id: '2', name: '10 Sohbet', nameEn: '10 Chats', icon: Target, unlocked: true },
  { id: '3', name: 'Belge Ustası', nameEn: 'Document Master', icon: BookOpen, unlocked: true },
  { id: '4', name: 'Araştırmacı', nameEn: 'Researcher', icon: Trophy, unlocked: false },
  { id: '5', name: 'Uzman', nameEn: 'Expert', icon: GraduationCap, unlocked: false },
];

export function LearningPage() {
  const { language } = useStore();
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null);

  const stats = {
    streak: 7,
    totalLessons: 15,
    completedLessons: 8,
    totalTime: '2h 45m'
  };

  const getDifficultyColor = (difficulty: Course['difficulty']) => {
    switch (difficulty) {
      case 'beginner': return 'text-green-500 bg-green-500/10';
      case 'intermediate': return 'text-yellow-500 bg-yellow-500/10';
      case 'advanced': return 'text-red-500 bg-red-500/10';
    }
  };

  const getDifficultyLabel = (difficulty: Course['difficulty']) => {
    if (language === 'tr') {
      switch (difficulty) {
        case 'beginner': return 'Başlangıç';
        case 'intermediate': return 'Orta';
        case 'advanced': return 'İleri';
      }
    }
    return difficulty.charAt(0).toUpperCase() + difficulty.slice(1);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-border bg-card/50 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 text-white">
            <GraduationCap className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-semibold">
              {language === 'tr' ? 'Öğrenme Merkezi' : 'Learning Center'}
            </h1>
            <p className="text-xs text-muted-foreground">
              {language === 'tr' ? 'Becerilerinizi geliştirin' : 'Improve your skills'}
            </p>
          </div>
        </div>
      </header>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-5xl mx-auto space-y-8">

          {/* Stats */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="grid grid-cols-2 md:grid-cols-4 gap-4"
          >
            <div className="bg-gradient-to-br from-orange-500 to-red-500 rounded-2xl p-5 text-white">
              <div className="flex items-center justify-between mb-3">
                <Flame className="w-8 h-8" />
                <span className="text-3xl font-bold">{stats.streak}</span>
              </div>
              <p className="text-sm opacity-90">
                {language === 'tr' ? 'Günlük Seri' : 'Day Streak'}
              </p>
            </div>

            <div className="bg-card border border-border rounded-2xl p-5">
              <div className="flex items-center justify-between mb-3">
                <BookOpen className="w-8 h-8 text-primary-500" />
                <span className="text-3xl font-bold">{stats.completedLessons}/{stats.totalLessons}</span>
              </div>
              <p className="text-sm text-muted-foreground">
                {language === 'tr' ? 'Tamamlanan Ders' : 'Completed Lessons'}
              </p>
            </div>

            <div className="bg-card border border-border rounded-2xl p-5">
              <div className="flex items-center justify-between mb-3">
                <Clock className="w-8 h-8 text-blue-500" />
                <span className="text-3xl font-bold">{stats.totalTime}</span>
              </div>
              <p className="text-sm text-muted-foreground">
                {language === 'tr' ? 'Toplam Süre' : 'Total Time'}
              </p>
            </div>

            <div className="bg-card border border-border rounded-2xl p-5">
              <div className="flex items-center justify-between mb-3">
                <Trophy className="w-8 h-8 text-yellow-500" />
                <span className="text-3xl font-bold">{achievements.filter(a => a.unlocked).length}/{achievements.length}</span>
              </div>
              <p className="text-sm text-muted-foreground">
                {language === 'tr' ? 'Başarı' : 'Achievements'}
              </p>
            </div>
          </motion.div>

          {/* Achievements */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Trophy className="w-5 h-5 text-yellow-500" />
              {language === 'tr' ? 'Başarılar' : 'Achievements'}
            </h2>
            <div className="flex gap-3 overflow-x-auto pb-2">
              {achievements.map((achievement) => (
                <div
                  key={achievement.id}
                  className={cn(
                    "flex flex-col items-center gap-2 p-4 rounded-2xl min-w-[100px] transition-all",
                    achievement.unlocked 
                      ? "bg-gradient-to-br from-yellow-500/10 to-orange-500/10 border border-yellow-500/30" 
                      : "bg-muted opacity-50"
                  )}
                >
                  <div className={cn(
                    "w-12 h-12 rounded-full flex items-center justify-center",
                    achievement.unlocked 
                      ? "bg-gradient-to-br from-yellow-500 to-orange-500 text-white" 
                      : "bg-muted-foreground/20"
                  )}>
                    <achievement.icon className="w-6 h-6" />
                  </div>
                  <span className="text-xs font-medium text-center">
                    {language === 'tr' ? achievement.name : achievement.nameEn}
                  </span>
                </div>
              ))}
            </div>
          </motion.section>

          {/* Courses */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-primary-500" />
              {language === 'tr' ? 'Kurslar' : 'Courses'}
            </h2>
            <div className="space-y-3">
              {courses.map((course, index) => (
                <motion.button
                  key={course.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.1 * index }}
                  onClick={() => !course.locked && setSelectedCourse(course)}
                  disabled={course.locked}
                  className={cn(
                    "w-full text-left bg-card border border-border rounded-2xl p-5 transition-all group",
                    course.locked 
                      ? "opacity-60 cursor-not-allowed" 
                      : "hover:border-primary-500/50 hover:shadow-lg"
                  )}
                >
                  <div className="flex items-center gap-4">
                    {/* Progress Circle */}
                    <div className="relative w-14 h-14 flex-shrink-0">
                      <svg className="w-14 h-14 transform -rotate-90">
                        <circle
                          cx="28"
                          cy="28"
                          r="24"
                          stroke="currentColor"
                          strokeWidth="4"
                          fill="none"
                          className="text-muted"
                        />
                        <circle
                          cx="28"
                          cy="28"
                          r="24"
                          stroke="currentColor"
                          strokeWidth="4"
                          fill="none"
                          strokeDasharray={2 * Math.PI * 24}
                          strokeDashoffset={2 * Math.PI * 24 * (1 - course.progress / 100)}
                          className="text-primary-500"
                          strokeLinecap="round"
                        />
                      </svg>
                      <div className="absolute inset-0 flex items-center justify-center">
                        {course.locked ? (
                          <Lock className="w-5 h-5 text-muted-foreground" />
                        ) : course.progress === 100 ? (
                          <CheckCircle2 className="w-5 h-5 text-green-500" />
                        ) : (
                          <span className="text-xs font-bold">{course.progress}%</span>
                        )}
                      </div>
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-semibold">
                          {language === 'tr' ? course.title : course.titleEn}
                        </h3>
                        <span className={cn(
                          "text-[10px] px-2 py-0.5 rounded-full font-medium",
                          getDifficultyColor(course.difficulty)
                        )}>
                          {getDifficultyLabel(course.difficulty)}
                        </span>
                      </div>
                      <p className="text-sm text-muted-foreground truncate">
                        {language === 'tr' ? course.description : course.descriptionEn}
                      </p>
                      <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <BookOpen className="w-3.5 h-3.5" />
                          {course.lessons} {language === 'tr' ? 'ders' : 'lessons'}
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5" />
                          {course.duration}
                        </span>
                      </div>
                    </div>

                    {/* Action */}
                    <div className="flex-shrink-0">
                      {!course.locked && (
                        <div className="w-10 h-10 rounded-full bg-primary-500 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                          <Play className="w-5 h-5 ml-0.5" />
                        </div>
                      )}
                    </div>
                  </div>
                </motion.button>
              ))}
            </div>
          </motion.section>

          {/* Continue Learning */}
          {courses.find(c => c.progress > 0 && c.progress < 100) && (
            <motion.section
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
            >
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Target className="w-5 h-5 text-green-500" />
                {language === 'tr' ? 'Devam Et' : 'Continue'}
              </h2>
              <div className="bg-gradient-to-r from-primary-500/10 to-primary-600/10 border border-primary-500/30 rounded-2xl p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">{language === 'tr' ? 'Gelişmiş Sohbet Teknikleri' : 'Advanced Chat Techniques'}</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      {language === 'tr' ? 'Ders 2: Prompt Yapıları' : 'Lesson 2: Prompt Structures'}
                    </p>
                  </div>
                  <button className="flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-xl hover:bg-primary-600 transition-colors">
                    <Play className="w-4 h-4" />
                    {language === 'tr' ? 'Devam Et' : 'Continue'}
                  </button>
                </div>
              </div>
            </motion.section>
          )}

        </div>
      </div>
    </div>
  );
}
