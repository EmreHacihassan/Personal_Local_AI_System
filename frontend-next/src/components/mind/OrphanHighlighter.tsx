'use client';

/**
 * OrphanHighlighter - Bağlantısız Notları Vurgulama
 * 
 * Mind Graf'ta hiç bağlantısı olmayan notları tespit eder ve vurgular.
 */

import React, { useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    AlertCircle,
    Link,
    Link2Off,
    Sparkles,
    X,
    ExternalLink
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface OrphanNode {
    id: string;
    title: string;
    color: string;
    createdAt?: Date;
}

interface GraphEdge {
    source: string;
    target: string;
}

interface OrphanHighlighterProps {
    nodes: OrphanNode[];
    edges: GraphEdge[];
    onSelectNode: (nodeId: string) => void;
    onSuggestConnections?: (nodeId: string) => void;
    onClose: () => void;
    language?: 'tr' | 'en' | 'de';
}

const translations = {
    title: { tr: 'Bağlantısız Notlar', en: 'Orphan Notes', de: 'Verwaiste Notizen' },
    description: { tr: 'Bu notların hiçbir bağlantısı yok', en: 'These notes have no connections', de: 'Diese Notizen haben keine Verbindungen' },
    empty: { tr: 'Tüm notlar bağlı! 🎉', en: 'All notes are connected! 🎉', de: 'Alle Notizen sind verbunden! 🎉' },
    suggestConnections: { tr: 'Bağlantı Öner', en: 'Suggest Connections', de: 'Verbindungen vorschlagen' },
    orphanCount: { tr: 'bağlantısız not', en: 'orphan notes', de: 'verwaiste Notizen' },
    goToNote: { tr: 'Nota Git', en: 'Go to Note', de: 'Zur Notiz' },
    tip: { tr: '[[link]] syntax ile bağlantı oluşturabilirsiniz', en: 'Use [[link]] syntax to create connections', de: 'Verwenden Sie [[link]], um Verbindungen zu erstellen' },
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

export function OrphanHighlighter({
    nodes,
    edges,
    onSelectNode,
    onSuggestConnections,
    onClose,
    language = 'tr'
}: OrphanHighlighterProps) {
    const t = translations;

    // Find orphan nodes (no incoming or outgoing edges)
    const orphanNodes = useMemo(() => {
        const connectedIds = new Set<string>();

        edges.forEach(edge => {
            connectedIds.add(edge.source);
            connectedIds.add(edge.target);
        });

        return nodes.filter(node => !connectedIds.has(node.id));
    }, [nodes, edges]);

    const getColorClass = (color: string) => colorClasses[color] || colorClasses.default;

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="absolute bottom-4 right-4 z-40 w-80 bg-card rounded-2xl border border-border shadow-2xl overflow-hidden"
        >
            {/* Header */}
            <div className="p-4 border-b border-border bg-gradient-to-r from-orange-500/10 to-red-500/10">
                <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-xl bg-orange-500/20">
                            <Link2Off className="w-5 h-5 text-orange-500" />
                        </div>
                        <div>
                            <h3 className="font-semibold">{t.title[language]}</h3>
                            <p className="text-xs text-muted-foreground">
                                {orphanNodes.length} {t.orphanCount[language]}
                            </p>
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
            <div className="max-h-64 overflow-y-auto">
                {orphanNodes.length === 0 ? (
                    <div className="p-6 text-center">
                        <div className="w-12 h-12 rounded-full bg-green-500/10 flex items-center justify-center mx-auto mb-3">
                            <Link className="w-6 h-6 text-green-500" />
                        </div>
                        <p className="font-medium text-green-600 dark:text-green-400">
                            {t.empty[language]}
                        </p>
                    </div>
                ) : (
                    <div className="p-2 space-y-1">
                        {orphanNodes.map((node, index) => {
                            const colorClass = getColorClass(node.color);
                            return (
                                <motion.div
                                    key={node.id}
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: index * 0.05 }}
                                    className={cn(
                                        "p-3 rounded-xl border group",
                                        colorClass.bg,
                                        colorClass.border
                                    )}
                                >
                                    <div className="flex items-center gap-3">
                                        <div className={cn(
                                            "w-2.5 h-2.5 rounded-full flex-shrink-0",
                                            colorClass.dot
                                        )} />
                                        <p className="flex-1 font-medium text-sm truncate">{node.title}</p>
                                    </div>
                                    <div className="flex items-center gap-2 mt-2 ml-5">
                                        <button
                                            onClick={() => onSelectNode(node.id)}
                                            className="px-2 py-1 rounded-lg bg-muted text-xs text-muted-foreground hover:bg-primary-500/10 hover:text-primary-500 transition-colors flex items-center gap-1"
                                        >
                                            <ExternalLink className="w-3 h-3" />
                                            {t.goToNote[language]}
                                        </button>
                                        {onSuggestConnections && (
                                            <button
                                                onClick={() => onSuggestConnections(node.id)}
                                                className="px-2 py-1 rounded-lg bg-muted text-xs text-muted-foreground hover:bg-amber-500/10 hover:text-amber-500 transition-colors flex items-center gap-1"
                                            >
                                                <Sparkles className="w-3 h-3" />
                                                {t.suggestConnections[language]}
                                            </button>
                                        )}
                                    </div>
                                </motion.div>
                            );
                        })}
                    </div>
                )}
            </div>

            {/* Tip */}
            {orphanNodes.length > 0 && (
                <div className="p-3 border-t border-border bg-muted/30 text-xs text-muted-foreground flex items-center gap-2">
                    <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
                    {t.tip[language]}
                </div>
            )}
        </motion.div>
    );
}

export default OrphanHighlighter;
