'use client';

import { useState, useEffect, useMemo, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Command,
    Search,
    StickyNote,
    Brain,
    MessageSquare,
    Settings,
    FileText,
    History,
    Star,
    GraduationCap,
    LayoutDashboard,
    Plus,
    Moon,
    Sun,
    Palette,
    Keyboard,
    X,
    ArrowRight,
    ChevronRight,
    Sparkles,
    Zap
} from 'lucide-react';
import { useStore, Page } from '@/store/useStore';
import { cn } from '@/lib/utils';

interface CommandItem {
    id: string;
    title: string;
    description?: string;
    icon: React.ElementType;
    action: () => void;
    category: 'navigation' | 'action' | 'settings' | 'note';
    shortcut?: string;
    keywords?: string[];
}

interface CommandPaletteProps {
    isOpen: boolean;
    onClose: () => void;
}

export function CommandPalette({ isOpen, onClose }: CommandPaletteProps) {
    const {
        setCurrentPage,
        language,
        theme,
        setTheme,
        notes,
        addNote
    } = useStore();

    const [query, setQuery] = useState('');
    const [selectedIndex, setSelectedIndex] = useState(0);
    const inputRef = useRef<HTMLInputElement>(null);
    const listRef = useRef<HTMLDivElement>(null);

    const t = {
        placeholder: { tr: 'Komut veya not ara...', en: 'Search commands or notes...', de: 'Befehle oder Notizen suchen...' },
        navigation: { tr: 'Gezinme', en: 'Navigation', de: 'Navigation' },
        actions: { tr: 'İşlemler', en: 'Actions', de: 'Aktionen' },
        settings: { tr: 'Ayarlar', en: 'Settings', de: 'Einstellungen' },
        notes: { tr: 'Notlar', en: 'Notes', de: 'Notizen' },
        noResults: { tr: 'Sonuç bulunamadı', en: 'No results found', de: 'Keine Ergebnisse' },
        goTo: { tr: 'Git', en: 'Go to', de: 'Gehe zu' },
        create: { tr: 'Oluştur', en: 'Create', de: 'Erstellen' },
        toggle: { tr: 'Değiştir', en: 'Toggle', de: 'Umschalten' },
    };

    // Build command list
    const commands = useMemo<CommandItem[]>(() => {
        const items: CommandItem[] = [
            // Navigation
            { id: 'nav-chat', title: language === 'tr' ? 'Sohbet' : 'Chat', icon: MessageSquare, action: () => setCurrentPage('chat'), category: 'navigation', shortcut: 'Ctrl+1', keywords: ['chat', 'sohbet', 'mesaj'] },
            { id: 'nav-notes', title: language === 'tr' ? 'Notlar' : 'Notes', icon: StickyNote, action: () => setCurrentPage('notes'), category: 'navigation', shortcut: 'Ctrl+3', keywords: ['notes', 'notlar'] },
            { id: 'nav-mind', title: 'Mind', icon: Brain, action: () => setCurrentPage('mind'), category: 'navigation', keywords: ['mind', 'graph', 'graf', 'harita'] },
            { id: 'nav-learning', title: language === 'tr' ? 'AI ile Öğren' : 'Learn with AI', icon: GraduationCap, action: () => setCurrentPage('learning'), category: 'navigation', shortcut: 'Ctrl+5', keywords: ['learn', 'öğren', 'ai'] },
            { id: 'nav-documents', title: language === 'tr' ? 'Dökümanlar' : 'Documents', icon: FileText, action: () => setCurrentPage('documents'), category: 'navigation', shortcut: 'Ctrl+4', keywords: ['documents', 'dökümanlar', 'belgeler'] },
            { id: 'nav-history', title: language === 'tr' ? 'Geçmiş' : 'History', icon: History, action: () => setCurrentPage('history'), category: 'navigation', shortcut: 'Ctrl+2', keywords: ['history', 'geçmiş'] },
            { id: 'nav-favorites', title: language === 'tr' ? 'Favoriler' : 'Favorites', icon: Star, action: () => setCurrentPage('favorites'), category: 'navigation', keywords: ['favorites', 'favoriler'] },
            { id: 'nav-dashboard', title: 'Dashboard', icon: LayoutDashboard, action: () => setCurrentPage('dashboard'), category: 'navigation', keywords: ['dashboard', 'panel'] },
            { id: 'nav-settings', title: language === 'tr' ? 'Ayarlar' : 'Settings', icon: Settings, action: () => setCurrentPage('settings'), category: 'navigation', shortcut: 'Ctrl+,', keywords: ['settings', 'ayarlar'] },

            // Actions
            { id: 'action-new-note', title: language === 'tr' ? 'Yeni Not Oluştur' : 'Create New Note', icon: Plus, action: () => { setCurrentPage('notes'); /* trigger new note */ }, category: 'action', shortcut: 'Ctrl+N', keywords: ['new', 'yeni', 'create', 'oluştur', 'not'] },
            { id: 'action-new-chat', title: language === 'tr' ? 'Yeni Sohbet' : 'New Chat', icon: MessageSquare, action: () => setCurrentPage('chat'), category: 'action', keywords: ['new chat', 'yeni sohbet'] },

            // Settings
            { id: 'setting-dark', title: language === 'tr' ? 'Koyu Tema' : 'Dark Theme', icon: Moon, action: () => setTheme('dark'), category: 'settings', keywords: ['dark', 'koyu', 'theme', 'tema', 'gece'] },
            { id: 'setting-light', title: language === 'tr' ? 'Açık Tema' : 'Light Theme', icon: Sun, action: () => setTheme('light'), category: 'settings', keywords: ['light', 'açık', 'theme', 'tema', 'gündüz'] },
            { id: 'setting-toggle-theme', title: language === 'tr' ? 'Tema Değiştir' : 'Toggle Theme', icon: Palette, action: () => setTheme(theme === 'dark' ? 'light' : 'dark'), category: 'settings', shortcut: 'Ctrl+Shift+T', keywords: ['toggle', 'değiştir', 'theme', 'tema'] },
        ];

        // Add notes as searchable items
        notes.slice(0, 10).forEach(note => {
            items.push({
                id: `note-${note.id}`,
                title: note.title,
                description: note.content?.substring(0, 50) + '...',
                icon: StickyNote,
                action: () => {
                    setCurrentPage('notes');
                    // We'd need a way to select the note
                },
                category: 'note',
                keywords: [note.title.toLowerCase(), ...(note.tags || []).map(t => t.toLowerCase())]
            });
        });

        return items;
    }, [language, notes, setCurrentPage, setTheme, theme]);

    // Filter commands based on query
    const filteredCommands = useMemo(() => {
        if (!query.trim()) return commands;

        const q = query.toLowerCase();
        return commands.filter(cmd => {
            const titleMatch = cmd.title.toLowerCase().includes(q);
            const descMatch = cmd.description?.toLowerCase().includes(q);
            const keywordMatch = cmd.keywords?.some(k => k.includes(q));
            return titleMatch || descMatch || keywordMatch;
        });
    }, [commands, query]);

    // Group by category
    const groupedCommands = useMemo(() => {
        const groups: Record<string, CommandItem[]> = {
            navigation: [],
            action: [],
            settings: [],
            note: []
        };

        filteredCommands.forEach(cmd => {
            groups[cmd.category].push(cmd);
        });

        return groups;
    }, [filteredCommands]);

    // Handle keyboard navigation
    const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                setSelectedIndex(prev => Math.min(prev + 1, filteredCommands.length - 1));
                break;
            case 'ArrowUp':
                e.preventDefault();
                setSelectedIndex(prev => Math.max(prev - 1, 0));
                break;
            case 'Enter':
                e.preventDefault();
                if (filteredCommands[selectedIndex]) {
                    filteredCommands[selectedIndex].action();
                    onClose();
                }
                break;
            case 'Escape':
                e.preventDefault();
                onClose();
                break;
        }
    }, [filteredCommands, selectedIndex, onClose]);

    // Reset on query change
    useEffect(() => {
        setSelectedIndex(0);
    }, [query]);

    // Focus input when opened
    useEffect(() => {
        if (isOpen) {
            setQuery('');
            setSelectedIndex(0);
            setTimeout(() => inputRef.current?.focus(), 100);
        }
    }, [isOpen]);

    // Scroll selected item into view
    useEffect(() => {
        const selectedEl = listRef.current?.querySelector(`[data-index="${selectedIndex}"]`);
        selectedEl?.scrollIntoView({ block: 'nearest' });
    }, [selectedIndex]);

    const getCategoryLabel = (category: string) => {
        switch (category) {
            case 'navigation': return t.navigation[language];
            case 'action': return t.actions[language];
            case 'settings': return t.settings[language];
            case 'note': return t.notes[language];
            default: return category;
        }
    };

    let flatIndex = -1;

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
                    />

                    {/* Modal */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: -20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: -20 }}
                        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
                        className="fixed top-[15%] left-1/2 -translate-x-1/2 w-full max-w-xl z-50"
                    >
                        <div className="bg-card/95 backdrop-blur-xl border border-border/50 rounded-2xl shadow-2xl overflow-hidden">
                            {/* Header */}
                            <div className="flex items-center gap-3 px-4 py-3 border-b border-border/50">
                                <div className="p-2 rounded-lg bg-gradient-to-r from-purple-500 to-pink-500">
                                    <Command className="w-4 h-4 text-white" />
                                </div>
                                <input
                                    ref={inputRef}
                                    type="text"
                                    value={query}
                                    onChange={(e) => setQuery(e.target.value)}
                                    onKeyDown={handleKeyDown}
                                    placeholder={t.placeholder[language]}
                                    className="flex-1 bg-transparent text-foreground placeholder-muted-foreground focus:outline-none text-sm"
                                />
                                <kbd className="hidden sm:inline-flex items-center gap-1 px-2 py-1 rounded-md bg-muted text-muted-foreground text-xs font-mono">
                                    ESC
                                </kbd>
                            </div>

                            {/* Command List */}
                            <div
                                ref={listRef}
                                className="max-h-[400px] overflow-y-auto py-2"
                            >
                                {filteredCommands.length === 0 ? (
                                    <div className="px-4 py-8 text-center text-muted-foreground">
                                        <Search className="w-8 h-8 mx-auto mb-2 opacity-50" />
                                        <p className="text-sm">{t.noResults[language]}</p>
                                    </div>
                                ) : (
                                    Object.entries(groupedCommands).map(([category, items]) => {
                                        if (items.length === 0) return null;

                                        return (
                                            <div key={category} className="mb-2">
                                                <div className="px-4 py-1">
                                                    <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                                        {getCategoryLabel(category)}
                                                    </span>
                                                </div>
                                                {items.map((cmd) => {
                                                    flatIndex++;
                                                    const isSelected = flatIndex === selectedIndex;
                                                    const Icon = cmd.icon;
                                                    const currentIndex = flatIndex;

                                                    return (
                                                        <button
                                                            key={cmd.id}
                                                            data-index={currentIndex}
                                                            onClick={() => {
                                                                cmd.action();
                                                                onClose();
                                                            }}
                                                            onMouseEnter={() => setSelectedIndex(currentIndex)}
                                                            className={cn(
                                                                "w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors",
                                                                isSelected
                                                                    ? "bg-primary-500/10 text-primary-600 dark:text-primary-400"
                                                                    : "hover:bg-accent text-foreground"
                                                            )}
                                                        >
                                                            <div className={cn(
                                                                "p-1.5 rounded-lg transition-colors",
                                                                isSelected ? "bg-primary-500/20" : "bg-muted"
                                                            )}>
                                                                <Icon className="w-4 h-4" />
                                                            </div>
                                                            <div className="flex-1 min-w-0">
                                                                <p className="text-sm font-medium truncate">{cmd.title}</p>
                                                                {cmd.description && (
                                                                    <p className="text-xs text-muted-foreground truncate">{cmd.description}</p>
                                                                )}
                                                            </div>
                                                            {cmd.shortcut && (
                                                                <kbd className="hidden sm:inline-flex items-center gap-1 px-2 py-0.5 rounded bg-muted text-muted-foreground text-xs font-mono">
                                                                    {cmd.shortcut}
                                                                </kbd>
                                                            )}
                                                            {isSelected && (
                                                                <ChevronRight className="w-4 h-4 text-primary-500" />
                                                            )}
                                                        </button>
                                                    );
                                                })}
                                            </div>
                                        );
                                    })
                                )}
                            </div>

                            {/* Footer */}
                            <div className="flex items-center justify-between px-4 py-2 border-t border-border/50 bg-muted/30">
                                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                                    <span className="flex items-center gap-1">
                                        <kbd className="px-1.5 py-0.5 rounded bg-muted font-mono">↑↓</kbd>
                                        {language === 'tr' ? 'gezin' : 'navigate'}
                                    </span>
                                    <span className="flex items-center gap-1">
                                        <kbd className="px-1.5 py-0.5 rounded bg-muted font-mono">↵</kbd>
                                        {language === 'tr' ? 'seç' : 'select'}
                                    </span>
                                </div>
                                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                                    <Sparkles className="w-3 h-3 text-purple-500" />
                                    <span>Command Palette</span>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
}

export default CommandPalette;
