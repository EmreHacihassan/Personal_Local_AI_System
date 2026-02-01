'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FiCheck, FiCloud, FiCloudOff, FiLoader } from 'react-icons/fi';

interface AutoSaveIndicatorProps {
  content: string;
  onSave: (content: string) => Promise<void>;
  delay?: number; // ms
  enabled?: boolean;
}

type SaveStatus = 'idle' | 'pending' | 'saving' | 'saved' | 'error';

const AutoSaveIndicator: React.FC<AutoSaveIndicatorProps> = ({
  content,
  onSave,
  delay = 2000,
  enabled = true
}) => {
  const [status, setStatus] = useState<SaveStatus>('idle');
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [pendingContent, setPendingContent] = useState<string>(content);

  // Debounced save
  useEffect(() => {
    if (!enabled || content === pendingContent) return;

    setStatus('pending');
    
    const timer = setTimeout(async () => {
      setStatus('saving');
      try {
        await onSave(content);
        setStatus('saved');
        setLastSaved(new Date());
        setPendingContent(content);
        
        // Reset to idle after showing 'saved'
        setTimeout(() => {
          setStatus('idle');
        }, 2000);
      } catch (error) {
        console.error('Auto-save failed:', error);
        setStatus('error');
      }
    }, delay);

    return () => clearTimeout(timer);
  }, [content, delay, enabled, onSave, pendingContent]);

  const formatLastSaved = () => {
    if (!lastSaved) return '';
    const now = new Date();
    const diff = Math.floor((now.getTime() - lastSaved.getTime()) / 1000);
    
    if (diff < 60) return 'Az önce';
    if (diff < 3600) return `${Math.floor(diff / 60)} dk önce`;
    return lastSaved.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' });
  };

  if (!enabled) return null;

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={status}
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        className="flex items-center gap-2 text-xs"
      >
        {status === 'idle' && lastSaved && (
          <span className="flex items-center gap-1.5 text-gray-400">
            <FiCloud className="w-3.5 h-3.5" />
            <span>Kaydedildi {formatLastSaved()}</span>
          </span>
        )}
        
        {status === 'pending' && (
          <span className="flex items-center gap-1.5 text-amber-500">
            <motion.div
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ duration: 0.5, repeat: Infinity }}
            >
              <FiCloud className="w-3.5 h-3.5" />
            </motion.div>
            <span>Değişiklikler algılandı...</span>
          </span>
        )}
        
        {status === 'saving' && (
          <span className="flex items-center gap-1.5 text-blue-500">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
            >
              <FiLoader className="w-3.5 h-3.5" />
            </motion.div>
            <span>Kaydediliyor...</span>
          </span>
        )}
        
        {status === 'saved' && (
          <span className="flex items-center gap-1.5 text-green-500">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', stiffness: 500 }}
            >
              <FiCheck className="w-3.5 h-3.5" />
            </motion.div>
            <span>Kaydedildi!</span>
          </span>
        )}
        
        {status === 'error' && (
          <span className="flex items-center gap-1.5 text-red-500">
            <FiCloudOff className="w-3.5 h-3.5" />
            <span>Kaydetme başarısız</span>
          </span>
        )}
      </motion.div>
    </AnimatePresence>
  );
};

export default AutoSaveIndicator;
