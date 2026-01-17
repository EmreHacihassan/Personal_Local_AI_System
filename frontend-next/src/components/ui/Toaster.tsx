'use client';

import { useState, useEffect, createContext, useContext } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, XCircle, AlertCircle, Info, X } from 'lucide-react';
import { cn } from '@/lib/utils';

type ToastType = 'success' | 'error' | 'warning' | 'info';

interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  duration?: number;
}

interface ToastContextValue {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    return {
      toast: (options: Omit<Toast, 'id'>) => {
        console.log('Toast:', options);
      }
    };
  }
  return {
    toast: context.addToast
  };
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = (toast: Omit<Toast, 'id'>) => {
    const id = Math.random().toString(36).substr(2, 9);
    setToasts((prev) => [...prev, { ...toast, id }]);

    // Auto remove
    setTimeout(() => {
      removeToast(id);
    }, toast.duration || 5000);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
      {children}
    </ToastContext.Provider>
  );
}

const icons = {
  success: CheckCircle2,
  error: XCircle,
  warning: AlertCircle,
  info: Info,
};

const colors = {
  success: 'bg-green-500',
  error: 'bg-red-500',
  warning: 'bg-yellow-500',
  info: 'bg-blue-500',
};

export function Toaster() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  // Global toast event listener
  useEffect(() => {
    const handleToast = (e: Event) => {
      const customEvent = e as CustomEvent<Omit<Toast, 'id'>>;
      const id = Math.random().toString(36).substr(2, 9);
      const toast = { ...customEvent.detail, id };
      setToasts((prev) => [...prev, toast]);

      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, customEvent.detail.duration || 5000);
    };

    window.addEventListener('toast', handleToast);
    return () => window.removeEventListener('toast', handleToast);
  }, []);

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  return (
    <div className="fixed bottom-4 right-4 z-[9999] flex flex-col gap-2">
      <AnimatePresence mode="popLayout">
        {toasts.map((toast) => {
          const Icon = icons[toast.type];
          return (
            <motion.div
              key={toast.id}
              initial={{ opacity: 0, x: 100, scale: 0.9 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 100, scale: 0.9 }}
              className={cn(
                "flex items-start gap-3 min-w-[300px] max-w-[400px] p-4 rounded-xl shadow-2xl bg-card border border-border"
              )}
            >
              <div className={cn(
                "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 text-white",
                colors[toast.type]
              )}>
                <Icon className="w-4 h-4" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-sm">{toast.title}</p>
                {toast.message && (
                  <p className="text-xs text-muted-foreground mt-1">{toast.message}</p>
                )}
              </div>
              <button
                onClick={() => removeToast(toast.id)}
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}

// Global toast function
export function toast(options: Omit<Toast, 'id'>) {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('toast', { detail: options }));
  }
}
