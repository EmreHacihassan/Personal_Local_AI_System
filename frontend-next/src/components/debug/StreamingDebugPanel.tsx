'use client';

/**
 * STREAMING DEBUG PANEL
 * Bu component streaming state'ini gerçek zamanlı izlemek için kullanılır.
 * Sorunun kaynağını bulmak için tüm state değişimlerini loglar.
 */

import React, { useEffect, useRef, useState } from 'react';
import { useStore } from '@/store/useStore';

interface DebugLog {
  timestamp: number;
  type: 'info' | 'warn' | 'error' | 'state' | 'ws';
  message: string;
  data?: unknown;
}

interface StreamingDebugPanelProps {
  wsIsStreaming: boolean;
  wsStreamingResponse: string;
  wsCurrentPhase: string | null;
  isTyping: boolean;
  isStreaming: boolean;
  streamingContent: string;
  pendingMessageRef: React.MutableRefObject<unknown>;
  streamingStartedRef: React.MutableRefObject<boolean>;
  prevWsIsStreamingRef: React.MutableRefObject<boolean>;
  elapsedTime: number;
}

export function StreamingDebugPanel({
  wsIsStreaming,
  wsStreamingResponse,
  wsCurrentPhase,
  isTyping,
  isStreaming,
  streamingContent,
  pendingMessageRef,
  streamingStartedRef,
  prevWsIsStreamingRef,
  elapsedTime,
}: StreamingDebugPanelProps) {
  const [logs, setLogs] = useState<DebugLog[]>([]);
  const [expanded, setExpanded] = useState(true);
  const [autoScroll, setAutoScroll] = useState(true);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const prevStateRef = useRef<Record<string, unknown>>({});

  // Store state
  const storeIsTyping = useStore((s) => s.isTyping);
  const storeIsStreaming = useStore((s) => s.isStreaming);
  const storeStreamingContent = useStore((s) => s.streamingContent);

  const addLog = (type: DebugLog['type'], message: string, data?: unknown) => {
    const log: DebugLog = {
      timestamp: Date.now(),
      type,
      message,
      data,
    };
    setLogs((prev) => [...prev.slice(-100), log]); // Keep last 100 logs
  };

  // Track state changes
  useEffect(() => {
    const currentState = {
      wsIsStreaming,
      wsStreamingResponseLen: wsStreamingResponse?.length || 0,
      wsCurrentPhase,
      isTyping,
      isStreaming,
      streamingContentLen: streamingContent?.length || 0,
      hasPendingMessage: !!pendingMessageRef.current,
      streamingStartedRef: streamingStartedRef.current,
      prevWsIsStreamingRef: prevWsIsStreamingRef.current,
      storeIsTyping,
      storeIsStreaming,
      storeStreamingContentLen: storeStreamingContent?.length || 0,
      elapsedTime,
    };

    // Compare with previous state
    const changes: string[] = [];
    Object.entries(currentState).forEach(([key, value]) => {
      if (prevStateRef.current[key] !== value) {
        changes.push(`${key}: ${JSON.stringify(prevStateRef.current[key])} → ${JSON.stringify(value)}`);
      }
    });

    if (changes.length > 0) {
      addLog('state', `STATE CHANGE: ${changes.join(', ')}`, currentState);
    }

    prevStateRef.current = currentState;
  }, [
    wsIsStreaming,
    wsStreamingResponse,
    wsCurrentPhase,
    isTyping,
    isStreaming,
    streamingContent,
    pendingMessageRef,
    streamingStartedRef,
    prevWsIsStreamingRef,
    storeIsTyping,
    storeIsStreaming,
    storeStreamingContent,
    elapsedTime,
  ]);

  // Auto-scroll to bottom
  useEffect(() => {
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll]);

  // Log critical transitions
  useEffect(() => {
    if (wsIsStreaming) {
      addLog('ws', '🚀 WS STREAMING STARTED', { wsIsStreaming: true });
    }
  }, [wsIsStreaming]);

  useEffect(() => {
    if (!wsIsStreaming && prevWsIsStreamingRef.current) {
      addLog('ws', '🏁 WS STREAMING ENDED', { 
        wsIsStreaming: false, 
        prevWsIsStreaming: prevWsIsStreamingRef.current,
        hasPendingMessage: !!pendingMessageRef.current,
        responseLength: wsStreamingResponse?.length || 0,
      });
    }
  }, [wsIsStreaming, wsStreamingResponse, pendingMessageRef, prevWsIsStreamingRef]);

  const formatTime = (ts: number) => {
    const d = new Date(ts);
    return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}:${d.getSeconds().toString().padStart(2, '0')}.${d.getMilliseconds().toString().padStart(3, '0')}`;
  };

  const getLogColor = (type: DebugLog['type']) => {
    switch (type) {
      case 'info': return 'text-blue-400';
      case 'warn': return 'text-yellow-400';
      case 'error': return 'text-red-400';
      case 'state': return 'text-green-400';
      case 'ws': return 'text-purple-400';
      default: return 'text-gray-400';
    }
  };

  const clearLogs = () => setLogs([]);

  if (!expanded) {
    return (
      <button
        onClick={() => setExpanded(true)}
        className="fixed bottom-4 right-4 z-50 bg-gray-900 text-white px-3 py-2 rounded-lg shadow-lg text-xs font-mono"
      >
        🔍 Debug Panel
      </button>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 z-50 w-[600px] max-h-[500px] bg-gray-900/95 backdrop-blur text-white rounded-lg shadow-2xl border border-gray-700 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 bg-gray-800 border-b border-gray-700">
        <span className="text-sm font-bold">🔍 Streaming Debug Panel</span>
        <div className="flex items-center gap-2">
          <label className="flex items-center gap-1 text-xs">
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
              className="w-3 h-3"
            />
            Auto-scroll
          </label>
          <button onClick={clearLogs} className="text-xs bg-red-600 px-2 py-1 rounded">
            Clear
          </button>
          <button onClick={() => setExpanded(false)} className="text-xs bg-gray-600 px-2 py-1 rounded">
            Minimize
          </button>
        </div>
      </div>

      {/* Current State Summary */}
      <div className="px-3 py-2 bg-gray-800/50 border-b border-gray-700 text-xs font-mono grid grid-cols-2 gap-x-4 gap-y-1">
        <div className="flex items-center gap-2">
          <span className={wsIsStreaming ? 'text-green-400' : 'text-red-400'}>●</span>
          <span>wsIsStreaming: <b>{String(wsIsStreaming)}</b></span>
        </div>
        <div className="flex items-center gap-2">
          <span className={isTyping ? 'text-green-400' : 'text-red-400'}>●</span>
          <span>isTyping: <b>{String(isTyping)}</b></span>
        </div>
        <div className="flex items-center gap-2">
          <span className={isStreaming ? 'text-green-400' : 'text-red-400'}>●</span>
          <span>isStreaming: <b>{String(isStreaming)}</b></span>
        </div>
        <div className="flex items-center gap-2">
          <span className={storeIsTyping ? 'text-green-400' : 'text-red-400'}>●</span>
          <span>store.isTyping: <b>{String(storeIsTyping)}</b></span>
        </div>
        <div>wsPhase: <b>{wsCurrentPhase || 'null'}</b></div>
        <div>elapsedTime: <b>{elapsedTime.toFixed(1)}s</b></div>
        <div>wsResponse: <b>{wsStreamingResponse?.length || 0}</b> chars</div>
        <div>pendingMsg: <b>{pendingMessageRef.current ? 'YES' : 'NO'}</b></div>
        <div>streamingStartedRef: <b>{String(streamingStartedRef.current)}</b></div>
        <div>prevWsIsStreamingRef: <b>{String(prevWsIsStreamingRef.current)}</b></div>
      </div>

      {/* Logs */}
      <div className="h-[250px] overflow-y-auto p-2 text-xs font-mono">
        {logs.length === 0 && (
          <div className="text-gray-500 text-center py-4">
            No logs yet. Send a message to start debugging.
          </div>
        )}
        {logs.map((log, i) => (
          <div key={i} className={`mb-1 ${getLogColor(log.type)}`}>
            <span className="text-gray-500">[{formatTime(log.timestamp)}]</span>{' '}
            <span className="font-bold">[{log.type.toUpperCase()}]</span>{' '}
            {log.message}
            {log.data && (
              <pre className="text-[10px] text-gray-400 ml-4 overflow-x-auto">
                {JSON.stringify(log.data, null, 2)}
              </pre>
            )}
          </div>
        ))}
        <div ref={logsEndRef} />
      </div>

      {/* Actions */}
      <div className="px-3 py-2 bg-gray-800 border-t border-gray-700 flex gap-2">
        <button
          onClick={() => addLog('info', 'Manual log test')}
          className="text-xs bg-blue-600 px-2 py-1 rounded"
        >
          Test Log
        </button>
        <button
          onClick={() => {
            const state = {
              wsIsStreaming,
              isTyping,
              isStreaming,
              storeIsTyping,
              storeIsStreaming,
              wsCurrentPhase,
              wsResponseLen: wsStreamingResponse?.length,
              streamingContentLen: streamingContent?.length,
              hasPendingMessage: !!pendingMessageRef.current,
              streamingStartedRef: streamingStartedRef.current,
              prevWsIsStreamingRef: prevWsIsStreamingRef.current,
              elapsedTime,
            };
            console.log('📊 CURRENT STATE DUMP:', state);
            addLog('info', 'State dumped to console', state);
          }}
          className="text-xs bg-green-600 px-2 py-1 rounded"
        >
          Dump State
        </button>
      </div>
    </div>
  );
}

export default StreamingDebugPanel;
