'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Shield,
  Save,
  Download,
  RefreshCw,
  Wifi,
  WifiOff,
  Loader2,
  HardDrive,
  Cloud,
  CloudOff,
  ListOrdered,
  Play,
  X,
  ChevronDown,
  ChevronUp,
  Info,
} from 'lucide-react';

// Types
interface ResilienceStatus {
  active_checkpoints: number;
  pending_offline_sync: number;
  queue_length: number;
  active_generations: number;
  features: {
    auto_save: boolean;
    checkpoint: boolean;
    error_recovery: boolean;
    queue: boolean;
    offline_mode: boolean;
    partial_export: boolean;
    connection_resilience: boolean;
  };
}

interface CheckpointInfo {
  document_id: string;
  workspace_id: string;
  state: string;
  progress: number;
  current_phase: string;
  completed_sections_count: number;
  total_words: number;
  updated_at: string;
  can_resume: boolean;
}

interface QueueItem {
  id: string;
  title: string;
  priority: number;
  position: number;
  created_at: string;
}

interface AutoSaveInfo {
  document_id: string;
  saved_sections: number;
  total_words: number;
  last_save: string | null;
}

// Props
interface DeepScholarResiliencePanelProps {
  documentId: string | null;
  workspaceId: string;
  isGenerating: boolean;
  apiUrl?: string;
  onResumeFromCheckpoint?: (checkpointInfo: CheckpointInfo) => void;
  onPartialExport?: (filepath: string) => void;
}

// Browser Tab Protection Hook
export function useTabProtection(isActive: boolean, message?: string) {
  useEffect(() => {
    if (!isActive) return;

    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      const warningMessage = message || 
        '⚠️ Döküman üretimi devam ediyor! Sayfayı kapatırsanız ilerleme kaybedilir. Devam etmek istediğinizden emin misiniz?';
      e.preventDefault();
      e.returnValue = warningMessage;
      return warningMessage;
    };

    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [isActive, message]);
}

// Connection Monitor Hook
export function useConnectionMonitor(documentId: string | null, apiUrl: string) {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [connectionState, setConnectionState] = useState<'connected' | 'disconnected' | 'reconnecting'>('connected');
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      setConnectionState('connected');
      setReconnectAttempts(0);
      
      // Reconnect bildirimi
      if (documentId) {
        fetch(`${apiUrl}/api/deep-scholar/resilience/connection/${documentId}/reset`, {
          method: 'POST'
        }).catch(() => {});
      }
    };

    const handleOffline = () => {
      setIsOnline(false);
      setConnectionState('disconnected');
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [documentId, apiUrl]);

  const attemptReconnect = useCallback(async () => {
    if (!documentId) return false;

    setConnectionState('reconnecting');
    setReconnectAttempts(prev => prev + 1);

    try {
      const response = await fetch(`${apiUrl}/api/deep-scholar/status/${documentId}`);
      if (response.ok) {
        setConnectionState('connected');
        setReconnectAttempts(0);
        return true;
      }
    } catch {
      // Retry with exponential backoff
      const delays = [1000, 2000, 5000, 10000, 30000];
      const delay = delays[Math.min(reconnectAttempts, delays.length - 1)];
      
      reconnectTimeoutRef.current = setTimeout(() => {
        if (reconnectAttempts < 5) {
          attemptReconnect();
        } else {
          setConnectionState('disconnected');
        }
      }, delay);
    }

    return false;
  }, [documentId, apiUrl, reconnectAttempts]);

  return {
    isOnline,
    connectionState,
    reconnectAttempts,
    attemptReconnect,
  };
}

// Auto-Save Indicator Component
function AutoSaveIndicator({ 
  lastSave, 
  totalWords, 
  savedSections 
}: { 
  lastSave: string | null;
  totalWords: number;
  savedSections: number;
}) {
  const [showDetails, setShowDetails] = useState(false);

  if (!lastSave) return null;

  const timeSince = () => {
    const diff = Date.now() - new Date(lastSave).getTime();
    const seconds = Math.floor(diff / 1000);
    if (seconds < 60) return `${seconds}s önce`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}dk önce`;
    return `${Math.floor(minutes / 60)}sa önce`;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex items-center gap-2 px-3 py-1.5 bg-green-500/10 border border-green-500/20 rounded-lg cursor-pointer"
      onClick={() => setShowDetails(!showDetails)}
    >
      <Save className="w-4 h-4 text-green-500" />
      <span className="text-xs text-green-600">
        Otomatik kaydedildi • {timeSince()}
      </span>
      
      {showDetails && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="absolute top-full left-0 mt-2 p-3 bg-card border border-border rounded-xl shadow-lg z-50 min-w-[200px]"
        >
          <div className="space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Kaydedilen bölümler:</span>
              <span className="font-medium">{savedSections}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Toplam kelime:</span>
              <span className="font-medium">{totalWords.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Son kayıt:</span>
              <span className="font-medium">{new Date(lastSave).toLocaleTimeString()}</span>
            </div>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}

// Connection Status Badge
function ConnectionStatusBadge({ 
  state, 
  attempts,
  onReconnect 
}: { 
  state: 'connected' | 'disconnected' | 'reconnecting';
  attempts: number;
  onReconnect: () => void;
}) {
  if (state === 'connected') {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 bg-green-500/10 border border-green-500/20 rounded-lg">
        <Wifi className="w-4 h-4 text-green-500" />
        <span className="text-xs text-green-600">Bağlı</span>
      </div>
    );
  }

  if (state === 'reconnecting') {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 bg-amber-500/10 border border-amber-500/20 rounded-lg">
        <Loader2 className="w-4 h-4 text-amber-500 animate-spin" />
        <span className="text-xs text-amber-600">Yeniden bağlanıyor... ({attempts})</span>
      </div>
    );
  }

  return (
    <button
      onClick={onReconnect}
      className="flex items-center gap-2 px-3 py-1.5 bg-red-500/10 border border-red-500/20 rounded-lg hover:bg-red-500/20 transition-colors"
    >
      <WifiOff className="w-4 h-4 text-red-500" />
      <span className="text-xs text-red-600">Bağlantı kesildi - Tıkla</span>
    </button>
  );
}

// Queue Item Component
function QueueItemCard({ 
  item, 
  onRemove, 
  onPriorityChange 
}: { 
  item: QueueItem;
  onRemove: (id: string) => void;
  onPriorityChange: (id: string, priority: number) => void;
}) {
  const priorityColors = {
    1: 'bg-gray-500/10 text-gray-600',
    2: 'bg-amber-500/10 text-amber-600',
    3: 'bg-red-500/10 text-red-600',
  };

  const priorityLabels = {
    1: 'Normal',
    2: 'Yüksek',
    3: 'Acil',
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      className="flex items-center gap-3 p-3 bg-accent/30 rounded-xl"
    >
      <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary-500/10 text-primary-500 font-bold">
        {item.position}
      </div>
      
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">{item.title}</p>
        <div className="flex items-center gap-2 mt-1">
          <span className={`text-[10px] px-2 py-0.5 rounded-full ${priorityColors[item.priority as keyof typeof priorityColors]}`}>
            {priorityLabels[item.priority as keyof typeof priorityLabels]}
          </span>
          <span className="text-[10px] text-muted-foreground">
            {new Date(item.created_at).toLocaleTimeString()}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-1">
        <button
          onClick={() => onPriorityChange(item.id, Math.min(3, item.priority + 1))}
          className="p-1.5 hover:bg-accent rounded-lg transition-colors"
          title="Önceliği artır"
        >
          <ChevronUp className="w-4 h-4" />
        </button>
        <button
          onClick={() => onRemove(item.id)}
          className="p-1.5 hover:bg-red-500/10 text-red-500 rounded-lg transition-colors"
          title="Kaldır"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </motion.div>
  );
}

// Main Resilience Panel Component
export function DeepScholarResiliencePanel({
  documentId,
  workspaceId: _workspaceId,
  isGenerating,
  apiUrl = 'http://localhost:8001',
  onResumeFromCheckpoint,
  onPartialExport,
}: DeepScholarResiliencePanelProps) {
  // State
  const [isExpanded, setIsExpanded] = useState(false);
  const [status, setStatus] = useState<ResilienceStatus | null>(null);
  const [autoSaveInfo, setAutoSaveInfo] = useState<AutoSaveInfo | null>(null);
  const [checkpoint, setCheckpoint] = useState<CheckpointInfo | null>(null);
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [_isLoading, setIsLoading] = useState(false);
  const [exportLoading, setExportLoading] = useState(false);

  // Hooks
  useTabProtection(isGenerating, 
    '⚠️ DeepScholar döküman üretimi devam ediyor! Kapatırsanız ilerleme kaybedilir.');
  
  const { isOnline: _isOnline, connectionState, reconnectAttempts, attemptReconnect } = 
    useConnectionMonitor(documentId, apiUrl);

  // Fetch status
  const fetchStatus = useCallback(async () => {
    try {
      const response = await fetch(`${apiUrl}/api/deep-scholar/resilience/status`);
      if (response.ok) {
        const data = await response.json();
        setStatus(data);
      }
    } catch (error) {
      console.error('Failed to fetch resilience status:', error);
    }
  }, [apiUrl]);

  // Fetch auto-save info
  const fetchAutoSaveInfo = useCallback(async () => {
    if (!documentId) return;
    
    try {
      const response = await fetch(`${apiUrl}/api/deep-scholar/resilience/autosave/${documentId}`);
      if (response.ok) {
        const data = await response.json();
        setAutoSaveInfo(data);
      }
    } catch (error) {
      console.error('Failed to fetch auto-save info:', error);
    }
  }, [apiUrl, documentId]);

  // Fetch checkpoint
  const fetchCheckpoint = useCallback(async () => {
    if (!documentId) return;
    
    try {
      const response = await fetch(`${apiUrl}/api/deep-scholar/resilience/checkpoint/${documentId}`);
      if (response.ok) {
        const data = await response.json();
        setCheckpoint(data);
      }
    } catch (_error) {
      // Checkpoint yok, sorun değil
    }
  }, [apiUrl, documentId]);

  // Fetch queue
  const fetchQueue = useCallback(async () => {
    try {
      const response = await fetch(`${apiUrl}/api/deep-scholar/resilience/queue`);
      if (response.ok) {
        const data = await response.json();
        setQueue(data.queue || []);
      }
    } catch (error) {
      console.error('Failed to fetch queue:', error);
    }
  }, [apiUrl]);

  // Initial fetch
  useEffect(() => {
    fetchStatus();
    if (documentId) {
      fetchAutoSaveInfo();
      fetchCheckpoint();
    }
    fetchQueue();

    // Polling
    const interval = setInterval(() => {
      if (isGenerating && documentId) {
        fetchAutoSaveInfo();
      }
    }, 10000);

    return () => clearInterval(interval);
  }, [fetchStatus, fetchAutoSaveInfo, fetchCheckpoint, fetchQueue, documentId, isGenerating]);

  // Handle partial export
  const handlePartialExport = async (format: 'markdown' | 'html') => {
    if (!documentId) return;
    
    setExportLoading(true);
    try {
      const response = await fetch(
        `${apiUrl}/api/deep-scholar/resilience/export/partial/${documentId}?format=${format}`,
        { method: 'POST' }
      );
      
      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = format === 'html' ? 'partial_export.html' : 'partial_export.md';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        onPartialExport?.(format);
      }
    } catch (error) {
      console.error('Partial export failed:', error);
    } finally {
      setExportLoading(false);
    }
  };

  // Handle queue operations
  const handleRemoveFromQueue = async (id: string) => {
    try {
      await fetch(`${apiUrl}/api/deep-scholar/resilience/queue/${id}`, {
        method: 'DELETE'
      });
      fetchQueue();
    } catch (error) {
      console.error('Failed to remove from queue:', error);
    }
  };

  const handlePriorityChange = async (id: string, priority: number) => {
    try {
      await fetch(`${apiUrl}/api/deep-scholar/resilience/queue/${id}/priority`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ priority })
      });
      fetchQueue();
    } catch (error) {
      console.error('Failed to update priority:', error);
    }
  };

  // Handle resume from checkpoint
  const handleResume = async () => {
    if (!checkpoint || !onResumeFromCheckpoint) return;
    
    try {
      await fetch(`${apiUrl}/api/deep-scholar/resilience/checkpoint/${documentId}/resume`, {
        method: 'POST'
      });
      onResumeFromCheckpoint(checkpoint);
    } catch (error) {
      console.error('Failed to resume:', error);
    }
  };

  if (!status) return null;

  return (
    <div className="relative">
      {/* Mini Status Bar (Always Visible) */}
      <div className="flex items-center gap-3">
        {/* Auto-save indicator */}
        {autoSaveInfo && autoSaveInfo.last_save && (
          <AutoSaveIndicator
            lastSave={autoSaveInfo.last_save}
            totalWords={autoSaveInfo.total_words}
            savedSections={autoSaveInfo.saved_sections}
          />
        )}

        {/* Connection status */}
        <ConnectionStatusBadge
          state={connectionState}
          attempts={reconnectAttempts}
          onReconnect={attemptReconnect}
        />

        {/* Resilience panel toggle */}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border transition-all ${
            isExpanded 
              ? 'bg-primary-500 text-white border-primary-500' 
              : 'bg-accent/50 border-border hover:bg-accent'
          }`}
        >
          <Shield className="w-4 h-4" />
          <span className="text-xs font-medium">Resilience</span>
          {isExpanded ? (
            <ChevronUp className="w-3 h-3" />
          ) : (
            <ChevronDown className="w-3 h-3" />
          )}
        </button>
      </div>

      {/* Expanded Panel */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ opacity: 0, y: -10, height: 0 }}
            animate={{ opacity: 1, y: 0, height: 'auto' }}
            exit={{ opacity: 0, y: -10, height: 0 }}
            className="absolute right-0 top-full mt-2 w-[400px] bg-card border border-border rounded-2xl shadow-xl overflow-hidden z-50"
          >
            {/* Header */}
            <div className="px-4 py-3 bg-gradient-to-r from-purple-500/10 to-pink-500/10 border-b border-border flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Shield className="w-5 h-5 text-purple-500" />
                <span className="font-medium">DeepScholar Resilience</span>
                <span className="px-2 py-0.5 text-[10px] bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-full">
                  Premium
                </span>
              </div>
              <button
                onClick={() => setIsExpanded(false)}
                className="p-1 hover:bg-accent rounded-lg transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Content */}
            <div className="p-4 max-h-[500px] overflow-y-auto space-y-4">
              {/* Features Grid */}
              <div className="grid grid-cols-4 gap-2">
                {[
                  { key: 'auto_save', icon: Save, label: 'Auto-Save', color: 'text-green-500' },
                  { key: 'checkpoint', icon: HardDrive, label: 'Checkpoint', color: 'text-blue-500' },
                  { key: 'error_recovery', icon: RefreshCw, label: 'Recovery', color: 'text-amber-500' },
                  { key: 'offline_mode', icon: CloudOff, label: 'Offline', color: 'text-purple-500' },
                ].map((feature) => (
                  <div
                    key={feature.key}
                    className={`flex flex-col items-center gap-1 p-2 rounded-lg ${
                      status.features[feature.key as keyof typeof status.features]
                        ? 'bg-accent/50'
                        : 'bg-muted/30 opacity-50'
                    }`}
                  >
                    <feature.icon className={`w-4 h-4 ${feature.color}`} />
                    <span className="text-[10px] font-medium">{feature.label}</span>
                  </div>
                ))}
              </div>

              {/* Checkpoint Section */}
              {checkpoint && checkpoint.can_resume && (
                <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-xl">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <HardDrive className="w-4 h-4 text-blue-500" />
                      <span className="text-sm font-medium">Checkpoint Mevcut</span>
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {checkpoint.progress}% tamamlandı
                    </span>
                  </div>
                  
                  <div className="h-2 bg-muted rounded-full overflow-hidden mb-3">
                    <motion.div
                      className="h-full bg-blue-500"
                      initial={{ width: 0 }}
                      animate={{ width: `${checkpoint.progress}%` }}
                    />
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleResume}
                      className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-blue-500 text-white rounded-lg text-sm font-medium hover:bg-blue-600 transition-colors"
                    >
                      <Play className="w-4 h-4" />
                      Devam Et
                    </button>
                    <button
                      onClick={() => handlePartialExport('markdown')}
                      disabled={exportLoading}
                      className="flex items-center justify-center gap-2 px-3 py-2 bg-accent rounded-lg text-sm font-medium hover:bg-accent/80 transition-colors"
                    >
                      {exportLoading ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Download className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                </div>
              )}

              {/* Queue Section */}
              {queue.length > 0 && (
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <ListOrdered className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm font-medium">Üretim Kuyruğu ({queue.length})</span>
                  </div>
                  
                  <div className="space-y-2">
                    <AnimatePresence>
                      {queue.slice(0, 3).map((item) => (
                        <QueueItemCard
                          key={item.id}
                          item={item}
                          onRemove={handleRemoveFromQueue}
                          onPriorityChange={handlePriorityChange}
                        />
                      ))}
                    </AnimatePresence>
                  </div>

                  {queue.length > 3 && (
                    <p className="text-xs text-muted-foreground text-center">
                      +{queue.length - 3} daha
                    </p>
                  )}
                </div>
              )}

              {/* Stats */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-accent/30 rounded-xl">
                  <div className="flex items-center gap-2 mb-1">
                    <HardDrive className="w-4 h-4 text-blue-500" />
                    <span className="text-xs text-muted-foreground">Aktif Checkpoint</span>
                  </div>
                  <p className="text-xl font-bold">{status.active_checkpoints}</p>
                </div>
                
                <div className="p-3 bg-accent/30 rounded-xl">
                  <div className="flex items-center gap-2 mb-1">
                    <Cloud className="w-4 h-4 text-purple-500" />
                    <span className="text-xs text-muted-foreground">Sync Bekleyen</span>
                  </div>
                  <p className="text-xl font-bold">{status.pending_offline_sync}</p>
                </div>
              </div>

              {/* Info */}
              <div className="flex items-start gap-2 p-3 bg-accent/30 rounded-xl">
                <Info className="w-4 h-4 text-muted-foreground mt-0.5" />
                <p className="text-xs text-muted-foreground">
                  DeepScholar Resilience, döküman üretimi sırasında otomatik kayıt yapar, 
                  bağlantı kesintilerinde veri korur ve hatalarda otomatik kurtarma sağlar.
                </p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// Export hooks and components
export default DeepScholarResiliencePanel;
