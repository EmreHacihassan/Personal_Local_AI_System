import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
    Trash2, 
    RefreshCw, 
    AlertTriangle, 
    X, 
    Clock, 
    FileText, 
    Folder, 
    RotateCcw,
    Loader2,
    AlertCircle,
    CheckCircle2,
    Eraser
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { API_BASE_URL } from '@/lib/api';

interface TrashNote {
    id: string;
    title: string;
    content: string;
    folder_id: string | null;
    tags: string[];
    created_at: string;
    updated_at: string;
    deleted_at: string;
    versions: any[];
}

interface TrashPanelProps {
    isOpen: boolean;
    onClose: () => void;
    onNoteRestored?: (noteId: string) => void;
}

export function TrashPanel({ isOpen, onClose, onNoteRestored }: TrashPanelProps) {
    const [trashedNotes, setTrashedNotes] = useState<TrashNote[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [selectedNotes, setSelectedNotes] = useState<Set<string>>(new Set());
    const [confirmEmptyTrash, setConfirmEmptyTrash] = useState(false);
    const [actionInProgress, setActionInProgress] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);

    // Fetch trashed notes
    const fetchTrash = useCallback(async () => {
        setIsLoading(true);
        setError(null);
        try {
            const response = await fetch(`${API_BASE_URL}/api/notes/trash`);
            if (!response.ok) throw new Error('Çöp kutusu yüklenemedi');
            const data = await response.json();
            setTrashedNotes(data.trash || []);
        } catch (err) {
            setError('Çöp kutusu yüklenirken hata oluştu');
            console.error('Trash fetch error:', err);
        } finally {
            setIsLoading(false);
        }
    }, []);

    // Load trash when panel opens
    useEffect(() => {
        if (isOpen) {
            fetchTrash();
            setSelectedNotes(new Set());
            setConfirmEmptyTrash(false);
        }
    }, [isOpen, fetchTrash]);

    // Show success message temporarily
    const showSuccess = (message: string) => {
        setSuccessMessage(message);
        setTimeout(() => setSuccessMessage(null), 3000);
    };

    // Restore a single note
    const handleRestore = async (noteId: string) => {
        setActionInProgress(noteId);
        try {
            const response = await fetch(`${API_BASE_URL}/api/notes/trash/${noteId}/restore`, {
                method: 'POST'
            });
            if (!response.ok) throw new Error('Geri yükleme başarısız');
            
            setTrashedNotes(prev => prev.filter(n => n.id !== noteId));
            showSuccess('Not başarıyla geri yüklendi');
            onNoteRestored?.(noteId);
        } catch (err) {
            setError('Geri yükleme sırasında hata oluştu');
            console.error('Restore error:', err);
        } finally {
            setActionInProgress(null);
        }
    };

    // Permanently delete a single note
    const handlePermanentDelete = async (noteId: string) => {
        setActionInProgress(noteId);
        try {
            const response = await fetch(`${API_BASE_URL}/api/notes/trash/${noteId}`, {
                method: 'DELETE'
            });
            if (!response.ok) throw new Error('Silme başarısız');
            
            setTrashedNotes(prev => prev.filter(n => n.id !== noteId));
            showSuccess('Not kalıcı olarak silindi');
        } catch (err) {
            setError('Silme sırasında hata oluştu');
            console.error('Delete error:', err);
        } finally {
            setActionInProgress(null);
        }
    };

    // Empty entire trash
    const handleEmptyTrash = async () => {
        setActionInProgress('empty-all');
        try {
            const response = await fetch(`${API_BASE_URL}/api/notes/trash`, {
                method: 'DELETE'
            });
            if (!response.ok) throw new Error('Çöp kutusu boşaltılamadı');
            
            setTrashedNotes([]);
            setConfirmEmptyTrash(false);
            showSuccess('Çöp kutusu boşaltıldı');
        } catch (err) {
            setError('Çöp kutusu boşaltılırken hata oluştu');
            console.error('Empty trash error:', err);
        } finally {
            setActionInProgress(null);
        }
    };

    // Toggle note selection
    const toggleSelection = (noteId: string) => {
        setSelectedNotes(prev => {
            const newSet = new Set(prev);
            if (newSet.has(noteId)) {
                newSet.delete(noteId);
            } else {
                newSet.add(noteId);
            }
            return newSet;
        });
    };

    // Restore selected notes
    const handleRestoreSelected = async () => {
        const noteIds = Array.from(selectedNotes);
        for (const noteId of noteIds) {
            await handleRestore(noteId);
        }
        setSelectedNotes(new Set());
    };

    // Format date for display
    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        const now = new Date();
        const diff = now.getTime() - date.getTime();
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        
        if (days === 0) return 'Bugün';
        if (days === 1) return 'Dün';
        if (days < 7) return `${days} gün önce`;
        return date.toLocaleDateString('tr-TR');
    };

    return (
        <AnimatePresence>
            {isOpen && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4"
                    onClick={onClose}
                >
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 20 }}
                        className="w-full max-w-2xl bg-card border border-border rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[80vh]"
                        onClick={(e) => e.stopPropagation()}
                    >
                        {/* Header */}
                        <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-gradient-to-r from-red-500/10 to-orange-500/10">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-red-500/20 rounded-xl">
                                    <Trash2 className="w-5 h-5 text-red-500" />
                                </div>
                                <div>
                                    <h3 className="font-semibold text-lg">Çöp Kutusu</h3>
                                    <p className="text-xs text-muted-foreground">
                                        {trashedNotes.length} silinen not
                                    </p>
                                </div>
                            </div>
                            <div className="flex items-center gap-2">
                                <button
                                    onClick={fetchTrash}
                                    disabled={isLoading}
                                    className="p-2 hover:bg-accent rounded-lg transition-colors"
                                    title="Yenile"
                                >
                                    <RefreshCw className={cn("w-4 h-4", isLoading && "animate-spin")} />
                                </button>
                                <button
                                    onClick={onClose}
                                    className="p-2 hover:bg-accent rounded-lg transition-colors"
                                >
                                    <X className="w-5 h-5" />
                                </button>
                            </div>
                        </div>

                        {/* Success Message */}
                        <AnimatePresence>
                            {successMessage && (
                                <motion.div
                                    initial={{ opacity: 0, height: 0 }}
                                    animate={{ opacity: 1, height: 'auto' }}
                                    exit={{ opacity: 0, height: 0 }}
                                    className="px-4 py-2 bg-green-500/10 border-b border-green-500/20 flex items-center gap-2 text-green-600 dark:text-green-400 text-sm"
                                >
                                    <CheckCircle2 className="w-4 h-4" />
                                    {successMessage}
                                </motion.div>
                            )}
                        </AnimatePresence>

                        {/* Error Message */}
                        {error && (
                            <div className="px-4 py-2 bg-red-500/10 border-b border-red-500/20 flex items-center gap-2 text-red-600 dark:text-red-400 text-sm">
                                <AlertCircle className="w-4 h-4" />
                                {error}
                                <button onClick={() => setError(null)} className="ml-auto">
                                    <X className="w-4 h-4" />
                                </button>
                            </div>
                        )}

                        {/* Content */}
                        <div className="flex-1 overflow-y-auto p-4">
                            {isLoading ? (
                                <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                                    <Loader2 className="w-8 h-8 animate-spin mb-3" />
                                    <p className="text-sm">Yükleniyor...</p>
                                </div>
                            ) : trashedNotes.length === 0 ? (
                                <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                                    <Trash2 className="w-12 h-12 mb-3 opacity-30" />
                                    <p className="font-medium">Çöp kutusu boş</p>
                                    <p className="text-sm mt-1">Silinen notlar burada görünecek</p>
                                </div>
                            ) : (
                                <div className="space-y-2">
                                    {trashedNotes.map((note) => (
                                        <motion.div
                                            key={note.id}
                                            layout
                                            initial={{ opacity: 0, x: -20 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            exit={{ opacity: 0, x: 20 }}
                                            className={cn(
                                                "p-4 bg-background border border-border rounded-xl hover:border-primary-500/30 transition-all group",
                                                selectedNotes.has(note.id) && "border-primary-500 bg-primary-500/5"
                                            )}
                                        >
                                            <div className="flex items-start gap-3">
                                                {/* Checkbox */}
                                                <input
                                                    type="checkbox"
                                                    checked={selectedNotes.has(note.id)}
                                                    onChange={() => toggleSelection(note.id)}
                                                    className="mt-1 rounded border-border text-primary-500 focus:ring-primary-500/50"
                                                />
                                                
                                                {/* Note Info */}
                                                <div className="flex-1 min-w-0">
                                                    <div className="flex items-center gap-2 mb-1">
                                                        <FileText className="w-4 h-4 text-muted-foreground" />
                                                        <h4 className="font-medium truncate">{note.title}</h4>
                                                    </div>
                                                    <p className="text-sm text-muted-foreground line-clamp-2 mb-2">
                                                        {note.content?.replace(/[#*`]/g, '').slice(0, 150)}...
                                                    </p>
                                                    <div className="flex items-center gap-3 text-xs text-muted-foreground">
                                                        <span className="flex items-center gap-1">
                                                            <Clock className="w-3 h-3" />
                                                            Silindi: {formatDate(note.deleted_at)}
                                                        </span>
                                                        {note.tags && note.tags.length > 0 && (
                                                            <span className="flex items-center gap-1">
                                                                {note.tags.slice(0, 2).map((tag, i) => (
                                                                    <span key={i} className="px-1.5 py-0.5 bg-muted rounded text-[10px]">
                                                                        {tag}
                                                                    </span>
                                                                ))}
                                                                {note.tags.length > 2 && (
                                                                    <span className="text-[10px]">+{note.tags.length - 2}</span>
                                                                )}
                                                            </span>
                                                        )}
                                                        {note.versions && note.versions.length > 0 && (
                                                            <span className="text-[10px] text-primary-500">
                                                                {note.versions.length} versiyon
                                                            </span>
                                                        )}
                                                    </div>
                                                </div>

                                                {/* Actions */}
                                                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                    <button
                                                        onClick={() => handleRestore(note.id)}
                                                        disabled={actionInProgress === note.id}
                                                        className="p-2 hover:bg-green-500/10 text-green-600 dark:text-green-400 rounded-lg transition-colors"
                                                        title="Geri Yükle"
                                                    >
                                                        {actionInProgress === note.id ? (
                                                            <Loader2 className="w-4 h-4 animate-spin" />
                                                        ) : (
                                                            <RotateCcw className="w-4 h-4" />
                                                        )}
                                                    </button>
                                                    <button
                                                        onClick={() => handlePermanentDelete(note.id)}
                                                        disabled={actionInProgress === note.id}
                                                        className="p-2 hover:bg-red-500/10 text-red-500 rounded-lg transition-colors"
                                                        title="Kalıcı Olarak Sil"
                                                    >
                                                        <Trash2 className="w-4 h-4" />
                                                    </button>
                                                </div>
                                            </div>
                                        </motion.div>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* Footer */}
                        {trashedNotes.length > 0 && (
                            <div className="px-6 py-4 border-t border-border bg-muted/30 flex items-center justify-between">
                                {/* Selection Actions */}
                                <div className="flex items-center gap-2">
                                    {selectedNotes.size > 0 && (
                                        <>
                                            <span className="text-sm text-muted-foreground">
                                                {selectedNotes.size} seçili
                                            </span>
                                            <button
                                                onClick={handleRestoreSelected}
                                                className="px-3 py-1.5 bg-green-500/10 hover:bg-green-500/20 text-green-600 dark:text-green-400 rounded-lg text-sm font-medium transition-colors flex items-center gap-1"
                                            >
                                                <RotateCcw className="w-3 h-3" />
                                                Seçilenleri Geri Yükle
                                            </button>
                                        </>
                                    )}
                                </div>

                                {/* Empty Trash */}
                                {confirmEmptyTrash ? (
                                    <div className="flex items-center gap-2">
                                        <span className="text-sm text-red-500 flex items-center gap-1">
                                            <AlertTriangle className="w-4 h-4" />
                                            Emin misiniz?
                                        </span>
                                        <button
                                            onClick={() => setConfirmEmptyTrash(false)}
                                            className="px-3 py-1.5 bg-muted hover:bg-accent rounded-lg text-sm transition-colors"
                                        >
                                            İptal
                                        </button>
                                        <button
                                            onClick={handleEmptyTrash}
                                            disabled={actionInProgress === 'empty-all'}
                                            className="px-3 py-1.5 bg-red-500 hover:bg-red-600 text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-1"
                                        >
                                            {actionInProgress === 'empty-all' ? (
                                                <Loader2 className="w-3 h-3 animate-spin" />
                                            ) : (
                                                <Eraser className="w-3 h-3" />
                                            )}
                                            Tümünü Sil
                                        </button>
                                    </div>
                                ) : (
                                    <button
                                        onClick={() => setConfirmEmptyTrash(true)}
                                        className="px-4 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-500 rounded-xl text-sm font-medium transition-colors flex items-center gap-2"
                                    >
                                        <Eraser className="w-4 h-4" />
                                        Çöp Kutusunu Boşalt
                                    </button>
                                )}
                            </div>
                        )}
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    );
}
