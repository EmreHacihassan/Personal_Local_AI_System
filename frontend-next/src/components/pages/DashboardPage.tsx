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
  HardDrive,
  Activity,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCw
} from 'lucide-react';
import { useStore } from '@/store/useStore';
import { getDashboardData, getStats, checkHealth } from '@/lib/api';
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

export function DashboardPage() {
  const { language, documents, messages } = useStore();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<any>(null);
  const [health, setHealth] = useState<any>(null);
  const [dashboard, setDashboard] = useState<any>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    
    const [statsRes, healthRes, dashboardRes] = await Promise.all([
      getStats(),
      checkHealth(),
      getDashboardData(),
    ]);

    if (statsRes.success) setStats(statsRes.data);
    if (healthRes.success) setHealth(healthRes.data);
    if (dashboardRes.success) setDashboard(dashboardRes.data);

    setLoading(false);
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
            <h1 className="text-lg font-semibold">Dashboard</h1>
            <p className="text-xs text-muted-foreground">
              {language === 'tr' ? 'Sistem genel bakış' : 'System overview'}
            </p>
          </div>
        </div>

        <button
          onClick={loadData}
          className="flex items-center gap-2 px-4 py-2 bg-muted hover:bg-accent rounded-xl transition-colors"
        >
          <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
          <span className="text-sm">{language === 'tr' ? 'Yenile' : 'Refresh'}</span>
        </button>
      </header>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-6xl mx-auto space-y-6">
          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              title={language === 'tr' ? 'Toplam Sohbet' : 'Total Chats'}
              value={messages.length}
              icon={MessageSquare}
              color="bg-gradient-to-br from-blue-500 to-blue-600"
              trend={{ value: 12, positive: true }}
            />
            <StatCard
              title={language === 'tr' ? 'Dökümanlar' : 'Documents'}
              value={documents.length}
              icon={FileText}
              color="bg-gradient-to-br from-emerald-500 to-teal-600"
              trend={{ value: 8, positive: true }}
            />
            <StatCard
              title={language === 'tr' ? 'Vector Sayısı' : 'Vector Count'}
              value={stats?.vector_count || 0}
              icon={Database}
              color="bg-gradient-to-br from-orange-500 to-amber-600"
            />
            <StatCard
              title={language === 'tr' ? 'Ort. Yanıt Süresi' : 'Avg Response Time'}
              value="1.2s"
              icon={Zap}
              color="bg-gradient-to-br from-pink-500 to-rose-600"
              trend={{ value: 5, positive: false }}
            />
          </div>

          {/* Service Status & Activity */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Services */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-card border border-border rounded-2xl p-5"
            >
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Activity className="w-5 h-5 text-primary-500" />
                {language === 'tr' ? 'Servis Durumu' : 'Service Status'}
              </h3>
              <div className="space-y-3">
                <ServiceStatus 
                  name="Ollama LLM" 
                  status={health?.ollama ? 'online' : 'offline'}
                  latency={45}
                />
                <ServiceStatus 
                  name="ChromaDB" 
                  status={health?.chromadb ? 'online' : 'offline'}
                  latency={12}
                />
                <ServiceStatus 
                  name="FastAPI Backend" 
                  status={health?.status === 'healthy' ? 'online' : 'offline'}
                  latency={8}
                />
                <ServiceStatus 
                  name="Circuit Breaker" 
                  status="online"
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
                {language === 'tr' ? 'Sistem Kaynakları' : 'System Resources'}
              </h3>
              
              <div className="space-y-4">
                {/* CPU */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">CPU</span>
                    <span className="text-sm text-muted-foreground">32%</span>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <div className="h-full w-[32%] bg-gradient-to-r from-blue-500 to-blue-600 rounded-full" />
                  </div>
                </div>

                {/* Memory */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">Memory</span>
                    <span className="text-sm text-muted-foreground">58%</span>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <div className="h-full w-[58%] bg-gradient-to-r from-emerald-500 to-teal-600 rounded-full" />
                  </div>
                </div>

                {/* Disk */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">Disk</span>
                    <span className="text-sm text-muted-foreground">45%</span>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <div className="h-full w-[45%] bg-gradient-to-r from-orange-500 to-amber-600 rounded-full" />
                  </div>
                </div>
              </div>
            </motion.div>
          </div>

          {/* Recent Activity */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="bg-card border border-border rounded-2xl p-5"
          >
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Clock className="w-5 h-5 text-primary-500" />
              {language === 'tr' ? 'Son Aktiviteler' : 'Recent Activities'}
            </h3>
            
            <div className="space-y-3">
              {[
                { action: 'Yeni döküman yüklendi', time: '2 dk önce', icon: FileText },
                { action: 'Chat oturumu başlatıldı', time: '15 dk önce', icon: MessageSquare },
                { action: 'RAG sorgusu çalıştırıldı', time: '1 saat önce', icon: Database },
              ].map((activity, i) => (
                <div key={i} className="flex items-center gap-4 p-3 rounded-xl hover:bg-muted/50 transition-colors">
                  <div className="p-2 rounded-lg bg-primary-500/10">
                    <activity.icon className="w-4 h-4 text-primary-500" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium">{activity.action}</p>
                  </div>
                  <span className="text-xs text-muted-foreground">{activity.time}</span>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
