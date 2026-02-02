'use client';

import React from 'react';
import TimelinePlanner from '@/components/premium/TimelinePlanner';

const CalendarPage: React.FC = () => {
  return (
    <div className="h-full w-full bg-background">
      <TimelinePlanner className="h-full" />
    </div>
  );
};

export default CalendarPage;
