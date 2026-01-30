'use client';

/**
 * ExportModal - Dışa Aktarma Modal'ı
 * 
 * PDF, Markdown, JSON export seçenekleri.
 * Premium tasarımlı PDF çıktısı.
 */

import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Download,
    FileText,
    FileJson,
    Image,
    Folder,
    CheckCircle,
    Loader2,
    X,
    Settings,
    Palette,
    FileType
} from 'lucide-react';
import { Note, NoteFolder } from '@/store/useStore';
import { cn, formatDate } from '@/lib/utils';

interface ExportModalProps {
    notes: Note[];
    folders: NoteFolder[];
    selectedNotes?: Note[];
    onClose: () => void;
    language?: 'tr' | 'en' | 'de';
}

type ExportFormat = 'pdf' | 'markdown' | 'json';
type ExportScope = 'selected' | 'folder' | 'all';

interface ExportOptions {
    format: ExportFormat;
    scope: ExportScope;
    folderId?: string;
    includeMetadata: boolean;
    darkMode: boolean;
    includeTableOfContents: boolean;
}

const translations = {
    title: { tr: 'Dışa Aktar', en: 'Export', de: 'Exportieren' },
    format: { tr: 'Format', en: 'Format', de: 'Format' },
    scope: { tr: 'Kapsam', en: 'Scope', de: 'Bereich' },
    selected: { tr: 'Seçili Notlar', en: 'Selected Notes', de: 'Ausgewählte Notizen' },
    folder: { tr: 'Klasör', en: 'Folder', de: 'Ordner' },
    all: { tr: 'Tüm Notlar', en: 'All Notes', de: 'Alle Notizen' },
    options: { tr: 'Seçenekler', en: 'Options', de: 'Optionen' },
    includeMetadata: { tr: 'Metadata dahil et', en: 'Include metadata', de: 'Metadaten einschließen' },
    darkMode: { tr: 'Koyu tema', en: 'Dark mode', de: 'Dunkler Modus' },
    tableOfContents: { tr: 'İçindekiler tablosu', en: 'Table of contents', de: 'Inhaltsverzeichnis' },
    export: { tr: 'Dışa Aktar', en: 'Export', de: 'Exportieren' },
    exporting: { tr: 'Hazırlanıyor...', en: 'Preparing...', de: 'Wird vorbereitet...' },
    success: { tr: 'İndirme başladı!', en: 'Download started!', de: 'Download gestartet!' },
};

const FORMAT_OPTIONS = [
    { id: 'pdf' as ExportFormat, name: 'PDF', icon: FileText, color: 'from-red-500 to-rose-500', desc: 'Premium tasarımlı PDF' },
    { id: 'markdown' as ExportFormat, name: 'Markdown', icon: FileType, color: 'from-blue-500 to-cyan-500', desc: '.md dosyaları' },
    { id: 'json' as ExportFormat, name: 'JSON', icon: FileJson, color: 'from-amber-500 to-orange-500', desc: 'Tam yedekleme' },
];

export function ExportModal({
    notes,
    folders,
    selectedNotes = [],
    onClose,
    language = 'tr'
}: ExportModalProps) {
    const t = translations;

    const [options, setOptions] = useState<ExportOptions>({
        format: 'pdf',
        scope: selectedNotes.length > 0 ? 'selected' : 'all',
        includeMetadata: true,
        darkMode: false,
        includeTableOfContents: true,
    });

    const [isExporting, setIsExporting] = useState(false);
    const [exportSuccess, setExportSuccess] = useState(false);

    // Export edilecek notları belirle
    const getNotesToExport = useCallback((): Note[] => {
        switch (options.scope) {
            case 'selected':
                return selectedNotes;
            case 'folder':
                return notes.filter(n => n.folder === options.folderId);
            case 'all':
            default:
                return notes;
        }
    }, [notes, selectedNotes, options.scope, options.folderId]);

    // PDF Export
    const exportToPdf = async (notesToExport: Note[]) => {
        // Generate HTML content
        const htmlContent = generatePdfHtml(notesToExport, options, folders, language);

        // Create a new window and print
        const printWindow = window.open('', '_blank');
        if (printWindow) {
            printWindow.document.write(htmlContent);
            printWindow.document.close();
            printWindow.focus();

            // Auto-trigger print dialog
            setTimeout(() => {
                printWindow.print();
            }, 500);
        }
    };

    // Markdown Export
    const exportToMarkdown = async (notesToExport: Note[]) => {
        if (notesToExport.length === 1) {
            // Single file download
            const note = notesToExport[0];
            const content = generateMarkdown(note, options.includeMetadata);
            downloadFile(`${note.title}.md`, content, 'text/markdown');
        } else {
            // Multiple files - create as single markdown with sections
            const content = notesToExport.map(note => {
                return `# ${note.title}\n\n${options.includeMetadata ? `> 📅 ${formatDate(note.updatedAt)}\n\n` : ''}${note.content}`;
            }).join('\n\n---\n\n');

            downloadFile('notes-export.md', content, 'text/markdown');
        }
    };

    // JSON Export
    const exportToJson = async (notesToExport: Note[]) => {
        const exportData = {
            exportDate: new Date().toISOString(),
            noteCount: notesToExport.length,
            notes: notesToExport.map(note => ({
                id: note.id,
                title: note.title,
                content: note.content,
                folder: note.folder,
                color: note.color,
                tags: note.tags,
                isPinned: note.isPinned,
                createdAt: note.createdAt,
                updatedAt: note.updatedAt,
            })),
            folders: folders.map(folder => ({
                id: folder.id,
                name: folder.name,
                parentId: folder.parentId,
                color: folder.color,
                icon: folder.icon,
            })),
        };

        const content = JSON.stringify(exportData, null, 2);
        downloadFile('notes-backup.json', content, 'application/json');
    };

    // Download helper
    const downloadFile = (filename: string, content: string, mimeType: string) => {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    // Main export handler
    const handleExport = async () => {
        setIsExporting(true);

        try {
            const notesToExport = getNotesToExport();

            switch (options.format) {
                case 'pdf':
                    await exportToPdf(notesToExport);
                    break;
                case 'markdown':
                    await exportToMarkdown(notesToExport);
                    break;
                case 'json':
                    await exportToJson(notesToExport);
                    break;
            }

            setExportSuccess(true);
            setTimeout(() => onClose(), 1500);
        } catch (error) {
            console.error('Export error:', error);
        } finally {
            setIsExporting(false);
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
                className="w-full max-w-lg bg-card rounded-2xl shadow-2xl border border-border overflow-hidden"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div className="p-4 border-b border-border bg-gradient-to-r from-emerald-500/10 to-teal-500/10">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="p-2.5 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-500">
                                <Download className="w-5 h-5 text-white" />
                            </div>
                            <div>
                                <h2 className="font-semibold text-lg">{t.title[language]}</h2>
                                <p className="text-xs text-muted-foreground">
                                    {getNotesToExport().length} not
                                </p>
                            </div>
                        </div>
                        <button onClick={onClose} className="p-2 rounded-lg hover:bg-muted transition-colors">
                            <X className="w-5 h-5 text-muted-foreground" />
                        </button>
                    </div>
                </div>

                {/* Content */}
                <div className="p-4 space-y-6">
                    {/* Format Selection */}
                    <div>
                        <label className="text-sm font-medium mb-3 block flex items-center gap-2">
                            <FileType className="w-4 h-4 text-muted-foreground" />
                            {t.format[language]}
                        </label>
                        <div className="grid grid-cols-3 gap-2">
                            {FORMAT_OPTIONS.map(format => (
                                <motion.button
                                    key={format.id}
                                    whileHover={{ scale: 1.02 }}
                                    whileTap={{ scale: 0.98 }}
                                    onClick={() => setOptions(prev => ({ ...prev, format: format.id }))}
                                    className={cn(
                                        "p-3 rounded-xl border transition-all text-left",
                                        options.format === format.id
                                            ? "border-primary-500 bg-primary-500/10"
                                            : "border-border hover:border-primary-500/50"
                                    )}
                                >
                                    <div className={cn(
                                        "w-8 h-8 rounded-lg flex items-center justify-center mb-2 bg-gradient-to-br",
                                        format.color
                                    )}>
                                        <format.icon className="w-4 h-4 text-white" />
                                    </div>
                                    <p className="text-sm font-medium">{format.name}</p>
                                    <p className="text-[10px] text-muted-foreground">{format.desc}</p>
                                </motion.button>
                            ))}
                        </div>
                    </div>

                    {/* Scope Selection */}
                    <div>
                        <label className="text-sm font-medium mb-3 block flex items-center gap-2">
                            <Folder className="w-4 h-4 text-muted-foreground" />
                            {t.scope[language]}
                        </label>
                        <div className="flex gap-2">
                            {selectedNotes.length > 0 && (
                                <button
                                    onClick={() => setOptions(prev => ({ ...prev, scope: 'selected' }))}
                                    className={cn(
                                        "flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                                        options.scope === 'selected'
                                            ? "bg-primary-500 text-white"
                                            : "bg-muted text-muted-foreground hover:bg-muted/80"
                                    )}
                                >
                                    {t.selected[language]} ({selectedNotes.length})
                                </button>
                            )}
                            <button
                                onClick={() => setOptions(prev => ({ ...prev, scope: 'all' }))}
                                className={cn(
                                    "flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                                    options.scope === 'all'
                                        ? "bg-primary-500 text-white"
                                        : "bg-muted text-muted-foreground hover:bg-muted/80"
                                )}
                            >
                                {t.all[language]} ({notes.length})
                            </button>
                        </div>
                    </div>

                    {/* Options */}
                    <div>
                        <label className="text-sm font-medium mb-3 block flex items-center gap-2">
                            <Settings className="w-4 h-4 text-muted-foreground" />
                            {t.options[language]}
                        </label>
                        <div className="space-y-2">
                            <label className="flex items-center gap-3 p-2 rounded-lg hover:bg-muted cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={options.includeMetadata}
                                    onChange={(e) => setOptions(prev => ({ ...prev, includeMetadata: e.target.checked }))}
                                    className="w-4 h-4 rounded border-border text-primary-500 focus:ring-primary-500"
                                />
                                <span className="text-sm">{t.includeMetadata[language]}</span>
                            </label>
                            {options.format === 'pdf' && (
                                <>
                                    <label className="flex items-center gap-3 p-2 rounded-lg hover:bg-muted cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={options.includeTableOfContents}
                                            onChange={(e) => setOptions(prev => ({ ...prev, includeTableOfContents: e.target.checked }))}
                                            className="w-4 h-4 rounded border-border text-primary-500 focus:ring-primary-500"
                                        />
                                        <span className="text-sm">{t.tableOfContents[language]}</span>
                                    </label>
                                    <label className="flex items-center gap-3 p-2 rounded-lg hover:bg-muted cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={options.darkMode}
                                            onChange={(e) => setOptions(prev => ({ ...prev, darkMode: e.target.checked }))}
                                            className="w-4 h-4 rounded border-border text-primary-500 focus:ring-primary-500"
                                        />
                                        <span className="text-sm">{t.darkMode[language]}</span>
                                    </label>
                                </>
                            )}
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="p-4 border-t border-border bg-muted/30">
                    <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={handleExport}
                        disabled={isExporting || exportSuccess}
                        className={cn(
                            "w-full py-3 rounded-xl font-medium transition-all flex items-center justify-center gap-2",
                            exportSuccess
                                ? "bg-emerald-500 text-white"
                                : "bg-gradient-to-r from-primary-500 to-purple-500 text-white hover:opacity-90"
                        )}
                    >
                        {isExporting ? (
                            <>
                                <Loader2 className="w-4 h-4 animate-spin" />
                                {t.exporting[language]}
                            </>
                        ) : exportSuccess ? (
                            <>
                                <CheckCircle className="w-4 h-4" />
                                {t.success[language]}
                            </>
                        ) : (
                            <>
                                <Download className="w-4 h-4" />
                                {t.export[language]}
                            </>
                        )}
                    </motion.button>
                </div>
            </motion.div>
        </motion.div>
    );
}

// Premium PDF HTML Generator
function generatePdfHtml(
    notes: Note[],
    options: ExportOptions,
    folders: NoteFolder[],
    language: string
): string {
    const isDark = options.darkMode;
    const getFolderName = (folderId?: string) => {
        if (!folderId) return 'Genel';
        const folder = folders.find(f => f.id === folderId);
        return folder?.name || 'Genel';
    };

    return `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Notlar Export - ${new Date().toLocaleDateString()}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    
    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      line-height: 1.6;
      color: ${isDark ? '#e5e7eb' : '#1f2937'};
      background: ${isDark ? '#111827' : '#ffffff'};
      padding: 40px;
    }
    
    .header {
      text-align: center;
      margin-bottom: 40px;
      padding-bottom: 20px;
      border-bottom: 2px solid ${isDark ? '#374151' : '#e5e7eb'};
    }
    
    .header h1 {
      font-size: 28px;
      font-weight: 700;
      background: linear-gradient(135deg, #6366f1, #a855f7);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 8px;
    }
    
    .header p {
      color: ${isDark ? '#9ca3af' : '#6b7280'};
      font-size: 14px;
    }
    
    .toc {
      background: ${isDark ? '#1f2937' : '#f9fafb'};
      border-radius: 12px;
      padding: 24px;
      margin-bottom: 40px;
    }
    
    .toc h2 {
      font-size: 18px;
      margin-bottom: 16px;
      color: ${isDark ? '#e5e7eb' : '#1f2937'};
    }
    
    .toc ul {
      list-style: none;
    }
    
    .toc li {
      padding: 8px 0;
      border-bottom: 1px solid ${isDark ? '#374151' : '#e5e7eb'};
    }
    
    .toc li:last-child {
      border-bottom: none;
    }
    
    .toc a {
      color: #6366f1;
      text-decoration: none;
    }
    
    .note {
      margin-bottom: 40px;
      page-break-inside: avoid;
    }
    
    .note-header {
      background: linear-gradient(135deg, ${isDark ? '#1f2937' : '#f3f4f6'}, ${isDark ? '#374151' : '#e5e7eb'});
      border-radius: 12px 12px 0 0;
      padding: 20px 24px;
      border-left: 4px solid #6366f1;
    }
    
    .note-title {
      font-size: 20px;
      font-weight: 600;
      margin-bottom: 8px;
    }
    
    .note-meta {
      display: flex;
      gap: 16px;
      font-size: 12px;
      color: ${isDark ? '#9ca3af' : '#6b7280'};
    }
    
    .note-content {
      background: ${isDark ? '#1f2937' : '#ffffff'};
      border: 1px solid ${isDark ? '#374151' : '#e5e7eb'};
      border-top: none;
      border-radius: 0 0 12px 12px;
      padding: 24px;
      white-space: pre-wrap;
    }
    
    .footer {
      text-align: center;
      margin-top: 60px;
      padding-top: 20px;
      border-top: 2px solid ${isDark ? '#374151' : '#e5e7eb'};
      color: ${isDark ? '#6b7280' : '#9ca3af'};
      font-size: 12px;
    }
    
    @media print {
      body {
        padding: 20px;
      }
      .note {
        page-break-inside: avoid;
      }
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>📝 Notlarım</h1>
    <p>Exported on ${new Date().toLocaleDateString(language === 'tr' ? 'tr-TR' : 'en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    })} • ${notes.length} notes</p>
  </div>

  ${options.includeTableOfContents ? `
  <div class="toc">
    <h2>📋 İçindekiler</h2>
    <ul>
      ${notes.map((note, i) => `<li>${i + 1}. ${note.title}</li>`).join('')}
    </ul>
  </div>
  ` : ''}

  ${notes.map((note, i) => `
  <div class="note" id="note-${i}">
    <div class="note-header">
      <h3 class="note-title">${note.title}</h3>
      ${options.includeMetadata ? `
      <div class="note-meta">
        <span>📁 ${getFolderName(note.folder)}</span>
        <span>📅 ${formatDate(note.updatedAt)}</span>
        ${note.tags && note.tags.length > 0 ? `<span>🏷️ ${note.tags.join(', ')}</span>` : ''}
      </div>
      ` : ''}
    </div>
    <div class="note-content">${note.content || 'Boş not'}</div>
  </div>
  `).join('')}

  <div class="footer">
    <p>Generated by AgenticManagingSystem • Premium Export</p>
  </div>
</body>
</html>
  `;
}

// Markdown Generator
function generateMarkdown(note: Note, includeMetadata: boolean): string {
    let md = `# ${note.title}\n\n`;

    if (includeMetadata) {
        md += `> 📅 Updated: ${formatDate(note.updatedAt)}\n`;
        if (note.tags && note.tags.length > 0) {
            md += `> 🏷️ Tags: ${note.tags.join(', ')}\n`;
        }
        md += '\n---\n\n';
    }

    md += note.content;

    return md;
}

export default ExportModal;
