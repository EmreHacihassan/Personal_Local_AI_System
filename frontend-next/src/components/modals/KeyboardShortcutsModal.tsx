'use client';

import { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Keyboard } from 'lucide-react';
import { useStore } from '@/store/useStore';

interface KeyboardShortcutsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function KeyboardShortcutsModal({ isOpen, onClose }: KeyboardShortcutsModalProps) {
  const { language } = useStore();

  // Close on escape
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      window.addEventListener('keydown', handleEscape);
      return () => window.removeEventListener('keydown', handleEscape);
    }
  }, [isOpen, onClose]);

  const t = {
    title: { tr: 'Klavye Kısayolları', en: 'Keyboard Shortcuts', de: 'Tastaturkürzel' },
    general: { tr: 'Genel', en: 'General', de: 'Allgemein' },
    chat: { tr: 'Sohbet', en: 'Chat', de: 'Chat' },
    navigation: { tr: 'Navigasyon', en: 'Navigation', de: 'Navigation' },
    editing: { tr: 'Düzenleme', en: 'Editing', de: 'Bearbeitung' },
  };

  const shortcuts = {
    general: [
      { keys: ['Ctrl', '?'], action: { tr: 'Kısayolları göster', en: 'Show shortcuts', de: 'Kürzel anzeigen' } },
      { keys: ['Ctrl', 'K'], action: { tr: 'Hızlı arama', en: 'Quick search', de: 'Schnellsuche' } },
      { keys: ['Ctrl', 'N'], action: { tr: 'Yeni sohbet', en: 'New chat', de: 'Neuer Chat' } },
      { keys: ['Ctrl', ','], action: { tr: 'Ayarlar', en: 'Settings', de: 'Einstellungen' } },
      { keys: ['Ctrl', 'Shift', 'T'], action: { tr: 'Tema değiştir', en: 'Toggle theme', de: 'Thema wechseln' } },
    ],
    chat: [
      { keys: ['Enter'], action: { tr: 'Mesaj gönder', en: 'Send message', de: 'Nachricht senden' } },
      { keys: ['Shift', 'Enter'], action: { tr: 'Yeni satır', en: 'New line', de: 'Neue Zeile' } },
      { keys: ['Ctrl', 'Enter'], action: { tr: 'Mesajı gönder (alternatif)', en: 'Send message (alt)', de: 'Nachricht senden (alt)' } },
      { keys: ['Esc'], action: { tr: 'Üretimi durdur', en: 'Stop generation', de: 'Generierung stoppen' } },
      { keys: ['Ctrl', 'R'], action: { tr: 'Yanıtı yeniden oluştur', en: 'Regenerate response', de: 'Antwort neu generieren' } },
      { keys: ['Ctrl', 'C'], action: { tr: 'Yanıtı kopyala', en: 'Copy response', de: 'Antwort kopieren' } },
    ],
    navigation: [
      { keys: ['Ctrl', '1'], action: { tr: 'Sohbet sayfasına git', en: 'Go to Chat', de: 'Zum Chat' } },
      { keys: ['Ctrl', '2'], action: { tr: 'Geçmiş sayfasına git', en: 'Go to History', de: 'Zum Verlauf' } },
      { keys: ['Ctrl', '3'], action: { tr: 'Notlar sayfasına git', en: 'Go to Notes', de: 'Zu Notizen' } },
      { keys: ['Ctrl', '4'], action: { tr: 'Belgeler sayfasına git', en: 'Go to Documents', de: 'Zu Dokumenten' } },
      { keys: ['Ctrl', '5'], action: { tr: 'Öğrenme sayfasına git', en: 'Go to Learning', de: 'Zum Lernen' } },
      { keys: ['Ctrl', 'B'], action: { tr: 'Kenar çubuğunu aç/kapa', en: 'Toggle sidebar', de: 'Seitenleiste umschalten' } },
    ],
    editing: [
      { keys: ['Ctrl', 'Z'], action: { tr: 'Geri al', en: 'Undo', de: 'Rückgängig' } },
      { keys: ['Ctrl', 'Shift', 'Z'], action: { tr: 'Yinele', en: 'Redo', de: 'Wiederholen' } },
      { keys: ['Ctrl', 'A'], action: { tr: 'Tümünü seç', en: 'Select all', de: 'Alles auswählen' } },
      { keys: ['Ctrl', 'S'], action: { tr: 'Kaydet', en: 'Save', de: 'Speichern' } },
      { keys: ['Tab'], action: { tr: 'Girinti ekle', en: 'Indent', de: 'Einrücken' } },
    ],
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50"
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="fixed inset-0 flex items-center justify-center z-50 p-4"
          >
            <div 
              className="bg-card border border-border rounded-2xl shadow-2xl w-full max-w-3xl max-h-[80vh] overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-muted/30">
                <div className="flex items-center gap-3">
                  <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 text-white">
                    <Keyboard className="w-5 h-5" />
                  </div>
                  <h2 className="text-lg font-semibold">{t.title[language]}</h2>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 hover:bg-accent rounded-lg transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Content */}
              <div className="p-6 overflow-y-auto max-h-[calc(80vh-80px)]">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* General */}
                  <div>
                    <h3 className="text-sm font-semibold text-muted-foreground mb-3">{t.general[language]}</h3>
                    <div className="space-y-2">
                      {shortcuts.general.map((shortcut, index) => (
                        <ShortcutRow key={index} keys={shortcut.keys} action={shortcut.action[language]} />
                      ))}
                    </div>
                  </div>

                  {/* Chat */}
                  <div>
                    <h3 className="text-sm font-semibold text-muted-foreground mb-3">{t.chat[language]}</h3>
                    <div className="space-y-2">
                      {shortcuts.chat.map((shortcut, index) => (
                        <ShortcutRow key={index} keys={shortcut.keys} action={shortcut.action[language]} />
                      ))}
                    </div>
                  </div>

                  {/* Navigation */}
                  <div>
                    <h3 className="text-sm font-semibold text-muted-foreground mb-3">{t.navigation[language]}</h3>
                    <div className="space-y-2">
                      {shortcuts.navigation.map((shortcut, index) => (
                        <ShortcutRow key={index} keys={shortcut.keys} action={shortcut.action[language]} />
                      ))}
                    </div>
                  </div>

                  {/* Editing */}
                  <div>
                    <h3 className="text-sm font-semibold text-muted-foreground mb-3">{t.editing[language]}</h3>
                    <div className="space-y-2">
                      {shortcuts.editing.map((shortcut, index) => (
                        <ShortcutRow key={index} keys={shortcut.keys} action={shortcut.action[language]} />
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Footer */}
              <div className="px-6 py-3 border-t border-border bg-muted/30 text-center">
                <p className="text-xs text-muted-foreground">
                  {language === 'tr' ? 'Kısayolları kapatmak için' : language === 'de' ? 'Drücken Sie' : 'Press'} 
                  <kbd className="mx-1 px-1.5 py-0.5 bg-background border border-border rounded text-xs font-mono">Esc</kbd> 
                  {language === 'tr' ? 'tuşuna basın' : language === 'de' ? 'zum Schließen' : 'to close'}
                </p>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

function ShortcutRow({ keys, action }: { keys: string[]; action: string }) {
  return (
    <div className="flex items-center justify-between py-1.5">
      <span className="text-sm">{action}</span>
      <div className="flex items-center gap-1">
        {keys.map((key, index) => (
          <span key={index} className="flex items-center">
            <kbd className="px-2 py-1 bg-background border border-border rounded text-xs font-mono min-w-[28px] text-center">
              {key}
            </kbd>
            {index < keys.length - 1 && <span className="mx-0.5 text-muted-foreground">+</span>}
          </span>
        ))}
      </div>
    </div>
  );
}
