'use client';

/**
 * BulkActionToolbar - Toplu İşlem Araç Çubuğu
 * 
 * Çoklu seçimde görünen floating toolbar.
 */

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Trash2,
    FolderInput,
    Archive,
    Palette,
    Tag,
    Pin,
    X,
    CheckSquare,
    Download
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface BulkActionToolbarProps {
    selectedCount: number;
    onDelete: () => void;
    onMove: () => void;
    onArchive: () => void;
    onChangeColor: (color: string) => void;
    onAddTag: (tag: string) => void;
    onTogglePin: () => void;
    onExport: () => void;
    onClear: () => void;
    language?: 'tr' | 'en' | 'de';
}

const COLORS = [
    { id: 'yellow', class: 'bg-yellow-400' },
    { id: 'green', class: 'bg-green-400' },
    { id: 'blue', class: 'bg-blue-400' },
    { id: 'purple', class: 'bg-purple-400' },
    { id: 'pink', class: 'bg-pink-400' },
    { id: 'orange', class: 'bg-orange-400' },
];

const translations = {
    selected: { tr: 'seçili', en: 'selected', de: 'ausgewählt' },
    delete: { tr: 'Sil', en: 'Delete', de: 'Löschen' },
    move: { tr: 'Taşı', en: 'Move', de: 'Verschieben' },
    archive: { tr: 'Arşivle', en: 'Archive', de: 'Archivieren' },
    pin: { tr: 'Sabitle', en: 'Pin', de: 'Anheften' },
    export: { tr: 'Dışa Aktar', en: 'Export', de: 'Exportieren' },
};

export function BulkActionToolbar({
    selectedCount,
    onDelete,
    onMove,
    onArchive,
    onChangeColor,
    onAddTag,
    onTogglePin,
    onExport,
    onClear,
    language = 'tr'
}: BulkActionToolbarProps) {
    const t = translations;
    const [showColorPicker, setShowColorPicker] = React.useState(false);

    if (selectedCount === 0) return null;

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0, y: 20, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 20, scale: 0.95 }}
                className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50"
            >
                <div className="flex items-center gap-2 px-4 py-3 rounded-2xl bg-card/95 backdrop-blur-xl border border-border shadow-2xl">
                    {/* Selection Count */}
                    <div className="flex items-center gap-2 pr-3 border-r border-border">
                        <div className="p-1.5 rounded-lg bg-primary-500/20">
                            <CheckSquare className="w-4 h-4 text-primary-500" />
                        </div>
                        <span className="text-sm font-medium">
                            {selectedCount} {t.selected[language]}
                        </span>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-1">
                        {/* Pin */}
                        <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={onTogglePin}
                            className="p-2.5 rounded-xl hover:bg-amber-500/10 text-muted-foreground hover:text-amber-500 transition-colors"
                            title={t.pin[language]}
                        >
                            <Pin className="w-4 h-4" />
                        </motion.button>

                        {/* Color Picker */}
                        <div className="relative">
                            <motion.button
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                onClick={() => setShowColorPicker(!showColorPicker)}
                                className="p-2.5 rounded-xl hover:bg-purple-500/10 text-muted-foreground hover:text-purple-500 transition-colors"
                            >
                                <Palette className="w-4 h-4" />
                            </motion.button>

                            <AnimatePresence>
                                {showColorPicker && (
                                    <motion.div
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, y: 10 }}
                                        className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 p-2 rounded-xl bg-card border border-border shadow-lg flex gap-1.5"
                                    >
                                        {COLORS.map(color => (
                                            <button
                                                key={color.id}
                                                onClick={() => {
                                                    onChangeColor(color.id);
                                                    setShowColorPicker(false);
                                                }}
                                                className={cn(
                                                    "w-6 h-6 rounded-full transition-transform hover:scale-110",
                                                    color.class
                                                )}
                                            />
                                        ))}
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>

                        {/* Move */}
                        <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={onMove}
                            className="p-2.5 rounded-xl hover:bg-blue-500/10 text-muted-foreground hover:text-blue-500 transition-colors"
                            title={t.move[language]}
                        >
                            <FolderInput className="w-4 h-4" />
                        </motion.button>

                        {/* Archive */}
                        <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={onArchive}
                            className="p-2.5 rounded-xl hover:bg-slate-500/10 text-muted-foreground hover:text-slate-500 transition-colors"
                            title={t.archive[language]}
                        >
                            <Archive className="w-4 h-4" />
                        </motion.button>

                        {/* Export */}
                        <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={onExport}
                            className="p-2.5 rounded-xl hover:bg-emerald-500/10 text-muted-foreground hover:text-emerald-500 transition-colors"
                            title={t.export[language]}
                        >
                            <Download className="w-4 h-4" />
                        </motion.button>

                        {/* Delete */}
                        <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={onDelete}
                            className="p-2.5 rounded-xl hover:bg-red-500/10 text-muted-foreground hover:text-red-500 transition-colors"
                            title={t.delete[language]}
                        >
                            <Trash2 className="w-4 h-4" />
                        </motion.button>
                    </div>

                    {/* Clear Selection */}
                    <button
                        onClick={onClear}
                        className="ml-2 p-2 rounded-lg hover:bg-muted transition-colors"
                    >
                        <X className="w-4 h-4 text-muted-foreground" />
                    </button>
                </div>
            </motion.div>
        </AnimatePresence>
    );
}

export default BulkActionToolbar;
