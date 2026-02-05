'use client';

import React, { useState, useEffect } from 'react';
import { 
  Mic, 
  MicOff, 
  Volume2, 
  VolumeX,
  Play,
  Square,
  Loader2,
  AudioLines
} from 'lucide-react';

interface VoiceAIPanelProps {
  className?: string;
}

export function VoiceAIPanel({ className = '' }: VoiceAIPanelProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [response, setResponse] = useState('');
  const [status, setStatus] = useState<any>(null);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const [audioChunks, setAudioChunks] = useState<Blob[]>([]);

  // Fetch status on mount
  useEffect(() => {
    fetchStatus();
  }, []);

  const fetchStatus = async () => {
    try {
      const res = await fetch('http://localhost:8001/api/voice/status');
      const data = await res.json();
      setStatus(data);
    } catch (error) {
      console.error('Failed to fetch voice status:', error);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks: Blob[] = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunks.push(e.data);
        }
      };

      recorder.onstop = async () => {
        const audioBlob = new Blob(chunks, { type: 'audio/webm' });
        await transcribeAudio(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      setMediaRecorder(recorder);
      setAudioChunks(chunks);
      recorder.start();
      setIsRecording(true);
      setTranscript('');
      setResponse('');
    } catch (error) {
      console.error('Failed to start recording:', error);
      alert('Mikrofon erişimi reddedildi. Lütfen tarayıcı izinlerini kontrol edin.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      setIsRecording(false);
    }
  };

  const transcribeAudio = async (audioBlob: Blob) => {
    setIsProcessing(true);
    try {
      const formData = new FormData();
      formData.append('file', audioBlob, 'recording.webm');

      const res = await fetch('http://localhost:8001/api/voice/transcribe', {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();
      if (data.success) {
        setTranscript(data.text);
        // Optionally send to chat and get response
        await getAIResponse(data.text);
      } else {
        setTranscript('Transkripsiyon başarısız: ' + (data.error || 'Bilinmeyen hata'));
      }
    } catch (error) {
      console.error('Transcription failed:', error);
      setTranscript('Transkripsiyon hatası');
    } finally {
      setIsProcessing(false);
    }
  };

  const getAIResponse = async (text: string) => {
    try {
      const res = await fetch('http://localhost:8001/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      });

      const data = await res.json();
      setResponse(data.response);
    } catch (error) {
      console.error('Chat failed:', error);
    }
  };

  const speakResponse = async () => {
    if (!response) return;
    
    setIsSpeaking(true);
    try {
      const res = await fetch('http://localhost:8001/api/voice/synthesize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: response }),
      });

      const audioBlob = await res.blob();
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      
      audio.onended = () => {
        setIsSpeaking(false);
        URL.revokeObjectURL(audioUrl);
      };
      
      audio.play();
    } catch (error) {
      console.error('TTS failed:', error);
      setIsSpeaking(false);
    }
  };

  return (
    <div className={`bg-gradient-to-br from-purple-900/30 to-indigo-900/30 rounded-xl border border-purple-500/30 p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-purple-500/20 rounded-lg">
            <Mic className="w-6 h-6 text-purple-400" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">Sesli AI Asistan</h2>
            <p className="text-sm text-gray-400">Konuşarak etkileşim kurun</p>
          </div>
        </div>
        <div className={`px-3 py-1 rounded-full text-xs ${status?.status === 'available' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'}`}>
          {status?.status === 'available' ? '🟢 Hazır' : '🟡 Yükleniyor'}
        </div>
      </div>

      {/* Recording Controls */}
      <div className="flex justify-center mb-6">
        <button
          onClick={isRecording ? stopRecording : startRecording}
          disabled={isProcessing}
          className={`relative w-24 h-24 rounded-full flex items-center justify-center transition-all duration-300 ${
            isRecording 
              ? 'bg-red-500 hover:bg-red-600 animate-pulse' 
              : 'bg-purple-500 hover:bg-purple-600'
          } ${isProcessing ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          {isProcessing ? (
            <Loader2 className="w-10 h-10 text-white animate-spin" />
          ) : isRecording ? (
            <Square className="w-10 h-10 text-white" />
          ) : (
            <Mic className="w-10 h-10 text-white" />
          )}
          
          {isRecording && (
            <div className="absolute inset-0 rounded-full border-4 border-red-300 animate-ping" />
          )}
        </button>
      </div>

      <p className="text-center text-sm text-gray-400 mb-6">
        {isProcessing ? 'İşleniyor...' : isRecording ? 'Konuşun, durdurmak için tekrar tıklayın' : 'Kayda başlamak için tıklayın'}
      </p>

      {/* Transcript */}
      {transcript && (
        <div className="mb-4">
          <label className="text-sm text-gray-400 mb-2 block">📝 Transkript:</label>
          <div className="bg-white/5 rounded-lg p-4 border border-white/10">
            <p className="text-white">{transcript}</p>
          </div>
        </div>
      )}

      {/* Response */}
      {response && (
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm text-gray-400">🤖 AI Yanıtı:</label>
            <button
              onClick={speakResponse}
              disabled={isSpeaking}
              className={`flex items-center gap-2 px-3 py-1 rounded-lg text-sm ${
                isSpeaking 
                  ? 'bg-purple-500/20 text-purple-300' 
                  : 'bg-purple-500/20 hover:bg-purple-500/30 text-purple-400'
              }`}
            >
              {isSpeaking ? (
                <>
                  <AudioLines className="w-4 h-4 animate-pulse" />
                  Konuşuyor...
                </>
              ) : (
                <>
                  <Volume2 className="w-4 h-4" />
                  Seslendir
                </>
              )}
            </button>
          </div>
          <div className="bg-white/5 rounded-lg p-4 border border-white/10 max-h-48 overflow-y-auto">
            <p className="text-white whitespace-pre-wrap">{response}</p>
          </div>
        </div>
      )}

      {/* Status Info */}
      <div className="mt-6 pt-4 border-t border-white/10 grid grid-cols-2 gap-4 text-sm">
        <div>
          <span className="text-gray-400">STT Model:</span>
          <span className="text-white ml-2">{status?.stt_model || 'Whisper'}</span>
        </div>
        <div>
          <span className="text-gray-400">TTS Engine:</span>
          <span className="text-white ml-2">{status?.tts_engine || 'pyttsx3'}</span>
        </div>
      </div>
    </div>
  );
}
