'use client';

import { cn } from '@/lib/utils';

interface SkeletonProps {
  className?: string;
}

/**
 * Base skeleton component with shimmer animation
 */
export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-md bg-muted",
        className
      )}
    />
  );
}

/**
 * Skeleton for text content
 */
export function SkeletonText({ 
  lines = 3, 
  className 
}: { 
  lines?: number; 
  className?: string;
}) {
  return (
    <div className={cn("space-y-2", className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          className={cn(
            "h-4",
            i === lines - 1 ? "w-3/4" : "w-full"
          )}
        />
      ))}
    </div>
  );
}

/**
 * Skeleton for avatar
 */
export function SkeletonAvatar({ 
  size = 'md',
  className 
}: { 
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}) {
  const sizeClasses = {
    sm: 'w-8 h-8',
    md: 'w-10 h-10',
    lg: 'w-16 h-16',
  };

  return (
    <Skeleton 
      className={cn(
        "rounded-full",
        sizeClasses[size],
        className
      )} 
    />
  );
}

/**
 * Skeleton for cards
 */
export function SkeletonCard({ className }: { className?: string }) {
  return (
    <div className={cn("p-4 border border-border rounded-xl space-y-4", className)}>
      <div className="flex items-center gap-4">
        <SkeletonAvatar />
        <div className="space-y-2 flex-1">
          <Skeleton className="h-4 w-1/3" />
          <Skeleton className="h-3 w-1/4" />
        </div>
      </div>
      <SkeletonText lines={2} />
    </div>
  );
}

/**
 * Skeleton for message bubbles in chat
 */
export function SkeletonMessage({ isUser = false }: { isUser?: boolean }) {
  return (
    <div className={cn("flex gap-3", isUser ? "flex-row-reverse" : "flex-row")}>
      <SkeletonAvatar size="sm" />
      <div className={cn(
        "space-y-2 flex-1 max-w-[80%]",
        isUser ? "items-end" : "items-start"
      )}>
        <Skeleton className={cn("h-20 rounded-2xl", isUser ? "w-1/2 ml-auto" : "w-3/4")} />
      </div>
    </div>
  );
}

/**
 * Skeleton for stat cards in dashboard
 */
export function SkeletonStatCard() {
  return (
    <div className="p-5 border border-border rounded-2xl space-y-4">
      <div className="flex items-start justify-between">
        <Skeleton className="w-12 h-12 rounded-xl" />
        <Skeleton className="w-16 h-6 rounded-full" />
      </div>
      <div className="space-y-2">
        <Skeleton className="h-8 w-1/2" />
        <Skeleton className="h-4 w-2/3" />
      </div>
    </div>
  );
}

/**
 * Skeleton for document list items
 */
export function SkeletonDocumentItem() {
  return (
    <div className="flex items-center gap-4 p-4 border border-border rounded-xl">
      <Skeleton className="w-12 h-12 rounded-xl" />
      <div className="flex-1 space-y-2">
        <Skeleton className="h-4 w-1/3" />
        <Skeleton className="h-3 w-1/4" />
      </div>
      <div className="flex gap-2">
        <Skeleton className="w-8 h-8 rounded-lg" />
        <Skeleton className="w-8 h-8 rounded-lg" />
      </div>
    </div>
  );
}

/**
 * Skeleton for sidebar navigation
 */
export function SkeletonSidebar() {
  return (
    <div className="w-64 h-full border-r border-border p-4 space-y-4">
      {/* Logo */}
      <div className="flex items-center gap-3 mb-8">
        <Skeleton className="w-10 h-10 rounded-xl" />
        <div className="space-y-1 flex-1">
          <Skeleton className="h-4 w-2/3" />
          <Skeleton className="h-3 w-1/3" />
        </div>
      </div>
      
      {/* Nav items */}
      {Array.from({ length: 7 }).map((_, i) => (
        <div key={i} className="flex items-center gap-3">
          <Skeleton className="w-5 h-5" />
          <Skeleton className="h-4 w-24" />
        </div>
      ))}
    </div>
  );
}

/**
 * Full page loading skeleton
 */
export function SkeletonPage() {
  return (
    <div className="flex h-screen">
      <SkeletonSidebar />
      <div className="flex-1 p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Skeleton className="w-10 h-10 rounded-xl" />
            <div className="space-y-1">
              <Skeleton className="h-5 w-32" />
              <Skeleton className="h-3 w-24" />
            </div>
          </div>
          <Skeleton className="w-32 h-10 rounded-xl" />
        </div>
        
        {/* Content grid */}
        <div className="grid grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <SkeletonStatCard key={i} />
          ))}
        </div>
        
        {/* Main content */}
        <div className="grid grid-cols-2 gap-6">
          <SkeletonCard />
          <SkeletonCard />
        </div>
      </div>
    </div>
  );
}
