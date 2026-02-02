'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search, Command, FileText, Folder, Plus, Trash2,
  Archive, Star, Lock, Unlock, Copy, Download,
  Upload, Tag, Settings, Moon, Sun, Zap,
  BookOpen, Clock, TrendingUp, Grid, List
} from 'lucide-react';

interface QuickAction {
  id: string;
  label: string;
  description?: string;
  icon: React.ReactNode;
  shortcut?: string;
  category: 'note' | 'folder' | 'view' | 'tools' | 'settings';
  action: () => void;
}

interface QuickActionsPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onAction: (actionId: string) => void;
  currentNote?: { id: string; title: string } | null;
}

const QuickActionsPanel: React.FC<QuickActionsPanelProps> = ({
  isOpen,
  onClose,
  onAction,
  currentNote
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  // Define all available actions
  const actions: QuickAction[] = [
    // Note Actions
    { id: 'new-note', label: 'Yeni Not', description: 'Hızlıca yeni not oluştur', icon: <Plus />, shortcut: 'Ctrl+N', category: 'note', action: () => onAction('new-note') },
    { id: 'save-note', label: 'Notu Kaydet', description: 'Aktif notu kaydet', icon: <Download />, shortcut: 'Ctrl+S', category: 'note', action: () => onAction('save-note') },
    { id: 'duplicate-note', label: 'Notu Kopyala', description: 'Aktif notun kopyasını oluştur', icon: <Copy />, category: 'note', action: () => onAction('duplicate-note') },
    { id: 'delete-note', label: 'Notu Sil', description: 'Aktif notu çöpe taşı', icon: <Trash2 />, category: 'note', action: () => onAction('delete-note') },
    { id: 'archive-note', label: 'Arşivle', description: 'Notu arşive taşı', icon: <Archive />, category: 'note', action: () => onAction('archive-note') },
    { id: 'pin-note', label: 'Sabitle/Kaldır', description: 'Notu en üste sabitle', icon: <Star />, shortcut: 'Ctrl+P', category: 'note', action: () => onAction('pin-note') },
    { id: 'lock-note', label: 'Kilitle/Aç', description: 'Notu kilitle veya aç', icon: <Lock />, category: 'note', action: () => onAction('lock-note') },
    { id: 'add-tags', label: 'Etiket Ekle', description: 'Nota etiket ekle', icon: <Tag />, shortcut: 'Ctrl+T', category: 'note', action: () => onAction('add-tags') },
    
    // Folder Actions
    { id: 'new-folder', label: 'Yeni Klasör', description: 'Yeni klasör oluştur', icon: <Folder />, category: 'folder', action: () => onAction('new-folder') },
    
    // View Actions
    { id: 'toggle-sidebar', label: 'Kenar Çubuğu', description: 'Kenar çubuğunu aç/kapat', icon: <List />, shortcut: 'Ctrl+B', category: 'view', action: () => onAction('toggle-sidebar') },
    { id: 'grid-view', label: 'Izgara Görünümü', description: 'Notları ızgara olarak göster', icon: <Grid />, category: 'view', action: () => onAction('grid-view') },
    { id: 'list-view', label: 'Liste Görünümü', description: 'Notları liste olarak göster', icon: <List />, category: 'view', action: () => onAction('list-view') },
    { id: 'focus-mode', label: 'Odak Modu', description: 'Dikkat dağıtmayan yazma modu', icon: <Zap />, shortcut: 'Ctrl+Shift+F', category: 'view', action: () => onAction('focus-mode') },
    { id: 'zen-mode', label: 'Zen Modu', description: 'Tam ekran yazma deneyimi', icon: <BookOpen />, shortcut: 'F11', category: 'view', action: () => onAction('zen-mode') },
    
    // Tools
    { id: 'smart-insights', label: 'Akıllı Analiz', description: 'AI ile not analizi', icon: <TrendingUp />, category: 'tools', action: () => onAction('smart-insights') },
    { id: 'pomodoro', label: 'Pomodoro Timer', description: 'Odaklanma zamanlayıcısı', icon: <Clock />, category: 'tools', action: () => onAction('pomodoro') },
    { id: 'export-pdf', label: 'PDF Olarak Dışa Aktar', description: 'Notu PDF formatında indir', icon: <Download />, category: 'tools', action: () => onAction('export-pdf') },
    { id: 'import-notes', label: 'Notları İçe Aktar', description: 'Dosyadan not içe aktar', icon: <Upload />, category: 'tools', action: () => onAction('import-notes') },
    
    // Settings
    { id: 'toggle-theme', label: 'Tema Değiştir', description: 'Açık/koyu tema', icon: <Moon />, shortcut: 'Ctrl+Shift+T', category: 'settings', action: () => onAction('toggle-theme') },
    { id: 'settings', label: 'Ayarlar', description: 'Uygulama ayarlarını aç', icon: <Settings />, shortcut: 'Ctrl+,', category: 'settings', action: () => onAction('settings') },
  ];

  // Filter actions based on search query
  const filteredActions = actions.filter(action => {
    const query = searchQuery.toLowerCase();
    return (
      action.label.toLowerCase().includes(query) ||
      action.description?.toLowerCase().includes(query) ||
      action.category.toLowerCase().includes(query)
    );
  });

  // Group actions by category
  const groupedActions = filteredActions.reduce((acc, action) => {
    if (!acc[action.category]) {
      acc[action.category] = [];
    }
    acc[action.category].push(action);
    return acc;
  }, {} as Record<string, QuickAction[]>);

  const categoryLabels: Record<string, string> = {
    note: '📝 Not İşlemleri',
    folder: '📁 Klasör İşlemleri',
    view: '👁️ Görünüm',
    tools: '🛠️ Araçlar',
    settings: '⚙️ Ayarlar'
  };

  // Flatten for keyboard navigation
  const flatActions = Object.values(groupedActions).flat();

  // Handle keyboard navigation
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (!isOpen) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => Math.min(prev + 1, flatActions.length - 1));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => Math.max(prev - 1, 0));
        break;
      case 'Enter':
        e.preventDefault();
        if (flatActions[selectedIndex]) {
          flatActions[selectedIndex].action();
          onClose();
        }
        break;
      case 'Escape':
        e.preventDefault();
        onClose();
        break;
    }
  }, [isOpen, flatActions, selectedIndex, onClose]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
      setSearchQuery('');
      setSelectedIndex(0);
    }
  }, [isOpen]);

  // Scroll selected item into view
  useEffect(() => {
    const selectedElement = listRef.current?.querySelector(`[data-index="${selectedIndex}"]`);
    selectedElement?.scrollIntoView({ block: 'nearest' });
  }, [selectedIndex]);

  // Global keyboard shortcut to open
  useEffect(() => {
    const handleGlobalKeydown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        if (isOpen) {
          onClose();
        } else {
          onAction('open-quick-actions');
        }
      }
    };
    window.addEventListener('keydown', handleGlobalKeydown);
    return () => window.removeEventListener('keydown', handleGlobalKeydown);
  }, [isOpen, onAction, onClose]);

  if (!isOpen) return null;

  let actionIndex = 0;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]"
        onClick={onClose}
      >
        {/* Backdrop */}
        <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />
        
        {/* Panel */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: -20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: -20 }}
          transition={{ duration: 0.15 }}
          className="relative w-full max-w-2xl mx-4 bg-white dark:bg-gray-900 rounded-2xl shadow-2xl overflow-hidden border border-gray-200 dark:border-gray-700"
          onClick={e => e.stopPropagation()}
        >
          {/* Search Header */}
          <div className="flex items-center gap-3 px-4 py-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-2 text-gray-400">
              <Command className="w-5 h-5" />
              <Search className="w-5 h-5" />
            </div>
            <input
              ref={inputRef}
              type="text"
              value={searchQuery}
              onChange={e => {
                setSearchQuery(e.target.value);
                setSelectedIndex(0);
              }}
              placeholder="Ne yapmak istiyorsunuz? Yazarak arayın..."
              className="flex-1 bg-transparent text-lg text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none"
            />
            <div className="flex items-center gap-1 px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded text-xs text-gray-500">
              ESC
            </div>
          </div>

          {/* Current Note Badge */}
          {currentNote && (
            <div className="px-4 py-2 bg-gradient-to-r from-purple-50 to-indigo-50 dark:from-purple-900/20 dark:to-indigo-900/20 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center gap-2 text-sm">
                <FileText className="text-purple-500" />
                <span className="text-gray-500">Aktif not:</span>
                <span className="font-medium text-gray-900 dark:text-white truncate">{currentNote.title}</span>
              </div>
            </div>
          )}

          {/* Actions List */}
          <div ref={listRef} className="max-h-[400px] overflow-y-auto p-2">
            {Object.entries(groupedActions).map(([category, categoryActions]) => (
              <div key={category} className="mb-2">
                <div className="px-3 py-2 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  {categoryLabels[category]}
                </div>
                {categoryActions.map(action => {
                  const currentIndex = actionIndex++;
                  const isSelected = currentIndex === selectedIndex;
                  
                  return (
                    <motion.button
                      key={action.id}
                      data-index={currentIndex}
                      onClick={() => {
                        action.action();
                        onClose();
                      }}
                      className={`w-full flex items-center gap-3 px-3 py-3 rounded-xl transition-all ${
                        isSelected
                          ? 'bg-gradient-to-r from-purple-500 to-indigo-500 text-white shadow-lg'
                          : 'hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300'
                      }`}
                      whileHover={{ scale: 1.01 }}
                      whileTap={{ scale: 0.99 }}
                    >
                      <div className={`p-2 rounded-lg ${
                        isSelected
                          ? 'bg-white/20'
                          : 'bg-gray-100 dark:bg-gray-700'
                      }`}>
                        {action.icon}
                      </div>
                      <div className="flex-1 text-left">
                        <div className="font-medium">{action.label}</div>
                        {action.description && (
                          <div className={`text-sm ${isSelected ? 'text-white/70' : 'text-gray-500'}`}>
                            {action.description}
                          </div>
                        )}
                      </div>
                      {action.shortcut && (
                        <div className={`px-2 py-1 rounded text-xs font-mono ${
                          isSelected
                            ? 'bg-white/20 text-white'
                            : 'bg-gray-100 dark:bg-gray-700 text-gray-500'
                        }`}>
                          {action.shortcut}
                        </div>
                      )}
                    </motion.button>
                  );
                })}
              </div>
            ))}

            {flatActions.length === 0 && (
              <div className="text-center py-12 text-gray-500">
                <Search className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>Sonuç bulunamadı</p>
                <p className="text-sm mt-1">Farklı bir arama deneyin</p>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
            <div className="flex items-center gap-4 text-xs text-gray-500">
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-gray-200 dark:bg-gray-700 rounded">↑↓</kbd>
                Gezin
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-gray-200 dark:bg-gray-700 rounded">Enter</kbd>
                Seç
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-gray-200 dark:bg-gray-700 rounded">ESC</kbd>
                Kapat
              </span>
            </div>
            <div className="text-xs text-gray-400">
              ⌘K ile hızlı erişim
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default QuickActionsPanel;
