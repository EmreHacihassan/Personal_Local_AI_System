'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { FiClock, FiType, FiFileText, FiBook } from 'react-icons/fi';

interface WordCounterProps {
  content: string;
  variant?: 'compact' | 'detailed';
  className?: string;
}

const WordCounter: React.FC<WordCounterProps> = ({
  content,
  variant = 'compact',
  className = ''
}) => {
  // Calculate stats
  const words = content.trim().split(/\s+/).filter(w => w.length > 0);
  const wordCount = words.length;
  const charCount = content.length;
  const charNoSpaces = content.replace(/\s/g, '').length;
  const sentences = content.split(/[.!?]+/).filter(s => s.trim().length > 0).length;
  const paragraphs = content.split(/\n\n+/).filter(p => p.trim().length > 0).length;
  
  // Reading time (average 200 words per minute)
  const readingTimeMinutes = Math.ceil(wordCount / 200);
  const readingTimeDisplay = readingTimeMinutes < 1 ? '<1 dk' : `${readingTimeMinutes} dk`;
  
  // Speaking time (average 150 words per minute)
  const speakingTimeMinutes = Math.ceil(wordCount / 150);

  if (variant === 'compact') {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className={`flex items-center gap-3 text-xs text-gray-500 ${className}`}
      >
        <span className="flex items-center gap-1">
          <FiType className="w-3 h-3" />
          {wordCount} kelime
        </span>
        <span className="text-gray-300 dark:text-gray-600">•</span>
        <span className="flex items-center gap-1">
          <FiClock className="w-3 h-3" />
          {readingTimeDisplay}
        </span>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`p-4 bg-gray-50 dark:bg-gray-800 rounded-xl space-y-3 ${className}`}
    >
      <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 flex items-center gap-2">
        <FiFileText className="w-4 h-4" />
        Metin İstatistikleri
      </h4>
      
      <div className="grid grid-cols-2 gap-3">
        <div className="p-3 bg-white dark:bg-gray-700 rounded-lg">
          <div className="text-2xl font-bold text-gray-900 dark:text-white">
            {wordCount.toLocaleString()}
          </div>
          <div className="text-xs text-gray-500">Kelime</div>
        </div>
        
        <div className="p-3 bg-white dark:bg-gray-700 rounded-lg">
          <div className="text-2xl font-bold text-gray-900 dark:text-white">
            {charCount.toLocaleString()}
          </div>
          <div className="text-xs text-gray-500">Karakter</div>
        </div>
        
        <div className="p-3 bg-white dark:bg-gray-700 rounded-lg">
          <div className="text-2xl font-bold text-gray-900 dark:text-white">
            {sentences}
          </div>
          <div className="text-xs text-gray-500">Cümle</div>
        </div>
        
        <div className="p-3 bg-white dark:bg-gray-700 rounded-lg">
          <div className="text-2xl font-bold text-gray-900 dark:text-white">
            {paragraphs}
          </div>
          <div className="text-xs text-gray-500">Paragraf</div>
        </div>
      </div>

      <div className="flex items-center justify-between pt-2 border-t border-gray-200 dark:border-gray-600">
        <div className="flex items-center gap-2 text-sm">
          <FiClock className="w-4 h-4 text-blue-500" />
          <span className="text-gray-600 dark:text-gray-400">
            Okuma: <strong className="text-gray-900 dark:text-white">{readingTimeMinutes} dk</strong>
          </span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <FiBook className="w-4 h-4 text-green-500" />
          <span className="text-gray-600 dark:text-gray-400">
            Konuşma: <strong className="text-gray-900 dark:text-white">{speakingTimeMinutes} dk</strong>
          </span>
        </div>
      </div>
    </motion.div>
  );
};

export default WordCounter;
