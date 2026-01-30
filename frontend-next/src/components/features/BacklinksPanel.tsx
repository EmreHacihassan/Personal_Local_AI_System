'use client';

/**
 * BacklinksPanel - Bir nota bağlanan notları gösteren panel
 * 
 * Obsidian ve Roam Research'ten ilham alınmıştır.
 * Seçili notun backlinks'lerini (ona bağlanan notlar) listeler.
 */

import React, { useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link2, ArrowLeft, FileText, ChevronRight, Clock, Tag, Network, X } from 'lucide-react';
import { Note } from '@/store/useStore';
import { cn, formatDate } from '@/lib/utils';
import { findBacklinks, extractWikiLinks } from './WikiLinkParser';

interface BacklinksPanelProps {
    note: Note;
    notes: Note[];
    onNavigate: (noteId: string) => void;
    onClose: () => void;
    language?: 'tr' | 'en' | 'de';
}

const translations = {
    backlinks: { tr: 'Gelen Bağlantılar', en: 'Backlinks', de: 'Rückverweise' },
    outgoingLinks: { tr: 'Giden Bağlantılar', en: 'Outgoing Links', de: 'Ausgehende Links' },
    noBacklinks: { tr: 'Bu nota bağlanan not yok', en: 'No notes link to this note', de: 'Keine Notizen verweisen auf diese Notiz' },
    noOutgoing: { tr: 'Bu not başka notlara bağlanmıyor', en: 'This note has no outgoing links', de: 'Diese Notiz hat keine ausgehenden Links' },
    linkedNotes: { tr: 'Bağlı Notlar', en: 'Linked Notes', de: 'Verknüpfte Notizen' },
};

export function BacklinksPanel({ note, notes, onNavigate, onClose, language = 'tr' }: BacklinksPanelProps) {
    const t = translations;

    // Backlinks - bu nota bağlanan notlar
    const backlinks = useMemo(() => {
        return findBacklinks(note.id, note.title, notes);
    }, [note.id, note.title, notes]);

    // Outgoing links - bu notun bağlandığı notlar
    const outgoingLinks = useMemo(() => {
        const linkTitles = extractWikiLinks(note.content);
        return linkTitles.map(title => {
            const linkedNote = notes.find(n =>
                n.title.toLowerCase() === title.toLowerCase() ||
                n.title.toLowerCase().includes(title.toLowerCase())
            );
            return { title, note: linkedNote };
        });
    }, [note.content, notes]);

    return (
        <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="h-full flex flex-col bg-card border-l border-border"
        >
            {/* Header */}
            <div className="p-4 border-b border-border bg-gradient-to-r from-primary-500/5 to-purple-500/5">
                <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                        <div className="p-2 rounded-lg bg-primary-500/10">
                            <Network className="w-4 h-4 text-primary-500" />
                        </div>
                        <h3 className="font-semibold">{t.linkedNotes[language]}</h3>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-1.5 rounded-lg hover:bg-muted transition-colors"
                    >
                        <X className="w-4 h-4 text-muted-foreground" />
                    </button>
                </div>
                <p className="text-xs text-muted-foreground line-clamp-1">
                    {note.title}
                </p>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto">
                {/* Backlinks Section */}
                <div className="p-4 border-b border-border">
                    <div className="flex items-center gap-2 mb-3">
                        <ArrowLeft className="w-4 h-4 text-emerald-500" />
                        <h4 className="text-sm font-medium text-emerald-600 dark:text-emerald-400">
                            {t.backlinks[language]}
                        </h4>
                        <span className="ml-auto px-2 py-0.5 rounded-full bg-emerald-500/10 text-xs font-medium text-emerald-600 dark:text-emerald-400">
                            {backlinks.length}
                        </span>
                    </div>

                    {backlinks.length > 0 ? (
                        <div className="space-y-2">
                            {backlinks.map((linkedNote) => (
                                <motion.button
                                    key={linkedNote.id}
                                    whileHover={{ scale: 1.01 }}
                                    whileTap={{ scale: 0.99 }}
                                    onClick={() => onNavigate(linkedNote.id)}
                                    className="w-full p-3 rounded-lg bg-muted/50 hover:bg-muted border border-transparent hover:border-emerald-500/30 transition-all text-left group"
                                >
                                    <div className="flex items-center gap-2 mb-1">
                                        <FileText className="w-3.5 h-3.5 text-muted-foreground group-hover:text-emerald-500 transition-colors" />
                                        <span className="text-sm font-medium truncate group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors">
                                            {linkedNote.title}
                                        </span>
                                        <ChevronRight className="w-3.5 h-3.5 ml-auto text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                                    </div>
                                    <p className="text-xs text-muted-foreground line-clamp-2 pl-5.5">
                                        {linkedNote.content?.slice(0, 100) || 'Boş not'}
                                    </p>
                                    <div className="flex items-center gap-2 mt-2 pl-5.5">
                                        <Clock className="w-3 h-3 text-muted-foreground" />
                                        <span className="text-[10px] text-muted-foreground">
                                            {formatDate(linkedNote.updatedAt)}
                                        </span>
                                    </div>
                                </motion.button>
                            ))}
                        </div>
                    ) : (
                        <div className="p-4 rounded-lg bg-muted/30 border border-dashed border-muted-foreground/20 text-center">
                            <Link2 className="w-6 h-6 mx-auto mb-2 text-muted-foreground/50" />
                            <p className="text-xs text-muted-foreground">{t.noBacklinks[language]}</p>
                        </div>
                    )}
                </div>

                {/* Outgoing Links Section */}
                <div className="p-4">
                    <div className="flex items-center gap-2 mb-3">
                        <ChevronRight className="w-4 h-4 text-blue-500" />
                        <h4 className="text-sm font-medium text-blue-600 dark:text-blue-400">
                            {t.outgoingLinks[language]}
                        </h4>
                        <span className="ml-auto px-2 py-0.5 rounded-full bg-blue-500/10 text-xs font-medium text-blue-600 dark:text-blue-400">
                            {outgoingLinks.length}
                        </span>
                    </div>

                    {outgoingLinks.length > 0 ? (
                        <div className="space-y-2">
                            {outgoingLinks.map((link, index) => (
                                <motion.button
                                    key={index}
                                    whileHover={{ scale: 1.01 }}
                                    whileTap={{ scale: 0.99 }}
                                    onClick={() => link.note && onNavigate(link.note.id)}
                                    disabled={!link.note}
                                    className={cn(
                                        "w-full p-3 rounded-lg border transition-all text-left group",
                                        link.note
                                            ? "bg-muted/50 hover:bg-muted border-transparent hover:border-blue-500/30"
                                            : "bg-amber-500/5 border-amber-500/20 border-dashed cursor-not-allowed"
                                    )}
                                >
                                    <div className="flex items-center gap-2">
                                        <Link2 className={cn(
                                            "w-3.5 h-3.5",
                                            link.note ? "text-blue-500" : "text-amber-500"
                                        )} />
                                        <span className={cn(
                                            "text-sm font-medium truncate",
                                            link.note
                                                ? "group-hover:text-blue-600 dark:group-hover:text-blue-400"
                                                : "text-amber-600 dark:text-amber-400"
                                        )}>
                                            {link.title}
                                        </span>
                                        {!link.note && (
                                            <span className="text-xs text-amber-500 ml-auto">(bulunamadı)</span>
                                        )}
                                        {link.note && (
                                            <ChevronRight className="w-3.5 h-3.5 ml-auto text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                                        )}
                                    </div>
                                    {link.note && (
                                        <p className="text-xs text-muted-foreground line-clamp-1 pl-5.5 mt-1">
                                            {link.note.content?.slice(0, 80) || 'Boş not'}
                                        </p>
                                    )}
                                </motion.button>
                            ))}
                        </div>
                    ) : (
                        <div className="p-4 rounded-lg bg-muted/30 border border-dashed border-muted-foreground/20 text-center">
                            <ChevronRight className="w-6 h-6 mx-auto mb-2 text-muted-foreground/50" />
                            <p className="text-xs text-muted-foreground">{t.noOutgoing[language]}</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Hint */}
            <div className="p-3 border-t border-border bg-muted/30">
                <p className="text-[10px] text-muted-foreground text-center">
                    💡 [[Not Adı]] yazarak bağlantı oluşturabilirsiniz
                </p>
            </div>
        </motion.div>
    );
}

export default BacklinksPanel;
