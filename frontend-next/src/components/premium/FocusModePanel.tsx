'use client';

/**
 * ⏱️ Focus Mode Panel - Pomodoro Timer
 * Premium productivity feature with animated timer
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  Timer, 
  Play, 
  Pause, 
  RotateCcw, 
  Coffee,
  Flame,
  Settings,
  X,
  Check,
  Volume2,
  VolumeX
} from 'lucide-react';

interface FocusModeProps {
  isOpen: boolean;
  onClose: () => void;
  noteId?: string;
  noteName?: string;
  onSessionComplete?: (wordsWritten: number) => void;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

// Preset durations
const PRESETS = [
  { label: '15 dk', work: 15, break: 3 },
  { label: '25 dk', work: 25, break: 5 },
  { label: '45 dk', work: 45, break: 10 },
  { label: '60 dk', work: 60, break: 15 },
];

type TimerState = 'idle' | 'work' | 'break' | 'paused';

export function FocusModePanel({ isOpen, onClose, noteId, noteName, onSessionComplete }: FocusModeProps) {
  const [timerState, setTimerState] = useState<TimerState>('idle');
  const [timeLeft, setTimeLeft] = useState(25 * 60); // seconds
  const [workDuration, setWorkDuration] = useState(25);
  const [breakDuration, setBreakDuration] = useState(5);
  const [totalPomodoros, setTotalPomodoros] = useState(0);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [soundEnabled, setSoundEnabled] = useState(true);
  
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Initialize audio
  useEffect(() => {
    audioRef.current = new Audio('/sounds/bell.mp3');
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  // Timer logic
  useEffect(() => {
    if (timerState === 'work' || timerState === 'break') {
      timerRef.current = setInterval(() => {
        setTimeLeft(prev => {
          if (prev <= 1) {
            handleTimerComplete();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [timerState]);

  const playSound = () => {
    if (soundEnabled && audioRef.current) {
      audioRef.current.play().catch(() => {});
    }
  };

  const handleTimerComplete = useCallback(async () => {
    playSound();
    
    if (timerState === 'work') {
      // Complete pomodoro
      setTotalPomodoros(prev => prev + 1);
      
      // Complete session on backend
      if (sessionId) {
        try {
          await fetch(`${API_URL}/api/notes/premium/focus/complete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId, words_written: 0 }),
          });
        } catch (err) {
          console.error('Failed to complete session:', err);
        }
      }
      
      // Switch to break
      setTimerState('break');
      setTimeLeft(breakDuration * 60);
      onSessionComplete?.(0);
    } else if (timerState === 'break') {
      // Break complete, back to idle
      setTimerState('idle');
      setTimeLeft(workDuration * 60);
    }
  }, [timerState, sessionId, breakDuration, workDuration, onSessionComplete]);

  const startTimer = async () => {
    if (timerState === 'idle' || timerState === 'paused') {
      // Start new session on backend
      try {
        const response = await fetch(`${API_URL}/api/notes/premium/focus/start`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            duration_minutes: workDuration,
            break_minutes: breakDuration,
            note_id: noteId,
          }),
        });
        const data = await response.json();
        if (data.success) {
          setSessionId(data.session_id);
        }
      } catch (err) {
        console.error('Failed to start session:', err);
      }
      
      setTimerState('work');
      if (timerState === 'idle') {
        setTimeLeft(workDuration * 60);
      }
    }
  };

  const pauseTimer = () => {
    if (timerState === 'work' || timerState === 'break') {
      setTimerState('paused');
    }
  };

  const resetTimer = () => {
    setTimerState('idle');
    setTimeLeft(workDuration * 60);
    setSessionId(null);
  };

  const selectPreset = (preset: typeof PRESETS[0]) => {
    setWorkDuration(preset.work);
    setBreakDuration(preset.break);
    setTimeLeft(preset.work * 60);
    setShowSettings(false);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const getProgress = () => {
    const total = timerState === 'break' ? breakDuration * 60 : workDuration * 60;
    return ((total - timeLeft) / total) * 100;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-white dark:bg-gray-900 rounded-3xl shadow-2xl w-full max-w-md overflow-hidden">
        {/* Header */}
        <div className={`p-6 text-center text-white ${
          timerState === 'break' 
            ? 'bg-gradient-to-r from-green-500 to-emerald-600' 
            : 'bg-gradient-to-r from-red-500 to-rose-600'
        }`}>
          <div className="flex justify-between items-center mb-4">
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="p-2 hover:bg-white/20 rounded-lg transition-colors"
            >
              <Settings className="w-5 h-5" />
            </button>
            <h2 className="text-xl font-bold flex items-center gap-2">
              {timerState === 'break' ? (
                <>
                  <Coffee className="w-6 h-6" />
                  Mola Zamanı
                </>
              ) : (
                <>
                  <Timer className="w-6 h-6" />
                  Focus Mode
                </>
              )}
            </h2>
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/20 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          
          {noteName && (
            <p className="text-white/80 text-sm mt-2">
              📝 {noteName}
            </p>
          )}
        </div>

        {/* Settings Panel */}
        {showSettings && (
          <div className="p-4 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">
              Süre Seç
            </h3>
            <div className="grid grid-cols-4 gap-2">
              {PRESETS.map((preset) => (
                <button
                  key={preset.label}
                  onClick={() => selectPreset(preset)}
                  className={`py-2 px-3 rounded-lg text-sm font-medium transition-all ${
                    workDuration === preset.work
                      ? 'bg-rose-500 text-white'
                      : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600'
                  }`}
                >
                  {preset.label}
                </button>
              ))}
            </div>
            <div className="mt-3 flex items-center justify-between">
              <span className="text-sm text-gray-500">Ses Bildirimi</span>
              <button
                onClick={() => setSoundEnabled(!soundEnabled)}
                className={`p-2 rounded-lg ${soundEnabled ? 'bg-rose-100 text-rose-600' : 'bg-gray-200 text-gray-400'}`}
              >
                {soundEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
              </button>
            </div>
          </div>
        )}

        {/* Timer Display */}
        <div className="p-8 text-center">
          {/* Circular Progress */}
          <div className="relative w-64 h-64 mx-auto mb-6">
            <svg className="w-full h-full transform -rotate-90">
              <circle
                cx="128"
                cy="128"
                r="120"
                stroke="currentColor"
                strokeWidth="8"
                fill="none"
                className="text-gray-200 dark:text-gray-700"
              />
              <circle
                cx="128"
                cy="128"
                r="120"
                stroke="currentColor"
                strokeWidth="8"
                fill="none"
                strokeLinecap="round"
                strokeDasharray={2 * Math.PI * 120}
                strokeDashoffset={2 * Math.PI * 120 * (1 - getProgress() / 100)}
                className={`transition-all duration-1000 ${
                  timerState === 'break' ? 'text-green-500' : 'text-rose-500'
                }`}
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-5xl font-bold text-gray-800 dark:text-white font-mono">
                {formatTime(timeLeft)}
              </span>
              <span className="text-sm text-gray-500 mt-2">
                {timerState === 'idle' ? 'Hazır' : 
                 timerState === 'paused' ? 'Duraklatıldı' :
                 timerState === 'break' ? 'Mola' : 'Odaklan'}
              </span>
            </div>
          </div>

          {/* Controls */}
          <div className="flex items-center justify-center gap-4">
            <button
              onClick={resetTimer}
              className="p-4 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
            >
              <RotateCcw className="w-6 h-6" />
            </button>
            
            {timerState === 'work' || timerState === 'break' ? (
              <button
                onClick={pauseTimer}
                className="p-6 rounded-full bg-rose-500 text-white hover:bg-rose-600 transition-colors shadow-lg"
              >
                <Pause className="w-8 h-8" />
              </button>
            ) : (
              <button
                onClick={startTimer}
                className="p-6 rounded-full bg-rose-500 text-white hover:bg-rose-600 transition-colors shadow-lg"
              >
                <Play className="w-8 h-8 ml-1" />
              </button>
            )}
            
            <button
              onClick={() => handleTimerComplete()}
              disabled={timerState === 'idle'}
              className="p-4 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
            >
              <Check className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Stats Footer */}
        <div className="p-4 bg-gray-50 dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-center gap-4">
            <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
              <Flame className="w-4 h-4 text-orange-500" />
              <span>
                Bugün: <strong className="text-gray-800 dark:text-white">{totalPomodoros}</strong> pomodoro
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default FocusModePanel;
