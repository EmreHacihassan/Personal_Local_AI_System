'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Send, 
  Globe, 
  Sparkles, 
  Paperclip, 
  Loader2,
  Copy,
  ThumbsUp,
  ThumbsDown,
  RefreshCw,
  Zap,
  FileText,
  ExternalLink,
  ChevronDown
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/cjs/styles/prism';
import { useStore, Message } from '@/store/useStore';
import { sendChatMessage } from '@/lib/api';
import { cn, generateId, formatDate } from '@/lib/utils';

// Sample questions
const sampleQuestions = [
  { icon: '🔬', text: 'RAG sistemi nasıl çalışır?', category: 'Teknik' },
  { icon: '📊', text: 'Veri analizi için en iyi pratikler', category: 'Analiz' },
  { icon: '🚀', text: 'Performans optimizasyonu önerileri', category: 'Performans' },
  { icon: '🛡️', text: 'Güvenlik en iyi pratikleri', category: 'Güvenlik' },
];

export function ChatPage() {
  const { 
    messages, 
    addMessage, 
    isTyping, 
    setIsTyping,
    webSearchEnabled,
    toggleWebSearch,
    responseMode,
    setResponseMode,
    language,
  } = useStore();

  const [inputValue, setInputValue] = useState('');
  const [showModeSelector, setShowModeSelector] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const handleSend = async () => {
    if (!inputValue.trim() || isTyping) return;

    const userMessage: Message = {
      id: generateId(),
      role: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
    };

    addMessage(userMessage);
    setInputValue('');
    setIsTyping(true);

    try {
      const response = await sendChatMessage({
        message: userMessage.content,
        web_search: webSearchEnabled,
        response_mode: responseMode,
      });

      if (response.success && response.data) {
        const assistantMessage: Message = {
          id: generateId(),
          role: 'assistant',
          content: response.data.response,
          timestamp: new Date(),
          sources: response.data.sources?.map(s => ({
            title: s.title,
            url: s.url,
            snippet: s.snippet,
            type: s.url ? 'web' : 'document',
          })),
          metadata: response.data.metadata,
        };
        addMessage(assistantMessage);
      } else {
        addMessage({
          id: generateId(),
          role: 'assistant',
          content: 'Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.',
          timestamp: new Date(),
        });
      }
    } catch (error) {
      console.error('Chat error:', error);
      addMessage({
        id: generateId(),
        role: 'assistant',
        content: 'Bağlantı hatası. Lütfen backend\'in çalıştığından emin olun.',
        timestamp: new Date(),
      });
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSampleQuestion = (question: string) => {
    setInputValue(question);
    inputRef.current?.focus();
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-border bg-card/50 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 text-white">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-semibold">
              {language === 'tr' ? 'AI Asistan' : 'AI Assistant'}
            </h1>
            <p className="text-xs text-muted-foreground">
              {language === 'tr' ? 'Sorularınızı yanıtlamaya hazırım' : 'Ready to answer your questions'}
            </p>
          </div>
        </div>

        {/* Mode Selector */}
        <div className="flex items-center gap-2">
          <button
            onClick={toggleWebSearch}
            className={cn(
              "flex items-center gap-2 px-3 py-2 rounded-lg transition-all",
              webSearchEnabled 
                ? "bg-blue-500/10 text-blue-600 border border-blue-500/30" 
                : "bg-muted text-muted-foreground hover:bg-accent"
            )}
          >
            <Globe className="w-4 h-4" />
            <span className="text-sm">Web</span>
          </button>

          <div className="relative">
            <button
              onClick={() => setShowModeSelector(!showModeSelector)}
              className="flex items-center gap-2 px-3 py-2 rounded-lg bg-muted hover:bg-accent transition-colors"
            >
              <Zap className="w-4 h-4" />
              <span className="text-sm capitalize">{responseMode}</span>
              <ChevronDown className="w-3 h-3" />
            </button>

            <AnimatePresence>
              {showModeSelector && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="absolute right-0 top-full mt-2 w-40 bg-card border border-border rounded-xl shadow-lg z-50 overflow-hidden"
                >
                  {['normal', 'detailed'].map((mode) => (
                    <button
                      key={mode}
                      onClick={() => {
                        setResponseMode(mode as 'normal' | 'detailed');
                        setShowModeSelector(false);
                      }}
                      className={cn(
                        "w-full px-4 py-2 text-left text-sm hover:bg-accent transition-colors",
                        responseMode === mode && "bg-primary-500/10 text-primary-600"
                      )}
                    >
                      {mode === 'normal' ? 'Normal' : 'Detaylı'}
                    </button>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </header>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Welcome State */}
          {messages.length === 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center py-12"
            >
              <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-primary-500 to-primary-700 text-white mb-6">
                <Sparkles className="w-10 h-10" />
              </div>
              <h2 className="text-2xl font-bold mb-2">
                {language === 'tr' ? 'Merhaba! Size nasıl yardımcı olabilirim?' : 'Hello! How can I help you?'}
              </h2>
              <p className="text-muted-foreground mb-8">
                {language === 'tr' 
                  ? 'Aşağıdaki örneklerden birini seçin veya kendi sorunuzu yazın'
                  : 'Choose from the examples below or write your own question'
                }
              </p>

              {/* Sample Questions Grid */}
              <div className="grid grid-cols-2 gap-3 max-w-2xl mx-auto">
                {sampleQuestions.map((q, i) => (
                  <motion.button
                    key={i}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.1 }}
                    onClick={() => handleSampleQuestion(q.text)}
                    className="flex items-center gap-3 p-4 rounded-xl bg-card border border-border hover:border-primary-500/50 hover:shadow-lg transition-all text-left group"
                  >
                    <span className="text-2xl">{q.icon}</span>
                    <div>
                      <p className="text-sm font-medium group-hover:text-primary-600 transition-colors">
                        {q.text}
                      </p>
                      <p className="text-xs text-muted-foreground">{q.category}</p>
                    </div>
                  </motion.button>
                ))}
              </div>
            </motion.div>
          )}

          {/* Messages */}
          <AnimatePresence mode="popLayout">
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
          </AnimatePresence>

          {/* Typing Indicator */}
          {isTyping && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-start gap-3"
            >
              <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-primary-700 text-white">
                <Sparkles className="w-4 h-4" />
              </div>
              <div className="bg-card border border-border rounded-2xl rounded-tl-sm px-4 py-3">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </motion.div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="border-t border-border bg-card/50 backdrop-blur-sm p-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-end gap-3 bg-background border border-border rounded-2xl p-2 focus-within:border-primary-500 focus-within:ring-2 focus-within:ring-primary-500/20 transition-all">
            {/* Attachment Button */}
            <button className="flex items-center justify-center w-10 h-10 rounded-xl hover:bg-accent transition-colors text-muted-foreground hover:text-foreground">
              <Paperclip className="w-5 h-5" />
            </button>

            {/* Input */}
            <textarea
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={language === 'tr' ? 'Mesajınızı yazın...' : 'Type your message...'}
              rows={1}
              className="flex-1 resize-none bg-transparent border-none outline-none text-foreground placeholder:text-muted-foreground py-2 max-h-32"
              style={{ minHeight: '40px' }}
            />

            {/* Send Button */}
            <button
              onClick={handleSend}
              disabled={!inputValue.trim() || isTyping}
              className={cn(
                "flex items-center justify-center w-10 h-10 rounded-xl transition-all",
                inputValue.trim() && !isTyping
                  ? "bg-gradient-to-br from-primary-500 to-primary-700 text-white hover:shadow-lg hover:shadow-primary-500/25"
                  : "bg-muted text-muted-foreground"
              )}
            >
              {isTyping ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>

          <p className="text-xs text-center text-muted-foreground mt-2">
            {language === 'tr' 
              ? 'Enter ile gönder, Shift+Enter ile yeni satır'
              : 'Press Enter to send, Shift+Enter for new line'
            }
          </p>
        </div>
      </div>
    </div>
  );
}

// Message Bubble Component
function MessageBubble({ message }: { message: Message }) {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === 'user';

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className={cn(
        "flex gap-3",
        isUser ? "flex-row-reverse" : "flex-row"
      )}
    >
      {/* Avatar */}
      <div className={cn(
        "flex items-center justify-center w-8 h-8 rounded-lg flex-shrink-0",
        isUser 
          ? "bg-primary-100 dark:bg-primary-900 text-primary-600 dark:text-primary-400"
          : "bg-gradient-to-br from-primary-500 to-primary-700 text-white"
      )}>
        {isUser ? '👤' : <Sparkles className="w-4 h-4" />}
      </div>

      {/* Content */}
      <div className={cn(
        "flex flex-col max-w-[80%]",
        isUser ? "items-end" : "items-start"
      )}>
        <div className={cn(
          "rounded-2xl px-4 py-3",
          isUser 
            ? "bg-primary-500 text-white rounded-tr-sm"
            : "bg-card border border-border rounded-tl-sm"
        )}>
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code({ inline, className, children, ...props }: { inline?: boolean; className?: string; children?: React.ReactNode }) {
                    const match = /language-(\w+)/.exec(className || '');
                    return !inline && match ? (
                      <SyntaxHighlighter
                        style={oneDark}
                        language={match[1]}
                        PreTag="div"
                        className="rounded-lg !mt-2 !mb-2"
                        {...props}
                      >
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                    ) : (
                      <code className="bg-muted px-1.5 py-0.5 rounded text-sm" {...props}>
                        {children}
                      </code>
                    );
                  },
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Sources */}
        {message.sources && message.sources.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-2">
            {message.sources.map((source, i) => (
              <a
                key={i}
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-muted text-xs text-muted-foreground hover:text-foreground transition-colors"
              >
                {source.type === 'web' ? <Globe className="w-3 h-3" /> : <FileText className="w-3 h-3" />}
                <span className="max-w-[150px] truncate">{source.title}</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            ))}
          </div>
        )}

        {/* Actions */}
        {!isUser && (
          <div className="flex items-center gap-2 mt-2">
            <button
              onClick={handleCopy}
              className="p-1.5 rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground transition-colors"
              title="Kopyala"
            >
              {copied ? '✓' : <Copy className="w-4 h-4" />}
            </button>
            <button className="p-1.5 rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground transition-colors">
              <ThumbsUp className="w-4 h-4" />
            </button>
            <button className="p-1.5 rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground transition-colors">
              <ThumbsDown className="w-4 h-4" />
            </button>
            <button className="p-1.5 rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground transition-colors">
              <RefreshCw className="w-4 h-4" />
            </button>
            <span className="text-xs text-muted-foreground ml-2">
              {formatDate(message.timestamp)}
            </span>
          </div>
        )}
      </div>
    </motion.div>
  );
}
