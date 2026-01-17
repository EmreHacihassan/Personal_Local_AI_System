'use client';

import { motion } from 'framer-motion';
import { Search, Calendar, Tag, FolderOpen, Star, Pin, Filter, X, MessageSquare } from 'lucide-react';
import { useStore, Message, Session } from '@/store/useStore';
import { cn } from '@/lib/utils';
import { useState, useMemo } from 'react';

// Function to highlight search query in text
const highlightText = (text: string, query: string): JSX.Element => {
  if (!query || query.length < 2) {
    return <>{text}</>;
  }
  
  const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
  const parts = text.split(regex);
  
  return (
    <>
      {parts.map((part, i) => 
        regex.test(part) ? (
          <mark key={i} className="bg-yellow-200 dark:bg-yellow-900/50 text-yellow-900 dark:text-yellow-100 px-0.5 rounded">
            {part}
          </mark>
        ) : (
          <span key={i}>{part}</span>
        )
      )}
    </>
  );
};

const CATEGORIES = [
  { id: 'all', tr: 'Tümü', en: 'All', de: 'Alle', icon: '📋' },
  { id: 'work', tr: 'İş', en: 'Work', de: 'Arbeit', icon: '💼' },
  { id: 'coding', tr: 'Kodlama', en: 'Coding', de: 'Programmierung', icon: '💻' },
  { id: 'research', tr: 'Araştırma', en: 'Research', de: 'Forschung', icon: '🔬' },
  { id: 'learning', tr: 'Öğrenme', en: 'Learning', de: 'Lernen', icon: '📚' },
  { id: 'creative', tr: 'Yaratıcı', en: 'Creative', de: 'Kreativ', icon: '🎨' },
];

interface SearchFilters {
  query: string;
  dateFrom: string;
  dateTo: string;
  category: string;
  tags: string[];
  onlyFavorites: boolean;
  onlyPinned: boolean;
  searchIn: 'all' | 'messages' | 'sessions';
}

export function SearchPage() {
  const { language, messages, sessions, setCurrentPage, setCurrentSession } = useStore();
  const [filters, setFilters] = useState<SearchFilters>({
    query: '',
    dateFrom: '',
    dateTo: '',
    category: 'all',
    tags: [],
    onlyFavorites: false,
    onlyPinned: false,
    searchIn: 'all',
  });
  const [tagInput, setTagInput] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  // Search results
  const searchResults = useMemo(() => {
    const results: { type: 'message' | 'session'; data: Message | Session; sessionTitle?: string }[] = [];
    
    if (filters.query.length < 2 && !filters.onlyFavorites && !filters.onlyPinned && filters.category === 'all') {
      return results;
    }

    const query = filters.query.toLowerCase();
    const dateFrom = filters.dateFrom ? new Date(filters.dateFrom) : null;
    const dateTo = filters.dateTo ? new Date(filters.dateTo + 'T23:59:59') : null;

    // Search in messages
    if (filters.searchIn === 'all' || filters.searchIn === 'messages') {
      messages.forEach((msg) => {
        let match = true;

        // Query match
        if (query && !msg.content.toLowerCase().includes(query)) {
          match = false;
        }

        // Date filter
        const msgDate = new Date(msg.timestamp);
        if (dateFrom && msgDate < dateFrom) match = false;
        if (dateTo && msgDate > dateTo) match = false;

        // Favorites filter
        if (filters.onlyFavorites && !msg.isFavorite) match = false;

        if (match) {
          results.push({ type: 'message', data: msg });
        }
      });
    }

    // Search in sessions
    if (filters.searchIn === 'all' || filters.searchIn === 'sessions') {
      sessions.forEach((session) => {
        let match = true;

        // Query match in title or messages
        if (query) {
          const titleMatch = session.title.toLowerCase().includes(query);
          const msgMatch = session.messages.some(m => m.content.toLowerCase().includes(query));
          if (!titleMatch && !msgMatch) match = false;
        }

        // Date filter
        const sessionDate = new Date(session.createdAt);
        if (dateFrom && sessionDate < dateFrom) match = false;
        if (dateTo && sessionDate > dateTo) match = false;

        // Category filter
        if (filters.category !== 'all' && session.category !== filters.category) match = false;

        // Tags filter
        if (filters.tags.length > 0) {
          const hasTags = filters.tags.some(tag => session.tags?.includes(tag));
          if (!hasTags) match = false;
        }

        // Pinned filter
        if (filters.onlyPinned && !session.isPinned) match = false;

        if (match) {
          results.push({ type: 'session', data: session });
        }
      });
    }

    return results.slice(0, 50); // Limit to 50 results
  }, [filters, messages, sessions]);

  const addTag = () => {
    if (tagInput.trim() && !filters.tags.includes(tagInput.trim())) {
      setFilters({ ...filters, tags: [...filters.tags, tagInput.trim()] });
      setTagInput('');
    }
  };

  const removeTag = (tag: string) => {
    setFilters({ ...filters, tags: filters.tags.filter(t => t !== tag) });
  };

  const clearFilters = () => {
    setFilters({
      query: '',
      dateFrom: '',
      dateTo: '',
      category: 'all',
      tags: [],
      onlyFavorites: false,
      onlyPinned: false,
      searchIn: 'all',
    });
  };

  const openSession = (sessionId: string) => {
    setCurrentSession(sessionId);
    setCurrentPage('chat');
  };

  const t = {
    title: { tr: 'Gelişmiş Arama', en: 'Advanced Search', de: 'Erweiterte Suche' },
    subtitle: { tr: 'Mesajlarınızı ve sohbetlerinizi arayın', en: 'Search your messages and chats', de: 'Durchsuchen Sie Nachrichten und Chats' },
    searchPlaceholder: { tr: 'Arama yapın...', en: 'Search...', de: 'Suchen...' },
    filters: { tr: 'Filtreler', en: 'Filters', de: 'Filter' },
    showFilters: { tr: 'Filtreleri Göster', en: 'Show Filters', de: 'Filter anzeigen' },
    hideFilters: { tr: 'Filtreleri Gizle', en: 'Hide Filters', de: 'Filter ausblenden' },
    clearFilters: { tr: 'Filtreleri Temizle', en: 'Clear Filters', de: 'Filter löschen' },
    dateFrom: { tr: 'Başlangıç Tarihi', en: 'From Date', de: 'Von Datum' },
    dateTo: { tr: 'Bitiş Tarihi', en: 'To Date', de: 'Bis Datum' },
    category: { tr: 'Kategori', en: 'Category', de: 'Kategorie' },
    tags: { tr: 'Etiketler', en: 'Tags', de: 'Tags' },
    addTag: { tr: 'Etiket ekle...', en: 'Add tag...', de: 'Tag hinzufügen...' },
    onlyFavorites: { tr: 'Sadece Favoriler', en: 'Only Favorites', de: 'Nur Favoriten' },
    onlyPinned: { tr: 'Sadece Sabitler', en: 'Only Pinned', de: 'Nur Angeheftete' },
    searchIn: { tr: 'Ara', en: 'Search In', de: 'Suchen in' },
    all: { tr: 'Tümü', en: 'All', de: 'Alle' },
    messages: { tr: 'Mesajlar', en: 'Messages', de: 'Nachrichten' },
    sessions: { tr: 'Sohbetler', en: 'Chats', de: 'Chats' },
    results: { tr: 'sonuç bulundu', en: 'results found', de: 'Ergebnisse gefunden' },
    noResults: { tr: 'Sonuç bulunamadı', en: 'No results found', de: 'Keine Ergebnisse' },
    startSearch: { tr: 'Arama yapmak için en az 2 karakter girin veya filtre seçin', en: 'Enter at least 2 characters or select filters to search', de: 'Geben Sie mindestens 2 Zeichen ein oder wählen Sie Filter' },
    message: { tr: 'Mesaj', en: 'Message', de: 'Nachricht' },
    session: { tr: 'Sohbet', en: 'Chat', de: 'Chat' },
    openChat: { tr: 'Sohbeti Aç', en: 'Open Chat', de: 'Chat öffnen' },
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-border bg-card/50 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 text-white">
            <Search className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-semibold">{t.title[language]}</h1>
            <p className="text-xs text-muted-foreground">{t.subtitle[language]}</p>
          </div>
        </div>
        {searchResults.length > 0 && (
          <span className="text-sm text-muted-foreground">
            {searchResults.length} {t.results[language]}
          </span>
        )}
      </header>

      {/* Search Bar */}
      <div className="px-6 py-4 border-b border-border bg-muted/30">
        <div className="flex gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-muted-foreground" />
            <input
              type="text"
              placeholder={t.searchPlaceholder[language]}
              value={filters.query}
              onChange={(e) => setFilters({ ...filters, query: e.target.value })}
              className="w-full pl-12 pr-4 py-3 bg-background border border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 text-lg"
            />
          </div>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={cn(
              "flex items-center gap-2 px-4 py-3 rounded-xl transition-all",
              showFilters 
                ? "bg-primary-500 text-white" 
                : "bg-background border border-border hover:bg-accent"
            )}
          >
            <Filter className="w-5 h-5" />
            {showFilters ? t.hideFilters[language] : t.showFilters[language]}
          </button>
        </div>

        {/* Filters Panel */}
        {showFilters && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-4 p-4 bg-background border border-border rounded-xl"
          >
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Date Range */}
              <div>
                <label className="text-sm font-medium mb-2 block flex items-center gap-2">
                  <Calendar className="w-4 h-4" />
                  {t.dateFrom[language]}
                </label>
                <input
                  type="date"
                  value={filters.dateFrom}
                  onChange={(e) => setFilters({ ...filters, dateFrom: e.target.value })}
                  className="w-full px-3 py-2 bg-muted border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block flex items-center gap-2">
                  <Calendar className="w-4 h-4" />
                  {t.dateTo[language]}
                </label>
                <input
                  type="date"
                  value={filters.dateTo}
                  onChange={(e) => setFilters({ ...filters, dateTo: e.target.value })}
                  className="w-full px-3 py-2 bg-muted border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>

              {/* Category */}
              <div>
                <label className="text-sm font-medium mb-2 block flex items-center gap-2">
                  <FolderOpen className="w-4 h-4" />
                  {t.category[language]}
                </label>
                <select
                  value={filters.category}
                  onChange={(e) => setFilters({ ...filters, category: e.target.value })}
                  className="w-full px-3 py-2 bg-muted border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  {CATEGORIES.map((cat) => (
                    <option key={cat.id} value={cat.id}>
                      {cat.icon} {cat[language as 'tr' | 'en' | 'de']}
                    </option>
                  ))}
                </select>
              </div>

              {/* Search In */}
              <div>
                <label className="text-sm font-medium mb-2 block flex items-center gap-2">
                  <MessageSquare className="w-4 h-4" />
                  {t.searchIn[language]}
                </label>
                <select
                  value={filters.searchIn}
                  onChange={(e) => setFilters({ ...filters, searchIn: e.target.value as 'all' | 'messages' | 'sessions' })}
                  className="w-full px-3 py-2 bg-muted border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="all">{t.all[language]}</option>
                  <option value="messages">{t.messages[language]}</option>
                  <option value="sessions">{t.sessions[language]}</option>
                </select>
              </div>
            </div>

            {/* Tags */}
            <div className="mt-4">
              <label className="text-sm font-medium mb-2 block flex items-center gap-2">
                <Tag className="w-4 h-4" />
                {t.tags[language]}
              </label>
              <div className="flex flex-wrap gap-2 mb-2">
                {filters.tags.map((tag) => (
                  <span
                    key={tag}
                    className="flex items-center gap-1 px-3 py-1 bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 rounded-full text-sm"
                  >
                    {tag}
                    <button onClick={() => removeTag(tag)} className="hover:text-primary-800">
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
              </div>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && addTag()}
                  placeholder={t.addTag[language]}
                  className="flex-1 px-3 py-2 bg-muted border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
                <button
                  onClick={addTag}
                  className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600"
                >
                  +
                </button>
              </div>
            </div>

            {/* Toggles */}
            <div className="mt-4 flex flex-wrap gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filters.onlyFavorites}
                  onChange={(e) => setFilters({ ...filters, onlyFavorites: e.target.checked })}
                  className="w-4 h-4 rounded border-border text-primary-500 focus:ring-primary-500"
                />
                <Star className="w-4 h-4 text-yellow-500" />
                <span className="text-sm">{t.onlyFavorites[language]}</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filters.onlyPinned}
                  onChange={(e) => setFilters({ ...filters, onlyPinned: e.target.checked })}
                  className="w-4 h-4 rounded border-border text-primary-500 focus:ring-primary-500"
                />
                <Pin className="w-4 h-4 text-primary-500" />
                <span className="text-sm">{t.onlyPinned[language]}</span>
              </label>
              <button
                onClick={clearFilters}
                className="ml-auto text-sm text-muted-foreground hover:text-foreground"
              >
                {t.clearFilters[language]}
              </button>
            </div>
          </motion.div>
        )}
      </div>

      {/* Results */}
      <div className="flex-1 overflow-y-auto p-6">
        {searchResults.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <Search className="w-16 h-16 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">
              {filters.query.length >= 2 || filters.onlyFavorites || filters.onlyPinned || filters.category !== 'all'
                ? t.noResults[language]
                : t.startSearch[language]
              }
            </p>
          </div>
        ) : (
          <div className="max-w-3xl mx-auto space-y-4">
            {searchResults.map((result, index) => (
              <motion.div
                key={`${result.type}-${(result.data as Message | Session).id}`}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.03 }}
                className="bg-card border border-border rounded-2xl p-4 hover:shadow-md transition-shadow"
              >
                {result.type === 'message' ? (
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 px-2 py-1 rounded-full">
                        {t.message[language]}
                      </span>
                      {(result.data as Message).isFavorite && (
                        <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
                      )}
                      <span className="text-xs text-muted-foreground ml-auto">
                        {new Date((result.data as Message).timestamp).toLocaleDateString()}
                      </span>
                    </div>
                    <p className="text-sm">
                      {highlightText(
                        (result.data as Message).content.length > 200
                          ? (result.data as Message).content.slice(0, 200) + '...'
                          : (result.data as Message).content,
                        filters.query
                      )}
                    </p>
                  </div>
                ) : (
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xs bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 px-2 py-1 rounded-full">
                        {t.session[language]}
                      </span>
                      {(result.data as Session).isPinned && (
                        <Pin className="w-4 h-4 text-primary-500" />
                      )}
                      {(result.data as Session).category && (
                        <span className="text-xs bg-muted px-2 py-1 rounded-full">
                          {(result.data as Session).category}
                        </span>
                      )}
                      <span className="text-xs text-muted-foreground ml-auto">
                        {new Date((result.data as Session).createdAt).toLocaleDateString()}
                      </span>
                    </div>
                    <h4 className="font-medium mb-2">{highlightText((result.data as Session).title, filters.query)}</h4>
                    <p className="text-sm text-muted-foreground mb-3">
                      {(result.data as Session).messages.length} {t.messages[language]}
                    </p>
                    {(result.data as Session).tags && (result.data as Session).tags!.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-3">
                        {(result.data as Session).tags!.map((tag) => (
                          <span key={tag} className="text-xs bg-muted px-2 py-1 rounded-full">
                            #{tag}
                          </span>
                        ))}
                      </div>
                    )}
                    <button
                      onClick={() => openSession((result.data as Session).id)}
                      className="text-sm text-primary-500 hover:text-primary-600"
                    >
                      {t.openChat[language]} →
                    </button>
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
