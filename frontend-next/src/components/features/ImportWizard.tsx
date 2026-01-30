'use client';

/**
 * ImportWizard - Notion & Obsidian Import Wizard
 * 
 * Dışarıdan not import etme sihirbazı.
 */

import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Upload,
    FileText,
    Folder,
    CheckCircle,
    AlertCircle,
    Loader2,
    X,
    ChevronRight,
    ArrowLeft,
    FileJson,
    BookOpen
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface ImportWizardProps {
    onImport: (notes: ImportedNote[], folders: ImportedFolder[]) => void;
    onClose: () => void;
    language?: 'tr' | 'en' | 'de';
}

interface ImportedNote {
    title: string;
    content: string;
    folder?: string;
    tags?: string[];
    createdAt?: Date;
}

interface ImportedFolder {
    name: string;
    parentName?: string;
}

type ImportSource = 'notion' | 'obsidian' | 'json' | 'markdown';
type Step = 'source' | 'upload' | 'preview' | 'complete';

const translations = {
    title: { tr: 'Not İçe Aktar', en: 'Import Notes', de: 'Notizen importieren' },
    selectSource: { tr: 'Kaynak Seç', en: 'Select Source', de: 'Quelle wählen' },
    upload: { tr: 'Dosya Yükle', en: 'Upload File', de: 'Datei hochladen' },
    preview: { tr: 'Önizleme', en: 'Preview', de: 'Vorschau' },
    complete: { tr: 'Tamamlandı', en: 'Complete', de: 'Abgeschlossen' },
    dragDrop: { tr: 'Dosyaları sürükleyip bırakın', en: 'Drag and drop files', de: 'Dateien hier ablegen' },
    or: { tr: 'veya', en: 'or', de: 'oder' },
    browse: { tr: 'Dosya Seç', en: 'Browse Files', de: 'Dateien durchsuchen' },
    importing: { tr: 'İçe aktarılıyor...', en: 'Importing...', de: 'Wird importiert...' },
    success: { tr: 'Başarıyla içe aktarıldı!', en: 'Successfully imported!', de: 'Erfolgreich importiert!' },
    next: { tr: 'Devam', en: 'Next', de: 'Weiter' },
    back: { tr: 'Geri', en: 'Back', de: 'Zurück' },
    import: { tr: 'İçe Aktar', en: 'Import', de: 'Importieren' },
    notes: { tr: 'not', en: 'notes', de: 'Notizen' },
    folders: { tr: 'klasör', en: 'folders', de: 'Ordner' },
};

const SOURCES = [
    {
        id: 'notion' as ImportSource,
        name: 'Notion',
        icon: '📝',
        color: 'from-gray-800 to-gray-900',
        desc: { tr: 'Notion export ZIP dosyası', en: 'Notion export ZIP file', de: 'Notion Export-ZIP-Datei' },
        accept: '.zip'
    },
    {
        id: 'obsidian' as ImportSource,
        name: 'Obsidian',
        icon: '💎',
        color: 'from-purple-600 to-violet-700',
        desc: { tr: 'Obsidian vault klasörü', en: 'Obsidian vault folder', de: 'Obsidian Vault-Ordner' },
        accept: '.md,.zip'
    },
    {
        id: 'json' as ImportSource,
        name: 'JSON Backup',
        icon: '📦',
        color: 'from-amber-500 to-orange-600',
        desc: { tr: 'Önceki yedek dosyası', en: 'Previous backup file', de: 'Vorherige Sicherungsdatei' },
        accept: '.json'
    },
    {
        id: 'markdown' as ImportSource,
        name: 'Markdown',
        icon: '📄',
        color: 'from-blue-500 to-cyan-600',
        desc: { tr: 'Markdown dosyaları', en: 'Markdown files', de: 'Markdown-Dateien' },
        accept: '.md'
    },
];

export function ImportWizard({ onImport, onClose, language = 'tr' }: ImportWizardProps) {
    const t = translations;

    const [step, setStep] = useState<Step>('source');
    const [source, setSource] = useState<ImportSource | null>(null);
    const [files, setFiles] = useState<File[]>([]);
    const [parsedNotes, setParsedNotes] = useState<ImportedNote[]>([]);
    const [parsedFolders, setParsedFolders] = useState<ImportedFolder[]>([]);
    const [isProcessing, setIsProcessing] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [isDragging, setIsDragging] = useState(false);

    const handleFileSelect = useCallback((selectedFiles: FileList | null) => {
        if (!selectedFiles) return;
        setFiles(Array.from(selectedFiles));
        setError(null);
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        handleFileSelect(e.dataTransfer.files);
    }, [handleFileSelect]);

    const processFiles = useCallback(async () => {
        setIsProcessing(true);
        setError(null);

        try {
            const notes: ImportedNote[] = [];
            const folders: ImportedFolder[] = [];

            for (const file of files) {
                if (file.name.endsWith('.json')) {
                    // JSON import
                    const text = await file.text();
                    const data = JSON.parse(text);

                    if (data.notes && Array.isArray(data.notes)) {
                        data.notes.forEach((n: any) => {
                            notes.push({
                                title: n.title || 'Untitled',
                                content: n.content || '',
                                folder: n.folder,
                                tags: n.tags,
                                createdAt: n.createdAt ? new Date(n.createdAt) : undefined,
                            });
                        });
                    }

                    if (data.folders && Array.isArray(data.folders)) {
                        data.folders.forEach((f: any) => {
                            folders.push({
                                name: f.name,
                                parentName: f.parentName,
                            });
                        });
                    }
                } else if (file.name.endsWith('.md')) {
                    // Markdown import
                    const text = await file.text();
                    const title = file.name.replace('.md', '');

                    notes.push({
                        title,
                        content: text,
                    });
                }
            }

            setParsedNotes(notes);
            setParsedFolders(folders);
            setStep('preview');
        } catch (err) {
            setError(language === 'tr' ? 'Dosya işlenirken hata oluştu' : 'Error processing file');
        } finally {
            setIsProcessing(false);
        }
    }, [files, language]);

    const handleImport = useCallback(() => {
        setIsProcessing(true);

        // Simulate import process
        setTimeout(() => {
            onImport(parsedNotes, parsedFolders);
            setStep('complete');
            setIsProcessing(false);

            // Auto close after success
            setTimeout(() => onClose(), 2000);
        }, 1000);
    }, [parsedNotes, parsedFolders, onImport, onClose]);

    const renderStep = () => {
        switch (step) {
            case 'source':
                return (
                    <motion.div
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        className="space-y-3"
                    >
                        <h4 className="text-sm font-medium text-muted-foreground mb-4">
                            {t.selectSource[language]}
                        </h4>
                        <div className="grid grid-cols-2 gap-3">
                            {SOURCES.map(s => (
                                <motion.button
                                    key={s.id}
                                    whileHover={{ scale: 1.02 }}
                                    whileTap={{ scale: 0.98 }}
                                    onClick={() => {
                                        setSource(s.id);
                                        setStep('upload');
                                    }}
                                    className="flex flex-col items-center gap-2 p-4 rounded-xl border border-border hover:border-primary-500/50 transition-all text-center group"
                                >
                                    <div className={cn(
                                        "w-12 h-12 rounded-xl flex items-center justify-center text-2xl bg-gradient-to-br",
                                        s.color
                                    )}>
                                        {s.icon}
                                    </div>
                                    <span className="text-sm font-medium">{s.name}</span>
                                    <span className="text-[10px] text-muted-foreground">{s.desc[language]}</span>
                                </motion.button>
                            ))}
                        </div>
                    </motion.div>
                );

            case 'upload':
                const sourceConfig = SOURCES.find(s => s.id === source);
                return (
                    <motion.div
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        className="space-y-4"
                    >
                        <button
                            onClick={() => setStep('source')}
                            className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
                        >
                            <ArrowLeft className="w-4 h-4" />
                            {t.back[language]}
                        </button>

                        <div
                            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                            onDragLeave={() => setIsDragging(false)}
                            onDrop={handleDrop}
                            className={cn(
                                "border-2 border-dashed rounded-xl p-8 text-center transition-all",
                                isDragging
                                    ? "border-primary-500 bg-primary-500/10"
                                    : "border-border hover:border-primary-500/50"
                            )}
                        >
                            <Upload className={cn(
                                "w-10 h-10 mx-auto mb-3 transition-colors",
                                isDragging ? "text-primary-500" : "text-muted-foreground"
                            )} />
                            <p className="text-sm font-medium mb-1">{t.dragDrop[language]}</p>
                            <p className="text-xs text-muted-foreground mb-3">{t.or[language]}</p>
                            <label className="inline-block">
                                <input
                                    type="file"
                                    accept={sourceConfig?.accept}
                                    multiple
                                    onChange={(e) => handleFileSelect(e.target.files)}
                                    className="sr-only"
                                />
                                <span className="px-4 py-2 rounded-lg bg-primary-500 text-white text-sm font-medium cursor-pointer hover:bg-primary-600 transition-colors">
                                    {t.browse[language]}
                                </span>
                            </label>
                        </div>

                        {files.length > 0 && (
                            <div className="space-y-2">
                                {files.map((file, i) => (
                                    <div key={i} className="flex items-center gap-2 p-2 rounded-lg bg-muted">
                                        <FileText className="w-4 h-4 text-muted-foreground" />
                                        <span className="text-sm flex-1 truncate">{file.name}</span>
                                        <button
                                            onClick={() => setFiles(files.filter((_, fi) => fi !== i))}
                                            className="p-1 hover:text-destructive transition-colors"
                                        >
                                            <X className="w-3 h-3" />
                                        </button>
                                    </div>
                                ))}

                                <motion.button
                                    whileHover={{ scale: 1.02 }}
                                    whileTap={{ scale: 0.98 }}
                                    onClick={processFiles}
                                    disabled={isProcessing}
                                    className="w-full py-2.5 rounded-lg bg-primary-500 text-white font-medium text-sm flex items-center justify-center gap-2"
                                >
                                    {isProcessing ? (
                                        <>
                                            <Loader2 className="w-4 h-4 animate-spin" />
                                            {t.importing[language]}
                                        </>
                                    ) : (
                                        <>
                                            {t.next[language]}
                                            <ChevronRight className="w-4 h-4" />
                                        </>
                                    )}
                                </motion.button>
                            </div>
                        )}

                        {error && (
                            <div className="flex items-center gap-2 p-3 rounded-lg bg-destructive/10 text-destructive text-sm">
                                <AlertCircle className="w-4 h-4" />
                                {error}
                            </div>
                        )}
                    </motion.div>
                );

            case 'preview':
                return (
                    <motion.div
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        className="space-y-4"
                    >
                        <button
                            onClick={() => setStep('upload')}
                            className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
                        >
                            <ArrowLeft className="w-4 h-4" />
                            {t.back[language]}
                        </button>

                        <div className="grid grid-cols-2 gap-3">
                            <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-center">
                                <FileText className="w-8 h-8 mx-auto mb-2 text-emerald-500" />
                                <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
                                    {parsedNotes.length}
                                </p>
                                <p className="text-xs text-muted-foreground">{t.notes[language]}</p>
                            </div>
                            <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/20 text-center">
                                <Folder className="w-8 h-8 mx-auto mb-2 text-blue-500" />
                                <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                                    {parsedFolders.length}
                                </p>
                                <p className="text-xs text-muted-foreground">{t.folders[language]}</p>
                            </div>
                        </div>

                        <div className="max-h-48 overflow-y-auto space-y-1">
                            {parsedNotes.slice(0, 10).map((note, i) => (
                                <div key={i} className="flex items-center gap-2 p-2 rounded-lg bg-muted text-sm">
                                    <FileText className="w-3.5 h-3.5 text-muted-foreground" />
                                    <span className="truncate">{note.title}</span>
                                </div>
                            ))}
                            {parsedNotes.length > 10 && (
                                <p className="text-xs text-muted-foreground text-center py-2">
                                    +{parsedNotes.length - 10} more...
                                </p>
                            )}
                        </div>

                        <motion.button
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            onClick={handleImport}
                            disabled={isProcessing}
                            className="w-full py-2.5 rounded-lg bg-gradient-to-r from-primary-500 to-purple-500 text-white font-medium text-sm flex items-center justify-center gap-2"
                        >
                            {isProcessing ? (
                                <>
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    {t.importing[language]}
                                </>
                            ) : (
                                <>
                                    <Upload className="w-4 h-4" />
                                    {t.import[language]}
                                </>
                            )}
                        </motion.button>
                    </motion.div>
                );

            case 'complete':
                return (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="text-center py-8"
                    >
                        <motion.div
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            transition={{ type: 'spring', delay: 0.2 }}
                            className="w-16 h-16 rounded-full bg-emerald-500 flex items-center justify-center mx-auto mb-4"
                        >
                            <CheckCircle className="w-8 h-8 text-white" />
                        </motion.div>
                        <h4 className="text-lg font-semibold mb-2">{t.success[language]}</h4>
                        <p className="text-sm text-muted-foreground">
                            {parsedNotes.length} {t.notes[language]}
                        </p>
                    </motion.div>
                );
        }
    };

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4"
            onClick={onClose}
        >
            <motion.div
                initial={{ scale: 0.95, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.95, opacity: 0 }}
                className="w-full max-w-md bg-card rounded-2xl shadow-2xl border border-border overflow-hidden"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div className="p-4 border-b border-border bg-gradient-to-r from-blue-500/10 to-violet-500/10 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <Upload className="w-5 h-5 text-blue-500" />
                        <h3 className="font-semibold">{t.title[language]}</h3>
                    </div>
                    <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-muted transition-colors">
                        <X className="w-4 h-4 text-muted-foreground" />
                    </button>
                </div>

                {/* Content */}
                <div className="p-4">
                    <AnimatePresence mode="wait">
                        {renderStep()}
                    </AnimatePresence>
                </div>
            </motion.div>
        </motion.div>
    );
}

export default ImportWizard;
