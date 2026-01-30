'use client';

/**
 * NodeDetailSidebar - Mind Graf Node Detay Sidebar'ı
 * 
 * Tıklanan node için detaylı bilgi, bağlantılar, backlinks ve hızlı düzenleme.
 */

import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    FileText,
    Link2,
    ArrowLeft,
    ArrowRight,
    Edit3,
    Tag,
    Folder,
    Clock,
    X,
    ChevronRight,
    Sparkles,
    Network,
    Save,
    ExternalLink
} from 'lucide-react';
import { Note, NoteFolder } from '@/store/useStore';
import { cn, formatDate } from '@/lib/utils';

interface NodeDetailSidebarProps {
    note: Note | null;
    allNotes: Note[];
    folders: NoteFolder[];
    backlinks: Note[];
    outgoingLinks: Note[];
    onNavigate: (noteId: string) => void;
    onEdit: (note: Note) => void;
    onClose: () => void;
    language?: 'tr' | 'en' | 'de';
}

const translations = {
    details: { tr: 'Not Detayları', en: 'Note Details', de: 'Notizdetails' },
    content: { tr: 'İçerik', en: 'Content', de: 'Inhalt' },
    connections: { tr: 'Bağlantılar', en: 'Connections', de: 'Verbindungen' },
    backlinks: { tr: 'Gelen', en: 'Incoming', de: 'Eingehend' },
    outgoing: { tr: 'Giden', en: 'Outgoing', de: 'Ausgehend' },
    tags: { tr: 'Etiketler', en: 'Tags', de: 'Tags' },
    folder: { tr: 'Klasör', en: 'Folder', de: 'Ordner' },
    edit: { tr: 'Düzenle', en: 'Edit', de: 'Bearbeiten' },
    openNote: { tr: 'Notu Aç', en: 'Open Note', de: 'Notiz öffnen' },
    noConnections: { tr: 'Bağlantı yok', en: 'No connections', de: 'Keine Verbindungen' },
    aiSummary: { tr: 'AI Özet', en: 'AI Summary', de: 'KI-Zusammenfassung' },
};

export function NodeDetailSidebar({
    note,
    allNotes,
    folders,
    backlinks,
    outgoingLinks,
    onNavigate,
    onEdit,
    onClose,
    language = 'tr'
}: NodeDetailSidebarProps) {
    const t = translations;
    const [activeTab, setActiveTab] = useState<'content' | 'connections'>('content');

    // Klasör adını bul
    const folderName = useMemo(() => {
        if (!note?.folder) return null;
        const folder = folders.find(f => f.id === note.folder || f.name === note.folder);
        return folder?.name || note.folder;
    }, [note?.folder, folders]);

    if (!note) {
        return (
            <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="w-80 h-full flex flex-col bg-card border-l border-border"
            >
                <div className="flex-1 flex items-center justify-center">
                    <div className="text-center p-6">
                        <div className="p-4 rounded-2xl bg-muted/30 mb-4 inline-block">
                            <Network className="w-12 h-12 text-muted-foreground/30" />
                        </div>
                        <p className="text-sm text-muted-foreground">
                            {language === 'tr' ? 'Detay görüntülemek için bir not seçin' : 'Select a note to view details'}
                        </p>
                    </div>
                </div>
            </motion.div>
        );
    }

    return (
        <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="w-80 h-full flex flex-col bg-card border-l border-border"
        >
            {/* Header */}
            <div className="p-4 border-b border-border bg-gradient-to-r from-primary-500/5 to-purple-500/5">
                <div className="flex items-center justify-between mb-3">
                    <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-muted transition-colors">
                        <X className="w-4 h-4 text-muted-foreground" />
                    </button>
                    <div className="flex items-center gap-1.5">
                        <button
                            onClick={() => onEdit(note)}
                            className="p-1.5 rounded-lg hover:bg-primary-500/10 text-muted-foreground hover:text-primary-500 transition-colors"
                        >
                            <Edit3 className="w-4 h-4" />
                        </button>
                        <button
                            onClick={() => onNavigate(note.id)}
                            className="px-2.5 py-1.5 rounded-lg bg-primary-500/10 text-primary-600 dark:text-primary-400 text-xs font-medium hover:bg-primary-500/20 transition-colors flex items-center gap-1"
                        >
                            <ExternalLink className="w-3.5 h-3.5" />
                            {t.openNote[language]}
                        </button>
                    </div>
                </div>

                {/* Note Title */}
                <div className="flex items-start gap-3">
                    <div className={cn(
                        "p-2.5 rounded-xl",
                        note.color === 'blue' ? 'bg-blue-500/20' :
                            note.color === 'green' ? 'bg-green-500/20' :
                                note.color === 'purple' ? 'bg-purple-500/20' :
                                    note.color === 'pink' ? 'bg-pink-500/20' :
                                        note.color === 'orange' ? 'bg-orange-500/20' :
                                            note.color === 'red' ? 'bg-red-500/20' :
                                                'bg-yellow-500/20'
                    )}>
                        <FileText className={cn(
                            "w-5 h-5",
                            note.color === 'blue' ? 'text-blue-500' :
                                note.color === 'green' ? 'text-green-500' :
                                    note.color === 'purple' ? 'text-purple-500' :
                                        note.color === 'pink' ? 'text-pink-500' :
                                            note.color === 'orange' ? 'text-orange-500' :
                                                note.color === 'red' ? 'text-red-500' :
                                                    'text-yellow-500'
                        )} />
                    </div>
                    <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-sm leading-tight mb-1">{note.title}</h3>
                        <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
                            <Clock className="w-3 h-3" />
                            {formatDate(note.updatedAt)}
                        </div>
                    </div>
                </div>

                {/* Metadata */}
                <div className="flex flex-wrap gap-2 mt-3">
                    {folderName && (
                        <div className="flex items-center gap-1 px-2 py-1 rounded-md bg-muted text-xs">
                            <Folder className="w-3 h-3 text-muted-foreground" />
                            <span>{folderName}</span>
                        </div>
                    )}
                    {note.tags && note.tags.length > 0 && note.tags.slice(0, 3).map(tag => (
                        <div key={tag} className="flex items-center gap-1 px-2 py-1 rounded-md bg-primary-500/10 text-xs text-primary-600 dark:text-primary-400">
                            <Tag className="w-3 h-3" />
                            <span>{tag}</span>
                        </div>
                    ))}
                    {note.tags && note.tags.length > 3 && (
                        <span className="px-2 py-1 text-xs text-muted-foreground">
                            +{note.tags.length - 3}
                        </span>
                    )}
                </div>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-border">
                <button
                    onClick={() => setActiveTab('content')}
                    className={cn(
                        "flex-1 px-4 py-2.5 text-xs font-medium transition-colors relative",
                        activeTab === 'content'
                            ? "text-primary-600 dark:text-primary-400"
                            : "text-muted-foreground hover:text-foreground"
                    )}
                >
                    {t.content[language]}
                    {activeTab === 'content' && (
                        <motion.div
                            layoutId="sidebar-tab"
                            className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-500"
                        />
                    )}
                </button>
                <button
                    onClick={() => setActiveTab('connections')}
                    className={cn(
                        "flex-1 px-4 py-2.5 text-xs font-medium transition-colors relative flex items-center justify-center gap-1.5",
                        activeTab === 'connections'
                            ? "text-primary-600 dark:text-primary-400"
                            : "text-muted-foreground hover:text-foreground"
                    )}
                >
                    {t.connections[language]}
                    <span className="px-1.5 py-0.5 rounded-full bg-muted text-[10px]">
                        {backlinks.length + outgoingLinks.length}
                    </span>
                    {activeTab === 'connections' && (
                        <motion.div
                            layoutId="sidebar-tab"
                            className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-500"
                        />
                    )}
                </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto">
                <AnimatePresence mode="wait">
                    {activeTab === 'content' ? (
                        <motion.div
                            key="content"
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            className="p-4"
                        >
                            <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                                {note.content || 'Bu not boş.'}
                            </p>
                        </motion.div>
                    ) : (
                        <motion.div
                            key="connections"
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            className="p-4 space-y-4"
                        >
                            {/* Backlinks */}
                            <div>
                                <div className="flex items-center gap-2 mb-2">
                                    <ArrowLeft className="w-3.5 h-3.5 text-emerald-500" />
                                    <span className="text-xs font-medium text-emerald-600 dark:text-emerald-400">
                                        {t.backlinks[language]}
                                    </span>
                                    <span className="ml-auto px-1.5 py-0.5 rounded-full bg-emerald-500/10 text-[10px] font-medium text-emerald-600 dark:text-emerald-400">
                                        {backlinks.length}
                                    </span>
                                </div>
                                {backlinks.length > 0 ? (
                                    <div className="space-y-1">
                                        {backlinks.map(linked => (
                                            <button
                                                key={linked.id}
                                                onClick={() => onNavigate(linked.id)}
                                                className="w-full flex items-center gap-2 p-2 rounded-lg hover:bg-muted text-left group transition-colors"
                                            >
                                                <FileText className="w-3.5 h-3.5 text-muted-foreground group-hover:text-emerald-500" />
                                                <span className="flex-1 text-xs truncate group-hover:text-emerald-600 dark:group-hover:text-emerald-400">
                                                    {linked.title}
                                                </span>
                                                <ChevronRight className="w-3.5 h-3.5 text-muted-foreground opacity-0 group-hover:opacity-100" />
                                            </button>
                                        ))}
                                    </div>
                                ) : (
                                    <p className="text-xs text-muted-foreground p-2">{t.noConnections[language]}</p>
                                )}
                            </div>

                            {/* Outgoing Links */}
                            <div>
                                <div className="flex items-center gap-2 mb-2">
                                    <ArrowRight className="w-3.5 h-3.5 text-blue-500" />
                                    <span className="text-xs font-medium text-blue-600 dark:text-blue-400">
                                        {t.outgoing[language]}
                                    </span>
                                    <span className="ml-auto px-1.5 py-0.5 rounded-full bg-blue-500/10 text-[10px] font-medium text-blue-600 dark:text-blue-400">
                                        {outgoingLinks.length}
                                    </span>
                                </div>
                                {outgoingLinks.length > 0 ? (
                                    <div className="space-y-1">
                                        {outgoingLinks.map(linked => (
                                            <button
                                                key={linked.id}
                                                onClick={() => onNavigate(linked.id)}
                                                className="w-full flex items-center gap-2 p-2 rounded-lg hover:bg-muted text-left group transition-colors"
                                            >
                                                <FileText className="w-3.5 h-3.5 text-muted-foreground group-hover:text-blue-500" />
                                                <span className="flex-1 text-xs truncate group-hover:text-blue-600 dark:group-hover:text-blue-400">
                                                    {linked.title}
                                                </span>
                                                <ChevronRight className="w-3.5 h-3.5 text-muted-foreground opacity-0 group-hover:opacity-100" />
                                            </button>
                                        ))}
                                    </div>
                                ) : (
                                    <p className="text-xs text-muted-foreground p-2">{t.noConnections[language]}</p>
                                )}
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </motion.div>
    );
}

export default NodeDetailSidebar;
