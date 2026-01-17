'use client';

import { useState, useEffect, useCallback, useRef } from 'react';

interface UseApiOptions<T> {
  /** Initial data before fetch completes */
  initialData?: T;
  /** Cache time in milliseconds (default: 5 minutes) */
  cacheTime?: number;
  /** Stale time in milliseconds (default: 30 seconds) */
  staleTime?: number;
  /** Whether to fetch on mount (default: true) */
  enabled?: boolean;
  /** Retry count on failure (default: 3) */
  retryCount?: number;
  /** Dependencies that trigger refetch when changed */
  deps?: unknown[];
  /** Callback on success */
  onSuccess?: (data: T) => void;
  /** Callback on error */
  onError?: (error: Error) => void;
}

interface UseApiResult<T> {
  /** The fetched data */
  data: T | undefined;
  /** Whether the request is loading */
  isLoading: boolean;
  /** Whether initial data is being fetched */
  isFetching: boolean;
  /** Any error that occurred */
  error: Error | null;
  /** Manually trigger a refetch */
  refetch: () => Promise<void>;
  /** Whether data is stale */
  isStale: boolean;
}

// Simple in-memory cache
const cache = new Map<string, { data: unknown; timestamp: number }>();

/**
 * Custom hook for API data fetching with caching, loading states, and error handling
 */
export function useApi<T>(
  key: string,
  fetcher: () => Promise<T>,
  options: UseApiOptions<T> = {}
): UseApiResult<T> {
  const {
    initialData,
    cacheTime = 5 * 60 * 1000, // 5 minutes
    staleTime = 30 * 1000, // 30 seconds
    enabled = true,
    retryCount = 3,
    deps = [],
    onSuccess,
    onError,
  } = options;

  const [data, setData] = useState<T | undefined>(() => {
    const cached = cache.get(key);
    if (cached && Date.now() - cached.timestamp < cacheTime) {
      return cached.data as T;
    }
    return initialData;
  });
  
  const [isLoading, setIsLoading] = useState(!data);
  const [isFetching, setIsFetching] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [isStale, setIsStale] = useState(false);

  const mountedRef = useRef(true);
  const retryCountRef = useRef(0);

  const fetchData = useCallback(async (isRetry = false) => {
    if (!enabled) return;

    // Check cache first
    const cached = cache.get(key);
    if (cached && !isRetry) {
      const age = Date.now() - cached.timestamp;
      
      // If cache is fresh, use it
      if (age < staleTime) {
        setData(cached.data as T);
        setIsLoading(false);
        setIsStale(false);
        return;
      }
      
      // If cache is stale but not expired, use it but refetch
      if (age < cacheTime) {
        setData(cached.data as T);
        setIsStale(true);
      }
    }

    setIsFetching(true);
    setError(null);

    try {
      const result = await fetcher();
      
      if (!mountedRef.current) return;

      // Update cache
      cache.set(key, { data: result, timestamp: Date.now() });
      
      setData(result);
      setIsStale(false);
      setError(null);
      retryCountRef.current = 0;
      
      onSuccess?.(result);
    } catch (err) {
      if (!mountedRef.current) return;

      const error = err instanceof Error ? err : new Error('Unknown error');
      
      // Retry logic
      if (retryCountRef.current < retryCount) {
        retryCountRef.current++;
        // Exponential backoff
        setTimeout(() => fetchData(true), 1000 * Math.pow(2, retryCountRef.current));
        return;
      }

      setError(error);
      onError?.(error);
    } finally {
      if (mountedRef.current) {
        setIsLoading(false);
        setIsFetching(false);
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, enabled, staleTime, cacheTime, retryCount, ...deps]);

  const refetch = useCallback(async () => {
    retryCountRef.current = 0;
    cache.delete(key);
    await fetchData();
  }, [key, fetchData]);

  useEffect(() => {
    mountedRef.current = true;
    fetchData();
    
    return () => {
      mountedRef.current = false;
    };
  }, [fetchData]);

  // Periodic stale check
  useEffect(() => {
    const interval = setInterval(() => {
      const cached = cache.get(key);
      if (cached) {
        const age = Date.now() - cached.timestamp;
        setIsStale(age > staleTime);
      }
    }, staleTime);

    return () => clearInterval(interval);
  }, [key, staleTime]);

  return {
    data,
    isLoading,
    isFetching,
    error,
    refetch,
    isStale,
  };
}

/**
 * Hook for mutations (POST, PUT, DELETE operations)
 */
interface UseMutationOptions<T, V> {
  onSuccess?: (data: T, variables: V) => void;
  onError?: (error: Error, variables: V) => void;
  /** Cache keys to invalidate on success */
  invalidateKeys?: string[];
}

interface UseMutationResult<T, V> {
  mutate: (variables: V) => Promise<T | undefined>;
  data: T | undefined;
  isLoading: boolean;
  error: Error | null;
  reset: () => void;
}

export function useMutation<T, V = void>(
  mutationFn: (variables: V) => Promise<T>,
  options: UseMutationOptions<T, V> = {}
): UseMutationResult<T, V> {
  const { onSuccess, onError, invalidateKeys = [] } = options;

  const [data, setData] = useState<T | undefined>(undefined);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const mutate = useCallback(async (variables: V): Promise<T | undefined> => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await mutationFn(variables);
      setData(result);
      
      // Invalidate specified cache keys
      invalidateKeys.forEach(key => cache.delete(key));
      
      onSuccess?.(result, variables);
      return result;
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Unknown error');
      setError(error);
      onError?.(error, variables);
      return undefined;
    } finally {
      setIsLoading(false);
    }
  }, [mutationFn, onSuccess, onError, invalidateKeys]);

  const reset = useCallback(() => {
    setData(undefined);
    setError(null);
    setIsLoading(false);
  }, []);

  return {
    mutate,
    data,
    isLoading,
    error,
    reset,
  };
}

/**
 * Clear all cached data
 */
export function clearApiCache(): void {
  cache.clear();
}

/**
 * Clear specific cache key
 */
export function invalidateCache(key: string): void {
  cache.delete(key);
}
