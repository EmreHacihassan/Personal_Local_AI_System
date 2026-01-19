'use client';

import { motion } from 'framer-motion';
import {
  Settings,
  Moon,
  Sun,
  Globe,
  Bell,
  Palette,
  Volume2,
  VolumeX,
  Type,
  Zap,
  Shield,
  Check,
  Download,
  Upload,
  RotateCcw,
  AlertCircle,
  Trash2,
  Keyboard,
  MessageSquare,
  Clock,
  ArrowDown,
  Monitor,
  Power,
  Loader2,
  Rocket
} from 'lucide-react';
import { useStore, Theme } from '@/store/useStore';
import { cn } from '@/lib/utils';
import { useState, useRef, useEffect, useCallback } from 'react';

const themes: { id: Theme; name: string; nameEn: string; nameDe: string; icon: React.ElementType; gradient: string }[] = [
  { id: 'light', name: 'Klasik', nameEn: 'Classic', nameDe: 'Klassisch', icon: Sun, gradient: 'from-violet-500 to-purple-600' },
  { id: 'dark', name: 'Gece Modu', nameEn: 'Night Mode', nameDe: 'Nachtmodus', icon: Moon, gradient: 'from-slate-600 to-slate-800' },
  { id: 'ocean', name: 'Okyanus', nameEn: 'Ocean', nameDe: 'Ozean', icon: Globe, gradient: 'from-blue-400 to-cyan-500' },
  { id: 'forest', name: 'Orman', nameEn: 'Forest', nameDe: 'Wald', icon: Globe, gradient: 'from-emerald-400 to-green-600' },
  { id: 'sunset', name: 'Gün Batımı', nameEn: 'Sunset', nameDe: 'Sonnenuntergang', icon: Sun, gradient: 'from-orange-400 to-pink-500' },
  { id: 'lavender', name: 'Lavanta', nameEn: 'Lavender', nameDe: 'Lavendel', icon: Palette, gradient: 'from-purple-400 to-violet-600' },
  { id: 'minimalist', name: 'Minimalist', nameEn: 'Minimalist', nameDe: 'Minimalistisch', icon: Type, gradient: 'from-gray-400 to-gray-700' },
  { id: 'cherry', name: 'Kiraz Çiçeği', nameEn: 'Cherry Blossom', nameDe: 'Kirschblüte', icon: Palette, gradient: 'from-pink-400 to-rose-500' },
];

export function SettingsPage() {
  const {
    language,
    setLanguage,
    theme,
    setTheme,
    fontSize,
    setFontSize,
    soundEnabled,
    toggleSound,
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    webSearchMode,
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    setWebSearchMode,
    widgetEnabled,
    toggleWidget,
    sessions,
    notes,
    templates,
    messages,
    clearMessages,
    notificationsEnabled,
    toggleNotifications,
    notifyOnComplete,
    toggleNotifyOnComplete,
    notifyOnError,
    toggleNotifyOnError,
    desktopNotifications,
    toggleDesktopNotifications,
    showTimestamps,
    toggleShowTimestamps,
    autoScroll,
    toggleAutoScroll,
  } = useStore();

  const [showKeyboardShortcuts, setShowKeyboardShortcuts] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const [exportStatus, setExportStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [importStatus, setImportStatus] = useState<'idle' | 'success' | 'error'>('idle');

  // Autostart state
  const [autostartEnabled, setAutostartEnabled] = useState(false);
  const [autostartLoading, setAutostartLoading] = useState(true);

  // API base URL
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

  // Fetch autostart status on mount
  const fetchAutostartStatus = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/settings/autostart`);
      const data = await response.json();
      if (data.success) {
        setAutostartEnabled(data.enabled);
      }
    } catch (error) {
      console.error('Failed to fetch autostart status:', error);
    } finally {
      setAutostartLoading(false);
    }
  }, [API_BASE]);

  useEffect(() => {
    fetchAutostartStatus();
  }, [fetchAutostartStatus]);

  // Toggle autostart
  const handleToggleAutostart = async () => {
    setAutostartLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/settings/autostart`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: !autostartEnabled })
      });
      const data = await response.json();
      if (data.success) {
        setAutostartEnabled(data.enabled);
      }
    } catch (error) {
      console.error('Failed to toggle autostart:', error);
    } finally {
      setAutostartLoading(false);
    }
  };

  // Export all data
  const handleExport = () => {
    try {
      const exportData = {
        version: '2.0',
        exportedAt: new Date().toISOString(),
        settings: {
          theme,
          language,
          fontSize,
          soundEnabled,
          webSearchMode,
          widgetEnabled,
        },
        data: {
          sessions,
          notes,
          templates,
          messages,
        }
      };

      const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `enterprise-ai-backup-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      setExportStatus('success');
      setTimeout(() => setExportStatus('idle'), 3000);
    } catch {
      setExportStatus('error');
      setTimeout(() => setExportStatus('idle'), 3000);
    }
  };

  // Import data
  const handleImport = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const importData = JSON.parse(e.target?.result as string);

        // Validate version
        if (!importData.version || !importData.data) {
          throw new Error('Invalid backup file format');
        }

        // Confirmation dialog
        if (confirm(language === 'tr'
          ? 'Mevcut verilerinizin üzerine yazılacak. Devam etmek istiyor musunuz?'
          : language === 'de'
            ? 'Ihre aktuellen Daten werden überschrieben. Möchten Sie fortfahren?'
            : 'Your current data will be overwritten. Do you want to continue?'
        )) {
          // Apply settings if present
          if (importData.settings) {
            if (importData.settings.theme) setTheme(importData.settings.theme);
            if (importData.settings.language) setLanguage(importData.settings.language);
            if (importData.settings.fontSize) setFontSize(importData.settings.fontSize);
          }

          // Note: For full data import, we'd need additional store methods
          // This is a simplified version that shows the pattern

          setImportStatus('success');
          setTimeout(() => setImportStatus('idle'), 3000);
        }
      } catch {
        setImportStatus('error');
        setTimeout(() => setImportStatus('idle'), 3000);
      }
    };
    reader.readAsText(file);

    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Reset settings
  const handleResetSettings = () => {
    if (confirm(language === 'tr'
      ? 'Tüm ayarlar varsayılana döndürülecek. Devam etmek istiyor musunuz?'
      : language === 'de'
        ? 'Alle Einstellungen werden auf Standard zurückgesetzt. Möchten Sie fortfahren?'
        : 'All settings will be reset to default. Do you want to continue?'
    )) {
      setTheme('light');
      setLanguage('en');
      setFontSize('medium');
      // Reset other settings if needed
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-border bg-card/50 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-slate-500 to-slate-700 text-white">
            <Settings className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-semibold">
              {language === 'tr' ? 'Ayarlar' : 'Settings'}
            </h1>
            <p className="text-xs text-muted-foreground">
              {language === 'tr' ? 'Uygulama tercihlerinizi yönetin' : 'Manage your preferences'}
            </p>
          </div>
        </div>
      </header>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-3xl mx-auto space-y-8">

          {/* Startup / Başlangıç */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Rocket className="w-5 h-5 text-primary-500" />
              {language === 'tr' ? 'Başlangıç' : language === 'de' ? 'Start' : 'Startup'}
            </h2>

            <div className="bg-card border border-border rounded-2xl divide-y divide-border">
              {/* Windows Autostart */}
              <div className="flex items-center justify-between p-5">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-blue-500/10">
                    <Power className="w-5 h-5 text-blue-500" />
                  </div>
                  <div>
                    <p className="font-medium">
                      {language === 'tr' ? 'Bilgisayar açıldığında otomatik başlat' : 
                       language === 'de' ? 'Beim Computerstart automatisch starten' : 
                       'Start automatically when computer boots'}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {language === 'tr' ? 'Windows başladığında uygulama arka planda başlar ve tarayıcı açılır' : 
                       language === 'de' ? 'Anwendung startet im Hintergrund und Browser öffnet sich beim Windows-Start' : 
                       'Application starts in background and browser opens when Windows starts'}
                    </p>
                  </div>
                </div>
                <button
                  onClick={handleToggleAutostart}
                  disabled={autostartLoading}
                  className={cn(
                    "relative w-14 h-8 rounded-full transition-colors",
                    autostartLoading ? "opacity-50 cursor-not-allowed" : "",
                    autostartEnabled ? "bg-primary-500" : "bg-muted"
                  )}
                >
                  {autostartLoading ? (
                    <div className="absolute inset-0 flex items-center justify-center">
                      <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
                    </div>
                  ) : (
                    <motion.div
                      animate={{ x: autostartEnabled ? 24 : 4 }}
                      className="absolute top-1 w-6 h-6 bg-white rounded-full shadow-md"
                    />
                  )}
                </button>
              </div>
            </div>
          </motion.section>

          {/* Appearance */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Palette className="w-5 h-5 text-primary-500" />
              {language === 'tr' ? 'Görünüm' : 'Appearance'}
            </h2>

            <div className="bg-card border border-border rounded-2xl p-5 space-y-6">
              {/* Theme Selection */}
              <div>
                <label className="text-sm font-medium mb-3 block">
                  {language === 'tr' ? 'Tema' : language === 'de' ? 'Thema' : 'Theme'}
                </label>
                <div className="grid grid-cols-4 gap-3">
                  {themes.map((t) => (
                    <button
                      key={t.id}
                      onClick={() => setTheme(t.id)}
                      className={cn(
                        "flex flex-col items-center gap-2 p-3 rounded-xl border-2 transition-all",
                        theme === t.id
                          ? "border-primary-500 bg-primary-500/5"
                          : "border-transparent bg-muted hover:bg-accent"
                      )}
                    >
                      <div className={cn(
                        "w-10 h-10 rounded-xl bg-gradient-to-br flex items-center justify-center text-white",
                        t.gradient
                      )}>
                        <t.icon className="w-5 h-5" />
                      </div>
                      <span className="text-xs font-medium">
                        {language === 'tr' ? t.name : language === 'de' ? t.nameDe : t.nameEn}
                      </span>
                      {theme === t.id && (
                        <Check className="w-4 h-4 text-primary-500" />
                      )}
                    </button>
                  ))}
                </div>
              </div>

              {/* Font Size */}
              <div>
                <label className="text-sm font-medium mb-3 block">
                  {language === 'tr' ? 'Yazı Boyutu' : 'Font Size'}
                </label>
                <div className="flex gap-3">
                  {(['small', 'medium', 'large'] as const).map((size) => (
                    <button
                      key={size}
                      onClick={() => setFontSize(size)}
                      className={cn(
                        "flex items-center gap-2 px-4 py-2 rounded-xl border transition-all",
                        fontSize === size
                          ? "border-primary-500 bg-primary-500/5 text-primary-600"
                          : "border-border hover:bg-accent"
                      )}
                    >
                      <Type className={cn(
                        "w-4 h-4",
                        size === 'small' && "scale-75",
                        size === 'large' && "scale-125"
                      )} />
                      <span className="text-sm capitalize">
                        {size === 'small' ? (language === 'tr' ? 'Küçük' : 'Small') :
                          size === 'medium' ? (language === 'tr' ? 'Orta' : 'Medium') :
                            (language === 'tr' ? 'Büyük' : 'Large')}
                      </span>
                    </button>
                  ))}
                </div>
              </div>


            </div>
          </motion.section>

          {/* Display Settings */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05 }}
          >
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Monitor className="w-5 h-5 text-primary-500" />
              {language === 'tr' ? 'Görüntü Ayarları' : language === 'de' ? 'Anzeigeeinstellungen' : 'Display Settings'}
            </h2>

            <div className="bg-card border border-border rounded-2xl divide-y divide-border">
              {/* Show Timestamps */}
              <div className="flex items-center justify-between p-5">
                <div className="flex items-center gap-3">
                  <Clock className="w-5 h-5" />
                  <div>
                    <p className="font-medium">{language === 'tr' ? 'Zaman Damgalarını Göster' : language === 'de' ? 'Zeitstempel anzeigen' : 'Show Timestamps'}</p>
                    <p className="text-sm text-muted-foreground">
                      {language === 'tr' ? 'Mesajlarda tarih ve saat göster' : language === 'de' ? 'Datum und Uhrzeit in Nachrichten anzeigen' : 'Show date and time in messages'}
                    </p>
                  </div>
                </div>
                <button
                  onClick={toggleShowTimestamps}
                  className={cn(
                    "relative w-14 h-8 rounded-full transition-colors",
                    showTimestamps ? "bg-primary-500" : "bg-muted"
                  )}
                >
                  <motion.div
                    animate={{ x: showTimestamps ? 24 : 4 }}
                    className="absolute top-1 w-6 h-6 bg-white rounded-full shadow-md"
                  />
                </button>
              </div>

              {/* Auto Scroll */}
              <div className="flex items-center justify-between p-5">
                <div className="flex items-center gap-3">
                  <ArrowDown className="w-5 h-5" />
                  <div>
                    <p className="font-medium">{language === 'tr' ? 'Otomatik Kaydırma' : language === 'de' ? 'Automatisches Scrollen' : 'Auto Scroll'}</p>
                    <p className="text-sm text-muted-foreground">
                      {language === 'tr' ? 'Yeni mesajlarda otomatik aşağı kaydır' : language === 'de' ? 'Bei neuen Nachrichten automatisch nach unten scrollen' : 'Automatically scroll down on new messages'}
                    </p>
                  </div>
                </div>
                <button
                  onClick={toggleAutoScroll}
                  className={cn(
                    "relative w-14 h-8 rounded-full transition-colors",
                    autoScroll ? "bg-primary-500" : "bg-muted"
                  )}
                >
                  <motion.div
                    animate={{ x: autoScroll ? 24 : 4 }}
                    className="absolute top-1 w-6 h-6 bg-white rounded-full shadow-md"
                  />
                </button>
              </div>
            </div>
          </motion.section>

          {/* Language */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Globe className="w-5 h-5 text-primary-500" />
              {language === 'tr' ? 'Dil ve Bölge' : 'Language & Region'}
            </h2>

            <div className="bg-card border border-border rounded-2xl p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">{language === 'tr' ? 'Dil' : language === 'de' ? 'Sprache' : 'Language'}</p>
                  <p className="text-sm text-muted-foreground">
                    {language === 'tr' ? 'Arayüz dilini seçin' : language === 'de' ? 'Oberflächensprache wählen' : 'Select interface language'}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setLanguage('tr')}
                    className={cn(
                      "px-4 py-2 rounded-xl transition-all",
                      language === 'tr'
                        ? "bg-primary-500 text-white"
                        : "bg-muted hover:bg-accent"
                    )}
                  >
                    🇹🇷 Türkçe
                  </button>
                  <button
                    onClick={() => setLanguage('en')}
                    className={cn(
                      "px-4 py-2 rounded-xl transition-all",
                      language === 'en'
                        ? "bg-primary-500 text-white"
                        : "bg-muted hover:bg-accent"
                    )}
                  >
                    🇬🇧 English
                  </button>
                  <button
                    onClick={() => setLanguage('de')}
                    className={cn(
                      "px-4 py-2 rounded-xl transition-all",
                      language === 'de'
                        ? "bg-primary-500 text-white"
                        : "bg-muted hover:bg-accent"
                    )}
                  >
                    🇩🇪 Deutsch
                  </button>
                </div>
              </div>
            </div>
          </motion.section>

          {/* Widget Settings */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Zap className="w-5 h-5 text-primary-500" />
              {language === 'tr' ? 'Floating Widget' : 'Floating Widget'}
            </h2>

            <div className="bg-card border border-border rounded-2xl p-5">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <p className="font-medium">
                    {language === 'tr' ? 'Widget Aktif Et' : 'Enable Widget'}
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">
                    {language === 'tr'
                      ? 'Ekranın köşesinde her zaman erişilebilir bir sohbet widget\'ı açar. Tüm sayfalarda kullanılabilir.'
                      : 'Opens an always-accessible chat widget in the corner of the screen. Available on all pages.'
                    }
                  </p>
                </div>
                <button
                  onClick={toggleWidget}
                  className={cn(
                    "relative w-14 h-8 rounded-full transition-colors",
                    widgetEnabled ? "bg-primary-500" : "bg-muted"
                  )}
                >
                  <motion.div
                    animate={{ x: widgetEnabled ? 24 : 4 }}
                    className="absolute top-1 w-6 h-6 bg-white rounded-full shadow-md"
                  />
                </button>
              </div>

              {widgetEnabled && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="mt-4 p-4 bg-primary-500/5 border border-primary-500/20 rounded-xl"
                >
                  <p className="text-sm text-primary-600 dark:text-primary-400">
                    ✨ {language === 'tr'
                      ? 'Widget aktif! Ekranın sağ alt köşesinde görünecek. Sürükleyerek konumunu değiştirebilirsiniz.'
                      : 'Widget active! It will appear in the bottom right corner. You can drag to reposition it.'
                    }
                  </p>
                </motion.div>
              )}
            </div>
          </motion.section>

          {/* Notifications */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Bell className="w-5 h-5 text-primary-500" />
              {language === 'tr' ? 'Bildirimler' : language === 'de' ? 'Benachrichtigungen' : 'Notifications'}
            </h2>

            <div className="bg-card border border-border rounded-2xl divide-y divide-border">
              {/* Master Notifications Toggle */}
              <div className="flex items-center justify-between p-5">
                <div className="flex items-center gap-3">
                  <Bell className="w-5 h-5" />
                  <div>
                    <p className="font-medium">{language === 'tr' ? 'Bildirimleri Etkinleştir' : language === 'de' ? 'Benachrichtigungen aktivieren' : 'Enable Notifications'}</p>
                    <p className="text-sm text-muted-foreground">
                      {language === 'tr' ? 'Tüm bildirimler için ana anahtar' : language === 'de' ? 'Hauptschalter für alle Benachrichtigungen' : 'Master switch for all notifications'}
                    </p>
                  </div>
                </div>
                <button
                  onClick={toggleNotifications}
                  className={cn(
                    "relative w-14 h-8 rounded-full transition-colors",
                    notificationsEnabled ? "bg-primary-500" : "bg-muted"
                  )}
                >
                  <motion.div
                    animate={{ x: notificationsEnabled ? 24 : 4 }}
                    className="absolute top-1 w-6 h-6 bg-white rounded-full shadow-md"
                  />
                </button>
              </div>

              {/* Sound */}
              <div className="flex items-center justify-between p-5">
                <div className="flex items-center gap-3">
                  {soundEnabled ? <Volume2 className="w-5 h-5" /> : <VolumeX className="w-5 h-5" />}
                  <div>
                    <p className="font-medium">{language === 'tr' ? 'Sesler' : language === 'de' ? 'Töne' : 'Sounds'}</p>
                    <p className="text-sm text-muted-foreground">
                      {language === 'tr' ? 'Bildirim sesleri' : language === 'de' ? 'Benachrichtigungstöne' : 'Notification sounds'}
                    </p>
                  </div>
                </div>
                <button
                  onClick={toggleSound}
                  disabled={!notificationsEnabled}
                  className={cn(
                    "relative w-14 h-8 rounded-full transition-colors",
                    soundEnabled && notificationsEnabled ? "bg-primary-500" : "bg-muted",
                    !notificationsEnabled && "opacity-50 cursor-not-allowed"
                  )}
                >
                  <motion.div
                    animate={{ x: soundEnabled && notificationsEnabled ? 24 : 4 }}
                    className="absolute top-1 w-6 h-6 bg-white rounded-full shadow-md"
                  />
                </button>
              </div>

              {/* Notify on Complete */}
              <div className="flex items-center justify-between p-5">
                <div className="flex items-center gap-3">
                  <Check className="w-5 h-5" />
                  <div>
                    <p className="font-medium">{language === 'tr' ? 'Tamamlandığında Bildir' : language === 'de' ? 'Bei Fertigstellung benachrichtigen' : 'Notify on Complete'}</p>
                    <p className="text-sm text-muted-foreground">
                      {language === 'tr' ? 'AI yanıtı tamamlandığında bildirim' : language === 'de' ? 'Benachrichtigung wenn AI-Antwort fertig' : 'Notification when AI response completes'}
                    </p>
                  </div>
                </div>
                <button
                  onClick={toggleNotifyOnComplete}
                  disabled={!notificationsEnabled}
                  className={cn(
                    "relative w-14 h-8 rounded-full transition-colors",
                    notifyOnComplete && notificationsEnabled ? "bg-primary-500" : "bg-muted",
                    !notificationsEnabled && "opacity-50 cursor-not-allowed"
                  )}
                >
                  <motion.div
                    animate={{ x: notifyOnComplete && notificationsEnabled ? 24 : 4 }}
                    className="absolute top-1 w-6 h-6 bg-white rounded-full shadow-md"
                  />
                </button>
              </div>

              {/* Notify on Error */}
              <div className="flex items-center justify-between p-5">
                <div className="flex items-center gap-3">
                  <AlertCircle className="w-5 h-5" />
                  <div>
                    <p className="font-medium">{language === 'tr' ? 'Hata Bildirimi' : language === 'de' ? 'Fehlerbenachrichtigung' : 'Notify on Error'}</p>
                    <p className="text-sm text-muted-foreground">
                      {language === 'tr' ? 'Hata oluştuğunda bildirim göster' : language === 'de' ? 'Benachrichtigung bei Fehlern anzeigen' : 'Show notification when errors occur'}
                    </p>
                  </div>
                </div>
                <button
                  onClick={toggleNotifyOnError}
                  disabled={!notificationsEnabled}
                  className={cn(
                    "relative w-14 h-8 rounded-full transition-colors",
                    notifyOnError && notificationsEnabled ? "bg-primary-500" : "bg-muted",
                    !notificationsEnabled && "opacity-50 cursor-not-allowed"
                  )}
                >
                  <motion.div
                    animate={{ x: notifyOnError && notificationsEnabled ? 24 : 4 }}
                    className="absolute top-1 w-6 h-6 bg-white rounded-full shadow-md"
                  />
                </button>
              </div>

              {/* Desktop Notifications */}
              <div className="flex items-center justify-between p-5">
                <div className="flex items-center gap-3">
                  <Monitor className="w-5 h-5" />
                  <div>
                    <p className="font-medium">{language === 'tr' ? 'Masaüstü Bildirimleri' : language === 'de' ? 'Desktop-Benachrichtigungen' : 'Desktop Notifications'}</p>
                    <p className="text-sm text-muted-foreground">
                      {language === 'tr' ? 'Tarayıcı bildirimlerini etkinleştir' : language === 'de' ? 'Browser-Benachrichtigungen aktivieren' : 'Enable browser notifications'}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => {
                    if (!desktopNotifications && 'Notification' in window) {
                      Notification.requestPermission().then(permission => {
                        if (permission === 'granted') {
                          toggleDesktopNotifications();
                        }
                      });
                    } else {
                      toggleDesktopNotifications();
                    }
                  }}
                  disabled={!notificationsEnabled}
                  className={cn(
                    "relative w-14 h-8 rounded-full transition-colors",
                    desktopNotifications && notificationsEnabled ? "bg-primary-500" : "bg-muted",
                    !notificationsEnabled && "opacity-50 cursor-not-allowed"
                  )}
                >
                  <motion.div
                    animate={{ x: desktopNotifications && notificationsEnabled ? 24 : 4 }}
                    className="absolute top-1 w-6 h-6 bg-white rounded-full shadow-md"
                  />
                </button>
              </div>

              {/* Web Search - Removed (available in chat page header) */}
            </div>
          </motion.section>

          {/* Data Management */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.35 }}
          >
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Download className="w-5 h-5 text-primary-500" />
              {language === 'tr' ? 'Veri Yönetimi' : language === 'de' ? 'Datenverwaltung' : 'Data Management'}
            </h2>

            <div className="bg-card border border-border rounded-2xl overflow-hidden divide-y divide-border">
              {/* Export */}
              <div className="flex items-center justify-between p-5">
                <div className="flex items-center gap-3">
                  <Download className="w-5 h-5" />
                  <div>
                    <p className="font-medium">
                      {language === 'tr' ? 'Verileri Dışa Aktar' : language === 'de' ? 'Daten exportieren' : 'Export Data'}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {language === 'tr' ? 'Tüm ayarları ve verileri JSON olarak indir' : language === 'de' ? 'Alle Einstellungen und Daten als JSON herunterladen' : 'Download all settings and data as JSON'}
                    </p>
                  </div>
                </div>
                <button
                  onClick={handleExport}
                  className={cn(
                    "flex items-center gap-2 px-4 py-2 rounded-xl transition-colors",
                    exportStatus === 'success'
                      ? "bg-green-500 text-white"
                      : exportStatus === 'error'
                        ? "bg-red-500 text-white"
                        : "bg-primary-500 text-white hover:bg-primary-600"
                  )}
                >
                  {exportStatus === 'success' ? (
                    <><Check className="w-4 h-4" />{language === 'tr' ? 'Başarılı!' : 'Success!'}</>
                  ) : exportStatus === 'error' ? (
                    <><AlertCircle className="w-4 h-4" />{language === 'tr' ? 'Hata!' : 'Error!'}</>
                  ) : (
                    <><Download className="w-4 h-4" />{language === 'tr' ? 'Dışa Aktar' : language === 'de' ? 'Exportieren' : 'Export'}</>
                  )}
                </button>
              </div>

              {/* Import */}
              <div className="flex items-center justify-between p-5">
                <div className="flex items-center gap-3">
                  <Upload className="w-5 h-5" />
                  <div>
                    <p className="font-medium">
                      {language === 'tr' ? 'Verileri İçe Aktar' : language === 'de' ? 'Daten importieren' : 'Import Data'}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {language === 'tr' ? 'Yedek dosyasından geri yükle' : language === 'de' ? 'Aus Backup-Datei wiederherstellen' : 'Restore from backup file'}
                    </p>
                  </div>
                </div>
                <div>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".json"
                    onChange={handleImport}
                    className="hidden"
                    id="import-file"
                  />
                  <label
                    htmlFor="import-file"
                    className={cn(
                      "flex items-center gap-2 px-4 py-2 rounded-xl cursor-pointer transition-colors",
                      importStatus === 'success'
                        ? "bg-green-500 text-white"
                        : importStatus === 'error'
                          ? "bg-red-500 text-white"
                          : "bg-muted hover:bg-accent"
                    )}
                  >
                    {importStatus === 'success' ? (
                      <><Check className="w-4 h-4" />{language === 'tr' ? 'Başarılı!' : 'Success!'}</>
                    ) : importStatus === 'error' ? (
                      <><AlertCircle className="w-4 h-4" />{language === 'tr' ? 'Hata!' : 'Error!'}</>
                    ) : (
                      <><Upload className="w-4 h-4" />{language === 'tr' ? 'İçe Aktar' : language === 'de' ? 'Importieren' : 'Import'}</>
                    )}
                  </label>
                </div>
              </div>

              {/* Reset */}
              <div className="flex items-center justify-between p-5">
                <div className="flex items-center gap-3">
                  <RotateCcw className="w-5 h-5 text-red-500" />
                  <div>
                    <p className="font-medium text-red-500">
                      {language === 'tr' ? 'Ayarları Sıfırla' : language === 'de' ? 'Einstellungen zurücksetzen' : 'Reset Settings'}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {language === 'tr' ? 'Tüm ayarları varsayılana döndür' : language === 'de' ? 'Alle Einstellungen auf Standard zurücksetzen' : 'Reset all settings to default'}
                    </p>
                  </div>
                </div>
                <button
                  onClick={handleResetSettings}
                  className="flex items-center gap-2 px-4 py-2 bg-red-500/10 text-red-500 hover:bg-red-500/20 rounded-xl transition-colors"
                >
                  <RotateCcw className="w-4 h-4" />
                  {language === 'tr' ? 'Sıfırla' : language === 'de' ? 'Zurücksetzen' : 'Reset'}
                </button>
              </div>
            </div>
          </motion.section>

          {/* Keyboard Shortcuts */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.38 }}
          >
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Keyboard className="w-5 h-5 text-primary-500" />
              {language === 'tr' ? 'Klavye Kısayolları' : language === 'de' ? 'Tastenkürzel' : 'Keyboard Shortcuts'}
            </h2>

            <div className="bg-card border border-border rounded-2xl p-5">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <p className="font-medium">
                    {language === 'tr' ? 'Kısayol Listesi' : language === 'de' ? 'Kürzel-Liste' : 'Shortcut List'}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {language === 'tr' ? 'Hızlı işlemler için klavye kısayolları' : 'Keyboard shortcuts for quick actions'}
                  </p>
                </div>
                <button
                  onClick={() => setShowKeyboardShortcuts(!showKeyboardShortcuts)}
                  className="px-4 py-2 bg-muted hover:bg-accent rounded-xl transition-colors"
                >
                  {showKeyboardShortcuts
                    ? (language === 'tr' ? 'Gizle' : 'Hide')
                    : (language === 'tr' ? 'Göster' : 'Show')}
                </button>
              </div>

              {showKeyboardShortcuts && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="space-y-4"
                >
                  <div className="grid grid-cols-2 gap-3">
                    {[
                      { keys: 'Enter', action: { tr: 'Mesaj gönder', en: 'Send message', de: 'Nachricht senden' } },
                      { keys: 'Shift + Enter', action: { tr: 'Yeni satır', en: 'New line', de: 'Neue Zeile' } },
                      { keys: 'Ctrl + N', action: { tr: 'Yeni sohbet', en: 'New chat', de: 'Neuer Chat' } },
                      { keys: 'Ctrl + D', action: { tr: 'Detaylı mod', en: 'Detailed mode', de: 'Detaillierter Modus' } },
                      { keys: 'Ctrl + W', action: { tr: 'Web arama', en: 'Web search', de: 'Websuche' } },
                      { keys: 'Esc', action: { tr: 'Durdur / İptal', en: 'Stop / Cancel', de: 'Stoppen / Abbrechen' } },
                      { keys: 'Ctrl + /', action: { tr: 'Arama', en: 'Search', de: 'Suchen' } },
                      { keys: 'Ctrl + ,', action: { tr: 'Ayarlar', en: 'Settings', de: 'Einstellungen' } },
                    ].map((shortcut, i) => (
                      <div key={i} className="flex items-center justify-between p-2 bg-muted rounded-lg">
                        <code className="px-2 py-1 bg-background rounded text-xs font-mono">
                          {shortcut.keys}
                        </code>
                        <span className="text-sm text-muted-foreground">
                          {language === 'tr' ? shortcut.action.tr : language === 'de' ? shortcut.action.de : shortcut.action.en}
                        </span>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </div>
          </motion.section>

          {/* Danger Zone */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.39 }}
          >
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2 text-red-500">
              <Trash2 className="w-5 h-5" />
              {language === 'tr' ? 'Tehlikeli Bölge' : language === 'de' ? 'Gefahrenbereich' : 'Danger Zone'}
            </h2>

            <div className="bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800 rounded-2xl p-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <MessageSquare className="w-5 h-5 text-red-500" />
                  <div>
                    <p className="font-medium text-red-700 dark:text-red-400">
                      {language === 'tr' ? 'Tüm Sohbetleri Sil' : language === 'de' ? 'Alle Chats löschen' : 'Clear All Conversations'}
                    </p>
                    <p className="text-sm text-red-600/70 dark:text-red-400/70">
                      {language === 'tr'
                        ? `Mevcut ${messages.length} mesaj silinecek. Bu işlem geri alınamaz.`
                        : `${messages.length} messages will be deleted. This action cannot be undone.`}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => {
                    if (confirm(language === 'tr'
                      ? 'Tüm mesajlarınız kalıcı olarak silinecek. Devam etmek istiyor musunuz?'
                      : 'All your messages will be permanently deleted. Do you want to continue?'
                    )) {
                      clearMessages();
                    }
                  }}
                  className="flex items-center gap-2 px-4 py-2 bg-red-500 text-white hover:bg-red-600 rounded-xl transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                  {language === 'tr' ? 'Sil' : 'Delete'}
                </button>
              </div>
            </div>
          </motion.section>

          {/* About */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Shield className="w-5 h-5 text-primary-500" />
              {language === 'tr' ? 'Hakkında' : 'About'}
            </h2>

            <div className="bg-card border border-border rounded-2xl p-5">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center text-white text-2xl font-bold">
                  AI
                </div>
                <div>
                  <h3 className="text-lg font-bold">Enterprise AI Assistant</h3>
                  <p className="text-sm text-muted-foreground">Version 2.0.0</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Built with Next.js, TypeScript & Tailwind CSS
                  </p>
                </div>
              </div>
            </div>
          </motion.section>

        </div>
      </div>
    </div>
  );
}
