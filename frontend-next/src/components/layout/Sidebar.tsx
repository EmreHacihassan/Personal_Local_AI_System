'use client';

import { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  MessageSquare, 
  FileText, 
  History, 
  LayoutDashboard, 
  Settings, 
  StickyNote,
  GraduationCap,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  Star,
  FileCode,
  Search,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Loader2,
  Database,
  Cpu,
  Pin,
  Tag,
  FolderOpen,
  X
} from 'lucide-react';
import { useStore, Page } from '@/store/useStore';
import { cn } from '@/lib/utils';
import { checkHealth, HealthStatus } from '@/lib/api';

const menuItems: { id: Page; icon: React.ElementType; label: string; labelEn: string; labelDe: string }[] = [
  { id: 'chat', icon: MessageSquare, label: 'Sohbet', labelEn: 'Chat', labelDe: 'Chat' },
  { id: 'favorites', icon: Star, label: 'Favoriler', labelEn: 'Favorites', labelDe: 'Favoriten' },
  { id: 'templates', icon: FileCode, label: 'Şablonlar', labelEn: 'Templates', labelDe: 'Vorlagen' },
  { id: 'search', icon: Search, label: 'Gelişmiş Arama', labelEn: 'Advanced Search', labelDe: 'Erweiterte Suche' },
  { id: 'documents', icon: FileText, label: 'Dökümanlar', labelEn: 'Documents', labelDe: 'Dokumente' },
  { id: 'history', icon: History, label: 'Geçmiş', labelEn: 'History', labelDe: 'Verlauf' },
  { id: 'notes', icon: StickyNote, label: 'Notlar', labelEn: 'Notes', labelDe: 'Notizen' },
  { id: 'learning', icon: GraduationCap, label: 'AI ile Öğren', labelEn: 'Learn with AI', labelDe: 'Mit KI lernen' },
  { id: 'dashboard', icon: LayoutDashboard, label: 'Dashboard', labelEn: 'Dashboard', labelDe: 'Dashboard' },
  { id: 'settings', icon: Settings, label: 'Ayarlar', labelEn: 'Settings', labelDe: 'Einstellungen' },
];

export function Sidebar() {
  const { 
    currentPage, 
    setCurrentPage, 
    sidebarCollapsed, 
    toggleSidebar,
    language,
    messages,
    currentSessionId,
    sessions,
    showPinnedOnly,
    toggleShowPinnedOnly,
    addSessionTag,
    removeSessionTag,
    setSessionCategory
  } = useStore();

  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [healthLoading, setHealthLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [newTag, setNewTag] = useState('');
  const [showTagInput, setShowTagInput] = useState(false);

  // Get all unique categories and tags from sessions
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { categories, allTags, currentSessionTags } = useMemo(() => {
    const cats = new Set<string>();
    const tags = new Set<string>();
    sessions.forEach(s => {
      if (s.category) cats.add(s.category);
      s.tags?.forEach(t => tags.add(t));
    });
    
    const currentSession = sessions.find(s => s.id === currentSessionId);
    return {
      categories: Array.from(cats),
      allTags: Array.from(tags),
      currentSessionTags: currentSession?.tags || []
    };
  }, [sessions, currentSessionId]);

  const handleAddTag = () => {
    if (newTag.trim() && currentSessionId) {
      addSessionTag(currentSessionId, newTag.trim());
      setNewTag('');
      setShowTagInput(false);
    }
  };

  const handleRemoveTag = (tag: string) => {
    if (currentSessionId) {
      removeSessionTag(currentSessionId, tag);
    }
  };

  const handleCategoryChange = (category: string) => {
    setSelectedCategory(category);
    if (currentSessionId && category !== 'all') {
      setSessionCategory(currentSessionId, category);
    }
  };

  // Health check
  useEffect(() => {
    const fetchHealth = async () => {
      setHealthLoading(true);
      try {
        const response = await checkHealth();
        if (response.success && response.data) {
          setHealth(response.data);
        }
      } catch {
        setHealth(null);
      }
      setHealthLoading(false);
    };
    
    fetchHealth();
    const interval = setInterval(fetchHealth, 30000); // Every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const getLabel = (item: typeof menuItems[0]) => {
    switch (language) {
      case 'de': return item.labelDe;
      case 'en': return item.labelEn;
      default: return item.label;
    }
  };

  const collapseLabel = {
    tr: 'Daralt',
    en: 'Collapse',
    de: 'Minimieren'
  };

  const t = {
    system: { tr: 'Sistem', en: 'System', de: 'System' },
    messages: { tr: 'mesaj', en: 'messages', de: 'Nachrichten' },
    session: { tr: 'Oturum', en: 'Session', de: 'Sitzung' },
    connecting: { tr: 'Bağlanıyor...', en: 'Connecting...', de: 'Verbinden...' },
    pinnedOnly: { tr: 'Sadece Sabitler', en: 'Pinned Only', de: 'Nur Fixierte' },
    category: { tr: 'Kategori', en: 'Category', de: 'Kategorie' },
    allCategories: { tr: 'Tümü', en: 'All', de: 'Alle' },
    tags: { tr: 'Etiketler', en: 'Tags', de: 'Tags' },
    addTag: { tr: 'Etiket ekle...', en: 'Add tag...', de: 'Tag hinzufügen...' },
  };

  return (
    <motion.aside
      initial={false}
      animate={{ width: sidebarCollapsed ? 72 : 260 }}
      transition={{ duration: 0.3, ease: 'easeInOut' }}
      className={cn(
        "flex flex-col h-full bg-card border-r border-border",
        "relative z-20"
      )}
    >
      {/* Logo */}
      <div className="flex items-center h-16 px-4 border-b border-border">
        <motion.div 
          className="flex items-center gap-3"
          animate={{ justifyContent: sidebarCollapsed ? 'center' : 'flex-start' }}
        >
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 text-white">
            <Sparkles className="w-5 h-5" />
          </div>
          <AnimatePresence>
            {!sidebarCollapsed && (
              <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                transition={{ duration: 0.2 }}
              >
                <h1 className="text-lg font-bold gradient-text whitespace-nowrap">
                  Enterprise AI
                </h1>
                <p className="text-xs text-muted-foreground">v2.0</p>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentPage === item.id;
          
          return (
            <motion.button
              key={item.id}
              onClick={() => setCurrentPage(item.id)}
              className={cn(
                "w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200",
                "hover:bg-accent group relative",
                isActive && "bg-primary-500/10 text-primary-600 dark:text-primary-400"
              )}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              {/* Active indicator */}
              {isActive && (
                <motion.div
                  layoutId="activeIndicator"
                  className="absolute left-0 w-1 h-8 bg-primary-500 rounded-r-full"
                  transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                />
              )}
              
              <Icon className={cn(
                "w-5 h-5 flex-shrink-0 transition-colors",
                isActive ? "text-primary-500" : "text-muted-foreground group-hover:text-foreground"
              )} />
              
              <AnimatePresence>
                {!sidebarCollapsed && (
                  <motion.span
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -10 }}
                    transition={{ duration: 0.2 }}
                    className={cn(
                      "text-sm font-medium whitespace-nowrap",
                      isActive ? "text-primary-600 dark:text-primary-400" : "text-foreground"
                    )}
                  >
                    {getLabel(item)}
                  </motion.span>
                )}
              </AnimatePresence>

              {/* Tooltip for collapsed state */}
              {sidebarCollapsed && (
                <div className="absolute left-full ml-2 px-2 py-1 bg-popover text-popover-foreground text-sm rounded-md shadow-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50">
                  {getLabel(item)}
                </div>
              )}
            </motion.button>
          );
        })}
      </nav>

      {/* Collapse Toggle */}
      <div className="p-3 border-t border-border">
        {/* System Status */}
        {!sidebarCollapsed && (
          <div className="mb-3 p-2 rounded-lg bg-muted/50">
            <p className="text-xs font-medium text-muted-foreground mb-2 flex items-center gap-1">
              <Cpu className="w-3 h-3" />
              {t.system[language]}
            </p>
            {healthLoading ? (
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Loader2 className="w-3 h-3 animate-spin" />
                {t.connecting[language]}
              </div>
            ) : health ? (
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  {health.components?.llm === 'healthy' || health.ollama ? (
                    <CheckCircle2 className="w-3 h-3 text-green-500" />
                  ) : health.components?.llm === 'degraded' ? (
                    <AlertCircle className="w-3 h-3 text-yellow-500" />
                  ) : (
                    <XCircle className="w-3 h-3 text-red-500" />
                  )}
                  <span className="text-xs">LLM</span>
                </div>
                <div className="flex items-center gap-2">
                  {health.components?.vector_store === 'healthy' || health.chromadb ? (
                    <CheckCircle2 className="w-3 h-3 text-green-500" />
                  ) : (
                    <XCircle className="w-3 h-3 text-red-500" />
                  )}
                  <span className="text-xs flex items-center gap-1">
                    <Database className="w-3 h-3" /> VectorDB
                  </span>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-xs text-yellow-500">
                <AlertCircle className="w-3 h-3" />
                Offline
              </div>
            )}
          </div>
        )}
        
        {/* Pinned Only Filter */}
        {!sidebarCollapsed && (
          <div className="mb-3">
            <button
              onClick={toggleShowPinnedOnly}
              className={cn(
                "w-full flex items-center gap-2 px-2 py-1.5 rounded-lg text-xs transition-colors",
                showPinnedOnly 
                  ? "bg-primary-500/10 text-primary-600 dark:text-primary-400" 
                  : "bg-muted/50 hover:bg-accent text-muted-foreground"
              )}
            >
              <Pin className="w-3 h-3" />
              {t.pinnedOnly[language]}
            </button>
          </div>
        )}

        {/* Category Selector */}
        {!sidebarCollapsed && categories.length > 0 && (
          <div className="mb-3">
            <p className="text-xs font-medium text-muted-foreground mb-1.5 flex items-center gap-1">
              <FolderOpen className="w-3 h-3" />
              {t.category[language]}
            </p>
            <select
              value={selectedCategory}
              onChange={(e) => handleCategoryChange(e.target.value)}
              className="w-full px-2 py-1.5 rounded-lg bg-muted/50 border border-border text-xs focus:outline-none focus:ring-1 focus:ring-primary-500"
            >
              <option value="all">{t.allCategories[language]}</option>
              {categories.map((cat) => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>
        )}

        {/* Quick Tag Manager */}
        {!sidebarCollapsed && currentSessionId && (
          <div className="mb-3">
            <p className="text-xs font-medium text-muted-foreground mb-1.5 flex items-center gap-1">
              <Tag className="w-3 h-3" />
              {t.tags[language]}
            </p>
            <div className="flex flex-wrap gap-1 mb-1.5">
              {currentSessionTags.map((tag) => (
                <span
                  key={tag}
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-primary-500/10 text-primary-600 dark:text-primary-400 text-xs"
                >
                  {tag}
                  <button
                    onClick={() => handleRemoveTag(tag)}
                    className="hover:text-red-500 transition-colors"
                  >
                    <X className="w-2.5 h-2.5" />
                  </button>
                </span>
              ))}
            </div>
            {showTagInput ? (
              <div className="flex gap-1">
                <input
                  type="text"
                  value={newTag}
                  onChange={(e) => setNewTag(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleAddTag()}
                  placeholder={t.addTag[language]}
                  className="flex-1 px-2 py-1 rounded-lg bg-muted/50 border border-border text-xs focus:outline-none focus:ring-1 focus:ring-primary-500"
                  autoFocus
                />
                <button
                  onClick={handleAddTag}
                  className="px-2 py-1 rounded-lg bg-primary-500 text-white text-xs hover:bg-primary-600 transition-colors"
                >
                  +
                </button>
              </div>
            ) : (
              <button
                onClick={() => setShowTagInput(true)}
                className="text-xs text-primary-500 hover:text-primary-600 transition-colors"
              >
                + {t.addTag[language]}
              </button>
            )}
          </div>
        )}
        
        {/* Session Info */}
        {!sidebarCollapsed && (
          <div className="mb-3 text-xs text-muted-foreground">
            <p className="flex items-center gap-1">
              <MessageSquare className="w-3 h-3" />
              {messages.length} {t.messages[language]}
            </p>
            {currentSessionId && (
              <p className="truncate mt-1">
                {t.session[language]}: {currentSessionId.slice(0, 8)}...
              </p>
            )}
          </div>
        )}
        
        <button
          onClick={toggleSidebar}
          className={cn(
            "w-full flex items-center justify-center gap-2 px-3 py-2 rounded-xl",
            "bg-muted hover:bg-accent transition-colors"
          )}
        >
          {sidebarCollapsed ? (
            <ChevronRight className="w-5 h-5" />
          ) : (
            <>
              <ChevronLeft className="w-5 h-5" />
              <span className="text-sm">{collapseLabel[language]}</span>
            </>
          )}
        </button>
      </div>
    </motion.aside>
  );
}
