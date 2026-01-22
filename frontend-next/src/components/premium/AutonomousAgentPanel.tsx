'use client';

import React, { useState, useEffect } from 'react';
import { 
  Bot, 
  Target, 
  Play, 
  Pause, 
  Square,
  Plus,
  Trash2,
  CheckCircle2,
  Clock,
  AlertCircle,
  Loader2,
  ChevronDown,
  ChevronUp,
  Sparkles
} from 'lucide-react';

interface AutonomousAgentPanelProps {
  className?: string;
}

interface Session {
  id: string;
  goal: string;
  status: string;
  iterations: number;
  final_result?: string;
  error?: string;
}

interface SessionUpdate {
  type: string;
  step?: number;
  action_type?: string;
  result?: string;
  reflection?: string;
  status?: string;
}

export function AutonomousAgentPanel({ className = '' }: AutonomousAgentPanelProps) {
  const [goal, setGoal] = useState('');
  const [maxIterations, setMaxIterations] = useState(10);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSession, setActiveSession] = useState<Session | null>(null);
  const [updates, setUpdates] = useState<SessionUpdate[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [expandedSession, setExpandedSession] = useState<string | null>(null);
  const [status, setStatus] = useState<any>(null);

  useEffect(() => {
    fetchStatus();
    fetchSessions();
  }, []);

  const fetchStatus = async () => {
    try {
      const res = await fetch('http://localhost:8001/api/autonomous/status');
      const data = await res.json();
      setStatus(data);
    } catch (error) {
      console.error('Failed to fetch status:', error);
    }
  };

  const fetchSessions = async () => {
    try {
      const res = await fetch('http://localhost:8001/api/autonomous/sessions');
      const data = await res.json();
      setSessions(data.sessions || []);
    } catch (error) {
      console.error('Failed to fetch sessions:', error);
    }
  };

  const startAgent = async () => {
    if (!goal.trim()) return;

    setIsRunning(true);
    setUpdates([]);
    setActiveSession(null);

    try {
      // Create and run via WebSocket for real-time updates
      const ws = new WebSocket(`ws://localhost:8001/api/autonomous/ws/new`);

      ws.onopen = () => {
        ws.send(JSON.stringify({
          goal: goal,
          max_iterations: maxIterations,
        }));
      };

      ws.onmessage = (event) => {
        const update = JSON.parse(event.data);
        
        if (update.type === 'session_created') {
          setActiveSession({
            id: update.session_id,
            goal: goal,
            status: 'running',
            iterations: 0,
          });
        } else if (update.type === 'update') {
          setUpdates(prev => [...prev, update]);
        } else if (update.type === 'completed') {
          setActiveSession(prev => prev ? {
            ...prev,
            status: update.status,
            iterations: update.iterations,
            final_result: update.final_result,
            error: update.error,
          } : null);
          setIsRunning(false);
          fetchSessions();
        } else if (update.type === 'error') {
          setIsRunning(false);
          alert('Agent hatası: ' + update.message);
        }
      };

      ws.onerror = () => {
        // Fallback to REST API
        runWithRestApi();
      };

      ws.onclose = () => {
        if (isRunning) {
          setIsRunning(false);
        }
      };
    } catch (error) {
      runWithRestApi();
    }
  };

  const runWithRestApi = async () => {
    try {
      const res = await fetch('http://localhost:8001/api/autonomous/run?goal=' + encodeURIComponent(goal) + '&max_iterations=' + maxIterations, {
        method: 'POST',
      });
      const data = await res.json();
      
      setActiveSession({
        id: data.session_id,
        goal: goal,
        status: data.status,
        iterations: data.iterations,
        final_result: data.result,
        error: data.error,
      });
      
      fetchSessions();
    } catch (error) {
      console.error('Failed to run agent:', error);
      alert('Agent başlatılamadı');
    } finally {
      setIsRunning(false);
    }
  };

  const stopAgent = async () => {
    if (!activeSession) return;

    try {
      await fetch(`http://localhost:8001/api/autonomous/sessions/${activeSession.id}/stop`, {
        method: 'POST',
      });
      setIsRunning(false);
    } catch (error) {
      console.error('Failed to stop agent:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'text-blue-400';
      case 'completed':
        return 'text-green-400';
      case 'failed':
        return 'text-red-400';
      case 'stopped':
        return 'text-yellow-400';
      default:
        return 'text-gray-400';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <Loader2 className="w-4 h-4 animate-spin" />;
      case 'completed':
        return <CheckCircle2 className="w-4 h-4" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4" />;
      default:
        return <Clock className="w-4 h-4" />;
    }
  };

  const exampleGoals = [
    "Proje için bir README.md dosyası oluştur",
    "Kod tabanındaki güvenlik açıklarını ara ve raporla",
    "API endpoint'lerini dokümante et",
    "Birim testleri için test senaryoları hazırla",
  ];

  return (
    <div className={`bg-gradient-to-br from-blue-900/30 to-cyan-900/30 rounded-xl border border-blue-500/30 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-500/20 rounded-lg">
            <Bot className="w-6 h-6 text-blue-400" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">Otonom AI Agent</h2>
            <p className="text-sm text-gray-400">Hedef belirle, agent çalışsın</p>
          </div>
        </div>
        <div className={`px-3 py-1 rounded-full text-xs ${status?.status === 'available' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'}`}>
          {status?.total_sessions || 0} oturum
        </div>
      </div>

      {/* Goal Input */}
      <div className="p-4 border-b border-white/10">
        <div className="flex items-center gap-2 mb-3">
          <Target className="w-4 h-4 text-blue-400" />
          <label className="text-sm text-gray-300">Hedef</label>
        </div>
        <textarea
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
          placeholder="Agent'ın gerçekleştirmesini istediğiniz görevi tanımlayın..."
          className="w-full h-24 bg-white/5 text-white rounded-lg p-3 border border-white/10 focus:border-blue-500/50 focus:outline-none resize-none"
          disabled={isRunning}
        />

        {/* Example Goals */}
        <div className="flex flex-wrap gap-2 mt-3">
          {exampleGoals.map((example, idx) => (
            <button
              key={idx}
              onClick={() => setGoal(example)}
              className="px-3 py-1 bg-white/5 hover:bg-white/10 rounded text-xs text-gray-400 hover:text-white transition-colors"
              disabled={isRunning}
            >
              {example.substring(0, 30)}...
            </button>
          ))}
        </div>

        {/* Settings & Run */}
        <div className="flex items-center justify-between mt-4">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-400">Maks. İterasyon:</label>
              <input
                type="number"
                value={maxIterations}
                onChange={(e) => setMaxIterations(parseInt(e.target.value) || 10)}
                min={1}
                max={50}
                className="w-16 bg-white/5 text-white rounded px-2 py-1 text-sm border border-white/10"
                disabled={isRunning}
              />
            </div>
          </div>

          <div className="flex items-center gap-2">
            {isRunning ? (
              <button
                onClick={stopAgent}
                className="flex items-center gap-2 px-4 py-2 bg-red-500 hover:bg-red-600 rounded-lg text-white"
              >
                <Square className="w-4 h-4" />
                Durdur
              </button>
            ) : (
              <button
                onClick={startAgent}
                disabled={!goal.trim()}
                className={`flex items-center gap-2 px-6 py-2 rounded-lg font-medium ${
                  goal.trim() 
                    ? 'bg-blue-500 hover:bg-blue-600 text-white' 
                    : 'bg-gray-600 text-gray-400 cursor-not-allowed'
                }`}
              >
                <Sparkles className="w-4 h-4" />
                Başlat
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Live Updates */}
      {(isRunning || activeSession) && (
        <div className="p-4 border-b border-white/10">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-white flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-blue-400" />
              Canlı İlerleme
            </h3>
            {activeSession && (
              <span className={`text-xs ${getStatusColor(activeSession.status)}`}>
                {getStatusIcon(activeSession.status)}
                <span className="ml-1">{activeSession.status}</span>
              </span>
            )}
          </div>

          <div className="bg-black/30 rounded-lg p-3 max-h-48 overflow-y-auto space-y-2">
            {updates.length === 0 ? (
              <p className="text-sm text-gray-400 text-center py-4">
                {isRunning ? 'Agent başlatılıyor...' : 'Henüz güncelleme yok'}
              </p>
            ) : (
              updates.map((update, idx) => (
                <div key={idx} className="text-sm border-l-2 border-blue-500/50 pl-3 py-1">
                  <div className="text-blue-400 font-medium">
                    Adım {update.step}: {update.action_type}
                  </div>
                  {update.result && (
                    <div className="text-gray-300 text-xs mt-1 truncate">
                      {update.result.substring(0, 100)}...
                    </div>
                  )}
                </div>
              ))
            )}
          </div>

          {/* Final Result */}
          {activeSession?.final_result && (
            <div className="mt-4 bg-green-500/10 border border-green-500/30 rounded-lg p-3">
              <h4 className="text-sm font-medium text-green-400 mb-2">Sonuç</h4>
              <p className="text-sm text-gray-300 whitespace-pre-wrap">
                {activeSession.final_result}
              </p>
            </div>
          )}

          {activeSession?.error && (
            <div className="mt-4 bg-red-500/10 border border-red-500/30 rounded-lg p-3">
              <h4 className="text-sm font-medium text-red-400 mb-2">Hata</h4>
              <p className="text-sm text-gray-300">{activeSession.error}</p>
            </div>
          )}
        </div>
      )}

      {/* Previous Sessions */}
      <div className="p-4">
        <h3 className="text-sm font-medium text-gray-400 mb-3">Önceki Oturumlar</h3>
        
        {sessions.length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-4">Henüz oturum yok</p>
        ) : (
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {sessions.slice(0, 10).map((session) => (
              <div
                key={session.id}
                className="bg-white/5 rounded-lg p-3 cursor-pointer hover:bg-white/10 transition-colors"
                onClick={() => setExpandedSession(expandedSession === session.id ? null : session.id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={getStatusColor(session.status)}>
                      {getStatusIcon(session.status)}
                    </span>
                    <span className="text-sm text-white truncate max-w-[200px]">
                      {session.goal}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-400">{session.iterations} adım</span>
                    {expandedSession === session.id ? (
                      <ChevronUp className="w-4 h-4 text-gray-400" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-gray-400" />
                    )}
                  </div>
                </div>
                
                {expandedSession === session.id && session.final_result && (
                  <div className="mt-2 pt-2 border-t border-white/10">
                    <p className="text-xs text-gray-400 whitespace-pre-wrap">
                      {session.final_result}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
