'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  History,
  MessageSquare,
  Trash2,
  Search,
  Calendar,
  Clock,
  ChevronRight,
  Pin,
  Tag,
  Folder,
  X,
  Plus,
  Filter,
  Edit2,
  Check,
  TrendingUp
} from 'lucide-react';
import { useStore, Session, Message } from '@/store/useStore';
import { getSessions, deleteSession, getSession } from '@/lib/api';
import { formatDate, cn } from '@/lib/utils';

interface SessionResponse {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  is_pinned?: boolean;
  tags?: string[];
  category?: string;
}

// Categories for sessions
const CATEGORIES = [
  { id: 'all', name: 'Tümü', nameEn: 'All', nameDe: 'Alle', icon: Folder },
  { id: 'work', name: 'İş', nameEn: 'Work', nameDe: 'Arbeit', icon: Folder },
  { id: 'personal', name: 'Kişisel', nameEn: 'Personal', nameDe: 'Persönlich', icon: Folder },
  { id: 'research', name: 'Araştırma', nameEn: 'Research', nameDe: 'Forschung', icon: Folder },
  { id: 'learning', name: 'Öğrenme', nameEn: 'Learning', nameDe: 'Lernen', icon: Folder },
  { id: 'project', name: 'Proje', nameEn: 'Project', nameDe: 'Projekt', icon: Folder },
];

export function HistoryPage() {
  const { setCurrentPage, language, renameSession, loadSessionMessages } = useStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [sessionLoading, setSessionLoading] = useState<string | null>(null);
  const [localSessions, setLocalSessions] = useState<Session[]>([]);
  const [showFilters, setShowFilters] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [filterPinned, setFilterPinned] = useState(false);
  const [filterByTag, setFilterByTag] = useState<string | null>(null);
  const [tagInput, setTagInput] = useState('');
  const [editingTagSessionId, setEditingTagSessionId] = useState<string | null>(null);
  const [editingNameSessionId, setEditingNameSessionId] = useState<string | null>(null);
  const [editingNameValue, setEditingNameValue] = useState('');

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    setLoading(true);
    const response = await getSessions();
    if (response.success && response.data) {
      setLocalSessions(response.data.sessions.map((s: SessionResponse) => ({
        id: s.id,
        title: s.title,
        messages: [],
        createdAt: new Date(s.created_at),
        updatedAt: new Date(s.updated_at),
        isPinned: s.is_pinned || false,
        tags: s.tags || [],
        category: s.category || undefined,
      })));
    }
    setLoading(false);
  };

  const handleDelete = async (sessionId: string) => {
    const response = await deleteSession(sessionId);
    if (response.success) {
      setLocalSessions(prev => prev.filter(s => s.id !== sessionId));
    }
  };

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const handleOpenSession = async (sessionId: string) => {
    // Session'ı API'den yükle ve chat sayfasına yönlendir
    setSessionLoading(sessionId);
    try {
      const response = await getSession(sessionId);
      if (response.success && response.data) {
        // API'den gelen mesajları store formatına çevir
        const messages: Message[] = response.data.messages.map((msg, index) => ({
          id: msg.id || `msg-${index}`,
          role: msg.role,
          content: msg.content,
          timestamp: new Date(msg.timestamp),
          sources: [],
          metadata: {},
        }));
        
        // Store'a yükle
        loadSessionMessages(sessionId, messages);
        
        // Chat sayfasına yönlendir
        setCurrentPage('chat');
      } else {
        console.error('Session yüklenemedi:', response.error);
        // Hata olsa bile chat'e git (boş olarak)
        setCurrentPage('chat');
      }
    } catch (error) {
      console.error('Session yükleme hatası:', error);
      setCurrentPage('chat');
    } finally {
      setSessionLoading(null);
    }
  };

  // Toggle pin for a session
  const handleTogglePin = (sessionId: string) => {
    setLocalSessions(prev => prev.map(s =>
      s.id === sessionId ? { ...s, isPinned: !s.isPinned } : s
    ));
    // TODO: Call API to persist pin state
  };

  // Rename session
  const handleSaveRename = (sessionId: string) => {
    if (!editingNameValue.trim()) {
      setEditingNameSessionId(null);
      return;
    }
    setLocalSessions(prev => prev.map(s =>
      s.id === sessionId ? { ...s, title: editingNameValue.trim(), updatedAt: new Date() } : s
    ));
    renameSession(sessionId, editingNameValue.trim());
    setEditingNameSessionId(null);
    // TODO: Call API to persist rename
  };

  // Set category for a session
  const handleSetCategory = (sessionId: string, category: string) => {
    setLocalSessions(prev => prev.map(s =>
      s.id === sessionId ? { ...s, category: category === 'all' ? undefined : category } : s
    ));
    // TODO: Call API to persist category
  };

  // Add tag to a session
  const handleAddTag = (sessionId: string) => {
    if (!tagInput.trim()) return;
    setLocalSessions(prev => prev.map(s =>
      s.id === sessionId
        ? { ...s, tags: [...(s.tags || []), tagInput.trim()] }
        : s
    ));
    setTagInput('');
    // TODO: Call API to persist tags
  };

  // Remove tag from a session
  const handleRemoveTag = (sessionId: string, tagToRemove: string) => {
    setLocalSessions(prev => prev.map(s =>
      s.id === sessionId
        ? { ...s, tags: (s.tags || []).filter(t => t !== tagToRemove) }
        : s
    ));
    // TODO: Call API to persist tags
  };

  // Get all unique tags from sessions
  const allTags = Array.from(new Set(localSessions.flatMap(s => s.tags || [])));

  // Filter sessions
  const filteredSessions = localSessions
    .filter(session => {
      const matchesSearch = session.title.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesCategory = selectedCategory === 'all' || session.category === selectedCategory;
      const matchesPinned = !filterPinned || session.isPinned;
      const matchesTag = !filterByTag || (session.tags || []).includes(filterByTag);
      return matchesSearch && matchesCategory && matchesPinned && matchesTag;
    })
    .sort((a, b) => {
      // Pinned sessions first
      if (a.isPinned && !b.isPinned) return -1;
      if (!a.isPinned && b.isPinned) return 1;
      // Then by date
      return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime();
    });

  // Group sessions by date
  const groupedSessions = filteredSessions.reduce((groups, session) => {
    const date = new Date(session.createdAt).toLocaleDateString(
      language === 'tr' ? 'tr-TR' : language === 'de' ? 'de-DE' : 'en-US',
      {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      }
    );
    if (!groups[date]) {
      groups[date] = [];
    }
    groups[date].push(session);
    return groups;
  }, {} as Record<string, Session[]>);

  const t = {
    title: { tr: 'Sohbet Geçmişi', en: 'Chat History', de: 'Chat-Verlauf' },
    saved: { tr: 'sohbet kaydedildi', en: 'conversations saved', de: 'Gespräche gespeichert' },
    searchPlaceholder: { tr: 'Geçmişte ara...', en: 'Search history...', de: 'Verlauf durchsuchen...' },
    noConversations: { tr: 'Henüz sohbet yok', en: 'No conversations yet', de: 'Noch keine Gespräche' },
    conversationsAppear: { tr: 'Sohbetleriniz burada görünecek', en: 'Your conversations will appear here', de: 'Ihre Gespräche erscheinen hier' },
    filters: { tr: 'Filtreler', en: 'Filters', de: 'Filter' },
    pinnedOnly: { tr: 'Sadece Sabitlenmiş', en: 'Pinned Only', de: 'Nur Angeheftete' },
    filterByTag: { tr: 'Etikete Göre', en: 'Filter by Tag', de: 'Nach Tag filtern' },
    allTags: { tr: 'Tüm Etiketler', en: 'All Tags', de: 'Alle Tags' },
    addTag: { tr: 'Etiket ekle...', en: 'Add tag...', de: 'Tag hinzufügen...' },
    pin: { tr: 'Sabitle', en: 'Pin', de: 'Anheften' },
    unpin: { tr: 'Kaldır', en: 'Unpin', de: 'Lösen' },
    category: { tr: 'Kategori', en: 'Category', de: 'Kategorie' },
    tags: { tr: 'Etiketler', en: 'Tags', de: 'Tags' },
    popularTopics: { tr: 'Popüler Konular', en: 'Popular Topics', de: 'Beliebte Themen' },
    expandSession: { tr: 'Mesajları Göster', en: 'Show Messages', de: 'Nachrichten anzeigen' },
    collapseSession: { tr: 'Mesajları Gizle', en: 'Hide Messages', de: 'Nachrichten ausblenden' },
  };

  const getCategoryName = (cat: typeof CATEGORIES[0]) => {
    if (language === 'de') return cat.nameDe;
    if (language === 'en') return cat.nameEn;
    return cat.name;
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-border bg-card/50 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 text-white">
            <History className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-semibold">{t.title[language]}</h1>
            <p className="text-xs text-muted-foreground">
              {localSessions.length} {t.saved[language]}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Filters Button */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={cn(
              "flex items-center gap-2 px-3 py-2 rounded-xl transition-colors",
              showFilters ? "bg-primary-500 text-white" : "bg-muted hover:bg-accent"
            )}
          >
            <Filter className="w-4 h-4" />
            {t.filters[language]}
          </button>

          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={t.searchPlaceholder[language]}
              className="pl-10 pr-4 py-2 w-64 bg-background border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
            />
          </div>
        </div>
      </header>

      {/* Filters Panel */}
      <AnimatePresence>
        {showFilters && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-b border-border bg-muted/30 overflow-hidden"
          >
            <div className="p-4 space-y-4">
              {/* Categories */}
              <div>
                <p className="text-xs font-medium text-muted-foreground mb-2">{t.category[language]}</p>
                <div className="flex flex-wrap gap-2">
                  {CATEGORIES.map((cat) => (
                    <button
                      key={cat.id}
                      onClick={() => setSelectedCategory(cat.id)}
                      className={cn(
                        "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors",
                        selectedCategory === cat.id
                          ? "bg-primary-500 text-white"
                          : "bg-card border border-border hover:bg-accent"
                      )}
                    >
                      <Folder className="w-3.5 h-3.5" />
                      {getCategoryName(cat)}
                    </button>
                  ))}
                </div>
              </div>

              {/* Pinned Filter & Tag Filter */}
              <div className="flex items-center gap-4">
                <button
                  onClick={() => setFilterPinned(!filterPinned)}
                  className={cn(
                    "flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-colors",
                    filterPinned
                      ? "bg-primary-500 text-white"
                      : "bg-card border border-border hover:bg-accent"
                  )}
                >
                  <Pin className="w-3.5 h-3.5" />
                  {t.pinnedOnly[language]}
                </button>

                {allTags.length > 0 && (
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">{t.filterByTag[language]}:</span>
                    <select
                      value={filterByTag || ''}
                      onChange={(e) => setFilterByTag(e.target.value || null)}
                      className="px-3 py-1.5 bg-card border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/50"
                    >
                      <option value="">{t.allTags[language]}</option>
                      {allTags.map((tag) => (
                        <option key={tag} value={tag}>{tag}</option>
                      ))}
                    </select>
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Popular Topics */}
      {localSessions.length > 5 && (
        <div className="px-6 py-3 border-b border-border bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-950/20 dark:to-orange-950/20">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-4 h-4 text-amber-600 dark:text-amber-400" />
            <span className="text-sm font-medium text-amber-700 dark:text-amber-300">
              {t.popularTopics[language]}
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {/* Extract keywords from session titles */}
            {Array.from(new Set(
              localSessions
                .flatMap(s => s.title.toLowerCase().split(/\s+/))
                .filter(word => word.length > 3)
                .filter(word => !['nasıl', 'nedir', 'what', 'about', 'how', 'the', 'bir', 'için', 'ile'].includes(word))
            ))
              .slice(0, 8)
              .map((topic, i) => (
                <button
                  key={i}
                  onClick={() => setSearchQuery(topic)}
                  className="px-3 py-1 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 rounded-full text-xs hover:bg-amber-200 dark:hover:bg-amber-800/40 transition-colors"
                >
                  {topic}
                </button>
              ))}
          </div>
        </div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-3xl mx-auto space-y-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary-500 border-t-transparent" />
            </div>
          ) : Object.keys(groupedSessions).length === 0 ? (
            <div className="text-center py-12">
              <History className="w-16 h-16 mx-auto text-muted-foreground/50 mb-4" />
              <p className="text-lg font-medium text-muted-foreground">{t.noConversations[language]}</p>
              <p className="text-sm text-muted-foreground mt-1">{t.conversationsAppear[language]}</p>
            </div>
          ) : (
            Object.entries(groupedSessions).map(([date, sessions]) => (
              <div key={date}>
                <div className="flex items-center gap-2 mb-3">
                  <Calendar className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm font-medium text-muted-foreground">{date}</span>
                </div>

                <div className="space-y-2">
                  {sessions.map((session, index) => (
                    <motion.div
                      key={session.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className={cn(
                        "group flex flex-col p-4 bg-card border rounded-xl hover:border-primary-500/30 hover:shadow-lg transition-all",
                        session.isPinned
                          ? "border-primary-500/50 bg-primary-500/5"
                          : "border-border"
                      )}
                    >
                      <div
                        className={cn(
                          "flex items-center gap-4 cursor-pointer",
                          sessionLoading === session.id && "opacity-50 pointer-events-none"
                        )}
                        onClick={() => handleOpenSession(session.id)}
                      >
                        {/* Icon */}
                        <div className={cn(
                          "flex items-center justify-center w-10 h-10 rounded-xl",
                          session.isPinned ? "bg-primary-500/20" : "bg-muted"
                        )}>
                          {sessionLoading === session.id ? (
                            <div className="animate-spin rounded-full h-5 w-5 border-2 border-primary-500 border-t-transparent" />
                          ) : session.isPinned ? (
                            <Pin className="w-5 h-5 text-primary-500" />
                          ) : (
                            <MessageSquare className="w-5 h-5 text-muted-foreground" />
                          )}
                        </div>

                        {/* Info */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            {editingNameSessionId === session.id ? (
                              <div className="flex items-center gap-2 flex-1" onClick={(e) => e.stopPropagation()}>
                                <input
                                  type="text"
                                  value={editingNameValue}
                                  onChange={(e) => setEditingNameValue(e.target.value)}
                                  className="flex-1 px-2 py-1 border border-border rounded bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                                  autoFocus
                                  onKeyDown={(e) => {
                                    if (e.key === 'Enter') {
                                      handleSaveRename(session.id);
                                    } else if (e.key === 'Escape') {
                                      setEditingNameSessionId(null);
                                    }
                                  }}
                                />
                                <button
                                  onClick={() => handleSaveRename(session.id)}
                                  className="p-1 text-green-500 hover:bg-green-500/10 rounded"
                                >
                                  <Check className="w-4 h-4" />
                                </button>
                                <button
                                  onClick={() => setEditingNameSessionId(null)}
                                  className="p-1 text-red-500 hover:bg-red-500/10 rounded"
                                >
                                  <X className="w-4 h-4" />
                                </button>
                              </div>
                            ) : (
                              <>
                                <p className="font-medium truncate">{session.title}</p>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setEditingNameSessionId(session.id);
                                    setEditingNameValue(session.title);
                                  }}
                                  className="p-1 opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-foreground hover:bg-accent rounded transition-all"
                                  title={language === 'tr' ? 'Yeniden Adlandır' : language === 'de' ? 'Umbenennen' : 'Rename'}
                                >
                                  <Edit2 className="w-3 h-3" />
                                </button>
                              </>
                            )}
                            {session.category && editingNameSessionId !== session.id && (
                              <span className="px-2 py-0.5 bg-muted rounded text-xs text-muted-foreground">
                                {getCategoryName(CATEGORIES.find(c => c.id === session.category) || CATEGORIES[0])}
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-2 text-xs text-muted-foreground mt-1">
                            <Clock className="w-3 h-3" />
                            <span>{formatDate(session.updatedAt, language)}</span>
                          </div>
                        </div>

                        {/* Actions */}
                        <div className="flex items-center gap-2">
                          {/* Pin Button */}
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleTogglePin(session.id);
                            }}
                            className={cn(
                              "p-2 rounded-lg transition-all",
                              session.isPinned
                                ? "bg-primary-500 text-white"
                                : "opacity-0 group-hover:opacity-100 hover:bg-accent text-muted-foreground"
                            )}
                            title={session.isPinned ? t.unpin[language] : t.pin[language]}
                          >
                            <Pin className="w-4 h-4" />
                          </button>

                          {/* Category Dropdown */}
                          <select
                            value={session.category || 'all'}
                            onClick={(e) => e.stopPropagation()}
                            onChange={(e) => {
                              e.stopPropagation();
                              handleSetCategory(session.id, e.target.value);
                            }}
                            className="p-2 rounded-lg bg-transparent opacity-0 group-hover:opacity-100 hover:bg-accent text-muted-foreground text-sm focus:outline-none cursor-pointer"
                            title={t.category[language]}
                          >
                            {CATEGORIES.map((cat) => (
                              <option key={cat.id} value={cat.id}>
                                {getCategoryName(cat)}
                              </option>
                            ))}
                          </select>

                          {/* Tag Button */}
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setEditingTagSessionId(editingTagSessionId === session.id ? null : session.id);
                            }}
                            className="p-2 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-accent text-muted-foreground transition-all"
                            title={t.tags[language]}
                          >
                            <Tag className="w-4 h-4" />
                          </button>

                          {/* Delete Button */}
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDelete(session.id);
                            }}
                            className="p-2 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-red-500/10 text-red-500 transition-all"
                            title="Sil"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                          <ChevronRight className="w-5 h-5 text-muted-foreground group-hover:text-foreground transition-colors" />
                        </div>
                      </div>

                      {/* Tags Section */}
                      {((session.tags && session.tags.length > 0) || editingTagSessionId === session.id) && (
                        <div className="mt-3 pt-3 border-t border-border">
                          <div className="flex items-center flex-wrap gap-2">
                            {(session.tags || []).map((tag) => (
                              <span
                                key={tag}
                                className="flex items-center gap-1 px-2 py-1 bg-muted rounded-md text-xs"
                              >
                                {tag}
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleRemoveTag(session.id, tag);
                                  }}
                                  className="p-0.5 hover:bg-destructive/20 hover:text-destructive rounded transition-colors"
                                >
                                  <X className="w-3 h-3" />
                                </button>
                              </span>
                            ))}

                            {editingTagSessionId === session.id && (
                              <div className="flex items-center gap-1">
                                <input
                                  type="text"
                                  value={tagInput}
                                  onChange={(e) => setTagInput(e.target.value)}
                                  onKeyPress={(e) => {
                                    if (e.key === 'Enter') {
                                      handleAddTag(session.id);
                                    }
                                  }}
                                  placeholder={t.addTag[language]}
                                  className="px-2 py-1 bg-background border border-border rounded-md text-xs focus:outline-none focus:ring-1 focus:ring-primary-500"
                                  onClick={(e) => e.stopPropagation()}
                                />
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleAddTag(session.id);
                                  }}
                                  className="p-1 bg-primary-500 text-white rounded-md hover:bg-primary-600 transition-colors"
                                >
                                  <Plus className="w-3 h-3" />
                                </button>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </motion.div>
                  ))}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
