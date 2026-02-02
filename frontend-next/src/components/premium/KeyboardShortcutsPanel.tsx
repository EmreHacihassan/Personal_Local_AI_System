'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Command, Info } from 'lucide-react';

interface ShortcutCategory {
  name: string;
  icon: string;
  shortcuts: {
    keys: string[];
    description: string;
  }[];
}

interface KeyboardShortcutsPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

const KeyboardShortcutsPanel: React.FC<KeyboardShortcutsPanelProps> = ({
  isOpen,
  onClose
}) => {
  const shortcutCategories: ShortcutCategory[] = [
    {
      name: 'Genel',
      icon: '⌨️',
      shortcuts: [
        { keys: ['Ctrl', 'K'], description: 'Hızlı Komutlar' },
        { keys: ['Ctrl', 'N'], description: 'Yeni Not' },
        { keys: ['Ctrl', 'S'], description: 'Kaydet' },
        { keys: ['Ctrl', 'F'], description: 'Ara' },
        { keys: ['Ctrl', 'Shift', 'F'], description: 'Gelişmiş Arama' },
        { keys: ['Esc'], description: 'Paneli Kapat / Vazgeç' },
      ]
    },
    {
      name: 'Düzenleme',
      icon: '✏️',
      shortcuts: [
        { keys: ['Ctrl', 'B'], description: 'Kalın' },
        { keys: ['Ctrl', 'I'], description: 'İtalik' },
        { keys: ['Ctrl', 'U'], description: 'Altı Çizili' },
        { keys: ['Ctrl', 'Z'], description: 'Geri Al' },
        { keys: ['Ctrl', 'Shift', 'Z'], description: 'Yinele' },
        { keys: ['Ctrl', 'A'], description: 'Tümünü Seç' },
      ]
    },
    {
      name: 'Görünüm',
      icon: '👁️',
      shortcuts: [
        { keys: ['F11'], description: 'Tam Ekran' },
        { keys: ['Ctrl', 'Shift', 'Z'], description: 'Zen Modu' },
        { keys: ['Ctrl', '+'], description: 'Yakınlaştır' },
        { keys: ['Ctrl', '-'], description: 'Uzaklaştır' },
        { keys: ['Ctrl', '0'], description: 'Varsayılan Zoom' },
      ]
    },
    {
      name: 'Navigasyon',
      icon: '🧭',
      shortcuts: [
        { keys: ['Ctrl', '↑'], description: 'Önceki Not' },
        { keys: ['Ctrl', '↓'], description: 'Sonraki Not' },
        { keys: ['Alt', '←'], description: 'Geri Git' },
        { keys: ['Alt', '→'], description: 'İleri Git' },
        { keys: ['Ctrl', 'Home'], description: 'En Üste' },
        { keys: ['Ctrl', 'End'], description: 'En Alta' },
      ]
    },
    {
      name: 'Premium Özellikler',
      icon: '✨',
      shortcuts: [
        { keys: ['Ctrl', 'Shift', 'I'], description: 'AI Asistanı' },
        { keys: ['Ctrl', 'Shift', 'P'], description: 'Pomodoro Timer' },
        { keys: ['Ctrl', 'Shift', 'S'], description: 'İstatistikler' },
        { keys: ['Ctrl', 'Shift', 'B'], description: 'Akıllı Analiz' },
        { keys: ['?'], description: 'Bu Paneli Aç' },
      ]
    },
  ];

  // Listen for ? key to open
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === '?' && !e.ctrlKey && !e.metaKey) {
        // Only if not in an input
        const target = e.target as HTMLElement;
        if (target.tagName !== 'INPUT' && target.tagName !== 'TEXTAREA') {
          e.preventDefault();
          // Toggle or callback
        }
      }
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center p-4"
        onClick={onClose}
      >
        {/* Backdrop */}
        <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />

        {/* Modal */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          className="relative w-full max-w-3xl max-h-[80vh] bg-white dark:bg-gray-900 rounded-2xl shadow-2xl overflow-hidden"
          onClick={e => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-indigo-500/10 to-purple-500/10">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-xl text-white">
                <Command className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-gray-900 dark:text-white">
                  Klavye Kısayolları
                </h2>
                <p className="text-xs text-gray-500">Daha hızlı çalışmak için kısayolları öğrenin</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>

          {/* Content */}
          <div className="p-6 overflow-y-auto max-h-[calc(80vh-100px)]">
            <div className="grid md:grid-cols-2 gap-6">
              {shortcutCategories.map((category, catIdx) => (
                <motion.div
                  key={category.name}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: catIdx * 0.05 }}
                  className="space-y-3"
                >
                  <h3 className="flex items-center gap-2 text-sm font-semibold text-gray-900 dark:text-white">
                    <span>{category.icon}</span>
                    {category.name}
                  </h3>
                  <div className="space-y-2">
                    {category.shortcuts.map((shortcut, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800 rounded-lg"
                      >
                        <span className="text-sm text-gray-600 dark:text-gray-400">
                          {shortcut.description}
                        </span>
                        <div className="flex items-center gap-1">
                          {shortcut.keys.map((key, keyIdx) => (
                            <React.Fragment key={keyIdx}>
                              <kbd className="px-2 py-1 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-xs font-mono shadow-sm">
                                {key}
                              </kbd>
                              {keyIdx < shortcut.keys.length - 1 && (
                                <span className="text-gray-400 text-xs">+</span>
                              )}
                            </React.Fragment>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </motion.div>
              ))}
            </div>

            {/* Tip */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 }}
              className="mt-6 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-xl border border-blue-100 dark:border-blue-800"
            >
              <div className="flex items-start gap-3">
                <Info className="w-5 h-5 text-blue-500 mt-0.5" />
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  <strong className="text-gray-900 dark:text-white">İpucu:</strong>{' '}
                  Bu paneli herhangi bir zamanda <kbd className="px-1.5 py-0.5 bg-white dark:bg-gray-700 rounded text-xs mx-1">?</kbd> tuşuna basarak açabilirsiniz.
                  Kısayolları öğrendikçe üretkenliğiniz artacak!
                </div>
              </div>
            </motion.div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default KeyboardShortcutsPanel;
