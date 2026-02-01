'use client';

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FiFileText, FiClock, FiTag, FiFolder } from 'react-icons/fi';

interface Note {
  id: string;
  title: string;
  content: string;
  folder?: string;
  tags?: string[];
  updatedAt?: Date;
  color?: string;
}

interface NotePreviewTooltipProps {
  note: Note;
  children: React.ReactNode;
  delay?: number;
  position?: 'top' | 'bottom' | 'left' | 'right';
  maxWidth?: number;
}

const NotePreviewTooltip: React.FC<NotePreviewTooltipProps> = ({
  note,
  children,
  delay = 500,
  position = 'right',
  maxWidth = 320
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [coords, setCoords] = useState({ x: 0, y: 0 });
  const timeoutRef = useRef<NodeJS.Timeout>();
  const triggerRef = useRef<HTMLDivElement>(null);

  const handleMouseEnter = (e: React.MouseEvent) => {
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
    
    // Position based on prop
    let x = rect.right + 10;
    let y = rect.top;
    
    if (position === 'left') {
      x = rect.left - maxWidth - 10;
    } else if (position === 'top') {
      x = rect.left;
      y = rect.top - 200;
    } else if (position === 'bottom') {
      x = rect.left;
      y = rect.bottom + 10;
    }
    
    // Keep within viewport
    if (x + maxWidth > window.innerWidth) {
      x = window.innerWidth - maxWidth - 20;
    }
    if (x < 20) x = 20;
    if (y < 20) y = 20;
    if (y + 200 > window.innerHeight) {
      y = window.innerHeight - 220;
    }
    
    setCoords({ x, y });
    
    timeoutRef.current = setTimeout(() => {
      setIsVisible(true);
    }, delay);
  };

  const handleMouseLeave = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setIsVisible(false);
  };

  // Get preview content
  const getPreviewContent = () => {
    const content = note.content || '';
    // Strip markdown
    const stripped = content
      .replace(/#{1,6}\s/g, '')
      .replace(/\*\*([^*]+)\*\*/g, '$1')
      .replace(/\*([^*]+)\*/g, '$1')
      .replace(/`([^`]+)`/g, '$1')
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
      .replace(/!\[([^\]]*)\]\([^)]+\)/g, '')
      .trim();
    
    if (stripped.length > 200) {
      return stripped.slice(0, 200) + '...';
    }
    return stripped || 'Boş not';
  };

  const formatDate = (date?: Date) => {
    if (!date) return '';
    return new Date(date).toLocaleDateString('tr-TR', {
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const colorMap: Record<string, string> = {
    yellow: 'from-yellow-400/20 to-orange-400/20 border-yellow-400/50',
    blue: 'from-blue-400/20 to-cyan-400/20 border-blue-400/50',
    green: 'from-green-400/20 to-emerald-400/20 border-green-400/50',
    pink: 'from-pink-400/20 to-rose-400/20 border-pink-400/50',
    purple: 'from-purple-400/20 to-indigo-400/20 border-purple-400/50',
    default: 'from-gray-100 to-gray-50 dark:from-gray-800 dark:to-gray-700 border-gray-200 dark:border-gray-600',
  };

  return (
    <>
      <div
        ref={triggerRef}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        className="inline-block"
      >
        {children}
      </div>

      <AnimatePresence>
        {isVisible && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 5 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 5 }}
            transition={{ duration: 0.15 }}
            className="fixed z-[100] pointer-events-none"
            style={{
              left: coords.x,
              top: coords.y,
              width: maxWidth
            }}
          >
            <div className={`bg-gradient-to-br ${colorMap[note.color || 'default']} backdrop-blur-xl rounded-xl border shadow-2xl overflow-hidden`}>
              {/* Header */}
              <div className="px-4 py-3 border-b border-gray-200/50 dark:border-gray-700/50">
                <div className="flex items-center gap-2">
                  <FiFileText className="w-4 h-4 text-gray-500" />
                  <h4 className="font-medium text-gray-900 dark:text-white truncate">
                    {note.title || 'Başlıksız Not'}
                  </h4>
                </div>
              </div>

              {/* Content Preview */}
              <div className="px-4 py-3">
                <p className="text-sm text-gray-600 dark:text-gray-300 leading-relaxed">
                  {getPreviewContent()}
                </p>
              </div>

              {/* Footer */}
              <div className="px-4 py-2 bg-black/5 dark:bg-white/5 flex flex-wrap items-center gap-3 text-xs text-gray-500">
                {note.updatedAt && (
                  <span className="flex items-center gap-1">
                    <FiClock className="w-3 h-3" />
                    {formatDate(note.updatedAt)}
                  </span>
                )}
                {note.folder && (
                  <span className="flex items-center gap-1">
                    <FiFolder className="w-3 h-3" />
                    {note.folder}
                  </span>
                )}
                {note.tags && note.tags.length > 0 && (
                  <span className="flex items-center gap-1">
                    <FiTag className="w-3 h-3" />
                    {note.tags.slice(0, 2).join(', ')}
                    {note.tags.length > 2 && ` +${note.tags.length - 2}`}
                  </span>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export default NotePreviewTooltip;
