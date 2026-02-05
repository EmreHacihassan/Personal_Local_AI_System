'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ExternalLink, 
  ChevronDown, 
  ChevronUp, 
  Star, 
  Shield, 
  AlertTriangle,
  Book,
  Newspaper,
  FileText,
  Globe,
  Award,
  CheckCircle
} from 'lucide-react';

// ============ TYPES ============

interface Source {
  title: string;
  url: string;
  snippet: string;
  domain?: string;
  sourceType?: 'academic' | 'wiki' | 'news' | 'blog' | 'official' | 'documentation' | 'forum' | 'unknown';
  reliabilityScore?: number;
  grade?: 'A' | 'B' | 'C' | 'D' | 'F';
  favicon?: string;
  author?: string;
  date?: string;
}

interface SourceCardsProps {
  sources: Source[];
  maxVisible?: number;
  variant?: 'compact' | 'detailed' | 'minimal' | 'grouped';
  showGrades?: boolean;
  enableGrouping?: boolean;
  enableSearch?: boolean;
  enableExport?: boolean;
  onSourceClick?: (source: Source) => void;
}

// ============ HELPER FUNCTIONS ============

const getSourceIcon = (type: string | undefined) => {
  switch (type) {
    case 'academic':
      return <Award className="w-4 h-4 text-purple-500" />;
    case 'wiki':
      return <Book className="w-4 h-4 text-blue-500" />;
    case 'news':
      return <Newspaper className="w-4 h-4 text-red-500" />;
    case 'documentation':
      return <FileText className="w-4 h-4 text-green-500" />;
    case 'official':
      return <Shield className="w-4 h-4 text-emerald-500" />;
    case 'blog':
      return <Globe className="w-4 h-4 text-orange-500" />;
    default:
      return <Globe className="w-4 h-4 text-gray-500" />;
  }
};

const getGradeColor = (grade: string | undefined) => {
  switch (grade) {
    case 'A':
      return 'bg-green-500/20 text-green-400 border-green-500/30';
    case 'B':
      return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
    case 'C':
      return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
    case 'D':
      return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
    case 'F':
      return 'bg-red-500/20 text-red-400 border-red-500/30';
    default:
      return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
  }
};

const getReliabilityIndicator = (score: number | undefined) => {
  if (!score) return null;
  
  const percentage = Math.round(score * 100);
  let color = 'text-gray-400';
  let Icon = AlertTriangle;
  
  if (percentage >= 80) {
    color = 'text-green-400';
    Icon = CheckCircle;
  } else if (percentage >= 60) {
    color = 'text-yellow-400';
    Icon = Star;
  }
  
  return (
    <div className={`flex items-center gap-1 text-xs ${color}`}>
      <Icon className="w-3 h-3" />
      <span>{percentage}%</span>
    </div>
  );
};

// ============ SINGLE SOURCE CARD ============

const SourceCard: React.FC<{
  source: Source;
  index: number;
  variant: 'compact' | 'detailed' | 'minimal';
  showGrade: boolean;
  onClick?: () => void;
}> = ({ source, index, variant, showGrade, onClick }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  // Extract domain from URL if not provided
  const domain = source.domain || new URL(source.url).hostname.replace('www.', '');
  
  // Minimal variant
  if (variant === 'minimal') {
    return (
      <motion.a
        href={source.url}
        target="_blank"
        rel="noopener noreferrer"
        initial={{ opacity: 0, x: -10 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: index * 0.05 }}
        className="inline-flex items-center gap-1 px-2 py-1 text-xs rounded-full 
                   bg-white/5 hover:bg-white/10 text-white/70 hover:text-white
                   border border-white/10 hover:border-white/20 transition-all"
        onClick={(e) => {
          if (onClick) {
            e.preventDefault();
            onClick();
          }
        }}
      >
        {getSourceIcon(source.sourceType)}
        <span className="truncate max-w-[120px]">{domain}</span>
        {showGrade && source.grade && (
          <span className={`px-1 rounded text-[10px] font-bold ${getGradeColor(source.grade)}`}>
            {source.grade}
          </span>
        )}
      </motion.a>
    );
  }
  
  // Compact variant
  if (variant === 'compact') {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: index * 0.05 }}
        className="group flex items-center gap-3 p-2 rounded-lg bg-white/[0.03] 
                   hover:bg-white/[0.06] border border-white/5 hover:border-white/10 
                   transition-all cursor-pointer"
        onClick={onClick}
      >
        {/* Index badge */}
        <div className="flex-shrink-0 w-6 h-6 rounded-full bg-white/10 
                        flex items-center justify-center text-xs font-medium text-white/60">
          {index + 1}
        </div>
        
        {/* Icon & Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            {getSourceIcon(source.sourceType)}
            <span className="text-sm font-medium text-white/90 truncate">
              {source.title}
            </span>
          </div>
          <div className="flex items-center gap-2 mt-0.5">
            <span className="text-xs text-white/50 truncate">{domain}</span>
            {showGrade && source.grade && (
              <span className={`px-1 py-0.5 rounded text-[10px] font-bold border ${getGradeColor(source.grade)}`}>
                {source.grade}
              </span>
            )}
          </div>
        </div>
        
        {/* External link */}
        <a
          href={source.url}
          target="_blank"
          rel="noopener noreferrer"
          className="opacity-0 group-hover:opacity-100 transition-opacity"
          onClick={(e) => e.stopPropagation()}
        >
          <ExternalLink className="w-4 h-4 text-white/50 hover:text-white" />
        </a>
      </motion.div>
    );
  }
  
  // Detailed variant
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08, type: 'spring', stiffness: 100 }}
      className="group rounded-xl bg-gradient-to-br from-white/[0.05] to-white/[0.02] 
                 border border-white/10 hover:border-white/20 overflow-hidden transition-all"
    >
      {/* Header */}
      <div className="p-4 border-b border-white/5">
        <div className="flex items-start gap-3">
          {/* Index badge with favicon */}
          <div className="relative flex-shrink-0">
            <div className="w-10 h-10 rounded-lg bg-white/10 flex items-center justify-center">
              {source.favicon ? (
                <img src={source.favicon} alt="" className="w-6 h-6 rounded" />
              ) : (
                getSourceIcon(source.sourceType)
              )}
            </div>
            <div className="absolute -bottom-1 -right-1 w-5 h-5 rounded-full bg-white/20 
                            flex items-center justify-center text-[10px] font-bold text-white">
              {index + 1}
            </div>
          </div>
          
          {/* Title & Meta */}
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-white/90 line-clamp-2 group-hover:text-white transition-colors">
              {source.title}
            </h3>
            <div className="flex items-center gap-2 mt-1 flex-wrap">
              <span className="text-xs text-white/50">{domain}</span>
              {source.date && (
                <span className="text-xs text-white/40">• {source.date}</span>
              )}
              {source.author && (
                <span className="text-xs text-white/40">• {source.author}</span>
              )}
            </div>
          </div>
          
          {/* Grade & Reliability */}
          <div className="flex flex-col items-end gap-1">
            {showGrade && source.grade && (
              <div className={`px-2 py-1 rounded-md text-sm font-bold border ${getGradeColor(source.grade)}`}>
                Grade {source.grade}
              </div>
            )}
            {getReliabilityIndicator(source.reliabilityScore)}
          </div>
        </div>
      </div>
      
      {/* Snippet */}
      <div className="p-4">
        <p className={`text-sm text-white/70 ${isExpanded ? '' : 'line-clamp-2'}`}>
          {source.snippet}
        </p>
        
        {source.snippet.length > 150 && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center gap-1 mt-2 text-xs text-blue-400 hover:text-blue-300 transition-colors"
          >
            {isExpanded ? (
              <>
                <ChevronUp className="w-3 h-3" />
                Daha az göster
              </>
            ) : (
              <>
                <ChevronDown className="w-3 h-3" />
                Daha fazla göster
              </>
            )}
          </button>
        )}
      </div>
      
      {/* Footer */}
      <div className="px-4 pb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          {getSourceIcon(source.sourceType)}
          <span className="text-xs text-white/40 capitalize">
            {source.sourceType || 'Web'}
          </span>
        </div>
        
        <a
          href={source.url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-blue-500/20 
                     text-blue-400 text-xs font-medium hover:bg-blue-500/30 transition-colors"
        >
          <ExternalLink className="w-3 h-3" />
          Kaynağı Aç
        </a>
      </div>
    </motion.div>
  );
};

// ============ MAIN COMPONENT ============

// Helper to group sources by type
const groupSourcesByType = (sources: Source[]) => {
  const groups: Record<string, Source[]> = {
    academic: [],
    wiki: [],
    documentation: [],
    official: [],
    news: [],
    blog: [],
    forum: [],
    other: [],
  };
  
  sources.forEach(source => {
    const type = source.sourceType || 'other';
    if (type in groups) {
      groups[type].push(source);
    } else {
      groups.other.push(source);
    }
  });
  
  // Remove empty groups
  return Object.fromEntries(
    Object.entries(groups).filter(([_, arr]) => arr.length > 0)
  );
};

const GROUP_LABELS: Record<string, { label: string; emoji: string }> = {
  academic: { label: 'Akademik', emoji: '🎓' },
  wiki: { label: 'Ansiklopedi', emoji: '📚' },
  documentation: { label: 'Dokümantasyon', emoji: '📖' },
  official: { label: 'Resmi', emoji: '🏛️' },
  news: { label: 'Haber', emoji: '📰' },
  blog: { label: 'Blog', emoji: '✍️' },
  forum: { label: 'Forum', emoji: '💬' },
  other: { label: 'Diğer', emoji: '🌐' },
};

export const SourceCards: React.FC<SourceCardsProps> = ({
  sources,
  maxVisible = 10,
  variant = 'compact',
  showGrades = true,
  enableGrouping = false,
  enableSearch = false,
  enableExport = false,
  onSourceClick,
}) => {
  const [showAll, setShowAll] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeGroup, setActiveGroup] = useState<string | null>(null);
  
  // Filter sources by search
  const filteredSources = searchQuery 
    ? sources.filter(s => 
        s.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.url.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : sources;
  
  // Group sources if enabled
  const groupedSources = enableGrouping ? groupSourcesByType(filteredSources) : null;
  
  // Determine visible sources
  const visibleSources = showAll 
    ? filteredSources 
    : filteredSources.slice(0, maxVisible);
  const hasMore = filteredSources.length > maxVisible;
  
  // Export function
  const exportSources = () => {
    const csvContent = [
      ['Title', 'URL', 'Type', 'Grade'].join(','),
      ...sources.map(s => [
        `"${s.title.replace(/"/g, '""')}"`,
        s.url,
        s.sourceType || 'unknown',
        s.grade || '-'
      ].join(','))
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'kaynaklar.csv';
    a.click();
    URL.revokeObjectURL(url);
  };
  
  if (sources.length === 0) {
    return null;
  }
  
  // Minimal variant - inline badges
  if (variant === 'minimal') {
    return (
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs text-white/40">Kaynaklar:</span>
        {visibleSources.map((source, index) => (
          <SourceCard
            key={source.url}
            source={source}
            index={index}
            variant="minimal"
            showGrade={showGrades}
            onClick={onSourceClick ? () => onSourceClick(source) : undefined}
          />
        ))}
        {hasMore && !showAll && (
          <button
            onClick={() => setShowAll(true)}
            className="text-xs text-blue-400 hover:text-blue-300"
          >
            +{sources.length - maxVisible} daha
          </button>
        )}
      </div>
    );
  }
  
  // Grouped variant - for 40+ sources
  if (variant === 'grouped' || (enableGrouping && groupedSources)) {
    const groups = groupedSources || groupSourcesByType(filteredSources);
    const groupKeys = Object.keys(groups);
    
    return (
      <div className="space-y-4">
        {/* Header with stats */}
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <div className="w-1 h-4 rounded-full bg-gradient-to-b from-green-500 to-blue-500" />
            <h3 className="text-sm font-semibold text-white/80">
              Kaynaklar
            </h3>
            <span className="px-2 py-0.5 rounded-full bg-green-500/20 text-xs text-green-400 font-bold">
              {sources.length}
            </span>
          </div>
          
          <div className="flex items-center gap-2">
            {enableSearch && (
              <input
                type="text"
                placeholder="Kaynak ara..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="px-3 py-1 text-xs rounded-lg bg-white/5 border border-white/10 
                           text-white placeholder-white/30 focus:outline-none focus:border-white/30"
              />
            )}
            {enableExport && (
              <button
                onClick={exportSources}
                className="px-2 py-1 text-xs rounded-lg bg-white/5 hover:bg-white/10 
                           text-white/60 hover:text-white transition-colors"
              >
                📥 Export
              </button>
            )}
          </div>
        </div>
        
        {/* Group tabs */}
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setActiveGroup(null)}
            className={`px-3 py-1.5 text-xs rounded-lg transition-colors ${
              activeGroup === null 
                ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' 
                : 'bg-white/5 text-white/60 hover:bg-white/10'
            }`}
          >
            Tümü ({sources.length})
          </button>
          {groupKeys.map(key => {
            const info = GROUP_LABELS[key] || { label: key, emoji: '📄' };
            const count = groups[key].length;
            return (
              <button
                key={key}
                onClick={() => setActiveGroup(activeGroup === key ? null : key)}
                className={`px-3 py-1.5 text-xs rounded-lg transition-colors ${
                  activeGroup === key 
                    ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' 
                    : 'bg-white/5 text-white/60 hover:bg-white/10'
                }`}
              >
                {info.emoji} {info.label} ({count})
              </button>
            );
          })}
        </div>
        
        {/* Sources list */}
        <div className="space-y-2 max-h-[400px] overflow-y-auto pr-2">
          <AnimatePresence mode="popLayout">
            {(activeGroup ? groups[activeGroup] : visibleSources).map((source, index) => (
              <SourceCard
                key={source.url}
                source={source}
                index={index}
                variant="compact"
                showGrade={showGrades}
                onClick={onSourceClick ? () => onSourceClick(source) : undefined}
              />
            ))}
          </AnimatePresence>
        </div>
        
        {/* Show more (only when no active group) */}
        {!activeGroup && hasMore && (
          <motion.button
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            onClick={() => setShowAll(!showAll)}
            className="w-full py-2 rounded-lg bg-white/[0.03] hover:bg-white/[0.06] 
                       border border-white/5 hover:border-white/10 transition-all
                       flex items-center justify-center gap-2 text-sm text-white/60 hover:text-white/80"
          >
            {showAll ? (
              <>
                <ChevronUp className="w-4 h-4" />
                Daha az göster
              </>
            ) : (
              <>
                <ChevronDown className="w-4 h-4" />
                {sources.length - maxVisible} kaynak daha göster
              </>
            )}
          </motion.button>
        )}
      </div>
    );
  }
  
  // Default compact/detailed view
  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-1 h-4 rounded-full bg-gradient-to-b from-blue-500 to-purple-500" />
          <h3 className="text-sm font-semibold text-white/80">
            Kaynaklar
          </h3>
          <span className="px-2 py-0.5 rounded-full bg-white/10 text-xs text-white/60">
            {sources.length}
          </span>
        </div>
        
        {showGrades && (
          <div className="flex items-center gap-1 text-xs text-white/40">
            <Shield className="w-3 h-3" />
            Kalite Puanlı
          </div>
        )}
      </div>
      
      {/* Sources Grid/List */}
      <div className={variant === 'detailed' ? 'grid gap-4 md:grid-cols-2' : 'space-y-2'}>
        <AnimatePresence mode="popLayout">
          {visibleSources.map((source, index) => (
            <SourceCard
              key={source.url}
              source={source}
              index={index}
              variant={variant}
              showGrade={showGrades}
              onClick={onSourceClick ? () => onSourceClick(source) : undefined}
            />
          ))}
        </AnimatePresence>
      </div>
      
      {/* Show More Button */}
      {hasMore && (
        <motion.button
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          onClick={() => setShowAll(!showAll)}
          className="w-full py-2 rounded-lg bg-white/[0.03] hover:bg-white/[0.06] 
                     border border-white/5 hover:border-white/10 transition-all
                     flex items-center justify-center gap-2 text-sm text-white/60 hover:text-white/80"
        >
          {showAll ? (
            <>
              <ChevronUp className="w-4 h-4" />
              Daha az göster
            </>
          ) : (
            <>
              <ChevronDown className="w-4 h-4" />
              {sources.length - maxVisible} kaynak daha göster
            </>
          )}
        </motion.button>
      )}
    </div>
  );
};

export default SourceCards;
