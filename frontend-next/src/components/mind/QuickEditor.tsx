'use client';

/**
 * QuickEditor - Hızlı Not Düzenleme
 * 
 * Graf'ta seçili not için hızlı düzenleme paneli.
 */

import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import {
    Edit3,
    Save,
    X,
    Tag,
    Palette,
    Type,
    Check,
    Pin,
    PinOff,
    Loader2
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface QuickEditorProps {
    noteId: string;
    initialTitle: string;
    initialContent: string;
    initialTags: string[];
    initialColor: string;
    isPinned?: boolean;
    onSave: (data: {
        title: string;
        content: string;
        tags: string[];
        color: string;
        isPinned: boolean;
    }) => Promise<void>;
    onClose: () => void;
    language?: 'tr' | 'en' | 'de';
}

const translations = {
    title: { tr: 'Hızlı Düzenleme', en: 'Quick Edit', de: 'Schnellbearbeitung' },
    noteTitle: { tr: 'Başlık', en: 'Title', de: 'Titel' },
    content: { tr: 'İçerik', en: 'Content', de: 'Inhalt' },
    tags: { tr: 'Etiketler', en: 'Tags', de: 'Tags' },
    addTag: { tr: 'Etiket ekle...', en: 'Add tag...', de: 'Tag hinzufügen...' },
    color: { tr: 'Renk', en: 'Color', de: 'Farbe' },
    save: { tr: 'Kaydet', en: 'Save', de: 'Speichern' },
    saving: { tr: 'Kaydediliyor...', en: 'Saving...', de: 'Wird gespeichert...' },
    pin: { tr: 'Sabitle', en: 'Pin', de: 'Anheften' },
    unpin: { tr: 'Sabitlenmeyi Kaldır', en: 'Unpin', de: 'Lösen' },
};

const COLORS = [
    { id: 'default', class: 'bg-slate-500' },
    { id: 'yellow', class: 'bg-yellow-500' },
    { id: 'green', class: 'bg-green-500' },
    { id: 'blue', class: 'bg-blue-500' },
    { id: 'purple', class: 'bg-purple-500' },
    { id: 'pink', class: 'bg-pink-500' },
    { id: 'orange', class: 'bg-orange-500' },
    { id: 'red', class: 'bg-red-500' },
];

export function QuickEditor({
    noteId,
    initialTitle,
    initialContent,
    initialTags,
    initialColor,
    isPinned = false,
    onSave,
    onClose,
    language = 'tr'
}: QuickEditorProps) {
    const t = translations;
    const [title, setTitle] = useState(initialTitle);
    const [content, setContent] = useState(initialContent);
    const [tags, setTags] = useState<string[]>(initialTags);
    const [newTag, setNewTag] = useState('');
    const [color, setColor] = useState(initialColor);
    const [pinned, setPinned] = useState(isPinned);
    const [saving, setSaving] = useState(false);
    const titleRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        titleRef.current?.focus();
    }, []);

    const handleAddTag = () => {
        const tag = newTag.trim();
        if (tag && !tags.includes(tag)) {
            setTags([...tags, tag]);
        }
        setNewTag('');
    };

    const handleRemoveTag = (tagToRemove: string) => {
        setTags(tags.filter(t => t !== tagToRemove));
    };

    const handleSave = async () => {
        if (!title.trim()) return;

        setSaving(true);
        try {
            await onSave({
                title: title.trim(),
                content,
                tags,
                color,
                isPinned: pinned
            });
            onClose();
        } catch (error) {
            console.error('Save error:', error);
        } finally {
            setSaving(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && e.ctrlKey) {
            handleSave();
        }
        if (e.key === 'Escape') {
            onClose();
        }
    };

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="absolute bottom-4 right-4 z-50 w-96 bg-card rounded-2xl border border-border shadow-2xl overflow-hidden"
            onKeyDown={handleKeyDown}
        >
            {/* Header */}
            <div className="p-4 border-b border-border bg-gradient-to-r from-violet-500/10 to-purple-500/10 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <div className="p-2 rounded-lg bg-violet-500/20">
                        <Edit3 className="w-4 h-4 text-violet-500" />
                    </div>
                    <h3 className="font-semibold">{t.title[language]}</h3>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => setPinned(!pinned)}
                        className={cn(
                            "p-2 rounded-lg transition-colors",
                            pinned
                                ? "bg-amber-500/20 text-amber-500"
                                : "hover:bg-muted text-muted-foreground"
                        )}
                        title={pinned ? t.unpin[language] : t.pin[language]}
                    >
                        {pinned ? <Pin className="w-4 h-4" /> : <PinOff className="w-4 h-4" />}
                    </button>
                    <button
                        onClick={onClose}
                        className="p-2 rounded-lg hover:bg-muted transition-colors"
                    >
                        <X className="w-4 h-4 text-muted-foreground" />
                    </button>
                </div>
            </div>

            {/* Content */}
            <div className="p-4 space-y-4 max-h-96 overflow-y-auto">
                {/* Title */}
                <div>
                    <label className="text-xs font-medium text-muted-foreground flex items-center gap-1 mb-1.5">
                        <Type className="w-3 h-3" />
                        {t.noteTitle[language]}
                    </label>
                    <input
                        ref={titleRef}
                        type="text"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        className="w-full px-3 py-2 rounded-lg bg-muted border border-border focus:outline-none focus:ring-2 focus:ring-violet-500/50 text-sm"
                        placeholder={t.noteTitle[language]}
                    />
                </div>

                {/* Content */}
                <div>
                    <label className="text-xs font-medium text-muted-foreground flex items-center gap-1 mb-1.5">
                        <Edit3 className="w-3 h-3" />
                        {t.content[language]}
                    </label>
                    <textarea
                        value={content}
                        onChange={(e) => setContent(e.target.value)}
                        rows={4}
                        className="w-full px-3 py-2 rounded-lg bg-muted border border-border focus:outline-none focus:ring-2 focus:ring-violet-500/50 text-sm resize-none"
                        placeholder={t.content[language]}
                    />
                </div>

                {/* Tags */}
                <div>
                    <label className="text-xs font-medium text-muted-foreground flex items-center gap-1 mb-1.5">
                        <Tag className="w-3 h-3" />
                        {t.tags[language]}
                    </label>
                    <div className="flex flex-wrap gap-1.5 mb-2">
                        {tags.map(tag => (
                            <span
                                key={tag}
                                className="px-2 py-0.5 rounded-full text-xs bg-violet-500/20 text-violet-600 dark:text-violet-400 flex items-center gap-1"
                            >
                                #{tag}
                                <button
                                    onClick={() => handleRemoveTag(tag)}
                                    className="hover:text-red-500 transition-colors"
                                >
                                    <X className="w-3 h-3" />
                                </button>
                            </span>
                        ))}
                    </div>
                    <div className="flex gap-2">
                        <input
                            type="text"
                            value={newTag}
                            onChange={(e) => setNewTag(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleAddTag()}
                            className="flex-1 px-3 py-1.5 rounded-lg bg-muted border border-border text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/50"
                            placeholder={t.addTag[language]}
                        />
                        <button
                            onClick={handleAddTag}
                            disabled={!newTag.trim()}
                            className="px-3 py-1.5 rounded-lg bg-violet-500/20 text-violet-600 dark:text-violet-400 hover:bg-violet-500/30 disabled:opacity-50 transition-colors"
                        >
                            <Check className="w-4 h-4" />
                        </button>
                    </div>
                </div>

                {/* Color */}
                <div>
                    <label className="text-xs font-medium text-muted-foreground flex items-center gap-1 mb-1.5">
                        <Palette className="w-3 h-3" />
                        {t.color[language]}
                    </label>
                    <div className="flex gap-2">
                        {COLORS.map(c => (
                            <button
                                key={c.id}
                                onClick={() => setColor(c.id)}
                                className={cn(
                                    "w-7 h-7 rounded-full transition-all",
                                    c.class,
                                    color === c.id
                                        ? "ring-2 ring-offset-2 ring-violet-500 scale-110"
                                        : "opacity-60 hover:opacity-100 hover:scale-105"
                                )}
                            />
                        ))}
                    </div>
                </div>
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-border bg-muted/30">
                <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={handleSave}
                    disabled={saving || !title.trim()}
                    className="w-full py-2.5 rounded-xl bg-gradient-to-r from-violet-500 to-purple-500 text-white font-medium hover:opacity-90 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
                >
                    {saving ? (
                        <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            {t.saving[language]}
                        </>
                    ) : (
                        <>
                            <Save className="w-4 h-4" />
                            {t.save[language]}
                        </>
                    )}
                </motion.button>
                <p className="text-xs text-center text-muted-foreground mt-2">
                    Ctrl+Enter
                </p>
            </div>
        </motion.div>
    );
}

export default QuickEditor;
