'use client';

/**
 * NoteCard - Premium Not Kartı Bileşeni
 * 
 * Mevcut NotesPage içindeki not kartlarının modülerize edilmiş versiyonu.
 * Backward compatibility için optional props ile tasarlandı.
 * 
 * ÖNEMLİ: Bu bileşen mevcut NotesPage.tsx'i bozmadan ayrı olarak geliştirildi.
 * Entegrasyon sonradan yapılacak.
 */

import { memo } from 'react';
import { motion } from 'framer-motion';
import { Pin, Lock, Unlock, Trash2, FileDown, Star, MoreHorizontal } from 'lucide-react';
import { cn, formatDate } from '@/lib/utils';
import { Note } from '@/store/useStore';

// Color classes - NotesPage'deki ile aynı
const getNoteColorClasses = (color?: string) => {
  const colorMap: Record<string, { bg: string; border: string }> = {
    default: { bg: 'bg-card', border: 'border-border' },
    yellow: { bg: 'bg-yellow-50 dark:bg-yellow-900/20', border: 'border-yellow-200 dark:border-yellow-800' },
    green: { bg: 'bg-green-50 dark:bg-green-900/20', border: 'border-green-200 dark:border-green-800' },
    blue: { bg: 'bg-blue-50 dark:bg-blue-900/20', border: 'border-blue-200 dark:border-blue-800' },
    purple: { bg: 'bg-purple-50 dark:bg-purple-900/20', border: 'border-purple-200 dark:border-purple-800' },
    pink: { bg: 'bg-pink-50 dark:bg-pink-900/20', border: 'border-pink-200 dark:border-pink-800' },
    orange: { bg: 'bg-orange-50 dark:bg-orange-900/20', border: 'border-orange-200 dark:border-orange-800' },
    red: { bg: 'bg-red-50 dark:bg-red-900/20', border: 'border-red-200 dark:border-red-800' },
  };
  return colorMap[color || 'default'] || colorMap.default;
};

export interface NoteCardProps {
  note: Note;
  isSelected?: boolean;
  viewMode: 'list' | 'grid';
  language: 'tr' | 'en' | 'de';
  
  // Actions
  onClick?: (note: Note) => void;
  onPin?: (note: Note) => void;
  onLock?: (note: Note) => void;
  onDelete?: (note: Note) => void;
  onDownload?: (note: Note) => void;
  onFavorite?: (note: Note) => void;
  
  // Optional premium features
  showFavoriteButton?: boolean;
  showDownloadButton?: boolean;
  enablePremiumEffects?: boolean;
}

const translations = {
  emptyNote: { tr: 'Boş not', en: 'Empty note', de: 'Leere Notiz' },
  pin: { tr: 'Sabitle', en: 'Pin', de: 'Anheften' },
  unpin: { tr: 'Sabitlemeyi Kaldır', en: 'Unpin', de: 'Lösen' },
  lock: { tr: 'Kilitle', en: 'Lock', de: 'Sperren' },
  unlock: { tr: 'Kilidi Kaldır', en: 'Unlock', de: 'Entsperren' },
  download: { tr: 'İndir', en: 'Download', de: 'Herunterladen' },
  delete: { tr: 'Sil', en: 'Delete', de: 'Löschen' },
  lockedNote: { tr: 'Kilitli not silinemez', en: 'Locked note cannot be deleted', de: 'Gesperrte Notiz kann nicht gelöscht werden' },
};

export const NoteCard = memo(function NoteCard({
  note,
  isSelected = false,
  viewMode,
  language,
  onClick,
  onPin,
  onLock,
  onDelete,
  onDownload,
  showDownloadButton = true,
  enablePremiumEffects = true,
}: NoteCardProps) {
  const colorClasses = getNoteColorClasses(note.color);
  const t = translations;

  // Premium hover glow effect
  const premiumClasses = enablePremiumEffects ? cn(
    // Glassmorphism effect
    "backdrop-blur-sm",
    // Subtle shadow on hover
    "hover:shadow-lg hover:shadow-primary-500/5",
    // Scale effect
    "hover:scale-[1.01] active:scale-[0.99]",
    // Premium border glow when selected
    isSelected && "shadow-md shadow-primary-500/10"
  ) : "";

  if (viewMode === 'list') {
    return (
      <motion.button
        layout
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95 }}
        onClick={() => onClick?.(note)}
        className={cn(
          "w-full text-left p-3 rounded-xl transition-all duration-200 group border",
          colorClasses.bg,
          isSelected ? "ring-2 ring-primary-500" : colorClasses.border,
          premiumClasses
        )}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5">
              {note.isPinned && (
                <Pin className="w-3 h-3 text-primary-500 flex-shrink-0" />
              )}
              {note.isLocked && (
                <Lock className="w-3 h-3 text-amber-500 flex-shrink-0" />
              )}
              <p className="font-medium text-sm truncate">{note.title}</p>
            </div>
            <p className="text-xs text-muted-foreground truncate mt-1">
              {note.content || t.emptyNote[language]}
            </p>
            <div className="flex items-center gap-2 mt-2">
              <p className="text-[10px] text-muted-foreground">
                {formatDate(note.updatedAt, language)}
              </p>
              {/* Tags preview */}
              {note.tags && note.tags.length > 0 && (
                <div className="flex items-center gap-1">
                  {note.tags.slice(0, 2).map((tag, i) => (
                    <span
                      key={i}
                      className="px-1.5 py-0.5 text-[9px] bg-muted rounded-full text-muted-foreground"
                    >
                      #{tag}
                    </span>
                  ))}
                  {note.tags.length > 2 && (
                    <span className="text-[9px] text-muted-foreground">
                      +{note.tags.length - 2}
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>
          
          {/* Action Buttons */}
          <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
            {showDownloadButton && onDownload && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDownload(note);
                }}
                className="p-1.5 text-emerald-500 hover:bg-emerald-100 dark:hover:bg-emerald-900/30 rounded-lg transition-colors"
                title={t.download[language]}
              >
                <FileDown className="w-3.5 h-3.5" />
              </button>
            )}
            {onPin && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onPin(note);
                }}
                className={cn(
                  "p-1.5 rounded-lg transition-colors",
                  note.isPinned
                    ? "text-primary-500 bg-primary-100 dark:bg-primary-900/30"
                    : "text-muted-foreground hover:bg-accent"
                )}
                title={note.isPinned ? t.unpin[language] : t.pin[language]}
              >
                <Pin className="w-3.5 h-3.5" />
              </button>
            )}
            {onLock && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onLock(note);
                }}
                className={cn(
                  "p-1.5 rounded-lg transition-colors",
                  note.isLocked
                    ? "text-amber-500 bg-amber-100 dark:bg-amber-900/30"
                    : "text-muted-foreground hover:bg-accent"
                )}
                title={note.isLocked ? t.unlock[language] : t.lock[language]}
              >
                {note.isLocked ? <Lock className="w-3.5 h-3.5" /> : <Unlock className="w-3.5 h-3.5" />}
              </button>
            )}
            {onDelete && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  if (!note.isLocked) onDelete(note);
                }}
                className={cn(
                  "p-1.5 rounded-lg transition-all",
                  note.isLocked
                    ? "text-muted-foreground/50 cursor-not-allowed"
                    : "text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                )}
                disabled={note.isLocked}
                title={note.isLocked ? t.lockedNote[language] : t.delete[language]}
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>
      </motion.button>
    );
  }

  // Grid View
  return (
    <motion.button
      layout
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      onClick={() => onClick?.(note)}
      className={cn(
        "text-left p-3 rounded-xl transition-all duration-200 group border aspect-square flex flex-col",
        colorClasses.bg,
        isSelected ? "ring-2 ring-primary-500" : colorClasses.border,
        premiumClasses
      )}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-1">
          {note.isPinned && <Pin className="w-3 h-3 text-primary-500" />}
          {note.isLocked && <Lock className="w-3 h-3 text-amber-500" />}
        </div>
        {onDelete && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              if (!note.isLocked) onDelete(note);
            }}
            className={cn(
              "p-1 rounded opacity-0 group-hover:opacity-100 transition-all",
              note.isLocked
                ? "text-muted-foreground/50 cursor-not-allowed"
                : "text-muted-foreground hover:text-destructive"
            )}
            disabled={note.isLocked}
          >
            <Trash2 className="w-3 h-3" />
          </button>
        )}
      </div>
      <p className="font-medium text-xs truncate">{note.title}</p>
      <p className="text-[10px] text-muted-foreground line-clamp-3 mt-1 flex-1">
        {note.content || t.emptyNote[language]}
      </p>
      <p className="text-[9px] text-muted-foreground mt-2">
        {formatDate(note.updatedAt, language)}
      </p>
    </motion.button>
  );
});

export default NoteCard;
