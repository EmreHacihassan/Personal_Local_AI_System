'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Send,
  Globe,
  Sparkles,
  Paperclip,
  Loader2,
  Copy,
  ThumbsUp,
  ThumbsDown,
  RefreshCw,
  Zap,
  FileText,
  ExternalLink,
  ChevronDown,
  ChevronRight,
  Star,
  Edit,
  X,
  Check,
  Image as ImageIcon,
  StopCircle,
  Clock,
  Gauge,
  Layers,
  Trash2,
  AlertTriangle,
  CheckCircle2,
  Timer,
  FileCode,
  ChevronUp,
  HelpCircle,
  Search,
  Keyboard
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/cjs/styles/prism';
import { useStore, Message } from '@/store/useStore';
import { sendChatMessage, streamChatMessage } from '@/lib/api';
import { cn, generateId, formatDate } from '@/lib/utils';

// Sample questions with multi-language support
const sampleQuestions = {
  tr: [
    { icon: '🔬', text: 'RAG sistemi nasıl çalışır?', category: 'Teknik' },
    { icon: '📊', text: 'Veri analizi için en iyi pratikler', category: 'Analiz' },
    { icon: '🚀', text: 'Performans optimizasyonu önerileri', category: 'Performans' },
    { icon: '🛡️', text: 'Güvenlik en iyi pratikleri', category: 'Güvenlik' },
  ],
  en: [
    { icon: '🔬', text: 'How does the RAG system work?', category: 'Technical' },
    { icon: '📊', text: 'Best practices for data analysis', category: 'Analysis' },
    { icon: '🚀', text: 'Performance optimization tips', category: 'Performance' },
    { icon: '🛡️', text: 'Security best practices', category: 'Security' },
  ],
  de: [
    { icon: '🔬', text: 'Wie funktioniert das RAG-System?', category: 'Technisch' },
    { icon: '📊', text: 'Best Practices für Datenanalyse', category: 'Analyse' },
    { icon: '🚀', text: 'Leistungsoptimierungstipps', category: 'Leistung' },
    { icon: '🛡️', text: 'Sicherheits-Best-Practices', category: 'Sicherheit' },
  ],
};

// Web Search Modes
const webSearchModes = [
  { id: 'auto', tr: '🔄 Otomatik', en: '🔄 Auto', de: '🔄 Automatisch', icon: '🔄' },
  { id: 'off', tr: '❌ Kapalı', en: '❌ Off', de: '❌ Aus', icon: '❌' },
  { id: 'on', tr: '✅ Aktif', en: '✅ On', de: '✅ Ein', icon: '✅' },
];

// Response Modes (AI Personality/Style)
const responseModes = [
  { id: 'auto', tr: '🤖 Otomatik', en: '🤖 Auto', de: '🤖 Automatisch', desc: { tr: 'AI en uygun stili seçer', en: 'AI chooses the best style', de: 'KI wählt den besten Stil' } },
  { id: 'creative', tr: '🎨 Yaratıcı', en: '🎨 Creative', de: '🎨 Kreativ', desc: { tr: 'Özgün ve ilham verici', en: 'Original and inspiring', de: 'Originell und inspirierend' } },
  { id: 'analytical', tr: '📊 Analitik', en: '📊 Analytical', de: '📊 Analytisch', desc: { tr: 'Veri odaklı ve mantıksal', en: 'Data-driven and logical', de: 'Datengesteuert und logisch' } },
  { id: 'technical', tr: '⚙️ Teknik', en: '⚙️ Technical', de: '⚙️ Technisch', desc: { tr: 'Detaylı ve kesin', en: 'Detailed and precise', de: 'Detailliert und präzise' } },
  { id: 'friendly', tr: '😊 Samimi', en: '😊 Friendly', de: '😊 Freundlich', desc: { tr: 'Sıcak ve anlaşılır', en: 'Warm and approachable', de: 'Warm und zugänglich' } },
  { id: 'academic', tr: '🎓 Akademik', en: '🎓 Academic', de: '🎓 Akademisch', desc: { tr: 'Bilimsel ve formal', en: 'Scientific and formal', de: 'Wissenschaftlich und formal' } },
];

// Complexity/Type levels
const complexityLevels = [
  { id: 'simple', tr: '🔹 Basit', en: '🔹 Simple', de: '🔹 Einfach', desc: { tr: 'Kısa ve öz cevap', en: 'Brief and concise', de: 'Kurz und prägnant' } },
  { id: 'normal', tr: '🔸 Normal', en: '🔸 Normal', de: '🔸 Normal', desc: { tr: 'Dengeli detay seviyesi', en: 'Balanced detail level', de: 'Ausgewogenes Detailniveau' } },
  { id: 'comprehensive', tr: '🔷 Kapsamlı', en: '🔷 Comprehensive', de: '🔷 Umfassend', desc: { tr: 'Derinlemesine analiz', en: 'In-depth analysis', de: 'Eingehende Analyse' } },
  { id: 'research', tr: '🔬 Araştırma', en: '🔬 Research', de: '🔬 Forschung', desc: { tr: 'Çoklu kaynak, maksimum derinlik', en: 'Multi-source, maximum depth', de: 'Multi-Quelle, maximale Tiefe' } },
];

// Response lengths
const responseLengths = [
  { id: 'auto', tr: '🔄 Otomatik', en: '🔄 Auto', de: '🔄 Automatisch' },
  { id: 'short', tr: '📝 Kısa', en: '📝 Short', de: '📝 Kurz' },
  { id: 'medium', tr: '📄 Orta', en: '📄 Medium', de: '📄 Mittel' },
  { id: 'long', tr: '📑 Uzun', en: '📑 Long', de: '📑 Lang' },
  { id: 'very_long', tr: '📚 Çok Uzun', en: '📚 Very Long', de: '📚 Sehr Lang' },
];

export function ChatPage() {
  const {
    messages,
    addMessage,
    clearMessages,
    isTyping,
    setIsTyping,
    webSearchMode,
    setWebSearchMode,
    responseMode,
    setResponseMode,
    language,
    complexityLevel,
    setComplexityLevel,
    responseLength,
    setResponseLength,
    toggleMessageFavorite,
    editMessage,
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    isStreaming,
    setIsStreaming,
    streamingContent,
    setStreamingContent,
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    appendStreamingContent,
    templates,
    showTimestamps,
    autoScroll,
  } = useStore();

  const [inputValue, setInputValue] = useState('');
  const [showModeSelector, setShowModeSelector] = useState(false);
  const [showComplexitySelector, setShowComplexitySelector] = useState(false);
  const [showLengthSelector, setShowLengthSelector] = useState(false);
  const [showWebSearchSelector, setShowWebSearchSelector] = useState(false);
  const [showTemplates, setShowTemplates] = useState(false);
  const [showAttachmentTooltip, setShowAttachmentTooltip] = useState(false);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [elapsedTime, setElapsedTime] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const scrollToBottom = useCallback(() => {
    if (autoScroll) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [autoScroll]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Timer for elapsed time during response
  useEffect(() => {
    if (isTyping) {
      setElapsedTime(0);
      timerRef.current = setInterval(() => {
        setElapsedTime(prev => prev + 0.1);
      }, 100);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [isTyping]);

  // Auto-hide attachment tooltip after 2 seconds
  useEffect(() => {
    if (showAttachmentTooltip) {
      const timeout = setTimeout(() => {
        setShowAttachmentTooltip(false);
      }, 2000);
      return () => clearTimeout(timeout);
    }
  }, [showAttachmentTooltip]);

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      // Check if click is inside any dropdown container
      const isInsideDropdown = target.closest('[data-dropdown-container]');
      if (!isInsideDropdown) {
        setShowModeSelector(false);
        setShowComplexitySelector(false);
        setShowLengthSelector(false);
        setShowWebSearchSelector(false);
      }
    };
    
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, []);

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.type.startsWith('image/')) {
      setSelectedImage(file);
      const reader = new FileReader();
      reader.onload = (e) => setImagePreview(e.target?.result as string);
      reader.readAsDataURL(file);
    }
  };

  const removeImage = () => {
    setSelectedImage(null);
    setImagePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const stopGeneration = () => {
    setIsTyping(false);
    setIsStreaming(false);
    abortControllerRef.current?.abort();
  };

  // Abort controller for streaming
  const abortControllerRef = useRef<AbortController | null>(null);

  const handleSend = async () => {
    if (!inputValue.trim() || isTyping) return;

    const startTime = Date.now();
    const userMessage: Message = {
      id: generateId(),
      role: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
    };

    addMessage(userMessage);
    setInputValue('');
    setIsTyping(true);
    setIsStreaming(true);
    setStreamingContent('');
    removeImage();

    // Create abort controller for this request
    abortControllerRef.current = new AbortController();

    try {
      // Map our new modes to API expected values
      const apiWebSearch = webSearchMode === 'on' ? true : webSearchMode === 'off' ? false : undefined;
      
      // Response mode mapping: auto/creative/analytical/technical/friendly/academic -> normal/detailed
      const apiResponseMode = (responseMode === 'analytical' || responseMode === 'technical' || responseMode === 'academic') 
                              ? 'detailed' : 'normal';
      
      // Complexity mapping: simple/normal/comprehensive/research -> simple/moderate/advanced/comprehensive
      const apiComplexity = complexityLevel === 'research' ? 'comprehensive' : 
                           complexityLevel === 'comprehensive' ? 'advanced' : 
                           complexityLevel === 'simple' ? 'simple' : 'moderate';
      
      // Length mapping: auto/short/medium/long/very_long -> short/normal/detailed/comprehensive
      const apiLength = responseLength === 'very_long' ? 'comprehensive' : 
                       responseLength === 'long' ? 'detailed' : 
                       responseLength === 'short' ? 'short' : 
                       responseLength === 'medium' ? 'normal' : 'normal';
      
      // Debug logging
      console.log('🔧 Chat Settings:', {
        webSearchMode,
        responseMode,
        complexityLevel,
        responseLength,
        '→ API Params': {
          web_search: apiWebSearch,
          response_mode: apiResponseMode,
          complexity_level: apiComplexity,
          response_length: apiLength,
        }
      });
      
      let fullContent = '';
      let metadata: Record<string, unknown> = {};
      
      // Try streaming first
      try {
        for await (const chunk of streamChatMessage({
          message: userMessage.content,
          web_search: apiWebSearch,
          response_mode: apiResponseMode as 'normal' | 'detailed',
          complexity_level: apiComplexity as 'auto' | 'simple' | 'moderate' | 'advanced' | 'comprehensive',
          response_length: apiLength as 'short' | 'normal' | 'detailed' | 'comprehensive',
        }, abortControllerRef.current.signal)) {
          if (chunk.type === 'token') {
            fullContent += chunk.content;
            setStreamingContent(fullContent);
          } else if (chunk.type === 'done') {
            if (chunk.content) fullContent = chunk.content;
            if (chunk.metadata) metadata = chunk.metadata;
            break;
          } else if (chunk.type === 'error') {
            throw new Error(chunk.content);
          }
        }
      } catch (streamError) {
        // Fallback to non-streaming if streaming fails
        console.log('Streaming failed, falling back to regular request:', streamError);
        const response = await sendChatMessage({
          message: userMessage.content,
          web_search: apiWebSearch,
          response_mode: apiResponseMode as 'normal' | 'detailed',
          complexity_level: apiComplexity as 'auto' | 'simple' | 'moderate' | 'advanced' | 'comprehensive',
          response_length: apiLength as 'short' | 'normal' | 'detailed' | 'comprehensive',
        });

        if (response.success && response.data) {
          fullContent = response.data.response;
          metadata = response.data.metadata || {};
        } else {
          throw new Error(response.error || 'Unknown error');
        }
      }

      const responseTime = (Date.now() - startTime) / 1000;

      if (fullContent) {
        const assistantMessage: Message = {
          id: generateId(),
          role: 'assistant',
          content: fullContent,
          timestamp: new Date(),
          metadata: metadata,
          responseTime: responseTime,
          wordCount: fullContent.split(/\s+/).filter(Boolean).length,
        };
        addMessage(assistantMessage);
      } else {
        // Empty response error
        throw new Error('Empty response from server');
      }
    } catch (error) {
      // Connection/Network error - permanent in chat
      console.error('Chat error:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      
      // Don't show error for user cancellation
      if (errorMessage === 'Request cancelled') {
        return;
      }
      
      const errorMessages = {
        tr: {
          title: '❌ Bağlantı Hatası',
          noConnection: 'Backend sunucusuna bağlanılamadı',
          suggestion: 'Backend servisinin çalıştığından emin olun: `python run.py`',
          checkList: [
            '🔍 Backend servisi (port 8001) çalışıyor mu?',
            '🔍 Ollama servisi aktif mi?',
            '🔍 Firewall bağlantıyı engelliyor olabilir mi?',
          ],
        },
        en: {
          title: '❌ Connection Error',
          noConnection: 'Could not connect to backend server',
          suggestion: 'Make sure the backend service is running: `python run.py`',
          checkList: [
            '🔍 Is the backend service (port 8001) running?',
            '🔍 Is Ollama service active?',
            '🔍 Could firewall be blocking the connection?',
          ],
        },
        de: {
          title: '❌ Verbindungsfehler',
          noConnection: 'Verbindung zum Backend-Server nicht möglich',
          suggestion: 'Stellen Sie sicher, dass der Backend-Service läuft: `python run.py`',
          checkList: [
            '🔍 Läuft der Backend-Service (Port 8001)?',
            '🔍 Ist der Ollama-Dienst aktiv?',
            '🔍 Könnte die Firewall die Verbindung blockieren?',
          ],
        },
      };
      const err = errorMessages[language] || errorMessages.en;
      addMessage({
        id: generateId(),
        role: 'assistant',
        content: `${err.title}\n\n**${err.noConnection}**\n\n**${language === 'tr' ? 'Hata' : 'Error'}:**\n\`\`\`\n${errorMessage}\n\`\`\`\n\n**${language === 'tr' ? 'Kontrol Listesi' : 'Checklist'}:**\n${err.checkList.join('\n')}\n\n💡 **${language === 'tr' ? 'Öneri' : 'Suggestion'}:** ${err.suggestion}`,
        timestamp: new Date(),
        isError: true,
        errorDetails: {
          type: 'connection_error',
          suggestion: err.suggestion,
        },
      });
    } finally {
      setIsTyping(false);
      setIsStreaming(false);
      setStreamingContent('');
    }
  };

  const regenerateResponse = async (messageId: string) => {
    const messageIndex = messages.findIndex(m => m.id === messageId);
    if (messageIndex === -1) return;

    // Find the previous user message
    let userMessage = null;
    for (let i = messageIndex - 1; i >= 0; i--) {
      if (messages[i].role === 'user') {
        userMessage = messages[i];
        break;
      }
    }

    if (!userMessage) return;

    setIsTyping(true);

    try {
      // Map our new modes to API expected values (same as handleSend)
      const apiWebSearch = webSearchMode === 'on' ? true : webSearchMode === 'off' ? false : undefined;
      const apiResponseMode = (responseMode === 'analytical' || responseMode === 'technical' || responseMode === 'academic') 
                              ? 'detailed' : 'normal';
      const apiComplexity = complexityLevel === 'research' ? 'comprehensive' : 
                           complexityLevel === 'comprehensive' ? 'advanced' : 
                           complexityLevel === 'simple' ? 'simple' : 'moderate';
      const apiLength = responseLength === 'very_long' ? 'comprehensive' : 
                       responseLength === 'long' ? 'detailed' : 
                       responseLength === 'short' ? 'short' : 
                       responseLength === 'medium' ? 'normal' : 'normal';
      
      const response = await sendChatMessage({
        message: userMessage.content,
        web_search: apiWebSearch,
        response_mode: apiResponseMode as 'normal' | 'detailed',
        complexity_level: apiComplexity as 'auto' | 'simple' | 'moderate' | 'advanced' | 'comprehensive',
        response_length: apiLength as 'short' | 'normal' | 'detailed' | 'comprehensive',
      });

      if (response.success && response.data) {
        editMessage(messageId, response.data.response);
      }
    } catch (error) {
      console.error('Regenerate error:', error);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSampleQuestion = (question: string) => {
    setInputValue(question);
    inputRef.current?.focus();
  };

  const handleFollowUpClick = (question: string) => {
    setInputValue(question);
    inputRef.current?.focus();
  };

  const handleRelatedQueryClick = (query: string) => {
    setInputValue(query);
    inputRef.current?.focus();
  };

  const t = {
    title: { tr: 'AI Asistan', en: 'AI Assistant', de: 'KI-Assistent' },
    subtitle: { tr: 'Sorularınızı yanıtlamaya hazırım', en: 'Ready to answer your questions', de: 'Bereit, Ihre Fragen zu beantworten' },
    hello: { tr: 'Merhaba! Size nasıl yardımcı olabilirim?', en: 'Hello! How can I help you?', de: 'Hallo! Wie kann ich Ihnen helfen?' },
    chooseExample: { tr: 'Aşağıdaki örneklerden birini seçin veya kendi sorunuzu yazın', en: 'Choose from the examples below or write your own question', de: 'Wählen Sie aus den Beispielen unten oder schreiben Sie Ihre eigene Frage' },
    placeholder: { tr: 'Mesajınızı yazın...', en: 'Type your message...', de: 'Geben Sie Ihre Nachricht ein...' },
    enterToSend: { tr: 'Enter ile gönder, Shift+Enter ile yeni satır', en: 'Press Enter to send, Shift+Enter for new line', de: 'Enter zum Senden, Shift+Enter für neue Zeile' },
    stop: { tr: 'Durdur', en: 'Stop', de: 'Stoppen' },
    webSearch: { tr: 'Web Arama', en: 'Web Search', de: 'Websuche' },
    complexity: { tr: 'Karmaşıklık', en: 'Complexity', de: 'Komplexität' },
    length: { tr: 'Uzunluk', en: 'Length', de: 'Länge' },
    visionMode: { tr: 'Görsel Analizi', en: 'Vision Analysis', de: 'Bildanalyse' },
    addImage: { tr: 'Görsel Ekle', en: 'Add Image', de: 'Bild hinzufügen' },
  };

  const currentQuestions = sampleQuestions[language] || sampleQuestions.tr;
  const currentComplexity = complexityLevels.find(c => c.id === complexityLevel);
  const currentLength = responseLengths.find(l => l.id === responseLength);
  const currentMode = responseModes.find(m => m.id === responseMode);
  const currentWebSearch = webSearchModes.find(w => w.id === webSearchMode);

  // Control bar labels
  const controlLabels = {
    webSearch: { tr: 'Web Arama', en: 'Web Search', de: 'Websuche' },
    aiStyle: { tr: 'AI Stili', en: 'AI Style', de: 'KI-Stil' },
    complexity: { tr: 'Detay', en: 'Detail', de: 'Detail' },
    length: { tr: 'Uzunluk', en: 'Length', de: 'Länge' },
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header with Controls on Right */}
      <header className="flex items-center justify-between px-4 py-3 border-b border-border bg-card/50 backdrop-blur-sm">
        {/* Left: Title */}
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 text-white">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h1 className="text-base font-semibold">{t.title[language]}</h1>
            <p className="text-[10px] text-muted-foreground hidden sm:block">{t.subtitle[language]}</p>
          </div>
        </div>

        {/* Right: Controls */}
        <div className="flex items-center gap-1.5">
          {/* Web Search */}
          <div className="relative" data-dropdown-container>
            <button
              onClick={(e) => {
                e.stopPropagation();
                console.log('Web Search button clicked! Current state:', showWebSearchSelector);
                setShowWebSearchSelector(!showWebSearchSelector);
                setShowModeSelector(false);
                setShowComplexitySelector(false);
                setShowLengthSelector(false);
              }}
              className={cn(
                "flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg transition-all text-xs font-medium",
                webSearchMode === 'on'
                  ? "bg-blue-500 text-white"
                  : webSearchMode === 'off'
                  ? "bg-muted text-muted-foreground hover:bg-muted/80"
                  : "bg-blue-500/10 text-blue-600 border border-blue-500/20"
              )}
              title={controlLabels.webSearch[language]}
            >
              <Globe className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">{currentWebSearch?.[language]?.replace(/^[^\s]+\s/, '') || 'Auto'}</span>
              <ChevronDown className="w-3 h-3 opacity-60" />
            </button>

            {/* Simple dropdown without AnimatePresence for testing */}
            {showWebSearchSelector && (
              <div
                className="absolute right-0 top-full mt-1.5 w-44 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl z-[9999] overflow-visible"
                style={{ zIndex: 9999 }}
                onClick={(e) => e.stopPropagation()}
              >
                <div className="p-1.5">
                  {webSearchModes.map((mode) => (
                    <div
                      key={mode.id}
                      onClick={() => {
                        console.log('Setting web search mode:', mode.id);
                        setWebSearchMode(mode.id as typeof webSearchMode);
                        setShowWebSearchSelector(false);
                      }}
                      className={cn(
                        "w-full px-2.5 py-2.5 text-left text-xs rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer select-none",
                        webSearchMode === mode.id && "bg-blue-500/10 text-blue-600"
                      )}
                    >
                      <div className="flex items-center gap-2">
                        <span>{mode.icon}</span>
                        <span className="font-medium">{mode[language]?.replace(/^[^\s]+\s/, '')}</span>
                        {webSearchMode === mode.id && <Check className="w-3 h-3 ml-auto text-blue-500" />}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* AI Style */}
          <div className="relative" data-dropdown-container>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setShowModeSelector(!showModeSelector);
                setShowWebSearchSelector(false);
                setShowComplexitySelector(false);
                setShowLengthSelector(false);
              }}
              className={cn(
                "flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg transition-all text-xs font-medium",
                responseMode !== 'auto'
                  ? "bg-amber-500/10 text-amber-600 border border-amber-500/20"
                  : "bg-muted text-foreground hover:bg-muted/80"
              )}
              title={controlLabels.aiStyle[language]}
            >
              <Zap className="w-3.5 h-3.5 text-amber-500" />
              <span className="hidden sm:inline">{currentMode?.[language]?.replace(/^[^\s]+\s/, '') || 'Auto'}</span>
              <ChevronDown className="w-3 h-3 opacity-60" />
            </button>

            {/* Simple dropdown */}
            {showModeSelector && (
              <div
                className="absolute right-0 top-full mt-1.5 w-52 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl overflow-visible"
                style={{ zIndex: 9999 }}
                onClick={(e) => e.stopPropagation()}
              >
                <div className="p-1.5">
                  {responseModes.map((mode) => (
                    <div
                      key={mode.id}
                      onClick={() => {
                        console.log('Setting response mode:', mode.id);
                        setResponseMode(mode.id as typeof responseMode);
                        setShowModeSelector(false);
                      }}
                      className={cn(
                        "w-full px-2.5 py-2.5 text-left rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer select-none",
                        responseMode === mode.id && "bg-amber-500/10 text-amber-600"
                      )}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-xs font-medium">{mode[language]}</div>
                          <div className="text-[10px] text-muted-foreground">{mode.desc[language]}</div>
                        </div>
                        {responseMode === mode.id && <Check className="w-3 h-3 text-amber-500 flex-shrink-0" />}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Complexity */}
          <div className="relative" data-dropdown-container>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setShowComplexitySelector(!showComplexitySelector);
                setShowWebSearchSelector(false);
                setShowModeSelector(false);
                setShowLengthSelector(false);
              }}
              className={cn(
                "flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg transition-all text-xs font-medium",
                complexityLevel !== 'normal'
                  ? "bg-emerald-500/10 text-emerald-600 border border-emerald-500/20"
                  : "bg-muted text-foreground hover:bg-muted/80"
              )}
              title={controlLabels.complexity[language]}
            >
              <Gauge className="w-3.5 h-3.5 text-emerald-500" />
              <span className="hidden sm:inline">{currentComplexity?.[language]?.replace(/^[^\s]+\s/, '') || 'Normal'}</span>
              <ChevronDown className="w-3 h-3 opacity-60" />
            </button>

            {/* Simple dropdown */}
            {showComplexitySelector && (
              <div
                className="absolute right-0 top-full mt-1.5 w-52 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl overflow-visible"
                style={{ zIndex: 9999 }}
                onClick={(e) => e.stopPropagation()}
              >
                <div className="p-1.5">
                  {complexityLevels.map((level) => (
                    <div
                      key={level.id}
                      onClick={() => {
                        console.log('Setting complexity level:', level.id);
                        setComplexityLevel(level.id as typeof complexityLevel);
                        setShowComplexitySelector(false);
                      }}
                      className={cn(
                        "w-full px-2.5 py-2.5 text-left rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer select-none",
                        complexityLevel === level.id && "bg-emerald-500/10 text-emerald-600"
                      )}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-xs font-medium">{level[language]}</div>
                          <div className="text-[10px] text-muted-foreground">{level.desc[language]}</div>
                        </div>
                        {complexityLevel === level.id && <Check className="w-3 h-3 text-emerald-500 flex-shrink-0" />}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Length */}
          <div className="relative" data-dropdown-container>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setShowLengthSelector(!showLengthSelector);
                setShowWebSearchSelector(false);
                setShowModeSelector(false);
                setShowComplexitySelector(false);
              }}
              className={cn(
                "flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg transition-all text-xs font-medium",
                responseLength !== 'auto'
                  ? "bg-purple-500/10 text-purple-600 border border-purple-500/20"
                  : "bg-muted text-foreground hover:bg-muted/80"
              )}
              title={controlLabels.length[language]}
            >
              <Layers className="w-3.5 h-3.5 text-purple-500" />
              <span className="hidden sm:inline">{currentLength?.[language]?.replace(/^[^\s]+\s/, '') || 'Auto'}</span>
              <ChevronDown className="w-3 h-3 opacity-60" />
            </button>

            {/* Simple dropdown */}
            {showLengthSelector && (
              <div
                className="absolute right-0 top-full mt-1.5 w-44 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl overflow-visible"
                style={{ zIndex: 9999 }}
                onClick={(e) => e.stopPropagation()}
              >
                <div className="p-1.5">
                  {responseLengths.map((length) => (
                    <div
                      key={length.id}
                      onClick={() => {
                        console.log('Setting response length:', length.id);
                        setResponseLength(length.id as typeof responseLength);
                        setShowLengthSelector(false);
                      }}
                      className={cn(
                        "w-full px-2.5 py-2.5 text-left text-xs rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer select-none",
                        responseLength === length.id && "bg-purple-500/10 text-purple-600"
                      )}
                    >
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{length[language]}</span>
                        {responseLength === length.id && <Check className="w-3 h-3 ml-auto text-purple-500" />}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Divider */}
          {messages.length > 0 && <div className="h-5 w-px bg-border mx-1" />}

          {/* Clear Chat */}
          {messages.length > 0 && (
            <button
              onClick={() => {
                if (confirm(language === 'tr' ? 'Tüm mesajları silmek istediğinize emin misiniz?' : 'Are you sure you want to clear all messages?')) {
                  clearMessages();
                }
              }}
              className="flex items-center gap-1 px-2 py-1.5 rounded-lg text-red-500 hover:bg-red-500/10 transition-colors text-xs"
              title={language === 'tr' ? 'Sohbeti Temizle' : 'Clear Chat'}
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </header>
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Welcome State */}
          {messages.length === 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center py-8"
            >
              {/* Hero Section */}
              <div className="relative mb-8">
                {/* Animated Background Rings */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <motion.div
                    animate={{ scale: [1, 1.2, 1], opacity: [0.3, 0.1, 0.3] }}
                    transition={{ duration: 3, repeat: Infinity }}
                    className="absolute w-32 h-32 rounded-full bg-gradient-to-br from-primary-500/20 to-violet-500/20"
                  />
                  <motion.div
                    animate={{ scale: [1, 1.3, 1], opacity: [0.2, 0.05, 0.2] }}
                    transition={{ duration: 4, repeat: Infinity, delay: 0.5 }}
                    className="absolute w-48 h-48 rounded-full bg-gradient-to-br from-primary-500/10 to-violet-500/10"
                  />
                </div>
                
                {/* Main Icon */}
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: "spring", stiffness: 200, damping: 15 }}
                  className="relative inline-flex items-center justify-center w-24 h-24 rounded-3xl bg-gradient-to-br from-primary-500 via-violet-500 to-purple-600 text-white shadow-2xl shadow-primary-500/30"
                >
                  <Sparkles className="w-12 h-12" />
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                    className="absolute inset-0 rounded-3xl border-2 border-dashed border-white/20"
                  />
                </motion.div>
              </div>

              {/* Title & Subtitle */}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
              >
                <h2 className="text-3xl font-bold bg-gradient-to-r from-foreground via-primary-600 to-foreground bg-clip-text text-transparent mb-3">
                  {t.hello[language]}
                </h2>
                <p className="text-lg text-muted-foreground max-w-md mx-auto">
                  {t.chooseExample[language]}
                </p>
              </motion.div>

              {/* Current Settings Display */}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="flex flex-wrap justify-center gap-2 mt-6 mb-8"
              >
                {/* Web Search Status */}
                <motion.span
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.4 }}
                  className={cn(
                    "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium",
                    webSearchMode === 'on'
                      ? "bg-blue-500/15 text-blue-600 border border-blue-500/30"
                      : webSearchMode === 'auto'
                      ? "bg-blue-500/10 text-blue-600 border border-blue-500/20"
                      : "bg-muted/50 text-muted-foreground border border-border"
                  )}
                >
                  <Globe className="w-3.5 h-3.5" />
                  {language === 'tr' ? 'Web' : 'Web'}: {currentWebSearch?.[language]?.replace(/^[^\s]+\s/, '')}
                  {webSearchMode !== 'off' && <span className="w-1.5 h-1.5 rounded-full bg-green-500" />}
                </motion.span>

                {/* AI Style Status */}
                <motion.span
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.5 }}
                  className={cn(
                    "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium",
                    responseMode !== 'auto'
                      ? "bg-amber-500/15 text-amber-600 border border-amber-500/30"
                      : "bg-muted/50 text-muted-foreground border border-border"
                  )}
                >
                  <Zap className="w-3.5 h-3.5" />
                  {language === 'tr' ? 'Stil' : 'Style'}: {currentMode?.[language]?.replace(/^[^\s]+\s/, '')}
                </motion.span>

                {/* Complexity Status */}
                <motion.span
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.6 }}
                  className={cn(
                    "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium",
                    complexityLevel !== 'normal'
                      ? "bg-emerald-500/15 text-emerald-600 border border-emerald-500/30"
                      : "bg-muted/50 text-muted-foreground border border-border"
                  )}
                >
                  <Gauge className="w-3.5 h-3.5" />
                  {language === 'tr' ? 'Detay' : 'Detail'}: {currentComplexity?.[language]?.replace(/^[^\s]+\s/, '')}
                </motion.span>

                {/* Length Status */}
                <motion.span
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.7 }}
                  className={cn(
                    "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium",
                    responseLength !== 'auto'
                      ? "bg-purple-500/15 text-purple-600 border border-purple-500/30"
                      : "bg-muted/50 text-muted-foreground border border-border"
                  )}
                >
                  <Layers className="w-3.5 h-3.5" />
                  {language === 'tr' ? 'Uzunluk' : 'Length'}: {currentLength?.[language]?.replace(/^[^\s]+\s/, '')}
                </motion.span>
              </motion.div>

              {/* Sample Questions Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-2xl mx-auto">
                {currentQuestions.map((q, i) => (
                  <motion.button
                    key={i}
                    initial={{ opacity: 0, y: 15 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.5 + i * 0.1 }}
                    whileHover={{ scale: 1.02, y: -2 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => handleSampleQuestion(q.text)}
                    className="flex items-center gap-4 p-4 rounded-2xl bg-gradient-to-br from-card to-card/50 border border-border hover:border-primary-500/50 hover:shadow-xl hover:shadow-primary-500/5 transition-all text-left group relative overflow-hidden"
                  >
                    {/* Background Glow on Hover */}
                    <div className="absolute inset-0 bg-gradient-to-br from-primary-500/5 to-violet-500/5 opacity-0 group-hover:opacity-100 transition-opacity" />
                    
                    <span className="text-3xl relative z-10 group-hover:scale-110 transition-transform">{q.icon}</span>
                    <div className="relative z-10">
                      <p className="text-sm font-semibold text-foreground group-hover:text-primary-600 transition-colors">
                        {q.text}
                      </p>
                      <p className="text-xs text-muted-foreground mt-0.5">{q.category}</p>
                    </div>
                    <ChevronRight className="w-4 h-4 ml-auto text-muted-foreground group-hover:text-primary-500 group-hover:translate-x-1 transition-all relative z-10" />
                  </motion.button>
                ))}
              </div>

              {/* Bottom Hint */}
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 1 }}
                className="text-xs text-muted-foreground mt-8 flex items-center justify-center gap-2"
              >
                <Keyboard className="w-3.5 h-3.5" />
                {language === 'tr' 
                  ? 'Yukarıdaki ayarlardan web araması, yanıt stili ve uzunluğunu değiştirebilirsiniz' 
                  : 'Use the settings above to customize web search, response style and length'}
              </motion.p>
            </motion.div>
          )}

          {/* Messages */}
          <AnimatePresence mode="popLayout">
            {messages.map((message) => (
              <MessageBubble
                key={message.id}
                message={message}
                onRegenerate={regenerateResponse}
                onToggleFavorite={toggleMessageFavorite}
                onEdit={editMessage}
                onFollowUpClick={handleFollowUpClick}
                onRelatedQueryClick={handleRelatedQueryClick}
                language={language}
                showTimestamps={showTimestamps}
              />
            ))}
          </AnimatePresence>

          {/* Streaming Response - Token by Token */}
          {isTyping && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-start gap-3"
            >
              <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-primary-700 text-white flex-shrink-0">
                <Sparkles className="w-4 h-4" />
              </div>
              <div className="flex flex-col max-w-[80%]">
                <div className="bg-card border border-border rounded-2xl rounded-tl-sm px-4 py-3">
                  {streamingContent ? (
                    <div className="prose prose-sm dark:prose-invert max-w-none">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          code({ inline, className, children, ...props }: { inline?: boolean; className?: string; children?: React.ReactNode }) {
                            const match = /language-(\w+)/.exec(className || '');
                            return !inline && match ? (
                              <SyntaxHighlighter
                                style={oneDark}
                                language={match[1]}
                                PreTag="div"
                                className="rounded-lg !mt-2 !mb-2"
                                {...props}
                              >
                                {String(children).replace(/\n$/, '')}
                              </SyntaxHighlighter>
                            ) : (
                              <code className="bg-muted px-1.5 py-0.5 rounded text-sm" {...props}>
                                {children}
                              </code>
                            );
                          },
                        }}
                      >
                        {streamingContent}
                      </ReactMarkdown>
                      <span className="inline-block w-2 h-4 bg-primary-500 animate-pulse ml-1" />
                    </div>
                  ) : (
                    <div className="typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-3 mt-2">
                  <span className="text-xs text-muted-foreground flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {elapsedTime.toFixed(1)}s
                  </span>
                  {streamingContent && (
                    <span className="text-xs text-muted-foreground">
                      {streamingContent.split(/\s+/).filter(Boolean).length} {language === 'tr' ? 'kelime' : 'words'}
                    </span>
                  )}
                  <button
                    onClick={stopGeneration}
                    className="flex items-center gap-1 text-xs text-red-500 hover:text-red-600"
                  >
                    <StopCircle className="w-3 h-3" />
                    {t.stop[language]}
                  </button>
                </div>
              </div>
            </motion.div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Quick Template Selector */}
      {templates.length > 0 && (
        <div className="px-4 pb-2">
          <div className="max-w-4xl mx-auto">
            <div className="bg-card border border-border rounded-xl overflow-hidden">
              <button
                onClick={() => setShowTemplates(!showTemplates)}
                className="w-full flex items-center justify-between gap-2 px-4 py-2 hover:bg-accent/50 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <FileCode className="w-4 h-4 text-primary-500" />
                  <span className="text-sm font-medium">
                    {language === 'tr' ? 'Hızlı Şablonlar' : language === 'de' ? 'Schnellvorlagen' : 'Quick Templates'}
                  </span>
                  <span className="text-xs text-muted-foreground">({templates.length})</span>
                </div>
                <ChevronUp className={`w-4 h-4 transition-transform ${showTemplates ? '' : 'rotate-180'}`} />
              </button>
              <AnimatePresence>
                {showTemplates && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="overflow-hidden"
                  >
                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2 p-3 border-t border-border bg-accent/20">
                      {templates.slice(0, 8).map((template) => (
                        <button
                          key={template.id}
                          onClick={() => {
                            setInputValue(template.content);
                            setShowTemplates(false);
                            inputRef.current?.focus();
                          }}
                          className="flex items-center gap-2 p-2 rounded-lg bg-background border border-border hover:border-primary-500/50 hover:shadow-sm transition-all text-left group"
                        >
                          <span className="text-lg">📝</span>
                          <span className="text-xs font-medium truncate group-hover:text-primary-600 transition-colors">
                            {template.title}
                          </span>
                        </button>
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>
      )}

      {/* Image Preview */}
      {imagePreview && (
        <div className="px-4 pb-2">
          <div className="max-w-4xl mx-auto">
            <div className="relative inline-block">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={imagePreview}
                alt="Preview"
                className="h-20 rounded-lg border border-border"
              />
              <button
                onClick={removeImage}
                className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Input Area */}
      <div className="border-t border-border bg-card/50 backdrop-blur-sm p-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-end gap-3 bg-background border border-border rounded-2xl p-2 focus-within:border-primary-400 focus-within:shadow-[0_0_0_3px_rgba(139,92,246,0.1)] transition-all duration-200">
            {/* Image Upload Button */}
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleImageSelect}
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              className="flex items-center justify-center w-10 h-10 rounded-xl hover:bg-accent transition-colors text-muted-foreground hover:text-foreground"
              title={t.addImage[language]}
            >
              <ImageIcon className="w-5 h-5" />
            </button>

            {/* Attachment Button */}
            <div className="relative">
              <button 
                onClick={() => setShowAttachmentTooltip(!showAttachmentTooltip)}
                className="flex items-center justify-center w-10 h-10 rounded-xl hover:bg-accent transition-colors text-muted-foreground hover:text-foreground"
              >
                <Paperclip className="w-5 h-5" />
              </button>
              
              {/* Tooltip */}
              <AnimatePresence>
                {showAttachmentTooltip && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 10 }}
                    className="absolute bottom-full left-0 mb-2 w-64 p-3 bg-card border border-border rounded-xl shadow-lg z-50"
                  >
                    <div className="flex items-start gap-2">
                      <FileText className="w-4 h-4 text-primary-500 mt-0.5 flex-shrink-0" />
                      <p className="text-sm text-foreground">
                        Dökümanlar bölümünden eklediğiniz dökümanlarla ilgili soru sorabilirsiniz.
                      </p>
                    </div>
                    <div className="absolute bottom-0 left-4 transform translate-y-1/2 rotate-45 w-2 h-2 bg-card border-r border-b border-border"></div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Input */}
            <textarea
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={t.placeholder[language]}
              rows={1}
              className="flex-1 resize-none bg-transparent border-none outline-none focus:outline-none focus:ring-0 text-foreground placeholder:text-muted-foreground py-2 max-h-32"
              style={{ minHeight: '40px' }}
            />

            {/* Send Button */}
            <button
              onClick={handleSend}
              disabled={!inputValue.trim() || isTyping}
              className={cn(
                "flex items-center justify-center w-10 h-10 rounded-xl transition-all",
                inputValue.trim() && !isTyping
                  ? "bg-gradient-to-br from-primary-500 to-primary-700 text-white hover:shadow-lg hover:shadow-primary-500/25"
                  : "bg-muted text-muted-foreground"
              )}
            >
              {isTyping ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>

          <p className="text-xs text-center text-muted-foreground mt-2">
            {t.enterToSend[language]}
          </p>
        </div>
      </div>
    </div>
  );
}

// Message Bubble Component
interface MessageBubbleProps {
  message: Message;
  onRegenerate: (id: string) => void;
  onToggleFavorite: (id: string) => void;
  onEdit: (id: string, content: string) => void;
  onFollowUpClick?: (question: string) => void;
  onRelatedQueryClick?: (query: string) => void;
  language: 'tr' | 'en' | 'de';
  showTimestamps?: boolean;
}

function MessageBubble({ message, onRegenerate, onToggleFavorite, onEdit, onFollowUpClick, onRelatedQueryClick, language, showTimestamps = true }: MessageBubbleProps) {
  const [copied, setCopied] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(message.content);
  const isUser = message.role === 'user';

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSaveEdit = () => {
    onEdit(message.id, editContent);
    setIsEditing(false);
  };

  const handleCancelEdit = () => {
    setEditContent(message.content);
    setIsEditing(false);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className={cn(
        "flex gap-3",
        isUser ? "flex-row-reverse" : "flex-row"
      )}
    >
      {/* Avatar */}
      <div className={cn(
        "flex items-center justify-center w-8 h-8 rounded-lg flex-shrink-0",
        isUser
          ? "bg-primary-100 dark:bg-primary-900 text-primary-600 dark:text-primary-400"
          : message.isError
            ? "bg-red-100 dark:bg-red-900 text-red-600 dark:text-red-400"
            : "bg-gradient-to-br from-primary-500 to-primary-700 text-white"
      )}>
        {isUser ? '👤' : message.isError ? <AlertTriangle className="w-4 h-4" /> : <Sparkles className="w-4 h-4" />}
      </div>

      {/* Content */}
      <div className={cn(
        "flex flex-col max-w-[80%]",
        isUser ? "items-end" : "items-start"
      )}>
        <div className={cn(
          "rounded-2xl px-4 py-3 relative group",
          isUser
            ? "bg-primary-500 text-white rounded-tr-sm"
            : message.isError
              ? "bg-gradient-to-br from-red-50 to-red-100 dark:from-red-950/50 dark:to-red-900/30 border-2 border-red-200 dark:border-red-800 rounded-tl-sm text-red-900 dark:text-red-100"
              : "bg-card border border-border rounded-tl-sm"
        )}>
          {/* Error indicator */}
          {message.isError && (
            <div className="absolute -top-2 -right-2 w-5 h-5 bg-red-500 rounded-full flex items-center justify-center shadow-lg">
              <AlertTriangle className="w-3 h-3 text-white" />
            </div>
          )}

          {/* Favorite indicator */}
          {message.isFavorite && !message.isError && (
            <Star className="absolute -top-2 -right-2 w-4 h-4 text-yellow-500 fill-yellow-500" />
          )}

          {/* Edited indicator */}
          {message.isEdited && (
            <span className="absolute -bottom-4 right-0 text-xs text-muted-foreground italic">
              {language === 'tr' ? '(düzenlendi)' : language === 'de' ? '(bearbeitet)' : '(edited)'}
            </span>
          )}

          {isEditing ? (
            <div className="space-y-2">
              <textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                className="w-full min-w-[300px] min-h-[100px] p-2 rounded-lg bg-background text-foreground border border-border"
              />
              <div className="flex gap-2">
                <button
                  onClick={handleSaveEdit}
                  className="flex items-center gap-1 px-3 py-1 bg-green-500 text-white rounded-lg text-sm"
                >
                  <Check className="w-3 h-3" />
                  {language === 'tr' ? 'Kaydet' : 'Save'}
                </button>
                <button
                  onClick={handleCancelEdit}
                  className="flex items-center gap-1 px-3 py-1 bg-muted rounded-lg text-sm"
                >
                  <X className="w-3 h-3" />
                  {language === 'tr' ? 'İptal' : 'Cancel'}
                </button>
              </div>
            </div>
          ) : isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code({ inline, className, children, ...props }: { inline?: boolean; className?: string; children?: React.ReactNode }) {
                    const match = /language-(\w+)/.exec(className || '');
                    return !inline && match ? (
                      <SyntaxHighlighter
                        style={oneDark}
                        language={match[1]}
                        PreTag="div"
                        className="rounded-lg !mt-2 !mb-2"
                        {...props}
                      >
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                    ) : (
                      <code className="bg-muted px-1.5 py-0.5 rounded text-sm" {...props}>
                        {children}
                      </code>
                    );
                  },
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Sources (Premium Box Style) */}
        {message.sources && message.sources.length > 0 && (
          <div className="mt-3 w-full">
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950/30 dark:to-indigo-950/30 border border-blue-200 dark:border-blue-800 rounded-xl p-3">
              <p className="text-xs font-medium text-blue-700 dark:text-blue-400 mb-2 flex items-center gap-1">
                <FileText className="w-3 h-3" />
                {language === 'tr' ? 'Kaynaklar' : language === 'de' ? 'Quellen' : 'Sources'}
              </p>
              <div className="space-y-2">
                {message.sources.map((source, i) => (
                  <a
                    key={i}
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-start gap-2 p-2 rounded-lg bg-white/50 dark:bg-black/20 hover:bg-white dark:hover:bg-black/30 transition-colors group"
                  >
                    <div className="flex-shrink-0 w-6 h-6 rounded-md bg-blue-100 dark:bg-blue-900 flex items-center justify-center text-blue-600 dark:text-blue-400">
                      {source.type === 'web' ? <Globe className="w-3 h-3" /> : <FileText className="w-3 h-3" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-blue-700 dark:text-blue-400 truncate group-hover:underline">
                        {source.title}
                      </p>
                      {source.snippet && (
                        <p className="text-xs text-muted-foreground line-clamp-2 mt-0.5">
                          {source.snippet}
                        </p>
                      )}
                    </div>
                    <ExternalLink className="w-3 h-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                  </a>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Confidence Score */}
        {!isUser && !message.isError && message.confidenceScore !== undefined && (
          <div className="mt-2 w-full">
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1 px-2 py-1 rounded-full bg-amber-100 dark:bg-amber-900/30 border border-amber-200 dark:border-amber-800">
                <Gauge className="w-3 h-3 text-amber-600 dark:text-amber-400" />
                <span className="text-xs font-medium text-amber-700 dark:text-amber-400">
                  {language === 'tr' ? 'Güven' : 'Confidence'}: {Math.round(message.confidenceScore * 100)}%
                </span>
              </div>
              <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
                <div 
                  className={cn(
                    "h-full rounded-full transition-all",
                    message.confidenceScore >= 0.8 ? "bg-green-500" :
                    message.confidenceScore >= 0.5 ? "bg-amber-500" : "bg-red-500"
                  )}
                  style={{ width: `${message.confidenceScore * 100}%` }}
                />
              </div>
            </div>
          </div>
        )}

        {/* Follow-up Questions */}
        {!isUser && !message.isError && message.followUpQuestions && message.followUpQuestions.length > 0 && (
          <div className="mt-3 w-full">
            <div className="bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-950/30 dark:to-pink-950/30 border border-purple-200 dark:border-purple-800 rounded-xl p-3">
              <p className="text-xs font-medium text-purple-700 dark:text-purple-400 mb-2 flex items-center gap-1">
                <HelpCircle className="w-3 h-3" />
                {language === 'tr' ? 'Takip Soruları' : language === 'de' ? 'Folgefragen' : 'Follow-up Questions'}
              </p>
              <div className="space-y-1.5">
                {message.followUpQuestions.map((question, i) => (
                  <button
                    key={i}
                    onClick={() => onFollowUpClick?.(question)}
                    className="w-full flex items-center gap-2 p-2 rounded-lg bg-white/50 dark:bg-black/20 hover:bg-white dark:hover:bg-black/30 transition-colors text-left group"
                  >
                    <span className="text-purple-500">💡</span>
                    <span className="text-sm text-purple-700 dark:text-purple-400 group-hover:underline">
                      {question}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Related Queries */}
        {!isUser && !message.isError && message.relatedQueries && message.relatedQueries.length > 0 && (
          <div className="mt-2 w-full">
            <div className="flex flex-wrap gap-1.5">
              {message.relatedQueries.map((query, i) => (
                <button
                  key={i}
                  onClick={() => onRelatedQueryClick?.(query)}
                  className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-muted hover:bg-accent text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
                >
                  <Search className="w-3 h-3" />
                  {query}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-2 mt-2">
          {/* User message actions */}
          {isUser && (
            <>
              <button
                onClick={() => setIsEditing(true)}
                className="p-1.5 rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground transition-colors"
                title={language === 'tr' ? 'Düzenle' : 'Edit'}
              >
                <Edit className="w-4 h-4" />
              </button>
            </>
          )}

          {/* Common actions */}
          <button
            onClick={handleCopy}
            className="p-1.5 rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground transition-colors"
            title={language === 'tr' ? 'Kopyala' : 'Copy'}
          >
            {copied ? '✓' : <Copy className="w-4 h-4" />}
          </button>

          <button
            onClick={() => onToggleFavorite(message.id)}
            className={cn(
              "p-1.5 rounded-lg transition-colors",
              message.isFavorite
                ? "text-yellow-500 hover:bg-yellow-100 dark:hover:bg-yellow-900/30"
                : "text-muted-foreground hover:text-foreground hover:bg-accent"
            )}
            title={language === 'tr' ? 'Favori' : 'Favorite'}
          >
            <Star className={cn("w-4 h-4", message.isFavorite && "fill-yellow-500")} />
          </button>

          {/* Assistant-only actions */}
          {!isUser && !message.isError && (
            <>
              <button className="p-1.5 rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground transition-colors">
                <ThumbsUp className="w-4 h-4" />
              </button>
              <button className="p-1.5 rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground transition-colors">
                <ThumbsDown className="w-4 h-4" />
              </button>
              <button
                onClick={() => onRegenerate(message.id)}
                className="p-1.5 rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground transition-colors"
                title={language === 'tr' ? 'Yeniden oluştur' : 'Regenerate'}
              >
                <RefreshCw className="w-4 h-4" />
              </button>
            </>
          )}

          {/* Timestamp */}
          {showTimestamps && (
            <span className="text-xs text-muted-foreground ml-2">
              {formatDate(message.timestamp)}
            </span>
          )}

          {/* Response Stats (for assistant messages) */}
          {!isUser && !message.isError && (message.responseTime || message.wordCount) && (
            <div className="flex items-center gap-2 ml-2 px-2 py-0.5 bg-green-100 dark:bg-green-900/30 rounded-full">
              <CheckCircle2 className="w-3 h-3 text-green-600 dark:text-green-400" />
              {message.wordCount && (
                <span className="text-xs text-green-700 dark:text-green-400">
                  {message.wordCount} {language === 'tr' ? 'kelime' : 'words'}
                </span>
              )}
              {message.responseTime && (
                <span className="text-xs text-green-700 dark:text-green-400 flex items-center gap-0.5">
                  <Timer className="w-3 h-3" />
                  {message.responseTime.toFixed(1)}s
                </span>
              )}
            </div>
          )}

          {/* Error Stats */}
          {message.isError && (
            <div className="flex items-center gap-1 ml-2 px-2 py-0.5 bg-red-100 dark:bg-red-900/30 rounded-full">
              <AlertTriangle className="w-3 h-3 text-red-600 dark:text-red-400" />
              <span className="text-xs text-red-700 dark:text-red-400">
                {language === 'tr' ? 'Hata kaydedildi' : 'Error logged'}
              </span>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
