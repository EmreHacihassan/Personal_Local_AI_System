'use client';

import React from 'react';
import { motion } from 'framer-motion';
import {
  Crown,
  Zap,
  Star,
  Lock,
  ArrowRight,
  Sparkles,
  Check,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type { PremiumFeature, PremiumTier } from '@/hooks/usePremiumTier';

interface UpgradePromptProps {
  feature?: PremiumFeature;
  requiredTier?: PremiumTier;
  currentTier?: PremiumTier;
  title?: string;
  description?: string;
  benefits?: string[];
  variant?: 'inline' | 'card' | 'modal' | 'banner';
  className?: string;
  onUpgrade?: (tier: PremiumTier) => void;
  onDismiss?: () => void;
}

// Feature display names
const FEATURE_NAMES: Record<PremiumFeature, string> = {
  web_search: 'Web Arama',
  voice_input: 'Ses Girişi',
  voice_output: 'Ses Çıkışı',
  vision: 'Görsel Analiz',
  knowledge_graph: 'Knowledge Graph',
  deep_scholar: 'DeepScholar',
  custom_models: 'Özel Modeller',
  priority_queue: 'Öncelikli Kuyruk',
  analytics: 'Analitik',
  export_pdf: 'PDF Export',
  multi_language: 'Çoklu Dil',
  auto_tagging: 'Otomatik Etiketleme',
  semantic_rerank: 'Semantic Reranking',
  computer_use: 'Computer Use Agent',
  mcp_tools: 'MCP Araçları',
};

// Tier display config
const TIER_CONFIG: Record<PremiumTier, { icon: React.ElementType; color: string; gradient: string }> = {
  free: { icon: Star, color: 'gray', gradient: 'from-gray-400 to-gray-500' },
  pro: { icon: Zap, color: 'blue', gradient: 'from-blue-500 to-purple-500' },
  enterprise: { icon: Crown, color: 'amber', gradient: 'from-amber-500 to-orange-500' },
};

// Default benefits per tier
const TIER_BENEFITS: Record<PremiumTier, string[]> = {
  free: [],
  pro: [
    'Web arama ile güncel bilgiler',
    'Ses girdi/çıktı desteği',
    'Görsel analiz ve işleme',
    'Knowledge Graph',
    'DeepScholar (30 sayfa)',
    '10K istek/gün limiti',
  ],
  enterprise: [
    'Tüm Pro özellikleri',
    'Computer Use Agent',
    'Özel model desteği',
    'Öncelikli kuyruk',
    '100K istek/gün limiti',
    'Premium destek',
  ],
};

export const UpgradePrompt: React.FC<UpgradePromptProps> = ({
  feature,
  requiredTier = 'pro',
  currentTier = 'free',
  title,
  description,
  benefits,
  variant = 'card',
  className = '',
  onUpgrade,
  onDismiss,
}) => {
  const tierConfig = TIER_CONFIG[requiredTier];
  const TierIcon = tierConfig.icon;
  const featureName = feature ? FEATURE_NAMES[feature] : null;
  const tierBenefits = benefits || TIER_BENEFITS[requiredTier];

  const defaultTitle = feature 
    ? `${featureName} özelliği ${requiredTier.charAt(0).toUpperCase() + requiredTier.slice(1)} planında`
    : `${requiredTier.charAt(0).toUpperCase() + requiredTier.slice(1)} plana yükseltin`;

  const defaultDescription = feature
    ? `Bu özelliği kullanmak için planınızı yükseltin.`
    : `Daha fazla özellik ve limite erişin.`;

  // Inline variant (simple text + button)
  if (variant === 'inline') {
    return (
      <div className={cn(
        'flex items-center gap-2 px-3 py-2 rounded-lg',
        'bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800',
        className
      )}>
        <Lock className="w-4 h-4 text-amber-500" />
        <span className="text-sm text-amber-700 dark:text-amber-300">
          {title || defaultTitle}
        </span>
        <button
          onClick={() => onUpgrade?.(requiredTier)}
          className="ml-auto flex items-center gap-1 px-2 py-1 bg-amber-500 text-white rounded text-xs font-medium hover:bg-amber-600 transition-colors"
        >
          Yükselt
          <ArrowRight className="w-3 h-3" />
        </button>
      </div>
    );
  }

  // Banner variant (full width strip)
  if (variant === 'banner') {
    return (
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className={cn(
          'relative flex items-center justify-between px-4 py-3',
          `bg-gradient-to-r ${tierConfig.gradient}`,
          'text-white',
          className
        )}
      >
        <div className="flex items-center gap-3">
          <TierIcon className="w-5 h-5" />
          <div>
            <p className="font-medium">{title || defaultTitle}</p>
            <p className="text-sm opacity-90">{description || defaultDescription}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => onUpgrade?.(requiredTier)}
            className="flex items-center gap-2 px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg font-medium transition-colors"
          >
            <Sparkles className="w-4 h-4" />
            Şimdi Yükselt
          </button>
          {onDismiss && (
            <button
              onClick={onDismiss}
              className="p-2 hover:bg-white/10 rounded-lg transition-colors"
            >
              ✕
            </button>
          )}
        </div>
      </motion.div>
    );
  }

  // Card variant (default)
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className={cn(
        'relative p-6 rounded-2xl border-2 overflow-hidden',
        'bg-white dark:bg-gray-800',
        'border-gray-200 dark:border-gray-700',
        className
      )}
    >
      {/* Background gradient */}
      <div className={cn(
        'absolute inset-0 opacity-5',
        `bg-gradient-to-br ${tierConfig.gradient}`
      )} />

      {/* Content */}
      <div className="relative z-10">
        {/* Icon & Title */}
        <div className="flex items-start gap-4 mb-4">
          <div className={cn(
            'p-3 rounded-xl',
            `bg-gradient-to-br ${tierConfig.gradient}`,
            'text-white'
          )}>
            <TierIcon className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {title || defaultTitle}
            </h3>
            <p className="text-sm text-gray-500 mt-1">
              {description || defaultDescription}
            </p>
          </div>
        </div>

        {/* Benefits */}
        {tierBenefits.length > 0 && (
          <ul className="space-y-2 mb-6">
            {tierBenefits.map((benefit, index) => (
              <li key={index} className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                <div className={cn(
                  'p-0.5 rounded-full',
                  `bg-${tierConfig.color}-100 dark:bg-${tierConfig.color}-900/30`
                )}>
                  <Check className={cn('w-3 h-3', `text-${tierConfig.color}-500`)} />
                </div>
                {benefit}
              </li>
            ))}
          </ul>
        )}

        {/* CTA Button */}
        <button
          onClick={() => onUpgrade?.(requiredTier)}
          className={cn(
            'w-full flex items-center justify-center gap-2 py-3 rounded-xl',
            `bg-gradient-to-r ${tierConfig.gradient}`,
            'text-white font-medium',
            'hover:opacity-90 transition-opacity',
            'shadow-lg hover:shadow-xl'
          )}
        >
          <Sparkles className="w-4 h-4" />
          {requiredTier === 'enterprise' ? 'Enterprise\'a Yükselt' : 'Pro\'ya Yükselt'}
          <ArrowRight className="w-4 h-4" />
        </button>

        {/* Current tier indicator */}
        <p className="text-center text-xs text-gray-400 mt-3">
          Şu anki planınız: {currentTier.charAt(0).toUpperCase() + currentTier.slice(1)}
        </p>
      </div>
    </motion.div>
  );
};

export default UpgradePrompt;
