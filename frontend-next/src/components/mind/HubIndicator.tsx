'use client';

/**
 * HubIndicator - Hub Notları Göstergesi
 * 
 * En çok bağlantıya sahip "hub" notları tespit eder ve gösterir.
 */

import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import {
    Network,
    Crown,
    ArrowUpRight,
    X,
    TrendingUp,
    Star
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface HubNode {
    id: string;
    title: string;
    color: string;
    connectionCount: number;
    incomingCount: number;
    outgoingCount: number;
}

interface GraphEdge {
    source: string;
    target: string;
}

interface GraphNode {
    id: string;
    title: string;
    color: string;
}

interface HubIndicatorProps {
    nodes: GraphNode[];
    edges: GraphEdge[];
    onSelectNode: (nodeId: string) => void;
    onClose: () => void;
    topCount?: number;
    language?: 'tr' | 'en' | 'de';
}

const translations = {
    title: { tr: 'Hub Notlar', en: 'Hub Notes', de: 'Hub-Notizen' },
    description: { tr: 'En çok bağlantıya sahip notlar', en: 'Notes with most connections', de: 'Notizen mit den meisten Verbindungen' },
    connections: { tr: 'bağlantı', en: 'connections', de: 'Verbindungen' },
    incoming: { tr: 'gelen', en: 'incoming', de: 'eingehend' },
    outgoing: { tr: 'giden', en: 'outgoing', de: 'ausgehend' },
    noHubs: { tr: 'Henüz yeterli bağlantı yok', en: 'Not enough connections yet', de: 'Noch nicht genug Verbindungen' },
    rank: { tr: 'Sıra', en: 'Rank', de: 'Rang' },
};

const colorClasses: Record<string, { bg: string; border: string; dot: string }> = {
    yellow: { bg: 'bg-yellow-500/10', border: 'border-yellow-500/30', dot: 'bg-yellow-500' },
    green: { bg: 'bg-green-500/10', border: 'border-green-500/30', dot: 'bg-green-500' },
    blue: { bg: 'bg-blue-500/10', border: 'border-blue-500/30', dot: 'bg-blue-500' },
    pink: { bg: 'bg-pink-500/10', border: 'border-pink-500/30', dot: 'bg-pink-500' },
    purple: { bg: 'bg-purple-500/10', border: 'border-purple-500/30', dot: 'bg-purple-500' },
    orange: { bg: 'bg-orange-500/10', border: 'border-orange-500/30', dot: 'bg-orange-500' },
    red: { bg: 'bg-red-500/10', border: 'border-red-500/30', dot: 'bg-red-500' },
    gray: { bg: 'bg-gray-500/10', border: 'border-gray-500/30', dot: 'bg-gray-500' },
    default: { bg: 'bg-slate-500/10', border: 'border-slate-500/30', dot: 'bg-slate-500' },
};

const rankColors = ['text-amber-500', 'text-slate-400', 'text-amber-700'];
const rankIcons = [Crown, Star, TrendingUp];

export function HubIndicator({
    nodes,
    edges,
    onSelectNode,
    onClose,
    topCount = 5,
    language = 'tr'
}: HubIndicatorProps) {
    const t = translations;

    // Calculate hub nodes
    const hubNodes = useMemo(() => {
        const connectionMap = new Map<string, { incoming: number; outgoing: number }>();

        // Initialize all nodes
        nodes.forEach(node => {
            connectionMap.set(node.id, { incoming: 0, outgoing: 0 });
        });

        // Count connections
        edges.forEach(edge => {
            const source = connectionMap.get(edge.source);
            const target = connectionMap.get(edge.target);

            if (source) source.outgoing++;
            if (target) target.incoming++;
        });

        // Map to HubNode and sort by total connections
        const hubs: HubNode[] = nodes.map(node => {
            const counts = connectionMap.get(node.id) || { incoming: 0, outgoing: 0 };
            return {
                id: node.id,
                title: node.title,
                color: node.color,
                connectionCount: counts.incoming + counts.outgoing,
                incomingCount: counts.incoming,
                outgoingCount: counts.outgoing
            };
        });

        return hubs
            .filter(h => h.connectionCount > 0)
            .sort((a, b) => b.connectionCount - a.connectionCount)
            .slice(0, topCount);
    }, [nodes, edges, topCount]);

    const getColorClass = (color: string) => colorClasses[color] || colorClasses.default;

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="absolute bottom-4 left-4 z-40 w-80 bg-card rounded-2xl border border-border shadow-2xl overflow-hidden"
        >
            {/* Header */}
            <div className="p-4 border-b border-border bg-gradient-to-r from-purple-500/10 to-pink-500/10">
                <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-xl bg-purple-500/20">
                            <Network className="w-5 h-5 text-purple-500" />
                        </div>
                        <div>
                            <h3 className="font-semibold">{t.title[language]}</h3>
                            <p className="text-xs text-muted-foreground">{t.description[language]}</p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-1.5 rounded-lg hover:bg-muted transition-colors"
                    >
                        <X className="w-4 h-4 text-muted-foreground" />
                    </button>
                </div>
            </div>

            {/* Content */}
            <div className="max-h-72 overflow-y-auto">
                {hubNodes.length === 0 ? (
                    <div className="p-6 text-center text-muted-foreground">
                        <Network className="w-10 h-10 mx-auto mb-2 opacity-30" />
                        <p className="text-sm">{t.noHubs[language]}</p>
                    </div>
                ) : (
                    <div className="p-2 space-y-1">
                        {hubNodes.map((node, index) => {
                            const colorClass = getColorClass(node.color);
                            const RankIcon = rankIcons[index] || TrendingUp;
                            const rankColor = rankColors[index] || 'text-muted-foreground';

                            return (
                                <motion.button
                                    key={node.id}
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: index * 0.05 }}
                                    onClick={() => onSelectNode(node.id)}
                                    className={cn(
                                        "w-full p-3 rounded-xl border text-left transition-all group hover:shadow-md",
                                        colorClass.bg,
                                        colorClass.border
                                    )}
                                >
                                    <div className="flex items-start gap-3">
                                        {/* Rank */}
                                        <div className={cn("flex items-center justify-center w-6 h-6", rankColor)}>
                                            <RankIcon className="w-5 h-5" />
                                        </div>

                                        {/* Info */}
                                        <div className="flex-1 min-w-0">
                                            <p className="font-medium text-sm truncate">{node.title}</p>
                                            <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                                                <span className="font-semibold text-foreground">
                                                    {node.connectionCount} {t.connections[language]}
                                                </span>
                                                <span>↓{node.incomingCount} {t.incoming[language]}</span>
                                                <span>↑{node.outgoingCount} {t.outgoing[language]}</span>
                                            </div>
                                        </div>

                                        {/* Arrow */}
                                        <ArrowUpRight className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                                    </div>

                                    {/* Connection Bar */}
                                    <div className="mt-2 ml-9 h-1.5 bg-muted rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full"
                                            style={{
                                                width: `${Math.min((node.connectionCount / (hubNodes[0]?.connectionCount || 1)) * 100, 100)}%`
                                            }}
                                        />
                                    </div>
                                </motion.button>
                            );
                        })}
                    </div>
                )}
            </div>
        </motion.div>
    );
}

export default HubIndicator;
