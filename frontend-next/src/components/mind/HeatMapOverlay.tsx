'use client';

/**
 * HeatMapOverlay - Aktivite Yoğunluğu Görselleştirme
 * 
 * Graf üzerinde notların aktivite yoğunluğunu ısı haritası olarak gösterir.
 */

import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import {
    Flame,
    Activity,
    X,
    TrendingUp,
    Calendar
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface HeatNode {
    id: string;
    title: string;
    x: number;
    y: number;
    heatValue: number; // 0-1
    activityScore: number;
    lastModified?: Date;
    viewCount?: number;
}

interface HeatMapOverlayProps {
    nodes: HeatNode[];
    enabled: boolean;
    onToggle: () => void;
    language?: 'tr' | 'en' | 'de';
}

const translations = {
    title: { tr: 'Isı Haritası', en: 'Heat Map', de: 'Heatmap' },
    enabled: { tr: 'Aktif', en: 'Enabled', de: 'Aktiviert' },
    disabled: { tr: 'Pasif', en: 'Disabled', de: 'Deaktiviert' },
    mostActive: { tr: 'En Aktif', en: 'Most Active', de: 'Aktivste' },
    leastActive: { tr: 'En Az Aktif', en: 'Least Active', de: 'Am wenigsten aktiv' },
    legend: { tr: 'Aktivite Yoğunluğu', en: 'Activity Density', de: 'Aktivitätsdichte' },
};

// Generate heat color based on value (0-1)
const getHeatColor = (value: number): string => {
    // Cold (blue) to Hot (red) gradient
    if (value < 0.2) return 'rgba(59, 130, 246, 0.3)'; // Blue
    if (value < 0.4) return 'rgba(34, 197, 94, 0.4)'; // Green
    if (value < 0.6) return 'rgba(250, 204, 21, 0.5)'; // Yellow
    if (value < 0.8) return 'rgba(249, 115, 22, 0.6)'; // Orange
    return 'rgba(239, 68, 68, 0.7)'; // Red
};

const getGlowColor = (value: number): string => {
    if (value < 0.2) return 'drop-shadow(0 0 8px rgba(59, 130, 246, 0.5))';
    if (value < 0.4) return 'drop-shadow(0 0 10px rgba(34, 197, 94, 0.5))';
    if (value < 0.6) return 'drop-shadow(0 0 15px rgba(250, 204, 21, 0.6))';
    if (value < 0.8) return 'drop-shadow(0 0 20px rgba(249, 115, 22, 0.7))';
    return 'drop-shadow(0 0 25px rgba(239, 68, 68, 0.8))';
};

// SVG Overlay Component for rendering on canvas
export function HeatMapOverlaySVG({
    nodes,
    zoom = 1,
    pan = { x: 0, y: 0 }
}: {
    nodes: HeatNode[];
    zoom?: number;
    pan?: { x: number; y: number };
}) {
    return (
        <g className="heat-map-overlay" style={{ opacity: 0.6 }}>
            {nodes.map(node => (
                <circle
                    key={`heat-${node.id}`}
                    cx={node.x * zoom + pan.x}
                    cy={node.y * zoom + pan.y}
                    r={30 + (node.heatValue * 30)}
                    fill={getHeatColor(node.heatValue)}
                    style={{
                        filter: getGlowColor(node.heatValue),
                        mixBlendMode: 'screen'
                    }}
                />
            ))}
        </g>
    );
}

// Control Panel Component
export function HeatMapOverlay({
    nodes,
    enabled,
    onToggle,
    language = 'tr'
}: HeatMapOverlayProps) {
    const t = translations;

    const stats = useMemo(() => {
        if (nodes.length === 0) return { hottest: null, coldest: null, avg: 0 };

        const sorted = [...nodes].sort((a, b) => b.heatValue - a.heatValue);
        const avg = nodes.reduce((sum, n) => sum + n.heatValue, 0) / nodes.length;

        return {
            hottest: sorted[0],
            coldest: sorted[sorted.length - 1],
            avg
        };
    }, [nodes]);

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex items-center gap-3 px-4 py-2 bg-card/90 backdrop-blur-sm rounded-xl border border-border shadow-lg"
        >
            {/* Toggle */}
            <button
                onClick={onToggle}
                className={cn(
                    "flex items-center gap-2 px-3 py-1.5 rounded-lg transition-all",
                    enabled
                        ? "bg-gradient-to-r from-orange-500 to-red-500 text-white"
                        : "bg-muted text-muted-foreground hover:bg-muted/80"
                )}
            >
                <Flame className={cn("w-4 h-4", enabled && "animate-pulse")} />
                <span className="text-sm font-medium">
                    {t.title[language]}
                </span>
            </button>

            {/* Legend */}
            {enabled && (
                <motion.div
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="flex items-center gap-2"
                >
                    <span className="text-xs text-muted-foreground">{t.legend[language]}:</span>
                    <div className="flex items-center gap-1">
                        <div className="w-4 h-4 rounded-full bg-blue-500/50" title={t.leastActive[language]} />
                        <div className="w-4 h-4 rounded-full bg-green-500/50" />
                        <div className="w-4 h-4 rounded-full bg-yellow-500/50" />
                        <div className="w-4 h-4 rounded-full bg-orange-500/50" />
                        <div className="w-4 h-4 rounded-full bg-red-500/50" title={t.mostActive[language]} />
                    </div>
                </motion.div>
            )}

            {/* Stats */}
            {enabled && stats.hottest && (
                <motion.div
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="flex items-center gap-2 text-xs text-muted-foreground"
                >
                    <div className="flex items-center gap-1">
                        <TrendingUp className="w-3 h-3 text-red-500" />
                        <span className="truncate max-w-20">{stats.hottest.title}</span>
                    </div>
                </motion.div>
            )}
        </motion.div>
    );
}

export default HeatMapOverlay;
