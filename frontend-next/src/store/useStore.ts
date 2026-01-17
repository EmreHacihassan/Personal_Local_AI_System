import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// Types
export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: Source[];
  metadata?: Record<string, any>;
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
  createdAt: Date;
  updatedAt: Date;
}

export type Theme = 'light' | 'dark' | 'ocean' | 'forest' | 'sunset';
export type Page = 'chat' | 'documents' | 'history' | 'dashboard' | 'settings' | 'notes' | 'learning';

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
  webSearchEnabled: boolean;
  toggleWebSearch: () => void;
  responseMode: 'normal' | 'detailed';
  setResponseMode: (mode: 'normal' | 'detailed') => void;

  // Sessions
  sessions: Session[];
  currentSessionId: string | null;
  setCurrentSession: (id: string | null) => void;
  addSession: (session: Session) => void;
  deleteSession: (id: string) => void;

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
  language: 'tr' | 'en';
  setLanguage: (lang: 'tr' | 'en') => void;
  fontSize: 'small' | 'medium' | 'large';
  setFontSize: (size: 'small' | 'medium' | 'large') => void;
  soundEnabled: boolean;
  toggleSound: () => void;
}

export const useStore = create<AppState>()(
  persist(
    (set, get) => ({
      // Theme
      theme: 'light',
      setTheme: (theme) => {
        set({ theme });
        document.documentElement.classList.remove('light', 'dark');
        document.documentElement.classList.add(theme === 'light' || theme === 'ocean' || theme === 'forest' ? 'light' : 'dark');
      },

      // Navigation
      currentPage: 'chat',
      setCurrentPage: (page) => set({ currentPage: page }),
      sidebarCollapsed: false,
      toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

      // Chat
      messages: [],
      addMessage: (message) => set((state) => ({ 
        messages: [...state.messages, message] 
      })),
      clearMessages: () => set({ messages: [] }),
      isTyping: false,
      setIsTyping: (typing) => set({ isTyping: typing }),
      webSearchEnabled: false,
      toggleWebSearch: () => set((state) => ({ webSearchEnabled: !state.webSearchEnabled })),
      responseMode: 'normal',
      setResponseMode: (mode) => set({ responseMode: mode }),

      // Sessions
      sessions: [],
      currentSessionId: null,
      setCurrentSession: (id) => set({ currentSessionId: id }),
      addSession: (session) => set((state) => ({ 
        sessions: [session, ...state.sessions] 
      })),
      deleteSession: (id) => set((state) => ({ 
        sessions: state.sessions.filter((s) => s.id !== id) 
      })),

      // Documents
      documents: [],
      setDocuments: (docs) => set({ documents: docs }),
      addDocument: (doc) => set((state) => ({ 
        documents: [doc, ...state.documents] 
      })),
      removeDocument: (id) => set((state) => ({ 
        documents: state.documents.filter((d) => d.id !== id) 
      })),

      // Notes
      notes: [],
      addNote: (note) => set((state) => ({ 
        notes: [note, ...state.notes] 
      })),
      updateNote: (id, updates) => set((state) => ({
        notes: state.notes.map((n) => 
          n.id === id ? { ...n, ...updates, updatedAt: new Date() } : n
        ),
      })),
      deleteNote: (id) => set((state) => ({ 
        notes: state.notes.filter((n) => n.id !== id) 
      })),

      // Widget
      widgetEnabled: false,
      toggleWidget: () => set((state) => ({ widgetEnabled: !state.widgetEnabled })),
      widgetPosition: { x: 100, y: 100 },
      setWidgetPosition: (pos) => set({ widgetPosition: pos }),

      // Settings
      language: 'tr',
      setLanguage: (lang) => set({ language: lang }),
      fontSize: 'medium',
      setFontSize: (size) => set({ fontSize: size }),
      soundEnabled: true,
      toggleSound: () => set((state) => ({ soundEnabled: !state.soundEnabled })),
    }),
    {
      name: 'enterprise-ai-store',
      partialize: (state) => ({
        theme: state.theme,
        sidebarCollapsed: state.sidebarCollapsed,
        sessions: state.sessions,
        notes: state.notes,
        widgetEnabled: state.widgetEnabled,
        widgetPosition: state.widgetPosition,
        language: state.language,
        fontSize: state.fontSize,
        soundEnabled: state.soundEnabled,
        webSearchEnabled: state.webSearchEnabled,
        responseMode: state.responseMode,
      }),
    }
  )
);
