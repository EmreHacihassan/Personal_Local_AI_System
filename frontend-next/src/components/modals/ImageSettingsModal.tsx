import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Check, AlignLeft, AlignCenter, AlignRight, Maximize2, Minimize2, Circle, Square, Image as ImageIcon, BoxSelect } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ImageSettingsModalProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: (settings: ImageSettings) => void;
    imageUrl: string;
    imageName: string;
}

export interface ImageSettings {
    size: 'small' | 'medium' | 'large' | 'full';
    align: 'left' | 'center' | 'right';
    shape: 'default' | 'rounded' | 'circle' | 'bordered';
    caption?: string;
}

export function ImageSettingsModal({ isOpen, onClose, onConfirm, imageUrl, imageName }: ImageSettingsModalProps) {
    const [settings, setSettings] = useState<ImageSettings>({
        size: 'medium',
        align: 'center',
        shape: 'rounded',
        caption: imageName.split('.')[0]
    });

    // Reset settings when modal opens
    useEffect(() => {
        if (isOpen) {
            setSettings({
                size: 'medium',
                align: 'center',
                shape: 'rounded',
                caption: imageName.split('.')[0]
            });
        }
    }, [isOpen, imageName]);

    const getSizeWidth = (size: string) => {
        switch (size) {
            case 'small': return 'max-w-[150px]';
            case 'medium': return 'max-w-[300px]';
            case 'large': return 'max-w-[500px]';
            case 'full': return 'max-w-full';
            default: return 'max-w-[300px]';
        }
    };

    const getShapeClass = (shape: string) => {
        switch (shape) {
            case 'rounded': return 'rounded-xl';
            case 'circle': return 'rounded-full aspect-square object-cover';
            case 'bordered': return 'rounded-lg border-4 border-white dark:border-gray-700 shadow-md';
            default: return 'rounded-none';
        }
    };

    return (
        <AnimatePresence>
            {isOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.9, y: 20 }}
                        className="w-full max-w-2xl bg-card border border-border rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
                    >
                        {/* Header */}
                        <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-muted/30">
                            <div className="flex items-center gap-2">
                                <div className="p-2 bg-primary-500/10 rounded-lg">
                                    <ImageIcon className="w-5 h-5 text-primary-500" />
                                </div>
                                <div>
                                    <h3 className="font-semibold text-lg">Görsel Ayarları</h3>
                                    <p className="text-xs text-muted-foreground">Premium düzenleyici</p>
                                </div>
                            </div>
                            <button onClick={onClose} className="p-2 hover:bg-accent rounded-full transition-colors">
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        <div className="flex flex-1 overflow-hidden">
                            {/* Preview Area (Left) */}
                            <div className="flex-1 bg-muted/50 p-6 flex flex-col items-center justify-center overflow-y-auto min-h-[300px]">
                                <p className="text-xs text-muted-foreground uppercase tracking-wider font-semibold mb-4">Canlı Önizleme</p>
                                <div className={cn(
                                    "relative transition-all duration-300 ease-in-out group",
                                    getSizeWidth(settings.size),
                                    // Alignment for the preview container itself in flex column
                                    settings.align === 'left' ? 'self-start' : settings.align === 'right' ? 'self-end' : 'self-center'
                                )}>
                                    <img
                                        src={imageUrl}
                                        alt="Preview"
                                        className={cn(
                                            "w-full h-auto transition-all duration-300 shadow-lg",
                                            getShapeClass(settings.shape)
                                        )}
                                    />
                                    {settings.caption && (
                                        <p className={cn(
                                            "mt-2 text-sm text-center text-muted-foreground font-medium",
                                            settings.align === 'left' ? 'text-left' : settings.align === 'right' ? 'text-right' : 'text-center'
                                        )}>
                                            {settings.caption}
                                        </p>
                                    )}

                                    {/* Size Indicator Badge */}
                                    <div className="absolute top-2 right-2 px-2 py-1 bg-black/50 backdrop-blur text-white text-[10px] rounded-full opacity-0 group-hover:opacity-100 transition-opacity">
                                        {settings.size.toUpperCase()}
                                    </div>
                                </div>
                            </div>

                            {/* Controls Area (Right) */}
                            <div className="w-80 bg-card border-l border-border p-6 flex flex-col gap-6 overflow-y-auto">

                                {/* Size Controls */}
                                <div>
                                    <label className="text-sm font-medium mb-3 block flex items-center gap-2">
                                        <Maximize2 className="w-4 h-4 text-primary-500" />
                                        Boyut
                                    </label>
                                    <div className="grid grid-cols-4 gap-2">
                                        {(['small', 'medium', 'large', 'full'] as const).map((size) => (
                                            <button
                                                key={size}
                                                onClick={() => setSettings({ ...settings, size })}
                                                className={cn(
                                                    "px-2 py-2 rounded-lg text-xs font-medium transition-all border",
                                                    settings.size === size
                                                        ? "bg-primary-500 text-white border-primary-500 shadow-sm"
                                                        : "bg-background hover:bg-accent border-border text-muted-foreground"
                                                )}
                                            >
                                                {size === 'small' ? 'S' : size === 'medium' ? 'M' : size === 'large' ? 'L' : 'XL'}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                {/* Alignment Controls */}
                                <div>
                                    <label className="text-sm font-medium mb-3 block flex items-center gap-2">
                                        <AlignCenter className="w-4 h-4 text-primary-500" />
                                        Hizalama
                                    </label>
                                    <div className="flex bg-muted p-1 rounded-lg">
                                        {[
                                            { val: 'left', icon: AlignLeft },
                                            { val: 'center', icon: AlignCenter },
                                            { val: 'right', icon: AlignRight }
                                        ].map(({ val, icon: Icon }) => (
                                            <button
                                                key={val}
                                                onClick={() => setSettings({ ...settings, align: val as any })}
                                                className={cn(
                                                    "flex-1 p-2 rounded-md flex items-center justify-center transition-all",
                                                    settings.align === val
                                                        ? "bg-background text-primary-500 shadow-sm"
                                                        : "text-muted-foreground hover:text-foreground"
                                                )}
                                            >
                                                <Icon className="w-4 h-4" />
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                {/* Shape Controls */}
                                <div>
                                    <label className="text-sm font-medium mb-3 block flex items-center gap-2">
                                        <BoxSelect className="w-4 h-4 text-primary-500" />
                                        Şekil
                                    </label>
                                    <div className="grid grid-cols-2 gap-2">
                                        {[
                                            { val: 'default', label: 'Normal', icon: Square },
                                            { val: 'rounded', label: 'Oval', icon: Square }, // Icon approximation
                                            { val: 'circle', label: 'Daire', icon: Circle },
                                            { val: 'bordered', label: 'Çerçeve', icon: BoxSelect }
                                        ].map((item) => (
                                            <button
                                                key={item.val}
                                                onClick={() => setSettings({ ...settings, shape: item.val as any })}
                                                className={cn(
                                                    "flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium transition-all border text-left",
                                                    settings.shape === item.val
                                                        ? "bg-primary-50/50 dark:bg-primary-900/10 border-primary-500 text-primary-600 dark:text-primary-400"
                                                        : "bg-background hover:bg-accent border-border text-muted-foreground"
                                                )}
                                            >
                                                <item.icon className={cn("w-3.5 h-3.5", item.val === 'rounded' && "rounded-md")} />
                                                {item.label}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                {/* Caption Input */}
                                <div>
                                    <label className="text-sm font-medium mb-3 block">Altyazı</label>
                                    <input
                                        type="text"
                                        value={settings.caption}
                                        onChange={(e) => setSettings({ ...settings, caption: e.target.value })}
                                        className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/50"
                                        placeholder="Görsel açıklaması..."
                                    />
                                </div>

                            </div>
                        </div>

                        {/* Footer */}
                        <div className="px-6 py-4 border-t border-border bg-muted/30 flex justify-end gap-3">
                            <button
                                onClick={onClose}
                                className="px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-accent rounded-xl transition-colors"
                            >
                                İptal
                            </button>
                            <button
                                onClick={() => onConfirm(settings)}
                                className="flex items-center gap-2 px-6 py-2 bg-gradient-to-r from-primary-600 to-indigo-600 hover:from-primary-700 hover:to-indigo-700 text-white rounded-xl shadow-lg shadow-primary-500/20 transition-all transform hover:scale-105"
                            >
                                <Check className="w-4 h-4" />
                                Görseli Ekle
                            </button>
                        </div>
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    );
}
