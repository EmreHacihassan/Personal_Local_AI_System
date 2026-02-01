'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FiClock, FiChevronRight, FiFileText, FiStar } from 'react-icons/fi';

interface Note {
  id: string;
  title: string;
  content?: string;
  updatedAt?: Date;
  isPinned?: boolean;
  color?: string;
}

interface RecentNotesWidgetProps {
  notes: Note[];
  maxItems?: number;
  onNoteClick: (noteId: string) => void;
  className?: string;
}

const RecentNotesWidget: React.FC<RecentNotesWidgetProps> = ({
  notes,
  maxItems = 5,
  onNoteClick,
  className = ''
}) => {
  // Sort by updatedAt and get recent notes
  const recentNotes = [...notes]
    .sort((a, b) => {
      const dateA = a.updatedAt ? new Date(a.updatedAt).getTime() : 0;
      const dateB = b.updatedAt ? new Date(b.updatedAt).getTime() : 0;
      return dateB - dateA;
    })
    .slice(0, maxItems);

  const formatTimeAgo = (date?: Date) => {
    if (!date) return '';
    const now = new Date();
    const then = new Date(date);
    const diff = Math.floor((now.getTime() - then.getTime()) / 1000);

    if (diff < 60) return 'Az önce';
    if (diff < 3600) return `${Math.floor(diff / 60)} dk önce`;
    if (diff < 86400) return `${Math.floor(diff / 3600)} saat önce`;
    if (diff < 604800) return `${Math.floor(diff / 86400)} gün önce`;
    return then.toLocaleDateString('tr-TR', { day: 'numeric', month: 'short' });
  };

  const getPreview = (content?: string) => {
    if (!content) return 'Boş not';
    const stripped = content
      .replace(/#{1,6}\s/g, '')
      .replace(/[*_`]/g, '')
      .trim();
    return stripped.length > 50 ? stripped.slice(0, 50) + '...' : stripped;
  };

  const colorMap: Record<string, string> = {
    yellow: 'bg-yellow-400',
    blue: 'bg-blue-400',
    green: 'bg-green-400',
    pink: 'bg-pink-400',
    purple: 'bg-purple-400',
    default: 'bg-gray-400',
  };

  if (recentNotes.length === 0) {
    return (
      <div className={`p-4 bg-gray-50 dark:bg-gray-800 rounded-xl text-center text-gray-500 ${className}`}>
        Henüz not yok
      </div>
    );
  }

  return (
    <div className={`bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20">
        <div className="flex items-center gap-2 text-gray-700 dark:text-gray-300">
          <FiClock className="w-4 h-4 text-blue-500" />
          <span className="font-medium text-sm">Son Erişilen</span>
        </div>
        <span className="text-xs text-gray-500">{recentNotes.length} not</span>
      </div>

      {/* Notes List */}
      <div className="divide-y divide-gray-100 dark:divide-gray-800">
        <AnimatePresence>
          {recentNotes.map((note, idx) => (
            <motion.button
              key={note.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 10 }}
              transition={{ delay: idx * 0.05 }}
              onClick={() => onNoteClick(note.id)}
              className="w-full flex items-center gap-3 px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors group"
            >
              {/* Color Indicator */}
              <div className={`w-2 h-2 rounded-full ${colorMap[note.color || 'default']}`} />
              
              {/* Content */}
              <div className="flex-1 min-w-0 text-left">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-900 dark:text-white truncate">
                    {note.title || 'Başlıksız'}
                  </span>
                  {note.isPinned && <FiStar className="w-3 h-3 text-amber-500 flex-shrink-0" />}
                </div>
                <div className="text-xs text-gray-500 truncate">
                  {getPreview(note.content)}
                </div>
              </div>
              
              {/* Time & Arrow */}
              <div className="flex items-center gap-2 flex-shrink-0">
                <span className="text-xs text-gray-400">
                  {formatTimeAgo(note.updatedAt)}
                </span>
                <FiChevronRight className="w-4 h-4 text-gray-300 group-hover:text-gray-500 transition-colors" />
              </div>
            </motion.button>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default RecentNotesWidget;
