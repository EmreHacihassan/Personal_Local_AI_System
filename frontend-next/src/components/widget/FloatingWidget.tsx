'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence, useDragControls, PanInfo } from 'framer-motion';
import { 
  MessageSquare, 
  X, 
  Minimize2, 
  Maximize2,
  Send,
  ImageIcon,
  Globe,
  Mic,
  Paperclip,
  Sparkles,
  GripVertical,
  Settings,
  FileText,
  History,
  Search as SearchIcon,
  Loader2
} from 'lucide-react';
import { useStore } from '@/store/useStore';
import { cn } from '@/lib/utils';
import { sendMessage } from '@/lib/api';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export function FloatingWidget() {
  const { widgetEnabled, language, toggleWidget } = useStore();
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'chat' | 'documents' | 'history' | 'search'>('chat');
  const [webSearchEnabled, setWebSearchEnabled] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const dragControls = useDragControls();

  // Widget pozisyonunu localStorage'dan yükle
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedPosition = localStorage.getItem('widgetPosition');
      if (savedPosition) {
        setPosition(JSON.parse(savedPosition));
      } else {
        // Varsayılan: sağ alt köşe
        setPosition({ 
          x: window.innerWidth - 80, 
          y: window.innerHeight - 80 
        });
      }
    }
  }, []);

  // Mesajların sonuna scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Pozisyonu kaydet
  const handleDragEnd = useCallback((_: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
    const newPosition = {
      x: position.x + info.offset.x,
      y: position.y + info.offset.y
    };
    
    // Ekran sınırları içinde tut
    const maxX = window.innerWidth - 60;
    const maxY = window.innerHeight - 60;
    newPosition.x = Math.max(0, Math.min(newPosition.x, maxX));
    newPosition.y = Math.max(0, Math.min(newPosition.y, maxY));
    
    setPosition(newPosition);
    localStorage.setItem('widgetPosition', JSON.stringify(newPosition));
  }, [position]);

  // Mesaj gönder
  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await sendMessage(input, webSearchEnabled);
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.content || response.response || 'Yanıt alınamadı.',
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: language === 'tr' 
          ? 'Bir hata oluştu. Lütfen tekrar deneyin.' 
          : 'An error occurred. Please try again.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Tuş basımı
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Widget etkin değilse gösterme
  if (!widgetEnabled) return null;

  return (
    <>
      {/* Ana Widget Butonu */}
      <AnimatePresence>
        {!isOpen && (
          <motion.div
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            drag
            dragControls={dragControls}
            dragMomentum={false}
            onDragEnd={handleDragEnd}
            style={{ 
              position: 'fixed', 
              left: position.x, 
              top: position.y,
              zIndex: 9999 
            }}
            className="cursor-grab active:cursor-grabbing"
          >
            <motion.button
              onClick={() => setIsOpen(true)}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              className="w-14 h-14 rounded-full bg-gradient-to-br from-primary-500 to-primary-700 text-white shadow-2xl flex items-center justify-center hover:shadow-primary-500/50 transition-shadow"
            >
              <MessageSquare className="w-6 h-6" />
            </motion.button>
            
            {/* Pulse Animation */}
            <div className="absolute inset-0 rounded-full bg-primary-500 animate-ping opacity-25" />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Widget Panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ 
              opacity: 1, 
              scale: 1, 
              y: 0,
              width: isExpanded ? 600 : 380,
              height: isMinimized ? 56 : (isExpanded ? 700 : 520)
            }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            drag
            dragControls={dragControls}
            dragMomentum={false}
            dragListener={false}
            style={{ 
              position: 'fixed',
              right: 20,
              bottom: 20,
              zIndex: 9999
            }}
            className="bg-card border border-border rounded-2xl shadow-2xl overflow-hidden flex flex-col"
          >
            {/* Header */}
            <div 
              onPointerDown={(e) => dragControls.start(e)}
              className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-primary-500 to-primary-600 text-white cursor-grab active:cursor-grabbing"
            >
              <div className="flex items-center gap-2">
                <GripVertical className="w-4 h-4 opacity-50" />
                <Sparkles className="w-5 h-5" />
                <span className="font-semibold">AI Assistant</span>
              </div>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setIsMinimized(!isMinimized)}
                  className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
                >
                  <Minimize2 className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setIsExpanded(!isExpanded)}
                  className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
                >
                  <Maximize2 className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Minimize edilmemişse içerik göster */}
            {!isMinimized && (
              <>
                {/* Tabs */}
                <div className="flex items-center border-b border-border px-2 py-1 gap-1 bg-muted/50">
                  {([
                    { id: 'chat', icon: MessageSquare, label: language === 'tr' ? 'Sohbet' : 'Chat' },
                    { id: 'documents', icon: FileText, label: language === 'tr' ? 'Belgeler' : 'Documents' },
                    { id: 'history', icon: History, label: language === 'tr' ? 'Geçmiş' : 'History' },
                    { id: 'search', icon: SearchIcon, label: language === 'tr' ? 'Ara' : 'Search' },
                  ] as const).map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={cn(
                        "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all",
                        activeTab === tab.id 
                          ? "bg-primary-500 text-white" 
                          : "text-muted-foreground hover:bg-accent"
                      )}
                    >
                      <tab.icon className="w-3.5 h-3.5" />
                      {tab.label}
                    </button>
                  ))}
                </div>

                {/* Chat Tab */}
                {activeTab === 'chat' && (
                  <>
                    {/* Messages */}
                    <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0">
                      {messages.length === 0 && (
                        <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground py-8">
                          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary-500/20 to-primary-600/20 flex items-center justify-center mb-4">
                            <Sparkles className="w-8 h-8 text-primary-500" />
                          </div>
                          <p className="font-medium">
                            {language === 'tr' ? 'Merhaba!' : 'Hello!'}
                          </p>
                          <p className="text-sm mt-1">
                            {language === 'tr' 
                              ? 'Size nasıl yardımcı olabilirim?' 
                              : 'How can I help you?'}
                          </p>
                        </div>
                      )}

                      {messages.map((message) => (
                        <motion.div
                          key={message.id}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          className={cn(
                            "flex",
                            message.role === 'user' ? 'justify-end' : 'justify-start'
                          )}
                        >
                          <div
                            className={cn(
                              "max-w-[85%] px-4 py-2.5 rounded-2xl text-sm",
                              message.role === 'user'
                                ? 'bg-primary-500 text-white rounded-br-md'
                                : 'bg-muted rounded-bl-md'
                            )}
                          >
                            <p className="whitespace-pre-wrap">{message.content}</p>
                            <p className={cn(
                              "text-[10px] mt-1",
                              message.role === 'user' ? 'text-white/70' : 'text-muted-foreground'
                            )}>
                              {new Date(message.timestamp).toLocaleTimeString(language === 'tr' ? 'tr-TR' : 'en-US', {
                                hour: '2-digit',
                                minute: '2-digit'
                              })}
                            </p>
                          </div>
                        </motion.div>
                      ))}

                      {isLoading && (
                        <motion.div
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          className="flex justify-start"
                        >
                          <div className="bg-muted px-4 py-3 rounded-2xl rounded-bl-md">
                            <div className="flex items-center gap-2">
                              <Loader2 className="w-4 h-4 animate-spin text-primary-500" />
                              <span className="text-sm text-muted-foreground">
                                {language === 'tr' ? 'Düşünüyor...' : 'Thinking...'}
                              </span>
                            </div>
                          </div>
                        </motion.div>
                      )}

                      <div ref={messagesEndRef} />
                    </div>

                    {/* Input */}
                    <div className="p-3 border-t border-border bg-background">
                      <div className="flex items-center gap-2 mb-2">
                        <button
                          onClick={() => setWebSearchEnabled(!webSearchEnabled)}
                          className={cn(
                            "flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs transition-all",
                            webSearchEnabled 
                              ? "bg-primary-500 text-white" 
                              : "bg-muted text-muted-foreground hover:bg-accent"
                          )}
                        >
                          <Globe className="w-3.5 h-3.5" />
                          Web
                        </button>
                        <button className="p-1.5 rounded-lg bg-muted text-muted-foreground hover:bg-accent transition-colors">
                          <ImageIcon className="w-4 h-4" />
                        </button>
                        <button className="p-1.5 rounded-lg bg-muted text-muted-foreground hover:bg-accent transition-colors">
                          <Paperclip className="w-4 h-4" />
                        </button>
                        <button className="p-1.5 rounded-lg bg-muted text-muted-foreground hover:bg-accent transition-colors">
                          <Mic className="w-4 h-4" />
                        </button>
                      </div>
                      
                      <div className="flex items-end gap-2">
                        <textarea
                          ref={inputRef}
                          value={input}
                          onChange={(e) => setInput(e.target.value)}
                          onKeyDown={handleKeyDown}
                          placeholder={language === 'tr' ? 'Mesajınızı yazın...' : 'Type your message...'}
                          rows={1}
                          className="flex-1 resize-none bg-muted border-0 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/50 max-h-24"
                          style={{ minHeight: '40px' }}
                        />
                        <button
                          onClick={handleSend}
                          disabled={!input.trim() || isLoading}
                          className="w-10 h-10 flex items-center justify-center rounded-xl bg-primary-500 text-white hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                          <Send className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </>
                )}

                {/* Documents Tab */}
                {activeTab === 'documents' && (
                  <div className="flex-1 overflow-y-auto p-4">
                    <div className="text-center py-8 text-muted-foreground">
                      <FileText className="w-12 h-12 mx-auto mb-3 opacity-50" />
                      <p className="text-sm">
                        {language === 'tr' 
                          ? 'Belgelerinizi ana sayfadan yükleyebilirsiniz.'
                          : 'You can upload documents from the main page.'}
                      </p>
                    </div>
                  </div>
                )}

                {/* History Tab */}
                {activeTab === 'history' && (
                  <div className="flex-1 overflow-y-auto p-4">
                    <div className="text-center py-8 text-muted-foreground">
                      <History className="w-12 h-12 mx-auto mb-3 opacity-50" />
                      <p className="text-sm">
                        {language === 'tr' 
                          ? 'Sohbet geçmişiniz burada görünecek.'
                          : 'Your chat history will appear here.'}
                      </p>
                    </div>
                  </div>
                )}

                {/* Search Tab */}
                {activeTab === 'search' && (
                  <div className="flex-1 overflow-y-auto p-4">
                    <div className="relative mb-4">
                      <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                      <input
                        type="text"
                        placeholder={language === 'tr' ? 'Belge veya sohbet ara...' : 'Search documents or chats...'}
                        className="w-full pl-10 pr-4 py-2.5 bg-muted rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/50"
                      />
                    </div>
                    <div className="text-center py-8 text-muted-foreground">
                      <SearchIcon className="w-12 h-12 mx-auto mb-3 opacity-50" />
                      <p className="text-sm">
                        {language === 'tr' 
                          ? 'Arama yapmak için yukarıdaki kutuyu kullanın.'
                          : 'Use the search box above to search.'}
                      </p>
                    </div>
                  </div>
                )}

                {/* Footer with Settings */}
                <div className="px-3 py-2 border-t border-border bg-muted/30 flex items-center justify-between">
                  <button
                    onClick={toggleWidget}
                    className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1 transition-colors"
                  >
                    <Settings className="w-3.5 h-3.5" />
                    {language === 'tr' ? 'Widget\'ı Kapat' : 'Disable Widget'}
                  </button>
                  <span className="text-[10px] text-muted-foreground">
                    Enterprise AI v2.0
                  </span>
                </div>
              </>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
