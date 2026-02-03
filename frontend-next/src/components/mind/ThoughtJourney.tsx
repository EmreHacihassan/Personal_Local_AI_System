'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import dynamic from 'next/dynamic';
import type { ComponentType } from 'react';
import { cn } from '@/lib/utils';
import type { UnifiedMindNode } from '@/hooks/useMindData';

// Dynamic icon imports
const Play = dynamic(() => import('lucide-react').then(mod => mod.Play), { ssr: false }) as ComponentType<any>;
const Pause = dynamic(() => import('lucide-react').then(mod => mod.Pause), { ssr: false }) as ComponentType<any>;
const SkipBack = dynamic(() => import('lucide-react').then(mod => mod.SkipBack), { ssr: false }) as ComponentType<any>;
const SkipForward = dynamic(() => import('lucide-react').then(mod => mod.SkipForward), { ssr: false }) as ComponentType<any>;
const X = dynamic(() => import('lucide-react').then(mod => mod.X), { ssr: false }) as ComponentType<any>;
const Sparkles = dynamic(() => import('lucide-react').then(mod => mod.Sparkles), { ssr: false }) as ComponentType<any>;
const Film = dynamic(() => import('lucide-react').then(mod => mod.Film), { ssr: false }) as ComponentType<any>;
const Route = dynamic(() => import('lucide-react').then(mod => mod.Route), { ssr: false }) as ComponentType<any>;

interface ThoughtJourneyProps {
  nodes: UnifiedMindNode[];
  onNodeFocus?: (nodeId: string) => void;
  onClose?: () => void;
  isOpen: boolean;
  language?: 'tr' | 'en' | 'de';
}

interface JourneyStep {
  nodeId: string;
  node: UnifiedMindNode;
  duration: number;
  narration?: string;
}

// Calculate journey path through nodes
const calculateJourneyPath = (nodes: UnifiedMindNode[]): JourneyStep[] => {
  if (nodes.length === 0) return [];

  // Sort by importance: pinned first, then by connection count
  const sorted = [...nodes].sort((a, b) => {
    // Pinned nodes first
    if (a.metadata.pinned && !b.metadata.pinned) return -1;
    if (!a.metadata.pinned && b.metadata.pinned) return 1;
    
    // Then by connection count
    return b.connections.length - a.connections.length;
  });

  // Take top nodes for journey
  const journeyNodes = sorted.slice(0, Math.min(10, sorted.length));

  return journeyNodes.map((node, index) => ({
    nodeId: node.id,
    node,
    duration: 3000 + (node.connections.length * 500), // Longer for connected nodes
    narration: generateNarration(node, index),
  }));
};

// Generate narration text for each step
const generateNarration = (node: UnifiedMindNode, index: number): string => {
  const typeLabels: Record<string, string> = {
    note: 'bir not',
    document: 'bir döküman',
    chat: 'bir sohbet',
    calendar: 'bir etkinlik',
  };

  const typeNarrations: Record<string, string[]> = {
    note: ['Bu notta şu yazıyor:', 'Burada bir düşünce var:', 'Dikkat çekici bir not:'],
    document: ['Bu döküman hakkında:', 'Önemli bir dosya:', 'Bilgi kaynağı:'],
    chat: ['Bu konuşmada:', 'AI ile diyalog:', 'Sohbet geçmişinden:'],
    calendar: ['Takvimdeki bu etkinlik:', 'Planlanmış:', 'Yaklaşan olay:'],
  };

  const narrations = typeNarrations[node.type] || typeNarrations.note;
  const prefix = narrations[index % narrations.length];
  
  return `${prefix} "${node.title}"`;
};

export const ThoughtJourney: React.FC<ThoughtJourneyProps> = ({
  nodes,
  onNodeFocus,
  onClose,
  isOpen,
  language = 'tr',
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(0);
  const [journeyPath, setJourneyPath] = useState<JourneyStep[]>([]);
  const timerRef = useRef<NodeJS.Timeout>();
  const progressRef = useRef<NodeJS.Timeout>();

  // Calculate journey path when nodes change
  useEffect(() => {
    if (isOpen && nodes.length > 0) {
      setJourneyPath(calculateJourneyPath(nodes));
      setCurrentStep(0);
      setProgress(0);
    }
  }, [isOpen, nodes]);

  // Focus on current node
  useEffect(() => {
    if (journeyPath[currentStep]) {
      onNodeFocus?.(journeyPath[currentStep].nodeId);
    }
  }, [currentStep, journeyPath, onNodeFocus]);

  // Auto-advance when playing
  useEffect(() => {
    if (!isPlaying || journeyPath.length === 0) {
      if (timerRef.current) clearTimeout(timerRef.current);
      if (progressRef.current) clearInterval(progressRef.current);
      return;
    }

    const currentDuration = journeyPath[currentStep]?.duration || 3000;
    
    // Progress update
    setProgress(0);
    progressRef.current = setInterval(() => {
      setProgress(prev => Math.min(100, prev + (100 / (currentDuration / 100))));
    }, 100);

    // Auto advance
    timerRef.current = setTimeout(() => {
      if (currentStep < journeyPath.length - 1) {
        setCurrentStep(prev => prev + 1);
      } else {
        setIsPlaying(false);
        setCurrentStep(0);
      }
    }, currentDuration);

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      if (progressRef.current) clearInterval(progressRef.current);
    };
  }, [isPlaying, currentStep, journeyPath]);

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying);
  };

  const handlePrevious = () => {
    setCurrentStep(prev => Math.max(0, prev - 1));
    setProgress(0);
  };

  const handleNext = () => {
    setCurrentStep(prev => Math.min(journeyPath.length - 1, prev + 1));
    setProgress(0);
  };

  const handleClose = () => {
    setIsPlaying(false);
    setCurrentStep(0);
    setProgress(0);
    onClose?.();
  };

  const currentNode = journeyPath[currentStep]?.node;

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 50 }}
          className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50"
        >
          <div className="backdrop-blur-2xl bg-slate-900/90 rounded-2xl border border-white/10 shadow-2xl overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-2 border-b border-white/5">
              <div className="flex items-center gap-2">
                <Film className="w-4 h-4 text-purple-400" />
                <span className="text-sm font-medium text-white">
                  {language === 'tr' ? 'Düşünce Yolculuğu' : 'Thought Journey'}
                </span>
                <Sparkles className="w-3 h-3 text-yellow-400 animate-pulse" />
              </div>
              <button
                onClick={handleClose}
                className="p-1 rounded-lg hover:bg-white/10 transition-colors"
              >
                <X className="w-4 h-4 text-slate-400" />
              </button>
            </div>

            {/* Current Node Info */}
            {currentNode && (
              <motion.div
                key={currentNode.id}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="px-4 py-3 border-b border-white/5"
              >
                <div className="flex items-center gap-3">
                  <div 
                    className="w-3 h-3 rounded-full"
                    style={{
                      backgroundColor: currentNode.type === 'note' ? '#a855f7' :
                                       currentNode.type === 'document' ? '#3b82f6' :
                                       currentNode.type === 'chat' ? '#10b981' : '#f59e0b',
                      boxShadow: `0 0 10px ${currentNode.type === 'note' ? 'rgba(168,85,247,0.5)' :
                                              currentNode.type === 'document' ? 'rgba(59,130,246,0.5)' :
                                              currentNode.type === 'chat' ? 'rgba(16,185,129,0.5)' : 'rgba(245,158,11,0.5)'}`,
                    }}
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-white font-medium truncate max-w-[300px]">
                      {currentNode.title}
                    </p>
                    <p className="text-xs text-slate-400">
                      {journeyPath[currentStep]?.narration}
                    </p>
                  </div>
                  <div className="text-xs text-slate-500">
                    {currentNode.connections.length} {language === 'tr' ? 'bağlantı' : 'connections'}
                  </div>
                </div>
              </motion.div>
            )}

            {/* Progress Bar */}
            <div className="px-4 py-2">
              <div className="relative h-1 bg-slate-700 rounded-full overflow-hidden">
                <motion.div
                  className="absolute left-0 top-0 h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <div className="flex justify-between mt-1 text-[10px] text-slate-500">
                <span>{currentStep + 1} / {journeyPath.length}</span>
                <span>{Math.round((currentStep / Math.max(1, journeyPath.length - 1)) * 100)}%</span>
              </div>
            </div>

            {/* Controls */}
            <div className="flex items-center justify-center gap-2 px-4 py-3">
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                onClick={handlePrevious}
                disabled={currentStep === 0}
                className={cn(
                  "p-2 rounded-lg transition-colors",
                  currentStep === 0
                    ? "text-slate-600 cursor-not-allowed"
                    : "text-slate-300 hover:bg-white/10 hover:text-white"
                )}
              >
                <SkipBack className="w-4 h-4" />
              </motion.button>

              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handlePlayPause}
                className={cn(
                  "p-3 rounded-xl transition-all",
                  isPlaying
                    ? "bg-white/20 text-white"
                    : "bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg"
                )}
              >
                {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
              </motion.button>

              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                onClick={handleNext}
                disabled={currentStep >= journeyPath.length - 1}
                className={cn(
                  "p-2 rounded-lg transition-colors",
                  currentStep >= journeyPath.length - 1
                    ? "text-slate-600 cursor-not-allowed"
                    : "text-slate-300 hover:bg-white/10 hover:text-white"
                )}
              >
                <SkipForward className="w-4 h-4" />
              </motion.button>
            </div>

            {/* Step Indicators */}
            <div className="flex justify-center gap-1 px-4 pb-3">
              {journeyPath.map((_, index) => (
                <button
                  key={index}
                  onClick={() => {
                    setCurrentStep(index);
                    setProgress(0);
                  }}
                  className={cn(
                    "w-2 h-2 rounded-full transition-all",
                    index === currentStep
                      ? "bg-purple-500 w-4"
                      : index < currentStep
                      ? "bg-purple-500/50"
                      : "bg-slate-600"
                  )}
                />
              ))}
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

// Journey Start Button Component
interface JourneyButtonProps {
  onClick: () => void;
  disabled?: boolean;
  language?: 'tr' | 'en' | 'de';
}

export const JourneyButton: React.FC<JourneyButtonProps> = ({
  onClick,
  disabled = false,
  language = 'tr',
}) => {
  return (
    <motion.button
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "flex items-center gap-2 px-4 py-2 rounded-xl",
        "bg-gradient-to-r from-purple-600 to-pink-600",
        "text-white font-medium text-sm",
        "shadow-lg shadow-purple-500/25",
        "transition-all duration-300",
        disabled && "opacity-50 cursor-not-allowed"
      )}
    >
      <Route className="w-4 h-4" />
      <span>{language === 'tr' ? 'Yolculuk Başlat' : 'Start Journey'}</span>
      <Sparkles className="w-3 h-3 text-yellow-300" />
    </motion.button>
  );
};

export default ThoughtJourney;
