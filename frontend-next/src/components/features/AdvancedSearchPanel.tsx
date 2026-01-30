'use client';

/**
 * AdvancedSearchPanel - Gelişmiş Arama Paneli
 * 
 * Full-text search, regex, filtre kombinasyonları ve kayıtlı aramalar.
 */

import React, { useState, useMemo, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Search,
    X,
    Filter,
    Calendar,
    Tag,
    Palette,
    Folder,
    Save,
    Clock,
    Trash2,
    ChevronDown,
    ChevronUp,
    Regex,
    FileText,
    Bookmark,
    History
} from 'lucide-react';
import { Note, NoteFolder } from '@/store/useStore';
import { cn, formatDate } from '@/lib/utils';

interface SearchFilters {
    query: string;
    isRegex: boolean;
    dateFrom?: Date;
    dateTo?: Date;
    tags: string[];
    colors: string[];
    folders: string[];
    pinnedOnly: boolean;
}

interface SavedSearch {
    id: string;
    name: string;
    filters: SearchFilters;
    createdAt: Date;
}

interface AdvancedSearchPanelProps {
    notes: Note[];
    folders: NoteFolder[];
    allTags: string[];
    onSelectNote: (note: Note) => void;
    onClose: () => void;
    language?: 'tr' | 'en' | 'de';
}

const NOTE_COLORS = [
    { id: 'default', name: 'Varsayılan', preview: 'bg-gray-400' },
    { id: 'yellow', name: 'Sarı', preview: 'bg-yellow-400' },
    { id: 'green', name: 'Yeşil', preview: 'bg-green-400' },
    { id: 'blue', name: 'Mavi', preview: 'bg-blue-400' },
    { id: 'purple', name: 'Mor', preview: 'bg-purple-400' },
    { id: 'pink', name: 'Pembe', preview: 'bg-pink-400' },
    { id: 'orange', name: 'Turuncu', preview: 'bg-orange-400' },
    { id: 'red', name: 'Kırmızı', preview: 'bg-red-400' },
];

const translations = {
    advancedSearch: { tr: 'Gelişmiş Arama', en: 'Advanced Search', de: 'Erweiterte Suche' },
    searchPlaceholder: { tr: 'Not ara...', en: 'Search notes...', de: 'Notizen suchen...' },
    regex: { tr: 'Regex', en: 'Regex', de: 'Regex' },
    filters: { tr: 'Filtreler', en: 'Filters', de: 'Filter' },
    dateRange: { tr: 'Tarih Aralığı', en: 'Date Range', de: 'Datumsbereich' },
    from: { tr: 'Başlangıç', en: 'From', de: 'Von' },
    to: { tr: 'Bitiş', en: 'To', de: 'Bis' },
    tags: { tr: 'Etiketler', en: 'Tags', de: 'Tags' },
    colors: { tr: 'Renkler', en: 'Colors', de: 'Farben' },
    folders: { tr: 'Klasörler', en: 'Folders', de: 'Ordner' },
    pinnedOnly: { tr: 'Sadece Sabitlenmiş', en: 'Pinned Only', de: 'Nur Angeheftete' },
    savedSearches: { tr: 'Kayıtlı Aramalar', en: 'Saved Searches', de: 'Gespeicherte Suchen' },
    saveSearch: { tr: 'Aramayı Kaydet', en: 'Save Search', de: 'Suche speichern' },
    clearFilters: { tr: 'Filtreleri Temizle', en: 'Clear Filters', de: 'Filter löschen' },
    results: { tr: 'sonuç', en: 'results', de: 'Ergebnisse' },
    noResults: { tr: 'Sonuç bulunamadı', en: 'No results found', de: 'Keine Ergebnisse gefunden' },
    recentSearches: { tr: 'Son Aramalar', en: 'Recent Searches', de: 'Letzte Suchen' },
};

export function AdvancedSearchPanel({
    notes,
    folders,
    allTags,
    onSelectNote,
    onClose,
    language = 'tr'
}: AdvancedSearchPanelProps) {
    const t = translations;

    const [filters, setFilters] = useState<SearchFilters>({
        query: '',
        isRegex: false,
        tags: [],
        colors: [],
        folders: [],
        pinnedOnly: false,
    });

    const [showFilters, setShowFilters] = useState(false);
    const [savedSearches, setSavedSearches] = useState<SavedSearch[]>([]);
    const [recentSearches, setRecentSearches] = useState<string[]>([]);
    const [saveSearchName, setSaveSearchName] = useState('');
    const [showSaveDialog, setShowSaveDialog] = useState(false);

    // Filtrelenmiş notlar
    const filteredNotes = useMemo(() => {
        return notes.filter(note => {
            // Query filter
            if (filters.query) {
                try {
                    if (filters.isRegex) {
                        const regex = new RegExp(filters.query, 'gi');
                        if (!regex.test(note.title) && !regex.test(note.content)) {
                            return false;
                        }
                    } else {
                        const query = filters.query.toLowerCase();
                        if (!note.title.toLowerCase().includes(query) &&
                            !note.content.toLowerCase().includes(query)) {
                            return false;
                        }
                    }
                } catch {
                    // Invalid regex, treat as normal search
                    const query = filters.query.toLowerCase();
                    if (!note.title.toLowerCase().includes(query) &&
                        !note.content.toLowerCase().includes(query)) {
                        return false;
                    }
                }
            }

            // Date filter
            if (filters.dateFrom) {
                if (new Date(note.updatedAt) < filters.dateFrom) return false;
            }
            if (filters.dateTo) {
                if (new Date(note.updatedAt) > filters.dateTo) return false;
            }

            // Tags filter
            if (filters.tags.length > 0) {
                const noteTags = note.tags || [];
                if (!filters.tags.some(tag => noteTags.includes(tag))) return false;
            }

            // Colors filter
            if (filters.colors.length > 0) {
                if (!filters.colors.includes(note.color || 'default')) return false;
            }

            // Folders filter
            if (filters.folders.length > 0) {
                if (!filters.folders.includes(note.folder || '')) return false;
            }

            // Pinned filter
            if (filters.pinnedOnly && !note.isPinned) return false;

            return true;
        }).sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime());
    }, [notes, filters]);

    // Highlight matched text
    const highlightMatch = useCallback((text: string, query: string, isRegex: boolean) => {
        if (!query) return text;

        try {
            const regex = isRegex ? new RegExp(`(${query})`, 'gi') : new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
            const parts = text.split(regex);

            return parts.map((part, i) =>
                regex.test(part) ? (
                    <mark key={i} className="bg-yellow-300 dark:bg-yellow-600 px-0.5 rounded">{part}</mark>
                ) : part
            );
        } catch {
            return text;
        }
    }, []);

    // Save search
    const handleSaveSearch = () => {
        if (!saveSearchName.trim()) return;

        const newSearch: SavedSearch = {
            id: Date.now().toString(),
            name: saveSearchName.trim(),
            filters: { ...filters },
            createdAt: new Date()
        };

        setSavedSearches(prev => [newSearch, ...prev]);
        setSaveSearchName('');
        setShowSaveDialog(false);
    };

    // Load saved search
    const loadSavedSearch = (search: SavedSearch) => {
        setFilters(search.filters);
    };

    // Delete saved search
    const deleteSavedSearch = (id: string) => {
        setSavedSearches(prev => prev.filter(s => s.id !== id));
    };

    // Clear filters
    const clearFilters = () => {
        setFilters({
            query: '',
            isRegex: false,
            tags: [],
            colors: [],
            folders: [],
            pinnedOnly: false,
        });
    };

    // Toggle filter value
    const toggleArrayFilter = (key: 'tags' | 'colors' | 'folders', value: string) => {
        setFilters(prev => ({
            ...prev,
            [key]: prev[key].includes(value)
                ? prev[key].filter(v => v !== value)
                : [...prev[key], value]
        }));
    };

    const hasActiveFilters = filters.tags.length > 0 || filters.colors.length > 0 ||
        filters.folders.length > 0 || filters.pinnedOnly || filters.dateFrom || filters.dateTo;

    return (
        <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="absolute inset-x-4 top-4 z-50 max-w-2xl mx-auto"
        >
            <div className="bg-card rounded-2xl shadow-2xl border border-border overflow-hidden">
                {/* Search Header */}
                <div className="p-4 border-b border-border bg-gradient-to-r from-primary-500/5 to-purple-500/5">
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-primary-500/10">
                            <Search className="w-5 h-5 text-primary-500" />
                        </div>
                        <div className="flex-1 relative">
                            <input
                                type="text"
                                value={filters.query}
                                onChange={(e) => setFilters(prev => ({ ...prev, query: e.target.value }))}
                                placeholder={t.searchPlaceholder[language]}
                                className="w-full px-4 py-2.5 rounded-xl bg-background border border-border focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 outline-none transition-all text-sm"
                                autoFocus
                            />
                            {filters.query && (
                                <button
                                    onClick={() => setFilters(prev => ({ ...prev, query: '' }))}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-full hover:bg-muted transition-colors"
                                >
                                    <X className="w-4 h-4 text-muted-foreground" />
                                </button>
                            )}
                        </div>
                        <button
                            onClick={() => setFilters(prev => ({ ...prev, isRegex: !prev.isRegex }))}
                            className={cn(
                                "px-3 py-2 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5",
                                filters.isRegex
                                    ? "bg-amber-500/20 text-amber-600 dark:text-amber-400 border border-amber-500/30"
                                    : "bg-muted text-muted-foreground hover:bg-muted/80"
                            )}
                        >
                            <Regex className="w-3.5 h-3.5" />
                            {t.regex[language]}
                        </button>
                        <button
                            onClick={() => setShowFilters(!showFilters)}
                            className={cn(
                                "px-3 py-2 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5",
                                hasActiveFilters || showFilters
                                    ? "bg-primary-500/20 text-primary-600 dark:text-primary-400 border border-primary-500/30"
                                    : "bg-muted text-muted-foreground hover:bg-muted/80"
                            )}
                        >
                            <Filter className="w-3.5 h-3.5" />
                            {t.filters[language]}
                            {hasActiveFilters && (
                                <span className="w-2 h-2 rounded-full bg-primary-500" />
                            )}
                        </button>
                        <button
                            onClick={onClose}
                            className="p-2 rounded-lg hover:bg-muted transition-colors"
                        >
                            <X className="w-5 h-5 text-muted-foreground" />
                        </button>
                    </div>
                </div>

                {/* Filters Panel */}
                <AnimatePresence>
                    {showFilters && (
                        <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="border-b border-border overflow-hidden"
                        >
                            <div className="p-4 space-y-4 bg-muted/30">
                                {/* Date Range */}
                                <div className="grid grid-cols-2 gap-3">
                                    <div>
                                        <label className="text-xs font-medium text-muted-foreground mb-1 block">
                                            {t.from[language]}
                                        </label>
                                        <input
                                            type="date"
                                            value={filters.dateFrom?.toISOString().split('T')[0] || ''}
                                            onChange={(e) => setFilters(prev => ({
                                                ...prev,
                                                dateFrom: e.target.value ? new Date(e.target.value) : undefined
                                            }))}
                                            className="w-full px-3 py-2 rounded-lg bg-background border border-border text-sm"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-xs font-medium text-muted-foreground mb-1 block">
                                            {t.to[language]}
                                        </label>
                                        <input
                                            type="date"
                                            value={filters.dateTo?.toISOString().split('T')[0] || ''}
                                            onChange={(e) => setFilters(prev => ({
                                                ...prev,
                                                dateTo: e.target.value ? new Date(e.target.value) : undefined
                                            }))}
                                            className="w-full px-3 py-2 rounded-lg bg-background border border-border text-sm"
                                        />
                                    </div>
                                </div>

                                {/* Tags */}
                                {allTags.length > 0 && (
                                    <div>
                                        <label className="text-xs font-medium text-muted-foreground mb-2 block flex items-center gap-1.5">
                                            <Tag className="w-3.5 h-3.5" />
                                            {t.tags[language]}
                                        </label>
                                        <div className="flex flex-wrap gap-1.5">
                                            {allTags.map(tag => (
                                                <button
                                                    key={tag}
                                                    onClick={() => toggleArrayFilter('tags', tag)}
                                                    className={cn(
                                                        "px-2.5 py-1 rounded-full text-xs font-medium transition-colors",
                                                        filters.tags.includes(tag)
                                                            ? "bg-primary-500 text-white"
                                                            : "bg-muted text-muted-foreground hover:bg-muted/80"
                                                    )}
                                                >
                                                    {tag}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Colors */}
                                <div>
                                    <label className="text-xs font-medium text-muted-foreground mb-2 block flex items-center gap-1.5">
                                        <Palette className="w-3.5 h-3.5" />
                                        {t.colors[language]}
                                    </label>
                                    <div className="flex flex-wrap gap-1.5">
                                        {NOTE_COLORS.map(color => (
                                            <button
                                                key={color.id}
                                                onClick={() => toggleArrayFilter('colors', color.id)}
                                                className={cn(
                                                    "w-7 h-7 rounded-full transition-all",
                                                    color.preview,
                                                    filters.colors.includes(color.id)
                                                        ? "ring-2 ring-offset-2 ring-primary-500"
                                                        : "opacity-60 hover:opacity-100"
                                                )}
                                                title={color.name}
                                            />
                                        ))}
                                    </div>
                                </div>

                                {/* Pinned Only */}
                                <label className="flex items-center gap-2 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={filters.pinnedOnly}
                                        onChange={(e) => setFilters(prev => ({ ...prev, pinnedOnly: e.target.checked }))}
                                        className="w-4 h-4 rounded border-border text-primary-500 focus:ring-primary-500"
                                    />
                                    <span className="text-sm">{t.pinnedOnly[language]}</span>
                                </label>

                                {/* Actions */}
                                <div className="flex items-center gap-2 pt-2 border-t border-border">
                                    <button
                                        onClick={clearFilters}
                                        className="px-3 py-1.5 rounded-lg text-xs font-medium bg-muted hover:bg-muted/80 transition-colors"
                                    >
                                        {t.clearFilters[language]}
                                    </button>
                                    <button
                                        onClick={() => setShowSaveDialog(true)}
                                        className="px-3 py-1.5 rounded-lg text-xs font-medium bg-primary-500/10 text-primary-600 dark:text-primary-400 hover:bg-primary-500/20 transition-colors flex items-center gap-1.5"
                                    >
                                        <Save className="w-3.5 h-3.5" />
                                        {t.saveSearch[language]}
                                    </button>
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Results */}
                <div className="max-h-96 overflow-y-auto">
                    {/* Result count */}
                    <div className="px-4 py-2 bg-muted/30 border-b border-border">
                        <span className="text-xs text-muted-foreground">
                            {filteredNotes.length} {t.results[language]}
                        </span>
                    </div>

                    {filteredNotes.length > 0 ? (
                        <div className="divide-y divide-border">
                            {filteredNotes.slice(0, 20).map(note => (
                                <motion.button
                                    key={note.id}
                                    whileHover={{ backgroundColor: 'var(--color-muted)' }}
                                    onClick={() => {
                                        onSelectNote(note);
                                        onClose();
                                    }}
                                    className="w-full p-4 text-left transition-colors"
                                >
                                    <div className="flex items-start gap-3">
                                        <FileText className="w-4 h-4 text-muted-foreground mt-0.5 flex-shrink-0" />
                                        <div className="flex-1 min-w-0">
                                            <h4 className="font-medium text-sm truncate">
                                                {highlightMatch(note.title, filters.query, filters.isRegex)}
                                            </h4>
                                            <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
                                                {highlightMatch(note.content.slice(0, 150), filters.query, filters.isRegex)}
                                            </p>
                                            <div className="flex items-center gap-2 mt-2">
                                                <Clock className="w-3 h-3 text-muted-foreground" />
                                                <span className="text-[10px] text-muted-foreground">
                                                    {formatDate(note.updatedAt)}
                                                </span>
                                                {note.tags && note.tags.length > 0 && (
                                                    <>
                                                        <Tag className="w-3 h-3 text-muted-foreground ml-2" />
                                                        <span className="text-[10px] text-muted-foreground">
                                                            {note.tags.join(', ')}
                                                        </span>
                                                    </>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                </motion.button>
                            ))}
                        </div>
                    ) : (
                        <div className="p-8 text-center">
                            <Search className="w-10 h-10 mx-auto mb-3 text-muted-foreground/30" />
                            <p className="text-sm text-muted-foreground">{t.noResults[language]}</p>
                        </div>
                    )}
                </div>

                {/* Saved Searches */}
                {savedSearches.length > 0 && (
                    <div className="border-t border-border p-3 bg-muted/30">
                        <h5 className="text-xs font-medium text-muted-foreground mb-2 flex items-center gap-1.5">
                            <Bookmark className="w-3.5 h-3.5" />
                            {t.savedSearches[language]}
                        </h5>
                        <div className="flex flex-wrap gap-1.5">
                            {savedSearches.map(search => (
                                <div
                                    key={search.id}
                                    className="flex items-center gap-1 px-2.5 py-1 rounded-full bg-background border border-border text-xs"
                                >
                                    <button
                                        onClick={() => loadSavedSearch(search)}
                                        className="hover:text-primary-500 transition-colors"
                                    >
                                        {search.name}
                                    </button>
                                    <button
                                        onClick={() => deleteSavedSearch(search.id)}
                                        className="p-0.5 hover:text-destructive transition-colors"
                                    >
                                        <X className="w-3 h-3" />
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Save Search Dialog */}
                <AnimatePresence>
                    {showSaveDialog && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="absolute inset-0 bg-black/50 flex items-center justify-center p-4"
                            onClick={() => setShowSaveDialog(false)}
                        >
                            <motion.div
                                initial={{ scale: 0.95 }}
                                animate={{ scale: 1 }}
                                exit={{ scale: 0.95 }}
                                className="bg-card rounded-xl p-4 w-full max-w-xs"
                                onClick={(e) => e.stopPropagation()}
                            >
                                <h4 className="font-semibold mb-3">{t.saveSearch[language]}</h4>
                                <input
                                    type="text"
                                    value={saveSearchName}
                                    onChange={(e) => setSaveSearchName(e.target.value)}
                                    placeholder="Arama adı..."
                                    className="w-full px-3 py-2 rounded-lg bg-muted border border-border text-sm mb-3"
                                    autoFocus
                                />
                                <div className="flex gap-2">
                                    <button
                                        onClick={() => setShowSaveDialog(false)}
                                        className="flex-1 px-3 py-2 rounded-lg bg-muted text-sm"
                                    >
                                        İptal
                                    </button>
                                    <button
                                        onClick={handleSaveSearch}
                                        className="flex-1 px-3 py-2 rounded-lg bg-primary-500 text-white text-sm"
                                    >
                                        Kaydet
                                    </button>
                                </div>
                            </motion.div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </motion.div>
    );
}

export default AdvancedSearchPanel;
