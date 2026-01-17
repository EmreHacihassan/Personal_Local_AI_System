'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  StickyNote,
  Plus,
  Search,
  Folder,
  FolderPlus,
  Trash2,
  Edit3,
  Save,
  X,
  FileText
} from 'lucide-react';
import { useStore, Note } from '@/store/useStore';
import { cn, generateId, formatDate } from '@/lib/utils';

export function NotesPage() {
  const { notes, addNote, updateNote, deleteNote, language } = useStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedNote, setSelectedNote] = useState<Note | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [editContent, setEditContent] = useState('');
  const [selectedFolder, setSelectedFolder] = useState<string | null>(null);

  // Klasörleri çıkar
  const folders = Array.from(new Set(notes.map(n => n.folder).filter(Boolean))) as string[];

  // Filtreleme
  const filteredNotes = notes.filter(note => {
    const matchesSearch = 
      note.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      note.content.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFolder = !selectedFolder || note.folder === selectedFolder;
    return matchesSearch && matchesFolder;
  });

  // Yeni not
  const handleNewNote = () => {
    const newNote: Note = {
      id: generateId(),
      title: language === 'tr' ? 'Yeni Not' : 'New Note',
      content: '',
      folder: selectedFolder || undefined,
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

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-border bg-card/50 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-yellow-500 to-orange-500 text-white">
            <StickyNote className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-semibold">
              {language === 'tr' ? 'Notlar' : 'Notes'}
            </h1>
            <p className="text-xs text-muted-foreground">
              {notes.length} {language === 'tr' ? 'not' : 'notes'}
            </p>
          </div>
        </div>
        <button
          onClick={handleNewNote}
          className="flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-xl hover:bg-primary-600 transition-colors"
        >
          <Plus className="w-4 h-4" />
          {language === 'tr' ? 'Yeni Not' : 'New Note'}
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
                placeholder={language === 'tr' ? 'Notlarda ara...' : 'Search notes...'}
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
                {language === 'tr' ? 'Tümü' : 'All'}
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
          </div>

          {/* Not Listesi */}
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            <AnimatePresence mode="popLayout">
              {filteredNotes.map((note) => (
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
                    "w-full text-left p-3 rounded-xl transition-all group",
                    selectedNote?.id === note.id 
                      ? "bg-primary-500/10 border border-primary-500/30" 
                      : "hover:bg-accent border border-transparent"
                  )}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm truncate">{note.title}</p>
                      <p className="text-xs text-muted-foreground truncate mt-1">
                        {note.content || (language === 'tr' ? 'Boş not' : 'Empty note')}
                      </p>
                      <p className="text-[10px] text-muted-foreground mt-2">
                        {formatDate(note.updatedAt, language)}
                      </p>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteNote(note.id);
                        if (selectedNote?.id === note.id) {
                          setSelectedNote(null);
                        }
                      }}
                      className="opacity-0 group-hover:opacity-100 p-1.5 text-muted-foreground hover:text-destructive rounded-lg hover:bg-destructive/10 transition-all"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </motion.button>
              ))}
            </AnimatePresence>

            {filteredNotes.length === 0 && (
              <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                <FileText className="w-12 h-12 mb-3 opacity-50" />
                <p className="text-sm">
                  {language === 'tr' ? 'Not bulunamadı' : 'No notes found'}
                </p>
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
                  <h2 className="text-xl font-semibold">{selectedNote.title}</h2>
                )}
                
                <div className="flex items-center gap-2">
                  {isEditing ? (
                    <>
                      <button
                        onClick={handleCancel}
                        className="flex items-center gap-2 px-3 py-1.5 text-muted-foreground hover:bg-accent rounded-lg transition-colors"
                      >
                        <X className="w-4 h-4" />
                        {language === 'tr' ? 'İptal' : 'Cancel'}
                      </button>
                      <button
                        onClick={handleSave}
                        className="flex items-center gap-2 px-3 py-1.5 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
                      >
                        <Save className="w-4 h-4" />
                        {language === 'tr' ? 'Kaydet' : 'Save'}
                      </button>
                    </>
                  ) : (
                    <button
                      onClick={() => handleEdit(selectedNote)}
                      className="flex items-center gap-2 px-3 py-1.5 bg-muted hover:bg-accent rounded-lg transition-colors"
                    >
                      <Edit3 className="w-4 h-4" />
                      {language === 'tr' ? 'Düzenle' : 'Edit'}
                    </button>
                  )}
                </div>
              </div>

              {/* Not İçeriği */}
              <div className="flex-1 overflow-y-auto p-6">
                {isEditing ? (
                  <textarea
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    placeholder={language === 'tr' ? 'Notunuzu buraya yazın...' : 'Write your note here...'}
                    className="w-full h-full resize-none bg-transparent focus:outline-none text-foreground placeholder:text-muted-foreground leading-relaxed"
                  />
                ) : (
                  <div className="prose prose-sm max-w-none dark:prose-invert">
                    {selectedNote.content ? (
                      <p className="whitespace-pre-wrap">{selectedNote.content}</p>
                    ) : (
                      <p className="text-muted-foreground italic">
                        {language === 'tr' ? 'Bu not boş. Düzenlemek için düzenle butonuna tıklayın.' : 'This note is empty. Click edit to add content.'}
                      </p>
                    )}
                  </div>
                )}
              </div>

              {/* Not Metadata */}
              <div className="px-6 py-3 border-t border-border bg-muted/30 text-xs text-muted-foreground">
                <span>{language === 'tr' ? 'Oluşturulma:' : 'Created:'} {formatDate(selectedNote.createdAt, language)}</span>
                <span className="mx-2">•</span>
                <span>{language === 'tr' ? 'Güncelleme:' : 'Updated:'} {formatDate(selectedNote.updatedAt, language)}</span>
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-muted-foreground">
              <StickyNote className="w-16 h-16 mb-4 opacity-50" />
              <p className="text-lg font-medium">
                {language === 'tr' ? 'Not Seçilmedi' : 'No Note Selected'}
              </p>
              <p className="text-sm mt-1">
                {language === 'tr' 
                  ? 'Görüntülemek için bir not seçin veya yeni bir not oluşturun'
                  : 'Select a note to view or create a new one'}
              </p>
              <button
                onClick={handleNewNote}
                className="flex items-center gap-2 px-4 py-2 mt-4 bg-primary-500 text-white rounded-xl hover:bg-primary-600 transition-colors"
              >
                <Plus className="w-4 h-4" />
                {language === 'tr' ? 'Yeni Not' : 'New Note'}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
