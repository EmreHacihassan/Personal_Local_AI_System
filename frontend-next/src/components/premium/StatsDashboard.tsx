'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X, TrendingUp, FileText, Folder, Clock,
  Calendar, Award, Activity, PieChart,
  BarChart2, Edit3, Zap, Star
} from 'lucide-react';

interface StatsDashboardProps {
  isOpen: boolean;
  onClose: () => void;
  noteCount: number;
  folderCount: number;
}

interface WeeklyData {
  day: string;
  notes: number;
  words: number;
}

interface CategoryData {
  name: string;
  count: number;
  color: string;
}

const StatsDashboard: React.FC<StatsDashboardProps> = ({
  isOpen,
  onClose,
  noteCount,
  folderCount
}) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'activity' | 'insights'>('overview');
  const [isLoading, setIsLoading] = useState(true);
  const [stats, setStats] = useState({
    totalWords: 0,
    totalCharacters: 0,
    avgWordsPerNote: 0,
    writingStreak: 0,
    totalReadingTime: 0,
    notesThisWeek: 0,
    favoriteTags: [] as string[],
  });

  // Mock weekly data
  const weeklyData: WeeklyData[] = [
    { day: 'Pzt', notes: 3, words: 450 },
    { day: 'Sal', notes: 5, words: 720 },
    { day: 'Çar', notes: 2, words: 280 },
    { day: 'Per', notes: 8, words: 1200 },
    { day: 'Cum', notes: 4, words: 560 },
    { day: 'Cmt', notes: 1, words: 150 },
    { day: 'Paz', notes: 6, words: 890 },
  ];

  // Mock category data
  const categoryData: CategoryData[] = [
    { name: 'İş', count: 12, color: 'bg-blue-500' },
    { name: 'Kişisel', count: 8, color: 'bg-purple-500' },
    { name: 'Fikirler', count: 15, color: 'bg-green-500' },
    { name: 'Toplantı', count: 6, color: 'bg-orange-500' },
    { name: 'Proje', count: 10, color: 'bg-pink-500' },
  ];

  const maxNotes = Math.max(...weeklyData.map(d => d.notes));
  const maxWords = Math.max(...weeklyData.map(d => d.words));
  const totalCategoryCount = categoryData.reduce((acc, c) => acc + c.count, 0);

  // Simulate loading stats
  useEffect(() => {
    if (isOpen) {
      setIsLoading(true);
      const timer = setTimeout(() => {
        setStats({
          totalWords: 12450,
          totalCharacters: 68750,
          avgWordsPerNote: Math.round(12450 / Math.max(noteCount, 1)),
          writingStreak: 7,
          totalReadingTime: 52,
          notesThisWeek: weeklyData.reduce((acc, d) => acc + d.notes, 0),
          favoriteTags: ['#proje', '#toplantı', '#fikir', '#önemli', '#günlük'],
        });
        setIsLoading(false);
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [isOpen, noteCount]);

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center p-4"
        onClick={onClose}
      >
        {/* Backdrop */}
        <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />

        {/* Modal */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          className="relative w-full max-w-4xl max-h-[85vh] bg-white dark:bg-gray-900 rounded-2xl shadow-2xl overflow-hidden"
          onClick={e => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-purple-500/10 via-indigo-500/10 to-blue-500/10">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-r from-purple-500 to-indigo-500 rounded-xl text-white">
                <BarChart2 className="w-6 h-6" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                  İstatistik Paneli
                </h2>
                <p className="text-sm text-gray-500">Yazma alışkanlıklarınızın analizi</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>

          {/* Tabs */}
          <div className="flex gap-1 px-6 pt-4">
            {[
              { id: 'overview', label: 'Genel Bakış', icon: <PieChart /> },
              { id: 'activity', label: 'Aktivite', icon: <Activity /> },
              { id: 'insights', label: 'İçgörüler', icon: <TrendingUp /> },
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as typeof activeTab)}
                className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-all ${
                  activeTab === tab.id
                    ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300'
                    : 'text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800'
                }`}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </div>

          {/* Content */}
          <div className="p-6 overflow-y-auto max-h-[calc(85vh-180px)]">
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <motion.div
                  className="w-12 h-12 border-3 border-purple-500 border-t-transparent rounded-full"
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                />
              </div>
            ) : (
              <>
                {activeTab === 'overview' && (
                  <div className="space-y-6">
                    {/* Stats Grid */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      {[
                        { label: 'Toplam Not', value: noteCount, icon: <FileText />, color: 'from-blue-500 to-cyan-500' },
                        { label: 'Klasör', value: folderCount, icon: <Folder />, color: 'from-purple-500 to-pink-500' },
                        { label: 'Toplam Kelime', value: stats.totalWords.toLocaleString(), icon: <Edit3 />, color: 'from-green-500 to-emerald-500' },
                        { label: 'Yazma Serisi', value: `${stats.writingStreak} gün 🔥`, icon: <Zap />, color: 'from-orange-500 to-red-500' },
                      ].map((stat, idx) => (
                        <motion.div
                          key={stat.label}
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: idx * 0.1 }}
                          className="relative overflow-hidden p-4 bg-gray-50 dark:bg-gray-800 rounded-xl"
                        >
                          <div className={`absolute top-0 left-0 w-1 h-full bg-gradient-to-b ${stat.color}`} />
                          <div className="flex items-center gap-3">
                            <div className={`p-2 rounded-lg bg-gradient-to-r ${stat.color} text-white`}>
                              {stat.icon}
                            </div>
                            <div>
                              <div className="text-2xl font-bold text-gray-900 dark:text-white">
                                {stat.value}
                              </div>
                              <div className="text-xs text-gray-500">{stat.label}</div>
                            </div>
                          </div>
                        </motion.div>
                      ))}
                    </div>

                    {/* Category Distribution */}
                    <div className="grid md:grid-cols-2 gap-6">
                      {/* Pie Chart */}
                      <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-xl">
                        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">
                          Kategori Dağılımı
                        </h3>
                        <div className="flex items-center gap-6">
                          {/* Simple Donut */}
                          <div className="relative w-32 h-32">
                            <svg className="w-full h-full transform -rotate-90">
                              {categoryData.map((cat, idx) => {
                                const offset = categoryData.slice(0, idx).reduce((acc, c) => acc + c.count, 0);
                                const percent = (cat.count / totalCategoryCount) * 100;
                                const dashArray = percent * 3.14;
                                const dashOffset = -offset / totalCategoryCount * 314;
                                return (
                                  <circle
                                    key={cat.name}
                                    cx="64"
                                    cy="64"
                                    r="50"
                                    fill="none"
                                    stroke={cat.color.replace('bg-', 'var(--color-')}
                                    strokeWidth="20"
                                    strokeDasharray={`${dashArray} 314`}
                                    strokeDashoffset={dashOffset}
                                    className={cat.color.replace('bg-', 'stroke-')}
                                  />
                                );
                              })}
                            </svg>
                            <div className="absolute inset-0 flex items-center justify-center">
                              <span className="text-2xl font-bold text-gray-900 dark:text-white">
                                {totalCategoryCount}
                              </span>
                            </div>
                          </div>
                          {/* Legend */}
                          <div className="flex-1 space-y-2">
                            {categoryData.map(cat => (
                              <div key={cat.name} className="flex items-center gap-2">
                                <div className={`w-3 h-3 rounded-full ${cat.color}`} />
                                <span className="text-sm text-gray-600 dark:text-gray-400 flex-1">
                                  {cat.name}
                                </span>
                                <span className="text-sm font-medium text-gray-900 dark:text-white">
                                  {cat.count}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>

                      {/* Quick Stats */}
                      <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-xl">
                        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">
                          Hızlı İstatistikler
                        </h3>
                        <div className="space-y-3">
                          {[
                            { label: 'Ortalama kelime/not', value: stats.avgWordsPerNote },
                            { label: 'Toplam karakter', value: stats.totalCharacters.toLocaleString() },
                            { label: 'Tahmini okuma süresi', value: `${stats.totalReadingTime} dk` },
                            { label: 'Bu haftaki not', value: stats.notesThisWeek },
                          ].map(item => (
                            <div key={item.label} className="flex items-center justify-between">
                              <span className="text-sm text-gray-600 dark:text-gray-400">
                                {item.label}
                              </span>
                              <span className="text-sm font-medium text-gray-900 dark:text-white">
                                {item.value}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {activeTab === 'activity' && (
                  <div className="space-y-6">
                    {/* Weekly Chart */}
                    <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-xl">
                      <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4 flex items-center gap-2">
                        <Calendar className="w-4 h-4" />
                        Haftalık Aktivite
                      </h3>
                      
                      {/* Bar Chart */}
                      <div className="h-48 flex items-end gap-4">
                        {weeklyData.map((day, idx) => (
                          <div key={day.day} className="flex-1 flex flex-col items-center gap-2">
                            <div className="w-full flex gap-1 justify-center h-40">
                              {/* Notes bar */}
                              <motion.div
                                initial={{ height: 0 }}
                                animate={{ height: `${(day.notes / maxNotes) * 100}%` }}
                                transition={{ delay: idx * 0.1, duration: 0.5 }}
                                className="w-4 bg-gradient-to-t from-purple-500 to-indigo-400 rounded-t-lg"
                                title={`${day.notes} not`}
                              />
                              {/* Words bar */}
                              <motion.div
                                initial={{ height: 0 }}
                                animate={{ height: `${(day.words / maxWords) * 100}%` }}
                                transition={{ delay: idx * 0.1 + 0.1, duration: 0.5 }}
                                className="w-4 bg-gradient-to-t from-green-500 to-emerald-400 rounded-t-lg"
                                title={`${day.words} kelime`}
                              />
                            </div>
                            <span className="text-xs text-gray-500">{day.day}</span>
                          </div>
                        ))}
                      </div>

                      {/* Legend */}
                      <div className="flex items-center justify-center gap-6 mt-4">
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 rounded bg-gradient-to-r from-purple-500 to-indigo-400" />
                          <span className="text-xs text-gray-500">Not sayısı</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 rounded bg-gradient-to-r from-green-500 to-emerald-400" />
                          <span className="text-xs text-gray-500">Kelime sayısı</span>
                        </div>
                      </div>
                    </div>

                    {/* Activity Heatmap */}
                    <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-xl">
                      <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">
                        Aktivite Haritası (Son 30 gün)
                      </h3>
                      <div className="grid grid-cols-7 gap-1">
                        {Array.from({ length: 30 }).map((_, idx) => {
                          const intensity = Math.random();
                          return (
                            <motion.div
                              key={idx}
                              initial={{ opacity: 0, scale: 0 }}
                              animate={{ opacity: 1, scale: 1 }}
                              transition={{ delay: idx * 0.02 }}
                              className={`aspect-square rounded-sm ${
                                intensity > 0.8 ? 'bg-green-500' :
                                intensity > 0.5 ? 'bg-green-400' :
                                intensity > 0.3 ? 'bg-green-300' :
                                intensity > 0.1 ? 'bg-green-200' :
                                'bg-gray-200 dark:bg-gray-700'
                              }`}
                              title={`Gün ${idx + 1}`}
                            />
                          );
                        })}
                      </div>
                    </div>
                  </div>
                )}

                {activeTab === 'insights' && (
                  <div className="space-y-6">
                    {/* Insights Cards */}
                    <div className="grid md:grid-cols-2 gap-4">
                      {[
                        {
                          icon: <TrendingUp className="w-6 h-6" />,
                          title: 'Üretkenlik Trendi',
                          value: '+23%',
                          description: 'Bu hafta geçen haftaya göre daha fazla yazdınız!',
                          color: 'from-green-500 to-emerald-500',
                          positive: true,
                        },
                        {
                          icon: <Clock className="w-6 h-6" />,
                          title: 'En Verimli Saat',
                          value: '14:00 - 16:00',
                          description: 'Bu saatlerde en çok içerik üretiyorsunuz.',
                          color: 'from-blue-500 to-cyan-500',
                        },
                        {
                          icon: <Star className="w-6 h-6" />,
                          title: 'En Popüler Etiket',
                          value: '#proje',
                          description: '15 notta kullanıldı',
                          color: 'from-purple-500 to-pink-500',
                        },
                        {
                          icon: <Award className="w-6 h-6" />,
                          title: 'Başarı',
                          value: 'Haftalık Hedef ✓',
                          description: 'Bu hafta 25+ not hedefine ulaştınız!',
                          color: 'from-orange-500 to-red-500',
                        },
                      ].map((insight, idx) => (
                        <motion.div
                          key={insight.title}
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: idx * 0.1 }}
                          className="p-4 bg-gray-50 dark:bg-gray-800 rounded-xl"
                        >
                          <div className="flex items-start gap-4">
                            <div className={`p-3 rounded-xl bg-gradient-to-r ${insight.color} text-white`}>
                              {insight.icon}
                            </div>
                            <div className="flex-1">
                              <div className="text-sm text-gray-500">{insight.title}</div>
                              <div className="text-xl font-bold text-gray-900 dark:text-white">
                                {insight.value}
                              </div>
                              <div className="text-sm text-gray-500 mt-1">
                                {insight.description}
                              </div>
                            </div>
                          </div>
                        </motion.div>
                      ))}
                    </div>

                    {/* Favorite Tags */}
                    <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-xl">
                      <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                        En Çok Kullanılan Etiketler
                      </h3>
                      <div className="flex flex-wrap gap-2">
                        {stats.favoriteTags.map((tag, idx) => (
                          <motion.span
                            key={tag}
                            initial={{ opacity: 0, scale: 0 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ delay: idx * 0.1 }}
                            className="px-3 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-full text-sm"
                          >
                            {tag}
                          </motion.span>
                        ))}
                      </div>
                    </div>

                    {/* AI Tip */}
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="p-4 bg-gradient-to-r from-purple-500/10 to-indigo-500/10 border border-purple-200 dark:border-purple-800 rounded-xl"
                    >
                      <div className="flex items-center gap-3 mb-2">
                        <Zap className="w-5 h-5 text-purple-500" />
                        <span className="font-medium text-purple-700 dark:text-purple-300">
                          AI Önerisi
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Öğleden sonra saatlerinde daha verimli olduğunuz görünüyor. 
                        Önemli notlarınızı bu saatlere planlamayı deneyin!
                      </p>
                    </motion.div>
                  </div>
                )}
              </>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default StatsDashboard;
