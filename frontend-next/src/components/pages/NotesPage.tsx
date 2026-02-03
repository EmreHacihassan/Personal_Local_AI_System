'use client';

import { useState, useMemo, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  StickyNote,
  Plus,
  Search,
  FolderOpen,
  FolderPlus,
  Trash2,
  Edit3,
  Save,
  X,
  Pin,
  Palette,
  Tag,
  ChevronRight,
  Home,
  ChevronUp,
  Grid3X3,
  List,
  Download,
  FileDown,
  FolderDown,
  Bold,
  Italic,
  Underline,
  ListOrdered,
  ListTodo,
  Heading1,
  Heading2,
  Quote,
  Code,
  Link2,
  FileText,
  Sparkles,
  // Premium feature icons
  Star,
  Archive,
  Upload,
  History,
  Filter,
  Layout,
  LayoutTemplate,
  Image as ImageIcon,
  Maximize2,
  Minimize2,
  Keyboard,
  Calculator,
  Lock,
  Unlock,
  Eye,
  EyeOff,
  // Premium WOW icons
  Brain,
  Timer,
  Flame,
  Trophy,
  Calendar
} from 'lucide-react';
import { jsPDF } from 'jspdf';
import { useStore, Note, NoteFolder } from '@/store/useStore';
import { cn, generateId, formatDate } from '@/lib/utils';
import { NoteAIToolbar } from '@/components/features/NoteAIToolbar';

// Premium Features
import { AdvancedSearchPanel } from '@/components/features/AdvancedSearchPanel';
import { BacklinksPanel } from '@/components/features/BacklinksPanel';
import { findBacklinks, extractWikiLinks, WikiContentRenderer } from '@/components/features/WikiLinkParser';
import { FavoritesPanel } from '@/components/features/FavoritesPanel';
import { ArchiveView } from '@/components/features/ArchiveView';
import { TemplateSelector } from '@/components/features/TemplateSelector';
import { BulkActionToolbar } from '@/components/features/BulkActionToolbar';
import { ExportModal } from '@/components/features/ExportModal';
import { VersionHistoryPanel } from '@/components/features/VersionHistoryPanel';
import { ImportWizard } from '@/components/features/ImportWizard';
import { TrashPanel } from '@/components/notes/TrashPanel';
import { useNoteVersions, NoteVersion } from '@/hooks/useNoteVersions';
import { API_BASE_URL } from '@/lib/api';
import { ToastContainer, useToast } from '@/components/ui/Toast';
import { useMultiSelect } from '@/hooks/useMultiSelect';
import { ImageSettingsModal, ImageSettings } from '@/components/modals/ImageSettingsModal';
import { compressImage } from '@/lib/imageUtils';
import { MATH_KEYBOARD_CATEGORIES, NORMAL_KEYBOARD_CATEGORIES } from '@/lib/constants/mathKeyboard';

// Premium WOW Features
import { SmartInsightsPanel } from '@/components/premium/SmartInsightsPanel';
import { FocusModePanel } from '@/components/premium/FocusModePanel';
import { GamificationWidget } from '@/components/premium/GamificationWidget';
import QuickActionsPanel from '@/components/premium/QuickActionsPanel';
import ZenMode from '@/components/premium/ZenMode';
import AIWritingAssistant from '@/components/premium/AIWritingAssistant';
import StatsDashboard from '@/components/premium/StatsDashboard';
import AutoSaveIndicator from '@/components/premium/AutoSaveIndicator';
import KeyboardShortcutsPanel from '@/components/premium/KeyboardShortcutsPanel';
import WordCounter from '@/components/premium/WordCounter';
import FloatingQuickNote from '@/components/premium/FloatingQuickNote';
import RecentNotesWidget from '@/components/premium/RecentNotesWidget';
import TimelinePlanner from '@/components/premium/TimelinePlanner';

// File Attachments (Premium)
import { AttachmentUploader } from '@/components/notes/AttachmentUploader';
import { AttachmentsList } from '@/components/notes/AttachmentsList';
import { FilePreviewModal } from '@/components/modals/FilePreviewModal';
import { Paperclip } from 'lucide-react';
import { NoteAttachment } from '@/store/useStore';

// Premium Note Components
import { PinnedNotesBar } from '@/components/notes/PinnedNotesBar';

// Backend - Frontend Data Mappers
const mapNoteFromApi = (note: any): Note => ({
  id: note.id,
  title: note.title,
  content: note.content,
  folder: note.folder_id, // Backend folder_id -> Frontend folder
  color: note.color,
  isPinned: note.pinned,
  isLocked: note.locked || false, // Kilit durumu
  isEncrypted: note.encrypted || false, // AI'dan gizleme durumu
  tags: note.tags || [],
  attachments: note.attachments || [], // File attachments
  createdAt: new Date(note.created_at),
  updatedAt: new Date(note.updated_at)
});

const mapFolderFromApi = (folder: any): NoteFolder => ({
  id: folder.id,
  name: folder.name,
  icon: folder.icon,
  parentId: folder.parent_id,
  color: folder.color,
  isLocked: folder.locked || false, // Kilit durumu
  isPinned: folder.pinned || false, // Sabitleme durumu
  createdAt: new Date(folder.created_at)
});

// Math keyboard kategorileri artık '@/lib/constants/mathKeyboard' modülünden import ediliyor
// MATH_KEYBOARD_CATEGORIES ve NORMAL_KEYBOARD_CATEGORIES dışarıdan geliyor

// Note colors matching Streamlit frontend
const NOTE_COLORS = [
  { id: 'default', name: 'Varsayılan', nameEn: 'Default', nameDe: 'Standard', color: 'bg-card', border: 'border-border', preview: 'bg-gray-200 dark:bg-gray-700' },
  { id: 'yellow', name: 'Sarı', nameEn: 'Yellow', nameDe: 'Gelb', color: 'bg-yellow-50 dark:bg-yellow-900/20', border: 'border-yellow-200 dark:border-yellow-800', preview: 'bg-yellow-400' },
  { id: 'green', name: 'Yeşil', nameEn: 'Green', nameDe: 'Grün', color: 'bg-green-50 dark:bg-green-900/20', border: 'border-green-200 dark:border-green-800', preview: 'bg-green-400' },
  { id: 'blue', name: 'Mavi', nameEn: 'Blue', nameDe: 'Blau', color: 'bg-blue-50 dark:bg-blue-900/20', border: 'border-blue-200 dark:border-blue-800', preview: 'bg-blue-400' },
  { id: 'purple', name: 'Mor', nameEn: 'Purple', nameDe: 'Lila', color: 'bg-purple-50 dark:bg-purple-900/20', border: 'border-purple-200 dark:border-purple-800', preview: 'bg-purple-400' },
  { id: 'pink', name: 'Pembe', nameEn: 'Pink', nameDe: 'Rosa', color: 'bg-pink-50 dark:bg-pink-900/20', border: 'border-pink-200 dark:border-pink-800', preview: 'bg-pink-400' },
  { id: 'orange', name: 'Turuncu', nameEn: 'Orange', nameDe: 'Orange', color: 'bg-orange-50 dark:bg-orange-900/20', border: 'border-orange-200 dark:border-orange-800', preview: 'bg-orange-400' },
  { id: 'red', name: 'Kırmızı', nameEn: 'Red', nameDe: 'Rot', color: 'bg-red-50 dark:bg-red-900/20', border: 'border-red-200 dark:border-red-800', preview: 'bg-red-400' },
];

// Folder icons for selection
const FOLDER_ICONS = [
  { id: 'folder', icon: '📁', name: 'Klasör' },
  { id: 'folder-open', icon: '📂', name: 'Açık Klasör' },
  { id: 'briefcase', icon: '💼', name: 'İş' },
  { id: 'books', icon: '📚', name: 'Kitaplar' },
  { id: 'target', icon: '🎯', name: 'Hedef' },
  { id: 'bulb', icon: '💡', name: 'Fikir' },
  { id: 'star', icon: '⭐', name: 'Favori' },
  { id: 'heart', icon: '❤️', name: 'Sevilen' },
  { id: 'lock', icon: '🔒', name: 'Özel' },
  { id: 'archive', icon: '🗂️', name: 'Arşiv' },
];

// NoteFolder interface is imported from useStore

export function NotesPage() {
  const {
    notes, addNote, updateNote, deleteNote,
    noteFolders, addFolder, updateFolder, deleteFolder,
    setNotes, setFolders,
    language, addNoteTag, removeNoteTag,
    targetNoteId, setTargetNoteId
  } = useStore();

  // API Sync logic moved to AppInitializer (Global sync)

  // Use store folders
  const folders = noteFolders;

  // Toast notifications
  const toast = useToast();

  // State
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedNote, setSelectedNote] = useState<Note | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [editContent, setEditContent] = useState('');
  const [showColorPicker, setShowColorPicker] = useState(false);
  const [showTagInput, setShowTagInput] = useState(false);
  const [tagInput, setTagInput] = useState('');
  const [filterByTag, setFilterByTag] = useState<string | null>(null);

  // Handle targetNoteId from store (navigation from Mind page)
  useEffect(() => {
    if (targetNoteId && notes.length > 0) {
      const targetNote = notes.find(n => n.id === targetNoteId);
      if (targetNote) {
        setSelectedNote(targetNote);
        setEditTitle(targetNote.title);
        setEditContent(targetNote.content);
        // Clear targetNoteId after selecting
        setTargetNoteId(null);
      }
    }
  }, [targetNoteId, notes, setTargetNoteId]);

  // New features state
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('list');
  const [currentFolderId, setCurrentFolderId] = useState<string | null>(null);
  // const [folders, setFolders] = useState<NoteFolder[]>([]); // REMOVED: Using store folders
  const [showNewFolderForm, setShowNewFolderForm] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');
  const [newFolderIcon, setNewFolderIcon] = useState('📁');
  const [showFolderIconPicker, setShowFolderIconPicker] = useState(false);

  // Image Upload & Settings
  const [showImageModal, setShowImageModal] = useState(false);
  const [uploadedImageInfo, setUploadedImageInfo] = useState<{ url: string, name: string } | null>(null);
  const [editingImageInfo, setEditingImageInfo] = useState<{ url: string; alt: string; options: Record<string, string> } | null>(null);

  // File Attachments State (Premium)
  const [showAttachmentUploader, setShowAttachmentUploader] = useState(false);
  const [noteAttachments, setNoteAttachments] = useState<NoteAttachment[]>([]);
  const [previewAttachment, setPreviewAttachment] = useState<NoteAttachment | null>(null);
  const [showFilePreview, setShowFilePreview] = useState(false);

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [editingFolderId, setEditingFolderId] = useState<string | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [showFolderMenu, setShowFolderMenu] = useState<string | null>(null);

  // Premium Features State
  const [showAdvancedSearch, setShowAdvancedSearch] = useState(false);
  const [showBacklinks, setShowBacklinks] = useState(false);
  const [showFavorites, setShowFavorites] = useState(false);
  const [showArchive, setShowArchive] = useState(false);
  const [showTemplates, setShowTemplates] = useState(false);
  const [showExport, setShowExport] = useState(false);
  const [showImport, setShowImport] = useState(false);
  const [showVersionHistory, setShowVersionHistory] = useState(false);
  const [showTrashPanel, setShowTrashPanel] = useState(false);
  const [showMoveModal, setShowMoveModal] = useState(false);
  const [recentNoteIds, setRecentNoteIds] = useState<string[]>([]);
  const [archivedNotes, setArchivedNotes] = useState<Note[]>([]);

  // Premium WOW Features State
  const [showSmartInsights, setShowSmartInsights] = useState(false);
  const [showFocusMode, setShowFocusMode] = useState(false);
  const [showGamification, setShowGamification] = useState(false);
  const [showQuickActions, setShowQuickActions] = useState(false);
  const [showZenMode, setShowZenMode] = useState(false);
  const [showAIAssistant, setShowAIAssistant] = useState(false);
  const [showStatsDashboard, setShowStatsDashboard] = useState(false);
  const [selectedTextForAI, setSelectedTextForAI] = useState('');
  const [showKeyboardShortcuts, setShowKeyboardShortcuts] = useState(false);
  const [autoSaveEnabled, setAutoSaveEnabled] = useState(true);
  const [showRecentNotes, setShowRecentNotes] = useState(false);
  const [showTimelinePlanner, setShowTimelinePlanner] = useState(false);

  // Tam Ekran Modları
  const [isNoteFullscreen, setIsNoteFullscreen] = useState(false);  // Sadece not detayı tam ekran
  const [isPageFullscreen, setIsPageFullscreen] = useState(false); // Tüm notlar sayfası tam ekran
  const [showMathKeyboard, setShowMathKeyboard] = useState(false); // Matematik ekran klavyesi
  const [mathCategory, setMathCategory] = useState('basic'); // Aktif matematik kategori
  const [keyboardType, setKeyboardType] = useState<'math' | 'normal'>('math'); // Klavye tipi seçimi

  // Klavye tipi değiştiğinde varsayılan kategoriyi ayarla
  useEffect(() => {
    if (keyboardType === 'math') {
      setMathCategory('basic');
    } else {
      setMathCategory('turkish');
    }
  }, [keyboardType]);

  // Multi-select hook
  const multiSelect = useMultiSelect({
    items: notes,
    getItemId: (note) => note.id,
  });

  // Version history hook
  const { versions: noteVersions, fetchVersions, restoreVersion } = useNoteVersions(selectedNote?.id || null);

  // ESC tuşu ile tam ekrandan çık + Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // ESC - Close fullscreen/modals
      if (e.key === 'Escape') {
        if (isNoteFullscreen) setIsNoteFullscreen(false);
        else if (isPageFullscreen) setIsPageFullscreen(false);
        else if (showAdvancedSearch) setShowAdvancedSearch(false);
        else if (showVersionHistory) setShowVersionHistory(false);
        else if (showTrashPanel) setShowTrashPanel(false);
        else if (showBacklinks) setShowBacklinks(false);
        return;
      }

      // Ignore shortcuts when typing in input/textarea
      const target = e.target as HTMLElement;
      const isTyping = ['INPUT', 'TEXTAREA'].includes(target.tagName) || target.isContentEditable;

      // Ctrl/Cmd shortcuts
      if (e.ctrlKey || e.metaKey) {
        switch (e.key.toLowerCase()) {
          case 's': // Save
            e.preventDefault();
            if (isEditing && selectedNote) {
              // Trigger save - handleSave is defined later, we'll call it via state
              document.getElementById('save-note-btn')?.click();
            }
            break;
          case 'n': // New note
            if (!isTyping) {
              e.preventDefault();
              setSelectedNote(null);
              setIsEditing(true);
              setEditTitle('');
              setEditContent('');
            }
            break;
          case 'f': // Focus search
            if (!isTyping) {
              e.preventDefault();
              document.getElementById('notes-search-input')?.focus();
            }
            break;
          case 'b': // Bold (when editing)
            if (isEditing) {
              e.preventDefault();
              document.getElementById('toolbar-bold-btn')?.click();
            }
            break;
          case 'i': // Italic (when editing)
            if (isEditing) {
              e.preventDefault();
              document.getElementById('toolbar-italic-btn')?.click();
            }
            break;
        }
      }

      // Delete key - delete selected note
      if (e.key === 'Delete' && selectedNote && !isTyping && !isEditing) {
        e.preventDefault();
        if (!selectedNote.isLocked) {
          handleDeleteNote(selectedNote);
        }
      }

      // ? key - show keyboard shortcuts help
      if (e.key === '?' && !isTyping) {
        // Could show a modal with all shortcuts
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isNoteFullscreen, isPageFullscreen, showAdvancedSearch, showVersionHistory, showTrashPanel, showBacklinks, isEditing, selectedNote]);

  // Get current folder and its path (breadcrumb)
  const currentFolder = useMemo(() => {
    return folders.find(f => f.id === currentFolderId) || null;
  }, [folders, currentFolderId]);

  const folderPath = useMemo(() => {
    const path: NoteFolder[] = [];
    let current = currentFolder;
    while (current) {
      path.unshift(current);
      current = folders.find(f => f.id === current?.parentId) || null;
    }
    return path;
  }, [currentFolder, folders]);

  // Get subfolders of current folder (pinned first)
  const subFolders = useMemo(() => {
    return folders
      .filter(f => f.parentId === currentFolderId)
      .sort((a, b) => {
        // Pinned folders first
        if (a.isPinned && !b.isPinned) return -1;
        if (!a.isPinned && b.isPinned) return 1;
        return 0;
      });
  }, [folders, currentFolderId]);

  // Recursive note count for a folder (includes all nested subfolders)
  const getRecursiveNoteCount = useCallback((folderId: string): number => {
    const folder = folders.find(f => f.id === folderId);
    if (!folder) return 0;
    
    // Direct notes in this folder
    const directNotes = notes.filter(n => n.folder === folderId || n.folder === folder.name).length;
    
    // Child folders
    const childFolders = folders.filter(f => f.parentId === folderId);
    
    // Recursive count from child folders
    const childNotes = childFolders.reduce((sum, child) => sum + getRecursiveNoteCount(child.id), 0);
    
    return directNotes + childNotes;
  }, [folders, notes]);

  // Get direct subfolder count
  const getDirectSubfolderCount = useCallback((folderId: string): number => {
    return folders.filter(f => f.parentId === folderId).length;
  }, [folders]);

  // Get all unique folder names from notes (for backward compatibility)
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const uniqueNoteFolderNames = useMemo(() => {
    return Array.from(new Set(notes.map(n => n.folder).filter(Boolean))) as string[];
  }, [notes]);

  // Get all tags
  const allTags = useMemo(() => {
    return Array.from(new Set(notes.flatMap(n => n.tags || []))).filter(Boolean);
  }, [notes]);

  // Filter notes based on current folder and search
  const filteredNotes = useMemo(() => {
    return notes
      .filter(note => {
        const matchesSearch =
          note.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          note.content.toLowerCase().includes(searchQuery.toLowerCase());

        // Match folder - either by folder ID or folder name
        const matchesFolder = !currentFolderId
          ? !note.folder // Root level - notes without folder
          : note.folder === currentFolderId || note.folder === currentFolder?.name;

        const matchesTag = !filterByTag || (note.tags || []).includes(filterByTag);

        // If searching, show all notes that match
        if (searchQuery) {
          return matchesSearch && matchesTag;
        }

        return matchesSearch && matchesFolder && matchesTag;
      })
      .sort((a, b) => {
        if (a.isPinned && !b.isPinned) return -1;
        if (!a.isPinned && b.isPinned) return 1;
        return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime();
      });
  }, [notes, searchQuery, currentFolderId, currentFolder, filterByTag]);

  // Folder operations
  const handleCreateFolder = () => {
    if (!newFolderName.trim()) return;

    const tempId = generateId();

    // Optimistic update
    const newFolder: NoteFolder = {
      id: tempId,
      name: newFolderName.trim(),
      icon: newFolderIcon,
      parentId: currentFolderId,
      color: 'blue',
      createdAt: new Date()
    };
    addFolder(newFolder);

    // Backend call
    fetch('/api/folders', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: newFolderName.trim(),
        icon: newFolderIcon,
        parent_id: currentFolderId,
        color: 'blue'
      })
    })
      .then(async res => {
        if (res.ok) {
          const data = await res.json();
          // Replace optimistic folder with real one (remove temp, add real)
          deleteFolder(tempId);
          addFolder(mapFolderFromApi(data));
        }
      })
      .catch(console.error);


    setNewFolderName('');
    setNewFolderIcon('📁');
    setShowNewFolderForm(false);
  };

  const handleDeleteFolder = async (folderId: string) => {
    // Delete folder and move notes to parent
    const folder = folders.find(f => f.id === folderId);
    if (!folder) return;

    // Kilit kontrolü
    if (folder.isLocked) {
      const lockedMessage = language === 'tr'
        ? 'Bu klasör kilitli. Silmek için önce kilidi kaldırın.'
        : language === 'de'
          ? 'Dieser Ordner ist gesperrt. Entsperren Sie ihn zuerst.'
          : 'This folder is locked. Unlock it first to delete.';
      toast.warning(lockedMessage);
      return;
    }

    // Confirm deletion
    const confirmMessage = language === 'tr'
      ? `"${folder.name}" klasörünü silmek istediğinizden emin misiniz?`
      : language === 'de'
        ? `Möchten Sie den Ordner "${folder.name}" wirklich löschen?`
        : `Are you sure you want to delete the folder "${folder.name}"?`;

    if (!confirm(confirmMessage)) return;

    // Move notes in this folder to parent
    notes.forEach(note => {
      if (note.folder === folderId || note.folder === folder.name) {
        updateNote(note.id, { folder: folder.parentId || undefined });
      }
    });

    const deleteRecursive = (id: string) => {
      folders.filter(f => f.parentId === id).forEach(sub => deleteRecursive(sub.id));
      deleteFolder(id);
    };

    deleteRecursive(folderId);

    if (currentFolderId === folderId) {
      setCurrentFolderId(folder.parentId);
    }

    // Backend API call to delete folder
    try {
      const response = await fetch(`/api/folders/${folderId}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        console.error('Failed to delete folder from backend');
      }
    } catch (error) {
      console.error('Delete folder error:', error);
    }
  };

  const handleNavigateUp = () => {
    if (currentFolder) {
      setCurrentFolderId(currentFolder.parentId);
    }
  };

  // Premium PDF Helper - Creates professional editable PDF
  const createPremiumPDF = useCallback((title: string): jsPDF => {
    const pdf = new jsPDF({
      orientation: 'portrait',
      unit: 'mm',
      format: 'a4',
    });

    // Page dimensions
    const pageWidth = pdf.internal.pageSize.getWidth();
    const _pageHeight = pdf.internal.pageSize.getHeight();
    const margin = 20;

    // Header gradient effect (simulated with rectangles)
    pdf.setFillColor(139, 92, 246); // Violet
    pdf.rect(0, 0, pageWidth, 35, 'F');
    pdf.setFillColor(124, 58, 237); // Darker violet
    pdf.rect(0, 30, pageWidth, 5, 'F');

    // App logo/branding
    pdf.setTextColor(255, 255, 255);
    pdf.setFontSize(10);
    pdf.text('Enterprise AI Assistant', margin, 12);

    // Main title
    pdf.setFontSize(18);
    pdf.setFont('helvetica', 'bold');
    pdf.text(title, margin, 24);

    // Reset for content
    pdf.setTextColor(0, 0, 0);
    pdf.setFont('helvetica', 'normal');

    return pdf;
  }, []);

  // Add text with word wrap and page breaks
  const addTextToPDF = useCallback((pdf: jsPDF, text: string, startY: number, options?: {
    fontSize?: number;
    fontStyle?: string;
    color?: [number, number, number];
    indent?: number;
  }): number => {
    const pageWidth = pdf.internal.pageSize.getWidth();
    const pageHeight = pdf.internal.pageSize.getHeight();
    const margin = 20;
    const maxWidth = pageWidth - margin * 2 - (options?.indent || 0);

    pdf.setFontSize(options?.fontSize || 11);
    pdf.setFont('helvetica', options?.fontStyle || 'normal');
    if (options?.color) {
      pdf.setTextColor(...options.color);
    } else {
      pdf.setTextColor(60, 60, 60);
    }

    const lines = pdf.splitTextToSize(text, maxWidth);
    let y = startY;

    for (const line of lines) {
      if (y > pageHeight - 25) {
        pdf.addPage();
        y = 25;
      }
      pdf.text(line, margin + (options?.indent || 0), y);
      y += (options?.fontSize || 11) * 0.4 + 2;
    }

    return y;
  }, []);

  // Download single note as premium PDF
  const handleDownloadNote = useCallback((note: Note) => {
    const pdf = createPremiumPDF(note.title);
    let y = 50;

    // Note metadata box
    pdf.setFillColor(248, 250, 252);
    pdf.roundedRect(20, y - 5, 170, 20, 3, 3, 'F');
    pdf.setFontSize(9);
    pdf.setTextColor(100, 100, 100);
    pdf.text(`Olusturulma: ${formatDate(note.createdAt)}  |  Guncelleme: ${formatDate(note.updatedAt)}`, 25, y + 5);

    if (note.tags && note.tags.length > 0) {
      pdf.text(`Etiketler: ${note.tags.join(', ')}`, 25, y + 12);
    }

    y += 30;

    // Divider line
    pdf.setDrawColor(200, 200, 200);
    pdf.setLineWidth(0.5);
    pdf.line(20, y, 190, y);
    y += 10;

    // Note content - şifreli notları decode et
    const displayContent = getDisplayContent(note);
    if (displayContent) {
      y = addTextToPDF(pdf, displayContent, y, { fontSize: 11 });
    } else {
      y = addTextToPDF(pdf, '(Bu not bos)', y, { fontSize: 11, fontStyle: 'italic', color: [150, 150, 150] });
    }

    // Footer
    const pageCount = pdf.getNumberOfPages();
    for (let i = 1; i <= pageCount; i++) {
      pdf.setPage(i);
      pdf.setFontSize(8);
      pdf.setTextColor(150, 150, 150);
      pdf.text(`Sayfa ${i} / ${pageCount}`, 105, 290, { align: 'center' });
      pdf.text('Enterprise AI Assistant ile olusturuldu', 105, 295, { align: 'center' });
    }

    // Save with sanitized filename
    const filename = note.title.replace(/[^a-zA-Z0-9\s]/g, '').trim() || 'not';
    pdf.save(`${filename}.pdf`);
  }, [createPremiumPDF, addTextToPDF]);

  // Download folder as premium PDF
  const handleDownloadFolder = useCallback(async (folderId: string) => {
    const folder = folders.find(f => f.id === folderId);
    if (!folder) return;

    const folderNotes = notes.filter(n => n.folder === folderId || n.folder === folder.name);

    const getAllSubfolderNotes = (parentId: string, path: string = ''): { path: string; note: Note }[] => {
      const result: { path: string; note: Note }[] = [];
      const subFolders = folders.filter(f => f.parentId === parentId);

      for (const subFolder of subFolders) {
        const subNotes = notes.filter(n => n.folder === subFolder.id || n.folder === subFolder.name);
        const subPath = path ? `${path} / ${subFolder.name}` : subFolder.name;
        subNotes.forEach(note => result.push({ path: subPath, note }));
        result.push(...getAllSubfolderNotes(subFolder.id, subPath));
      }

      return result;
    };

    const allNotes = [
      ...folderNotes.map(note => ({ path: '', note })),
      ...getAllSubfolderNotes(folderId)
    ];

    if (allNotes.length === 0) {
      const pdf = createPremiumPDF(`${folder.name} Klasoru`);
      addTextToPDF(pdf, 'Bu klasor bos.', 55, { fontSize: 12, fontStyle: 'italic', color: [150, 150, 150] });
      pdf.save(`${folder.name}_bos.pdf`);
      return;
    }

    const pdf = createPremiumPDF(`${folder.name} Klasoru`);
    let y = 50;

    // Summary box
    pdf.setFillColor(248, 250, 252);
    pdf.roundedRect(20, y - 5, 170, 15, 3, 3, 'F');
    pdf.setFontSize(10);
    pdf.setTextColor(100, 100, 100);
    pdf.text(`Toplam ${allNotes.length} not  |  Indirilme: ${new Date().toLocaleString('tr-TR')}`, 25, y + 5);
    y += 25;

    allNotes.forEach(({ path, note }, index) => {
      // Check for page break
      if (y > 250) {
        pdf.addPage();
        y = 25;
      }

      // Note card background
      pdf.setFillColor(252, 252, 254);
      pdf.setDrawColor(230, 230, 235);
      pdf.roundedRect(20, y - 5, 170, 8, 2, 2, 'FD');

      // Note title
      pdf.setFontSize(12);
      pdf.setFont('helvetica', 'bold');
      pdf.setTextColor(60, 60, 60);
      const titleText = path ? `${path} / ${note.title}` : note.title;
      pdf.text(titleText, 25, y + 2);
      y += 12;

      // Note content - şifreli notları decode et
      const displayContent = getDisplayContent(note);
      if (displayContent) {
        const contentPreview = displayContent.length > 500 ? displayContent.substring(0, 500) + '...' : displayContent;
        y = addTextToPDF(pdf, contentPreview, y, { fontSize: 10 });
      }

      // Tags and date
      pdf.setFontSize(8);
      pdf.setTextColor(130, 130, 130);
      let metaText = formatDate(note.updatedAt);
      if (note.tags && note.tags.length > 0) {
        metaText += `  |  ${note.tags.join(', ')}`;
      }
      pdf.text(metaText, 25, y + 2);
      y += 15;

      // Separator
      if (index < allNotes.length - 1) {
        pdf.setDrawColor(230, 230, 230);
        pdf.setLineWidth(0.3);
        pdf.line(30, y - 5, 180, y - 5);
      }
    });

    // Footer on all pages
    const pageCount = pdf.getNumberOfPages();
    for (let i = 1; i <= pageCount; i++) {
      pdf.setPage(i);
      pdf.setFontSize(8);
      pdf.setTextColor(150, 150, 150);
      pdf.text(`Sayfa ${i} / ${pageCount}`, 105, 290, { align: 'center' });
      pdf.text('Enterprise AI Assistant ile olusturuldu', 105, 295, { align: 'center' });
    }

    pdf.save(`${folder.name}_notlar.pdf`);
  }, [folders, notes, createPremiumPDF, addTextToPDF]);

  // Download all notes as premium PDF
  const handleDownloadAllNotes = useCallback(() => {
    if (notes.length === 0) return;

    const pdf = createPremiumPDF('Tum Notlarim');
    let y = 50;

    // Summary box
    pdf.setFillColor(248, 250, 252);
    pdf.roundedRect(20, y - 5, 170, 15, 3, 3, 'F');
    pdf.setFontSize(10);
    pdf.setTextColor(100, 100, 100);
    pdf.text(`Toplam ${notes.length} not  |  ${folders.length} klasor  |  ${new Date().toLocaleString('tr-TR')}`, 25, y + 5);
    y += 25;

    // Group by folder
    const notesWithoutFolder = notes.filter(n => !n.folder);
    const foldersWithNotes = folders.map(folder => ({
      folder,
      notes: notes.filter(n => n.folder === folder.id || n.folder === folder.name)
    })).filter(f => f.notes.length > 0);

    // Root level notes
    if (notesWithoutFolder.length > 0) {
      if (y > 250) { pdf.addPage(); y = 25; }

      // Section header
      pdf.setFillColor(139, 92, 246);
      pdf.roundedRect(20, y - 3, 170, 10, 2, 2, 'F');
      pdf.setFontSize(11);
      pdf.setFont('helvetica', 'bold');
      pdf.setTextColor(255, 255, 255);
      pdf.text(`Ana Dizin (${notesWithoutFolder.length} not)`, 25, y + 4);
      y += 18;

      notesWithoutFolder.forEach((note) => {
        if (y > 260) { pdf.addPage(); y = 25; }

        pdf.setFontSize(11);
        pdf.setFont('helvetica', 'bold');
        pdf.setTextColor(60, 60, 60);
        pdf.text(note.title, 25, y);
        y += 6;

        const displayContent = getDisplayContent(note);
        if (displayContent) {
          const preview = displayContent.length > 200 ? displayContent.substring(0, 200) + '...' : displayContent;
          y = addTextToPDF(pdf, preview, y, { fontSize: 9, indent: 5 });
        }

        pdf.setFontSize(8);
        pdf.setTextColor(130, 130, 130);
        pdf.text(formatDate(note.updatedAt), 30, y);
        y += 10;
      });

      y += 5;
    }

    // Folder notes
    foldersWithNotes.forEach(({ folder, notes: folderNotes }) => {
      if (y > 250) { pdf.addPage(); y = 25; }

      // Section header
      pdf.setFillColor(99, 102, 241);
      pdf.roundedRect(20, y - 3, 170, 10, 2, 2, 'F');
      pdf.setFontSize(11);
      pdf.setFont('helvetica', 'bold');
      pdf.setTextColor(255, 255, 255);
      pdf.text(`${folder.name} (${folderNotes.length} not)`, 25, y + 4);
      y += 18;

      folderNotes.forEach((note) => {
        if (y > 260) { pdf.addPage(); y = 25; }

        pdf.setFontSize(11);
        pdf.setFont('helvetica', 'bold');
        pdf.setTextColor(60, 60, 60);
        pdf.text(note.title, 25, y);
        y += 6;

        // Not içeriğini ekle
        if (note.content) {
          const preview = note.content.length > 200 ? note.content.substring(0, 200) + '...' : note.content;
          y = addTextToPDF(pdf, preview, y, { fontSize: 9, indent: 5 });
        }

        pdf.setFontSize(8);
        pdf.setTextColor(130, 130, 130);
        pdf.text(formatDate(note.updatedAt), 30, y);
        y += 10;
      });

      y += 5;
    });

    // Footer on all pages
    const pageCount = pdf.getNumberOfPages();
    for (let i = 1; i <= pageCount; i++) {
      pdf.setPage(i);
      pdf.setFontSize(8);
      pdf.setTextColor(150, 150, 150);
      pdf.text(`Sayfa ${i} / ${pageCount}`, 105, 290, { align: 'center' });
      pdf.text('Enterprise AI Assistant ile olusturuldu', 105, 295, { align: 'center' });
    }

    pdf.save(`tum_notlarim_${new Date().toISOString().split('T')[0]}.pdf`);
  }, [notes, folders, createPremiumPDF, addTextToPDF]);

  // Handle adding tag
  const handleAddTag = () => {
    if (!tagInput.trim() || !selectedNote) return;
    addNoteTag(selectedNote.id, tagInput.trim());
    setSelectedNote(prev => prev ? { ...prev, tags: [...(prev.tags || []), tagInput.trim()] } : null);
    setTagInput('');
    setShowTagInput(false);
  };

  // Handle removing tag
  const handleRemoveTag = (tag: string) => {
    if (!selectedNote) return;
    removeNoteTag(selectedNote.id, tag);
    setSelectedNote(prev => prev ? { ...prev, tags: (prev.tags || []).filter(t => t !== tag) } : null);
  };

  // Yeni not
  const handleNewNote = async () => {
    const tempId = generateId();
    const newNote: Note = {
      id: tempId,
      title: language === 'tr' ? 'Yeni Not' : language === 'de' ? 'Neue Notiz' : 'New Note',
      content: '',
      folder: currentFolderId || undefined,
      color: 'default',
      isPinned: false,
      createdAt: new Date(),
      updatedAt: new Date()
    };

    addNote(newNote);
    setSelectedNote(newNote);
    setEditTitle(newNote.title);
    setEditContent(newNote.content);
    setIsEditing(true);

    // Backend call
    try {
      const res = await fetch('/api/notes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: newNote.title,
          content: '',
          folder_id: currentFolderId || null,
          color: 'default',
          pinned: false,
          tags: []
        })
      });

      if (res.ok) {
        const data = await res.json();
        const realNote = mapNoteFromApi(data);
        deleteNote(tempId); // Remove temp
        addNote(realNote);  // Add real
        setSelectedNote(realNote); // Update selection to real note
      }
    } catch (e) {
      console.error('Create note failed:', e);
    }
  };

  // Not düzenlemeye başla
  const handleEdit = (note: Note) => {
    setSelectedNote(note);
    setEditTitle(note.title);
    setEditContent(note.content);
    setIsEditing(true);
    // Load attachments for this note
    setNoteAttachments((note as any).attachments || []);
  };

  // Kaydet
  const handleSave = async () => {
    if (selectedNote) {
      const contentToSave = editContent;
      
      // Optimistic update
      const updatedNote = {
        ...selectedNote,
        title: editTitle,
        content: contentToSave,
        updatedAt: new Date()
      };
      updateNote(selectedNote.id, {
        title: editTitle,
        content: contentToSave
      });
      setSelectedNote(updatedNote);
      setIsEditing(false);

      // Backend call
      try {
        await fetch(`/api/notes/${selectedNote.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            title: editTitle,
            content: contentToSave,
            attachments: noteAttachments // Save attachments
          })
        });
        
        // Record writing activity for gamification
        const wordCount = editContent.split(/\s+/).filter(w => w.length > 0).length;
        await fetch(`/api/notes/premium/activity?activity_type=note_edit&words=${wordCount}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });
      } catch (e) {
        console.error('Save note failed:', e);
      }
    }
  };

  // İptal
  const handleCancel = () => {
    setIsEditing(false);
    if (selectedNote) {
      setEditTitle(selectedNote.title);
      setEditContent(selectedNote.content);
    }
  };

  // Not silme - backend API ile senkronize
  const handleDeleteNote = async (note: Note) => {
    // Kilit kontrolü
    if (note.isLocked) {
      const lockedMessage = language === 'tr'
        ? 'Bu not kilitli. Silmek için önce kilidi kaldırın.'
        : language === 'de'
          ? 'Diese Notiz ist gesperrt. Entsperren Sie sie zuerst.'
          : 'This note is locked. Unlock it first to delete.';
      toast.warning(lockedMessage);
      return;
    }

    const confirmMessage = language === 'tr'
      ? `"${note.title}" notunu silmek istediğinizden emin misiniz?`
      : language === 'de'
        ? `Möchten Sie die Notiz "${note.title}" wirklich löschen?`
        : `Are you sure you want to delete the note "${note.title}"?`;

    if (!confirm(confirmMessage)) return;

    // Optimistic delete
    deleteNote(note.id);
    if (selectedNote?.id === note.id) {
      setSelectedNote(null);
    }

    // Backend API call
    try {
      const response = await fetch(`/api/notes/${note.id}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        console.error('Failed to delete note from backend');
      }
    } catch (error) {
      console.error('Delete note error:', error);
    }
  };

  // Toggle pin
  const handleTogglePin = (note: Note) => {
    updateNote(note.id, { isPinned: !note.isPinned });
    if (selectedNote?.id === note.id) {
      setSelectedNote({ ...note, isPinned: !note.isPinned });
    }
  };

  // Toggle note lock - Kilitli notlar silinemez
  const handleToggleNoteLock = async (note: Note) => {
    const newLockState = !note.isLocked;
    
    // Optimistic update
    updateNote(note.id, { isLocked: newLockState });
    if (selectedNote?.id === note.id) {
      setSelectedNote({ ...note, isLocked: newLockState });
    }

    // Backend API call
    try {
      const response = await fetch(`/api/notes/${note.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ locked: newLockState }),
      });
      if (!response.ok) {
        // Revert on failure
        updateNote(note.id, { isLocked: note.isLocked });
        if (selectedNote?.id === note.id) {
          setSelectedNote({ ...note, isLocked: note.isLocked });
        }
        console.error('Failed to toggle note lock');
      }
    } catch (error) {
      console.error('Toggle note lock error:', error);
    }
  };

  // Toggle folder lock - Kilitli klasörler silinemez
  const handleToggleFolderLock = async (folder: NoteFolder) => {
    const newLockState = !folder.isLocked;
    
    // Optimistic update
    updateFolder(folder.id, { isLocked: newLockState });

    // Backend API call
    try {
      const response = await fetch(`/api/folders/${folder.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ locked: newLockState }),
      });
      if (!response.ok) {
        // Revert on failure
        updateFolder(folder.id, { isLocked: folder.isLocked });
        console.error('Failed to toggle folder lock');
      }
    } catch (error) {
      console.error('Toggle folder lock error:', error);
    }
  };

  // Toggle folder pin - Sabitlenmiş klasörler üstte görünür
  const handleToggleFolderPin = async (folder: NoteFolder) => {
    const newPinState = !folder.isPinned;
    
    // Optimistic update
    updateFolder(folder.id, { isPinned: newPinState });

    // Backend API call
    try {
      const response = await fetch(`/api/folders/${folder.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pinned: newPinState }),
      });
      if (!response.ok) {
        // Revert on failure
        updateFolder(folder.id, { isPinned: folder.isPinned });
        console.error('Failed to toggle folder pin');
      }
    } catch (error) {
      console.error('Toggle folder pin error:', error);
    }
  };

  // ==================== AI'DAN GİZLEME (OBFUSCATION) - DEAKTIF ====================
  
  // Not'u AI'dan gizle/göster toggle - ŞİMDİLİK DEVRE DIŞI
  const handleToggleNoteHidden = async (_note: Note) => {
    // DEAKTIF - Hiçbir şey yapma
    return;
  };

  // Gizli not içeriğini decode et (UI görüntüleme için)
  const getDisplayContent = (note: Note): string => {
    if (!note.isEncrypted) return note.content;
    try {
      return decodeURIComponent(escape(atob(note.content)));
    } catch {
      return note.content;
    }
  };

  // Set color
  const handleSetColor = (note: Note, colorId: string) => {
    updateNote(note.id, { color: colorId });
    if (selectedNote?.id === note.id) {
      setSelectedNote({ ...note, color: colorId });
    }
    setShowColorPicker(false);
  };

  // Get note color classes
  const getNoteColorClasses = (colorId?: string) => {
    const noteColor = NOTE_COLORS.find(c => c.id === colorId) || NOTE_COLORS[0];
    return { bg: noteColor.color, border: noteColor.border };
  };

  // Handle Image Settings Confirm
  const handleImageConfirm = (settings: ImageSettings) => {
    if (!uploadedImageInfo) return;

    const options = [
      `size:${settings.size}`,
      `align:${settings.align}`,
      `shape:${settings.shape}`,
      `showCaption:${settings.showCaption !== false}`
    ].join('|');

    // ![Caption|size:medium|align:center|shape:rounded|showCaption:true](url)
    // Use empty string if caption is empty, not fallback to filename
    const caption = settings.caption !== undefined ? settings.caption : uploadedImageInfo.name;
    const imageMarkdown = `\n![${caption}|${options}](${uploadedImageInfo.url})\n`;

    const textarea = document.querySelector('textarea');
    if (textarea) {
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const text = editContent;
      setEditContent(text.substring(0, start) + imageMarkdown + text.substring(end));
    } else {
      setEditContent(editContent + imageMarkdown);
    }

    setShowImageModal(false);
    setUploadedImageInfo(null);
    setEditingImageInfo(null);
  };

  // Handle existing image edit (when clicking on image in preview mode)
  const handleImageEdit = (imageInfo: { url: string; alt: string; options: Record<string, string> }) => {
    setEditingImageInfo(imageInfo);
    setUploadedImageInfo({ url: imageInfo.url, name: imageInfo.alt || 'image' });
    setShowImageModal(true);
  };

  // Handle image update (replacing old image markdown with new settings)
  const handleImageUpdate = (settings: ImageSettings) => {
    if (!editingImageInfo || !selectedNote) return;

    const oldOptions = [
      `size:${editingImageInfo.options.size || 'medium'}`,
      `align:${editingImageInfo.options.align || 'center'}`,
      `shape:${editingImageInfo.options.shape || 'rounded'}`
    ].join('|');

    const newOptions = [
      `size:${settings.size}`,
      `align:${settings.align}`,
      `shape:${settings.shape}`,
      `showCaption:${settings.showCaption !== false}`
    ].join('|');

    // Build old and new markdown patterns
    const oldAlt = editingImageInfo.alt || '';
    // Use empty string if caption is cleared, not fallback
    const newCaption = settings.caption !== undefined ? settings.caption : (editingImageInfo.alt || '');
    
    // Escape special regex characters in URL
    const escapedUrl = editingImageInfo.url.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    
    // Create regex to find the old image markdown
    const oldMarkdownRegex = new RegExp(
      `!\\[([^\\]]*\\|)?${oldOptions.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\]\\(${escapedUrl}\\)`,
      'g'
    );
    
    // Also try simpler pattern for backwards compat
    const simpleRegex = new RegExp(
      `!\\[${oldAlt.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\|[^\\]]*\\]\\(${escapedUrl}\\)`,
      'g'
    );

    const newMarkdown = `![${newCaption}|${newOptions}](${editingImageInfo.url})`;

    let updatedContent = selectedNote.content;
    
    // Try to replace with the complex regex first, then simple
    if (oldMarkdownRegex.test(updatedContent)) {
      updatedContent = updatedContent.replace(oldMarkdownRegex, newMarkdown);
    } else if (simpleRegex.test(selectedNote.content)) {
      updatedContent = selectedNote.content.replace(simpleRegex, newMarkdown);
    } else {
      // Fallback: find any image with same URL
      const fallbackRegex = new RegExp(`!\\[[^\\]]*\\]\\(${escapedUrl}\\)`, 'g');
      updatedContent = selectedNote.content.replace(fallbackRegex, newMarkdown);
    }

    // Update note
    updateNote(selectedNote.id, { content: updatedContent });
    setSelectedNote(prev => prev ? { ...prev, content: updatedContent } : null);

    setShowImageModal(false);
    setUploadedImageInfo(null);
    setEditingImageInfo(null);
  };

  // Handle inline image update (from InlineImageEditor - köşelerden sürükle-boyutlandır)
  const handleInlineImageUpdate = (imageUrl: string, newOptions: Record<string, any>) => {
    if (!selectedNote) return;

    // Escape special regex characters in URL
    const escapedUrl = imageUrl.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    
    // Build new options string
    const optionsArr = [];
    if (newOptions.size) optionsArr.push(`size:${newOptions.size}`);
    else if (newOptions.width) optionsArr.push(`size:custom`);
    if (newOptions.align) optionsArr.push(`align:${newOptions.align}`);
    if (newOptions.shape) optionsArr.push(`shape:${newOptions.shape}`);
    if (newOptions.width) optionsArr.push(`width:${Math.round(newOptions.width)}`);
    if (newOptions.height) optionsArr.push(`height:${Math.round(newOptions.height)}`);
    // Offset (taşıma pozisyonu) - yeni
    if (newOptions.offsetX !== undefined && newOptions.offsetX !== 0) optionsArr.push(`offsetX:${Math.round(newOptions.offsetX)}`);
    if (newOptions.offsetY !== undefined && newOptions.offsetY !== 0) optionsArr.push(`offsetY:${Math.round(newOptions.offsetY)}`);
    
    const newOptionsStr = optionsArr.join('|');
    
    // Find and replace image markdown
    const imageRegex = new RegExp(`!\\[([^\\]]*)\\]\\(${escapedUrl}\\)`, 'g');
    
    const updatedContent = selectedNote.content.replace(imageRegex, (match, altText) => {
      // Parse existing alt text to get caption (before first |)
      // Use newOptions.caption if provided, otherwise keep existing caption
      const existingCaption = altText.split('|')[0];
      const caption = newOptions.caption !== undefined ? newOptions.caption : existingCaption;
      return `![${caption}|${newOptionsStr}](${imageUrl})`;
    });

    // Update note
    updateNote(selectedNote.id, { content: updatedContent });
    setSelectedNote(prev => prev ? { ...prev, content: updatedContent } : null);
  };

  // Handle paste event for images (Ctrl+V)
  const handlePaste = useCallback(async (e: React.ClipboardEvent<HTMLTextAreaElement>) => {
    const items = e.clipboardData?.items;
    if (!items) return;

    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      if (item.type.startsWith('image/')) {
        e.preventDefault();
        const file = item.getAsFile();
        if (!file) continue;

        try {
          // Upload image to backend
          const formData = new FormData();
          formData.append('file', file);

          let res;
          try {
            res = await fetch('/api/v1/upload/image', {
              method: 'POST',
              body: formData,
            });
            if (!res.ok) throw new Error(`Proxy error: ${res.status}`);
          } catch {
            res = await fetch(`${API_BASE_URL}/api/v1/upload/image`, {
              method: 'POST',
              body: formData,
            });
          }

          if (res.ok) {
            const data = await res.json();
            setUploadedImageInfo({ url: data.url, name: data.original_name || 'pasted-image' });
            setShowImageModal(true);
          } else {
            toast.error(language === 'tr' ? 'Görsel yüklenemedi' : 'Image upload failed');
          }
        } catch (error) {
          console.error('Paste image error:', error);
          toast.error(language === 'tr' ? 'Görsel yapıştırılamadı' : 'Failed to paste image');
        }
        return;
      }
    }
  }, [language]);

  const t = {
    title: { tr: 'Notlarım', en: 'My Notes', de: 'Meine Notizen' },
    notes: { tr: 'not', en: 'notes', de: 'Notizen' },
    newNote: { tr: 'Yeni Not', en: 'New Note', de: 'Neue Notiz' },
    newFolder: { tr: 'Yeni Klasör', en: 'New Folder', de: 'Neuer Ordner' },
    searchNotes: { tr: 'Not veya klasör ara...', en: 'Search notes or folders...', de: 'Notizen oder Ordner durchsuchen...' },
    all: { tr: 'Tümü', en: 'All', de: 'Alle' },
    emptyNote: { tr: 'Boş not', en: 'Empty note', de: 'Leere Notiz' },
    noNotes: { tr: 'Not bulunamadı', en: 'No notes found', de: 'Keine Notizen gefunden' },
    cancel: { tr: 'İptal', en: 'Cancel', de: 'Abbrechen' },
    save: { tr: 'Kaydet', en: 'Save', de: 'Speichern' },
    edit: { tr: 'Düzenle', en: 'Edit', de: 'Bearbeiten' },
    noNoteSelected: { tr: 'Not Seçilmedi', en: 'No Note Selected', de: 'Keine Notiz ausgewählt' },
    selectNote: { tr: 'Görüntülemek için bir not seçin veya yeni bir not oluşturun', en: 'Select a note to view or create a new one', de: 'Wählen Sie eine Notiz oder erstellen Sie eine neue' },
    writePlaceholder: { tr: 'Notunuzu buraya yazın...', en: 'Write your note here...', de: 'Schreiben Sie Ihre Notiz hier...' },
    emptyNoteHint: { tr: 'Bu not boş. Düzenlemek için düzenle butonuna tıklayın.', en: 'This note is empty. Click edit to add content.', de: 'Diese Notiz ist leer. Klicken Sie auf Bearbeiten.' },
    created: { tr: 'Oluşturulma:', en: 'Created:', de: 'Erstellt:' },
    updated: { tr: 'Güncelleme:', en: 'Updated:', de: 'Aktualisiert:' },
    pin: { tr: 'Sabitle', en: 'Pin', de: 'Anheften' },
    unpin: { tr: 'Sabitlemeyi Kaldır', en: 'Unpin', de: 'Lösen' },
    color: { tr: 'Renk', en: 'Color', de: 'Farbe' },
    home: { tr: 'Ana Dizin', en: 'Home', de: 'Startseite' },
    parentFolder: { tr: 'Üst Klasör', en: 'Parent Folder', de: 'Übergeordneter Ordner' },
    folderName: { tr: 'Klasör adı', en: 'Folder name', de: 'Ordnername' },
    create: { tr: 'Oluştur', en: 'Create', de: 'Erstellen' },
    delete: { tr: 'Sil', en: 'Delete', de: 'Löschen' },
    emptyFolder: { tr: 'Bu klasör boş', en: 'This folder is empty', de: 'Dieser Ordner ist leer' },
    emptyFolderHint: { tr: 'Yeni bir klasör veya not oluşturmak için yukarıdaki butonları kullanın.', en: 'Use the buttons above to create a new folder or note.', de: 'Verwenden Sie die Schaltflächen oben, um einen neuen Ordner oder eine Notiz zu erstellen.' },
    gridView: { tr: 'Izgara Görünümü', en: 'Grid View', de: 'Rasteransicht' },
    listView: { tr: 'Liste Görünümü', en: 'List View', de: 'Listenansicht' },
    selectIcon: { tr: 'İkon Seç', en: 'Select Icon', de: 'Symbol auswählen' },
    downloadNote: { tr: 'Notu İndir', en: 'Download Note', de: 'Notiz herunterladen' },
    downloadFolder: { tr: 'Klasörü İndir', en: 'Download Folder', de: 'Ordner herunterladen' },
    downloadAll: { tr: 'Tümünü İndir', en: 'Download All', de: 'Alle herunterladen' },
  };

  return (
    <div className={cn(
      "flex flex-col h-full",
      // Sayfa tam ekran modunda fixed overlay olarak göster
      isPageFullscreen && "fixed inset-0 z-50 bg-background"
    )}>
      {/* Header - Not tam ekran modunda gizle */}
      {!isNoteFullscreen && (
      <header className="flex items-center justify-between px-6 py-4 border-b border-border bg-card/50 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-yellow-500 to-orange-500 text-white">
            <StickyNote className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-semibold">{t.title[language]}</h1>
            <p className="text-xs text-muted-foreground">
              {notes.length} {t.notes[language]} • {folders.length} {language === 'tr' ? 'klasör' : language === 'de' ? 'Ordner' : 'folders'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* View Mode Toggle */}
          <div className="flex items-center bg-muted rounded-lg p-1">
            <button
              onClick={() => setViewMode('list')}
              className={cn(
                "p-2 rounded-md transition-colors",
                viewMode === 'list'
                  ? "bg-background shadow-sm text-primary-500"
                  : "text-muted-foreground hover:text-foreground"
              )}
              title={t.listView[language]}
            >
              <List className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('grid')}
              className={cn(
                "p-2 rounded-md transition-colors",
                viewMode === 'grid'
                  ? "bg-background shadow-sm text-primary-500"
                  : "text-muted-foreground hover:text-foreground"
              )}
              title={t.gridView[language]}
            >
              <Grid3X3 className="w-4 h-4" />
            </button>
          </div>

          {/* New Folder Button */}
          <button
            onClick={() => setShowNewFolderForm(true)}
            className="flex items-center gap-2 px-3 py-2 bg-muted hover:bg-accent rounded-xl transition-colors"
          >
            <FolderPlus className="w-4 h-4" />
            <span className="hidden sm:inline">{t.newFolder[language]}</span>
          </button>

          {/* New Note Button */}
          <button
            onClick={handleNewNote}
            className="flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-xl hover:bg-primary-600 transition-colors"
          >
            <Plus className="w-4 h-4" />
            {t.newNote[language]}
          </button>

          {/* Download All Button */}
          {notes.length > 0 && (
            <button
              onClick={handleDownloadAllNotes}
              className="flex items-center gap-2 px-3 py-2 bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl transition-colors"
              title={t.downloadAll[language]}
            >
              <Download className="w-4 h-4" />
              <span className="hidden sm:inline">{t.downloadAll[language]}</span>
            </button>
          )}

          {/* Premium Feature Buttons */}
          <div className="flex items-center gap-1 pl-2 border-l border-border">
            {/* Favorites */}
            <button
              onClick={() => setShowFavorites(!showFavorites)}
              className={cn(
                "p-2 rounded-lg transition-colors",
                showFavorites ? "bg-amber-500/20 text-amber-500" : "text-muted-foreground hover:text-foreground hover:bg-muted"
              )}
              title={language === 'tr' ? 'Favoriler' : 'Favorites'}
            >
              <Star className="w-4 h-4" />
            </button>

            {/* Archive */}
            <button
              onClick={() => setShowArchive(true)}
              className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
              title={language === 'tr' ? 'Arşiv' : 'Archive'}
            >
              <Archive className="w-4 h-4" />
            </button>

            {/* Trash */}
            <button
              onClick={() => setShowTrashPanel(true)}
              className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
              title={language === 'tr' ? 'Çöp Kutusu' : 'Trash'}
            >
              <Trash2 className="w-4 h-4" />
            </button>

            {/* Templates */}
            <button
              onClick={() => setShowTemplates(true)}
              className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
              title={language === 'tr' ? 'Şablonlar' : 'Templates'}
            >
              <LayoutTemplate className="w-4 h-4" />
            </button>

            {/* Import */}
            <button
              onClick={() => setShowImport(true)}
              className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
              title={language === 'tr' ? 'İçe Aktar' : 'Import'}
            >
              <Upload className="w-4 h-4" />
            </button>

            {/* Export */}
            <button
              onClick={() => setShowExport(true)}
              className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
              title={language === 'tr' ? 'Dışa Aktar' : 'Export'}
            >
              <Download className="w-4 h-4" />
            </button>

            {/* 🏆 Gamification / Achievements */}
            <button
              onClick={() => setShowGamification(true)}
              className="p-2 rounded-lg bg-gradient-to-r from-amber-100 to-orange-100 dark:from-amber-900/30 dark:to-orange-900/30 text-amber-600 dark:text-amber-400 hover:from-amber-200 hover:to-orange-200 dark:hover:from-amber-800/40 dark:hover:to-orange-800/40 transition-colors"
              title={language === 'tr' ? 'Başarılarım' : 'Achievements'}
            >
              <Trophy className="w-4 h-4" />
            </button>

            {/* 📊 Statistics Dashboard */}
            <button
              onClick={() => setShowStatsDashboard(true)}
              className="p-2 rounded-lg bg-gradient-to-r from-blue-100 to-cyan-100 dark:from-blue-900/30 dark:to-cyan-900/30 text-blue-600 dark:text-blue-400 hover:from-blue-200 hover:to-cyan-200 dark:hover:from-blue-800/40 dark:hover:to-cyan-800/40 transition-colors"
              title={language === 'tr' ? 'İstatistikler' : 'Statistics'}
            >
              <Flame className="w-4 h-4" />
            </button>

            {/* 🧘 Zen Mode */}
            <button
              onClick={() => setShowZenMode(true)}
              disabled={!selectedNote}
              className={cn(
                "p-2 rounded-lg transition-colors",
                selectedNote
                  ? "bg-gradient-to-r from-purple-100 to-indigo-100 dark:from-purple-900/30 dark:to-indigo-900/30 text-purple-600 dark:text-purple-400 hover:from-purple-200 hover:to-indigo-200"
                  : "opacity-50 cursor-not-allowed text-muted-foreground"
              )}
              title={language === 'tr' ? 'Zen Modu' : 'Zen Mode'}
            >
              <Sparkles className="w-4 h-4" />
            </button>

            {/* 🤖 AI Writing Assistant */}
            <button
              onClick={() => setShowAIAssistant(!showAIAssistant)}
              className={cn(
                "p-2 rounded-lg transition-colors",
                showAIAssistant
                  ? "bg-gradient-to-r from-green-500 to-emerald-500 text-white"
                  : "bg-gradient-to-r from-green-100 to-emerald-100 dark:from-green-900/30 dark:to-emerald-900/30 text-green-600 dark:text-green-400 hover:from-green-200 hover:to-emerald-200"
              )}
              title={language === 'tr' ? 'AI Yazma Asistanı' : 'AI Writing Assistant'}
            >
              <Brain className="w-4 h-4" />
            </button>

            {/* ⌨️ Keyboard Shortcuts */}
            <button
              onClick={() => setShowKeyboardShortcuts(true)}
              className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
              title={language === 'tr' ? 'Klavye Kısayolları (?)' : 'Keyboard Shortcuts (?)'}
            >
              <Keyboard className="w-4 h-4" />
            </button>

            {/* 🕐 Recent Notes */}
            <button
              onClick={() => setShowRecentNotes(!showRecentNotes)}
              className={cn(
                "p-2 rounded-lg transition-colors",
                showRecentNotes 
                  ? "bg-blue-500/20 text-blue-500" 
                  : "text-muted-foreground hover:text-foreground hover:bg-muted"
              )}
              title={language === 'tr' ? 'Son Erişilen Notlar' : 'Recent Notes'}
            >
              <History className="w-4 h-4" />
            </button>

            {/* 📅 Timeline Planner */}
            <button
              onClick={() => setShowTimelinePlanner(true)}
              className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-gradient-to-r hover:from-purple-500/20 hover:to-pink-500/20 transition-all group"
              title={language === 'tr' ? 'Takvim Planlayıcı' : 'Timeline Planner'}
            >
              <Calendar className="w-4 h-4 group-hover:text-purple-500 transition-colors" />
            </button>

            {/* Compact Streak Widget */}
            <GamificationWidget compact={true} />

            {/* Advanced Search */}
            <button
              onClick={() => setShowAdvancedSearch(!showAdvancedSearch)}
              className={cn(
                "p-2 rounded-lg transition-colors",
                showAdvancedSearch ? "bg-primary-500/20 text-primary-500" : "text-muted-foreground hover:text-foreground hover:bg-muted"
              )}
              title={language === 'tr' ? 'Gelişmiş Arama' : 'Advanced Search'}
            >
              <Filter className="w-4 h-4" />
            </button>

            {/* Sayfa Tam Ekran */}
            <button
              onClick={() => setIsPageFullscreen(!isPageFullscreen)}
              className={cn(
                "p-2 rounded-lg transition-colors",
                isPageFullscreen ? "bg-primary-500 text-white" : "text-muted-foreground hover:text-foreground hover:bg-muted"
              )}
              title={isPageFullscreen ? "Tam Ekrandan Çık (ESC)" : "Sayfa Tam Ekran"}
            >
              {isPageFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </header>
      )}

      {/* Pinned Notes Bar - Premium Feature */}
      {!isNoteFullscreen && (
        <PinnedNotesBar
          notes={notes}
          selectedNoteId={selectedNote?.id}
          language={language}
          onSelectNote={(note) => {
            setSelectedNote(note);
            setIsEditing(false);
          }}
          onUnpinNote={(note) => handleTogglePin(note)}
        />
      )}

      {/* Breadcrumb Navigation - Not tam ekran modunda gizle */}
      {!isNoteFullscreen && (
      <div className="px-6 py-3 border-b border-border bg-muted/30 flex items-center gap-2 overflow-x-auto">
        <button
          onClick={() => setCurrentFolderId(null)}
          className={cn(
            "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium whitespace-nowrap transition-all",
            !currentFolderId
              ? "bg-primary-500 text-white"
              : "bg-background hover:bg-accent text-foreground"
          )}
        >
          <Home className="w-4 h-4" />
          {t.home[language]}
        </button>

        {folderPath.map((folder, index) => (
          <div key={folder.id} className="flex items-center gap-2">
            <ChevronRight className="w-4 h-4 text-muted-foreground" />
            <button
              onClick={() => setCurrentFolderId(folder.id)}
              className={cn(
                "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium whitespace-nowrap transition-all",
                index === folderPath.length - 1
                  ? "bg-primary-500 text-white"
                  : "bg-background hover:bg-accent text-foreground"
              )}
            >
              <span>{folder.icon}</span>
              {folder.name}
            </button>
          </div>
        ))}

        {/* Go Up Button */}
        {currentFolderId && (
          <button
            onClick={handleNavigateUp}
            className="flex items-center gap-1.5 px-3 py-1.5 ml-auto bg-muted hover:bg-accent rounded-lg text-sm font-medium transition-colors"
          >
            <ChevronUp className="w-4 h-4" />
            {t.parentFolder[language]}
          </button>
        )}
      </div>
      )}

      {/* New Folder Form */}
      <AnimatePresence>
        {showNewFolderForm && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="border-b border-border bg-card/50 overflow-hidden"
          >
            <div className="px-6 py-4">
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <FolderPlus className="w-4 h-4" />
                {t.newFolder[language]}
              </h3>
              <div className="flex items-center gap-3">
                {/* Icon Picker */}
                <div className="relative">
                  <button
                    onClick={() => setShowFolderIconPicker(!showFolderIconPicker)}
                    className="w-12 h-12 flex items-center justify-center text-2xl bg-muted hover:bg-accent rounded-xl border-2 border-dashed border-border transition-colors"
                    title={t.selectIcon[language]}
                  >
                    {newFolderIcon}
                  </button>

                  {showFolderIconPicker && (
                    <div className="absolute left-0 top-full mt-2 p-2 bg-card border border-border rounded-xl shadow-lg z-50 grid grid-cols-5 gap-1">
                      {FOLDER_ICONS.map((item) => (
                        <button
                          key={item.id}
                          onClick={() => {
                            setNewFolderIcon(item.icon);
                            setShowFolderIconPicker(false);
                          }}
                          className={cn(
                            "w-10 h-10 flex items-center justify-center text-xl rounded-lg hover:bg-accent transition-colors",
                            newFolderIcon === item.icon && "bg-primary-100 dark:bg-primary-900/30 ring-2 ring-primary-500"
                          )}
                          title={item.name}
                        >
                          {item.icon}
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {/* Folder Name Input */}
                <input
                  type="text"
                  value={newFolderName}
                  onChange={(e) => setNewFolderName(e.target.value)}
                  placeholder={t.folderName[language]}
                  className="flex-1 px-4 py-2.5 bg-background border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/50"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleCreateFolder();
                    if (e.key === 'Escape') setShowNewFolderForm(false);
                  }}
                  autoFocus
                />

                {/* Action Buttons */}
                <button
                  onClick={handleCreateFolder}
                  disabled={!newFolderName.trim()}
                  className="flex items-center gap-2 px-4 py-2.5 bg-primary-500 text-white rounded-xl hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <Plus className="w-4 h-4" />
                  {t.create[language]}
                </button>
                <button
                  onClick={() => {
                    setShowNewFolderForm(false);
                    setNewFolderName('');
                    setNewFolderIcon('📁');
                  }}
                  className="p-2.5 text-muted-foreground hover:text-foreground hover:bg-accent rounded-xl transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex flex-1 overflow-hidden">
        {/* Sol Panel - Not Listesi (Not tam ekranda gizle) */}
        {!isNoteFullscreen && (
        <div className="w-80 border-r border-border flex flex-col bg-muted/30">
          {/* Arama - Premium Search */}
          <div className="p-4 border-b border-border">
            <div className="relative group">
              <div className="absolute inset-0 bg-gradient-to-r from-primary-500/10 to-purple-500/10 rounded-xl opacity-0 group-focus-within:opacity-100 blur-xl transition-opacity" />
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground group-focus-within:text-primary-500 transition-colors" />
              <input
                id="notes-search-input"
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={t.searchNotes[language]}
                className="relative w-full pl-10 pr-10 py-2.5 bg-background border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500/50 transition-all"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-0.5 rounded-full hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
            {/* Ctrl+F hint */}
            <p className="mt-1.5 text-[10px] text-muted-foreground flex items-center gap-1">
              <kbd className="px-1 py-0.5 bg-muted rounded text-[9px] font-mono">Ctrl+F</kbd>
              <span>{language === 'tr' ? 'ile hızlı ara' : language === 'de' ? 'zum schnellen Suchen' : 'to quick search'}</span>
            </p>
          </div>

          {/* Tags Filter */}
          {allTags.length > 0 && (
            <div className="px-4 py-2 border-b border-border">
              <div className="flex gap-1 flex-wrap">
                <button
                  onClick={() => setFilterByTag(null)}
                  className={cn(
                    "flex items-center gap-1 px-2 py-1 rounded-lg text-xs transition-all",
                    !filterByTag
                      ? "bg-green-500 text-white"
                      : "bg-muted hover:bg-accent text-muted-foreground"
                  )}
                >
                  <Tag className="w-3 h-3" />
                  {t.all[language]}
                </button>
                {allTags.map(tag => (
                  <button
                    key={tag}
                    onClick={() => setFilterByTag(tag)}
                    className={cn(
                      "flex items-center gap-1 px-2 py-1 rounded-lg text-xs transition-all",
                      filterByTag === tag
                        ? "bg-green-500 text-white"
                        : "bg-muted hover:bg-accent text-muted-foreground"
                    )}
                  >
                    #{tag}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Folders and Notes List */}
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {/* Subfolders */}
            <AnimatePresence mode="popLayout">
              {subFolders.map((folder) => (
                <motion.div
                  key={folder.id}
                  layout
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  whileHover={{ scale: 1.01, x: 2 }}
                  whileTap={{ scale: 0.99 }}
                  className="group"
                >
                  <div
                    className="flex items-center gap-3 p-3 rounded-xl bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border border-blue-200 dark:border-blue-800 cursor-pointer hover:shadow-lg hover:shadow-blue-500/10 transition-all backdrop-blur-sm"
                    onClick={() => setCurrentFolderId(folder.id)}
                  >
                    <span className="text-2xl">{folder.icon}</span>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm text-blue-700 dark:text-blue-300 truncate flex items-center gap-1">
                        {folder.isPinned && <Pin className="w-3 h-3 text-primary-500" />}
                        {folder.name}
                        {folder.isLocked && <Lock className="w-3 h-3 text-amber-500" />}
                      </p>
                      <p className="text-xs text-blue-500/70 dark:text-blue-400/70">
                        {getRecursiveNoteCount(folder.id)} {t.notes[language]}
                        {getDirectSubfolderCount(folder.id) > 0 && (
                          <span className="ml-1">• {getDirectSubfolderCount(folder.id)} {language === 'tr' ? 'klasör' : language === 'de' ? 'Ordner' : 'folders'}</span>
                        )}
                      </p>
                    </div>
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      {/* Pin Button */}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleToggleFolderPin(folder);
                        }}
                        className={cn(
                          "p-1.5 rounded-lg transition-colors",
                          folder.isPinned
                            ? "text-primary-500 bg-primary-100 dark:bg-primary-900/30"
                            : "text-muted-foreground hover:bg-accent"
                        )}
                        title={folder.isPinned 
                          ? (language === 'tr' ? 'Sabitlemeyi Kaldır' : language === 'de' ? 'Lösen' : 'Unpin')
                          : (language === 'tr' ? 'Sabitle' : language === 'de' ? 'Anheften' : 'Pin')
                        }
                      >
                        <Pin className="w-4 h-4" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDownloadFolder(folder.id);
                        }}
                        className="p-1.5 text-emerald-500 hover:bg-emerald-100 dark:hover:bg-emerald-900/30 rounded-lg transition-colors"
                        title={t.downloadFolder[language]}
                      >
                        <FolderDown className="w-4 h-4" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleToggleFolderLock(folder);
                        }}
                        className={cn(
                          "p-1.5 rounded-lg transition-colors",
                          folder.isLocked
                            ? "text-amber-500 bg-amber-100 dark:bg-amber-900/30"
                            : "text-muted-foreground hover:bg-accent"
                        )}
                        title={folder.isLocked 
                          ? (language === 'tr' ? 'Kilidi Kaldır' : language === 'de' ? 'Entsperren' : 'Unlock')
                          : (language === 'tr' ? 'Kilitle' : language === 'de' ? 'Sperren' : 'Lock')
                        }
                      >
                        {folder.isLocked ? <Lock className="w-4 h-4" /> : <Unlock className="w-4 h-4" />}
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteFolder(folder.id);
                        }}
                        className={cn(
                          "p-1.5 rounded-lg transition-colors",
                          folder.isLocked
                            ? "text-muted-foreground/50 cursor-not-allowed"
                            : "text-red-500 hover:bg-red-100 dark:hover:bg-red-900/30"
                        )}
                        disabled={folder.isLocked}
                        title={folder.isLocked ? (language === 'tr' ? 'Kilitli klasör silinemez' : 'Locked folder cannot be deleted') : t.delete[language]}
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>

            {/* Notes */}
            <AnimatePresence mode="popLayout">
              {viewMode === 'list' ? (
                // List View
                filteredNotes.map((note) => {
                  const colorClasses = getNoteColorClasses(note.color);
                  return (
                    <motion.button
                      key={note.id}
                      layout
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, scale: 0.95 }}
                      whileHover={{ scale: 1.01 }}
                      whileTap={{ scale: 0.99 }}
                      onClick={() => {
                        setSelectedNote(note);
                        setIsEditing(false);
                      }}
                      className={cn(
                        "w-full text-left p-3 rounded-xl transition-all group border backdrop-blur-sm",
                        "hover:shadow-lg hover:shadow-primary-500/5",
                        colorClasses.bg,
                        selectedNote?.id === note.id
                          ? "ring-2 ring-primary-500 shadow-md shadow-primary-500/10"
                          : colorClasses.border
                      )}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-1">
                            {note.isPinned && <Pin className="w-3 h-3 text-primary-500" />}
                            {note.isLocked && <Lock className="w-3 h-3 text-amber-500" />}
                            <p className="font-medium text-sm truncate">{note.title}</p>
                          </div>
                          <p className="text-xs text-muted-foreground truncate mt-1">
                            {note.content || t.emptyNote[language]}
                          </p>
                          <p className="text-[10px] text-muted-foreground mt-2">
                            {formatDate(note.updatedAt, language)}
                          </p>
                        </div>
                        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDownloadNote(note);
                            }}
                            className="p-1.5 text-emerald-500 hover:bg-emerald-100 dark:hover:bg-emerald-900/30 rounded-lg transition-colors"
                            title={t.downloadNote[language]}
                          >
                            <FileDown className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleTogglePin(note);
                            }}
                            className={cn(
                              "p-1.5 rounded-lg transition-colors",
                              note.isPinned
                                ? "text-primary-500 bg-primary-100 dark:bg-primary-900/30"
                                : "text-muted-foreground hover:bg-accent"
                            )}
                            title={note.isPinned ? t.unpin[language] : t.pin[language]}
                          >
                            <Pin className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleToggleNoteLock(note);
                            }}
                            className={cn(
                              "p-1.5 rounded-lg transition-colors",
                              note.isLocked
                                ? "text-amber-500 bg-amber-100 dark:bg-amber-900/30"
                                : "text-muted-foreground hover:bg-accent"
                            )}
                            title={note.isLocked 
                              ? (language === 'tr' ? 'Kilidi Kaldır' : language === 'de' ? 'Entsperren' : 'Unlock')
                              : (language === 'tr' ? 'Kilitle' : language === 'de' ? 'Sperren' : 'Lock')
                            }
                          >
                            {note.isLocked ? <Lock className="w-3.5 h-3.5" /> : <Unlock className="w-3.5 h-3.5" />}
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteNote(note);
                            }}
                            className={cn(
                              "p-1.5 rounded-lg transition-all",
                              note.isLocked
                                ? "text-muted-foreground/50 cursor-not-allowed"
                                : "text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                            )}
                            disabled={note.isLocked}
                            title={note.isLocked ? (language === 'tr' ? 'Kilitli not silinemez' : 'Locked note cannot be deleted') : undefined}
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    </motion.button>
                  );
                })
              ) : (
                // Grid View
                <div className="grid grid-cols-2 gap-2">
                  {filteredNotes.map((note) => {
                    const colorClasses = getNoteColorClasses(note.color);
                    return (
                      <motion.button
                        key={note.id}
                        layout
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.9 }}
                        whileHover={{ scale: 1.02, y: -2 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => {
                          setSelectedNote(note);
                          setIsEditing(false);
                        }}
                        className={cn(
                          "text-left p-3 rounded-xl transition-all group border aspect-square flex flex-col backdrop-blur-sm",
                          "hover:shadow-xl hover:shadow-primary-500/10",
                          colorClasses.bg,
                          selectedNote?.id === note.id
                            ? "ring-2 ring-primary-500 shadow-lg shadow-primary-500/15"
                            : colorClasses.border
                        )}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-1">
                            {note.isPinned && <Pin className="w-3 h-3 text-primary-500" />}
                            {note.isLocked && <Lock className="w-3 h-3 text-amber-500" />}
                          </div>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteNote(note);
                            }}
                            className={cn(
                              "p-1 rounded opacity-0 group-hover:opacity-100 transition-all",
                              note.isLocked
                                ? "text-muted-foreground/50 cursor-not-allowed"
                                : "text-muted-foreground hover:text-destructive"
                            )}
                            disabled={note.isLocked}
                          >
                            <Trash2 className="w-3 h-3" />
                          </button>
                        </div>
                        <p className="font-medium text-xs truncate">{note.title}</p>
                        <p className="text-[10px] text-muted-foreground line-clamp-3 mt-1 flex-1">
                          {note.content || t.emptyNote[language]}
                        </p>
                        <p className="text-[9px] text-muted-foreground mt-2">
                          {formatDate(note.updatedAt, language)}
                        </p>
                      </motion.button>
                    );
                  })}
                </div>
              )}
            </AnimatePresence>

            {/* Empty State - Premium */}
            {subFolders.length === 0 && filteredNotes.length === 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex flex-col items-center justify-center py-16 text-center"
              >
                {/* Animated Icon */}
                <motion.div
                  initial={{ scale: 0.8 }}
                  animate={{ scale: 1 }}
                  transition={{ type: "spring", stiffness: 200, damping: 15 }}
                  className="relative mb-6"
                >
                  <div className="absolute inset-0 bg-gradient-to-br from-primary-500/20 to-purple-500/20 rounded-full blur-2xl" />
                  <div className="relative w-24 h-24 rounded-full bg-gradient-to-br from-muted to-muted/50 flex items-center justify-center border border-border/50 shadow-inner">
                    <motion.div
                      animate={{ rotate: [0, 5, -5, 0] }}
                      transition={{ duration: 2, repeat: Infinity, repeatDelay: 3 }}
                    >
                      <FolderOpen className="w-12 h-12 text-muted-foreground/50" />
                    </motion.div>
                  </div>
                </motion.div>
                
                <h3 className="text-base font-semibold text-foreground mb-2">
                  {t.emptyFolder[language]}
                </h3>
                <p className="text-sm text-muted-foreground max-w-[280px] mb-6">
                  {t.emptyFolderHint[language]}
                </p>
                
                {/* Premium Action Buttons */}
                <div className="flex items-center gap-3">
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => setShowNewFolderForm(true)}
                    className="flex items-center gap-2 px-4 py-2 text-sm bg-muted hover:bg-accent rounded-xl border border-border/50 transition-all hover:shadow-md"
                  >
                    <FolderPlus className="w-4 h-4" />
                    {t.newFolder[language]}
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={handleNewNote}
                    className="flex items-center gap-2 px-4 py-2 text-sm bg-gradient-to-r from-primary-500 to-primary-600 text-white rounded-xl hover:from-primary-600 hover:to-primary-700 transition-all shadow-md hover:shadow-lg hover:shadow-primary-500/20"
                  >
                    <Plus className="w-4 h-4" />
                    {t.newNote[language]}
                  </motion.button>
                </div>
              </motion.div>
            )}
          </div>
        </div>
        )}

        {/* Sağ Panel - Not İçeriği */}
        <div className="flex-1 flex flex-col overflow-hidden bg-background">
          {selectedNote ? (
            <>
              {/* Not Başlığı */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-border">
                {isEditing ? (
                  <input
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    className="text-xl font-semibold bg-transparent border-b-2 border-primary-500 focus:outline-none flex-1 mr-4"
                    autoFocus
                  />
                ) : (
                  <div className="flex items-center gap-2">
                    {selectedNote.isPinned && <Pin className="w-5 h-5 text-primary-500" />}
                    {selectedNote.isLocked && <Lock className="w-5 h-5 text-amber-500" />}
                    <h2 className="text-xl font-semibold">{selectedNote.title}</h2>
                  </div>
                )}

                <div className="flex items-center gap-2">
                  {/* Color Picker */}
                  <div className="relative">
                    <button
                      onClick={() => setShowColorPicker(!showColorPicker)}
                      className="flex items-center gap-2 px-3 py-1.5 bg-muted hover:bg-accent rounded-lg transition-colors"
                      title={t.color[language]}
                    >
                      <Palette className="w-4 h-4" />
                    </button>
                    {showColorPicker && (
                      <div className="absolute right-0 top-full mt-2 p-2 bg-card border border-border rounded-xl shadow-lg z-50">
                        <div className="grid grid-cols-4 gap-2">
                          {NOTE_COLORS.map((c) => (
                            <button
                              key={c.id}
                              onClick={() => handleSetColor(selectedNote, c.id)}
                              className={cn(
                                "w-8 h-8 rounded-lg border-2 transition-all",
                                c.color,
                                c.border,
                                selectedNote.color === c.id && "ring-2 ring-primary-500"
                              )}
                              title={c[`name${language === 'tr' ? '' : language === 'en' ? 'En' : 'De'}` as keyof typeof c] as string}
                            />
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Pin Button */}
                  <button
                    onClick={() => handleTogglePin(selectedNote)}
                    className={cn(
                      "flex items-center gap-2 px-3 py-1.5 rounded-lg transition-colors",
                      selectedNote.isPinned
                        ? "bg-primary-500 text-white"
                        : "bg-muted hover:bg-accent"
                    )}
                    title={selectedNote.isPinned ? t.unpin[language] : t.pin[language]}
                  >
                    <Pin className="w-4 h-4" />
                  </button>

                  {/* Lock Button */}
                  <button
                    onClick={() => handleToggleNoteLock(selectedNote)}
                    className={cn(
                      "flex items-center gap-2 px-3 py-1.5 rounded-lg transition-colors",
                      selectedNote.isLocked
                        ? "bg-amber-500 text-white"
                        : "bg-muted hover:bg-accent"
                    )}
                    title={selectedNote.isLocked 
                      ? (language === 'tr' ? 'Kilidi Kaldır' : language === 'de' ? 'Entsperren' : 'Unlock')
                      : (language === 'tr' ? 'Kilitle' : language === 'de' ? 'Sperren' : 'Lock')
                    }
                  >
                    {selectedNote.isLocked ? <Lock className="w-4 h-4" /> : <Unlock className="w-4 h-4" />}
                  </button>

                  {/* Version History Button */}
                  <button
                    onClick={() => setShowVersionHistory(true)}
                    className="flex items-center gap-2 px-3 py-1.5 bg-muted hover:bg-accent rounded-lg transition-colors"
                    title={language === 'tr' ? 'Versiyon Geçmişi' : 'Version History'}
                  >
                    <History className="w-4 h-4" />
                  </button>

                  {/* Backlinks Button */}
                  <button
                    onClick={() => setShowBacklinks(true)}
                    className="flex items-center gap-2 px-3 py-1.5 bg-muted hover:bg-accent rounded-lg transition-colors"
                    title={language === 'tr' ? 'Bağlantılar' : 'Backlinks'}
                  >
                    <Link2 className="w-4 h-4" />
                  </button>

                  {/* 🧠 Smart Insights Button */}
                  <button
                    onClick={() => setShowSmartInsights(true)}
                    className="flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-purple-500 to-indigo-500 hover:from-purple-600 hover:to-indigo-600 text-white rounded-lg transition-colors shadow-sm"
                    title={language === 'tr' ? 'Akıllı Analiz' : 'Smart Insights'}
                  >
                    <Brain className="w-4 h-4" />
                  </button>

                  {/* ⏱️ Focus Mode Button */}
                  <button
                    onClick={() => setShowFocusMode(true)}
                    className="flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-rose-500 to-red-500 hover:from-rose-600 hover:to-red-600 text-white rounded-lg transition-colors shadow-sm"
                    title={language === 'tr' ? 'Odaklanma Modu' : 'Focus Mode'}
                  >
                    <Timer className="w-4 h-4" />
                  </button>

                  {/* Tag Button */}
                  <button
                    onClick={() => setShowTagInput(!showTagInput)}
                    className="flex items-center gap-2 px-3 py-1.5 bg-muted hover:bg-accent rounded-lg transition-colors"
                    title={language === 'tr' ? 'Etiket Ekle' : language === 'de' ? 'Tag hinzufügen' : 'Add Tag'}
                  >
                    <Tag className="w-4 h-4" />
                  </button>

                  {/* Download Note Button */}
                  <button
                    onClick={() => handleDownloadNote(selectedNote)}
                    className="flex items-center gap-2 px-3 py-1.5 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg transition-colors"
                    title={t.downloadNote[language]}
                  >
                    <FileDown className="w-4 h-4" />
                  </button>

                  {isEditing ? (
                    <>
                      <button
                        onClick={handleCancel}
                        className="flex items-center gap-2 px-3 py-1.5 text-muted-foreground hover:bg-accent rounded-lg transition-colors"
                      >
                        <X className="w-4 h-4" />
                        {t.cancel[language]}
                      </button>
                      <button
                        id="save-note-btn"
                        onClick={handleSave}
                        className="flex items-center gap-2 px-3 py-1.5 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
                      >
                        <Save className="w-4 h-4" />
                        {t.save[language]}
                      </button>
                    </>
                  ) : (
                    <button
                      onClick={() => handleEdit(selectedNote)}
                      className="flex items-center gap-2 px-3 py-1.5 bg-muted hover:bg-accent rounded-lg transition-colors"
                    >
                      <Edit3 className="w-4 h-4" />
                      {t.edit[language]}
                    </button>
                  )}

                  {/* Matematik Ekran Klavyesi */}
                  {isEditing && (
                    <button
                      onClick={() => setShowMathKeyboard(!showMathKeyboard)}
                      className={cn(
                        "flex items-center gap-2 px-3 py-1.5 rounded-lg transition-colors",
                        showMathKeyboard 
                          ? "bg-indigo-500 text-white" 
                          : "bg-muted hover:bg-accent"
                      )}
                      title="Matematik Klavyesi"
                    >
                      <Keyboard className="w-4 h-4" />
                    </button>
                  )}

                  {/* Not Detayı Tam Ekran */}
                  <button
                    onClick={() => setIsNoteFullscreen(!isNoteFullscreen)}
                    className={cn(
                      "flex items-center gap-2 px-3 py-1.5 rounded-lg transition-colors",
                      isNoteFullscreen 
                        ? "bg-primary-500 text-white" 
                        : "bg-muted hover:bg-accent"
                    )}
                    title={isNoteFullscreen ? "Tam Ekrandan Çık (ESC)" : "Not Tam Ekran"}
                  >
                    {isNoteFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Not İçeriği */}
              <div className={cn(
                "flex-1 overflow-y-auto flex flex-col",
                getNoteColorClasses(selectedNote.color).bg
              )}>
                {isEditing ? (
                  <div className="flex flex-col h-full">
                    {/* Rich Text Toolbar */}
                    <div className="flex items-center gap-1 px-4 py-2 border-b border-border/50 bg-background/50 backdrop-blur-sm flex-wrap">
                      <div className="flex items-center gap-0.5 pr-2 border-r border-border/50">
                        <button
                          id="toolbar-bold-btn"
                          onClick={() => {
                            const textarea = document.querySelector('textarea');
                            if (textarea) {
                              const start = textarea.selectionStart;
                              const end = textarea.selectionEnd;
                              const text = editContent;
                              const selectedText = text.substring(start, end);
                              setEditContent(text.substring(0, start) + `**${selectedText}**` + text.substring(end));
                            }
                          }}
                          className="p-2 hover:bg-accent rounded-lg transition-colors"
                          title={language === 'tr' ? 'Kalın' : 'Bold'}
                        >
                          <Bold className="w-4 h-4" />
                        </button>
                        <button
                          id="toolbar-italic-btn"
                          onClick={() => {
                            const textarea = document.querySelector('textarea');
                            if (textarea) {
                              const start = textarea.selectionStart;
                              const end = textarea.selectionEnd;
                              const text = editContent;
                              const selectedText = text.substring(start, end);
                              setEditContent(text.substring(0, start) + `*${selectedText}*` + text.substring(end));
                            }
                          }}
                          className="p-2 hover:bg-accent rounded-lg transition-colors"
                          title={language === 'tr' ? 'İtalik' : 'Italic'}
                        >
                          <Italic className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => {
                            const textarea = document.querySelector('textarea');
                            if (textarea) {
                              const start = textarea.selectionStart;
                              const end = textarea.selectionEnd;
                              const text = editContent;
                              const selectedText = text.substring(start, end);
                              setEditContent(text.substring(0, start) + `__${selectedText}__` + text.substring(end));
                            }
                          }}
                          className="p-2 hover:bg-accent rounded-lg transition-colors"
                          title={language === 'tr' ? 'Altı Çizili' : 'Underline'}
                        >
                          <Underline className="w-4 h-4" />
                        </button>
                      </div>

                      <div className="flex items-center gap-0.5 px-2 border-r border-border/50">
                        <button
                          onClick={() => setEditContent(editContent + '\n# ')}
                          className="p-2 hover:bg-accent rounded-lg transition-colors"
                          title={language === 'tr' ? 'Başlık 1' : 'Heading 1'}
                        >
                          <Heading1 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => setEditContent(editContent + '\n## ')}
                          className="p-2 hover:bg-accent rounded-lg transition-colors"
                          title={language === 'tr' ? 'Başlık 2' : 'Heading 2'}
                        >
                          <Heading2 className="w-4 h-4" />
                        </button>
                      </div>

                      <div className="flex items-center gap-0.5 px-2 border-r border-border/50">
                        <button
                          onClick={() => setEditContent(editContent + '\n- ')}
                          className="p-2 hover:bg-accent rounded-lg transition-colors"
                          title={language === 'tr' ? 'Liste' : 'List'}
                        >
                          <ListOrdered className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => setEditContent(editContent + '\n- [ ] ')}
                          className="p-2 hover:bg-accent rounded-lg transition-colors"
                          title={language === 'tr' ? 'Yapılacaklar' : 'Checklist'}
                        >
                          <ListTodo className="w-4 h-4" />
                        </button>
                      </div>

                      <div className="flex items-center gap-0.5 px-2 border-r border-border/50">
                        <button
                          onClick={() => setEditContent(editContent + '\n> ')}
                          className="p-2 hover:bg-accent rounded-lg transition-colors"
                          title={language === 'tr' ? 'Alıntı' : 'Quote'}
                        >
                          <Quote className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => {
                            const textarea = document.querySelector('textarea');
                            if (textarea) {
                              const start = textarea.selectionStart;
                              const end = textarea.selectionEnd;
                              const text = editContent;
                              const selectedText = text.substring(start, end);
                              setEditContent(text.substring(0, start) + `\`${selectedText}\`` + text.substring(end));
                            }
                          }}
                          className="p-2 hover:bg-accent rounded-lg transition-colors"
                          title={language === 'tr' ? 'Kod' : 'Code'}
                        >
                          <Code className="w-4 h-4" />
                        </button>
                      </div>

                      <div className="flex items-center gap-0.5 pl-2">
                        <button
                          onClick={() => {
                            const url = prompt(language === 'tr' ? 'Link URL:' : 'Link URL:');
                            if (url) {
                              const textarea = document.querySelector('textarea');
                              if (textarea) {
                                const start = textarea.selectionStart;
                                const end = textarea.selectionEnd;
                                const text = editContent;
                                const selectedText = text.substring(start, end) || 'link';
                                setEditContent(text.substring(0, start) + `[${selectedText}](${url})` + text.substring(end));
                              }
                            }
                          }}
                          className="p-2 hover:bg-accent rounded-lg transition-colors"
                          title={language === 'tr' ? 'Link Ekle' : 'Add Link'}
                        >
                          <Link2 className="w-4 h-4" />
                        </button>

                        {/* Image Upload Button */}
                        <div className="relative">
                          <input
                            type="file"
                            accept="image/*"
                            className="hidden"
                            id="image-upload"
                            onChange={async (e) => {
                              const file = e.target.files?.[0];
                              if (!file) return;

                              // Base64 Upload (Compressed & Optimized)
                              try {
                                const base64String = await compressImage(file);

                                const formData = new FormData();
                                formData.append('file', file);

                                let res;
                                try {
                                  // 1. Deneme: Proxy üzerinden (Standart)
                                  res = await fetch('/api/v1/upload/image', {
                                    method: 'POST',
                                    body: formData,
                                  });

                                  if (!res.ok) throw new Error(`Proxy error: ${res.status}`);
                                } catch (proxyError) {
                                  console.warn('Proxy upload failed, trying direct...', proxyError);
                                  // 2. Deneme: Doğrudan Backend'e (Fallback)
                                  try {
                                    res = await fetch(`${API_BASE_URL}/api/v1/upload/image`, {
                                      method: 'POST',
                                      body: formData,
                                    });
                                  } catch (directError) {
                                    throw new Error(`CONNECTION_REFUSED: Backend sunucusuna ulaşılamıyor. (Port 8001 açık mı?)`);
                                  }
                                }

                                if (res.ok) {
                                  const data = await res.json();
                                  setUploadedImageInfo({ url: data.url, name: data.original_name });
                                  setShowImageModal(true);
                                } else {
                                  const status = res.status;
                                  const rawText = await res.text();
                                  let errorMessage = rawText;
                                  try {
                                    const parsed = JSON.parse(rawText);
                                    errorMessage = parsed.detail || parsed.message || JSON.stringify(parsed);
                                  } catch (e) {
                                    if (rawText.length > 200) errorMessage = rawText.substring(0, 200) + '...';
                                  }

                                  toast.error(language === 'tr'
                                    ? `Görsel yüklenemedi: ${errorMessage} (Kod: ${status})`
                                    : `Image upload failed: ${errorMessage} (Code: ${status})`);
                                }
                              } catch (error) {
                                console.error('Image upload error:', error);
                                toast.error(language === 'tr' ? `Bir hata oluştu: ${error}` : `An error occurred: ${error}`);
                              }

                              e.target.value = '';
                            }}

                          />
                          <button
                            onClick={() => document.getElementById('image-upload')?.click()}
                            className="p-2 hover:bg-accent rounded-lg transition-colors"
                            title={language === 'tr' ? 'Görsel Ekle' : 'Add Image'}
                          >
                            <ImageIcon className="w-4 h-4" />
                          </button>
                        </div>

                        {/* File Attachment Button */}
                        <button
                          onClick={() => setShowAttachmentUploader(true)}
                          className="p-2 hover:bg-accent rounded-lg transition-colors"
                          title={language === 'tr' ? 'Dosya Ekle' : 'Add File'}
                        >
                          <Paperclip className="w-4 h-4" />
                        </button>

                        {/* Attachment Count Badge */}
                        {noteAttachments.length > 0 && (
                          <span className="px-1.5 py-0.5 bg-primary-500/20 text-primary-600 text-xs font-medium rounded-full">
                            {noteAttachments.length}
                          </span>
                        )}
                      </div>

                      <div className="flex-1" />

                      <div className="flex items-center gap-1 px-2 py-1 bg-primary-500/10 rounded-lg">
                        <Sparkles className="w-3.5 h-3.5 text-primary-500" />
                        <span className="text-xs font-medium text-primary-600">Premium Editor</span>
                      </div>
                    </div>

                    {/* Editor Area */}
                    <div className="flex-1 p-6 flex flex-col gap-4">
                      <textarea
                        id="note-editor-textarea"
                        value={editContent}
                        onChange={(e) => setEditContent(e.target.value)}
                        onPaste={handlePaste}
                        placeholder={t.writePlaceholder[language]}
                        className="w-full flex-1 resize-none bg-transparent focus:outline-none text-foreground placeholder:text-muted-foreground leading-relaxed font-mono text-sm"
                        style={{ minHeight: showMathKeyboard ? '200px' : '300px' }}
                      />
                      
                      {/* Editor Footer - Word Counter & Auto Save */}
                      <div className="flex items-center justify-between px-2 py-1.5 border-t border-border/50 bg-muted/20 rounded-lg">
                        <WordCounter content={editContent} variant="detailed" />
                        <AutoSaveIndicator 
                          content={editContent} 
                          onSave={async (content) => {
                            if (selectedNote) {
                              try {
                                await fetch(`/api/notes/${selectedNote.id}`, {
                                  method: 'PUT',
                                  headers: { 'Content-Type': 'application/json' },
                                  body: JSON.stringify({ title: editTitle, content })
                                });
                              } catch (e) {
                                console.error('Auto-save failed:', e);
                                throw e;
                              }
                            }
                          }}
                          delay={3000}
                          enabled={isEditing && !!selectedNote}
                        />
                      </div>
                      
                      {/* Matematik Ekran Klavyesi */}
                      {showMathKeyboard && (
                        <div className="border border-border rounded-xl bg-card shadow-lg overflow-hidden">
                          {/* Klavye Tipi Seçici (Math / Normal) */}
                          <div className="flex items-center gap-2 p-2 bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-950/30 dark:to-purple-950/30 border-b border-border">
                            <div className="flex bg-background rounded-lg p-0.5 shadow-inner">
                              <button
                                onClick={() => setKeyboardType('math')}
                                className={cn(
                                  "px-3 py-1.5 text-xs font-medium rounded-md transition-all flex items-center gap-1.5",
                                  keyboardType === 'math' 
                                    ? "bg-indigo-500 text-white shadow-sm" 
                                    : "text-muted-foreground hover:text-foreground"
                                )}
                              >
                                <Calculator className="w-3.5 h-3.5" />
                                Matematik
                              </button>
                              <button
                                onClick={() => setKeyboardType('normal')}
                                className={cn(
                                  "px-3 py-1.5 text-xs font-medium rounded-md transition-all flex items-center gap-1.5",
                                  keyboardType === 'normal' 
                                    ? "bg-purple-500 text-white shadow-sm" 
                                    : "text-muted-foreground hover:text-foreground"
                                )}
                              >
                                <Keyboard className="w-3.5 h-3.5" />
                                Normal
                              </button>
                            </div>
                            <span className="ml-auto text-xs text-muted-foreground">
                              {keyboardType === 'math' ? '600+ sembol' : '200+ karakter'}
                            </span>
                          </div>
                          
                          {/* Kategori Seçicileri */}
                          <div className="flex flex-wrap gap-1 p-2 bg-muted/50 border-b border-border overflow-x-auto">
                            {(keyboardType === 'math' ? MATH_KEYBOARD_CATEGORIES : NORMAL_KEYBOARD_CATEGORIES).map((cat) => (
                              <button
                                key={cat.id}
                                onClick={() => setMathCategory(cat.id)}
                                className={cn(
                                  "px-3 py-1.5 text-xs font-medium rounded-lg transition-all whitespace-nowrap flex items-center gap-1",
                                  mathCategory === cat.id 
                                    ? keyboardType === 'math' 
                                      ? "bg-indigo-500 text-white shadow-sm" 
                                      : "bg-purple-500 text-white shadow-sm"
                                    : "bg-background hover:bg-accent text-foreground"
                                )}
                              >
                                <span>{cat.icon}</span>
                                {cat.name}
                              </button>
                            ))}
                          </div>
                          
                          {/* Semboller */}
                          <div className="p-3 max-h-48 overflow-y-auto">
                            <div className="flex flex-wrap gap-1.5">
                              {(keyboardType === 'math' ? MATH_KEYBOARD_CATEGORIES : NORMAL_KEYBOARD_CATEGORIES)
                                .find(c => c.id === mathCategory)?.symbols.map((sym, idx) => (
                                <button
                                  key={idx}
                                  onClick={() => {
                                    const textarea = document.getElementById('note-editor-textarea') as HTMLTextAreaElement;
                                    if (textarea) {
                                      const start = textarea.selectionStart;
                                      const end = textarea.selectionEnd;
                                      const text = editContent;
                                      const newContent = text.substring(0, start) + sym.s + text.substring(end);
                                      setEditContent(newContent);
                                      // Cursor'ı sembolün sonrasına taşı
                                      setTimeout(() => {
                                        textarea.focus();
                                        textarea.setSelectionRange(start + sym.s.length, start + sym.s.length);
                                      }, 0);
                                    }
                                  }}
                                  className={cn(
                                    "min-w-[40px] h-10 px-2 flex items-center justify-center border border-border rounded-lg text-base font-mono transition-all hover:scale-105 hover:shadow-sm",
                                    keyboardType === 'math' 
                                      ? "bg-background hover:bg-indigo-100 dark:hover:bg-indigo-900/30" 
                                      : "bg-background hover:bg-purple-100 dark:hover:bg-purple-900/30"
                                  )}
                                  title={sym.d}
                                >
                                  {sym.s}
                                </button>
                              ))}
                            </div>
                          </div>
                          
                          {/* Footer */}
                          <div className="px-3 py-2 bg-muted/30 border-t border-border flex items-center justify-between text-xs text-muted-foreground">
                            <span className="flex items-center gap-1.5">
                              {keyboardType === 'math' ? <Calculator className="w-3.5 h-3.5" /> : <Keyboard className="w-3.5 h-3.5" />}
                              {(keyboardType === 'math' ? MATH_KEYBOARD_CATEGORIES : NORMAL_KEYBOARD_CATEGORIES)
                                .find(c => c.id === mathCategory)?.symbols.length || 0} sembol
                            </span>
                            <span>Tıklayarak ekleyin</span>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Editor Footer */}
                    <div className="px-4 py-2 border-t border-border/50 bg-muted/30 flex items-center justify-between">
                      <div className="flex items-center gap-4 text-xs text-muted-foreground">
                        <span>{editContent.length} {language === 'tr' ? 'karakter' : 'characters'}</span>
                        <span>{editContent.split(/\s+/).filter(Boolean).length} {language === 'tr' ? 'kelime' : 'words'}</span>
                        <span>{editContent.split('\n').length} {language === 'tr' ? 'satır' : 'lines'}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-muted-foreground">Markdown {language === 'tr' ? 'desteklenir' : 'supported'}</span>
                        <FileText className="w-3.5 h-3.5 text-muted-foreground" />
                      </div>
                    </div>

                    {/* Attachments List */}
                    {noteAttachments.length > 0 && (
                      <div className="border-t border-border">
                        <AttachmentsList
                          attachments={noteAttachments}
                          onPreview={(attachment) => {
                            setPreviewAttachment(attachment);
                            setShowFilePreview(true);
                          }}
                          onDelete={async (attachment) => {
                            try {
                              await fetch(`${API_BASE_URL}/api/v1/upload/file/${attachment.id}`, {
                                method: 'DELETE',
                              });
                              setNoteAttachments(prev => prev.filter(a => a.id !== attachment.id));
                              toast.success(language === 'tr' ? 'Dosya silindi' : 'File deleted');
                            } catch (error) {
                              toast.error(language === 'tr' ? 'Dosya silinemedi' : 'Failed to delete file');
                            }
                          }}
                          language={language}
                        />
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="prose prose-sm max-w-none dark:prose-invert p-6">
                    {selectedNote.content ? (
                      <WikiContentRenderer
                        content={selectedNote.content}
                        notes={notes}
                        onNavigate={(noteId) => {
                          const note = notes.find(n => n.id === noteId);
                          if (note) {
                            setSelectedNote(note);
                          }
                        }}
                        onImageEdit={handleImageEdit}
                        onImageUpdate={handleInlineImageUpdate}
                      />
                    ) : (
                      <p className="text-muted-foreground italic">
                        {t.emptyNoteHint[language]}
                      </p>
                    )}
                    
                    {/* Attachments List (View Mode) */}
                    {noteAttachments.length > 0 && (
                      <div className="mt-4 pt-4 border-t border-border">
                        <AttachmentsList
                          attachments={noteAttachments}
                          onPreview={(attachment) => {
                            setPreviewAttachment(attachment);
                            setShowFilePreview(true);
                          }}
                          onDelete={async (attachment) => {
                            try {
                              await fetch(`${API_BASE_URL}/api/v1/upload/file/${attachment.id}`, {
                                method: 'DELETE',
                              });
                              setNoteAttachments(prev => prev.filter(a => a.id !== attachment.id));
                              toast.success(language === 'tr' ? 'Dosya silindi' : 'File deleted');
                            } catch (error) {
                              toast.error(language === 'tr' ? 'Dosya silinemedi' : 'Failed to delete file');
                            }
                          }}
                          language={language}
                        />
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* AI Toolbar - Premium AI özellikleri */}
              {selectedNote && !isEditing && (
                <NoteAIToolbar
                  noteId={selectedNote.id}
                  noteTitle={selectedNote.title}
                  noteContent={selectedNote.content}
                  language={language}
                  onApplyTags={(tags) => {
                    tags.forEach(tag => addNoteTag(selectedNote.id, tag));
                    setSelectedNote(prev => prev ? { ...prev, tags: [...(prev.tags || []), ...tags] } : null);
                  }}
                  onApplySuggestion={(content) => {
                    updateNote(selectedNote.id, { content });
                    setSelectedNote(prev => prev ? { ...prev, content } : null);
                  }}
                />
              )}

              {/* Not Metadata */}
              <div className="px-6 py-3 border-t border-border bg-muted/30">
                {/* Tags */}
                <div className="flex flex-wrap gap-2 mb-2">
                  {(selectedNote.tags || []).map(tag => (
                    <span
                      key={tag}
                      className="inline-flex items-center gap-1 px-2 py-0.5 bg-green-500/10 text-green-600 text-xs rounded-lg"
                    >
                      #{tag}
                      <button
                        onClick={() => handleRemoveTag(tag)}
                        className="ml-1 text-green-600 hover:text-red-500 transition-colors"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                  {showTagInput && (
                    <div className="flex items-center gap-1">
                      <input
                        type="text"
                        value={tagInput}
                        onChange={(e) => setTagInput(e.target.value)}
                        placeholder={language === 'tr' ? 'Etiket...' : language === 'de' ? 'Tag...' : 'Tag...'}
                        className="w-20 px-2 py-0.5 border border-border rounded text-xs bg-background focus:outline-none focus:ring-1 focus:ring-primary-500"
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') handleAddTag();
                          if (e.key === 'Escape') setShowTagInput(false);
                        }}
                        autoFocus
                      />
                      <button
                        onClick={handleAddTag}
                        className="p-1 text-green-500 hover:bg-green-500/10 rounded"
                      >
                        <Plus className="w-3 h-3" />
                      </button>
                    </div>
                  )}
                </div>
                <div className="text-xs text-muted-foreground">
                  <span>{t.created[language]} {formatDate(selectedNote.createdAt, language)}</span>
                  <span className="mx-2">•</span>
                  <span>{t.updated[language]} {formatDate(selectedNote.updatedAt, language)}</span>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-muted-foreground">
              <StickyNote className="w-16 h-16 mb-4 opacity-50" />
              <p className="text-lg font-medium">{t.noNoteSelected[language]}</p>
              <p className="text-sm mt-1">{t.selectNote[language]}</p>
              <button
                onClick={handleNewNote}
                className="flex items-center gap-2 px-4 py-2 mt-4 bg-primary-500 text-white rounded-xl hover:bg-primary-600 transition-colors"
              >
                <Plus className="w-4 h-4" />
                {t.newNote[language]}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Premium Features - Modals & Panels */}

      {/* ==================== PREMIUM WOW FEATURES ==================== */}
      
      {/* Smart Insights Panel */}
      <SmartInsightsPanel
        noteId={selectedNote?.id || ''}
        noteTitle={selectedNote?.title}
        isOpen={showSmartInsights}
        onClose={() => setShowSmartInsights(false)}
      />

      {/* Focus Mode / Pomodoro Panel */}
      <FocusModePanel
        isOpen={showFocusMode}
        onClose={() => setShowFocusMode(false)}
        noteId={selectedNote?.id}
        noteName={selectedNote?.title}
        onSessionComplete={(words) => {
          toast.success('🎉 Pomodoro tamamlandı!');
        }}
      />

      {/* Gamification Sidebar */}
      <AnimatePresence>
        {showGamification && (
          <motion.div
            initial={{ x: 400, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 400, opacity: 0 }}
            className="fixed inset-y-0 right-0 w-96 bg-white dark:bg-gray-900 shadow-2xl z-50 flex flex-col border-l border-gray-200 dark:border-gray-700 overflow-y-auto"
          >
            <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-amber-500 to-orange-600">
              <div className="flex items-center gap-2 text-white">
                <Trophy className="w-6 h-6" />
                <span className="font-semibold">Başarılarım</span>
              </div>
              <button
                onClick={() => setShowGamification(false)}
                className="p-1.5 hover:bg-white/20 rounded-lg text-white transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="p-4">
              <GamificationWidget 
                showDigest={true} 
                onNoteClick={(noteId) => {
                  const note = notes.find(n => n.id === noteId);
                  if (note) {
                    setSelectedNote(note);
                    setShowGamification(false);
                  }
                }}
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Advanced Search Panel */}
      <AnimatePresence>
        {showAdvancedSearch && (
          <AdvancedSearchPanel
            notes={notes}
            folders={folders}
            allTags={allTags}
            onSelectNote={(note) => {
              setSelectedNote(note);
              setShowAdvancedSearch(false);
            }}
            onClose={() => setShowAdvancedSearch(false)}
            language={language}
          />
        )}
      </AnimatePresence>

      {/* Archive View */}
      <AnimatePresence>
        {showArchive && (
          <ArchiveView
            archivedNotes={archivedNotes}
            onRestore={(noteId) => {
              const note = archivedNotes.find(n => n.id === noteId);
              if (note) {
                addNote(note);
                setArchivedNotes(prev => prev.filter(n => n.id !== noteId));
              }
            }}
            onPermanentDelete={(noteId) => {
              setArchivedNotes(prev => prev.filter(n => n.id !== noteId));
            }}
            onClose={() => setShowArchive(false)}
            language={language}
          />
        )}
      </AnimatePresence>

      {/* Template Selector */}
      <AnimatePresence>
        {showTemplates && (
          <TemplateSelector
            onSelect={(content, title) => {
              const newNote: Note = {
                id: generateId(),
                title,
                content,
                folder: currentFolderId || undefined,
                color: 'default',
                isPinned: false,
                createdAt: new Date(),
                updatedAt: new Date()
              };
              addNote(newNote);
              setSelectedNote(newNote);
              setEditTitle(title);
              setEditContent(content);
              setIsEditing(true);
            }}
            onClose={() => setShowTemplates(false)}
            language={language}
          />
        )}
      </AnimatePresence>

      {/* Export Modal */}
      <AnimatePresence>
        {showExport && (
          <ExportModal
            notes={notes}
            folders={folders}
            selectedNotes={multiSelect.selectedItems}
            onClose={() => setShowExport(false)}
            language={language}
          />
        )}
      </AnimatePresence>

      {/* Import Wizard */}
      <AnimatePresence>
        {showImport && (
          <ImportWizard
            onImport={(importedNotes, importedFolders) => {
              // Add imported folders
              importedFolders.forEach(folder => {
                addFolder({
                  id: generateId(),
                  name: folder.name,
                  icon: '📁',
                  parentId: null,
                  color: 'blue',
                  createdAt: new Date()
                });
              });
              // Add imported notes
              importedNotes.forEach(note => {
                addNote({
                  id: generateId(),
                  title: note.title,
                  content: note.content,
                  folder: undefined,
                  color: 'default',
                  isPinned: false,
                  tags: note.tags || [],
                  createdAt: note.createdAt || new Date(),
                  updatedAt: new Date()
                });
              });
            }}
            onClose={() => setShowImport(false)}
            language={language}
          />
        )}
      </AnimatePresence>

      {/* Backlinks Panel */}
      <AnimatePresence>
        {showBacklinks && selectedNote && (
          <BacklinksPanel
            note={selectedNote}
            notes={notes}
            onNavigate={(noteId) => {
              const note = notes.find(n => n.id === noteId);
              if (note) {
                setSelectedNote(note);
                // Add to recent
                setRecentNoteIds(prev => [noteId, ...prev.filter(id => id !== noteId)].slice(0, 20));
              }
            }}
            onClose={() => setShowBacklinks(false)}
            language={language}
          />
        )}
      </AnimatePresence>

      {/* Bulk Action Toolbar */}
      {
        multiSelect.hasSelection && (
          <BulkActionToolbar
            selectedCount={multiSelect.selectionCount}
            onDelete={() => {
              multiSelect.selectedItems.forEach(note => deleteNote(note.id));
              multiSelect.clearSelection();
            }}
            onMove={() => {
              setShowMoveModal(true);
            }}
            onArchive={() => {
              multiSelect.selectedItems.forEach(note => {
                setArchivedNotes(prev => [...prev, note]);
                deleteNote(note.id);
              });
              multiSelect.clearSelection();
            }}
            onChangeColor={(color) => {
              multiSelect.selectedItems.forEach(note => updateNote(note.id, { color }));
              multiSelect.clearSelection();
            }}
            onAddTag={(tag) => {
              multiSelect.selectedItems.forEach(note => addNoteTag(note.id, tag));
              multiSelect.clearSelection();
            }}
            onTogglePin={() => {
              multiSelect.selectedItems.forEach(note => updateNote(note.id, { isPinned: !note.isPinned }));
              multiSelect.clearSelection();
            }}
            onExport={() => {
              setShowExport(true);
            }}
            onClear={() => multiSelect.clearSelection()}
            language={language}
          />
        )
      }

      {/* Move Modal */}
      <AnimatePresence>
        {showMoveModal && multiSelect.hasSelection && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4"
            onClick={() => setShowMoveModal(false)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="w-full max-w-md bg-card border border-border rounded-2xl shadow-2xl overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="px-6 py-4 border-b border-border bg-gradient-to-r from-blue-500/10 to-indigo-500/10">
                <h3 className="font-semibold text-lg">
                  {language === 'tr' ? 'Notları Taşı' : 'Move Notes'}
                </h3>
                <p className="text-xs text-muted-foreground mt-1">
                  {multiSelect.selectionCount} {language === 'tr' ? 'not seçili' : 'notes selected'}
                </p>
              </div>
              <div className="p-4 max-h-80 overflow-y-auto space-y-2">
                {/* Root folder option */}
                <button
                  onClick={() => {
                    multiSelect.selectedItems.forEach(note => {
                      updateNote(note.id, { folder: undefined });
                    });
                    multiSelect.clearSelection();
                    setShowMoveModal(false);
                  }}
                  className="w-full p-3 flex items-center gap-3 bg-muted/50 hover:bg-accent rounded-xl transition-colors text-left"
                >
                  <Home className="w-5 h-5 text-muted-foreground" />
                  <span className="font-medium">{language === 'tr' ? 'Ana Dizin' : 'Root'}</span>
                </button>
                
                {/* Folder options */}
                {folders.map((folder) => (
                  <button
                    key={folder.id}
                    onClick={() => {
                      multiSelect.selectedItems.forEach(note => {
                        updateNote(note.id, { folder: folder.id });
                      });
                      multiSelect.clearSelection();
                      setShowMoveModal(false);
                    }}
                    className="w-full p-3 flex items-center gap-3 bg-muted/50 hover:bg-accent rounded-xl transition-colors text-left"
                  >
                    <FolderOpen className="w-5 h-5 text-amber-500" />
                    <span className="font-medium">{folder.name}</span>
                    {folder.isLocked && <Lock className="w-3 h-3 text-amber-500 ml-auto" />}
                  </button>
                ))}
                
                {folders.length === 0 && (
                  <p className="text-center text-muted-foreground text-sm py-4">
                    {language === 'tr' ? 'Henüz klasör yok' : 'No folders yet'}
                  </p>
                )}
              </div>
              <div className="px-6 py-4 border-t border-border bg-muted/30">
                <button
                  onClick={() => setShowMoveModal(false)}
                  className="w-full py-2 bg-muted hover:bg-accent rounded-lg transition-colors font-medium"
                >
                  {language === 'tr' ? 'İptal' : 'Cancel'}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Image Settings Modal */}
      {uploadedImageInfo && (
        <ImageSettingsModal
          isOpen={showImageModal}
          onClose={() => {
            setShowImageModal(false);
            setUploadedImageInfo(null);
            setEditingImageInfo(null);
          }}
          onConfirm={editingImageInfo ? handleImageUpdate : handleImageConfirm}
          imageUrl={uploadedImageInfo.url}
          imageName={uploadedImageInfo.name}
          isEditMode={!!editingImageInfo}
          initialSettings={editingImageInfo ? {
            size: (editingImageInfo.options.size as ImageSettings['size']) || 'medium',
            align: (editingImageInfo.options.align as ImageSettings['align']) || 'center',
            shape: (editingImageInfo.options.shape as ImageSettings['shape']) || 'rounded',
            caption: editingImageInfo.alt,
            showCaption: editingImageInfo.options.showCaption !== 'false'
          } : undefined}
        />
      )}

      {/* File Attachment Uploader Modal */}
      {showAttachmentUploader && selectedNote && (
        <AttachmentUploader
          noteId={selectedNote.id}
          onUploadComplete={(attachment) => {
            setNoteAttachments(prev => [...prev, attachment]);
            toast.success(language === 'tr' ? 'Dosya eklendi' : 'File attached');
          }}
          onClose={() => setShowAttachmentUploader(false)}
          onError={(message) => toast.error(message)}
          language={language}
        />
      )}

      {/* File Preview Modal */}
      <FilePreviewModal
        isOpen={showFilePreview}
        onClose={() => {
          setShowFilePreview(false);
          setPreviewAttachment(null);
        }}
        attachment={previewAttachment}
        language={language}
      />

      {/* Trash Panel */}
      <TrashPanel
        isOpen={showTrashPanel}
        onClose={() => setShowTrashPanel(false)}
        onNoteRestored={(noteId) => {
          // Refresh notes from backend
          fetch('/api/notes')
            .then(res => res.json())
            .then(data => {
              if (data.notes) {
                data.notes.forEach((n: any) => {
                  const mapped = mapNoteFromApi(n);
                  if (!notes.find(existing => existing.id === mapped.id)) {
                    addNote(mapped);
                  }
                });
              }
            });
        }}
      />

      {/* Version History Panel */}
      {showVersionHistory && selectedNote && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-2xl h-[80vh] bg-card rounded-2xl shadow-2xl overflow-hidden">
            <VersionHistoryPanel
              note={selectedNote}
              versions={noteVersions.map(v => ({
                id: v.id,
                noteId: v.note_id,
                title: v.title,
                content: v.content,
                timestamp: new Date(v.created_at),
                changeType: 'edit' as const
              }))}
              onClose={() => setShowVersionHistory(false)}
              onRestore={(version) => {
                updateNote(selectedNote.id, { content: version.content });
                setSelectedNote(prev => prev ? { ...prev, content: version.content } : null);
                setEditContent(version.content);
                setShowVersionHistory(false);
              }}
              language={language}
            />
          </div>
        </div>
      )}

      {/* Quick Actions Panel (Cmd+K) */}
      <QuickActionsPanel
        isOpen={showQuickActions}
        onClose={() => setShowQuickActions(false)}
        currentNote={selectedNote}
        onAction={(actionId) => {
          switch (actionId) {
            case 'open-quick-actions':
              setShowQuickActions(true);
              break;
            case 'new-note':
              handleNewNote();
              break;
            case 'save-note':
              if (selectedNote) handleSave();
              break;
            case 'delete-note':
              if (selectedNote) handleDeleteNote(selectedNote);
              break;
            case 'pin-note':
              if (selectedNote) handleTogglePin(selectedNote);
              break;
            case 'zen-mode':
              if (selectedNote) setShowZenMode(true);
              break;
            case 'focus-mode':
              setShowFocusMode(true);
              break;
            case 'smart-insights':
              setShowSmartInsights(true);
              break;
            case 'pomodoro':
              setShowFocusMode(true);
              break;
            case 'toggle-sidebar':
              // Toggle sidebar visibility
              break;
            default:
              console.log('Action:', actionId);
          }
          setShowQuickActions(false);
        }}
      />

      {/* Zen Mode - Distraction Free Writing */}
      <ZenMode
        isOpen={showZenMode}
        onClose={() => setShowZenMode(false)}
        initialContent={selectedNote?.content || ''}
        initialTitle={selectedNote?.title || ''}
        onSave={async (content, title) => {
          if (selectedNote) {
            updateNote(selectedNote.id, { content, title });
            setSelectedNote({ ...selectedNote, content, title });
            setEditContent(content);
            setEditTitle(title);
            try {
              await fetch(`/api/notes/${selectedNote.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content, title })
              });
              toast.success('Not kaydedildi!');
            } catch (e) {
              console.error('Zen save failed:', e);
            }
          }
        }}
      />

      {/* AI Writing Assistant */}
      <AIWritingAssistant
        isOpen={showAIAssistant}
        onClose={() => setShowAIAssistant(false)}
        currentText={editContent}
        selectedText={selectedTextForAI}
        noteId={selectedNote?.id}
        onApplySuggestion={(text) => {
          setEditContent(text);
          toast.success('Öneri uygulandı!');
        }}
      />

      {/* Statistics Dashboard */}
      <StatsDashboard
        isOpen={showStatsDashboard}
        onClose={() => setShowStatsDashboard(false)}
        noteCount={notes.length}
        folderCount={folders.length}
      />

      {/* Keyboard Shortcuts Panel */}
      <KeyboardShortcutsPanel
        isOpen={showKeyboardShortcuts}
        onClose={() => setShowKeyboardShortcuts(false)}
      />

      {/* Timeline Planner Modal */}
      <AnimatePresence>
        {showTimelinePlanner && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4"
            onClick={() => setShowTimelinePlanner(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.9, opacity: 0, y: 20 }}
              transition={{ type: 'spring', damping: 25 }}
              onClick={e => e.stopPropagation()}
              className="w-full max-w-6xl h-[85vh] bg-card border border-border rounded-2xl shadow-2xl overflow-hidden"
            >
              {/* Close button */}
              <button
                onClick={() => setShowTimelinePlanner(false)}
                className="absolute top-4 right-4 z-10 p-2 rounded-lg bg-background/80 hover:bg-muted transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
              <TimelinePlanner className="h-full" />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Floating Quick Note (always available) */}
      <FloatingQuickNote
        onSave={async (content, title) => {
          const tempId = generateId();
          const newNote: Note = {
            id: tempId,
            title: title || 'Hızlı Not',
            content: content,
            folder: currentFolderId || undefined,
            color: 'default',
            isPinned: false,
            createdAt: new Date(),
            updatedAt: new Date()
          };
          addNote(newNote);
          
          try {
            const res = await fetch('/api/notes', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                title: newNote.title,
                content: content,
                folder_id: currentFolderId || null,
                color: 'default'
              })
            });
            if (res.ok) {
              const data = await res.json();
              updateNote(tempId, { id: data.id });
              toast.success('Hızlı not oluşturuldu!');
            }
          } catch (e) {
            console.error('Quick note save failed:', e);
          }
        }}
      />

      {/* Recent Notes Sidebar */}
      <AnimatePresence>
        {showRecentNotes && (
          <motion.div
            initial={{ x: -320, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: -320, opacity: 0 }}
            className="fixed left-4 top-24 z-40 w-80"
          >
            <RecentNotesWidget
              notes={notes}
              maxItems={8}
              onNoteClick={(noteId) => {
                const note = notes.find(n => n.id === noteId);
                if (note) {
                  setSelectedNote(note);
                  setShowRecentNotes(false);
                }
              }}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Toast Notifications */}
      <ToastContainer />
    </div >
  );
}
