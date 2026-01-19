'use client';

import { useState, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FileText,
  Upload,
  Trash2,
  Search,
  File,
  FileImage,
  FileCode,
  Download,
  Eye,
  Loader2,
  CheckCircle2,
  XCircle,
  FolderOpen,
  HardDrive,
  Layers,
  BarChart3,
  AlertTriangle,
  RefreshCw
} from 'lucide-react';
import { useStore } from '@/store/useStore';
import { uploadDocument, getDocuments, deleteDocument, downloadDocument, previewDocument, DocumentPreview, apiCall } from '@/lib/api';
import { cn, formatFileSize, formatDate } from '@/lib/utils';
import { useEffect } from 'react';

interface SyncStatus {
  synced: boolean;
  total_files: number;
  indexed_files: number;
  unindexed_files: number;
  total_chunks: number;
  unindexed_list?: string[];
}

interface DocumentResponse {
  // Backend returns both formats - handle both
  document_id?: string;
  id?: string;
  filename?: string;
  name?: string;
  size: number;
  type?: string;
  uploaded_at?: string;
  uploadedAt?: string;
  chunks?: number;
  chunks_created?: number;
}

const fileIcons: Record<string, React.ElementType> = {
  pdf: FileText,
  doc: FileText,
  docx: FileText,
  txt: FileText,
  md: FileCode,
  json: FileCode,
  csv: File,
  xls: File,
  xlsx: File,
  png: FileImage,
  jpg: FileImage,
  jpeg: FileImage,
  default: File,
};

export function DocumentsPage() {
  const { documents, setDocuments, addDocument, removeDocument, language } = useStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({});
  const [dragOver, setDragOver] = useState(false);
  const [previewDoc, setPreviewDoc] = useState<{ id: string; preview: DocumentPreview } | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null);
  const [isSyncing, setIsSyncing] = useState(false);

  // Check sync status
  const checkSyncStatus = useCallback(async () => {
    try {
      const response = await apiCall<{ sync_status: SyncStatus }>('/api/rag/sync-status');
      if (response.sync_status) {
        setSyncStatus(response.sync_status);
      }
    } catch (error) {
      console.error('Failed to check sync status:', error);
    }
  }, []);

  // Auto sync unindexed documents
  const handleAutoSync = useCallback(async () => {
    setIsSyncing(true);
    try {
      await apiCall<{ reindexed: number; message: string }>('/api/rag/auto-sync', {
        method: 'POST'
      });
      // Reload documents after sync
      const docsResponse = await getDocuments();
      if (docsResponse.success && docsResponse.data) {
        setDocuments(docsResponse.data.documents.map((d: DocumentResponse) => ({
          id: d.document_id || d.id || '',
          name: d.filename || d.name || 'Unknown',
          size: d.size || 0,
          type: d.type || (d.filename || d.name || '').split('.').pop() || 'file',
          uploadedAt: new Date(d.uploaded_at || d.uploadedAt || new Date()),
          chunks: d.chunks || d.chunks_created || 0,
        })));
      }
      // Recheck sync status
      await checkSyncStatus();
    } catch (error) {
      console.error('Auto sync failed:', error);
    } finally {
      setIsSyncing(false);
    }
  }, [checkSyncStatus, setDocuments]);

  // Load documents on mount
  useEffect(() => {
    const loadDocuments = async () => {
      try {
        const response = await getDocuments();
        console.log('Documents API response:', response);
        if (response.success && response.data) {
          setDocuments(response.data.documents.map((d: DocumentResponse) => ({
            id: d.document_id || d.id || '',
            name: d.filename || d.name || 'Unknown',
            size: d.size || 0,
            type: d.type || (d.filename || d.name || '').split('.').pop() || 'file',
            uploadedAt: new Date(d.uploaded_at || d.uploadedAt || new Date()),
            chunks: d.chunks || d.chunks_created || 0,
          })));
        }
        // Also check sync status
        await checkSyncStatus();
      } catch (error) {
        console.error('Failed to load documents:', error);
      }
    };
    loadDocuments();
  }, [setDocuments, checkSyncStatus]);

  const handleUpload = useCallback(async (files: FileList | null) => {
    if (!files || files.length === 0) return;

    for (const file of Array.from(files)) {
      const tempId = `temp-${Date.now()}-${file.name}`;
      setUploadProgress((prev) => ({ ...prev, [tempId]: 0 }));

      try {
        // Simulate progress
        const progressInterval = setInterval(() => {
          setUploadProgress((prev) => ({
            ...prev,
            [tempId]: Math.min((prev[tempId] || 0) + 10, 90),
          }));
        }, 200);

        const response = await uploadDocument(file);

        clearInterval(progressInterval);
        setUploadProgress((prev) => ({ ...prev, [tempId]: 100 }));

        console.log('Upload response:', response);
        if (response.success && response.data) {
          const data = response.data as DocumentResponse;
          addDocument({
            id: data.document_id || data.id || tempId,
            name: data.filename || data.name || file.name,
            size: data.size || file.size,
            type: data.type || file.name.split('.').pop() || 'file',
            uploadedAt: new Date(data.uploaded_at || data.uploadedAt || new Date()),
            chunks: data.chunks || data.chunks_created || 0,
          });
          
          // Reload documents list to get accurate data
          setTimeout(async () => {
            const docsResponse = await getDocuments();
            if (docsResponse.success && docsResponse.data) {
              setDocuments(docsResponse.data.documents.map((d: DocumentResponse) => ({
                id: d.document_id || d.id || '',
                name: d.filename || d.name || 'Unknown',
                size: d.size || 0,
                type: d.type || (d.filename || d.name || '').split('.').pop() || 'file',
                uploadedAt: new Date(d.uploaded_at || d.uploadedAt || new Date()),
                chunks: d.chunks || d.chunks_created || 0,
              })));
            }
          }, 500);
        }

        // Clean up progress after delay
        setTimeout(() => {
          setUploadProgress((prev) => {
            const newProgress = { ...prev };
            delete newProgress[tempId];
            return newProgress;
          });
        }, 1000);
      } catch (error) {
        console.error('Upload error:', error);
        setUploadProgress((prev) => ({ ...prev, [tempId]: -1 })); // -1 indicates error
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [addDocument]);

  const handleDelete = async (docId: string) => {
    const response = await deleteDocument(docId);
    if (response.success) {
      removeDocument(docId);
    }
  };

  const handleDownload = (docId: string) => {
    downloadDocument(docId);
  };

  const handlePreview = async (docId: string) => {
    setPreviewLoading(true);
    try {
      const response = await previewDocument(docId);
      if (response.success && response.data) {
        setPreviewDoc({ id: docId, preview: response.data });
      }
    } catch (error) {
      console.error('Preview error:', error);
    }
    setPreviewLoading(false);
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    handleUpload(e.dataTransfer.files);
  }, [handleUpload]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  }, []);

  const getFileIcon = (fileName: string) => {
    const ext = fileName.split('.').pop()?.toLowerCase() || '';
    return fileIcons[ext] || fileIcons.default;
  };

  const filteredDocuments = documents.filter((doc) =>
    doc.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Calculate statistics
  const stats = useMemo(() => {
    const totalSize = documents.reduce((acc, doc) => acc + doc.size, 0);
    const totalChunks = documents.reduce((acc, doc) => acc + (doc.chunks || 0), 0);
    const fileTypes = documents.reduce((acc, doc) => {
      const ext = doc.name.split('.').pop()?.toLowerCase() || 'other';
      acc[ext] = (acc[ext] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    return { totalSize, totalChunks, fileTypes, totalDocs: documents.length };
  }, [documents]);

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-border bg-card/50 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 text-white">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-semibold">
              {language === 'tr' ? 'Dökümanlar' : 'Documents'}
            </h1>
            <p className="text-xs text-muted-foreground">
              {language === 'tr'
                ? `${documents.length} döküman yüklendi`
                : `${documents.length} documents uploaded`
              }
            </p>
          </div>
        </div>

        {/* Search */}
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={language === 'tr' ? 'Döküman ara...' : 'Search documents...'}
              className="pl-10 pr-4 py-2 w-64 bg-background border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
            />
          </div>
        </div>
      </header>

      {/* Statistics Cards */}
      {stats.totalDocs > 0 && (
        <div className="px-6 py-4 bg-gradient-to-r from-emerald-50 to-teal-50 dark:from-emerald-950/20 dark:to-teal-950/20 border-b border-border">
          <div className="max-w-5xl mx-auto grid grid-cols-4 gap-4">
            <div className="flex items-center gap-3 p-3 bg-white/50 dark:bg-black/20 rounded-xl">
              <div className="w-10 h-10 rounded-lg bg-emerald-100 dark:bg-emerald-900/50 flex items-center justify-center">
                <FileText className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-emerald-700 dark:text-emerald-300">{stats.totalDocs}</p>
                <p className="text-xs text-muted-foreground">{language === 'tr' ? 'Toplam Döküman' : 'Total Documents'}</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 bg-white/50 dark:bg-black/20 rounded-xl">
              <div className="w-10 h-10 rounded-lg bg-blue-100 dark:bg-blue-900/50 flex items-center justify-center">
                <Layers className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-blue-700 dark:text-blue-300">{stats.totalChunks}</p>
                <p className="text-xs text-muted-foreground">{language === 'tr' ? 'Toplam Chunk' : 'Total Chunks'}</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 bg-white/50 dark:bg-black/20 rounded-xl">
              <div className="w-10 h-10 rounded-lg bg-purple-100 dark:bg-purple-900/50 flex items-center justify-center">
                <HardDrive className="w-5 h-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-purple-700 dark:text-purple-300">{formatFileSize(stats.totalSize)}</p>
                <p className="text-xs text-muted-foreground">{language === 'tr' ? 'Toplam Boyut' : 'Total Size'}</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 bg-white/50 dark:bg-black/20 rounded-xl">
              <div className="w-10 h-10 rounded-lg bg-amber-100 dark:bg-amber-900/50 flex items-center justify-center">
                <BarChart3 className="w-5 h-5 text-amber-600 dark:text-amber-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-amber-700 dark:text-amber-300">{Object.keys(stats.fileTypes).length}</p>
                <p className="text-xs text-muted-foreground">{language === 'tr' ? 'Dosya Türü' : 'File Types'}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Sync Warning */}
      {syncStatus && !syncStatus.synced && syncStatus.unindexed_files > 0 && (
        <div className="px-6 py-3 bg-amber-50 dark:bg-amber-950/30 border-b border-amber-200 dark:border-amber-800">
          <div className="max-w-5xl mx-auto flex items-center justify-between">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400" />
              <div>
                <p className="font-medium text-amber-800 dark:text-amber-200">
                  {language === 'tr' 
                    ? `${syncStatus.unindexed_files} döküman indekslenmemiş` 
                    : `${syncStatus.unindexed_files} documents not indexed`}
                </p>
                <p className="text-sm text-amber-600 dark:text-amber-400">
                  {language === 'tr'
                    ? 'Bu belgeler arama sonuçlarında görünmeyecek. Senkronize edin.'
                    : 'These documents won\'t appear in search results. Sync to fix.'}
                </p>
              </div>
            </div>
            <button
              onClick={handleAutoSync}
              disabled={isSyncing}
              className={cn(
                "flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all",
                isSyncing
                  ? "bg-amber-200 dark:bg-amber-800 text-amber-600 dark:text-amber-300 cursor-not-allowed"
                  : "bg-amber-500 hover:bg-amber-600 text-white"
              )}
            >
              <RefreshCw className={cn("w-4 h-4", isSyncing && "animate-spin")} />
              {isSyncing 
                ? (language === 'tr' ? 'Senkronize ediliyor...' : 'Syncing...') 
                : (language === 'tr' ? 'Şimdi Senkronize Et' : 'Sync Now')}
            </button>
          </div>
        </div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-5xl mx-auto space-y-6">
          {/* Upload Area */}
          <motion.div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            className={cn(
              "relative border-2 border-dashed rounded-2xl p-8 text-center transition-all",
              dragOver
                ? "border-primary-500 bg-primary-500/5"
                : "border-border hover:border-primary-500/50"
            )}
          >
            <input
              type="file"
              multiple
              onChange={(e) => handleUpload(e.target.files)}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              accept=".pdf,.doc,.docx,.txt,.md,.json,.csv,.xls,.xlsx"
            />

            <div className="flex flex-col items-center gap-4">
              <div className={cn(
                "w-16 h-16 rounded-2xl flex items-center justify-center transition-colors",
                dragOver ? "bg-primary-500/10" : "bg-muted"
              )}>
                <Upload className={cn(
                  "w-8 h-8 transition-colors",
                  dragOver ? "text-primary-500" : "text-muted-foreground"
                )} />
              </div>
              <div>
                <p className="text-lg font-medium">
                  {language === 'tr'
                    ? 'Dosyaları sürükleyip bırakın'
                    : 'Drag and drop files here'
                  }
                </p>
                <p className="text-sm text-muted-foreground mt-1">
                  {language === 'tr'
                    ? 'veya dosya seçmek için tıklayın'
                    : 'or click to select files'
                  }
                </p>
              </div>
              <p className="text-xs text-muted-foreground">
                PDF, DOC, DOCX, TXT, MD, JSON, CSV, XLS, XLSX
              </p>
            </div>
          </motion.div>

          {/* Upload Progress */}
          <AnimatePresence>
            {Object.entries(uploadProgress).map(([id, progress]) => (
              <motion.div
                key={id}
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="bg-card border border-border rounded-xl p-4"
              >
                <div className="flex items-center gap-3">
                  {progress === 100 ? (
                    <CheckCircle2 className="w-5 h-5 text-green-500" />
                  ) : progress === -1 ? (
                    <XCircle className="w-5 h-5 text-red-500" />
                  ) : (
                    <Loader2 className="w-5 h-5 animate-spin text-primary-500" />
                  )}
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium">{id.replace('temp-', '').split('-').pop()}</span>
                      <span className="text-xs text-muted-foreground">{Math.max(0, progress)}%</span>
                    </div>
                    <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${Math.max(0, progress)}%` }}
                        className={cn(
                          "h-full rounded-full",
                          progress === -1 ? "bg-red-500" : "bg-primary-500"
                        )}
                      />
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Documents List */}
          {filteredDocuments.length === 0 ? (
            <div className="text-center py-12">
              <FolderOpen className="w-16 h-16 mx-auto text-muted-foreground/50 mb-4" />
              <p className="text-lg font-medium text-muted-foreground">
                {language === 'tr' ? 'Henüz döküman yok' : 'No documents yet'}
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                {language === 'tr'
                  ? 'Dosya yükleyerek başlayın'
                  : 'Start by uploading files'
                }
              </p>
            </div>
          ) : (
            <div className="grid gap-3">
              {filteredDocuments.map((doc, index) => {
                const FileIcon = getFileIcon(doc.name);

                return (
                  <motion.div
                    key={doc.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="group flex items-center gap-4 p-4 bg-card border border-border rounded-xl hover:border-primary-500/30 hover:shadow-lg transition-all"
                  >
                    {/* Icon */}
                    <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-muted">
                      <FileIcon className="w-6 h-6 text-muted-foreground" />
                    </div>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <p className="font-medium truncate">{doc.name}</p>
                      <div className="flex items-center gap-3 text-xs text-muted-foreground mt-1">
                        <span>{formatFileSize(doc.size)}</span>
                        <span>•</span>
                        <span>{formatDate(doc.uploadedAt)}</span>
                        {doc.chunks && (
                          <>
                            <span>•</span>
                            <span>{doc.chunks} chunks</span>
                          </>
                        )}
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button 
                        onClick={() => handlePreview(doc.id)}
                        className="p-2 rounded-lg hover:bg-accent transition-colors" 
                        title={language === 'tr' ? 'Görüntüle' : 'Preview'}
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      <button 
                        onClick={() => handleDownload(doc.id)}
                        className="p-2 rounded-lg hover:bg-accent transition-colors" 
                        title={language === 'tr' ? 'İndir' : 'Download'}
                      >
                        <Download className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(doc.id)}
                        className="p-2 rounded-lg hover:bg-red-500/10 text-red-500 transition-colors"
                        title={language === 'tr' ? 'Sil' : 'Delete'}
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Preview Modal */}
      <AnimatePresence>
        {(previewDoc || previewLoading) && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4"
            onClick={() => setPreviewDoc(null)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-card border border-border rounded-2xl shadow-2xl w-full max-w-4xl max-h-[80vh] flex flex-col overflow-hidden"
            >
              {/* Modal Header */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-border">
                <div className="flex items-center gap-3">
                  <Eye className="w-5 h-5 text-primary-500" />
                  <h2 className="text-lg font-semibold">
                    {language === 'tr' ? 'Döküman Önizleme' : 'Document Preview'}
                  </h2>
                  {previewDoc?.preview.filename && (
                    <span className="text-sm text-muted-foreground">- {previewDoc.preview.filename}</span>
                  )}
                </div>
                <button
                  onClick={() => setPreviewDoc(null)}
                  className="p-2 rounded-lg hover:bg-accent transition-colors"
                >
                  <XCircle className="w-5 h-5" />
                </button>
              </div>

              {/* Modal Content */}
              <div className="flex-1 overflow-auto p-6">
                {previewLoading ? (
                  <div className="flex items-center justify-center h-full">
                    <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
                  </div>
                ) : previewDoc?.preview.success ? (
                  <div className="space-y-4">
                    {previewDoc.preview.type === 'pdf' && previewDoc.preview.page_count && (
                      <div className="text-sm text-muted-foreground">
                        {language === 'tr' ? 'Sayfa sayısı:' : 'Page count:'} {previewDoc.preview.page_count}
                        {previewDoc.preview.truncated && (
                          <span className="ml-2 text-amber-500">
                            ({language === 'tr' ? 'İlk 10 sayfa gösteriliyor' : 'Showing first 10 pages'})
                          </span>
                        )}
                      </div>
                    )}
                    <pre className="whitespace-pre-wrap text-sm font-mono bg-muted/50 p-4 rounded-xl overflow-x-auto">
                      {previewDoc.preview.content}
                    </pre>
                    {previewDoc.preview.truncated && (
                      <p className="text-sm text-amber-500 text-center">
                        {language === 'tr' ? 'İçerik kısaltılmıştır. Tam içerik için indirin.' : 'Content truncated. Download for full content.'}
                      </p>
                    )}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center h-full gap-4">
                    <XCircle className="w-12 h-12 text-red-500" />
                    <p className="text-lg font-medium text-red-500">
                      {previewDoc?.preview.error || (language === 'tr' ? 'Önizleme yüklenemedi' : 'Preview failed to load')}
                    </p>
                    {previewDoc && (
                      <button
                        onClick={() => {
                          handleDownload(previewDoc.id);
                          setPreviewDoc(null);
                        }}
                        className="flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
                      >
                        <Download className="w-4 h-4" />
                        {language === 'tr' ? 'Bunun yerine indir' : 'Download instead'}
                      </button>
                    )}
                  </div>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
