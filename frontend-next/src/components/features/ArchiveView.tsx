'use client';

/**
 * ArchiveView - Arşivlenmiş notlar görünümü
 * 
 * Silmeden gizlenen (arşivlenen) notları yönetir.
 */

import React, { useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Archive,
    ArchiveRestore,
    Trash2,
    Search,
    FileText,
    Clock,
    X,
    AlertTriangle,
    CheckCircle
} from 'lucide-react';
import { Note } from '@/store/useStore';
import { cn, formatDate } from '@/lib/utils';

interface ArchiveViewProps {
    archivedNotes: Note[];
    onRestore: (noteId: string) => void;
    onPermanentDelete: (noteId: string) => void;
    onClose: () => void;
    language?: 'tr' | 'en' | 'de';
}

const translations = {
    archive: { tr: 'Arşiv', en: 'Archive', de: 'Archiv' },
    search: { tr: 'Arşivde ara...', en: 'Search archive...', de: 'Archiv durchsuchen...' },
    restore: { tr: 'Geri Yükle', en: 'Restore', de: 'Wiederherstellen' },
    delete: { tr: 'Kalıcı Sil', en: 'Delete Forever', de: 'Endgültig löschen' },
    emptyArchive: { tr: 'Arşiv boş', en: 'Archive is empty', de: 'Archiv ist leer' },
    emptyHint: { tr: 'Arşivlenen notlar burada görünür', en: 'Archived notes appear here', de: 'Archivierte Notizen erscheinen hier' },
    confirmDelete: { tr: 'Bu notu kalıcı olarak silmek istediğinizden emin misiniz?', en: 'Are you sure you want to permanently delete this note?', de: 'Möchten Sie diese Notiz wirklich dauerhaft löschen?' },
    restored: { tr: 'Not geri yüklendi', en: 'Note restored', de: 'Notiz wiederhergestellt' },
    deleted: { tr: 'Not kalıcı olarak silindi', en: 'Note permanently deleted', de: 'Notiz dauerhaft gelöscht' },
};

export function ArchiveView({
    archivedNotes,
    onRestore,
    onPermanentDelete,
    onClose,
    language = 'tr'
}: ArchiveViewProps) {
    const t = translations;
    const [searchQuery, setSearchQuery] = useState('');
    const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
    const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

    // Filtrelenmiş arşiv notları
    const filteredNotes = useMemo(() => {
        if (!searchQuery) return archivedNotes;
        const query = searchQuery.toLowerCase();
        return archivedNotes.filter(note =>
            note.title.toLowerCase().includes(query) ||
            note.content.toLowerCase().includes(query)
        );
    }, [archivedNotes, searchQuery]);

    const handleRestore = (noteId: string) => {
        onRestore(noteId);
        showNotification('success', t.restored[language]);
    };

    const handleDelete = (noteId: string) => {
        onPermanentDelete(noteId);
        setConfirmDeleteId(null);
        showNotification('success', t.deleted[language]);
    };

    const showNotification = (type: 'success' | 'error', message: string) => {
        setNotification({ type, message });
        setTimeout(() => setNotification(null), 3000);
    };

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4"
            onClick={onClose}
        >
            <motion.div
                initial={{ scale: 0.95, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.95, opacity: 0 }}
                className="w-full max-w-2xl max-h-[80vh] bg-card rounded-2xl shadow-2xl border border-border overflow-hidden flex flex-col"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div className="p-4 border-b border-border bg-gradient-to-r from-slate-500/10 to-zinc-500/10 flex-shrink-0">
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-3">
                            <div className="p-2.5 rounded-xl bg-slate-500/20">
                                <Archive className="w-5 h-5 text-slate-600 dark:text-slate-400" />
                            </div>
                            <div>
                                <h2 className="font-semibold text-lg">{t.archive[language]}</h2>
                                <p className="text-xs text-muted-foreground">
                                    {archivedNotes.length} not
                                </p>
                            </div>
                        </div>
                        <button
                            onClick={onClose}
                            className="p-2 rounded-lg hover:bg-muted transition-colors"
                        >
                            <X className="w-5 h-5 text-muted-foreground" />
                        </button>
                    </div>

                    {/* Search */}
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder={t.search[language]}
                            className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-background border border-border focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 outline-none transition-all text-sm"
                        />
                    </div>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-4">
                    {filteredNotes.length > 0 ? (
                        <div className="space-y-2">
                            <AnimatePresence mode="popLayout">
                                {filteredNotes.map((note, index) => (
                                    <motion.div
                                        key={note.id}
                                        layout
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0, transition: { delay: index * 0.03 } }}
                                        exit={{ opacity: 0, x: -20 }}
                                        className="p-4 rounded-xl bg-muted/50 border border-border hover:border-slate-500/30 transition-all group"
                                    >
                                        <div className="flex items-start gap-3">
                                            <FileText className="w-5 h-5 text-muted-foreground mt-0.5 flex-shrink-0" />
                                            <div className="flex-1 min-w-0">
                                                <h4 className="font-medium text-sm truncate">{note.title}</h4>
                                                <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
                                                    {note.content || 'Boş not'}
                                                </p>
                                                <div className="flex items-center gap-2 mt-2">
                                                    <Clock className="w-3 h-3 text-muted-foreground" />
                                                    <span className="text-[10px] text-muted-foreground">
                                                        Arşivlenme: {formatDate(note.updatedAt)}
                                                    </span>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                                                <motion.button
                                                    whileHover={{ scale: 1.05 }}
                                                    whileTap={{ scale: 0.95 }}
                                                    onClick={() => handleRestore(note.id)}
                                                    className="p-2 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500/20 transition-colors"
                                                    title={t.restore[language]}
                                                >
                                                    <ArchiveRestore className="w-4 h-4" />
                                                </motion.button>
                                                <motion.button
                                                    whileHover={{ scale: 1.05 }}
                                                    whileTap={{ scale: 0.95 }}
                                                    onClick={() => setConfirmDeleteId(note.id)}
                                                    className="p-2 rounded-lg bg-red-500/10 text-red-600 dark:text-red-400 hover:bg-red-500/20 transition-colors"
                                                    title={t.delete[language]}
                                                >
                                                    <Trash2 className="w-4 h-4" />
                                                </motion.button>
                                            </div>
                                        </div>
                                    </motion.div>
                                ))}
                            </AnimatePresence>
                        </div>
                    ) : (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="flex flex-col items-center justify-center h-64 text-center"
                        >
                            <div className="p-4 rounded-2xl bg-muted/30 mb-4">
                                <Archive className="w-12 h-12 text-muted-foreground/30" />
                            </div>
                            <h3 className="font-medium text-muted-foreground mb-1">{t.emptyArchive[language]}</h3>
                            <p className="text-xs text-muted-foreground/60">{t.emptyHint[language]}</p>
                        </motion.div>
                    )}
                </div>

                {/* Delete Confirmation Dialog */}
                <AnimatePresence>
                    {confirmDeleteId && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="absolute inset-0 bg-black/60 flex items-center justify-center p-4"
                            onClick={() => setConfirmDeleteId(null)}
                        >
                            <motion.div
                                initial={{ scale: 0.95 }}
                                animate={{ scale: 1 }}
                                exit={{ scale: 0.95 }}
                                className="bg-card rounded-xl p-6 max-w-sm w-full border border-border shadow-2xl"
                                onClick={(e) => e.stopPropagation()}
                            >
                                <div className="flex items-center gap-3 mb-4">
                                    <div className="p-2.5 rounded-xl bg-red-500/20">
                                        <AlertTriangle className="w-5 h-5 text-red-500" />
                                    </div>
                                    <h3 className="font-semibold">{t.delete[language]}</h3>
                                </div>
                                <p className="text-sm text-muted-foreground mb-6">
                                    {t.confirmDelete[language]}
                                </p>
                                <div className="flex gap-3">
                                    <button
                                        onClick={() => setConfirmDeleteId(null)}
                                        className="flex-1 px-4 py-2.5 rounded-xl bg-muted hover:bg-muted/80 text-sm font-medium transition-colors"
                                    >
                                        İptal
                                    </button>
                                    <button
                                        onClick={() => handleDelete(confirmDeleteId)}
                                        className="flex-1 px-4 py-2.5 rounded-xl bg-red-500 hover:bg-red-600 text-white text-sm font-medium transition-colors"
                                    >
                                        Sil
                                    </button>
                                </div>
                            </motion.div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Notification Toast */}
                <AnimatePresence>
                    {notification && (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: 20 }}
                            className={cn(
                                "absolute bottom-4 left-1/2 -translate-x-1/2 px-4 py-2.5 rounded-xl shadow-lg flex items-center gap-2",
                                notification.type === 'success' ? "bg-emerald-500 text-white" : "bg-red-500 text-white"
                            )}
                        >
                            <CheckCircle className="w-4 h-4" />
                            <span className="text-sm font-medium">{notification.message}</span>
                        </motion.div>
                    )}
                </AnimatePresence>
            </motion.div>
        </motion.div>
    );
}

export default ArchiveView;
