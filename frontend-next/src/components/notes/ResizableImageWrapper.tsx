import React, { useState, useRef, useCallback, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Maximize2, Move, Settings } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ResizableImageWrapperProps {
    src: string;
    alt?: string;
    initialWidth?: number;
    initialHeight?: number;
    minWidth?: number;
    minHeight?: number;
    maxWidth?: number;
    maxHeight?: number;
    caption?: string;
    shape?: 'default' | 'rounded' | 'circle' | 'bordered';
    align?: 'left' | 'center' | 'right';
    onResize?: (width: number, height: number) => void;
    onSettingsClick?: () => void;
    className?: string;
    snapToGrid?: number; // Snap to this pixel value on release (default: 5)
}

interface DragState {
    isDragging: boolean;
    startX: number;
    startY: number;
    startWidth: number;
    startHeight: number;
    corner: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right' | null;
}

export function ResizableImageWrapper({
    src,
    alt = 'Image',
    initialWidth = 300,
    initialHeight = 200,
    minWidth = 50,
    minHeight = 50,
    maxWidth = 1200,
    maxHeight = 800,
    caption,
    shape = 'rounded',
    align = 'center',
    onResize,
    onSettingsClick,
    className,
    snapToGrid = 5
}: ResizableImageWrapperProps) {
    const [dimensions, setDimensions] = useState({ width: initialWidth, height: initialHeight });
    const [aspectRatio, setAspectRatio] = useState(initialWidth / initialHeight);
    const [isHovered, setIsHovered] = useState(false);
    const [dragState, setDragState] = useState<DragState>({
        isDragging: false,
        startX: 0,
        startY: 0,
        startWidth: 0,
        startHeight: 0,
        corner: null
    });
    
    const containerRef = useRef<HTMLDivElement>(null);
    const imageRef = useRef<HTMLImageElement>(null);

    // Load actual image aspect ratio
    useEffect(() => {
        const img = new Image();
        img.onload = () => {
            const ratio = img.naturalWidth / img.naturalHeight;
            setAspectRatio(ratio);
            // Adjust initial height based on aspect ratio
            if (initialWidth && !initialHeight) {
                setDimensions({ width: initialWidth, height: initialWidth / ratio });
            }
        };
        img.src = src;
    }, [src, initialWidth, initialHeight]);

    // Snap value to grid
    const snapToGridValue = useCallback((value: number) => {
        return Math.round(value / snapToGrid) * snapToGrid;
    }, [snapToGrid]);

    // Handle mouse down on resize handle
    const handleMouseDown = useCallback((e: React.MouseEvent, corner: DragState['corner']) => {
        e.preventDefault();
        e.stopPropagation();
        
        setDragState({
            isDragging: true,
            startX: e.clientX,
            startY: e.clientY,
            startWidth: dimensions.width,
            startHeight: dimensions.height,
            corner
        });
    }, [dimensions]);

    // Handle mouse move during drag
    const handleMouseMove = useCallback((e: MouseEvent) => {
        if (!dragState.isDragging || !dragState.corner) return;

        const deltaX = e.clientX - dragState.startX;
        const deltaY = e.clientY - dragState.startY;
        
        let newWidth = dragState.startWidth;
        let newHeight = dragState.startHeight;

        // Calculate new dimensions based on which corner is being dragged
        switch (dragState.corner) {
            case 'top-left':
                newWidth = dragState.startWidth - deltaX;
                newHeight = dragState.startHeight - deltaY;
                break;
            case 'top-right':
                newWidth = dragState.startWidth + deltaX;
                newHeight = dragState.startHeight - deltaY;
                break;
            case 'bottom-left':
                newWidth = dragState.startWidth - deltaX;
                newHeight = dragState.startHeight + deltaY;
                break;
            case 'bottom-right':
                newWidth = dragState.startWidth + deltaX;
                newHeight = dragState.startHeight + deltaY;
                break;
        }

        // If shift is held, maintain aspect ratio
        if (e.shiftKey) {
            // Use width as the primary dimension
            newHeight = newWidth / aspectRatio;
        }

        // Apply constraints
        newWidth = Math.max(minWidth, Math.min(maxWidth, newWidth));
        newHeight = Math.max(minHeight, Math.min(maxHeight, newHeight));

        setDimensions({ width: newWidth, height: newHeight });
    }, [dragState, aspectRatio, minWidth, minHeight, maxWidth, maxHeight]);

    // Handle mouse up (end drag)
    const handleMouseUp = useCallback(() => {
        if (dragState.isDragging) {
            // Snap to grid on release
            const snappedWidth = snapToGridValue(dimensions.width);
            const snappedHeight = snapToGridValue(dimensions.height);
            
            setDimensions({ width: snappedWidth, height: snappedHeight });
            onResize?.(snappedWidth, snappedHeight);
        }
        
        setDragState(prev => ({ ...prev, isDragging: false, corner: null }));
    }, [dragState.isDragging, dimensions, snapToGridValue, onResize]);

    // Add and remove global mouse event listeners
    useEffect(() => {
        if (dragState.isDragging) {
            window.addEventListener('mousemove', handleMouseMove);
            window.addEventListener('mouseup', handleMouseUp);
            document.body.style.cursor = 'nwse-resize';
            document.body.style.userSelect = 'none';
        }

        return () => {
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('mouseup', handleMouseUp);
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        };
    }, [dragState.isDragging, handleMouseMove, handleMouseUp]);

    const getShapeClass = (shape: string) => {
        switch (shape) {
            case 'rounded': return 'rounded-xl';
            case 'circle': return 'rounded-full aspect-square object-cover';
            case 'bordered': return 'rounded-lg border-4 border-white dark:border-gray-700 shadow-md';
            default: return 'rounded-none';
        }
    };

    const getAlignClass = (align: string) => {
        switch (align) {
            case 'left': return 'mr-auto';
            case 'right': return 'ml-auto';
            default: return 'mx-auto';
        }
    };

    // Common styles for resize handles
    const handleBaseClass = "absolute w-4 h-4 bg-primary-500 border-2 border-white rounded-full shadow-lg opacity-0 group-hover:opacity-100 transition-opacity cursor-nwse-resize z-10 hover:scale-125 active:scale-90";

    return (
        <div 
            className={cn("relative inline-block group", getAlignClass(align), className)}
            ref={containerRef}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
        >
            {/* Image Container */}
            <motion.div
                style={{ width: dimensions.width, height: dimensions.height }}
                className="relative"
                animate={{ width: dimensions.width, height: dimensions.height }}
                transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            >
                <img
                    ref={imageRef}
                    src={src}
                    alt={alt}
                    className={cn(
                        "w-full h-full object-cover transition-all duration-200",
                        getShapeClass(shape),
                        dragState.isDragging && "ring-2 ring-primary-500 ring-offset-2"
                    )}
                    draggable={false}
                />

                {/* Resize Handles - Only visible on hover */}
                {/* Top Left */}
                <div
                    className={cn(handleBaseClass, "-top-2 -left-2 cursor-nw-resize")}
                    onMouseDown={(e) => handleMouseDown(e, 'top-left')}
                />
                {/* Top Right */}
                <div
                    className={cn(handleBaseClass, "-top-2 -right-2 cursor-ne-resize")}
                    onMouseDown={(e) => handleMouseDown(e, 'top-right')}
                />
                {/* Bottom Left */}
                <div
                    className={cn(handleBaseClass, "-bottom-2 -left-2 cursor-sw-resize")}
                    onMouseDown={(e) => handleMouseDown(e, 'bottom-left')}
                />
                {/* Bottom Right */}
                <div
                    className={cn(handleBaseClass, "-bottom-2 -right-2 cursor-se-resize")}
                    onMouseDown={(e) => handleMouseDown(e, 'bottom-right')}
                />

                {/* Dimension Badge */}
                <div className={cn(
                    "absolute top-2 left-2 px-2 py-1 bg-black/60 backdrop-blur text-white text-[10px] rounded-full transition-opacity",
                    (isHovered || dragState.isDragging) ? "opacity-100" : "opacity-0"
                )}>
                    {Math.round(dimensions.width)} × {Math.round(dimensions.height)}
                </div>

                {/* Settings Button */}
                {onSettingsClick && (
                    <button
                        onClick={onSettingsClick}
                        className={cn(
                            "absolute top-2 right-2 p-1.5 bg-black/60 backdrop-blur text-white rounded-full transition-all hover:bg-black/80 hover:scale-110",
                            isHovered ? "opacity-100" : "opacity-0"
                        )}
                    >
                        <Settings className="w-3.5 h-3.5" />
                    </button>
                )}

                {/* Shift hint during drag */}
                {dragState.isDragging && (
                    <div className="absolute -bottom-8 left-1/2 -translate-x-1/2 px-2 py-1 bg-black/80 text-white text-[10px] rounded-full whitespace-nowrap">
                        Shift basılı tutun: En-boy oranını koru
                    </div>
                )}
            </motion.div>

            {/* Caption */}
            {caption && (
                <p className={cn(
                    "mt-2 text-sm text-muted-foreground font-medium",
                    align === 'left' ? 'text-left' : align === 'right' ? 'text-right' : 'text-center'
                )}
                style={{ width: dimensions.width }}
                >
                    {caption}
                </p>
            )}
        </div>
    );
}
