'use client';

import React, { useState, useEffect } from 'react';

const DigitalClock: React.FC = () => {
  const [time, setTime] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const turkeyTime = now.toLocaleTimeString('tr-TR', { 
        timeZone: 'Europe/Istanbul',
        hour: '2-digit', 
        minute: '2-digit',
        second: '2-digit',
        hour12: false 
      });
      setTime(turkeyTime);
    };
    
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="flex items-center gap-1.5 text-xs">
      <span className="text-[10px]">🇹🇷</span>
      <span className="font-mono text-muted-foreground">{time}</span>
    </div>
  );
};

export default DigitalClock;
