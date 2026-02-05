'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Crown,
  Zap,
  Star,
  TrendingUp,
  AlertTriangle,
  ChevronDown,
  RefreshCw,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface UsageMeterProps {
  userId?: string;
  compact?: boolean;
  showTierBadge?: boolean;
  className?: string;
  onUpgradeClick?: () => void;
}

interface UsageData {
  tier: string;
  usage: {
    requests_today: number;
    tokens_today: number;
  };
  limits: {
    requests_per_day: number;
    tokens_per_day: number;
  };
  percentages: {
    requests_per_day: number;
    tokens_per_day: number;
  };
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

const TIER_CONFIGS: Record<string, { color: string; icon: React.ElementType; gradient: string }> = {
  free: { color: 'gray', icon: Star, gradient: 'from-gray-400 to-gray-500' },
  pro: { color: 'blue', icon: Zap, gradient: 'from-blue-500 to-purple-500' },
  enterprise: { color: 'amber', icon: Crown, gradient: 'from-amber-500 to-orange-500' },
};

export const UsageMeter: React.FC<UsageMeterProps> = ({
  userId = 'default-user',
  compact = false,
  showTierBadge = true,
  className = '',
  onUpgradeClick,
}) => {
  const [usage, setUsage] = useState<UsageData | null>(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(false);
  const [error, setError] = useState(false);

  const fetchUsage = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/tiers/user/${userId}/usage`);
      if (!response.ok) throw new Error('Failed to fetch');
      const data = await response.json();
      setUsage(data);
      setError(false);
    } catch (err) {
      console.error('Failed to fetch usage:', err);
      setError(true);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    fetchUsage();
    // Refresh every 5 minutes
    const interval = setInterval(fetchUsage, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [fetchUsage]);

  if (loading) {
    return (
      <div className={cn('flex items-center gap-2 px-3 py-1.5', className)}>
        <RefreshCw className="w-4 h-4 animate-spin text-gray-400" />
      </div>
    );
  }

  if (error || !usage) {
    return (
      <div className={cn('flex items-center gap-2 px-3 py-1.5', className)}>
        <AlertTriangle className="w-4 h-4 text-amber-500" />
      </div>
    );
  }

  const tierConfig = TIER_CONFIGS[usage.tier] || TIER_CONFIGS.free;
  const TierIcon = tierConfig.icon;
  const requestPercent = usage.percentages?.requests_per_day || 0;
  const isNearLimit = requestPercent >= 80;
  const isAtLimit = requestPercent >= 95;

  // Compact mode (just a badge)
  if (compact) {
    return (
      <button
        onClick={() => setExpanded(!expanded)}
        className={cn(
          'relative flex items-center gap-1.5 px-2 py-1 rounded-lg',
          'bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700',
          'transition-colors',
          className
        )}
      >
        <TierIcon className={cn('w-4 h-4', `text-${tierConfig.color}-500`)} />
        <span className={cn(
          'text-xs font-medium',
          isAtLimit ? 'text-red-500' : isNearLimit ? 'text-amber-500' : 'text-gray-600 dark:text-gray-400'
        )}>
          {requestPercent}%
        </span>
        
        {/* Warning indicator */}
        {isNearLimit && (
          <span className={cn(
            'absolute -top-1 -right-1 w-2 h-2 rounded-full',
            isAtLimit ? 'bg-red-500' : 'bg-amber-500',
            'animate-pulse'
          )} />
        )}
      </button>
    );
  }

  return (
    <div className={cn('relative', className)}>
      {/* Main Button */}
      <button
        onClick={() => setExpanded(!expanded)}
        className={cn(
          'flex items-center gap-2 px-3 py-1.5 rounded-lg',
          'bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700',
          'transition-all duration-200',
          expanded && 'ring-2 ring-blue-500 ring-offset-2'
        )}
      >
        {/* Tier Badge */}
        {showTierBadge && (
          <div className={cn(
            'flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium',
            `bg-gradient-to-r ${tierConfig.gradient} text-white`
          )}>
            <TierIcon className="w-3 h-3" />
            {usage.tier.charAt(0).toUpperCase() + usage.tier.slice(1)}
          </div>
        )}

        {/* Usage Bar */}
        <div className="flex items-center gap-2">
          <div className="w-16 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${requestPercent}%` }}
              className={cn(
                'h-full rounded-full',
                isAtLimit ? 'bg-red-500' : isNearLimit ? 'bg-amber-500' : 'bg-blue-500'
              )}
            />
          </div>
          <span className={cn(
            'text-xs font-medium',
            isAtLimit ? 'text-red-500' : isNearLimit ? 'text-amber-500' : 'text-gray-600 dark:text-gray-400'
          )}>
            {requestPercent}%
          </span>
        </div>

        <ChevronDown className={cn(
          'w-4 h-4 text-gray-400 transition-transform',
          expanded && 'rotate-180'
        )} />
      </button>

      {/* Expanded Panel */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            className="absolute right-0 top-full mt-2 w-72 p-4 bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 z-50"
          >
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <div className={cn(
                  'p-2 rounded-lg',
                  `bg-gradient-to-r ${tierConfig.gradient}`
                )}>
                  <TierIcon className="w-4 h-4 text-white" />
                </div>
                <div>
                  <p className="font-semibold text-gray-900 dark:text-gray-100">
                    {usage.tier.charAt(0).toUpperCase() + usage.tier.slice(1)} Plan
                  </p>
                  <p className="text-xs text-gray-500">Günlük Kullanım</p>
                </div>
              </div>
              <button
                onClick={fetchUsage}
                className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                <RefreshCw className="w-4 h-4 text-gray-400" />
              </button>
            </div>

            {/* Stats */}
            <div className="space-y-3">
              {/* Requests */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    İstekler
                  </span>
                  <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {usage.usage.requests_today.toLocaleString()} / {usage.limits.requests_per_day.toLocaleString()}
                  </span>
                </div>
                <div className="h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${usage.percentages.requests_per_day}%` }}
                    className={cn(
                      'h-full rounded-full',
                      usage.percentages.requests_per_day >= 90 ? 'bg-red-500' :
                      usage.percentages.requests_per_day >= 70 ? 'bg-amber-500' : 'bg-blue-500'
                    )}
                  />
                </div>
              </div>

              {/* Tokens */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    Tokenlar
                  </span>
                  <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {(usage.usage.tokens_today / 1000).toFixed(1)}K / {(usage.limits.tokens_per_day / 1000).toFixed(0)}K
                  </span>
                </div>
                <div className="h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${usage.percentages.tokens_per_day}%` }}
                    className={cn(
                      'h-full rounded-full',
                      usage.percentages.tokens_per_day >= 90 ? 'bg-red-500' :
                      usage.percentages.tokens_per_day >= 70 ? 'bg-amber-500' : 'bg-purple-500'
                    )}
                  />
                </div>
              </div>
            </div>

            {/* Upgrade CTA */}
            {usage.tier !== 'enterprise' && (
              <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                <button
                  onClick={() => {
                    onUpgradeClick?.();
                    setExpanded(false);
                  }}
                  className={cn(
                    'w-full flex items-center justify-center gap-2 py-2 rounded-lg',
                    'bg-gradient-to-r from-blue-500 to-purple-500 text-white',
                    'font-medium text-sm hover:opacity-90 transition-opacity'
                  )}
                >
                  <TrendingUp className="w-4 h-4" />
                  {usage.tier === 'free' ? 'Pro\'ya Yükselt' : 'Enterprise\'a Yükselt'}
                </button>
              </div>
            )}

            {/* Warning message */}
            {isNearLimit && (
              <div className={cn(
                'mt-3 p-2 rounded-lg text-xs',
                isAtLimit ? 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400' :
                'bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400'
              )}>
                <AlertTriangle className="w-3 h-3 inline mr-1" />
                {isAtLimit 
                  ? 'Günlük limitinize ulaştınız!' 
                  : 'Günlük limitinize yaklaşıyorsunuz.'}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default UsageMeter;
