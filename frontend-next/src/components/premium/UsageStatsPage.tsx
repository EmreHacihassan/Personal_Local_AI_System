'use client';

import React from 'react';
import { motion } from 'framer-motion';
import {
  Activity,
  Database,
  MessageSquare,
  FileText,
  Clock,
  RefreshCw,
  Crown,
  Zap,
  Star,
  Check,
  Cpu,
  HardDrive,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { usePremiumTier, PremiumTier } from '@/hooks/usePremiumTier';

interface UsageStatsPageProps {
  userId?: string;
  className?: string;
}

const TIER_ICONS: Record<PremiumTier, React.ElementType> = {
  free: Star,
  pro: Zap,
  enterprise: Crown,
};

// Stat card component
interface StatCardProps {
  icon: React.ElementType;
  label: string;
  current: number;
  max: number;
  format?: 'number' | 'size' | 'tokens';
  color?: string;
}

const StatCard: React.FC<StatCardProps> = ({ 
  icon: Icon, 
  label, 
  current, 
  max, 
  format = 'number',
  color = 'blue' 
}) => {
  const percent = Math.min(100, (current / max) * 100);
  const status = percent >= 90 ? 'critical' : percent >= 70 ? 'warning' : 'normal';
  
  const formatValue = (val: number) => {
    if (format === 'size') {
      if (val >= 1000) return `${(val / 1000).toFixed(1)}GB`;
      return `${val}MB`;
    }
    if (format === 'tokens') {
      if (val >= 1000000) return `${(val / 1000000).toFixed(1)}M`;
      if (val >= 1000) return `${(val / 1000).toFixed(0)}K`;
      return val.toString();
    }
    return val.toLocaleString();
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-5"
    >
      <div className="flex items-center gap-3 mb-4">
        <div className={cn(
          'p-2.5 rounded-xl',
          `bg-${color}-100 dark:bg-${color}-900/30`
        )}>
          <Icon className={cn('w-5 h-5', `text-${color}-500`)} />
        </div>
        <div>
          <p className="text-sm text-gray-500">{label}</p>
          <p className="text-lg font-bold text-gray-900 dark:text-gray-100">
            {formatValue(current)} <span className="text-sm font-normal text-gray-400">/ {formatValue(max)}</span>
          </p>
        </div>
      </div>
      
      <div className="h-3 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${percent}%` }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
          className={cn(
            'h-full rounded-full',
            status === 'critical' && 'bg-red-500',
            status === 'warning' && 'bg-yellow-500',
            status === 'normal' && `bg-${color}-500`
          )}
        />
      </div>
      
      <p className={cn(
        'text-xs mt-2',
        status === 'critical' ? 'text-red-500' : 
        status === 'warning' ? 'text-yellow-600' : 'text-gray-400'
      )}>
        {percent.toFixed(0)}% kullanıldı
      </p>
    </motion.div>
  );
};

export const UsageStatsPage: React.FC<UsageStatsPageProps> = ({
  userId = 'default-user',
  className = '',
}) => {
  const { tier, tierDisplay, usage, limits, features, isLoading, refetch } = usePremiumTier({ userId });
  
  const TierIcon = TIER_ICONS[tier];
  
  // Active features list
  const activeFeatures = Object.entries(features)
    .filter(([_, enabled]) => enabled)
    .map(([name]) => name);

  if (isLoading) {
    return (
      <div className={cn('min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center', className)}>
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500" />
      </div>
    );
  }

  return (
    <div className={cn('min-h-screen bg-gray-50 dark:bg-gray-900', className)}>
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-5xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className={cn(
                'p-3 rounded-2xl',
                tier === 'enterprise' && 'bg-gradient-to-br from-amber-500 to-orange-500',
                tier === 'pro' && 'bg-gradient-to-br from-blue-500 to-purple-500',
                tier === 'free' && 'bg-gray-200 dark:bg-gray-700'
              )}>
                <TierIcon className={cn(
                  'w-7 h-7',
                  tier === 'free' ? 'text-gray-500' : 'text-white'
                )} />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">
                  Kullanım İstatistikleri
                </h1>
                <p className="text-sm text-gray-500">
                  {tierDisplay} Plan - Tüm özellikler aktif
                </p>
              </div>
            </div>
            
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={refetch}
              className="flex items-center gap-2 px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-xl transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              Yenile
            </motion.button>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-6 py-8 space-y-8">
        {/* Usage Stats Grid */}
        {usage && limits && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <StatCard
              icon={MessageSquare}
              label="Bugünkü İstekler"
              current={usage.requests_today}
              max={limits.requests_per_day}
              color="blue"
            />
            <StatCard
              icon={Cpu}
              label="Bugünkü Tokenler"
              current={usage.tokens_today}
              max={limits.tokens_per_day}
              format="tokens"
              color="purple"
            />
            <StatCard
              icon={Activity}
              label="Aktif Oturumlar"
              current={usage.sessions}
              max={limits.max_sessions}
              color="green"
            />
            <StatCard
              icon={FileText}
              label="Belgeler"
              current={usage.documents}
              max={limits.max_documents}
              color="orange"
            />
            <StatCard
              icon={HardDrive}
              label="Dosya Boyutu Limiti"
              current={0}
              max={limits.max_file_size_mb}
              format="size"
              color="teal"
            />
            <StatCard
              icon={Database}
              label="Sayfa Limiti"
              current={0}
              max={limits.max_document_pages}
              color="pink"
            />
          </div>
        )}

        {/* Active Features */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6"
        >
          <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
            <Check className="w-5 h-5 text-green-500" />
            Aktif Özellikler ({activeFeatures.length})
          </h2>
          
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
            {activeFeatures.map((feature, index) => (
              <motion.div
                key={feature}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.3 + index * 0.05 }}
                className="flex items-center gap-2 px-3 py-2 bg-green-50 dark:bg-green-900/20 rounded-lg"
              >
                <Check className="w-4 h-4 text-green-500 shrink-0" />
                <span className="text-sm text-green-700 dark:text-green-400 truncate">
                  {feature.replace(/_/g, ' ')}
                </span>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Quick Info */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="grid grid-cols-1 sm:grid-cols-3 gap-4"
        >
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-2xl p-5 text-center">
            <Clock className="w-8 h-8 text-blue-500 mx-auto mb-2" />
            <p className="text-2xl font-bold text-blue-700 dark:text-blue-400">
              {new Date().toLocaleDateString('tr-TR')}
            </p>
            <p className="text-sm text-blue-600 dark:text-blue-500">Bugün</p>
          </div>
          
          <div className="bg-purple-50 dark:bg-purple-900/20 rounded-2xl p-5 text-center">
            <Activity className="w-8 h-8 text-purple-500 mx-auto mb-2" />
            <p className="text-2xl font-bold text-purple-700 dark:text-purple-400">
              {usage?.requests_today || 0}
            </p>
            <p className="text-sm text-purple-600 dark:text-purple-500">Bugünkü İstek</p>
          </div>
          
          <div className="bg-green-50 dark:bg-green-900/20 rounded-2xl p-5 text-center">
            <Check className="w-8 h-8 text-green-500 mx-auto mb-2" />
            <p className="text-2xl font-bold text-green-700 dark:text-green-400">
              {activeFeatures.length}
            </p>
            <p className="text-sm text-green-600 dark:text-green-500">Aktif Özellik</p>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

// Keep backward compatibility
export const BillingPage = UsageStatsPage;

export default UsageStatsPage;
