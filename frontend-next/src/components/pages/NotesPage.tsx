'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  StickyNote,
  Plus,
  Search,
  Folder,
  Trash2,
  Edit3,
  Save,
  X,
  FileText,
  Pin,
  Palette,
  Tag
} from 'lucide-react';
import { useStore, Note } from '@/store/useStore';
import { cn, generateId, formatDate } from '@/lib/utils';

// Note colors matching Streamlit frontend
const NOTE_COLORS = [
  { id: 'default', name: 'Varsayılan', nameEn: 'Default', nameDe: 'Standard', color: 'bg-card', border: 'border-border' },
  { id: 'yellow', name: 'Sarı', nameEn: 'Yellow', nameDe: 'Gelb', color: 'bg-yellow-50 dark:bg-yellow-900/20', border: 'border-yellow-200 dark:border-yellow-800' },
  { id: 'green', name: 'Yeşil', nameEn: 'Green', nameDe: 'Grün', color: 'bg-green-50 dark:bg-green-900/20', border: 'border-green-200 dark:border-green-800' },
  { id: 'blue', name: 'Mavi', nameEn: 'Blue', nameDe: 'Blau', color: 'bg-blue-50 dark:bg-blue-900/20', border: 'border-blue-200 dark:border-blue-800' },
  { id: 'purple', name: 'Mor', nameEn: 'Purple', nameDe: 'Lila', color: 'bg-purple-50 dark:bg-purple-900/20', border: 'border-purple-200 dark:border-purple-800' },
  { id: 'pink', name: 'Pembe', nameEn: 'Pink', nameDe: 'Rosa', color: 'bg-pink-50 dark:bg-pink-900/20', border: 'border-pink-200 dark:border-pink-800' },
  { id: 'orange', name: 'Turuncu', nameEn: 'Orange', nameDe: 'Orange', color: 'bg-orange-50 dark:bg-orange-900/20', border: 'border-orange-200 dark:border-orange-800' },
  { id: 'red', name: 'Kırmızı', nameEn: 'Red', nameDe: 'Rot', color: 'bg-red-50 dark:bg-red-900/20', border: 'border-red-200 dark:border-red-800' },
];

export function NotesPage() {
  const { notes, addNote, updateNote, deleteNote, language, addNoteTag, removeNoteTag } = useStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedNote, setSelectedNote] = useState<Note | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [editContent, setEditContent] = useState('');
  const [selectedFolder, setSelectedFolder] = useState<string | null>(null);
  const [showColorPicker, setShowColorPicker] = useState(false);
  const [showTagInput, setShowTagInput] = useState(false);
  const [tagInput, setTagInput] = useState('');
  const [filterByTag, setFilterByTag] = useState<string | null>(null);

  // Klasörleri çıkar
  const folders = Array.from(new Set(notes.map(n => n.folder).filter(Boolean))) as string[];

  // Get all tags
  const allTags = Array.from(new Set(notes.flatMap(n => n.tags || []))).filter(Boolean);

  // Filtreleme (pinned notes first)
  const filteredNotes = notes
    .filter(note => {
      const matchesSearch = 
        note.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        note.content.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesFolder = !selectedFolder || note.folder === selectedFolder;
      const matchesTag = !filterByTag || (note.tags || []).includes(filterByTag);
      return matchesSearch && matchesFolder && matchesTag;
    })
    .sort((a, b) => {
      // Pinned notes first
      if (a.isPinned && !b.isPinned) return -1;
      if (!a.isPinned && b.isPinned) return 1;
      // Then by date
      return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime();
    });

  // Handle adding tag
  const handleAddTag = () => {
    if (!tagInput.trim() || !selectedNote) return;
    addNoteTag(selectedNote.id, tagInput.trim());
    // Update selectedNote
    setSelectedNote(prev => prev ? { ...prev, tags: [...(prev.tags || []), tagInput.trim()] } : null);
    setTagInput('');
    setShowTagInput(false);
  };

  // Handle removing tag
  const handleRemoveTag = (tag: string) => {
    if (!selectedNote) return;
    removeNoteTag(selectedNote.id, tag);
    // Update selectedNote
    setSelectedNote(prev => prev ? { ...prev, tags: (prev.tags || []).filter(t => t !== tag) } : null);
  };

  // Yeni not
  const handleNewNote = () => {
    const newNote: Note = {
      id: generateId(),
      title: language === 'tr' ? 'Yeni Not' : language === 'de' ? 'Neue Notiz' : 'New Note',
      content: '',
      folder: selectedFolder || undefined,
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
    title: { tr: 'Notlar', en: 'Notes', de: 'Notizen' },
    notes: { tr: 'not', en: 'notes', de: 'Notizen' },
    newNote: { tr: 'Yeni Not', en: 'New Note', de: 'Neue Notiz' },
    searchNotes: { tr: 'Notlarda ara...', en: 'Search notes...', de: 'Notizen durchsuchen...' },
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
              {notes.length} {t.notes[language]}
            </p>
          </div>
        </div>
        <button
          onClick={handleNewNote}
          className="flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-xl hover:bg-primary-600 transition-colors"
        >
          <Plus className="w-4 h-4" />
          {t.newNote[language]}
        </button>
      </header>

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

          {/* Klasörler */}
          <div className="p-2 border-b border-border">
            <div className="flex items-center gap-1 overflow-x-auto pb-2">
              <button
                onClick={() => setSelectedFolder(null)}
                className={cn(
                  "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all",
                  !selectedFolder 
                    ? "bg-primary-500 text-white" 
                    : "bg-muted hover:bg-accent"
                )}
              >
                <Folder className="w-3.5 h-3.5" />
                {t.all[language]}
              </button>
              {folders.map(folder => (
                <button
                  key={folder}
                  onClick={() => setSelectedFolder(folder)}
                  className={cn(
                    "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all",
                    selectedFolder === folder 
                      ? "bg-primary-500 text-white" 
                      : "bg-muted hover:bg-accent"
                  )}
                >
                  <Folder className="w-3.5 h-3.5" />
                  {folder}
                </button>
              ))}
            </div>

            {/* Tags Filter */}
            {allTags.length > 0 && (
              <div className="flex gap-1 flex-wrap mt-2">
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
                  {language === 'tr' ? 'Tümü' : language === 'de' ? 'Alle' : 'All'}
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
            )}
          </div>

          {/* Not Listesi */}
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            <AnimatePresence mode="popLayout">
              {filteredNotes.map((note) => {
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
              })}
            </AnimatePresence>

            {filteredNotes.length === 0 && (
              <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                <FileText className="w-12 h-12 mb-3 opacity-50" />
                <p className="text-sm">{t.noNotes[language]}</p>
              </div>
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
                "flex-1 overflow-y-auto p-6",
                getNoteColorClasses(selectedNote.color).bg
              )}>
                {isEditing ? (
                  <textarea
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    placeholder={t.writePlaceholder[language]}
                    className="w-full h-full resize-none bg-transparent focus:outline-none text-foreground placeholder:text-muted-foreground leading-relaxed"
                  />
                ) : (
                  <div className="prose prose-sm max-w-none dark:prose-invert">
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
