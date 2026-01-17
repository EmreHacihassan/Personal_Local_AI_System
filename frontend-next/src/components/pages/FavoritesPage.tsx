'use client';

import { motion } from 'framer-motion';
import { Star, Copy, Trash2, Search, Calendar } from 'lucide-react';
import { useStore } from '@/store/useStore';
import { cn } from '@/lib/utils';
import { useState, useMemo } from 'react';

export function FavoritesPage() {
  const { language, messages, toggleMessageFavorite } = useStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [filterRole, setFilterRole] = useState<'all' | 'user' | 'assistant'>('all');

  const favoriteMessages = useMemo(() => {
    return messages
      .filter((m) => m.isFavorite)
      .filter((m) => filterRole === 'all' || m.role === filterRole)
      .filter((m) => 
        searchQuery === '' || 
        m.content.toLowerCase().includes(searchQuery.toLowerCase())
      );
  }, [messages, searchQuery, filterRole]);

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const t = {
    title: { tr: 'Favoriler', en: 'Favorites', de: 'Favoriten' },
    subtitle: { tr: 'Kaydettiğiniz mesajlar', en: 'Your saved messages', de: 'Ihre gespeicherten Nachrichten' },
    search: { tr: 'Favorilerde ara...', en: 'Search favorites...', de: 'Favoriten durchsuchen...' },
    all: { tr: 'Tümü', en: 'All', de: 'Alle' },
    myMessages: { tr: 'Sorularım', en: 'My Messages', de: 'Meine Nachrichten' },
    aiResponses: { tr: 'AI Yanıtları', en: 'AI Responses', de: 'AI-Antworten' },
    noFavorites: { tr: 'Henüz favori mesaj yok', en: 'No favorite messages yet', de: 'Noch keine Favoriten' },
    noFavoritesHint: { 
      tr: 'Sohbette mesajlara ⭐ tıklayarak favorilere ekleyebilirsiniz.', 
      en: 'Click ⭐ on messages in chat to add to favorites.', 
      de: 'Klicken Sie auf ⭐ in Nachrichten, um sie zu Favoriten hinzuzufügen.' 
    },
    copy: { tr: 'Kopyala', en: 'Copy', de: 'Kopieren' },
    remove: { tr: 'Favorilerden çıkar', en: 'Remove from favorites', de: 'Aus Favoriten entfernen' },
    you: { tr: 'Siz', en: 'You', de: 'Sie' },
    ai: { tr: 'AI Asistan', en: 'AI Assistant', de: 'KI-Assistent' },
    total: { tr: 'Toplam', en: 'Total', de: 'Gesamt' },
    favorites: { tr: 'favori', en: 'favorites', de: 'Favoriten' },
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-border bg-card/50 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-yellow-400 to-orange-500 text-white">
            <Star className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-semibold">{t.title[language]}</h1>
            <p className="text-xs text-muted-foreground">{t.subtitle[language]}</p>
          </div>
        </div>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Star className="w-4 h-4 text-yellow-500" />
          <span>{t.total[language]}: {favoriteMessages.length} {t.favorites[language]}</span>
        </div>
      </header>

      {/* Search and Filter */}
      <div className="px-6 py-4 border-b border-border bg-muted/30">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              type="text"
              placeholder={t.search[language]}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-background border border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          {/* Filter */}
          <div className="flex gap-2">
            <button
              onClick={() => setFilterRole('all')}
              className={cn(
                "px-4 py-2 rounded-xl text-sm transition-all",
                filterRole === 'all' 
                  ? "bg-primary-500 text-white" 
                  : "bg-background border border-border hover:bg-accent"
              )}
            >
              {t.all[language]}
            </button>
            <button
              onClick={() => setFilterRole('user')}
              className={cn(
                "px-4 py-2 rounded-xl text-sm transition-all",
                filterRole === 'user' 
                  ? "bg-primary-500 text-white" 
                  : "bg-background border border-border hover:bg-accent"
              )}
            >
              {t.myMessages[language]}
            </button>
            <button
              onClick={() => setFilterRole('assistant')}
              className={cn(
                "px-4 py-2 rounded-xl text-sm transition-all",
                filterRole === 'assistant' 
                  ? "bg-primary-500 text-white" 
                  : "bg-background border border-border hover:bg-accent"
              )}
            >
              {t.aiResponses[language]}
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {favoriteMessages.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col items-center justify-center h-full text-center"
          >
            <div className="w-20 h-20 rounded-full bg-yellow-100 dark:bg-yellow-900/20 flex items-center justify-center mb-4">
              <Star className="w-10 h-10 text-yellow-500" />
            </div>
            <h3 className="text-lg font-semibold mb-2">{t.noFavorites[language]}</h3>
            <p className="text-sm text-muted-foreground max-w-md">
              {t.noFavoritesHint[language]}
            </p>
          </motion.div>
        ) : (
          <div className="max-w-3xl mx-auto space-y-4">
            {favoriteMessages.map((message, index) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className={cn(
                  "bg-card border border-border rounded-2xl p-4 hover:shadow-md transition-shadow",
                  message.role === 'assistant' && "border-l-4 border-l-primary-500"
                )}
              >
                {/* Header */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <div className={cn(
                      "w-8 h-8 rounded-full flex items-center justify-center text-white text-sm",
                      message.role === 'user' 
                        ? "bg-gradient-to-br from-blue-500 to-purple-500" 
                        : "bg-gradient-to-br from-primary-500 to-primary-700"
                    )}>
                      {message.role === 'user' ? '👤' : '🤖'}
                    </div>
                    <span className="font-medium text-sm">
                      {message.role === 'user' ? t.you[language] : t.ai[language]}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      <Calendar className="w-3 h-3 inline mr-1" />
                      {new Date(message.timestamp).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => copyToClipboard(message.content)}
                      className="p-2 hover:bg-accent rounded-lg transition-colors"
                      title={t.copy[language]}
                    >
                      <Copy className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => toggleMessageFavorite(message.id)}
                      className="p-2 hover:bg-red-100 dark:hover:bg-red-900/20 rounded-lg transition-colors text-red-500"
                      title={t.remove[language]}
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Content */}
                <div className="text-sm leading-relaxed">
                  {message.content.length > 500 
                    ? message.content.slice(0, 500) + '...' 
                    : message.content
                  }
                </div>

                {/* Sources */}
                {message.sources && message.sources.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-border">
                    <p className="text-xs text-muted-foreground mb-2">
                      📚 {language === 'tr' ? 'Kaynaklar' : language === 'de' ? 'Quellen' : 'Sources'}:
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {message.sources.slice(0, 3).map((source, i) => (
                        <span key={i} className="text-xs bg-muted px-2 py-1 rounded-full">
                          {source.title}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
