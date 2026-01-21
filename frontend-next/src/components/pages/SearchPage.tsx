'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { 
  Search, Calendar, Tag, FolderOpen, Star, Pin, Filter, X, 
  MessageSquare, Loader2, RefreshCw, FileText, ChevronDown, 
  ChevronUp, User, Bot, ExternalLink, Hash, Clock
} from 'lucide-react';
import { useStore, Message } from '@/store/useStore';
import { cn } from '@/lib/utils';
import { useState, useMemo, useEffect, useCallback } from 'react';
import { 
  getSessions, getSession, advancedSessionSearch, getAllTags, 
  getAllCategories, searchDocuments,
  SearchResult, MatchedMessage, DocumentSearchResult
} from '@/lib/api';

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
          <mark key={i} className="bg-yellow-200 dark:bg-yellow-900/50 text-yellow-900 dark:text-yellow-100 px-0.5 rounded font-medium">
            {part}
          </mark>
        ) : (
          <span key={i}>{part}</span>
        )
      )}
    </>
  );
};

// Default categories (will be merged with backend categories)
const DEFAULT_CATEGORIES = [
  { id: 'all', tr: 'Tümü', en: 'All', de: 'Alle', icon: '📋' },
  { id: 'work', tr: 'İş', en: 'Work', de: 'Arbeit', icon: '💼' },
  { id: 'coding', tr: 'Kodlama', en: 'Coding', de: 'Programmierung', icon: '💻' },
  { id: 'research', tr: 'Araştırma', en: 'Research', de: 'Forschung', icon: '🔬' },
  { id: 'learning', tr: 'Öğrenme', en: 'Learning', de: 'Lernen', icon: '📚' },
  { id: 'creative', tr: 'Yaratıcı', en: 'Creative', de: 'Kreativ', icon: '🎨' },
];

type SearchTab = 'conversations' | 'documents';

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
  const { language, setCurrentPage, setCurrentSession, loadSessionMessages } = useStore();
  
  // Tab state
  const [activeTab, setActiveTab] = useState<SearchTab>('conversations');
  
  // Conversation search states
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
  
  // Document search states
  const [docQuery, setDocQuery] = useState('');
  const [docTopK, setDocTopK] = useState(5);
  const [docResults, setDocResults] = useState<DocumentSearchResult[]>([]);
  const [isSearchingDocs, setIsSearchingDocs] = useState(false);
  const [expandedDocIndex, setExpandedDocIndex] = useState<number | null>(null);
  
  // Backend data states
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [availableTags, setAvailableTags] = useState<string[]>([]);
  const [availableCategories, setAvailableCategories] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [totalSessions, setTotalSessions] = useState(0);
  const [hasSearched, setHasSearched] = useState(false);

  // Load tags and categories from backend
  const loadMetadata = useCallback(async () => {
    try {
      const [tagsRes, catsRes, sessionsRes] = await Promise.all([
        getAllTags(),
        getAllCategories(),
        getSessions(1) // Just to get total count
      ]);
      
      if (tagsRes.success && tagsRes.data) {
        setAvailableTags(tagsRes.data.tags);
      }
      if (catsRes.success && catsRes.data) {
        setAvailableCategories(catsRes.data.categories);
      }
      if (sessionsRes.success && sessionsRes.data) {
        setTotalSessions(sessionsRes.data.total || sessionsRes.data.sessions.length);
      }
    } catch (err) {
      console.error('Failed to load metadata:', err);
    }
  }, []);

  // Initial load
  useEffect(() => {
    loadMetadata();
  }, [loadMetadata]);

  // Perform conversation search
  const performSearch = useCallback(async () => {
    // Check if we have any search criteria
    const hasQuery = filters.query.length >= 2;
    const hasFilters = filters.onlyFavorites || filters.onlyPinned || 
                       filters.category !== 'all' || filters.tags.length > 0 ||
                       filters.dateFrom || filters.dateTo;
    
    if (!hasQuery && !hasFilters) {
      setSearchResults([]);
      setHasSearched(false);
      return;
    }
    
    setIsSearching(true);
    setError(null);
    setHasSearched(true);
    
    try {
      const response = await advancedSessionSearch({
        query: filters.query || undefined,
        date_from: filters.dateFrom || undefined,
        date_to: filters.dateTo || undefined,
        tags: filters.tags.length > 0 ? filters.tags : undefined,
        category: filters.category !== 'all' ? filters.category : undefined,
        pinned_only: filters.onlyPinned,
        favorites_only: filters.onlyFavorites,
        limit: 100,
      });
      
      if (response.success && response.data) {
        setSearchResults(response.data.results);
      } else {
        setError(response.error || 'Arama başarısız');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Arama hatası');
    } finally {
      setIsSearching(false);
    }
  }, [filters]);

  // Auto-search when filters change (with debounce for query)
  useEffect(() => {
    const hasQuery = filters.query.length >= 2;
    const hasFilters = filters.onlyFavorites || filters.onlyPinned || 
                       filters.category !== 'all' || filters.tags.length > 0 ||
                       filters.dateFrom || filters.dateTo;
    
    if (hasQuery || hasFilters) {
      const timer = setTimeout(() => {
        performSearch();
      }, hasQuery ? 300 : 0); // Debounce for query, instant for filters
      
      return () => clearTimeout(timer);
    } else {
      setSearchResults([]);
      setHasSearched(false);
    }
  }, [filters, performSearch]);

  // Perform document search
  const performDocSearch = async () => {
    if (!docQuery.trim()) return;
    
    setIsSearchingDocs(true);
    setError(null);
    
    try {
      const response = await searchDocuments(docQuery, docTopK);
      
      if (response.success && response.data) {
        setDocResults(response.data.results);
      } else {
        setError(response.error || 'Döküman araması başarısız');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Döküman arama hatası');
    } finally {
      setIsSearchingDocs(false);
    }
  };

  const addTag = () => {
    if (tagInput.trim() && !filters.tags.includes(tagInput.trim())) {
      setFilters({ ...filters, tags: [...filters.tags, tagInput.trim()] });
      setTagInput('');
    }
  };

  const removeTag = (tag: string) => {
    setFilters({ ...filters, tags: filters.tags.filter(t => t !== tag) });
  };

  const selectExistingTag = (tag: string) => {
    if (!filters.tags.includes(tag)) {
      setFilters({ ...filters, tags: [...filters.tags, tag] });
    }
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
    setSearchResults([]);
    setHasSearched(false);
  };

  const openSession = async (sessionId: string) => {
    try {
      const response = await getSession(sessionId);
      if (response.success && response.data) {
        const messages: Message[] = response.data.messages.map((m: any) => ({
          id: m.id || crypto.randomUUID(),
          role: m.role,
          content: m.content,
          timestamp: m.timestamp,
          isFavorite: m.is_favorite || false,
        }));
        loadSessionMessages(sessionId, messages);
        setCurrentSession(sessionId);
        setCurrentPage('chat');
      }
    } catch (err) {
      console.error('Failed to open session:', err);
    }
  };

  // Merge default and backend categories
  const allCategories = useMemo(() => {
    const merged = [...DEFAULT_CATEGORIES];
    availableCategories.forEach(cat => {
      if (!merged.find(c => c.id === cat)) {
        merged.push({ id: cat, tr: cat, en: cat, de: cat, icon: '📁' });
      }
    });
    return merged;
  }, [availableCategories]);

  // Translations
  const t = {
    title: { tr: 'Gelişmiş Arama', en: 'Advanced Search', de: 'Erweiterte Suche' },
    subtitle: { tr: 'Konuşmalar, mesajlar ve dökümanlarda kapsamlı arama', en: 'Comprehensive search in conversations, messages and documents', de: 'Umfassende Suche in Gesprächen, Nachrichten und Dokumenten' },
    tabConversations: { tr: '💬 Konuşmalarda Ara', en: '💬 Search Conversations', de: '💬 Gespräche durchsuchen' },
    tabDocuments: { tr: '📁 Dökümanlarda Ara', en: '📁 Search Documents', de: '📁 Dokumente durchsuchen' },
    conversationSearch: { tr: 'Konuşma ve Mesaj Araması', en: 'Conversation and Message Search', de: 'Gespräch und Nachricht Suche' },
    documentSearch: { tr: 'Bilgi Tabanında Arama', en: 'Knowledge Base Search', de: 'Wissensdatenbank Suche' },
    documentSearchDesc: { tr: 'Yüklenen dökümanlarda semantik arama yapın', en: 'Perform semantic search in uploaded documents', de: 'Semantische Suche in hochgeladenen Dokumenten' },
    searchPlaceholder: { tr: 'Aramak istediğiniz kelime veya cümle...', en: 'Word or phrase to search...', de: 'Wort oder Phrase zum Suchen...' },
    docSearchPlaceholder: { tr: 'Ne aramak istiyorsunuz?', en: 'What are you looking for?', de: 'Was suchen Sie?' },
    filters: { tr: 'Filtreler', en: 'Filters', de: 'Filter' },
    advancedFilters: { tr: '🎛️ Gelişmiş Filtreler', en: '🎛️ Advanced Filters', de: '🎛️ Erweiterte Filter' },
    showFilters: { tr: 'Filtreleri Göster', en: 'Show Filters', de: 'Filter anzeigen' },
    hideFilters: { tr: 'Filtreleri Gizle', en: 'Hide Filters', de: 'Filter ausblenden' },
    clearFilters: { tr: 'Filtreleri Temizle', en: 'Clear Filters', de: 'Filter löschen' },
    dateRange: { tr: '📅 Tarih Aralığı', en: '📅 Date Range', de: '📅 Datumsbereich' },
    dateFrom: { tr: 'Başlangıç', en: 'From', de: 'Von' },
    dateTo: { tr: 'Bitiş', en: 'To', de: 'Bis' },
    category: { tr: '📂 Kategori', en: '📂 Category', de: '📂 Kategorie' },
    tags: { tr: '🏷️ Etiketler', en: '🏷️ Tags', de: '🏷️ Tags' },
    addTag: { tr: 'Etiket ekle...', en: 'Add tag...', de: 'Tag hinzufügen...' },
    existingTags: { tr: 'Mevcut etiketler:', en: 'Existing tags:', de: 'Vorhandene Tags:' },
    onlyFavorites: { tr: '⭐ Sadece Favoriler', en: '⭐ Only Favorites', de: '⭐ Nur Favoriten' },
    onlyPinned: { tr: '📌 Sadece Sabitlenmiş', en: '📌 Only Pinned', de: '📌 Nur Angeheftete' },
    searchIn: { tr: 'Ara:', en: 'Search In:', de: 'Suchen in:' },
    searchBtn: { tr: '🔍 Ara', en: '🔍 Search', de: '🔍 Suchen' },
    all: { tr: 'Tümü', en: 'All', de: 'Alle' },
    messages: { tr: 'Mesajlar', en: 'Messages', de: 'Nachrichten' },
    titles: { tr: 'Başlıklar', en: 'Titles', de: 'Titel' },
    sessions: { tr: 'Sohbetler', en: 'Chats', de: 'Chats' },
    results: { tr: 'sonuç bulundu', en: 'results found', de: 'Ergebnisse gefunden' },
    noResults: { tr: '😔 Sonuç bulunamadı. Farklı arama terimleri deneyin.', en: '😔 No results found. Try different search terms.', de: '😔 Keine Ergebnisse gefunden. Versuchen Sie andere Suchbegriffe.' },
    startSearch: { tr: 'Arama yapmak için en az 2 karakter girin veya filtre seçin', en: 'Enter at least 2 characters or select filters to search', de: 'Geben Sie mindestens 2 Zeichen ein oder wählen Sie Filter' },
    matchedMessages: { tr: 'Eşleşen mesajlar:', en: 'Matched messages:', de: 'Übereinstimmende Nachrichten:' },
    goToChat: { tr: '💬 Konuşmaya Git', en: '💬 Go to Chat', de: '💬 Zum Chat' },
    loading: { tr: 'Yükleniyor...', en: 'Loading...', de: 'Laden...' },
    searching: { tr: 'Aranıyor...', en: 'Searching...', de: 'Suche läuft...' },
    refresh: { tr: 'Yenile', en: 'Refresh', de: 'Aktualisieren' },
    totalSessions: { tr: 'toplam sohbet', en: 'total chats', de: 'Chats insgesamt' },
    user: { tr: 'Kullanıcı', en: 'User', de: 'Benutzer' },
    assistant: { tr: 'Asistan', en: 'Assistant', de: 'Assistent' },
    resultCount: { tr: 'Sonuç', en: 'Results', de: 'Ergebnisse' },
    score: { tr: 'Skor', en: 'Score', de: 'Punktzahl' },
    metadata: { tr: 'Metadata', en: 'Metadata', de: 'Metadaten' },
    messagesLabel: { tr: 'mesaj', en: 'messages', de: 'Nachrichten' },
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
        <div className="flex items-center gap-4">
          <span className="text-xs text-muted-foreground">
            {totalSessions} {t.totalSessions[language]}
          </span>
          {searchResults.length > 0 && activeTab === 'conversations' && (
            <span className="text-sm font-medium text-primary-600">
              ✅ {searchResults.length} {t.results[language]}
            </span>
          )}
          <button
            onClick={loadMetadata}
            disabled={isLoading}
            className="flex items-center gap-2 px-3 py-1.5 text-sm bg-muted hover:bg-muted/80 rounded-lg transition-colors disabled:opacity-50"
          >
            <RefreshCw className={cn("w-4 h-4", isLoading && "animate-spin")} />
            {t.refresh[language]}
          </button>
        </div>
      </header>

      {/* Tabs */}
      <div className="px-6 pt-4 border-b border-border bg-muted/20">
        <div className="flex gap-1">
          <button
            onClick={() => setActiveTab('conversations')}
            className={cn(
              "px-4 py-2 text-sm font-medium rounded-t-lg transition-colors",
              activeTab === 'conversations'
                ? "bg-background text-foreground border-t border-l border-r border-border"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            {t.tabConversations[language]}
          </button>
          <button
            onClick={() => setActiveTab('documents')}
            className={cn(
              "px-4 py-2 text-sm font-medium rounded-t-lg transition-colors",
              activeTab === 'documents'
                ? "bg-background text-foreground border-t border-l border-r border-border"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            {t.tabDocuments[language]}
          </button>
        </div>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-hidden">
        <AnimatePresence mode="wait">
          {activeTab === 'conversations' ? (
            <motion.div
              key="conversations"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="h-full flex flex-col"
            >
              {/* Conversation Search Section */}
              <div className="px-6 py-4 border-b border-border bg-muted/30">
                <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
                  <MessageSquare className="w-4 h-4" />
                  {t.conversationSearch[language]}
                </h3>
                
                {/* Search Box */}
                <div className="relative">
                  <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                  <input
                    type="text"
                    placeholder={t.searchPlaceholder[language]}
                    value={filters.query}
                    onChange={(e) => setFilters({ ...filters, query: e.target.value })}
                    className="w-full pl-12 pr-4 py-3 bg-background border border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 text-lg"
                  />
                  {isSearching && (
                    <div className="absolute right-4 top-1/2 transform -translate-y-1/2">
                      <Loader2 className="w-5 h-5 animate-spin text-primary-500" />
                    </div>
                  )}
                </div>

                {/* Advanced Filters Expander */}
                <div className="mt-4">
                  <button
                    onClick={() => setShowFilters(!showFilters)}
                    className="flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {showFilters ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    {t.advancedFilters[language]}
                  </button>
                  
                  <AnimatePresence>
                    {showFilters && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="mt-4 p-4 bg-background border border-border rounded-xl overflow-hidden"
                      >
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          {/* Date Range */}
                          <div>
                            <label className="text-sm font-medium mb-2 block">{t.dateRange[language]}</label>
                            <div className="flex gap-2">
                              <input
                                type="date"
                                value={filters.dateFrom}
                                onChange={(e) => setFilters({ ...filters, dateFrom: e.target.value })}
                                className="flex-1 px-3 py-2 bg-muted border border-border rounded-lg text-sm"
                                placeholder={t.dateFrom[language]}
                              />
                              <input
                                type="date"
                                value={filters.dateTo}
                                onChange={(e) => setFilters({ ...filters, dateTo: e.target.value })}
                                className="flex-1 px-3 py-2 bg-muted border border-border rounded-lg text-sm"
                                placeholder={t.dateTo[language]}
                              />
                            </div>
                          </div>

                          {/* Tags */}
                          <div>
                            <label className="text-sm font-medium mb-2 block">{t.tags[language]}</label>
                            <div className="flex flex-wrap gap-1 mb-2">
                              {filters.tags.map((tag) => (
                                <span
                                  key={tag}
                                  className="flex items-center gap-1 px-2 py-1 bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 rounded-full text-xs"
                                >
                                  {tag}
                                  <button onClick={() => removeTag(tag)} className="hover:text-primary-800">
                                    <X className="w-3 h-3" />
                                  </button>
                                </span>
                              ))}
                            </div>
                            {availableTags.length > 0 && (
                              <div className="flex flex-wrap gap-1 mb-2">
                                <span className="text-xs text-muted-foreground">{t.existingTags[language]}</span>
                                {availableTags.filter(t => !filters.tags.includes(t)).slice(0, 5).map((tag) => (
                                  <button
                                    key={tag}
                                    onClick={() => selectExistingTag(tag)}
                                    className="px-2 py-0.5 bg-muted text-xs rounded-full hover:bg-accent transition-colors"
                                  >
                                    +{tag}
                                  </button>
                                ))}
                              </div>
                            )}
                            <div className="flex gap-1">
                              <input
                                type="text"
                                value={tagInput}
                                onChange={(e) => setTagInput(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && addTag()}
                                placeholder={t.addTag[language]}
                                className="flex-1 px-3 py-1.5 bg-muted border border-border rounded-lg text-sm"
                              />
                              <button
                                onClick={addTag}
                                className="px-3 py-1.5 bg-primary-500 text-white rounded-lg hover:bg-primary-600 text-sm"
                              >
                                +
                              </button>
                            </div>
                          </div>

                          {/* Category */}
                          <div>
                            <label className="text-sm font-medium mb-2 block">{t.category[language]}</label>
                            <select
                              value={filters.category}
                              onChange={(e) => setFilters({ ...filters, category: e.target.value })}
                              className="w-full px-3 py-2 bg-muted border border-border rounded-lg text-sm"
                            >
                              {allCategories.map((cat) => (
                                <option key={cat.id} value={cat.id}>
                                  {cat.icon} {cat[language as 'tr' | 'en' | 'de']}
                                </option>
                              ))}
                            </select>
                          </div>
                        </div>

                        {/* Toggle Filters */}
                        <div className="mt-4 flex flex-wrap gap-4">
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
                          <button
                            onClick={clearFilters}
                            className="ml-auto text-sm text-muted-foreground hover:text-foreground"
                          >
                            {t.clearFilters[language]}
                          </button>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>

                {/* Search Button */}
                <button
                  onClick={performSearch}
                  disabled={isSearching}
                  className="mt-4 w-full py-3 bg-gradient-to-r from-red-500 to-pink-500 text-white rounded-xl font-medium hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {isSearching ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      {t.searching[language]}
                    </>
                  ) : (
                    <>
                      <Search className="w-5 h-5" />
                      {t.searchBtn[language]}
                    </>
                  )}
                </button>
              </div>

              {/* Conversation Results */}
              <div className="flex-1 overflow-y-auto p-6">
                {error ? (
                  <div className="flex flex-col items-center justify-center h-full text-center">
                    <div className="text-red-500 text-4xl mb-4">⚠️</div>
                    <p className="text-red-500 mb-4">{error}</p>
                    <button
                      onClick={performSearch}
                      className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600"
                    >
                      {t.refresh[language]}
                    </button>
                  </div>
                ) : !hasSearched ? (
                  <div className="flex flex-col items-center justify-center h-full text-center">
                    <Search className="w-16 h-16 text-muted-foreground mb-4" />
                    <p className="text-muted-foreground">{t.startSearch[language]}</p>
                  </div>
                ) : searchResults.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-full text-center">
                    <Search className="w-16 h-16 text-muted-foreground mb-4" />
                    <p className="text-muted-foreground">{t.noResults[language]}</p>
                  </div>
                ) : (
                  <div className="max-w-3xl mx-auto space-y-4">
                    {searchResults.map((result, index) => (
                      <motion.div
                        key={result.session.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.03 }}
                        className="bg-card border border-border rounded-2xl p-4 hover:shadow-md transition-shadow"
                      >
                        {/* Session Header */}
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              {result.session.is_pinned && (
                                <Pin className="w-4 h-4 text-primary-500" />
                              )}
                              <h4 className="font-medium">
                                {highlightText(result.session.title, filters.query)}
                              </h4>
                            </div>
                            <div className="flex items-center gap-3 text-xs text-muted-foreground">
                              <span className="flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                {new Date(result.session.created_at).toLocaleDateString()}
                              </span>
                              <span className="flex items-center gap-1">
                                <MessageSquare className="w-3 h-3" />
                                {result.session.message_count} {t.messagesLabel[language]}
                              </span>
                              {result.session.category && (
                                <span className="px-2 py-0.5 bg-muted rounded-full">
                                  {result.session.category}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>

                        {/* Tags */}
                        {result.session.tags && result.session.tags.length > 0 && (
                          <div className="flex flex-wrap gap-1 mb-3">
                            {result.session.tags.map((tag) => (
                              <span key={tag} className="text-xs bg-muted px-2 py-0.5 rounded-full flex items-center gap-1">
                                <Hash className="w-3 h-3" />
                                {tag}
                              </span>
                            ))}
                          </div>
                        )}

                        {/* Matched Messages */}
                        {result.matched_messages.length > 0 && (
                          <div className="mb-3">
                            <p className="text-xs font-medium text-muted-foreground mb-2">
                              {t.matchedMessages[language]}
                            </p>
                            <div className="space-y-2">
                              {result.matched_messages.map((msg, msgIndex) => (
                                <div
                                  key={msgIndex}
                                  className="flex items-start gap-2 p-2 bg-muted/50 rounded-lg"
                                >
                                  <span className={cn(
                                    "flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center",
                                    msg.role === 'user'
                                      ? "bg-blue-100 dark:bg-blue-900/30 text-blue-600"
                                      : "bg-purple-100 dark:bg-purple-900/30 text-purple-600"
                                  )}>
                                    {msg.role === 'user' ? <User className="w-3 h-3" /> : <Bot className="w-3 h-3" />}
                                  </span>
                                  <div className="flex-1 min-w-0">
                                    <p className="text-sm">
                                      {highlightText(
                                        msg.content.length > 200 ? msg.content.slice(0, 200) + '...' : msg.content,
                                        filters.query
                                      )}
                                    </p>
                                  </div>
                                  {msg.is_favorite && (
                                    <Star className="w-4 h-4 text-yellow-500 fill-yellow-500 flex-shrink-0" />
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Go to Chat Button */}
                        <button
                          onClick={() => openSession(result.session.id)}
                          className="flex items-center gap-2 text-sm text-primary-500 hover:text-primary-600 font-medium"
                        >
                          {t.goToChat[language]}
                          <ExternalLink className="w-4 h-4" />
                        </button>
                      </motion.div>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="documents"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="h-full flex flex-col"
            >
              {/* Document Search Section */}
              <div className="px-6 py-4 border-b border-border bg-muted/30">
                <h3 className="text-sm font-medium mb-1 flex items-center gap-2">
                  <FileText className="w-4 h-4" />
                  {t.documentSearch[language]}
                </h3>
                <p className="text-xs text-muted-foreground mb-4">{t.documentSearchDesc[language]}</p>
                
                <div className="flex gap-4">
                  <div className="relative flex-1">
                    <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                    <input
                      type="text"
                      placeholder={t.docSearchPlaceholder[language]}
                      value={docQuery}
                      onChange={(e) => setDocQuery(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && performDocSearch()}
                      className="w-full pl-12 pr-4 py-3 bg-background border border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 text-lg"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="text-sm text-muted-foreground">{t.resultCount[language]}:</label>
                    <input
                      type="number"
                      min={1}
                      max={20}
                      value={docTopK}
                      onChange={(e) => setDocTopK(Math.min(20, Math.max(1, parseInt(e.target.value) || 5)))}
                      className="w-16 px-3 py-2 bg-muted border border-border rounded-lg text-center"
                    />
                  </div>
                </div>

                <button
                  onClick={performDocSearch}
                  disabled={isSearchingDocs || !docQuery.trim()}
                  className="mt-4 w-full py-3 bg-gradient-to-r from-red-500 to-pink-500 text-white rounded-xl font-medium hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {isSearchingDocs ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      {t.searching[language]}
                    </>
                  ) : (
                    <>
                      <Search className="w-5 h-5" />
                      {t.searchBtn[language]}
                    </>
                  )}
                </button>
              </div>

              {/* Document Results */}
              <div className="flex-1 overflow-y-auto p-6">
                {docResults.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-full text-center">
                    <FileText className="w-16 h-16 text-muted-foreground mb-4" />
                    <p className="text-muted-foreground">
                      {docQuery ? t.noResults[language] : t.startSearch[language]}
                    </p>
                  </div>
                ) : (
                  <div className="max-w-3xl mx-auto space-y-4">
                    <h3 className="text-lg font-medium mb-4">
                      📊 {docResults.length} {t.results[language]}
                    </h3>
                    
                    {docResults.map((result, index) => (
                      <motion.div
                        key={index}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.05 }}
                        className="bg-card border border-border rounded-2xl overflow-hidden"
                      >
                        <button
                          onClick={() => setExpandedDocIndex(expandedDocIndex === index ? null : index)}
                          className="w-full p-4 flex items-center justify-between text-left hover:bg-muted/50 transition-colors"
                        >
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-green-500 to-emerald-500 flex items-center justify-center text-white font-medium">
                              {index + 1}
                            </div>
                            <div>
                              <p className="font-medium">📄 {t.resultCount[language]} {index + 1}</p>
                              <p className="text-xs text-muted-foreground">
                                {t.score[language]}: {result.score.toFixed(2)}
                              </p>
                            </div>
                          </div>
                          {expandedDocIndex === index ? (
                            <ChevronUp className="w-5 h-5 text-muted-foreground" />
                          ) : (
                            <ChevronDown className="w-5 h-5 text-muted-foreground" />
                          )}
                        </button>
                        
                        <AnimatePresence>
                          {expandedDocIndex === index && (
                            <motion.div
                              initial={{ height: 0, opacity: 0 }}
                              animate={{ height: 'auto', opacity: 1 }}
                              exit={{ height: 0, opacity: 0 }}
                              className="overflow-hidden"
                            >
                              <div className="p-4 pt-0 border-t border-border">
                                <div className="prose prose-sm dark:prose-invert max-w-none">
                                  <p className="whitespace-pre-wrap">{result.document}</p>
                                </div>
                                
                                {result.metadata && Object.keys(result.metadata).length > 0 && (
                                  <div className="mt-4">
                                    <p className="text-xs font-medium text-muted-foreground mb-2">{t.metadata[language]}:</p>
                                    <pre className="p-3 bg-muted rounded-lg text-xs overflow-x-auto">
                                      {JSON.stringify(result.metadata, null, 2)}
                                    </pre>
                                  </div>
                                )}
                              </div>
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </motion.div>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
