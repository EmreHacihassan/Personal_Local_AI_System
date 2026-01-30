'use client';

/**
 * RecentNotesPanel - Son Görüntülenen Notlar Paneli
 * 
 * Kullanıcının son görüntülediği notlara hızlı erişim.
 */

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Clock,
    StickyNote,
    X,
    Trash2,
    Eye,
    ExternalLink
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Note } from '@/store/useStore';

interface RecentNote {
    id: string;
    title: string;
    color: string;
    viewedAt: Date;
    preview?: string;
}

interface RecentNotesPanelProps {
    notes: Note[];
    onSelectNote: (noteId: string) => void;
    onClose: () => void;
    maxItems?: number;
    language?: 'tr' | 'en' | 'de';
}

const translations = {
    title: { tr: 'Son Görüntülenenler', en: 'Recently Viewed', de: 'Zuletzt angesehen' },
    empty: { tr: 'Henüz not görüntülemediniz', en: 'No recently viewed notes', de: 'Keine kürzlich angesehenen Notizen' },
    viewedAt: { tr: 'Görüntülenme', en: 'Viewed', de: 'Angesehen' },
    clearAll: { tr: 'Temizle', en: 'Clear All', de: 'Alle löschen' },
    openNote: { tr: 'Notu Aç', en: 'Open Note', de: 'Notiz öffnen' },
    today: { tr: 'Bugün', en: 'Today', de: 'Heute' },
    yesterday: { tr: 'Dün', en: 'Yesterday', de: 'Gestern' },
    daysAgo: { tr: 'gün önce', en: 'days ago', de: 'Tage her' },
};

const STORAGE_KEY = 'recent_notes';
const MAX_RECENT = 15;

// Color classes
const colorClasses: Record<string, { bg: string; border: string; dot: string }> = {
    yellow: { bg: 'bg-yellow-500/10', border: 'border-yellow-500/30', dot: 'bg-yellow-500' },
    green: { bg: 'bg-green-500/10', border: 'border-green-500/30', dot: 'bg-green-500' },
    blue: { bg: 'bg-blue-500/10', border: 'border-blue-500/30', dot: 'bg-blue-500' },
    pink: { bg: 'bg-pink-500/10', border: 'border-pink-500/30', dot: 'bg-pink-500' },
    purple: { bg: 'bg-purple-500/10', border: 'border-purple-500/30', dot: 'bg-purple-500' },
    orange: { bg: 'bg-orange-500/10', border: 'border-orange-500/30', dot: 'bg-orange-500' },
    red: { bg: 'bg-red-500/10', border: 'border-red-500/30', dot: 'bg-red-500' },
    gray: { bg: 'bg-gray-500/10', border: 'border-gray-500/30', dot: 'bg-gray-500' },
    default: { bg: 'bg-slate-500/10', border: 'border-slate-500/30', dot: 'bg-slate-500' },
};

const loadRecentNotes = (): RecentNote[] => {
    if (typeof window === 'undefined') return [];
    try {
        const data = localStorage.getItem(STORAGE_KEY);
        if (data) {
            return JSON.parse(data).map((n: any) => ({
                ...n,
                viewedAt: new Date(n.viewedAt)
            }));
        }
    } catch (e) {
        console.error('Failed to load recent notes:', e);
    }
    return [];
};

const saveRecentNotes = (notes: RecentNote[]) => {
    if (typeof window === 'undefined') return;
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(notes.slice(0, MAX_RECENT)));
    } catch (e) {
        console.error('Failed to save recent notes:', e);
    }
};

// Export function to add a note to recent
export const addToRecentNotes = (note: Note) => {
    const recent = loadRecentNotes();
    const existing = recent.findIndex(n => n.id === note.id);

    const newEntry: RecentNote = {
        id: note.id,
        title: note.title,
        color: note.color || 'default',
        viewedAt: new Date(),
        preview: note.content.slice(0, 100)
    };

    if (existing >= 0) {
        recent.splice(existing, 1);
    }

    saveRecentNotes([newEntry, ...recent]);
};

export function RecentNotesPanel({
    notes,
    onSelectNote,
    onClose,
    maxItems = 10,
    language = 'tr'
}: RecentNotesPanelProps) {
    const t = translations;
    const [recentNotes, setRecentNotes] = useState<RecentNote[]>([]);

    useEffect(() => {
        const loaded = loadRecentNotes();
        // Filter out deleted notes
        const validNotes = loaded.filter(r => notes.some(n => n.id === r.id));
        setRecentNotes(validNotes.slice(0, maxItems));
    }, [notes, maxItems]);

    const handleClearAll = () => {
        setRecentNotes([]);
        if (typeof window !== 'undefined') {
            localStorage.removeItem(STORAGE_KEY);
        }
    };

    const formatTimeAgo = (date: Date) => {
        const now = new Date();
        const diff = now.getTime() - date.getTime();
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));

        if (days === 0) return t.today[language];
        if (days === 1) return t.yesterday[language];
        return `${days} ${t.daysAgo[language]}`;
    };

    const getColorClass = (color: string) => colorClasses[color] || colorClasses.default;

    return (
        <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="w-80 h-full bg-card border-l border-border shadow-xl flex flex-col"
        >
            {/* Header */}
            <div className="p-4 border-b border-border bg-gradient-to-r from-blue-500/5 to-cyan-500/5 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <div className="p-2 rounded-lg bg-blue-500/10">
                        <Clock className="w-4 h-4 text-blue-500" />
                    </div>
                    <div>
                        <h3 className="font-semibold text-sm">{t.title[language]}</h3>
                        <p className="text-xs text-muted-foreground">{recentNotes.length} not</p>
                    </div>
                </div>
                <div className="flex items-center gap-1">
                    {recentNotes.length > 0 && (
                        <button
                            onClick={handleClearAll}
                            className="p-1.5 rounded-lg hover:bg-red-500/10 text-muted-foreground hover:text-red-500 transition-colors"
                            title={t.clearAll[language]}
                        >
                            <Trash2 className="w-4 h-4" />
                        </button>
                    )}
                    <button
                        onClick={onClose}
                        className="p-1.5 rounded-lg hover:bg-muted transition-colors"
                    >
                        <X className="w-4 h-4 text-muted-foreground" />
                    </button>
                </div>
            </div>

            {/* Notes List */}
            <div className="flex-1 overflow-y-auto p-2">
                {recentNotes.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground">
                        <Eye className="w-10 h-10 mb-3 opacity-30" />
                        <p className="text-sm">{t.empty[language]}</p>
                    </div>
                ) : (
                    <div className="space-y-1">
                        {recentNotes.map((note, index) => {
                            const colorClass = getColorClass(note.color);
                            return (
                                <motion.button
                                    key={note.id}
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: index * 0.05 }}
                                    onClick={() => onSelectNote(note.id)}
                                    className={cn(
                                        "w-full p-3 rounded-xl border text-left transition-all group hover:shadow-md",
                                        colorClass.bg,
                                        colorClass.border
                                    )}
                                >
                                    <div className="flex items-start gap-3">
                                        <div className={cn(
                                            "w-2.5 h-2.5 rounded-full mt-1.5 flex-shrink-0",
                                            colorClass.dot
                                        )} />
                                        <div className="flex-1 min-w-0">
                                            <p className="font-medium text-sm truncate">{note.title}</p>
                                            {note.preview && (
                                                <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
                                                    {note.preview}
                                                </p>
                                            )}
                                            <div className="flex items-center gap-1 mt-2 text-xs text-muted-foreground">
                                                <Clock className="w-3 h-3" />
                                                <span>{formatTimeAgo(note.viewedAt)}</span>
                                            </div>
                                        </div>
                                        <ExternalLink className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
                                    </div>
                                </motion.button>
                            );
                        })}
                    </div>
                )}
            </div>
        </motion.div>
    );
}

export default RecentNotesPanel;
