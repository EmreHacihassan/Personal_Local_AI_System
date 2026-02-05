'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Crown,
  Sparkles,
  Zap,
  Shield,
  Check,
  X,
  ArrowRight,
  TrendingUp,
  Clock,
  FileText,
  Mic,
  Eye,
  Search,
  Brain,
  Download,
  Globe,
  Star,
  ChevronRight,
  AlertCircle,
  RefreshCw
} from 'lucide-react';
import { cn } from '@/lib/utils';

// Types
interface TierInfo {
  id: string;
  name: string;
  priority: number;
  limits: {
    requests_per_day: number;
    tokens_per_day: number;
    max_sessions: number;
    max_documents: number;
    max_file_size_mb: number;
    max_document_pages: number;
  };
  features: string[];
  feature_count: number;
}

interface UsageStats {
  tier: string;
  usage: {
    requests_today: number;
    tokens_today: number;
    sessions: number;
    documents: number;
  };
  limits: {
    requests_per_day: number;
    tokens_per_day: number;
    max_sessions: number;
    max_documents: number;
  };
  features: Record<string, boolean>;
}

interface PricingTier {
  name: string;
  price_monthly: number;
  price_yearly: number;
  currency: string;
  highlights: string[];
}

interface PremiumTierDashboardProps {
  userId?: string;
  className?: string;
  onUpgradeClick?: (tier: string) => void;
}

// Feature icons mapping
const FEATURE_ICONS: Record<string, React.ElementType> = {
  web_search: Search,
  voice_input: Mic,
  voice_output: Mic,
  vision: Eye,
  knowledge_graph: Brain,
  deep_scholar: FileText,
  custom_models: Sparkles,
  priority_queue: Zap,
  analytics: TrendingUp,
  export_pdf: Download,
  multi_language: Globe,
  auto_tagging: Star,
  semantic_rerank: TrendingUp,
  computer_use: Shield,
  mcp_tools: Sparkles,
};

// Tier colors
const TIER_STYLES: Record<string, { bg: string; border: string; text: string; icon: React.ElementType }> = {
  free: {
    bg: 'bg-gray-100 dark:bg-gray-800',
    border: 'border-gray-300 dark:border-gray-600',
    text: 'text-gray-600 dark:text-gray-400',
    icon: Star,
  },
  pro: {
    bg: 'bg-gradient-to-br from-blue-500/10 to-purple-500/10',
    border: 'border-blue-500/50',
    text: 'text-blue-600 dark:text-blue-400',
    icon: Zap,
  },
  enterprise: {
    bg: 'bg-gradient-to-br from-amber-500/10 to-orange-500/10',
    border: 'border-amber-500/50',
    text: 'text-amber-600 dark:text-amber-400',
    icon: Crown,
  },
};

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export const PremiumTierDashboard: React.FC<PremiumTierDashboardProps> = ({
  userId = 'default-user',
  className = '',
  onUpgradeClick,
}) => {
  // State
  const [tiers, setTiers] = useState<TierInfo[]>([]);
  const [userUsage, setUserUsage] = useState<UsageStats | null>(null);
  const [pricing, setPricing] = useState<Record<string, PricingTier>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTab, setSelectedTab] = useState<'overview' | 'usage' | 'features'>('overview');

  // Fetch data
  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [tiersRes, usageRes, pricingRes] = await Promise.all([
        fetch(`${API_BASE}/api/tiers/`),
        fetch(`${API_BASE}/api/tiers/user/${userId}/usage`),
        fetch(`${API_BASE}/api/tiers/pricing`),
      ]);

      if (!tiersRes.ok || !usageRes.ok || !pricingRes.ok) {
        throw new Error('API request failed');
      }

      const tiersData = await tiersRes.json();
      const usageData = await usageRes.json();
      const pricingData = await pricingRes.json();

      setTiers(tiersData.tiers || []);
      setUserUsage(usageData);
      setPricing(pricingData.pricing || {});
    } catch (err) {
      console.error('Failed to fetch tier data:', err);
      setError('Tier bilgileri yüklenemedi');
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Get current tier
  const currentTier = userUsage?.tier || 'free';
  const currentTierStyle = TIER_STYLES[currentTier] || TIER_STYLES.free;
  const TierIcon = currentTierStyle.icon;

  // Calculate usage percentages
  const getUsagePercent = (used: number, limit: number) => {
    if (limit === 0) return 0;
    return Math.min(100, Math.round((used / limit) * 100));
  };

  // Render loading state
  if (loading) {
    return (
      <div className={cn('flex items-center justify-center p-8', className)}>
        <RefreshCw className="w-6 h-6 animate-spin text-blue-500" />
        <span className="ml-2 text-gray-500">Yükleniyor...</span>
      </div>
    );
  }

  // Render error state
  if (error) {
    return (
      <div className={cn('flex items-center justify-center p-8', className)}>
        <AlertCircle className="w-6 h-6 text-red-500" />
        <span className="ml-2 text-red-500">{error}</span>
        <button
          onClick={fetchData}
          className="ml-4 px-3 py-1 bg-blue-500 text-white rounded-lg text-sm hover:bg-blue-600"
        >
          Tekrar Dene
        </button>
      </div>
    );
  }

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header - Current Tier Badge */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={cn(
            'p-3 rounded-xl',
            currentTierStyle.bg,
            'border',
            currentTierStyle.border
          )}>
            <TierIcon className={cn('w-6 h-6', currentTierStyle.text)} />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {currentTier.charAt(0).toUpperCase() + currentTier.slice(1)} Plan
            </h2>
            <p className="text-sm text-gray-500">
              {currentTier === 'enterprise' 
                ? 'Tüm özellikler aktif'
                : currentTier === 'pro'
                ? 'Gelişmiş özellikler'
                : 'Temel özellikler'}
            </p>
          </div>
        </div>

        {currentTier !== 'enterprise' && (
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => onUpgradeClick?.(currentTier === 'free' ? 'pro' : 'enterprise')}
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-medium shadow-lg hover:shadow-xl transition-shadow"
          >
            <Sparkles className="w-4 h-4" />
            Yükselt
            <ArrowRight className="w-4 h-4" />
          </motion.button>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-200 dark:border-gray-700">
        {(['overview', 'usage', 'features'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setSelectedTab(tab)}
            className={cn(
              'px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-[2px]',
              selectedTab === tab
                ? 'text-blue-600 border-blue-600'
                : 'text-gray-500 border-transparent hover:text-gray-700'
            )}
          >
            {tab === 'overview' ? 'Genel Bakış' : tab === 'usage' ? 'Kullanım' : 'Özellikler'}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <AnimatePresence mode="wait">
        {selectedTab === 'overview' && (
          <motion.div
            key="overview"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-6"
          >
            {/* Tier Comparison Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {tiers.map((tier) => {
                const style = TIER_STYLES[tier.id] || TIER_STYLES.free;
                const Icon = style.icon;
                const isCurrentTier = tier.id === currentTier;
                const tierPricing = pricing[tier.id];

                return (
                  <motion.div
                    key={tier.id}
                    whileHover={{ y: -4 }}
                    className={cn(
                      'relative p-5 rounded-xl border-2 transition-all',
                      style.bg,
                      isCurrentTier ? style.border : 'border-gray-200 dark:border-gray-700',
                      isCurrentTier && 'ring-2 ring-offset-2 ring-blue-500'
                    )}
                  >
                    {isCurrentTier && (
                      <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-blue-500 text-white text-xs font-medium rounded-full">
                        Mevcut Plan
                      </div>
                    )}

                    <div className="flex items-center gap-3 mb-4">
                      <Icon className={cn('w-8 h-8', style.text)} />
                      <div>
                        <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                          {tier.name}
                        </h3>
                        {tierPricing && (
                          <p className="text-sm text-gray-500">
                            {tierPricing.price_monthly === 0 
                              ? 'Ücretsiz'
                              : `$${tierPricing.price_monthly}/ay`}
                          </p>
                        )}
                      </div>
                    </div>

                    <ul className="space-y-2 mb-4">
                      <li className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                        <Clock className="w-4 h-4" />
                        {tier.limits.requests_per_day.toLocaleString()} istek/gün
                      </li>
                      <li className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                        <FileText className="w-4 h-4" />
                        {tier.limits.max_documents.toLocaleString()} döküman
                      </li>
                      <li className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                        <Sparkles className="w-4 h-4" />
                        {tier.feature_count} özellik
                      </li>
                    </ul>

                    {!isCurrentTier && tier.priority > (tiers.find(t => t.id === currentTier)?.priority || 0) && (
                      <button
                        onClick={() => onUpgradeClick?.(tier.id)}
                        className={cn(
                          'w-full py-2 rounded-lg font-medium text-sm transition-colors',
                          tier.id === 'enterprise'
                            ? 'bg-gradient-to-r from-amber-500 to-orange-500 text-white'
                            : 'bg-gradient-to-r from-blue-500 to-purple-500 text-white'
                        )}
                      >
                        Yükselt
                      </button>
                    )}
                  </motion.div>
                );
              })}
            </div>
          </motion.div>
        )}

        {selectedTab === 'usage' && userUsage && (
          <motion.div
            key="usage"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-6"
          >
            {/* Usage Stats Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                {
                  label: 'Günlük İstek',
                  used: userUsage.usage.requests_today,
                  limit: userUsage.limits.requests_per_day,
                  icon: Clock,
                  color: 'blue',
                },
                {
                  label: 'Token Kullanımı',
                  used: userUsage.usage.tokens_today,
                  limit: userUsage.limits.tokens_per_day,
                  icon: Zap,
                  color: 'purple',
                },
                {
                  label: 'Oturumlar',
                  used: userUsage.usage.sessions,
                  limit: userUsage.limits.max_sessions,
                  icon: FileText,
                  color: 'green',
                },
                {
                  label: 'Dökümanlar',
                  used: userUsage.usage.documents,
                  limit: userUsage.limits.max_documents,
                  icon: FileText,
                  color: 'amber',
                },
              ].map((stat, index) => {
                const percent = getUsagePercent(stat.used, stat.limit);
                const Icon = stat.icon;

                return (
                  <div
                    key={index}
                    className="p-4 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700"
                  >
                    <div className="flex items-center gap-2 mb-3">
                      <Icon className={`w-4 h-4 text-${stat.color}-500`} />
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        {stat.label}
                      </span>
                    </div>

                    <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                      {stat.used.toLocaleString()}
                      <span className="text-sm font-normal text-gray-500">
                        /{stat.limit.toLocaleString()}
                      </span>
                    </div>

                    {/* Progress bar */}
                    <div className="mt-2 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${percent}%` }}
                        transition={{ duration: 0.5, ease: 'easeOut' }}
                        className={cn(
                          'h-full rounded-full',
                          percent >= 90 ? 'bg-red-500' :
                          percent >= 70 ? 'bg-amber-500' :
                          `bg-${stat.color}-500`
                        )}
                      />
                    </div>

                    <p className="mt-1 text-xs text-gray-500">
                      {percent}% kullanıldı
                    </p>
                  </div>
                );
              })}
            </div>
          </motion.div>
        )}

        {selectedTab === 'features' && userUsage && (
          <motion.div
            key="features"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-4"
          >
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              {Object.entries(userUsage.features).map(([feature, enabled]) => {
                const Icon = FEATURE_ICONS[feature] || Sparkles;
                const featureName = feature
                  .replace(/_/g, ' ')
                  .replace(/\b\w/g, (c) => c.toUpperCase());

                return (
                  <div
                    key={feature}
                    className={cn(
                      'flex items-center gap-3 p-3 rounded-lg border transition-colors',
                      enabled
                        ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
                        : 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700 opacity-60'
                    )}
                  >
                    <div className={cn(
                      'p-2 rounded-lg',
                      enabled
                        ? 'bg-green-100 dark:bg-green-800'
                        : 'bg-gray-100 dark:bg-gray-700'
                    )}>
                      <Icon className={cn(
                        'w-4 h-4',
                        enabled
                          ? 'text-green-600 dark:text-green-400'
                          : 'text-gray-400'
                      )} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className={cn(
                        'text-sm font-medium truncate',
                        enabled
                          ? 'text-green-800 dark:text-green-200'
                          : 'text-gray-500'
                      )}>
                        {featureName}
                      </p>
                    </div>
                    {enabled ? (
                      <Check className="w-4 h-4 text-green-500" />
                    ) : (
                      <X className="w-4 h-4 text-gray-400" />
                    )}
                  </div>
                );
              })}
            </div>

            {/* Upgrade CTA */}
            {currentTier !== 'enterprise' && (
              <div className="p-4 bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-xl border border-blue-200 dark:border-blue-800">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-semibold text-gray-900 dark:text-gray-100">
                      Daha fazla özellik ister misiniz?
                    </h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Pro veya Enterprise plana yükseltin
                    </p>
                  </div>
                  <button
                    onClick={() => onUpgradeClick?.(currentTier === 'free' ? 'pro' : 'enterprise')}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
                  >
                    Planları Gör
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default PremiumTierDashboard;
