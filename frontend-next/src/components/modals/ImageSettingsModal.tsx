import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Check, AlignLeft, AlignCenter, AlignRight, Maximize2, Minimize2, Circle, Square, Image as ImageIcon, BoxSelect, Lock, Unlock, RotateCcw, ScanText, Loader2, Copy, FileText } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ImageSettingsModalProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: (settings: ImageSettings) => void;
    imageUrl: string;
    imageName: string;
    initialSettings?: Partial<ImageSettings>;
    isEditMode?: boolean;
}

export interface ImageSettings {
    size: 'small' | 'medium' | 'large' | 'full' | 'custom';
    align: 'left' | 'center' | 'right';
    shape: 'default' | 'rounded' | 'circle' | 'bordered';
    caption?: string;
    // New custom sizing options
    customWidth?: number;
    customHeight?: number;
    scalePercent?: number;
    aspectRatioLocked?: boolean;
}

interface ImageDimensions {
    width: number;
    height: number;
    aspectRatio: number;
}

export function ImageSettingsModal({ isOpen, onClose, onConfirm, imageUrl, imageName, initialSettings, isEditMode }: ImageSettingsModalProps) {
    const [settings, setSettings] = useState<ImageSettings>({
        size: initialSettings?.size || 'medium',
        align: initialSettings?.align || 'center',
        shape: initialSettings?.shape || 'rounded',
        caption: initialSettings?.caption || imageName.split('.')[0],
        customWidth: initialSettings?.customWidth || 300,
        customHeight: initialSettings?.customHeight || 200,
        scalePercent: initialSettings?.scalePercent || 100,
        aspectRatioLocked: initialSettings?.aspectRatioLocked ?? true
    });

    // Original image dimensions
    const [originalDimensions, setOriginalDimensions] = useState<ImageDimensions>({ width: 300, height: 200, aspectRatio: 1.5 });
    
    // OCR state
    const [isExtracting, setIsExtracting] = useState(false);
    const [extractedText, setExtractedText] = useState<string>('');
    const [ocrError, setOcrError] = useState<string>('');
    
    const imageRef = useRef<HTMLImageElement>(null);

    // Load original image dimensions
    useEffect(() => {
        if (imageUrl) {
            const img = new Image();
            img.onload = () => {
                const dims = {
                    width: img.naturalWidth,
                    height: img.naturalHeight,
                    aspectRatio: img.naturalWidth / img.naturalHeight
                };
                setOriginalDimensions(dims);
                setSettings(prev => ({
                    ...prev,
                    customWidth: dims.width,
                    customHeight: dims.height,
                    scalePercent: 100
                }));
            };
            img.src = imageUrl;
        }
    }, [imageUrl]);

    // Reset settings when modal opens
    useEffect(() => {
        if (isOpen) {
            setSettings({
                size: initialSettings?.size || 'medium',
                align: initialSettings?.align || 'center',
                shape: initialSettings?.shape || 'rounded',
                caption: initialSettings?.caption || imageName.split('.')[0],
                customWidth: initialSettings?.customWidth || originalDimensions.width,
                customHeight: initialSettings?.customHeight || originalDimensions.height,
                scalePercent: initialSettings?.scalePercent || 100,
                aspectRatioLocked: initialSettings?.aspectRatioLocked ?? true
            });
            setExtractedText('');
            setOcrError('');
        }
    }, [isOpen, imageName, originalDimensions, initialSettings]);

    // Handle width change with aspect ratio lock
    const handleWidthChange = useCallback((newWidth: number) => {
        if (settings.aspectRatioLocked) {
            const newHeight = Math.round(newWidth / originalDimensions.aspectRatio);
            setSettings(prev => ({
                ...prev,
                customWidth: newWidth,
                customHeight: newHeight,
                size: 'custom',
                scalePercent: Math.round((newWidth / originalDimensions.width) * 100)
            }));
        } else {
            setSettings(prev => ({
                ...prev,
                customWidth: newWidth,
                size: 'custom'
            }));
        }
    }, [settings.aspectRatioLocked, originalDimensions]);

    // Handle height change with aspect ratio lock
    const handleHeightChange = useCallback((newHeight: number) => {
        if (settings.aspectRatioLocked) {
            const newWidth = Math.round(newHeight * originalDimensions.aspectRatio);
            setSettings(prev => ({
                ...prev,
                customWidth: newWidth,
                customHeight: newHeight,
                size: 'custom',
                scalePercent: Math.round((newHeight / originalDimensions.height) * 100)
            }));
        } else {
            setSettings(prev => ({
                ...prev,
                customHeight: newHeight,
                size: 'custom'
            }));
        }
    }, [settings.aspectRatioLocked, originalDimensions]);

    // Handle scale slider change
    const handleScaleChange = useCallback((percent: number) => {
        const newWidth = Math.round(originalDimensions.width * (percent / 100));
        const newHeight = Math.round(originalDimensions.height * (percent / 100));
        setSettings(prev => ({
            ...prev,
            customWidth: newWidth,
            customHeight: newHeight,
            scalePercent: percent,
            size: 'custom'
        }));
    }, [originalDimensions]);

    // Reset to original size
    const handleResetSize = useCallback(() => {
        setSettings(prev => ({
            ...prev,
            customWidth: originalDimensions.width,
            customHeight: originalDimensions.height,
            scalePercent: 100,
            size: 'medium'
        }));
    }, [originalDimensions]);

    // OCR text extraction
    const handleExtractText = async () => {
        setIsExtracting(true);
        setOcrError('');
        try {
            const response = await fetch('http://localhost:8001/api/notes/ocr', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image_path: imageUrl })
            });
            
            if (!response.ok) {
                throw new Error('OCR işlemi başarısız');
            }
            
            const data = await response.json();
            setExtractedText(data.text || 'Metin bulunamadı');
        } catch (error) {
            setOcrError('Metin çıkarma hatası. Lütfen tekrar deneyin.');
            console.error('OCR error:', error);
        } finally {
            setIsExtracting(false);
        }
    };

    // Copy extracted text
    const handleCopyText = () => {
        navigator.clipboard.writeText(extractedText);
    };

    // Insert extracted text as caption
    const handleInsertAsCaption = () => {
        setSettings(prev => ({ ...prev, caption: extractedText }));
    };

    const getSizeWidth = (size: string) => {
        switch (size) {
            case 'small': return 'max-w-[150px]';
            case 'medium': return 'max-w-[300px]';
            case 'large': return 'max-w-[500px]';
            case 'full': return 'max-w-full';
            case 'custom': return '';
            default: return 'max-w-[300px]';
        }
    };

    const getCustomStyle = () => {
        if (settings.size === 'custom' && settings.customWidth) {
            return {
                width: `${Math.min(settings.customWidth, 500)}px`,
                height: 'auto'
            };
        }
        return {};
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
                                    settings.size !== 'custom' && getSizeWidth(settings.size),
                                    // Alignment for the preview container itself in flex column
                                    settings.align === 'left' ? 'self-start' : settings.align === 'right' ? 'self-end' : 'self-center'
                                )}
                                style={getCustomStyle()}
                                >
                                    <img
                                        ref={imageRef}
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
                                        {settings.size === 'custom' 
                                            ? `${settings.customWidth}×${settings.customHeight}px (${settings.scalePercent}%)`
                                            : settings.size.toUpperCase()
                                        }
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
                                    <div className="grid grid-cols-5 gap-2">
                                        {(['small', 'medium', 'large', 'full', 'custom'] as const).map((size) => (
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
                                                {size === 'small' ? 'S' : size === 'medium' ? 'M' : size === 'large' ? 'L' : size === 'full' ? 'XL' : '✎'}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                {/* Custom Size Controls - Only visible when custom is selected */}
                                {settings.size === 'custom' && (
                                    <div className="space-y-4 p-4 bg-muted/50 rounded-xl border border-border">
                                        {/* Pixel Inputs */}
                                        <div className="flex gap-3 items-center">
                                            <div className="flex-1">
                                                <label className="text-xs text-muted-foreground mb-1 block">Genişlik (px)</label>
                                                <input
                                                    type="number"
                                                    value={settings.customWidth}
                                                    onChange={(e) => handleWidthChange(parseInt(e.target.value) || 0)}
                                                    className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/50"
                                                    min={10}
                                                    max={2000}
                                                />
                                            </div>
                                            <button
                                                onClick={() => setSettings(prev => ({ ...prev, aspectRatioLocked: !prev.aspectRatioLocked }))}
                                                className={cn(
                                                    "p-2 rounded-lg transition-colors mt-5",
                                                    settings.aspectRatioLocked 
                                                        ? "bg-primary-500/20 text-primary-500" 
                                                        : "bg-muted text-muted-foreground hover:text-foreground"
                                                )}
                                                title={settings.aspectRatioLocked ? "En-boy oranı kilitli" : "En-boy oranı serbest"}
                                            >
                                                {settings.aspectRatioLocked ? <Lock className="w-4 h-4" /> : <Unlock className="w-4 h-4" />}
                                            </button>
                                            <div className="flex-1">
                                                <label className="text-xs text-muted-foreground mb-1 block">Yükseklik (px)</label>
                                                <input
                                                    type="number"
                                                    value={settings.customHeight}
                                                    onChange={(e) => handleHeightChange(parseInt(e.target.value) || 0)}
                                                    className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/50"
                                                    min={10}
                                                    max={2000}
                                                    disabled={settings.aspectRatioLocked}
                                                />
                                            </div>
                                        </div>

                                        {/* Scale Slider */}
                                        <div>
                                            <div className="flex justify-between items-center mb-2">
                                                <label className="text-xs text-muted-foreground">Ölçek</label>
                                                <span className="text-xs font-medium text-primary-500">{settings.scalePercent}%</span>
                                            </div>
                                            <input
                                                type="range"
                                                min={10}
                                                max={200}
                                                value={settings.scalePercent}
                                                onChange={(e) => handleScaleChange(parseInt(e.target.value))}
                                                className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-primary-500"
                                            />
                                            <div className="flex justify-between text-[10px] text-muted-foreground mt-1">
                                                <span>10%</span>
                                                <span>100%</span>
                                                <span>200%</span>
                                            </div>
                                        </div>

                                        {/* Reset Button */}
                                        <button
                                            onClick={handleResetSize}
                                            className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-background hover:bg-accent border border-border rounded-lg text-sm text-muted-foreground hover:text-foreground transition-colors"
                                        >
                                            <RotateCcw className="w-4 h-4" />
                                            Orijinal Boyuta Sıfırla ({originalDimensions.width}×{originalDimensions.height}px)
                                        </button>
                                    </div>
                                )}

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

                                {/* OCR / Text Extraction */}
                                <div className="p-4 bg-gradient-to-br from-indigo-500/5 to-purple-500/5 rounded-xl border border-indigo-500/20">
                                    <label className="text-sm font-medium mb-3 block flex items-center gap-2">
                                        <ScanText className="w-4 h-4 text-indigo-500" />
                                        Metin Çıkarma (OCR)
                                        <span className="text-[10px] bg-indigo-500/20 text-indigo-600 dark:text-indigo-400 px-1.5 py-0.5 rounded-full">AI</span>
                                    </label>
                                    
                                    <button
                                        onClick={handleExtractText}
                                        disabled={isExtracting}
                                        className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-indigo-500 hover:bg-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors mb-3"
                                    >
                                        {isExtracting ? (
                                            <>
                                                <Loader2 className="w-4 h-4 animate-spin" />
                                                Metin çıkarılıyor...
                                            </>
                                        ) : (
                                            <>
                                                <ScanText className="w-4 h-4" />
                                                Görselden Metin Çıkar
                                            </>
                                        )}
                                    </button>

                                    {ocrError && (
                                        <p className="text-xs text-red-500 mb-2">{ocrError}</p>
                                    )}

                                    {extractedText && (
                                        <div className="space-y-2">
                                            <div className="p-3 bg-background rounded-lg border border-border max-h-24 overflow-y-auto">
                                                <p className="text-xs text-foreground whitespace-pre-wrap">{extractedText}</p>
                                            </div>
                                            <div className="flex gap-2">
                                                <button
                                                    onClick={handleCopyText}
                                                    className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 bg-background hover:bg-accent border border-border rounded-lg text-xs transition-colors"
                                                >
                                                    <Copy className="w-3 h-3" />
                                                    Kopyala
                                                </button>
                                                <button
                                                    onClick={handleInsertAsCaption}
                                                    className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 bg-background hover:bg-accent border border-border rounded-lg text-xs transition-colors"
                                                >
                                                    <FileText className="w-3 h-3" />
                                                    Altyazı Yap
                                                </button>
                                            </div>
                                        </div>
                                    )}
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
                                {isEditMode ? 'Değişiklikleri Kaydet' : 'Görseli Ekle'}
                            </button>
                        </div>
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    );
}
