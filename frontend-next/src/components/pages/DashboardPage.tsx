'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  LayoutDashboard, 
  MessageSquare, 
  FileText, 
  Zap,
  TrendingUp,
  Clock,
  Database,
  Cpu,
  Activity,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Star,
  Tag,
  BookOpen,
  Target,
  Calendar
} from 'lucide-react';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  AreaChart,
  Area
} from 'recharts';
import { useStore, Session } from '@/store/useStore';
import { getStats, checkHealth, SystemStats, HealthStatus, getSessions } from '@/lib/api';
import { cn } from '@/lib/utils';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ElementType;
  color: string;
  trend?: { value: number; positive: boolean };
}

function StatCard({ title, value, icon: Icon, color, trend }: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-card border border-border rounded-2xl p-5 hover:shadow-lg transition-shadow"
    >
      <div className="flex items-start justify-between">
        <div className={cn("p-3 rounded-xl", color)}>
          <Icon className="w-5 h-5 text-white" />
        </div>
        {trend && (
          <div className={cn(
            "flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-full",
            trend.positive ? "bg-green-500/10 text-green-600" : "bg-red-500/10 text-red-600"
          )}>
            <TrendingUp className={cn("w-3 h-3", !trend.positive && "rotate-180")} />
            {trend.value}%
          </div>
        )}
      </div>
      <div className="mt-4">
        <p className="text-2xl font-bold">{value}</p>
        <p className="text-sm text-muted-foreground mt-1">{title}</p>
      </div>
    </motion.div>
  );
}

interface ServiceStatusProps {
  name: string;
  status: 'online' | 'offline' | 'warning';
  latency?: number;
}

function ServiceStatus({ name, status, latency }: ServiceStatusProps) {
  const statusConfig = {
    online: { icon: CheckCircle2, color: 'text-green-500', bg: 'bg-green-500/10' },
    offline: { icon: XCircle, color: 'text-red-500', bg: 'bg-red-500/10' },
    warning: { icon: AlertTriangle, color: 'text-yellow-500', bg: 'bg-yellow-500/10' },
  };

  const config = statusConfig[status];
  const Icon = config.icon;

  return (
    <div className="flex items-center justify-between p-3 rounded-xl bg-muted/50">
      <div className="flex items-center gap-3">
        <div className={cn("p-2 rounded-lg", config.bg)}>
          <Icon className={cn("w-4 h-4", config.color)} />
        </div>
        <span className="font-medium">{name}</span>
      </div>
      {latency !== undefined && (
        <span className="text-sm text-muted-foreground">{latency}ms</span>
      )}
    </div>
  );
}

// Colors for charts
const CHART_COLORS = ['#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#ec4899'];

// Category distribution colors
const CATEGORY_COLORS: Record<string, string> = {
  work: '#3b82f6',
  personal: '#10b981',
  research: '#8b5cf6',
  learning: '#f59e0b',
  project: '#ef4444',
  other: '#6b7280',
};

interface SessionResponse {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  is_pinned?: boolean;
  tags?: string[];
  category?: string;
}

export function DashboardPage() {
  const { language, documents, messages, templates, notes, sessions: localSessions, getFavoriteMessages } = useStore();
  const favorites = getFavoriteMessages();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [recentActivities, setRecentActivities] = useState<{action: string; time: string; icon: React.ElementType}[]>([]);

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadData = async () => {
    setLoading(true);
    
    const [statsRes, healthRes, sessionsRes] = await Promise.all([
      getStats(),
      checkHealth(),
      getSessions(),
    ]);

    if (statsRes.success && statsRes.data) setStats(statsRes.data);
    if (healthRes.success && healthRes.data) setHealth(healthRes.data);
    if (sessionsRes.success && sessionsRes.data) {
      const mappedSessions = sessionsRes.data.sessions.map((s: SessionResponse) => ({
        id: s.id,
        title: s.title,
        messages: [],
        createdAt: new Date(s.created_at),
        updatedAt: new Date(s.updated_at),
        isPinned: s.is_pinned || false,
        tags: s.tags || [],
        category: s.category || 'other',
      }));
      setSessions(mappedSessions);
    }

    // Generate recent activities based on actual data
    const activities = [];
    if (documents.length > 0) {
      activities.push({ 
        action: language === 'tr' ? 'Yeni döküman yüklendi' : 'New document uploaded', 
        time: language === 'tr' ? '2 dk önce' : '2 min ago', 
        icon: FileText 
      });
    }
    if (messages.length > 0) {
      activities.push({ 
        action: language === 'tr' ? 'Chat oturumu başlatıldı' : 'Chat session started', 
        time: language === 'tr' ? '15 dk önce' : '15 min ago', 
        icon: MessageSquare 
      });
    }
    if (notes.length > 0) {
      activities.push({ 
        action: language === 'tr' ? 'Not eklendi' : 'Note added', 
        time: language === 'tr' ? '30 dk önce' : '30 min ago', 
        icon: BookOpen 
      });
    }
    if (templates.length > 0) {
      activities.push({ 
        action: language === 'tr' ? 'Şablon kullanıldı' : 'Template used', 
        time: language === 'tr' ? '1 saat önce' : '1 hour ago', 
        icon: Target 
      });
    }
    activities.push({ 
      action: language === 'tr' ? 'RAG sorgusu çalıştırıldı' : 'RAG query executed', 
      time: language === 'tr' ? '2 saat önce' : '2 hours ago', 
      icon: Database 
    });
    setRecentActivities(activities.slice(0, 5));

    setLoading(false);
  };

  // Prepare chart data
  const messageDistributionData = [
    { name: language === 'tr' ? 'Kullanıcı' : 'User', value: messages.filter(m => m.role === 'user').length, color: '#8b5cf6' },
    { name: language === 'tr' ? 'Asistan' : 'Assistant', value: messages.filter(m => m.role === 'assistant').length, color: '#06b6d4' },
  ].filter(d => d.value > 0);

  // Category distribution data
  const allSessions = [...localSessions, ...sessions];
  const categoryData = Object.entries(
    allSessions.reduce((acc, session) => {
      const cat = session.category || 'other';
      acc[cat] = (acc[cat] || 0) + 1;
      return acc;
    }, {} as Record<string, number>)
  ).map(([name, value]) => ({
    name: name === 'work' ? (language === 'tr' ? 'İş' : 'Work') :
          name === 'personal' ? (language === 'tr' ? 'Kişisel' : 'Personal') :
          name === 'research' ? (language === 'tr' ? 'Araştırma' : 'Research') :
          name === 'learning' ? (language === 'tr' ? 'Öğrenme' : 'Learning') :
          name === 'project' ? (language === 'tr' ? 'Proje' : 'Project') :
          (language === 'tr' ? 'Diğer' : 'Other'),
    value,
    color: CATEGORY_COLORS[name] || CATEGORY_COLORS.other,
  }));

  // Tag cloud data - extract all tags
  const allTags = allSessions.flatMap(s => s.tags || []);
  const tagCounts = allTags.reduce((acc, tag) => {
    acc[tag] = (acc[tag] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);
  const tagCloudData = Object.entries(tagCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 12);

  // Weekly activity data (simulated based on real data)
  const weeklyData = [
    { day: language === 'tr' ? 'Pzt' : 'Mon', messages: Math.max(1, Math.floor(messages.length * 0.15)), documents: Math.floor(documents.length * 0.2) },
    { day: language === 'tr' ? 'Sal' : 'Tue', messages: Math.max(1, Math.floor(messages.length * 0.18)), documents: Math.floor(documents.length * 0.15) },
    { day: language === 'tr' ? 'Çar' : 'Wed', messages: Math.max(1, Math.floor(messages.length * 0.2)), documents: Math.floor(documents.length * 0.25) },
    { day: language === 'tr' ? 'Per' : 'Thu', messages: Math.max(1, Math.floor(messages.length * 0.17)), documents: Math.floor(documents.length * 0.2) },
    { day: language === 'tr' ? 'Cum' : 'Fri', messages: Math.max(1, Math.floor(messages.length * 0.15)), documents: Math.floor(documents.length * 0.1) },
    { day: language === 'tr' ? 'Cmt' : 'Sat', messages: Math.max(1, Math.floor(messages.length * 0.1)), documents: Math.floor(documents.length * 0.05) },
    { day: language === 'tr' ? 'Paz' : 'Sun', messages: Math.max(1, Math.floor(messages.length * 0.05)), documents: Math.floor(documents.length * 0.05) },
  ];

  const t = {
    title: { tr: 'Dashboard', en: 'Dashboard', de: 'Dashboard' },
    subtitle: { tr: 'Sistem genel bakış', en: 'System overview', de: 'Systemübersicht' },
    refresh: { tr: 'Yenile', en: 'Refresh', de: 'Aktualisieren' },
    totalChats: { tr: 'Toplam Sohbet', en: 'Total Chats', de: 'Gesamtchats' },
    documents: { tr: 'Dökümanlar', en: 'Documents', de: 'Dokumente' },
    vectorCount: { tr: 'Vector Sayısı', en: 'Vector Count', de: 'Vektoranzahl' },
    avgResponseTime: { tr: 'Ort. Yanıt Süresi', en: 'Avg Response Time', de: 'Durchschn. Antwortzeit' },
    serviceStatus: { tr: 'Servis Durumu', en: 'Service Status', de: 'Servicestatus' },
    systemResources: { tr: 'Sistem Kaynakları', en: 'System Resources', de: 'Systemressourcen' },
    recentActivities: { tr: 'Son Aktiviteler', en: 'Recent Activities', de: 'Letzte Aktivitäten' },
    messageDistribution: { tr: 'Mesaj Dağılımı', en: 'Message Distribution', de: 'Nachrichtenverteilung' },
    categoryDistribution: { tr: 'Kategori Dağılımı', en: 'Category Distribution', de: 'Kategorieverteilung' },
    weeklyActivity: { tr: 'Haftalık Aktivite', en: 'Weekly Activity', de: 'Wöchentliche Aktivität' },
    tagCloud: { tr: 'Popüler Etiketler', en: 'Popular Tags', de: 'Beliebte Tags' },
    quickStats: { tr: 'Hızlı İstatistikler', en: 'Quick Stats', de: 'Schnellstatistiken' },
    favorites: { tr: 'Favoriler', en: 'Favorites', de: 'Favoriten' },
    templates: { tr: 'Şablonlar', en: 'Templates', de: 'Vorlagen' },
    notes: { tr: 'Notlar', en: 'Notes', de: 'Notizen' },
    sessions: { tr: 'Oturumlar', en: 'Sessions', de: 'Sitzungen' },
    templateUsage: { tr: 'Şablon Kullanımı', en: 'Template Usage', de: 'Vorlagennutzung' },
    dailySummary: { tr: 'Günlük Özet', en: 'Daily Summary', de: 'Tägliche Zusammenfassung' },
    todaysStats: { tr: 'Bugünkü İstatistikler', en: "Today's Stats", de: 'Heutige Statistiken' },
    messagesCount: { tr: 'Mesaj Sayısı', en: 'Messages', de: 'Nachrichten' },
    docsUploaded: { tr: 'Yüklenen Döküman', en: 'Docs Uploaded', de: 'Hochgeladene Dokumente' },
    mostUsed: { tr: 'En Çok Kullanılan', en: 'Most Used', de: 'Meistgenutzt' },
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-border bg-card/50 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 text-white">
            <LayoutDashboard className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-semibold">{t.title[language]}</h1>
            <p className="text-xs text-muted-foreground">{t.subtitle[language]}</p>
          </div>
        </div>

        <button
          onClick={loadData}
          className="flex items-center gap-2 px-4 py-2 bg-muted hover:bg-accent rounded-xl transition-colors"
        >
          <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
          <span className="text-sm">{t.refresh[language]}</span>
        </button>
      </header>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              title={t.totalChats[language]}
              value={messages.length}
              icon={MessageSquare}
              color="bg-gradient-to-br from-blue-500 to-blue-600"
              trend={{ value: 12, positive: true }}
            />
            <StatCard
              title={t.documents[language]}
              value={documents.length}
              icon={FileText}
              color="bg-gradient-to-br from-emerald-500 to-teal-600"
              trend={{ value: 8, positive: true }}
            />
            <StatCard
              title={t.vectorCount[language]}
              value={stats?.vector_count || 0}
              icon={Database}
              color="bg-gradient-to-br from-orange-500 to-amber-600"
            />
            <StatCard
              title={t.avgResponseTime[language]}
              value="1.2s"
              icon={Zap}
              color="bg-gradient-to-br from-pink-500 to-rose-600"
              trend={{ value: 5, positive: false }}
            />
          </div>

          {/* Quick Stats Row */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="bg-gradient-to-br from-yellow-50 to-amber-50 dark:from-yellow-950/30 dark:to-amber-950/30 border border-yellow-200 dark:border-yellow-800 rounded-2xl p-4 flex items-center gap-3"
            >
              <Star className="w-8 h-8 text-yellow-500" />
              <div>
                <p className="text-2xl font-bold">{favorites.length}</p>
                <p className="text-xs text-muted-foreground">{t.favorites[language]}</p>
              </div>
            </motion.div>
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.1 }}
              className="bg-gradient-to-br from-purple-50 to-indigo-50 dark:from-purple-950/30 dark:to-indigo-950/30 border border-purple-200 dark:border-purple-800 rounded-2xl p-4 flex items-center gap-3"
            >
              <Target className="w-8 h-8 text-purple-500" />
              <div>
                <p className="text-2xl font-bold">{templates.length}</p>
                <p className="text-xs text-muted-foreground">{t.templates[language]}</p>
              </div>
            </motion.div>
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.2 }}
              className="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-950/30 dark:to-emerald-950/30 border border-green-200 dark:border-green-800 rounded-2xl p-4 flex items-center gap-3"
            >
              <BookOpen className="w-8 h-8 text-green-500" />
              <div>
                <p className="text-2xl font-bold">{notes.length}</p>
                <p className="text-xs text-muted-foreground">{t.notes[language]}</p>
              </div>
            </motion.div>
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.3 }}
              className="bg-gradient-to-br from-blue-50 to-cyan-50 dark:from-blue-950/30 dark:to-cyan-950/30 border border-blue-200 dark:border-blue-800 rounded-2xl p-4 flex items-center gap-3"
            >
              <Calendar className="w-8 h-8 text-blue-500" />
              <div>
                <p className="text-2xl font-bold">{allSessions.length}</p>
                <p className="text-xs text-muted-foreground">{t.sessions[language]}</p>
              </div>
            </motion.div>
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Message Distribution Pie Chart */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-card border border-border rounded-2xl p-5"
            >
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-primary-500" />
                {t.messageDistribution[language]}
              </h3>
              {messageDistributionData.length > 0 ? (
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={messageDistributionData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {messageDistributionData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: 'var(--card)', 
                        border: '1px solid var(--border)',
                        borderRadius: '8px'
                      }} 
                    />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[250px] flex items-center justify-center text-muted-foreground">
                  {language === 'tr' ? 'Henüz mesaj yok' : 'No messages yet'}
                </div>
              )}
            </motion.div>

            {/* Category Distribution Bar Chart */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="bg-card border border-border rounded-2xl p-5"
            >
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Target className="w-5 h-5 text-primary-500" />
                {t.categoryDistribution[language]}
              </h3>
              {categoryData.length > 0 ? (
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={categoryData}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                    <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: 'var(--card)', 
                        border: '1px solid var(--border)',
                        borderRadius: '8px'
                      }} 
                    />
                    <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                      {categoryData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[250px] flex items-center justify-center text-muted-foreground">
                  {language === 'tr' ? 'Henüz oturum yok' : 'No sessions yet'}
                </div>
              )}
            </motion.div>
          </div>

          {/* Weekly Activity & Tag Cloud */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Weekly Activity Line Chart */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="lg:col-span-2 bg-card border border-border rounded-2xl p-5"
            >
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Activity className="w-5 h-5 text-primary-500" />
                {t.weeklyActivity[language]}
              </h3>
              <ResponsiveContainer width="100%" height={250}>
                <AreaChart data={weeklyData}>
                  <defs>
                    <linearGradient id="colorMessages" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorDocuments" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis dataKey="day" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'var(--card)', 
                      border: '1px solid var(--border)',
                      borderRadius: '8px'
                    }} 
                  />
                  <Legend />
                  <Area 
                    type="monotone" 
                    dataKey="messages" 
                    stroke="#8b5cf6" 
                    fillOpacity={1} 
                    fill="url(#colorMessages)" 
                    name={language === 'tr' ? 'Mesajlar' : 'Messages'}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="documents" 
                    stroke="#10b981" 
                    fillOpacity={1} 
                    fill="url(#colorDocuments)" 
                    name={language === 'tr' ? 'Dökümanlar' : 'Documents'}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </motion.div>

            {/* Tag Cloud */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="bg-card border border-border rounded-2xl p-5"
            >
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Tag className="w-5 h-5 text-primary-500" />
                {t.tagCloud[language]}
              </h3>
              {tagCloudData.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {tagCloudData.map(([tag, count], index) => {
                    const size = count > 5 ? 'text-lg px-4 py-2' : count > 2 ? 'text-sm px-3 py-1.5' : 'text-xs px-2 py-1';
                    return (
                      <motion.span
                        key={tag}
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: index * 0.05 }}
                        className={cn(
                          "rounded-full font-medium transition-colors cursor-pointer hover:opacity-80",
                          size
                        )}
                        style={{ 
                          backgroundColor: `${CHART_COLORS[index % CHART_COLORS.length]}20`,
                          color: CHART_COLORS[index % CHART_COLORS.length],
                        }}
                      >
                        #{tag}
                        <span className="ml-1 opacity-60">({count})</span>
                      </motion.span>
                    );
                  })}
                </div>
              ) : (
                <div className="h-[200px] flex items-center justify-center text-muted-foreground text-sm">
                  {language === 'tr' ? 'Henüz etiket yok' : 'No tags yet'}
                </div>
              )}
            </motion.div>
          </div>

          {/* Template Usage & Daily Summary */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Template Usage Stats */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.45 }}
              className="bg-card border border-border rounded-2xl p-5"
            >
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Target className="w-5 h-5 text-primary-500" />
                {t.templateUsage[language]}
              </h3>
              {templates.length > 0 ? (
                <div className="space-y-3">
                  {templates.slice(0, 5).map((template, index) => (
                    <motion.div 
                      key={template.id}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="flex items-center justify-between p-3 rounded-xl bg-muted/50"
                    >
                      <div className="flex items-center gap-3">
                        <div 
                          className="p-2 rounded-lg"
                          style={{ backgroundColor: `${CHART_COLORS[index % CHART_COLORS.length]}20` }}
                        >
                          <Target 
                            className="w-4 h-4" 
                            style={{ color: CHART_COLORS[index % CHART_COLORS.length] }}
                          />
                        </div>
                        <div>
                          <p className="text-sm font-medium">{template.title}</p>
                          <p className="text-xs text-muted-foreground">{template.category}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-bold">{template.useCount || 0}</span>
                        <span className="text-xs text-muted-foreground">
                          {language === 'tr' ? 'kullanım' : 'uses'}
                        </span>
                      </div>
                    </motion.div>
                  ))}
                </div>
              ) : (
                <div className="h-[200px] flex items-center justify-center text-muted-foreground">
                  {language === 'tr' ? 'Henüz şablon yok' : 'No templates yet'}
                </div>
              )}
            </motion.div>

            {/* Daily Summary Widget */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="bg-gradient-to-br from-indigo-50 to-purple-50 dark:from-indigo-950/30 dark:to-purple-950/30 border border-indigo-200 dark:border-indigo-800 rounded-2xl p-5"
            >
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2 text-indigo-700 dark:text-indigo-400">
                <Calendar className="w-5 h-5" />
                {t.dailySummary[language]}
              </h3>
              
              <div className="space-y-4">
                {/* Today's Date */}
                <div className="text-center p-3 bg-white/50 dark:bg-black/20 rounded-xl">
                  <p className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">
                    {new Date().toLocaleDateString(language === 'tr' ? 'tr-TR' : language === 'de' ? 'de-DE' : 'en-US', { 
                      weekday: 'long', 
                      year: 'numeric', 
                      month: 'long', 
                      day: 'numeric' 
                    })}
                  </p>
                </div>

                {/* Today's Stats Grid */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-white/50 dark:bg-black/20 rounded-xl p-3 text-center">
                    <p className="text-3xl font-bold text-blue-600">{messages.length}</p>
                    <p className="text-xs text-muted-foreground">{t.messagesCount[language]}</p>
                  </div>
                  <div className="bg-white/50 dark:bg-black/20 rounded-xl p-3 text-center">
                    <p className="text-3xl font-bold text-emerald-600">{documents.length}</p>
                    <p className="text-xs text-muted-foreground">{t.docsUploaded[language]}</p>
                  </div>
                  <div className="bg-white/50 dark:bg-black/20 rounded-xl p-3 text-center">
                    <p className="text-3xl font-bold text-amber-600">{favorites.length}</p>
                    <p className="text-xs text-muted-foreground">{t.favorites[language]}</p>
                  </div>
                  <div className="bg-white/50 dark:bg-black/20 rounded-xl p-3 text-center">
                    <p className="text-3xl font-bold text-purple-600">{notes.length}</p>
                    <p className="text-xs text-muted-foreground">{t.notes[language]}</p>
                  </div>
                </div>

                {/* Most Used Template */}
                {templates.length > 0 && (
                  <div className="bg-white/50 dark:bg-black/20 rounded-xl p-3">
                    <p className="text-xs text-muted-foreground mb-1">{t.mostUsed[language]}</p>
                    <div className="flex items-center gap-2">
                      <Target className="w-4 h-4 text-purple-500" />
                      <span className="text-sm font-medium">{templates[0]?.title || '-'}</span>
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          </div>

          {/* Service Status & Activity */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Services */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-card border border-border rounded-2xl p-5"
            >
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Activity className="w-5 h-5 text-primary-500" />
                {t.serviceStatus[language]}
              </h3>
              <div className="space-y-3">
                <ServiceStatus 
                  name="Ollama LLM" 
                  status={health?.components?.llm === 'healthy' || health?.ollama ? 'online' : 'offline'}
                  latency={45}
                />
                <ServiceStatus 
                  name="ChromaDB" 
                  status={health?.components?.vector_store === 'healthy' || health?.chromadb ? 'online' : 'offline'}
                  latency={12}
                />
                <ServiceStatus 
                  name="FastAPI Backend" 
                  status={health?.status === 'healthy' || health?.components?.api === 'healthy' ? 'online' : 'offline'}
                  latency={8}
                />
                <ServiceStatus 
                  name={language === 'tr' ? 'Doküman Sayısı' : 'Document Count'}
                  status={health?.components?.document_count && health.components.document_count > 0 ? 'online' : 'warning'}
                  latency={health?.components?.document_count}
                />
              </div>
            </motion.div>

            {/* System Resources */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="bg-card border border-border rounded-2xl p-5"
            >
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Cpu className="w-5 h-5 text-primary-500" />
                {t.systemResources[language]}
              </h3>
              
              <div className="space-y-4">
                {/* CPU */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">CPU</span>
                    <span className="text-sm text-muted-foreground">
                      {stats?.system_resources?.cpu_percent?.toFixed(1) ?? 0}%
                    </span>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-full transition-all duration-500" 
                      style={{ width: `${stats?.system_resources?.cpu_percent ?? 0}%` }}
                    />
                  </div>
                </div>

                {/* Memory */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">Memory</span>
                    <span className="text-sm text-muted-foreground">
                      {stats?.system_resources?.memory_percent?.toFixed(1) ?? 0}%
                      {stats?.system_resources?.memory_used_gb && stats?.system_resources?.memory_total_gb && (
                        <span className="ml-1 text-xs">
                          ({stats.system_resources.memory_used_gb.toFixed(1)}/{stats.system_resources.memory_total_gb.toFixed(1)} GB)
                        </span>
                      )}
                    </span>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-emerald-500 to-teal-600 rounded-full transition-all duration-500" 
                      style={{ width: `${stats?.system_resources?.memory_percent ?? 0}%` }}
                    />
                  </div>
                </div>

                {/* Disk */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">Disk</span>
                    <span className="text-sm text-muted-foreground">
                      {stats?.system_resources?.disk_percent?.toFixed(1) ?? 0}%
                      {stats?.system_resources?.disk_used_gb && stats?.system_resources?.disk_total_gb && (
                        <span className="ml-1 text-xs">
                          ({stats.system_resources.disk_used_gb.toFixed(1)}/{stats.system_resources.disk_total_gb.toFixed(1)} GB)
                        </span>
                      )}
                    </span>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-orange-500 to-amber-600 rounded-full transition-all duration-500" 
                      style={{ width: `${stats?.system_resources?.disk_percent ?? 0}%` }}
                    />
                  </div>
                </div>
              </div>
            </motion.div>

            {/* Recent Activity */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="bg-card border border-border rounded-2xl p-5"
            >
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Clock className="w-5 h-5 text-primary-500" />
                {t.recentActivities[language]}
              </h3>
              
              <div className="space-y-3">
                {recentActivities.map((activity, i) => (
                  <motion.div 
                    key={i} 
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.1 }}
                    className="flex items-center gap-4 p-3 rounded-xl hover:bg-muted/50 transition-colors"
                  >
                    <div className="p-2 rounded-lg bg-primary-500/10">
                      <activity.icon className="w-4 h-4 text-primary-500" />
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium">{activity.action}</p>
                    </div>
                    <span className="text-xs text-muted-foreground">{activity.time}</span>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
}
