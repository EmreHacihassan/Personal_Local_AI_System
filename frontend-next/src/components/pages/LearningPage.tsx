'use client';

import React, { useState, useEffect, useRef, useCallback, Suspense, lazy } from 'react';
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
  List,
  // Visual Learning & Premium Features
  Network,
  GitBranch,
  Calendar,
  Video,
  Mic,
  Link2,
  Route,
  Layers,
  // Image - unused
  Music,
  Film,
  Share2,
  // ChevronDown - unused
  Copy,
  // Stats & Archive
  BarChart3,
  Archive,
  TrendingUp,
  Award,
  // New Premium Features
  Bot,
  Repeat,
  Theater,
  PieChart,
  Flame,
  Star,
  ThumbsUp,
  ThumbsDown,
  RotateCcw,
  Rocket,
  Map
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { useStore } from '@/store/useStore';
import { cn } from '@/lib/utils';
import { DeepScholarCreator } from '@/components/learning/DeepScholarCreator';

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
const API_BASE = 'http://localhost:8000';

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

type LearningView = 'list' | 'create' | 'workspace' | 'generating' | 'reading' | 'journey' | 'stage';
type WorkspaceTab = 'sources' | 'documents' | 'tests' | 'chat' | 'tutor' | 'flashcards' | 'simulations' | 'analytics' | 'stats' | 'visual' | 'multimedia' | 'linking' | 'quality' | 'fullmeta' | 'journey';

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
  
  // DeepScholar Premium Mode
  const [useDeepScholar, setUseDeepScholar] = useState(false);
  const [reconnectDocumentId, setReconnectDocumentId] = useState<string | null>(null);

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
  const [testMode, setTestMode] = useState<'taking' | 'results' | 'generating' | null>(null);
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
    // Premium Feature Tabs
    visual: { tr: 'Görsel Araçlar', en: 'Visual Tools', de: 'Visuelle Tools' },
    multimedia: { tr: 'Multimedya', en: 'Multimedia', de: 'Multimedia' },
    linking: { tr: 'Akıllı Bağlantı', en: 'Smart Linking', de: 'Intelligente Verknüpfung' },
    quality: { tr: 'Kalite Merkezi', en: 'Quality Hub', de: 'Qualitätszentrum' },
    fullmeta: { tr: 'Full Meta', en: 'Full Meta', de: 'Full Meta' },
    journey: { tr: 'Öğrenme Yolculuğu', en: 'Learning Journey', de: 'Lernreise' },
    // Visual Learning
    mindMap: { tr: 'Zihin Haritası', en: 'Mind Map', de: 'Gedankenkarte' },
    conceptMap: { tr: 'Kavram Haritası', en: 'Concept Map', de: 'Konzeptkarte' },
    timeline: { tr: 'Zaman Çizelgesi', en: 'Timeline', de: 'Zeitleiste' },
    flowchart: { tr: 'Akış Şeması', en: 'Flowchart', de: 'Flussdiagramm' },
    infographic: { tr: 'İnfografik', en: 'Infographic', de: 'Infografik' },
    generateVisual: { tr: 'Görsel Oluştur', en: 'Generate Visual', de: 'Visuell generieren' },
    // Multimedia
    videoScript: { tr: 'Video Senaryosu', en: 'Video Script', de: 'Videoskript' },
    slidesDeck: { tr: 'Slayt Sunumu', en: 'Slide Deck', de: 'Folienpräsentation' },
    podcastScript: { tr: 'Podcast Metni', en: 'Podcast Script', de: 'Podcast-Skript' },
    audioSummary: { tr: 'Sesli Özet', en: 'Audio Summary', de: 'Audio-Zusammenfassung' },
    generateMultimedia: { tr: 'Multimedya Oluştur', en: 'Generate Multimedia', de: 'Multimedia generieren' },
    // Smart Linking
    prerequisites: { tr: 'Ön Koşullar', en: 'Prerequisites', de: 'Voraussetzungen' },
    relatedContent: { tr: 'İlgili İçerik', en: 'Related Content', de: 'Verwandte Inhalte' },
    learningPath: { tr: 'Öğrenme Yolu', en: 'Learning Path', de: 'Lernpfad' },
    nextTopics: { tr: 'Sonraki Konular', en: 'Next Topics', de: 'Nächste Themen' },
    analyzeContent: { tr: 'İçeriği Analiz Et', en: 'Analyze Content', de: 'Inhalt analysieren' },
    depth: { tr: 'Derinlik', en: 'Depth', de: 'Tiefe' },
    copyToClipboard: { tr: 'Panoya Kopyala', en: 'Copy to Clipboard', de: 'In Zwischenablage kopieren' },
    copied: { tr: 'Kopyalandı!', en: 'Copied!', de: 'Kopiert!' },
    // Stats & Archive
    stats: { tr: 'İstatistikler', en: 'Statistics', de: 'Statistiken' },
    archive: { tr: 'Arşivle', en: 'Archive', de: 'Archivieren' },
    totalDocuments: { tr: 'Toplam Döküman', en: 'Total Documents', de: 'Gesamte Dokumente' },
    completedDocuments: { tr: 'Tamamlanan Döküman', en: 'Completed Documents', de: 'Fertige Dokumente' },
    totalTests: { tr: 'Toplam Test', en: 'Total Tests', de: 'Gesamte Tests' },
    completedTests: { tr: 'Tamamlanan Test', en: 'Completed Tests', de: 'Abgeschlossene Tests' },
    averageScore: { tr: 'Ortalama Puan', en: 'Average Score', de: 'Durchschnittsnote' },
    progressOverview: { tr: 'İlerleme Özeti', en: 'Progress Overview', de: 'Fortschrittsübersicht' },
    noStatsYet: { tr: 'Henüz istatistik yok', en: 'No statistics yet', de: 'Noch keine Statistiken' },
    // New Premium Features
    tutor: { tr: 'AI Öğretmen', en: 'AI Tutor', de: 'KI-Tutor' },
    flashcards: { tr: 'Hafıza Kartları', en: 'Flashcards', de: 'Karteikarten' },
    simulations: { tr: 'Simülasyonlar', en: 'Simulations', de: 'Simulationen' },
    analytics: { tr: 'Analitik', en: 'Analytics', de: 'Analytik' },
    // AI Tutor
    startTutorSession: { tr: 'Oturum Başlat', en: 'Start Session', de: 'Sitzung starten' },
    tutorModes: { tr: 'Öğretim Modu', en: 'Teaching Mode', de: 'Lehrmodus' },
    socratic: { tr: 'Sokratik', en: 'Socratic', de: 'Sokratisch' },
    explanatory: { tr: 'Açıklayıcı', en: 'Explanatory', de: 'Erklärend' },
    challenging: { tr: 'Zorlayıcı', en: 'Challenging', de: 'Herausfordernd' },
    adaptive: { tr: 'Adaptif', en: 'Adaptive', de: 'Adaptiv' },
    questionsAsked: { tr: 'Soru Soruldu', en: 'Questions Asked', de: 'Gestellte Fragen' },
    correctAnswers: { tr: 'Doğru Cevap', en: 'Correct Answers', de: 'Richtige Antworten' },
    endSession: { tr: 'Oturumu Bitir', en: 'End Session', de: 'Sitzung beenden' },
    // Flashcards
    createCard: { tr: 'Kart Oluştur', en: 'Create Card', de: 'Karte erstellen' },
    generateCards: { tr: 'Otomatik Oluştur', en: 'Auto Generate', de: 'Auto generieren' },
    dueToday: { tr: 'Bugün Tekrar', en: 'Due Today', de: 'Heute fällig' },
    startReview: { tr: 'Tekrara Başla', en: 'Start Review', de: 'Überprüfung starten' },
    showAnswer: { tr: 'Cevabı Göster', en: 'Show Answer', de: 'Antwort anzeigen' },
    again: { tr: 'Tekrar', en: 'Again', de: 'Nochmal' },
    hard: { tr: 'Zor', en: 'Hard', de: 'Schwer' },
    good: { tr: 'İyi', en: 'Good', de: 'Gut' },
    easy: { tr: 'Kolay', en: 'Easy', de: 'Leicht' },
    newCards: { tr: 'Yeni', en: 'New', de: 'Neu' },
    learningCards: { tr: 'Öğreniliyor', en: 'Learning', de: 'Lernend' },
    reviewCards: { tr: 'Tekrar', en: 'Review', de: 'Überprüfung' },
    graduated: { tr: 'Tamamlandı', en: 'Graduated', de: 'Abgeschlossen' },
    retentionRate: { tr: 'Hatırlama Oranı', en: 'Retention Rate', de: 'Behaltensrate' },
    // Simulations
    startSimulation: { tr: 'Simülasyon Başlat', en: 'Start Simulation', de: 'Simulation starten' },
    scenarioType: { tr: 'Senaryo Türü', en: 'Scenario Type', de: 'Szenario-Typ' },
    interview: { tr: 'Mülakat', en: 'Interview', de: 'Interview' },
    presentation: { tr: 'Sunum', en: 'Presentation', de: 'Präsentation' },
    problemSolving: { tr: 'Problem Çözme', en: 'Problem Solving', de: 'Problemlösung' },
    debate: { tr: 'Tartışma', en: 'Debate', de: 'Debatte' },
    caseStudy: { tr: 'Vaka Analizi', en: 'Case Study', de: 'Fallstudie' },
    rolePlay: { tr: 'Rol Yapma', en: 'Role Play', de: 'Rollenspiel' },
    examSimulation: { tr: 'Sınav Simülasyonu', en: 'Exam Simulation', de: 'Prüfungssimulation' },
    scenarioObjectives: { tr: 'Hedefler', en: 'Objectives', de: 'Ziele' },
    turnCount: { tr: 'Tur Sayısı', en: 'Turn Count', de: 'Rundenanzahl' },
    // Analytics
    studyTime: { tr: 'Çalışma Süresi', en: 'Study Time', de: 'Lernzeit' },
    streakDays: { tr: 'Seri', en: 'Streak', de: 'Serie' },
    performanceTrend: { tr: 'Performans Trendi', en: 'Performance Trend', de: 'Leistungstrend' },
    improving: { tr: 'Yükseliyor', en: 'Improving', de: 'Verbessernd' },
    stable: { tr: 'Sabit', en: 'Stable', de: 'Stabil' },
    declining: { tr: 'Düşüyor', en: 'Declining', de: 'Abnehmend' },
    insights: { tr: 'İçgörüler', en: 'Insights', de: 'Einblicke' },
    weakAreas: { tr: 'Zayıf Alanlar', en: 'Weak Areas', de: 'Schwache Bereiche' },
    weeklyActivity: { tr: 'Haftalık Aktivite', en: 'Weekly Activity', de: 'Wöchentliche Aktivität' },
    minutes: { tr: 'dakika', en: 'minutes', de: 'Minuten' },
  };

  // Premium Features State
  const [visualTopic, setVisualTopic] = useState('');
  const [visualContent, setVisualContent] = useState('');
  const [visualLoading, setVisualLoading] = useState(false);
  const [visualResult, setVisualResult] = useState<{type: string; mermaid: string; nodes?: number; edges?: number} | null>(null);
  
  const [multimediaTopic, setMultimediaTopic] = useState('');
  const [multimediaContent, setMultimediaContent] = useState('');
  const [multimediaDuration, setMultimediaDuration] = useState(10);
  const [multimediaSlideCount, setMultimediaSlideCount] = useState(10);
  const [multimediaLoading, setMultimediaLoading] = useState(false);
  const [multimediaResult, setMultimediaResult] = useState<{type: string; content: string | object} | null>(null);
  
  const [linkingTopic, setLinkingTopic] = useState('');
  const [linkingContent, setLinkingContent] = useState('');
  const [linkingCurrentKnowledge, setLinkingCurrentKnowledge] = useState('');
  const [linkingLoading, setLinkingLoading] = useState(false);
  const [linkingResult, setLinkingResult] = useState<{type: string; data: unknown} | null>(null);
  
  const [copied, setCopied] = useState(false);
  
  // Stats State
  const [stats, setStats] = useState<{
    total_documents: number;
    completed_documents: number;
    total_tests: number;
    completed_tests: number;
    average_score: number;
  } | null>(null);
  const [statsLoading, setStatsLoading] = useState(false);
  
  // Document Integration State
  const [selectedDocForVisual, setSelectedDocForVisual] = useState<string | null>(null);
  const [selectedVisualTypes, setSelectedVisualTypes] = useState<string[]>(['mindmap', 'timeline']);
  const [docVisualLoading, setDocVisualLoading] = useState(false);
  const [docVisualResult, setDocVisualResult] = useState<Record<string, unknown> | null>(null);
  
  const [selectedDocForMultimedia, setSelectedDocForMultimedia] = useState<string | null>(null);
  const [selectedMultimediaType, setSelectedMultimediaType] = useState('slides');
  const [docMultimediaLoading, setDocMultimediaLoading] = useState(false);
  const [docMultimediaResult, setDocMultimediaResult] = useState<Record<string, unknown> | null>(null);

  // 🤖 AI Tutor State
  const [tutorSessionId, setTutorSessionId] = useState<string | null>(null);
  const [tutorTopic, setTutorTopic] = useState('');
  const [tutorMode, setTutorMode] = useState('adaptive');
  const [tutorMessages, setTutorMessages] = useState<{role: string; content: string}[]>([]);
  const [tutorInput, setTutorInput] = useState('');
  const [tutorLoading, setTutorLoading] = useState(false);
  const [tutorSession, setTutorSession] = useState<{
    questions_asked: number;
    correct_answers: number;
    accuracy: number;
    current_difficulty: string;
  } | null>(null);

  // 📚 Flashcards (SRS) State
  type FlashcardType = {
    id: string;
    front: string;
    back: string;
    status: string;
    ease_factor: number;
    interval: number;
    next_review: string;
    streak: number;
    accuracy: number;
  };
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [flashcards, setFlashcards] = useState<FlashcardType[]>([]);
  const [dueCards, setDueCards] = useState<FlashcardType[]>([]);
  const [flashcardStats, setFlashcardStats] = useState<{
    total: number;
    new: number;
    learning: number;
    review: number;
    graduated: number;
    due_today: number;
    retention_rate: number;
  } | null>(null);
  const [flashcardFront, setFlashcardFront] = useState('');
  const [flashcardBack, setFlashcardBack] = useState('');
  const [flashcardContent, setFlashcardContent] = useState('');
  const [flashcardLoading, setFlashcardLoading] = useState(false);
  const [reviewingCard, setReviewingCard] = useState<FlashcardType | null>(null);
  const [showCardBack, setShowCardBack] = useState(false);

  // 🎭 Simulations State
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [scenarioTypes, setScenarioTypes] = useState<{id: string; name: string; icon: string}[]>([]);
  const [scenarios, setScenarios] = useState<{
    id: string;
    title: string;
    scenario_type: string;
    status: string;
    difficulty: string;
    turn_count: number;
    evaluation?: {overall_score: number; grade: string};
  }[]>([]);
  const [activeScenario, setActiveScenario] = useState<{
    id: string;
    title: string;
    description: string;
    objectives: string[];
    conversation: {role: string; content: string}[];
    status: string;
    evaluation?: Record<string, unknown>;
  } | null>(null);
  const [scenarioTopic, setScenarioTopic] = useState('');
  const [scenarioType, setScenarioType] = useState('interview');
  const [scenarioDifficulty, setScenarioDifficulty] = useState('medium');
  const [scenarioInput, setScenarioInput] = useState('');
  const [scenarioLoading, setScenarioLoading] = useState(false);

  // 📊 Analytics State
  const [analyticsData, setAnalyticsData] = useState<{
    total_study_time: number;
    session_count: number;
    documents_read: number;
    tests_completed: number;
    cards_reviewed: number;
    average_score: number;
    streak_days: number;
    performance_trend: string;
  } | null>(null);
  const [weeklyActivity, setWeeklyActivity] = useState<{
    date: string;
    day_name: string;
    minutes: number;
    events: number;
  }[]>([]);
  const [learningInsights, setLearningInsights] = useState<{
    insight_type: string;
    title: string;
    description: string;
    importance: string;
    action_items: string[];
  }[]>([]);
  const [weakAreas, setWeakAreas] = useState<{topic: string; average_score: number}[]>([]);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);

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

    if (response.success && response.test) {
      // Test oluşturuldu, şimdi soru üretimini başlat
      const testId = response.test.id;
      
      try {
        // SSE ile soru üretimi
        const eventSource = new EventSource(
          `${typeof window !== 'undefined' ? window.location.origin : ''}/api/learning/tests/${testId}/generate`
        );
        
        eventSource.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'complete' || data.type === 'error') {
              eventSource.close();
              // Workspace'i yeniden yükle
              if (currentWorkspaceId) {
                loadWorkspaceData(currentWorkspaceId);
              }
            }
          } catch (e) {
            console.error('SSE parse error:', e);
          }
        };
        
        eventSource.onerror = () => {
          eventSource.close();
          // Workspace'i yeniden yükle
          if (currentWorkspaceId) {
            loadWorkspaceData(currentWorkspaceId);
          }
        };
        
        // 60 saniye timeout
        setTimeout(() => {
          eventSource.close();
          if (currentWorkspaceId) {
            loadWorkspaceData(currentWorkspaceId);
          }
        }, 60000);
        
      } catch (e) {
        console.error('Test generation error:', e);
      }
      
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
      const testData = response.test;
      
      // Eğer sorular üretilmemişse, önce üret
      if (!testData.questions || testData.questions.length === 0) {
        // Loading state göster
        setActiveTest({ ...testData, questions: [] });
        setTestMode('generating');
        
        try {
          // SSE ile soru üretimi
          const eventSource = new EventSource(
            `${typeof window !== 'undefined' ? window.location.origin : ''}/api/learning/tests/${test.id}/generate`
          );
          
          const generatedQuestions: any[] = [];
          
          eventSource.onmessage = async (event) => {
            try {
              const data = JSON.parse(event.data);
              
              if (data.type === 'question') {
                generatedQuestions.push(data.question);
                setActiveTest(prev => prev ? {
                  ...prev,
                  questions: [...generatedQuestions]
                } : null);
              }
              
              if (data.type === 'complete') {
                eventSource.close();
                // Test'i yeniden al
                const updatedResponse = await apiGet(`/api/learning/tests/${test.id}`);
                if (updatedResponse.test) {
                  setActiveTest(updatedResponse.test);
                  setCurrentQuestion(0);
                  setTestMode('taking');
                }
              }
              
              if (data.type === 'error') {
                eventSource.close();
                setTestMode('taking');
              }
            } catch (e) {
              console.error('SSE parse error:', e);
            }
          };
          
          eventSource.onerror = () => {
            eventSource.close();
            setTestMode('taking');
          };
          
          // 120 saniye timeout
          setTimeout(() => {
            eventSource.close();
          }, 120000);
          
        } catch (e) {
          console.error('Test generation error:', e);
          setTestMode('taking');
        }
      } else {
        // Sorular zaten var
        setActiveTest(testData);
        setCurrentQuestion(0);
        setTestMode('taking');
      }
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
                <div className="flex items-center gap-1">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleArchiveWorkspace(ws.id);
                    }}
                    className="p-1.5 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-amber-500/10 text-amber-600 transition-all"
                    title={t.archive[language]}
                  >
                    <Archive className="w-4 h-4" />
                  </button>
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
      {/* Mode Toggle - Premium/Standard */}
      <div className="flex items-center justify-between p-4 bg-gradient-to-r from-purple-500/10 via-blue-500/10 to-emerald-500/10 border border-purple-500/30 rounded-2xl">
        <div className="flex items-center gap-3">
          <div className={cn(
            "p-2 rounded-xl transition-all",
            useDeepScholar ? "bg-gradient-to-br from-purple-500 to-blue-500 text-white" : "bg-muted"
          )}>
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-semibold flex items-center gap-2">
              🚀 DeepScholar v2.0
              <span className="text-xs px-2 py-0.5 bg-gradient-to-r from-purple-500 to-blue-500 text-white rounded-full">
                PREMIUM
              </span>
            </h3>
            <p className="text-xs text-muted-foreground">
              {language === 'tr' 
                ? 'Çoklu ajan, akademik kaynak, PDF export, canlı izleme' 
                : 'Multi-agent, academic sources, PDF export, live tracking'}
            </p>
          </div>
        </div>
        <button
          onClick={() => setUseDeepScholar(!useDeepScholar)}
          className={cn(
            "relative w-14 h-7 rounded-full transition-all duration-300",
            useDeepScholar 
              ? "bg-gradient-to-r from-purple-500 to-blue-500" 
              : "bg-muted"
          )}
        >
          <div className={cn(
            "absolute top-1 w-5 h-5 rounded-full bg-white shadow-lg transition-all duration-300",
            useDeepScholar ? "left-8" : "left-1"
          )} />
        </button>
      </div>

      {/* DeepScholar or Standard Form */}
      {useDeepScholar ? (
        <DeepScholarCreator
          workspaceId={currentWorkspaceId || ''}
          language={language as 'tr' | 'en'}
          reconnectDocumentId={reconnectDocumentId}
          initialTitle={docTitle}
          initialTopic={docTopic}
          initialPageCount={docPageCount}
          initialStyle={docStyle}
          onClose={() => {
            setUseDeepScholar(false);
            setReconnectDocumentId(null);
            // Clear form values
            setDocTitle('');
            setDocTopic('');
            setDocPageCount(10);
            setDocStyle('academic');
          }}
          onComplete={async (_documentId) => {
            setUseDeepScholar(false);
            setReconnectDocumentId(null);
            // Clear form values
            setDocTitle('');
            setDocTopic('');
            setDocPageCount(10);
            setDocStyle('academic');
            // Reload workspace data to get new document
            if (currentWorkspaceId) {
              await loadWorkspaceData(currentWorkspaceId);
            }
          }}
        />
      ) : (
        <>
          {/* Standard Create Document Form */}
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
        </>
      )}

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
                {doc.status === 'generating' && (
                  <button
                    onClick={() => {
                      // DeepScholar reconnect
                      setReconnectDocumentId(doc.id);
                      setUseDeepScholar(true);
                    }}
                    className="flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:from-purple-600 hover:to-pink-600 transition-colors animate-pulse"
                  >
                    <Loader2 className="w-4 h-4 animate-spin" />
                    🔗 {language === 'tr' ? 'Bağlan' : 'Reconnect'}
                  </button>
                )}
                {(doc.status === 'cancelled' || doc.status === 'failed') && (
                  <button
                    onClick={() => {
                      // Yeniden başlat - DeepScholar kullan
                      setDocTitle(doc.title);
                      setDocTopic(doc.topic || '');
                      setDocPageCount(doc.page_count);
                      setDocStyle(doc.style);
                      setUseDeepScholar(true);
                    }}
                    className="flex items-center gap-2 px-3 py-1.5 bg-amber-500 text-white rounded-lg hover:bg-amber-600 transition-colors"
                  >
                    <RefreshCw className="w-4 h-4" />
                    🔄 {language === 'tr' ? 'Yeniden Oluştur' : 'Restart'}
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
      if (testMode === 'generating') {
        return (
          <div className="flex flex-col items-center justify-center p-12 bg-card rounded-2xl border border-border">
            <Loader2 className="w-12 h-12 animate-spin text-primary-500 mb-4" />
            <h3 className="text-xl font-semibold mb-2">
              {language === 'tr' ? 'Sorular Üretiliyor...' : 'Generating Questions...'}
            </h3>
            <p className="text-muted-foreground text-center">
              {language === 'tr' 
                ? `${activeTest.questions?.length || 0} / ${activeTest.question_count} soru üretildi`
                : `${activeTest.questions?.length || 0} / ${activeTest.question_count} questions generated`
              }
            </p>
            <div className="w-64 h-2 bg-muted rounded-full mt-4 overflow-hidden">
              <div 
                className="h-full bg-primary-500 transition-all duration-300"
                style={{ 
                  width: `${((activeTest.questions?.length || 0) / (activeTest.question_count || 1)) * 100}%` 
                }}
              />
            </div>
          </div>
        );
      }
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

  // ==================== PREMIUM FEATURES - VISUAL LEARNING ====================
  const handleGenerateVisual = async (type: string) => {
    if (!visualTopic.trim() || !visualContent.trim()) return;
    
    setVisualLoading(true);
    setVisualResult(null);
    
    try {
      const endpoint = `/api/learning/visual/${type}`;
      const response = await apiPost(endpoint, { 
        topic: visualTopic, 
        content: visualContent 
      });
      
      if (!response.error && response.success) {
        setVisualResult({
          type,
          mermaid: response.mermaid || response.diagram || '',
          nodes: response.nodes,
          edges: response.edges
        });
      }
    } catch (err) {
      console.error('Visual generation error:', err);
    }
    
    setVisualLoading(false);
  };
  
  // Document Visual Generation
  const handleDocumentVisualize = async () => {
    if (!selectedDocForVisual || selectedVisualTypes.length === 0) return;
    
    setDocVisualLoading(true);
    setDocVisualResult(null);
    
    try {
      const response = await apiPost(`/api/learning/documents/${selectedDocForVisual}/visualize`, {
        visual_types: selectedVisualTypes
      });
      
      if (!response.error && response.success) {
        setDocVisualResult(response.visuals);
      }
    } catch (err) {
      console.error('Document visualize error:', err);
    }
    
    setDocVisualLoading(false);
  };
  
  // Document Multimedia Generation
  const handleDocumentMultimedia = async () => {
    if (!selectedDocForMultimedia) return;
    
    setDocMultimediaLoading(true);
    setDocMultimediaResult(null);
    
    try {
      const response = await apiPost(`/api/learning/documents/${selectedDocForMultimedia}/multimedia`, {
        content_type: selectedMultimediaType
      });
      
      if (!response.error && response.success) {
        setDocMultimediaResult(response);
      }
    } catch (err) {
      console.error('Document multimedia error:', err);
    }
    
    setDocMultimediaLoading(false);
  };
  
  // Load Stats
  const loadStats = async () => {
    if (!currentWorkspaceId) return;
    
    setStatsLoading(true);
    try {
      const response = await apiGet(`/api/learning/workspaces/${currentWorkspaceId}/stats`);
      if (!response.error) {
        setStats(response);
      }
    } catch (err) {
      console.error('Stats load error:', err);
    }
    setStatsLoading(false);
  };
  
  // Archive Workspace
  const handleArchiveWorkspace = async (workspaceId: string) => {
    const response = await apiPost(`/api/learning/workspaces/${workspaceId}/archive`, {});
    if (response.success) {
      await loadWorkspaces();
      if (currentWorkspaceId === workspaceId) {
        setCurrentWorkspaceId(null);
        setView('list');
      }
    }
  };

  const handleCopyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const renderVisualTab = () => (
    <div className="space-y-6">
      {/* Premium Badge */}
      <div className="bg-gradient-to-r from-violet-500/10 to-purple-500/10 border border-violet-300 dark:border-violet-700 rounded-2xl p-4 flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="font-semibold text-violet-700 dark:text-violet-300">🎨 {t.visual[language]} - Premium</h3>
          <p className="text-sm text-muted-foreground">
            {language === 'tr' ? 'Konularınızı görsel diyagramlara dönüştürün' : 'Transform your topics into visual diagrams'}
          </p>
        </div>
      </div>

      {/* Input Section */}
      <div className="bg-card border border-border rounded-2xl p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">📌 {t.topic[language]}</label>
          <input
            type="text"
            value={visualTopic}
            onChange={(e) => setVisualTopic(e.target.value)}
            placeholder={language === 'tr' ? 'Örn: Machine Learning, Python OOP, Neural Networks...' : 'E.g., Machine Learning, Python OOP, Neural Networks...'}
            className="w-full px-4 py-3 bg-background border border-border rounded-xl"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium mb-2">� {t.content[language]} *</label>
          <textarea
            value={visualContent}
            onChange={(e) => setVisualContent(e.target.value)}
            placeholder={language === 'tr' ? 'Görselleştirmek istediğiniz içeriği buraya yazın veya yapıştırın. En az 10 karakter olmalıdır...' : 'Write or paste the content you want to visualize here. Must be at least 10 characters...'}
            rows={6}
            className="w-full px-4 py-3 bg-background border border-border rounded-xl resize-none"
          />
          <p className="text-xs text-muted-foreground mt-1">
            {visualContent.length}/100000 {language === 'tr' ? 'karakter' : 'characters'}
          </p>
        </div>
      </div>

      {/* Visual Type Buttons */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {[
          { id: 'mindmap', label: t.mindMap, icon: Brain, emoji: '🧠', color: 'from-blue-500 to-cyan-500' },
          { id: 'conceptmap', label: t.conceptMap, icon: Network, emoji: '🔗', color: 'from-green-500 to-emerald-500' },
          { id: 'timeline', label: t.timeline, icon: Calendar, emoji: '📅', color: 'from-orange-500 to-amber-500' },
          { id: 'flowchart', label: t.flowchart, icon: GitBranch, emoji: '📊', color: 'from-purple-500 to-pink-500' },
          { id: 'infographic', label: t.infographic, icon: Layers, emoji: '📈', color: 'from-red-500 to-rose-500' },
        ].map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              onClick={() => handleGenerateVisual(item.id)}
              disabled={!visualTopic.trim() || visualContent.length < 10 || visualLoading}
              className={cn(
                "flex flex-col items-center p-4 rounded-2xl border-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed",
                "hover:scale-105 hover:shadow-lg",
                `bg-gradient-to-br ${item.color} text-white border-transparent`
              )}
            >
              <Icon className="w-6 h-6 mb-2" />
              <span className="text-sm font-medium">{item.emoji} {item.label[language]}</span>
            </button>
          );
        })}
      </div>
      
      {/* Document Integration Section */}
      {documents.length > 0 && (
        <div className="bg-gradient-to-r from-blue-500/10 to-indigo-500/10 border border-blue-300 dark:border-blue-700 rounded-2xl p-6 space-y-4">
          <h4 className="font-semibold text-blue-700 dark:text-blue-300 flex items-center gap-2">
            <FileText className="w-5 h-5" />
            📄 {language === 'tr' ? 'Dökümanlardan Görsel Oluştur' : 'Create Visuals from Documents'}
          </h4>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">{language === 'tr' ? 'Döküman Seç' : 'Select Document'}</label>
              <select
                value={selectedDocForVisual || ''}
                onChange={(e) => setSelectedDocForVisual(e.target.value || null)}
                className="w-full px-4 py-2 bg-background border border-border rounded-xl"
              >
                <option value="">{language === 'tr' ? 'Döküman seçin...' : 'Select document...'}</option>
                {documents.filter(d => d.status === 'completed' && d.content).map((doc) => (
                  <option key={doc.id} value={doc.id}>{doc.title}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">{language === 'tr' ? 'Görsel Türleri' : 'Visual Types'}</label>
              <div className="flex flex-wrap gap-2">
                {['mindmap', 'timeline', 'flowchart', 'conceptmap', 'infographic'].map((type) => (
                  <button
                    key={type}
                    onClick={() => setSelectedVisualTypes(prev => 
                      prev.includes(type) ? prev.filter(t => t !== type) : [...prev, type]
                    )}
                    className={cn(
                      "px-3 py-1 rounded-lg text-xs font-medium transition-colors",
                      selectedVisualTypes.includes(type)
                        ? "bg-blue-500 text-white"
                        : "bg-muted hover:bg-accent"
                    )}
                  >
                    {type}
                  </button>
                ))}
              </div>
            </div>
          </div>
          
          <button
            onClick={handleDocumentVisualize}
            disabled={!selectedDocForVisual || selectedVisualTypes.length === 0 || docVisualLoading}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-blue-500 text-white rounded-xl hover:bg-blue-600 disabled:opacity-50 transition-colors"
          >
            {docVisualLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
            🚀 {language === 'tr' ? 'Dökümanı Görselleştir' : 'Visualize Document'}
          </button>
          
          {/* Document Visual Result */}
          {docVisualResult && (
            <div className="bg-card border border-border rounded-xl p-4 space-y-4 mt-4">
              <h5 className="font-medium">✅ {language === 'tr' ? 'Oluşturulan Görseller' : 'Generated Visuals'}</h5>
              {Object.entries(docVisualResult).map(([key, value]) => (
                <details key={key} className="bg-muted/50 rounded-xl overflow-hidden">
                  <summary className="px-4 py-3 cursor-pointer hover:bg-accent font-medium capitalize">{key}</summary>
                  <pre className="p-4 text-xs font-mono whitespace-pre-wrap overflow-x-auto">
                    {typeof value === 'string' ? value : JSON.stringify(value, null, 2)}
                  </pre>
                </details>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Loading State */}
      {visualLoading && (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <Loader2 className="w-12 h-12 animate-spin text-violet-500 mx-auto mb-4" />
            <p className="text-muted-foreground">{language === 'tr' ? 'Görsel oluşturuluyor...' : 'Generating visual...'}</p>
          </div>
        </div>
      )}

      {/* Result */}
      {visualResult && (
        <div className="bg-card border border-border rounded-2xl overflow-hidden">
          <div className="flex items-center justify-between p-4 border-b border-border bg-muted/50">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-green-500" />
              <span className="font-medium">
                {visualResult.type === 'mindmap' && t.mindMap[language]}
                {visualResult.type === 'conceptmap' && t.conceptMap[language]}
                {visualResult.type === 'timeline' && t.timeline[language]}
                {visualResult.type === 'flowchart' && t.flowchart[language]}
                {visualResult.type === 'infographic' && t.infographic[language]}
              </span>
              {visualResult.nodes && (
                <span className="text-xs text-muted-foreground">
                  ({visualResult.nodes} nodes, {visualResult.edges} edges)
                </span>
              )}
            </div>
            <button
              onClick={() => handleCopyToClipboard(visualResult.mermaid)}
              className="flex items-center gap-2 px-3 py-1.5 bg-primary-500 text-white rounded-lg hover:bg-primary-600"
            >
              {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
              {copied ? t.copied[language] : t.copyToClipboard[language]}
            </button>
          </div>
          <div className="p-4">
            <pre className="bg-muted/50 p-4 rounded-xl overflow-x-auto text-sm font-mono whitespace-pre-wrap">
              {visualResult.mermaid}
            </pre>
            <p className="text-xs text-muted-foreground mt-3">
              💡 {language === 'tr' 
                ? 'Mermaid kodunu Mermaid Live Editor veya destekleyen herhangi bir editörde görselleştirebilirsiniz.'
                : 'You can visualize this Mermaid code in Mermaid Live Editor or any supporting editor.'}
            </p>
          </div>
        </div>
      )}
    </div>
  );

  // ==================== PREMIUM FEATURES - MULTIMEDIA ====================
  const handleGenerateMultimedia = async (type: string) => {
    if (!multimediaTopic.trim() || !multimediaContent.trim()) return;
    
    setMultimediaLoading(true);
    setMultimediaResult(null);
    
    try {
      const endpoint = `/api/learning/multimedia/${type}`;
      const body: Record<string, unknown> = { 
        topic: multimediaTopic, 
        content: multimediaContent 
      };
      
      // Add type-specific parameters
      if (type === 'video-script' || type === 'podcast') {
        body.duration_minutes = multimediaDuration;
        body.style = 'educational';
      }
      if (type === 'slides') {
        body.slide_count = multimediaSlideCount;
        body.include_notes = true;
      }
      if (type === 'podcast') {
        body.host_count = 1;
      }
      
      const response = await apiPost(endpoint, body);
      
      if (!response.error && response.success) {
        setMultimediaResult({
          type,
          content: response.script || response.slides || response.content || response
        });
      }
    } catch (err) {
      console.error('Multimedia generation error:', err);
    }
    
    setMultimediaLoading(false);
  };

  const renderMultimediaTab = () => (
    <div className="space-y-6">
      {/* Premium Badge */}
      <div className="bg-gradient-to-r from-pink-500/10 to-rose-500/10 border border-pink-300 dark:border-pink-700 rounded-2xl p-4 flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-pink-500 to-rose-600 flex items-center justify-center">
          <Film className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="font-semibold text-pink-700 dark:text-pink-300">🎬 {t.multimedia[language]} - Premium</h3>
          <p className="text-sm text-muted-foreground">
            {language === 'tr' ? 'Video, slayt ve podcast içerikleri oluşturun' : 'Create video, slide and podcast content'}
          </p>
        </div>
      </div>

      {/* Input Section */}
      <div className="bg-card border border-border rounded-2xl p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">📌 {t.topic[language]}</label>
          <input
            type="text"
            value={multimediaTopic}
            onChange={(e) => setMultimediaTopic(e.target.value)}
            placeholder={language === 'tr' ? 'Örn: React Hooks, Python Decorators...' : 'E.g., React Hooks, Python Decorators...'}
            className="w-full px-4 py-3 bg-background border border-border rounded-xl"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium mb-2">📝 {t.content[language]} *</label>
          <textarea
            value={multimediaContent}
            onChange={(e) => setMultimediaContent(e.target.value)}
            placeholder={language === 'tr' ? 'Multimedya içeriği oluşturmak istediğiniz metni buraya yazın veya yapıştırın. En az 10 karakter olmalıdır...' : 'Write or paste the text you want to convert to multimedia content here. Must be at least 10 characters...'}
            rows={6}
            className="w-full px-4 py-3 bg-background border border-border rounded-xl resize-none"
          />
          <p className="text-xs text-muted-foreground mt-1">
            {multimediaContent.length}/100000 {language === 'tr' ? 'karakter' : 'characters'}
          </p>
        </div>
        
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">⏱️ {language === 'tr' ? 'Süre' : 'Duration'}: {multimediaDuration} {language === 'tr' ? 'dakika' : 'minutes'}</label>
            <input
              type="range"
              min={3}
              max={60}
              value={multimediaDuration}
              onChange={(e) => setMultimediaDuration(parseInt(e.target.value))}
              className="w-full"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">📊 {language === 'tr' ? 'Slayt Sayısı' : 'Slide Count'}: {multimediaSlideCount}</label>
            <input
              type="range"
              min={3}
              max={30}
              value={multimediaSlideCount}
              onChange={(e) => setMultimediaSlideCount(parseInt(e.target.value))}
              className="w-full"
            />
          </div>
        </div>
      </div>

      {/* Multimedia Type Buttons */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { id: 'video-script', label: t.videoScript, icon: Video, emoji: '🎥', color: 'from-red-500 to-pink-500' },
          { id: 'slides', label: t.slidesDeck, icon: Presentation, emoji: '📊', color: 'from-blue-500 to-indigo-500' },
          { id: 'podcast', label: t.podcastScript, icon: Mic, emoji: '🎙️', color: 'from-purple-500 to-violet-500' },
          { id: 'audio-summary', label: t.audioSummary, icon: Music, emoji: '🔊', color: 'from-green-500 to-teal-500' },
        ].map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              onClick={() => handleGenerateMultimedia(item.id)}
              disabled={!multimediaTopic.trim() || multimediaContent.length < 10 || multimediaLoading}
              className={cn(
                "flex flex-col items-center p-4 rounded-2xl border-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed",
                "hover:scale-105 hover:shadow-lg",
                `bg-gradient-to-br ${item.color} text-white border-transparent`
              )}
            >
              <Icon className="w-6 h-6 mb-2" />
              <span className="text-sm font-medium">{item.emoji} {item.label[language]}</span>
            </button>
          );
        })}
      </div>
      
      {/* Document Integration Section */}
      {documents.length > 0 && (
        <div className="bg-gradient-to-r from-orange-500/10 to-amber-500/10 border border-orange-300 dark:border-orange-700 rounded-2xl p-6 space-y-4">
          <h4 className="font-semibold text-orange-700 dark:text-orange-300 flex items-center gap-2">
            <FileText className="w-5 h-5" />
            📄 {language === 'tr' ? 'Dökümanlardan Multimedya Oluştur' : 'Create Multimedia from Documents'}
          </h4>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">{language === 'tr' ? 'Döküman Seç' : 'Select Document'}</label>
              <select
                value={selectedDocForMultimedia || ''}
                onChange={(e) => setSelectedDocForMultimedia(e.target.value || null)}
                className="w-full px-4 py-2 bg-background border border-border rounded-xl"
              >
                <option value="">{language === 'tr' ? 'Döküman seçin...' : 'Select document...'}</option>
                {documents.filter(d => d.status === 'completed' && d.content).map((doc) => (
                  <option key={doc.id} value={doc.id}>{doc.title}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">{language === 'tr' ? 'İçerik Türü' : 'Content Type'}</label>
              <select
                value={selectedMultimediaType}
                onChange={(e) => setSelectedMultimediaType(e.target.value)}
                className="w-full px-4 py-2 bg-background border border-border rounded-xl"
              >
                <option value="slides">📊 {t.slidesDeck[language]}</option>
                <option value="video">🎥 {t.videoScript[language]}</option>
                <option value="podcast">🎙️ {t.podcastScript[language]}</option>
                <option value="audio">🔊 {t.audioSummary[language]}</option>
              </select>
            </div>
          </div>
          
          <button
            onClick={handleDocumentMultimedia}
            disabled={!selectedDocForMultimedia || docMultimediaLoading}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-orange-500 text-white rounded-xl hover:bg-orange-600 disabled:opacity-50 transition-colors"
          >
            {docMultimediaLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
            🚀 {language === 'tr' ? 'Dökümanı Dönüştür' : 'Convert Document'}
          </button>
          
          {/* Document Multimedia Result */}
          {docMultimediaResult && (
            <div className="bg-card border border-border rounded-xl p-4 space-y-4 mt-4">
              <div className="flex items-center justify-between">
                <h5 className="font-medium">✅ {docMultimediaResult.content_type as string}</h5>
                <button
                  onClick={() => handleCopyToClipboard(
                    typeof docMultimediaResult === 'string' 
                      ? docMultimediaResult 
                      : JSON.stringify(docMultimediaResult, null, 2)
                  )}
                  className="flex items-center gap-2 px-3 py-1.5 bg-primary-500 text-white rounded-lg hover:bg-primary-600"
                >
                  {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                  {copied ? t.copied[language] : t.copyToClipboard[language]}
                </button>
              </div>
              <pre className="bg-muted/50 p-4 rounded-xl text-xs font-mono whitespace-pre-wrap overflow-x-auto max-h-96 overflow-y-auto">
                {JSON.stringify(docMultimediaResult, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* Loading State */}
      {multimediaLoading && (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <Loader2 className="w-12 h-12 animate-spin text-pink-500 mx-auto mb-4" />
            <p className="text-muted-foreground">{language === 'tr' ? 'İçerik oluşturuluyor...' : 'Generating content...'}</p>
          </div>
        </div>
      )}

      {/* Result */}
      {multimediaResult && (
        <div className="bg-card border border-border rounded-2xl overflow-hidden">
          <div className="flex items-center justify-between p-4 border-b border-border bg-muted/50">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-green-500" />
              <span className="font-medium">
                {multimediaResult.type === 'video-script' && t.videoScript[language]}
                {multimediaResult.type === 'slides' && t.slidesDeck[language]}
                {multimediaResult.type === 'podcast' && t.podcastScript[language]}
                {multimediaResult.type === 'audio-summary' && t.audioSummary[language]}
              </span>
            </div>
            <button
              onClick={() => handleCopyToClipboard(
                typeof multimediaResult.content === 'string' 
                  ? multimediaResult.content 
                  : JSON.stringify(multimediaResult.content, null, 2)
              )}
              className="flex items-center gap-2 px-3 py-1.5 bg-primary-500 text-white rounded-lg hover:bg-primary-600"
            >
              {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
              {copied ? t.copied[language] : t.copyToClipboard[language]}
            </button>
          </div>
          <div className="p-4 max-h-96 overflow-y-auto">
            {typeof multimediaResult.content === 'string' ? (
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <ReactMarkdown>{multimediaResult.content}</ReactMarkdown>
              </div>
            ) : (
              <pre className="bg-muted/50 p-4 rounded-xl overflow-x-auto text-sm font-mono whitespace-pre-wrap">
                {JSON.stringify(multimediaResult.content, null, 2)}
              </pre>
            )}
          </div>
        </div>
      )}
    </div>
  );

  // ==================== PREMIUM FEATURES - SMART LINKING ====================
  const handleAnalyzeContent = async (type: string) => {
    if (!linkingTopic.trim()) return;
    
    setLinkingLoading(true);
    setLinkingResult(null);
    
    try {
      const endpoint = `/api/learning/linking/${type}`;
      let body: Record<string, unknown> = {};
      
      if (type === 'learning-path') {
        // LearningPathRequest format
        body = {
          target_topic: linkingTopic,
          current_knowledge: linkingCurrentKnowledge.split(',').map(s => s.trim()).filter(s => s),
          max_steps: 10
        };
      } else if (type === 'next-topics') {
        // NextTopicsRequest format
        body = {
          completed_topics: linkingCurrentKnowledge.split(',').map(s => s.trim()).filter(s => s),
          interests: linkingTopic.split(',').map(s => s.trim()).filter(s => s)
        };
        // Ensure at least one completed topic
        if ((body.completed_topics as string[]).length === 0) {
          body.completed_topics = [linkingTopic];
        }
      } else {
        // VisualContentRequest format (prerequisites, related)
        body = {
          topic: linkingTopic,
          content: linkingContent.trim() || `${linkingTopic} - ${language === 'tr' ? 'Bu konu hakkında analiz yap' : 'Analyze this topic'}`
        };
      }
      
      const response = await apiPost(endpoint, body);
      
      if (!response.error && response.success) {
        setLinkingResult({
          type,
          data: response.prerequisites || response.related || response.path || response.next_topics || response.steps || response
        });
      }
    } catch (err) {
      console.error('Linking analysis error:', err);
    }
    
    setLinkingLoading(false);
  };

  const renderLinkingTab = () => (
    <div className="space-y-6">
      {/* Premium Badge */}
      <div className="bg-gradient-to-r from-cyan-500/10 to-teal-500/10 border border-cyan-300 dark:border-cyan-700 rounded-2xl p-4 flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-teal-600 flex items-center justify-center">
          <Link2 className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="font-semibold text-cyan-700 dark:text-cyan-300">🔗 {t.linking[language]} - Premium</h3>
          <p className="text-sm text-muted-foreground">
            {language === 'tr' ? 'Konular arası bağlantıları ve öğrenme yollarını keşfedin' : 'Discover connections between topics and learning paths'}
          </p>
        </div>
      </div>

      {/* Input Section */}
      <div className="bg-card border border-border rounded-2xl p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">📌 {t.topic[language]} / {language === 'tr' ? 'Hedef' : 'Target'}</label>
          <input
            type="text"
            value={linkingTopic}
            onChange={(e) => setLinkingTopic(e.target.value)}
            placeholder={language === 'tr' ? 'Örn: Deep Learning, Kubernetes, Data Science...' : 'E.g., Deep Learning, Kubernetes, Data Science...'}
            className="w-full px-4 py-3 bg-background border border-border rounded-xl"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium mb-2">📝 {t.content[language]} ({language === 'tr' ? 'İsteğe bağlı - Prerequisites/Related için' : 'Optional - for Prerequisites/Related'})</label>
          <textarea
            value={linkingContent}
            onChange={(e) => setLinkingContent(e.target.value)}
            placeholder={language === 'tr' ? 'Analiz edilecek içerik veya konu açıklaması...' : 'Content or topic description to analyze...'}
            rows={4}
            className="w-full px-4 py-3 bg-background border border-border rounded-xl resize-none"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium mb-2">📚 {language === 'tr' ? 'Mevcut Bilgiler' : 'Current Knowledge'} ({language === 'tr' ? 'virgülle ayırın' : 'comma separated'})</label>
          <input
            type="text"
            value={linkingCurrentKnowledge}
            onChange={(e) => setLinkingCurrentKnowledge(e.target.value)}
            placeholder={language === 'tr' ? 'Örn: Python, Math, Statistics...' : 'E.g., Python, Math, Statistics...'}
            className="w-full px-4 py-3 bg-background border border-border rounded-xl"
          />
          <p className="text-xs text-muted-foreground mt-1">
            {language === 'tr' ? 'Öğrenme yolu ve sonraki konular için mevcut bilgilerinizi girin' : 'Enter your current knowledge for learning path and next topics'}
          </p>
        </div>
      </div>

      {/* Linking Type Buttons */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { id: 'prerequisites', label: t.prerequisites, icon: ArrowLeft, emoji: '⬅️', color: 'from-amber-500 to-orange-500', desc: language === 'tr' ? 'Önceden bilinmesi gerekenler' : 'What you need to know first' },
          { id: 'related', label: t.relatedContent, icon: Share2, emoji: '🔄', color: 'from-blue-500 to-cyan-500', desc: language === 'tr' ? 'İlgili konular' : 'Related topics' },
          { id: 'learning-path', label: t.learningPath, icon: Route, emoji: '🛤️', color: 'from-green-500 to-emerald-500', desc: language === 'tr' ? 'Adım adım öğrenme yolu' : 'Step by step learning path' },
          { id: 'next-topics', label: t.nextTopics, icon: ChevronRight, emoji: '➡️', color: 'from-purple-500 to-violet-500', desc: language === 'tr' ? 'Sonra ne öğrenilmeli' : 'What to learn next' },
        ].map((item) => {
          const Icon = item.icon;
          const needsContent = ['prerequisites', 'related'].includes(item.id);
          // const needsKnowledge = ['learning-path', 'next-topics'].includes(item.id);
          const isDisabled = !linkingTopic.trim() || 
            (needsContent && linkingContent.length < 10) ||
            linkingLoading;
          
          return (
            <button
              key={item.id}
              onClick={() => handleAnalyzeContent(item.id)}
              disabled={isDisabled}
              className={cn(
                "flex flex-col items-center p-4 rounded-2xl border-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed",
                "hover:scale-105 hover:shadow-lg",
                `bg-gradient-to-br ${item.color} text-white border-transparent`
              )}
            >
              <Icon className="w-6 h-6 mb-2" />
              <span className="text-sm font-medium">{item.emoji} {item.label[language]}</span>
              <span className="text-xs opacity-80 mt-1">{item.desc}</span>
            </button>
          );
        })}
      </div>
      
      {/* Info Box */}
      <div className="bg-muted/50 border border-border rounded-xl p-4">
        <p className="text-sm text-muted-foreground">
          💡 <strong>{language === 'tr' ? 'İpucu:' : 'Tip:'}</strong> {language === 'tr' 
            ? 'Prerequisites ve Related için içerik alanını doldurun. Learning Path ve Next Topics için mevcut bilgilerinizi girin.'
            : 'Fill in the content field for Prerequisites and Related. Enter your current knowledge for Learning Path and Next Topics.'}
        </p>
      </div>

      {/* Loading State */}
      {linkingLoading && (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <Loader2 className="w-12 h-12 animate-spin text-cyan-500 mx-auto mb-4" />
            <p className="text-muted-foreground">{language === 'tr' ? 'Analiz ediliyor...' : 'Analyzing...'}</p>
          </div>
        </div>
      )}

      {/* Result */}
      {linkingResult && (
        <div className="bg-card border border-border rounded-2xl overflow-hidden">
          <div className="flex items-center justify-between p-4 border-b border-border bg-muted/50">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-green-500" />
              <span className="font-medium">
                {linkingResult.type === 'prerequisites' && t.prerequisites[language]}
                {linkingResult.type === 'related' && t.relatedContent[language]}
                {linkingResult.type === 'learning-path' && t.learningPath[language]}
                {linkingResult.type === 'next-topics' && t.nextTopics[language]}
              </span>
            </div>
            <button
              onClick={() => handleCopyToClipboard(JSON.stringify(linkingResult.data, null, 2))}
              className="flex items-center gap-2 px-3 py-1.5 bg-primary-500 text-white rounded-lg hover:bg-primary-600"
            >
              {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
              {copied ? t.copied[language] : t.copyToClipboard[language]}
            </button>
          </div>
          <div className="p-4">
            {Array.isArray(linkingResult.data) ? (
              <div className="space-y-2">
                {(linkingResult.data as Array<{topic?: string; name?: string; title?: string; description?: string; order?: number; step?: number; reason?: string; importance?: string}>).map((item, idx) => (
                  <div key={idx} className="flex items-start gap-3 p-3 bg-muted/50 rounded-xl">
                    <span className="flex items-center justify-center w-6 h-6 rounded-full bg-primary-500 text-white text-xs font-bold shrink-0">
                      {item.order || item.step || idx + 1}
                    </span>
                    <div className="flex-1">
                      <p className="font-medium">{item.topic || item.name || item.title || String(item)}</p>
                      {item.description && <p className="text-sm text-muted-foreground mt-1">{item.description}</p>}
                      {item.reason && <p className="text-sm text-blue-600 dark:text-blue-400 mt-1">💡 {item.reason}</p>}
                      {item.importance && <p className="text-xs text-orange-600 dark:text-orange-400 mt-1">⭐ {item.importance}</p>}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <pre className="bg-muted/50 p-4 rounded-xl overflow-x-auto text-sm font-mono whitespace-pre-wrap">
                {JSON.stringify(linkingResult.data, null, 2)}
              </pre>
            )}
          </div>
        </div>
      )}
    </div>
  );

  // ==================== QUALITY HUB TAB ====================
  const renderQualityTab = () => {
    // Dynamically import FullMetaQualityDashboard
    const QualityDashboard = lazy(() => import('@/components/premium/FullMetaQualityDashboard'));
    
    return (
      <div className="space-y-6">
        {/* Premium Badge */}
        <div className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 border border-purple-300 dark:border-purple-700 rounded-2xl p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-purple-700 dark:text-purple-300">⚡ {t.quality[language]} - Premium</h3>
            <p className="text-sm text-muted-foreground">
              {language === 'tr' ? '2026 nesil öğrenme optimizasyonu - Dikkat, mikro-öğrenme, momentum takibi' : '2026 generation learning optimization - Attention, micro-learning, momentum tracking'}
            </p>
          </div>
        </div>

        {/* Quality Dashboard */}
        <div className="bg-card border border-border rounded-2xl overflow-hidden" style={{ height: '600px' }}>
          <Suspense fallback={
            <div className="flex items-center justify-center h-full">
              <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
            </div>
          }>
            <QualityDashboard />
          </Suspense>
        </div>
      </div>
    );
  };

  // ==================== FULL META TAB ====================
  const renderFullMetaTab = () => {
    // Dynamically import FullMetaPanel and FullMetaPremiumFeatures
    const FullMetaPanel = lazy(() => import('@/components/premium/FullMetaPanel'));
    const FullMetaPremiumFeatures = lazy(() => import('@/components/premium/FullMetaPremiumFeatures'));
    
    return (
      <div className="space-y-6">
        {/* Premium Badge */}
        <div className="bg-gradient-to-r from-indigo-500/10 to-purple-500/10 border border-indigo-300 dark:border-indigo-700 rounded-2xl p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-indigo-700 dark:text-indigo-300">🧠 {t.fullmeta[language]} - Neuro-Adaptive Mastery</h3>
            <p className="text-sm text-muted-foreground">
              {language === 'tr' ? '12 katmanlı öğrenme motoru - Nörobilim, gamifikasyon, adaptif sistemler' : '12-layer learning engine - Neuroscience, gamification, adaptive systems'}
            </p>
          </div>
        </div>

        {/* Full Meta Panels */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Main Panel */}
          <div className="bg-card border border-border rounded-2xl overflow-hidden" style={{ minHeight: '500px' }}>
            <Suspense fallback={
              <div className="flex items-center justify-center h-full">
                <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
              </div>
            }>
              <FullMetaPanel />
            </Suspense>
          </div>
          
          {/* Premium Features */}
          <div className="bg-card border border-border rounded-2xl overflow-hidden" style={{ minHeight: '500px' }}>
            <Suspense fallback={
              <div className="flex items-center justify-center h-full">
                <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
              </div>
            }>
              <FullMetaPremiumFeatures />
            </Suspense>
          </div>
        </div>
      </div>
    );
  };

  // ==================== LEARNING JOURNEY TAB ====================
  const renderJourneyTab = () => {
    const StageMapView = lazy(() => import('@/components/premium/StageMapView'));
    const StageContentView = lazy(() => import('@/components/premium/StageContentView'));
    
    return (
      <div className="space-y-6">
        {/* Premium Badge */}
        <div className="bg-gradient-to-r from-pink-500/10 to-orange-500/10 border border-pink-300 dark:border-pink-700 rounded-2xl p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-pink-500 to-orange-600 flex items-center justify-center">
            <Rocket className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-pink-700 dark:text-pink-300">🎮 {t.journey[language]} - Candy Crush Style Learning</h3>
            <p className="text-sm text-muted-foreground">
              {language === 'tr' ? 'Görsel stage haritasıyla eğlenceli öğrenme deneyimi' : 'Fun learning experience with visual stage map'}
            </p>
          </div>
        </div>

        {/* Stage Map */}
        <div className="bg-card border border-border rounded-2xl overflow-hidden" style={{ minHeight: '600px' }}>
          <Suspense fallback={
            <div className="flex items-center justify-center h-full min-h-[600px]">
              <Loader2 className="w-8 h-8 animate-spin text-pink-500" />
            </div>
          }>
            <StageMapView
              userId="user_123"
              language={language}
              onStageClick={(stageId) => {
                console.log('Stage clicked:', stageId);
              }}
              onContentStart={(stageId, contentId) => {
                console.log('Content started:', stageId, contentId);
              }}
            />
          </Suspense>
        </div>
      </div>
    );
  };

  // ==================== PREMIUM DATA LOADING ====================
  
  const loadAnalytics = async () => {
    if (!currentWorkspaceId) return;
    setAnalyticsLoading(true);
    try {
      const [statsRes, weeklyRes, insightsRes, weakRes] = await Promise.all([
        apiGet(`/api/learning/workspaces/${currentWorkspaceId}/analytics/stats`),
        apiGet(`/api/learning/workspaces/${currentWorkspaceId}/analytics/weekly`),
        apiGet(`/api/learning/workspaces/${currentWorkspaceId}/analytics/insights`),
        apiGet(`/api/learning/workspaces/${currentWorkspaceId}/analytics/weak-areas`)
      ]);
      
      if (statsRes.stats) setAnalyticsData(statsRes.stats);
      if (weeklyRes.weekly_activity) setWeeklyActivity(weeklyRes.weekly_activity);
      if (insightsRes.insights) setLearningInsights(insightsRes.insights);
      if (weakRes.weak_areas) setWeakAreas(weakRes.weak_areas);
    } catch (error) {
      console.error('Analytics load error:', error);
    }
    setAnalyticsLoading(false);
  };

  const loadFlashcards = async () => {
    if (!currentWorkspaceId) return;
    setFlashcardLoading(true);
    try {
      const [cardsRes, dueRes, statsRes] = await Promise.all([
        apiGet(`/api/learning/workspaces/${currentWorkspaceId}/flashcards`),
        apiGet(`/api/learning/workspaces/${currentWorkspaceId}/flashcards/due`),
        apiGet(`/api/learning/workspaces/${currentWorkspaceId}/flashcards/stats`)
      ]);
      
      if (cardsRes.cards) setFlashcards(cardsRes.cards);
      if (dueRes.cards) setDueCards(dueRes.cards);
      if (statsRes.stats) setFlashcardStats(statsRes.stats);
    } catch (error) {
      console.error('Flashcards load error:', error);
    }
    setFlashcardLoading(false);
  };

  const loadSimulations = async () => {
    if (!currentWorkspaceId) return;
    setScenarioLoading(true);
    try {
      const [typesRes, scenariosRes] = await Promise.all([
        apiGet('/api/learning/simulations/types'),
        apiGet(`/api/learning/workspaces/${currentWorkspaceId}/simulations`)
      ]);
      
      if (typesRes.scenario_types) setScenarioTypes(typesRes.scenario_types);
      if (scenariosRes.scenarios) setScenarios(scenariosRes.scenarios);
    } catch (error) {
      console.error('Simulations load error:', error);
    }
    setScenarioLoading(false);
  };

  // ==================== AI TUTOR TAB ====================
  const renderTutorTab = () => (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="font-semibold flex items-center gap-2">
          <Bot className="w-5 h-5" />
          🤖 {t.tutor[language]}
        </h3>
        {tutorSessionId && (
          <button
            onClick={async () => {
              await apiPost(`/api/learning/tutor/${tutorSessionId}/end`);
              setTutorSessionId(null);
              setTutorMessages([]);
              setTutorSession(null);
            }}
            className="flex items-center gap-2 px-3 py-1.5 bg-red-500 text-white rounded-lg hover:bg-red-600"
          >
            <X className="w-4 h-4" />
            {t.endSession[language]}
          </button>
        )}
      </div>

      {!tutorSessionId ? (
        // Start Session Form
        <div className="bg-gradient-to-br from-violet-500/10 to-purple-500/10 border border-violet-300 dark:border-violet-700 rounded-2xl p-6 space-y-4">
          <div className="flex items-center gap-3 text-lg font-semibold">
            <Bot className="w-6 h-6 text-violet-500" />
            <span>{language === 'tr' ? 'AI Öğretmen ile Oturum Başlat' : 'Start Session with AI Tutor'}</span>
          </div>
          
          <input
            type="text"
            value={tutorTopic}
            onChange={(e) => setTutorTopic(e.target.value)}
            placeholder={language === 'tr' ? 'Öğrenmek istediğiniz konu...' : 'Topic you want to learn...'}
            className="w-full px-4 py-3 rounded-xl border border-border bg-card"
          />
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {[
              { id: 'adaptive', icon: '🎯', label: t.adaptive },
              { id: 'socratic', icon: '🤔', label: t.socratic },
              { id: 'explain', icon: '📖', label: t.explanatory },
              { id: 'quiz', icon: '❓', label: { tr: 'Quiz', en: 'Quiz', de: 'Quiz' } }
            ].map(mode => (
              <button
                key={mode.id}
                onClick={() => setTutorMode(mode.id)}
                className={cn(
                  "p-3 rounded-xl border transition-all",
                  tutorMode === mode.id
                    ? "bg-violet-500 text-white border-violet-500"
                    : "bg-card hover:bg-accent border-border"
                )}
              >
                <span className="text-lg">{mode.icon}</span>
                <span className="ml-2 text-sm">{mode.label[language]}</span>
              </button>
            ))}
          </div>
          
          <button
            onClick={async () => {
              if (!tutorTopic.trim() || !currentWorkspaceId) return;
              setTutorLoading(true);
              const res = await apiPost(`/api/learning/workspaces/${currentWorkspaceId}/tutor/session`, {
                topic: tutorTopic,
                mode: tutorMode
              });
              if (res.session) {
                setTutorSessionId(res.session.id);
                setTutorMessages(res.session.messages || []);
                setTutorSession(res.session);
              }
              setTutorLoading(false);
            }}
            disabled={!tutorTopic.trim() || tutorLoading}
            className="w-full py-3 bg-violet-500 text-white rounded-xl hover:bg-violet-600 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {tutorLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Play className="w-5 h-5" />}
            {t.startTutorSession[language]}
          </button>
        </div>
      ) : (
        // Active Session
        <div className="space-y-4">
          {/* Session Stats */}
          {tutorSession && (
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-blue-500/10 rounded-xl p-4 text-center">
                <div className="text-2xl font-bold text-blue-600">{tutorSession.questions_asked}</div>
                <div className="text-sm text-muted-foreground">{t.questionsAsked[language]}</div>
              </div>
              <div className="bg-green-500/10 rounded-xl p-4 text-center">
                <div className="text-2xl font-bold text-green-600">{tutorSession.correct_answers}</div>
                <div className="text-sm text-muted-foreground">{t.correctAnswers[language]}</div>
              </div>
              <div className="bg-purple-500/10 rounded-xl p-4 text-center">
                <div className="text-2xl font-bold text-purple-600">{tutorSession.accuracy}%</div>
                <div className="text-sm text-muted-foreground">{language === 'tr' ? 'Başarı' : 'Accuracy'}</div>
              </div>
            </div>
          )}
          
          {/* Messages */}
          <div className="h-96 overflow-y-auto space-y-4 p-4 bg-muted/30 rounded-xl">
            {tutorMessages.map((msg, idx) => (
              <div key={idx} className={cn("flex", msg.role === 'student' ? "justify-end" : "justify-start")}>
                <div className={cn(
                  "max-w-[80%] rounded-2xl px-4 py-3",
                  msg.role === 'student'
                    ? "bg-primary-500 text-white"
                    : "bg-card border border-border"
                )}>
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>
              </div>
            ))}
          </div>
          
          {/* Input */}
          <div className="flex gap-2">
            <input
              type="text"
              value={tutorInput}
              onChange={(e) => setTutorInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && !tutorLoading && sendTutorMessage()}
              placeholder={language === 'tr' ? 'Mesajınızı yazın...' : 'Type your message...'}
              className="flex-1 px-4 py-3 rounded-xl border border-border bg-card"
            />
            <button
              onClick={sendTutorMessage}
              disabled={!tutorInput.trim() || tutorLoading}
              className="px-6 py-3 bg-violet-500 text-white rounded-xl hover:bg-violet-600 disabled:opacity-50"
            >
              {tutorLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
            </button>
          </div>
        </div>
      )}
    </div>
  );

  const sendTutorMessage = async () => {
    if (!tutorInput.trim() || !tutorSessionId) return;
    const message = tutorInput;
    setTutorInput('');
    setTutorLoading(true);
    
    // Add user message immediately
    setTutorMessages(prev => [...prev, { role: 'student', content: message }]);
    
    const res = await apiPost(`/api/learning/tutor/${tutorSessionId}/message`, { message });
    
    if (res.message) {
      setTutorMessages(prev => [...prev, { role: 'tutor', content: res.message }]);
      if (res.metadata) {
        setTutorSession(prev => prev ? { ...prev, ...res.metadata } : null);
      }
    }
    setTutorLoading(false);
  };

  // ==================== FLASHCARDS TAB ====================
  const renderFlashcardsTab = () => (
    <div className="space-y-6">
      {/* Header & Stats */}
      <div className="flex items-center justify-between">
        <h3 className="font-semibold flex items-center gap-2">
          <Repeat className="w-5 h-5" />
          📚 {t.flashcards[language]}
        </h3>
        <button
          onClick={loadFlashcards}
          disabled={flashcardLoading}
          className="flex items-center gap-2 px-3 py-1.5 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50"
        >
          {flashcardLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
        </button>
      </div>

      {/* Stats Grid */}
      {flashcardStats && (
        <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
          <div className="bg-blue-500/10 rounded-xl p-3 text-center">
            <div className="text-xl font-bold">{flashcardStats.total}</div>
            <div className="text-xs text-muted-foreground">{language === 'tr' ? 'Toplam' : 'Total'}</div>
          </div>
          <div className="bg-green-500/10 rounded-xl p-3 text-center">
            <div className="text-xl font-bold">{flashcardStats.new}</div>
            <div className="text-xs text-muted-foreground">{t.newCards[language]}</div>
          </div>
          <div className="bg-yellow-500/10 rounded-xl p-3 text-center">
            <div className="text-xl font-bold">{flashcardStats.learning}</div>
            <div className="text-xs text-muted-foreground">{t.learningCards[language]}</div>
          </div>
          <div className="bg-orange-500/10 rounded-xl p-3 text-center">
            <div className="text-xl font-bold">{flashcardStats.due_today}</div>
            <div className="text-xs text-muted-foreground">{t.dueToday[language]}</div>
          </div>
          <div className="bg-purple-500/10 rounded-xl p-3 text-center">
            <div className="text-xl font-bold">{flashcardStats.graduated}</div>
            <div className="text-xs text-muted-foreground">{t.graduated[language]}</div>
          </div>
          <div className="bg-emerald-500/10 rounded-xl p-3 text-center">
            <div className="text-xl font-bold">{flashcardStats.retention_rate}%</div>
            <div className="text-xs text-muted-foreground">{t.retentionRate[language]}</div>
          </div>
        </div>
      )}

      {/* Review Mode */}
      {reviewingCard ? (
        <div className="bg-gradient-to-br from-amber-500/10 to-orange-500/10 border border-amber-300 dark:border-amber-700 rounded-2xl p-6 space-y-6">
          <div className="text-center">
            <div className="text-sm text-muted-foreground mb-4">{language === 'tr' ? 'Kart' : 'Card'} {dueCards.findIndex(c => c.id === reviewingCard.id) + 1}/{dueCards.length}</div>
            
            {/* Front */}
            <div className="bg-card rounded-xl p-6 mb-4 min-h-32 flex items-center justify-center">
              <p className="text-lg font-medium">{reviewingCard.front}</p>
            </div>
            
            {/* Back (conditionally shown) */}
            {showCardBack ? (
              <>
                <div className="bg-green-500/10 rounded-xl p-6 min-h-32 flex items-center justify-center mb-4">
                  <p className="text-lg">{reviewingCard.back}</p>
                </div>
                
                {/* Rating Buttons */}
                <div className="grid grid-cols-4 gap-2">
                  {[
                    { rating: 0, label: t.again, color: 'bg-red-500', icon: <RotateCcw className="w-4 h-4" /> },
                    { rating: 1, label: t.hard, color: 'bg-orange-500', icon: <ThumbsDown className="w-4 h-4" /> },
                    { rating: 2, label: t.good, color: 'bg-green-500', icon: <ThumbsUp className="w-4 h-4" /> },
                    { rating: 3, label: t.easy, color: 'bg-blue-500', icon: <Star className="w-4 h-4" /> }
                  ].map(btn => (
                    <button
                      key={btn.rating}
                      onClick={async () => {
                        await apiPost(`/api/learning/flashcards/${reviewingCard.id}/review`, { rating: btn.rating });
                        const nextIndex = dueCards.findIndex(c => c.id === reviewingCard.id) + 1;
                        if (nextIndex < dueCards.length) {
                          setReviewingCard(dueCards[nextIndex]);
                          setShowCardBack(false);
                        } else {
                          setReviewingCard(null);
                          loadFlashcards();
                        }
                      }}
                      className={cn("flex items-center justify-center gap-2 py-3 text-white rounded-xl", btn.color)}
                    >
                      {btn.icon}
                      {btn.label[language]}
                    </button>
                  ))}
                </div>
              </>
            ) : (
              <button
                onClick={() => setShowCardBack(true)}
                className="w-full py-4 bg-amber-500 text-white rounded-xl hover:bg-amber-600 flex items-center justify-center gap-2"
              >
                <Eye className="w-5 h-5" />
                {t.showAnswer[language]}
              </button>
            )}
          </div>
        </div>
      ) : (
        <>
          {/* Start Review Button */}
          {dueCards.length > 0 && (
            <button
              onClick={() => {
                setReviewingCard(dueCards[0]);
                setShowCardBack(false);
              }}
              className="w-full py-4 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-xl hover:from-amber-600 hover:to-orange-600 flex items-center justify-center gap-2"
            >
              <Play className="w-5 h-5" />
              {t.startReview[language]} ({dueCards.length} {language === 'tr' ? 'kart' : 'cards'})
            </button>
          )}

          {/* Create Card Form */}
          <div className="bg-card rounded-2xl p-4 border border-border space-y-3">
            <h4 className="font-medium">{t.createCard[language]}</h4>
            <input
              type="text"
              value={flashcardFront}
              onChange={(e) => setFlashcardFront(e.target.value)}
              placeholder={language === 'tr' ? 'Ön yüz (soru)...' : 'Front (question)...'}
              className="w-full px-4 py-2 rounded-lg border border-border bg-background"
            />
            <input
              type="text"
              value={flashcardBack}
              onChange={(e) => setFlashcardBack(e.target.value)}
              placeholder={language === 'tr' ? 'Arka yüz (cevap)...' : 'Back (answer)...'}
              className="w-full px-4 py-2 rounded-lg border border-border bg-background"
            />
            <button
              onClick={async () => {
                if (!flashcardFront.trim() || !flashcardBack.trim() || !currentWorkspaceId) return;
                await apiPost(`/api/learning/workspaces/${currentWorkspaceId}/flashcards`, {
                  front: flashcardFront,
                  back: flashcardBack
                });
                setFlashcardFront('');
                setFlashcardBack('');
                loadFlashcards();
              }}
              disabled={!flashcardFront.trim() || !flashcardBack.trim()}
              className="w-full py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50"
            >
              <Plus className="w-4 h-4 inline mr-2" />
              {t.createCard[language]}
            </button>
          </div>

          {/* Auto Generate */}
          <div className="bg-card rounded-2xl p-4 border border-border space-y-3">
            <h4 className="font-medium">{t.generateCards[language]}</h4>
            <textarea
              value={flashcardContent}
              onChange={(e) => setFlashcardContent(e.target.value)}
              placeholder={language === 'tr' ? 'İçerik yapıştırın, otomatik kartlar oluşturulsun...' : 'Paste content to auto-generate cards...'}
              className="w-full px-4 py-3 rounded-lg border border-border bg-background h-32"
            />
            <button
              onClick={async () => {
                if (!flashcardContent.trim() || !currentWorkspaceId) return;
                setFlashcardLoading(true);
                await apiPost(`/api/learning/workspaces/${currentWorkspaceId}/flashcards/generate`, {
                  content: flashcardContent
                });
                setFlashcardContent('');
                loadFlashcards();
              }}
              disabled={!flashcardContent.trim() || flashcardLoading}
              className="w-full py-2 bg-violet-500 text-white rounded-lg hover:bg-violet-600 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {flashcardLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
              {t.generateCards[language]}
            </button>
          </div>
        </>
      )}
    </div>
  );

  // ==================== SIMULATIONS TAB ====================
  const renderSimulationsTab = () => (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="font-semibold flex items-center gap-2">
          <Theater className="w-5 h-5" />
          🎭 {t.simulations[language]}
        </h3>
      </div>

      {activeScenario ? (
        // Active Scenario
        <div className="space-y-4">
          <div className="bg-gradient-to-br from-pink-500/10 to-rose-500/10 border border-pink-300 dark:border-pink-700 rounded-2xl p-4">
            <div className="flex items-center justify-between mb-2">
              <h4 className="font-semibold">{activeScenario.title}</h4>
              <span className={cn("px-2 py-1 rounded-full text-xs", 
                activeScenario.status === 'completed' ? "bg-green-500/20 text-green-600" : "bg-blue-500/20 text-blue-600"
              )}>
                {activeScenario.status}
              </span>
            </div>
            <p className="text-sm text-muted-foreground mb-3">{activeScenario.description}</p>
            <div className="flex flex-wrap gap-2">
              {activeScenario.objectives.map((obj, idx) => (
                <span key={idx} className="px-2 py-1 bg-muted rounded-full text-xs">{obj}</span>
              ))}
            </div>
          </div>

          {/* Conversation */}
          <div className="h-80 overflow-y-auto space-y-3 p-4 bg-muted/30 rounded-xl">
            {activeScenario.conversation.map((msg, idx) => (
              <div key={idx} className={cn("flex", msg.role === 'user' ? "justify-end" : "justify-start")}>
                <div className={cn(
                  "max-w-[80%] rounded-2xl px-4 py-3",
                  msg.role === 'user' ? "bg-primary-500 text-white" : "bg-card border border-border"
                )}>
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>
              </div>
            ))}
          </div>

          {activeScenario.status === 'active' ? (
            <div className="flex gap-2">
              <input
                type="text"
                value={scenarioInput}
                onChange={(e) => setScenarioInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && !scenarioLoading && sendScenarioMessage()}
                placeholder={language === 'tr' ? 'Yanıtınızı yazın...' : 'Type your response...'}
                className="flex-1 px-4 py-3 rounded-xl border border-border bg-card"
              />
              <button
                onClick={sendScenarioMessage}
                disabled={!scenarioInput.trim() || scenarioLoading}
                className="px-6 py-3 bg-pink-500 text-white rounded-xl hover:bg-pink-600 disabled:opacity-50"
              >
                {scenarioLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
              </button>
            </div>
          ) : activeScenario.evaluation && (
            <div className="bg-green-500/10 rounded-xl p-4">
              <h4 className="font-semibold mb-2">{language === 'tr' ? 'Değerlendirme' : 'Evaluation'}</h4>
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-600">{activeScenario.evaluation.overall_score as number}</div>
                  <div className="text-sm text-muted-foreground">{language === 'tr' ? 'Puan' : 'Score'}</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold">{activeScenario.evaluation.grade as string}</div>
                  <div className="text-sm text-muted-foreground">{language === 'tr' ? 'Not' : 'Grade'}</div>
                </div>
              </div>
              <button
                onClick={() => setActiveScenario(null)}
                className="w-full mt-4 py-2 bg-muted rounded-lg hover:bg-accent"
              >
                {language === 'tr' ? 'Kapat' : 'Close'}
              </button>
            </div>
          )}
        </div>
      ) : (
        <>
          {/* Create Scenario */}
          <div className="bg-gradient-to-br from-pink-500/10 to-rose-500/10 border border-pink-300 dark:border-pink-700 rounded-2xl p-6 space-y-4">
            <h4 className="font-semibold">{t.startSimulation[language]}</h4>
            
            <input
              type="text"
              value={scenarioTopic}
              onChange={(e) => setScenarioTopic(e.target.value)}
              placeholder={language === 'tr' ? 'Senaryo konusu...' : 'Scenario topic...'}
              className="w-full px-4 py-3 rounded-xl border border-border bg-card"
            />
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {[
                { id: 'interview', icon: '👔', label: t.interview },
                { id: 'presentation', icon: '🎤', label: t.presentation },
                { id: 'problem_solving', icon: '🧩', label: t.problemSolving },
                { id: 'debate', icon: '⚔️', label: t.debate }
              ].map(type => (
                <button
                  key={type.id}
                  onClick={() => setScenarioType(type.id)}
                  className={cn(
                    "p-3 rounded-xl border transition-all text-center",
                    scenarioType === type.id
                      ? "bg-pink-500 text-white border-pink-500"
                      : "bg-card hover:bg-accent border-border"
                  )}
                >
                  <span className="text-xl block">{type.icon}</span>
                  <span className="text-xs">{type.label[language]}</span>
                </button>
              ))}
            </div>

            <div className="grid grid-cols-3 gap-2">
              {['easy', 'medium', 'hard'].map(diff => (
                <button
                  key={diff}
                  onClick={() => setScenarioDifficulty(diff)}
                  className={cn(
                    "py-2 rounded-lg border transition-all",
                    scenarioDifficulty === diff
                      ? "bg-pink-500 text-white border-pink-500"
                      : "bg-card hover:bg-accent border-border"
                  )}
                >
                  {diff === 'easy' ? '🟢' : diff === 'medium' ? '🟡' : '🔴'} {diff}
                </button>
              ))}
            </div>
            
            <button
              onClick={async () => {
                if (!scenarioTopic.trim() || !currentWorkspaceId) return;
                setScenarioLoading(true);
                const res = await apiPost(`/api/learning/workspaces/${currentWorkspaceId}/simulations`, {
                  scenario_type: scenarioType,
                  topic: scenarioTopic,
                  difficulty: scenarioDifficulty
                });
                if (res.scenario) {
                  setActiveScenario(res.scenario);
                }
                setScenarioLoading(false);
              }}
              disabled={!scenarioTopic.trim() || scenarioLoading}
              className="w-full py-3 bg-pink-500 text-white rounded-xl hover:bg-pink-600 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {scenarioLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Play className="w-5 h-5" />}
              {t.startSimulation[language]}
            </button>
          </div>

          {/* Previous Scenarios */}
          {scenarios.length > 0 && (
            <div className="space-y-2">
              <h4 className="font-medium">{language === 'tr' ? 'Önceki Senaryolar' : 'Previous Scenarios'}</h4>
              {scenarios.map(scenario => (
                <button
                  key={scenario.id}
                  onClick={async () => {
                    const res = await apiGet(`/api/learning/simulations/${scenario.id}`);
                    if (res.scenario) setActiveScenario(res.scenario);
                  }}
                  className="w-full p-4 bg-card rounded-xl border border-border hover:bg-accent text-left"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{scenario.title}</span>
                    <span className={cn("px-2 py-1 rounded-full text-xs",
                      scenario.status === 'completed' ? "bg-green-500/20 text-green-600" : "bg-blue-500/20 text-blue-600"
                    )}>
                      {scenario.evaluation ? `${scenario.evaluation.overall_score} - ${scenario.evaluation.grade}` : scenario.status}
                    </span>
                  </div>
                  <div className="text-sm text-muted-foreground mt-1">
                    {scenario.scenario_type} • {scenario.difficulty} • {scenario.turn_count} {language === 'tr' ? 'tur' : 'turns'}
                  </div>
                </button>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );

  const sendScenarioMessage = async () => {
    if (!scenarioInput.trim() || !activeScenario) return;
    const message = scenarioInput;
    setScenarioInput('');
    setScenarioLoading(true);
    
    const res = await apiPost(`/api/learning/simulations/${activeScenario.id}/interact`, { message });
    
    if (res.response) {
      const updatedScenario = await apiGet(`/api/learning/simulations/${activeScenario.id}`);
      if (updatedScenario.scenario) {
        setActiveScenario(updatedScenario.scenario);
      }
    }
    setScenarioLoading(false);
  };

  // ==================== ANALYTICS TAB ====================
  const renderAnalyticsTab = () => (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="font-semibold flex items-center gap-2">
          <PieChart className="w-5 h-5" />
          📊 {t.analytics[language]}
        </h3>
        <button
          onClick={loadAnalytics}
          disabled={analyticsLoading}
          className="flex items-center gap-2 px-3 py-1.5 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50"
        >
          {analyticsLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
        </button>
      </div>

      {analyticsLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
        </div>
      ) : analyticsData ? (
        <>
          {/* Main Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gradient-to-br from-blue-500/10 to-cyan-500/10 border border-blue-300 dark:border-blue-700 rounded-2xl p-4 text-center">
              <Clock className="w-6 h-6 mx-auto mb-2 text-blue-500" />
              <div className="text-2xl font-bold">{analyticsData.total_study_time}</div>
              <div className="text-sm text-muted-foreground">{t.minutes[language]}</div>
            </div>
            <div className="bg-gradient-to-br from-orange-500/10 to-amber-500/10 border border-orange-300 dark:border-orange-700 rounded-2xl p-4 text-center">
              <Flame className="w-6 h-6 mx-auto mb-2 text-orange-500" />
              <div className="text-2xl font-bold">{analyticsData.streak_days}</div>
              <div className="text-sm text-muted-foreground">{t.streakDays[language]}</div>
            </div>
            <div className="bg-gradient-to-br from-green-500/10 to-emerald-500/10 border border-green-300 dark:border-green-700 rounded-2xl p-4 text-center">
              <Trophy className="w-6 h-6 mx-auto mb-2 text-green-500" />
              <div className="text-2xl font-bold">{analyticsData.average_score}%</div>
              <div className="text-sm text-muted-foreground">{t.averageScore[language]}</div>
            </div>
            <div className="bg-gradient-to-br from-purple-500/10 to-violet-500/10 border border-purple-300 dark:border-purple-700 rounded-2xl p-4 text-center">
              <TrendingUp className="w-6 h-6 mx-auto mb-2 text-purple-500" />
              <div className="text-2xl font-bold capitalize">{t[analyticsData.performance_trend as keyof typeof t]?.[language] || analyticsData.performance_trend}</div>
              <div className="text-sm text-muted-foreground">{t.performanceTrend[language]}</div>
            </div>
          </div>

          {/* Weekly Activity */}
          {weeklyActivity.length > 0 && (
            <div className="bg-card rounded-2xl p-4 border border-border">
              <h4 className="font-medium mb-4">{t.weeklyActivity[language]}</h4>
              <div className="flex items-end justify-between gap-2 h-32">
                {weeklyActivity.map((day, idx) => {
                  const maxMinutes = Math.max(...weeklyActivity.map(d => d.minutes), 1);
                  const height = (day.minutes / maxMinutes) * 100;
                  return (
                    <div key={idx} className="flex-1 flex flex-col items-center">
                      <div
                        className="w-full bg-primary-500 rounded-t-lg transition-all"
                        style={{ height: `${Math.max(height, 4)}%` }}
                      />
                      <div className="text-xs mt-2 text-muted-foreground">{day.day_name}</div>
                      <div className="text-xs font-medium">{day.minutes}m</div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Insights */}
          {learningInsights.length > 0 && (
            <div className="space-y-3">
              <h4 className="font-medium">{t.insights[language]}</h4>
              {learningInsights.map((insight, idx) => (
                <div key={idx} className={cn(
                  "rounded-xl p-4 border",
                  insight.insight_type === 'strength' ? "bg-green-500/10 border-green-300" :
                  insight.insight_type === 'weakness' ? "bg-red-500/10 border-red-300" :
                  insight.insight_type === 'milestone' ? "bg-purple-500/10 border-purple-300" :
                  "bg-blue-500/10 border-blue-300"
                )}>
                  <h5 className="font-medium">{insight.title}</h5>
                  <p className="text-sm text-muted-foreground mt-1">{insight.description}</p>
                  {insight.action_items.length > 0 && (
                    <ul className="mt-2 space-y-1">
                      {insight.action_items.map((item, i) => (
                        <li key={i} className="text-sm flex items-center gap-2">
                          <ChevronRight className="w-4 h-4" />
                          {item}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Weak Areas */}
          {weakAreas.length > 0 && (
            <div className="bg-red-500/10 rounded-2xl p-4 border border-red-300">
              <h4 className="font-medium mb-3">{t.weakAreas[language]}</h4>
              <div className="space-y-2">
                {weakAreas.map((area, idx) => (
                  <div key={idx} className="flex items-center justify-between bg-card rounded-lg p-3">
                    <span>{area.topic}</span>
                    <span className="text-red-600 font-medium">{area.average_score}%</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="text-center py-12 text-muted-foreground">
          {language === 'tr' ? 'Henüz analitik verisi yok' : 'No analytics data yet'}
        </div>
      )}
    </div>
  );

  // ==================== STATS TAB ====================
  const renderStatsTab = () => (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="font-semibold flex items-center gap-2">
          <BarChart3 className="w-5 h-5" />
          📊 {t.stats[language]}
        </h3>
        <button
          onClick={loadStats}
          disabled={statsLoading}
          className="flex items-center gap-2 px-3 py-1.5 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50"
        >
          {statsLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
          {language === 'tr' ? 'Yenile' : 'Refresh'}
        </button>
      </div>

      {statsLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
        </div>
      ) : stats ? (
        <>
          {/* Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="bg-gradient-to-br from-blue-500/10 to-cyan-500/10 border border-blue-300 dark:border-blue-700 rounded-2xl p-4 text-center">
              <FileText className="w-8 h-8 mx-auto text-blue-500 mb-2" />
              <p className="text-3xl font-bold text-blue-600 dark:text-blue-400">{stats.total_documents}</p>
              <p className="text-xs text-muted-foreground">📄 {t.totalDocuments[language]}</p>
            </div>
            
            <div className="bg-gradient-to-br from-green-500/10 to-emerald-500/10 border border-green-300 dark:border-green-700 rounded-2xl p-4 text-center">
              <CheckCircle2 className="w-8 h-8 mx-auto text-green-500 mb-2" />
              <p className="text-3xl font-bold text-green-600 dark:text-green-400">{stats.completed_documents}</p>
              <p className="text-xs text-muted-foreground">✅ {t.completedDocuments[language]}</p>
            </div>
            
            <div className="bg-gradient-to-br from-purple-500/10 to-violet-500/10 border border-purple-300 dark:border-purple-700 rounded-2xl p-4 text-center">
              <Target className="w-8 h-8 mx-auto text-purple-500 mb-2" />
              <p className="text-3xl font-bold text-purple-600 dark:text-purple-400">{stats.total_tests}</p>
              <p className="text-xs text-muted-foreground">📝 {t.totalTests[language]}</p>
            </div>
            
            <div className="bg-gradient-to-br from-orange-500/10 to-amber-500/10 border border-orange-300 dark:border-orange-700 rounded-2xl p-4 text-center">
              <Award className="w-8 h-8 mx-auto text-orange-500 mb-2" />
              <p className="text-3xl font-bold text-orange-600 dark:text-orange-400">{stats.completed_tests}</p>
              <p className="text-xs text-muted-foreground">🏆 {t.completedTests[language]}</p>
            </div>
            
            <div className="bg-gradient-to-br from-pink-500/10 to-rose-500/10 border border-pink-300 dark:border-pink-700 rounded-2xl p-4 text-center">
              <TrendingUp className="w-8 h-8 mx-auto text-pink-500 mb-2" />
              <p className="text-3xl font-bold text-pink-600 dark:text-pink-400">{(stats?.average_score ?? 0).toFixed(1)}%</p>
              <p className="text-xs text-muted-foreground">📈 {t.averageScore[language]}</p>
            </div>
          </div>

          {/* Progress Overview */}
          <div className="bg-card border border-border rounded-2xl p-6">
            <h4 className="font-semibold mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              📊 {t.progressOverview[language]}
            </h4>
            
            <div className="space-y-4">
              {/* Document Progress */}
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>📄 {t.documents[language]}</span>
                  <span>{stats.completed_documents}/{stats.total_documents}</span>
                </div>
                <div className="h-3 bg-muted rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full transition-all duration-500"
                    style={{ width: `${stats.total_documents > 0 ? (stats.completed_documents / stats.total_documents) * 100 : 0}%` }}
                  />
                </div>
              </div>
              
              {/* Test Progress */}
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>📝 {t.tests[language]}</span>
                  <span>{stats.completed_tests}/{stats.total_tests}</span>
                </div>
                <div className="h-3 bg-muted rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-purple-500 to-violet-500 rounded-full transition-all duration-500"
                    style={{ width: `${stats.total_tests > 0 ? (stats.completed_tests / stats.total_tests) * 100 : 0}%` }}
                  />
                </div>
              </div>
              
              {/* Average Score */}
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>🎯 {t.averageScore[language]}</span>
                  <span>{(stats?.average_score ?? 0).toFixed(1)}%</span>
                </div>
                <div className="h-3 bg-muted rounded-full overflow-hidden">
                  <div 
                    className={cn(
                      "h-full rounded-full transition-all duration-500",
                      stats.average_score >= 80 ? "bg-gradient-to-r from-green-500 to-emerald-500" :
                      stats.average_score >= 60 ? "bg-gradient-to-r from-yellow-500 to-amber-500" :
                      "bg-gradient-to-r from-red-500 to-orange-500"
                    )}
                    style={{ width: `${stats.average_score}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-muted/50 border border-border rounded-2xl p-4">
            <h4 className="font-medium mb-3">🚀 {language === 'tr' ? 'Hızlı Eylemler' : 'Quick Actions'}</h4>
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => setActiveTab('documents')}
                className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-xl hover:bg-blue-600 transition-colors"
              >
                <Plus className="w-4 h-4" />
                {t.createDocument[language]}
              </button>
              <button
                onClick={() => setActiveTab('tests')}
                className="flex items-center gap-2 px-4 py-2 bg-purple-500 text-white rounded-xl hover:bg-purple-600 transition-colors"
              >
                <Plus className="w-4 h-4" />
                {t.createTest[language]}
              </button>
              <button
                onClick={() => setActiveTab('visual')}
                className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-violet-500 to-purple-500 text-white rounded-xl hover:from-violet-600 hover:to-purple-600 transition-colors"
              >
                <Sparkles className="w-4 h-4" />
                {t.visual[language]}
              </button>
            </div>
          </div>
        </>
      ) : (
        <div className="text-center py-12">
          <BarChart3 className="w-16 h-16 mx-auto text-muted-foreground/50 mb-4" />
          <p className="text-lg font-medium text-muted-foreground">{t.noStatsYet[language]}</p>
          <p className="text-sm text-muted-foreground mt-1">
            {language === 'tr' ? 'Döküman ve test oluşturarak başlayın' : 'Start by creating documents and tests'}
          </p>
          <button
            onClick={loadStats}
            className="mt-4 flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-xl hover:bg-primary-600 mx-auto"
          >
            <RefreshCw className="w-4 h-4" />
            {language === 'tr' ? 'İstatistikleri Yükle' : 'Load Statistics'}
          </button>
        </div>
      )}
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
        {(['sources', 'documents', 'tests', 'chat', 'tutor', 'flashcards', 'simulations', 'analytics', 'stats', 'visual', 'multimedia', 'linking', 'quality', 'fullmeta', 'journey'] as WorkspaceTab[]).map((tab) => {
          const icons: Record<WorkspaceTab, typeof BookOpen> = { 
            sources: BookOpen, 
            documents: FileText, 
            tests: Target, 
            chat: MessageSquare,
            tutor: Bot,
            flashcards: Repeat,
            simulations: Theater,
            analytics: PieChart,
            stats: BarChart3,
            visual: Network,
            multimedia: Video,
            linking: Link2,
            quality: Zap,
            fullmeta: Brain,
            journey: Rocket
          };
          const emojis: Record<WorkspaceTab, string> = { 
            sources: '📚', 
            documents: '📄', 
            tests: '📝', 
            chat: '💬',
            tutor: '🤖',
            flashcards: '📚',
            simulations: '🎭',
            analytics: '📊',
            stats: '📈',
            visual: '🎨',
            multimedia: '🎬',
            linking: '🔗',
            quality: '⚡',
            fullmeta: '🧠',
            journey: '🎮'
          };
          const isPremium = ['tutor', 'flashcards', 'simulations', 'analytics', 'visual', 'multimedia', 'linking', 'quality', 'fullmeta', 'journey'].includes(tab);
          const Icon = icons[tab];
          return (
            <button
              key={tab}
              onClick={() => {
                setActiveTab(tab);
                if (tab === 'stats') loadStats();
                if (tab === 'analytics') loadAnalytics();
                if (tab === 'flashcards') loadFlashcards();
                if (tab === 'simulations') loadSimulations();
              }}
              className={cn(
                "flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium whitespace-nowrap transition-colors",
                activeTab === tab 
                  ? "bg-primary-500 text-white" 
                  : isPremium 
                    ? "bg-gradient-to-r from-violet-100 to-purple-100 dark:from-violet-900/30 dark:to-purple-900/30 hover:from-violet-200 hover:to-purple-200 dark:hover:from-violet-800/40 dark:hover:to-purple-800/40 border border-violet-300 dark:border-violet-700"
                    : "bg-muted hover:bg-accent"
              )}
            >
              <Icon className="w-4 h-4" />
              {emojis[tab]} {t[tab][language]}
              {isPremium && activeTab !== tab && <Sparkles className="w-3 h-3 text-violet-500" />}
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
            {activeTab === 'tutor' && renderTutorTab()}
            {activeTab === 'flashcards' && renderFlashcardsTab()}
            {activeTab === 'simulations' && renderSimulationsTab()}
            {activeTab === 'analytics' && renderAnalyticsTab()}
            {activeTab === 'stats' && renderStatsTab()}
            {activeTab === 'visual' && renderVisualTab()}
            {activeTab === 'multimedia' && renderMultimediaTab()}
            {activeTab === 'linking' && renderLinkingTab()}
            {activeTab === 'quality' && renderQualityTab()}
            {activeTab === 'fullmeta' && renderFullMetaTab()}
            {activeTab === 'journey' && renderJourneyTab()}
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
