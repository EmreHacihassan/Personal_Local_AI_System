'use client';

/**
 * WikiLinkParser - Wiki-style [[link]] Parser ve Renderer
 * 
 * Not içeriğindeki [[Not Adı]] formatındaki bağlantıları tanır ve
 * tıklanabilir linklere dönüştürür.
 * 
 * Özellikler:
 * - [[Not Adı]] syntax desteği
 * - Hover preview
 * - Backlinks tracking
 * - Link oluşturma kısayolu
 */

import React, { useState, useRef, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link2, ExternalLink, FileText, Clock, Tag } from 'lucide-react';
import { Note } from '@/store/useStore';
import { cn, formatDate } from '@/lib/utils';

// Wiki link regex pattern
const WIKI_LINK_REGEX = /\[\[([^\]]+)\]\]/g;

interface WikiLinkProps {
    noteTitle: string;
    notes: Note[];
    onNavigate: (noteId: string) => void;
    className?: string;
}

interface NotePreviewProps {
    note: Note;
    position: { x: number; y: number };
    onClose: () => void;
    onNavigate: (noteId: string) => void;
}

/**
 * Not önizleme popup'ı - Hover'da gösterilir
 */
export function NoteHoverPreview({ note, position, onClose, onNavigate }: NotePreviewProps) {
    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -10 }}
            transition={{ duration: 0.15 }}
            className="fixed z-[9999] w-80 max-h-96 overflow-hidden rounded-xl bg-card border border-border shadow-2xl"
            style={{
                left: Math.min(position.x, window.innerWidth - 340),
                top: Math.min(position.y + 10, window.innerHeight - 400),
            }}
            onMouseLeave={onClose}
        >
            {/* Header */}
            <div className="p-4 border-b border-border bg-gradient-to-r from-primary-500/10 to-purple-500/10">
                <div className="flex items-center gap-2 mb-2">
                    <FileText className="w-4 h-4 text-primary-500" />
                    <h4 className="font-semibold text-sm truncate">{note.title}</h4>
                </div>
                <div className="flex items-center gap-3 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatDate(note.updatedAt)}
                    </span>
                    {note.tags && note.tags.length > 0 && (
                        <span className="flex items-center gap-1">
                            <Tag className="w-3 h-3" />
                            {note.tags.length}
                        </span>
                    )}
                </div>
            </div>

            {/* Content Preview */}
            <div className="p-4 max-h-48 overflow-y-auto">
                <p className="text-sm text-muted-foreground whitespace-pre-wrap line-clamp-6">
                    {note.content || 'Bu not boş.'}
                </p>
            </div>

            {/* Footer */}
            <div className="p-3 border-t border-border bg-muted/30">
                <button
                    onClick={() => onNavigate(note.id)}
                    className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-primary-500 text-white text-sm font-medium hover:bg-primary-600 transition-colors"
                >
                    <ExternalLink className="w-3.5 h-3.5" />
                    Nota Git
                </button>
            </div>
        </motion.div>
    );
}

/**
 * Wiki Link bileşeni - Tek bir [[link]]'i temsil eder
 */
export function WikiLink({ noteTitle, notes, onNavigate, className }: WikiLinkProps) {
    const [showPreview, setShowPreview] = useState(false);
    const [previewPosition, setPreviewPosition] = useState({ x: 0, y: 0 });
    const linkRef = useRef<HTMLSpanElement>(null);
    const timeoutRef = useRef<NodeJS.Timeout>();

    // Notu bul
    const linkedNote = useMemo(() => {
        return notes.find(n =>
            n.title.toLowerCase() === noteTitle.toLowerCase() ||
            n.title.toLowerCase().includes(noteTitle.toLowerCase())
        );
    }, [notes, noteTitle]);

    const handleMouseEnter = useCallback((e: React.MouseEvent) => {
        if (!linkedNote) return;

        timeoutRef.current = setTimeout(() => {
            const rect = (e.target as HTMLElement).getBoundingClientRect();
            setPreviewPosition({ x: rect.left, y: rect.bottom });
            setShowPreview(true);
        }, 300); // 300ms delay before showing preview
    }, [linkedNote]);

    const handleMouseLeave = useCallback(() => {
        if (timeoutRef.current) {
            clearTimeout(timeoutRef.current);
        }
        // Delay hiding to allow mouse to move to preview
        setTimeout(() => setShowPreview(false), 100);
    }, []);

    const handleClick = useCallback(() => {
        if (linkedNote) {
            onNavigate(linkedNote.id);
        }
    }, [linkedNote, onNavigate]);

    return (
        <>
            <span
                ref={linkRef}
                onClick={handleClick}
                onMouseEnter={handleMouseEnter}
                onMouseLeave={handleMouseLeave}
                className={cn(
                    "inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md transition-all cursor-pointer",
                    linkedNote
                        ? "bg-primary-500/10 text-primary-600 dark:text-primary-400 hover:bg-primary-500/20 border border-primary-500/20"
                        : "bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20 border-dashed",
                    className
                )}
            >
                <Link2 className="w-3 h-3" />
                <span className="text-sm font-medium">{noteTitle}</span>
                {!linkedNote && <span className="text-xs opacity-60">(bulunamadı)</span>}
            </span>

            <AnimatePresence>
                {showPreview && linkedNote && (
                    <NoteHoverPreview
                        note={linkedNote}
                        position={previewPosition}
                        onClose={() => setShowPreview(false)}
                        onNavigate={onNavigate}
                    />
                )}
            </AnimatePresence>
        </>
    );
}

const IMAGE_REGEX = /!\[(.*?)\]\((.*?)\)/g;

type ContentPart =
    | { type: 'text'; content: string }
    | { type: 'wiki'; title: string }
    | { type: 'image'; alt: string; url: string; options?: ImageOptions };

interface ImageOptions {
    size?: string;
    align?: string;
    shape?: string;
    caption?: string;
}

const parseImageOptions = (altText: string): { caption: string, options: ImageOptions } => {
    if (!altText.includes('|')) {
        return { caption: altText, options: {} };
    }

    const parts = altText.split('|');
    const caption = parts[0];
    const options: ImageOptions = {};

    for (let i = 1; i < parts.length; i++) {
        const part = parts[i].trim();
        if (part.startsWith('size:')) options.size = part.replace('size:', '');
        else if (part.startsWith('align:')) options.align = part.replace('align:', '');
        else if (part.startsWith('shape:')) options.shape = part.replace('shape:', '');
    }

    return { caption, options };
};

/**
 * İçeriği parse edip wiki linkleri ve resimleri çıkaran utility
 */
export function parseContent(content: string): ContentPart[] {
    const parts: ContentPart[] = [];

    // Geçici olarak resimleri maskele veya split et
    // Basit yaklaşım: Regex exec ile sırayla gitmek zor çünkü iç içe olabilir veya sıra karışık
    // Parçalama stratejisi: Önce resimlere göre böl, sonra text kısımlarını wiki linklere göre böl

    let lastIndex = 0;
    let match;
    const imageRegex = new RegExp(IMAGE_REGEX);

    // 1. Resimleri bul ve parçala
    const imageParts: { start: number; end: number; alt: string; url: string }[] = [];
    while ((match = imageRegex.exec(content)) !== null) {
        imageParts.push({
            start: match.index,
            end: match.index + match[0].length,
            alt: match[1],
            url: match[2]
        });
    }

    // Eğer hiç resim yoksa direkt wiki link parse et
    if (imageParts.length === 0) {
        return parseWikiLinksOnly(content);
    }

    let currentIdx = 0;
    for (const img of imageParts) {
        // Resimden önceki text
        if (img.start > currentIdx) {
            const textSegment = content.slice(currentIdx, img.start);
            parts.push(...parseWikiLinksOnly(textSegment));
        }

        // Resim parse
        const { caption, options } = parseImageOptions(img.alt);
        parts.push({ type: 'image', alt: caption, url: img.url, options });
        currentIdx = img.end;
    }

    // Kalan text
    if (currentIdx < content.length) {
        parts.push(...parseWikiLinksOnly(content.slice(currentIdx)));
    }

    return parts;
}

function parseWikiLinksOnly(content: string): ContentPart[] {
    const parts: ContentPart[] = [];
    let lastIndex = 0;
    let match;
    const regex = new RegExp(WIKI_LINK_REGEX);

    while ((match = regex.exec(content)) !== null) {
        if (match.index > lastIndex) {
            parts.push({ type: 'text', content: content.slice(lastIndex, match.index) });
        }
        parts.push({ type: 'wiki', title: match[1] });
        lastIndex = match.index + match[0].length;
    }

    if (lastIndex < content.length) {
        parts.push({ type: 'text', content: content.slice(lastIndex) });
    }
    return parts;
}

/**
 * Wiki linklerini içeren içerik renderer
 */
interface WikiContentRendererProps {
    content: string;
    notes: Note[];
    onNavigate: (noteId: string) => void;
    className?: string;
}

export function WikiContentRenderer({ content, notes, onNavigate, className }: WikiContentRendererProps) {
    const parts = useMemo(() => parseContent(content), [content]);

    return (
        <div className={cn("whitespace-pre-wrap", className)}>
            {parts.map((part, index) => {
                if (part.type === 'image') {
                    const opts = part.options || {};

                    // Size classes
                    const sizeClass =
                        opts.size === 'small' ? 'max-w-[150px]' :
                            opts.size === 'medium' ? 'max-w-[300px]' :
                                opts.size === 'large' ? 'max-w-[500px]' :
                                    opts.size === 'full' ? 'max-w-full' : 'max-w-[300px]'; // default medium

                    // Align classes for container
                    const containerClass =
                        opts.align === 'left' ? 'flex justify-start' :
                            opts.align === 'right' ? 'flex justify-end' :
                                'flex justify-center'; // default center

                    // Shape classes
                    const shapeClass =
                        opts.shape === 'rounded' ? 'rounded-xl' :
                            opts.shape === 'circle' ? 'rounded-full aspect-square object-cover' :
                                opts.shape === 'bordered' ? 'rounded-lg border-4 border-white dark:border-gray-700 shadow-md' :
                                    'rounded-lg'; // default

                    return (
                        <div key={index} className={cn("my-4 w-full", containerClass)}>
                            <div className={cn("flex flex-col gap-2", opts.align === 'center' ? 'items-center' : opts.align === 'right' ? 'items-end' : 'items-start')}>
                                <img
                                    src={part.url}
                                    alt={part.alt}
                                    className={cn(
                                        "h-auto transition-all shadow-sm max-h-[600px] object-contain",
                                        sizeClass,
                                        shapeClass
                                    )}
                                    loading="lazy"
                                />
                                {part.alt && <span className="text-xs text-muted-foreground font-medium">{part.alt}</span>}
                            </div>
                        </div>
                    );
                } else if (part.type === 'wiki') {
                    return (
                        <WikiLink
                            key={index}
                            noteTitle={part.title}
                            notes={notes}
                            onNavigate={onNavigate}
                        />
                    );
                } else {
                    return <span key={index}>{part.content}</span>;
                }
            })}
        </div>
    );
}

/**
 * Backlinks finder - Bir nota bağlanan notları bulur
 */
export function findBacklinks(noteId: string, noteTitle: string, allNotes: Note[]): Note[] {
    return allNotes.filter(note => {
        if (note.id === noteId) return false;

        const regex = new RegExp(`\\[\\[${noteTitle}\\]\\]`, 'gi');
        return regex.test(note.content);
    });
}

/**
 * Wiki link oluşturma yardımcısı
 */
export function createWikiLink(noteTitle: string): string {
    return `[[${noteTitle}]]`;
}

/**
 * İçerikteki tüm wiki linkleri çıkar
 */
export function extractWikiLinks(content: string): string[] {
    const matches = content.match(WIKI_LINK_REGEX);
    if (!matches) return [];

    return matches.map(match => match.slice(2, -2)); // [[ ve ]] kaldır
}

export default WikiContentRenderer;
