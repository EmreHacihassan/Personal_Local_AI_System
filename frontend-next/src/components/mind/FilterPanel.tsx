'use client';

/**
 * FilterPanel - Mind Graf Filtre Paneli
 * 
 * Renk, tag, tarih ve derinlik bazlı filtreleme.
 * Heat map ve layout seçenekleri.
 */

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import dynamic from 'next/dynamic';
import type { ComponentType } from 'react';
import { cn } from '@/lib/utils';

// Dynamic icon imports to prevent SSR/hydration issues
const Filter = dynamic(() => import('lucide-react').then(mod => mod.Filter), { ssr: false }) as ComponentType<any>;
const Palette = dynamic(() => import('lucide-react').then(mod => mod.Palette), { ssr: false }) as ComponentType<any>;
const Tag = dynamic(() => import('lucide-react').then(mod => mod.Tag), { ssr: false }) as ComponentType<any>;
const Calendar = dynamic(() => import('lucide-react').then(mod => mod.Calendar), { ssr: false }) as ComponentType<any>;
const Layers = dynamic(() => import('lucide-react').then(mod => mod.Layers), { ssr: false }) as ComponentType<any>;
const Flame = dynamic(() => import('lucide-react').then(mod => mod.Flame), { ssr: false }) as ComponentType<any>;
const LayoutGrid = dynamic(() => import('lucide-react').then(mod => mod.LayoutGrid), { ssr: false }) as ComponentType<any>;
const Network = dynamic(() => import('lucide-react').then(mod => mod.Network), { ssr: false }) as ComponentType<any>;
const CircleDot = dynamic(() => import('lucide-react').then(mod => mod.CircleDot), { ssr: false }) as ComponentType<any>;
const Clock = dynamic(() => import('lucide-react').then(mod => mod.Clock), { ssr: false }) as ComponentType<any>;
const TreeDeciduous = dynamic(() => import('lucide-react').then(mod => mod.TreeDeciduous), { ssr: false }) as ComponentType<any>;
const X = dynamic(() => import('lucide-react').then(mod => mod.X), { ssr: false }) as ComponentType<any>;
const ChevronDown = dynamic(() => import('lucide-react').then(mod => mod.ChevronDown), { ssr: false }) as ComponentType<any>;
const RotateCcw = dynamic(() => import('lucide-react').then(mod => mod.RotateCcw), { ssr: false }) as ComponentType<any>;

export type LayoutType = 'force' | 'hierarchical' | 'radial' | 'timeline';

interface FilterPanelProps {
    // Filters
    selectedColors: string[];
    selectedTags: string[];
    dateRange: { from?: Date; to?: Date };
    depthLimit: number;
    showHeatMap: boolean;
    layout: LayoutType;
    // All available options
    allTags: string[];
    // Callbacks
    onColorsChange: (colors: string[]) => void;
    onTagsChange: (tags: string[]) => void;
    onDateRangeChange: (range: { from?: Date; to?: Date }) => void;
    onDepthLimitChange: (depth: number) => void;
    onHeatMapToggle: () => void;
    onLayoutChange: (layout: LayoutType) => void;
    onReset: () => void;
    onClose: () => void;
    language?: 'tr' | 'en' | 'de';
}

const COLORS = [
    { id: 'default', name: 'Gri', class: 'bg-gray-400' },
    { id: 'yellow', name: 'Sarı', class: 'bg-yellow-400' },
    { id: 'green', name: 'Yeşil', class: 'bg-green-400' },
    { id: 'blue', name: 'Mavi', class: 'bg-blue-400' },
    { id: 'purple', name: 'Mor', class: 'bg-purple-400' },
    { id: 'pink', name: 'Pembe', class: 'bg-pink-400' },
    { id: 'orange', name: 'Turuncu', class: 'bg-orange-400' },
    { id: 'red', name: 'Kırmızı', class: 'bg-red-400' },
];

const LAYOUTS: { id: LayoutType; name: string; nameEn: string; iconId: 'network' | 'tree' | 'circle' | 'clock' }[] = [
    { id: 'force', name: 'Fizik Tabanlı', nameEn: 'Force-Directed', iconId: 'network' },
    { id: 'hierarchical', name: 'Hiyerarşik', nameEn: 'Hierarchical', iconId: 'tree' },
    { id: 'radial', name: 'Dairesel', nameEn: 'Radial', iconId: 'circle' },
    { id: 'timeline', name: 'Zaman Çizgisi', nameEn: 'Timeline', iconId: 'clock' },
];

// Helper component to render layout icons
const LayoutIcon = ({ iconId }: { iconId: string }) => {
    switch (iconId) {
        case 'network': return <Network className="w-4 h-4" />;
        case 'tree': return <TreeDeciduous className="w-4 h-4" />;
        case 'circle': return <CircleDot className="w-4 h-4" />;
        case 'clock': return <Clock className="w-4 h-4" />;
        default: return null;
    }
};

const translations = {
    filters: { tr: 'Filtreler', en: 'Filters', de: 'Filter' },
    layout: { tr: 'Düzen', en: 'Layout', de: 'Layout' },
    colors: { tr: 'Renkler', en: 'Colors', de: 'Farben' },
    tags: { tr: 'Etiketler', en: 'Tags', de: 'Tags' },
    dateRange: { tr: 'Tarih Aralığı', en: 'Date Range', de: 'Datumsbereich' },
    from: { tr: 'Başlangıç', en: 'From', de: 'Von' },
    to: { tr: 'Bitiş', en: 'To', de: 'Bis' },
    depth: { tr: 'Bağlantı Derinliği', en: 'Connection Depth', de: 'Verbindungstiefe' },
    heatMap: { tr: 'Isı Haritası', en: 'Heat Map', de: 'Heatmap' },
    reset: { tr: 'Sıfırla', en: 'Reset', de: 'Zurücksetzen' },
    all: { tr: 'Tümü', en: 'All', de: 'Alle' },
};

export function FilterPanel({
    selectedColors,
    selectedTags,
    dateRange,
    depthLimit,
    showHeatMap,
    layout,
    allTags,
    onColorsChange,
    onTagsChange,
    onDateRangeChange,
    onDepthLimitChange,
    onHeatMapToggle,
    onLayoutChange,
    onReset,
    onClose,
    language = 'tr'
}: FilterPanelProps) {
    const t = translations;
    const [expandedSection, setExpandedSection] = useState<string | null>('layout');

    const toggleColor = (colorId: string) => {
        if (selectedColors.includes(colorId)) {
            onColorsChange(selectedColors.filter(c => c !== colorId));
        } else {
            onColorsChange([...selectedColors, colorId]);
        }
    };

    const toggleTag = (tag: string) => {
        if (selectedTags.includes(tag)) {
            onTagsChange(selectedTags.filter(t => t !== tag));
        } else {
            onTagsChange([...selectedTags, tag]);
        }
    };

    const hasActiveFilters = selectedColors.length > 0 ||
        selectedTags.length > 0 ||
        dateRange.from ||
        dateRange.to ||
        depthLimit > 0;

    const Section = ({ id, title, icon, children }: { id: string; title: string; icon: React.ReactNode; children: React.ReactNode }) => (
        <div className="border-b border-border last:border-b-0">
            <button
                onClick={() => setExpandedSection(expandedSection === id ? null : id)}
                className="w-full flex items-center justify-between p-3 hover:bg-muted/50 transition-colors"
            >
                <div className="flex items-center gap-2">
                    {icon}
                    <span className="text-sm font-medium">{title}</span>
                </div>
                <ChevronDown className={cn(
                    "w-4 h-4 text-muted-foreground transition-transform",
                    expandedSection === id && "rotate-180"
                )} />
            </button>
            <AnimatePresence>
                {expandedSection === id && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden"
                    >
                        <div className="p-3 pt-0">
                            {children}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );

    return (
        <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="w-72 h-full flex flex-col bg-card border-r border-border"
        >
            {/* Header */}
            <div className="p-4 border-b border-border bg-gradient-to-r from-violet-500/5 to-fuchsia-500/5">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="p-2 rounded-lg bg-violet-500/10">
                            <Filter className="w-4 h-4 text-violet-500" />
                        </div>
                        <h3 className="font-semibold">{t.filters[language]}</h3>
                    </div>
                    <div className="flex items-center gap-1">
                        {hasActiveFilters && (
                            <button
                                onClick={onReset}
                                className="p-1.5 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                                title={t.reset[language]}
                            >
                                <RotateCcw className="w-4 h-4" />
                            </button>
                        )}
                        <button
                            onClick={onClose}
                            className="p-1.5 rounded-lg hover:bg-muted transition-colors"
                        >
                            <X className="w-4 h-4 text-muted-foreground" />
                        </button>
                    </div>
                </div>
            </div>

            {/* Sections */}
            <div className="flex-1 overflow-y-auto">
                {/* Layout Section */}
                <Section
                    id="layout"
                    title={t.layout[language]}
                    icon={<LayoutGrid className="w-4 h-4 text-muted-foreground" />}
                >
                    <div className="grid grid-cols-2 gap-2">
                        {LAYOUTS.map(l => (
                            <motion.button
                                key={l.id}
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                                onClick={() => onLayoutChange(l.id)}
                                className={cn(
                                    "flex flex-col items-center gap-2 p-3 rounded-xl border transition-all",
                                    layout === l.id
                                        ? "border-primary-500 bg-primary-500/10"
                                        : "border-border hover:border-primary-500/50"
                                )}
                            >
                                <div className={cn(
                                    "p-2 rounded-lg",
                                    layout === l.id ? "bg-primary-500/20 text-primary-500" : "bg-muted text-muted-foreground"
                                )}>
                                    <LayoutIcon iconId={l.iconId} />
                                </div>
                                <span className="text-xs font-medium">
                                    {language === 'tr' ? l.name : l.nameEn}
                                </span>
                            </motion.button>
                        ))}
                    </div>
                </Section>

                {/* Colors Section */}
                <Section
                    id="colors"
                    title={t.colors[language]}
                    icon={<Palette className="w-4 h-4 text-muted-foreground" />}
                >
                    <div className="flex flex-wrap gap-2">
                        {COLORS.map(color => (
                            <button
                                key={color.id}
                                onClick={() => toggleColor(color.id)}
                                className={cn(
                                    "w-8 h-8 rounded-full transition-all",
                                    color.class,
                                    selectedColors.includes(color.id)
                                        ? "ring-2 ring-offset-2 ring-primary-500 scale-110"
                                        : "opacity-60 hover:opacity-100 hover:scale-105"
                                )}
                                title={color.name}
                            />
                        ))}
                    </div>
                </Section>

                {/* Tags Section */}
                {allTags.length > 0 && (
                    <Section
                        id="tags"
                        title={t.tags[language]}
                        icon={<Tag className="w-4 h-4 text-muted-foreground" />}
                    >
                        <div className="flex flex-wrap gap-1.5">
                            {allTags.map(tag => (
                                <button
                                    key={tag}
                                    onClick={() => toggleTag(tag)}
                                    className={cn(
                                        "px-2.5 py-1 rounded-full text-xs font-medium transition-colors",
                                        selectedTags.includes(tag)
                                            ? "bg-primary-500 text-white"
                                            : "bg-muted text-muted-foreground hover:bg-muted/80"
                                    )}
                                >
                                    {tag}
                                </button>
                            ))}
                        </div>
                    </Section>
                )}

                {/* Date Range Section */}
                <Section
                    id="date"
                    title={t.dateRange[language]}
                    icon={<Calendar className="w-4 h-4 text-muted-foreground" />}
                >
                    <div className="space-y-2">
                        <div>
                            <label className="text-xs text-muted-foreground mb-1 block">{t.from[language]}</label>
                            <input
                                type="date"
                                value={dateRange.from?.toISOString().split('T')[0] || ''}
                                onChange={(e) => onDateRangeChange({
                                    ...dateRange,
                                    from: e.target.value ? new Date(e.target.value) : undefined
                                })}
                                className="w-full px-3 py-2 rounded-lg bg-muted border border-border text-sm"
                            />
                        </div>
                        <div>
                            <label className="text-xs text-muted-foreground mb-1 block">{t.to[language]}</label>
                            <input
                                type="date"
                                value={dateRange.to?.toISOString().split('T')[0] || ''}
                                onChange={(e) => onDateRangeChange({
                                    ...dateRange,
                                    to: e.target.value ? new Date(e.target.value) : undefined
                                })}
                                className="w-full px-3 py-2 rounded-lg bg-muted border border-border text-sm"
                            />
                        </div>
                    </div>
                </Section>

                {/* Depth Limit Section */}
                <Section
                    id="depth"
                    title={t.depth[language]}
                    icon={<Layers className="w-4 h-4 text-muted-foreground" />}
                >
                    <div className="space-y-3">
                        <input
                            type="range"
                            min="0"
                            max="5"
                            value={depthLimit}
                            onChange={(e) => onDepthLimitChange(parseInt(e.target.value))}
                            className="w-full accent-primary-500"
                        />
                        <div className="flex justify-between text-xs text-muted-foreground">
                            <span>{t.all[language]}</span>
                            <span className="font-medium text-foreground">
                                {depthLimit === 0 ? t.all[language] : `${depthLimit} seviye`}
                            </span>
                            <span>5</span>
                        </div>
                    </div>
                </Section>

                {/* Heat Map Toggle */}
                <div className="p-3 border-b border-border">
                    <label className="flex items-center gap-3 cursor-pointer group">
                        <div className={cn(
                            "p-2 rounded-lg transition-colors",
                            showHeatMap ? "bg-orange-500/20" : "bg-muted"
                        )}>
                            <Flame className={cn(
                                "w-4 h-4 transition-colors",
                                showHeatMap ? "text-orange-500" : "text-muted-foreground"
                            )} />
                        </div>
                        <div className="flex-1">
                            <span className="text-sm font-medium">{t.heatMap[language]}</span>
                            <p className="text-xs text-muted-foreground">
                                {language === 'tr' ? 'Bağlantı yoğunluğunu göster' : 'Show connection density'}
                            </p>
                        </div>
                        <div className={cn(
                            "w-10 h-6 rounded-full transition-colors flex items-center px-1",
                            showHeatMap ? "bg-orange-500" : "bg-muted"
                        )}>
                            <motion.div
                                animate={{ x: showHeatMap ? 16 : 0 }}
                                className="w-4 h-4 rounded-full bg-white shadow-sm"
                            />
                        </div>
                        <input
                            type="checkbox"
                            checked={showHeatMap}
                            onChange={onHeatMapToggle}
                            className="sr-only"
                        />
                    </label>
                </div>
            </div>
        </motion.div>
    );
}

export default FilterPanel;
