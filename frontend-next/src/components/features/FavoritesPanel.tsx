'use client';

/**
 * FavoritesPanel - Favori notlar ve son görüntülenen notlar paneli
 * 
 * Premium tasarımlı, animasyonlu favorites sidebar.
 */

import React, { useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Star,
    History,
    Clock,
    FileText,
    ChevronRight,
    Sparkles,
    Calendar,
    X
} from 'lucide-react';
import { Note } from '@/store/useStore';
import { cn, formatDate } from '@/lib/utils';

interface FavoritesPanelProps {
    notes: Note[];
    recentNoteIds: string[];
    onSelectNote: (note: Note) => void;
    onToggleFavorite: (noteId: string) => void;
    onClose: () => void;
    language?: 'tr' | 'en' | 'de';
}

const translations = {
    favorites: { tr: 'Favoriler', en: 'Favorites', de: 'Favoriten' },
    recent: { tr: 'Son Görüntülenenler', en: 'Recent', de: 'Zuletzt angesehen' },
    noFavorites: { tr: 'Henüz favori not yok', en: 'No favorites yet', de: 'Noch keine Favoriten' },
    noRecent: { tr: 'Henüz görüntülenen not yok', en: 'No recent notes', de: 'Keine kürzlich angesehenen' },
    addFavorite: { tr: 'Yıldız ile favori ekle', en: 'Star notes to add favorites', de: 'Notizen mit Stern markieren' },
};

export function FavoritesPanel({
    notes,
    recentNoteIds,
    onSelectNote,
    onToggleFavorite,
    onClose,
    language = 'tr'
}: FavoritesPanelProps) {
    const t = translations;

    // Favori notlar
    const favoriteNotes = useMemo(() => {
        return notes.filter(note => note.isPinned);
    }, [notes]);

    // Son görüntülenen notlar
    const recentNotes = useMemo(() => {
        return recentNoteIds
            .map(id => notes.find(n => n.id === id))
            .filter((n): n is Note => n !== undefined)
            .slice(0, 10);
    }, [notes, recentNoteIds]);

    return (
        <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="h-full flex flex-col bg-card border-r border-border"
        >
            {/* Header */}
            <div className="p-4 border-b border-border bg-gradient-to-r from-amber-500/10 to-orange-500/10">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="p-2 rounded-lg bg-amber-500/20">
                            <Sparkles className="w-4 h-4 text-amber-500" />
                        </div>
                        <h3 className="font-semibold">Quick Access</h3>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-1.5 rounded-lg hover:bg-muted transition-colors"
                    >
                        <X className="w-4 h-4 text-muted-foreground" />
                    </button>
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto">
                {/* Favorites Section */}
                <div className="p-4 border-b border-border">
                    <div className="flex items-center gap-2 mb-3">
                        <Star className="w-4 h-4 text-amber-500 fill-amber-500" />
                        <h4 className="text-sm font-medium">{t.favorites[language]}</h4>
                        <span className="ml-auto px-2 py-0.5 rounded-full bg-amber-500/10 text-xs font-medium text-amber-600 dark:text-amber-400">
                            {favoriteNotes.length}
                        </span>
                    </div>

                    {favoriteNotes.length > 0 ? (
                        <div className="space-y-2">
                            <AnimatePresence mode="popLayout">
                                {favoriteNotes.map((note, index) => (
                                    <motion.button
                                        key={note.id}
                                        layout
                                        initial={{ opacity: 0, y: -10 }}
                                        animate={{ opacity: 1, y: 0, transition: { delay: index * 0.05 } }}
                                        exit={{ opacity: 0, scale: 0.95 }}
                                        whileHover={{ scale: 1.02, x: 4 }}
                                        whileTap={{ scale: 0.98 }}
                                        onClick={() => onSelectNote(note)}
                                        className="w-full flex items-center gap-3 p-3 rounded-xl bg-gradient-to-r from-amber-500/5 to-orange-500/5 hover:from-amber-500/10 hover:to-orange-500/10 border border-amber-500/10 hover:border-amber-500/30 transition-all text-left group"
                                    >
                                        <div className="relative">
                                            <FileText className="w-4 h-4 text-amber-500" />
                                            <Star className="absolute -top-1 -right-1 w-2.5 h-2.5 text-amber-400 fill-amber-400" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm font-medium truncate">{note.title}</p>
                                            <p className="text-[10px] text-muted-foreground">
                                                {formatDate(note.updatedAt)}
                                            </p>
                                        </div>
                                        <ChevronRight className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                                    </motion.button>
                                ))}
                            </AnimatePresence>
                        </div>
                    ) : (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="p-4 rounded-xl bg-muted/30 border border-dashed border-muted-foreground/20 text-center"
                        >
                            <Star className="w-8 h-8 mx-auto mb-2 text-muted-foreground/30" />
                            <p className="text-xs text-muted-foreground mb-1">{t.noFavorites[language]}</p>
                            <p className="text-[10px] text-muted-foreground/60">{t.addFavorite[language]}</p>
                        </motion.div>
                    )}
                </div>

                {/* Recent Section */}
                <div className="p-4">
                    <div className="flex items-center gap-2 mb-3">
                        <History className="w-4 h-4 text-blue-500" />
                        <h4 className="text-sm font-medium">{t.recent[language]}</h4>
                        <span className="ml-auto px-2 py-0.5 rounded-full bg-blue-500/10 text-xs font-medium text-blue-600 dark:text-blue-400">
                            {recentNotes.length}
                        </span>
                    </div>

                    {recentNotes.length > 0 ? (
                        <div className="space-y-1.5">
                            <AnimatePresence mode="popLayout">
                                {recentNotes.map((note, index) => (
                                    <motion.button
                                        key={note.id}
                                        layout
                                        initial={{ opacity: 0, x: -10 }}
                                        animate={{ opacity: 1, x: 0, transition: { delay: index * 0.03 } }}
                                        exit={{ opacity: 0, x: -10 }}
                                        whileHover={{ x: 4 }}
                                        onClick={() => onSelectNote(note)}
                                        className="w-full flex items-center gap-2.5 p-2.5 rounded-lg hover:bg-muted transition-all text-left group"
                                    >
                                        <Clock className="w-3.5 h-3.5 text-muted-foreground" />
                                        <span className="flex-1 text-sm truncate">{note.title}</span>
                                        <span className="text-[10px] text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity">
                                            {formatDate(note.updatedAt)}
                                        </span>
                                    </motion.button>
                                ))}
                            </AnimatePresence>
                        </div>
                    ) : (
                        <div className="p-4 rounded-lg bg-muted/30 border border-dashed border-muted-foreground/20 text-center">
                            <History className="w-6 h-6 mx-auto mb-2 text-muted-foreground/30" />
                            <p className="text-xs text-muted-foreground">{t.noRecent[language]}</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Footer Gradient */}
            <div className="h-8 bg-gradient-to-t from-card to-transparent pointer-events-none" />
        </motion.div>
    );
}

export default FavoritesPanel;
