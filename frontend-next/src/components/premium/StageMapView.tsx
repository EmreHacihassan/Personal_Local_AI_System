'use client';

/**
 * 🎮 StageMapView - Candy Crush Style Learning Journey Map
 * 
 * Öğrenme yolculuğunu görsel stage haritası olarak gösterir.
 * Her stage bir konu, her paket bir bölge temsil eder.
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Star,
  Lock,
  Play,
  CheckCircle,
  Trophy,
  Zap,
  Crown,
  Sparkles,
  ChevronLeft,
  ChevronRight,
  Book,
  FileText,
  Video,
  PenTool,
  ClipboardCheck,
  Gift,
  Target,
  Flame,
  Brain,
  Rocket
} from 'lucide-react';

// Types
interface StagePosition {
  x: number;
  y: number;
}

interface StageData {
  id: string;
  number: number;
  title: string;
  status: 'locked' | 'available' | 'in_progress' | 'completed' | 'mastered';
  stars: number;
  position: StagePosition;
  is_boss: boolean;
  has_special_reward: boolean;
  xp_total: number;
  xp_earned: number;
}

interface Connection {
  from: string;
  to: string;
  is_unlocked: boolean;
}

interface PackageMapData {
  package_id: string;
  package_name: string;
  theme: string;
  color_scheme: {
    primary: string;
    secondary: string;
    background: string;
    accent: string;
  };
  stages: StageData[];
  connections: Connection[];
  current_stage_id: string | null;
}

interface PackageSummary {
  id: string;
  name: string;
  theme: string;
  is_unlocked: boolean;
  total_stages: number;
  completed_stages: number;
  completion_percentage: number;
  total_xp: number;
  earned_xp: number;
}

interface StageMapViewProps {
  userId: string;
  onStageClick?: (stageId: string) => void;
  onContentStart?: (stageId: string, contentId: string) => void;
  language?: 'tr' | 'en' | 'de';
}

// Theme backgrounds
const THEME_BACKGROUNDS: Record<string, string> = {
  candy: 'linear-gradient(180deg, #FFF0F5 0%, #FFB6C1 50%, #FF69B4 100%)',
  forest: 'linear-gradient(180deg, #E8F5E9 0%, #81C784 50%, #388E3C 100%)',
  ocean: 'linear-gradient(180deg, #E0F7FA 0%, #4DD0E1 50%, #00838F 100%)',
  space: 'linear-gradient(180deg, #1A1A2E 0%, #16213E 50%, #0F0F1A 100%)',
  desert: 'linear-gradient(180deg, #FDF5E6 0%, #DEB887 50%, #D2691E 100%)',
  arctic: 'linear-gradient(180deg, #F0FFFF 0%, #B0E0E6 50%, #4682B4 100%)',
  volcano: 'linear-gradient(180deg, #2D0A0A 0%, #8B0000 50%, #FF4500 100%)',
  crystal: 'linear-gradient(180deg, #F5E6FF 0%, #9B59B6 50%, #6C3483 100%)'
};

// Translations
const translations = {
  tr: {
    loading: 'Yükleniyor...',
    createPath: 'Öğrenme Yolunu Oluştur',
    noPath: 'Henüz bir öğrenme yolu oluşturulmadı',
    startJourney: 'Yolculuğa Başla',
    locked: 'Kilitli',
    available: 'Başla',
    inProgress: 'Devam Et',
    completed: 'Tamamlandı',
    mastered: 'Ustalaştın',
    xp: 'XP',
    stars: 'Yıldız',
    stage: 'Aşama',
    boss: 'Final Sınavı',
    packages: 'Paketler',
    progress: 'İlerleme',
    lesson: 'Ders',
    formula: 'Formüller',
    video: 'Video',
    practice: 'Alıştırma',
    quiz: 'Sınav'
  },
  en: {
    loading: 'Loading...',
    createPath: 'Create Learning Path',
    noPath: 'No learning path created yet',
    startJourney: 'Start Journey',
    locked: 'Locked',
    available: 'Start',
    inProgress: 'Continue',
    completed: 'Completed',
    mastered: 'Mastered',
    xp: 'XP',
    stars: 'Stars',
    stage: 'Stage',
    boss: 'Final Exam',
    packages: 'Packages',
    progress: 'Progress',
    lesson: 'Lesson',
    formula: 'Formulas',
    video: 'Video',
    practice: 'Practice',
    quiz: 'Quiz'
  },
  de: {
    loading: 'Laden...',
    createPath: 'Lernpfad erstellen',
    noPath: 'Noch kein Lernpfad erstellt',
    startJourney: 'Reise beginnen',
    locked: 'Gesperrt',
    available: 'Starten',
    inProgress: 'Fortsetzen',
    completed: 'Abgeschlossen',
    mastered: 'Gemeistert',
    xp: 'XP',
    stars: 'Sterne',
    stage: 'Stufe',
    boss: 'Abschlussprüfung',
    packages: 'Pakete',
    progress: 'Fortschritt',
    lesson: 'Lektion',
    formula: 'Formeln',
    video: 'Video',
    practice: 'Übung',
    quiz: 'Quiz'
  }
};

// API Base
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Stars Component
const StarsDisplay: React.FC<{ stars: number; size?: number }> = ({ stars, size = 16 }) => (
  <div className="flex gap-0.5">
    {[1, 2, 3].map((i) => (
      <Star
        key={i}
        size={size}
        className={`${i <= stars ? 'fill-yellow-400 text-yellow-400' : 'fill-gray-600 text-gray-600'}`}
      />
    ))}
  </div>
);

// Stage Node Component
const StageNode: React.FC<{
  stage: StageData;
  isSelected: boolean;
  isCurrent: boolean;
  colorScheme: PackageMapData['color_scheme'];
  onClick: () => void;
  t: typeof translations.tr;
}> = ({ stage, isSelected, isCurrent, colorScheme, onClick, t }) => {
  const getStatusStyle = () => {
    switch (stage.status) {
      case 'locked':
        return 'bg-gray-700 border-gray-600 opacity-60';
      case 'available':
        return `bg-gradient-to-br from-blue-500 to-blue-700 border-blue-400 shadow-lg shadow-blue-500/30`;
      case 'in_progress':
        return `bg-gradient-to-br from-amber-500 to-orange-600 border-amber-400 shadow-lg shadow-amber-500/30 animate-pulse`;
      case 'completed':
        return `bg-gradient-to-br from-emerald-500 to-green-700 border-emerald-400 shadow-lg shadow-emerald-500/30`;
      case 'mastered':
        return `bg-gradient-to-br from-purple-500 to-pink-600 border-purple-400 shadow-lg shadow-purple-500/30`;
      default:
        return 'bg-gray-700 border-gray-600';
    }
  };

  const getIcon = () => {
    if (stage.is_boss) return <Crown size={24} className="text-yellow-300" />;
    if (stage.status === 'locked') return <Lock size={20} className="text-gray-400" />;
    if (stage.status === 'available') return <Play size={20} className="text-white" />;
    if (stage.status === 'in_progress') return <Zap size={20} className="text-yellow-300" />;
    if (stage.status === 'completed') return <CheckCircle size={20} className="text-white" />;
    if (stage.status === 'mastered') return <Trophy size={20} className="text-yellow-300" />;
    return <span className="text-lg font-bold">{stage.number}</span>;
  };

  return (
    <motion.div
      className="absolute transform -translate-x-1/2 -translate-y-1/2 cursor-pointer"
      style={{
        left: `${stage.position.x}%`,
        top: `${stage.position.y}%`
      }}
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ delay: stage.number * 0.1 }}
      whileHover={{ scale: 1.15 }}
      whileTap={{ scale: 0.95 }}
      onClick={onClick}
    >
      {/* Glow effect for current stage */}
      {isCurrent && (
        <motion.div
          className="absolute inset-0 rounded-full"
          style={{ backgroundColor: colorScheme.accent }}
          animate={{ 
            scale: [1, 1.5, 1],
            opacity: [0.5, 0, 0.5]
          }}
          transition={{ duration: 2, repeat: Infinity }}
        />
      )}
      
      {/* Main node */}
      <div
        className={`
          relative w-14 h-14 rounded-full border-4 flex items-center justify-center
          ${getStatusStyle()}
          ${isSelected ? 'ring-4 ring-white ring-opacity-50' : ''}
          ${stage.is_boss ? 'w-18 h-18 border-yellow-400' : ''}
        `}
      >
        {getIcon()}
        
        {/* Special reward indicator */}
        {stage.has_special_reward && stage.status !== 'locked' && (
          <motion.div
            className="absolute -top-1 -right-1 w-5 h-5 bg-yellow-400 rounded-full flex items-center justify-center"
            animate={{ rotate: 360 }}
            transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
          >
            <Gift size={12} className="text-yellow-900" />
          </motion.div>
        )}
        
        {/* Stars display */}
        {(stage.status === 'completed' || stage.status === 'mastered') && (
          <div className="absolute -bottom-5">
            <StarsDisplay stars={stage.stars} size={12} />
          </div>
        )}
      </div>
      
      {/* Stage number badge */}
      <div className="absolute -top-2 -left-2 w-6 h-6 bg-gray-900 rounded-full flex items-center justify-center text-xs font-bold border-2 border-gray-700">
        {stage.number}
      </div>
    </motion.div>
  );
};

// Connection Path Component
const ConnectionPath: React.FC<{
  from: StageData;
  to: StageData;
  isUnlocked: boolean;
  colorScheme: PackageMapData['color_scheme'];
}> = ({ from, to, isUnlocked, colorScheme }) => {
  const pathRef = useRef<SVGPathElement>(null);
  
  // Calculate bezier curve control points
  const fromX = from.position.x;
  const fromY = from.position.y;
  const toX = to.position.x;
  const toY = to.position.y;
  
  const midX = (fromX + toX) / 2;
  const midY = (fromY + toY) / 2;
  
  // Create a curved path
  const d = `M ${fromX} ${fromY} Q ${midX} ${midY - 5} ${toX} ${toY}`;
  
  return (
    <svg
      className="absolute inset-0 w-full h-full pointer-events-none"
      viewBox="0 0 100 100"
      preserveAspectRatio="none"
    >
      {/* Background path */}
      <path
        d={d}
        fill="none"
        stroke={isUnlocked ? colorScheme.secondary : '#4B5563'}
        strokeWidth="0.8"
        strokeDasharray={isUnlocked ? 'none' : '2,2'}
        opacity={isUnlocked ? 0.8 : 0.4}
      />
      
      {/* Animated dots for unlocked paths */}
      {isUnlocked && (
        <motion.circle
          r="0.8"
          fill={colorScheme.accent}
          animate={{
            offsetDistance: ['0%', '100%']
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: 'linear'
          }}
          style={{
            offsetPath: `path('${d}')`
          }}
        />
      )}
    </svg>
  );
};

// Package Selector Component
const PackageSelector: React.FC<{
  packages: PackageSummary[];
  currentPackageId: string;
  onSelect: (id: string) => void;
  t: typeof translations.tr;
}> = ({ packages, currentPackageId, onSelect, t }) => {
  return (
    <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-thin">
      {packages.map((pkg) => (
        <motion.button
          key={pkg.id}
          onClick={() => pkg.is_unlocked && onSelect(pkg.id)}
          className={`
            flex-shrink-0 px-4 py-2 rounded-lg border-2 transition-all
            ${pkg.id === currentPackageId 
              ? 'bg-purple-600 border-purple-400 text-white' 
              : pkg.is_unlocked 
                ? 'bg-gray-800 border-gray-600 text-gray-200 hover:bg-gray-700'
                : 'bg-gray-900 border-gray-700 text-gray-500 cursor-not-allowed'
            }
          `}
          whileHover={pkg.is_unlocked ? { scale: 1.05 } : {}}
          whileTap={pkg.is_unlocked ? { scale: 0.95 } : {}}
        >
          <div className="flex items-center gap-2">
            {!pkg.is_unlocked && <Lock size={14} />}
            <span className="font-medium whitespace-nowrap">{pkg.name}</span>
          </div>
          {pkg.is_unlocked && (
            <div className="text-xs mt-1 opacity-75">
              {pkg.completed_stages}/{pkg.total_stages} • {Math.round(pkg.completion_percentage)}%
            </div>
          )}
        </motion.button>
      ))}
    </div>
  );
};

// Stage Detail Panel
const StageDetailPanel: React.FC<{
  stage: StageData | null;
  packageName: string;
  onStart: () => void;
  onClose: () => void;
  t: typeof translations.tr;
}> = ({ stage, packageName, onStart, onClose, t }) => {
  if (!stage) return null;

  const getStatusText = () => {
    switch (stage.status) {
      case 'locked': return t.locked;
      case 'available': return t.available;
      case 'in_progress': return t.inProgress;
      case 'completed': return t.completed;
      case 'mastered': return t.mastered;
      default: return '';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 50 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 50 }}
      className="fixed bottom-0 left-0 right-0 bg-gray-900/95 backdrop-blur-lg border-t border-gray-700 p-4 z-50"
    >
      <div className="max-w-2xl mx-auto">
        <div className="flex justify-between items-start mb-4">
          <div>
            <div className="text-sm text-gray-400">{packageName} • {t.stage} {stage.number}</div>
            <h3 className="text-xl font-bold text-white flex items-center gap-2">
              {stage.is_boss && <Crown className="text-yellow-400" size={20} />}
              {stage.title}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-800 rounded-full"
          >
            ✕
          </button>
        </div>

        {/* Stars and XP */}
        <div className="flex gap-6 mb-4">
          <div className="flex items-center gap-2">
            <StarsDisplay stars={stage.stars} />
          </div>
          <div className="flex items-center gap-2 text-yellow-400">
            <Zap size={16} />
            <span>{stage.xp_earned}/{stage.xp_total} {t.xp}</span>
          </div>
        </div>

        {/* Content types preview */}
        <div className="flex gap-2 mb-4">
          {[
            { icon: Book, label: t.lesson },
            { icon: FileText, label: t.formula },
            { icon: Video, label: t.video },
            { icon: PenTool, label: t.practice },
            { icon: ClipboardCheck, label: t.quiz }
          ].map(({ icon: Icon, label }) => (
            <div key={label} className="flex items-center gap-1 px-2 py-1 bg-gray-800 rounded text-xs">
              <Icon size={12} />
              <span>{label}</span>
            </div>
          ))}
        </div>

        {/* Action button */}
        {stage.status !== 'locked' && (
          <motion.button
            onClick={onStart}
            className={`
              w-full py-3 rounded-lg font-bold text-lg flex items-center justify-center gap-2
              ${stage.status === 'available' 
                ? 'bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700'
                : stage.status === 'in_progress'
                  ? 'bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700'
                  : 'bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700'
              }
            `}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            {stage.status === 'available' && <Play size={20} />}
            {stage.status === 'in_progress' && <Zap size={20} />}
            {(stage.status === 'completed' || stage.status === 'mastered') && <CheckCircle size={20} />}
            {getStatusText()}
          </motion.button>
        )}

        {stage.status === 'locked' && (
          <div className="w-full py-3 rounded-lg bg-gray-800 text-gray-400 font-medium text-center flex items-center justify-center gap-2">
            <Lock size={18} />
            {t.locked}
          </div>
        )}
      </div>
    </motion.div>
  );
};

// Main StageMapView Component
export const StageMapView: React.FC<StageMapViewProps> = ({
  userId,
  onStageClick,
  onContentStart,
  language = 'tr'
}) => {
  const t = translations[language];
  const containerRef = useRef<HTMLDivElement>(null);
  
  // State
  const [loading, setLoading] = useState(true);
  const [packages, setPackages] = useState<PackageSummary[]>([]);
  const [currentPackageId, setCurrentPackageId] = useState<string>('');
  const [mapData, setMapData] = useState<PackageMapData | null>(null);
  const [selectedStage, setSelectedStage] = useState<StageData | null>(null);
  const [pathExists, setPathExists] = useState(false);
  const [stats, setStats] = useState<{ total_xp: number; total_stars: number; streak_days: number } | null>(null);

  // Load path summary
  const loadPathSummary = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/learning-journey/path/${userId}/summary`);
      if (res.ok) {
        const data = await res.json();
        setPackages(data.packages);
        setStats(data.stats);
        setPathExists(true);
        
        // Set current package
        const unlockedPackages = data.packages.filter((p: PackageSummary) => p.is_unlocked);
        if (unlockedPackages.length > 0) {
          setCurrentPackageId(unlockedPackages[unlockedPackages.length - 1].id);
        }
      } else {
        setPathExists(false);
      }
    } catch (error) {
      console.error('Failed to load path summary:', error);
      setPathExists(false);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  // Load package map
  const loadPackageMap = useCallback(async (packageId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/learning-journey/package/${userId}/${packageId}/map`);
      if (res.ok) {
        const data = await res.json();
        setMapData(data);
      }
    } catch (error) {
      console.error('Failed to load package map:', error);
    }
  }, [userId]);

  // Create learning path
  const createLearningPath = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/learning-journey/path/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          subject: 'Matematik',
          goal: 'AYT matematik sınavında başarılı olmak'
        })
      });
      
      if (res.ok) {
        await loadPathSummary();
      }
    } catch (error) {
      console.error('Failed to create learning path:', error);
    } finally {
      setLoading(false);
    }
  };

  // Start stage
  const startStage = async (stageId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/learning-journey/stage/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          stage_id: stageId
        })
      });
      
      if (res.ok) {
        const data = await res.json();
        if (onContentStart && data.first_content) {
          onContentStart(stageId, data.first_content.id);
        } else if (onStageClick) {
          onStageClick(stageId);
        }
        
        // Reload map to reflect changes
        if (currentPackageId) {
          loadPackageMap(currentPackageId);
        }
      }
    } catch (error) {
      console.error('Failed to start stage:', error);
    }
  };

  // Effects
  useEffect(() => {
    loadPathSummary();
  }, [loadPathSummary]);

  useEffect(() => {
    if (currentPackageId) {
      loadPackageMap(currentPackageId);
    }
  }, [currentPackageId, loadPackageMap]);

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
        >
          <Sparkles className="w-12 h-12 text-purple-500" />
        </motion.div>
        <span className="ml-3 text-lg">{t.loading}</span>
      </div>
    );
  }

  // No path state
  if (!pathExists) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-center">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring' }}
        >
          <Rocket className="w-24 h-24 text-purple-500 mb-6" />
        </motion.div>
        <h2 className="text-2xl font-bold mb-2">{t.noPath}</h2>
        <p className="text-gray-400 mb-6">{t.startJourney}</p>
        <motion.button
          onClick={createLearningPath}
          className="px-8 py-4 bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl font-bold text-lg"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          {t.createPath}
        </motion.button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header Stats */}
      {stats && (
        <div className="flex justify-between items-center mb-4 px-4">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 bg-yellow-500/20 px-3 py-1.5 rounded-lg">
              <Zap className="text-yellow-400" size={18} />
              <span className="font-bold text-yellow-400">{stats.total_xp} XP</span>
            </div>
            <div className="flex items-center gap-2 bg-amber-500/20 px-3 py-1.5 rounded-lg">
              <Star className="text-amber-400 fill-amber-400" size={18} />
              <span className="font-bold text-amber-400">{stats.total_stars}</span>
            </div>
            <div className="flex items-center gap-2 bg-orange-500/20 px-3 py-1.5 rounded-lg">
              <Flame className="text-orange-400" size={18} />
              <span className="font-bold text-orange-400">{stats.streak_days} gün</span>
            </div>
          </div>
        </div>
      )}

      {/* Package Selector */}
      <div className="px-4 mb-4">
        <PackageSelector
          packages={packages}
          currentPackageId={currentPackageId}
          onSelect={setCurrentPackageId}
          t={t}
        />
      </div>

      {/* Stage Map */}
      {mapData && (
        <div
          ref={containerRef}
          className="flex-1 relative overflow-hidden rounded-xl mx-4"
          style={{
            background: THEME_BACKGROUNDS[mapData.theme] || THEME_BACKGROUNDS.candy,
            minHeight: '400px'
          }}
        >
          {/* Connections */}
          {mapData.connections.map((conn) => {
            const fromStage = mapData.stages.find(s => s.id === conn.from);
            const toStage = mapData.stages.find(s => s.id === conn.to);
            if (!fromStage || !toStage) return null;
            
            return (
              <ConnectionPath
                key={`${conn.from}-${conn.to}`}
                from={fromStage}
                to={toStage}
                isUnlocked={conn.is_unlocked}
                colorScheme={mapData.color_scheme}
              />
            );
          })}

          {/* Stages */}
          {mapData.stages.map((stage) => (
            <StageNode
              key={stage.id}
              stage={stage}
              isSelected={selectedStage?.id === stage.id}
              isCurrent={stage.id === mapData.current_stage_id}
              colorScheme={mapData.color_scheme}
              onClick={() => setSelectedStage(stage)}
              t={t}
            />
          ))}

          {/* Package Title */}
          <div className="absolute top-4 left-4 bg-black/40 backdrop-blur-sm px-4 py-2 rounded-lg">
            <h2 className="text-lg font-bold text-white">{mapData.package_name}</h2>
          </div>
        </div>
      )}

      {/* Stage Detail Panel */}
      <AnimatePresence>
        {selectedStage && (
          <StageDetailPanel
            stage={selectedStage}
            packageName={mapData?.package_name || ''}
            onStart={() => startStage(selectedStage.id)}
            onClose={() => setSelectedStage(null)}
            t={t}
          />
        )}
      </AnimatePresence>
    </div>
  );
};

export default StageMapView;
