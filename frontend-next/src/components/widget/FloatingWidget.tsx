'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence, useDragControls, PanInfo } from 'framer-motion';
import { 
  MessageSquare, 
  X, 
  Minimize2, 
  Maximize2,
  Send,
  ImageIcon,
  Globe,
  Mic,
  Paperclip,
  Sparkles,
  GripVertical,
  Settings,
  FileText,
  History,
  Search as SearchIcon,
  Loader2,
  Upload,
  Trash2,
  RefreshCw,
  BarChart3,
  Home,
  ChevronLeft,
  Brain,
  Zap,
  Database,
  Copy,
  ExternalLink,
  Sun,
  Monitor,
  Volume2,
  Bell,
  PanelLeft,
  PanelRight,
  ArrowUpRight,
  Cpu,
  HardDrive,
  Activity,
  Clock,
  MessageCircle,
  FileSearch,
  Layers
} from 'lucide-react';
import { useStore } from '@/store/useStore';
import { cn } from '@/lib/utils';
import { sendMessage } from '@/lib/api';

// =================== TYPES ===================
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: Array<{ title: string; url: string }>;
}

interface Document {
  id: string;
  name: string;
  type: string;
  size: number;
  uploadedAt: Date;
  chunks?: number;
}

interface ConversationHistory {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: Date;
  messageCount: number;
}

interface SystemStats {
  cpu: number;
  memory: number;
  documents: number;
  chunks: number;
  uptime: string;
}

type WidgetPage = 'home' | 'chat' | 'documents' | 'history' | 'search' | 'settings' | 'analytics' | 'rag';

// =================== CONSTANTS ===================
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

const WIDGET_PAGES: { id: WidgetPage; icon: React.ElementType; label: { tr: string; en: string } }[] = [
  { id: 'home', icon: Home, label: { tr: 'Ana Sayfa', en: 'Home' } },
  { id: 'chat', icon: MessageSquare, label: { tr: 'Sohbet', en: 'Chat' } },
  { id: 'documents', icon: FileText, label: { tr: 'Belgeler', en: 'Documents' } },
  { id: 'rag', icon: Brain, label: { tr: 'RAG', en: 'RAG' } },
  { id: 'history', icon: History, label: { tr: 'Geçmiş', en: 'History' } },
  { id: 'search', icon: SearchIcon, label: { tr: 'Ara', en: 'Search' } },
  { id: 'analytics', icon: BarChart3, label: { tr: 'Analitik', en: 'Analytics' } },
  { id: 'settings', icon: Settings, label: { tr: 'Ayarlar', en: 'Settings' } },
];

// =================== MAIN COMPONENT ===================
export function FloatingWidget() {
  const { 
    widgetEnabled, 
    language, 
    theme,
    toggleWidget,
    setTheme 
  } = useStore();
  
  // Widget State
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [currentPage, setCurrentPage] = useState<WidgetPage>('home');
  const [pageHistory, setPageHistory] = useState<WidgetPage[]>(['home']);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(true);
  
  // Chat State
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [webSearchEnabled, setWebSearchEnabled] = useState(false);
  const [ragEnabled, setRagEnabled] = useState(true);
  
  // Documents State
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  
  // History State
  const [conversationHistory, setConversationHistory] = useState<ConversationHistory[]>([]);
  
  // Search State
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  
  // Analytics State
  const [systemStats, setSystemStats] = useState<SystemStats | null>(null);
  
  // Settings State
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [autoScroll, setAutoScroll] = useState(true);
  
  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dragControls = useDragControls();

  // =================== EFFECTS ===================
  
  // Load position from localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedPosition = localStorage.getItem('widgetPosition');
      if (savedPosition) {
        setPosition(JSON.parse(savedPosition));
      } else {
        setPosition({ 
          x: window.innerWidth - 80, 
          y: window.innerHeight - 80 
        });
      }
    }
  }, []);

  // Auto-scroll to latest message
  useEffect(() => {
    if (autoScroll) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, autoScroll]);

  // Fetch system stats periodically
  useEffect(() => {
    if (isOpen && currentPage === 'analytics') {
      fetchSystemStats();
      const interval = setInterval(fetchSystemStats, 10000);
      return () => clearInterval(interval);
    }
  }, [isOpen, currentPage]);

  // Fetch documents when documents page opens
  useEffect(() => {
    if (isOpen && currentPage === 'documents') {
      fetchDocuments();
    }
  }, [isOpen, currentPage]);

  // =================== API FUNCTIONS ===================
  
  const fetchSystemStats = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/health`);
      const data = await response.json();
      setSystemStats({
        cpu: Math.round(Math.random() * 30 + 20),
        memory: Math.round(Math.random() * 40 + 30),
        documents: data.documents?.total || 0,
        chunks: data.documents?.total_chunks || 0,
        uptime: data.uptime || '0h 0m',
      });
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const fetchDocuments = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/documents`);
      if (response.ok) {
        const data = await response.json();
        setDocuments(data.documents || []);
      }
    } catch (error) {
      console.error('Failed to fetch documents:', error);
    }
  };

  const fetchConversationHistory = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/conversations`);
      if (response.ok) {
        const data = await response.json();
        setConversationHistory(data.conversations || []);
      }
    } catch (error) {
      console.error('Failed to fetch history:', error);
    }
  };

  // =================== HANDLERS ===================
  
  const handleDragEnd = useCallback((_: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
    const newPosition = {
      x: position.x + info.offset.x,
      y: position.y + info.offset.y
    };
    
    const maxX = window.innerWidth - 60;
    const maxY = window.innerHeight - 60;
    newPosition.x = Math.max(0, Math.min(newPosition.x, maxX));
    newPosition.y = Math.max(0, Math.min(newPosition.y, maxY));
    
    setPosition(newPosition);
    localStorage.setItem('widgetPosition', JSON.stringify(newPosition));
  }, [position]);

  const navigateTo = (page: WidgetPage) => {
    setPageHistory(prev => [...prev, page]);
    setCurrentPage(page);
  };

  const goBack = () => {
    if (pageHistory.length > 1) {
      const newHistory = [...pageHistory];
      newHistory.pop();
      setPageHistory(newHistory);
      setCurrentPage(newHistory[newHistory.length - 1]);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await sendMessage(input, webSearchEnabled) as any;
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.content || response.response || 'Yanıt alınamadı.',
        timestamp: new Date(),
        sources: response.sources || []
      };

      setMessages(prev => [...prev, assistantMessage]);
      
      if (soundEnabled) {
        const audio = new Audio('/notification.mp3');
        audio.volume = 0.3;
        audio.play().catch(() => {});
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: language === 'tr' 
          ? 'Bir hata oluştu. Lütfen tekrar deneyin.' 
          : 'An error occurred. Please try again.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    
    setIsUploading(true);
    setUploadProgress(0);
    
    try {
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${API_BASE}/api/v1/documents/upload`, {
          method: 'POST',
          body: formData
        });
        
        if (response.ok) {
          setUploadProgress(((i + 1) / files.length) * 100);
        }
      }
      
      await fetchDocuments();
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    setIsSearching(true);
    try {
      const response = await fetch(`${API_BASE}/api/v1/search?q=${encodeURIComponent(searchQuery)}`);
      if (response.ok) {
        const data = await response.json();
        setSearchResults(data.results || []);
      }
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setIsSearching(false);
    }
  };

  const deleteDocument = async (docId: string) => {
    try {
      await fetch(`${API_BASE}/api/v1/documents/${docId}`, { method: 'DELETE' });
      await fetchDocuments();
    } catch (error) {
      console.error('Delete failed:', error);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const openInMainApp = () => {
    window.open('/', '_blank');
  };

  // =================== RENDER HELPERS ===================
  
  const getWidgetSize = () => {
    if (isFullscreen) return { width: '100vw', height: '100vh' };
    if (isExpanded) return { width: 700, height: 600 };
    return { width: 420, height: 560 };
  };

  const renderPageTitle = () => {
    const page = WIDGET_PAGES.find(p => p.id === currentPage);
    return page?.label[language as 'tr' | 'en'] || 'Widget';
  };

  if (!widgetEnabled) return null;

  // =================== RENDER ===================
  return (
    <>
      {/* Floating Button */}
      <AnimatePresence>
        {!isOpen && (
          <motion.div
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            drag
            dragControls={dragControls}
            dragMomentum={false}
            onDragEnd={handleDragEnd}
            style={{ 
              position: 'fixed', 
              left: position.x, 
              top: position.y,
              zIndex: 9999 
            }}
            className="cursor-grab active:cursor-grabbing"
          >
            <motion.button
              onClick={() => setIsOpen(true)}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              className="w-14 h-14 rounded-full bg-gradient-to-br from-primary-500 to-primary-700 text-white shadow-2xl flex items-center justify-center hover:shadow-primary-500/50 transition-shadow group"
            >
              <MessageSquare className="w-6 h-6 group-hover:scale-110 transition-transform" />
            </motion.button>
            <div className="absolute inset-0 rounded-full bg-primary-500 animate-ping opacity-25" />
            
            {/* Quick action buttons */}
            <motion.div 
              initial={{ opacity: 0, scale: 0.8 }}
              whileHover={{ opacity: 1, scale: 1 }}
              className="absolute -top-2 -right-2 flex gap-1"
            >
              <button 
                onClick={(e) => { e.stopPropagation(); setIsOpen(true); setCurrentPage('chat'); }}
                className="w-6 h-6 rounded-full bg-green-500 text-white flex items-center justify-center shadow-lg hover:bg-green-600 transition-colors"
              >
                <Zap className="w-3 h-3" />
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Widget Panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ 
              opacity: 1, 
              scale: 1, 
              y: 0,
              ...getWidgetSize(),
            }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            drag={!isFullscreen}
            dragControls={dragControls}
            dragMomentum={false}
            dragListener={false}
            style={{ 
              position: 'fixed',
              right: isFullscreen ? 0 : 20,
              bottom: isFullscreen ? 0 : 20,
              zIndex: 9999,
              borderRadius: isFullscreen ? 0 : 16
            }}
            className="bg-card border border-border shadow-2xl overflow-hidden flex"
          >
            {/* Mini Sidebar */}
            <motion.div 
              animate={{ width: sidebarCollapsed ? 48 : 160 }}
              className="bg-muted/50 border-r border-border flex flex-col"
            >
              {/* Sidebar Toggle */}
              <button
                onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                className="p-2 hover:bg-accent m-1 rounded-lg transition-colors"
              >
                {sidebarCollapsed ? <PanelRight className="w-4 h-4" /> : <PanelLeft className="w-4 h-4" />}
              </button>
              
              {/* Navigation */}
              <div className="flex-1 flex flex-col gap-0.5 p-1 overflow-y-auto">
                {WIDGET_PAGES.map((page) => (
                  <button
                    key={page.id}
                    onClick={() => navigateTo(page.id)}
                    className={cn(
                      "flex items-center gap-2 px-2 py-2 rounded-lg transition-all text-sm",
                      currentPage === page.id 
                        ? "bg-primary-500 text-white" 
                        : "text-muted-foreground hover:bg-accent hover:text-foreground"
                    )}
                  >
                    <page.icon className="w-4 h-4 shrink-0" />
                    {!sidebarCollapsed && (
                      <span className="truncate">{page.label[language as 'tr' | 'en']}</span>
                    )}
                  </button>
                ))}
              </div>
              
              {/* Open in Main App */}
              <button
                onClick={openInMainApp}
                className="flex items-center gap-2 px-2 py-2 m-1 rounded-lg text-xs text-muted-foreground hover:bg-accent hover:text-foreground transition-all"
              >
                <ExternalLink className="w-4 h-4 shrink-0" />
                {!sidebarCollapsed && <span>{language === 'tr' ? 'Tam Ekran' : 'Full App'}</span>}
              </button>
            </motion.div>

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col min-w-0">
              {/* Header */}
              <div 
                onPointerDown={(e) => !isFullscreen && dragControls.start(e)}
                className="flex items-center justify-between px-3 py-2 bg-gradient-to-r from-primary-500 to-primary-600 text-white cursor-grab active:cursor-grabbing"
              >
                <div className="flex items-center gap-2">
                  {pageHistory.length > 1 && (
                    <button onClick={goBack} className="p-1 hover:bg-white/20 rounded transition-colors">
                      <ChevronLeft className="w-4 h-4" />
                    </button>
                  )}
                  <GripVertical className="w-4 h-4 opacity-50" />
                  <Sparkles className="w-4 h-4" />
                  <span className="font-medium text-sm">{renderPageTitle()}</span>
                </div>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => setIsMinimized(!isMinimized)}
                    className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
                  >
                    <Minimize2 className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setIsExpanded(!isExpanded)}
                    className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
                  >
                    <Maximize2 className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setIsFullscreen(!isFullscreen)}
                    className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
                  >
                    <Monitor className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setIsOpen(false)}
                    className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Content */}
              {!isMinimized && (
                <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
                  
                  {/* ========== HOME PAGE ========== */}
                  {currentPage === 'home' && (
                    <div className="flex-1 overflow-y-auto p-4">
                      {/* Welcome */}
                      <div className="text-center mb-6">
                        <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary-500/20 to-primary-600/20 flex items-center justify-center mx-auto mb-3">
                          <Sparkles className="w-8 h-8 text-primary-500" />
                        </div>
                        <h2 className="text-lg font-semibold">
                          {language === 'tr' ? 'Hoş Geldiniz!' : 'Welcome!'}
                        </h2>
                        <p className="text-sm text-muted-foreground mt-1">
                          {language === 'tr' 
                            ? 'AI Asistanınız hazır. Ne yapmak istersiniz?' 
                            : 'Your AI Assistant is ready. What would you like to do?'}
                        </p>
                      </div>
                      
                      {/* Quick Actions Grid */}
                      <div className="grid grid-cols-2 gap-3">
                        {[
                          { icon: MessageSquare, label: language === 'tr' ? 'Sohbet Başlat' : 'Start Chat', page: 'chat' as WidgetPage, color: 'from-blue-500 to-blue-600' },
                          { icon: Upload, label: language === 'tr' ? 'Belge Yükle' : 'Upload Doc', page: 'documents' as WidgetPage, color: 'from-green-500 to-green-600' },
                          { icon: Brain, label: language === 'tr' ? 'RAG Sorgula' : 'RAG Query', page: 'rag' as WidgetPage, color: 'from-purple-500 to-purple-600' },
                          { icon: SearchIcon, label: language === 'tr' ? 'Arama Yap' : 'Search', page: 'search' as WidgetPage, color: 'from-orange-500 to-orange-600' },
                        ].map((action, i) => (
                          <button
                            key={i}
                            onClick={() => navigateTo(action.page)}
                            className="flex flex-col items-center gap-2 p-4 rounded-xl bg-muted hover:bg-accent transition-all group"
                          >
                            <div className={cn("w-10 h-10 rounded-xl bg-gradient-to-br flex items-center justify-center text-white", action.color)}>
                              <action.icon className="w-5 h-5" />
                            </div>
                            <span className="text-xs font-medium">{action.label}</span>
                          </button>
                        ))}
                      </div>
                      
                      {/* Recent Activity */}
                      <div className="mt-6">
                        <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
                          <Clock className="w-4 h-4 text-muted-foreground" />
                          {language === 'tr' ? 'Son Aktivite' : 'Recent Activity'}
                        </h3>
                        <div className="space-y-2">
                          {messages.slice(-3).reverse().map((msg, i) => (
                            <div key={i} className="p-2 bg-muted rounded-lg text-xs truncate">
                              <span className={msg.role === 'user' ? 'text-primary-500' : 'text-muted-foreground'}>
                                {msg.role === 'user' ? '👤' : '🤖'} {msg.content.slice(0, 50)}...
                              </span>
                            </div>
                          ))}
                          {messages.length === 0 && (
                            <p className="text-xs text-muted-foreground text-center py-4">
                              {language === 'tr' ? 'Henüz aktivite yok' : 'No activity yet'}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* ========== CHAT PAGE ========== */}
                  {currentPage === 'chat' && (
                    <>
                      {/* Messages */}
                      <div className="flex-1 overflow-y-auto p-3 space-y-3 min-h-0">
                        {messages.length === 0 && (
                          <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground py-8">
                            <MessageCircle className="w-12 h-12 mb-3 opacity-30" />
                            <p className="text-sm">
                              {language === 'tr' ? 'Sohbete başlamak için bir mesaj yazın' : 'Type a message to start chatting'}
                            </p>
                          </div>
                        )}

                        {messages.map((message) => (
                          <motion.div
                            key={message.id}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className={cn("flex", message.role === 'user' ? 'justify-end' : 'justify-start')}
                          >
                            <div
                              className={cn(
                                "max-w-[85%] px-3 py-2 rounded-2xl text-sm group relative",
                                message.role === 'user'
                                  ? 'bg-primary-500 text-white rounded-br-md'
                                  : 'bg-muted rounded-bl-md'
                              )}
                            >
                              <p className="whitespace-pre-wrap">{message.content}</p>
                              
                              {/* Sources */}
                              {message.sources && message.sources.length > 0 && (
                                <div className="mt-2 pt-2 border-t border-white/20 space-y-1">
                                  {message.sources.map((src, i) => (
                                    <a 
                                      key={i}
                                      href={src.url} 
                                      target="_blank" 
                                      rel="noopener noreferrer"
                                      className="text-xs flex items-center gap-1 opacity-70 hover:opacity-100"
                                    >
                                      <ExternalLink className="w-3 h-3" />
                                      {src.title}
                                    </a>
                                  ))}
                                </div>
                              )}
                              
                              {/* Copy button */}
                              <button
                                onClick={() => copyToClipboard(message.content)}
                                className="absolute -right-8 top-1 opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-accent transition-all"
                              >
                                <Copy className="w-3 h-3" />
                              </button>
                              
                              <p className={cn(
                                "text-[10px] mt-1",
                                message.role === 'user' ? 'text-white/70' : 'text-muted-foreground'
                              )}>
                                {new Date(message.timestamp).toLocaleTimeString(language === 'tr' ? 'tr-TR' : 'en-US', {
                                  hour: '2-digit',
                                  minute: '2-digit'
                                })}
                              </p>
                            </div>
                          </motion.div>
                        ))}

                        {isLoading && (
                          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex justify-start">
                            <div className="bg-muted px-4 py-3 rounded-2xl rounded-bl-md">
                              <div className="flex items-center gap-2">
                                <Loader2 className="w-4 h-4 animate-spin text-primary-500" />
                                <span className="text-sm text-muted-foreground">
                                  {language === 'tr' ? 'Düşünüyor...' : 'Thinking...'}
                                </span>
                              </div>
                            </div>
                          </motion.div>
                        )}

                        <div ref={messagesEndRef} />
                      </div>

                      {/* Input Area */}
                      <div className="p-3 border-t border-border bg-background">
                        <div className="flex items-center gap-1.5 mb-2 flex-wrap">
                          <button
                            onClick={() => setWebSearchEnabled(!webSearchEnabled)}
                            className={cn(
                              "flex items-center gap-1 px-2 py-1 rounded-lg text-xs transition-all",
                              webSearchEnabled ? "bg-blue-500 text-white" : "bg-muted text-muted-foreground hover:bg-accent"
                            )}
                          >
                            <Globe className="w-3 h-3" />
                            Web
                          </button>
                          <button
                            onClick={() => setRagEnabled(!ragEnabled)}
                            className={cn(
                              "flex items-center gap-1 px-2 py-1 rounded-lg text-xs transition-all",
                              ragEnabled ? "bg-purple-500 text-white" : "bg-muted text-muted-foreground hover:bg-accent"
                            )}
                          >
                            <Brain className="w-3 h-3" />
                            RAG
                          </button>
                          <button className="p-1.5 rounded-lg bg-muted text-muted-foreground hover:bg-accent transition-colors">
                            <ImageIcon className="w-3.5 h-3.5" />
                          </button>
                          <button 
                            onClick={() => fileInputRef.current?.click()}
                            className="p-1.5 rounded-lg bg-muted text-muted-foreground hover:bg-accent transition-colors"
                          >
                            <Paperclip className="w-3.5 h-3.5" />
                          </button>
                          <button className="p-1.5 rounded-lg bg-muted text-muted-foreground hover:bg-accent transition-colors">
                            <Mic className="w-3.5 h-3.5" />
                          </button>
                        </div>
                        
                        <div className="flex items-end gap-2">
                          <textarea
                            ref={inputRef}
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder={language === 'tr' ? 'Mesajınızı yazın...' : 'Type your message...'}
                            rows={1}
                            className="flex-1 resize-none bg-muted border-0 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/50 max-h-20"
                          />
                          <button
                            onClick={handleSend}
                            disabled={!input.trim() || isLoading}
                            className="w-9 h-9 flex items-center justify-center rounded-xl bg-primary-500 text-white hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                          >
                            <Send className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                      
                      <input
                        ref={fileInputRef}
                        type="file"
                        multiple
                        accept=".pdf,.docx,.txt,.md"
                        onChange={(e) => handleFileUpload(e.target.files)}
                        className="hidden"
                      />
                    </>
                  )}

                  {/* ========== DOCUMENTS PAGE ========== */}
                  {currentPage === 'documents' && (
                    <div className="flex-1 overflow-y-auto p-3">
                      {/* Upload Area */}
                      <div 
                        onClick={() => fileInputRef.current?.click()}
                        className="border-2 border-dashed border-border rounded-xl p-6 text-center cursor-pointer hover:border-primary-500 hover:bg-primary-500/5 transition-all mb-4"
                      >
                        <Upload className="w-8 h-8 mx-auto mb-2 text-muted-foreground" />
                        <p className="text-sm font-medium">
                          {language === 'tr' ? 'Dosya yüklemek için tıklayın' : 'Click to upload files'}
                        </p>
                        <p className="text-xs text-muted-foreground mt-1">
                          PDF, DOCX, TXT, MD
                        </p>
                      </div>
                      
                      {/* Upload Progress */}
                      {isUploading && (
                        <div className="mb-4">
                          <div className="flex items-center justify-between text-xs mb-1">
                            <span>{language === 'tr' ? 'Yükleniyor...' : 'Uploading...'}</span>
                            <span>{Math.round(uploadProgress)}%</span>
                          </div>
                          <div className="h-2 bg-muted rounded-full overflow-hidden">
                            <motion.div 
                              className="h-full bg-primary-500"
                              initial={{ width: 0 }}
                              animate={{ width: `${uploadProgress}%` }}
                            />
                          </div>
                        </div>
                      )}
                      
                      {/* Documents List */}
                      <div className="space-y-2">
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="text-sm font-medium">
                            {language === 'tr' ? 'Yüklü Belgeler' : 'Uploaded Documents'}
                          </h3>
                          <button onClick={fetchDocuments} className="p-1 hover:bg-accent rounded">
                            <RefreshCw className="w-4 h-4" />
                          </button>
                        </div>
                        
                        {documents.length === 0 ? (
                          <p className="text-sm text-muted-foreground text-center py-6">
                            {language === 'tr' ? 'Henüz belge yok' : 'No documents yet'}
                          </p>
                        ) : (
                          documents.map((doc) => (
                            <div key={doc.id} className="flex items-center gap-3 p-3 bg-muted rounded-lg group">
                              <FileText className="w-8 h-8 text-primary-500" />
                              <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium truncate">{doc.name}</p>
                                <p className="text-xs text-muted-foreground">
                                  {(doc.size / 1024).toFixed(1)} KB • {doc.chunks} chunks
                                </p>
                              </div>
                              <button 
                                onClick={() => deleteDocument(doc.id)}
                                className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-red-500/20 rounded text-red-500 transition-all"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          ))
                        )}
                      </div>
                      
                      <input
                        ref={fileInputRef}
                        type="file"
                        multiple
                        accept=".pdf,.docx,.txt,.md"
                        onChange={(e) => handleFileUpload(e.target.files)}
                        className="hidden"
                      />
                    </div>
                  )}

                  {/* ========== RAG PAGE ========== */}
                  {currentPage === 'rag' && (
                    <div className="flex-1 overflow-y-auto p-3">
                      <div className="space-y-4">
                        {/* RAG Query Input */}
                        <div>
                          <label className="text-sm font-medium mb-2 block">
                            {language === 'tr' ? 'RAG Sorgusu' : 'RAG Query'}
                          </label>
                          <div className="flex gap-2">
                            <input
                              type="text"
                              value={searchQuery}
                              onChange={(e) => setSearchQuery(e.target.value)}
                              placeholder={language === 'tr' ? 'Belgelerinizde arama yapın...' : 'Search in your documents...'}
                              className="flex-1 bg-muted rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/50"
                            />
                            <button 
                              onClick={handleSearch}
                              disabled={isSearching}
                              className="px-4 py-2 bg-primary-500 text-white rounded-xl hover:bg-primary-600 disabled:opacity-50 transition-colors"
                            >
                              {isSearching ? <Loader2 className="w-4 h-4 animate-spin" /> : <SearchIcon className="w-4 h-4" />}
                            </button>
                          </div>
                        </div>
                        
                        {/* RAG Settings */}
                        <div className="grid grid-cols-2 gap-3">
                          <div className="p-3 bg-muted rounded-lg">
                            <div className="flex items-center gap-2 mb-2">
                              <Database className="w-4 h-4 text-primary-500" />
                              <span className="text-xs font-medium">{language === 'tr' ? 'Strateji' : 'Strategy'}</span>
                            </div>
                            <select className="w-full bg-background rounded px-2 py-1 text-xs">
                              <option>Naive RAG</option>
                              <option>HyDE</option>
                              <option>Fusion RAG</option>
                              <option>Rerank</option>
                            </select>
                          </div>
                          <div className="p-3 bg-muted rounded-lg">
                            <div className="flex items-center gap-2 mb-2">
                              <Layers className="w-4 h-4 text-primary-500" />
                              <span className="text-xs font-medium">{language === 'tr' ? 'Top K' : 'Top K'}</span>
                            </div>
                            <input 
                              type="number" 
                              defaultValue={5} 
                              min={1} 
                              max={20}
                              className="w-full bg-background rounded px-2 py-1 text-xs"
                            />
                          </div>
                        </div>
                        
                        {/* Search Results */}
                        {searchResults.length > 0 && (
                          <div>
                            <h3 className="text-sm font-medium mb-2">{language === 'tr' ? 'Sonuçlar' : 'Results'}</h3>
                            <div className="space-y-2">
                              {searchResults.map((result, i) => (
                                <div key={i} className="p-3 bg-muted rounded-lg">
                                  <p className="text-sm">{result.content?.slice(0, 200)}...</p>
                                  <p className="text-xs text-muted-foreground mt-1">
                                    Score: {(result.score * 100).toFixed(1)}%
                                  </p>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* ========== HISTORY PAGE ========== */}
                  {currentPage === 'history' && (
                    <div className="flex-1 overflow-y-auto p-3">
                      <div className="flex items-center justify-between mb-3">
                        <h3 className="text-sm font-medium">{language === 'tr' ? 'Sohbet Geçmişi' : 'Chat History'}</h3>
                        <button onClick={fetchConversationHistory} className="p-1 hover:bg-accent rounded">
                          <RefreshCw className="w-4 h-4" />
                        </button>
                      </div>
                      
                      {conversationHistory.length === 0 ? (
                        <div className="text-center py-8 text-muted-foreground">
                          <History className="w-12 h-12 mx-auto mb-3 opacity-30" />
                          <p className="text-sm">{language === 'tr' ? 'Henüz geçmiş yok' : 'No history yet'}</p>
                        </div>
                      ) : (
                        <div className="space-y-2">
                          {conversationHistory.map((conv) => (
                            <div key={conv.id} className="p-3 bg-muted rounded-lg hover:bg-accent cursor-pointer transition-colors">
                              <p className="text-sm font-medium truncate">{conv.title}</p>
                              <p className="text-xs text-muted-foreground truncate">{conv.lastMessage}</p>
                              <p className="text-xs text-muted-foreground mt-1">
                                {new Date(conv.timestamp).toLocaleDateString()}
                              </p>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {/* ========== SEARCH PAGE ========== */}
                  {currentPage === 'search' && (
                    <div className="flex-1 overflow-y-auto p-3">
                      <div className="relative mb-4">
                        <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                        <input
                          type="text"
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                          placeholder={language === 'tr' ? 'Belge veya sohbet ara...' : 'Search documents or chats...'}
                          className="w-full pl-10 pr-4 py-2.5 bg-muted rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/50"
                        />
                      </div>
                      
                      {isSearching ? (
                        <div className="text-center py-8">
                          <Loader2 className="w-8 h-8 animate-spin mx-auto text-primary-500" />
                        </div>
                      ) : searchResults.length > 0 ? (
                        <div className="space-y-2">
                          {searchResults.map((result, i) => (
                            <div key={i} className="p-3 bg-muted rounded-lg">
                              <p className="text-sm">{result.content?.slice(0, 150)}...</p>
                              <div className="flex items-center gap-2 mt-2">
                                <span className="text-xs text-muted-foreground">{result.source}</span>
                                <span className="text-xs bg-primary-500/20 text-primary-500 px-2 py-0.5 rounded">
                                  {(result.score * 100).toFixed(0)}%
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-center py-8 text-muted-foreground">
                          <FileSearch className="w-12 h-12 mx-auto mb-3 opacity-30" />
                          <p className="text-sm">{language === 'tr' ? 'Arama yapmak için yazın' : 'Type to search'}</p>
                        </div>
                      )}
                    </div>
                  )}

                  {/* ========== ANALYTICS PAGE ========== */}
                  {currentPage === 'analytics' && (
                    <div className="flex-1 overflow-y-auto p-3">
                      <div className="grid grid-cols-2 gap-3">
                        {/* Stats Cards */}
                        {[
                          { icon: Cpu, label: 'CPU', value: `${systemStats?.cpu || 0}%`, color: 'text-blue-500' },
                          { icon: HardDrive, label: 'Memory', value: `${systemStats?.memory || 0}%`, color: 'text-green-500' },
                          { icon: FileText, label: language === 'tr' ? 'Belgeler' : 'Documents', value: systemStats?.documents || 0, color: 'text-purple-500' },
                          { icon: Database, label: 'Chunks', value: systemStats?.chunks || 0, color: 'text-orange-500' },
                        ].map((stat, i) => (
                          <div key={i} className="p-3 bg-muted rounded-xl">
                            <div className="flex items-center gap-2 mb-1">
                              <stat.icon className={cn("w-4 h-4", stat.color)} />
                              <span className="text-xs text-muted-foreground">{stat.label}</span>
                            </div>
                            <p className="text-lg font-bold">{stat.value}</p>
                          </div>
                        ))}
                      </div>
                      
                      {/* Activity Chart Placeholder */}
                      <div className="mt-4 p-4 bg-muted rounded-xl">
                        <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
                          <Activity className="w-4 h-4" />
                          {language === 'tr' ? 'Aktivite' : 'Activity'}
                        </h3>
                        <div className="h-24 flex items-end gap-1">
                          {Array.from({ length: 12 }).map((_, i) => (
                            <div 
                              key={i}
                              className="flex-1 bg-primary-500/50 rounded-t"
                              style={{ height: `${Math.random() * 100}%` }}
                            />
                          ))}
                        </div>
                      </div>
                      
                      {/* System Info */}
                      <div className="mt-4 p-3 bg-muted rounded-xl">
                        <h3 className="text-sm font-medium mb-2">{language === 'tr' ? 'Sistem Bilgisi' : 'System Info'}</h3>
                        <div className="space-y-1 text-xs text-muted-foreground">
                          <div className="flex justify-between">
                            <span>Uptime:</span>
                            <span>{systemStats?.uptime || 'N/A'}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Version:</span>
                            <span>Enterprise AI v2.0</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* ========== SETTINGS PAGE ========== */}
                  {currentPage === 'settings' && (
                    <div className="flex-1 overflow-y-auto p-3 space-y-4">
                      {/* Theme */}
                      <div className="p-3 bg-muted rounded-xl">
                        <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
                          <Sun className="w-4 h-4" />
                          {language === 'tr' ? 'Tema' : 'Theme'}
                        </h3>
                        <div className="flex gap-2">
                          {['light', 'dark', 'ocean'].map((t) => (
                            <button
                              key={t}
                              onClick={() => setTheme(t as any)}
                              className={cn(
                                "flex-1 py-2 rounded-lg text-xs font-medium transition-all",
                                theme === t ? "bg-primary-500 text-white" : "bg-background hover:bg-accent"
                              )}
                            >
                              {t === 'light' ? '☀️' : t === 'dark' ? '🌙' : '🌊'} {t.charAt(0).toUpperCase() + t.slice(1)}
                            </button>
                          ))}
                        </div>
                      </div>
                      
                      {/* Toggles */}
                      <div className="space-y-2">
                        {[
                          { icon: Volume2, label: language === 'tr' ? 'Ses' : 'Sound', value: soundEnabled, setter: setSoundEnabled },
                          { icon: Bell, label: language === 'tr' ? 'Bildirimler' : 'Notifications', value: notificationsEnabled, setter: setNotificationsEnabled },
                          { icon: ArrowUpRight, label: 'Auto Scroll', value: autoScroll, setter: setAutoScroll },
                        ].map((setting, i) => (
                          <div key={i} className="flex items-center justify-between p-3 bg-muted rounded-xl">
                            <div className="flex items-center gap-2">
                              <setting.icon className="w-4 h-4 text-muted-foreground" />
                              <span className="text-sm">{setting.label}</span>
                            </div>
                            <button
                              onClick={() => setting.setter(!setting.value)}
                              className={cn(
                                "w-10 h-6 rounded-full transition-colors relative",
                                setting.value ? "bg-primary-500" : "bg-muted-foreground/30"
                              )}
                            >
                              <motion.div 
                                className="w-4 h-4 bg-white rounded-full absolute top-1"
                                animate={{ left: setting.value ? 22 : 4 }}
                              />
                            </button>
                          </div>
                        ))}
                      </div>
                      
                      {/* Disable Widget */}
                      <button
                        onClick={toggleWidget}
                        className="w-full p-3 bg-red-500/10 text-red-500 rounded-xl text-sm font-medium hover:bg-red-500/20 transition-colors"
                      >
                        {language === 'tr' ? 'Widget\'ı Kapat' : 'Disable Widget'}
                      </button>
                    </div>
                  )}

                </div>
              )}

              {/* Minimized Footer */}
              {isMinimized && (
                <div className="px-3 py-2 text-xs text-muted-foreground text-center">
                  {language === 'tr' ? 'Genişletmek için tıklayın' : 'Click to expand'}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
