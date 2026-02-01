'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';

interface ReadingProgressBarProps {
  containerRef: React.RefObject<HTMLElement>;
  color?: string;
  height?: number;
  showPercentage?: boolean;
  position?: 'top' | 'bottom';
}

const ReadingProgressBar: React.FC<ReadingProgressBarProps> = ({
  containerRef,
  color = 'from-purple-500 to-indigo-500',
  height = 3,
  showPercentage = false,
  position = 'top'
}) => {
  const [progress, setProgress] = useState(0);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const calculateProgress = () => {
      const scrollTop = container.scrollTop;
      const scrollHeight = container.scrollHeight - container.clientHeight;
      
      if (scrollHeight <= 0) {
        setProgress(0);
        setIsVisible(false);
        return;
      }
      
      const currentProgress = Math.min(100, Math.max(0, (scrollTop / scrollHeight) * 100));
      setProgress(currentProgress);
      setIsVisible(scrollTop > 50);
    };

    calculateProgress();
    container.addEventListener('scroll', calculateProgress);
    
    // Recalculate on resize
    const resizeObserver = new ResizeObserver(calculateProgress);
    resizeObserver.observe(container);

    return () => {
      container.removeEventListener('scroll', calculateProgress);
      resizeObserver.disconnect();
    };
  }, [containerRef]);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: isVisible ? 1 : 0 }}
      className={`fixed left-0 right-0 z-40 ${position === 'top' ? 'top-0' : 'bottom-0'}`}
      style={{ height: `${height}px` }}
    >
      {/* Background */}
      <div className="absolute inset-0 bg-gray-200/50 dark:bg-gray-700/50" />
      
      {/* Progress */}
      <motion.div
        className={`h-full bg-gradient-to-r ${color} shadow-lg`}
        initial={{ width: 0 }}
        animate={{ width: `${progress}%` }}
        transition={{ duration: 0.1 }}
      />
      
      {/* Percentage Badge */}
      {showPercentage && progress > 0 && (
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          className={`absolute ${position === 'top' ? 'top-2' : 'bottom-2'} right-4 px-2 py-0.5 bg-black/70 text-white rounded text-xs font-mono`}
          style={{ marginTop: position === 'top' ? height : 0 }}
        >
          {Math.round(progress)}%
        </motion.div>
      )}
    </motion.div>
  );
};

export default ReadingProgressBar;
