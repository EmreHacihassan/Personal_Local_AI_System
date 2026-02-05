'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Eye, Camera, Monitor, Loader2, X, Send, 
  Maximize2, Minimize2, RefreshCw,
  AlertCircle, CheckCircle, Info, Video, VideoOff,
  Play, Pause, Radio
} from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
const WS_BASE = API_BASE.replace('http', 'ws');

interface VisionStatus {
  vision_available: boolean;
  model: string;
  streaming: boolean;
}

interface VisionResponse {
  success: boolean;
  result?: {
    answer?: string;
    analysis?: string;
    description?: string;
  };
  error?: string;
}

interface LiveFrame {
  id: string;
  timestamp: string;
  width: number;
  height: number;
  image: string;
}

export default function VisionPanel() {
  // State
  const [isOpen, setIsOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState<VisionStatus | null>(null);
  const [screenshot, setScreenshot] = useState<string | null>(null);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<'ask' | 'analyze' | 'live'>('live');
  
  // Live streaming state
  const [isLive, setIsLive] = useState(false);
  const [liveFrame, setLiveFrame] = useState<LiveFrame | null>(null);
  const [fps, setFps] = useState(0);
  const [frameCount, setFrameCount] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);
  const frameTimesRef = useRef<number[]>([]);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  // Fetch vision status
  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/vision/status`);
      const data = await res.json();
      setStatus(data);
    } catch (e) {
      console.error('Vision status error:', e);
    }
  }, []);
  
  // Live streaming connection
  const connectLiveStream = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    
    try {
      const ws = new WebSocket(`${WS_BASE}/api/vision/ws/stream`);
      
      ws.onopen = () => {
        console.log('Live stream connected');
        setError(null);
        // Start streaming
        ws.send(JSON.stringify({ type: 'start' }));
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'frame' && data.data) {
            const frame = data.data as LiveFrame;
            setLiveFrame(frame);
            setFrameCount(prev => prev + 1);
            
            // Calculate FPS
            const now = Date.now();
            frameTimesRef.current.push(now);
            // Keep only last 30 frames for FPS calculation
            if (frameTimesRef.current.length > 30) {
              frameTimesRef.current.shift();
            }
            if (frameTimesRef.current.length > 1) {
              const elapsed = (frameTimesRef.current[frameTimesRef.current.length - 1] - frameTimesRef.current[0]) / 1000;
              const calculatedFps = (frameTimesRef.current.length - 1) / elapsed;
              setFps(Math.round(calculatedFps * 10) / 10);
            }
          } else if (data.type === 'analysis' && data.data) {
            setAnswer(data.data.ai_response || data.data.description || '');
          } else if (data.type === 'error') {
            setError(data.message);
          } else if (data.type === 'ping') {
            ws.send(JSON.stringify({ type: 'pong' }));
          }
        } catch (e) {
          console.error('WS message parse error:', e);
        }
      };
      
      ws.onerror = (e) => {
        console.error('WebSocket error:', e);
        setError('Live stream connection error');
      };
      
      ws.onclose = () => {
        console.log('Live stream disconnected');
        setIsLive(false);
        wsRef.current = null;
        
        // Auto reconnect if still in live mode
        if (mode === 'live' && isOpen) {
          reconnectTimeoutRef.current = setTimeout(() => {
            connectLiveStream();
          }, 2000);
        }
      };
      
      wsRef.current = ws;
      setIsLive(true);
    } catch (e) {
      console.error('Failed to connect live stream:', e);
      setError('Failed to connect to live stream');
    }
  }, [mode, isOpen]);
  
  // Disconnect live stream
  const disconnectLiveStream = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (wsRef.current) {
      if (wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'stop' }));
      }
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsLive(false);
    setFps(0);
    frameTimesRef.current = [];
  }, []);
  
  // Toggle live stream
  const toggleLiveStream = useCallback(() => {
    if (isLive) {
      disconnectLiveStream();
    } else {
      connectLiveStream();
    }
  }, [isLive, connectLiveStream, disconnectLiveStream]);
  
  // Ask AI about current live frame
  const askLiveQuestion = useCallback(async (q: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    
    setIsLoading(true);
    wsRef.current.send(JSON.stringify({
      type: 'analyze',
      question: q,
    }));
    
    // Loading will be cleared when we receive the analysis response
    setTimeout(() => setIsLoading(false), 500);
  }, []);
  
  useEffect(() => {
    if (isOpen) {
      fetchStatus();
      // Auto-start live mode
      if (mode === 'live') {
        connectLiveStream();
      }
    } else {
      disconnectLiveStream();
    }
    
    return () => {
      disconnectLiveStream();
    };
  }, [isOpen, fetchStatus, mode, connectLiveStream, disconnectLiveStream]);
  
  // Capture screenshot
  const captureScreen = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/vision/capture`, {
        method: 'GET',
      });
      const data = await res.json();
      if (data.success && data.image_base64) {
        setScreenshot(`data:image/jpeg;base64,${data.image_base64}`);
      } else {
        setError(data.error || 'Failed to capture screen');
      }
    } catch {
      setError('Connection error');
    } finally {
      setIsLoading(false);
    }
  };
  
  // Ask question about screen
  const askQuestion = async () => {
    if (!question.trim()) return;
    
    setIsLoading(true);
    setError(null);
    setAnswer('');
    
    try {
      const res = await fetch(`${API_BASE}/api/vision/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: question,
          capture_new: true,
        }),
      });
      
      const data: VisionResponse = await res.json();
      
      if (data.success && data.result) {
        setAnswer(data.result.answer || data.result.analysis || '');
        if (data.result.description) {
          setScreenshot(`data:image/jpeg;base64,${data.result.description}`);
        }
      } else {
        setError(data.error || 'Analysis failed');
      }
    } catch {
      setError('Connection error');
    } finally {
      setIsLoading(false);
    }
  };
  
  // Analyze screen
  const analyzeScreen = async () => {
    setIsLoading(true);
    setError(null);
    setAnswer('');
    
    try {
      const res = await fetch(`${API_BASE}/api/vision/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mode: 'describe',
        }),
      });
      
      const data: VisionResponse = await res.json();
      
      if (data.success && data.result) {
        setAnswer(data.result.analysis || data.result.description || '');
      } else {
        setError(data.error || 'Analysis failed');
      }
    } catch {
      setError('Connection error');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) {
    return (
      <motion.button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-24 right-4 z-50 p-3 rounded-full bg-purple-600 text-white shadow-lg hover:bg-purple-700 transition-colors"
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        title="Vision AI - Screen Analysis"
      >
        <Eye className="w-6 h-6" />
      </motion.button>
    );
  }

  const panelWidth = isExpanded ? 'w-[800px]' : 'w-96';
  const panelHeight = isExpanded ? 'max-h-[85vh]' : 'max-h-[60vh]';

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, scale: 0.9, x: 100 }}
        animate={{ opacity: 1, scale: 1, x: 0 }}
        exit={{ opacity: 0, scale: 0.9, x: 100 }}
        className={`fixed bottom-4 right-4 z-50 ${panelWidth} bg-gray-900 rounded-2xl shadow-2xl border border-gray-700 overflow-hidden transition-all duration-300`}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700 bg-gradient-to-r from-purple-900/50 to-blue-900/50">
          <div className="flex items-center gap-2">
            <Eye className="w-5 h-5 text-purple-400" />
            <span className="font-semibold text-white">Vision AI</span>
            {status?.vision_available && (
              <span className="px-2 py-0.5 text-xs bg-green-500/20 text-green-400 rounded-full">
                Online
              </span>
            )}
            {isLive && (
              <span className="flex items-center gap-1 px-2 py-0.5 text-xs bg-red-500/20 text-red-400 rounded-full animate-pulse">
                <Radio className="w-3 h-3" />
                LIVE
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            {isLive && (
              <span className="text-xs text-gray-400">{fps} FPS</span>
            )}
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-1.5 hover:bg-gray-700 rounded-lg transition-colors"
              title={isExpanded ? "Minimize" : "Expand"}
            >
              {isExpanded ? (
                <Minimize2 className="w-4 h-4 text-gray-400" />
              ) : (
                <Maximize2 className="w-4 h-4 text-gray-400" />
              )}
            </button>
            <button
              onClick={fetchStatus}
              className="p-1.5 hover:bg-gray-700 rounded-lg transition-colors"
              title="Refresh status"
            >
              <RefreshCw className="w-4 h-4 text-gray-400" />
            </button>
            <button
              onClick={() => setIsOpen(false)}
              className="p-1.5 hover:bg-gray-700 rounded-lg transition-colors"
            >
              <X className="w-4 h-4 text-gray-400" />
            </button>
          </div>
        </div>
        
        {/* Content */}
        <div className={`p-4 space-y-4 ${panelHeight} overflow-y-auto`}>
          {/* Mode Toggle */}
          <div className="flex gap-2">
            <button
              onClick={() => { setMode('live'); if (!isLive) connectLiveStream(); }}
              className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-1 ${
                mode === 'live' 
                  ? 'bg-red-600 text-white' 
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              <Video className="w-4 h-4" />
              Live Monitor
            </button>
            <button
              onClick={() => { setMode('ask'); disconnectLiveStream(); }}
              className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-colors ${
                mode === 'ask' 
                  ? 'bg-purple-600 text-white' 
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              Ask Question
            </button>
            <button
              onClick={() => { setMode('analyze'); disconnectLiveStream(); }}
              className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-colors ${
                mode === 'analyze' 
                  ? 'bg-purple-600 text-white' 
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              Analyze
            </button>
          </div>
          
          {/* Live Monitor Mode */}
          {mode === 'live' && (
            <div className="space-y-3">
              {/* Live View Container */}
              <div className="relative rounded-lg overflow-hidden border border-gray-700 bg-black">
                {liveFrame ? (
                  <img 
                    src={`data:image/jpeg;base64,${liveFrame.image}`}
                    alt="Live screen" 
                    className="w-full h-auto"
                  />
                ) : (
                  <div className="flex items-center justify-center h-48 text-gray-500">
                    {isLive ? (
                      <div className="flex flex-col items-center gap-2">
                        <Loader2 className="w-8 h-8 animate-spin" />
                        <span className="text-sm">Connecting to live stream...</span>
                      </div>
                    ) : (
                      <div className="flex flex-col items-center gap-2">
                        <VideoOff className="w-8 h-8" />
                        <span className="text-sm">Live stream stopped</span>
                      </div>
                    )}
                  </div>
                )}
                
                {/* Live indicator overlay */}
                {isLive && liveFrame && (
                  <div className="absolute top-2 left-2 flex items-center gap-2">
                    <span className="flex items-center gap-1 px-2 py-1 text-xs bg-red-600/90 text-white rounded-full animate-pulse">
                      <Radio className="w-3 h-3" />
                      LIVE
                    </span>
                    <span className="px-2 py-1 text-xs bg-black/70 text-white rounded-full">
                      {liveFrame.width}x{liveFrame.height}
                    </span>
                  </div>
                )}
              </div>
              
              {/* Live Controls */}
              <div className="flex gap-2">
                <button
                  onClick={toggleLiveStream}
                  className={`flex-1 py-3 px-4 rounded-lg flex items-center justify-center gap-2 transition-colors ${
                    isLive 
                      ? 'bg-red-600 hover:bg-red-700 text-white' 
                      : 'bg-green-600 hover:bg-green-700 text-white'
                  }`}
                >
                  {isLive ? (
                    <>
                      <Pause className="w-5 h-5" />
                      Stop Live
                    </>
                  ) : (
                    <>
                      <Play className="w-5 h-5" />
                      Start Live
                    </>
                  )}
                </button>
              </div>
              
              {/* Quick Question in Live Mode */}
              <div className="space-y-2">
                <label className="text-sm text-gray-400">Quick AI Question:</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && askLiveQuestion(question)}
                    placeholder="Ask about current screen..."
                    className="flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
                  />
                  <button
                    onClick={() => askLiveQuestion(question)}
                    disabled={isLoading || !question.trim() || !isLive}
                    className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 rounded-lg transition-colors"
                  >
                    <Send className="w-5 h-5" />
                  </button>
                </div>
                <div className="flex gap-2 flex-wrap">
                  {['What app is open?', 'Any errors?', 'Describe screen'].map((q) => (
                    <button
                      key={q}
                      onClick={() => askLiveQuestion(q)}
                      disabled={!isLive}
                      className="px-2 py-1 text-xs bg-gray-800 hover:bg-gray-700 disabled:opacity-50 rounded-lg text-gray-400 transition-colors"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
              
              {/* Stats */}
              {isLive && (
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="p-2 bg-gray-800 rounded-lg">
                    <div className="text-lg font-bold text-white">{fps}</div>
                    <div className="text-xs text-gray-400">FPS</div>
                  </div>
                  <div className="p-2 bg-gray-800 rounded-lg">
                    <div className="text-lg font-bold text-white">{frameCount}</div>
                    <div className="text-xs text-gray-400">Frames</div>
                  </div>
                  <div className="p-2 bg-gray-800 rounded-lg">
                    <div className="text-lg font-bold text-green-400">●</div>
                    <div className="text-xs text-gray-400">Connected</div>
                  </div>
                </div>
              )}
            </div>
          )}
          
          {/* Ask Mode Content */}
          {mode === 'ask' && (
            <>
              {screenshot && (
                <div className="relative rounded-lg overflow-hidden border border-gray-700">
                  <img 
                    src={screenshot} 
                    alt="Screen capture" 
                    className="w-full h-auto"
                  />
                  <button
                    onClick={() => setScreenshot(null)}
                    className="absolute top-2 right-2 p-1 bg-black/50 rounded-full hover:bg-black/70"
                  >
                    <X className="w-4 h-4 text-white" />
                  </button>
                </div>
              )}
              
              {/* Capture Button */}
              <button
                onClick={captureScreen}
                disabled={isLoading}
                className="w-full py-3 px-4 bg-gray-800 hover:bg-gray-700 disabled:opacity-50 rounded-lg flex items-center justify-center gap-2 transition-colors"
              >
                {isLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Camera className="w-5 h-5" />
                )}
                <span>Capture Screen</span>
              </button>
              
              <div className="space-y-2">
                <label className="text-sm text-gray-400">Ask about your screen:</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && askQuestion()}
                    placeholder="What's on my screen?"
                    className="flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
                  />
                  <button
                    onClick={askQuestion}
                    disabled={isLoading || !question.trim()}
                    className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 rounded-lg transition-colors"
                  >
                    <Send className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </>
          )}
          
          {/* Analyze Mode Content */}
          {mode === 'analyze' && (
            <>
              {screenshot && (
                <div className="relative rounded-lg overflow-hidden border border-gray-700">
                  <img 
                    src={screenshot} 
                    alt="Screen capture" 
                    className="w-full h-auto"
                  />
                  <button
                    onClick={() => setScreenshot(null)}
                    className="absolute top-2 right-2 p-1 bg-black/50 rounded-full hover:bg-black/70"
                  >
                    <X className="w-4 h-4 text-white" />
                  </button>
                </div>
              )}
              
              <button
                onClick={captureScreen}
                disabled={isLoading}
                className="w-full py-3 px-4 bg-gray-800 hover:bg-gray-700 disabled:opacity-50 rounded-lg flex items-center justify-center gap-2 transition-colors"
              >
                {isLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Camera className="w-5 h-5" />
                )}
                <span>Capture Screen</span>
              </button>
              
              <button
                onClick={analyzeScreen}
                disabled={isLoading}
                className="w-full py-3 px-4 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 rounded-lg flex items-center justify-center gap-2 transition-colors"
              >
                {isLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Monitor className="w-5 h-5" />
                )}
                <span>Analyze Screen</span>
              </button>
            </>
          )}
          
          {/* Error Display */}
          {error && (
            <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg flex items-center gap-2 text-red-400">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <span className="text-sm">{error}</span>
            </div>
          )}
          
          {/* Answer Display */}
          {answer && (
            <div className="p-3 bg-gray-800 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle className="w-4 h-4 text-green-400" />
                <span className="text-sm font-medium text-green-400">AI Response</span>
              </div>
              <p className="text-sm text-gray-300 whitespace-pre-wrap">{answer}</p>
            </div>
          )}
        </div>
        
        {/* Footer */}
        <div className="p-3 border-t border-gray-700 bg-gray-900/50">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>Model: {status?.model || 'llava'}</span>
            <span className="flex items-center gap-1">
              <Info className="w-3 h-3" />
              100% Local
            </span>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
