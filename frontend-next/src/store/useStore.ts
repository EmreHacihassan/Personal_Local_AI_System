import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// Types
export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: Source[];
  metadata?: Record<string, unknown>;
  isFavorite?: boolean;
  isEdited?: boolean;
  isError?: boolean;
  errorDetails?: {
    code?: number;
    type?: string;
    suggestion?: string;
  };
  responseTime?: number;
  wordCount?: number;
  confidenceScore?: number;
  followUpQuestions?: string[];
  relatedQueries?: string[];
}

export interface Source {
  title: string;
  url?: string;
  snippet?: string;
  type: 'document' | 'web' | 'knowledge';
}

export interface Session {
  id: string;
  title: string;
  messages: Message[];
  createdAt: Date;
  updatedAt: Date;
  isPinned?: boolean;
  tags?: string[];
  category?: string;
}

export interface Template {
  id: string;
  title: string;
  content: string;
  category: string;
  createdAt: Date;
  useCount?: number;
}

export interface Document {
  id: string;
  name: string;
  size: number;
  type: string;
  uploadedAt: Date;
  chunks?: number;
}

export interface Note {
  id: string;
  title: string;
  content: string;
  folder?: string;
  color?: string;
  isPinned?: boolean;
  tags?: string[];
  createdAt: Date;
  updatedAt: Date;
}

export type Theme = 'light' | 'dark' | 'ocean' | 'forest' | 'sunset' | 'lavender' | 'minimalist' | 'cherry';
export type Page = 'chat' | 'documents' | 'history' | 'dashboard' | 'settings' | 'notes' | 'learning' | 'favorites' | 'templates' | 'search';

interface AppState {
  // Theme
  theme: Theme;
  setTheme: (theme: Theme) => void;

  // Navigation
  currentPage: Page;
  setCurrentPage: (page: Page) => void;
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;

  // Chat
  messages: Message[];
  addMessage: (message: Message) => void;
  clearMessages: () => void;
  isTyping: boolean;
  setIsTyping: (typing: boolean) => void;
  webSearchMode: 'auto' | 'off' | 'on';
  setWebSearchMode: (mode: 'auto' | 'off' | 'on') => void;
  responseMode: 'auto' | 'creative' | 'analytical' | 'technical' | 'friendly' | 'academic';
  setResponseMode: (mode: 'auto' | 'creative' | 'analytical' | 'technical' | 'friendly' | 'academic') => void;

  // Sessions
  sessions: Session[];
  currentSessionId: string | null;
  setCurrentSession: (id: string | null) => void;
  addSession: (session: Session) => void;
  deleteSession: (id: string) => void;
  loadSessionMessages: (sessionId: string, messages: Message[]) => void;
  updateCurrentSession: (sessionId: string, messages: Message[]) => void;

  // Documents
  documents: Document[];
  setDocuments: (docs: Document[]) => void;
  addDocument: (doc: Document) => void;
  removeDocument: (id: string) => void;

  // Notes
  notes: Note[];
  addNote: (note: Note) => void;
  updateNote: (id: string, updates: Partial<Note>) => void;
  deleteNote: (id: string) => void;

  // Widget
  widgetEnabled: boolean;
  toggleWidget: () => void;
  widgetPosition: { x: number; y: number };
  setWidgetPosition: (pos: { x: number; y: number }) => void;

  // Settings
  language: 'tr' | 'en' | 'de';
  setLanguage: (lang: 'tr' | 'en' | 'de') => void;
  fontSize: 'small' | 'medium' | 'large';
  setFontSize: (size: 'small' | 'medium' | 'large') => void;
  soundEnabled: boolean;
  toggleSound: () => void;
  responseLength: 'auto' | 'short' | 'medium' | 'long' | 'very_long';
  setResponseLength: (length: 'auto' | 'short' | 'medium' | 'long' | 'very_long') => void;
  complexityLevel: 'simple' | 'normal' | 'comprehensive' | 'research';
  setComplexityLevel: (level: 'simple' | 'normal' | 'comprehensive' | 'research') => void;

  // Notifications
  notificationsEnabled: boolean;
  toggleNotifications: () => void;
  notifyOnComplete: boolean;
  toggleNotifyOnComplete: () => void;
  notifyOnError: boolean;
  toggleNotifyOnError: () => void;
  desktopNotifications: boolean;
  toggleDesktopNotifications: () => void;

  // Display Settings
  showTimestamps: boolean;
  toggleShowTimestamps: () => void;
  autoScroll: boolean;
  toggleAutoScroll: () => void;
  responseStyle: 'professional' | 'friendly' | 'academic' | 'technical';
  setResponseStyle: (style: 'professional' | 'friendly' | 'academic' | 'technical') => void;

  // Sidebar Filters
  showPinnedOnly: boolean;
  toggleShowPinnedOnly: () => void;

  // Templates
  templates: Template[];
  addTemplate: (template: Template) => void;
  updateTemplate: (id: string, updates: Partial<Template>) => void;
  deleteTemplate: (id: string) => void;

  // Message actions
  toggleMessageFavorite: (id: string) => void;
  editMessage: (id: string, newContent: string) => void;
  getFavoriteMessages: () => Message[];

  // Session actions
  toggleSessionPin: (id: string) => void;
  addSessionTag: (id: string, tag: string) => void;
  removeSessionTag: (id: string, tag: string) => void;
  setSessionCategory: (id: string, category: string) => void;
  renameSession: (id: string, newTitle: string) => void;

  // Note actions
  addNoteTag: (id: string, tag: string) => void;
  removeNoteTag: (id: string, tag: string) => void;

  // Streaming
  isStreaming: boolean;
  setIsStreaming: (streaming: boolean) => void;
  streamingContent: string;
  setStreamingContent: (content: string) => void;
  appendStreamingContent: (chunk: string) => void;
}

export const useStore = create<AppState>()(
  persist(
    (set, get) => ({
      // Theme
      theme: 'light' as Theme,
      setTheme: (theme: Theme) => {
        set({ theme });
        document.documentElement.classList.remove('light', 'dark');
        document.documentElement.classList.add(theme === 'light' || theme === 'ocean' || theme === 'forest' ? 'light' : 'dark');
      },

      // Navigation
      currentPage: 'chat' as Page,
      setCurrentPage: (page: Page) => set({ currentPage: page }),
      sidebarCollapsed: false,
      toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

      // Chat
      messages: [] as Message[],
      addMessage: (message: Message) => set((state) => ({ 
        messages: [...state.messages, message] 
      })),
      clearMessages: () => set({ messages: [] as Message[] }),
      isTyping: false,
      setIsTyping: (typing: boolean) => set({ isTyping: typing }),
      webSearchMode: 'auto' as 'auto' | 'off' | 'on',
      setWebSearchMode: (mode: 'auto' | 'off' | 'on') => set({ webSearchMode: mode }),
      responseMode: 'auto' as 'auto' | 'creative' | 'analytical' | 'technical' | 'friendly' | 'academic',
      setResponseMode: (mode: 'auto' | 'creative' | 'analytical' | 'technical' | 'friendly' | 'academic') => set({ responseMode: mode }),

      // Sessions
      sessions: [] as Session[],
      currentSessionId: null as string | null,
      setCurrentSession: (id: string | null) => set({ currentSessionId: id }),
      addSession: (session: Session) => set((state) => ({ 
        sessions: [session, ...state.sessions] 
      })),
      deleteSession: (id: string) => set((state) => ({ 
        sessions: state.sessions.filter((s) => s.id !== id) 
      })),
      loadSessionMessages: (sessionId: string, messages: Message[]) => set({ 
        currentSessionId: sessionId,
        messages: messages 
      }),
      updateCurrentSession: (sessionId: string, messages: Message[]) => set((state) => ({
        currentSessionId: sessionId,
        messages: messages,
        sessions: state.sessions.map((s) =>
          s.id === sessionId ? { ...s, messages, updatedAt: new Date() } : s
        ),
      })),

      // Documents
      documents: [] as Document[],
      setDocuments: (docs: Document[]) => set({ documents: docs }),
      addDocument: (doc: Document) => set((state) => ({ 
        documents: [doc, ...state.documents] 
      })),
      removeDocument: (id: string) => set((state) => ({ 
        documents: state.documents.filter((d) => d.id !== id) 
      })),

      // Notes
      notes: [] as Note[],
      addNote: (note: Note) => set((state) => ({ 
        notes: [note, ...state.notes] 
      })),
      updateNote: (id: string, updates: Partial<Note>) => set((state) => ({
        notes: state.notes.map((n) => 
          n.id === id ? { ...n, ...updates, updatedAt: new Date() } : n
        ),
      })),
      deleteNote: (id: string) => set((state) => ({ 
        notes: state.notes.filter((n) => n.id !== id) 
      })),

      // Widget
      widgetEnabled: false,
      toggleWidget: () => set((state) => ({ widgetEnabled: !state.widgetEnabled })),
      widgetPosition: { x: 100, y: 100 },
      setWidgetPosition: (pos: { x: number; y: number }) => set({ widgetPosition: pos }),

      // Settings
      language: 'tr' as 'tr' | 'en' | 'de',
      setLanguage: (lang: 'tr' | 'en' | 'de') => set({ language: lang }),
      fontSize: 'medium' as 'small' | 'medium' | 'large',
      setFontSize: (size: 'small' | 'medium' | 'large') => set({ fontSize: size }),
      soundEnabled: true,
      toggleSound: () => set((state) => ({ soundEnabled: !state.soundEnabled })),
      responseLength: 'auto' as 'auto' | 'short' | 'medium' | 'long' | 'very_long',
      setResponseLength: (length: 'auto' | 'short' | 'medium' | 'long' | 'very_long') => set({ responseLength: length }),
      complexityLevel: 'normal' as 'simple' | 'normal' | 'comprehensive' | 'research',
      setComplexityLevel: (level: 'simple' | 'normal' | 'comprehensive' | 'research') => set({ complexityLevel: level }),

      // Notifications
      notificationsEnabled: true,
      toggleNotifications: () => set((state) => ({ notificationsEnabled: !state.notificationsEnabled })),
      notifyOnComplete: true,
      toggleNotifyOnComplete: () => set((state) => ({ notifyOnComplete: !state.notifyOnComplete })),
      notifyOnError: true,
      toggleNotifyOnError: () => set((state) => ({ notifyOnError: !state.notifyOnError })),
      desktopNotifications: false,
      toggleDesktopNotifications: () => set((state) => ({ desktopNotifications: !state.desktopNotifications })),

      // Display Settings
      showTimestamps: true,
      toggleShowTimestamps: () => set((state) => ({ showTimestamps: !state.showTimestamps })),
      autoScroll: true,
      toggleAutoScroll: () => set((state) => ({ autoScroll: !state.autoScroll })),
      responseStyle: 'professional' as 'professional' | 'friendly' | 'academic' | 'technical',
      setResponseStyle: (style: 'professional' | 'friendly' | 'academic' | 'technical') => set({ responseStyle: style }),

      // Sidebar Filters
      showPinnedOnly: false,
      toggleShowPinnedOnly: () => set((state) => ({ showPinnedOnly: !state.showPinnedOnly })),

      // Templates
      templates: [] as Template[],
      addTemplate: (template: Template) => set((state) => ({ 
        templates: [template, ...state.templates] 
      })),
      updateTemplate: (id: string, updates: Partial<Template>) => set((state) => ({
        templates: state.templates.map((t) => 
          t.id === id ? { ...t, ...updates } : t
        ),
      })),
      deleteTemplate: (id: string) => set((state) => ({ 
        templates: state.templates.filter((t) => t.id !== id) 
      })),

      // Message actions
      toggleMessageFavorite: (id: string) => set((state) => ({
        messages: state.messages.map((m) =>
          m.id === id ? { ...m, isFavorite: !m.isFavorite } : m
        ),
      })),
      editMessage: (id: string, newContent: string) => set((state) => ({
        messages: state.messages.map((m) =>
          m.id === id ? { ...m, content: newContent, isEdited: true } : m
        ),
      })),
      getFavoriteMessages: (): Message[] => {
        return get().messages.filter((m: Message) => m.isFavorite);
      },

      // Session actions
      toggleSessionPin: (id: string) => set((state) => ({
        sessions: state.sessions.map((s) =>
          s.id === id ? { ...s, isPinned: !s.isPinned } : s
        ),
      })),
      addSessionTag: (id: string, tag: string) => set((state) => ({
        sessions: state.sessions.map((s) =>
          s.id === id ? { ...s, tags: [...(s.tags || []), tag] } : s
        ),
      })),
      removeSessionTag: (id: string, tag: string) => set((state) => ({
        sessions: state.sessions.map((s) =>
          s.id === id ? { ...s, tags: (s.tags || []).filter((t) => t !== tag) } : s
        ),
      })),
      setSessionCategory: (id: string, category: string) => set((state) => ({
        sessions: state.sessions.map((s) =>
          s.id === id ? { ...s, category } : s
        ),
      })),
      renameSession: (id: string, newTitle: string) => set((state) => ({
        sessions: state.sessions.map((s) =>
          s.id === id ? { ...s, title: newTitle, updatedAt: new Date() } : s
        ),
      })),

      // Note actions
      addNoteTag: (id: string, tag: string) => set((state) => ({
        notes: state.notes.map((n) =>
          n.id === id ? { ...n, tags: [...(n.tags || []), tag] } : n
        ),
      })),
      removeNoteTag: (id: string, tag: string) => set((state) => ({
        notes: state.notes.map((n) =>
          n.id === id ? { ...n, tags: (n.tags || []).filter((t) => t !== tag) } : n
        ),
      })),

      // Streaming
      isStreaming: false,
      setIsStreaming: (streaming: boolean) => set({ isStreaming: streaming }),
      streamingContent: '',
      setStreamingContent: (content: string) => set({ streamingContent: content }),
      appendStreamingContent: (chunk: string) => set((state) => ({ 
        streamingContent: state.streamingContent + chunk 
      })),
    }),
    {
      name: 'enterprise-ai-store',
      partialize: (state) => ({
        theme: state.theme,
        sidebarCollapsed: state.sidebarCollapsed,
        sessions: state.sessions,
        notes: state.notes,
        templates: state.templates,
        widgetEnabled: state.widgetEnabled,
        widgetPosition: state.widgetPosition,
        language: state.language,
        fontSize: state.fontSize,
        soundEnabled: state.soundEnabled,
        webSearchMode: state.webSearchMode,
        responseMode: state.responseMode,
        responseLength: state.responseLength,
        complexityLevel: state.complexityLevel,
        showTimestamps: state.showTimestamps,
        autoScroll: state.autoScroll,
        responseStyle: state.responseStyle,
        desktopNotifications: state.desktopNotifications,
        notificationsEnabled: state.notificationsEnabled,
        showPinnedOnly: state.showPinnedOnly,
      }),
    }
  )
);
