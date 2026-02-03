'use client';

/**
 * FilePreviewModal - Premium Dosya Önizleme Modalı
 * 
 * Özellikler:
 * - PDF inline görüntüleme (iframe)
 * - Resim büyütme
 * - Metin dosyası görüntüleme
 * - İndirme butonu
 * - Tam ekran modu
 */

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  X, 
  Download, 
  Maximize2, 
  Minimize2, 
  ExternalLink,
  FileText,
  ZoomIn,
  ZoomOut,
  RotateCw,
  Loader2
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { NoteAttachment } from '@/store/useStore';
import { API_BASE_URL } from '@/lib/api';

interface FilePreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  attachment: NoteAttachment | null;
  language?: 'tr' | 'en' | 'de';
}

// Dosya türünü belirle
function getPreviewType(fileType: string, fileName: string): 'pdf' | 'image' | 'text' | 'video' | 'audio' | 'other' {
  const ext = fileName.split('.').pop()?.toLowerCase() || '';
  
  if (ext === 'pdf' || fileType?.includes('pdf')) return 'pdf';
  if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp'].includes(ext)) return 'image';
  if (fileType?.startsWith('image/')) return 'image';
  if (['txt', 'md', 'json', 'xml', 'html', 'css', 'js', 'ts', 'py', 'java', 'c', 'cpp', 'h', 'log', 'yaml', 'yml'].includes(ext)) return 'text';
  if (fileType?.startsWith('text/')) return 'text';
  if (['mp4', 'webm', 'ogg'].includes(ext)) return 'video';
  if (fileType?.startsWith('video/')) return 'video';
  if (['mp3', 'wav', 'ogg', 'm4a'].includes(ext)) return 'audio';
  if (fileType?.startsWith('audio/')) return 'audio';
  
  return 'other';
}

// Boyutu formatla
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

const t = {
  preview: {
    tr: 'Önizleme',
    en: 'Preview',
    de: 'Vorschau'
  },
  download: {
    tr: 'İndir',
    en: 'Download',
    de: 'Herunterladen'
  },
  openNew: {
    tr: 'Yeni sekmede aç',
    en: 'Open in new tab',
    de: 'In neuem Tab öffnen'
  },
  fullscreen: {
    tr: 'Tam ekran',
    en: 'Fullscreen',
    de: 'Vollbild'
  },
  loading: {
    tr: 'Yükleniyor...',
    en: 'Loading...',
    de: 'Wird geladen...'
  },
  notPreviewable: {
    tr: 'Bu dosya türü önizlenemez',
    en: 'This file type cannot be previewed',
    de: 'Dieser Dateityp kann nicht angezeigt werden'
  },
  downloadToView: {
    tr: 'Görüntülemek için indirin',
    en: 'Download to view',
    de: 'Zum Ansehen herunterladen'
  }
};

export function FilePreviewModal({ isOpen, onClose, attachment, language = 'en' }: FilePreviewModalProps) {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [imageZoom, setImageZoom] = useState(1);
  const [imageRotation, setImageRotation] = useState(0);
  const [textContent, setTextContent] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // ESC tuşu ile kapatma
  useEffect(() => {
    if (!isOpen) return;
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [isOpen, onClose]);

  // Reset state when attachment changes
  useEffect(() => {
    setImageZoom(1);
    setImageRotation(0);
    setTextContent(null);
    setIsLoading(true);
  }, [attachment?.id]);

  // Metin dosyası içeriğini yükle
  useEffect(() => {
    if (!attachment) return;
    
    const previewType = getPreviewType(attachment.file_type, attachment.original_name);
    
    if (previewType === 'text') {
      setIsLoading(true);
      fetch(`${API_BASE_URL}${attachment.url}`)
        .then(res => res.text())
        .then(text => {
          setTextContent(text);
          setIsLoading(false);
        })
        .catch(err => {
          console.error('Error loading text file:', err);
          setTextContent('Error loading file content');
          setIsLoading(false);
        });
    } else {
      setIsLoading(false);
    }
  }, [attachment]);

  if (!attachment) return null;

  const previewType = getPreviewType(attachment.file_type, attachment.original_name);
  const fileUrl = `${API_BASE_URL}${attachment.url}`;

  // İndirme
  const handleDownload = () => {
    window.open(`${API_BASE_URL}/api/upload/file/${attachment.id}`, '_blank');
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md"
          onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 30 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 30 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className={cn(
              "bg-card/95 backdrop-blur-xl border border-border rounded-2xl shadow-2xl overflow-hidden flex flex-col",
              isFullscreen 
                ? "fixed inset-4" 
                : "w-full max-w-5xl max-h-[90vh]"
            )}
            style={{ boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255,255,255,0.1)' }}
          >
            {/* Header - Premium Gradient */}
            <div className="relative flex items-center justify-between px-6 py-4 border-b border-border bg-gradient-to-r from-primary-500/5 via-purple-500/5 to-pink-500/5">
              <div className="absolute inset-0 bg-gradient-to-b from-white/5 to-transparent" />
              <div className="relative flex items-center gap-3 min-w-0">
                <div className="p-2.5 bg-gradient-to-br from-primary-500/20 to-purple-500/20 rounded-xl shadow-lg shadow-primary-500/10">
                  <FileText className="w-5 h-5 text-primary-500" />
                </div>
                <div className="min-w-0">
                  <h3 className="font-semibold text-lg truncate">{attachment.original_name}</h3>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span className="font-medium">{formatFileSize(attachment.size)}</span>
                    <span className="text-muted-foreground/50">•</span>
                    <span className="px-1.5 py-0.5 bg-muted rounded-md font-mono text-[10px]">
                      {attachment.file_type.split('/').pop()}
                    </span>
                  </div>
                </div>
              </div>

              <div className="relative flex items-center gap-1">
                {/* Resim kontrolleri - Premium */}
                {previewType === 'image' && (
                  <>
                    <div className="flex items-center gap-1 px-2 py-1 bg-muted/50 rounded-lg">
                      <motion.button
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => setImageZoom(z => Math.max(0.25, z - 0.25))}
                        className="p-1.5 hover:bg-accent rounded-md transition-colors"
                        title="Zoom Out"
                      >
                        <ZoomOut className="w-4 h-4" />
                      </motion.button>
                      
                      {/* Zoom Slider */}
                      <div className="flex items-center gap-2 px-2">
                        <input
                          type="range"
                          min="25"
                          max="400"
                          value={imageZoom * 100}
                          onChange={(e) => setImageZoom(parseInt(e.target.value) / 100)}
                          className="w-20 h-1 bg-border rounded-full appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:bg-primary-500 [&::-webkit-slider-thumb]:rounded-full"
                        />
                        <span className="text-xs font-medium text-primary-500 w-10 text-center">
                          {Math.round(imageZoom * 100)}%
                        </span>
                      </div>
                      
                      <motion.button
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => setImageZoom(z => Math.min(4, z + 0.25))}
                        className="p-1.5 hover:bg-accent rounded-md transition-colors"
                        title="Zoom In"
                      >
                        <ZoomIn className="w-4 h-4" />
                      </motion.button>
                    </div>
                    
                    <motion.button
                      whileHover={{ scale: 1.1, rotate: 90 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => setImageRotation(r => (r + 90) % 360)}
                      className="p-2 hover:bg-accent rounded-lg transition-colors"
                      title="Rotate"
                    >
                      <RotateCw className="w-4 h-4" />
                    </motion.button>
                    
                    <div className="w-px h-6 bg-border mx-1" />
                  </>
                )}

                {/* Tam ekran */}
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => setIsFullscreen(!isFullscreen)}
                  className="p-2 hover:bg-accent rounded-lg transition-colors"
                  title={t.fullscreen[language]}
                >
                  {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
                </motion.button>

                {/* Yeni sekmede aç */}
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => window.open(fileUrl, '_blank')}
                  className="p-2 hover:bg-accent rounded-lg transition-colors"
                  title={t.openNew[language]}
                >
                  <ExternalLink className="w-4 h-4" />
                </motion.button>

                {/* İndir */}
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={handleDownload}
                  className="p-2 hover:bg-green-500/10 rounded-lg transition-colors"
                  title={t.download[language]}
                >
                  <Download className="w-4 h-4 text-green-500" />
                </motion.button>

                {/* Kapat */}
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={onClose}
                  className="p-2 hover:bg-red-500/10 rounded-lg transition-colors ml-1"
                >
                  <X className="w-5 h-5 text-red-500" />
                </motion.button>
              </div>
            </div>

            {/* İçerik - Premium Background */}
            <div className="flex-1 overflow-hidden bg-gradient-to-br from-muted/30 via-background to-muted/20">
              {isLoading ? (
                <div className="flex flex-col items-center justify-center h-full gap-3">
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                  >
                    <Loader2 className="w-10 h-10 text-primary-500" />
                  </motion.div>
                  <p className="text-sm text-muted-foreground">{t.loading[language]}</p>
                </div>
              ) : (
                <>
                  {/* PDF */}
                  {previewType === 'pdf' && (
                    <iframe
                      src={`${fileUrl}#toolbar=1&navpanes=1&scrollbar=1`}
                      className="w-full h-full min-h-[600px]"
                      title={attachment.original_name}
                    />
                  )}

                  {/* Resim */}
                  {previewType === 'image' && (
                    <div className="w-full h-full overflow-auto flex items-center justify-center p-4">
                      <img
                        src={fileUrl}
                        alt={attachment.original_name}
                        className="max-w-full max-h-full object-contain transition-transform duration-200"
                        style={{
                          transform: `scale(${imageZoom}) rotate(${imageRotation}deg)`
                        }}
                        onLoad={() => setIsLoading(false)}
                      />
                    </div>
                  )}

                  {/* Metin - Code highlighting style */}
                  {previewType === 'text' && textContent !== null && (
                    <div className="w-full h-full overflow-auto p-6">
                      <div className="relative">
                        {/* Line Numbers */}
                        <pre className="text-sm font-mono bg-gradient-to-br from-background to-muted/50 p-6 rounded-xl border border-border shadow-inner">
                          <code className="text-foreground/90 leading-relaxed">
                            {textContent}
                          </code>
                        </pre>
                      </div>
                    </div>
                  )}

                  {/* Video */}
                  {previewType === 'video' && (
                    <div className="w-full h-full flex items-center justify-center p-4">
                      <video
                        src={fileUrl}
                        controls
                        className="max-w-full max-h-full rounded-lg"
                      >
                        Your browser does not support video playback.
                      </video>
                    </div>
                  )}

                  {/* Audio */}
                  {previewType === 'audio' && (
                    <div className="w-full h-full flex items-center justify-center p-8">
                      <div className="w-full max-w-md bg-background p-6 rounded-xl border border-border">
                        <div className="flex items-center gap-4 mb-4">
                          <div className="p-4 bg-primary-500/10 rounded-full">
                            <FileText className="w-8 h-8 text-primary-500" />
                          </div>
                          <div>
                            <p className="font-medium">{attachment.original_name}</p>
                            <p className="text-sm text-muted-foreground">{formatFileSize(attachment.size)}</p>
                          </div>
                        </div>
                        <audio
                          src={fileUrl}
                          controls
                          className="w-full"
                        >
                          Your browser does not support audio playback.
                        </audio>
                      </div>
                    </div>
                  )}

                  {/* Diğer - Premium Empty State */}
                  {previewType === 'other' && (
                    <div className="w-full h-full flex flex-col items-center justify-center p-8">
                      <motion.div 
                        initial={{ scale: 0.9, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        className="p-8 bg-gradient-to-br from-muted to-muted/50 rounded-3xl shadow-xl mb-6"
                      >
                        <FileText className="w-16 h-16 text-muted-foreground" />
                      </motion.div>
                      <h4 className="text-xl font-semibold mb-2">{attachment.original_name}</h4>
                      <p className="text-sm text-muted-foreground mb-8">{t.notPreviewable[language]}</p>
                      <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={handleDownload}
                        className="flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-primary-500 to-purple-500 hover:from-primary-600 hover:to-purple-600 text-white rounded-2xl font-medium shadow-lg shadow-primary-500/25 transition-all"
                      >
                        <Download className="w-5 h-5" />
                        {t.downloadToView[language]}
                      </motion.button>
                    </div>
                  )}
                </>
              )}
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}

export default FilePreviewModal;
