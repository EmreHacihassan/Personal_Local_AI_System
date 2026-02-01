import React from 'react';
import { motion } from 'framer-motion';
import { Plus, Minus, FileText, ArrowRight } from 'lucide-react';
import { cn } from '@/lib/utils';

interface DiffLine {
    type: 'added' | 'removed' | 'unchanged';
    content: string;
    lineNumber?: number;
}

interface VersionDiffViewerProps {
    oldVersion: {
        title: string;
        content: string;
        timestamp: string;
    };
    newVersion: {
        title: string;
        content: string;
        timestamp: string;
    };
    showSideBySide?: boolean;
    className?: string;
}

// Parse content into diff lines
function computeDiff(oldContent: string, newContent: string): DiffLine[] {
    const oldLines = oldContent.split('\n');
    const newLines = newContent.split('\n');
    const result: DiffLine[] = [];
    
    // Simple line-by-line diff (LCS-based would be better for production)
    let i = 0, j = 0;
    
    while (i < oldLines.length || j < newLines.length) {
        if (i >= oldLines.length) {
            // Remaining new lines are additions
            result.push({ type: 'added', content: newLines[j], lineNumber: j + 1 });
            j++;
        } else if (j >= newLines.length) {
            // Remaining old lines are removals
            result.push({ type: 'removed', content: oldLines[i], lineNumber: i + 1 });
            i++;
        } else if (oldLines[i] === newLines[j]) {
            // Lines match
            result.push({ type: 'unchanged', content: oldLines[i], lineNumber: i + 1 });
            i++;
            j++;
        } else {
            // Check if the old line exists later in new content
            const foundInNew = newLines.slice(j + 1).indexOf(oldLines[i]);
            const foundInOld = oldLines.slice(i + 1).indexOf(newLines[j]);
            
            if (foundInNew !== -1 && (foundInOld === -1 || foundInNew <= foundInOld)) {
                // New lines were added
                result.push({ type: 'added', content: newLines[j], lineNumber: j + 1 });
                j++;
            } else {
                // Old line was removed
                result.push({ type: 'removed', content: oldLines[i], lineNumber: i + 1 });
                i++;
            }
        }
    }
    
    return result;
}

export function VersionDiffViewer({
    oldVersion,
    newVersion,
    showSideBySide = true,
    className
}: VersionDiffViewerProps) {
    const diffLines = computeDiff(oldVersion.content, newVersion.content);
    const titleChanged = oldVersion.title !== newVersion.title;
    
    const stats = {
        added: diffLines.filter(l => l.type === 'added').length,
        removed: diffLines.filter(l => l.type === 'removed').length,
        unchanged: diffLines.filter(l => l.type === 'unchanged').length
    };

    // Split lines for side-by-side view
    const getOldLines = () => diffLines.filter(l => l.type !== 'added');
    const getNewLines = () => diffLines.filter(l => l.type !== 'removed');

    return (
        <div className={cn("flex flex-col h-full", className)}>
            {/* Header with stats */}
            <div className="p-4 border-b border-border bg-muted/30">
                <div className="flex items-center justify-between mb-3">
                    <h3 className="font-semibold flex items-center gap-2">
                        <FileText className="w-4 h-4 text-primary-500" />
                        Değişiklikler
                    </h3>
                    <div className="flex items-center gap-3 text-sm">
                        <span className="flex items-center gap-1 text-green-500">
                            <Plus className="w-3 h-3" />
                            {stats.added} eklenen
                        </span>
                        <span className="flex items-center gap-1 text-red-500">
                            <Minus className="w-3 h-3" />
                            {stats.removed} silinen
                        </span>
                    </div>
                </div>

                {/* Title change indicator */}
                {titleChanged && (
                    <div className="flex items-center gap-2 text-sm p-2 bg-amber-500/10 rounded-lg border border-amber-500/20 mb-2">
                        <span className="text-amber-600 dark:text-amber-400 font-medium">Başlık değişti:</span>
                        <span className="line-through text-muted-foreground">{oldVersion.title}</span>
                        <ArrowRight className="w-3 h-3 text-muted-foreground" />
                        <span className="font-medium">{newVersion.title}</span>
                    </div>
                )}

                {/* Version timestamps */}
                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    <span>Eski: {new Date(oldVersion.timestamp).toLocaleString('tr-TR')}</span>
                    <ArrowRight className="w-3 h-3" />
                    <span>Yeni: {new Date(newVersion.timestamp).toLocaleString('tr-TR')}</span>
                </div>
            </div>

            {/* Diff content */}
            <div className="flex-1 overflow-auto">
                {showSideBySide ? (
                    /* Side-by-side view */
                    <div className="grid grid-cols-2 divide-x divide-border min-h-full">
                        {/* Old version */}
                        <div className="flex flex-col">
                            <div className="p-2 bg-red-500/5 border-b border-border text-xs font-medium text-red-600 dark:text-red-400 sticky top-0">
                                Eski Versiyon
                            </div>
                            <div className="flex-1 font-mono text-sm">
                                {getOldLines().map((line, idx) => (
                                    <div
                                        key={idx}
                                        className={cn(
                                            "px-3 py-0.5 flex",
                                            line.type === 'removed' && "bg-red-500/10"
                                        )}
                                    >
                                        <span className="w-8 text-xs text-muted-foreground shrink-0">
                                            {line.lineNumber}
                                        </span>
                                        <span className={cn(
                                            "flex-1",
                                            line.type === 'removed' && "text-red-600 dark:text-red-400"
                                        )}>
                                            {line.type === 'removed' && <Minus className="w-3 h-3 inline mr-1" />}
                                            {line.content || ' '}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* New version */}
                        <div className="flex flex-col">
                            <div className="p-2 bg-green-500/5 border-b border-border text-xs font-medium text-green-600 dark:text-green-400 sticky top-0">
                                Yeni Versiyon
                            </div>
                            <div className="flex-1 font-mono text-sm">
                                {getNewLines().map((line, idx) => (
                                    <div
                                        key={idx}
                                        className={cn(
                                            "px-3 py-0.5 flex",
                                            line.type === 'added' && "bg-green-500/10"
                                        )}
                                    >
                                        <span className="w-8 text-xs text-muted-foreground shrink-0">
                                            {line.lineNumber}
                                        </span>
                                        <span className={cn(
                                            "flex-1",
                                            line.type === 'added' && "text-green-600 dark:text-green-400"
                                        )}>
                                            {line.type === 'added' && <Plus className="w-3 h-3 inline mr-1" />}
                                            {line.content || ' '}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                ) : (
                    /* Unified view */
                    <div className="font-mono text-sm">
                        {diffLines.map((line, idx) => (
                            <motion.div
                                key={idx}
                                initial={{ opacity: 0, x: line.type === 'added' ? 10 : line.type === 'removed' ? -10 : 0 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: idx * 0.01 }}
                                className={cn(
                                    "px-3 py-0.5 flex",
                                    line.type === 'added' && "bg-green-500/10",
                                    line.type === 'removed' && "bg-red-500/10"
                                )}
                            >
                                <span className="w-6 text-center shrink-0">
                                    {line.type === 'added' && <Plus className="w-3 h-3 inline text-green-500" />}
                                    {line.type === 'removed' && <Minus className="w-3 h-3 inline text-red-500" />}
                                </span>
                                <span className="w-8 text-xs text-muted-foreground shrink-0">
                                    {line.lineNumber}
                                </span>
                                <span className={cn(
                                    "flex-1",
                                    line.type === 'added' && "text-green-600 dark:text-green-400",
                                    line.type === 'removed' && "text-red-600 dark:text-red-400 line-through"
                                )}>
                                    {line.content || ' '}
                                </span>
                            </motion.div>
                        ))}
                    </div>
                )}
            </div>

            {/* Summary footer */}
            <div className="p-3 border-t border-border bg-muted/30 text-xs text-muted-foreground text-center">
                {stats.unchanged} satır değişmedi • {stats.added + stats.removed} toplam değişiklik
            </div>
        </div>
    );
}
