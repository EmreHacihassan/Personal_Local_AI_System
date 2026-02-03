'use client';

/**
 * AttachmentsList - Premium Dosya Listesi Bileşeni
 * 
 * Özellikler:
 * - Dosya türü ikonları
 * - İndirme butonu
 * - Önizleme butonu
 * - Silme butonu
 * - Boyut ve tarih gösterimi
 */

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  FileText, 
  FileSpreadsheet, 
  FileImage, 
  FileArchive, 
  FileVideo, 
  FileAudio, 
  File, 
  Download, 
  Trash2, 
  Eye,
  ExternalLink,
  MoreVertical,
  Paperclip
} from 'lucide-react';
import { cn, formatDate } from '@/lib/utils';
import { NoteAttachment } from '@/store/useStore';
import { API_BASE_URL } from '@/lib/api';

interface AttachmentsListProps {
  attachments: NoteAttachment[];
  onDelete?: (attachment: NoteAttachment) => void | Promise<void>;
  onPreview?: (attachment: NoteAttachment) => void;
  language?: 'tr' | 'en' | 'de';
  className?: string;
  compact?: boolean;  // Kompakt mod
}

// Dosya türüne göre ikon
function getFileIcon(fileType: string, fileName: string, size: 'sm' | 'md' | 'lg' = 'md') {
  const sizeClass = size === 'sm' ? 'w-4 h-4' : size === 'lg' ? 'w-8 h-8' : 'w-5 h-5';
  const ext = fileName.split('.').pop()?.toLowerCase() || '';
  
  // Uzantıya göre kontrol
  if (['pdf'].includes(ext)) return <FileText className={cn(sizeClass, "text-red-500")} />;
  if (['doc', 'docx', 'odt'].includes(ext)) return <FileText className={cn(sizeClass, "text-blue-500")} />;
  if (['xls', 'xlsx', 'ods', 'csv'].includes(ext)) return <FileSpreadsheet className={cn(sizeClass, "text-green-500")} />;
  if (['ppt', 'pptx', 'odp'].includes(ext)) return <FileText className={cn(sizeClass, "text-orange-500")} />;
  if (['zip', 'rar', '7z', 'tar', 'gz'].includes(ext)) return <FileArchive className={cn(sizeClass, "text-amber-500")} />;
  if (['mp4', 'avi', 'mov', 'mkv', 'webm'].includes(ext)) return <FileVideo className={cn(sizeClass, "text-purple-500")} />;
  if (['mp3', 'wav', 'ogg', 'flac', 'm4a'].includes(ext)) return <FileAudio className={cn(sizeClass, "text-pink-500")} />;
  if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp'].includes(ext)) return <FileImage className={cn(sizeClass, "text-cyan-500")} />;
  if (['txt', 'md', 'json', 'xml', 'html', 'css', 'js', 'ts'].includes(ext)) return <FileText className={cn(sizeClass, "text-gray-500")} />;
  
  // MIME type'a göre kontrol
  if (fileType?.startsWith('image/')) return <FileImage className={cn(sizeClass, "text-cyan-500")} />;
  if (fileType?.startsWith('video/')) return <FileVideo className={cn(sizeClass, "text-purple-500")} />;
  if (fileType?.startsWith('audio/')) return <FileAudio className={cn(sizeClass, "text-pink-500")} />;
  if (fileType?.includes('pdf')) return <FileText className={cn(sizeClass, "text-red-500")} />;
  
  return <File className={cn(sizeClass, "text-muted-foreground")} />;
}

// Boyutu formatla
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

// Önizlenebilir dosya mı?
function isPreviewable(fileType: string, fileName: string): boolean {
  const ext = fileName.split('.').pop()?.toLowerCase() || '';
  
  // PDF
  if (ext === 'pdf' || fileType?.includes('pdf')) return true;
  
  // Resimler
  if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp'].includes(ext)) return true;
  if (fileType?.startsWith('image/')) return true;
  
  // Metin dosyaları
  if (['txt', 'md', 'json', 'xml', 'html', 'css', 'js', 'ts', 'py', 'java', 'c', 'cpp', 'h'].includes(ext)) return true;
  if (fileType?.startsWith('text/')) return true;
  
  return false;
}

const t = {
  attachments: {
    tr: 'Ekler',
    en: 'Attachments',
    de: 'Anhänge'
  },
  download: {
    tr: 'İndir',
    en: 'Download',
    de: 'Herunterladen'
  },
  preview: {
    tr: 'Önizle',
    en: 'Preview',
    de: 'Vorschau'
  },
  delete: {
    tr: 'Sil',
    en: 'Delete',
    de: 'Löschen'
  },
  noAttachments: {
    tr: 'Ek dosya yok',
    en: 'No attachments',
    de: 'Keine Anhänge'
  },
  confirmDelete: {
    tr: 'Bu dosyayı silmek istediğinize emin misiniz?',
    en: 'Are you sure you want to delete this file?',
    de: 'Sind Sie sicher, dass Sie diese Datei löschen möchten?'
  }
};

export function AttachmentsList({ 
  attachments, 
  onDelete, 
  onPreview, 
  language = 'en', 
  className,
  compact = false
}: AttachmentsListProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  if (!attachments || attachments.length === 0) {
    return null;
  }

  // Dosya indirme
  const handleDownload = async (attachment: NoteAttachment) => {
    try {
      // Proxy üzerinden indir
      window.open(`/api/upload/file/${attachment.id}`, '_blank');
    } catch (error) {
      // Fallback: Doğrudan URL
      window.open(`${API_BASE_URL}${attachment.url}`, '_blank');
    }
  };

  // Dosya silme
  const handleDelete = async (attachment: NoteAttachment) => {
    if (!onDelete) return;
    
    setDeletingId(attachment.id);
    
    try {
      // Parent component handles the API call
      await onDelete(attachment);
    } finally {
      setDeletingId(null);
    }
  };

  // Kompakt mod (not kartlarında gösterilecek)
  if (compact) {
    return (
      <div className={cn("flex items-center gap-1 flex-wrap", className)}>
        <Paperclip className="w-3 h-3 text-muted-foreground" />
        <span className="text-xs text-muted-foreground">
          {attachments.length} {language === 'tr' ? 'ek' : 'attachments'}
        </span>
      </div>
    );
  }

  return (
    <div className={cn("space-y-3", className)}>
      {/* Başlık - Premium Gradient */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-gradient-to-br from-primary-500/20 to-purple-500/20 rounded-lg">
            <Paperclip className="w-4 h-4 text-primary-500" />
          </div>
          <span className="text-sm font-semibold bg-gradient-to-r from-primary-600 to-purple-600 bg-clip-text text-transparent">
            {t.attachments[language]}
          </span>
          <span className="px-1.5 py-0.5 text-xs font-medium bg-primary-500/10 text-primary-600 rounded-full">
            {attachments.length}
          </span>
        </div>
      </div>

      {/* Liste - Premium Style */}
      <div className="space-y-2">
        <AnimatePresence>
          {attachments.map((attachment, index) => (
            <motion.div
              key={attachment.id}
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 10, scale: 0.95 }}
              transition={{ delay: index * 0.05 }}
              className={cn(
                "group relative flex items-center gap-3 p-3 rounded-xl border transition-all duration-200",
                "bg-gradient-to-r from-muted/50 to-transparent hover:from-muted hover:to-muted/30",
                "border-border/50 hover:border-primary-500/30 hover:shadow-lg hover:shadow-primary-500/5",
                deletingId === attachment.id && "opacity-50 pointer-events-none scale-95"
              )}
            >
              {/* Glow Effect */}
              <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-primary-500/0 to-purple-500/0 group-hover:from-primary-500/5 group-hover:to-purple-500/5 transition-all" />

              {/* İkon - Premium Badge */}
              <div className="relative flex-shrink-0 p-2.5 bg-gradient-to-br from-background to-muted rounded-xl border border-border shadow-sm group-hover:shadow-md transition-all">
                {getFileIcon(attachment.file_type, attachment.original_name)}
              </div>

              {/* Bilgiler */}
              <div className="relative flex-1 min-w-0">
                <p className="text-sm font-medium truncate group-hover:text-primary-600 transition-colors" title={attachment.original_name}>
                  {attachment.original_name}
                </p>
                <div className="flex items-center gap-2 text-xs text-muted-foreground mt-0.5">
                  <span className="font-medium">{formatFileSize(attachment.size)}</span>
                  <span className="text-muted-foreground/50">•</span>
                  <span>{formatDate(new Date(attachment.uploaded_at))}</span>
                </div>
              </div>

              {/* Butonlar - Premium */}
              <div className="relative flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-all duration-200 translate-x-2 group-hover:translate-x-0">
                {/* Önizleme */}
                {isPreviewable(attachment.file_type, attachment.original_name) && onPreview && (
                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => onPreview(attachment)}
                    className="p-2 hover:bg-primary-500/10 rounded-lg transition-colors"
                    title={t.preview[language]}
                  >
                    <Eye className="w-4 h-4 text-primary-500" />
                  </motion.button>
                )}

                {/* İndirme */}
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => handleDownload(attachment)}
                  className="p-2 hover:bg-green-500/10 rounded-lg transition-colors"
                  title={t.download[language]}
                >
                  <Download className="w-4 h-4 text-green-500" />
                </motion.button>

                {/* Yeni sekmede aç */}
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => window.open(`${API_BASE_URL}${attachment.url}`, '_blank')}
                  className="p-2 hover:bg-blue-500/10 rounded-lg transition-colors"
                  title={language === 'tr' ? 'Yeni sekmede aç' : 'Open in new tab'}
                >
                  <ExternalLink className="w-4 h-4 text-blue-500" />
                </motion.button>

                {/* Silme */}
                {onDelete && (
                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => {
                      if (confirm(t.confirmDelete[language])) {
                        handleDelete(attachment);
                      }
                    }}
                    className="p-2 hover:bg-red-500/10 rounded-lg transition-colors"
                    title={t.delete[language]}
                  >
                    <Trash2 className="w-4 h-4 text-red-500" />
                  </motion.button>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}

// Kompakt badge
export function AttachmentBadge({ count, language = 'en' }: { count: number; language?: 'tr' | 'en' | 'de' }) {
  if (count === 0) return null;
  
  return (
    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-primary-500/10 text-primary-600 text-xs rounded-md">
      <Paperclip className="w-3 h-3" />
      {count}
    </span>
  );
}

export default AttachmentsList;
