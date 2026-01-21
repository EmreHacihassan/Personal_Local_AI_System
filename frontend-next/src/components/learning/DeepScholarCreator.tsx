'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FileText,
  Sparkles,
  ChevronDown,
  ChevronUp,
  Globe,
  GraduationCap,
  BookOpen,
  Check,
  X,
  Download,
  Loader2,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Settings2,
  Play,
  Pause,
  Eye,
  Brain,
  Search,
  Users,
  Zap,
  Layers,
  Target,
  BookMarked,
  FileCheck,
  MessageSquare,
  Languages,
  Quote,
  ArrowLeft,
  Info,
} from 'lucide-react';

// Types
interface DeepScholarConfig {
  title: string;
  topic: string;
  page_count: number;
  language: string;
  style: string;
  citation_style: string;
  web_search: string;
  academic_search: boolean;
  max_sources_per_section: number;
  enable_fact_checking: boolean;
  enable_user_proxy: boolean;
  enable_conflict_detection: boolean;
  custom_instructions: string;
  user_persona: string;
  parallel_research: boolean;
  max_research_depth: number;
}

interface DeepScholarEvent {
  type: string;
  timestamp?: string;
  phase?: string;
  message?: string;
  progress?: number;
  agent?: string;
  section?: string;
  section_title?: string;
  section_index?: number;
  sources_count?: number;
  sources?: any[];
  data?: any;
  document?: any;
  error?: string;
  conflicts?: any[];
  score?: number;
  clarity?: number;
  issues?: any[];
  verified_count?: number;
  unverified_count?: number;
  word_count?: number;
  content_preview?: string;
}

interface AgentInfo {
  role: string;
  name: string;
  icon: string;
  description: string;
}

// Agent icons mapping
const agentIcons: Record<string, React.ReactNode> = {
  orchestrator: <Target className="w-4 h-4" />,
  planner: <Layers className="w-4 h-4" />,
  researcher: <Search className="w-4 h-4" />,
  writer: <FileText className="w-4 h-4" />,
  fact_checker: <FileCheck className="w-4 h-4" />,
  user_proxy: <Users className="w-4 h-4" />,
  synthesizer: <Zap className="w-4 h-4" />,
};

// Agent colors
const agentColors: Record<string, string> = {
  orchestrator: 'text-purple-500 bg-purple-500/10',
  planner: 'text-blue-500 bg-blue-500/10',
  researcher: 'text-emerald-500 bg-emerald-500/10',
  writer: 'text-amber-500 bg-amber-500/10',
  fact_checker: 'text-green-500 bg-green-500/10',
  user_proxy: 'text-pink-500 bg-pink-500/10',
  synthesizer: 'text-cyan-500 bg-cyan-500/10',
};

// Language options
const languageOptions = [
  { value: 'tr', label: 'Türkçe', flag: '🇹🇷' },
  { value: 'en', label: 'English', flag: '🇬🇧' },
  { value: 'de', label: 'Deutsch', flag: '🇩🇪' },
];

// Citation style options
const citationStyleOptions = [
  { value: 'apa', label: 'APA Style', description: 'American Psychological Association' },
  { value: 'ieee', label: 'IEEE', description: 'Institute of Electrical and Electronics Engineers' },
  { value: 'chicago', label: 'Chicago', description: 'Chicago Manual of Style' },
  { value: 'harvard', label: 'Harvard', description: 'Harvard Referencing' },
];

// Document style options
const styleOptions = [
  { value: 'academic', label: 'Akademik', description: 'Formal, detaylı, teknik dil', icon: <GraduationCap className="w-4 h-4" /> },
  { value: 'casual', label: 'Samimi', description: 'Anlaşılır, akıcı, günlük dil', icon: <MessageSquare className="w-4 h-4" /> },
  { value: 'detailed', label: 'Detaylı', description: 'Her detayı açıklayan, kapsamlı', icon: <BookOpen className="w-4 h-4" /> },
  { value: 'summary', label: 'Özet', description: 'Ana noktaları vurgulayan, kısa', icon: <FileText className="w-4 h-4" /> },
  { value: 'exam_prep', label: 'Sınav Hazırlık', description: 'Önemli noktalar, test odaklı', icon: <Target className="w-4 h-4" /> },
];

// Web search options
const webSearchOptions = [
  { value: 'off', label: 'Kapalı', description: 'Web araması yapma' },
  { value: 'auto', label: 'Otomatik', description: 'Gerektiğinde ara' },
  { value: 'on', label: 'Açık', description: 'Her bölüm için ara' },
];

interface DeepScholarCreatorProps {
  workspaceId: string;
  language: 'tr' | 'en';
  onClose: () => void;
  onComplete: (documentId: string) => void;
  apiUrl?: string;
}

export function DeepScholarCreator({
  workspaceId,
  language,
  onClose,
  onComplete,
  apiUrl = 'http://localhost:8001',
}: DeepScholarCreatorProps) {
  // Form state
  const [title, setTitle] = useState('');
  const [topic, setTopic] = useState('');
  const [pageCount, setPageCount] = useState(10);
  const [docLanguage, setDocLanguage] = useState('tr');
  const [style, setStyle] = useState('academic');
  const [citationStyle, setCitationStyle] = useState('apa');
  const [webSearch, setWebSearch] = useState('auto');
  const [academicSearch, setAcademicSearch] = useState(true);
  const [maxSourcesPerSection, setMaxSourcesPerSection] = useState(10);
  const [enableFactChecking, setEnableFactChecking] = useState(true);
  const [enableUserProxy, setEnableUserProxy] = useState(true);
  const [enableConflictDetection, setEnableConflictDetection] = useState(true);
  const [customInstructions, setCustomInstructions] = useState('');
  const [userPersona, setUserPersona] = useState('');
  const [parallelResearch, setParallelResearch] = useState(true);
  const [maxResearchDepth, setMaxResearchDepth] = useState(3);

  // UI state
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [view, setView] = useState<'form' | 'generating' | 'complete'>('form');
  const [progress, setProgress] = useState(0);
  const [events, setEvents] = useState<DeepScholarEvent[]>([]);
  const [currentPhase, setCurrentPhase] = useState('');
  const [currentAgent, setCurrentAgent] = useState('');
  const [documentId, setDocumentId] = useState<string | null>(null);
  const [finalDocument, setFinalDocument] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  // Refs
  const wsRef = useRef<WebSocket | null>(null);
  const eventsEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll events
  useEffect(() => {
    if (eventsEndRef.current) {
      eventsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [events]);

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // Start generation
  const handleStartGeneration = async () => {
    if (!title.trim() || !topic.trim()) {
      setError('Başlık ve konu zorunludur.');
      return;
    }

    setError(null);
    setView('generating');
    setEvents([]);
    setProgress(0);

    const config: DeepScholarConfig = {
      title,
      topic,
      page_count: pageCount,
      language: docLanguage,
      style,
      citation_style: citationStyle,
      web_search: webSearch,
      academic_search: academicSearch,
      max_sources_per_section: maxSourcesPerSection,
      enable_fact_checking: enableFactChecking,
      enable_user_proxy: enableUserProxy,
      enable_conflict_detection: enableConflictDetection,
      custom_instructions: customInstructions,
      user_persona: userPersona,
      parallel_research: parallelResearch,
      max_research_depth: maxResearchDepth,
    };

    try {
      // Start generation via REST API
      const response = await fetch(`${apiUrl}/api/deep-scholar/generate?workspace_id=${workspaceId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });

      const data = await response.json();

      if (!data.success) {
        setError(data.detail || 'Üretim başlatılamadı');
        setView('form');
        return;
      }

      const docId = data.document_id;
      setDocumentId(docId);

      // Connect WebSocket for live updates
      connectWebSocket(docId);
    } catch (err: any) {
      setError(err.message || 'Bağlantı hatası');
      setView('form');
    }
  };

  // WebSocket connection
  const connectWebSocket = (docId: string) => {
    const wsUrl = apiUrl.replace('http', 'ws') + `/api/deep-scholar/ws/${docId}`;
    
    setEvents(prev => [...prev, {
      type: 'system',
      message: '🔌 WebSocket bağlantısı kuruluyor...',
      timestamp: new Date().toISOString(),
    }]);

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      setEvents(prev => [...prev, {
        type: 'system',
        message: '✅ Bağlantı kuruldu, üretim başlıyor...',
        timestamp: new Date().toISOString(),
      }]);
    };

    ws.onmessage = (event) => {
      try {
        const data: DeepScholarEvent = JSON.parse(event.data);
        handleEvent(data);
      } catch (err) {
        console.error('WebSocket message parse error:', err);
      }
    };

    ws.onerror = (err) => {
      console.error('WebSocket error:', err);
      setEvents(prev => [...prev, {
        type: 'error',
        message: '❌ WebSocket bağlantı hatası',
        timestamp: new Date().toISOString(),
      }]);
    };

    ws.onclose = () => {
      setIsConnected(false);
      setEvents(prev => [...prev, {
        type: 'system',
        message: '🔌 Bağlantı kapatıldı',
        timestamp: new Date().toISOString(),
      }]);
    };
  };

  // Handle WebSocket events
  const handleEvent = (event: DeepScholarEvent) => {
    setEvents(prev => [...prev, event]);

    if (event.progress !== undefined) {
      setProgress(event.progress);
    }

    if (event.phase) {
      setCurrentPhase(event.phase);
    }

    if (event.agent) {
      setCurrentAgent(event.agent);
    }

    switch (event.type) {
      case 'complete':
        setView('complete');
        setFinalDocument(event.document);
        setProgress(100);
        break;

      case 'error':
        setError(event.error || event.message || 'Bilinmeyen hata');
        break;
    }
  };

  // Cancel generation
  const handleCancel = async () => {
    if (documentId) {
      try {
        await fetch(`${apiUrl}/api/deep-scholar/cancel/${documentId}`, {
          method: 'POST',
        });
      } catch (err) {
        console.error('Cancel error:', err);
      }
    }

    if (wsRef.current) {
      wsRef.current.close();
    }

    onClose();
  };

  // Download document
  const handleDownload = async (format: 'pdf' | 'markdown') => {
    if (!documentId) return;

    try {
      if (format === 'pdf') {
        const response = await fetch(`${apiUrl}/api/deep-scholar/export/pdf/${documentId}`, {
          method: 'POST',
        });
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${title.replace(/[^\w\s-]/g, '').trim().replace(/\s+/g, '_')}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      } else {
        const response = await fetch(`${apiUrl}/api/deep-scholar/export/markdown/${documentId}`);
        const text = await response.text();
        const blob = new Blob([text], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${title.replace(/[^\w\s-]/g, '').trim().replace(/\s+/g, '_')}.md`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }
    } catch (err) {
      console.error('Download error:', err);
    }
  };

  // Get depth label
  const getDepthLabel = (pages: number) => {
    if (pages <= 5) return { label: 'Yüzeysel', color: 'text-blue-500' };
    if (pages <= 15) return { label: 'Orta', color: 'text-emerald-500' };
    if (pages <= 30) return { label: 'Derin', color: 'text-amber-500' };
    return { label: 'Kapsamlı', color: 'text-purple-500' };
  };

  // Render event
  const renderEvent = (event: DeepScholarEvent, index: number) => {
    const agentColor = event.agent ? agentColors[event.agent] || 'text-gray-500 bg-gray-500/10' : '';
    const agentIcon = event.agent ? agentIcons[event.agent] : null;

    return (
      <motion.div
        key={index}
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        className="flex items-start gap-3 p-3 rounded-lg hover:bg-accent/30 transition-colors"
      >
        {/* Agent badge */}
        {event.agent && (
          <div className={`flex items-center justify-center w-8 h-8 rounded-lg ${agentColor}`}>
            {agentIcon}
          </div>
        )}
        {!event.agent && event.type === 'error' && (
          <div className="flex items-center justify-center w-8 h-8 rounded-lg text-red-500 bg-red-500/10">
            <AlertCircle className="w-4 h-4" />
          </div>
        )}
        {!event.agent && event.type !== 'error' && (
          <div className="flex items-center justify-center w-8 h-8 rounded-lg text-primary-500 bg-primary-500/10">
            <Sparkles className="w-4 h-4" />
          </div>
        )}

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            {event.phase && (
              <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                {event.phase}
              </span>
            )}
            {event.section_title && (
              <span className="text-xs font-medium text-primary-500">
                📄 {event.section_title}
              </span>
            )}
          </div>
          
          <p className="text-sm text-foreground">
            {event.message}
          </p>

          {/* Sources info */}
          {event.sources_count !== undefined && (
            <p className="text-xs text-muted-foreground mt-1">
              📚 {event.sources_count} kaynak bulundu
            </p>
          )}

          {/* Conflicts */}
          {event.conflicts && event.conflicts.length > 0 && (
            <div className="mt-2 p-2 bg-amber-500/10 rounded-lg">
              <p className="text-xs font-medium text-amber-600">
                ⚠️ {event.conflicts.length} çelişki tespit edildi
              </p>
            </div>
          )}

          {/* Fact check score */}
          {event.score !== undefined && event.type === 'fact_check' && (
            <div className="mt-2 flex items-center gap-2">
              <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                <div 
                  className="h-full bg-green-500 transition-all"
                  style={{ width: `${event.score * 100}%` }}
                />
              </div>
              <span className="text-xs font-medium text-green-600">
                {Math.round(event.score * 100)}%
              </span>
            </div>
          )}

          {/* Word count */}
          {event.word_count !== undefined && (
            <p className="text-xs text-muted-foreground mt-1">
              📝 {event.word_count} kelime
            </p>
          )}
        </div>

        {/* Timestamp */}
        <span className="text-xs text-muted-foreground whitespace-nowrap">
          {event.timestamp ? new Date(event.timestamp).toLocaleTimeString() : ''}
        </span>
      </motion.div>
    );
  };

  // Render form
  const renderForm = () => (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button
          onClick={onClose}
          className="p-2 hover:bg-accent rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="flex items-center gap-2">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 text-white">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xl font-bold">DeepScholar v2.0</h2>
            <p className="text-xs text-muted-foreground">Premium Akademik Döküman Üretici</p>
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-3 p-4 bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800 rounded-xl">
          <AlertCircle className="w-5 h-5 text-red-500" />
          <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
          <button onClick={() => setError(null)} className="ml-auto">
            <X className="w-4 h-4 text-red-500" />
          </button>
        </div>
      )}

      {/* Main form */}
      <div className="bg-card border border-border rounded-2xl p-6 space-y-5">
        {/* Title */}
        <div>
          <label className="block text-sm font-medium mb-2">📝 Döküman Başlığı *</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Örn: Yapay Zeka ve Makine Öğrenmesi Temelleri"
            className="w-full px-4 py-3 bg-background border border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500/50"
          />
        </div>

        {/* Topic */}
        <div>
          <label className="block text-sm font-medium mb-2">🎯 Araştırma Konusu *</label>
          <textarea
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="Dökümanın detaylı konusunu ve kapsamını açıklayın..."
            rows={3}
            className="w-full px-4 py-3 bg-background border border-border rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-primary-500/50"
          />
        </div>

        {/* Page count and language */}
        <div className="grid grid-cols-2 gap-4">
          {/* Page count */}
          <div>
            <label className="block text-sm font-medium mb-2">
              📄 Sayfa Sayısı 
              <span className={`ml-2 text-xs ${getDepthLabel(pageCount).color}`}>
                ({getDepthLabel(pageCount).label})
              </span>
            </label>
            <div className="flex items-center gap-3">
              <input
                type="range"
                min="1"
                max="60"
                value={pageCount}
                onChange={(e) => setPageCount(parseInt(e.target.value))}
                className="flex-1 accent-primary-500"
              />
              <span className="text-lg font-bold w-12 text-center">{pageCount}</span>
            </div>
          </div>

          {/* Language */}
          <div>
            <label className="block text-sm font-medium mb-2">🌍 Dil</label>
            <div className="flex gap-2">
              {languageOptions.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setDocLanguage(opt.value)}
                  className={`flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl border transition-all ${
                    docLanguage === opt.value
                      ? 'border-primary-500 bg-primary-500/10 text-primary-600'
                      : 'border-border hover:border-primary-500/50'
                  }`}
                >
                  <span>{opt.flag}</span>
                  <span className="text-sm">{opt.label}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Style */}
        <div>
          <label className="block text-sm font-medium mb-2">✨ Yazım Stili</label>
          <div className="grid grid-cols-5 gap-2">
            {styleOptions.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setStyle(opt.value)}
                className={`flex flex-col items-center gap-2 p-3 rounded-xl border transition-all ${
                  style === opt.value
                    ? 'border-primary-500 bg-primary-500/10 text-primary-600'
                    : 'border-border hover:border-primary-500/50'
                }`}
              >
                {opt.icon}
                <span className="text-xs font-medium">{opt.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Citation style */}
        <div>
          <label className="block text-sm font-medium mb-2">📚 Kaynakça Stili</label>
          <div className="grid grid-cols-4 gap-2">
            {citationStyleOptions.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setCitationStyle(opt.value)}
                className={`flex flex-col items-center gap-1 p-3 rounded-xl border transition-all ${
                  citationStyle === opt.value
                    ? 'border-primary-500 bg-primary-500/10'
                    : 'border-border hover:border-primary-500/50'
                }`}
              >
                <span className="font-bold text-sm">{opt.label}</span>
                <span className="text-xs text-muted-foreground text-center line-clamp-1">
                  {opt.description}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Advanced settings toggle */}
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          <Settings2 className="w-4 h-4" />
          Gelişmiş Ayarlar
          {showAdvanced ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>

        {/* Advanced settings */}
        <AnimatePresence>
          {showAdvanced && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="space-y-4 overflow-hidden"
            >
              {/* Research settings */}
              <div className="p-4 bg-accent/30 rounded-xl space-y-4">
                <h4 className="text-sm font-medium flex items-center gap-2">
                  <Search className="w-4 h-4" /> Araştırma Ayarları
                </h4>

                {/* Web search */}
                <div>
                  <label className="block text-xs font-medium mb-2">Web Araması</label>
                  <div className="flex gap-2">
                    {webSearchOptions.map((opt) => (
                      <button
                        key={opt.value}
                        onClick={() => setWebSearch(opt.value)}
                        className={`flex-1 px-3 py-2 rounded-lg text-xs transition-all ${
                          webSearch === opt.value
                            ? 'bg-primary-500 text-white'
                            : 'bg-background border border-border hover:border-primary-500/50'
                        }`}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Academic search */}
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">Akademik Arama</p>
                    <p className="text-xs text-muted-foreground">Semantic Scholar, arXiv, CrossRef</p>
                  </div>
                  <button
                    onClick={() => setAcademicSearch(!academicSearch)}
                    className={`w-12 h-6 rounded-full transition-colors ${
                      academicSearch ? 'bg-primary-500' : 'bg-muted'
                    }`}
                  >
                    <div className={`w-5 h-5 bg-white rounded-full shadow transition-transform ${
                      academicSearch ? 'translate-x-6' : 'translate-x-0.5'
                    }`} />
                  </button>
                </div>

                {/* Max sources */}
                <div>
                  <label className="block text-xs font-medium mb-2">
                    Bölüm Başına Maks. Kaynak: {maxSourcesPerSection}
                  </label>
                  <input
                    type="range"
                    min="3"
                    max="20"
                    value={maxSourcesPerSection}
                    onChange={(e) => setMaxSourcesPerSection(parseInt(e.target.value))}
                    className="w-full accent-primary-500"
                  />
                </div>

                {/* Research depth */}
                <div>
                  <label className="block text-xs font-medium mb-2">
                    Fraktal Araştırma Derinliği: {maxResearchDepth}
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="5"
                    value={maxResearchDepth}
                    onChange={(e) => setMaxResearchDepth(parseInt(e.target.value))}
                    className="w-full accent-primary-500"
                  />
                </div>
              </div>

              {/* Quality settings */}
              <div className="p-4 bg-accent/30 rounded-xl space-y-3">
                <h4 className="text-sm font-medium flex items-center gap-2">
                  <CheckCircle className="w-4 h-4" /> Kalite Kontrolleri
                </h4>

                {/* Fact checking */}
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm">Doğrulama (Fact-Check)</p>
                    <p className="text-xs text-muted-foreground">Halüsinasyon kontrolü</p>
                  </div>
                  <button
                    onClick={() => setEnableFactChecking(!enableFactChecking)}
                    className={`w-12 h-6 rounded-full transition-colors ${
                      enableFactChecking ? 'bg-primary-500' : 'bg-muted'
                    }`}
                  >
                    <div className={`w-5 h-5 bg-white rounded-full shadow transition-transform ${
                      enableFactChecking ? 'translate-x-6' : 'translate-x-0.5'
                    }`} />
                  </button>
                </div>

                {/* User proxy */}
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm">Okuyucu Simülasyonu</p>
                    <p className="text-xs text-muted-foreground">User Proxy değerlendirmesi</p>
                  </div>
                  <button
                    onClick={() => setEnableUserProxy(!enableUserProxy)}
                    className={`w-12 h-6 rounded-full transition-colors ${
                      enableUserProxy ? 'bg-primary-500' : 'bg-muted'
                    }`}
                  >
                    <div className={`w-5 h-5 bg-white rounded-full shadow transition-transform ${
                      enableUserProxy ? 'translate-x-6' : 'translate-x-0.5'
                    }`} />
                  </button>
                </div>

                {/* Conflict detection */}
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm">Çelişki Tespiti</p>
                    <p className="text-xs text-muted-foreground">Kaynak çapraz kontrolü</p>
                  </div>
                  <button
                    onClick={() => setEnableConflictDetection(!enableConflictDetection)}
                    className={`w-12 h-6 rounded-full transition-colors ${
                      enableConflictDetection ? 'bg-primary-500' : 'bg-muted'
                    }`}
                  >
                    <div className={`w-5 h-5 bg-white rounded-full shadow transition-transform ${
                      enableConflictDetection ? 'translate-x-6' : 'translate-x-0.5'
                    }`} />
                  </button>
                </div>
              </div>

              {/* Custom instructions */}
              <div>
                <label className="block text-sm font-medium mb-2">
                  💬 Özel Talimatlar (Opsiyonel)
                </label>
                <textarea
                  value={customInstructions}
                  onChange={(e) => setCustomInstructions(e.target.value)}
                  placeholder="AI'ya özel talimatlar verin..."
                  rows={3}
                  className="w-full px-4 py-3 bg-background border border-border rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-primary-500/50 text-sm"
                />
              </div>

              {/* User persona */}
              <div>
                <label className="block text-sm font-medium mb-2">
                  👤 Hedef Okuyucu Profili (Opsiyonel)
                </label>
                <input
                  type="text"
                  value={userPersona}
                  onChange={(e) => setUserPersona(e.target.value)}
                  placeholder="Örn: Lisans öğrencisi, teknik olmayan okuyucu, uzman araştırmacı"
                  className="w-full px-4 py-2.5 bg-background border border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500/50 text-sm"
                />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Info box */}
      <div className="flex items-start gap-3 p-4 bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-xl">
        <Info className="w-5 h-5 text-blue-500 mt-0.5" />
        <div>
          <p className="text-sm font-medium text-blue-700 dark:text-blue-300">
            DeepScholar v2.0 Özellikleri
          </p>
          <ul className="text-xs text-blue-600 dark:text-blue-400 mt-1 space-y-1">
            <li>• Fraktal Araştırma ile dinamik derinlik</li>
            <li>• 6 uzman ajan (Planlayıcı, Araştırmacı, Yazar, Doğrulayıcı, Okuyucu, Sentezci)</li>
            <li>• Akademik kaynak entegrasyonu (Semantic Scholar, arXiv, CrossRef)</li>
            <li>• Çelişki tespiti ve kaynak sentezi</li>
            <li>• Profesyonel kaynakça (APA, IEEE, Chicago, Harvard)</li>
          </ul>
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-end gap-3">
        <button
          onClick={onClose}
          className="px-6 py-2.5 rounded-xl border border-border hover:bg-accent transition-colors"
        >
          İptal
        </button>
        <button
          onClick={handleStartGeneration}
          disabled={!title.trim() || !topic.trim()}
          className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-xl hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Sparkles className="w-4 h-4" />
          Üretimi Başlat
        </button>
      </div>
    </div>
  );

  // Render generating view
  const renderGenerating = () => (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 text-white animate-pulse">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xl font-bold">DeepScholar Üretiyor...</h2>
            <p className="text-sm text-muted-foreground">
              {title}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-amber-500'} animate-pulse`} />
          <span className="text-xs text-muted-foreground">
            {isConnected ? 'Bağlı' : 'Bağlanıyor...'}
          </span>
        </div>
      </div>

      {/* Progress */}
      <div className="bg-card border border-border rounded-2xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium capitalize">{currentPhase || 'Başlatılıyor...'}</span>
          <span className="text-sm font-bold text-primary-500">{progress}%</span>
        </div>
        <div className="h-3 bg-muted rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-purple-500 to-pink-500"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.3 }}
          />
        </div>

        {/* Current agent */}
        {currentAgent && (
          <div className="flex items-center gap-2">
            <div className={`flex items-center justify-center w-6 h-6 rounded-lg ${agentColors[currentAgent] || 'text-gray-500 bg-gray-500/10'}`}>
              {agentIcons[currentAgent] || <Brain className="w-3 h-3" />}
            </div>
            <span className="text-sm text-muted-foreground capitalize">{currentAgent.replace('_', ' ')}</span>
          </div>
        )}
      </div>

      {/* Events log */}
      <div className="bg-card border border-border rounded-2xl overflow-hidden">
        <div className="px-4 py-3 bg-accent/30 border-b border-border flex items-center justify-between">
          <h3 className="text-sm font-medium flex items-center gap-2">
            <Eye className="w-4 h-4" /> Agent Aktivitesi
          </h3>
          <span className="text-xs text-muted-foreground">{events.length} olay</span>
        </div>
        <div className="max-h-[400px] overflow-y-auto p-2 space-y-1">
          {events.map((event, index) => renderEvent(event, index))}
          <div ref={eventsEndRef} />
        </div>
      </div>

      {/* Cancel button */}
      <div className="flex justify-center">
        <button
          onClick={handleCancel}
          className="flex items-center gap-2 px-6 py-2.5 text-red-500 hover:bg-red-500/10 rounded-xl transition-colors"
        >
          <X className="w-4 h-4" />
          İptal Et
        </button>
      </div>
    </div>
  );

  // Render complete view
  const renderComplete = () => (
    <div className="space-y-6">
      {/* Success header */}
      <div className="text-center py-6">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 dark:bg-green-900/30 text-green-500 mb-4"
        >
          <CheckCircle className="w-8 h-8" />
        </motion.div>
        <h2 className="text-2xl font-bold">Döküman Hazır!</h2>
        <p className="text-muted-foreground mt-1">{title}</p>
      </div>

      {/* Stats */}
      {finalDocument && (
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-card border border-border rounded-xl p-4 text-center">
            <FileText className="w-6 h-6 mx-auto text-primary-500 mb-2" />
            <p className="text-2xl font-bold">{finalDocument.page_count || pageCount}</p>
            <p className="text-xs text-muted-foreground">Sayfa</p>
          </div>
          <div className="bg-card border border-border rounded-xl p-4 text-center">
            <BookMarked className="w-6 h-6 mx-auto text-emerald-500 mb-2" />
            <p className="text-2xl font-bold">{finalDocument.word_count || 0}</p>
            <p className="text-xs text-muted-foreground">Kelime</p>
          </div>
          <div className="bg-card border border-border rounded-xl p-4 text-center">
            <Quote className="w-6 h-6 mx-auto text-amber-500 mb-2" />
            <p className="text-2xl font-bold">{finalDocument.citations_count || 0}</p>
            <p className="text-xs text-muted-foreground">Kaynak</p>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex flex-col gap-3">
        <button
          onClick={() => documentId && onComplete(documentId)}
          className="flex items-center justify-center gap-2 w-full px-6 py-3 bg-primary-500 text-white rounded-xl hover:bg-primary-600 transition-colors"
        >
          <Eye className="w-5 h-5" />
          Dökümanı Görüntüle
        </button>
        
        <div className="flex gap-3">
          <button
            onClick={() => handleDownload('markdown')}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 border border-border rounded-xl hover:bg-accent transition-colors"
          >
            <Download className="w-4 h-4" />
            Markdown
          </button>
          <button
            onClick={() => handleDownload('pdf')}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 border border-border rounded-xl hover:bg-accent transition-colors"
          >
            <Download className="w-4 h-4" />
            PDF
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="max-w-3xl mx-auto">
      <AnimatePresence mode="wait">
        {view === 'form' && (
          <motion.div
            key="form"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            {renderForm()}
          </motion.div>
        )}
        {view === 'generating' && (
          <motion.div
            key="generating"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            {renderGenerating()}
          </motion.div>
        )}
        {view === 'complete' && (
          <motion.div
            key="complete"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            {renderComplete()}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default DeepScholarCreator;
