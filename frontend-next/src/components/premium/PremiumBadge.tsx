'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Crown, Zap, Star, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { PremiumTier } from '@/hooks/usePremiumTier';

interface PremiumBadgeProps {
  tier: PremiumTier;
  size?: 'xs' | 'sm' | 'md' | 'lg';
  variant?: 'default' | 'outline' | 'glow' | 'minimal';
  showLabel?: boolean;
  animated?: boolean;
  className?: string;
}

const TIER_CONFIG: Record<PremiumTier, {
  label: string;
  icon: React.ElementType;
  colors: {
    bg: string;
    border: string;
    text: string;
    gradient: string;
    glow: string;
  };
}> = {
  free: {
    label: 'Free',
    icon: Star,
    colors: {
      bg: 'bg-gray-100 dark:bg-gray-800',
      border: 'border-gray-300 dark:border-gray-600',
      text: 'text-gray-600 dark:text-gray-400',
      gradient: 'from-gray-400 to-gray-500',
      glow: 'shadow-gray-300/50',
    },
  },
  pro: {
    label: 'Pro',
    icon: Zap,
    colors: {
      bg: 'bg-blue-100 dark:bg-blue-900/30',
      border: 'border-blue-400 dark:border-blue-600',
      text: 'text-blue-600 dark:text-blue-400',
      gradient: 'from-blue-500 to-purple-500',
      glow: 'shadow-blue-500/50',
    },
  },
  enterprise: {
    label: 'Enterprise',
    icon: Crown,
    colors: {
      bg: 'bg-amber-100 dark:bg-amber-900/30',
      border: 'border-amber-400 dark:border-amber-600',
      text: 'text-amber-600 dark:text-amber-400',
      gradient: 'from-amber-500 to-orange-500',
      glow: 'shadow-amber-500/50',
    },
  },
};

const SIZE_CONFIG = {
  xs: {
    container: 'px-1.5 py-0.5 gap-1',
    icon: 'w-3 h-3',
    text: 'text-[10px]',
  },
  sm: {
    container: 'px-2 py-1 gap-1.5',
    icon: 'w-3.5 h-3.5',
    text: 'text-xs',
  },
  md: {
    container: 'px-3 py-1.5 gap-2',
    icon: 'w-4 h-4',
    text: 'text-sm',
  },
  lg: {
    container: 'px-4 py-2 gap-2',
    icon: 'w-5 h-5',
    text: 'text-base',
  },
};

export const PremiumBadge: React.FC<PremiumBadgeProps> = ({
  tier,
  size = 'sm',
  variant = 'default',
  showLabel = true,
  animated = true,
  className = '',
}) => {
  const config = TIER_CONFIG[tier];
  const sizeConfig = SIZE_CONFIG[size];
  const Icon = config.icon;

  const baseClasses = cn(
    'inline-flex items-center rounded-full font-medium',
    sizeConfig.container,
    sizeConfig.text
  );

  // Minimal variant - just icon
  if (variant === 'minimal') {
    return (
      <motion.span
        initial={animated ? { scale: 0.8 } : false}
        animate={{ scale: 1 }}
        className={cn(
          'inline-flex items-center justify-center',
          className
        )}
      >
        <Icon className={cn(sizeConfig.icon, config.colors.text)} />
      </motion.span>
    );
  }

  // Outline variant
  if (variant === 'outline') {
    return (
      <motion.span
        initial={animated ? { scale: 0.9, opacity: 0 } : false}
        animate={{ scale: 1, opacity: 1 }}
        className={cn(
          baseClasses,
          'bg-transparent border',
          config.colors.border,
          config.colors.text,
          className
        )}
      >
        <Icon className={sizeConfig.icon} />
        {showLabel && <span>{config.label}</span>}
      </motion.span>
    );
  }

  // Glow variant - premium animated effect
  if (variant === 'glow') {
    return (
      <motion.span
        initial={animated ? { scale: 0.9, opacity: 0 } : false}
        animate={{ scale: 1, opacity: 1 }}
        className={cn(
          baseClasses,
          `bg-gradient-to-r ${config.colors.gradient}`,
          'text-white',
          'shadow-lg',
          config.colors.glow,
          className
        )}
      >
        {animated && tier !== 'free' && (
          <motion.span
            className="absolute inset-0 rounded-full"
            animate={{
              boxShadow: [
                `0 0 10px var(--tw-shadow-color)`,
                `0 0 20px var(--tw-shadow-color)`,
                `0 0 10px var(--tw-shadow-color)`,
              ],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          />
        )}
        <Icon className={sizeConfig.icon} />
        {showLabel && <span>{config.label}</span>}
        {tier === 'enterprise' && animated && (
          <Sparkles className={cn(sizeConfig.icon, 'animate-pulse')} />
        )}
      </motion.span>
    );
  }

  // Default variant - solid background
  return (
    <motion.span
      initial={animated ? { scale: 0.9, opacity: 0 } : false}
      animate={{ scale: 1, opacity: 1 }}
      className={cn(
        baseClasses,
        tier === 'free' ? config.colors.bg : `bg-gradient-to-r ${config.colors.gradient}`,
        tier === 'free' ? config.colors.text : 'text-white',
        className
      )}
    >
      <Icon className={sizeConfig.icon} />
      {showLabel && <span>{config.label}</span>}
    </motion.span>
  );
};

/**
 * Compact tier indicator for use in headers/avatars
 */
interface TierIndicatorProps {
  tier: PremiumTier;
  className?: string;
}

export const TierIndicator: React.FC<TierIndicatorProps> = ({ tier, className }) => {
  if (tier === 'free') return null;
  
  const config = TIER_CONFIG[tier];
  const Icon = config.icon;

  return (
    <motion.div
      initial={{ scale: 0 }}
      animate={{ scale: 1 }}
      className={cn(
        'absolute -top-1 -right-1 p-1 rounded-full',
        `bg-gradient-to-r ${config.colors.gradient}`,
        'text-white shadow-md',
        className
      )}
    >
      <Icon className="w-3 h-3" />
    </motion.div>
  );
};

export default PremiumBadge;
