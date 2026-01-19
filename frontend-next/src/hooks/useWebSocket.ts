/**
 * WebSocket Hook for Enterprise AI Assistant
 * Real-time communication with backend
 */

import { useEffect, useRef, useState, useCallback } from 'react';

const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8001';

export type WebSocketStatus = 'connecting' | 'connected' | 'disconnected' | 'reconnecting' | 'error';

export interface WebSocketMessage {
  type: string;
  data?: unknown;
  error?: string;
  timestamp?: string;
}

export interface UseWebSocketOptions {
  /** Auto-connect on mount */
  autoConnect?: boolean;
  /** Reconnect on disconnect */
  autoReconnect?: boolean;
  /** Max reconnection attempts */
  maxReconnectAttempts?: number;
  /** Reconnection delay in ms */
  reconnectDelay?: number;
  /** Ping interval in ms (0 to disable) */
  pingInterval?: number;
  /** Message handler */
  onMessage?: (message: WebSocketMessage) => void;
  /** Status change handler */
  onStatusChange?: (status: WebSocketStatus) => void;
  /** Error handler */
  onError?: (error: Event) => void;
}

const DEFAULT_OPTIONS: Required<UseWebSocketOptions> = {
  autoConnect: true,
  autoReconnect: true,
  maxReconnectAttempts: 5,
  reconnectDelay: 3000,
  pingInterval: 30000,
  onMessage: () => {},
  onStatusChange: () => {},
  onError: () => {},
};

export function useWebSocket(
  endpoint: string = '/ws',
  options: UseWebSocketOptions = {}
) {
  const opts = { ...DEFAULT_OPTIONS, ...options };
  
  const [status, setStatus] = useState<WebSocketStatus>('disconnected');
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [messageHistory, setMessageHistory] = useState<WebSocketMessage[]>([]);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const mountedRef = useRef(true);

  // Update status with callback
  const updateStatus = useCallback((newStatus: WebSocketStatus) => {
    if (!mountedRef.current) return;
    setStatus(newStatus);
    opts.onStatusChange(newStatus);
  }, [opts]);

  // Clear intervals and timeouts
  const clearTimers = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }
  }, []);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('[WS] Already connected');
      return;
    }

    clearTimers();
    updateStatus('connecting');

    try {
      const wsUrl = `${WS_BASE_URL}${endpoint}`;
      console.log('[WS] Connecting to:', wsUrl);
      
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[WS] Connected');
        reconnectAttemptsRef.current = 0;
        updateStatus('connected');

        // Start ping interval
        if (opts.pingInterval > 0) {
          pingIntervalRef.current = setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
              ws.send(JSON.stringify({ type: 'ping' }));
            }
          }, opts.pingInterval);
        }
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          message.timestamp = new Date().toISOString();

          // Skip pong messages from history
          if (message.type !== 'pong') {
            setLastMessage(message);
            setMessageHistory(prev => [...prev.slice(-99), message]);
          }

          opts.onMessage(message);
        } catch (error) {
          console.error('[WS] Failed to parse message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('[WS] Error:', error);
        updateStatus('error');
        opts.onError(error);
      };

      ws.onclose = (event) => {
        console.log('[WS] Closed:', event.code, event.reason);
        clearTimers();

        if (mountedRef.current && opts.autoReconnect && reconnectAttemptsRef.current < opts.maxReconnectAttempts) {
          updateStatus('reconnecting');
          reconnectAttemptsRef.current++;
          
          const delay = opts.reconnectDelay * Math.pow(1.5, reconnectAttemptsRef.current - 1);
          console.log(`[WS] Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current}/${opts.maxReconnectAttempts})`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            if (mountedRef.current) {
              connect();
            }
          }, delay);
        } else {
          updateStatus('disconnected');
        }
      };
    } catch (error) {
      console.error('[WS] Connection error:', error);
      updateStatus('error');
    }
  }, [endpoint, opts, updateStatus, clearTimers]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    clearTimers();
    reconnectAttemptsRef.current = opts.maxReconnectAttempts; // Prevent reconnection
    
    if (wsRef.current) {
      wsRef.current.close(1000, 'Client disconnect');
      wsRef.current = null;
    }
    
    updateStatus('disconnected');
  }, [opts.maxReconnectAttempts, updateStatus, clearTimers]);

  // Send message through WebSocket
  const sendMessage = useCallback((message: WebSocketMessage | string) => {
    if (wsRef.current?.readyState !== WebSocket.OPEN) {
      console.warn('[WS] Cannot send message, not connected');
      return false;
    }

    try {
      const data = typeof message === 'string' ? message : JSON.stringify(message);
      wsRef.current.send(data);
      return true;
    } catch (error) {
      console.error('[WS] Send error:', error);
      return false;
    }
  }, []);

  // Send typed messages
  const sendChatMessage = useCallback((content: string, sessionId?: string) => {
    return sendMessage({
      type: 'chat',
      data: { content, session_id: sessionId },
    });
  }, [sendMessage]);

  const sendStreamRequest = useCallback((content: string, options?: Record<string, unknown>) => {
    return sendMessage({
      type: 'stream',
      data: { content, ...options },
    });
  }, [sendMessage]);

  // Clear message history
  const clearHistory = useCallback(() => {
    setMessageHistory([]);
    setLastMessage(null);
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    mountedRef.current = true;

    if (opts.autoConnect) {
      connect();
    }

    return () => {
      mountedRef.current = false;
      clearTimers();
      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmount');
        wsRef.current = null;
      }
    };
  }, [opts.autoConnect, connect, clearTimers]);

  return {
    // State
    status,
    isConnected: status === 'connected',
    lastMessage,
    messageHistory,
    
    // Actions
    connect,
    disconnect,
    sendMessage,
    sendChatMessage,
    sendStreamRequest,
    clearHistory,
  };
}

// Specialized hook for chat streaming
export function useChatWebSocket(sessionId?: string, options?: Omit<UseWebSocketOptions, 'onMessage'>) {
  const [streamingResponse, setStreamingResponse] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamError, setStreamError] = useState<string | null>(null);

  const handleMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case 'stream_start':
        setStreamingResponse('');
        setIsStreaming(true);
        setStreamError(null);
        break;
      
      case 'stream_token':
        setStreamingResponse(prev => prev + (message.data as string || ''));
        break;
      
      case 'stream_end':
        setIsStreaming(false);
        break;
      
      case 'error':
        setStreamError(message.error || 'Unknown error');
        setIsStreaming(false);
        break;
    }
  }, []);

  const ws = useWebSocket('/ws/chat', {
    ...options,
    onMessage: handleMessage,
  });

  const startStream = useCallback((content: string) => {
    setStreamingResponse('');
    setStreamError(null);
    return ws.sendStreamRequest(content, { session_id: sessionId });
  }, [ws, sessionId]);

  const stopStream = useCallback(() => {
    ws.sendMessage({ type: 'stream_stop' });
    setIsStreaming(false);
  }, [ws]);

  return {
    ...ws,
    streamingResponse,
    isStreaming,
    streamError,
    startStream,
    stopStream,
  };
}

// Hook for real-time notifications
export function useNotificationWebSocket(options?: UseWebSocketOptions) {
  const [notifications, setNotifications] = useState<WebSocketMessage[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);

  const handleMessage = useCallback((message: WebSocketMessage) => {
    if (message.type === 'notification') {
      setNotifications(prev => [message, ...prev.slice(0, 49)]);
      setUnreadCount(prev => prev + 1);
    }
    options?.onMessage?.(message);
  }, [options]);

  const ws = useWebSocket('/ws/notifications', {
    ...options,
    onMessage: handleMessage,
  });

  const markAsRead = useCallback(() => {
    setUnreadCount(0);
    ws.sendMessage({ type: 'mark_read' });
  }, [ws]);

  const clearNotifications = useCallback(() => {
    setNotifications([]);
    setUnreadCount(0);
  }, []);

  return {
    ...ws,
    notifications,
    unreadCount,
    markAsRead,
    clearNotifications,
  };
}

export default useWebSocket;
