'use client';

import React, { useState, useRef, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Calendar, Plus, ChevronLeft, ChevronRight, X,
  Clock, Edit2, Trash2, Check, Star,
  Bell, Tag, Search, Download, Upload, 
  History, ChevronDown, ChevronUp, ArrowRight
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

const MONTHS_SHORT_TR = [
  'Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz',
  'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara'
];

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

const getMonthKey = (year: number, month: number): string => {
  return `${year}-${String(month + 1).padStart(2, '0')}`;
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
  const [selectedMonth, setSelectedMonth] = useState<{ year: number; month: number } | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<PlanEvent | null>(null);
  const [showEventModal, setShowEventModal] = useState(false);
  const [editingEvent, setEditingEvent] = useState<PlanEvent | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [showSearch, setShowSearch] = useState(false);
  
  // Form state
  const [eventTitle, setEventTitle] = useState('');
  const [eventDescription, setEventDescription] = useState('');
  const [eventDate, setEventDate] = useState('');
  const [eventTime, setEventTime] = useState('');
  const [eventColor, setEventColor] = useState(EVENT_COLORS[4].value);
  const [eventCategory, setEventCategory] = useState('');
  const [eventReminder, setEventReminder] = useState(false);
  
  const timelineRef = useRef<HTMLDivElement>(null);
  const today = new Date();
  const currentMonthKey = getMonthKey(today.getFullYear(), today.getMonth());

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

  // Filter events
  const filteredEvents = useMemo(() => {
    if (!searchQuery) return events;
    const query = searchQuery.toLowerCase();
    return events.filter(e => 
      e.title.toLowerCase().includes(query) ||
      e.description?.toLowerCase().includes(query) ||
      e.category?.toLowerCase().includes(query)
    );
  }, [events, searchQuery]);

  // Separate future and past events
  const { futureMonths, pastEvents } = useMemo(() => {
    const todayStr = formatDate(today);
    const future: { [key: string]: PlanEvent[] } = {};
    const past: PlanEvent[] = [];
    
    filteredEvents.forEach(event => {
      if (event.date < todayStr) {
        past.push(event);
      } else {
        const eventDate = new Date(event.date);
        const monthKey = getMonthKey(eventDate.getFullYear(), eventDate.getMonth());
        if (!future[monthKey]) future[monthKey] = [];
        future[monthKey].push(event);
      }
    });
    
    // Sort past events by date descending
    past.sort((a, b) => b.date.localeCompare(a.date));
    
    return { futureMonths: future, pastEvents: past };
  }, [filteredEvents, today]);

  // Generate future months for timeline (12 months from now)
  const timelineMonthsData = useMemo(() => {
    const months: { year: number; month: number; key: string }[] = [];
    for (let i = 0; i < 12; i++) {
      const date = new Date(today.getFullYear(), today.getMonth() + i, 1);
      months.push({
        year: date.getFullYear(),
        month: date.getMonth(),
        key: getMonthKey(date.getFullYear(), date.getMonth())
      });
    }
    return months;
  }, [today]);

  // Get events for a specific month
  const getEventsForMonth = (monthKey: string): PlanEvent[] => {
    return futureMonths[monthKey] || [];
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

  // Open event modal
  const openEventModal = (event?: PlanEvent, defaultMonth?: { year: number; month: number }) => {
    if (event) {
      setEditingEvent(event);
      setEventTitle(event.title);
      setEventDescription(event.description || '');
      setEventDate(event.date);
      setEventTime(event.time || '');
      setEventColor(event.color || EVENT_COLORS[4].value);
      setEventCategory(event.category || '');
      setEventReminder(event.reminder || false);
    } else {
      setEditingEvent(null);
      setEventTitle('');
      setEventDescription('');
      // Default to first day of selected month or today
      if (defaultMonth) {
        const defaultDate = new Date(defaultMonth.year, defaultMonth.month, 1);
        setEventDate(formatDate(defaultDate));
      } else {
        setEventDate(formatDate(new Date()));
      }
      setEventTime('');
      setEventColor(EVENT_COLORS[4].value);
      setEventCategory('');
      setEventReminder(false);
    }
    setShowEventModal(true);
  };

  // Save event
  const saveEvent = () => {
    if (!eventTitle.trim() || !eventDate) return;

    const newEvent: PlanEvent = {
      id: editingEvent?.id || `event-${Date.now()}`,
      date: eventDate,
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
    setSelectedEvent(null);
  };

  // Delete event
  const deleteEvent = (id: string) => {
    setEvents(prev => prev.filter(e => e.id !== id));
    onEventDelete?.(id);
    setShowEventModal(false);
    setSelectedEvent(null);
  };

  return (
    <div className={cn("flex flex-col h-full bg-background", className)}>
      {/* Header */}
      <div className="border-b border-border bg-gradient-to-r from-primary-500/5 to-purple-500/5 px-6 py-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold flex items-center gap-2">
            <Calendar className="w-6 h-6 text-primary-500" />
            Takvim Planlayıcı
          </h2>
          
          {/* Toolbar */}
          <div className="flex items-center gap-3">
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

            {/* Import/Export */}
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

            {/* Add Event Button */}
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
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {/* Timeline - Months from Today */}
        <div className="mb-8">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <ArrowRight className="w-5 h-5 text-primary-500" />
            Gelecek Aylar
          </h3>
          
          {/* Horizontal Timeline */}
          <div 
            ref={timelineRef}
            className="relative overflow-x-auto pb-4"
          >
            {/* Timeline Line */}
            <div className="absolute top-20 left-0 right-0 h-1 bg-gradient-to-r from-primary-500 via-purple-500 to-blue-500 rounded-full" style={{ minWidth: `${timelineMonthsData.length * 200}px` }} />
            
            <div className="flex gap-2" style={{ minWidth: `${timelineMonthsData.length * 200}px` }}>
              {timelineMonthsData.map((monthData, idx) => {
                const monthEvents = getEventsForMonth(monthData.key);
                const isCurrentMonth = monthData.key === currentMonthKey;
                const isSelected = selectedMonth?.year === monthData.year && selectedMonth?.month === monthData.month;
                
                return (
                  <motion.div
                    key={monthData.key}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.05 }}
                    className="flex-shrink-0 w-48"
                  >
                    {/* Events Above Line */}
                    <div className="h-16 mb-2 flex flex-col justify-end">
                      {monthEvents.slice(0, 3).map((event, evIdx) => (
                        <motion.div
                          key={event.id}
                          whileHover={{ scale: 1.05, y: -2 }}
                          onClick={() => {
                            setSelectedEvent(event);
                            openEventModal(event);
                          }}
                          className="cursor-pointer mb-1 px-2 py-1 rounded-lg text-xs font-medium truncate transition-all hover:shadow-lg"
                          style={{ 
                            backgroundColor: `${event.color}20`,
                            borderLeft: `3px solid ${event.color}`,
                            color: event.color
                          }}
                          title={`${event.title} - ${new Date(event.date).getDate()} ${MONTHS_SHORT_TR[monthData.month]}`}
                        >
                          {event.title}
                        </motion.div>
                      ))}
                      {monthEvents.length > 3 && (
                        <span className="text-xs text-muted-foreground pl-2">
                          +{monthEvents.length - 3} daha
                        </span>
                      )}
                    </div>
                    
                    {/* Month Node on Line */}
                    <motion.button
                      whileHover={{ scale: 1.1 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => {
                        if (isSelected) {
                          setSelectedMonth(null);
                        } else {
                          setSelectedMonth({ year: monthData.year, month: monthData.month });
                        }
                      }}
                      className={cn(
                        "relative w-full flex flex-col items-center py-3 rounded-xl transition-all",
                        isSelected && "bg-primary-500/20 ring-2 ring-primary-500",
                        isCurrentMonth && !isSelected && "bg-green-500/10 ring-2 ring-green-500",
                        !isSelected && !isCurrentMonth && "hover:bg-muted/50"
                      )}
                    >
                      {/* Node Circle */}
                      <div className={cn(
                        "w-5 h-5 rounded-full border-4 mb-2",
                        isCurrentMonth ? "bg-green-500 border-green-300" : "bg-primary-500 border-primary-300",
                        monthEvents.length > 0 && "ring-4 ring-primary-500/20"
                      )} />
                      
                      {/* Month Name */}
                      <span className={cn(
                        "font-bold text-base",
                        isCurrentMonth ? "text-green-500" : isSelected ? "text-primary-500" : "text-foreground"
                      )}>
                        {MONTHS_TR[monthData.month]}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {monthData.year}
                      </span>
                      
                      {/* Event Count Badge */}
                      {monthEvents.length > 0 && (
                        <span className="absolute -top-1 -right-1 w-6 h-6 bg-primary-500 text-white text-xs font-bold rounded-full flex items-center justify-center shadow-lg">
                          {monthEvents.length}
                        </span>
                      )}
                    </motion.button>
                  </motion.div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Selected Month Detail */}
        <AnimatePresence>
          {selectedMonth && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mb-8 overflow-hidden"
            >
              <div className="bg-card border border-border rounded-2xl p-6">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="text-lg font-bold flex items-center gap-2">
                    <Calendar className="w-5 h-5 text-primary-500" />
                    {MONTHS_TR[selectedMonth.month]} {selectedMonth.year} Etkinlikleri
                  </h4>
                  <div className="flex gap-2">
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => openEventModal(undefined, selectedMonth)}
                      className="flex items-center gap-2 px-3 py-1.5 bg-primary-500 text-white rounded-lg text-sm font-medium hover:bg-primary-600 transition-colors"
                    >
                      <Plus className="w-4 h-4" />
                      Ekle
                    </motion.button>
                    <button
                      onClick={() => setSelectedMonth(null)}
                      className="p-1.5 hover:bg-muted rounded-lg transition-colors"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                
                {getEventsForMonth(getMonthKey(selectedMonth.year, selectedMonth.month)).length === 0 ? (
                  <p className="text-muted-foreground text-center py-8">
                    Bu ayda henüz etkinlik yok
                  </p>
                ) : (
                  <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
                    {getEventsForMonth(getMonthKey(selectedMonth.year, selectedMonth.month))
                      .sort((a, b) => a.date.localeCompare(b.date))
                      .map((event) => {
                        const eventDate = new Date(event.date);
                        return (
                          <motion.div
                            key={event.id}
                            whileHover={{ scale: 1.02 }}
                            onClick={() => openEventModal(event)}
                            className="group cursor-pointer bg-background border border-border rounded-xl p-4 hover:shadow-lg transition-all"
                            style={{ borderLeftWidth: '4px', borderLeftColor: event.color }}
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-1">
                                  <span className="text-sm font-bold" style={{ color: event.color }}>
                                    {eventDate.getDate()} {MONTHS_SHORT_TR[eventDate.getMonth()]}
                                  </span>
                                  {event.time && (
                                    <span className="flex items-center gap-1 text-xs text-muted-foreground">
                                      <Clock className="w-3 h-3" />
                                      {event.time}
                                    </span>
                                  )}
                                </div>
                                <h5 className="font-semibold truncate">{event.title}</h5>
                                {event.description && (
                                  <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
                                    {event.description}
                                  </p>
                                )}
                              </div>
                              <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity ml-2">
                                <button
                                  onClick={(e) => { e.stopPropagation(); deleteEvent(event.id); }}
                                  className="p-1 hover:bg-red-500/10 rounded text-red-500"
                                >
                                  <Trash2 className="w-3.5 h-3.5" />
                                </button>
                              </div>
                            </div>
                          </motion.div>
                        );
                      })}
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* History Section */}
        <div className="border-t border-border pt-6">
          <button
            onClick={() => setShowHistory(!showHistory)}
            className="flex items-center gap-2 text-lg font-semibold mb-4 hover:text-primary-500 transition-colors"
          >
            <History className="w-5 h-5 text-muted-foreground" />
            Geçmiş
            <span className="text-sm text-muted-foreground font-normal">
              ({pastEvents.length} etkinlik)
            </span>
            {showHistory ? (
              <ChevronUp className="w-4 h-4 ml-auto" />
            ) : (
              <ChevronDown className="w-4 h-4 ml-auto" />
            )}
          </button>
          
          <AnimatePresence>
            {showHistory && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="overflow-hidden"
              >
                {pastEvents.length === 0 ? (
                  <p className="text-muted-foreground text-center py-8">
                    Henüz geçmiş etkinlik yok
                  </p>
                ) : (
                  <div className="space-y-2 max-h-96 overflow-y-auto pr-2">
                    {pastEvents.map((event) => {
                      const eventDate = new Date(event.date);
                      return (
                        <motion.div
                          key={event.id}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          whileHover={{ x: 4 }}
                          onClick={() => openEventModal(event)}
                          className="group cursor-pointer flex items-center gap-4 p-3 bg-muted/30 rounded-xl hover:bg-muted/50 transition-all"
                        >
                          {/* Date */}
                          <div className="flex-shrink-0 w-16 text-center">
                            <span className="block text-lg font-bold text-muted-foreground">
                              {eventDate.getDate()}
                            </span>
                            <span className="text-xs text-muted-foreground">
                              {MONTHS_SHORT_TR[eventDate.getMonth()]} {eventDate.getFullYear()}
                            </span>
                          </div>
                          
                          {/* Color Bar */}
                          <div 
                            className="w-1 h-10 rounded-full flex-shrink-0"
                            style={{ backgroundColor: event.color }}
                          />
                          
                          {/* Content */}
                          <div className="flex-1 min-w-0">
                            <h5 className="font-medium truncate">{event.title}</h5>
                            {event.description && (
                              <p className="text-xs text-muted-foreground truncate">
                                {event.description}
                              </p>
                            )}
                          </div>
                          
                          {/* Category & Actions */}
                          <div className="flex items-center gap-2">
                            {event.category && (
                              <span className="px-2 py-0.5 bg-background text-xs rounded-full border border-border">
                                {event.category}
                              </span>
                            )}
                            <button
                              onClick={(e) => { e.stopPropagation(); deleteEvent(event.id); }}
                              className="p-1.5 opacity-0 group-hover:opacity-100 hover:bg-red-500/10 rounded-lg text-red-500 transition-all"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </motion.div>
                      );
                    })}
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
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
                {/* Date Picker */}
                <div>
                  <label className="text-sm font-medium text-muted-foreground mb-1 block">
                    Tarih *
                  </label>
                  <input
                    type="date"
                    value={eventDate}
                    onChange={e => setEventDate(e.target.value)}
                    className="w-full px-4 py-2.5 bg-background border border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 transition-all"
                  />
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
                    disabled={!eventTitle.trim() || !eventDate}
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
