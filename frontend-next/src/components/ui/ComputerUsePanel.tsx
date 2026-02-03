'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Monitor, Play, Square, Check, X, AlertTriangle,
  Loader2, ChevronRight, Clock, Shield, Eye,
  Mouse, Keyboard, AppWindow, RotateCcw, History,
  ShieldAlert, ShieldCheck, AlertOctagon, Power, RefreshCw
} from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ComputerStatus {
  running: boolean;
  security_mode: string;
  current_plan_id: string | null;
  pending_approvals: number;
  emergency_stopped: boolean;
}

interface PendingApproval {
  request_id: string;
  action_type: string;
  description: string;
  params: Record<string, any>;
  risk_level: string;
  timestamp: string;
}

interface ActionHistory {
  plan_id: string;
  action_type: string;
  status: string;
  timestamp: string;
  duration?: number;
}

export default function ComputerUsePanel() {
  // State
  const [isOpen, setIsOpen] = useState(false);
  const [status, setStatus] = useState<ComputerStatus | null>(null);
  const [approvals, setApprovals] = useState<PendingApproval[]>([]);
  const [history, setHistory] = useState<ActionHistory[]>([]);
  const [taskInput, setTaskInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'task' | 'approvals' | 'history'>('task');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [wsMessages, setWsMessages] = useState<string[]>([]);

  // Fetch status
  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/computer/status`);
      const data = await res.json();
      setStatus(data);
    } catch (e) {
      console.error('Computer Use status error:', e);
    }
  }, []);

  // Fetch pending approvals
  const fetchApprovals = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/computer/approvals`);
      const data = await res.json();
      // Backend returns 'pending' not 'approvals'
      const pendingApprovals = data.pending || data.approvals || [];
      // Transform to expected format
      const transformed = pendingApprovals.map((item: any) => ({
        request_id: item.id,
        action_type: item.action?.action_type || 'unknown',
        description: item.action?.description || '',
        risk_level: item.action?.risk_level || 'medium',
        params: {
          x: item.action?.x,
          y: item.action?.y,
          text: item.action?.text,
          keys: item.action?.keys,
        },
        plan_id: item.plan_id,
        expires_at: item.expires_at,
      }));
      setApprovals(transformed);
    } catch (err) {
      console.error('Approvals error:', err);
    }
  }, []);

  // Fetch history
  const fetchHistory = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/computer/history?limit=20`);
      const data = await res.json();
      setHistory(data.history || []);
    } catch (e) {
      console.error('History error:', e);
    }
  }, []);

  // Poll for updates
  useEffect(() => {
    if (isOpen) {
      fetchStatus();
      fetchApprovals();
      fetchHistory();

      const interval = setInterval(() => {
        fetchStatus();
        fetchApprovals();
      }, 3000);

      return () => clearInterval(interval);
    }
  }, [isOpen, fetchStatus, fetchApprovals, fetchHistory]);

  // Create task
  const createTask = async () => {
    if (!taskInput.trim()) return;

    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const res = await fetch(`${API_BASE}/api/computer/task`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task: taskInput,
        }),
      });

      const data = await res.json();

      if (data.success) {
        const planId = data.plan?.id || data.plan_id;
        setSuccess(`Task created: ${planId}`);
        setTaskInput('');
        fetchStatus();

        // Connect WebSocket for real-time updates
        if (planId) {
          connectWebSocket(planId);
        }
      } else {
        setError(data.error || data.detail || 'Failed to create task');
      }
    } catch (e) {
      setError('Connection error');
    } finally {
      setIsLoading(false);
    }
  };

  // WebSocket connection
  const connectWebSocket = (planId: string) => {
    if (wsRef.current) {
      wsRef.current.close();
    }

    const wsUrl = `${API_BASE.replace('http', 'ws')}/api/computer/ws/execute/${planId}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setWsConnected(true);
      setWsMessages([]);
    };

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      setWsMessages(prev => [...prev, msg.message || JSON.stringify(msg)]);

      if (msg.type === 'approval_required') {
        fetchApprovals();
      } else if (msg.type === 'completed' || msg.type === 'failed') {
        fetchStatus();
        fetchHistory();
      }
    };

    ws.onclose = () => {
      setWsConnected(false);
    };

    ws.onerror = () => {
      setError('WebSocket connection failed');
    };

    wsRef.current = ws;
  };

  // Approve action
  const approveAction = async (requestId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/computer/approve/${requestId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });

      if (res.ok) {
        fetchApprovals();
        setSuccess('Action approved');
      } else {
        const data = await res.json();
        setError(data.detail || 'Failed to approve action');
      }
    } catch (e) {
      setError('Failed to approve action: Network error');
    }
  };

  // Reject action
  const rejectAction = async (requestId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/computer/reject/${requestId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });

      if (res.ok) {
        fetchApprovals();
        setSuccess('Action rejected');
      } else {
        const data = await res.json();
        setError(data.detail || 'Failed to reject action');
      }
    } catch (e) {
      setError('Failed to reject action: Network error');
    }
  };

  // Emergency stop
  const emergencyStop = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/computer/emergency-stop`, {
        method: 'POST',
      });

      if (res.ok) {
        fetchStatus();
        setSuccess('Emergency stop activated');

        if (wsRef.current) {
          wsRef.current.close();
        }
      }
    } catch (e) {
      setError('Failed to activate emergency stop');
    }
  };

  // Reset emergency
  const resetEmergency = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/computer/reset-emergency`, {
        method: 'POST',
      });

      if (res.ok) {
        fetchStatus();
        setSuccess('Emergency stop reset');
      }
    } catch (e) {
      setError('Failed to reset emergency stop');
    }
  };

  // Get risk level color
  const getRiskColor = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'low': return 'text-green-400 bg-green-500/10';
      case 'medium': return 'text-yellow-400 bg-yellow-500/10';
      case 'high': return 'text-orange-400 bg-orange-500/10';
      case 'critical': return 'text-red-400 bg-red-500/10';
      default: return 'text-gray-400 bg-gray-500/10';
    }
  };

  // Get action icon
  const getActionIcon = (actionType: string) => {
    switch (actionType) {
      case 'click':
      case 'double_click':
      case 'right_click':
        return <Mouse className="w-4 h-4" />;
      case 'type':
      case 'hotkey':
        return <Keyboard className="w-4 h-4" />;
      case 'open_app':
        return <AppWindow className="w-4 h-4" />;
      case 'screenshot':
        return <Eye className="w-4 h-4" />;
      default:
        return <Monitor className="w-4 h-4" />;
    }
  };

  // Floating button when closed
  if (!isOpen) {
    return (
      <motion.button
        onClick={() => setIsOpen(true)}
        className={`fixed bottom-40 right-4 z-50 p-3 rounded-full shadow-lg transition-colors ${status?.pending_approvals
            ? 'bg-orange-500 hover:bg-orange-600 animate-pulse'
            : status?.emergency_stopped
              ? 'bg-red-600 hover:bg-red-700'
              : 'bg-blue-600 hover:bg-blue-700'
          } text-white`}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        title="Computer Use Agent"
      >
        <Monitor className="w-6 h-6" />
        {status?.pending_approvals && status.pending_approvals > 0 && (
          <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
            {status.pending_approvals}
          </span>
        )}
      </motion.button>
    );
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, scale: 0.9, x: 100 }}
        animate={{ opacity: 1, scale: 1, x: 0 }}
        exit={{ opacity: 0, scale: 0.9, x: 100 }}
        className="fixed bottom-4 right-4 z-50 w-[420px] bg-gray-900 rounded-2xl shadow-2xl border border-gray-700 overflow-hidden"
      >
        {/* Header */}
        <div className={`flex items-center justify-between p-4 border-b border-gray-700 ${status?.emergency_stopped
            ? 'bg-gradient-to-r from-red-900/50 to-red-800/50'
            : 'bg-gradient-to-r from-blue-900/50 to-cyan-900/50'
          }`}>
          <div className="flex items-center gap-2">
            <Monitor className="w-5 h-5 text-blue-400" />
            <span className="font-semibold text-white">Computer Use Agent</span>
            {status?.running && (
              <span className="px-2 py-0.5 text-xs bg-green-500/20 text-green-400 rounded-full animate-pulse">
                Running
              </span>
            )}
            {status?.emergency_stopped && (
              <span className="px-2 py-0.5 text-xs bg-red-500/20 text-red-400 rounded-full">
                STOPPED
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            {/* Emergency Stop Button */}
            {!status?.emergency_stopped ? (
              <button
                onClick={emergencyStop}
                className="p-1.5 bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
                title="Emergency Stop"
              >
                <Power className="w-4 h-4 text-white" />
              </button>
            ) : (
              <button
                onClick={resetEmergency}
                className="p-1.5 bg-green-600 hover:bg-green-700 rounded-lg transition-colors"
                title="Reset Emergency Stop"
              >
                <RotateCcw className="w-4 h-4 text-white" />
              </button>
            )}
            <button
              onClick={() => setIsOpen(false)}
              className="p-1.5 hover:bg-gray-700 rounded-lg transition-colors"
            >
              <X className="w-4 h-4 text-gray-400" />
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-700">
          <button
            onClick={() => setActiveTab('task')}
            className={`flex-1 py-2 text-sm font-medium transition-colors ${activeTab === 'task'
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-gray-300'
              }`}
          >
            New Task
          </button>
          <button
            onClick={() => { setActiveTab('approvals'); fetchApprovals(); }}
            className={`flex-1 py-2 text-sm font-medium transition-colors relative ${activeTab === 'approvals'
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-gray-300'
              }`}
          >
            Approvals
            {approvals.length > 0 && (
              <span className="ml-1 px-1.5 py-0.5 text-xs bg-orange-500 text-white rounded-full">
                {approvals.length}
              </span>
            )}
          </button>
          <button
            onClick={() => { setActiveTab('history'); fetchHistory(); }}
            className={`flex-1 py-2 text-sm font-medium transition-colors ${activeTab === 'history'
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-gray-300'
              }`}
          >
            History
          </button>
        </div>

        {/* Content */}
        <div className="p-4 max-h-[50vh] overflow-y-auto">
          {/* Error/Success Messages */}
          <AnimatePresence>
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="mb-3 p-3 bg-red-500/10 border border-red-500/30 rounded-lg flex items-center gap-2 text-red-400"
              >
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                <span className="text-sm">{error}</span>
                <button onClick={() => setError(null)} className="ml-auto">
                  <X className="w-4 h-4" />
                </button>
              </motion.div>
            )}

            {success && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="mb-3 p-3 bg-green-500/10 border border-green-500/30 rounded-lg flex items-center gap-2 text-green-400"
              >
                <Check className="w-4 h-4 flex-shrink-0" />
                <span className="text-sm">{success}</span>
                <button onClick={() => setSuccess(null)} className="ml-auto">
                  <X className="w-4 h-4" />
                </button>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Task Tab */}
          {activeTab === 'task' && (
            <div className="space-y-4">
              {/* Security Mode Indicator */}
              <div className="flex items-center gap-2 p-2 bg-gray-800 rounded-lg">
                <ShieldCheck className="w-4 h-4 text-green-400" />
                <span className="text-sm text-gray-300">
                  Security Mode: <span className="text-green-400 font-medium">{status?.security_mode || 'CONFIRM_ALL'}</span>
                </span>
              </div>

              {/* Task Input */}
              <div className="space-y-2">
                <label className="text-sm text-gray-400">Describe the task:</label>
                <textarea
                  value={taskInput}
                  onChange={(e) => setTaskInput(e.target.value)}
                  placeholder="e.g., Open Chrome and search for 'weather'"
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 resize-none"
                  rows={3}
                  disabled={status?.emergency_stopped}
                />
              </div>

              <button
                onClick={createTask}
                disabled={isLoading || !taskInput.trim() || status?.emergency_stopped}
                className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg flex items-center justify-center gap-2 transition-colors"
              >
                {isLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Play className="w-5 h-5" />
                )}
                <span>Create & Execute Task</span>
              </button>

              {/* WebSocket Messages */}
              {wsConnected && wsMessages.length > 0 && (
                <div className="mt-4 p-3 bg-gray-800 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                    <span className="text-sm font-medium text-gray-300">Live Updates</span>
                  </div>
                  <div className="space-y-1 max-h-32 overflow-y-auto">
                    {wsMessages.slice(-5).map((msg, i) => (
                      <div key={i} className="text-xs text-gray-400 font-mono">
                        {msg}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Approvals Tab */}
          {activeTab === 'approvals' && (
            <div className="space-y-4">
              {/* Header */}
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-white">Pending Actions</h3>
                <button
                  onClick={fetchApprovals}
                  className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
                  title="Refresh"
                >
                  <RefreshCw className="w-4 h-4 text-gray-400" />
                </button>
              </div>

              {approvals.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <Shield className="w-16 h-16 mx-auto mb-3 opacity-50" />
                  <p className="text-lg">No pending approvals</p>
                  <p className="text-sm mt-1">Actions will appear here for your review</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Approve All / Reject All */}
                  <div className="flex gap-2">
                    <button
                      onClick={() => approvals.forEach(a => approveAction(a.request_id))}
                      className="flex-1 py-2 px-4 bg-green-600 hover:bg-green-700 rounded-lg flex items-center justify-center gap-2 text-sm font-medium transition-colors"
                    >
                      <Check className="w-4 h-4" />
                      Approve All ({approvals.length})
                    </button>
                    <button
                      onClick={() => approvals.forEach(a => rejectAction(a.request_id))}
                      className="flex-1 py-2 px-4 bg-red-600 hover:bg-red-700 rounded-lg flex items-center justify-center gap-2 text-sm font-medium transition-colors"
                    >
                      <X className="w-4 h-4" />
                      Reject All
                    </button>
                  </div>

                  {approvals.map((approval, index) => (
                    <motion.div
                      key={approval.request_id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="p-4 bg-gradient-to-r from-gray-800 to-gray-800/50 border-2 border-orange-500/50 rounded-xl shadow-lg"
                    >
                      {/* Step Number & Action Type */}
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 bg-orange-500 rounded-full flex items-center justify-center text-white font-bold">
                            {index + 1}
                          </div>
                          <div>
                            <span className="font-semibold text-white text-lg capitalize">
                              {(approval.action_type || 'unknown').replace('_', ' ')}
                            </span>
                            <span className={`ml-2 px-2 py-0.5 text-xs rounded-full ${getRiskColor(approval.risk_level || 'low')}`}>
                              {approval.risk_level || 'low'}
                            </span>
                          </div>
                        </div>
                        {getActionIcon(approval.action_type || 'unknown')}
                      </div>

                      {/* Description */}
                      <p className="text-gray-300 mb-4 text-base">{approval.description}</p>

                      {/* Action Details */}
                      <div className="mb-4 p-3 bg-gray-900 rounded-lg">
                        <div className="text-sm text-gray-400 space-y-1">
                          {approval.params?.keys && (
                            <div className="flex items-center gap-2">
                              <span className="text-gray-500">Keys:</span>
                              <code className="px-2 py-0.5 bg-gray-800 rounded text-blue-400">
                                {Array.isArray(approval.params.keys) ? approval.params.keys.join(' + ') : approval.params.keys}
                              </code>
                            </div>
                          )}
                          {approval.params?.text && (
                            <div className="flex items-center gap-2">
                              <span className="text-gray-500">Text:</span>
                              <code className="px-2 py-0.5 bg-gray-800 rounded text-green-400">
                                &ldquo;{approval.params.text}&rdquo;
                              </code>
                            </div>
                          )}
                          {approval.params?.x !== null && approval.params?.y !== null && (
                            <div className="flex items-center gap-2">
                              <span className="text-gray-500">Position:</span>
                              <code className="px-2 py-0.5 bg-gray-800 rounded text-purple-400">
                                ({approval.params.x}, {approval.params.y})
                              </code>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Action Buttons - Large and Clear */}
                      <div className="flex gap-3">
                        <button
                          onClick={() => approveAction(approval.request_id)}
                          className="flex-1 py-3 px-4 bg-green-600 hover:bg-green-500 rounded-xl flex items-center justify-center gap-2 text-base font-semibold transition-all transform hover:scale-[1.02] shadow-lg"
                        >
                          <Check className="w-5 h-5" />
                          ✓ APPROVE
                        </button>
                        <button
                          onClick={() => rejectAction(approval.request_id)}
                          className="flex-1 py-3 px-4 bg-red-600 hover:bg-red-500 rounded-xl flex items-center justify-center gap-2 text-base font-semibold transition-all transform hover:scale-[1.02] shadow-lg"
                        >
                          <X className="w-5 h-5" />
                          ✗ REJECT
                        </button>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* History Tab */}
          {activeTab === 'history' && (
            <div className="space-y-2">
              {history.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <History className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>No action history</p>
                </div>
              ) : (
                history.map((item, i) => (
                  <div
                    key={i}
                    className="p-2 bg-gray-800 rounded-lg flex items-center gap-3"
                  >
                    <div className={`p-1.5 rounded ${item.status === 'success' ? 'bg-green-500/20' :
                        item.status === 'failed' ? 'bg-red-500/20' :
                          'bg-gray-700'
                      }`}>
                      {getActionIcon(item.action_type || 'unknown')}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm text-white capitalize truncate">
                        {(item.action_type || 'unknown').replace('_', ' ')}
                      </div>
                      <div className="text-xs text-gray-500">
                        {item.timestamp ? new Date(item.timestamp).toLocaleTimeString() : '-'}
                      </div>
                    </div>
                    <span className={`text-xs ${item.status === 'success' ? 'text-green-400' :
                        item.status === 'failed' ? 'text-red-400' :
                          'text-gray-400'
                      }`}>
                      {item.status}
                    </span>
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-gray-700 bg-gray-900/50">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span className="flex items-center gap-1">
              <Shield className="w-3 h-3" />
              All actions require approval
            </span>
            <span>
              Plan: {status?.current_plan_id?.slice(0, 8) || 'None'}
            </span>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
