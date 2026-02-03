'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import dynamic from 'next/dynamic';
import type { ComponentType } from 'react';
import { cn } from '@/lib/utils';

// Dynamic icon imports
const Network = dynamic(() => import('lucide-react').then(mod => mod.Network), { ssr: false }) as ComponentType<any>;
const Orbit = dynamic(() => import('lucide-react').then(mod => mod.Orbit), { ssr: false }) as ComponentType<any>;
const GitBranch = dynamic(() => import('lucide-react').then(mod => mod.GitBranch), { ssr: false }) as ComponentType<any>;
const CircleDot = dynamic(() => import('lucide-react').then(mod => mod.CircleDot), { ssr: false }) as ComponentType<any>;
const Clock = dynamic(() => import('lucide-react').then(mod => mod.Clock), { ssr: false }) as ComponentType<any>;
const Sparkles = dynamic(() => import('lucide-react').then(mod => mod.Sparkles), { ssr: false }) as ComponentType<any>;

export type ViewMode = '2d' | '3d' | 'hierarchical' | 'radial' | 'timeline';
export type LayoutType = 'force' | 'hierarchical' | 'radial' | 'timeline';

interface ViewOption {
  id: ViewMode;
  label: string;
  labelEn: string;
  icon: 'Network' | 'Orbit' | 'GitBranch' | 'CircleDot' | 'Clock';
  description: string;
  descriptionEn: string;
  isPremium?: boolean;
  gradient: string;
}

const VIEW_OPTIONS: ViewOption[] = [
  {
    id: '2d',
    label: 'Klasik 2D',
    labelEn: 'Classic 2D',
    icon: 'Network',
    description: 'Standart graf görünümü',
    descriptionEn: 'Standard graph view',
    gradient: 'from-slate-500 to-slate-600',
  },
  {
    id: '3d',
    label: '3D Galaksi',
    labelEn: '3D Galaxy',
    icon: 'Orbit',
    description: 'Kozmik 3D deneyim',
    descriptionEn: 'Cosmic 3D experience',
    isPremium: true,
    gradient: 'from-purple-500 to-pink-600',
  },
  {
    id: 'hierarchical',
    label: 'Hiyerarşik',
    labelEn: 'Hierarchical',
    icon: 'GitBranch',
    description: 'Ağaç yapısı görünümü',
    descriptionEn: 'Tree structure view',
    gradient: 'from-blue-500 to-cyan-600',
  },
  {
    id: 'radial',
    label: 'Radyal',
    labelEn: 'Radial',
    icon: 'CircleDot',
    description: 'Dairesel yerleşim',
    descriptionEn: 'Circular layout',
    gradient: 'from-emerald-500 to-teal-600',
  },
  {
    id: 'timeline',
    label: 'Zaman Çizelgesi',
    labelEn: 'Timeline',
    icon: 'Clock',
    description: 'Kronolojik görünüm',
    descriptionEn: 'Chronological view',
    gradient: 'from-amber-500 to-orange-600',
  },
];

const ICON_MAP: Record<string, ComponentType<any>> = {
  Network,
  Orbit,
  GitBranch,
  CircleDot,
  Clock,
};

interface ViewModeSelectorProps {
  currentMode: ViewMode;
  onModeChange: (mode: ViewMode) => void;
  language?: 'tr' | 'en' | 'de';
  className?: string;
  compact?: boolean;
}

export const ViewModeSelector: React.FC<ViewModeSelectorProps> = ({
  currentMode,
  onModeChange,
  language = 'tr',
  className = '',
  compact = false,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const currentOption = VIEW_OPTIONS.find(o => o.id === currentMode) || VIEW_OPTIONS[0];
  const CurrentIcon = ICON_MAP[currentOption.icon];

  const getText = (option: ViewOption, field: 'label' | 'description') => {
    if (language === 'en') {
      return field === 'label' ? option.labelEn : option.descriptionEn;
    }
    return field === 'label' ? option.label : option.description;
  };

  if (compact) {
    return (
      <div className={cn("flex gap-1", className)}>
        {VIEW_OPTIONS.map(option => {
          const IconComponent = ICON_MAP[option.icon];
          const isActive = currentMode === option.id;

          return (
            <motion.button
              key={option.id}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => onModeChange(option.id)}
              className={cn(
                "relative p-2 rounded-lg transition-all duration-300",
                isActive
                  ? `bg-gradient-to-r ${option.gradient} text-white shadow-lg`
                  : "bg-white/5 text-slate-400 hover:bg-white/10 hover:text-white"
              )}
              title={getText(option, 'label')}
            >
              {IconComponent && <IconComponent className="w-4 h-4" />}
              
              {option.isPremium && !isActive && (
                <Sparkles className="absolute -top-1 -right-1 w-3 h-3 text-yellow-400" />
              )}
            </motion.button>
          );
        })}
      </div>
    );
  }

  return (
    <div className={cn("relative", className)}>
      {/* Current Mode Button */}
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={() => setIsExpanded(!isExpanded)}
        className={cn(
          "flex items-center gap-3 px-4 py-2.5 rounded-xl w-full",
          "bg-gradient-to-r backdrop-blur-xl border transition-all",
          `${currentOption.gradient} border-white/20`,
          "text-white shadow-lg"
        )}
      >
        {CurrentIcon && <CurrentIcon className="w-5 h-5" />}
        <div className="flex-1 text-left">
          <div className="font-medium text-sm">{getText(currentOption, 'label')}</div>
          <div className="text-xs opacity-75">{getText(currentOption, 'description')}</div>
        </div>
        {currentOption.isPremium && (
          <Sparkles className="w-4 h-4 text-yellow-300" />
        )}
      </motion.button>

      {/* Dropdown */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            className="absolute top-full left-0 right-0 mt-2 z-50"
          >
            <div className="backdrop-blur-2xl bg-slate-900/95 rounded-xl border border-white/10 overflow-hidden shadow-2xl">
              {VIEW_OPTIONS.map((option, index) => {
                const IconComponent = ICON_MAP[option.icon];
                const isActive = currentMode === option.id;

                return (
                  <motion.button
                    key={option.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                    onClick={() => {
                      onModeChange(option.id);
                      setIsExpanded(false);
                    }}
                    className={cn(
                      "flex items-center gap-3 px-4 py-3 w-full text-left transition-all",
                      isActive
                        ? `bg-gradient-to-r ${option.gradient} text-white`
                        : "text-slate-300 hover:bg-white/5 hover:text-white"
                    )}
                  >
                    <div
                      className={cn(
                        "p-2 rounded-lg",
                        isActive
                          ? "bg-white/20"
                          : "bg-white/5"
                      )}
                    >
                      {IconComponent && <IconComponent className="w-4 h-4" />}
                    </div>
                    <div className="flex-1">
                      <div className="font-medium text-sm flex items-center gap-2">
                        {getText(option, 'label')}
                        {option.isPremium && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-yellow-500/20 text-yellow-300 font-semibold">
                            PREMIUM
                          </span>
                        )}
                      </div>
                      <div className="text-xs opacity-60">{getText(option, 'description')}</div>
                    </div>
                    {isActive && (
                      <div className="w-2 h-2 rounded-full bg-white" />
                    )}
                  </motion.button>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Click outside handler */}
      {isExpanded && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={() => setIsExpanded(false)}
        />
      )}
    </div>
  );
};

export default ViewModeSelector;
