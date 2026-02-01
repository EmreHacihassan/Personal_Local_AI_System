'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FiZap, FiRefreshCw, FiCheck, FiX, FiEdit3, FiType,
  FiAlignLeft, FiBookOpen, FiMessageSquare, FiList,
  FiChevronRight, FiSparkles, FiPenTool, FiFileText
} from 'react-icons/fi';

interface AIWritingAssistantProps {
  isOpen: boolean;
  onClose: () => void;
  currentText: string;
  selectedText?: string;
  onApplySuggestion: (text: string) => void;
  noteId?: string;
}

interface Suggestion {
  id: string;
  type: 'improve' | 'expand' | 'summarize' | 'rewrite' | 'continue' | 'fix';
  label: string;
  preview: string;
  fullText: string;
}

const AIWritingAssistant: React.FC<AIWritingAssistantProps> = ({
  isOpen,
  onClose,
  currentText,
  selectedText,
  onApplySuggestion,
  noteId
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [activeTab, setActiveTab] = useState<'quick' | 'improve' | 'generate'>('quick');
  const [customPrompt, setCustomPrompt] = useState('');

  // Quick Actions
  const quickActions = [
    { id: 'improve', icon: <FiEdit3 />, label: 'İyileştir', description: 'Yazımı daha akıcı yap' },
    { id: 'expand', icon: <FiAlignLeft />, label: 'Genişlet', description: 'Daha detaylı hale getir' },
    { id: 'summarize', icon: <FiFileText />, label: 'Özetle', description: 'Kısa ve öz hale getir' },
    { id: 'rewrite', icon: <FiRefreshCw />, label: 'Yeniden Yaz', description: 'Farklı bir tarzda yaz' },
    { id: 'continue', icon: <FiChevronRight />, label: 'Devam Et', description: 'Metni devam ettir' },
    { id: 'fix', icon: <FiCheck />, label: 'Düzelt', description: 'Yazım hatalarını düzelt' },
  ];

  // Writing Style Options
  const writingStyles = [
    { id: 'formal', label: 'Resmi', emoji: '👔' },
    { id: 'casual', label: 'Günlük', emoji: '😊' },
    { id: 'academic', label: 'Akademik', emoji: '🎓' },
    { id: 'creative', label: 'Yaratıcı', emoji: '🎨' },
    { id: 'technical', label: 'Teknik', emoji: '⚙️' },
    { id: 'storytelling', label: 'Hikaye', emoji: '📖' },
  ];

  // Content Generation Templates
  const generateTemplates = [
    { id: 'outline', icon: <FiList />, label: 'Taslak Oluştur', prompt: 'Bu konu için bir taslak oluştur' },
    { id: 'brainstorm', icon: <FiSparkles />, label: 'Beyin Fırtınası', prompt: 'Bu konuyla ilgili fikirler üret' },
    { id: 'intro', icon: <FiBookOpen />, label: 'Giriş Yaz', prompt: 'Etkileyici bir giriş paragrafı yaz' },
    { id: 'conclusion', icon: <FiPenTool />, label: 'Sonuç Yaz', prompt: 'Güçlü bir sonuç paragrafı yaz' },
    { id: 'questions', icon: <FiMessageSquare />, label: 'Sorular Üret', prompt: 'Bu konuyla ilgili sorular oluştur' },
  ];

  // Handle quick action
  const handleQuickAction = async (actionId: string) => {
    setIsLoading(true);
    
    // Simulate API call - in real implementation, this would call the backend
    try {
      const textToProcess = selectedText || currentText.slice(-500);
      
      // Mock AI response based on action
      await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 500));
      
      const mockSuggestions: Suggestion[] = [];
      
      if (actionId === 'improve') {
        mockSuggestions.push({
          id: '1',
          type: 'improve',
          label: 'Daha Akıcı Versiyon',
          preview: textToProcess.slice(0, 100) + '...',
          fullText: `${textToProcess}\n\n[AI tarafından iyileştirilmiş versiyon - Backend bağlantısı gerekli]`
        });
      } else if (actionId === 'expand') {
        mockSuggestions.push({
          id: '1',
          type: 'expand',
          label: 'Genişletilmiş Versiyon',
          preview: 'Metin genişletildi...',
          fullText: `${textToProcess}\n\nEk detaylar:\n- [AI ekleme 1]\n- [AI ekleme 2]\n- [AI ekleme 3]`
        });
      } else if (actionId === 'summarize') {
        mockSuggestions.push({
          id: '1',
          type: 'summarize',
          label: 'Özet',
          preview: 'Kısa özet oluşturuldu...',
          fullText: `Özet: ${textToProcess.slice(0, 150)}...`
        });
      } else if (actionId === 'continue') {
        mockSuggestions.push({
          id: '1',
          type: 'continue',
          label: 'Devam Önerisi',
          preview: 'Metin devam ettirildi...',
          fullText: `${textToProcess}\n\n[AI tarafından eklenen devam metni...]`
        });
      } else if (actionId === 'fix') {
        mockSuggestions.push({
          id: '1',
          type: 'fix',
          label: 'Düzeltilmiş Versiyon',
          preview: 'Yazım hataları düzeltildi...',
          fullText: textToProcess.replace(/\s+/g, ' ').trim()
        });
      } else if (actionId === 'rewrite') {
        mockSuggestions.push({
          id: '1',
          type: 'rewrite',
          label: 'Alternatif Yazım',
          preview: 'Farklı bir tarzda yazıldı...',
          fullText: `[Yeniden yazılmış versiyon]\n\n${textToProcess}`
        });
      }
      
      setSuggestions(mockSuggestions);
    } catch (error) {
      console.error('AI suggestion error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle custom prompt
  const handleCustomPrompt = async () => {
    if (!customPrompt.trim()) return;
    setIsLoading(true);
    
    try {
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      setSuggestions([{
        id: 'custom',
        type: 'improve',
        label: 'Özel İstek Sonucu',
        preview: `"${customPrompt}" için oluşturuldu...`,
        fullText: `[AI yanıtı: ${customPrompt}]\n\n${currentText.slice(0, 200)}...`
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: 20 }}
        className="fixed right-4 top-24 bottom-24 w-96 z-50"
      >
        <div className="h-full bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 flex flex-col overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-4 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-purple-500/10 to-indigo-500/10">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-r from-purple-500 to-indigo-500 rounded-xl text-white">
                <FiZap className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-gray-900 dark:text-white">AI Yazma Asistanı</h3>
                <p className="text-xs text-gray-500">Akıllı yazma önerileri</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            >
              <FiX className="w-5 h-5 text-gray-500" />
            </button>
          </div>

          {/* Selected Text Preview */}
          {selectedText && (
            <div className="mx-4 mt-4 p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
              <div className="text-xs text-purple-600 dark:text-purple-400 mb-1 font-medium">
                Seçili metin:
              </div>
              <div className="text-sm text-gray-700 dark:text-gray-300 line-clamp-2">
                "{selectedText}"
              </div>
            </div>
          )}

          {/* Tabs */}
          <div className="flex gap-1 px-4 mt-4">
            {[
              { id: 'quick', label: 'Hızlı İşlemler' },
              { id: 'improve', label: 'Stil' },
              { id: 'generate', label: 'Üret' },
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as typeof activeTab)}
                className={`flex-1 py-2 px-3 text-sm font-medium rounded-lg transition-all ${
                  activeTab === tab.id
                    ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300'
                    : 'text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-4">
            {activeTab === 'quick' && (
              <div className="grid grid-cols-2 gap-2">
                {quickActions.map(action => (
                  <motion.button
                    key={action.id}
                    onClick={() => handleQuickAction(action.id)}
                    disabled={isLoading}
                    className="flex flex-col items-center gap-2 p-4 bg-gray-50 dark:bg-gray-800 hover:bg-purple-50 dark:hover:bg-purple-900/20 rounded-xl transition-all border border-transparent hover:border-purple-200 dark:hover:border-purple-700 disabled:opacity-50"
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <div className="p-2 bg-white dark:bg-gray-700 rounded-lg shadow-sm">
                      {action.icon}
                    </div>
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      {action.label}
                    </span>
                    <span className="text-xs text-gray-500 text-center">
                      {action.description}
                    </span>
                  </motion.button>
                ))}
              </div>
            )}

            {activeTab === 'improve' && (
              <div className="space-y-4">
                <div className="text-sm text-gray-500 mb-2">Yazma stili seç:</div>
                <div className="grid grid-cols-2 gap-2">
                  {writingStyles.map(style => (
                    <motion.button
                      key={style.id}
                      onClick={() => handleQuickAction(style.id)}
                      disabled={isLoading}
                      className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 hover:bg-purple-50 dark:hover:bg-purple-900/20 rounded-xl transition-all disabled:opacity-50"
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      <span className="text-2xl">{style.emoji}</span>
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        {style.label}
                      </span>
                    </motion.button>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'generate' && (
              <div className="space-y-4">
                <div className="space-y-2">
                  {generateTemplates.map(template => (
                    <motion.button
                      key={template.id}
                      onClick={() => handleQuickAction(template.id)}
                      disabled={isLoading}
                      className="w-full flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 hover:bg-purple-50 dark:hover:bg-purple-900/20 rounded-xl transition-all disabled:opacity-50"
                      whileHover={{ scale: 1.01 }}
                      whileTap={{ scale: 0.99 }}
                    >
                      <div className="p-2 bg-white dark:bg-gray-700 rounded-lg">
                        {template.icon}
                      </div>
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        {template.label}
                      </span>
                    </motion.button>
                  ))}
                </div>

                {/* Custom Prompt */}
                <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                  <div className="text-sm text-gray-500 mb-2">Özel istek:</div>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={customPrompt}
                      onChange={e => setCustomPrompt(e.target.value)}
                      placeholder="Ne yapılmasını istiyorsun?"
                      className="flex-1 px-3 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                      onKeyDown={e => e.key === 'Enter' && handleCustomPrompt()}
                    />
                    <motion.button
                      onClick={handleCustomPrompt}
                      disabled={isLoading || !customPrompt.trim()}
                      className="px-4 py-2 bg-gradient-to-r from-purple-500 to-indigo-500 text-white rounded-lg disabled:opacity-50"
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                    >
                      <FiZap />
                    </motion.button>
                  </div>
                </div>
              </div>
            )}

            {/* Loading State */}
            {isLoading && (
              <div className="mt-6 flex flex-col items-center justify-center py-8">
                <motion.div
                  className="w-12 h-12 border-3 border-purple-500 border-t-transparent rounded-full"
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                />
                <p className="mt-4 text-sm text-gray-500">AI düşünüyor...</p>
              </div>
            )}

            {/* Suggestions */}
            {!isLoading && suggestions.length > 0 && (
              <div className="mt-6 space-y-3">
                <div className="text-sm font-medium text-gray-700 dark:text-gray-300">Öneriler:</div>
                {suggestions.map(suggestion => (
                  <motion.div
                    key={suggestion.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="p-4 bg-gradient-to-r from-purple-50 to-indigo-50 dark:from-purple-900/20 dark:to-indigo-900/20 rounded-xl border border-purple-100 dark:border-purple-800"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-purple-700 dark:text-purple-300">
                        {suggestion.label}
                      </span>
                      <motion.button
                        onClick={() => {
                          onApplySuggestion(suggestion.fullText);
                          setSuggestions([]);
                        }}
                        className="flex items-center gap-1 px-3 py-1 bg-purple-500 text-white text-xs rounded-lg"
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                      >
                        <FiCheck className="w-3 h-3" />
                        Uygula
                      </motion.button>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-3">
                      {suggestion.preview}
                    </p>
                  </motion.div>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="px-4 py-3 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>💡 Metin seçerek daha spesifik öneriler alın</span>
              <span className="flex items-center gap-1">
                <FiZap className="w-3 h-3 text-purple-500" />
                Powered by AI
              </span>
            </div>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

export default AIWritingAssistant;
