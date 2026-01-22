'use client';

import React, { useState, useEffect } from 'react';

interface AnalogClockProps {
  size?: number;
  showDigital?: boolean;
}

const AnalogClock: React.FC<AnalogClockProps> = ({ size = 120, showDigital = true }) => {
  const [time, setTime] = useState<Date>(new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      // Get Turkey time (UTC+3)
      const now = new Date();
      const turkeyTime = new Date(now.toLocaleString('en-US', { timeZone: 'Europe/Istanbul' }));
      setTime(turkeyTime);
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const seconds = time.getSeconds();
  const minutes = time.getMinutes();
  const hours = time.getHours() % 12;

  // Calculate angles
  const secondAngle = (seconds / 60) * 360;
  const minuteAngle = ((minutes + seconds / 60) / 60) * 360;
  const hourAngle = ((hours + minutes / 60) / 12) * 360;

  const center = size / 2;
  const radius = (size / 2) - 8;

  // Generate hour markers
  const hourMarkers = Array.from({ length: 12 }, (_, i) => {
    const angle = ((i * 30 - 90) * Math.PI) / 180;
    const innerRadius = radius - 8;
    const outerRadius = radius - 2;
    return {
      x1: center + innerRadius * Math.cos(angle),
      y1: center + innerRadius * Math.sin(angle),
      x2: center + outerRadius * Math.cos(angle),
      y2: center + outerRadius * Math.sin(angle),
    };
  });

  // Generate minute markers
  const minuteMarkers = Array.from({ length: 60 }, (_, i) => {
    if (i % 5 === 0) return null; // Skip hour positions
    const angle = ((i * 6 - 90) * Math.PI) / 180;
    const innerRadius = radius - 4;
    const outerRadius = radius - 2;
    return {
      x1: center + innerRadius * Math.cos(angle),
      y1: center + innerRadius * Math.sin(angle),
      x2: center + outerRadius * Math.cos(angle),
      y2: center + outerRadius * Math.sin(angle),
    };
  }).filter(Boolean);

  return (
    <div className="flex flex-col items-center gap-1">
      {/* Clock face */}
      <div 
        className="relative"
        style={{ width: size, height: size }}
      >
        <svg width={size} height={size} className="drop-shadow-lg">
          {/* Outer ring gradient */}
          <defs>
            <linearGradient id="clockGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#1e293b" />
              <stop offset="50%" stopColor="#334155" />
              <stop offset="100%" stopColor="#1e293b" />
            </linearGradient>
            <radialGradient id="faceGradient" cx="30%" cy="30%">
              <stop offset="0%" stopColor="#475569" />
              <stop offset="100%" stopColor="#1e293b" />
            </radialGradient>
            <filter id="glow">
              <feGaussianBlur stdDeviation="1" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
          </defs>

          {/* Clock face background */}
          <circle
            cx={center}
            cy={center}
            r={radius + 4}
            fill="url(#clockGradient)"
            stroke="#64748b"
            strokeWidth="1"
          />
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="url(#faceGradient)"
          />

          {/* Hour markers */}
          {hourMarkers.map((marker, i) => (
            <line
              key={`hour-${i}`}
              x1={marker.x1}
              y1={marker.y1}
              x2={marker.x2}
              y2={marker.y2}
              stroke="#e2e8f0"
              strokeWidth="2"
              strokeLinecap="round"
            />
          ))}

          {/* Minute markers */}
          {minuteMarkers.map((marker, i) => (
            marker && (
              <line
                key={`minute-${i}`}
                x1={marker.x1}
                y1={marker.y1}
                x2={marker.x2}
                y2={marker.y2}
                stroke="#94a3b8"
                strokeWidth="1"
                strokeLinecap="round"
              />
            )
          ))}

          {/* Hour hand */}
          <line
            x1={center}
            y1={center}
            x2={center + (radius * 0.5) * Math.cos((hourAngle - 90) * Math.PI / 180)}
            y2={center + (radius * 0.5) * Math.sin((hourAngle - 90) * Math.PI / 180)}
            stroke="#f8fafc"
            strokeWidth="3"
            strokeLinecap="round"
            filter="url(#glow)"
          />

          {/* Minute hand */}
          <line
            x1={center}
            y1={center}
            x2={center + (radius * 0.7) * Math.cos((minuteAngle - 90) * Math.PI / 180)}
            y2={center + (radius * 0.7) * Math.sin((minuteAngle - 90) * Math.PI / 180)}
            stroke="#e2e8f0"
            strokeWidth="2"
            strokeLinecap="round"
            filter="url(#glow)"
          />

          {/* Second hand */}
          <line
            x1={center}
            y1={center}
            x2={center + (radius * 0.8) * Math.cos((secondAngle - 90) * Math.PI / 180)}
            y2={center + (radius * 0.8) * Math.sin((secondAngle - 90) * Math.PI / 180)}
            stroke="#ef4444"
            strokeWidth="1"
            strokeLinecap="round"
          />

          {/* Center dot */}
          <circle
            cx={center}
            cy={center}
            r="4"
            fill="#ef4444"
            stroke="#fca5a5"
            strokeWidth="1"
          />
        </svg>

        {/* Turkey flag icon */}
        <div className="absolute -top-1 -right-1 w-6 h-6 rounded-full bg-red-600 flex items-center justify-center shadow-lg border border-red-400">
          <span className="text-white text-xs">🇹🇷</span>
        </div>
      </div>

      {/* Digital time display */}
      {showDigital && (
        <div className="text-center">
          <div className="text-sm font-mono text-white font-semibold tracking-wider">
            {time.toLocaleTimeString('tr-TR', { 
              hour: '2-digit', 
              minute: '2-digit',
              second: '2-digit',
              hour12: false 
            })}
          </div>
          <div className="text-[10px] text-gray-400 uppercase tracking-widest">
            Türkiye
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalogClock;
