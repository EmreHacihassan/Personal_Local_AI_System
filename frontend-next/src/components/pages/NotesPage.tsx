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
  EyeOff
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
import { useMultiSelect } from '@/hooks/useMultiSelect';
import { ImageSettingsModal, ImageSettings } from '@/components/modals/ImageSettingsModal';
import { compressImage } from '@/lib/imageUtils';
import { MATH_KEYBOARD_CATEGORIES, NORMAL_KEYBOARD_CATEGORIES } from '@/lib/constants/mathKeyboard';

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
    language, addNoteTag, removeNoteTag
  } = useStore();

  // API Sync logic moved to AppInitializer (Global sync)

  // Use store folders
  const folders = noteFolders;

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
  const [recentNoteIds, setRecentNoteIds] = useState<string[]>([]);
  const [archivedNotes, setArchivedNotes] = useState<Note[]>([]);

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

  // ESC tuşu ile tam ekrandan çık
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (isNoteFullscreen) setIsNoteFullscreen(false);
        else if (isPageFullscreen) setIsPageFullscreen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isNoteFullscreen, isPageFullscreen]);

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

  // Get subfolders of current folder
  const subFolders = useMemo(() => {
    return folders.filter(f => f.parentId === currentFolderId);
  }, [folders, currentFolderId]);

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
      alert(lockedMessage);
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

    // Note content
    if (note.content) {
      y = addTextToPDF(pdf, note.content, y, { fontSize: 11 });
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

      // Note content
      if (note.content) {
        const contentPreview = note.content.length > 500 ? note.content.substring(0, 500) + '...' : note.content;
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
  };

  // Kaydet
  const handleSave = async () => {
    if (selectedNote) {
      // Optimistic update
      const updatedNote = {
        ...selectedNote,
        title: editTitle,
        content: editContent,
        updatedAt: new Date()
      };
      updateNote(selectedNote.id, {
        title: editTitle,
        content: editContent
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
            content: editContent
          })
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
      alert(lockedMessage);
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

  // ==================== AI'DAN GİZLEME (OBFUSCATION) ====================
  
  // Not'u AI'dan gizle/göster toggle
  const handleToggleNoteHidden = async (note: Note) => {
    const newHiddenState = !note.isEncrypted;
    
    // İçeriği obfuscate/deobfuscate et
    let newContent = note.content;
    if (newHiddenState) {
      // Base64 encode et (AI anlayamaz ama UI'da decode edilir)
      newContent = btoa(unescape(encodeURIComponent(note.content)));
    } else {
      // Base64 decode et
      try {
        newContent = decodeURIComponent(escape(atob(note.content)));
      } catch {
        newContent = note.content;
      }
    }
    
    updateNote(note.id, { 
      content: newContent,
      isEncrypted: newHiddenState 
    });
    
    if (selectedNote?.id === note.id) {
      setSelectedNote({ 
        ...note, 
        content: newContent,
        isEncrypted: newHiddenState 
      });
      setEditContent(newHiddenState ? decodeURIComponent(escape(atob(newContent))) : newContent);
    }

    // Backend'e kaydet
    try {
      await fetch(`/api/notes/${note.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          content: newContent,
          encrypted: newHiddenState 
        }),
      });
    } catch (error) {
      console.error('Toggle hidden error:', error);
    }
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
      `shape:${settings.shape}`
    ].join('|');

    // ![Caption|size:medium|align:center|shape:rounded](url)
    const caption = settings.caption || uploadedImageInfo.name;
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
      `shape:${settings.shape}`
    ].join('|');

    // Build old and new markdown patterns
    const oldAlt = editingImageInfo.alt || '';
    const newCaption = settings.caption || editingImageInfo.alt || 'image';
    
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
      const caption = altText.split('|')[0] || 'image';
      return `![${caption}|${newOptionsStr}](${imageUrl})`;
    });

    // Update note
    updateNote(selectedNote.id, { content: updatedContent });
    setSelectedNote(prev => prev ? { ...prev, content: updatedContent } : null);
  };

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
          {/* Arama */}
          <div className="p-4 border-b border-border">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={t.searchNotes[language]}
                className="w-full pl-10 pr-4 py-2.5 bg-background border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/50"
              />
            </div>
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
                  className="group"
                >
                  <div
                    className="flex items-center gap-3 p-3 rounded-xl bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border border-blue-200 dark:border-blue-800 cursor-pointer hover:shadow-md transition-all"
                    onClick={() => setCurrentFolderId(folder.id)}
                  >
                    <span className="text-2xl">{folder.icon}</span>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm text-blue-700 dark:text-blue-300 truncate flex items-center gap-1">
                        {folder.name}
                        {folder.isLocked && <Lock className="w-3 h-3 text-amber-500" />}
                      </p>
                      <p className="text-xs text-blue-500/70 dark:text-blue-400/70">
                        {notes.filter(n => n.folder === folder.id || n.folder === folder.name).length} {t.notes[language]}
                      </p>
                    </div>
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
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
                      onClick={() => {
                        setSelectedNote(note);
                        setIsEditing(false);
                      }}
                      className={cn(
                        "w-full text-left p-3 rounded-xl transition-all group border",
                        colorClasses.bg,
                        selectedNote?.id === note.id
                          ? "ring-2 ring-primary-500"
                          : colorClasses.border
                      )}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-1">
                            {note.isPinned && <Pin className="w-3 h-3 text-primary-500" />}
                            {note.isLocked && <Lock className="w-3 h-3 text-amber-500" />}
                            {note.isEncrypted && <EyeOff className="w-3 h-3 text-purple-500" />}
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
                              handleToggleNoteHidden(note);
                            }}
                            className={cn(
                              "p-1.5 rounded-lg transition-colors",
                              note.isEncrypted
                                ? "text-purple-500 bg-purple-100 dark:bg-purple-900/30"
                                : "text-muted-foreground hover:bg-accent"
                            )}
                            title={note.isEncrypted 
                              ? (language === 'tr' ? 'AI Görebilir' : 'AI Can See')
                              : (language === 'tr' ? 'AI\'dan Gizle' : 'Hide from AI')
                            }
                          >
                            {note.isEncrypted ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
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
                        onClick={() => {
                          setSelectedNote(note);
                          setIsEditing(false);
                        }}
                        className={cn(
                          "text-left p-3 rounded-xl transition-all group border aspect-square flex flex-col",
                          colorClasses.bg,
                          selectedNote?.id === note.id
                            ? "ring-2 ring-primary-500"
                            : colorClasses.border
                        )}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-1">
                            {note.isPinned && <Pin className="w-3 h-3 text-primary-500" />}
                            {note.isLocked && <Lock className="w-3 h-3 text-amber-500" />}
                            {note.isEncrypted && <EyeOff className="w-3 h-3 text-purple-500" />}
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

            {/* Empty State */}
            {subFolders.length === 0 && filteredNotes.length === 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex flex-col items-center justify-center py-12 text-center"
              >
                <div className="w-20 h-20 mb-4 rounded-full bg-muted/50 flex items-center justify-center">
                  <FolderOpen className="w-10 h-10 text-muted-foreground/50" />
                </div>
                <h3 className="text-sm font-medium text-foreground mb-1">
                  {t.emptyFolder[language]}
                </h3>
                <p className="text-xs text-muted-foreground max-w-[200px]">
                  {t.emptyFolderHint[language]}
                </p>
                <div className="flex items-center gap-2 mt-4">
                  <button
                    onClick={() => setShowNewFolderForm(true)}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-muted hover:bg-accent rounded-lg transition-colors"
                  >
                    <FolderPlus className="w-3.5 h-3.5" />
                    {t.newFolder[language]}
                  </button>
                  <button
                    onClick={handleNewNote}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    {t.newNote[language]}
                  </button>
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
                    {selectedNote.isEncrypted && (
                      <span title={language === 'tr' ? 'AI\'dan Gizli' : 'Hidden from AI'}>
                        <EyeOff className="w-5 h-5 text-purple-500" />
                      </span>
                    )}
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

                  {/* AI'dan Gizle/Göster Button */}
                  <button
                    onClick={() => handleToggleNoteHidden(selectedNote)}
                    className={cn(
                      "flex items-center gap-2 px-3 py-1.5 rounded-lg transition-colors",
                      selectedNote.isEncrypted
                        ? "bg-purple-500 text-white"
                        : "bg-muted hover:bg-accent"
                    )}
                    title={selectedNote.isEncrypted 
                      ? (language === 'tr' ? 'AI Görebilir Yap' : 'Make AI Visible')
                      : (language === 'tr' ? 'AI\'dan Gizle' : 'Hide from AI')
                    }
                  >
                    {selectedNote.isEncrypted ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
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
                                    res = await fetch('http://localhost:8001/api/v1/upload/image', {
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

                                  alert(language === 'tr'
                                    ? `Görsel yüklenemedi: ${errorMessage} (Kod: ${status})`
                                    : `Image upload failed: ${errorMessage} (Code: ${status})`);
                                }
                              } catch (error) {
                                console.error('Image upload error:', error);
                                alert(language === 'tr' ? `Bir hata oluştu: ${error}` : `An error occurred: ${error}`);
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
                        placeholder={t.writePlaceholder[language]}
                        className="w-full flex-1 resize-none bg-transparent focus:outline-none text-foreground placeholder:text-muted-foreground leading-relaxed font-mono text-sm"
                        style={{ minHeight: showMathKeyboard ? '200px' : '300px' }}
                      />
                      
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
                  </div>
                ) : selectedNote.isEncrypted ? (
                  <div className="prose prose-sm max-w-none dark:prose-invert p-6">
                    {/* AI'dan gizli içerik banner'ı */}
                    <div className="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-xl p-3 mb-4 not-prose">
                      <div className="flex items-center gap-2">
                        <EyeOff className="w-5 h-5 text-purple-600" />
                        <span className="text-sm text-purple-700 dark:text-purple-300">
                          {language === 'tr' ? 'Bu not AI\'dan gizleniyor' : 'This note is hidden from AI'}
                        </span>
                      </div>
                    </div>
                    {getDisplayContent(selectedNote) ? (
                      <WikiContentRenderer
                        content={getDisplayContent(selectedNote)}
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
              // TODO: Implement move modal
              console.log('Move selected notes');
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
            caption: editingImageInfo.alt
          } : undefined}
        />
      )}
    </div >
  );
}
