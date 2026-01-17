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
  Wifi,
  Check
} from 'lucide-react';
import { useStore, Theme } from '@/store/useStore';
import { cn } from '@/lib/utils';

const themes: { id: Theme; name: string; nameEn: string; icon: React.ElementType; gradient: string }[] = [
  { id: 'light', name: 'Açık Tema', nameEn: 'Light', icon: Sun, gradient: 'from-amber-400 to-orange-500' },
  { id: 'dark', name: 'Koyu Tema', nameEn: 'Dark', icon: Moon, gradient: 'from-slate-600 to-slate-800' },
  { id: 'ocean', name: 'Okyanus', nameEn: 'Ocean', icon: Globe, gradient: 'from-blue-400 to-cyan-500' },
  { id: 'forest', name: 'Orman', nameEn: 'Forest', icon: Globe, gradient: 'from-emerald-400 to-green-600' },
  { id: 'sunset', name: 'Gün Batımı', nameEn: 'Sunset', icon: Sun, gradient: 'from-orange-400 to-pink-500' },
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
    webSearchEnabled,
    toggleWebSearch,
    widgetEnabled,
    toggleWidget,
  } = useStore();

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
                  {language === 'tr' ? 'Tema' : 'Theme'}
                </label>
                <div className="grid grid-cols-5 gap-3">
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
                        {language === 'tr' ? t.name : t.nameEn}
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
                  <p className="font-medium">{language === 'tr' ? 'Dil' : 'Language'}</p>
                  <p className="text-sm text-muted-foreground">
                    {language === 'tr' ? 'Arayüz dilini seçin' : 'Select interface language'}
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
              {language === 'tr' ? 'Bildirimler' : 'Notifications'}
            </h2>
            
            <div className="bg-card border border-border rounded-2xl divide-y divide-border">
              {/* Sound */}
              <div className="flex items-center justify-between p-5">
                <div className="flex items-center gap-3">
                  {soundEnabled ? <Volume2 className="w-5 h-5" /> : <VolumeX className="w-5 h-5" />}
                  <div>
                    <p className="font-medium">{language === 'tr' ? 'Sesler' : 'Sounds'}</p>
                    <p className="text-sm text-muted-foreground">
                      {language === 'tr' ? 'Bildirim sesleri' : 'Notification sounds'}
                    </p>
                  </div>
                </div>
                <button
                  onClick={toggleSound}
                  className={cn(
                    "relative w-14 h-8 rounded-full transition-colors",
                    soundEnabled ? "bg-primary-500" : "bg-muted"
                  )}
                >
                  <motion.div
                    animate={{ x: soundEnabled ? 24 : 4 }}
                    className="absolute top-1 w-6 h-6 bg-white rounded-full shadow-md"
                  />
                </button>
              </div>

              {/* Web Search Default */}
              <div className="flex items-center justify-between p-5">
                <div className="flex items-center gap-3">
                  <Wifi className="w-5 h-5" />
                  <div>
                    <p className="font-medium">{language === 'tr' ? 'Web Arama' : 'Web Search'}</p>
                    <p className="text-sm text-muted-foreground">
                      {language === 'tr' ? 'Varsayılan olarak aktif' : 'Enabled by default'}
                    </p>
                  </div>
                </div>
                <button
                  onClick={toggleWebSearch}
                  className={cn(
                    "relative w-14 h-8 rounded-full transition-colors",
                    webSearchEnabled ? "bg-primary-500" : "bg-muted"
                  )}
                >
                  <motion.div
                    animate={{ x: webSearchEnabled ? 24 : 4 }}
                    className="absolute top-1 w-6 h-6 bg-white rounded-full shadow-md"
                  />
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
