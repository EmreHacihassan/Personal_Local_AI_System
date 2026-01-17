'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  History, 
  MessageSquare, 
  Trash2, 
  Search,
  Calendar,
  Clock,
  ChevronRight
} from 'lucide-react';
import { useStore, Session } from '@/store/useStore';
import { getSessions, deleteSession } from '@/lib/api';
import { formatDate } from '@/lib/utils';

interface SessionResponse {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export function HistoryPage() {
  const { setCurrentPage, language } = useStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [localSessions, setLocalSessions] = useState<Session[]>([]);

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    setLoading(true);
    const response = await getSessions();
    if (response.success && response.data) {
      setLocalSessions(response.data.sessions.map((s: SessionResponse) => ({
        id: s.id,
        title: s.title,
        messages: [],
        createdAt: new Date(s.created_at),
        updatedAt: new Date(s.updated_at),
      })));
    }
    setLoading(false);
  };

  const handleDelete = async (sessionId: string) => {
    const response = await deleteSession(sessionId);
    if (response.success) {
      setLocalSessions(prev => prev.filter(s => s.id !== sessionId));
    }
  };

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const handleOpenSession = (sessionId: string) => {
    // TODO: Navigate to chat with this session
    // In the future, implement session loading here with sessionId
    setCurrentPage('chat');
  };

  const filteredSessions = localSessions.filter(session =>
    session.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Group sessions by date
  const groupedSessions = filteredSessions.reduce((groups, session) => {
    const date = new Date(session.createdAt).toLocaleDateString('tr-TR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
    if (!groups[date]) {
      groups[date] = [];
    }
    groups[date].push(session);
    return groups;
  }, {} as Record<string, Session[]>);

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-border bg-card/50 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 text-white">
            <History className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-semibold">
              {language === 'tr' ? 'Sohbet Geçmişi' : 'Chat History'}
            </h1>
            <p className="text-xs text-muted-foreground">
              {language === 'tr' 
                ? `${localSessions.length} sohbet kaydedildi`
                : `${localSessions.length} conversations saved`
              }
            </p>
          </div>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={language === 'tr' ? 'Geçmişte ara...' : 'Search history...'}
            className="pl-10 pr-4 py-2 w-64 bg-background border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
          />
        </div>
      </header>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-3xl mx-auto space-y-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary-500 border-t-transparent" />
            </div>
          ) : Object.keys(groupedSessions).length === 0 ? (
            <div className="text-center py-12">
              <History className="w-16 h-16 mx-auto text-muted-foreground/50 mb-4" />
              <p className="text-lg font-medium text-muted-foreground">
                {language === 'tr' ? 'Henüz sohbet yok' : 'No conversations yet'}
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                {language === 'tr' 
                  ? 'Sohbetleriniz burada görünecek'
                  : 'Your conversations will appear here'
                }
              </p>
            </div>
          ) : (
            Object.entries(groupedSessions).map(([date, sessions]) => (
              <div key={date}>
                <div className="flex items-center gap-2 mb-3">
                  <Calendar className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm font-medium text-muted-foreground">{date}</span>
                </div>

                <div className="space-y-2">
                  {sessions.map((session, index) => (
                    <motion.div
                      key={session.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="group flex items-center gap-4 p-4 bg-card border border-border rounded-xl hover:border-primary-500/30 hover:shadow-lg transition-all cursor-pointer"
                      onClick={() => handleOpenSession(session.id)}
                    >
                      {/* Icon */}
                      <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-muted">
                        <MessageSquare className="w-5 h-5 text-muted-foreground" />
                      </div>

                      {/* Info */}
                      <div className="flex-1 min-w-0">
                        <p className="font-medium truncate">{session.title}</p>
                        <div className="flex items-center gap-2 text-xs text-muted-foreground mt-1">
                          <Clock className="w-3 h-3" />
                          <span>{formatDate(session.updatedAt)}</span>
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex items-center gap-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(session.id);
                          }}
                          className="p-2 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-red-500/10 text-red-500 transition-all"
                          title="Sil"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                        <ChevronRight className="w-5 h-5 text-muted-foreground group-hover:text-foreground transition-colors" />
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
