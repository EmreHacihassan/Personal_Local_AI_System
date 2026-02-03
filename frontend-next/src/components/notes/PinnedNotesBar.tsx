'use client';

/**
 * PinnedNotesBar - Sabitlenmiş Notlar Çubuğu
 * 
 * Ekranın üst kısmında sabitlenmiş notlara hızlı erişim sağlar.
 * NotesPage'e entegre edilebilir veya bağımsız kullanılabilir.
 */

import { memo, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Pin, X, ChevronRight, StickyNote } from 'lucide-react';
import { cn, formatDate } from '@/lib/utils';
import { Note } from '@/store/useStore';

export interface PinnedNotesBarProps {
  notes: Note[];
  selectedNoteId?: string;
  language: 'tr' | 'en' | 'de';
  onSelectNote: (note: Note) => void;
  onUnpinNote?: (note: Note) => void;
  className?: string;
  maxVisible?: number;
}

const translations = {
  pinnedNotes: { tr: 'Sabitlenmiş Notlar', en: 'Pinned Notes', de: 'Angeheftete Notizen' },
  noPinned: { tr: 'Sabitlenmiş not yok', en: 'No pinned notes', de: 'Keine angehefteten Notizen' },
  unpin: { tr: 'Sabitlemeyi kaldır', en: 'Unpin', de: 'Lösen' },
};

// Not rengi için gradient
const getNoteGradient = (color?: string) => {
  const gradients: Record<string, string> = {
    default: 'from-slate-400 to-slate-500',
    yellow: 'from-yellow-400 to-amber-500',
    green: 'from-green-400 to-emerald-500',
    blue: 'from-blue-400 to-indigo-500',
    purple: 'from-purple-400 to-violet-500',
    pink: 'from-pink-400 to-rose-500',
    orange: 'from-orange-400 to-red-500',
    red: 'from-red-400 to-rose-500',
  };
  return gradients[color || 'default'] || gradients.default;
};

export const PinnedNotesBar = memo(function PinnedNotesBar({
  notes,
  selectedNoteId,
  language,
  onSelectNote,
  onUnpinNote,
  className,
  maxVisible = 5,
}: PinnedNotesBarProps) {
  const t = translations;
  
  // Sadece pinned notları al
  const pinnedNotes = useMemo(() => {
    return notes.filter(n => n.isPinned).slice(0, maxVisible);
  }, [notes, maxVisible]);

  // Pinned note yoksa gösterme
  if (pinnedNotes.length === 0) {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-primary-50/50 to-transparent dark:from-primary-950/30 border-b border-border/50",
        className
      )}
    >
      {/* Label */}
      <div className="flex items-center gap-1.5 text-xs text-muted-foreground shrink-0">
        <Pin className="w-3 h-3 text-primary-500" />
        <span className="hidden sm:inline">{t.pinnedNotes[language]}</span>
      </div>

      {/* Divider */}
      <div className="w-px h-4 bg-border" />

      {/* Pinned Notes */}
      <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-hide">
        <AnimatePresence mode="popLayout">
          {pinnedNotes.map((note, index) => (
            <motion.button
              key={note.id}
              initial={{ opacity: 0, scale: 0.8, x: -10 }}
              animate={{ opacity: 1, scale: 1, x: 0 }}
              exit={{ opacity: 0, scale: 0.8, x: -10 }}
              transition={{ delay: index * 0.05 }}
              onClick={() => onSelectNote(note)}
              className={cn(
                "group relative flex items-center gap-2 px-3 py-1.5 rounded-lg transition-all duration-200",
                "bg-background/80 backdrop-blur-sm border",
                selectedNoteId === note.id
                  ? "border-primary-500 ring-1 ring-primary-500/20 shadow-sm"
                  : "border-border/50 hover:border-primary-300 hover:shadow-sm"
              )}
            >
              {/* Color indicator */}
              <div className={cn(
                "w-2 h-2 rounded-full bg-gradient-to-br shrink-0",
                getNoteGradient(note.color)
              )} />
              
              {/* Title */}
              <span className="text-xs font-medium truncate max-w-[100px] sm:max-w-[150px]">
                {note.title}
              </span>

              {/* Unpin button - hover'da görünür */}
              {onUnpinNote && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onUnpinNote(note);
                  }}
                  className="opacity-0 group-hover:opacity-100 p-0.5 -mr-1 rounded hover:bg-muted transition-all"
                  title={t.unpin[language]}
                >
                  <X className="w-3 h-3 text-muted-foreground hover:text-foreground" />
                </button>
              )}
            </motion.button>
          ))}
        </AnimatePresence>
      </div>

      {/* Overflow indicator */}
      {notes.filter(n => n.isPinned).length > maxVisible && (
        <div className="flex items-center gap-1 text-xs text-muted-foreground shrink-0">
          <span>+{notes.filter(n => n.isPinned).length - maxVisible}</span>
          <ChevronRight className="w-3 h-3" />
        </div>
      )}
    </motion.div>
  );
});

export default PinnedNotesBar;
