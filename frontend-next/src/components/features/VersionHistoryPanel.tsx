'use client';

/**
 * VersionHistoryPanel - Not versiyon geçmişi paneli
 * 
 * Her kaydetmede otomatik versiyon, diff görünümü, geri yükleme.
 */

import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    History,
    Clock,
    RotateCcw,
    Eye,
    X,
    ChevronDown,
    ChevronUp,
    FileDiff,
    CheckCircle
} from 'lucide-react';
import { Note } from '@/store/useStore';
import { cn, formatDate } from '@/lib/utils';

interface NoteVersion {
    id: string;
    noteId: string;
    title: string;
    content: string;
    timestamp: Date;
    changeType: 'create' | 'edit' | 'restore';
}

interface VersionHistoryPanelProps {
    note: Note;
    versions: NoteVersion[];
    onRestore: (version: NoteVersion) => void;
    onClose: () => void;
    language?: 'tr' | 'en' | 'de';
}

const translations = {
    history: { tr: 'Versiyon Geçmişi', en: 'Version History', de: 'Versionshistorie' },
    current: { tr: 'Mevcut', en: 'Current', de: 'Aktuell' },
    restore: { tr: 'Geri Yükle', en: 'Restore', de: 'Wiederherstellen' },
    preview: { tr: 'Önizle', en: 'Preview', de: 'Vorschau' },
    noVersions: { tr: 'Henüz versiyon geçmişi yok', en: 'No version history yet', de: 'Noch keine Versionshistorie' },
    created: { tr: 'Oluşturuldu', en: 'Created', de: 'Erstellt' },
    edited: { tr: 'Düzenlendi', en: 'Edited', de: 'Bearbeitet' },
    restored: { tr: 'Geri yüklendi', en: 'Restored', de: 'Wiederhergestellt' },
    confirmRestore: { tr: 'Bu versiyonu geri yüklemek istiyor musunuz?', en: 'Restore this version?', de: 'Diese Version wiederherstellen?' },
    changes: { tr: 'değişiklik', en: 'changes', de: 'Änderungen' },
};

// Simple diff calculator
function calculateDiff(oldText: string, newText: string): { added: number; removed: number } {
    const oldLines = oldText.split('\n');
    const newLines = newText.split('\n');

    let added = 0;
    let removed = 0;

    // Simple line-based diff
    newLines.forEach(line => {
        if (!oldLines.includes(line)) added++;
    });

    oldLines.forEach(line => {
        if (!newLines.includes(line)) removed++;
    });

    return { added, removed };
}

export function VersionHistoryPanel({
    note,
    versions,
    onRestore,
    onClose,
    language = 'tr'
}: VersionHistoryPanelProps) {
    const t = translations;
    const [selectedVersion, setSelectedVersion] = useState<NoteVersion | null>(null);
    const [confirmRestore, setConfirmRestore] = useState<string | null>(null);
    const [showDiff, setShowDiff] = useState(false);

    // Versiyonları tarihe göre sırala (en yeni en üstte)
    const sortedVersions = useMemo(() => {
        return [...versions].sort((a, b) =>
            new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
        );
    }, [versions]);

    const handleRestore = (version: NoteVersion) => {
        onRestore(version);
        setConfirmRestore(null);
        setSelectedVersion(null);
    };

    const getChangeTypeLabel = (type: NoteVersion['changeType']) => {
        switch (type) {
            case 'create': return t.created[language];
            case 'edit': return t.edited[language];
            case 'restore': return t.restored[language];
        }
    };

    const getChangeTypeColor = (type: NoteVersion['changeType']) => {
        switch (type) {
            case 'create': return 'text-emerald-500 bg-emerald-500/10';
            case 'edit': return 'text-blue-500 bg-blue-500/10';
            case 'restore': return 'text-amber-500 bg-amber-500/10';
        }
    };

    return (
        <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="h-full flex flex-col bg-card border-l border-border"
        >
            {/* Header */}
            <div className="p-4 border-b border-border bg-gradient-to-r from-indigo-500/5 to-violet-500/5">
                <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                        <div className="p-2 rounded-lg bg-indigo-500/10">
                            <History className="w-4 h-4 text-indigo-500" />
                        </div>
                        <h3 className="font-semibold">{t.history[language]}</h3>
                    </div>
                    <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-muted transition-colors">
                        <X className="w-4 h-4 text-muted-foreground" />
                    </button>
                </div>
                <p className="text-xs text-muted-foreground line-clamp-1">{note.title}</p>
            </div>

            {/* Timeline */}
            <div className="flex-1 overflow-y-auto p-4">
                {sortedVersions.length > 0 ? (
                    <div className="relative">
                        {/* Timeline line */}
                        <div className="absolute left-4 top-6 bottom-6 w-0.5 bg-border" />

                        {/* Version items */}
                        <div className="space-y-4">
                            {/* Current version indicator */}
                            <div className="relative flex items-start gap-4">
                                <div className="relative z-10 w-8 h-8 rounded-full bg-primary-500 flex items-center justify-center">
                                    <CheckCircle className="w-4 h-4 text-white" />
                                </div>
                                <div className="flex-1 p-3 rounded-xl bg-primary-500/10 border border-primary-500/30">
                                    <div className="flex items-center justify-between mb-1">
                                        <span className="text-xs font-medium text-primary-600 dark:text-primary-400">
                                            {t.current[language]}
                                        </span>
                                        <span className="text-[10px] text-muted-foreground">
                                            {formatDate(note.updatedAt)}
                                        </span>
                                    </div>
                                    <p className="text-sm font-medium truncate">{note.title}</p>
                                    <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
                                        {note.content?.slice(0, 100) || 'Boş not'}
                                    </p>
                                </div>
                            </div>

                            {/* Previous versions */}
                            {sortedVersions.map((version, index) => {
                                const prevVersion = sortedVersions[index + 1];
                                const diff = prevVersion
                                    ? calculateDiff(prevVersion.content, version.content)
                                    : { added: 0, removed: 0 };

                                return (
                                    <div key={version.id} className="relative flex items-start gap-4">
                                        {/* Timeline dot */}
                                        <div className={cn(
                                            "relative z-10 w-8 h-8 rounded-full flex items-center justify-center border-2 border-background",
                                            getChangeTypeColor(version.changeType)
                                        )}>
                                            <Clock className="w-3.5 h-3.5" />
                                        </div>

                                        {/* Version card */}
                                        <motion.div
                                            whileHover={{ scale: 1.01 }}
                                            className="flex-1 p-3 rounded-xl bg-muted/50 hover:bg-muted border border-transparent hover:border-border transition-all cursor-pointer"
                                            onClick={() => setSelectedVersion(selectedVersion?.id === version.id ? null : version)}
                                        >
                                            <div className="flex items-center justify-between mb-1">
                                                <span className={cn("text-xs font-medium px-2 py-0.5 rounded-full", getChangeTypeColor(version.changeType))}>
                                                    {getChangeTypeLabel(version.changeType)}
                                                </span>
                                                <span className="text-[10px] text-muted-foreground">
                                                    {formatDate(version.timestamp)}
                                                </span>
                                            </div>
                                            <p className="text-sm font-medium truncate">{version.title}</p>

                                            {/* Diff indicator */}
                                            {(diff.added > 0 || diff.removed > 0) && (
                                                <div className="flex items-center gap-2 mt-2 text-[10px]">
                                                    {diff.added > 0 && (
                                                        <span className="text-emerald-500">+{diff.added}</span>
                                                    )}
                                                    {diff.removed > 0 && (
                                                        <span className="text-red-500">-{diff.removed}</span>
                                                    )}
                                                    <span className="text-muted-foreground">{t.changes[language]}</span>
                                                </div>
                                            )}

                                            {/* Expanded content */}
                                            <AnimatePresence>
                                                {selectedVersion?.id === version.id && (
                                                    <motion.div
                                                        initial={{ height: 0, opacity: 0 }}
                                                        animate={{ height: 'auto', opacity: 1 }}
                                                        exit={{ height: 0, opacity: 0 }}
                                                        className="mt-3 pt-3 border-t border-border overflow-hidden"
                                                    >
                                                        <p className="text-xs text-muted-foreground whitespace-pre-wrap line-clamp-6 mb-3">
                                                            {version.content || 'Boş not'}
                                                        </p>
                                                        <div className="flex gap-2">
                                                            <button
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    setConfirmRestore(version.id);
                                                                }}
                                                                className="flex-1 py-2 rounded-lg bg-primary-500/10 text-primary-600 dark:text-primary-400 text-xs font-medium hover:bg-primary-500/20 transition-colors flex items-center justify-center gap-1.5"
                                                            >
                                                                <RotateCcw className="w-3.5 h-3.5" />
                                                                {t.restore[language]}
                                                            </button>
                                                        </div>
                                                    </motion.div>
                                                )}
                                            </AnimatePresence>
                                        </motion.div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center h-full text-center">
                        <div className="p-4 rounded-2xl bg-muted/30 mb-3">
                            <History className="w-10 h-10 text-muted-foreground/30" />
                        </div>
                        <p className="text-sm text-muted-foreground">{t.noVersions[language]}</p>
                    </div>
                )}
            </div>

            {/* Restore Confirmation */}
            <AnimatePresence>
                {confirmRestore && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="absolute inset-0 bg-black/60 flex items-center justify-center p-4"
                        onClick={() => setConfirmRestore(null)}
                    >
                        <motion.div
                            initial={{ scale: 0.95 }}
                            animate={{ scale: 1 }}
                            exit={{ scale: 0.95 }}
                            className="bg-card rounded-xl p-4 max-w-xs w-full border border-border"
                            onClick={(e) => e.stopPropagation()}
                        >
                            <h4 className="font-semibold mb-3">{t.confirmRestore[language]}</h4>
                            <div className="flex gap-2">
                                <button
                                    onClick={() => setConfirmRestore(null)}
                                    className="flex-1 py-2 rounded-lg bg-muted text-sm"
                                >
                                    İptal
                                </button>
                                <button
                                    onClick={() => {
                                        const version = versions.find(v => v.id === confirmRestore);
                                        if (version) handleRestore(version);
                                    }}
                                    className="flex-1 py-2 rounded-lg bg-primary-500 text-white text-sm"
                                >
                                    {t.restore[language]}
                                </button>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
}

export default VersionHistoryPanel;
