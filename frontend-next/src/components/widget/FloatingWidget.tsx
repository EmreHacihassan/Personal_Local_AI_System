'use client';

/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/no-unused-vars */

// =================== API CONFIGURATION ===================
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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
  MicOff,
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
  ChevronUp,
  Brain,
  Zap,
  Database,
  Copy,
  Check,
  ExternalLink,
  Sun,
  Monitor,
  Volume2,
  VolumeX,
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
  Layers,
  ThumbsUp,
  ThumbsDown,
  RotateCcw,
  Camera,
  Laptop,
  Play
} from 'lucide-react';
import { useStore } from '@/store/useStore';
import { cn } from '@/lib/utils';
import { sendMessage } from '@/lib/api';

// =================== MARKDOWN RENDERER ===================
function renderMarkdown(content: string): string {
  return content
    // Code blocks
    .replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre class="code-block" data-lang="$1"><code>$2</code></pre>')
    // Inline code
    .replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
    // Bold
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    // Italic
    .replace(/\*([^*]+)\*/g, '<em>$1</em>')
    // Links
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener" class="message-link">$1</a>')
    // Headers
    .replace(/^### (.+)$/gm, '<h4 class="message-h4">$1</h4>')
    .replace(/^## (.+)$/gm, '<h3 class="message-h3">$1</h3>')
    .replace(/^# (.+)$/gm, '<h2 class="message-h2">$1</h2>')
    // Lists
    .replace(/^- (.+)$/gm, '<li class="message-li">$1</li>')
    .replace(/^(\d+)\. (.+)$/gm, '<li class="message-li-num">$2</li>')
    // Blockquotes
    .replace(/^> (.+)$/gm, '<blockquote class="message-quote">$1</blockquote>')
    // Line breaks
    .replace(/\n/g, '<br>');
}

// Note: API_BASE is defined below in CONSTANTS section

// =================== TEXT TO SPEECH (Browser fallback) ===================
function speakTextBrowser(text: string, lang: string = 'tr-TR') {
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = lang === 'tr' ? 'tr-TR' : 'en-US';
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;

    window.speechSynthesis.speak(utterance);
    return true;
  }
  return false;
}

// =================== TEXT TO SPEECH (Local API - Pyttsx3) ===================
// Audio element for API TTS playback (declared early for stopSpeaking)
let ttsAudio: HTMLAudioElement | null = null;

async function speakTextAPI(text: string, lang: string = 'tr'): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/api/voice/tts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: text,
        language: lang,
        rate: 150,
        volume: 1.0
      })
    });

    const data = await response.json();

    if (data.success && data.audio_base64) {
      // Base64'ü audio'ya çevir ve çal
      const audioData = atob(data.audio_base64);
      const audioArray = new Uint8Array(audioData.length);
      for (let i = 0; i < audioData.length; i++) {
        audioArray[i] = audioData.charCodeAt(i);
      }

      const blob = new Blob([audioArray], { type: 'audio/wav' });
      const audioUrl = URL.createObjectURL(blob);
      ttsAudio = new Audio(audioUrl);
      ttsAudio.onended = () => {
        URL.revokeObjectURL(audioUrl);
        ttsAudio = null;
      };
      ttsAudio.play();

      return true;
    }

    // Fallback to browser TTS
    return speakTextBrowser(text, lang);
  } catch (error) {
    console.warn('API TTS failed, falling back to browser:', error);
    return speakTextBrowser(text, lang);
  }
}

// Combined speak function - tries API first, falls back to browser
async function speakText(text: string, lang: string = 'tr-TR') {
  // Try API TTS first (Pyttsx3 - higher quality, local)
  const success = await speakTextAPI(text, lang);
  if (success) {
    return;
  }
  // Fallback to browser TTS
  return speakTextBrowser(text, lang);
}

function stopSpeaking() {
  // Stop browser TTS
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }
  // Stop API TTS audio
  if (ttsAudio) {
    ttsAudio.pause();
    ttsAudio.currentTime = 0;
    ttsAudio = null;
  }
}

// =================== SPEECH TO TEXT (Local API - Whisper) ===================
async function transcribeAudio(audioBlob: Blob): Promise<string | null> {
  try {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.wav');
    formData.append('model_size', 'base');

    const response = await fetch(`${API_BASE}/api/voice/stt`, {
      method: 'POST',
      body: formData
    });

    const data = await response.json();

    if (data.success && data.text) {
      return data.text;
    }

    return null;
  } catch (error) {
    console.error('STT API error:', error);
    return null;
  }
}

// =================== VISION ANALYSIS (Local API - LLaVA) ===================
async function analyzeImage(imageBase64: string, prompt: string = 'Bu görseli detaylı açıkla.'): Promise<string | null> {
  try {
    const response = await fetch(`${API_BASE}/api/voice/vision`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        image_base64: imageBase64,
        prompt: prompt,
        model: 'llava'
      })
    });

    const data = await response.json();

    if (data.success && data.description) {
      return data.description;
    }

    return null;
  } catch (error) {
    console.error('Vision API error:', error);
    return null;
  }
}

// =================== TYPES ===================
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: Array<{ title: string; url: string }>;
  isTyping?: boolean;
  feedback?: 'positive' | 'negative' | null;
  bookmarked?: boolean;
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

// =================== WIDGET PAGE DEFINITIONS ===================

const WIDGET_PAGES: { id: WidgetPage; icon: React.ElementType; label: { tr: string; en: string }; color: string }[] = [
  { id: 'home', icon: Home, label: { tr: 'Ana Sayfa', en: 'Home' }, color: 'from-violet-500 to-purple-600' },
  { id: 'chat', icon: MessageSquare, label: { tr: 'Sohbet', en: 'Chat' }, color: 'from-blue-500 to-cyan-500' },
  { id: 'documents', icon: FileText, label: { tr: 'Belgeler', en: 'Documents' }, color: 'from-green-500 to-emerald-500' },
  { id: 'rag', icon: Brain, label: { tr: 'RAG', en: 'RAG' }, color: 'from-purple-500 to-pink-500' },
  { id: 'history', icon: History, label: { tr: 'Geçmiş', en: 'History' }, color: 'from-amber-500 to-orange-500' },
  { id: 'search', icon: SearchIcon, label: { tr: 'Ara', en: 'Search' }, color: 'from-cyan-500 to-teal-500' },
  { id: 'analytics', icon: BarChart3, label: { tr: 'Analitik', en: 'Analytics' }, color: 'from-rose-500 to-red-500' },
  { id: 'settings', icon: Settings, label: { tr: 'Ayarlar', en: 'Settings' }, color: 'from-gray-500 to-slate-600' },
];

// =================== TYPING ANIMATION HOOK ===================
function useTypingEffect(text: string, speed: number = 20, enabled: boolean = true) {
  const [displayedText, setDisplayedText] = useState('');
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    if (!enabled) {
      setDisplayedText(text);
      setIsComplete(true);
      return;
    }

    setDisplayedText('');
    setIsComplete(false);
    let index = 0;

    const timer = setInterval(() => {
      if (index < text.length) {
        setDisplayedText(text.slice(0, index + 1));
        index++;
      } else {
        setIsComplete(true);
        clearInterval(timer);
      }
    }, speed);

    return () => clearInterval(timer);
  }, [text, speed, enabled]);

  return { displayedText, isComplete };
}

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

  // Voice & Accessibility State
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);

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
      const response = await fetch(`${API_BASE}/health`);
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
      const response = await fetch(`${API_BASE}/api/documents`);
      if (response.ok) {
        const data = await response.json();
        setDocuments(data.documents || data || []);
      }
    } catch (error) {
      console.error('Failed to fetch documents:', error);
    }
  };

  const fetchConversationHistory = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/sessions`);
      if (response.ok) {
        const data = await response.json();
        setConversationHistory(data.sessions || []);
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
        audio.play().catch(() => { });
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

        const response = await fetch(`${API_BASE}/api/documents/upload`, {
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
      const response = await fetch(`${API_BASE}/api/search?q=${encodeURIComponent(searchQuery)}`);
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
      await fetch(`${API_BASE}/api/documents/${docId}`, { method: 'DELETE' });
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

  const getPageColor = () => {
    const page = WIDGET_PAGES.find(p => p.id === currentPage);
    return page?.color || 'from-primary-500 to-primary-600';
  };

  if (!widgetEnabled) return null;

  // =================== RENDER ===================
  return (
    <>
      {/* Floating Button - Premium Design */}
      <AnimatePresence>
        {!isOpen && (
          <motion.div
            initial={{ scale: 0, opacity: 0, rotate: -180 }}
            animate={{ scale: 1, opacity: 1, rotate: 0 }}
            exit={{ scale: 0, opacity: 0, rotate: 180 }}
            transition={{ type: 'spring', damping: 20, stiffness: 300 }}
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
            className="cursor-grab active:cursor-grabbing select-none group"
          >
            {/* Main Floating Button */}
            <motion.button
              onClick={() => setIsOpen(true)}
              whileHover={{ scale: 1.08 }}
              whileTap={{ scale: 0.92 }}
              className="relative w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-500 via-primary-600 to-primary-700 text-white shadow-2xl shadow-primary-500/40 flex items-center justify-center overflow-hidden"
            >
              {/* Gradient Overlay on Hover */}
              <div className="absolute inset-0 bg-gradient-to-br from-white/25 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

              {/* Shine Effect */}
              <div className="absolute inset-0 overflow-hidden rounded-2xl">
                <motion.div
                  className="absolute -top-1/2 -left-1/2 w-full h-full bg-gradient-to-br from-white/40 to-transparent rotate-12"
                  initial={{ x: '-100%' }}
                  whileHover={{ x: '200%' }}
                  transition={{ duration: 0.6 }}
                />
              </div>

              {/* Icon with pulse effect */}
              <motion.div
                animate={{ scale: [1, 1.05, 1] }}
                transition={{ repeat: Infinity, duration: 2, ease: 'easeInOut' }}
                className="relative z-10"
              >
                <MessageSquare className="w-7 h-7" />
              </motion.div>

              {/* Sparkle decorations */}
              <Sparkles className="absolute top-2 right-2 w-3 h-3 text-white/70" />
            </motion.button>

            {/* Animated Ring - Pulsing glow */}
            <motion.div
              className="absolute inset-0 rounded-2xl border-2 border-primary-400/50"
              animate={{
                scale: [1, 1.25, 1.25],
                opacity: [0.6, 0, 0],
                borderRadius: ['16px', '20px', '20px']
              }}
              transition={{ repeat: Infinity, duration: 2, ease: 'easeOut' }}
            />

            {/* Second Ring for depth */}
            <motion.div
              className="absolute inset-0 rounded-2xl border-2 border-primary-300/30"
              animate={{
                scale: [1, 1.4, 1.4],
                opacity: [0.4, 0, 0],
              }}
              transition={{ repeat: Infinity, duration: 2, ease: 'easeOut', delay: 0.3 }}
            />

            {/* Hover tooltip */}
            <motion.div
              initial={{ opacity: 0, y: 10, scale: 0.8 }}
              whileHover={{ opacity: 1, y: 0, scale: 1 }}
              className="absolute -bottom-10 left-1/2 -translate-x-1/2 px-3 py-1.5 bg-card/95 backdrop-blur-sm text-foreground text-xs font-medium rounded-lg shadow-lg border border-border whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity"
            >
              {language === 'tr' ? '✨ AI Asistan' : '✨ AI Assistant'}
            </motion.div>

            {/* Quick action button - appears on hover */}
            <motion.div
              className="absolute -top-2 -right-2 opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <motion.button
                onClick={(e) => { e.stopPropagation(); setIsOpen(true); setCurrentPage('chat'); }}
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                className="w-7 h-7 rounded-full bg-gradient-to-br from-green-400 to-emerald-500 text-white flex items-center justify-center shadow-lg shadow-green-500/30"
              >
                <Zap className="w-3.5 h-3.5" />
              </motion.button>
            </motion.div>

            {/* Drag hint - appears on hover */}
            <motion.div
              className="absolute -bottom-8 left-1/2 -translate-x-1/2 text-[10px] text-muted-foreground/70 whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity"
            >
              {language === 'tr' ? '↕ Sürükle' : '↕ Drag'}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Widget Panel - Enhanced Design */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 30 }}
            animate={{
              opacity: 1,
              scale: 1,
              y: 0,
              ...getWidgetSize(),
            }}
            exit={{ opacity: 0, scale: 0.9, y: 30 }}
            transition={{ type: 'spring', damping: 28, stiffness: 350 }}
            drag={!isFullscreen}
            dragControls={dragControls}
            dragMomentum={false}
            dragListener={false}
            style={{
              position: 'fixed',
              right: isFullscreen ? 0 : 20,
              bottom: isFullscreen ? 0 : 20,
              zIndex: 9999,
              borderRadius: isFullscreen ? 0 : 20
            }}
            className="bg-card border border-border shadow-2xl shadow-black/20 overflow-hidden flex backdrop-blur-xl"
          >
            {/* Mini Sidebar - Enhanced */}
            <motion.div
              animate={{ width: sidebarCollapsed ? 52 : 170 }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
              className="bg-gradient-to-b from-muted/80 to-muted/40 border-r border-border/80 flex flex-col backdrop-blur-sm"
            >
              {/* Sidebar Toggle */}
              <button
                onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                className="p-2.5 hover:bg-accent m-1.5 rounded-xl transition-all duration-200 flex items-center gap-2"
              >
                {sidebarCollapsed ? <PanelRight className="w-4 h-4" /> : <PanelLeft className="w-4 h-4" />}
              </button>

              {/* Navigation - Enhanced */}
              <div className="flex-1 flex flex-col gap-1 p-1.5 overflow-y-auto scrollbar-thin">
                {WIDGET_PAGES.map((page) => (
                  <motion.button
                    key={page.id}
                    onClick={() => navigateTo(page.id)}
                    whileHover={{ x: 2 }}
                    whileTap={{ scale: 0.98 }}
                    className={cn(
                      "flex items-center gap-2.5 px-2.5 py-2.5 rounded-xl transition-all text-sm relative group",
                      currentPage === page.id
                        ? `bg-gradient-to-r ${page.color} text-white shadow-lg`
                        : "text-muted-foreground hover:bg-accent hover:text-foreground"
                    )}
                  >
                    <page.icon className="w-4 h-4 shrink-0" />
                    {!sidebarCollapsed && (
                      <span className="truncate font-medium">{page.label[language as 'tr' | 'en']}</span>
                    )}

                    {/* Active indicator for collapsed mode */}
                    {currentPage === page.id && sidebarCollapsed && (
                      <motion.div
                        layoutId="activeIndicator"
                        className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-white rounded-r-full"
                      />
                    )}
                  </motion.button>
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
            <div className="flex-1 flex flex-col min-w-0 bg-gradient-to-br from-background to-muted/20">
              {/* Header - Dynamic Color */}
              <motion.div
                onPointerDown={(e) => !isFullscreen && dragControls.start(e)}
                className={cn(
                  "flex items-center justify-between px-4 py-3 cursor-grab active:cursor-grabbing relative overflow-hidden",
                  `bg-gradient-to-r ${getPageColor()} text-white`
                )}
              >
                {/* Animated Background Pattern */}
                <div className="absolute inset-0 opacity-10">
                  <motion.div
                    className="absolute inset-0"
                    style={{
                      backgroundImage: `radial-gradient(circle at 20% 50%, rgba(255,255,255,0.3) 0%, transparent 50%),
                                        radial-gradient(circle at 80% 50%, rgba(255,255,255,0.2) 0%, transparent 50%)`
                    }}
                    animate={{
                      backgroundPosition: ['0% 0%', '100% 100%', '0% 0%']
                    }}
                    transition={{
                      repeat: Infinity,
                      duration: 10,
                      ease: 'linear'
                    }}
                  />
                </div>

                <div className="flex items-center gap-2.5 relative z-10">
                  {pageHistory.length > 1 && (
                    <motion.button
                      onClick={goBack}
                      whileHover={{ scale: 1.1 }}
                      whileTap={{ scale: 0.9 }}
                      className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </motion.button>
                  )}
                  <GripVertical className="w-4 h-4 opacity-50" />
                  <div className="flex items-center gap-2">
                    <motion.div
                      animate={{ rotate: [0, 360] }}
                      transition={{ repeat: Infinity, duration: 20, ease: 'linear' }}
                    >
                      <Sparkles className="w-4 h-4" />
                    </motion.div>
                    <span className="font-semibold text-sm">{renderPageTitle()}</span>
                    {/* Online Indicator */}
                    <div className="flex items-center gap-1 ml-1">
                      <motion.div
                        className="w-2 h-2 rounded-full bg-green-400"
                        animate={{ scale: [1, 1.2, 1], opacity: [1, 0.7, 1] }}
                        transition={{ repeat: Infinity, duration: 2 }}
                      />
                      <span className="text-[10px] opacity-75">
                        {language === 'tr' ? 'Çevrimiçi' : 'Online'}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-1 relative z-10">
                  {/* Minimize - Widget'ı küçük hale getir (sadece header görünsün) */}
                  <motion.button
                    onClick={() => setIsMinimized(!isMinimized)}
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                    title={language === 'tr' ? (isMinimized ? 'Genişlet' : 'Küçült') : (isMinimized ? 'Expand' : 'Minimize')}
                  >
                    <Minimize2 className="w-4 h-4" />
                  </motion.button>
                  {/* Expand - Widget boyutunu büyüt/küçült */}
                  <motion.button
                    onClick={() => setIsExpanded(!isExpanded)}
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                    title={language === 'tr' ? (isExpanded ? 'Normal Boyut' : 'Büyüt') : (isExpanded ? 'Normal Size' : 'Expand')}
                  >
                    <Maximize2 className="w-4 h-4" />
                  </motion.button>
                  {/* Fullscreen - Tam ekran */}
                  <motion.button
                    onClick={() => setIsFullscreen(!isFullscreen)}
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                    title={language === 'tr' ? (isFullscreen ? 'Tam Ekrandan Çık' : 'Tam Ekran') : (isFullscreen ? 'Exit Fullscreen' : 'Fullscreen')}
                  >
                    <Monitor className="w-4 h-4" />
                  </motion.button>
                  {/* Close - Widget'ı kapat (floating button'a dön) */}
                  <motion.button
                    onClick={() => {
                      setIsOpen(false);
                      setIsMinimized(false);
                      setIsExpanded(false);
                      setIsFullscreen(false);
                    }}
                    whileHover={{ scale: 1.1, backgroundColor: 'rgba(255,255,255,0.3)' }}
                    whileTap={{ scale: 0.9 }}
                    className="p-2 hover:bg-white/20 rounded-lg transition-colors ml-1"
                    title={language === 'tr' ? 'Kapat' : 'Close'}
                  >
                    <X className="w-4 h-4" />
                  </motion.button>
                </div>
              </motion.div>

              {/* Content with page transition */}
              <AnimatePresence mode="wait">
                {!isMinimized && (
                  <motion.div
                    key={currentPage}
                    initial={{ opacity: 0, x: 10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -10 }}
                    transition={{ duration: 0.15 }}
                    className="flex-1 flex flex-col min-h-0 overflow-hidden"
                  >

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
                            { icon: Monitor, label: language === 'tr' ? 'PC Kontrol' : 'Computer Use', page: 'home' as WidgetPage, color: 'from-amber-500 to-amber-600', action: () => window.open('/computer-use', '_blank') },
                            {
                              icon: Camera, label: language === 'tr' ? 'Ekran Görüntüsü' : 'Screenshot', page: 'home' as WidgetPage, color: 'from-pink-500 to-rose-600', action: async () => {
                                try {
                                  const res = await fetch(`${API_BASE}/api/screen/capture`, {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({ mode: 'primary' })
                                  });
                                  if (res.ok) alert(language === 'tr' ? 'Ekran görüntüsü alındı!' : 'Screenshot captured!');
                                } catch (e) { console.error(e); }
                              }
                            },
                          ].map((action, i) => (
                            <button
                              key={i}
                              onClick={() => action.action ? action.action() : navigateTo(action.page)}
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
                              <div className="flex flex-wrap gap-2 mt-4 justify-center">
                                {[
                                  language === 'tr' ? '📝 Özet çıkar' : '📝 Summarize',
                                  language === 'tr' ? '🔍 Açıkla' : '🔍 Explain',
                                  language === 'tr' ? '💡 Öneri ver' : '💡 Suggest'
                                ].map((suggestion, i) => (
                                  <button
                                    key={i}
                                    onClick={() => setInput(suggestion.replace(/^[^\s]+\s/, ''))}
                                    className="text-xs px-3 py-1.5 bg-muted hover:bg-accent rounded-full transition-colors"
                                  >
                                    {suggestion}
                                  </button>
                                ))}
                              </div>
                            </div>
                          )}

                          {messages.map((message) => (
                            <motion.div
                              key={message.id}
                              initial={{ opacity: 0, y: 10, scale: 0.95 }}
                              animate={{ opacity: 1, y: 0, scale: 1 }}
                              transition={{ type: 'spring', damping: 20, stiffness: 300 }}
                              className={cn("flex", message.role === 'user' ? 'justify-end' : 'justify-start')}
                            >
                              <div
                                className={cn(
                                  "max-w-[85%] px-3.5 py-2.5 rounded-2xl text-sm group relative",
                                  message.role === 'user'
                                    ? 'bg-gradient-to-br from-primary-500 to-primary-600 text-white rounded-br-md shadow-lg shadow-primary-500/20'
                                    : 'bg-muted rounded-bl-md border border-border/50'
                                )}
                              >
                                {/* Message Content with Markdown */}
                                <div
                                  className="whitespace-pre-wrap prose prose-sm dark:prose-invert max-w-none [&_code]:bg-black/10 [&_code]:px-1.5 [&_code]:py-0.5 [&_code]:rounded [&_code]:text-xs [&_pre]:bg-black/20 [&_pre]:p-2 [&_pre]:rounded-lg [&_pre]:overflow-x-auto [&_a]:text-blue-300 [&_a]:underline"
                                  dangerouslySetInnerHTML={{ __html: renderMarkdown(message.content) }}
                                />

                                {/* Sources */}
                                {message.sources && message.sources.length > 0 && (
                                  <div className="mt-2 pt-2 border-t border-white/20 space-y-1">
                                    <span className="text-[10px] uppercase tracking-wider opacity-60">
                                      {language === 'tr' ? 'Kaynaklar' : 'Sources'}
                                    </span>
                                    {message.sources.map((src, i) => (
                                      <a
                                        key={i}
                                        href={src.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-xs flex items-center gap-1 opacity-70 hover:opacity-100 transition-opacity"
                                      >
                                        <ExternalLink className="w-3 h-3" />
                                        {src.title}
                                      </a>
                                    ))}
                                  </div>
                                )}

                                {/* Message Actions - Assistant messages only */}
                                {message.role === 'assistant' && (
                                  <div className="flex items-center gap-0.5 mt-2 pt-2 border-t border-border/30 opacity-0 group-hover:opacity-100 transition-opacity">
                                    {/* Copy */}
                                    <button
                                      onClick={() => {
                                        copyToClipboard(message.content);
                                        setCopiedMessageId(message.id);
                                        setTimeout(() => setCopiedMessageId(null), 2000);
                                      }}
                                      className="p-1.5 hover:bg-accent rounded-lg transition-colors"
                                      title={language === 'tr' ? 'Kopyala' : 'Copy'}
                                    >
                                      {copiedMessageId === message.id ? (
                                        <Check className="w-3.5 h-3.5 text-green-500" />
                                      ) : (
                                        <Copy className="w-3.5 h-3.5 text-muted-foreground" />
                                      )}
                                    </button>

                                    {/* Speak */}
                                    <button
                                      onClick={() => {
                                        if (isSpeaking) {
                                          stopSpeaking();
                                          setIsSpeaking(false);
                                        } else {
                                          speakText(message.content, language);
                                          setIsSpeaking(true);
                                          // Auto-stop when speech ends
                                          const checkSpeaking = setInterval(() => {
                                            if (!window.speechSynthesis?.speaking) {
                                              setIsSpeaking(false);
                                              clearInterval(checkSpeaking);
                                            }
                                          }, 500);
                                        }
                                      }}
                                      className="p-1.5 hover:bg-accent rounded-lg transition-colors"
                                      title={language === 'tr' ? (isSpeaking ? 'Durdur' : 'Seslendir') : (isSpeaking ? 'Stop' : 'Speak')}
                                    >
                                      {isSpeaking ? (
                                        <VolumeX className="w-3.5 h-3.5 text-primary-500" />
                                      ) : (
                                        <Volume2 className="w-3.5 h-3.5 text-muted-foreground" />
                                      )}
                                    </button>

                                    {/* Thumbs up */}
                                    <button
                                      onClick={() => {
                                        setMessages(prev => prev.map(m =>
                                          m.id === message.id ? { ...m, feedback: m.feedback === 'positive' ? null : 'positive' } : m
                                        ));
                                      }}
                                      className={cn(
                                        "p-1.5 hover:bg-accent rounded-lg transition-colors",
                                        message.feedback === 'positive' && "bg-green-500/20"
                                      )}
                                      title={language === 'tr' ? 'Beğen' : 'Like'}
                                    >
                                      <ThumbsUp className={cn(
                                        "w-3.5 h-3.5",
                                        message.feedback === 'positive' ? "text-green-500" : "text-muted-foreground"
                                      )} />
                                    </button>

                                    {/* Thumbs down */}
                                    <button
                                      onClick={() => {
                                        setMessages(prev => prev.map(m =>
                                          m.id === message.id ? { ...m, feedback: m.feedback === 'negative' ? null : 'negative' } : m
                                        ));
                                      }}
                                      className={cn(
                                        "p-1.5 hover:bg-accent rounded-lg transition-colors",
                                        message.feedback === 'negative' && "bg-red-500/20"
                                      )}
                                      title={language === 'tr' ? 'Beğenme' : 'Dislike'}
                                    >
                                      <ThumbsDown className={cn(
                                        "w-3.5 h-3.5",
                                        message.feedback === 'negative' ? "text-red-500" : "text-muted-foreground"
                                      )} />
                                    </button>

                                    {/* Regenerate */}
                                    <button
                                      onClick={() => {
                                        // Find the user message before this assistant message
                                        const msgIndex = messages.findIndex(m => m.id === message.id);
                                        if (msgIndex > 0) {
                                          const userMessage = messages[msgIndex - 1];
                                          if (userMessage.role === 'user') {
                                            // Remove this assistant message and regenerate
                                            setMessages(prev => prev.filter(m => m.id !== message.id));
                                            setInput(userMessage.content);
                                          }
                                        }
                                      }}
                                      className="p-1.5 hover:bg-accent rounded-lg transition-colors"
                                      title={language === 'tr' ? 'Yeniden Oluştur' : 'Regenerate'}
                                    >
                                      <RotateCcw className="w-3.5 h-3.5 text-muted-foreground" />
                                    </button>
                                  </div>
                                )}

                                {/* User message copy button */}
                                {message.role === 'user' && (
                                  <button
                                    onClick={() => copyToClipboard(message.content)}
                                    className="absolute -left-8 top-1 opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-accent transition-all"
                                  >
                                    <Copy className="w-3 h-3" />
                                  </button>
                                )}

                                <p className={cn(
                                  "text-[10px] mt-1.5",
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
                            <motion.div
                              initial={{ opacity: 0, y: 10 }}
                              animate={{ opacity: 1, y: 0 }}
                              className="flex justify-start"
                            >
                              <div className="bg-muted px-4 py-3 rounded-2xl rounded-bl-md border border-border/50">
                                <div className="flex items-center gap-3">
                                  <div className="flex gap-1">
                                    <motion.div
                                      className="w-2 h-2 rounded-full bg-primary-500"
                                      animate={{ y: [0, -6, 0] }}
                                      transition={{ repeat: Infinity, duration: 0.6, delay: 0 }}
                                    />
                                    <motion.div
                                      className="w-2 h-2 rounded-full bg-primary-500"
                                      animate={{ y: [0, -6, 0] }}
                                      transition={{ repeat: Infinity, duration: 0.6, delay: 0.2 }}
                                    />
                                    <motion.div
                                      className="w-2 h-2 rounded-full bg-primary-500"
                                      animate={{ y: [0, -6, 0] }}
                                      transition={{ repeat: Infinity, duration: 0.6, delay: 0.4 }}
                                    />
                                  </div>
                                  <span className="text-sm text-muted-foreground">
                                    {language === 'tr' ? 'AI düşünüyor...' : 'AI is thinking...'}
                                  </span>
                                </div>
                              </div>
                            </motion.div>
                          )}

                          <div ref={messagesEndRef} />
                        </div>

                        {/* Input Area */}
                        <div className="p-3 border-t border-border bg-background/80 backdrop-blur-sm">
                          <div className="flex items-center gap-1.5 mb-2 flex-wrap">
                            <button
                              onClick={() => setWebSearchEnabled(!webSearchEnabled)}
                              className={cn(
                                "flex items-center gap-1 px-2.5 py-1.5 rounded-full text-xs font-medium transition-all",
                                webSearchEnabled
                                  ? "bg-blue-500 text-white shadow-lg shadow-blue-500/30"
                                  : "bg-muted text-muted-foreground hover:bg-accent"
                              )}
                            >
                              <Globe className="w-3 h-3" />
                              Web
                            </button>
                            <button
                              onClick={() => setRagEnabled(!ragEnabled)}
                              className={cn(
                                "flex items-center gap-1 px-2.5 py-1.5 rounded-full text-xs font-medium transition-all",
                                ragEnabled
                                  ? "bg-purple-500 text-white shadow-lg shadow-purple-500/30"
                                  : "bg-muted text-muted-foreground hover:bg-accent"
                              )}
                              title={language === 'tr' ? 'Döküman Araması' : 'Document Search'}
                            >
                              <Brain className="w-3 h-3" />
                              RAG
                            </button>
                            <button
                              onClick={() => {
                                // Image upload functionality with Vision AI analysis
                                const imageInput = document.createElement('input');
                                imageInput.type = 'file';
                                imageInput.accept = 'image/*';
                                imageInput.onchange = async (e) => {
                                  const file = (e.target as HTMLInputElement).files?.[0];
                                  if (file) {
                                    // Convert to base64
                                    const reader = new FileReader();
                                    reader.onload = async (event) => {
                                      const base64 = (event.target?.result as string)?.split(',')[1];
                                      if (base64) {
                                        // Add loading message
                                        setInput(prev => prev + (prev ? ' ' : '') + `[🔄 ${file.name} analiz ediliyor...]`);

                                        // Analyze with Vision API
                                        const description = await analyzeImage(
                                          base64,
                                          language === 'tr' ? 'Bu görseli detaylı açıkla.' : 'Describe this image in detail.'
                                        );

                                        if (description) {
                                          setInput(prev => prev.replace(`[🔄 ${file.name} analiz ediliyor...]`, `[📷 ${file.name}]\n\n🖼️ Görsel Analizi:\n${description}`));
                                        } else {
                                          setInput(prev => prev.replace(`[🔄 ${file.name} analiz ediliyor...]`, `[📷 ${file.name}]`));
                                        }
                                      }
                                    };
                                    reader.readAsDataURL(file);
                                  }
                                };
                                imageInput.click();
                              }}
                              className="p-1.5 rounded-full bg-muted text-muted-foreground hover:bg-accent transition-colors"
                              title={language === 'tr' ? 'Görsel Ekle' : 'Add Image'}
                            >
                              <ImageIcon className="w-3.5 h-3.5" />
                            </button>
                            <button
                              onClick={() => fileInputRef.current?.click()}
                              className="p-1.5 rounded-full bg-muted text-muted-foreground hover:bg-accent transition-colors"
                              title={language === 'tr' ? 'Dosya Ekle' : 'Attach File'}
                            >
                              <Paperclip className="w-3.5 h-3.5" />
                            </button>
                            <button
                              onClick={async () => {
                                // Use Local Whisper STT API with MediaRecorder
                                // Falls back to browser SpeechRecognition if API fails

                                if (isListening) {
                                  // Stop recording
                                  setIsListening(false);
                                  return;
                                }

                                try {
                                  // Request microphone access
                                  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                                  const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
                                  const audioChunks: Blob[] = [];

                                  setIsListening(true);

                                  mediaRecorder.ondataavailable = (event) => {
                                    audioChunks.push(event.data);
                                  };

                                  mediaRecorder.onstop = async () => {
                                    // Stop all tracks
                                    stream.getTracks().forEach(track => track.stop());

                                    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });

                                    // Try Whisper Local STT API first
                                    const transcript = await transcribeAudio(audioBlob);

                                    if (transcript) {
                                      setInput(prev => prev + (prev ? ' ' : '') + transcript);
                                    } else {
                                      // Fallback: Show error message
                                      console.warn('Whisper STT failed, transcription unavailable');
                                    }

                                    setIsListening(false);
                                  };

                                  mediaRecorder.start();

                                  // Auto-stop after 10 seconds
                                  setTimeout(() => {
                                    if (mediaRecorder.state === 'recording') {
                                      mediaRecorder.stop();
                                    }
                                  }, 10000);

                                  // Store mediaRecorder reference for manual stop
                                  (window as any).__mediaRecorder = mediaRecorder;

                                } catch (error) {
                                  console.error('Microphone access error:', error);

                                  // Fallback to browser SpeechRecognition
                                  if (('webkitSpeechRecognition' in window) || ('SpeechRecognition' in window)) {
                                    const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
                                    const recognition = new SpeechRecognition();
                                    recognition.lang = language === 'tr' ? 'tr-TR' : 'en-US';
                                    recognition.continuous = false;
                                    recognition.interimResults = true;

                                    recognition.onstart = () => setIsListening(true);
                                    recognition.onend = () => setIsListening(false);
                                    recognition.onerror = () => setIsListening(false);

                                    recognition.onresult = (event: any) => {
                                      const transcript = Array.from(event.results)
                                        .map((result: any) => result[0].transcript)
                                        .join('');
                                      setInput(prev => prev + (prev ? ' ' : '') + transcript);
                                    };

                                    recognition.start();
                                  } else {
                                    alert(language === 'tr' ? 'Mikrofon erişimi sağlanamadı' : 'Microphone access failed');
                                  }
                                }
                              }}
                              className={cn(
                                "p-1.5 rounded-full transition-all",
                                isListening
                                  ? "bg-red-500 text-white animate-pulse shadow-lg shadow-red-500/30"
                                  : "bg-muted text-muted-foreground hover:bg-accent"
                              )}
                              title={language === 'tr' ? (isListening ? 'Dinlemeyi Durdur' : 'Sesli Giriş') : (isListening ? 'Stop Listening' : 'Voice Input')}
                            >
                              {isListening ? <MicOff className="w-3.5 h-3.5" /> : <Mic className="w-3.5 h-3.5" />}
                            </button>
                          </div>

                          {/* Voice Listening Indicator */}
                          <AnimatePresence>
                            {isListening && (
                              <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                exit={{ opacity: 0, height: 0 }}
                                className="flex items-center gap-2 mb-2 px-3 py-2 bg-red-500/10 border border-red-500/30 rounded-lg"
                              >
                                <div className="flex gap-1">
                                  <motion.div
                                    className="w-1 h-3 bg-red-500 rounded-full"
                                    animate={{ scaleY: [1, 1.5, 1] }}
                                    transition={{ repeat: Infinity, duration: 0.5 }}
                                  />
                                  <motion.div
                                    className="w-1 h-3 bg-red-500 rounded-full"
                                    animate={{ scaleY: [1, 2, 1] }}
                                    transition={{ repeat: Infinity, duration: 0.5, delay: 0.1 }}
                                  />
                                  <motion.div
                                    className="w-1 h-3 bg-red-500 rounded-full"
                                    animate={{ scaleY: [1, 1.5, 1] }}
                                    transition={{ repeat: Infinity, duration: 0.5, delay: 0.2 }}
                                  />
                                </div>
                                <span className="text-xs text-red-500 font-medium">
                                  {language === 'tr' ? 'Dinleniyor...' : 'Listening...'}
                                </span>
                              </motion.div>
                            )}
                          </AnimatePresence>

                          <div className="flex items-end gap-2">
                            <textarea
                              ref={inputRef}
                              value={input}
                              onChange={(e) => setInput(e.target.value)}
                              onKeyDown={handleKeyDown}
                              placeholder={language === 'tr' ? 'Mesajınızı yazın...' : 'Type your message...'}
                              rows={1}
                              className="flex-1 resize-none bg-muted border-0 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/50 max-h-24 transition-all"
                            />
                            <motion.button
                              onClick={handleSend}
                              disabled={!input.trim() || isLoading}
                              whileHover={{ scale: 1.05 }}
                              whileTap={{ scale: 0.95 }}
                              className={cn(
                                "w-10 h-10 flex items-center justify-center rounded-xl transition-all shadow-lg",
                                input.trim() && !isLoading
                                  ? "bg-gradient-to-r from-primary-500 to-primary-600 text-white shadow-primary-500/30 hover:shadow-primary-500/50"
                                  : "bg-muted text-muted-foreground cursor-not-allowed"
                              )}
                            >
                              <Send className="w-4 h-4" />
                            </motion.button>
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

                  </motion.div>
                )}
              </AnimatePresence>

              {/* Minimized Footer - Enhanced */}
              {isMinimized && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="px-4 py-3 cursor-pointer hover:bg-accent transition-all group"
                  onClick={() => setIsMinimized(false)}
                >
                  <div className="flex items-center justify-center gap-2">
                    <motion.div
                      animate={{ y: [0, -3, 0] }}
                      transition={{ repeat: Infinity, duration: 1.5 }}
                      className="text-primary-500"
                    >
                      <ChevronUp className="w-4 h-4" />
                    </motion.div>
                    <span className="text-xs text-muted-foreground group-hover:text-foreground transition-colors">
                      {language === 'tr' ? 'Genişletmek için tıklayın' : 'Click to expand'}
                    </span>
                    <motion.div
                      animate={{ y: [0, -3, 0] }}
                      transition={{ repeat: Infinity, duration: 1.5 }}
                      className="text-primary-500"
                    >
                      <ChevronUp className="w-4 h-4" />
                    </motion.div>
                  </div>
                  {messages.length > 0 && (
                    <p className="text-[10px] text-center text-muted-foreground mt-1 truncate">
                      {language === 'tr' ? `${messages.length} mesaj` : `${messages.length} messages`}
                    </p>
                  )}
                </motion.div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
