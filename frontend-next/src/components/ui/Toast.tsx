'use client';

/**
 * Toast Notification System
 * 
 * Lightweight toast implementation using existing dependencies (framer-motion + zustand).
 * Usage:
 *   import { toast, ToastContainer } from '@/components/ui/Toast';
 *   
 *   toast.success('Note saved!');
 *   toast.error('Failed to save');
 *   toast.info('Processing...');
 *   toast.warning('Are you sure?');
 */

import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  CheckCircle2, 
  XCircle, 
  AlertCircle, 
  Info, 
  X 
} from 'lucide-react';
import { create } from 'zustand';
import { cn } from '@/lib/utils';

// Toast types
type ToastType = 'success' | 'error' | 'warning' | 'info';

interface Toast {
  id: string;
  type: ToastType;
  message: string;
  duration?: number;
}

// Zustand store for toasts
interface ToastStore {
  toasts: Toast[];
  addToast: (type: ToastType, message: string, duration?: number) => void;
  removeToast: (id: string) => void;
}

const useToastStore = create<ToastStore>((set) => ({
  toasts: [],
  addToast: (type, message, duration = 4000) => {
    const id = Math.random().toString(36).substring(2, 9);
    set((state) => ({
      toasts: [...state.toasts, { id, type, message, duration }]
    }));
    
    // Auto remove after duration
    if (duration > 0) {
      setTimeout(() => {
        set((state) => ({
          toasts: state.toasts.filter((t) => t.id !== id)
        }));
      }, duration);
    }
  },
  removeToast: (id) => {
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id)
    }));
  }
}));

// Toast API for easy usage
export const toast = {
  success: (message: string, duration?: number) => {
    useToastStore.getState().addToast('success', message, duration);
  },
  error: (message: string, duration?: number) => {
    useToastStore.getState().addToast('error', message, duration);
  },
  warning: (message: string, duration?: number) => {
    useToastStore.getState().addToast('warning', message, duration);
  },
  info: (message: string, duration?: number) => {
    useToastStore.getState().addToast('info', message, duration);
  }
};

// Icons and colors for each type
const toastConfig = {
  success: {
    icon: CheckCircle2,
    bg: 'bg-emerald-500/10 border-emerald-500/30',
    iconColor: 'text-emerald-500',
    text: 'text-emerald-700 dark:text-emerald-300'
  },
  error: {
    icon: XCircle,
    bg: 'bg-red-500/10 border-red-500/30',
    iconColor: 'text-red-500',
    text: 'text-red-700 dark:text-red-300'
  },
  warning: {
    icon: AlertCircle,
    bg: 'bg-amber-500/10 border-amber-500/30',
    iconColor: 'text-amber-500',
    text: 'text-amber-700 dark:text-amber-300'
  },
  info: {
    icon: Info,
    bg: 'bg-blue-500/10 border-blue-500/30',
    iconColor: 'text-blue-500',
    text: 'text-blue-700 dark:text-blue-300'
  }
};

// Single toast component
function ToastItem({ toast: t, onRemove }: { toast: Toast; onRemove: () => void }) {
  const config = toastConfig[t.type];
  const Icon = config.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: -20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -20, scale: 0.95 }}
      className={cn(
        "flex items-center gap-3 px-4 py-3 rounded-xl border backdrop-blur-sm shadow-lg min-w-[280px] max-w-[400px]",
        config.bg
      )}
    >
      <Icon className={cn("w-5 h-5 flex-shrink-0", config.iconColor)} />
      <p className={cn("flex-1 text-sm font-medium", config.text)}>
        {t.message}
      </p>
      <button 
        onClick={onRemove}
        className="p-1 rounded-lg hover:bg-black/10 dark:hover:bg-white/10 transition-colors"
      >
        <X className="w-4 h-4 text-muted-foreground" />
      </button>
    </motion.div>
  );
}

// Toast container - add to your layout
export function ToastContainer() {
  const { toasts, removeToast } = useToastStore();

  return (
    <div className="fixed top-4 right-4 z-[100] flex flex-col gap-2 pointer-events-none">
      <AnimatePresence mode="popLayout">
        {toasts.map((t) => (
          <div key={t.id} className="pointer-events-auto">
            <ToastItem toast={t} onRemove={() => removeToast(t.id)} />
          </div>
        ))}
      </AnimatePresence>
    </div>
  );
}

// Hook for component-level usage
export function useToast() {
  const { addToast, removeToast } = useToastStore();
  
  return {
    success: (message: string, duration?: number) => addToast('success', message, duration),
    error: (message: string, duration?: number) => addToast('error', message, duration),
    warning: (message: string, duration?: number) => addToast('warning', message, duration),
    info: (message: string, duration?: number) => addToast('info', message, duration),
    dismiss: removeToast
  };
}
