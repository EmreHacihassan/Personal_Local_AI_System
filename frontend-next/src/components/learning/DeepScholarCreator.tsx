'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FileText,
  Sparkles,
  ChevronDown,
  ChevronUp,
  GraduationCap,
  BookOpen,
  X,
  Download,
  Loader2,
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
  Quote,
  ArrowLeft,
  Info,
  BarChart3,
  GitBranch,
  Code,
  Table,
  TrendingUp,
} from 'lucide-react';

// Premium Resilience Components
import { 
  DeepScholarResiliencePanel, 
  useTabProtection
} from './DeepScholarResilience';

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
  // Görsel ayarları
  enable_visuals: boolean;
  visual_types: string[];
  visuals_per_section: number;
  enable_code_examples: boolean;
  enable_formulas: boolean;
}

interface VisualItem {
  type: string;
  title: string;
  code?: string;
  data?: any;
  render_type: string;
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
  section_level?: number;
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
  content?: string;
  content_preview?: string;
  // Görsel ve pause/resume
  visuals?: VisualItem[];
  visual?: VisualItem;
  visual_type?: string;
  visual_title?: string;
  checkpoint_id?: string;
  completed_sections?: number;
  pending_sections?: number;
  // 🚀 Premium V2 Event Fields
  thought?: string;  // agent_thinking için
  originality_score?: number;
  similarity_index?: number;
  unique_phrases_ratio?: number;
  citation_count?: number;
  quality_score?: number;
  diversity_score?: number;
  recency_score?: number;
  topic_clusters?: string[];
  gaps?: string[];
  recommendations?: string[];
}

interface CompletedSection {
  id: string;
  title: string;
  level: number;
  content: string;
  wordCount: number;
}

interface AgentThought {
  agent: string;
  message: string;
  timestamp: string;
  type: 'thinking' | 'action' | 'result';
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
  // Reconnect desteği - devam eden bir üretimi takip etmek için
  reconnectDocumentId?: string | null;
  // Initial values - "Yeniden Oluştur" için
  initialTitle?: string;
  initialTopic?: string;
  initialPageCount?: number;
  initialStyle?: string;
}

export function DeepScholarCreator({
  workspaceId,
  language: _language,
  onClose,
  onComplete,
  apiUrl = 'http://localhost:8001',
  reconnectDocumentId = null,
  initialTitle = '',
  initialTopic = '',
  initialPageCount = 10,
  initialStyle = 'academic',
}: DeepScholarCreatorProps) {
  // Form state
  const [title, setTitle] = useState(initialTitle);
  const [topic, setTopic] = useState(initialTopic);
  const [pageCount, setPageCount] = useState(initialPageCount);
  const [docLanguage, setDocLanguage] = useState('tr');
  const [style, setStyle] = useState(initialStyle);
  const [citationStyle, setCitationStyle] = useState('apa');
  const [webSearch, setWebSearch] = useState('auto');
  const [academicSearch, setAcademicSearch] = useState(true);
  const [maxSourcesPerSection, setMaxSourcesPerSection] = useState(10);
  const [enableFactChecking, setEnableFactChecking] = useState(true);
  const [enableUserProxy, setEnableUserProxy] = useState(true);
  const [enableConflictDetection, setEnableConflictDetection] = useState(true);
  const [customInstructions, setCustomInstructions] = useState('');
  const [userPersona, setUserPersona] = useState('');
  const [parallelResearch, _setParallelResearch] = useState(true);
  const [maxResearchDepth, setMaxResearchDepth] = useState(3);
  // Görsel ayarları
  const [enableVisuals, setEnableVisuals] = useState(true);
  const [visualsPerSection, setVisualsPerSection] = useState(2);
  const [enableCodeExamples, setEnableCodeExamples] = useState(true);
  const [enableFormulas, setEnableFormulas] = useState(true);

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
  const [_isConnected, setIsConnected] = useState(false);
  
  // Pause/Resume state
  const [isPaused, setIsPaused] = useState(false);
  const [_canResume, setCanResume] = useState(false);
  
  // Live preview state
  const [completedSections, setCompletedSections] = useState<CompletedSection[]>([]);
  const [agentThoughts, setAgentThoughts] = useState<AgentThought[]>([]);
  const [generatedVisuals, setGeneratedVisuals] = useState<VisualItem[]>([]);
  const [_showPreview, _setShowPreview] = useState(true);
  const [activeTab, setActiveTab] = useState<'preview' | 'thinking' | 'activity' | 'visuals'>('preview');

  // Refs
  const wsRef = useRef<WebSocket | null>(null);
  const eventsEndRef = useRef<HTMLDivElement>(null);
  const previewEndRef = useRef<HTMLDivElement>(null);
  const thoughtsEndRef = useRef<HTMLDivElement>(null);

  // 🛡️ Premium Tab Protection - Sayfa kapatılırken uyarı göster
  useTabProtection(
    view === 'generating' && !isPaused,
    '⚠️ DeepScholar döküman üretimi devam ediyor! Sayfayı kapatırsanız ilerleme kaybedilir.'
  );

  // Auto-scroll events
  useEffect(() => {
    if (eventsEndRef.current) {
      eventsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [events]);
  
  // Auto-scroll preview
  useEffect(() => {
    if (previewEndRef.current && activeTab === 'preview') {
      previewEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [completedSections, activeTab]);
  
  // Auto-scroll thoughts
  useEffect(() => {
    if (thoughtsEndRef.current && activeTab === 'thinking') {
      thoughtsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [agentThoughts, activeTab]);

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // Update form when initial values change (for "Yeniden Oluştur")
  useEffect(() => {
    if (initialTitle) setTitle(initialTitle);
    if (initialTopic) setTopic(initialTopic);
    if (initialPageCount) setPageCount(initialPageCount);
    if (initialStyle) setStyle(initialStyle);
  }, [initialTitle, initialTopic, initialPageCount, initialStyle]);

  // Reconnect to an existing generation
  useEffect(() => {
    if (reconnectDocumentId) {
      // Önce durumu kontrol et
      fetch(`${apiUrl}/api/deep-scholar/status/${reconnectDocumentId}`)
        .then(res => {
          if (!res.ok) {
            throw new Error(`Status: ${res.status}`);
          }
          return res.json();
        })
        .then(data => {
          console.log('[DeepScholar] Status check result:', data);
          
          if (data.active && data.can_reconnect) {
            // Aktif üretim var, reconnect yap
            setDocumentId(reconnectDocumentId);
            setView('generating');
            setProgress(data.progress || 0);
            setCurrentPhase(data.current_phase || '');
            setCurrentAgent(data.current_agent || '');
            
            // WebSocket bağlantısı kur
            const wsUrl = apiUrl.replace('http', 'ws');
            const ws = new WebSocket(`${wsUrl}/api/deep-scholar/ws/${reconnectDocumentId}`);
            
            ws.onopen = () => {
              setIsConnected(true);
              console.log('[DeepScholar] Reconnected to WebSocket');
            };
            
            ws.onmessage = (event) => {
              const eventData = JSON.parse(event.data);
              handleEvent(eventData);
            };
            
            ws.onerror = (err) => {
              console.error('[DeepScholar] WebSocket error:', err);
              setError('Bağlantı hatası');
            };
            
            ws.onclose = () => {
              setIsConnected(false);
              console.log('[DeepScholar] WebSocket closed');
            };
            
            wsRef.current = ws;
          } else {
            // Aktif üretim yok - stale generating durumu
            // Kullanıcıya bilgi ver ve yeniden başlatma seçeneği sun
            setError('Üretim artık aktif değil. Sayfadan çıkıldığında üretim durduruldu. Lütfen yeniden başlatın.');
            setView('form');
          }
        })
        .catch(err => {
          console.error('[DeepScholar] Status check failed:', err);
          // 404 veya diğer hatalar - üretim yok
          setError('Bu döküman için aktif üretim bulunamadı. Lütfen yeniden başlatın.');
          setView('form');
        });
    }
  }, [reconnectDocumentId, apiUrl]);

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
    setCompletedSections([]);
    setAgentThoughts([]);
    setGeneratedVisuals([]);
    setActiveTab('preview');
    setIsPaused(false);

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
      // Görsel ayarları
      enable_visuals: enableVisuals,
      visual_types: ['mermaid_flowchart', 'mermaid_mindmap', 'ascii_table', 'statistics_box'],
      visuals_per_section: visualsPerSection,
      enable_code_examples: enableCodeExamples,
      enable_formulas: enableFormulas,
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

      // Queue bilgisini göster
      if (data.queue_position && data.queue_position > 1) {
        setEvents(prev => [...prev, {
          type: 'system',
          message: `📋 Kuyruğa eklendi (Sıra: ${data.queue_position}). Önceki dökümanlar tamamlandığında başlayacak...`,
          timestamp: new Date().toISOString(),
        }]);
      }

      // Hemen başladıysa veya kuyruk sonuysa WebSocket bağlan
      if (data.is_immediate) {
        connectWebSocket(docId);
      } else {
        // Kuyrukta bekliyor - polling ile kontrol et
        setEvents(prev => [...prev, {
          type: 'system',
          message: `⏳ Kuyrukta bekleniyor... Sıra geldiğinde otomatik başlayacak.`,
          timestamp: new Date().toISOString(),
        }]);
        
        // Poll for queue position and auto-connect when ready
        const pollQueue = setInterval(async () => {
          try {
            const statusRes = await fetch(`${apiUrl}/api/deep-scholar/status/${docId}`);
            const statusData = await statusRes.json();
            
            if (statusData.active || statusData.status === 'generating') {
              clearInterval(pollQueue);
              connectWebSocket(docId);
            } else if (statusData.status === 'completed') {
              clearInterval(pollQueue);
              setView('complete');
            } else if (statusData.status === 'cancelled' || statusData.status === 'error') {
              clearInterval(pollQueue);
              setError('Üretim iptal edildi veya hata oluştu');
              setView('form');
            }
          } catch (e) {
            // Polling devam etsin
          }
        }, 3000);
      }
    } catch (_err: any) {
      setError(_err.message || 'Bağlantı hatası');
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

    // Handle section complete - add to live preview
    if (event.type === 'section_complete' && event.content) {
      const sectionContent = event.content;
      setCompletedSections(prev => [...prev, {
        id: `section-${event.section_index}`,
        title: event.section_title || 'Bölüm',
        level: event.section_level || 1,
        content: sectionContent,
        wordCount: event.word_count || 0
      }]);
    }
    
    // Handle visual generated - add to visuals list
    if (event.type === 'visual_generated' && event.visual) {
      setGeneratedVisuals(prev => [...prev, event.visual!]);
    }
    
    // Handle agent messages - add to thinking panel
    if (event.type === 'agent_message' && event.agent && event.message) {
      const thoughtType = event.message.includes('🧠') || event.message.includes('Düşünüyor') 
        ? 'thinking' as const
        : event.message.includes('✅') || event.message.includes('tamamlandı')
        ? 'result' as const
        : 'action' as const;
        
      setAgentThoughts(prev => [...prev, {
        agent: event.agent!,
        message: event.message!,
        timestamp: event.timestamp || new Date().toISOString(),
        type: thoughtType
      }]);
    }
    
    // 🚀 Handle agent thinking - for live thoughts
    if (event.type === 'agent_thinking' && event.agent && event.thought) {
      setAgentThoughts(prev => [...prev, {
        agent: event.agent!,
        message: event.thought!,
        timestamp: event.timestamp || new Date().toISOString(),
        type: 'thinking'
      }]);
    }
    
    // 🚀 Handle originality check result
    if (event.type === 'originality_check') {
      setAgentThoughts(prev => [...prev, {
        agent: 'OriginalityChecker',
        message: `📊 Orijinallik: ${(event.originality_score * 100).toFixed(0)}% | Benzerlik: ${(event.similarity_index * 100).toFixed(0)}%`,
        timestamp: new Date().toISOString(),
        type: 'result'
      }]);
    }
    
    // 🚀 Handle research analytics
    if (event.type === 'research_analytics') {
      setAgentThoughts(prev => [...prev, {
        agent: 'ResearchAnalytics',
        message: `📊 Kalite: ${event.quality_score}/100 | Çeşitlilik: ${(event.diversity_score * 100).toFixed(0)}% | Güncellik: ${(event.recency_score * 100).toFixed(0)}%`,
        timestamp: new Date().toISOString(),
        type: 'result'
      }]);
    }

    switch (event.type) {
      case 'complete':
        setView('complete');
        setFinalDocument(event.document);
        setProgress(100);
        setIsPaused(false);
        break;

      case 'error':
        setError(event.error || event.message || 'Bilinmeyen hata');
        break;
      
      case 'paused':
        setIsPaused(true);
        setCanResume(true);
        break;
      
      case 'resumed':
        setIsPaused(false);
        break;
    }
  };
  
  // Pause generation
  const handlePause = async () => {
    if (documentId) {
      try {
        await fetch(`${apiUrl}/api/deep-scholar/pause/${documentId}`, {
          method: 'POST',
        });
        setIsPaused(true);
      } catch (err) {
        console.error('Pause error:', err);
      }
    }
  };
  
  // Resume generation
  const handleResume = async () => {
    if (documentId) {
      try {
        await fetch(`${apiUrl}/api/deep-scholar/resume/${documentId}`, {
          method: 'POST',
        });
        setIsPaused(false);
      } catch (err) {
        console.error('Resume error:', err);
      }
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

              {/* Visual Generation Settings - Premium Feature */}
              <div className="p-4 bg-gradient-to-br from-purple-500/10 to-pink-500/10 rounded-xl space-y-3 border border-purple-500/20">
                <h4 className="text-sm font-medium flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-purple-500" /> 
                  Görsel Üretimi
                  <span className="ml-auto px-2 py-0.5 text-xs bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-full">
                    Premium
                  </span>
                </h4>

                {/* Enable visuals */}
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm">Görsel Üretimini Aktifleştir</p>
                    <p className="text-xs text-muted-foreground">Diyagram, grafik ve tablolar</p>
                  </div>
                  <button
                    onClick={() => setEnableVisuals(!enableVisuals)}
                    className={`w-12 h-6 rounded-full transition-colors ${
                      enableVisuals ? 'bg-gradient-to-r from-purple-500 to-pink-500' : 'bg-muted'
                    }`}
                  >
                    <div className={`w-5 h-5 bg-white rounded-full shadow transition-transform ${
                      enableVisuals ? 'translate-x-6' : 'translate-x-0.5'
                    }`} />
                  </button>
                </div>

                {enableVisuals && (
                  <>
                    {/* Visuals per section */}
                    <div>
                      <label className="block text-xs font-medium mb-2">
                        Bölüm Başına Görsel: {visualsPerSection}
                      </label>
                      <input
                        type="range"
                        min="1"
                        max="5"
                        value={visualsPerSection}
                        onChange={(e) => setVisualsPerSection(parseInt(e.target.value))}
                        className="w-full accent-purple-500"
                      />
                    </div>

                    {/* Code examples */}
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm">Kod Örnekleri</p>
                        <p className="text-xs text-muted-foreground">Python, JavaScript vb.</p>
                      </div>
                      <button
                        onClick={() => setEnableCodeExamples(!enableCodeExamples)}
                        className={`w-12 h-6 rounded-full transition-colors ${
                          enableCodeExamples ? 'bg-purple-500' : 'bg-muted'
                        }`}
                      >
                        <div className={`w-5 h-5 bg-white rounded-full shadow transition-transform ${
                          enableCodeExamples ? 'translate-x-6' : 'translate-x-0.5'
                        }`} />
                      </button>
                    </div>

                    {/* Formulas */}
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm">Matematiksel Formüller</p>
                        <p className="text-xs text-muted-foreground">LaTeX formüller</p>
                      </div>
                      <button
                        onClick={() => setEnableFormulas(!enableFormulas)}
                        className={`w-12 h-6 rounded-full transition-colors ${
                          enableFormulas ? 'bg-purple-500' : 'bg-muted'
                        }`}
                      >
                        <div className={`w-5 h-5 bg-white rounded-full shadow transition-transform ${
                          enableFormulas ? 'translate-x-6' : 'translate-x-0.5'
                        }`} />
                      </button>
                    </div>

                    {/* Visual types info */}
                    <div className="mt-2 p-3 bg-accent/50 rounded-lg">
                      <p className="text-xs text-muted-foreground">
                        <span className="font-medium text-foreground">Desteklenen görseller:</span>
                        {' '}Akış diyagramları, zihin haritaları, zaman çizelgeleri, pasta grafikler, 
                        karşılaştırma tabloları, istatistik kutuları, kod blokları
                      </p>
                    </div>
                  </>
                )}
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
    <div className="space-y-4">
      {/* Header with Resilience Panel */}
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
        
        {/* Premium Resilience Panel */}
        <DeepScholarResiliencePanel
          documentId={documentId}
          workspaceId={workspaceId}
          isGenerating={view === 'generating'}
          apiUrl={apiUrl}
          onResumeFromCheckpoint={(checkpoint) => {
            setProgress(checkpoint.progress);
            setCurrentPhase(checkpoint.current_phase);
          }}
          onPartialExport={(filepath) => {
            console.log('Partial export created:', filepath);
          }}
        />
      </div>

      {/* Progress */}
      <div className="bg-card border border-border rounded-2xl p-4 space-y-3">
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

        {/* Current agent and Pause/Resume */}
        <div className="flex items-center justify-between">
          {currentAgent && (
            <div className="flex items-center gap-2">
              <div className={`flex items-center justify-center w-6 h-6 rounded-lg ${agentColors[currentAgent] || 'text-gray-500 bg-gray-500/10'}`}>
                {agentIcons[currentAgent] || <Brain className="w-3 h-3" />}
              </div>
              <span className="text-sm text-muted-foreground capitalize">{currentAgent.replace('_', ' ')}</span>
            </div>
          )}
          
          {/* Pause/Resume Buttons */}
          <div className="flex items-center gap-2">
            {isPaused ? (
              <>
                <span className="text-xs text-amber-500 flex items-center gap-1">
                  <Pause className="w-3 h-3" />
                  Duraklatıldı
                </span>
                <motion.button
                  onClick={handleResume}
                  className="flex items-center gap-1 px-3 py-1.5 bg-green-500 text-white rounded-lg text-sm font-medium hover:bg-green-600 transition-colors"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <Play className="w-4 h-4" />
                  Devam Et
                </motion.button>
              </>
            ) : (
              <motion.button
                onClick={handlePause}
                className="flex items-center gap-1 px-3 py-1.5 bg-amber-500 text-white rounded-lg text-sm font-medium hover:bg-amber-600 transition-colors"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <Pause className="w-4 h-4" />
                Duraklat
              </motion.button>
            )}
            <motion.button
              onClick={handleCancel}
              className="flex items-center gap-1 px-3 py-1.5 bg-red-500/10 text-red-500 rounded-lg text-sm font-medium hover:bg-red-500/20 transition-colors"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <X className="w-4 h-4" />
              İptal
            </motion.button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 bg-card border border-border rounded-xl p-1">
        <button
          onClick={() => setActiveTab('preview')}
          className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            activeTab === 'preview'
              ? 'bg-primary-500 text-white'
              : 'hover:bg-accent text-muted-foreground'
          }`}
        >
          <FileText className="w-4 h-4" />
          Canlı Önizleme
          {completedSections.length > 0 && (
            <span className="ml-1 px-1.5 py-0.5 text-xs rounded-full bg-white/20">
              {completedSections.length}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('thinking')}
          className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            activeTab === 'thinking'
              ? 'bg-primary-500 text-white'
              : 'hover:bg-accent text-muted-foreground'
          }`}
        >
          <Brain className="w-4 h-4" />
          Agent Düşünceleri
          {agentThoughts.length > 0 && (
            <span className="ml-1 px-1.5 py-0.5 text-xs rounded-full bg-white/20">
              {agentThoughts.length}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('activity')}
          className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            activeTab === 'activity'
              ? 'bg-primary-500 text-white'
              : 'hover:bg-accent text-muted-foreground'
          }`}
        >
          <Eye className="w-4 h-4" />
          Aktivite
          <span className="ml-1 px-1.5 py-0.5 text-xs rounded-full bg-white/20">
            {events.length}
          </span>
        </button>
        {enableVisuals && (
          <button
            onClick={() => setActiveTab('visuals')}
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'visuals'
                ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white'
                : 'hover:bg-accent text-muted-foreground'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            Görseller
            {generatedVisuals.length > 0 && (
              <span className="ml-1 px-1.5 py-0.5 text-xs rounded-full bg-white/20">
                {generatedVisuals.length}
              </span>
            )}
          </button>
        )}
      </div>

      {/* Tab content */}
      <div className="bg-card border border-border rounded-2xl overflow-hidden">
        <AnimatePresence mode="wait">
          {activeTab === 'preview' && (
            <motion.div
              key="preview"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="max-h-[500px] overflow-y-auto"
            >
              <div className="px-4 py-3 bg-gradient-to-r from-purple-500/10 to-pink-500/10 border-b border-border flex items-center justify-between sticky top-0 backdrop-blur-sm z-10">
                <h3 className="text-sm font-medium flex items-center gap-2">
                  <FileText className="w-4 h-4 text-purple-500" /> 
                  Döküman Oluşuyor
                </h3>
                <span className="text-xs text-muted-foreground">
                  {completedSections.reduce((acc, s) => acc + s.wordCount, 0)} kelime
                </span>
              </div>
              
              {completedSections.length === 0 ? (
                <div className="p-12 text-center">
                  <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-accent mb-4">
                    <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
                  </div>
                  <p className="text-muted-foreground">Bölümler yazılıyor...</p>
                  <p className="text-xs text-muted-foreground mt-1">İlk bölüm hazır olduğunda burada görüntülenecek</p>
                </div>
              ) : (
                <div className="p-6 prose prose-sm dark:prose-invert max-w-none">
                  {completedSections.map((section, _idx) => (
                    <motion.div
                      key={section.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="mb-6"
                    >
                      {section.level === 1 ? (
                        <h2 className="text-xl font-bold text-foreground border-b border-border pb-2 mb-4">
                          {section.title}
                        </h2>
                      ) : section.level === 2 ? (
                        <h3 className="text-lg font-semibold text-foreground mb-3">
                          {section.title}
                        </h3>
                      ) : (
                        <h4 className="text-base font-medium text-foreground mb-2">
                          {section.title}
                        </h4>
                      )}
                      <div className="text-sm text-foreground/90 leading-relaxed whitespace-pre-wrap">
                        {section.content}
                      </div>
                      <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <FileText className="w-3 h-3" />
                          {section.wordCount} kelime
                        </span>
                        <span>•</span>
                        <span className="text-green-500 flex items-center gap-1">
                          <CheckCircle className="w-3 h-3" />
                          Tamamlandı
                        </span>
                      </div>
                    </motion.div>
                  ))}
                  <div ref={previewEndRef} />
                </div>
              )}
            </motion.div>
          )}

          {activeTab === 'thinking' && (
            <motion.div
              key="thinking"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="max-h-[500px] overflow-y-auto"
            >
              <div className="px-4 py-3 bg-gradient-to-r from-blue-500/10 to-cyan-500/10 border-b border-border flex items-center justify-between sticky top-0 backdrop-blur-sm z-10">
                <h3 className="text-sm font-medium flex items-center gap-2">
                  <Brain className="w-4 h-4 text-blue-500" /> 
                  Agent Düşünce Süreci
                </h3>
                <span className="text-xs text-muted-foreground">{agentThoughts.length} düşünce</span>
              </div>
              
              {agentThoughts.length === 0 ? (
                <div className="p-12 text-center">
                  <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-accent mb-4">
                    <Brain className="w-8 h-8 text-muted-foreground animate-pulse" />
                  </div>
                  <p className="text-muted-foreground">Agentlar düşünüyor...</p>
                  <p className="text-xs text-muted-foreground mt-1">Agent mesajları burada görüntülenecek</p>
                </div>
              ) : (
                <div className="p-4 space-y-3">
                  {agentThoughts.map((thought, idx) => (
                    <motion.div
                      key={idx}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      className={`flex items-start gap-3 p-3 rounded-xl ${
                        thought.type === 'thinking' 
                          ? 'bg-blue-500/5 border border-blue-500/20' 
                          : thought.type === 'result'
                          ? 'bg-green-500/5 border border-green-500/20'
                          : 'bg-accent/50'
                      }`}
                    >
                      <div className={`flex items-center justify-center w-8 h-8 rounded-lg shrink-0 ${agentColors[thought.agent] || 'text-gray-500 bg-gray-500/10'}`}>
                        {agentIcons[thought.agent] || <Brain className="w-4 h-4" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                            {thought.agent.replace('_', ' ')}
                          </span>
                          <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                            thought.type === 'thinking' 
                              ? 'bg-blue-500/20 text-blue-600' 
                              : thought.type === 'result'
                              ? 'bg-green-500/20 text-green-600'
                              : 'bg-amber-500/20 text-amber-600'
                          }`}>
                            {thought.type === 'thinking' ? '💭 Düşünüyor' : thought.type === 'result' ? '✅ Sonuç' : '⚡ Aksiyon'}
                          </span>
                        </div>
                        <p className="text-sm text-foreground">{thought.message}</p>
                        <span className="text-[10px] text-muted-foreground mt-1 block">
                          {new Date(thought.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                    </motion.div>
                  ))}
                  <div ref={thoughtsEndRef} />
                </div>
              )}
            </motion.div>
          )}

          {activeTab === 'activity' && (
            <motion.div
              key="activity"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="max-h-[500px] overflow-y-auto"
            >
              <div className="px-4 py-3 bg-accent/30 border-b border-border flex items-center justify-between sticky top-0 backdrop-blur-sm z-10">
                <h3 className="text-sm font-medium flex items-center gap-2">
                  <Eye className="w-4 h-4" /> Agent Aktivitesi
                </h3>
                <span className="text-xs text-muted-foreground">{events.length} olay</span>
              </div>
              <div className="p-2 space-y-1">
                {events.map((event, index) => renderEvent(event, index))}
                <div ref={eventsEndRef} />
              </div>
            </motion.div>
          )}

          {activeTab === 'visuals' && (
            <motion.div
              key="visuals"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="max-h-[500px] overflow-y-auto"
            >
              <div className="px-4 py-3 bg-gradient-to-r from-purple-500/10 to-pink-500/10 border-b border-border flex items-center justify-between sticky top-0 backdrop-blur-sm z-10">
                <h3 className="text-sm font-medium flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-purple-500" /> 
                  Üretilen Görseller
                </h3>
                <span className="text-xs text-muted-foreground">{generatedVisuals.length} görsel</span>
              </div>
              
              {generatedVisuals.length === 0 ? (
                <div className="p-12 text-center">
                  <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-accent mb-4">
                    <BarChart3 className="w-8 h-8 text-muted-foreground animate-pulse" />
                  </div>
                  <p className="text-muted-foreground">Görseller üretiliyor...</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Diyagramlar, grafikler ve tablolar burada görünecek
                  </p>
                </div>
              ) : (
                <div className="p-4 space-y-4">
                  {generatedVisuals.map((visual, idx) => (
                    <motion.div
                      key={`visual-${idx}`}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="bg-accent/30 rounded-xl overflow-hidden"
                    >
                      {/* Visual Header */}
                      <div className="px-4 py-3 border-b border-border flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {visual.render_type?.startsWith('mermaid') ? (
                            <GitBranch className="w-4 h-4 text-blue-500" />
                          ) : visual.render_type === 'table' ? (
                            <Table className="w-4 h-4 text-green-500" />
                          ) : visual.render_type === 'code' ? (
                            <Code className="w-4 h-4 text-purple-500" />
                          ) : visual.render_type === 'latex' ? (
                            <span className="text-amber-500 font-serif text-sm">∑</span>
                          ) : (
                            <BarChart3 className="w-4 h-4 text-pink-500" />
                          )}
                          <span className="text-sm font-medium">{visual.title}</span>
                        </div>
                        <span className="text-xs text-muted-foreground px-2 py-0.5 bg-accent rounded-full">
                          {visual.type}
                        </span>
                      </div>
                      
                      {/* Visual Content */}
                      <div className="p-4">
                        {visual.code && (
                          <div className="relative">
                            <pre className="bg-muted/50 rounded-lg p-4 text-xs overflow-x-auto">
                              <code className="text-foreground/80 whitespace-pre">
                                {visual.code}
                              </code>
                            </pre>
                            {visual.render_type?.startsWith('mermaid') && (
                              <div className="mt-2 text-xs text-muted-foreground flex items-center gap-1">
                                <TrendingUp className="w-3 h-3" />
                                Mermaid diyagramı - döküman export edildiğinde render edilecek
                              </div>
                            )}
                          </div>
                        )}
                        
                        {visual.data && !visual.code && (
                          <div className="bg-muted/50 rounded-lg p-4 text-sm">
                            <pre className="whitespace-pre-wrap text-foreground/80">
                              {typeof visual.data === 'string' 
                                ? visual.data 
                                : JSON.stringify(visual.data, null, 2)
                              }
                            </pre>
                          </div>
                        )}
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
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
    <div className={view === 'generating' ? 'max-w-5xl mx-auto' : 'max-w-3xl mx-auto'}>
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
