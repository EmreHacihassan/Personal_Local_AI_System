'use client';

/**
 * GraphExportMenu - Mind Graf Dışa Aktarma Menüsü
 * 
 * PNG, SVG ve JSON export seçenekleri.
 */

import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Download,
    Image,
    FileCode,
    FileJson,
    CheckCircle,
    Loader2,
    X,
    Settings
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface GraphExportMenuProps {
    graphContainerId: string;
    graphData: {
        nodes: any[];
        edges: any[];
    };
    onClose: () => void;
    language?: 'tr' | 'en' | 'de';
}

type ExportFormat = 'png' | 'svg' | 'json';

const translations = {
    title: { tr: 'Graf Dışa Aktar', en: 'Export Graph', de: 'Graph exportieren' },
    png: { tr: 'PNG Görsel', en: 'PNG Image', de: 'PNG-Bild' },
    svg: { tr: 'SVG Vektörel', en: 'SVG Vector', de: 'SVG-Vektor' },
    json: { tr: 'JSON Veri', en: 'JSON Data', de: 'JSON-Daten' },
    quality: { tr: 'Kalite', en: 'Quality', de: 'Qualität' },
    background: { tr: 'Arka Plan', en: 'Background', de: 'Hintergrund' },
    transparent: { tr: 'Şeffaf', en: 'Transparent', de: 'Transparent' },
    white: { tr: 'Beyaz', en: 'White', de: 'Weiß' },
    dark: { tr: 'Koyu', en: 'Dark', de: 'Dunkel' },
    export: { tr: 'Dışa Aktar', en: 'Export', de: 'Exportieren' },
    exporting: { tr: 'Hazırlanıyor...', en: 'Preparing...', de: 'Wird vorbereitet...' },
    success: { tr: 'İndirme başladı!', en: 'Download started!', de: 'Download gestartet!' },
};

const FORMAT_OPTIONS = [
    {
        id: 'png' as ExportFormat,
        icon: Image,
        color: 'from-emerald-500 to-teal-500',
        desc: { tr: 'Yüksek çözünürlüklü görsel', en: 'High-resolution image', de: 'Hochauflösendes Bild' }
    },
    {
        id: 'svg' as ExportFormat,
        icon: FileCode,
        color: 'from-blue-500 to-cyan-500',
        desc: { tr: 'Ölçeklenebilir vektör', en: 'Scalable vector', de: 'Skalierbar Vektor' }
    },
    {
        id: 'json' as ExportFormat,
        icon: FileJson,
        color: 'from-amber-500 to-orange-500',
        desc: { tr: 'Graf verisi (nodes & edges)', en: 'Graph data (nodes & edges)', de: 'Graphdaten (Knoten & Kanten)' }
    },
];

export function GraphExportMenu({
    graphContainerId,
    graphData,
    onClose,
    language = 'tr'
}: GraphExportMenuProps) {
    const t = translations;

    const [format, setFormat] = useState<ExportFormat>('png');
    const [quality, setQuality] = useState(2); // 1x, 2x, 3x
    const [background, setBackground] = useState<'transparent' | 'white' | 'dark'>('white');
    const [isExporting, setIsExporting] = useState(false);
    const [exportSuccess, setExportSuccess] = useState(false);

    const exportToPng = useCallback(async () => {
        const container = document.getElementById(graphContainerId);
        if (!container) return;

        try {
            // Use html-to-image library if available, otherwise use canvas
            const canvas = document.createElement('canvas');
            const rect = container.getBoundingClientRect();

            canvas.width = rect.width * quality;
            canvas.height = rect.height * quality;

            const ctx = canvas.getContext('2d');
            if (!ctx) return;

            // Set background
            if (background !== 'transparent') {
                ctx.fillStyle = background === 'dark' ? '#111827' : '#ffffff';
                ctx.fillRect(0, 0, canvas.width, canvas.height);
            }

            // For now, create a placeholder image with graph info
            ctx.scale(quality, quality);
            ctx.font = '16px Inter, sans-serif';
            ctx.fillStyle = background === 'dark' ? '#ffffff' : '#111827';
            ctx.fillText(`Mind Graph Export`, 20, 30);
            ctx.font = '12px Inter, sans-serif';
            ctx.fillStyle = background === 'dark' ? '#9ca3af' : '#6b7280';
            ctx.fillText(`${graphData.nodes.length} nodes, ${graphData.edges.length} edges`, 20, 50);
            ctx.fillText(`Exported: ${new Date().toLocaleString()}`, 20, 70);

            // Download
            const link = document.createElement('a');
            link.download = `mind-graph-${Date.now()}.png`;
            link.href = canvas.toDataURL('image/png');
            link.click();
        } catch (error) {
            console.error('PNG export error:', error);
        }
    }, [graphContainerId, quality, background, graphData]);

    const exportToSvg = useCallback(async () => {
        const container = document.getElementById(graphContainerId);
        if (!container) return;

        try {
            // Get the SVG element from React Flow
            const svgElement = container.querySelector('svg');
            if (!svgElement) {
                // Create a simple SVG with graph info
                const svg = `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">
  <rect width="100%" height="100%" fill="${background === 'dark' ? '#111827' : background === 'white' ? '#ffffff' : 'none'}"/>
  <text x="20" y="30" font-family="Inter, sans-serif" font-size="16" fill="${background === 'dark' ? '#ffffff' : '#111827'}">Mind Graph Export</text>
  <text x="20" y="50" font-family="Inter, sans-serif" font-size="12" fill="${background === 'dark' ? '#9ca3af' : '#6b7280'}">${graphData.nodes.length} nodes, ${graphData.edges.length} edges</text>
  <text x="20" y="70" font-family="Inter, sans-serif" font-size="12" fill="${background === 'dark' ? '#9ca3af' : '#6b7280'}">Exported: ${new Date().toLocaleString()}</text>
</svg>`;

                const blob = new Blob([svg], { type: 'image/svg+xml' });
                const link = document.createElement('a');
                link.download = `mind-graph-${Date.now()}.svg`;
                link.href = URL.createObjectURL(blob);
                link.click();
                URL.revokeObjectURL(link.href);
                return;
            }

            const svgData = new XMLSerializer().serializeToString(svgElement);
            const blob = new Blob([svgData], { type: 'image/svg+xml' });
            const link = document.createElement('a');
            link.download = `mind-graph-${Date.now()}.svg`;
            link.href = URL.createObjectURL(blob);
            link.click();
            URL.revokeObjectURL(link.href);
        } catch (error) {
            console.error('SVG export error:', error);
        }
    }, [graphContainerId, background, graphData]);

    const exportToJson = useCallback(() => {
        const exportData = {
            exportDate: new Date().toISOString(),
            metadata: {
                nodeCount: graphData.nodes.length,
                edgeCount: graphData.edges.length,
            },
            nodes: graphData.nodes,
            edges: graphData.edges,
        };

        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const link = document.createElement('a');
        link.download = `mind-graph-${Date.now()}.json`;
        link.href = URL.createObjectURL(blob);
        link.click();
        URL.revokeObjectURL(link.href);
    }, [graphData]);

    const handleExport = async () => {
        setIsExporting(true);

        try {
            switch (format) {
                case 'png':
                    await exportToPng();
                    break;
                case 'svg':
                    await exportToSvg();
                    break;
                case 'json':
                    exportToJson();
                    break;
            }

            setExportSuccess(true);
            setTimeout(() => onClose(), 1500);
        } catch (error) {
            console.error('Export error:', error);
        } finally {
            setIsExporting(false);
        }
    };

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="absolute right-4 top-16 z-50 w-72 bg-card rounded-xl shadow-2xl border border-border overflow-hidden"
        >
            {/* Header */}
            <div className="p-3 border-b border-border bg-gradient-to-r from-emerald-500/5 to-teal-500/5 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Download className="w-4 h-4 text-emerald-500" />
                    <h4 className="font-medium text-sm">{t.title[language]}</h4>
                </div>
                <button onClick={onClose} className="p-1 rounded hover:bg-muted transition-colors">
                    <X className="w-4 h-4 text-muted-foreground" />
                </button>
            </div>

            {/* Content */}
            <div className="p-3 space-y-4">
                {/* Format Selection */}
                <div className="grid grid-cols-3 gap-2">
                    {FORMAT_OPTIONS.map(f => (
                        <motion.button
                            key={f.id}
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            onClick={() => setFormat(f.id)}
                            className={cn(
                                "flex flex-col items-center gap-1.5 p-2.5 rounded-lg border transition-all",
                                format === f.id
                                    ? "border-primary-500 bg-primary-500/10"
                                    : "border-border hover:border-primary-500/50"
                            )}
                        >
                            <div className={cn(
                                "p-1.5 rounded-lg bg-gradient-to-br",
                                f.color
                            )}>
                                <f.icon className="w-3.5 h-3.5 text-white" />
                            </div>
                            <span className="text-xs font-medium uppercase">{f.id}</span>
                        </motion.button>
                    ))}
                </div>

                <p className="text-xs text-muted-foreground text-center">
                    {FORMAT_OPTIONS.find(f => f.id === format)?.desc[language]}
                </p>

                {/* PNG/SVG Options */}
                {format !== 'json' && (
                    <div className="space-y-3 pt-2 border-t border-border">
                        {/* Quality (PNG only) */}
                        {format === 'png' && (
                            <div>
                                <label className="text-xs font-medium mb-2 block">{t.quality[language]}</label>
                                <div className="flex gap-2">
                                    {[1, 2, 3].map(q => (
                                        <button
                                            key={q}
                                            onClick={() => setQuality(q)}
                                            className={cn(
                                                "flex-1 py-1.5 rounded-lg text-xs font-medium transition-colors",
                                                quality === q
                                                    ? "bg-primary-500 text-white"
                                                    : "bg-muted text-muted-foreground hover:bg-muted/80"
                                            )}
                                        >
                                            {q}x
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Background */}
                        <div>
                            <label className="text-xs font-medium mb-2 block">{t.background[language]}</label>
                            <div className="flex gap-2">
                                {(['transparent', 'white', 'dark'] as const).map(bg => (
                                    <button
                                        key={bg}
                                        onClick={() => setBackground(bg)}
                                        className={cn(
                                            "flex-1 py-1.5 rounded-lg text-xs font-medium transition-colors",
                                            background === bg
                                                ? "bg-primary-500 text-white"
                                                : "bg-muted text-muted-foreground hover:bg-muted/80"
                                        )}
                                    >
                                        {t[bg][language]}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Footer */}
            <div className="p-3 border-t border-border bg-muted/30">
                <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={handleExport}
                    disabled={isExporting || exportSuccess}
                    className={cn(
                        "w-full py-2.5 rounded-lg font-medium text-sm transition-all flex items-center justify-center gap-2",
                        exportSuccess
                            ? "bg-emerald-500 text-white"
                            : "bg-gradient-to-r from-primary-500 to-purple-500 text-white hover:opacity-90"
                    )}
                >
                    {isExporting ? (
                        <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            {t.exporting[language]}
                        </>
                    ) : exportSuccess ? (
                        <>
                            <CheckCircle className="w-4 h-4" />
                            {t.success[language]}
                        </>
                    ) : (
                        <>
                            <Download className="w-4 h-4" />
                            {t.export[language]}
                        </>
                    )}
                </motion.button>
            </div>
        </motion.div>
    );
}

export default GraphExportMenu;
