'use client';

import { useState, useCallback } from 'react';
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
  FolderOpen
} from 'lucide-react';
import { useStore } from '@/store/useStore';
import { uploadDocument, getDocuments, deleteDocument } from '@/lib/api';
import { cn, formatFileSize, formatDate } from '@/lib/utils';
import { useEffect } from 'react';

interface DocumentResponse {
  id: string;
  name: string;
  size: number;
  type: string;
  uploaded_at: string;
  chunks?: number;
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

  // Load documents on mount
  useEffect(() => {
    const loadDocuments = async () => {
      const response = await getDocuments();
      if (response.success && response.data) {
        setDocuments(response.data.documents.map((d: DocumentResponse) => ({
          id: d.id,
          name: d.name,
          size: d.size,
          type: d.type,
          uploadedAt: new Date(d.uploaded_at),
          chunks: d.chunks,
        })));
      }
    };
    loadDocuments();
  }, [setDocuments]);

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

        if (response.success && response.data) {
          addDocument({
            id: response.data.id,
            name: response.data.name,
            size: response.data.size,
            type: response.data.type,
            uploadedAt: new Date(response.data.uploaded_at),
            chunks: response.data.chunks,
          });
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
  }, [addDocument]);

  const handleDelete = async (docId: string) => {
    const response = await deleteDocument(docId);
    if (response.success) {
      removeDocument(docId);
    }
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
                      <button className="p-2 rounded-lg hover:bg-accent transition-colors" title="Görüntüle">
                        <Eye className="w-4 h-4" />
                      </button>
                      <button className="p-2 rounded-lg hover:bg-accent transition-colors" title="İndir">
                        <Download className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(doc.id)}
                        className="p-2 rounded-lg hover:bg-red-500/10 text-red-500 transition-colors"
                        title="Sil"
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
    </div>
  );
}
