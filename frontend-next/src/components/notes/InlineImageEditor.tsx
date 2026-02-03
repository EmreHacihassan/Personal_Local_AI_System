'use client';

/**
 * InlineImageEditor - Yatay Görsel Düzenleme Toolbar'ı
 * 
 * Özellikler:
 * - Tek tıkla seç → görselin ALTINDA yatay toolbar çıkar
 * - Köşelerden/kenarlardan CANLI boyutlandırma
 * - Tüm ayarlar (boyut, hizalama, şekil, altyazı, OCR) toolbar'da
 * - Görsel kendi yerinde kalır, ekranı kaplamaz
 */

import React, { useState, useRef, useCallback, useEffect } from 'react';
import { motion } from 'framer-motion';
import { API_BASE_URL } from '@/lib/api';
import { 
    Move, 
    Maximize2, 
    AlignLeft, 
    AlignCenter, 
    AlignRight,
    Square, 
    Circle, 
    BoxSelect,
    Lock,
    Unlock,
    RotateCcw,
    ScanText,
    Loader2,
    Copy,
    FileText,
    X,
    Check,
    ChevronDown,
    ChevronUp
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface ImageOptions {
    size?: string;
    align?: string;
    shape?: string;
    width?: number;
    height?: number;
    caption?: string;
    offsetX?: number;
    offsetY?: number;
}

interface InlineImageEditorProps {
    src: string;
    alt: string;
    initialWidth: number;
    initialHeight: number;
    options: ImageOptions;
    onRealtimeUpdate: (newOptions: Partial<ImageOptions>) => void;
    onSave: (finalOptions: ImageOptions) => void;
    onDeselect: () => void;
}

type ResizeHandle = 'nw' | 'n' | 'ne' | 'e' | 'se' | 's' | 'sw' | 'w';

export function InlineImageEditor({
    src,
    alt,
    initialWidth,
    initialHeight,
    options,
    onRealtimeUpdate,
    onSave,
    onDeselect
}: InlineImageEditorProps) {
    // State
    const [dimensions, setDimensions] = useState({
        width: initialWidth,
        height: initialHeight
    });
    const [originalDimensions, setOriginalDimensions] = useState({ width: 300, height: 200 });
    const [originalAspectRatio, setOriginalAspectRatio] = useState(initialWidth / initialHeight);
    const [aspectRatioLocked, setAspectRatioLocked] = useState(true);
    const [size, setSize] = useState<string>(options.size || 'medium');
    const [align, setAlign] = useState<string>(options.align || 'center');
    const [shape, setShape] = useState<string>(options.shape || 'rounded');
    const [caption, setCaption] = useState<string>(options.caption !== undefined ? options.caption : (alt !== 'image' ? alt : ''));
    const [showAdvanced, setShowAdvanced] = useState(false);
    
    // OCR
    const [isExtracting, setIsExtracting] = useState(false);
    const [extractedText, setExtractedText] = useState('');
    const [ocrError, setOcrError] = useState('');
    
    // Resize & Move
    const [isResizing, setIsResizing] = useState(false);
    const [isMoving, setIsMoving] = useState(false);
    const [resizeHandle, setResizeHandle] = useState<ResizeHandle | null>(null);
    
    // Kullanıcı aktif olarak etkileşimde mi? (resize/move sırasında click outside'ı engelle)
    const isInteractingRef = useRef(false);
    
    // Görsel taşıma pozisyonu (props'tan başlat)
    const [moveOffset, setMoveOffset] = useState({ 
        x: options.offsetX || 0, 
        y: options.offsetY || 0 
    });
    
    const containerRef = useRef<HTMLDivElement>(null);
    const startRef = useRef({ x: 0, y: 0, width: 0, height: 0, offsetX: 0, offsetY: 0 });

    // Load original aspect ratio from image
    useEffect(() => {
        const img = new Image();
        img.onload = () => {
            setOriginalAspectRatio(img.naturalWidth / img.naturalHeight);
            setOriginalDimensions({ width: img.naturalWidth, height: img.naturalHeight });
        };
        img.src = src;
    }, [src]);

    // Sync with prop changes
    useEffect(() => {
        setDimensions({ width: initialWidth, height: initialHeight });
    }, [initialWidth, initialHeight]);

    // Get shape class
    const getShapeClass = () => {
        switch (shape) {
            case 'rounded': return 'rounded-xl';
            case 'circle': return 'rounded-full';
            case 'bordered': return 'rounded-lg border-4 border-white shadow-lg';
            default: return 'rounded-lg';
        }
    };

    // Size presets
    const sizePresets: Record<string, number> = {
        'small': 150,
        'medium': 300,
        'large': 500,
        'full': 800
    };

    // Handle size preset change
    const handleSizeChange = (newSize: string) => {
        setSize(newSize);
        if (newSize !== 'custom' && sizePresets[newSize]) {
            const newWidth = sizePresets[newSize];
            const newHeight = newWidth / originalAspectRatio;
            setDimensions({ width: newWidth, height: newHeight });
            onRealtimeUpdate({ size: newSize, width: newWidth, height: newHeight });
        }
    };

    // Handle width change
    const handleWidthChange = (newWidth: number) => {
        const clampedWidth = Math.max(50, Math.min(1200, newWidth));
        const newHeight = aspectRatioLocked ? clampedWidth / originalAspectRatio : dimensions.height;
        setDimensions({ width: clampedWidth, height: newHeight });
        setSize('custom');
        onRealtimeUpdate({ width: clampedWidth, height: newHeight, size: 'custom' });
    };

    // Handle height change
    const handleHeightChange = (newHeight: number) => {
        const clampedHeight = Math.max(50, Math.min(800, newHeight));
        const newWidth = aspectRatioLocked ? clampedHeight * originalAspectRatio : dimensions.width;
        setDimensions({ width: newWidth, height: clampedHeight });
        setSize('custom');
        onRealtimeUpdate({ width: newWidth, height: clampedHeight, size: 'custom' });
    };

    // Handle align change
    const handleAlignChange = (newAlign: string) => {
        setAlign(newAlign);
        onRealtimeUpdate({ align: newAlign });
    };

    // Handle shape change
    const handleShapeChange = (newShape: string) => {
        setShape(newShape);
        onRealtimeUpdate({ shape: newShape });
    };

    // Handle caption change
    const handleCaptionChange = (newCaption: string) => {
        setCaption(newCaption);
        onRealtimeUpdate({ caption: newCaption });
    };

    // Reset to original size
    const handleResetSize = () => {
        setDimensions(originalDimensions);
        setSize('custom');
        onRealtimeUpdate({ width: originalDimensions.width, height: originalDimensions.height, size: 'custom' });
    };

    // OCR text extraction
    const handleExtractText = async () => {
        setIsExtracting(true);
        setOcrError('');
        try {
            const response = await fetch(`${API_BASE_URL}/api/notes/ocr`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image_path: src })
            });
            
            if (!response.ok) throw new Error('OCR işlemi başarısız');
            
            const data = await response.json();
            setExtractedText(data.text || 'Metin bulunamadı');
        } catch (error) {
            setOcrError('Metin çıkarma hatası');
            console.error('OCR error:', error);
        } finally {
            setIsExtracting(false);
        }
    };

    // Copy extracted text
    const handleCopyText = () => navigator.clipboard.writeText(extractedText);

    // Insert text as caption
    const handleInsertAsCaption = () => {
        setCaption(extractedText);
        onRealtimeUpdate({ caption: extractedText });
    };

    // Handle save
    const handleSave = () => {
        onSave({
            size,
            align,
            shape,
            width: Math.round(dimensions.width),
            height: Math.round(dimensions.height),
            caption,
            offsetX: Math.round(moveOffset.x),
            offsetY: Math.round(moveOffset.y)
        });
    };

    // Handle resize start
    const handleResizeStart = useCallback((e: React.MouseEvent, handle: ResizeHandle) => {
        e.preventDefault();
        e.stopPropagation();
        isInteractingRef.current = true;
        setIsResizing(true);
        setResizeHandle(handle);
        startRef.current = { x: e.clientX, y: e.clientY, width: dimensions.width, height: dimensions.height, offsetX: 0, offsetY: 0 };
    }, [dimensions]);

    // Handle move start (Taşı butonu için)
    const handleMoveStart = useCallback((e: React.MouseEvent) => {
        e.preventDefault();
        e.stopPropagation();
        isInteractingRef.current = true;
        setIsMoving(true);
        startRef.current = { 
            x: e.clientX, 
            y: e.clientY, 
            width: dimensions.width, 
            height: dimensions.height,
            offsetX: moveOffset.x,
            offsetY: moveOffset.y
        };
    }, [dimensions, moveOffset]);

    // Handle mouse move for resize AND move
    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            if (isResizing && resizeHandle) {
                const deltaX = e.clientX - startRef.current.x;
                const deltaY = e.clientY - startRef.current.y;
                
                let newWidth = startRef.current.width;
                let newHeight = startRef.current.height;

                switch (resizeHandle) {
                    case 'e': case 'se': case 'ne':
                        newWidth = startRef.current.width + deltaX;
                        newHeight = newWidth / originalAspectRatio;
                        break;
                    case 'w': case 'sw': case 'nw':
                        newWidth = startRef.current.width - deltaX;
                        newHeight = newWidth / originalAspectRatio;
                        break;
                    case 's':
                        newHeight = startRef.current.height + deltaY;
                        newWidth = newHeight * originalAspectRatio;
                        break;
                    case 'n':
                        newHeight = startRef.current.height - deltaY;
                        newWidth = newHeight * originalAspectRatio;
                        break;
                }

                newWidth = Math.max(50, Math.min(1200, newWidth));
                newHeight = Math.max(50, Math.min(800, newHeight));

                setDimensions({ width: newWidth, height: newHeight });
                setSize('custom');
                onRealtimeUpdate({ width: newWidth, height: newHeight, size: 'custom' });
            }
            
            // Move işlemi - görseli gerçek zamanlı taşı
            if (isMoving) {
                const deltaX = e.clientX - startRef.current.x;
                const deltaY = e.clientY - startRef.current.y;
                const newOffsetX = startRef.current.offsetX + deltaX;
                const newOffsetY = startRef.current.offsetY + deltaY;
                setMoveOffset({ x: newOffsetX, y: newOffsetY });
                // Gerçek zamanlı güncelleme
                onRealtimeUpdate({ offsetX: Math.round(newOffsetX), offsetY: Math.round(newOffsetY) });
            }
        };

        const handleMouseUp = () => {
            if (isResizing || isMoving) {
                setIsResizing(false);
                setIsMoving(false);
                setResizeHandle(null);
                document.body.style.cursor = '';
                document.body.style.userSelect = '';
                
                // Kısa bir gecikme ile interacting flag'ini kapat
                setTimeout(() => {
                    isInteractingRef.current = false;
                }, 100);
            }
        };

        if (isResizing || isMoving) {
            window.addEventListener('mousemove', handleMouseMove);
            window.addEventListener('mouseup', handleMouseUp);
            document.body.style.cursor = isMoving ? 'move' : 'nwse-resize';
            document.body.style.userSelect = 'none';
        }

        return () => {
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('mouseup', handleMouseUp);
        };
    }, [isResizing, isMoving, resizeHandle, originalAspectRatio, onRealtimeUpdate]);

    // Click outside to save and deselect - SADECE etkileşim yoksa
    useEffect(() => {
        const handleClickOutside = (e: MouseEvent) => {
            // Resize veya move sırasında click outside'ı engelle
            if (isInteractingRef.current || isResizing || isMoving) {
                return;
            }
            
            if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
                handleSave();
                onDeselect();
            }
        };

        const timer = setTimeout(() => {
            document.addEventListener('mousedown', handleClickOutside);
        }, 150);

        return () => {
            clearTimeout(timer);
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [onDeselect, dimensions, size, align, shape, caption, isResizing, isMoving]);

    // Resize handle component
    const ResizeHandleEl = ({ position: pos }: { position: ResizeHandle }) => (
        <div
            className={cn(
                "absolute w-3 h-3 bg-primary-500 border-2 border-white rounded-full shadow-md z-20 transition-transform hover:scale-125",
                pos === 'nw' && "-top-1.5 -left-1.5 cursor-nw-resize",
                pos === 'n' && "-top-1.5 left-1/2 -translate-x-1/2 cursor-n-resize",
                pos === 'ne' && "-top-1.5 -right-1.5 cursor-ne-resize",
                pos === 'e' && "top-1/2 -right-1.5 -translate-y-1/2 cursor-e-resize",
                pos === 'se' && "-bottom-1.5 -right-1.5 cursor-se-resize",
                pos === 's' && "-bottom-1.5 left-1/2 -translate-x-1/2 cursor-s-resize",
                pos === 'sw' && "-bottom-1.5 -left-1.5 cursor-sw-resize",
                pos === 'w' && "top-1/2 -left-1.5 -translate-y-1/2 cursor-w-resize"
            )}
            onMouseDown={(e) => handleResizeStart(e, pos)}
        />
    );

    // Taşıma sırasındaki geçici offset (sadece sürükleme anında görünür)
    const dragOffset = isMoving ? {
        x: moveOffset.x - (options.offsetX || 0),
        y: moveOffset.y - (options.offsetY || 0)
    } : { x: 0, y: 0 };

    return (
        <div
            ref={containerRef}
            className="relative inline-block"
            style={{ 
                // Sadece sürükleme sırasında geçici transform uygula
                transform: (dragOffset.x !== 0 || dragOffset.y !== 0) 
                    ? `translate(${dragOffset.x}px, ${dragOffset.y}px)` 
                    : undefined,
                width: dimensions.width
            }}
        >
            {/* Taşı Çubuğu - Üstte ABSOLUTE */}
            <div 
                className="absolute left-1/2 -translate-x-1/2 z-20"
                style={{ top: -32 }}
            >
                <div 
                    className={cn(
                        "px-3 py-1 bg-primary-500 text-white rounded-lg shadow-lg flex items-center gap-2 cursor-move select-none text-xs whitespace-nowrap",
                        isMoving && "ring-2 ring-white ring-opacity-50"
                    )}
                    onMouseDown={handleMoveStart}
                    title="Görseli sürükleyerek taşıyın"
                >
                    <Move className="w-3.5 h-3.5" />
                    {isMoving ? 'Taşınıyor...' : 'Taşı'}
                </div>
            </div>

            {/* Selection Border */}
            <div className="absolute inset-0 border-2 border-primary-500 rounded-lg pointer-events-none z-10" />
            
            {/* 8 Resize Handle */}
            <ResizeHandleEl position="nw" />
            <ResizeHandleEl position="n" />
            <ResizeHandleEl position="ne" />
            <ResizeHandleEl position="e" />
            <ResizeHandleEl position="se" />
            <ResizeHandleEl position="s" />
            <ResizeHandleEl position="sw" />
            <ResizeHandleEl position="w" />

            {/* Image - Aynı boyut, kayma yok */}
            <img
                src={src}
                alt={alt}
                className={cn("w-full h-auto object-contain", getShapeClass())}
                style={{ width: dimensions.width, height: dimensions.height, maxHeight: 600 }}
                draggable={false}
            />

            {/* Caption - Aynı konumda - only show if not empty */}
            {caption && (
                <p className={cn(
                    "mt-1 text-xs text-muted-foreground",
                    align === 'left' ? 'text-left' : align === 'right' ? 'text-right' : 'text-center'
                )}>
                    {caption}
                </p>
            )}

            {/* ========== YATAY TOOLBAR - Görselin Altında ABSOLUTE ========== */}
            <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="absolute left-1/2 -translate-x-1/2 bg-card border border-border rounded-xl shadow-xl overflow-hidden z-30"
                style={{ 
                    top: dimensions.height + (caption ? 30 : 10),
                    width: Math.max(dimensions.width, 400),
                    maxWidth: '90vw'
                }}
            >
                {/* Ana Kontroller - Tek Satır */}
                <div className="flex items-center gap-1 p-2 flex-wrap">
                    {/* Boyut Presetleri */}
                    <div className="flex items-center gap-1 px-2 border-r border-border">
                        <Maximize2 className="w-3.5 h-3.5 text-muted-foreground" />
                        {(['small', 'medium', 'large', 'full'] as const).map((s) => (
                            <button
                                key={s}
                                onClick={() => handleSizeChange(s)}
                                className={cn(
                                    "px-2 py-1 rounded text-[11px] font-medium transition-all",
                                    size === s
                                        ? "bg-primary-500 text-white"
                                        : "hover:bg-accent text-muted-foreground"
                                )}
                            >
                                {s === 'small' ? 'S' : s === 'medium' ? 'M' : s === 'large' ? 'L' : 'XL'}
                            </button>
                        ))}
                    </div>

                    {/* Pixel Boyutları */}
                    <div className="flex items-center gap-1 px-2 border-r border-border">
                        <input
                            type="number"
                            value={Math.round(dimensions.width)}
                            onChange={(e) => handleWidthChange(parseInt(e.target.value) || 0)}
                            className="w-14 px-1.5 py-1 bg-muted border border-border rounded text-[11px] text-center"
                            min={50}
                            max={1200}
                        />
                        <button
                            onClick={() => setAspectRatioLocked(!aspectRatioLocked)}
                            className={cn(
                                "p-1 rounded transition-colors",
                                aspectRatioLocked ? "text-primary-500" : "text-muted-foreground"
                            )}
                            title={aspectRatioLocked ? "Kilitli" : "Serbest"}
                        >
                            {aspectRatioLocked ? <Lock className="w-3 h-3" /> : <Unlock className="w-3 h-3" />}
                        </button>
                        <input
                            type="number"
                            value={Math.round(dimensions.height)}
                            onChange={(e) => handleHeightChange(parseInt(e.target.value) || 0)}
                            className="w-14 px-1.5 py-1 bg-muted border border-border rounded text-[11px] text-center"
                            min={50}
                            max={800}
                            disabled={aspectRatioLocked}
                        />
                        <span className="text-[10px] text-muted-foreground">px</span>
                    </div>

                    {/* Hizalama */}
                    <div className="flex items-center gap-0.5 px-2 border-r border-border">
                        {[
                            { val: 'left', icon: AlignLeft },
                            { val: 'center', icon: AlignCenter },
                            { val: 'right', icon: AlignRight }
                        ].map(({ val, icon: Icon }) => (
                            <button
                                key={val}
                                onClick={() => handleAlignChange(val)}
                                className={cn(
                                    "p-1.5 rounded transition-colors",
                                    align === val ? "bg-primary-500/20 text-primary-500" : "hover:bg-accent text-muted-foreground"
                                )}
                            >
                                <Icon className="w-3.5 h-3.5" />
                            </button>
                        ))}
                    </div>

                    {/* Şekil */}
                    <div className="flex items-center gap-0.5 px-2 border-r border-border">
                        {[
                            { val: 'default', icon: Square, title: 'Normal' },
                            { val: 'rounded', icon: Square, title: 'Oval', className: 'rounded' },
                            { val: 'circle', icon: Circle, title: 'Daire' },
                            { val: 'bordered', icon: BoxSelect, title: 'Çerçeve' }
                        ].map(({ val, icon: Icon, title, className }) => (
                            <button
                                key={val}
                                onClick={() => handleShapeChange(val)}
                                className={cn(
                                    "p-1.5 rounded transition-colors",
                                    shape === val ? "bg-primary-500/20 text-primary-500" : "hover:bg-accent text-muted-foreground"
                                )}
                                title={title}
                            >
                                <Icon className={cn("w-3.5 h-3.5", className)} />
                            </button>
                        ))}
                    </div>

                    {/* Sıfırla */}
                    <button
                        onClick={handleResetSize}
                        className="p-1.5 hover:bg-accent rounded transition-colors text-muted-foreground"
                        title="Orijinal Boyut"
                    >
                        <RotateCcw className="w-3.5 h-3.5" />
                    </button>

                    {/* Gelişmiş Toggle */}
                    <button
                        onClick={() => setShowAdvanced(!showAdvanced)}
                        className={cn(
                            "ml-auto flex items-center gap-1 px-2 py-1 rounded text-[11px] transition-colors",
                            showAdvanced ? "bg-primary-500/20 text-primary-500" : "hover:bg-accent text-muted-foreground"
                        )}
                    >
                        {showAdvanced ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                        Daha Fazla
                    </button>

                    {/* Kaydet & Kapat */}
                    <button
                        onClick={() => { handleSave(); onDeselect(); }}
                        className="px-3 py-1.5 bg-primary-500 hover:bg-primary-600 text-white rounded-lg text-[11px] font-medium flex items-center gap-1"
                    >
                        <Check className="w-3 h-3" />
                        Tamam
                    </button>

                    {/* X/Y Koordinatları - Tamam'ın sağında */}
                    <div className="flex items-center gap-1 ml-2 pl-2 border-l border-border">
                        <input
                            type="number"
                            value={Math.round(moveOffset.x)}
                            onChange={(e) => {
                                const newX = parseInt(e.target.value) || 0;
                                setMoveOffset(prev => ({ ...prev, x: newX }));
                                onRealtimeUpdate({ offsetX: newX });
                            }}
                            className="w-12 px-1.5 py-1 bg-muted border border-border rounded text-[11px] text-center"
                            title="X koordinatı (sağa +)"
                        />
                        <span className="text-[10px] text-muted-foreground font-medium">X</span>
                        <input
                            type="number"
                            value={Math.round(-moveOffset.y)}
                            onChange={(e) => {
                                const inputY = parseInt(e.target.value) || 0;
                                const newY = -inputY;
                                setMoveOffset(prev => ({ ...prev, y: newY }));
                                onRealtimeUpdate({ offsetY: newY });
                            }}
                            className="w-12 px-1.5 py-1 bg-muted border border-border rounded text-[11px] text-center"
                            title="Y koordinatı (yukarı +)"
                        />
                        <span className="text-[10px] text-muted-foreground font-medium">Y</span>
                    </div>
                </div>

                {/* Gelişmiş Kontroller - Açılabilir */}
                {showAdvanced && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="border-t border-border p-3 space-y-3"
                    >
                        {/* Altyazı */}
                        <div className="flex items-center gap-2">
                            <label className="text-[11px] text-muted-foreground w-16">Altyazı:</label>
                            <input
                                type="text"
                                value={caption}
                                onChange={(e) => handleCaptionChange(e.target.value)}
                                className="flex-1 px-2 py-1.5 bg-muted border border-border rounded-lg text-xs"
                                placeholder="Görsel açıklaması..."
                            />
                        </div>

                        {/* OCR */}
                        <div className="flex items-center gap-2">
                            <label className="text-[11px] text-muted-foreground w-16 flex items-center gap-1">
                                <ScanText className="w-3 h-3" />
                                OCR:
                            </label>
                            <button
                                onClick={handleExtractText}
                                disabled={isExtracting}
                                className="px-3 py-1.5 bg-indigo-500 hover:bg-indigo-600 disabled:opacity-50 text-white rounded-lg text-[11px] font-medium flex items-center gap-1"
                            >
                                {isExtracting ? (
                                    <><Loader2 className="w-3 h-3 animate-spin" /> Çıkarılıyor...</>
                                ) : (
                                    <><ScanText className="w-3 h-3" /> Metin Çıkar</>
                                )}
                            </button>
                            <span className="text-[10px] bg-indigo-500/20 text-indigo-600 dark:text-indigo-400 px-1.5 py-0.5 rounded-full">AI</span>
                        </div>

                        {/* OCR Sonuç */}
                        {ocrError && <p className="text-[11px] text-red-500">{ocrError}</p>}
                        {extractedText && (
                            <div className="space-y-2">
                                <div className="p-2 bg-muted rounded-lg border border-border max-h-20 overflow-y-auto">
                                    <p className="text-[11px] whitespace-pre-wrap">{extractedText}</p>
                                </div>
                                <div className="flex gap-2">
                                    <button onClick={handleCopyText} className="flex-1 flex items-center justify-center gap-1 px-2 py-1 bg-background hover:bg-accent border border-border rounded text-[10px]">
                                        <Copy className="w-3 h-3" /> Kopyala
                                    </button>
                                    <button onClick={handleInsertAsCaption} className="flex-1 flex items-center justify-center gap-1 px-2 py-1 bg-background hover:bg-accent border border-border rounded text-[10px]">
                                        <FileText className="w-3 h-3" /> Altyazı Yap
                                    </button>
                                </div>
                            </div>
                        )}

                        {/* Boyut Bilgisi */}
                        <div className="text-[10px] text-muted-foreground text-center">
                            Orijinal: {originalDimensions.width}×{originalDimensions.height}px • 
                            Şu an: {Math.round(dimensions.width)}×{Math.round(dimensions.height)}px • 
                            Ölçek: {Math.round((dimensions.width / originalDimensions.width) * 100)}%
                        </div>
                    </motion.div>
                )}
            </motion.div>
        </div>
    );
}

export default InlineImageEditor;
