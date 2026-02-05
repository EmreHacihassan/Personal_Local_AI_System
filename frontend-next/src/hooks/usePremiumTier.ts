/**
 * usePremiumTier Hook
 * ====================
 * 
 * Premium tier ve kullanım yönetimi için React hook.
 * 
 * Kullanım:
 * ```tsx
 * const { tier, hasFeature, usage, isLoading, refetch } = usePremiumTier();
 * 
 * if (!hasFeature('web_search')) {
 *   return <UpgradePrompt feature="web_search" />;
 * }
 * ```
 */

import { useState, useEffect, useCallback, useMemo } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

// Types
export type PremiumTier = 'free' | 'pro' | 'enterprise';

export type PremiumFeature = 
  | 'web_search'
  | 'voice_input'
  | 'voice_output'
  | 'vision'
  | 'knowledge_graph'
  | 'deep_scholar'
  | 'custom_models'
  | 'priority_queue'
  | 'analytics'
  | 'export_pdf'
  | 'multi_language'
  | 'auto_tagging'
  | 'semantic_rerank'
  | 'computer_use'
  | 'mcp_tools';

export interface TierLimits {
  requests_per_day: number;
  tokens_per_day: number;
  max_sessions: number;
  max_documents: number;
  max_file_size_mb: number;
  max_document_pages: number;
}

export interface UsageStats {
  requests_today: number;
  tokens_today: number;
  sessions: number;
  documents: number;
}

export interface TierInfo {
  tier: PremiumTier;
  tierDisplay: string;
  usage: UsageStats;
  limits: TierLimits;
  features: Record<string, boolean>;
  percentages: {
    requests: number;
    tokens: number;
  };
}

export interface UsePremiumTierOptions {
  userId?: string;
  autoRefresh?: boolean;
  refreshInterval?: number; // ms
}

export interface UsePremiumTierResult {
  // State
  tier: PremiumTier;
  tierDisplay: string;
  usage: UsageStats | null;
  limits: TierLimits | null;
  features: Record<string, boolean>;
  isLoading: boolean;
  error: string | null;
  
  // Computed
  isPremium: boolean;
  isEnterprise: boolean;
  usagePercent: { requests: number; tokens: number };
  isNearLimit: boolean;
  isAtLimit: boolean;
  
  // Methods
  hasFeature: (feature: PremiumFeature) => boolean;
  checkLimit: (limitName: keyof TierLimits, currentValue: number) => boolean;
  refetch: () => Promise<void>;
}

export function usePremiumTier(options: UsePremiumTierOptions = {}): UsePremiumTierResult {
  const {
    userId = 'default-user',
    autoRefresh = true,
    refreshInterval = 5 * 60 * 1000, // 5 minutes
  } = options;

  // State
  const [tier, setTier] = useState<PremiumTier>('free');
  const [tierDisplay, setTierDisplay] = useState('Free');
  const [usage, setUsage] = useState<UsageStats | null>(null);
  const [limits, setLimits] = useState<TierLimits | null>(null);
  const [features, setFeatures] = useState<Record<string, boolean>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch tier data
  const fetchTierData = useCallback(async () => {
    try {
      setError(null);
      
      const response = await fetch(`${API_BASE}/api/tiers/user/${userId}/usage`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch tier data: ${response.status}`);
      }
      
      const data = await response.json();
      
      setTier(data.tier || 'free');
      setTierDisplay(data.tier?.charAt(0).toUpperCase() + data.tier?.slice(1) || 'Free');
      setUsage(data.usage || null);
      setLimits(data.limits || null);
      setFeatures(data.features || {});
    } catch (err) {
      console.error('Failed to fetch tier data:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  }, [userId]);

  // Initial fetch and auto refresh
  useEffect(() => {
    fetchTierData();
    
    if (autoRefresh) {
      const interval = setInterval(fetchTierData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [fetchTierData, autoRefresh, refreshInterval]);

  // Computed values
  const isPremium = useMemo(() => tier !== 'free', [tier]);
  const isEnterprise = useMemo(() => tier === 'enterprise', [tier]);

  const usagePercent = useMemo(() => {
    if (!usage || !limits) {
      return { requests: 0, tokens: 0 };
    }
    return {
      requests: Math.min(100, Math.round((usage.requests_today / limits.requests_per_day) * 100)),
      tokens: Math.min(100, Math.round((usage.tokens_today / limits.tokens_per_day) * 100)),
    };
  }, [usage, limits]);

  const isNearLimit = useMemo(() => 
    usagePercent.requests >= 80 || usagePercent.tokens >= 80,
    [usagePercent]
  );

  const isAtLimit = useMemo(() => 
    usagePercent.requests >= 95 || usagePercent.tokens >= 95,
    [usagePercent]
  );

  // Methods
  const hasFeature = useCallback((feature: PremiumFeature): boolean => {
    return features[feature] ?? false;
  }, [features]);

  const checkLimit = useCallback((limitName: keyof TierLimits, currentValue: number): boolean => {
    if (!limits) return true;
    const limit = limits[limitName];
    return currentValue < limit;
  }, [limits]);

  const refetch = useCallback(async () => {
    setIsLoading(true);
    await fetchTierData();
  }, [fetchTierData]);

  return {
    // State
    tier,
    tierDisplay,
    usage,
    limits,
    features,
    isLoading,
    error,
    
    // Computed
    isPremium,
    isEnterprise,
    usagePercent,
    isNearLimit,
    isAtLimit,
    
    // Methods
    hasFeature,
    checkLimit,
    refetch,
  };
}

/**
 * Feature gating için yardımcı hook.
 * 
 * Kullanım:
 * ```tsx
 * const { canAccess, showUpgradePrompt, RequiredTier } = useFeatureGate('web_search');
 * 
 * if (!canAccess) {
 *   return <RequiredTier message="Web search için Pro plana yükseltin" />;
 * }
 * ```
 */
export function useFeatureGate(feature: PremiumFeature) {
  const { hasFeature, tier, isPremium } = usePremiumTier();
  
  const canAccess = hasFeature(feature);
  const showUpgradePrompt = !canAccess;
  
  // Feature minimum tier mapping
  const featureTiers: Record<PremiumFeature, PremiumTier> = {
    web_search: 'pro',
    voice_input: 'pro',
    voice_output: 'pro',
    vision: 'pro',
    knowledge_graph: 'pro',
    deep_scholar: 'pro',
    custom_models: 'enterprise',
    priority_queue: 'enterprise',
    analytics: 'free',
    export_pdf: 'pro',
    multi_language: 'pro',
    auto_tagging: 'free',
    semantic_rerank: 'pro',
    computer_use: 'enterprise',
    mcp_tools: 'pro',
  };
  
  const requiredTier = featureTiers[feature] || 'pro';
  
  return {
    canAccess,
    showUpgradePrompt,
    currentTier: tier,
    requiredTier,
    isPremium,
  };
}

export default usePremiumTier;
