'use client';

/**
 * AttachmentUploader - Premium Dosya Yükleme Bileşeni
 * 
 * Özellikler:
 * - Drag & Drop desteği
 * - Çoklu dosya yükleme
 * - Progress bar
 * - Dosya türü ikonları
 * - 500MB limit
 */

import React, { useState, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Upload, 
  FileText, 
  FileSpreadsheet, 
  FileImage, 
  FileArchive, 
  FileVideo, 
  FileAudio, 
  File, 
  X, 
  CheckCircle2, 
  AlertCircle,
  Loader2,
  Paperclip
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { API_BASE_URL } from '@/lib/api';
import { NoteAttachment } from '@/store/useStore';

interface AttachmentUploaderProps {
  noteId: string;
  onUploadComplete: (attachment: NoteAttachment) => void;
  onClose: () => void;
  onError?: (message: string) => void;
  language?: 'tr' | 'en' | 'de';
  className?: string;
}

interface UploadingFile {
  id: string;
  file: File;
  progress: number;
  status: 'uploading' | 'completed' | 'error';
  error?: string;
}

const MAX_FILE_SIZE = 500 * 1024 * 1024; // 500 MB

// Dosya türüne göre ikon
function getFileIcon(mimeType: string, fileName: string) {
  const ext = fileName.split('.').pop()?.toLowerCase() || '';
  
  // Uzantıya göre kontrol
  if (['pdf'].includes(ext)) return <FileText className="w-5 h-5 text-red-500" />;
  if (['doc', 'docx', 'odt'].includes(ext)) return <FileText className="w-5 h-5 text-blue-500" />;
  if (['xls', 'xlsx', 'ods', 'csv'].includes(ext)) return <FileSpreadsheet className="w-5 h-5 text-green-500" />;
  if (['ppt', 'pptx', 'odp'].includes(ext)) return <FileText className="w-5 h-5 text-orange-500" />;
  if (['zip', 'rar', '7z', 'tar', 'gz'].includes(ext)) return <FileArchive className="w-5 h-5 text-amber-500" />;
  if (['mp4', 'avi', 'mov', 'mkv', 'webm'].includes(ext)) return <FileVideo className="w-5 h-5 text-purple-500" />;
  if (['mp3', 'wav', 'ogg', 'flac', 'm4a'].includes(ext)) return <FileAudio className="w-5 h-5 text-pink-500" />;
  if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp'].includes(ext)) return <FileImage className="w-5 h-5 text-cyan-500" />;
  
  // MIME type'a göre kontrol
  if (mimeType.startsWith('image/')) return <FileImage className="w-5 h-5 text-cyan-500" />;
  if (mimeType.startsWith('video/')) return <FileVideo className="w-5 h-5 text-purple-500" />;
  if (mimeType.startsWith('audio/')) return <FileAudio className="w-5 h-5 text-pink-500" />;
  if (mimeType.includes('pdf')) return <FileText className="w-5 h-5 text-red-500" />;
  if (mimeType.includes('word') || mimeType.includes('document')) return <FileText className="w-5 h-5 text-blue-500" />;
  if (mimeType.includes('excel') || mimeType.includes('spreadsheet')) return <FileSpreadsheet className="w-5 h-5 text-green-500" />;
  if (mimeType.includes('powerpoint') || mimeType.includes('presentation')) return <FileText className="w-5 h-5 text-orange-500" />;
  if (mimeType.includes('zip') || mimeType.includes('archive') || mimeType.includes('compressed')) return <FileArchive className="w-5 h-5 text-amber-500" />;
  
  return <File className="w-5 h-5 text-muted-foreground" />;
}

// Boyutu formatla
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Desteklenen dosya formatları
const SUPPORTED_FORMATS = [
  { label: 'PDF', color: 'text-red-500' },
  { label: 'Word', color: 'text-blue-500' },
  { label: 'Excel', color: 'text-green-500' },
  { label: 'PowerPoint', color: 'text-orange-500' },
  { label: 'Images', color: 'text-cyan-500' },
  { label: 'Videos', color: 'text-purple-500' },
  { label: 'Audio', color: 'text-pink-500' },
  { label: 'Archives', color: 'text-amber-500' },
];

const t = {
  dropzone: {
    tr: 'Dosyaları buraya sürükleyin veya tıklayarak seçin',
    en: 'Drag files here or click to select',
    de: 'Dateien hierher ziehen oder klicken zum Auswählen'
  },
  maxSize: {
    tr: 'Maksimum dosya boyutu:',
    en: 'Maximum file size:',
    de: 'Maximale Dateigröße:'
  },
  uploading: {
    tr: 'Yükleniyor...',
    en: 'Uploading...',
    de: 'Wird hochgeladen...'
  },
  uploaded: {
    tr: 'Yüklendi',
    en: 'Uploaded',
    de: 'Hochgeladen'
  },
  error: {
    tr: 'Hata',
    en: 'Error',
    de: 'Fehler'
  },
  tooLarge: {
    tr: 'Dosya çok büyük (max 500MB)',
    en: 'File too large (max 500MB)',
    de: 'Datei zu groß (max 500MB)'
  },
  supportedFormats: {
    tr: 'Desteklenen formatlar',
    en: 'Supported formats',
    de: 'Unterstützte Formate'
  },
  allFormats: {
    tr: 'Tüm dosya türleri desteklenir',
    en: 'All file types supported',
    de: 'Alle Dateitypen werden unterstützt'
  }
};

export function AttachmentUploader({ noteId, onUploadComplete, onClose, onError, language = 'en', className }: AttachmentUploaderProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Dosya yükleme
  const uploadFile = useCallback(async (file: File) => {
    const fileId = `upload-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    // Boyut kontrolü
    if (file.size > MAX_FILE_SIZE) {
      onError?.(t.tooLarge[language]);
      return;
    }

    // Uploading state'e ekle
    setUploadingFiles(prev => [...prev, {
      id: fileId,
      file,
      progress: 0,
      status: 'uploading'
    }]);

    try {
      const formData = new FormData();
      formData.append('file', file);

      // XMLHttpRequest ile progress takibi
      const xhr = new XMLHttpRequest();
      
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
          const progress = Math.round((e.loaded / e.total) * 100);
          setUploadingFiles(prev => prev.map(f => 
            f.id === fileId ? { ...f, progress } : f
          ));
        }
      };

      await new Promise<void>((resolve, reject) => {
        xhr.onload = async () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            try {
              const data = JSON.parse(xhr.responseText);
              
              const attachment: NoteAttachment = {
                id: data.id,
                name: data.name,
                original_name: data.original_name,
                url: data.url,
                file_type: data.file_type,
                size: data.size,
                uploaded_at: data.uploaded_at
              };

              // Başarılı
              setUploadingFiles(prev => prev.map(f => 
                f.id === fileId ? { ...f, progress: 100, status: 'completed' } : f
              ));

              onUploadComplete(attachment);
              
              // 2 saniye sonra listeden kaldır
              setTimeout(() => {
                setUploadingFiles(prev => prev.filter(f => f.id !== fileId));
              }, 2000);

              resolve();
            } catch (e) {
              reject(new Error('Invalid response'));
            }
          } else {
            reject(new Error(`Upload failed: ${xhr.status}`));
          }
        };

        xhr.onerror = () => reject(new Error('Network error'));
        xhr.ontimeout = () => reject(new Error('Timeout'));

        // Önce proxy, sonra direct
        xhr.open('POST', '/api/upload/file');
        xhr.send(formData);
      });

    } catch (error) {
      console.error('Upload error:', error);
      
      // Hata durumu
      setUploadingFiles(prev => prev.map(f => 
        f.id === fileId ? { ...f, status: 'error', error: String(error) } : f
      ));

      // Fallback: Doğrudan backend'e dene
      try {
        const formData = new FormData();
        formData.append('file', file);
        
        const res = await fetch(`${API_BASE_URL}/api/upload/file`, {
          method: 'POST',
          body: formData
        });

        if (res.ok) {
          const data = await res.json();
          
          const attachment: NoteAttachment = {
            id: data.id,
            name: data.name,
            original_name: data.original_name,
            url: data.url,
            file_type: data.file_type,
            size: data.size,
            uploaded_at: data.uploaded_at
          };

          setUploadingFiles(prev => prev.map(f => 
            f.id === fileId ? { ...f, progress: 100, status: 'completed' } : f
          ));

          onUploadComplete(attachment);
          
          setTimeout(() => {
            setUploadingFiles(prev => prev.filter(f => f.id !== fileId));
          }, 2000);
        } else {
          throw new Error('Direct upload also failed');
        }
      } catch (e2) {
        console.error('Fallback upload also failed:', e2);
        onError?.(language === 'tr' ? 'Dosya yüklenemedi' : 'File upload failed');
      }
    }
  }, [language, onUploadComplete, onError]);

  // Dosya seçildiğinde
  const handleFileSelect = useCallback((files: FileList | null) => {
    if (!files) return;
    
    Array.from(files).forEach(file => {
      uploadFile(file);
    });
  }, [uploadFile]);

  // Drag events
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
    handleFileSelect(e.dataTransfer.files);
  }, [handleFileSelect]);

  // Yükleniyor mu?
  const isUploading = uploadingFiles.some(f => f.status === 'uploading');

  // ESC tuşu ile kapatma
  React.useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !isUploading) onClose();
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [onClose, isUploading]);

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md"
      onClick={(e) => { if (e.target === e.currentTarget && !isUploading) onClose(); }}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.9, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.9, y: 20 }}
        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        className="w-full max-w-lg bg-card rounded-2xl shadow-2xl border border-border overflow-hidden"
        style={{ boxShadow: '0 25px 50px -12px rgba(99, 102, 241, 0.25)' }}
      >
        {/* Header - Premium Gradient */}
        <div className="relative flex items-center justify-between px-6 py-4 border-b border-border bg-gradient-to-r from-primary-500/10 via-purple-500/10 to-pink-500/10">
          <div className="absolute inset-0 bg-gradient-to-r from-primary-500/5 to-transparent" />
          <div className="relative flex items-center gap-3">
            <div className="p-2 bg-primary-500/20 rounded-xl">
              <Paperclip className="w-5 h-5 text-primary-500" />
            </div>
            <div>
              <h3 className="font-semibold text-lg">
                {language === 'tr' ? 'Dosya Ekle' : language === 'de' ? 'Datei anhängen' : 'Attach File'}
              </h3>
              <p className="text-xs text-muted-foreground">
                {t.allFormats[language]}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={isUploading}
            className={cn(
              "relative p-2 rounded-xl transition-all",
              isUploading 
                ? "opacity-50 cursor-not-allowed" 
                : "hover:bg-accent hover:scale-105 active:scale-95"
            )}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className={cn("p-6 space-y-4", className)}>
          {/* Dropzone */}
          <div
            onClick={() => fileInputRef.current?.click()}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={cn(
              "relative border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all",
              isDragOver
                ? "border-primary-500 bg-primary-50 dark:bg-primary-950/20"
                : "border-border hover:border-primary-400 hover:bg-muted/50"
            )}
          >
            <input
              ref={fileInputRef}
              type="file"
              multiple
              className="hidden"
              onChange={(e) => handleFileSelect(e.target.files)}
            />
            
            <div className="flex flex-col items-center gap-3">
              <motion.div 
              className={cn(
                "p-5 rounded-2xl transition-all duration-300",
                isDragOver 
                  ? "bg-gradient-to-br from-primary-500/30 to-purple-500/30 shadow-lg shadow-primary-500/20" 
                  : "bg-gradient-to-br from-muted to-muted/50"
              )}
              animate={{ scale: isDragOver ? 1.1 : 1 }}
              transition={{ type: 'spring', stiffness: 400, damping: 25 }}
            >
              {isUploading ? (
                <Loader2 className="w-10 h-10 text-primary-500 animate-spin" />
              ) : (
                <Upload className={cn(
                  "w-10 h-10 transition-all duration-300",
                  isDragOver ? "text-primary-500 scale-110" : "text-muted-foreground"
                )} />
              )}
            </motion.div>
              
            <div className="space-y-2">
              <p className={cn(
                "text-base font-medium transition-colors",
                isDragOver ? "text-primary-600" : "text-foreground"
              )}>
                {t.dropzone[language]}
              </p>
              <p className="text-sm text-muted-foreground">
                {t.maxSize[language]} <span className="font-semibold text-primary-500">500 MB</span>
              </p>
            </div>

            {/* Desteklenen Format Badges */}
            <div className="flex flex-wrap justify-center gap-1.5 mt-2 pt-3 border-t border-border/50">
              {SUPPORTED_FORMATS.map((format, idx) => (
                <span 
                  key={idx}
                  className={cn(
                    "px-2 py-0.5 text-[10px] font-medium rounded-full bg-background border border-border",
                    format.color
                  )}
                >
                  {format.label}
                </span>
              ))}
            </div>
          </div>
        </div>
        </div>

        {/* Yükleme Listesi */}
          <AnimatePresence>
            {uploadingFiles.length > 0 && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="px-6 pb-6 space-y-2"
              >
                {uploadingFiles.map(uploadFile => (
                  <motion.div
                    key={uploadFile.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                    className="flex items-center gap-3 p-3 bg-muted/50 rounded-lg border border-border"
                  >
                    {getFileIcon(uploadFile.file.type, uploadFile.file.name)}
                    
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{uploadFile.file.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {formatFileSize(uploadFile.file.size)}
                      </p>
                    </div>

                    {uploadFile.status === 'uploading' && (
                      <div className="flex items-center gap-2">
                        <div className="w-28 h-2 bg-muted rounded-full overflow-hidden">
                          <motion.div 
                            className="h-full bg-gradient-to-r from-primary-500 to-purple-500 rounded-full"
                            initial={{ width: 0 }}
                            animate={{ width: `${uploadFile.progress}%` }}
                            transition={{ duration: 0.3 }}
                          />
                        </div>
                        <span className="text-xs font-medium text-primary-500 w-10">
                          {uploadFile.progress}%
                        </span>
                      </div>
                    )}

                    {uploadFile.status === 'completed' && (
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ type: 'spring', stiffness: 500, damping: 25 }}
                      >
                        <CheckCircle2 className="w-5 h-5 text-green-500" />
                      </motion.div>
                    )}

                    {uploadFile.status === 'error' && (
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ type: 'spring', stiffness: 500, damping: 25 }}
                      >
                        <AlertCircle className="w-5 h-5 text-red-500" />
                      </motion.div>
                    )}
                  </motion.div>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
      </motion.div>
    </div>
  );
}

// Kompakt versiyon - toolbar için
export function AttachmentButton({ onClick, language = 'en' }: { onClick: () => void; language?: 'tr' | 'en' | 'de' }) {
  return (
    <button
      onClick={onClick}
      className="p-2 hover:bg-accent rounded-lg transition-colors"
      title={language === 'tr' ? 'Dosya Ekle' : language === 'de' ? 'Datei anhängen' : 'Attach File'}
    >
      <Paperclip className="w-4 h-4" />
    </button>
  );
}

export default AttachmentUploader;
