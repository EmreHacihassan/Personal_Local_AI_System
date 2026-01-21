'use client';

import { useState, useMemo, useCallback } from 'react';
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
  AlignLeft,
  AlignCenter,
  AlignRight,
  ListOrdered,
  ListTodo,
  Heading1,
  Heading2,
  Quote,
  Code,
  Link2,
  Image,
  FileText,
  Sparkles
} from 'lucide-react';
import { jsPDF } from 'jspdf';
import { useStore, Note } from '@/store/useStore';
import { cn, generateId, formatDate } from '@/lib/utils';

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

// Folder interface
interface NoteFolder {
  id: string;
  name: string;
  icon: string;
  parentId: string | null;
  color: string;
  createdAt: Date;
}

export function NotesPage() {
  const { notes, addNote, updateNote, deleteNote, language, addNoteTag, removeNoteTag } = useStore();
  
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
  const [folders, setFolders] = useState<NoteFolder[]>([]);
  const [showNewFolderForm, setShowNewFolderForm] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');
  const [newFolderIcon, setNewFolderIcon] = useState('📁');
  const [showFolderIconPicker, setShowFolderIconPicker] = useState(false);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [editingFolderId, setEditingFolderId] = useState<string | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [showFolderMenu, setShowFolderMenu] = useState<string | null>(null);

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
  const noteFolders = useMemo(() => {
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
    
    const newFolder: NoteFolder = {
      id: generateId(),
      name: newFolderName.trim(),
      icon: newFolderIcon,
      parentId: currentFolderId,
      color: 'blue',
      createdAt: new Date()
    };
    
    setFolders(prev => [...prev, newFolder]);
    setNewFolderName('');
    setNewFolderIcon('📁');
    setShowNewFolderForm(false);
  };

  const handleDeleteFolder = (folderId: string) => {
    // Delete folder and move notes to parent
    const folder = folders.find(f => f.id === folderId);
    if (!folder) return;
    
    // Move notes in this folder to parent
    notes.forEach(note => {
      if (note.folder === folderId || note.folder === folder.name) {
        updateNote(note.id, { folder: folder.parentId || undefined });
      }
    });
    
    // Delete subfolders recursively
    const deleteRecursive = (id: string) => {
      folders.filter(f => f.parentId === id).forEach(sub => deleteRecursive(sub.id));
      setFolders(prev => prev.filter(f => f.id !== id));
    };
    
    deleteRecursive(folderId);
    
    if (currentFolderId === folderId) {
      setCurrentFolderId(folder.parentId);
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
    const pageHeight = pdf.internal.pageSize.getHeight();
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
  const handleNewNote = () => {
    const newNote: Note = {
      id: generateId(),
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
  };

  // Not düzenlemeye başla
  const handleEdit = (note: Note) => {
    setSelectedNote(note);
    setEditTitle(note.title);
    setEditContent(note.content);
    setIsEditing(true);
  };

  // Kaydet
  const handleSave = () => {
    if (selectedNote) {
      updateNote(selectedNote.id, {
        title: editTitle,
        content: editContent
      });
      setSelectedNote({ ...selectedNote, title: editTitle, content: editContent });
      setIsEditing(false);
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

  // Toggle pin
  const handleTogglePin = (note: Note) => {
    updateNote(note.id, { isPinned: !note.isPinned });
    if (selectedNote?.id === note.id) {
      setSelectedNote({ ...note, isPinned: !note.isPinned });
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
    <div className="flex flex-col h-full">
      {/* Header */}
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
        </div>
      </header>

      {/* Breadcrumb Navigation */}
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
        {/* Sol Panel - Not Listesi */}
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
                      <p className="font-medium text-sm text-blue-700 dark:text-blue-300 truncate">{folder.name}</p>
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
                          handleDeleteFolder(folder.id);
                        }}
                        className="p-1.5 text-red-500 hover:bg-red-100 dark:hover:bg-red-900/30 rounded-lg transition-colors"
                        title={t.delete[language]}
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
                              deleteNote(note.id);
                              if (selectedNote?.id === note.id) {
                                setSelectedNote(null);
                              }
                            }}
                            className="p-1.5 text-muted-foreground hover:text-destructive rounded-lg hover:bg-destructive/10 transition-all"
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
                          {note.isPinned && <Pin className="w-3 h-3 text-primary-500" />}
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              deleteNote(note.id);
                              if (selectedNote?.id === note.id) {
                                setSelectedNote(null);
                              }
                            }}
                            className="p-1 text-muted-foreground hover:text-destructive rounded opacity-0 group-hover:opacity-100 transition-all ml-auto"
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
                      </div>
                      
                      <div className="flex-1" />
                      
                      <div className="flex items-center gap-1 px-2 py-1 bg-primary-500/10 rounded-lg">
                        <Sparkles className="w-3.5 h-3.5 text-primary-500" />
                        <span className="text-xs font-medium text-primary-600">Premium Editor</span>
                      </div>
                    </div>
                    
                    {/* Editor Area */}
                    <div className="flex-1 p-6">
                      <textarea
                        value={editContent}
                        onChange={(e) => setEditContent(e.target.value)}
                        placeholder={t.writePlaceholder[language]}
                        className="w-full h-full resize-none bg-transparent focus:outline-none text-foreground placeholder:text-muted-foreground leading-relaxed font-mono text-sm"
                        style={{ minHeight: '300px' }}
                      />
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
                ) : (
                  <div className="prose prose-sm max-w-none dark:prose-invert p-6">
                    {selectedNote.content ? (
                      <p className="whitespace-pre-wrap">{selectedNote.content}</p>
                    ) : (
                      <p className="text-muted-foreground italic">
                        {t.emptyNoteHint[language]}
                      </p>
                    )}
                  </div>
                )}
              </div>

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
    </div>
  );
}
