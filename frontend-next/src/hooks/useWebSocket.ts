/**
 * WebSocket Hook for Enterprise AI Assistant
 * Real-time communication with backend
 * 
 * Protocol v2 (with Model Routing):
 *   Client -> Server:
 *     {"type": "chat", "message": "...", "session_id": "...", "routing": true}
 *     {"type": "chat_legacy", "message": "..."} - Routing olmadan
 *     {"type": "feedback", "response_id": "...", "feedback_type": "correct|downgrade|upgrade"}
 *     {"type": "compare", "feedback_id": "..."}
 *     {"type": "confirm", "feedback_id": "...", "confirmed": true|false}
 *     {"type": "stop"}  - Streaming'i durdur
 *     {"type": "ping"}
 *   
 *   Server -> Client:
 *     {"type": "connected", "client_id": "...", "features": {...}, "models": {...}}
 *     {"type": "start", "ts": ...}
 *     {"type": "routing", "routing": {...}} - Model routing bilgisi
 *     {"type": "token", "content": "...", "index": N} (or "chunk")
 *     {"type": "status", "message": "...", "phase": "..."}
 *     {"type": "sources", "sources": [...]}
 *     {"type": "end", "response_id": "...", "model_size": "...", ...}
 *     {"type": "feedback_received", "feedback": {...}, "requires_comparison": bool}
 *     {"type": "compare_start", "comparison_routing": {...}}
 *     {"type": "feedback_confirmed", "feedback": {...}, "learning_applied": bool}
 *     {"type": "error", "message": "..."}
 *     {"type": "pong", "ts": ...}
 */

import { useEffect, useRef, useState, useCallback, useMemo } from 'react';

const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8001';

export type WebSocketStatus = 'connecting' | 'connected' | 'disconnected' | 'reconnecting' | 'error';

export interface WebSocketMessage {
  type: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data?: any;
  content?: string;
  message?: string;
  error?: string;
  timestamp?: string;
  index?: number;
  stream_id?: string;
  session_id?: string;
  client_id?: string;
  from_index?: number;
  
  // Chat request fields
  use_routing?: boolean;
  force_model?: string;
  web_search?: boolean;
  complexity_level?: string;
  response_mode?: string;
  
  sources?: Array<{
    title: string;
    url: string;
    domain: string;
    snippet: string;
    type: string;
    reliability: number;
  }>;
  stats?: {
    duration_ms: number;
    tokens: number;
    chars?: number;
    tokens_per_second?: number;
    was_stopped?: boolean;
  };
  phase?: string;
  ts?: number;
  
  // Model info from end message
  model_info?: {
    model_size: 'small' | 'large';
    model_name: string;
    model_icon: string;
    model_display_name: string;
    confidence: number;
    decision_source?: string;
  };
  
  // Model Routing fields
  routing?: {
    model_size: 'small' | 'large';
    model_name: string;
    model_icon: string;
    model_display_name: string;
    confidence: number;
    decision_source: string;
    reasoning?: string;
    response_id: string;
    attempt_number: number;
  };
  // Backend may send routing_info instead of routing
  routing_info?: {
    model_size: 'small' | 'large';
    model_name: string;
    model_icon: string;
    model_display_name: string;
    confidence: number;
    decision_source: string;
    reasoning?: string;
    response_id: string;
    attempt_number: number;
  };
  response_id?: string;
  model_size?: string;
  model_name?: string;
  model_icon?: string;
  model_display_name?: string;
  confidence?: number;
  decision_source?: string;
  attempt_number?: number;
  
  // Feedback fields
  feedback?: {
    id: string;
    response_id: string;
    feedback_type: string;
    status: string;
    final_decision?: string;
  };
  requires_comparison?: boolean;
  learning_applied?: boolean;
  comparison_routing?: {
    model_size: 'small' | 'large';
    model_name: string;
    model_icon: string;
    model_display_name: string;
    response_id: string;
    attempt_number: number;
  };
  
  // Outgoing message fields (client to server)
  feedback_type?: 'correct' | 'downgrade' | 'upgrade';
  comment?: string;
  query?: string;
  selected_model?: 'small' | 'large';
  
  // Features & Models from connected message
  features?: {
    real_streaming: boolean;
    cancellation: boolean;
    sources: boolean;
    model_routing?: boolean;
    feedback?: boolean;
    comparison?: boolean;
  };
  models?: Record<string, {
    name: string;
    display_name: string;
    icon: string;
  }>;
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
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const opts = useMemo(() => ({ ...DEFAULT_OPTIONS, ...options }), [
    options.autoConnect,
    options.autoReconnect,
    options.maxReconnectAttempts,
    options.reconnectDelay,
    options.pingInterval,
    options.onMessage,
    options.onStatusChange,
    options.onError,
  ]);
  
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

// Specialized hook for chat streaming (Protocol v2 with Model Routing)
export interface ModelRoutingInfo {
  model_size: 'small' | 'large';
  model_name: string;
  model_icon: string;
  model_display_name: string;
  confidence: number;
  decision_source: string;
  response_id: string;
  attempt_number: number;
  reasoning?: string;
  matched_pattern?: string;
}

export interface FeedbackInfo {
  id: string;
  response_id: string;
  feedback_type: string;
  status: string;
  final_decision?: string;
}

export interface ChatStreamState {
  streamingResponse: string;
  thinkingContent: string;  // AI düşünce süreci içeriği
  isStreaming: boolean;
  streamError: string | null;
  currentStreamId: string | null;
  sources: WebSocketMessage['sources'];
  statusMessage: string | null;
  currentPhase: string | null;  // Current pipeline phase
  stats: WebSocketMessage['stats'] | null;
  // Model Routing state
  routingInfo: ModelRoutingInfo | null;
  feedbackInfo: FeedbackInfo | null;
  requiresComparison: boolean;
  comparisonRouting: WebSocketMessage['comparison_routing'];
  learningApplied: boolean;
  // Available models (from connected message)
  availableModels: Record<string, { name: string; display_name: string; icon: string }>;
  routingEnabled: boolean;
  // Session ID from backend (for new sessions)
  receivedSessionId: string | null;
}

export function useChatWebSocket(
  sessionId?: string, 
  options?: Omit<UseWebSocketOptions, 'onMessage'>
) {
  const [streamState, setStreamState] = useState<ChatStreamState>({
    streamingResponse: '',
    thinkingContent: '',
    isStreaming: false,
    streamError: null,
    currentStreamId: null,
    sources: undefined,
    statusMessage: null,
    currentPhase: null,
    stats: null,
    // Model Routing initial state
    routingInfo: null,
    feedbackInfo: null,
    requiresComparison: false,
    comparisonRouting: undefined,
    learningApplied: false,
    availableModels: {},
    routingEnabled: false,
    receivedSessionId: null,
  });

  // Generate unique client ID
  const clientIdRef = useRef<string>(`client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);

  const handleMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case 'connected':
        console.log('[WS Chat] Connected with client_id:', message.client_id);
        // Store available models and features
        setStreamState(prev => ({
          ...prev,
          availableModels: message.models || {},
          routingEnabled: message.features?.model_routing || false,
        }));
        break;

      case 'start':
        // Backend'den gelen session_id'yi yakala (yeni session oluşturulduğunda)
        if (message.session_id) {
          console.log('📌 [WS] Received session_id from backend:', message.session_id);
        }
        setStreamState(prev => ({
          ...prev,
          streamingResponse: '',
          thinkingContent: '',
          isStreaming: true,
          streamError: null,
          currentStreamId: message.stream_id || null,
          sources: undefined,
          statusMessage: null,
          currentPhase: 'routing',  // Initial phase
          stats: null,
          routingInfo: null,
          feedbackInfo: null,
          requiresComparison: false,
          comparisonRouting: undefined,
          learningApplied: false,
          receivedSessionId: message.session_id || null,
        }));
        break;

      // Model Routing - Routing bilgisi geldi
      case 'routing':
        setStreamState(prev => ({
          ...prev,
          routingInfo: message.routing_info || message.routing || null,
        }));
        break;
      
      case 'token':
      case 'chunk':  // Backend 'chunk' olarak da gönderebilir
        setStreamState(prev => ({
          ...prev,
          streamingResponse: prev.streamingResponse + (message.content || ''),
          statusMessage: null,
          currentPhase: 'generate',  // Tokens mean we're generating
        }));
        break;

      case 'thinking':  // AI düşünce süreci
        setStreamState(prev => ({
          ...prev,
          thinkingContent: prev.thinkingContent + (message.content || ''),
          currentPhase: 'thinking',
        }));
        break;

      case 'status':
      case 'processing':
        setStreamState(prev => ({
          ...prev,
          statusMessage: message.message || null,
          currentPhase: message.phase || prev.currentPhase,
        }));
        break;

      case 'sources':
        setStreamState(prev => ({
          ...prev,
          sources: message.sources,
        }));
        break;
      
      case 'end':
      case 'complete':  // Backend may send 'complete' or 'end'
        // End mesajı artık model bilgilerini de içerir
        setStreamState(prev => ({
          ...prev,
          isStreaming: false,
          stats: message.stats || null,
          statusMessage: null,
          currentPhase: 'complete',  // Mark as complete
          // Model bilgilerini routingInfo'ya ekle (eğer yoksa)
          routingInfo: prev.routingInfo || (message.model_info ? {
            ...message.model_info,
            decision_source: message.model_info.decision_source || '',
            response_id: message.response_id || '',
            attempt_number: 1,
            reasoning: '',
          } as ModelRoutingInfo : null) || (message.response_id ? {
            model_size: message.model_size as 'small' | 'large',
            model_name: message.model_name || '',
            model_icon: message.model_icon || '',
            model_display_name: message.model_display_name || '',
            confidence: message.confidence || 0,
            decision_source: message.decision_source || '',
            response_id: message.response_id || '',
            attempt_number: message.attempt_number || 1,
          } : null),
        }));
        break;

      case 'stopped':
      case 'cancelled':
        setStreamState(prev => ({
          ...prev,
          isStreaming: false,
          statusMessage: 'Yanıt durduruldu',
        }));
        break;
      
      // Feedback received
      case 'feedback_received':
        setStreamState(prev => ({
          ...prev,
          feedbackInfo: message.feedback || null,
          requiresComparison: message.requires_comparison || false,
          statusMessage: message.message || null,
        }));
        break;
      
      // Comparison started
      case 'compare_start':
        setStreamState(prev => ({
          ...prev,
          comparisonRouting: message.comparison_routing || undefined,
          isStreaming: true,
          streamingResponse: '',
          thinkingContent: '',
        }));
        break;
      
      // Feedback confirmed
      case 'feedback_confirmed':
        setStreamState(prev => ({
          ...prev,
          feedbackInfo: message.feedback || null,
          learningApplied: message.learning_applied || false,
          requiresComparison: false,
          statusMessage: message.message || null,
        }));
        break;
      
      case 'error':
        console.error('[WS Chat] Received error:', message.error || message.message);
        setStreamState(prev => ({
          ...prev,
          streamError: message.error || message.message || 'Bilinmeyen hata',
          isStreaming: false,
          statusMessage: null,
          currentPhase: 'error',
        }));
        break;

      case 'pong':
        // Keepalive response, ignore
        break;
      
      default:
        // Log unknown message types for debugging
        if (message.type && !['pong', 'ping'].includes(message.type)) {
          console.log('[WS Chat] Unknown message type:', message.type, message);
        }
    }
  }, []);

  // Connect with client_id in URL
  const ws = useWebSocket(`/ws/chat/${clientIdRef.current}`, {
    ...options,
    onMessage: handleMessage,
  });

  // Reset streaming state when WebSocket disconnects
  useEffect(() => {
    if (ws.status === 'disconnected' || ws.status === 'error') {
      setStreamState(prev => {
        if (prev.isStreaming) {
          console.warn('[WS Chat] Connection lost during streaming, resetting state');
          return {
            ...prev,
            isStreaming: false,
            streamError: 'Bağlantı kesildi',
            statusMessage: null,
            currentPhase: 'error',
          };
        }
        return prev;
      });
    }
  }, [ws.status]);

  const startStream = useCallback((content: string, streamSessionId?: string) => {
    // Reset state
    setStreamState(prev => ({
      ...prev,
      streamingResponse: '',
      thinkingContent: '',
      streamError: null,
      sources: undefined,
      statusMessage: null,
      stats: null,
    }));

    // Send chat message in v2 format
    return ws.sendMessage({
      type: 'chat',
      data: {
        message: content,
        session_id: streamSessionId || sessionId,
      },
    });
  }, [ws, sessionId]);

  // Send message in v2 format (message at root level) - WITH routing support
  const sendChatMessage = useCallback((content: string, chatSessionId?: string, useRouting: boolean = true) => {
    setStreamState(prev => ({
      ...prev,
      streamingResponse: '',
      thinkingContent: '',
      streamError: null,
      sources: undefined,
      statusMessage: null,
      stats: null,
      currentPhase: 'routing',  // Reset phase
      routingInfo: null,
    }));

    return ws.sendMessage({
      type: 'chat',
      message: content,
      session_id: chatSessionId || sessionId,
      use_routing: useRouting,  // Enable model routing by default
    });
  }, [ws, sessionId]);

  const stopStream = useCallback(() => {
    ws.sendMessage({ type: 'stop' });
    setStreamState(prev => ({
      ...prev,
      isStreaming: false,
    }));
  }, [ws]);

  const resumeStream = useCallback((streamId: string, fromIndex: number = 0) => {
    ws.sendMessage({
      type: 'resume',
      stream_id: streamId,
      from_index: fromIndex,
    });
  }, [ws]);

  // ============ Model Routing Methods ============

  /**
   * Enhanced chat message with model routing support
   * @param content - Message content
   * @param opts - Routing options: use_routing, force_model
   */
  const sendRoutedMessage = useCallback((
    content: string,
    opts?: {
      sessionId?: string;
      useRouting?: boolean;
      forceModel?: 'small' | 'large';
      webSearch?: boolean;
      complexityLevel?: 'auto' | 'simple' | 'normal' | 'comprehensive' | 'research';
      responseMode?: 'normal' | 'analytical' | 'creative' | 'technical';
    }
  ) => {
    // 🔍 DEBUG: Log session ID being sent
    const effectiveSessionId = opts?.sessionId || sessionId;
    console.log('📤 [WS DEBUG] sendRoutedMessage called:', {
      content: content.substring(0, 50) + '...',
      optsSessionId: opts?.sessionId,
      hookSessionId: sessionId,
      effectiveSessionId: effectiveSessionId,
      timestamp: new Date().toISOString()
    });

    setStreamState(prev => ({
      ...prev,
      streamingResponse: '',
      thinkingContent: '',
      streamError: null,
      sources: undefined,
      statusMessage: null,
      stats: null,
      routingInfo: null,
      feedbackInfo: null,
      requiresComparison: false,
      comparisonRouting: undefined,
      learningApplied: false,
    }));

    const messagePayload = {
      type: 'chat',
      message: content,
      session_id: effectiveSessionId,
      use_routing: opts?.useRouting !== false, // Default true
      force_model: opts?.forceModel,
      web_search: opts?.webSearch || false,
      complexity_level: opts?.complexityLevel || 'auto',
      response_mode: opts?.responseMode || 'normal',
    };
    
    console.log('📤 [WS DEBUG] Sending payload:', messagePayload);
    return ws.sendMessage(messagePayload);
  }, [ws, sessionId]);

  /**
   * Submit feedback for a model response
   * @param responseId - ID of the response
   * @param feedbackType - Type: 'correct', 'downgrade', 'upgrade'
   * @param comment - Optional user comment
   */
  const sendFeedback = useCallback((
    responseId: string,
    feedbackType: 'correct' | 'downgrade' | 'upgrade',
    comment?: string
  ) => {
    return ws.sendMessage({
      type: 'feedback',
      response_id: responseId,
      feedback_type: feedbackType,
      comment,
    });
  }, [ws]);

  /**
   * Request comparison between small and large model responses
   * @param responseId - ID of the original response
   * @param query - Original query text
   */
  const requestComparison = useCallback((
    responseId: string,
    query: string
  ) => {
    setStreamState(prev => ({
      ...prev,
      streamingResponse: '',
      thinkingContent: '',
      isStreaming: true,
    }));

    return ws.sendMessage({
      type: 'compare',
      response_id: responseId,
      query,
    });
  }, [ws]);

  /**
   * Confirm feedback after comparison
   * @param responseId - ID of the response
   * @param selectedModel - Which model user preferred: 'small' or 'large'
   * @param comment - Optional comment
   */
  const confirmFeedback = useCallback((
    responseId: string,
    selectedModel: 'small' | 'large',
    comment?: string
  ) => {
    return ws.sendMessage({
      type: 'confirm',
      response_id: responseId,
      selected_model: selectedModel,
      comment,
    });
  }, [ws]);

  /**
   * Reset routing state (for UI cleanup)
   */
  const resetRoutingState = useCallback(() => {
    setStreamState(prev => ({
      ...prev,
      routingInfo: null,
      feedbackInfo: null,
      requiresComparison: false,
      comparisonRouting: undefined,
      learningApplied: false,
    }));
  }, []);

  return {
    ...ws,
    ...streamState,
    startStream,
    sendChatMessage,
    stopStream,
    resumeStream,
    clientId: clientIdRef.current,
    // Model Routing methods
    sendRoutedMessage,
    sendFeedback,
    requestComparison,
    confirmFeedback,
    resetRoutingState,
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
