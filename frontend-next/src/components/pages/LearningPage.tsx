'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  GraduationCap,
  BookOpen,
  Trophy,
  Target,
  Clock,
  Play,
  CheckCircle2,
  Plus,
  ArrowLeft,
  FileText,
  MessageSquare,
  Trash2,
  Eye,
  Send,
  ChevronRight,
  Loader2,
  X,
  Download,
  Edit3,
  Save,
  Brain,
  Sparkles,
  StopCircle,
  AlertCircle,
  Globe,
  Lock,
  Settings2,
  FileQuestion,
  ToggleLeft,
  ToggleRight,
  RefreshCw,
  Folder,
  File,
  FileSpreadsheet,
  FileType,
  Presentation,
  Check,
  XCircle,
  Zap,
  List
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { useStore } from '@/store/useStore';
import { cn } from '@/lib/utils';

// Types
interface LearningWorkspace {
  id: string;
  name: string;
  topic?: string;
  description?: string;
  documents?: LearningDocument[];
  tests?: LearningTest[];
  chat_history?: ChatMessage[];
  active_sources?: string[];
  created_at?: string;
}

interface LearningDocument {
  id: string;
  title: string;
  topic?: string;
  page_count: number;
  style: string;
  status: 'pending' | 'generating' | 'completed' | 'failed' | 'cancelled';
  content?: string;
  references?: Array<{ source: string; line?: number } | string>;
  generation_log?: string[];
  custom_instructions?: string;
  web_search?: 'off' | 'auto' | 'on';
}

interface LearningTest {
  id: string;
  title: string;
  test_type: 'mixed' | 'multiple_choice' | 'true_false' | 'fill_blank' | 'short_answer';
  question_count: number;
  difficulty: 'mixed' | 'easy' | 'medium' | 'hard';
  status: 'pending' | 'in_progress' | 'completed';
  score?: number;
  questions?: TestQuestion[];
  user_answers?: Record<string, string>;
}

interface TestQuestion {
  id: string;
  question: string;
  type: string;
  options?: string[];
  correct_answer: string;
  explanation?: string;
}

interface LearningSource {
  id: string;
  name: string;
  type: string;
  size: number;
  active: boolean;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  sources?: string[];
}

// API Base
const API_BASE = 'http://localhost:8001';

// API Functions
async function apiGet(endpoint: string) {
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, { 
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });
    return await response.json();
  } catch (error) {
    return { error: String(error) };
  }
}

async function apiPost(endpoint: string, data?: Record<string, unknown>) {
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data || {}),
    });
    return await response.json();
  } catch (error) {
    return { error: String(error) };
  }
}

async function apiDelete(endpoint: string) {
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, { 
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' }
    });
    return await response.json();
  } catch (error) {
    return { error: String(error) };
  }
}

async function apiPut(endpoint: string, data?: Record<string, unknown>) {
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data || {}),
    });
    return await response.json();
  } catch (error) {
    return { error: String(error) };
  }
}

type LearningView = 'list' | 'create' | 'workspace' | 'generating' | 'reading';
type WorkspaceTab = 'sources' | 'documents' | 'tests' | 'chat';

// Document styles
const DOCUMENT_STYLES = [
  { id: 'detailed', label: { tr: 'Detaylı', en: 'Detailed', de: 'Detailliert' }, icon: '📖' },
  { id: 'academic', label: { tr: 'Akademik', en: 'Academic', de: 'Akademisch' }, icon: '🎓' },
  { id: 'casual', label: { tr: 'Günlük', en: 'Casual', de: 'Alltäglich' }, icon: '💬' },
  { id: 'summary', label: { tr: 'Özet', en: 'Summary', de: 'Zusammenfassung' }, icon: '📋' },
  { id: 'exam_prep', label: { tr: 'Sınav Hazırlık', en: 'Exam Prep', de: 'Prüfungsvorbereitung' }, icon: '📝' },
];

// Test types
const TEST_TYPES = [
  { id: 'mixed', label: { tr: 'Karışık', en: 'Mixed', de: 'Gemischt' }, icon: '🎲' },
  { id: 'multiple_choice', label: { tr: 'Çoktan Seçmeli', en: 'Multiple Choice', de: 'Multiple Choice' }, icon: '📋' },
  { id: 'true_false', label: { tr: 'Doğru/Yanlış', en: 'True/False', de: 'Richtig/Falsch' }, icon: '✅' },
  { id: 'fill_blank', label: { tr: 'Boşluk Doldurma', en: 'Fill Blank', de: 'Lückentext' }, icon: '📝' },
  { id: 'short_answer', label: { tr: 'Kısa Cevap', en: 'Short Answer', de: 'Kurzantwort' }, icon: '💬' },
];

// Difficulties
const DIFFICULTIES = [
  { id: 'mixed', label: { tr: 'Karışık', en: 'Mixed', de: 'Gemischt' }, icon: '🎲', color: 'text-purple-500' },
  { id: 'easy', label: { tr: 'Kolay', en: 'Easy', de: 'Leicht' }, icon: '🟢', color: 'text-green-500' },
  { id: 'medium', label: { tr: 'Orta', en: 'Medium', de: 'Mittel' }, icon: '🟡', color: 'text-yellow-500' },
  { id: 'hard', label: { tr: 'Zor', en: 'Hard', de: 'Schwer' }, icon: '🔴', color: 'text-red-500' },
];

// Web search options
const WEB_SEARCH_OPTIONS = [
  { id: 'off', label: { tr: 'Kapalı', en: 'Off', de: 'Aus' }, icon: Lock, description: { tr: 'Sadece yüklü kaynaklardan', en: 'Only from uploaded sources', de: 'Nur aus hochgeladenen Quellen' } },
  { id: 'auto', label: { tr: 'Otomatik', en: 'Auto', de: 'Auto' }, icon: Settings2, description: { tr: 'AI karar versin', en: 'Let AI decide', de: 'KI entscheiden lassen' } },
  { id: 'on', label: { tr: 'Açık', en: 'On', de: 'Ein' }, icon: Globe, description: { tr: "Web'i de tara", en: 'Search web too', de: 'Auch Web durchsuchen' } },
];

// File type icons
function getFileIcon(type: string) {
  const t = type.toUpperCase();
  if (t === 'PDF') return { icon: FileText, color: 'text-red-500', bg: 'bg-red-50' };
  if (['DOCX', 'DOC'].includes(t)) return { icon: FileType, color: 'text-blue-500', bg: 'bg-blue-50' };
  if (['PPTX', 'PPT'].includes(t)) return { icon: Presentation, color: 'text-orange-500', bg: 'bg-orange-50' };
  if (['XLSX', 'XLS'].includes(t)) return { icon: FileSpreadsheet, color: 'text-green-500', bg: 'bg-green-50' };
  if (t === 'TXT') return { icon: File, color: 'text-gray-500', bg: 'bg-gray-50' };
  return { icon: Folder, color: 'text-purple-500', bg: 'bg-purple-50' };
}

// Format file size
function formatFileSize(bytes: number): string {
  if (bytes > 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / 1024).toFixed(1)} KB`;
}

export function LearningPage() {
  const { language } = useStore();
  
  // View state
  const [view, setView] = useState<LearningView>('list');
  const [currentWorkspaceId, setCurrentWorkspaceId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<WorkspaceTab>('sources');
  
  // Data state
  const [workspaces, setWorkspaces] = useState<LearningWorkspace[]>([]);
  const [currentWorkspace, setCurrentWorkspace] = useState<LearningWorkspace | null>(null);
  const [documents, setDocuments] = useState<LearningDocument[]>([]);
  const [tests, setTests] = useState<LearningTest[]>([]);
  const [sources, setSources] = useState<LearningSource[]>([]);
  const [activeSourceCount, setActiveSourceCount] = useState(0);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  
  // UI state
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [bulkToggling, setBulkToggling] = useState(false);
  
  // Form state - Create workspace
  const [newWorkspaceName, setNewWorkspaceName] = useState('');
  const [newWorkspaceTopic, setNewWorkspaceTopic] = useState('');
  const [newWorkspaceDescription, setNewWorkspaceDescription] = useState('');

  // Form state - Create document
  const [docTitle, setDocTitle] = useState('');
  const [docTopic, setDocTopic] = useState('');
  const [docPageCount, setDocPageCount] = useState(5);
  const [docStyle, setDocStyle] = useState('detailed');
  const [docWebSearch, setDocWebSearch] = useState<'off' | 'auto' | 'on'>('auto');
  const [docCustomInstructions, setDocCustomInstructions] = useState('');

  // Form state - Create test
  const [testTitle, setTestTitle] = useState('');
  const [testType, setTestType] = useState('mixed');
  const [testDifficulty, setTestDifficulty] = useState('mixed');
  const [testQuestionCount, setTestQuestionCount] = useState(10);

  // Chat state
  const [chatInput, setChatInput] = useState('');
  const [sendingChat, setSendingChat] = useState(false);

  // Document generation state
  const [generatingDocId, setGeneratingDocId] = useState<string | null>(null);
  const [generatingDocConfig, setGeneratingDocConfig] = useState<{
    title?: string;
    topic?: string;
    page_count?: number;
    style?: string;
    web_search?: 'off' | 'auto' | 'on';
    custom_instructions?: string;
  } | null>(null);
  const [generationLogs, setGenerationLogs] = useState<string[]>([]);
  const [generationProgress, setGenerationProgress] = useState(0);

  // Document reading state
  const [readingDocument, setReadingDocument] = useState<LearningDocument | null>(null);
  const [isEditingDoc, setIsEditingDoc] = useState(false);
  const [editDocTitle, setEditDocTitle] = useState('');
  const [editDocTopic, setEditDocTopic] = useState('');
  const [editDocPageCount, setEditDocPageCount] = useState(5);
  const [editDocStyle, setEditDocStyle] = useState('detailed');
  const [confirmDeleteDoc, setConfirmDeleteDoc] = useState(false);

  // Test taking state
  const [activeTest, setActiveTest] = useState<LearningTest | null>(null);
  const [testMode, setTestMode] = useState<'taking' | 'results' | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState('');

  // Refs
  const pollingRef = useRef<NodeJS.Timeout | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Translations
  const t = {
    title: { tr: 'AI ile Öğren', en: 'Learn with AI', de: 'Lernen mit KI' },
    subtitle: { tr: 'Kişiselleştirilmiş öğrenme platformu', en: 'Personalized learning platform', de: 'Personalisierte Lernplattform' },
    workspaces: { tr: 'Çalışma Ortamlarım', en: 'My Workspaces', de: 'Meine Arbeitsbereiche' },
    newWorkspace: { tr: 'Yeni Oluştur', en: 'Create New', de: 'Neu erstellen' },
    noWorkspaces: { tr: 'Henüz çalışma ortamı yok', en: 'No workspaces yet', de: 'Noch keine Arbeitsbereiche' },
    createFirst: { tr: 'Yeni bir tane oluşturun!', en: 'Create a new one!', de: 'Erstellen Sie einen neuen!' },
    open: { tr: 'Aç', en: 'Open', de: 'Öffnen' },
    back: { tr: 'Geri', en: 'Back', de: 'Zurück' },
    name: { tr: 'Ad', en: 'Name', de: 'Name' },
    topic: { tr: 'Konu', en: 'Topic', de: 'Thema' },
    description: { tr: 'Açıklama', en: 'Description', de: 'Beschreibung' },
    create: { tr: 'Oluştur', en: 'Create', de: 'Erstellen' },
    sources: { tr: 'Kaynaklar', en: 'Sources', de: 'Quellen' },
    documents: { tr: 'Dökümanlar', en: 'Documents', de: 'Dokumente' },
    tests: { tr: 'Testler', en: 'Tests', de: 'Tests' },
    chat: { tr: 'Chat', en: 'Chat', de: 'Chat' },
    noDocuments: { tr: 'Henüz döküman yok', en: 'No documents yet', de: 'Noch keine Dokumente' },
    noTests: { tr: 'Henüz test yok', en: 'No tests yet', de: 'Noch keine Tests' },
    pages: { tr: 'sayfa', en: 'pages', de: 'Seiten' },
    questions: { tr: 'soru', en: 'questions', de: 'Fragen' },
    read: { tr: 'Oku', en: 'Read', de: 'Lesen' },
    start: { tr: 'Başlat', en: 'Start', de: 'Starten' },
    continue: { tr: 'Devam', en: 'Continue', de: 'Fortsetzen' },
    results: { tr: 'Sonuçlar', en: 'Results', de: 'Ergebnisse' },
    score: { tr: 'Puan', en: 'Score', de: 'Punktzahl' },
    correct: { tr: 'Doğru', en: 'Correct', de: 'Richtig' },
    wrong: { tr: 'Yanlış', en: 'Wrong', de: 'Falsch' },
    next: { tr: 'Sonraki', en: 'Next', de: 'Weiter' },
    previous: { tr: 'Önceki', en: 'Previous', de: 'Zurück' },
    saveAnswer: { tr: 'Cevabı Kaydet', en: 'Save Answer', de: 'Antwort speichern' },
    finishTest: { tr: 'Testi Bitir', en: 'Finish Test', de: 'Test beenden' },
    yourAnswer: { tr: 'Cevabınız', en: 'Your Answer', de: 'Ihre Antwort' },
    correctAnswer: { tr: 'Doğru Cevap', en: 'Correct Answer', de: 'Richtige Antwort' },
    explanation: { tr: 'Açıklama', en: 'Explanation', de: 'Erklärung' },
    askQuestion: { tr: 'Sorunuzu yazın...', en: 'Type your question...', de: 'Ihre Frage eingeben...' },
    noSources: { tr: 'Henüz kaynak yok', en: 'No sources yet', de: 'Noch keine Quellen' },
    active: { tr: 'Aktif', en: 'Active', de: 'Aktiv' },
    delete: { tr: 'Sil', en: 'Delete', de: 'Löschen' },
    cancel: { tr: 'İptal', en: 'Cancel', de: 'Abbrechen' },
    save: { tr: 'Kaydet', en: 'Save', de: 'Speichern' },
    edit: { tr: 'Düzenle', en: 'Edit', de: 'Bearbeiten' },
    regenerate: { tr: 'Yeniden Oluştur', en: 'Regenerate', de: 'Neu generieren' },
    generating: { tr: 'Döküman Oluşturuluyor', en: 'Generating Document', de: 'Dokument wird erstellt' },
    aiThinking: { tr: 'AI Düşünme Süreci', en: 'AI Thinking Process', de: 'KI-Denkprozess' },
    detailedLogs: { tr: 'Detaylı İşlem Logları', en: 'Detailed Process Logs', de: 'Detaillierte Prozessprotokolle' },
    generatedContent: { tr: 'Oluşturulan İçerik', en: 'Generated Content', de: 'Generierter Inhalt' },
    downloadMd: { tr: 'Markdown İndir', en: 'Download MD', de: 'MD herunterladen' },
    downloadTxt: { tr: 'TXT İndir', en: 'Download TXT', de: 'TXT herunterladen' },
    references: { tr: 'Kaynakça', en: 'References', de: 'Referenzen' },
    saveAndRegenerate: { tr: 'Kaydet & Yeniden Oluştur', en: 'Save & Regenerate', de: 'Speichern & Neu generieren' },
    confirmDelete: { tr: 'Bu dökümanı silmek istediğinizden emin misiniz?', en: 'Are you sure you want to delete this document?', de: 'Sind Sie sicher, dass Sie dieses Dokument löschen möchten?' },
    yesDelete: { tr: 'Evet, Sil', en: 'Yes, Delete', de: 'Ja, löschen' },
    totalSources: { tr: 'Toplam Kaynak', en: 'Total Sources', de: 'Gesamtquellen' },
    activeSources: { tr: 'Aktif Kaynaklar', en: 'Active Sources', de: 'Aktive Quellen' },
    inactiveSources: { tr: 'Deaktif Kaynaklar', en: 'Inactive Sources', de: 'Inaktive Quellen' },
    activateAll: { tr: 'Tümünü Aktif Yap', en: 'Activate All', de: 'Alle aktivieren' },
    deactivateAll: { tr: 'Tümünü Deaktif Yap', en: 'Deactivate All', de: 'Alle deaktivieren' },
    webSearch: { tr: 'Web Araması', en: 'Web Search', de: 'Websuche' },
    customInstructions: { tr: 'Özel Talimatlar', en: 'Custom Instructions', de: 'Benutzerdefinierte Anweisungen' },
    createDocument: { tr: 'Döküman Oluştur', en: 'Create Document', de: 'Dokument erstellen' },
    createTest: { tr: 'Test Oluştur', en: 'Create Test', de: 'Test erstellen' },
    testType: { tr: 'Soru Türü', en: 'Question Type', de: 'Fragetyp' },
    difficulty: { tr: 'Zorluk', en: 'Difficulty', de: 'Schwierigkeit' },
    questionCount: { tr: 'Soru Sayısı', en: 'Question Count', de: 'Anzahl Fragen' },
    style: { tr: 'Yazım Stili', en: 'Writing Style', de: 'Schreibstil' },
    pageCount: { tr: 'Sayfa Sayısı', en: 'Page Count', de: 'Seitenzahl' },
    workingWith: { tr: 'aktif kaynak ile çalışıyor', en: 'active sources working', de: 'aktive Quellen arbeiten' },
    noActiveSource: { tr: 'Aktif kaynak yok. Kaynaklar sekmesinden kaynak ekleyin.', en: 'No active sources. Add sources from Sources tab.', de: 'Keine aktiven Quellen. Fügen Sie Quellen im Quellenregister hinzu.' },
    startChat: { tr: 'Aşağıdan bir soru sorarak başlayın!', en: 'Start by asking a question below!', de: 'Beginnen Sie mit einer Frage unten!' },
    sourcesUsed: { tr: 'Kaynaklar', en: 'Sources', de: 'Quellen' },
    content: { tr: 'İçerik', en: 'Content', de: 'Inhalt' },
    contentNotGenerated: { tr: 'İçerik henüz oluşturulmamış', en: 'Content not generated yet', de: 'Inhalt noch nicht generiert' },
  };

  // Load initial data
  useEffect(() => {
    loadWorkspaces();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Load workspace data when selected
  useEffect(() => {
    if (currentWorkspaceId && view === 'workspace') {
      loadWorkspaceData(currentWorkspaceId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentWorkspaceId, view, activeTab]);

  // Scroll chat to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, []);

  const loadWorkspaces = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiGet('/api/learning/workspaces');
      console.log('Learning workspaces response:', response);
      if (response.error) {
        setError(language === 'tr' 
          ? 'Backend bağlantısı kurulamadı. Lütfen backend sunucusunun çalıştığından emin olun.'
          : 'Could not connect to backend. Please make sure the backend server is running.'
        );
      } else {
        setWorkspaces(response.workspaces || []);
      }
    } catch (err) {
      console.error('Learning API error:', err);
      setError(language === 'tr'
        ? 'API hatası oluştu. Backend sunucusu çalışmıyor olabilir.'
        : 'API error occurred. Backend server may not be running.'
      );
    }
    setLoading(false);
  };

  const loadWorkspaceData = async (workspaceId: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiGet(`/api/learning/workspaces/${workspaceId}`);
      console.log('Workspace data response:', response);
      if (response.error) {
        setError(language === 'tr' 
          ? 'Çalışma ortamı yüklenemedi.'
          : 'Could not load workspace.'
        );
        setLoading(false);
        return;
      }
      if (response.workspace) {
        setCurrentWorkspace(response.workspace);
        setDocuments(response.documents || response.workspace.documents || []);
        setTests(response.tests || response.workspace.tests || []);
        setChatMessages(response.workspace.chat_history || []);
      }

      // Load sources
      const sourcesResponse = await apiGet(`/api/learning/workspaces/${workspaceId}/sources`);
      console.log('Workspace sources response:', sourcesResponse);
      if (!sourcesResponse.error) {
        setSources(sourcesResponse.sources || []);
        setActiveSourceCount(sourcesResponse.active_count || 0);
      }
    } catch (err) {
      console.error('Workspace data error:', err);
      setError(language === 'tr'
        ? 'Çalışma ortamı yüklenirken hata oluştu.'
        : 'Error loading workspace.'
      );
    }

    setLoading(false);
  };

  const handleCreateWorkspace = async () => {
    if (!newWorkspaceName.trim()) return;
    
    setCreating(true);
    const response = await apiPost('/api/learning/workspaces', {
      name: newWorkspaceName,
      topic: newWorkspaceTopic || undefined,
      description: newWorkspaceDescription || undefined,
    });

    if (response.success && response.workspace) {
      setCurrentWorkspaceId(response.workspace.id);
      setView('workspace');
      setNewWorkspaceName('');
      setNewWorkspaceTopic('');
      setNewWorkspaceDescription('');
      await loadWorkspaces();
    }
    setCreating(false);
  };

  const handleDeleteWorkspace = async (workspaceId: string) => {
    const response = await apiDelete(`/api/learning/workspaces/${workspaceId}`);
    if (response.success) {
      await loadWorkspaces();
      if (currentWorkspaceId === workspaceId) {
        setCurrentWorkspaceId(null);
        setView('list');
      }
    }
  };

  const handleToggleSource = async (sourceId: string, active: boolean) => {
    if (!currentWorkspaceId) return;
    await apiPost(`/api/learning/workspaces/${currentWorkspaceId}/sources/toggle`, {
      source_id: sourceId,
      active
    });
    // Reload sources
    const sourcesResponse = await apiGet(`/api/learning/workspaces/${currentWorkspaceId}/sources`);
    if (!sourcesResponse.error) {
      setSources(sourcesResponse.sources || []);
      setActiveSourceCount(sourcesResponse.active_count || 0);
    }
  };

  const handleBulkToggleSources = async (active: boolean) => {
    if (!currentWorkspaceId || bulkToggling) return;
    setBulkToggling(true);
    try {
      const response = await apiPost(`/api/learning/workspaces/${currentWorkspaceId}/sources/bulk-toggle`, { active });
      console.log('Bulk toggle response:', response);
      // Reload sources
      const sourcesResponse = await apiGet(`/api/learning/workspaces/${currentWorkspaceId}/sources`);
      console.log('Sources reload response:', sourcesResponse);
      if (!sourcesResponse.error) {
        setSources(sourcesResponse.sources || []);
        setActiveSourceCount(sourcesResponse.active_count || 0);
      }
    } catch (err) {
      console.error('Bulk toggle error:', err);
    } finally {
      setBulkToggling(false);
    }
  };

  // Document generation
  const handleCreateDocument = async () => {
    if (!currentWorkspaceId || !docTitle.trim() || !docTopic.trim()) return;

    const config = {
      title: docTitle,
      topic: docTopic,
      page_count: docPageCount,
      style: docStyle,
      web_search: docWebSearch,
      custom_instructions: docCustomInstructions || undefined,
    };

    setGeneratingDocConfig(config);
    setGenerationLogs([]);
    setGenerationProgress(0);
    setView('generating');

    // Create document
    const response = await apiPost(`/api/learning/workspaces/${currentWorkspaceId}/documents`, config);
    
    if (response.error || !response.document) {
      setGenerationLogs(prev => [...prev, `❌ Döküman oluşturulamadı: ${response.error || 'Bilinmeyen hata'}`]);
      return;
    }

    const docId = response.document.id;
    setGeneratingDocId(docId);
    setGenerationLogs(prev => [...prev, `✅ Döküman kaydı oluşturuldu: ${docId.slice(0, 8)}...`]);

    // Start generation
    setGenerationLogs(prev => [...prev, '🚀 AI içerik üretimi başlatılıyor...']);
    
    const startResponse = await apiPost(`/api/learning/documents/${docId}/generate`, {
      custom_instructions: docCustomInstructions,
      web_search: docWebSearch
    });

    if (startResponse.error) {
      setGenerationLogs(prev => [...prev, `❌ Üretim başlatılamadı: ${startResponse.error}`]);
      return;
    }

    setGenerationLogs(prev => [...prev, '✅ Arka plan görevi başlatıldı']);
    
    // Start polling
    startPolling(docId);
  };

  const startPolling = useCallback((docId: string) => {
    let pollCount = 0;
    let lastLogCount = 0;

    pollingRef.current = setInterval(async () => {
      pollCount++;
      
      const response = await apiGet(`/api/learning/documents/${docId}`);
      if (response.error || !response.document) return;

      const doc = response.document;
      const status = doc.status;
      const genLogs = doc.generation_log || [];

      // Update logs
      if (genLogs.length > lastLogCount) {
        const newLogs = genLogs.slice(lastLogCount);
        setGenerationLogs(prev => [...prev, ...newLogs.map((l: string) => `📋 ${l}`)]);
        lastLogCount = genLogs.length;
      }

      // Update progress
      if (status === 'generating') {
        const progress = Math.min(15 + pollCount * 2, 85);
        setGenerationProgress(progress);
      } else if (status === 'completed') {
        setGenerationProgress(100);
        setGenerationLogs(prev => [...prev, '🎉 Döküman başarıyla tamamlandı!']);
        
        if (pollingRef.current) {
          clearInterval(pollingRef.current);
          pollingRef.current = null;
        }

        // Navigate to reading view
        setTimeout(() => {
          setReadingDocument(doc);
          setView('reading');
          setGeneratingDocId(null);
          setGeneratingDocConfig(null);
          
          // Reset form
          setDocTitle('');
          setDocTopic('');
          setDocPageCount(5);
          setDocStyle('detailed');
          setDocWebSearch('auto');
          setDocCustomInstructions('');
        }, 1000);
      } else if (status === 'failed' || status === 'cancelled') {
        setGenerationLogs(prev => [...prev, `❌ ${status === 'failed' ? 'Döküman oluşturma başarısız' : 'Üretim iptal edildi'}`]);
        
        if (pollingRef.current) {
          clearInterval(pollingRef.current);
          pollingRef.current = null;
        }
      }

      // Timeout after 20 minutes
      if (pollCount > 400) {
        setGenerationLogs(prev => [...prev, '⏰ Zaman aşımı!']);
        if (pollingRef.current) {
          clearInterval(pollingRef.current);
          pollingRef.current = null;
        }
      }
    }, 3000);
  }, []);

  const handleCancelGeneration = async () => {
    if (generatingDocId) {
      await apiPost(`/api/learning/documents/${generatingDocId}/cancel`, {});
    }
    
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
    
    setView('workspace');
    setGeneratingDocId(null);
    setGeneratingDocConfig(null);
  };

  // Document reading
  const handleViewDocument = async (doc: LearningDocument) => {
    const response = await apiGet(`/api/learning/documents/${doc.id}`);
    if (!response.error && response.document) {
      setReadingDocument(response.document);
      setEditDocTitle(response.document.title);
      setEditDocTopic(response.document.topic || '');
      setEditDocPageCount(response.document.page_count);
      setEditDocStyle(response.document.style);
      setView('reading');
    }
  };

  const handleSaveDocument = async () => {
    if (!readingDocument) return;
    
    const response = await apiPut(`/api/learning/documents/${readingDocument.id}`, {
      title: editDocTitle,
      topic: editDocTopic,
      page_count: editDocPageCount,
      style: editDocStyle
    });

    if (response.success) {
      setReadingDocument({
        ...readingDocument,
        title: editDocTitle,
        topic: editDocTopic,
        page_count: editDocPageCount,
        style: editDocStyle
      });
      setIsEditingDoc(false);
    }
  };

  const handleSaveAndRegenerate = async () => {
    if (!readingDocument) return;

    const response = await apiPost(`/api/learning/documents/${readingDocument.id}/edit-and-restart`, {
      title: editDocTitle,
      topic: editDocTopic,
      page_count: editDocPageCount,
      style: editDocStyle
    });

    if (response.success) {
      setIsEditingDoc(false);
      setGeneratingDocId(readingDocument.id);
      setGeneratingDocConfig({
        title: editDocTitle,
        topic: editDocTopic,
        page_count: editDocPageCount,
        style: editDocStyle,
        web_search: 'auto'
      });
      setGenerationLogs([]);
      setGenerationProgress(0);
      setView('generating');
      startPolling(readingDocument.id);
    }
  };

  const handleRegenerateDocument = async () => {
    if (!readingDocument) return;

    const response = await apiPost(`/api/learning/documents/${readingDocument.id}/restart`, {});
    
    if (response.success) {
      setGeneratingDocId(readingDocument.id);
      setGeneratingDocConfig({
        title: readingDocument.title,
        topic: readingDocument.topic,
        page_count: readingDocument.page_count,
        style: readingDocument.style,
        web_search: 'auto'
      });
      setGenerationLogs([]);
      setGenerationProgress(0);
      setView('generating');
      startPolling(readingDocument.id);
    }
  };

  const handleDeleteDocument = async () => {
    if (!readingDocument) return;

    const response = await apiDelete(`/api/learning/documents/${readingDocument.id}`);
    if (response.success) {
      setConfirmDeleteDoc(false);
      setReadingDocument(null);
      setView('workspace');
      if (currentWorkspaceId) {
        await loadWorkspaceData(currentWorkspaceId);
      }
    }
  };

  const handleDownloadDocument = (format: 'md' | 'txt') => {
    if (!readingDocument?.content) return;
    
    let content = readingDocument.content;
    if (format === 'txt') {
      content = content.replace(/## /g, '\n\n=== ').replace(/### /g, '\n--- ').replace(/\*\*/g, '').replace(/\*/g, '');
    }
    
    const filename = `${readingDocument.title.replace(/[^\w\s-]/g, '').trim().replace(/\s+/g, '_')}.${format}`;
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Test handling
  const handleCreateTest = async () => {
    if (!currentWorkspaceId || !testTitle.trim()) return;

    setCreating(true);
    const response = await apiPost(`/api/learning/workspaces/${currentWorkspaceId}/tests`, {
      title: testTitle,
      test_type: testType,
      question_count: testQuestionCount,
      difficulty: testDifficulty
    });

    if (response.success) {
      await loadWorkspaceData(currentWorkspaceId);
      setTestTitle('');
      setTestType('mixed');
      setTestDifficulty('mixed');
      setTestQuestionCount(10);
    }
    setCreating(false);
  };

  const handleStartTest = async (test: LearningTest) => {
    const response = await apiGet(`/api/learning/tests/${test.id}`);
    if (!response.error && response.test) {
      setActiveTest(response.test);
      setCurrentQuestion(0);
      setTestMode('taking');
    }
  };

  const handleSubmitAnswer = async () => {
    if (!activeTest || !selectedAnswer) return;
    
    const question = activeTest.questions?.[currentQuestion];
    if (!question) return;

    await apiPost(`/api/learning/tests/${activeTest.id}/answer`, {
      question_id: question.id,
      answer: selectedAnswer
    });

    setActiveTest(prev => prev ? {
      ...prev,
      user_answers: { ...(prev.user_answers || {}), [question.id]: selectedAnswer }
    } : null);
    setSelectedAnswer('');
    
    if (currentQuestion < (activeTest.questions?.length || 0) - 1) {
      setCurrentQuestion(prev => prev + 1);
    }
  };

  const handleCompleteTest = async () => {
    if (!activeTest) return;
    
    const response = await apiPost(`/api/learning/tests/${activeTest.id}/complete`, {});
    if (response.success) {
      setActiveTest(prev => prev ? { ...prev, status: 'completed', score: response.score } : null);
      setTestMode('results');
      if (currentWorkspaceId) {
        await loadWorkspaceData(currentWorkspaceId);
      }
    }
  };

  // Chat handling
  const handleSendChat = async () => {
    if (!chatInput.trim() || !currentWorkspaceId) return;
    
    setSendingChat(true);
    const messageToSend = chatInput;
    setChatMessages(prev => [...prev, { role: 'user', content: messageToSend }]);
    setChatInput('');
    
    const response = await apiPost(`/api/learning/workspaces/${currentWorkspaceId}/chat`, {
      message: messageToSend
    });
    
    if (response.success) {
      setChatMessages(prev => [...prev, { 
        role: 'assistant', 
        content: response.response || response.message,
        sources: response.sources
      }]);
    } else {
      setChatMessages(prev => [...prev, { 
        role: 'assistant', 
        content: language === 'tr' 
          ? 'Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.' 
          : 'Sorry, an error occurred. Please try again.',
      }]);
    }
    
    setSendingChat(false);
  };

  // =============== RENDER FUNCTIONS ===============

  const renderWorkspaceList = () => (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">{t.workspaces[language]}</h2>
        <button
          onClick={() => setView('create')}
          className="flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-xl hover:bg-primary-600 transition-colors"
        >
          <Plus className="w-4 h-4" />
          {t.newWorkspace[language]}
        </button>
      </div>

      {/* Workspaces Grid */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
        </div>
      ) : error ? (
        <div className="bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-xl p-6 text-center">
          <AlertCircle className="w-12 h-12 mx-auto text-amber-500 mb-4" />
          <p className="text-lg font-medium text-amber-700 dark:text-amber-300 mb-2">
            {language === 'tr' ? 'Bağlantı Hatası' : 'Connection Error'}
          </p>
          <p className="text-sm text-amber-600 dark:text-amber-400 mb-4">{error}</p>
          <button
            onClick={loadWorkspaces}
            className="flex items-center gap-2 px-4 py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600 transition-colors mx-auto"
          >
            <RefreshCw className="w-4 h-4" />
            {language === 'tr' ? 'Tekrar Dene' : 'Try Again'}
          </button>
        </div>
      ) : workspaces.length === 0 ? (
        <div className="text-center py-12">
          <BookOpen className="w-16 h-16 mx-auto text-muted-foreground/50 mb-4" />
          <p className="text-lg font-medium text-muted-foreground">{t.noWorkspaces[language]}</p>
          <p className="text-sm text-muted-foreground mt-1">{t.createFirst[language]}</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {workspaces.map((ws) => (
            <motion.div
              key={ws.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-card border border-border rounded-2xl p-5 hover:border-primary-500/50 hover:shadow-lg transition-all group"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-primary-500/10 text-primary-500">
                    <BookOpen className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-semibold">{ws.name}</h3>
                    {ws.topic && <p className="text-xs text-muted-foreground">📌 {ws.topic}</p>}
                  </div>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteWorkspace(ws.id);
                  }}
                  className="p-1.5 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-destructive/10 text-destructive transition-all"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
              
              {ws.description && (
                <p className="text-sm text-muted-foreground mb-3 line-clamp-2 italic">{ws.description}</p>
              )}
              
              <div className="flex items-center gap-4 text-xs text-muted-foreground mb-4">
                <span className="flex items-center gap-1">
                  <FileText className="w-3.5 h-3.5" />
                  {ws.documents?.length || 0} {t.documents[language].toLowerCase()}
                </span>
                <span className="flex items-center gap-1">
                  <Target className="w-3.5 h-3.5" />
                  {ws.tests?.length || 0} {t.tests[language].toLowerCase()}
                </span>
                <span className="flex items-center gap-1">
                  <MessageSquare className="w-3.5 h-3.5" />
                  {ws.chat_history?.length || 0}
                </span>
              </div>
              
              <button
                onClick={() => {
                  setCurrentWorkspaceId(ws.id);
                  setView('workspace');
                }}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-xl hover:bg-primary-600 transition-colors"
              >
                <Play className="w-4 h-4" />
                {t.open[language]}
              </button>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );

  const renderCreateWorkspace = () => (
    <div className="max-w-xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <button
          onClick={() => setView('list')}
          className="p-2 hover:bg-accent rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <h2 className="text-xl font-semibold">{t.newWorkspace[language]}</h2>
      </div>

      <div className="bg-card border border-border rounded-2xl p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">📝 {t.name[language]} *</label>
          <input
            type="text"
            value={newWorkspaceName}
            onChange={(e) => setNewWorkspaceName(e.target.value)}
            placeholder={language === 'tr' ? 'Örn: Makine Öğrenmesi Çalışması' : 'E.g., Machine Learning Study'}
            className="w-full px-4 py-2.5 bg-background border border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500/50"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">📌 {t.topic[language]}</label>
          <input
            type="text"
            value={newWorkspaceTopic}
            onChange={(e) => setNewWorkspaceTopic(e.target.value)}
            placeholder={language === 'tr' ? 'Örn: Supervised Learning, Neural Networks' : 'E.g., Supervised Learning, Neural Networks'}
            className="w-full px-4 py-2.5 bg-background border border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500/50"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">📄 {t.description[language]}</label>
          <textarea
            value={newWorkspaceDescription}
            onChange={(e) => setNewWorkspaceDescription(e.target.value)}
            placeholder={language === 'tr' ? 'Bu çalışma ortamının amacı...' : 'Purpose of this workspace...'}
            rows={3}
            className="w-full px-4 py-2.5 bg-background border border-border rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-primary-500/50"
          />
        </div>

        <button
          onClick={handleCreateWorkspace}
          disabled={!newWorkspaceName.trim() || creating}
          className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-primary-500 text-white rounded-xl hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
          {t.create[language]}
        </button>
      </div>
    </div>
  );

  const renderGeneratingView = () => (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button
          onClick={handleCancelGeneration}
          className="p-2 hover:bg-accent rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <h2 className="text-xl font-semibold">🔄 {t.generating[language]}...</h2>
      </div>

      {/* Document Config Info */}
      {generatingDocConfig && (
        <div className="bg-card border border-border rounded-2xl p-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-muted-foreground">📖 {language === 'tr' ? 'Başlık' : 'Title'}:</span>
              <p className="font-medium">{generatingDocConfig.title}</p>
            </div>
            <div>
              <span className="text-muted-foreground">📌 {language === 'tr' ? 'Konu' : 'Topic'}:</span>
              <p className="font-medium">{generatingDocConfig.topic}</p>
            </div>
            <div>
              <span className="text-muted-foreground">📄 {language === 'tr' ? 'Sayfa' : 'Pages'}:</span>
              <p className="font-medium">{generatingDocConfig.page_count}</p>
            </div>
            <div>
              <span className="text-muted-foreground">✍️ {language === 'tr' ? 'Stil' : 'Style'}:</span>
              <p className="font-medium">{generatingDocConfig.style}</p>
            </div>
          </div>
          {generatingDocConfig.web_search && (
            <div className="mt-3 pt-3 border-t border-border">
              <span className="text-sm">
                {generatingDocConfig.web_search === 'off' && '🔒 Web Araması: Kapalı'}
                {generatingDocConfig.web_search === 'auto' && '🤖 Web Araması: Otomatik'}
                {generatingDocConfig.web_search === 'on' && '🌐 Web Araması: Açık'}
              </span>
            </div>
          )}
        </div>
      )}

      {/* AI Thinking Process */}
      <div className="bg-gradient-to-r from-violet-50 to-purple-50 dark:from-violet-950/30 dark:to-purple-950/30 border-2 border-violet-300 dark:border-violet-700 rounded-2xl p-6">
        <div className="flex items-center gap-4 mb-4">
          <div className="relative">
            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
              <Brain className="w-6 h-6 text-white animate-pulse" />
            </div>
            <Sparkles className="absolute -top-1 -right-1 w-5 h-5 text-yellow-500 animate-bounce" />
          </div>
          <div className="flex-1">
            <h3 className="font-semibold text-violet-700 dark:text-violet-300 flex items-center gap-2">
              🧠 {t.aiThinking[language]}
              {generationProgress < 100 && <Loader2 className="w-4 h-4 animate-spin" />}
            </h3>
          </div>
          {generationProgress < 100 && (
            <button
              onClick={handleCancelGeneration}
              className="flex items-center gap-2 px-4 py-2 bg-red-500/10 text-red-600 rounded-xl hover:bg-red-500/20 transition-colors"
            >
              <StopCircle className="w-4 h-4" />
              {t.cancel[language]}
            </button>
          )}
        </div>
        
        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs text-violet-600 dark:text-violet-400">
            <span>{language === 'tr' ? 'İlerleme' : 'Progress'}</span>
            <span>{Math.round(generationProgress)}%</span>
          </div>
          <div className="h-3 bg-violet-200 dark:bg-violet-800 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-violet-500 to-purple-600 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${generationProgress}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
        </div>
      </div>

      {/* Detailed Logs */}
      <details open className="bg-card border border-border rounded-2xl overflow-hidden">
        <summary className="px-4 py-3 cursor-pointer hover:bg-accent font-medium flex items-center gap-2">
          <List className="w-4 h-4" />
          📋 {t.detailedLogs[language]}
        </summary>
        <div className="p-4 bg-muted/30 max-h-80 overflow-y-auto">
          <pre className="text-xs font-mono whitespace-pre-wrap">
            {generationLogs.slice(-25).join('\n') || 'Bekleniyor...'}
          </pre>
        </div>
      </details>
    </div>
  );

  const renderReadingView = () => {
    if (!readingDocument) return null;

    return (
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                setReadingDocument(null);
                setIsEditingDoc(false);
                setConfirmDeleteDoc(false);
                setView('workspace');
              }}
              className="p-2 hover:bg-accent rounded-lg transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <h2 className="text-xl font-semibold">📖 {readingDocument.title}</h2>
              <p className="text-sm text-muted-foreground">📄 {readingDocument.page_count} {t.pages[language]}</p>
            </div>
          </div>
        </div>

        {/* Meta Info */}
        <div className="bg-card border border-border rounded-xl p-4">
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <span className="text-muted-foreground">📌 {t.topic[language]}:</span>
              <p className="font-medium">{readingDocument.topic || '-'}</p>
            </div>
            <div>
              <span className="text-muted-foreground">✍️ {t.style[language]}:</span>
              <p className="font-medium">{DOCUMENT_STYLES.find(s => s.id === readingDocument.style)?.label[language] || readingDocument.style}</p>
            </div>
            <div>
              <span className="text-muted-foreground">{language === 'tr' ? 'Durum' : 'Status'}:</span>
              <p className="font-medium flex items-center gap-1">
                {readingDocument.status === 'completed' ? (
                  <><CheckCircle2 className="w-4 h-4 text-green-500" /> {language === 'tr' ? 'Tamamlandı' : 'Completed'}</>
                ) : (
                  <><Clock className="w-4 h-4 text-yellow-500" /> {readingDocument.status}</>
                )}
              </p>
            </div>
          </div>
        </div>

        {/* Edit Mode */}
        {isEditingDoc && (
          <div className="bg-yellow-50 dark:bg-yellow-950/30 border-2 border-yellow-300 dark:border-yellow-700 rounded-2xl p-6 space-y-4">
            <h3 className="font-semibold flex items-center gap-2">
              <Edit3 className="w-5 h-5" />
              ✏️ {t.edit[language]}
            </h3>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">📖 {language === 'tr' ? 'Başlık' : 'Title'}</label>
                <input
                  type="text"
                  value={editDocTitle}
                  onChange={(e) => setEditDocTitle(e.target.value)}
                  className="w-full px-4 py-2 bg-background border border-border rounded-xl"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">📌 {t.topic[language]}</label>
                <input
                  type="text"
                  value={editDocTopic}
                  onChange={(e) => setEditDocTopic(e.target.value)}
                  className="w-full px-4 py-2 bg-background border border-border rounded-xl"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">📄 {t.pageCount[language]}</label>
                <input
                  type="number"
                  min={1}
                  max={40}
                  value={editDocPageCount}
                  onChange={(e) => setEditDocPageCount(parseInt(e.target.value) || 5)}
                  className="w-full px-4 py-2 bg-background border border-border rounded-xl"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">✍️ {t.style[language]}</label>
                <select
                  value={editDocStyle}
                  onChange={(e) => setEditDocStyle(e.target.value)}
                  className="w-full px-4 py-2 bg-background border border-border rounded-xl"
                >
                  {DOCUMENT_STYLES.map((style) => (
                    <option key={style.id} value={style.id}>
                      {style.icon} {style.label[language]}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleSaveDocument}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-primary-500 text-white rounded-xl hover:bg-primary-600"
              >
                <Save className="w-4 h-4" />
                💾 {t.save[language]}
              </button>
              <button
                onClick={handleSaveAndRegenerate}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-green-500 text-white rounded-xl hover:bg-green-600"
              >
                <RefreshCw className="w-4 h-4" />
                🔄 {t.saveAndRegenerate[language]}
              </button>
              <button
                onClick={() => setIsEditingDoc(false)}
                className="px-4 py-2.5 bg-muted hover:bg-accent rounded-xl"
              >
                {t.cancel[language]}
              </button>
            </div>
          </div>
        )}

        {/* Content */}
        <div className="bg-card border border-border rounded-2xl p-6">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <FileText className="w-5 h-5" />
            📚 {t.content[language]}
          </h3>
          {readingDocument.content ? (
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown>{readingDocument.content}</ReactMarkdown>
            </div>
          ) : (
            <p className="text-muted-foreground italic">{t.contentNotGenerated[language]}</p>
          )}
        </div>

        {/* References */}
        {readingDocument.references && readingDocument.references.length > 0 && (
          <div className="bg-card border border-border rounded-2xl p-6">
            <h3 className="font-semibold mb-4 flex items-center gap-2">
              <BookOpen className="w-5 h-5" />
              📖 {t.references[language]}
            </h3>
            <ol className="list-decimal list-inside space-y-1 text-sm">
              {readingDocument.references.map((ref, idx) => (
                <li key={idx} className="text-muted-foreground">
                  {typeof ref === 'string' ? ref : `${ref.source} - Satır ${ref.line || '?'}`}
                </li>
              ))}
            </ol>
          </div>
        )}

        {/* Actions */}
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => handleDownloadDocument('md')}
            className="flex items-center gap-2 px-4 py-2 bg-muted hover:bg-accent rounded-xl transition-colors"
          >
            <Download className="w-4 h-4" />
            📥 {t.downloadMd[language]}
          </button>
          <button
            onClick={() => handleDownloadDocument('txt')}
            className="flex items-center gap-2 px-4 py-2 bg-muted hover:bg-accent rounded-xl transition-colors"
          >
            <Download className="w-4 h-4" />
            📄 {t.downloadTxt[language]}
          </button>
          <button
            onClick={() => {
              setEditDocTitle(readingDocument.title);
              setEditDocTopic(readingDocument.topic || '');
              setEditDocPageCount(readingDocument.page_count);
              setEditDocStyle(readingDocument.style);
              setIsEditingDoc(true);
            }}
            className="flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-xl hover:bg-primary-600 transition-colors"
          >
            <Edit3 className="w-4 h-4" />
            ✏️ {t.edit[language]}
          </button>
          <button
            onClick={handleRegenerateDocument}
            className="flex items-center gap-2 px-4 py-2 bg-green-500 text-white rounded-xl hover:bg-green-600 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            🔄 {t.regenerate[language]}
          </button>
          <button
            onClick={() => setConfirmDeleteDoc(true)}
            className="flex items-center gap-2 px-4 py-2 bg-destructive/10 text-destructive rounded-xl hover:bg-destructive/20 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
            🗑️ {t.delete[language]}
          </button>
        </div>

        {/* Delete Confirmation */}
        {confirmDeleteDoc && (
          <div className="bg-red-50 dark:bg-red-950/30 border-2 border-red-300 dark:border-red-700 rounded-2xl p-6">
            <p className="font-medium mb-4">⚠️ {t.confirmDelete[language]}</p>
            <div className="flex gap-3">
              <button
                onClick={handleDeleteDocument}
                className="flex items-center gap-2 px-4 py-2 bg-red-500 text-white rounded-xl hover:bg-red-600"
              >
                <Check className="w-4 h-4" />
                ✅ {t.yesDelete[language]}
              </button>
              <button
                onClick={() => setConfirmDeleteDoc(false)}
                className="px-4 py-2 bg-muted hover:bg-accent rounded-xl"
              >
                ❌ {t.cancel[language]}
              </button>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderSourcesTab = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold flex items-center gap-2">
          <BookOpen className="w-5 h-5" />
          📚 {t.sources[language]}
        </h3>
      </div>

      <p className="text-sm text-muted-foreground">
        {language === 'tr' 
          ? 'RAG sistemindeki dökümanları bu çalışma ortamı için aktif/deaktif edebilirsiniz.'
          : 'You can activate/deactivate documents in the RAG system for this workspace.'}
      </p>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-card border border-border rounded-xl p-4 text-center">
          <Folder className="w-6 h-6 mx-auto text-primary-500 mb-2" />
          <p className="text-2xl font-bold">{sources.length}</p>
          <p className="text-xs text-muted-foreground">📁 {t.totalSources[language]}</p>
        </div>
        <div className="bg-card border border-border rounded-xl p-4 text-center">
          <CheckCircle2 className="w-6 h-6 mx-auto text-green-500 mb-2" />
          <p className="text-2xl font-bold">{activeSourceCount}</p>
          <p className="text-xs text-muted-foreground">✅ {t.activeSources[language]}</p>
        </div>
        <div className="bg-card border border-border rounded-xl p-4 text-center">
          <XCircle className="w-6 h-6 mx-auto text-red-500 mb-2" />
          <p className="text-2xl font-bold">{sources.length - activeSourceCount}</p>
          <p className="text-xs text-muted-foreground">❌ {t.inactiveSources[language]}</p>
        </div>
      </div>

      {/* Bulk Actions */}
      {sources.length > 0 && (
        <div className="flex gap-3">
          <button
            onClick={() => handleBulkToggleSources(true)}
            disabled={bulkToggling}
            className="flex items-center gap-2 px-4 py-2 bg-green-500 text-white rounded-xl hover:bg-green-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {bulkToggling ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <ToggleRight className="w-4 h-4" />
            )}
            ✅ {t.activateAll[language]}
          </button>
          <button
            onClick={() => handleBulkToggleSources(false)}
            disabled={bulkToggling}
            className="flex items-center gap-2 px-4 py-2 bg-red-500 text-white rounded-xl hover:bg-red-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {bulkToggling ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <ToggleLeft className="w-4 h-4" />
            )}
            ❌ {t.deactivateAll[language]}
          </button>
        </div>
      )}

      {/* Sources List */}
      {sources.length === 0 ? (
        <div className="text-center py-12">
          <FileQuestion className="w-12 h-12 mx-auto text-muted-foreground/50 mb-4" />
          <p className="text-muted-foreground">{t.noSources[language]}</p>
        </div>
      ) : (
        <div className="space-y-2">
          {sources.map((source) => {
            const fileInfo = getFileIcon(source.type);
            const FileIcon = fileInfo.icon;
            
            return (
              <div
                key={source.id}
                className="flex items-center justify-between p-4 bg-card border border-border rounded-xl hover:border-primary-500/30 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className={cn("p-2 rounded-lg", fileInfo.bg)}>
                    <FileIcon className={cn("w-5 h-5", fileInfo.color)} />
                  </div>
                  <div>
                    <p className="font-medium">{source.name}</p>
                    <p className="text-xs text-muted-foreground">📏 {formatFileSize(source.size)}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-muted-foreground uppercase">{source.type}</span>
                  <button
                    onClick={() => handleToggleSource(source.id, !source.active)}
                    className={cn(
                      "relative w-12 h-6 rounded-full transition-colors",
                      source.active ? "bg-green-500" : "bg-gray-300 dark:bg-gray-600"
                    )}
                  >
                    <span
                      className={cn(
                        "absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform",
                        source.active ? "translate-x-6" : "translate-x-0.5"
                      )}
                    />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );

  const renderDocumentsTab = () => (
    <div className="space-y-6">
      {/* Create Document Form */}
      <details className="bg-card border border-border rounded-2xl overflow-hidden" open>
        <summary className="px-4 py-3 cursor-pointer hover:bg-accent font-medium flex items-center gap-2">
          <Plus className="w-4 h-4" />
          ➕ {t.createDocument[language]}
        </summary>
        <div className="p-4 border-t border-border space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">{language === 'tr' ? 'Başlık' : 'Title'} *</label>
              <input
                type="text"
                value={docTitle}
                onChange={(e) => setDocTitle(e.target.value)}
                placeholder={language === 'tr' ? 'Örn: ML Temelleri' : 'E.g., ML Basics'}
                className="w-full px-4 py-2 bg-background border border-border rounded-xl"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">{t.topic[language]} *</label>
              <input
                type="text"
                value={docTopic}
                onChange={(e) => setDocTopic(e.target.value)}
                placeholder={language === 'tr' ? 'Örn: Supervised Learning' : 'E.g., Supervised Learning'}
                className="w-full px-4 py-2 bg-background border border-border rounded-xl"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">{t.pageCount[language]}</label>
              <input
                type="range"
                min={1}
                max={40}
                value={docPageCount}
                onChange={(e) => setDocPageCount(parseInt(e.target.value))}
                className="w-full"
              />
              <p className="text-center text-sm text-muted-foreground">{docPageCount} {t.pages[language]}</p>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">{t.style[language]}</label>
              <select
                value={docStyle}
                onChange={(e) => setDocStyle(e.target.value)}
                className="w-full px-4 py-2 bg-background border border-border rounded-xl"
              >
                {DOCUMENT_STYLES.map((style) => (
                  <option key={style.id} value={style.id}>
                    {style.icon} {style.label[language]}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Web Search Option */}
          <div className="border-t border-border pt-4">
            <label className="block text-sm font-medium mb-3">🌐 {t.webSearch[language]}</label>
            <div className="grid grid-cols-3 gap-3">
              {WEB_SEARCH_OPTIONS.map((opt) => {
                const Icon = opt.icon;
                return (
                  <button
                    key={opt.id}
                    onClick={() => setDocWebSearch(opt.id as 'off' | 'auto' | 'on')}
                    className={cn(
                      "flex flex-col items-center p-3 rounded-xl border-2 transition-all",
                      docWebSearch === opt.id
                        ? "border-primary-500 bg-primary-500/10"
                        : "border-border hover:border-primary-500/50"
                    )}
                  >
                    <Icon className="w-5 h-5 mb-1" />
                    <span className="text-sm font-medium">{opt.label[language]}</span>
                    <span className="text-xs text-muted-foreground text-center">{opt.description[language]}</span>
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">{t.customInstructions[language]}</label>
            <textarea
              value={docCustomInstructions}
              onChange={(e) => setDocCustomInstructions(e.target.value)}
              placeholder={language === 'tr' ? 'Örn: Kod örnekleri ekle, tablolarla açıkla...' : 'E.g., Add code examples, explain with tables...'}
              rows={2}
              className="w-full px-4 py-2 bg-background border border-border rounded-xl resize-none"
            />
          </div>

          <button
            onClick={handleCreateDocument}
            disabled={!docTitle.trim() || !docTopic.trim()}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-primary-500 text-white rounded-xl hover:bg-primary-600 disabled:opacity-50 transition-colors"
          >
            <Zap className="w-4 h-4" />
            🚀 {t.createDocument[language]}
          </button>
        </div>
      </details>

      {/* Documents List */}
      <h3 className="font-semibold flex items-center gap-2">
        <FileText className="w-5 h-5" />
        📚 {language === 'tr' ? 'Oluşturulan Dökümanlar' : 'Created Documents'}
      </h3>

      {documents.length === 0 ? (
        <div className="text-center py-12">
          <FileText className="w-12 h-12 mx-auto text-muted-foreground/50 mb-4" />
          <p className="text-muted-foreground">{t.noDocuments[language]}</p>
        </div>
      ) : (
        <div className="space-y-3">
          {documents.map((doc) => (
            <div
              key={doc.id}
              className="flex items-center justify-between p-4 bg-card border border-border rounded-xl hover:border-primary-500/30 transition-colors"
            >
              <div className="flex items-center gap-3">
                {doc.status === 'completed' ? (
                  <CheckCircle2 className="w-5 h-5 text-green-500" />
                ) : doc.status === 'generating' ? (
                  <Loader2 className="w-5 h-5 text-yellow-500 animate-spin" />
                ) : doc.status === 'failed' ? (
                  <AlertCircle className="w-5 h-5 text-red-500" />
                ) : (
                  <Clock className="w-5 h-5 text-muted-foreground" />
                )}
                <div>
                  <p className="font-medium">{doc.title}</p>
                  <p className="text-xs text-muted-foreground">
                    📄 {doc.page_count} {t.pages[language]} • {DOCUMENT_STYLES.find(s => s.id === doc.style)?.label[language] || doc.style} • {doc.topic}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {doc.status === 'completed' && (
                  <button
                    onClick={() => handleViewDocument(doc)}
                    className="flex items-center gap-2 px-3 py-1.5 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
                  >
                    <Eye className="w-4 h-4" />
                    👁️ {t.read[language]}
                  </button>
                )}
                {doc.status === 'pending' && (
                  <button
                    onClick={() => {
                      setGeneratingDocId(doc.id);
                      setGeneratingDocConfig({
                        title: doc.title,
                        topic: doc.topic,
                        page_count: doc.page_count,
                        style: doc.style
                      });
                      setGenerationLogs([]);
                      setGenerationProgress(0);
                      setView('generating');
                      
                      // Start generation
                      apiPost(`/api/learning/documents/${doc.id}/generate`, {}).then(() => {
                        startPolling(doc.id);
                      });
                    }}
                    className="flex items-center gap-2 px-3 py-1.5 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
                  >
                    <Zap className="w-4 h-4" />
                    🚀 {language === 'tr' ? 'Oluştur' : 'Generate'}
                  </button>
                )}
                <button
                  onClick={async () => {
                    await apiDelete(`/api/learning/documents/${doc.id}`);
                    if (currentWorkspaceId) {
                      await loadWorkspaceData(currentWorkspaceId);
                    }
                  }}
                  className="p-1.5 hover:bg-destructive/10 text-destructive rounded-lg transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const renderTestsTab = () => {
    if (activeTest && testMode) {
      return testMode === 'taking' ? renderTestTaking() : renderTestResults();
    }

    return (
      <div className="space-y-6">
        {/* Create Test Form */}
        <details className="bg-card border border-border rounded-2xl overflow-hidden">
          <summary className="px-4 py-3 cursor-pointer hover:bg-accent font-medium flex items-center gap-2">
            <Plus className="w-4 h-4" />
            ➕ {t.createTest[language]}
          </summary>
          <div className="p-4 border-t border-border space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">{language === 'tr' ? 'Test Başlığı' : 'Test Title'} *</label>
              <input
                type="text"
                value={testTitle}
                onChange={(e) => setTestTitle(e.target.value)}
                placeholder={language === 'tr' ? 'Örn: ML Quiz 1' : 'E.g., ML Quiz 1'}
                className="w-full px-4 py-2 bg-background border border-border rounded-xl"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">{t.questionCount[language]}</label>
                <input
                  type="range"
                  min={5}
                  max={50}
                  value={testQuestionCount}
                  onChange={(e) => setTestQuestionCount(parseInt(e.target.value))}
                  className="w-full"
                />
                <p className="text-center text-sm text-muted-foreground">{testQuestionCount} {t.questions[language]}</p>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">{t.testType[language]}</label>
                <select
                  value={testType}
                  onChange={(e) => setTestType(e.target.value)}
                  className="w-full px-4 py-2 bg-background border border-border rounded-xl"
                >
                  {TEST_TYPES.map((type) => (
                    <option key={type.id} value={type.id}>
                      {type.icon} {type.label[language]}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">{t.difficulty[language]}</label>
              <div className="grid grid-cols-4 gap-2">
                {DIFFICULTIES.map((diff) => (
                  <button
                    key={diff.id}
                    onClick={() => setTestDifficulty(diff.id)}
                    className={cn(
                      "flex flex-col items-center p-3 rounded-xl border-2 transition-all",
                      testDifficulty === diff.id
                        ? "border-primary-500 bg-primary-500/10"
                        : "border-border hover:border-primary-500/50"
                    )}
                  >
                    <span className="text-xl">{diff.icon}</span>
                    <span className="text-sm">{diff.label[language]}</span>
                  </button>
                ))}
              </div>
            </div>

            <button
              onClick={handleCreateTest}
              disabled={!testTitle.trim() || creating}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-primary-500 text-white rounded-xl hover:bg-primary-600 disabled:opacity-50 transition-colors"
            >
              {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
              🚀 {t.createTest[language]}
            </button>
          </div>
        </details>

        {/* Tests List */}
        <h3 className="font-semibold flex items-center gap-2">
          <Target className="w-5 h-5" />
          📝 {language === 'tr' ? 'Oluşturulan Testler' : 'Created Tests'}
        </h3>

        {tests.length === 0 ? (
          <div className="text-center py-12">
            <Target className="w-12 h-12 mx-auto text-muted-foreground/50 mb-4" />
            <p className="text-muted-foreground">{t.noTests[language]}</p>
          </div>
        ) : (
          <div className="space-y-3">
            {tests.map((test) => {
              const diffInfo = DIFFICULTIES.find(d => d.id === test.difficulty);
              
              return (
                <div
                  key={test.id}
                  className="flex items-center justify-between p-4 bg-card border border-border rounded-xl hover:border-primary-500/30 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    {test.status === 'completed' ? (
                      <CheckCircle2 className="w-5 h-5 text-green-500" />
                    ) : test.status === 'in_progress' ? (
                      <Clock className="w-5 h-5 text-yellow-500" />
                    ) : (
                      <Target className="w-5 h-5 text-muted-foreground" />
                    )}
                    <div>
                      <p className="font-medium">{test.title}</p>
                      <p className="text-xs text-muted-foreground">
                        📋 {test.question_count} {t.questions[language]} • {diffInfo?.icon} {diffInfo?.label[language]}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {test.status === 'completed' && test.score !== undefined && (
                      <span className={cn(
                        "px-3 py-1 rounded-lg text-sm font-medium",
                        test.score >= 80 ? "bg-green-500/10 text-green-500" :
                        test.score >= 60 ? "bg-yellow-500/10 text-yellow-500" :
                        "bg-red-500/10 text-red-500"
                      )}>
                        🏆 %{test.score.toFixed(0)}
                      </span>
                    )}
                    <button
                      onClick={() => handleStartTest(test)}
                      className="flex items-center gap-2 px-3 py-1.5 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
                    >
                      <Play className="w-4 h-4" />
                      {test.status === 'pending' ? `🚀 ${t.start[language]}` : 
                       test.status === 'in_progress' ? `📝 ${t.continue[language]}` : 
                       `👁️ ${t.results[language]}`}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    );
  };

  const renderTestTaking = () => {
    if (!activeTest?.questions?.length) return null;
    
    const question = activeTest.questions[currentQuestion];
    const answeredCount = Object.keys(activeTest.user_answers || {}).length;

    return (
      <div className="max-w-2xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">{activeTest.title}</h3>
          <button
            onClick={() => {
              setActiveTest(null);
              setTestMode(null);
              setCurrentQuestion(0);
            }}
            className="p-2 hover:bg-accent rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-2">
          <div className="h-2 bg-muted rounded-full overflow-hidden">
            <div 
              className="h-full bg-primary-500 transition-all"
              style={{ width: `${(answeredCount / activeTest.questions.length) * 100}%` }}
            />
          </div>
          <p className="text-sm text-muted-foreground text-center">
            {answeredCount}/{activeTest.questions.length} {language === 'tr' ? 'cevaplandı' : 'answered'}
          </p>
        </div>

        <div className="bg-card border border-border rounded-2xl p-6">
          <p className="text-sm text-muted-foreground mb-2">
            {language === 'tr' ? 'Soru' : 'Question'} {currentQuestion + 1}
          </p>
          <p className="text-lg font-medium mb-6">{question.question}</p>

          {question.options && (
            <div className="space-y-2">
              {question.options.map((option, idx) => (
                <button
                  key={idx}
                  onClick={() => setSelectedAnswer(option[0])}
                  className={cn(
                    "w-full text-left p-4 rounded-xl border transition-all",
                    selectedAnswer === option[0]
                      ? "border-primary-500 bg-primary-500/10"
                      : "border-border hover:border-primary-500/50"
                  )}
                >
                  {option}
                </button>
              ))}
            </div>
          )}

          {!question.options && (
            <textarea
              value={selectedAnswer}
              onChange={(e) => setSelectedAnswer(e.target.value)}
              placeholder={t.yourAnswer[language]}
              rows={3}
              className="w-full px-4 py-3 bg-background border border-border rounded-xl resize-none"
            />
          )}
        </div>

        <div className="flex items-center justify-between">
          <button
            onClick={() => setCurrentQuestion(prev => Math.max(0, prev - 1))}
            disabled={currentQuestion === 0}
            className="flex items-center gap-2 px-4 py-2 bg-muted hover:bg-accent rounded-xl disabled:opacity-50 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            {t.previous[language]}
          </button>

          <button
            onClick={handleSubmitAnswer}
            disabled={!selectedAnswer}
            className="flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-xl hover:bg-primary-600 disabled:opacity-50 transition-colors"
          >
            {t.saveAnswer[language]}
          </button>

          {currentQuestion < activeTest.questions.length - 1 ? (
            <button
              onClick={() => setCurrentQuestion(prev => prev + 1)}
              className="flex items-center gap-2 px-4 py-2 bg-muted hover:bg-accent rounded-xl transition-colors"
            >
              {t.next[language]}
              <ChevronRight className="w-4 h-4" />
            </button>
          ) : (
            <button
              onClick={handleCompleteTest}
              disabled={answeredCount < activeTest.questions.length}
              className="flex items-center gap-2 px-4 py-2 bg-green-500 text-white rounded-xl hover:bg-green-600 disabled:opacity-50 transition-colors"
            >
              {t.finishTest[language]}
            </button>
          )}
        </div>
      </div>
    );
  };

  const renderTestResults = () => {
    if (!activeTest?.questions?.length) return null;

    const correctAnswers = activeTest.questions.filter(q => 
      (activeTest.user_answers?.[q.id] || '').toLowerCase().trim() === q.correct_answer.toLowerCase().trim()
    ).length;

    return (
      <div className="max-w-2xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">{t.results[language]}: {activeTest.title}</h3>
          <button
            onClick={() => {
              setActiveTest(null);
              setTestMode(null);
              setCurrentQuestion(0);
            }}
            className="p-2 hover:bg-accent rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div className="bg-primary-500/10 border border-primary-500/30 rounded-2xl p-5 text-center">
            <Trophy className="w-8 h-8 mx-auto text-primary-500 mb-2" />
            <p className="text-3xl font-bold">{activeTest.score || 0}%</p>
            <p className="text-sm text-muted-foreground">{t.score[language]}</p>
          </div>
          <div className="bg-green-500/10 border border-green-500/30 rounded-2xl p-5 text-center">
            <CheckCircle2 className="w-8 h-8 mx-auto text-green-500 mb-2" />
            <p className="text-3xl font-bold">{correctAnswers}</p>
            <p className="text-sm text-muted-foreground">{t.correct[language]}</p>
          </div>
          <div className="bg-red-500/10 border border-red-500/30 rounded-2xl p-5 text-center">
            <X className="w-8 h-8 mx-auto text-red-500 mb-2" />
            <p className="text-3xl font-bold">{activeTest.questions.length - correctAnswers}</p>
            <p className="text-sm text-muted-foreground">{t.wrong[language]}</p>
          </div>
        </div>

        <div className="space-y-3">
          {activeTest.questions.map((q, idx) => {
            const userAnswer = activeTest.user_answers?.[q.id] || '-';
            const isCorrect = userAnswer.toLowerCase().trim() === q.correct_answer.toLowerCase().trim();

            return (
              <div
                key={q.id}
                className={cn(
                  "p-4 rounded-xl border",
                  isCorrect ? "bg-green-500/5 border-green-500/30" : "bg-red-500/5 border-red-500/30"
                )}
              >
                <div className="flex items-start gap-3">
                  {isCorrect ? (
                    <CheckCircle2 className="w-5 h-5 text-green-500 mt-0.5" />
                  ) : (
                    <X className="w-5 h-5 text-red-500 mt-0.5" />
                  )}
                  <div className="flex-1">
                    <p className="font-medium mb-2">{idx + 1}. {q.question}</p>
                    <p className="text-sm">
                      <span className="text-muted-foreground">{t.yourAnswer[language]}:</span>{' '}
                      <span className={isCorrect ? 'text-green-500' : 'text-red-500'}>{userAnswer}</span>
                    </p>
                    {!isCorrect && (
                      <p className="text-sm">
                        <span className="text-muted-foreground">{t.correctAnswer[language]}:</span>{' '}
                        <span className="text-green-500">{q.correct_answer}</span>
                      </p>
                    )}
                    {q.explanation && (
                      <p className="text-sm text-muted-foreground mt-2">
                        <span className="font-medium">{t.explanation[language]}:</span> {q.explanation}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const renderChatTab = () => (
    <div className="flex flex-col h-[600px]">
      {/* Active Sources Info */}
      {activeSourceCount > 0 ? (
        <div className="mb-4 p-3 bg-green-500/10 border border-green-500/30 rounded-xl flex items-center gap-2">
          <CheckCircle2 className="w-5 h-5 text-green-500" />
          <span className="text-sm">✅ {activeSourceCount} {t.workingWith[language]}</span>
        </div>
      ) : (
        <div className="mb-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-xl flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-yellow-500" />
          <span className="text-sm">⚠️ {t.noActiveSource[language]}</span>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 p-4 bg-muted/30 rounded-t-2xl">
        {chatMessages.length === 0 ? (
          <div className="text-center py-12">
            <MessageSquare className="w-12 h-12 mx-auto text-muted-foreground/50 mb-4" />
            <p className="text-muted-foreground">💬 {t.startChat[language]}</p>
          </div>
        ) : (
          chatMessages.map((msg, idx) => (
            <div
              key={idx}
              className={cn(
                "flex gap-3",
                msg.role === 'user' ? 'justify-end' : 'justify-start'
              )}
            >
              <div
                className={cn(
                  "max-w-[80%] p-4 rounded-2xl",
                  msg.role === 'user'
                    ? "bg-primary-500 text-white"
                    : "bg-card border border-border"
                )}
              >
                {msg.role === 'assistant' ? (
                  <div className="prose prose-sm dark:prose-invert max-w-none">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>
                ) : (
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                )}
                {msg.sources && msg.sources.length > 0 && (
                  <p className="text-xs mt-2 opacity-70">
                    📚 {t.sourcesUsed[language]}: {msg.sources.join(', ')}
                  </p>
                )}
              </div>
            </div>
          ))
        )}
        {sendingChat && (
          <div className="flex gap-3 justify-start">
            <div className="bg-card border border-border p-4 rounded-2xl">
              <Loader2 className="w-5 h-5 animate-spin text-primary-500" />
            </div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-border bg-card rounded-b-2xl">
        <div className="flex items-center gap-3">
          <input
            type="text"
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendChat()}
            placeholder={t.askQuestion[language]}
            className="flex-1 px-4 py-3 bg-background border border-border rounded-xl"
          />
          <button
            onClick={handleSendChat}
            disabled={!chatInput.trim() || sendingChat}
            className="p-3 bg-primary-500 text-white rounded-xl hover:bg-primary-600 disabled:opacity-50 transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );

  const renderWorkspaceDetail = () => (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              setView('list');
              setCurrentWorkspaceId(null);
              setActiveTab('sources');
            }}
            className="p-2 hover:bg-accent rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h2 className="text-xl font-semibold">📖 {currentWorkspace?.name}</h2>
            {currentWorkspace?.topic && (
              <p className="text-sm text-muted-foreground">📌 Konu: {currentWorkspace.topic}</p>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2">
        {(['sources', 'documents', 'tests', 'chat'] as WorkspaceTab[]).map((tab) => {
          const icons = { sources: BookOpen, documents: FileText, tests: Target, chat: MessageSquare };
          const emojis = { sources: '📚', documents: '📄', tests: '📝', chat: '💬' };
          const Icon = icons[tab];
          return (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={cn(
                "flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium whitespace-nowrap transition-colors",
                activeTab === tab 
                  ? "bg-primary-500 text-white" 
                  : "bg-muted hover:bg-accent"
              )}
            >
              <Icon className="w-4 h-4" />
              {emojis[tab]} {t[tab][language]}
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
        </div>
      ) : (
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            {activeTab === 'sources' && renderSourcesTab()}
            {activeTab === 'documents' && renderDocumentsTab()}
            {activeTab === 'tests' && renderTestsTab()}
            {activeTab === 'chat' && renderChatTab()}
          </motion.div>
        </AnimatePresence>
      )}
    </div>
  );

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-border bg-card/50 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 text-white">
            <GraduationCap className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-semibold">📚 {t.title[language]}</h1>
            <p className="text-xs text-muted-foreground">{t.subtitle[language]}</p>
          </div>
        </div>
      </header>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-5xl mx-auto">
          <AnimatePresence mode="wait">
            <motion.div
              key={view}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              {view === 'list' && renderWorkspaceList()}
              {view === 'create' && renderCreateWorkspace()}
              {view === 'workspace' && renderWorkspaceDetail()}
              {view === 'generating' && renderGeneratingView()}
              {view === 'reading' && renderReadingView()}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
