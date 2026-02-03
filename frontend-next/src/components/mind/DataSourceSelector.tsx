'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import dynamic from 'next/dynamic';
import type { ComponentType } from 'react';
import { cn } from '@/lib/utils';

// Dynamic icon imports
const StickyNote = dynamic(() => import('lucide-react').then(mod => mod.StickyNote), { ssr: false }) as ComponentType<any>;
const FileText = dynamic(() => import('lucide-react').then(mod => mod.FileText), { ssr: false }) as ComponentType<any>;
const MessageSquare = dynamic(() => import('lucide-react').then(mod => mod.MessageSquare), { ssr: false }) as ComponentType<any>;
const Calendar = dynamic(() => import('lucide-react').then(mod => mod.Calendar), { ssr: false }) as ComponentType<any>;
const Database = dynamic(() => import('lucide-react').then(mod => mod.Database), { ssr: false }) as ComponentType<any>;
const ChevronDown = dynamic(() => import('lucide-react').then(mod => mod.ChevronDown), { ssr: false }) as ComponentType<any>;
const ChevronUp = dynamic(() => import('lucide-react').then(mod => mod.ChevronUp), { ssr: false }) as ComponentType<any>;
const Sparkles = dynamic(() => import('lucide-react').then(mod => mod.Sparkles), { ssr: false }) as ComponentType<any>;
const Layers = dynamic(() => import('lucide-react').then(mod => mod.Layers), { ssr: false }) as ComponentType<any>;

export interface DataSource {
  id: 'notes' | 'documents' | 'chat' | 'calendar';
  name: string;
  nameEn: string;
  description: string;
  descriptionEn: string;
  icon: 'StickyNote' | 'FileText' | 'MessageSquare' | 'Calendar';
  color: string;
  gradient: string;
  count?: number;
  isActive: boolean;
}

interface DataSourceSelectorProps {
  sources: DataSource[];
  onSourceToggle: (sourceId: DataSource['id']) => void;
  onSourcesChange?: (sources: DataSource[]) => void;
  language?: 'tr' | 'en' | 'de';
  className?: string;
  compact?: boolean;
}

const ICON_MAP: Record<string, ComponentType<any>> = {
  StickyNote,
  FileText,
  MessageSquare,
  Calendar,
};

export const defaultDataSources: DataSource[] = [
  {
    id: 'notes',
    name: 'Notlarım',
    nameEn: 'My Notes',
    description: 'Tüm notlarınız ve klasörleriniz',
    descriptionEn: 'All your notes and folders',
    icon: 'StickyNote',
    color: '#8b5cf6',
    gradient: 'from-violet-500 to-purple-600',
    isActive: true,
  },
  {
    id: 'documents',
    name: 'Dökümanlar',
    nameEn: 'Documents',
    description: 'Yüklenmiş PDF, Word ve diğer dosyalar',
    descriptionEn: 'Uploaded PDFs, Word docs and other files',
    icon: 'FileText',
    color: '#3b82f6',
    gradient: 'from-blue-500 to-cyan-600',
    isActive: false,
  },
  {
    id: 'chat',
    name: 'Sohbet Geçmişi',
    nameEn: 'Chat History',
    description: 'AI ile olan tüm konuşmalarınız',
    descriptionEn: 'All your conversations with AI',
    icon: 'MessageSquare',
    color: '#10b981',
    gradient: 'from-emerald-500 to-teal-600',
    isActive: false,
  },
  {
    id: 'calendar',
    name: 'Takvim',
    nameEn: 'Calendar',
    description: 'Planlarınız ve etkinlikleriniz',
    descriptionEn: 'Your plans and events',
    icon: 'Calendar',
    color: '#f59e0b',
    gradient: 'from-amber-500 to-orange-600',
    isActive: false,
  },
];

export const DataSourceSelector: React.FC<DataSourceSelectorProps> = ({
  sources,
  onSourceToggle,
  onSourcesChange,
  language = 'tr',
  className = '',
  compact = false,
}) => {
  const [isExpanded, setIsExpanded] = useState(!compact);
  const [hoveredSource, setHoveredSource] = useState<string | null>(null);

  const activeCount = sources.filter(s => s.isActive).length;

  const getText = (source: DataSource, field: 'name' | 'description') => {
    if (language === 'en') {
      return field === 'name' ? source.nameEn : source.descriptionEn;
    }
    return field === 'name' ? source.name : source.description;
  };

  return (
    <motion.div
      className={cn(
        "relative backdrop-blur-2xl rounded-2xl border transition-all duration-300",
        "bg-gradient-to-br from-slate-900/90 via-slate-800/90 to-slate-900/90",
        "border-white/10 shadow-xl",
        isExpanded ? "p-4" : "p-2",
        className
      )}
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {/* Header */}
      <div 
        className={cn(
          "flex items-center justify-between cursor-pointer",
          isExpanded ? "mb-4" : "mb-0"
        )}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-gradient-to-br from-violet-500/20 to-purple-600/20">
            <Database className="w-4 h-4 text-violet-400" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">
              {language === 'tr' ? 'Veri Kaynakları' : 'Data Sources'}
            </h3>
            {!isExpanded && (
              <p className="text-xs text-slate-400">
                {activeCount} {language === 'tr' ? 'aktif' : 'active'}
              </p>
            )}
          </div>
        </div>
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
        >
          {isExpanded ? (
            <ChevronUp className="w-4 h-4 text-slate-400" />
          ) : (
            <ChevronDown className="w-4 h-4 text-slate-400" />
          )}
        </motion.button>
      </div>

      {/* Collapsed View - Mini Badges */}
      <AnimatePresence>
        {!isExpanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="flex gap-1.5 flex-wrap mt-2"
          >
            {sources.map(source => {
              const IconComponent = ICON_MAP[source.icon];
              return (
                <motion.button
                  key={source.id}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={(e) => {
                    e.stopPropagation();
                    onSourceToggle(source.id);
                  }}
                  className={cn(
                    "flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-medium transition-all",
                    source.isActive
                      ? "bg-gradient-to-r text-white shadow-lg"
                      : "bg-white/5 text-slate-400 hover:bg-white/10"
                  )}
                  style={{
                    backgroundImage: source.isActive
                      ? `linear-gradient(to right, ${source.color}99, ${source.color}66)`
                      : undefined,
                    boxShadow: source.isActive
                      ? `0 0 15px ${source.color}33`
                      : undefined,
                  }}
                >
                  {IconComponent && <IconComponent className="w-3 h-3" />}
                  {source.count !== undefined && (
                    <span className="opacity-75">{source.count}</span>
                  )}
                </motion.button>
              );
            })}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Expanded View - Full Cards */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-2"
          >
            {sources.map((source, index) => {
              const IconComponent = ICON_MAP[source.icon];
              const isHovered = hoveredSource === source.id;

              return (
                <motion.div
                  key={source.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  onMouseEnter={() => setHoveredSource(source.id)}
                  onMouseLeave={() => setHoveredSource(null)}
                  onClick={() => onSourceToggle(source.id)}
                  className={cn(
                    "relative flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-all duration-300",
                    "group overflow-hidden"
                  )}
                  style={{
                    background: source.isActive
                      ? `linear-gradient(135deg, ${source.color}15, ${source.color}05)`
                      : 'rgba(255,255,255,0.02)',
                    borderWidth: 1,
                    borderStyle: 'solid',
                    borderColor: source.isActive
                      ? `${source.color}40`
                      : 'rgba(255,255,255,0.05)',
                    boxShadow: source.isActive && isHovered
                      ? `0 0 30px ${source.color}20, inset 0 0 30px ${source.color}05`
                      : undefined,
                  }}
                >
                  {/* Animated Background Gradient */}
                  {source.isActive && (
                    <motion.div
                      className="absolute inset-0 opacity-20"
                      style={{
                        background: `radial-gradient(circle at ${isHovered ? '30%' : '0%'} 50%, ${source.color}30 0%, transparent 70%)`,
                      }}
                      animate={{
                        background: isHovered
                          ? `radial-gradient(circle at 70% 50%, ${source.color}30 0%, transparent 70%)`
                          : `radial-gradient(circle at 30% 50%, ${source.color}30 0%, transparent 70%)`,
                      }}
                      transition={{ duration: 0.5 }}
                    />
                  )}

                  {/* Icon */}
                  <motion.div
                    className={cn(
                      "relative flex-shrink-0 p-2.5 rounded-xl transition-all duration-300",
                      source.isActive
                        ? `bg-gradient-to-br ${source.gradient} shadow-lg`
                        : "bg-white/5"
                    )}
                    style={{
                      boxShadow: source.isActive
                        ? `0 4px 20px ${source.color}40`
                        : undefined,
                    }}
                    whileHover={{ scale: 1.05, rotate: 5 }}
                  >
                    {IconComponent && (
                      <IconComponent
                        className={cn(
                          "w-5 h-5 transition-colors",
                          source.isActive ? "text-white" : "text-slate-400"
                        )}
                      />
                    )}
                    
                    {/* Sparkle effect when active */}
                    {source.isActive && (
                      <motion.div
                        className="absolute -top-1 -right-1"
                        initial={{ scale: 0, rotate: -45 }}
                        animate={{ scale: 1, rotate: 0 }}
                        transition={{ type: "spring", stiffness: 500 }}
                      >
                        <Sparkles className="w-3 h-3 text-yellow-300" />
                      </motion.div>
                    )}
                  </motion.div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h4
                        className={cn(
                          "font-medium text-sm transition-colors",
                          source.isActive ? "text-white" : "text-slate-300"
                        )}
                      >
                        {getText(source, 'name')}
                      </h4>
                      {source.count !== undefined && (
                        <span
                          className={cn(
                            "px-1.5 py-0.5 rounded-full text-xs font-medium",
                            source.isActive
                              ? "bg-white/20 text-white"
                              : "bg-white/10 text-slate-400"
                          )}
                        >
                          {source.count}
                        </span>
                      )}
                    </div>
                    <p
                      className={cn(
                        "text-xs mt-0.5 truncate transition-colors",
                        source.isActive ? "text-slate-300" : "text-slate-500"
                      )}
                    >
                      {getText(source, 'description')}
                    </p>
                  </div>

                  {/* Toggle Button */}
                  <motion.div
                    className={cn(
                      "relative w-12 h-6 rounded-full p-0.5 transition-all duration-300 cursor-pointer",
                      source.isActive
                        ? `bg-gradient-to-r ${source.gradient}`
                        : "bg-slate-700"
                    )}
                    whileTap={{ scale: 0.95 }}
                  >
                    <motion.div
                      className="w-5 h-5 rounded-full bg-white shadow-lg"
                      animate={{
                        x: source.isActive ? 24 : 0,
                      }}
                      transition={{ type: "spring", stiffness: 500, damping: 30 }}
                    />
                  </motion.div>
                </motion.div>
              );
            })}

            {/* Summary Bar */}
            <motion.div
              className="flex items-center justify-between pt-3 mt-3 border-t border-white/5"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 }}
            >
              <div className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-slate-400" />
                <span className="text-xs text-slate-400">
                  {activeCount} / {sources.length}{' '}
                  {language === 'tr' ? 'kaynak aktif' : 'sources active'}
                </span>
              </div>
              
              {/* Quick toggles */}
              <div className="flex gap-1">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    sources.forEach(s => {
                      if (!s.isActive) onSourceToggle(s.id);
                    });
                  }}
                  className="px-2 py-1 text-xs text-slate-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
                >
                  {language === 'tr' ? 'Tümü' : 'All'}
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    sources.forEach(s => {
                      if (s.isActive && s.id !== 'notes') onSourceToggle(s.id);
                    });
                    if (!sources.find(s => s.id === 'notes')?.isActive) {
                      onSourceToggle('notes');
                    }
                  }}
                  className="px-2 py-1 text-xs text-slate-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
                >
                  {language === 'tr' ? 'Sadece Notlar' : 'Notes Only'}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default DataSourceSelector;
