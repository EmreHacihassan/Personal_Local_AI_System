'use client';

import React, { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';
import { PremiumTier, PremiumFeature, UsageStats, TierLimits } from '@/hooks/usePremiumTier';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

interface PremiumContextValue {
  // User identification
  userId: string;
  setUserId: (id: string) => void;
  
  // Tier state
  tier: PremiumTier;
  tierDisplay: string;
  usage: UsageStats | null;
  limits: TierLimits | null;
  features: Record<string, boolean>;
  
  // Loading & Error state
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
  trackUsage: (requests?: number, tokens?: number) => Promise<void>;
  upgradeTier: (newTier: PremiumTier) => Promise<boolean>;
}

const PremiumContext = createContext<PremiumContextValue | null>(null);

interface PremiumProviderProps {
  children: ReactNode;
  defaultUserId?: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export const PremiumProvider: React.FC<PremiumProviderProps> = ({
  children,
  defaultUserId = 'default-user',
  autoRefresh = true,
  refreshInterval = 5 * 60 * 1000, // 5 minutes
}) => {
  // User ID state
  const [userId, setUserIdState] = useState(defaultUserId);
  
  // Tier state
  const [tier, setTier] = useState<PremiumTier>('free');
  const [tierDisplay, setTierDisplay] = useState('Free');
  const [usage, setUsage] = useState<UsageStats | null>(null);
  const [limits, setLimits] = useState<TierLimits | null>(null);
  const [features, setFeatures] = useState<Record<string, boolean>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load userId from localStorage on mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedUserId = localStorage.getItem('premium_user_id');
      if (savedUserId) {
        setUserIdState(savedUserId);
      }
    }
  }, []);

  // Save userId to localStorage
  const setUserId = useCallback((id: string) => {
    setUserIdState(id);
    if (typeof window !== 'undefined') {
      localStorage.setItem('premium_user_id', id);
    }
  }, []);

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
    setIsLoading(true);
    fetchTierData();
    
    if (autoRefresh) {
      const interval = setInterval(fetchTierData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [fetchTierData, autoRefresh, refreshInterval]);

  // Computed values
  const isPremium = tier !== 'free';
  const isEnterprise = tier === 'enterprise';

  const usagePercent = React.useMemo(() => {
    if (!usage || !limits) {
      return { requests: 0, tokens: 0 };
    }
    return {
      requests: Math.min(100, Math.round((usage.requests_today / limits.requests_per_day) * 100)),
      tokens: Math.min(100, Math.round((usage.tokens_today / limits.tokens_per_day) * 100)),
    };
  }, [usage, limits]);

  const isNearLimit = usagePercent.requests >= 80 || usagePercent.tokens >= 80;
  const isAtLimit = usagePercent.requests >= 95 || usagePercent.tokens >= 95;

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

  const trackUsage = useCallback(async (requests: number = 1, tokens: number = 0) => {
    try {
      await fetch(`${API_BASE}/api/tiers/user/${userId}/usage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ requests, tokens }),
      });
      // Optionally refetch to update local state
      // await fetchTierData();
    } catch (err) {
      console.error('Failed to track usage:', err);
    }
  }, [userId]);

  const upgradeTier = useCallback(async (newTier: PremiumTier): Promise<boolean> => {
    try {
      const response = await fetch(`${API_BASE}/api/tiers/user/${userId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tier: newTier }),
      });
      
      if (response.ok) {
        await fetchTierData();
        return true;
      }
      return false;
    } catch (err) {
      console.error('Failed to upgrade tier:', err);
      return false;
    }
  }, [userId, fetchTierData]);

  const value: PremiumContextValue = {
    userId,
    setUserId,
    tier,
    tierDisplay,
    usage,
    limits,
    features,
    isLoading,
    error,
    isPremium,
    isEnterprise,
    usagePercent,
    isNearLimit,
    isAtLimit,
    hasFeature,
    checkLimit,
    refetch,
    trackUsage,
    upgradeTier,
  };

  return (
    <PremiumContext.Provider value={value}>
      {children}
    </PremiumContext.Provider>
  );
};

/**
 * Hook to access premium context
 * Must be used within PremiumProvider
 */
export function usePremiumContext(): PremiumContextValue {
  const context = useContext(PremiumContext);
  if (!context) {
    throw new Error('usePremiumContext must be used within a PremiumProvider');
  }
  return context;
}

/**
 * HOC to wrap components that need premium tier
 */
export function withPremium<P extends object>(
  WrappedComponent: React.ComponentType<P & { premium: PremiumContextValue }>
): React.FC<P> {
  return function WithPremiumComponent(props: P) {
    const premium = usePremiumContext();
    return <WrappedComponent {...props} premium={premium} />;
  };
}

export default PremiumProvider;
