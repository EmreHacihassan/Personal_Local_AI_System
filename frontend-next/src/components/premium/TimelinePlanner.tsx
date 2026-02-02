'use client';

import React, { useState, useRef, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Calendar, Plus, ChevronLeft, ChevronRight, X,
  Clock, Edit2, Trash2, Save, Check, Star,
  AlertCircle, Bell, Repeat, Tag, Search, 
  Download, Upload, Copy, Filter, Eye, 
  ChevronDown, LayoutGrid, List, ArrowRight
} from 'lucide-react';
import { cn } from '@/lib/utils';

// Types
interface PlanEvent {
  id: string;
  date: string; // YYYY-MM-DD
  title: string;
  description?: string;
  time?: string;
  color?: string;
  isPinned?: boolean;
  reminder?: boolean;
  category?: string;
  repeat?: 'daily' | 'weekly' | 'monthly' | 'yearly' | null;
}

interface TimelinePlannerProps {
  events?: PlanEvent[];
  onEventAdd?: (event: PlanEvent) => void;
  onEventUpdate?: (event: PlanEvent) => void;
  onEventDelete?: (id: string) => void;
  className?: string;
}

// Turkish month names
const MONTHS_TR = [
  'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
  'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'
];

const DAYS_TR = ['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz'];

const EVENT_COLORS = [
  { name: 'Kırmızı', value: '#ef4444' },
  { name: 'Turuncu', value: '#f97316' },
  { name: 'Sarı', value: '#eab308' },
  { name: 'Yeşil', value: '#22c55e' },
  { name: 'Mavi', value: '#3b82f6' },
  { name: 'Mor', value: '#a855f7' },
  { name: 'Pembe', value: '#ec4899' },
];

const CATEGORIES = [
  'İş', 'Kişisel', 'Sağlık', 'Eğitim', 'Sosyal', 'Seyahat', 'Diğer'
];

// Helper functions
const formatDate = (date: Date): string => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

const getDaysInMonth = (year: number, month: number): number => {
  return new Date(year, month + 1, 0).getDate();
};

const getFirstDayOfMonth = (year: number, month: number): number => {
  const day = new Date(year, month, 1).getDay();
  return day === 0 ? 6 : day - 1; // Monday = 0
};

const TimelinePlanner: React.FC<TimelinePlannerProps> = ({
  events: initialEvents = [],
  onEventAdd,
  onEventUpdate,
  onEventDelete,
  className = ''
}) => {
  // State
  const [events, setEvents] = useState<PlanEvent[]>(initialEvents);
  const [selectedDate, setSelectedDate] = useState<string>(formatDate(new Date()));
  const [currentMonth, setCurrentMonth] = useState(new Date().getMonth());
  const [currentYear, setCurrentYear] = useState(new Date().getFullYear());
  const [showEventModal, setShowEventModal] = useState(false);
  const [editingEvent, setEditingEvent] = useState<PlanEvent | null>(null);
  const [timelineMonths, setTimelineMonths] = useState<Date[]>([]);
  
  // New comfort features state
  const [searchQuery, setSearchQuery] = useState('');
  const [showSearch, setShowSearch] = useState(false);
  const [viewMode, setViewMode] = useState<'month' | 'week'>('month');
  const [filterCategory, setFilterCategory] = useState<string>('');
  const [showUpcoming, setShowUpcoming] = useState(true);
  const [quickAddText, setQuickAddText] = useState('');
  
  // Form state
  const [eventTitle, setEventTitle] = useState('');
  const [eventDescription, setEventDescription] = useState('');
  const [eventTime, setEventTime] = useState('');
  const [eventColor, setEventColor] = useState(EVENT_COLORS[4].value);
  const [eventCategory, setEventCategory] = useState('');
  const [eventReminder, setEventReminder] = useState(false);
  
  const timelineRef = useRef<HTMLDivElement>(null);

  // Initialize timeline months (12 months centered on current)
  useEffect(() => {
    const months: Date[] = [];
    const now = new Date();
    for (let i = -3; i <= 8; i++) {
      const date = new Date(now.getFullYear(), now.getMonth() + i, 1);
      months.push(date);
    }
    setTimelineMonths(months);
  }, []);

  // Load events from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('timeline-planner-events');
    if (saved) {
      try {
        setEvents(JSON.parse(saved));
      } catch (e) {
        console.error('Failed to load events:', e);
      }
    }
  }, []);

  // Save events to localStorage
  useEffect(() => {
    localStorage.setItem('timeline-planner-events', JSON.stringify(events));
  }, [events]);

  // Get events for a specific date
  const getEventsForDate = (dateStr: string): PlanEvent[] => {
    return events.filter(e => e.date === dateStr).sort((a, b) => {
      if (a.isPinned && !b.isPinned) return -1;
      if (!a.isPinned && b.isPinned) return 1;
      return (a.time || '').localeCompare(b.time || '');
    });
  };

  // Check if date has events
  const hasEvents = (dateStr: string): boolean => {
    return events.some(e => e.date === dateStr);
  };

  // Search and filter events
  const filteredEvents = useMemo(() => {
    let result = events;
    
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(e => 
        e.title.toLowerCase().includes(query) ||
        e.description?.toLowerCase().includes(query) ||
        e.category?.toLowerCase().includes(query)
      );
    }
    
    if (filterCategory) {
      result = result.filter(e => e.category === filterCategory);
    }
    
    return result;
  }, [events, searchQuery, filterCategory]);

  // Upcoming events (next 7 days)
  const upcomingEvents = useMemo(() => {
    const today = new Date();
    const weekLater = new Date(today);
    weekLater.setDate(weekLater.getDate() + 7);
    
    return events
      .filter(e => {
        const eventDate = new Date(e.date);
        return eventDate >= today && eventDate <= weekLater;
      })
      .sort((a, b) => a.date.localeCompare(b.date));
  }, [events]);

  // Quick add event
  const handleQuickAdd = () => {
    if (!quickAddText.trim()) return;
    
    const newEvent: PlanEvent = {
      id: `event-${Date.now()}`,
      date: selectedDate,
      title: quickAddText.trim(),
      color: EVENT_COLORS[4].value
    };
    
    setEvents(prev => [...prev, newEvent]);
    setQuickAddText('');
    onEventAdd?.(newEvent);
  };

  // Duplicate event
  const duplicateEvent = (event: PlanEvent) => {
    const newEvent: PlanEvent = {
      ...event,
      id: `event-${Date.now()}`,
      title: `${event.title} (kopya)`
    };
    setEvents(prev => [...prev, newEvent]);
  };

  // Export events
  const exportEvents = () => {
    const data = JSON.stringify(events, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `takvim-${formatDate(new Date())}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Import events
  const importEvents = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const imported = JSON.parse(event.target?.result as string);
        if (Array.isArray(imported)) {
          setEvents(prev => [...prev, ...imported.map((ev: PlanEvent) => ({
            ...ev,
            id: `event-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
          }))]);
        }
      } catch (err) {
        console.error('Import failed:', err);
      }
    };
    reader.readAsText(file);
    e.target.value = '';
  };

  // Get week days for week view
  const getWeekDays = () => {
    const selected = new Date(selectedDate);
    const dayOfWeek = selected.getDay();
    const monday = new Date(selected);
    monday.setDate(selected.getDate() - (dayOfWeek === 0 ? 6 : dayOfWeek - 1));
    
    const days: Date[] = [];
    for (let i = 0; i < 7; i++) {
      const day = new Date(monday);
      day.setDate(monday.getDate() + i);
      days.push(day);
    }
    return days;
  };

  // Navigate months
  const prevMonth = () => {
    if (currentMonth === 0) {
      setCurrentMonth(11);
      setCurrentYear(currentYear - 1);
    } else {
      setCurrentMonth(currentMonth - 1);
    }
  };

  const nextMonth = () => {
    if (currentMonth === 11) {
      setCurrentMonth(0);
      setCurrentYear(currentYear + 1);
    } else {
      setCurrentMonth(currentMonth + 1);
    }
  };

  const goToToday = () => {
    const today = new Date();
    setCurrentMonth(today.getMonth());
    setCurrentYear(today.getFullYear());
    setSelectedDate(formatDate(today));
  };

  // Open event modal
  const openEventModal = (event?: PlanEvent) => {
    if (event) {
      setEditingEvent(event);
      setEventTitle(event.title);
      setEventDescription(event.description || '');
      setEventTime(event.time || '');
      setEventColor(event.color || EVENT_COLORS[4].value);
      setEventCategory(event.category || '');
      setEventReminder(event.reminder || false);
    } else {
      setEditingEvent(null);
      setEventTitle('');
      setEventDescription('');
      setEventTime('');
      setEventColor(EVENT_COLORS[4].value);
      setEventCategory('');
      setEventReminder(false);
    }
    setShowEventModal(true);
  };

  // Save event
  const saveEvent = () => {
    if (!eventTitle.trim()) return;

    const newEvent: PlanEvent = {
      id: editingEvent?.id || `event-${Date.now()}`,
      date: selectedDate,
      title: eventTitle.trim(),
      description: eventDescription.trim() || undefined,
      time: eventTime || undefined,
      color: eventColor,
      category: eventCategory || undefined,
      reminder: eventReminder,
      isPinned: editingEvent?.isPinned
    };

    if (editingEvent) {
      setEvents(prev => prev.map(e => e.id === editingEvent.id ? newEvent : e));
      onEventUpdate?.(newEvent);
    } else {
      setEvents(prev => [...prev, newEvent]);
      onEventAdd?.(newEvent);
    }

    setShowEventModal(false);
  };

  // Delete event
  const deleteEvent = (id: string) => {
    setEvents(prev => prev.filter(e => e.id !== id));
    onEventDelete?.(id);
    setShowEventModal(false);
  };

  // Toggle pin
  const togglePin = (id: string) => {
    setEvents(prev => prev.map(e => 
      e.id === id ? { ...e, isPinned: !e.isPinned } : e
    ));
  };

  // Render calendar grid
  const renderCalendar = () => {
    const daysInMonth = getDaysInMonth(currentYear, currentMonth);
    const firstDay = getFirstDayOfMonth(currentYear, currentMonth);
    const today = formatDate(new Date());
    const days: JSX.Element[] = [];

    // Empty cells for days before month starts
    for (let i = 0; i < firstDay; i++) {
      days.push(<div key={`empty-${i}`} className="h-8" />);
    }

    // Days of month
    for (let day = 1; day <= daysInMonth; day++) {
      const dateStr = `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
      const isSelected = dateStr === selectedDate;
      const isToday = dateStr === today;
      const hasEvent = hasEvents(dateStr);
      const dayEvents = getEventsForDate(dateStr);
      const eventColor = dayEvents[0]?.color;

      days.push(
        <motion.button
          key={day}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => setSelectedDate(dateStr)}
          className={cn(
            "relative h-8 w-8 rounded-lg text-sm font-medium transition-all",
            "hover:bg-primary-500/20",
            isSelected && "bg-primary-500 text-white hover:bg-primary-600",
            isToday && !isSelected && "ring-2 ring-primary-500 ring-offset-1 ring-offset-background",
            !isSelected && !isToday && "text-foreground/80"
          )}
        >
          {day}
          {hasEvent && !isSelected && (
            <span 
              className="absolute bottom-0.5 left-1/2 -translate-x-1/2 w-1.5 h-1.5 rounded-full"
              style={{ backgroundColor: eventColor || '#3b82f6' }}
            />
          )}
        </motion.button>
      );
    }

    return days;
  };

  // Render timeline
  const renderTimeline = () => {
    const today = new Date();
    const todayStr = formatDate(today);

    return (
      <div 
        ref={timelineRef}
        className="flex overflow-x-auto pb-4 scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent"
      >
        {timelineMonths.map((monthDate, monthIdx) => {
          const year = monthDate.getFullYear();
          const month = monthDate.getMonth();
          const daysInMonth = getDaysInMonth(year, month);
          const isCurrentMonth = month === today.getMonth() && year === today.getFullYear();

          return (
            <div key={monthIdx} className="flex-shrink-0">
              {/* Month header */}
              <div className={cn(
                "sticky top-0 px-3 py-1.5 text-sm font-semibold border-b border-border/50 mb-2",
                isCurrentMonth ? "text-primary-500" : "text-muted-foreground"
              )}>
                {MONTHS_TR[month]} {year}
              </div>
              
              {/* Days */}
              <div className="flex gap-1 px-2">
                {Array.from({ length: daysInMonth }, (_, i) => {
                  const day = i + 1;
                  const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
                  const isToday = dateStr === todayStr;
                  const isSelected = dateStr === selectedDate;
                  const dayEvents = getEventsForDate(dateStr);
                  const hasEvent = dayEvents.length > 0;

                  return (
                    <motion.div
                      key={day}
                      whileHover={{ scale: 1.05 }}
                      onClick={() => {
                        setSelectedDate(dateStr);
                        setCurrentMonth(month);
                        setCurrentYear(year);
                      }}
                      className={cn(
                        "flex flex-col items-center cursor-pointer transition-all min-w-[40px]",
                        "rounded-lg p-1.5",
                        isSelected && "bg-primary-500/20 ring-2 ring-primary-500",
                        isToday && !isSelected && "bg-green-500/10 ring-1 ring-green-500",
                        !isSelected && !isToday && "hover:bg-muted/50"
                      )}
                    >
                      <span className={cn(
                        "text-[10px] font-medium",
                        isToday ? "text-green-500" : "text-muted-foreground"
                      )}>
                        {DAYS_TR[new Date(year, month, day).getDay() === 0 ? 6 : new Date(year, month, day).getDay() - 1]}
                      </span>
                      <span className={cn(
                        "text-sm font-semibold",
                        isSelected ? "text-primary-500" : isToday ? "text-green-500" : "text-foreground"
                      )}>
                        {day}
                      </span>
                      {hasEvent && (
                        <div className="flex gap-0.5 mt-0.5">
                          {dayEvents.slice(0, 3).map((ev, evIdx) => (
                            <span 
                              key={evIdx}
                              className="w-1.5 h-1.5 rounded-full"
                              style={{ backgroundColor: ev.color || '#3b82f6' }}
                            />
                          ))}
                          {dayEvents.length > 3 && (
                            <span className="text-[8px] text-muted-foreground">+{dayEvents.length - 3}</span>
                          )}
                        </div>
                      )}
                    </motion.div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  // Get selected date info
  const selectedDateObj = new Date(selectedDate);
  const selectedDateEvents = getEventsForDate(selectedDate);
  const isSelectedToday = selectedDate === formatDate(new Date());

  return (
    <div className={cn("flex flex-col h-full bg-background", className)}>
      {/* Header with Timeline */}
      <div className="border-b border-border bg-gradient-to-r from-primary-500/5 to-purple-500/5">
        <div className="flex items-center justify-between px-4 py-3">
          <h2 className="text-lg font-bold flex items-center gap-2">
            <Calendar className="w-5 h-5 text-primary-500" />
            Takvim Planlayıcı
          </h2>
          
          {/* Toolbar */}
          <div className="flex items-center gap-2">
            {/* Search */}
            <div className="relative">
              {showSearch ? (
                <motion.div
                  initial={{ width: 0, opacity: 0 }}
                  animate={{ width: 200, opacity: 1 }}
                  className="flex items-center"
                >
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={e => setSearchQuery(e.target.value)}
                    placeholder="Etkinlik ara..."
                    className="w-full px-3 py-1.5 text-sm bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    autoFocus
                  />
                  <button
                    onClick={() => { setShowSearch(false); setSearchQuery(''); }}
                    className="ml-1 p-1 hover:bg-muted rounded"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </motion.div>
              ) : (
                <button
                  onClick={() => setShowSearch(true)}
                  className="p-2 hover:bg-muted rounded-lg transition-colors"
                  title="Ara"
                >
                  <Search className="w-4 h-4" />
                </button>
              )}
            </div>

            {/* Category Filter */}
            <select
              value={filterCategory}
              onChange={e => setFilterCategory(e.target.value)}
              className="px-2 py-1.5 text-sm bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">Tüm Kategoriler</option>
              {CATEGORIES.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>

            {/* View Mode Toggle */}
            <div className="flex bg-muted rounded-lg p-0.5">
              <button
                onClick={() => setViewMode('month')}
                className={cn(
                  "p-1.5 rounded transition-colors",
                  viewMode === 'month' ? "bg-background shadow-sm" : "hover:bg-background/50"
                )}
                title="Aylık Görünüm"
              >
                <LayoutGrid className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode('week')}
                className={cn(
                  "p-1.5 rounded transition-colors",
                  viewMode === 'week' ? "bg-background shadow-sm" : "hover:bg-background/50"
                )}
                title="Haftalık Görünüm"
              >
                <List className="w-4 h-4" />
              </button>
            </div>

            {/* Import/Export */}
            <div className="flex gap-1">
              <button
                onClick={exportEvents}
                className="p-2 hover:bg-muted rounded-lg transition-colors"
                title="Dışa Aktar"
              >
                <Download className="w-4 h-4" />
              </button>
              <label className="p-2 hover:bg-muted rounded-lg transition-colors cursor-pointer" title="İçe Aktar">
                <Upload className="w-4 h-4" />
                <input
                  type="file"
                  accept=".json"
                  onChange={importEvents}
                  className="hidden"
                />
              </label>
            </div>

            {/* Today Button */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={goToToday}
              className="px-3 py-1.5 text-sm font-medium bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
            >
              Bugün
            </motion.button>
          </div>
        </div>
        
        {/* Horizontal Timeline */}
        <div className="px-4 py-2">
          {renderTimeline()}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left: Mini Calendar */}
        <div className="w-72 border-r border-border p-4 flex flex-col gap-4">
          {/* Month Navigator */}
          <div className="flex items-center justify-between">
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={prevMonth}
              className="p-1.5 rounded-lg hover:bg-muted transition-colors"
            >
              <ChevronLeft className="w-5 h-5" />
            </motion.button>
            <span className="font-semibold text-sm">
              {MONTHS_TR[currentMonth]} {currentYear}
            </span>
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={nextMonth}
              className="p-1.5 rounded-lg hover:bg-muted transition-colors"
            >
              <ChevronRight className="w-5 h-5" />
            </motion.button>
          </div>

          {/* Days of Week */}
          <div className="grid grid-cols-7 gap-1 text-center">
            {DAYS_TR.map(day => (
              <div key={day} className="text-xs font-medium text-muted-foreground py-1">
                {day}
              </div>
            ))}
          </div>

          {/* Calendar Grid */}
          <div className="grid grid-cols-7 gap-1">
            {renderCalendar()}
          </div>

          {/* Quick Stats */}
          <div className="mt-auto pt-4 border-t border-border space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Bu ay:</span>
              <span className="font-medium">
                {events.filter(e => {
                  const d = new Date(e.date);
                  return d.getMonth() === currentMonth && d.getFullYear() === currentYear;
                }).length} etkinlik
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Yaklaşan:</span>
              <span className="font-medium text-orange-500">
                {events.filter(e => new Date(e.date) > new Date()).length} etkinlik
              </span>
            </div>
          </div>

          {/* Upcoming Events Panel */}
          {showUpcoming && upcomingEvents.length > 0 && (
            <div className="mt-4 pt-4 border-t border-border">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-semibold flex items-center gap-1">
                  <Bell className="w-3.5 h-3.5 text-orange-500" />
                  Yaklaşan
                </h4>
                <button
                  onClick={() => setShowUpcoming(false)}
                  className="text-xs text-muted-foreground hover:text-foreground"
                >
                  Gizle
                </button>
              </div>
              <div className="space-y-1.5 max-h-32 overflow-y-auto">
                {upcomingEvents.slice(0, 5).map(event => {
                  const eventDate = new Date(event.date);
                  const isToday = formatDate(eventDate) === formatDate(new Date());
                  return (
                    <motion.div
                      key={event.id}
                      whileHover={{ x: 2 }}
                      onClick={() => setSelectedDate(event.date)}
                      className="flex items-center gap-2 p-1.5 rounded-lg hover:bg-muted cursor-pointer text-xs"
                    >
                      <span 
                        className="w-2 h-2 rounded-full flex-shrink-0"
                        style={{ backgroundColor: event.color || '#3b82f6' }}
                      />
                      <span className="flex-1 truncate">{event.title}</span>
                      <span className={cn(
                        "text-[10px] flex-shrink-0",
                        isToday ? "text-green-500 font-medium" : "text-muted-foreground"
                      )}>
                        {isToday ? 'Bugün' : `${eventDate.getDate()}/${eventDate.getMonth() + 1}`}
                      </span>
                    </motion.div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Right: Selected Day Events */}
        <div className="flex-1 p-4 overflow-y-auto">
          {/* Selected Date Header */}
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className={cn(
                "text-xl font-bold",
                isSelectedToday && "text-green-500"
              )}>
                {selectedDateObj.getDate()} {MONTHS_TR[selectedDateObj.getMonth()]}
                {isSelectedToday && <span className="ml-2 text-sm font-normal">(Bugün)</span>}
              </h3>
              <p className="text-sm text-muted-foreground">
                {['Pazar', 'Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi'][selectedDateObj.getDay()]}
                , {selectedDateObj.getFullYear()}
              </p>
            </div>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => openEventModal()}
              className="flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-xl font-medium hover:bg-primary-600 transition-colors shadow-lg shadow-primary-500/20"
            >
              <Plus className="w-4 h-4" />
              Etkinlik Ekle
            </motion.button>
          </div>

          {/* Quick Add Bar */}
          <div className="mb-4">
            <div className="flex gap-2">
              <input
                type="text"
                value={quickAddText}
                onChange={e => setQuickAddText(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleQuickAdd()}
                placeholder="Hızlı etkinlik ekle... (Enter)"
                className="flex-1 px-4 py-2.5 bg-muted/50 border border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
              />
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleQuickAdd}
                disabled={!quickAddText.trim()}
                className="px-4 py-2.5 bg-green-500 text-white rounded-xl hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Check className="w-5 h-5" />
              </motion.button>
            </div>
          </div>

          {/* Events List */}
          {selectedDateEvents.length === 0 ? (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex flex-col items-center justify-center py-16 text-center"
            >
              <div className="w-20 h-20 rounded-full bg-muted/50 flex items-center justify-center mb-4">
                <Calendar className="w-8 h-8 text-muted-foreground" />
              </div>
              <p className="text-muted-foreground mb-2">Bu tarihte etkinlik yok</p>
              <button
                onClick={() => openEventModal()}
                className="text-primary-500 hover:underline text-sm font-medium"
              >
                İlk etkinliği ekle →
              </button>
            </motion.div>
          ) : (
            <div className="space-y-3">
              <AnimatePresence>
                {selectedDateEvents.map((event, idx) => (
                  <motion.div
                    key={event.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                    transition={{ delay: idx * 0.05 }}
                    className="group relative bg-card border border-border rounded-xl p-4 hover:shadow-lg transition-all"
                    style={{ borderLeftWidth: '4px', borderLeftColor: event.color }}
                  >
                    {/* Pin indicator */}
                    {event.isPinned && (
                      <span className="absolute -top-2 -right-2 w-6 h-6 bg-yellow-500 rounded-full flex items-center justify-center shadow-lg">
                        <Star className="w-3 h-3 text-white" />
                      </span>
                    )}

                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        {/* Time & Category */}
                        <div className="flex items-center gap-2 mb-1">
                          {event.time && (
                            <span className="flex items-center gap-1 text-xs text-muted-foreground">
                              <Clock className="w-3 h-3" />
                              {event.time}
                            </span>
                          )}
                          {event.category && (
                            <span className="flex items-center gap-1 px-2 py-0.5 bg-muted rounded-full text-xs">
                              <Tag className="w-3 h-3" />
                              {event.category}
                            </span>
                          )}
                          {event.reminder && (
                            <span className="flex items-center gap-1 text-xs text-orange-500">
                              <Bell className="w-3 h-3" />
                            </span>
                          )}
                        </div>
                        
                        {/* Title */}
                        <h4 className="font-semibold text-foreground mb-1">{event.title}</h4>
                        
                        {/* Description */}
                        {event.description && (
                          <p className="text-sm text-muted-foreground line-clamp-2">
                            {event.description}
                          </p>
                        )}
                      </div>

                      {/* Actions */}
                      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <motion.button
                          whileHover={{ scale: 1.1 }}
                          whileTap={{ scale: 0.9 }}
                          onClick={() => togglePin(event.id)}
                          className={cn(
                            "p-1.5 rounded-lg transition-colors",
                            event.isPinned ? "text-yellow-500 bg-yellow-500/10" : "text-muted-foreground hover:bg-muted"
                          )}
                          title="Sabitle"
                        >
                          <Star className="w-4 h-4" />
                        </motion.button>
                        <motion.button
                          whileHover={{ scale: 1.1 }}
                          whileTap={{ scale: 0.9 }}
                          onClick={() => duplicateEvent(event)}
                          className="p-1.5 rounded-lg text-muted-foreground hover:bg-muted transition-colors"
                          title="Kopyala"
                        >
                          <Copy className="w-4 h-4" />
                        </motion.button>
                        <motion.button
                          whileHover={{ scale: 1.1 }}
                          whileTap={{ scale: 0.9 }}
                          onClick={() => openEventModal(event)}
                          className="p-1.5 rounded-lg text-muted-foreground hover:bg-muted transition-colors"
                          title="Düzenle"
                        >
                          <Edit2 className="w-4 h-4" />
                        </motion.button>
                        <motion.button
                          whileHover={{ scale: 1.1 }}
                          whileTap={{ scale: 0.9 }}
                          onClick={() => deleteEvent(event.id)}
                          className="p-1.5 rounded-lg text-red-500 hover:bg-red-500/10 transition-colors"
                          title="Sil"
                        >
                          <Trash2 className="w-4 h-4" />
                        </motion.button>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          )}
        </div>
      </div>

      {/* Event Modal */}
      <AnimatePresence>
        {showEventModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowEventModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={e => e.stopPropagation()}
              className="w-full max-w-md bg-card border border-border rounded-2xl shadow-2xl overflow-hidden"
            >
              {/* Modal Header */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-gradient-to-r from-primary-500/10 to-purple-500/10">
                <h3 className="text-lg font-semibold">
                  {editingEvent ? 'Etkinliği Düzenle' : 'Yeni Etkinlik'}
                </h3>
                <button
                  onClick={() => setShowEventModal(false)}
                  className="p-1.5 rounded-lg hover:bg-muted transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Modal Body */}
              <div className="p-6 space-y-4">
                {/* Date Display */}
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Calendar className="w-4 h-4" />
                  {selectedDateObj.getDate()} {MONTHS_TR[selectedDateObj.getMonth()]} {selectedDateObj.getFullYear()}
                </div>

                {/* Title */}
                <div>
                  <label className="text-sm font-medium text-muted-foreground mb-1 block">
                    Başlık *
                  </label>
                  <input
                    type="text"
                    value={eventTitle}
                    onChange={e => setEventTitle(e.target.value)}
                    placeholder="Ne olacak bu tarihte?"
                    className="w-full px-4 py-2.5 bg-background border border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 transition-all"
                    autoFocus
                  />
                </div>

                {/* Description */}
                <div>
                  <label className="text-sm font-medium text-muted-foreground mb-1 block">
                    Açıklama
                  </label>
                  <textarea
                    value={eventDescription}
                    onChange={e => setEventDescription(e.target.value)}
                    placeholder="Detayları yaz..."
                    rows={3}
                    className="w-full px-4 py-2.5 bg-background border border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none transition-all"
                  />
                </div>

                {/* Time & Category Row */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-sm font-medium text-muted-foreground mb-1 block">
                      Saat
                    </label>
                    <input
                      type="time"
                      value={eventTime}
                      onChange={e => setEventTime(e.target.value)}
                      className="w-full px-4 py-2.5 bg-background border border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 transition-all"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium text-muted-foreground mb-1 block">
                      Kategori
                    </label>
                    <select
                      value={eventCategory}
                      onChange={e => setEventCategory(e.target.value)}
                      className="w-full px-4 py-2.5 bg-background border border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 transition-all"
                    >
                      <option value="">Seç...</option>
                      {CATEGORIES.map(cat => (
                        <option key={cat} value={cat}>{cat}</option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Color Picker */}
                <div>
                  <label className="text-sm font-medium text-muted-foreground mb-2 block">
                    Renk
                  </label>
                  <div className="flex gap-2">
                    {EVENT_COLORS.map(color => (
                      <motion.button
                        key={color.value}
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                        onClick={() => setEventColor(color.value)}
                        className={cn(
                          "w-8 h-8 rounded-full transition-all",
                          eventColor === color.value && "ring-2 ring-offset-2 ring-offset-background ring-primary-500"
                        )}
                        style={{ backgroundColor: color.value }}
                        title={color.name}
                      />
                    ))}
                  </div>
                </div>

                {/* Reminder Toggle */}
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={eventReminder}
                    onChange={e => setEventReminder(e.target.checked)}
                    className="w-5 h-5 rounded border-border text-primary-500 focus:ring-primary-500"
                  />
                  <div className="flex items-center gap-2">
                    <Bell className="w-4 h-4 text-orange-500" />
                    <span className="text-sm">Hatırlatıcı ekle</span>
                  </div>
                </label>
              </div>

              {/* Modal Footer */}
              <div className="flex items-center justify-between px-6 py-4 border-t border-border bg-muted/30">
                {editingEvent && (
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => deleteEvent(editingEvent.id)}
                    className="flex items-center gap-2 px-4 py-2 text-red-500 hover:bg-red-500/10 rounded-xl transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                    Sil
                  </motion.button>
                )}
                <div className={cn("flex gap-2", !editingEvent && "ml-auto")}>
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => setShowEventModal(false)}
                    className="px-4 py-2 text-muted-foreground hover:bg-muted rounded-xl transition-colors"
                  >
                    İptal
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={saveEvent}
                    disabled={!eventTitle.trim()}
                    className="flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-xl font-medium hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    <Check className="w-4 h-4" />
                    {editingEvent ? 'Güncelle' : 'Ekle'}
                  </motion.button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default TimelinePlanner;
