'use client';

/**
 * DiffViewer - Versiyon Karşılaştırma Bileşeni
 * 
 * İki metin arasındaki farkları satır satır gösterir.
 * Eklenen, silinen ve değişen satırları renklendirir.
 */

import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import {
    Plus,
    Minus,
    GitCompare,
    Copy,
    ArrowLeftRight,
    X
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface DiffLine {
    type: 'added' | 'removed' | 'unchanged' | 'modified';
    lineNumber: { old?: number; new?: number };
    content: string;
}

interface DiffViewerProps {
    oldContent: string;
    newContent: string;
    oldLabel?: string;
    newLabel?: string;
    onClose?: () => void;
    language?: 'tr' | 'en' | 'de';
}

const translations = {
    title: { tr: 'Değişiklikleri Karşılaştır', en: 'Compare Changes', de: 'Änderungen vergleichen' },
    old: { tr: 'Önceki', en: 'Previous', de: 'Vorherige' },
    new: { tr: 'Yeni', en: 'New', de: 'Neue' },
    linesAdded: { tr: 'satır eklendi', en: 'lines added', de: 'Zeilen hinzugefügt' },
    linesRemoved: { tr: 'satır silindi', en: 'lines removed', de: 'Zeilen entfernt' },
    noChanges: { tr: 'Değişiklik yok', en: 'No changes', de: 'Keine Änderungen' },
    copyOld: { tr: 'Öncekini Kopyala', en: 'Copy Previous', de: 'Vorherige kopieren' },
    copyNew: { tr: 'Yeniyi Kopyala', en: 'Copy New', de: 'Neue kopieren' },
};

// Simple diff algorithm
function computeDiff(oldText: string, newText: string): DiffLine[] {
    const oldLines = oldText.split('\n');
    const newLines = newText.split('\n');
    const result: DiffLine[] = [];

    let oldIndex = 0;
    let newIndex = 0;
    let oldLineNum = 1;
    let newLineNum = 1;

    // Simple line-by-line comparison
    while (oldIndex < oldLines.length || newIndex < newLines.length) {
        const oldLine = oldLines[oldIndex];
        const newLine = newLines[newIndex];

        if (oldIndex >= oldLines.length) {
            // Only new lines left
            result.push({
                type: 'added',
                lineNumber: { new: newLineNum++ },
                content: newLine
            });
            newIndex++;
        } else if (newIndex >= newLines.length) {
            // Only old lines left
            result.push({
                type: 'removed',
                lineNumber: { old: oldLineNum++ },
                content: oldLine
            });
            oldIndex++;
        } else if (oldLine === newLine) {
            // Lines match
            result.push({
                type: 'unchanged',
                lineNumber: { old: oldLineNum++, new: newLineNum++ },
                content: oldLine
            });
            oldIndex++;
            newIndex++;
        } else {
            // Lines differ - check if it's a modification or addition/removal
            // Simple heuristic: look ahead for matching lines
            let foundInNew = false;
            let foundInOld = false;

            for (let i = newIndex + 1; i < Math.min(newIndex + 5, newLines.length); i++) {
                if (newLines[i] === oldLine) {
                    foundInNew = true;
                    break;
                }
            }

            for (let i = oldIndex + 1; i < Math.min(oldIndex + 5, oldLines.length); i++) {
                if (oldLines[i] === newLine) {
                    foundInOld = true;
                    break;
                }
            }

            if (foundInNew && !foundInOld) {
                // New line was added
                result.push({
                    type: 'added',
                    lineNumber: { new: newLineNum++ },
                    content: newLine
                });
                newIndex++;
            } else if (foundInOld && !foundInNew) {
                // Old line was removed
                result.push({
                    type: 'removed',
                    lineNumber: { old: oldLineNum++ },
                    content: oldLine
                });
                oldIndex++;
            } else {
                // Line was modified (show both)
                result.push({
                    type: 'removed',
                    lineNumber: { old: oldLineNum++ },
                    content: oldLine
                });
                result.push({
                    type: 'added',
                    lineNumber: { new: newLineNum++ },
                    content: newLine
                });
                oldIndex++;
                newIndex++;
            }
        }
    }

    return result;
}

export function DiffViewer({
    oldContent,
    newContent,
    oldLabel,
    newLabel,
    onClose,
    language = 'tr'
}: DiffViewerProps) {
    const t = translations;

    const diff = useMemo(() => computeDiff(oldContent, newContent), [oldContent, newContent]);

    const stats = useMemo(() => {
        const added = diff.filter(d => d.type === 'added').length;
        const removed = diff.filter(d => d.type === 'removed').length;
        return { added, removed };
    }, [diff]);

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text);
    };

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
        >
            <div className="w-full max-w-4xl max-h-[80vh] bg-card rounded-2xl border border-border shadow-2xl overflow-hidden flex flex-col">
                {/* Header */}
                <div className="p-4 border-b border-border bg-gradient-to-r from-blue-500/5 to-cyan-500/5 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-xl bg-blue-500/10">
                            <GitCompare className="w-5 h-5 text-blue-500" />
                        </div>
                        <div>
                            <h3 className="font-semibold">{t.title[language]}</h3>
                            <div className="flex items-center gap-4 text-sm">
                                <span className="flex items-center gap-1 text-green-500">
                                    <Plus className="w-3.5 h-3.5" />
                                    {stats.added} {t.linesAdded[language]}
                                </span>
                                <span className="flex items-center gap-1 text-red-500">
                                    <Minus className="w-3.5 h-3.5" />
                                    {stats.removed} {t.linesRemoved[language]}
                                </span>
                            </div>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => copyToClipboard(oldContent)}
                            className="px-3 py-1.5 rounded-lg bg-muted text-muted-foreground hover:bg-muted/80 text-sm flex items-center gap-1.5 transition-colors"
                            title={t.copyOld[language]}
                        >
                            <Copy className="w-3.5 h-3.5" />
                            {t.old[language]}
                        </button>
                        <button
                            onClick={() => copyToClipboard(newContent)}
                            className="px-3 py-1.5 rounded-lg bg-muted text-muted-foreground hover:bg-muted/80 text-sm flex items-center gap-1.5 transition-colors"
                            title={t.copyNew[language]}
                        >
                            <Copy className="w-3.5 h-3.5" />
                            {t.new[language]}
                        </button>
                        {onClose && (
                            <button
                                onClick={onClose}
                                className="p-2 rounded-lg hover:bg-muted transition-colors"
                            >
                                <X className="w-5 h-5 text-muted-foreground" />
                            </button>
                        )}
                    </div>
                </div>

                {/* Labels */}
                <div className="grid grid-cols-2 border-b border-border text-sm font-medium">
                    <div className="p-2 px-4 bg-red-500/5 text-red-600 dark:text-red-400 flex items-center gap-2">
                        <Minus className="w-3.5 h-3.5" />
                        {oldLabel || t.old[language]}
                    </div>
                    <div className="p-2 px-4 bg-green-500/5 text-green-600 dark:text-green-400 flex items-center gap-2 border-l border-border">
                        <Plus className="w-3.5 h-3.5" />
                        {newLabel || t.new[language]}
                    </div>
                </div>

                {/* Diff Content */}
                <div className="flex-1 overflow-y-auto font-mono text-sm">
                    {diff.length === 0 || (stats.added === 0 && stats.removed === 0) ? (
                        <div className="p-8 text-center text-muted-foreground">
                            <ArrowLeftRight className="w-8 h-8 mx-auto mb-2 opacity-50" />
                            {t.noChanges[language]}
                        </div>
                    ) : (
                        <div className="divide-y divide-border/50">
                            {diff.map((line, index) => (
                                <div
                                    key={index}
                                    className={cn(
                                        "flex",
                                        line.type === 'added' && "bg-green-500/10",
                                        line.type === 'removed' && "bg-red-500/10",
                                        line.type === 'unchanged' && "bg-transparent hover:bg-muted/30"
                                    )}
                                >
                                    {/* Line Numbers */}
                                    <div className="w-12 flex-shrink-0 px-2 py-1 text-right text-muted-foreground select-none border-r border-border/50">
                                        {line.lineNumber.old || ''}
                                    </div>
                                    <div className="w-12 flex-shrink-0 px-2 py-1 text-right text-muted-foreground select-none border-r border-border/50">
                                        {line.lineNumber.new || ''}
                                    </div>

                                    {/* Change Indicator */}
                                    <div className={cn(
                                        "w-6 flex-shrink-0 flex items-center justify-center py-1 border-r border-border/50",
                                        line.type === 'added' && "text-green-500",
                                        line.type === 'removed' && "text-red-500"
                                    )}>
                                        {line.type === 'added' && <Plus className="w-3.5 h-3.5" />}
                                        {line.type === 'removed' && <Minus className="w-3.5 h-3.5" />}
                                    </div>

                                    {/* Content */}
                                    <div className={cn(
                                        "flex-1 px-3 py-1 whitespace-pre-wrap break-all",
                                        line.type === 'added' && "text-green-700 dark:text-green-300",
                                        line.type === 'removed' && "text-red-700 dark:text-red-300",
                                        line.type === 'unchanged' && "text-foreground"
                                    )}>
                                        {line.content || ' '}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </motion.div>
    );
}

export default DiffViewer;
