'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FiX, FiSave, FiClock, FiType, FiMaximize2, FiMusic, FiVolume2, FiVolumeX } from 'react-icons/fi';

interface ZenModeProps {
  isOpen: boolean;
  onClose: () => void;
  initialContent: string;
  initialTitle: string;
  onSave: (content: string, title: string) => void;
}

const ZenMode: React.FC<ZenModeProps> = ({
  isOpen,
  onClose,
  initialContent,
  initialTitle,
  onSave
}) => {
  const [content, setContent] = useState(initialContent);
  const [title, setTitle] = useState(initialTitle);
  const [wordCount, setWordCount] = useState(0);
  const [charCount, setCharCount] = useState(0);
  const [sessionTime, setSessionTime] = useState(0);
  const [isSaving, setIsSaving] = useState(false);
  const [showControls, setShowControls] = useState(true);
  const [ambientSound, setAmbientSound] = useState<'none' | 'rain' | 'cafe' | 'forest'>('none');
  const [fontSize, setFontSize] = useState<'small' | 'medium' | 'large'>('medium');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const controlsTimeoutRef = useRef<NodeJS.Timeout>();

  // Font size classes
  const fontSizeClasses = {
    small: 'text-lg leading-relaxed',
    medium: 'text-xl leading-relaxed',
    large: 'text-2xl leading-loose'
  };

  // Initialize content when opening
  useEffect(() => {
    if (isOpen) {
      setContent(initialContent);
      setTitle(initialTitle);
      setSessionTime(0);
    }
  }, [isOpen, initialContent, initialTitle]);

  // Word and character count
  useEffect(() => {
    const words = content.trim().split(/\s+/).filter(w => w.length > 0);
    setWordCount(words.length);
    setCharCount(content.length);
  }, [content]);

  // Session timer
  useEffect(() => {
    if (!isOpen) return;
    const timer = setInterval(() => {
      setSessionTime(prev => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, [isOpen]);

  // Auto-hide controls
  const handleMouseMove = useCallback(() => {
    setShowControls(true);
    if (controlsTimeoutRef.current) {
      clearTimeout(controlsTimeoutRef.current);
    }
    controlsTimeoutRef.current = setTimeout(() => {
      setShowControls(false);
    }, 3000);
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        handleSave();
      }
      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, content, title, onClose]);

  // Focus textarea when opened
  useEffect(() => {
    if (isOpen && textareaRef.current) {
      setTimeout(() => {
        textareaRef.current?.focus();
      }, 300);
    }
  }, [isOpen]);

  const handleSave = async () => {
    setIsSaving(true);
    await onSave(content, title);
    setTimeout(() => setIsSaving(false), 500);
  };

  const formatTime = (seconds: number) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    if (hrs > 0) {
      return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Ambient sounds (placeholder - would need actual audio files)
  const ambientSounds = [
    { id: 'none', label: 'Sessiz', icon: <FiVolumeX /> },
    { id: 'rain', label: 'Yağmur', icon: <FiVolume2 /> },
    { id: 'cafe', label: 'Kafe', icon: <FiVolume2 /> },
    { id: 'forest', label: 'Orman', icon: <FiVolume2 /> },
  ];

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.3 }}
        className="fixed inset-0 z-[100] bg-gradient-to-br from-slate-900 via-purple-900/20 to-slate-900"
        onMouseMove={handleMouseMove}
      >
        {/* Ambient Background Animation */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <motion.div
            className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-500/5 rounded-full blur-3xl"
            animate={{
              x: [0, 50, 0],
              y: [0, 30, 0],
              scale: [1, 1.1, 1],
            }}
            transition={{ duration: 20, repeat: Infinity, ease: 'easeInOut' }}
          />
          <motion.div
            className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-indigo-500/5 rounded-full blur-3xl"
            animate={{
              x: [0, -30, 0],
              y: [0, 50, 0],
              scale: [1, 1.2, 1],
            }}
            transition={{ duration: 15, repeat: Infinity, ease: 'easeInOut' }}
          />
        </div>

        {/* Top Controls */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: showControls ? 1 : 0, y: showControls ? 0 : -20 }}
          transition={{ duration: 0.2 }}
          className="absolute top-0 left-0 right-0 flex items-center justify-between px-6 py-4 bg-gradient-to-b from-black/50 to-transparent"
        >
          {/* Left - Session Stats */}
          <div className="flex items-center gap-6 text-white/60">
            <div className="flex items-center gap-2">
              <FiClock className="w-4 h-4" />
              <span className="font-mono">{formatTime(sessionTime)}</span>
            </div>
            <div className="flex items-center gap-2">
              <FiType className="w-4 h-4" />
              <span>{wordCount} kelime</span>
            </div>
            <div className="text-sm text-white/40">
              {charCount} karakter
            </div>
          </div>

          {/* Center - Title */}
          <input
            type="text"
            value={title}
            onChange={e => setTitle(e.target.value)}
            placeholder="Başlık..."
            className="absolute left-1/2 transform -translate-x-1/2 bg-transparent text-xl font-medium text-white/80 text-center focus:outline-none focus:text-white placeholder-white/40 w-80"
          />

          {/* Right - Actions */}
          <div className="flex items-center gap-3">
            {/* Font Size */}
            <div className="flex items-center gap-1 bg-white/10 rounded-lg p-1">
              {(['small', 'medium', 'large'] as const).map(size => (
                <button
                  key={size}
                  onClick={() => setFontSize(size)}
                  className={`px-2 py-1 rounded text-xs transition-all ${
                    fontSize === size
                      ? 'bg-white/20 text-white'
                      : 'text-white/50 hover:text-white'
                  }`}
                >
                  {size === 'small' ? 'A' : size === 'medium' ? 'A' : 'A'}
                  <span className="sr-only">{size}</span>
                </button>
              ))}
            </div>

            {/* Ambient Sound */}
            <div className="flex items-center gap-1 bg-white/10 rounded-lg p-1">
              {ambientSounds.map(sound => (
                <button
                  key={sound.id}
                  onClick={() => setAmbientSound(sound.id as typeof ambientSound)}
                  className={`px-2 py-1 rounded text-xs transition-all ${
                    ambientSound === sound.id
                      ? 'bg-white/20 text-white'
                      : 'text-white/50 hover:text-white'
                  }`}
                  title={sound.label}
                >
                  {sound.icon}
                </button>
              ))}
            </div>

            {/* Save */}
            <motion.button
              onClick={handleSave}
              disabled={isSaving}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-500 to-indigo-500 text-white rounded-lg hover:from-purple-600 hover:to-indigo-600 transition-all disabled:opacity-50"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <FiSave className={isSaving ? 'animate-pulse' : ''} />
              {isSaving ? 'Kaydediliyor...' : 'Kaydet'}
            </motion.button>

            {/* Close */}
            <button
              onClick={onClose}
              className="p-2 text-white/50 hover:text-white hover:bg-white/10 rounded-lg transition-all"
            >
              <FiX className="w-5 h-5" />
            </button>
          </div>
        </motion.div>

        {/* Main Writing Area */}
        <div className="absolute inset-0 flex items-center justify-center pt-20 pb-16 px-4">
          <div className="w-full max-w-3xl h-full">
            <textarea
              ref={textareaRef}
              value={content}
              onChange={e => setContent(e.target.value)}
              placeholder="Yazmaya başlayın..."
              className={`w-full h-full bg-transparent text-white/90 placeholder-white/30 focus:outline-none resize-none ${fontSizeClasses[fontSize]}`}
              style={{
                fontFamily: "'Georgia', 'Times New Roman', serif",
                lineHeight: '1.8',
              }}
            />
          </div>
        </div>

        {/* Bottom Status Bar */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: showControls ? 1 : 0, y: showControls ? 0 : 20 }}
          transition={{ duration: 0.2 }}
          className="absolute bottom-0 left-0 right-0 flex items-center justify-center py-4 bg-gradient-to-t from-black/50 to-transparent"
        >
          <div className="flex items-center gap-8 text-white/40 text-sm">
            <span>🧘 Zen Mode</span>
            <span className="flex items-center gap-1">
              <kbd className="px-1.5 py-0.5 bg-white/10 rounded text-xs">Ctrl+S</kbd>
              Kaydet
            </span>
            <span className="flex items-center gap-1">
              <kbd className="px-1.5 py-0.5 bg-white/10 rounded text-xs">ESC</kbd>
              Çık
            </span>
          </div>
        </motion.div>

        {/* Session Goal Progress (Optional) */}
        {wordCount > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: showControls ? 0.5 : 0 }}
            className="absolute bottom-20 left-1/2 transform -translate-x-1/2"
          >
            <div className="text-center text-white/40 text-sm">
              {wordCount >= 500 ? (
                <span className="text-green-400">🎉 500+ kelime! Harika gidiyorsun!</span>
              ) : wordCount >= 250 ? (
                <span className="text-blue-400">💪 Yarı yoldasın, devam et!</span>
              ) : wordCount >= 100 ? (
                <span>✨ İyi bir başlangıç!</span>
              ) : null}
            </div>
          </motion.div>
        )}
      </motion.div>
    </AnimatePresence>
  );
};

export default ZenMode;
