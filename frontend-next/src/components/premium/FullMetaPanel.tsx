'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  BookOpen,
  GraduationCap,
  Brain,
  Target,
  Trophy,
  Zap,
  ChevronRight,
  ChevronDown,
  Play,
  Pause,
  CheckCircle,
  Circle,
  Lock,
  Star,
  Flame,
  Sparkles,
  FileText,
  Plus,
  Settings,
  BarChart3,
  Clock,
  Award,
  Lightbulb,
  HelpCircle,
  MessageSquare,
  Mic,
  Volume2,
  Map,
  Layers,
  TrendingUp,
  RefreshCw,
  AlertCircle,
  ArrowRight,
  Check,
  X,
} from 'lucide-react';

// ============================================================================
// TYPES
// ============================================================================

interface Workspace {
  id: string;
  name: string;
  description: string;
  target_goal: string;
  stages_count: number;
  total_packages: number;
  overall_progress: number;
  total_xp: number;
  level: number;
  streak_days: number;
  created_at: string;
  last_activity: string | null;
  stages?: Stage[];
}

interface Stage {
  id: string;
  name: string;
  description: string;
  order: number;
  packages: Package[];
  status: string;
  mastery_score: number;
}

interface Package {
  id: string;
  name: string;
  description: string;
  order: number;
  concepts_count: number;
  layers_count: number;
  current_layer_index: number;
  status: string;
  overall_score: number;
  xp_earned: number;
}

interface Layer {
  id: string;
  index: number;
  layer_type: string;
  title: string;
  description: string;
  estimated_minutes: number;
  content: any;
  questions: Question[];
  completed: boolean;
  score: number | null;
  is_current: boolean;
  is_locked: boolean;
}

interface Question {
  id: string;
  question_type: string;
  difficulty: string;
  question_text: string;
  options?: string[];
  hints?: string[];
  points: number;
  time_limit_seconds?: number;
}

interface LayerTypeInfo {
  type: string;
  title: string;
  description: string;
  scientific_basis: string;
  estimated_minutes: number;
}

// ============================================================================
// CONSTANTS
// ============================================================================

const LAYER_ICONS: Record<string, React.ReactNode> = {
  warmup: <Flame className="w-5 h-5" />,
  prime: <Lightbulb className="w-5 h-5" />,
  acquire: <BookOpen className="w-5 h-5" />,
  interrogate: <HelpCircle className="w-5 h-5" />,
  practice: <Target className="w-5 h-5" />,
  connect: <Layers className="w-5 h-5" />,
  challenge: <Zap className="w-5 h-5" />,
  error_lab: <AlertCircle className="w-5 h-5" />,
  feynman: <Mic className="w-5 h-5" />,
  transfer: <TrendingUp className="w-5 h-5" />,
  meta_reflection: <Brain className="w-5 h-5" />,
  consolidate: <CheckCircle className="w-5 h-5" />,
};

const LAYER_COLORS: Record<string, string> = {
  warmup: 'from-orange-500 to-red-500',
  prime: 'from-yellow-500 to-amber-500',
  acquire: 'from-blue-500 to-indigo-500',
  interrogate: 'from-purple-500 to-violet-500',
  practice: 'from-green-500 to-emerald-500',
  connect: 'from-cyan-500 to-blue-500',
  challenge: 'from-red-500 to-pink-500',
  error_lab: 'from-amber-500 to-orange-500',
  feynman: 'from-pink-500 to-rose-500',
  transfer: 'from-teal-500 to-cyan-500',
  meta_reflection: 'from-indigo-500 to-purple-500',
  consolidate: 'from-emerald-500 to-green-500',
};

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

// ============================================================================
// API FUNCTIONS
// ============================================================================

async function fetchWorkspaces(userId: string = 'default_user'): Promise<Workspace[]> {
  const res = await fetch(`${API_BASE}/api/full-meta/workspaces?user_id=${userId}`);
  const data = await res.json();
  return data.workspaces || [];
}

async function fetchWorkspaceDetails(workspaceId: string): Promise<Workspace | null> {
  const res = await fetch(`${API_BASE}/api/full-meta/workspaces/${workspaceId}`);
  const data = await res.json();
  return data.workspace || null;
}

async function fetchLayerTypes(): Promise<LayerTypeInfo[]> {
  const res = await fetch(`${API_BASE}/api/full-meta/layer-types`);
  const data = await res.json();
  return data.layer_types || [];
}

async function fetchCurrentLayer(packageId: string): Promise<{ package: any; layer: Layer } | null> {
  const res = await fetch(`${API_BASE}/api/full-meta/packages/${packageId}/current-layer`);
  const data = await res.json();
  if (data.package_completed) return { package: data.package, layer: null as any };
  return { package: data.package, layer: data.layer };
}

async function fetchAllLayers(packageId: string): Promise<Layer[]> {
  const res = await fetch(`${API_BASE}/api/full-meta/packages/${packageId}/layers`);
  const data = await res.json();
  return data.layers || [];
}

async function startPackage(packageId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/api/full-meta/packages/${packageId}/start`, {
    method: 'POST',
  });
  return await res.json();
}

async function completeLayer(packageId: string, score: number): Promise<any> {
  const res = await fetch(`${API_BASE}/api/full-meta/packages/${packageId}/complete-layer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ score }),
  });
  return await res.json();
}

async function createWorkspace(data: {
  name: string;
  description: string;
  target_goal: string;
}): Promise<any> {
  const res = await fetch(`${API_BASE}/api/full-meta/workspaces`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...data, user_id: 'default_user' }),
  });
  return await res.json();
}

async function createDemoWorkspace(): Promise<any> {
  const res = await fetch(`${API_BASE}/api/full-meta/demo/create-sample`, {
    method: 'POST',
  });
  return await res.json();
}

async function submitFeynman(packageId: string, data: {
  target_audience: string;
  format: string;
  content: string;
}): Promise<any> {
  const res = await fetch(`${API_BASE}/api/full-meta/packages/${packageId}/feynman`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...data, user_id: 'default_user' }),
  });
  return await res.json();
}

// ============================================================================
// COMPONENTS
// ============================================================================

// XP ve Level göstergesi
const XPIndicator: React.FC<{ xp: number; level: number }> = ({ xp, level }) => {
  const xpForNextLevel = ((level + 1) ** 2) * 100;
  const currentLevelXp = (level ** 2) * 100;
  const progress = ((xp - currentLevelXp) / (xpForNextLevel - currentLevelXp)) * 100;

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
            animate={{ width: `${Math.min(progress, 100)}%` }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
          />
        </div>
        <div className="text-xs text-gray-400 mt-1">
          {xpForNextLevel - xp} XP sonraki level
        </div>
      </div>
    </div>
  );
};

// Streak göstergesi
const StreakIndicator: React.FC<{ days: number }> = ({ days }) => (
  <div className="flex items-center gap-2 bg-gradient-to-r from-orange-900/50 to-red-900/50 rounded-xl p-3 border border-orange-500/30">
    <Flame className="w-8 h-8 text-orange-400" />
    <div>
      <div className="text-2xl font-bold text-orange-400">{days}</div>
      <div className="text-xs text-orange-200">gün streak 🔥</div>
    </div>
  </div>
);

// Workspace kartı
const WorkspaceCard: React.FC<{
  workspace: Workspace;
  onSelect: (ws: Workspace) => void;
}> = ({ workspace, onSelect }) => (
  <motion.div
    whileHover={{ scale: 1.02, y: -4 }}
    whileTap={{ scale: 0.98 }}
    onClick={() => onSelect(workspace)}
    className="cursor-pointer bg-gradient-to-br from-gray-800/80 to-gray-900/80 rounded-2xl p-6 border border-gray-700/50 hover:border-purple-500/50 transition-all"
  >
    <div className="flex items-start justify-between mb-4">
      <div className="p-3 rounded-xl bg-gradient-to-br from-purple-500 to-indigo-500">
        <GraduationCap className="w-6 h-6 text-white" />
      </div>
      <div className="flex items-center gap-1 text-amber-400">
        <Star className="w-4 h-4 fill-current" />
        <span className="text-sm font-medium">Lvl {workspace.level}</span>
      </div>
    </div>
    
    <h3 className="text-lg font-semibold text-white mb-1">{workspace.name}</h3>
    <p className="text-sm text-gray-400 mb-4 line-clamp-2">{workspace.description || workspace.target_goal}</p>
    
    <div className="flex items-center justify-between text-sm text-gray-400 mb-3">
      <span>{workspace.stages_count} aşama</span>
      <span>{workspace.total_packages} paket</span>
    </div>
    
    <div className="h-2 bg-gray-700 rounded-full overflow-hidden mb-2">
      <motion.div
        className="h-full bg-gradient-to-r from-green-400 to-emerald-500"
        initial={{ width: 0 }}
        animate={{ width: `${workspace.overall_progress}%` }}
      />
    </div>
    <div className="flex justify-between text-xs">
      <span className="text-gray-500">İlerleme</span>
      <span className="text-green-400">{workspace.overall_progress.toFixed(1)}%</span>
    </div>
    
    {workspace.streak_days > 0 && (
      <div className="mt-3 flex items-center gap-1 text-orange-400 text-sm">
        <Flame className="w-4 h-4" />
        <span>{workspace.streak_days} gün streak!</span>
      </div>
    )}
  </motion.div>
);

// Stage bileşeni
const StageSection: React.FC<{
  stage: Stage;
  isExpanded: boolean;
  onToggle: () => void;
  onSelectPackage: (pkg: Package) => void;
}> = ({ stage, isExpanded, onToggle, onSelectPackage }) => {
  const isLocked = stage.status === 'locked';
  const completedPackages = stage.packages.filter(p => p.status === 'completed').length;
  const progress = stage.packages.length > 0 ? (completedPackages / stage.packages.length) * 100 : 0;

  return (
    <div className={`rounded-2xl border ${isLocked ? 'border-gray-700 opacity-60' : 'border-gray-700/50'} overflow-hidden`}>
      <motion.div
        onClick={!isLocked ? onToggle : undefined}
        className={`p-4 flex items-center justify-between ${!isLocked ? 'cursor-pointer hover:bg-gray-800/50' : ''} transition-colors`}
      >
        <div className="flex items-center gap-4">
          <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
            isLocked ? 'bg-gray-700' : 'bg-gradient-to-br from-indigo-500 to-purple-500'
          }`}>
            {isLocked ? <Lock className="w-6 h-6 text-gray-500" /> : <Map className="w-6 h-6 text-white" />}
          </div>
          <div>
            <h3 className="font-semibold text-white">{stage.name}</h3>
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
      </motion.div>
      
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
              {stage.packages.map((pkg) => (
                <PackageCard key={pkg.id} pkg={pkg} onSelect={onSelectPackage} />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

// Package kartı
const PackageCard: React.FC<{
  pkg: Package;
  onSelect: (pkg: Package) => void;
}> = ({ pkg, onSelect }) => {
  const isLocked = pkg.status === 'locked';
  const isCompleted = pkg.status === 'completed';
  const isActive = pkg.status === 'in_progress' || pkg.status === 'available';
  const progress = pkg.layers_count > 0 ? (pkg.current_layer_index / pkg.layers_count) * 100 : 0;

  return (
    <motion.div
      whileHover={!isLocked ? { scale: 1.01, x: 4 } : {}}
      onClick={() => !isLocked && onSelect(pkg)}
      className={`p-4 rounded-xl border transition-all ${
        isLocked
          ? 'border-gray-700 bg-gray-800/30 opacity-50 cursor-not-allowed'
          : isCompleted
          ? 'border-green-500/50 bg-green-900/20 cursor-pointer'
          : 'border-gray-700/50 bg-gray-800/50 cursor-pointer hover:border-purple-500/50'
      }`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
            isLocked
              ? 'bg-gray-700'
              : isCompleted
              ? 'bg-green-500'
              : 'bg-gradient-to-br from-blue-500 to-indigo-500'
          }`}>
            {isLocked ? (
              <Lock className="w-5 h-5 text-gray-500" />
            ) : isCompleted ? (
              <CheckCircle className="w-5 h-5 text-white" />
            ) : (
              <BookOpen className="w-5 h-5 text-white" />
            )}
          </div>
          <div>
            <h4 className="font-medium text-white">{pkg.name}</h4>
            <p className="text-xs text-gray-400">{pkg.concepts_count} kavram • {pkg.layers_count} katman</p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          {pkg.xp_earned > 0 && (
            <div className="flex items-center gap-1 text-amber-400 text-sm">
              <Star className="w-4 h-4" />
              <span>{pkg.xp_earned}</span>
            </div>
          )}
          
          {isActive && (
            <div className="w-20">
              <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-blue-400 to-indigo-500"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <div className="text-xs text-gray-400 text-right mt-1">
                {pkg.current_layer_index}/{pkg.layers_count}
              </div>
            </div>
          )}
          
          {isCompleted && (
            <div className="text-green-400 text-sm font-medium">
              {pkg.overall_score.toFixed(0)}%
            </div>
          )}
          
          {!isLocked && <ChevronRight className="w-5 h-5 text-gray-400" />}
        </div>
      </div>
    </motion.div>
  );
};

// Layer listesi
const LayerList: React.FC<{
  layers: Layer[];
  currentIndex: number;
  onSelectLayer: (layer: Layer, index: number) => void;
}> = ({ layers, currentIndex, onSelectLayer }) => (
  <div className="space-y-2">
    {layers.map((layer, index) => {
      const isLocked = layer.is_locked;
      const isCurrent = layer.is_current;
      const isCompleted = layer.completed;

      return (
        <motion.div
          key={layer.id}
          whileHover={!isLocked ? { x: 4 } : {}}
          onClick={() => !isLocked && onSelectLayer(layer, index)}
          className={`p-3 rounded-xl flex items-center gap-3 transition-all ${
            isLocked
              ? 'bg-gray-800/30 opacity-50 cursor-not-allowed'
              : isCurrent
              ? 'bg-gradient-to-r from-purple-900/50 to-indigo-900/50 border border-purple-500/50 cursor-pointer'
              : isCompleted
              ? 'bg-green-900/20 border border-green-500/30 cursor-pointer'
              : 'bg-gray-800/50 hover:bg-gray-800 cursor-pointer'
          }`}
        >
          <div className={`w-10 h-10 rounded-lg flex items-center justify-center bg-gradient-to-br ${
            LAYER_COLORS[layer.layer_type] || 'from-gray-500 to-gray-600'
          }`}>
            {LAYER_ICONS[layer.layer_type] || <Circle className="w-5 h-5" />}
          </div>
          
          <div className="flex-1">
            <div className="font-medium text-white text-sm">{layer.title}</div>
            <div className="text-xs text-gray-400">{layer.estimated_minutes} dk</div>
          </div>
          
          <div className="flex items-center gap-2">
            {isCompleted && layer.score !== null && (
              <span className="text-green-400 text-sm font-medium">{layer.score.toFixed(0)}%</span>
            )}
            {isLocked && <Lock className="w-4 h-4 text-gray-500" />}
            {isCurrent && (
              <motion.div
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ repeat: Infinity, duration: 1.5 }}
              >
                <Play className="w-5 h-5 text-purple-400" />
              </motion.div>
            )}
            {isCompleted && <CheckCircle className="w-5 h-5 text-green-400" />}
          </div>
        </motion.div>
      );
    })}
  </div>
);

// Katman içerik görüntüleyici
const LayerContent: React.FC<{
  layer: Layer;
  packageName: string;
  onComplete: (score: number) => void;
  onSubmitFeynman?: (data: any) => void;
}> = ({ layer, packageName, onComplete, onSubmitFeynman }) => {
  const [answer, setAnswer] = useState<string>('');
  const [showHint, setShowHint] = useState(false);
  const [feynmanText, setFeynmanText] = useState('');
  const [feynmanAudience, setFeynmanAudience] = useState('child');

  const handleComplete = () => {
    // Basit skor hesaplama
    const score = answer.length > 20 ? 90 : answer.length > 10 ? 75 : 60;
    onComplete(score);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className={`p-6 rounded-2xl bg-gradient-to-r ${LAYER_COLORS[layer.layer_type] || 'from-gray-600 to-gray-700'}`}>
        <div className="flex items-center gap-3 mb-2">
          <div className="w-12 h-12 rounded-xl bg-white/20 flex items-center justify-center">
            {LAYER_ICONS[layer.layer_type]}
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">{layer.title}</h2>
            <p className="text-white/80">{packageName}</p>
          </div>
        </div>
        <p className="text-white/90 mt-4">{layer.description}</p>
        <div className="flex items-center gap-4 mt-4 text-white/70 text-sm">
          <span className="flex items-center gap-1">
            <Clock className="w-4 h-4" />
            {layer.estimated_minutes} dakika
          </span>
        </div>
      </div>

      {/* Content based on layer type */}
      <div className="bg-gray-800/50 rounded-2xl p-6 border border-gray-700/50">
        {layer.layer_type === 'warmup' && (
          <div className="space-y-4">
            <h3 className="font-semibold text-white">🔥 Hafıza Aktivasyonu</h3>
            <p className="text-gray-300">{layer.content?.recall_prompt}</p>
            {layer.content?.brain_activation && (
              <div className="bg-yellow-900/30 border border-yellow-500/30 rounded-xl p-4">
                <p className="text-yellow-200">{layer.content.brain_activation.question}</p>
              </div>
            )}
          </div>
        )}

        {layer.layer_type === 'prime' && (
          <div className="space-y-4">
            <h3 className="font-semibold text-white">💡 Bu Pakette Öğreneceklerin</h3>
            <ul className="space-y-2">
              {layer.content?.learning_objectives?.map((obj: string, i: number) => (
                <li key={i} className="flex items-center gap-2 text-gray-300">
                  <Star className="w-4 h-4 text-yellow-400" />
                  {obj}
                </li>
              ))}
            </ul>
            <div className="bg-blue-900/30 border border-blue-500/30 rounded-xl p-4">
              <p className="text-blue-200">{layer.content?.curiosity_question}</p>
            </div>
          </div>
        )}

        {layer.layer_type === 'feynman' && (
          <div className="space-y-4">
            <h3 className="font-semibold text-white">🎤 Feynman Tekniği</h3>
            <p className="text-gray-300">Öğrendiklerini kendi kelimelerinle açıkla. Hedef kitleni seç:</p>
            
            <div className="flex gap-2">
              {layer.content?.target_audiences?.map((aud: any) => (
                <button
                  key={aud.id}
                  onClick={() => setFeynmanAudience(aud.id)}
                  className={`px-4 py-2 rounded-xl transition-all ${
                    feynmanAudience === aud.id
                      ? 'bg-pink-500 text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  {aud.label} (+{aud.bonus_xp} XP)
                </button>
              ))}
            </div>
            
            <div className="space-y-2">
              <label className="text-sm text-gray-400">Açıklaman:</label>
              <textarea
                value={feynmanText}
                onChange={(e) => setFeynmanText(e.target.value)}
                className="w-full h-40 bg-gray-900 border border-gray-600 rounded-xl p-4 text-white resize-none focus:border-pink-500 focus:outline-none"
                placeholder="Bu konuyu bir çocuğa anlatıyormuş gibi yaz..."
              />
            </div>
            
            <div className="bg-pink-900/30 border border-pink-500/30 rounded-xl p-4">
              <h4 className="font-medium text-pink-200 mb-2">Kontrol Listesi:</h4>
              <ul className="space-y-1 text-sm text-pink-200/80">
                {layer.content?.checklist?.map((item: string, i: number) => (
                  <li key={i} className="flex items-center gap-2">
                    <Circle className="w-3 h-3" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Questions */}
        {layer.questions && layer.questions.length > 0 && (
          <div className="mt-6 space-y-4">
            <h3 className="font-semibold text-white">📝 Sorular</h3>
            {layer.questions.map((q, i) => (
              <div key={q.id} className="bg-gray-900/50 rounded-xl p-4 border border-gray-600/50">
                <div className="flex justify-between items-start mb-3">
                  <span className="text-gray-300">{q.question_text}</span>
                  <span className="text-xs bg-purple-900/50 text-purple-300 px-2 py-1 rounded-lg">
                    {q.points} XP
                  </span>
                </div>
                
                {q.question_type === 'multiple_choice' && q.options && (
                  <div className="space-y-2">
                    {q.options.map((opt, j) => (
                      <button
                        key={j}
                        onClick={() => setAnswer(opt)}
                        className={`w-full text-left p-3 rounded-lg transition-all ${
                          answer === opt
                            ? 'bg-purple-500 text-white'
                            : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                        }`}
                      >
                        {opt}
                      </button>
                    ))}
                  </div>
                )}
                
                {q.question_type === 'free_text' && (
                  <textarea
                    value={answer}
                    onChange={(e) => setAnswer(e.target.value)}
                    className="w-full h-24 bg-gray-800 border border-gray-600 rounded-lg p-3 text-white resize-none focus:border-purple-500 focus:outline-none"
                    placeholder="Cevabını yaz..."
                  />
                )}
                
                {q.hints && q.hints.length > 0 && (
                  <div className="mt-3">
                    <button
                      onClick={() => setShowHint(!showHint)}
                      className="text-sm text-amber-400 hover:text-amber-300 flex items-center gap-1"
                    >
                      <Lightbulb className="w-4 h-4" />
                      {showHint ? 'İpucunu gizle' : 'İpucu göster'}
                    </button>
                    {showHint && (
                      <p className="mt-2 text-sm text-amber-200/80 bg-amber-900/30 rounded-lg p-3">
                        {q.hints[0]}
                      </p>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Complete button */}
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={handleComplete}
        className="w-full py-4 rounded-xl bg-gradient-to-r from-green-500 to-emerald-500 text-white font-semibold flex items-center justify-center gap-2"
      >
        <CheckCircle className="w-5 h-5" />
        Katmanı Tamamla
      </motion.button>
    </div>
  );
};

// Yeni Workspace oluşturma modalı
const CreateWorkspaceModal: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  onCreate: (data: any) => void;
  onCreateDemo: () => void;
}> = ({ isOpen, onClose, onCreate, onCreateDemo }) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [targetGoal, setTargetGoal] = useState('');

  if (!isOpen) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
        className="bg-gray-900 rounded-2xl p-6 w-full max-w-lg border border-gray-700"
      >
        <h2 className="text-xl font-bold text-white mb-6">🎓 Yeni Öğrenme Yolculuğu</h2>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Konu / Alan</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full bg-gray-800 border border-gray-600 rounded-xl p-3 text-white focus:border-purple-500 focus:outline-none"
              placeholder="ör: Python Programlama, Makine Öğrenimi..."
            />
          </div>
          
          <div>
            <label className="block text-sm text-gray-400 mb-1">Açıklama (opsiyonel)</label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full bg-gray-800 border border-gray-600 rounded-xl p-3 text-white focus:border-purple-500 focus:outline-none"
              placeholder="Bu yolculukta neler öğreneceksin?"
            />
          </div>
          
          <div>
            <label className="block text-sm text-gray-400 mb-1">Hedef</label>
            <input
              type="text"
              value={targetGoal}
              onChange={(e) => setTargetGoal(e.target.value)}
              className="w-full bg-gray-800 border border-gray-600 rounded-xl p-3 text-white focus:border-purple-500 focus:outline-none"
              placeholder="ör: Kendi web sitemi yapabilecek seviyeye gelmek"
            />
          </div>
        </div>
        
        <div className="flex gap-3 mt-6">
          <button
            onClick={onClose}
            className="flex-1 py-3 rounded-xl bg-gray-700 text-gray-300 hover:bg-gray-600 transition-colors"
          >
            İptal
          </button>
          <button
            onClick={() => onCreate({ name, description, target_goal: targetGoal })}
            disabled={!name || !targetGoal}
            className="flex-1 py-3 rounded-xl bg-gradient-to-r from-purple-500 to-indigo-500 text-white font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Oluştur
          </button>
        </div>
        
        <div className="mt-4 pt-4 border-t border-gray-700">
          <button
            onClick={onCreateDemo}
            className="w-full py-3 rounded-xl border border-dashed border-gray-600 text-gray-400 hover:text-white hover:border-gray-500 transition-colors flex items-center justify-center gap-2"
          >
            <Sparkles className="w-5 h-5" />
            Demo Workspace Oluştur (Deep Learning)
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function FullMetaPanel() {
  // State
  const [view, setView] = useState<'list' | 'workspace' | 'package' | 'layer'>('list');
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [selectedWorkspace, setSelectedWorkspace] = useState<Workspace | null>(null);
  const [selectedPackage, setSelectedPackage] = useState<Package | null>(null);
  const [layers, setLayers] = useState<Layer[]>([]);
  const [currentLayer, setCurrentLayer] = useState<Layer | null>(null);
  const [expandedStages, setExpandedStages] = useState<Set<string>>(new Set());
  const [layerTypes, setLayerTypes] = useState<LayerTypeInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Load workspaces
  useEffect(() => {
    loadWorkspaces();
    loadLayerTypes();
  }, []);

  const loadWorkspaces = async () => {
    setLoading(true);
    try {
      const data = await fetchWorkspaces();
      setWorkspaces(data);
    } catch (error) {
      console.error('Failed to load workspaces:', error);
    }
    setLoading(false);
  };

  const loadLayerTypes = async () => {
    try {
      const types = await fetchLayerTypes();
      setLayerTypes(types);
    } catch (error) {
      console.error('Failed to load layer types:', error);
    }
  };

  const handleSelectWorkspace = async (ws: Workspace) => {
    try {
      const details = await fetchWorkspaceDetails(ws.id);
      if (details) {
        setSelectedWorkspace(details);
        setView('workspace');
        // Auto-expand first stage
        if (details.stages && details.stages.length > 0) {
          setExpandedStages(new Set([details.stages[0].id]));
        }
      }
    } catch (error) {
      console.error('Failed to load workspace details:', error);
    }
  };

  const handleSelectPackage = async (pkg: Package) => {
    setSelectedPackage(pkg);
    try {
      // Start package if not started
      if (pkg.status === 'available') {
        await startPackage(pkg.id);
      }
      
      // Load layers
      const layersData = await fetchAllLayers(pkg.id);
      setLayers(layersData);
      
      // Load current layer
      const current = await fetchCurrentLayer(pkg.id);
      if (current && current.layer) {
        setCurrentLayer(current.layer);
      }
      
      setView('package');
    } catch (error) {
      console.error('Failed to load package:', error);
    }
  };

  const handleSelectLayer = (layer: Layer, index: number) => {
    if (!layer.is_locked) {
      setCurrentLayer(layer);
      setView('layer');
    }
  };

  const handleCompleteLayer = async (score: number) => {
    if (!selectedPackage) return;
    
    try {
      const result = await completeLayer(selectedPackage.id, score);
      
      if (result.success) {
        // Reload layers
        const layersData = await fetchAllLayers(selectedPackage.id);
        setLayers(layersData);
        
        // If there's a next layer, load it
        if (result.result.next_layer_index < layersData.length) {
          const nextLayer = layersData[result.result.next_layer_index];
          setCurrentLayer(nextLayer);
        } else {
          // Package completed
          setView('package');
          setCurrentLayer(null);
        }
      }
    } catch (error) {
      console.error('Failed to complete layer:', error);
    }
  };

  const handleCreateWorkspace = async (data: any) => {
    try {
      const result = await createWorkspace(data);
      if (result.success) {
        setShowCreateModal(false);
        loadWorkspaces();
      }
    } catch (error) {
      console.error('Failed to create workspace:', error);
    }
  };

  const handleCreateDemo = async () => {
    try {
      const result = await createDemoWorkspace();
      if (result.success) {
        setShowCreateModal(false);
        loadWorkspaces();
      }
    } catch (error) {
      console.error('Failed to create demo:', error);
    }
  };

  const toggleStage = (stageId: string) => {
    const newExpanded = new Set(expandedStages);
    if (newExpanded.has(stageId)) {
      newExpanded.delete(stageId);
    } else {
      newExpanded.add(stageId);
    }
    setExpandedStages(newExpanded);
  };

  // Render based on current view
  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-gray-900 via-gray-900 to-gray-800">
      {/* Header */}
      <div className="p-6 border-b border-gray-700/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {view !== 'list' && (
              <button
                onClick={() => {
                  if (view === 'layer') setView('package');
                  else if (view === 'package') setView('workspace');
                  else setView('list');
                }}
                className="p-2 rounded-xl bg-gray-800 hover:bg-gray-700 transition-colors"
              >
                <ChevronRight className="w-5 h-5 text-gray-400 rotate-180" />
              </button>
            )}
            <div>
              <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                <GraduationCap className="w-7 h-7 text-purple-400" />
                AI ile Öğren
              </h1>
              <p className="text-sm text-gray-400">Nöro-Adaptif Mastery Sistemi</p>
            </div>
          </div>
          
          {view === 'list' && (
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setShowCreateModal(true)}
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
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}
            >
              <RefreshCw className="w-8 h-8 text-purple-400" />
            </motion.div>
          </div>
        ) : (
          <AnimatePresence mode="wait">
            {/* Workspace List View */}
            {view === 'list' && (
              <motion.div
                key="list"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-6"
              >
                {workspaces.length === 0 ? (
                  <div className="text-center py-16">
                    <GraduationCap className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                    <h2 className="text-xl font-semibold text-white mb-2">
                      Henüz bir öğrenme yolculuğun yok
                    </h2>
                    <p className="text-gray-400 mb-6">
                      Yeni bir yolculuk başlat veya demo workspace&apos;i dene
                    </p>
                    <button
                      onClick={() => setShowCreateModal(true)}
                      className="px-6 py-3 rounded-xl bg-gradient-to-r from-purple-500 to-indigo-500 text-white font-medium"
                    >
                      İlk Yolculuğunu Başlat
                    </button>
                  </div>
                ) : (
                  <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {workspaces.map((ws) => (
                      <WorkspaceCard key={ws.id} workspace={ws} onSelect={handleSelectWorkspace} />
                    ))}
                  </div>
                )}
              </motion.div>
            )}

            {/* Workspace Detail View */}
            {view === 'workspace' && selectedWorkspace && (
              <motion.div
                key="workspace"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-6"
              >
                {/* Stats Row */}
                <div className="grid md:grid-cols-3 gap-4">
                  <XPIndicator xp={selectedWorkspace.total_xp} level={selectedWorkspace.level} />
                  <StreakIndicator days={selectedWorkspace.streak_days} />
                  <div className="bg-gradient-to-r from-green-900/50 to-emerald-900/50 rounded-xl p-4 border border-green-500/30">
                    <div className="text-2xl font-bold text-green-400">
                      {selectedWorkspace.overall_progress.toFixed(1)}%
                    </div>
                    <div className="text-sm text-green-200">Genel İlerleme</div>
                  </div>
                </div>

                {/* Workspace Info */}
                <div className="bg-gray-800/50 rounded-2xl p-6 border border-gray-700/50">
                  <h2 className="text-xl font-bold text-white mb-2">{selectedWorkspace.name}</h2>
                  <p className="text-gray-400 mb-4">🎯 Hedef: {selectedWorkspace.target_goal}</p>
                </div>

                {/* Stages */}
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                    <Map className="w-5 h-5 text-indigo-400" />
                    Öğrenme Yol Haritası
                  </h3>
                  
                  {selectedWorkspace.stages?.map((stage) => (
                    <StageSection
                      key={stage.id}
                      stage={stage}
                      isExpanded={expandedStages.has(stage.id)}
                      onToggle={() => toggleStage(stage.id)}
                      onSelectPackage={handleSelectPackage}
                    />
                  ))}
                </div>
              </motion.div>
            )}

            {/* Package View */}
            {view === 'package' && selectedPackage && (
              <motion.div
                key="package"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="max-w-3xl mx-auto space-y-6"
              >
                {/* Package Header */}
                <div className="bg-gradient-to-r from-blue-900/50 to-indigo-900/50 rounded-2xl p-6 border border-blue-500/30">
                  <h2 className="text-xl font-bold text-white mb-2">{selectedPackage.name}</h2>
                  <p className="text-gray-300 mb-4">{selectedPackage.description}</p>
                  <div className="flex items-center gap-4 text-sm text-gray-400">
                    <span>{selectedPackage.concepts_count} kavram</span>
                    <span>•</span>
                    <span>{selectedPackage.layers_count} katman</span>
                    {selectedPackage.xp_earned > 0 && (
                      <>
                        <span>•</span>
                        <span className="text-amber-400">{selectedPackage.xp_earned} XP kazanıldı</span>
                      </>
                    )}
                  </div>
                </div>

                {/* 12 Layers */}
                <div>
                  <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <Layers className="w-5 h-5 text-purple-400" />
                    12 Katmanlı Öğrenme
                  </h3>
                  <LayerList
                    layers={layers}
                    currentIndex={selectedPackage.current_layer_index}
                    onSelectLayer={handleSelectLayer}
                  />
                </div>
              </motion.div>
            )}

            {/* Layer Content View */}
            {view === 'layer' && currentLayer && selectedPackage && (
              <motion.div
                key="layer"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="max-w-3xl mx-auto"
              >
                <LayerContent
                  layer={currentLayer}
                  packageName={selectedPackage.name}
                  onComplete={handleCompleteLayer}
                />
              </motion.div>
            )}
          </AnimatePresence>
        )}
      </div>

      {/* Create Modal */}
      <AnimatePresence>
        {showCreateModal && (
          <CreateWorkspaceModal
            isOpen={showCreateModal}
            onClose={() => setShowCreateModal(false)}
            onCreate={handleCreateWorkspace}
            onCreateDemo={handleCreateDemo}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
