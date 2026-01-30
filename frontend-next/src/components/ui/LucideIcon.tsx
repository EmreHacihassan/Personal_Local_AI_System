'use client';

/**
 * LucideIcon - Merkezi İkon Wrapper Bileşeni
 * 
 * Bu bileşen, Next.js'in barrel import optimization hatası nedeniyle oluşturuldu.
 * Tüm lucide-react ikonlarını dynamic import ile yükleyerek "is not a constructor" 
 * hatasını önler.
 * 
 * Kullanım:
 * ```tsx
 * import { LucideIcon } from '@/components/ui/LucideIcon';
 * 
 * <LucideIcon name="Brain" className="w-6 h-6" />
 * ```
 */

import { memo, lazy, Suspense, ComponentType } from 'react';
import type { LucideProps } from 'lucide-react';

// Tüm kullanılan ikon isimleri
export type IconName =
    | 'AlertCircle'
    | 'AlertTriangle'
    | 'ArrowLeft'
    | 'ArrowRight'
    | 'Award'
    | 'BarChart'
    | 'BarChart2'
    | 'BarChart3'
    | 'Bell'
    | 'Book'
    | 'BookOpen'
    | 'Bot'
    | 'Brain'
    | 'Bug'
    | 'Calendar'
    | 'Check'
    | 'CheckCircle'
    | 'CheckCircle2'
    | 'ChevronDown'
    | 'ChevronLeft'
    | 'ChevronRight'
    | 'ChevronUp'
    | 'Circle'
    | 'Clock'
    | 'Cloud'
    | 'Code'
    | 'Code2'
    | 'Compass'
    | 'Copy'
    | 'Cpu'
    | 'Crown'
    | 'Database'
    | 'Download'
    | 'Edit'
    | 'Edit2'
    | 'Edit3'
    | 'ExternalLink'
    | 'Eye'
    | 'EyeOff'
    | 'File'
    | 'FileCode'
    | 'FileText'
    | 'Filter'
    | 'Flag'
    | 'Folder'
    | 'FolderOpen'
    | 'Gauge'
    | 'Gift'
    | 'GitBranch'
    | 'Globe'
    | 'GraduationCap'
    | 'Grid'
    | 'Hash'
    | 'Heart'
    | 'HelpCircle'
    | 'History'
    | 'Home'
    | 'Image'
    | 'Info'
    | 'Key'
    | 'Keyboard'
    | 'Laptop'
    | 'Layers'
    | 'Layout'
    | 'LayoutGrid'
    | 'Library'
    | 'Lightbulb'
    | 'Link'
    | 'Link2'
    | 'List'
    | 'Loader'
    | 'Loader2'
    | 'Lock'
    | 'LogOut'
    | 'Mail'
    | 'Map'
    | 'MapPin'
    | 'Maximize'
    | 'Maximize2'
    | 'Menu'
    | 'MessageCircle'
    | 'MessageSquare'
    | 'Mic'
    | 'MicOff'
    | 'Minimize'
    | 'Minus'
    | 'Monitor'
    | 'Moon'
    | 'MoreHorizontal'
    | 'MoreVertical'
    | 'MousePointer'
    | 'Move'
    | 'Music'
    | 'Network'
    | 'Palette'
    | 'Paperclip'
    | 'Pause'
    | 'PenTool'
    | 'Phone'
    | 'Pin'
    | 'Play'
    | 'PlayCircle'
    | 'Plus'
    | 'PlusCircle'
    | 'Power'
    | 'RefreshCcw'
    | 'RefreshCw'
    | 'Rocket'
    | 'RotateCcw'
    | 'RotateCw'
    | 'Route'
    | 'Save'
    | 'Scan'
    | 'Search'
    | 'Send'
    | 'Settings'
    | 'Settings2'
    | 'Share'
    | 'Share2'
    | 'Shield'
    | 'ShieldCheck'
    | 'Shuffle'
    | 'Sidebar'
    | 'SkipBack'
    | 'SkipForward'
    | 'Sliders'
    | 'Sparkle'
    | 'Sparkles'
    | 'Speaker'
    | 'Square'
    | 'Star'
    | 'StopCircle'
    | 'Sun'
    | 'Table'
    | 'Tag'
    | 'Target'
    | 'Terminal'
    | 'ThumbsDown'
    | 'ThumbsUp'
    | 'Timer'
    | 'ToggleLeft'
    | 'ToggleRight'
    | 'Trash'
    | 'Trash2'
    | 'TrendingUp'
    | 'Trophy'
    | 'Type'
    | 'Undo'
    | 'Unlock'
    | 'Upload'
    | 'User'
    | 'UserPlus'
    | 'Users'
    | 'Video'
    | 'VideoOff'
    | 'Volume'
    | 'Volume2'
    | 'VolumeX'
    | 'Wand'
    | 'Wand2'
    | 'Wifi'
    | 'WifiOff'
    | 'X'
    | 'XCircle'
    | 'Zap'
    | 'ZoomIn'
    | 'ZoomOut';

// İkon import map'i - lazy loading ile
const iconComponents: Record<IconName, ComponentType<LucideProps>> = {} as any;

// Dynamic icon loader
const getIconComponent = (name: IconName): ComponentType<LucideProps> => {
    if (!iconComponents[name]) {
        iconComponents[name] = lazy(() =>
            import('lucide-react').then(module => ({
                default: (module as any)[name] as ComponentType<LucideProps>
            }))
        );
    }
    return iconComponents[name];
};

// Fallback loading indicator
const IconFallback = () => (
    <span className="inline-block w-4 h-4 bg-current opacity-20 rounded animate-pulse" />
);

// Props tipi
export interface LucideIconProps extends Omit<LucideProps, 'ref'> {
    name: IconName;
    fallback?: React.ReactNode;
}

/**
 * LucideIcon Bileşeni
 * 
 * Next.js barrel optimization hatasını önlemek için oluşturulmuş
 * merkezi ikon wrapper bileşeni.
 */
export const LucideIcon = memo(function LucideIcon({
    name,
    fallback = <IconFallback />,
    ...props
}: LucideIconProps) {
    const IconComponent = getIconComponent(name);

    return (
        <Suspense fallback={fallback}>
            <IconComponent {...props} />
        </Suspense>
    );
});

// Kolaylık için direct export'lar - sık kullanılan ikonlar için
export const Icons = {
    brain: (props: LucideProps) => <LucideIcon name="Brain" {...props} />,
    zoomIn: (props: LucideProps) => <LucideIcon name="ZoomIn" {...props} />,
    zoomOut: (props: LucideProps) => <LucideIcon name="ZoomOut" {...props} />,
    search: (props: LucideProps) => <LucideIcon name="Search" {...props} />,
    settings: (props: LucideProps) => <LucideIcon name="Settings" {...props} />,
    x: (props: LucideProps) => <LucideIcon name="X" {...props} />,
    check: (props: LucideProps) => <LucideIcon name="Check" {...props} />,
    loader: (props: LucideProps) => <LucideIcon name="Loader2" {...props} />,
    spinner: (props: LucideProps) => <LucideIcon name="Loader2" className="animate-spin" {...props} />,
} as const;

export default LucideIcon;
