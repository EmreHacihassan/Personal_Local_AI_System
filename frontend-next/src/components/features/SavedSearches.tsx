'use client';

/**
 * SavedSearches - Kayıtlı Aramalar Bileşeni
 * 
 * Kullanıcının sık kullandığı aramaları kaydetme ve hızlı erişim.
 */

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Search,
    Star,
    Plus,
    Trash2,
    Clock,
    Filter,
    X,
    ChevronDown,
    Save
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface SavedSearch {
    id: string;
    name: string;
    query: string;
    filters: {
        tags?: string[];
        colors?: string[];
        dateFrom?: Date;
        dateTo?: Date;
        folders?: string[];
    };
    createdAt: Date;
    usageCount: number;
}

interface SavedSearchesProps {
    onSelectSearch: (search: SavedSearch) => void;
    currentQuery?: string;
    currentFilters?: SavedSearch['filters'];
    onClose: () => void;
    language?: 'tr' | 'en' | 'de';
}

const translations = {
    title: { tr: 'Kayıtlı Aramalar', en: 'Saved Searches', de: 'Gespeicherte Suchen' },
    saveCurrentSearch: { tr: 'Aramayı Kaydet', en: 'Save Search', de: 'Suche speichern' },
    searchName: { tr: 'Arama Adı', en: 'Search Name', de: 'Suchname' },
    noSearches: { tr: 'Henüz kayıtlı arama yok', en: 'No saved searches yet', de: 'Noch keine gespeicherten Suchen' },
    recent: { tr: 'Son Kullanılan', en: 'Recently Used', de: 'Zuletzt verwendet' },
    favorites: { tr: 'Favoriler', en: 'Favorites', de: 'Favoriten' },
    deleteSearch: { tr: 'Aramayı Sil', en: 'Delete Search', de: 'Suche löschen' },
    usedTimes: { tr: 'kez kullanıldı', en: 'times used', de: 'mal verwendet' },
    save: { tr: 'Kaydet', en: 'Save', de: 'Speichern' },
    cancel: { tr: 'İptal', en: 'Cancel', de: 'Abbrechen' },
};

// LocalStorage key
const STORAGE_KEY = 'saved_searches';

const loadSavedSearches = (): SavedSearch[] => {
    if (typeof window === 'undefined') return [];
    try {
        const data = localStorage.getItem(STORAGE_KEY);
        if (data) {
            return JSON.parse(data).map((s: any) => ({
                ...s,
                createdAt: new Date(s.createdAt)
            }));
        }
    } catch (e) {
        console.error('Failed to load saved searches:', e);
    }
    return [];
};

const saveSavedSearches = (searches: SavedSearch[]) => {
    if (typeof window === 'undefined') return;
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(searches));
    } catch (e) {
        console.error('Failed to save searches:', e);
    }
};

export function SavedSearches({
    onSelectSearch,
    currentQuery = '',
    currentFilters = {},
    onClose,
    language = 'tr'
}: SavedSearchesProps) {
    const t = translations;
    const [searches, setSearches] = useState<SavedSearch[]>([]);
    const [showSaveForm, setShowSaveForm] = useState(false);
    const [newSearchName, setNewSearchName] = useState('');

    useEffect(() => {
        setSearches(loadSavedSearches());
    }, []);

    const handleSaveSearch = () => {
        if (!newSearchName.trim() || !currentQuery.trim()) return;

        const newSearch: SavedSearch = {
            id: `search-${Date.now()}`,
            name: newSearchName.trim(),
            query: currentQuery,
            filters: currentFilters,
            createdAt: new Date(),
            usageCount: 0
        };

        const updated = [newSearch, ...searches];
        setSearches(updated);
        saveSavedSearches(updated);
        setNewSearchName('');
        setShowSaveForm(false);
    };

    const handleSelectSearch = (search: SavedSearch) => {
        // Increment usage count
        const updated = searches.map(s =>
            s.id === search.id ? { ...s, usageCount: s.usageCount + 1 } : s
        );
        setSearches(updated);
        saveSavedSearches(updated);
        onSelectSearch(search);
    };

    const handleDeleteSearch = (searchId: string) => {
        const updated = searches.filter(s => s.id !== searchId);
        setSearches(updated);
        saveSavedSearches(updated);
    };

    const sortedByRecent = [...searches].sort((a, b) =>
        b.createdAt.getTime() - a.createdAt.getTime()
    );

    const sortedByUsage = [...searches].sort((a, b) =>
        b.usageCount - a.usageCount
    );

    return (
        <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="absolute top-full left-0 right-0 mt-2 z-50 bg-card rounded-xl border border-border shadow-2xl overflow-hidden max-h-96"
        >
            {/* Header */}
            <div className="p-3 border-b border-border bg-gradient-to-r from-amber-500/5 to-orange-500/5 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Star className="w-4 h-4 text-amber-500" />
                    <h4 className="font-medium text-sm">{t.title[language]}</h4>
                </div>
                <button onClick={onClose} className="p-1 rounded hover:bg-muted transition-colors">
                    <X className="w-4 h-4 text-muted-foreground" />
                </button>
            </div>

            <div className="max-h-72 overflow-y-auto">
                {/* Save Current Search */}
                {currentQuery && (
                    <div className="p-3 border-b border-border">
                        {showSaveForm ? (
                            <div className="space-y-2">
                                <input
                                    type="text"
                                    value={newSearchName}
                                    onChange={(e) => setNewSearchName(e.target.value)}
                                    placeholder={t.searchName[language]}
                                    className="w-full px-3 py-2 rounded-lg bg-muted border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/50"
                                    autoFocus
                                />
                                <div className="flex gap-2">
                                    <button
                                        onClick={handleSaveSearch}
                                        disabled={!newSearchName.trim()}
                                        className="flex-1 px-3 py-1.5 rounded-lg bg-primary-500 text-white text-sm font-medium hover:bg-primary-600 disabled:opacity-50 transition-colors"
                                    >
                                        {t.save[language]}
                                    </button>
                                    <button
                                        onClick={() => setShowSaveForm(false)}
                                        className="px-3 py-1.5 rounded-lg bg-muted text-muted-foreground text-sm hover:bg-muted/80 transition-colors"
                                    >
                                        {t.cancel[language]}
                                    </button>
                                </div>
                            </div>
                        ) : (
                            <button
                                onClick={() => setShowSaveForm(true)}
                                className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-amber-500/10 text-amber-600 dark:text-amber-400 hover:bg-amber-500/20 transition-colors text-sm font-medium"
                            >
                                <Save className="w-4 h-4" />
                                {t.saveCurrentSearch[language]}
                            </button>
                        )}
                    </div>
                )}

                {/* Search List */}
                {searches.length === 0 ? (
                    <div className="p-6 text-center text-muted-foreground text-sm">
                        <Search className="w-8 h-8 mx-auto mb-2 opacity-50" />
                        {t.noSearches[language]}
                    </div>
                ) : (
                    <div className="p-2 space-y-1">
                        {sortedByRecent.map(search => (
                            <motion.div
                                key={search.id}
                                whileHover={{ scale: 1.01 }}
                                className="group flex items-center gap-3 p-2.5 rounded-lg hover:bg-muted/50 cursor-pointer transition-colors"
                            >
                                <button
                                    onClick={() => handleSelectSearch(search)}
                                    className="flex-1 flex items-start gap-3 text-left"
                                >
                                    <div className="p-1.5 rounded-lg bg-amber-500/10">
                                        <Search className="w-3.5 h-3.5 text-amber-500" />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="font-medium text-sm truncate">{search.name}</p>
                                        <p className="text-xs text-muted-foreground truncate">
                                            &ldquo;{search.query}&rdquo;
                                        </p>
                                        <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                                            <Clock className="w-3 h-3" />
                                            <span>{search.usageCount} {t.usedTimes[language]}</span>
                                        </div>
                                    </div>
                                </button>
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        handleDeleteSearch(search.id);
                                    }}
                                    className="p-1.5 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-red-500/10 text-muted-foreground hover:text-red-500 transition-all"
                                    title={t.deleteSearch[language]}
                                >
                                    <Trash2 className="w-3.5 h-3.5" />
                                </button>
                            </motion.div>
                        ))}
                    </div>
                )}
            </div>
        </motion.div>
    );
}

export default SavedSearches;
