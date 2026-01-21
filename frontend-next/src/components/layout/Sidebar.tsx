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
  Pin,
  Tag,
  FolderOpen,
  X,
  WifiOff,
  Server,
  Brain,
  HardDrive,
  Activity,
  Clock,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Zap,
  Shield,
  Play,
  RotateCcw
} from 'lucide-react';
import { useStore, Page } from '@/store/useStore';
import { cn } from '@/lib/utils';
import { checkHealth, HealthStatus, startOllamaService, startChromaDBService, getBackendRestartInfo } from '@/lib/api';

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
  const [systemExpanded, setSystemExpanded] = useState(false);
  const [lastHealthCheck, setLastHealthCheck] = useState<Date | null>(null);
  const [connectionAttempts, setConnectionAttempts] = useState(0);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [startingService, setStartingService] = useState<string | null>(null);
  const [serviceMessage, setServiceMessage] = useState<{type: 'success' | 'error' | 'info', text: string} | null>(null);

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

  // Health check with retry tracking
  const fetchHealth = async (isManual = false) => {
    if (isManual) setIsRefreshing(true);
    setHealthLoading(true);
    try {
      const response = await checkHealth();
      if (response.success && response.data) {
        setHealth(response.data);
        setConnectionAttempts(0); // Reset on success
      } else {
        setHealth(null);
        setConnectionAttempts(prev => prev + 1);
      }
    } catch {
      setHealth(null);
      setConnectionAttempts(prev => prev + 1);
    }
    setHealthLoading(false);
    setLastHealthCheck(new Date());
    if (isManual) setIsRefreshing(false);
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(() => fetchHealth(), 15000); // Every 15 seconds
    return () => clearInterval(interval);
  }, []);

  // Service start handlers
  const handleStartOllama = async () => {
    setStartingService('ollama');
    setServiceMessage(null);
    try {
      const response = await startOllamaService();
      if (response.success && response.data) {
        setServiceMessage({
          type: response.data.success ? 'success' : 'error',
          text: response.data.message
        });
        if (response.data.success) {
          fetchHealth(true); // Refresh health status
        }
      }
    } catch {
      setServiceMessage({
        type: 'error',
        text: language === 'tr' ? 'Ollama başlatılamadı' : 'Failed to start Ollama'
      });
    }
    setStartingService(null);
    // Clear message after 5 seconds
    setTimeout(() => setServiceMessage(null), 5000);
  };

  const handleStartChromaDB = async () => {
    setStartingService('chromadb');
    setServiceMessage(null);
    try {
      const response = await startChromaDBService();
      if (response.success && response.data) {
        setServiceMessage({
          type: response.data.success ? 'success' : 'error',
          text: response.data.message
        });
        if (response.data.success) {
          fetchHealth(true);
        }
      }
    } catch {
      setServiceMessage({
        type: 'error',
        text: language === 'tr' ? 'ChromaDB bağlanamadı' : 'Failed to connect ChromaDB'
      });
    }
    setStartingService(null);
    setTimeout(() => setServiceMessage(null), 5000);
  };

  const handleBackendInfo = async () => {
    setStartingService('backend');
    try {
      const response = await getBackendRestartInfo();
      if (response.success && response.data) {
        setServiceMessage({
          type: 'info',
          text: response.data.steps?.join(' ') || response.data.message
        });
      }
    } catch {
      setServiceMessage({
        type: 'info',
        text: language === 'tr' 
          ? "Terminal'de: python run.py" 
          : "In terminal: python run.py"
      });
    }
    setStartingService(null);
    setTimeout(() => setServiceMessage(null), 8000);
  };

  // Derive system issues from health data
  const systemIssues = useMemo(() => {
    const issues: { severity: 'error' | 'warning' | 'info'; message: string; detail?: string }[] = [];
    
    if (!health) {
      issues.push({
        severity: 'error',
        message: language === 'tr' ? 'API bağlantısı yok' : 'No API connection',
        detail: language === 'tr' ? 'Backend sunucusu çalışmıyor olabilir' : 'Backend server may not be running'
      });
      return issues;
    }
    
    // Check LLM status
    if (health.components?.llm !== 'healthy') {
      issues.push({
        severity: 'error',
        message: language === 'tr' ? 'LLM yanıt vermiyor' : 'LLM not responding',
        detail: language === 'tr' ? 'Ollama servisi çalışmıyor olabilir. Chat yanıtları alınamaz.' : 'Ollama service may not be running. Chat responses unavailable.'
      });
    }
    
    // Check Vector Store
    if (health.components?.vector_store !== 'healthy') {
      issues.push({
        severity: 'warning',
        message: language === 'tr' ? 'VectorDB sorunu' : 'VectorDB issue',
        detail: language === 'tr' ? 'Belge araması çalışmayabilir' : 'Document search may not work'
      });
    }
    
    // Check document count
    const docCount = health.components?.document_count;
    if (typeof docCount === 'number' && docCount === 0) {
      issues.push({
        severity: 'info',
        message: language === 'tr' ? 'Belge yüklenmemiş' : 'No documents loaded',
        detail: language === 'tr' ? 'RAG için belge yükleyin' : 'Upload documents for RAG'
      });
    }
    
    // Check RAG sync status
    const ragSynced = health.components?.rag_synced;
    const unindexedFiles = health.components?.unindexed_files;
    if (ragSynced === false && typeof unindexedFiles === 'number' && unindexedFiles > 0) {
      issues.push({
        severity: 'warning',
        message: language === 'tr' ? 'Belge senkronizasyonu gerekli' : 'Document sync required',
        detail: language === 'tr' ? `${unindexedFiles} belge indekslenmemiş` : `${unindexedFiles} documents not indexed`
      });
    }
    
    // Connection retry warning
    if (connectionAttempts > 2) {
      issues.push({
        severity: 'warning',
        message: language === 'tr' ? 'Bağlantı kararsız' : 'Unstable connection',
        detail: language === 'tr' ? `${connectionAttempts} başarısız deneme` : `${connectionAttempts} failed attempts`
      });
    }
    
    return issues;
  }, [health, language, connectionAttempts]);

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
        {/* Enhanced System Status Panel */}
        {!sidebarCollapsed && (
          <div className={cn(
            "mb-3 rounded-lg overflow-hidden transition-all duration-300",
            systemIssues.length > 0 && systemIssues[0].severity === 'error' 
              ? "bg-red-500/10 border border-red-500/30" 
              : systemIssues.length > 0 && systemIssues[0].severity === 'warning'
              ? "bg-yellow-500/10 border border-yellow-500/30"
              : "bg-green-500/10 border border-green-500/30"
          )}>
            {/* Header - Clickable */}
            <button
              onClick={() => setSystemExpanded(!systemExpanded)}
              className="w-full p-2 flex items-center justify-between hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
            >
              <div className="flex items-center gap-2">
                {healthLoading || isRefreshing ? (
                  <Loader2 className="w-4 h-4 animate-spin text-primary-500" />
                ) : health ? (
                  systemIssues.length === 0 ? (
                    <div className="relative">
                      <Shield className="w-4 h-4 text-green-500" />
                      <Activity className="w-2 h-2 text-green-400 absolute -top-0.5 -right-0.5 animate-pulse" />
                    </div>
                  ) : systemIssues[0].severity === 'error' ? (
                    <div className="relative">
                      <XCircle className="w-4 h-4 text-red-500" />
                      <span className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full animate-ping" />
                    </div>
                  ) : (
                    <AlertCircle className="w-4 h-4 text-yellow-500" />
                  )
                ) : (
                  <WifiOff className="w-4 h-4 text-red-500" />
                )}
                <span className="text-xs font-medium">
                  {t.system[language]}
                </span>
              </div>
              <div className="flex items-center gap-1">
                {/* Issue Count Badge */}
                {systemIssues.length > 0 && (
                  <span className={cn(
                    "px-1.5 py-0.5 rounded-full text-[10px] font-bold",
                    systemIssues[0].severity === 'error' 
                      ? "bg-red-500 text-white" 
                      : "bg-yellow-500 text-black"
                  )}>
                    {systemIssues.length}
                  </span>
                )}
                {systemExpanded ? (
                  <ChevronUp className="w-3 h-3 text-muted-foreground" />
                ) : (
                  <ChevronDown className="w-3 h-3 text-muted-foreground" />
                )}
              </div>
            </button>

            {/* Collapsed Quick Status */}
            {!systemExpanded && (
              <div className="px-2 pb-2">
                <div className="flex items-center gap-2 text-[10px]">
                  {/* Quick status icons */}
                  <div className="flex items-center gap-1" title="API">
                    <Server className="w-3 h-3" />
                    {health ? (
                      <CheckCircle2 className="w-2.5 h-2.5 text-green-500" />
                    ) : (
                      <XCircle className="w-2.5 h-2.5 text-red-500" />
                    )}
                  </div>
                  <div className="flex items-center gap-1" title="LLM (Ollama)">
                    <Brain className="w-3 h-3" />
                    {health?.components?.llm === 'healthy' ? (
                      <CheckCircle2 className="w-2.5 h-2.5 text-green-500" />
                    ) : (
                      <XCircle className="w-2.5 h-2.5 text-red-500" />
                    )}
                  </div>
                  <div className="flex items-center gap-1" title="VectorDB">
                    <HardDrive className="w-3 h-3" />
                    {health?.components?.vector_store === 'healthy' ? (
                      <CheckCircle2 className="w-2.5 h-2.5 text-green-500" />
                    ) : (
                      <XCircle className="w-2.5 h-2.5 text-red-500" />
                    )}
                  </div>
                  <div className="ml-auto text-muted-foreground flex items-center gap-0.5">
                    <Clock className="w-2.5 h-2.5" />
                    {lastHealthCheck ? (
                      <span>{Math.round((Date.now() - lastHealthCheck.getTime()) / 1000)}s</span>
                    ) : '-'}
                  </div>
                </div>
              </div>
            )}

            {/* Expanded Details */}
            <AnimatePresence>
              {systemExpanded && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="overflow-hidden"
                >
                  <div className="px-2 pb-2 space-y-2">
                    {/* Services Status */}
                    <div className="space-y-1">
                      <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                        {language === 'tr' ? 'Servisler' : 'Services'}
                      </p>
                      
                      {/* API Status */}
                      <div className="flex items-center justify-between p-1.5 rounded bg-black/5 dark:bg-white/5">
                        <div className="flex items-center gap-2">
                          <Server className="w-3 h-3" />
                          <span className="text-xs">API Backend</span>
                        </div>
                        <div className="flex items-center gap-1">
                          {health ? (
                            <span className="flex items-center gap-1 text-[10px] text-green-600 dark:text-green-400">
                              <Zap className="w-2.5 h-2.5" />
                              {language === 'tr' ? 'Aktif' : 'Active'}
                            </span>
                          ) : (
                            <>
                              <span className="text-[10px] text-red-500">Offline</span>
                              <button
                                onClick={handleBackendInfo}
                                disabled={startingService === 'backend'}
                                className="ml-1 p-0.5 rounded hover:bg-primary-500/20 transition-colors"
                                title={language === 'tr' ? 'Nasıl başlatılır?' : 'How to start?'}
                              >
                                {startingService === 'backend' ? (
                                  <Loader2 className="w-3 h-3 animate-spin text-primary-500" />
                                ) : (
                                  <Play className="w-3 h-3 text-primary-500" />
                                )}
                              </button>
                            </>
                          )}
                        </div>
                      </div>

                      {/* LLM Status */}
                      <div className="flex items-center justify-between p-1.5 rounded bg-black/5 dark:bg-white/5">
                        <div className="flex items-center gap-2">
                          <Brain className="w-3 h-3" />
                          <span className="text-xs">LLM (Ollama)</span>
                        </div>
                        <div className="flex items-center gap-1">
                          {health?.components?.llm === 'healthy' ? (
                            <span className="flex items-center gap-1 text-[10px] text-green-600 dark:text-green-400">
                              <Zap className="w-2.5 h-2.5" />
                              {language === 'tr' ? 'Hazır' : 'Ready'}
                            </span>
                          ) : (
                            <>
                              <span className="text-[10px] text-red-500">
                                {language === 'tr' ? 'Hata' : 'Error'}
                              </span>
                              <button
                                onClick={handleStartOllama}
                                disabled={startingService === 'ollama'}
                                className="ml-1 p-0.5 rounded hover:bg-primary-500/20 transition-colors"
                                title={language === 'tr' ? 'Ollama Başlat' : 'Start Ollama'}
                              >
                                {startingService === 'ollama' ? (
                                  <Loader2 className="w-3 h-3 animate-spin text-primary-500" />
                                ) : (
                                  <Play className="w-3 h-3 text-primary-500" />
                                )}
                              </button>
                            </>
                          )}
                        </div>
                      </div>

                      {/* Vector DB Status */}
                      <div className="flex items-center justify-between p-1.5 rounded bg-black/5 dark:bg-white/5">
                        <div className="flex items-center gap-2">
                          <Database className="w-3 h-3" />
                          <span className="text-xs">VectorDB</span>
                        </div>
                        <div className="flex items-center gap-1">
                          {typeof health?.components?.document_count === 'number' && (
                            <span className="text-[10px] text-muted-foreground">
                              {health.components.document_count} {language === 'tr' ? 'belge' : 'docs'}
                            </span>
                          )}
                          {health?.components?.vector_store === 'healthy' ? (
                            <CheckCircle2 className="w-3 h-3 text-green-500" />
                          ) : (
                            <>
                              <XCircle className="w-3 h-3 text-red-500" />
                              <button
                                onClick={handleStartChromaDB}
                                disabled={startingService === 'chromadb'}
                                className="ml-1 p-0.5 rounded hover:bg-primary-500/20 transition-colors"
                                title={language === 'tr' ? 'Yeniden Bağlan' : 'Reconnect'}
                              >
                                {startingService === 'chromadb' ? (
                                  <Loader2 className="w-3 h-3 animate-spin text-primary-500" />
                                ) : (
                                  <RotateCcw className="w-3 h-3 text-primary-500" />
                                )}
                              </button>
                            </>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Service Message */}
                    {serviceMessage && (
                      <div className={cn(
                        "p-1.5 rounded text-[10px]",
                        serviceMessage.type === 'success' ? "bg-green-500/20 text-green-700 dark:text-green-300" :
                        serviceMessage.type === 'error' ? "bg-red-500/20 text-red-700 dark:text-red-300" :
                        "bg-blue-500/20 text-blue-700 dark:text-blue-300"
                      )}>
                        {serviceMessage.text}
                      </div>
                    )}

                    {/* Issues Section */}
                    {systemIssues.length > 0 && (
                      <div className="space-y-1">
                        <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                          {language === 'tr' ? 'Sorunlar' : 'Issues'}
                        </p>
                        {systemIssues.map((issue, idx) => (
                          <div
                            key={idx}
                            className={cn(
                              "p-1.5 rounded text-xs",
                              issue.severity === 'error' ? "bg-red-500/20 text-red-700 dark:text-red-300" :
                              issue.severity === 'warning' ? "bg-yellow-500/20 text-yellow-700 dark:text-yellow-300" :
                              "bg-blue-500/20 text-blue-700 dark:text-blue-300"
                            )}
                          >
                            <div className="font-medium flex items-center gap-1">
                              {issue.severity === 'error' && <XCircle className="w-3 h-3" />}
                              {issue.severity === 'warning' && <AlertCircle className="w-3 h-3" />}
                              {issue.severity === 'info' && <AlertCircle className="w-3 h-3" />}
                              {issue.message}
                            </div>
                            {issue.detail && (
                              <p className="text-[10px] opacity-80 mt-0.5 ml-4">{issue.detail}</p>
                            )}
                          </div>
                        ))}
                      </div>
                    )}

                    {/* All Clear Message */}
                    {systemIssues.length === 0 && health && (
                      <div className="p-2 rounded bg-green-500/20 text-green-700 dark:text-green-300 text-xs text-center">
                        <CheckCircle2 className="w-4 h-4 mx-auto mb-1" />
                        <p className="font-medium">
                          {language === 'tr' ? 'Tüm sistemler çalışıyor' : 'All systems operational'}
                        </p>
                        <p className="text-[10px] opacity-80">
                          {language === 'tr' ? 'Chat için hazır' : 'Ready to chat'}
                        </p>
                      </div>
                    )}

                    {/* Refresh Button */}
                    <button
                      onClick={() => fetchHealth(true)}
                      disabled={isRefreshing}
                      className={cn(
                        "w-full flex items-center justify-center gap-1 p-1.5 rounded text-xs transition-colors",
                        "bg-black/5 dark:bg-white/5 hover:bg-black/10 dark:hover:bg-white/10",
                        isRefreshing && "opacity-50 cursor-not-allowed"
                      )}
                    >
                      <RefreshCw className={cn("w-3 h-3", isRefreshing && "animate-spin")} />
                      {language === 'tr' ? 'Yenile' : 'Refresh'}
                    </button>

                    {/* Last Check Time */}
                    {lastHealthCheck && (
                      <p className="text-[10px] text-center text-muted-foreground">
                        {language === 'tr' ? 'Son kontrol: ' : 'Last check: '}
                        {lastHealthCheck.toLocaleTimeString()}
                      </p>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}

        {/* Collapsed sidebar - mini status indicator */}
        {sidebarCollapsed && (
          <div className="mb-3 flex justify-center">
            <div 
              className={cn(
                "w-8 h-8 rounded-lg flex items-center justify-center cursor-pointer group relative",
                health && systemIssues.length === 0 
                  ? "bg-green-500/20" 
                  : health && systemIssues[0]?.severity === 'warning'
                  ? "bg-yellow-500/20"
                  : "bg-red-500/20"
              )}
              onClick={() => setSystemExpanded(!systemExpanded)}
            >
              {healthLoading ? (
                <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
              ) : health ? (
                systemIssues.length === 0 ? (
                  <CheckCircle2 className="w-4 h-4 text-green-500" />
                ) : (
                  <AlertCircle className={cn(
                    "w-4 h-4",
                    systemIssues[0]?.severity === 'error' ? "text-red-500" : "text-yellow-500"
                  )} />
                )
              ) : (
                <WifiOff className="w-4 h-4 text-red-500" />
              )}
              
              {/* Tooltip */}
              <div className="absolute left-full ml-2 px-2 py-1 bg-popover text-popover-foreground text-xs rounded-md shadow-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50">
                {health ? (
                  systemIssues.length === 0 
                    ? (language === 'tr' ? 'Sistem stabil' : 'System stable')
                    : `${systemIssues.length} ${language === 'tr' ? 'sorun' : 'issue(s)'}`
                ) : (
                  language === 'tr' ? 'Bağlantı yok' : 'No connection'
                )}
              </div>
            </div>
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
