'use client';

import React, { ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Lock, Crown, Zap, Star } from 'lucide-react';
import { cn } from '@/lib/utils';
import { usePremiumTier, PremiumFeature, PremiumTier } from '@/hooks/usePremiumTier';
import { UpgradePrompt } from './UpgradePrompt';

interface FeatureGateProps {
  /** The feature to check access for */
  feature: PremiumFeature;
  /** User ID for tier lookup */
  userId?: string;
  /** Content to show when user has access */
  children: ReactNode;
  /** Fallback content when user doesn't have access (overrides default upgrade prompt) */
  fallback?: ReactNode;
  /** Visual style when locked */
  lockedStyle?: 'blur' | 'overlay' | 'replace' | 'hide';
  /** Show feature preview even when locked */
  showPreview?: boolean;
  /** Custom class name */
  className?: string;
  /** Callback when user clicks upgrade */
  onUpgrade?: (tier: PremiumTier) => void;
}

// Maps features to their required tier
const FEATURE_TIERS: Record<PremiumFeature, PremiumTier> = {
  web_search: 'pro',
  voice_input: 'pro',
  voice_output: 'pro',
  vision: 'pro',
  knowledge_graph: 'pro',
  deep_scholar: 'pro',
  custom_models: 'enterprise',
  priority_queue: 'enterprise',
  analytics: 'pro',
  export_pdf: 'pro',
  multi_language: 'free',
  auto_tagging: 'pro',
  semantic_rerank: 'pro',
  computer_use: 'enterprise',
  mcp_tools: 'pro',
};

const TIER_ICONS: Record<PremiumTier, React.ElementType> = {
  free: Star,
  pro: Zap,
  enterprise: Crown,
};

export const FeatureGate: React.FC<FeatureGateProps> = ({
  feature,
  userId = 'default',
  children,
  fallback,
  lockedStyle = 'overlay',
  showPreview = false,
  className = '',
  onUpgrade,
}) => {
  const { hasFeature, tier, isLoading } = usePremiumTier({ userId });
  
  const hasAccess = hasFeature(feature);
  const requiredTier = FEATURE_TIERS[feature];
  const TierIcon = TIER_ICONS[requiredTier];

  // Loading state
  if (isLoading) {
    return (
      <div className={cn('animate-pulse bg-gray-100 dark:bg-gray-800 rounded-lg', className)}>
        {showPreview ? children : <div className="h-32 w-full" />}
      </div>
    );
  }

  // User has access - render children
  if (hasAccess) {
    return <>{children}</>;
  }

  // User doesn't have access - show locked state
  
  // Hide completely
  if (lockedStyle === 'hide') {
    return null;
  }

  // Custom fallback
  if (fallback) {
    return <>{fallback}</>;
  }

  // Replace with upgrade prompt
  if (lockedStyle === 'replace') {
    return (
      <UpgradePrompt
        feature={feature}
        requiredTier={requiredTier}
        currentTier={tier}
        variant="card"
        className={className}
        onUpgrade={onUpgrade}
      />
    );
  }

  // Blur or overlay (show preview with lock)
  return (
    <div className={cn('relative', className)}>
      {/* Content with blur effect */}
      <div
        className={cn(
          'transition-all duration-300',
          lockedStyle === 'blur' && 'blur-sm pointer-events-none select-none',
          lockedStyle === 'overlay' && 'opacity-50 pointer-events-none select-none'
        )}
      >
        {children}
      </div>

      {/* Lock overlay */}
      <AnimatePresence>
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 flex items-center justify-center bg-white/50 dark:bg-gray-900/50 backdrop-blur-sm rounded-lg"
        >
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ type: 'spring', stiffness: 300, damping: 25 }}
            className="flex flex-col items-center gap-3 p-6"
          >
            <div className={cn(
              'p-4 rounded-full',
              requiredTier === 'enterprise' 
                ? 'bg-gradient-to-br from-amber-500 to-orange-500' 
                : 'bg-gradient-to-br from-blue-500 to-purple-500',
              'text-white shadow-lg'
            )}>
              <Lock className="w-6 h-6" />
            </div>
            
            <div className="text-center">
              <div className="flex items-center justify-center gap-2 mb-1">
                <TierIcon className={cn(
                  'w-4 h-4',
                  requiredTier === 'enterprise' ? 'text-amber-500' : 'text-blue-500'
                )} />
                <span className="font-semibold text-gray-900 dark:text-gray-100">
                  {requiredTier === 'enterprise' ? 'Enterprise' : 'Pro'} Özelliği
                </span>
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Bu özelliği kullanmak için yükseltme yapın
              </p>
            </div>

            <button
              onClick={() => onUpgrade?.(requiredTier)}
              className={cn(
                'flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-white',
                'transition-all hover:scale-105',
                requiredTier === 'enterprise'
                  ? 'bg-gradient-to-r from-amber-500 to-orange-500'
                  : 'bg-gradient-to-r from-blue-500 to-purple-500'
              )}
            >
              Şimdi Yükselt
            </button>
          </motion.div>
        </motion.div>
      </AnimatePresence>
    </div>
  );
};

/**
 * Hook version for programmatic feature checking
 */
export const useFeatureGateLocal = (feature: PremiumFeature, userId: string = 'default') => {
  const { hasFeature, tier, isLoading, error } = usePremiumTier({ userId });
  
  const hasAccess = hasFeature(feature);
  const requiredTier = FEATURE_TIERS[feature];
  const isLocked = !hasAccess && !isLoading;

  return {
    hasAccess,
    isLocked,
    requiredTier,
    currentTier: tier,
    isLoading,
    error,
  };
};

export default FeatureGate;

