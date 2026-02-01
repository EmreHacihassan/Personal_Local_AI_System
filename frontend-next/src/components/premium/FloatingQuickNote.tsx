'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence, useDragControls } from 'framer-motion';
import { FiPlus, FiX, FiCheck, FiMinimize2, FiMaximize2, FiMove } from 'react-icons/fi';

interface FloatingQuickNoteProps {
  onSave: (content: string, title?: string) => Promise<void>;
  defaultPosition?: { x: number; y: number };
}

const FloatingQuickNote: React.FC<FloatingQuickNoteProps> = ({
  onSave,
  defaultPosition = { x: window.innerWidth - 380, y: window.innerHeight - 350 }
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [content, setContent] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [position, setPosition] = useState(defaultPosition);
  const dragControls = useDragControls();
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Focus textarea when opened
  useEffect(() => {
    if (isOpen && !isMinimized && textareaRef.current) {
      setTimeout(() => textareaRef.current?.focus(), 100);
    }
  }, [isOpen, isMinimized]);

  // Keyboard shortcut to open
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Alt+N to toggle quick note
      if (e.altKey && e.key === 'n') {
        e.preventDefault();
        setIsOpen(prev => !prev);
        setIsMinimized(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleSave = async () => {
    if (!content.trim()) return;
    
    setIsSaving(true);
    try {
      // Extract title from first line if exists
      const lines = content.split('\n');
      const title = lines[0].replace(/^#\s*/, '').trim() || `Hızlı Not - ${new Date().toLocaleTimeString('tr-TR')}`;
      
      await onSave(content, title);
      setContent('');
      setIsOpen(false);
    } catch (error) {
      console.error('Quick note save failed:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleClose = () => {
    if (content.trim()) {
      if (window.confirm('Kaydedilmemiş değişiklikler var. Vazgeçmek istiyor musunuz?')) {
        setContent('');
        setIsOpen(false);
      }
    } else {
      setIsOpen(false);
    }
  };

  return (
    <>
      {/* FAB Button */}
      <AnimatePresence>
        {!isOpen && (
          <motion.button
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={() => setIsOpen(true)}
            className="fixed bottom-6 right-6 z-50 p-4 bg-gradient-to-r from-purple-500 to-indigo-500 text-white rounded-full shadow-lg hover:shadow-xl transition-shadow"
            title="Hızlı Not (Alt+N)"
          >
            <FiPlus className="w-6 h-6" />
          </motion.button>
        )}
      </AnimatePresence>

      {/* Quick Note Panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.8, opacity: 0 }}
            drag
            dragControls={dragControls}
            dragMomentum={false}
            dragElastic={0}
            onDragEnd={(_, info) => {
              setPosition(prev => ({
                x: prev.x + info.offset.x,
                y: prev.y + info.offset.y
              }));
            }}
            style={{
              position: 'fixed',
              left: position.x,
              top: position.y,
              zIndex: 9999
            }}
            className={`w-80 bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden ${isMinimized ? 'h-auto' : ''}`}
          >
            {/* Header - Draggable */}
            <div
              className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-purple-500 to-indigo-500 cursor-move"
              onPointerDown={(e) => dragControls.start(e)}
            >
              <div className="flex items-center gap-2 text-white">
                <FiMove className="w-4 h-4 opacity-60" />
                <span className="font-medium text-sm">Hızlı Not</span>
                {content.length > 0 && (
                  <span className="text-xs opacity-70">
                    ({content.length} karakter)
                  </span>
                )}
              </div>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setIsMinimized(!isMinimized)}
                  className="p-1.5 hover:bg-white/20 rounded transition-colors text-white"
                >
                  {isMinimized ? <FiMaximize2 className="w-3.5 h-3.5" /> : <FiMinimize2 className="w-3.5 h-3.5" />}
                </button>
                <button
                  onClick={handleClose}
                  className="p-1.5 hover:bg-white/20 rounded transition-colors text-white"
                >
                  <FiX className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* Content */}
            {!isMinimized && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
              >
                <div className="p-3">
                  <textarea
                    ref={textareaRef}
                    value={content}
                    onChange={e => setContent(e.target.value)}
                    placeholder="Hızlıca bir not yazın...&#10;&#10;İpucu: İlk satır başlık olarak kullanılır."
                    className="w-full h-40 p-3 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-sm resize-none focus:outline-none focus:ring-2 focus:ring-purple-500"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                        e.preventDefault();
                        handleSave();
                      }
                    }}
                  />
                </div>

                {/* Footer */}
                <div className="flex items-center justify-between px-3 pb-3">
                  <span className="text-xs text-gray-400">
                    Ctrl+Enter ile kaydet
                  </span>
                  <motion.button
                    onClick={handleSave}
                    disabled={!content.trim() || isSaving}
                    className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-500 to-indigo-500 text-white text-sm rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <FiCheck className="w-4 h-4" />
                    {isSaving ? 'Kaydediliyor...' : 'Kaydet'}
                  </motion.button>
                </div>
              </motion.div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export default FloatingQuickNote;
