'use client';

import { useState, useEffect, useCallback, useMemo, useRef, lazy, Suspense, ComponentType } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import dynamic from 'next/dynamic';
import { useRouter } from 'next/navigation';
import { cn } from '@/lib/utils';

// Dynamic icon imports to avoid Next.js barrel optimization error
const Brain = dynamic(() => import('lucide-react').then(mod => mod.Brain), { ssr: false }) as ComponentType<any>;
const ZoomIn = dynamic(() => import('lucide-react').then(mod => mod.ZoomIn), { ssr: false }) as ComponentType<any>;
const ZoomOut = dynamic(() => import('lucide-react').then(mod => mod.ZoomOut), { ssr: false }) as ComponentType<any>;
const Maximize2 = dynamic(() => import('lucide-react').then(mod => mod.Maximize2), { ssr: false }) as ComponentType<any>;
const Filter = dynamic(() => import('lucide-react').then(mod => mod.Filter), { ssr: false }) as ComponentType<any>;
const RefreshCw = dynamic(() => import('lucide-react').then(mod => mod.RefreshCw), { ssr: false }) as ComponentType<any>;
const Settings2 = dynamic(() => import('lucide-react').then(mod => mod.Settings2), { ssr: false }) as ComponentType<any>;
const Eye = dynamic(() => import('lucide-react').then(mod => mod.Eye), { ssr: false }) as ComponentType<any>;
const EyeOff = dynamic(() => import('lucide-react').then(mod => mod.EyeOff), { ssr: false }) as ComponentType<any>;
const Link2 = dynamic(() => import('lucide-react').then(mod => mod.Link2), { ssr: false }) as ComponentType<any>;
const Tag = dynamic(() => import('lucide-react').then(mod => mod.Tag), { ssr: false }) as ComponentType<any>;
const Sparkles = dynamic(() => import('lucide-react').then(mod => mod.Sparkles), { ssr: false }) as ComponentType<any>;
const Search = dynamic(() => import('lucide-react').then(mod => mod.Search), { ssr: false }) as ComponentType<any>;
const Info = dynamic(() => import('lucide-react').then(mod => mod.Info), { ssr: false }) as ComponentType<any>;
const ChevronRight = dynamic(() => import('lucide-react').then(mod => mod.ChevronRight), { ssr: false }) as ComponentType<any>;
const Circle = dynamic(() => import('lucide-react').then(mod => mod.Circle), { ssr: false }) as ComponentType<any>;
const ArrowRight = dynamic(() => import('lucide-react').then(mod => mod.ArrowRight), { ssr: false }) as ComponentType<any>;
const Layers = dynamic(() => import('lucide-react').then(mod => mod.Layers), { ssr: false }) as ComponentType<any>;
const Network = dynamic(() => import('lucide-react').then(mod => mod.Network), { ssr: false }) as ComponentType<any>;
const X = dynamic(() => import('lucide-react').then(mod => mod.X), { ssr: false }) as ComponentType<any>;
const ExternalLink = dynamic(() => import('lucide-react').then(mod => mod.ExternalLink), { ssr: false }) as ComponentType<any>;
const Clock = dynamic(() => import('lucide-react').then(mod => mod.Clock), { ssr: false }) as ComponentType<any>;
const Pin = dynamic(() => import('lucide-react').then(mod => mod.Pin), { ssr: false }) as ComponentType<any>;
const Folder = dynamic(() => import('lucide-react').then(mod => mod.Folder), { ssr: false }) as ComponentType<any>;
const Route = dynamic(() => import('lucide-react').then(mod => mod.Route), { ssr: false }) as ComponentType<any>;
const Download = dynamic(() => import('lucide-react').then(mod => mod.Download), { ssr: false }) as ComponentType<any>;
const MapIcon = dynamic(() => import('lucide-react').then(mod => mod.Map), { ssr: false }) as ComponentType<any>;
const Cpu = dynamic(() => import('lucide-react').then(mod => mod.Cpu), { ssr: false }) as ComponentType<any>;
const MessageSquare = dynamic(() => import('lucide-react').then(mod => mod.MessageSquare), { ssr: false }) as ComponentType<any>;
const Palette = dynamic(() => import('lucide-react').then(mod => mod.Palette), { ssr: false }) as ComponentType<any>;
const GitBranch = dynamic(() => import('lucide-react').then(mod => mod.GitBranch), { ssr: false }) as ComponentType<any>;
const SidebarOpen = dynamic(() => import('lucide-react').then(mod => mod.PanelRight), { ssr: false }) as ComponentType<any>;

// Premium Mind Components
import { NodeDetailSidebar } from '@/components/mind/NodeDetailSidebar';
import { FilterPanel } from '@/components/mind/FilterPanel';
import { GraphExportMenu } from '@/components/mind/GraphExportMenu';

// Types
interface GraphNode {
    id: string;
    data: {
        label: string;
        title: string;
        color: string;
        folder_id?: string;
        pinned?: boolean;
        tags?: string[];
    };
    position: { x: number; y: number };
    style?: { width: number; height: number };
}

interface GraphEdge {
    id: string;
    source: string;
    target: string;
    label?: string;
    type: string;
    animated?: boolean;
    style?: { strokeWidth: number; opacity: number };
    data?: { strength: number };
}

interface GraphData {
    nodes: GraphNode[];
    edges: GraphEdge[];
    stats: {
        total_nodes: number;
        total_edges: number;
        connected_nodes: number;
        orphan_nodes: number;
        wiki_links: number;
        tag_links: number;
        similarity_links: number;
    };
}

interface Particle {
    id: number;
    x: number;
    y: number;
    size: number;
    opacity: number;
    velocity: { x: number; y: number };
    color: string;
}

// Premium Color Palette
const NOTE_COLORS: Record<string, { bg: string; glow: string; border: string }> = {
    yellow: { bg: '#fef3c7', glow: 'rgba(251, 191, 36, 0.4)', border: '#f59e0b' },
    green: { bg: '#d1fae5', glow: 'rgba(16, 185, 129, 0.4)', border: '#10b981' },
    blue: { bg: '#dbeafe', glow: 'rgba(59, 130, 246, 0.4)', border: '#3b82f6' },
    pink: { bg: '#fce7f3', glow: 'rgba(236, 72, 153, 0.4)', border: '#ec4899' },
    purple: { bg: '#ede9fe', glow: 'rgba(139, 92, 246, 0.4)', border: '#8b5cf6' },
    orange: { bg: '#ffedd5', glow: 'rgba(249, 115, 22, 0.4)', border: '#f97316' },
    red: { bg: '#fee2e2', glow: 'rgba(239, 68, 68, 0.4)', border: '#ef4444' },
    gray: { bg: '#f3f4f6', glow: 'rgba(107, 114, 128, 0.3)', border: '#6b7280' },
    default: { bg: '#ffffff', glow: 'rgba(168, 85, 247, 0.3)', border: '#a855f7' }
};

const EDGE_COLORS: Record<string, { stroke: string; glow: string }> = {
    wiki_link: { stroke: '#3b82f6', glow: 'rgba(59, 130, 246, 0.5)' },
    tag_based: { stroke: '#10b981', glow: 'rgba(16, 185, 129, 0.5)' },
    similarity: { stroke: '#f59e0b', glow: 'rgba(245, 158, 11, 0.5)' },
    default: { stroke: '#6b7280', glow: 'rgba(107, 114, 128, 0.3)' }
};

// Particle colors for neural effect
const PARTICLE_COLORS = ['#a855f7', '#8b5cf6', '#6366f1', '#3b82f6', '#06b6d4', '#ec4899'];

export default function MindPage() {
    // Router
    const router = useRouter();

    // State
    const [graphData, setGraphData] = useState<GraphData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [zoom, setZoom] = useState(1);
    const [pan, setPan] = useState({ x: 0, y: 0 });
    const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
    const [hoveredNode, setHoveredNode] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [focusedSearch, setFocusedSearch] = useState(false);

    // Filters
    const [showOrphans, setShowOrphans] = useState(true);
    const [showSimilarity, setShowSimilarity] = useState(true);
    const [showTags, setShowTags] = useState(true);
    const [showSettings, setShowSettings] = useState(false);
    const [similarityThreshold, setSimilarityThreshold] = useState(0.2);

    // Neural particles
    const [particles, setParticles] = useState<Particle[]>([]);
    const [connectionParticles, setConnectionParticles] = useState<{ x: number; y: number; progress: number; edgeId: string }[]>([]);

    // Premium Feature States
    const [pathMode, setPathMode] = useState(false);
    const [pathSource, setPathSource] = useState<string | null>(null);
    const [pathTarget, setPathTarget] = useState<string | null>(null);
    const [highlightedPath, setHighlightedPath] = useState<string[]>([]);
    const [pathLoading, setPathLoading] = useState(false);

    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [noteDetails, setNoteDetails] = useState<any>(null);
    const [detailsLoading, setDetailsLoading] = useState(false);

    const [aiSummary, setAiSummary] = useState<string | null>(null);
    const [summaryLoading, setSummaryLoading] = useState(false);

    const [clusters, setClusters] = useState<any[]>([]);
    const [showClusters, setShowClusters] = useState(false);

    const [connectionCounts, setConnectionCounts] = useState<Record<string, number>>({});
    const [showMinimap, setShowMinimap] = useState(true);
    const [exporting, setExporting] = useState(false);

    // Premium Panel States
    const [showFilterPanel, setShowFilterPanel] = useState(false);
    const [showExportMenu, setShowExportMenu] = useState(false);
    const [showNodeSidebar, setShowNodeSidebar] = useState(false);
    const [layoutType, setLayoutType] = useState<'force' | 'hierarchical' | 'radial' | 'timeline'>('force');
    const [colorFilters, setColorFilters] = useState<string[]>([]);
    const [tagFilters, setTagFilters] = useState<string[]>([]);
    const [dateRangeFilter, setDateRangeFilter] = useState<{ from?: Date; to?: Date }>({});
    const [depthLimit, setDepthLimit] = useState(0);
    const [showHeatMap, setShowHeatMap] = useState(false);

    const containerRef = useRef<HTMLDivElement>(null);
    const svgRef = useRef<SVGSVGElement>(null);
    const isDragging = useRef(false);
    const draggedNode = useRef<string | null>(null);
    const lastMousePos = useRef({ x: 0, y: 0 });
    const animationFrameRef = useRef<number>();

    // Initialize neural particles with colors
    useEffect(() => {
        const count = 80;
        const newParticles = Array.from({ length: count }).map((_, i) => ({
            id: i,
            x: Math.random() * 2000 - 1000,
            y: Math.random() * 2000 - 1000,
            size: Math.random() * 3 + 0.5,
            opacity: Math.random() * 0.6 + 0.1,
            velocity: {
                x: (Math.random() - 0.5) * 0.3,
                y: (Math.random() - 0.5) * 0.3
            },
            color: PARTICLE_COLORS[Math.floor(Math.random() * PARTICLE_COLORS.length)]
        }));
        setParticles(newParticles);
    }, []);

    // Optimized particle animation with RAF
    useEffect(() => {
        let lastTime = performance.now();

        const animate = (currentTime: number) => {
            const deltaTime = (currentTime - lastTime) / 16; // Normalize to ~60fps
            lastTime = currentTime;

            setParticles(prev => prev.map(p => {
                let newX = p.x + p.velocity.x * deltaTime;
                let newY = p.y + p.velocity.y * deltaTime;

                // Wrap around
                if (newX > 1500) newX = -1500;
                if (newX < -1500) newX = 1500;
                if (newY > 1200) newY = -1200;
                if (newY < -1200) newY = 1200;

                return { ...p, x: newX, y: newY };
            }));

            // Animate connection particles along edges
            setConnectionParticles(prev =>
                prev.map(cp => ({
                    ...cp,
                    progress: (cp.progress + 0.02 * deltaTime) % 1
                })).filter(() => Math.random() > 0.001) // Slowly remove old particles
            );

            animationFrameRef.current = requestAnimationFrame(animate);
        };

        animationFrameRef.current = requestAnimationFrame(animate);
        return () => {
            if (animationFrameRef.current) {
                cancelAnimationFrame(animationFrameRef.current);
            }
        };
    }, []);

    // Add flowing particles on edges periodically
    useEffect(() => {
        if (!graphData?.edges.length) return;

        const interval = setInterval(() => {
            if (graphData.edges.length > 0) {
                const randomEdge = graphData.edges[Math.floor(Math.random() * graphData.edges.length)];
                setConnectionParticles(prev => [...prev.slice(-30), {
                    x: 0,
                    y: 0,
                    progress: 0,
                    edgeId: randomEdge.id
                }]);
            }
        }, 200);

        return () => clearInterval(interval);
    }, [graphData?.edges]);

    // Fetch graph data with debounce
    const fetchGraph = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);

            const params = new URLSearchParams({
                include_orphans: showOrphans.toString(),
                include_similarity: showSimilarity.toString(),
                include_tags: showTags.toString(),
                similarity_threshold: similarityThreshold.toString()
            });

            console.log('[MindPage] Fetching graph with params:', Object.fromEntries(params));

            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 30000);

            const response = await fetch(`/api/notes/graph?${params}`, {
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'Graf yüklenemedi' }));
                console.error('[MindPage] API Error:', response.status, errorData);

                if (response.status === 503) {
                    throw new Error('Backend çalışmıyor. Lütfen "python run.py" ile başlatın.');
                }
                throw new Error(errorData.detail || errorData.hint || 'Graf yüklenemedi');
            }

            const data = await response.json();
            console.log('[MindPage] Graph data received:', {
                nodes: data.nodes?.length || 0,
                edges: data.edges?.length || 0,
                stats: data.stats
            });

            if (!data.nodes || data.nodes.length === 0) {
                console.warn('[MindPage] No nodes in response');
            }

            // Apply enhanced force-directed layout
            const layoutedData = applyForceLayout(data);
            setGraphData(layoutedData);
        } catch (err) {
            console.error('[MindPage] Graph fetch error:', err);
            if (err instanceof Error && err.name === 'AbortError') {
                setError('İstek zaman aşımına uğradı. Backend yanıt vermiyor.');
            } else {
                setError(err instanceof Error ? err.message : 'Bilinmeyen hata');
            }
        } finally {
            setLoading(false);
        }
    }, [showOrphans, showSimilarity, showTags, similarityThreshold]);

    useEffect(() => {
        fetchGraph();
    }, [fetchGraph]);

    // ============ PREMIUM API FUNCTIONS ============

    // Fetch path between two nodes
    const fetchPath = useCallback(async (sourceId: string, targetId: string) => {
        if (!sourceId || !targetId) return;
        setPathLoading(true);
        try {
            const response = await fetch(`/api/notes/graph/path?source_id=${sourceId}&target_id=${targetId}`);
            if (response.ok) {
                const data = await response.json();
                if (data.found) {
                    setHighlightedPath(data.path);
                } else {
                    setHighlightedPath([]);
                }
            }
        } catch (error) {
            console.error('Path finding error:', error);
        } finally {
            setPathLoading(false);
        }
    }, []);

    // Fetch note details for sidebar
    const fetchNoteDetails = useCallback(async (noteId: string) => {
        setDetailsLoading(true);
        try {
            const response = await fetch(`/api/notes/${noteId}/details`);
            if (response.ok) {
                const data = await response.json();
                setNoteDetails(data);
                setSidebarOpen(true);
            }
        } catch (error) {
            console.error('Note details error:', error);
        } finally {
            setDetailsLoading(false);
        }
    }, []);

    // Fetch AI summary for a note
    const fetchAISummary = useCallback(async (noteId: string) => {
        setSummaryLoading(true);
        setAiSummary(null);
        try {
            const response = await fetch(`/api/notes/${noteId}/ai-summary`);
            if (response.ok) {
                const data = await response.json();
                setAiSummary(data.summary);
            }
        } catch (error) {
            console.error('AI summary error:', error);
        } finally {
            setSummaryLoading(false);
        }
    }, []);

    // Fetch clusters
    const fetchClusters = useCallback(async () => {
        try {
            const response = await fetch('/api/notes/graph/clusters');
            if (response.ok) {
                const data = await response.json();
                setClusters(data.clusters || []);
            }
        } catch (error) {
            console.error('Clusters error:', error);
        }
    }, []);

    // Fetch connection counts for heat map
    const fetchConnectionCounts = useCallback(async () => {
        try {
            const response = await fetch('/api/notes/graph/connections');
            if (response.ok) {
                const data = await response.json();
                setConnectionCounts(data.connections || {});
            }
        } catch (error) {
            console.error('Connection counts error:', error);
        }
    }, []);

    // Export graph as PNG
    const exportGraph = useCallback(async () => {
        if (!svgRef.current) return;
        setExporting(true);
        try {
            const svgElement = svgRef.current;
            const svgData = new XMLSerializer().serializeToString(svgElement);
            const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
            const url = URL.createObjectURL(svgBlob);

            const link = document.createElement('a');
            link.href = url;
            link.download = `mind-map-${new Date().toISOString().split('T')[0]}.svg`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Export error:', error);
        } finally {
            setExporting(false);
        }
    }, []);

    // Handle node click for path mode or sidebar
    const handleNodeClick = useCallback((nodeId: string) => {
        if (pathMode) {
            if (!pathSource) {
                setPathSource(nodeId);
            } else if (!pathTarget && nodeId !== pathSource) {
                setPathTarget(nodeId);
                fetchPath(pathSource, nodeId);
            }
        } else {
            fetchNoteDetails(nodeId);
        }
    }, [pathMode, pathSource, pathTarget, fetchPath, fetchNoteDetails]);

    // Reset path mode
    const resetPathMode = useCallback(() => {
        setPathMode(false);
        setPathSource(null);
        setPathTarget(null);
        setHighlightedPath([]);
    }, []);

    // Toggle clusters
    const toggleClusters = useCallback(() => {
        if (!showClusters) {
            fetchClusters();
        }
        setShowClusters(!showClusters);
    }, [showClusters, fetchClusters]);

    // Load connection counts on graph load
    useEffect(() => {
        if (graphData) {
            fetchConnectionCounts();
        }
    }, [graphData, fetchConnectionCounts]);

    // Get heat map intensity for node
    const getHeatMapIntensity = useCallback((nodeId: string) => {
        const count = connectionCounts[nodeId] || 0;
        if (count >= 6) return 1.0;
        if (count >= 4) return 0.8;
        if (count >= 2) return 0.6;
        return 0.4;
    }, [connectionCounts]);

    // Check if node is in highlighted path
    const isInPath = useCallback((nodeId: string) => {
        return highlightedPath.includes(nodeId);
    }, [highlightedPath]);

    // Get cluster color for node
    const getClusterColor = useCallback((nodeId: string) => {
        if (!showClusters) return null;
        for (const cluster of clusters) {
            if (cluster.notes.includes(nodeId)) {
                return cluster.color;
            }
        }
        return null;
    }, [showClusters, clusters]);

    // Enhanced Force-Directed Layout with better physics
    const applyForceLayout = (data: GraphData): GraphData => {
        if (!data.nodes.length) return data;

        const width = 1200;
        const height = 900;
        const centerX = width / 2;
        const centerY = height / 2;

        // Initial positions - golden ratio spiral for organic feel
        const phi = (1 + Math.sqrt(5)) / 2;
        const nodes = data.nodes.map((node, i) => {
            const angle = i * 2 * Math.PI / phi;
            const radius = Math.sqrt(i + 1) * 40;
            return {
                ...node,
                position: {
                    x: centerX + Math.cos(angle) * radius,
                    y: centerY + Math.sin(angle) * radius
                },
                velocity: { x: 0, y: 0 }
            };
        });

        const nodeMap = new Map(nodes.map(n => [n.id, n]));

        // Physics constants - tuned for better visualization
        const REPULSION = 15000;
        const SPRING_LENGTH = 180;
        const SPRING_K = 0.04;
        const DAMPING = 0.9;
        const CENTER_GRAVITY = 0.008;
        const ITERATIONS = 200;
        const MIN_DISTANCE = 60;

        for (let iter = 0; iter < ITERATIONS; iter++) {
            const cooling = 1 - (iter / ITERATIONS) * 0.7;

            // Repulsion between all nodes
            for (let a = 0; a < nodes.length; a++) {
                const nodeA = nodes[a];
                for (let b = a + 1; b < nodes.length; b++) {
                    const nodeB = nodes[b];
                    const dx = nodeA.position.x - nodeB.position.x;
                    const dy = nodeA.position.y - nodeB.position.y;
                    const distSq = Math.max(dx * dx + dy * dy, MIN_DISTANCE * MIN_DISTANCE);
                    const dist = Math.sqrt(distSq);

                    const force = (REPULSION / distSq) * cooling;
                    const fx = (dx / dist) * force;
                    const fy = (dy / dist) * force;

                    nodeA.velocity.x += fx;
                    nodeA.velocity.y += fy;
                    nodeB.velocity.x -= fx;
                    nodeB.velocity.y -= fy;
                }
            }

            // Spring attraction for edges
            for (const edge of data.edges) {
                const source = nodeMap.get(edge.source);
                const target = nodeMap.get(edge.target);

                if (source && target) {
                    const dx = target.position.x - source.position.x;
                    const dy = target.position.y - source.position.y;
                    const dist = Math.sqrt(dx * dx + dy * dy) || 1;

                    const force = (dist - SPRING_LENGTH) * SPRING_K * cooling;
                    const fx = (dx / dist) * force;
                    const fy = (dy / dist) * force;

                    source.velocity.x += fx;
                    source.velocity.y += fy;
                    target.velocity.x -= fx;
                    target.velocity.y -= fy;
                }
            }

            // Apply forces
            for (const node of nodes) {
                // Center gravity
                node.velocity.x += (centerX - node.position.x) * CENTER_GRAVITY;
                node.velocity.y += (centerY - node.position.y) * CENTER_GRAVITY;

                // Update position
                node.position.x += node.velocity.x * cooling;
                node.position.y += node.velocity.y * cooling;

                // Damping
                node.velocity.x *= DAMPING;
                node.velocity.y *= DAMPING;

                // Keep in bounds with soft boundaries
                const margin = 100;
                if (node.position.x < margin) node.velocity.x += 2;
                if (node.position.x > width - margin) node.velocity.x -= 2;
                if (node.position.y < margin) node.velocity.y += 2;
                if (node.position.y > height - margin) node.velocity.y -= 2;
            }
        }

        return { ...data, nodes };
    };

    // Filtered nodes with memoization
    const { filteredNodes, filteredEdges } = useMemo(() => {
        if (!graphData) return { filteredNodes: [], filteredEdges: [] };

        if (!searchQuery) {
            return { filteredNodes: graphData.nodes, filteredEdges: graphData.edges };
        }

        const query = searchQuery.toLowerCase();
        const matchingNodes = graphData.nodes.filter(node =>
            node.data.title.toLowerCase().includes(query) ||
            node.data.tags?.some(tag => tag.toLowerCase().includes(query))
        );

        const matchingIds = new Set(matchingNodes.map(n => n.id));
        const matchingEdges = graphData.edges.filter(
            e => matchingIds.has(e.source) || matchingIds.has(e.target)
        );

        return { filteredNodes: matchingNodes, filteredEdges: matchingEdges };
    }, [graphData, searchQuery]);

    // Mouse handlers with smooth interactions
    const handleMouseDown = (e: React.MouseEvent, nodeId?: string) => {
        if (nodeId) {
            e.stopPropagation();
            draggedNode.current = nodeId;
            setSelectedNode(graphData?.nodes.find(n => n.id === nodeId) || null);
        } else if (e.button === 0) {
            isDragging.current = true;
        }
        lastMousePos.current = { x: e.clientX, y: e.clientY };
    };

    const handleMouseMove = (e: React.MouseEvent) => {
        const dx = e.clientX - lastMousePos.current.x;
        const dy = e.clientY - lastMousePos.current.y;
        lastMousePos.current = { x: e.clientX, y: e.clientY };

        if (draggedNode.current && graphData) {
            const nodes = [...graphData.nodes];
            const node = nodes.find(n => n.id === draggedNode.current);
            if (node) {
                node.position.x += dx / zoom;
                node.position.y += dy / zoom;
                setGraphData({ ...graphData, nodes });
            }
        } else if (isDragging.current) {
            setPan(prev => ({ x: prev.x + dx, y: prev.y + dy }));
        }
    };

    const handleMouseUp = () => {
        isDragging.current = false;
        draggedNode.current = null;
    };

    const handleWheel = (e: React.WheelEvent) => {
        e.preventDefault();
        const delta = e.deltaY > 0 ? 0.92 : 1.08;
        setZoom(prev => Math.max(0.15, Math.min(4, prev * delta)));
    };

    const handleZoomIn = () => setZoom(prev => Math.min(4, prev * 1.25));
    const handleZoomOut = () => setZoom(prev => Math.max(0.15, prev * 0.8));
    const handleFit = () => {
        setZoom(1);
        setPan({ x: 0, y: 0 });
    };

    // Get connected info
    const getNodeEdges = (nodeId: string) => {
        if (!graphData) return [];
        return graphData.edges.filter(e => e.source === nodeId || e.target === nodeId);
    };

    const getConnectedNodes = (nodeId: string) => {
        const edges = getNodeEdges(nodeId);
        const connectedIds = new Set<string>();
        edges.forEach(e => {
            if (e.source === nodeId) connectedIds.add(e.target);
            if (e.target === nodeId) connectedIds.add(e.source);
        });
        return connectedIds;
    };

    // Compute edge path for curved lines
    const getEdgePath = (sourceNode: GraphNode, targetNode: GraphNode, index: number = 0) => {
        const dx = targetNode.position.x - sourceNode.position.x;
        const dy = targetNode.position.y - sourceNode.position.y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        // Curved path with bezier
        const midX = (sourceNode.position.x + targetNode.position.x) / 2;
        const midY = (sourceNode.position.y + targetNode.position.y) / 2;

        // Perpendicular offset for curve
        const curveFactor = Math.min(dist * 0.15, 40) * (index % 2 === 0 ? 1 : -1);
        const perpX = -dy / dist * curveFactor;
        const perpY = dx / dist * curveFactor;

        return `M ${sourceNode.position.x} ${sourceNode.position.y} Q ${midX + perpX} ${midY + perpY} ${targetNode.position.x} ${targetNode.position.y}`;
    };

    return (
        <div className="flex flex-col h-full bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 overflow-hidden">
            {/* Premium Header */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex-shrink-0 px-6 py-4 border-b border-white/10 backdrop-blur-2xl bg-black/20"
            >
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <div className="relative group">
                            <div className="absolute inset-0 bg-gradient-to-r from-purple-500 via-pink-500 to-cyan-500 blur-xl opacity-60 group-hover:opacity-80 transition-opacity" />
                            <motion.div
                                className="relative p-3 rounded-2xl bg-gradient-to-r from-purple-600 via-pink-500 to-cyan-500"
                                whileHover={{ scale: 1.05, rotate: 5 }}
                                whileTap={{ scale: 0.95 }}
                            >
                                <Brain className="w-7 h-7 text-white" />
                            </motion.div>
                        </div>
                        <div>
                            <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-400 via-pink-400 to-cyan-400 bg-clip-text text-transparent">
                                Mind
                            </h1>
                            <p className="text-sm text-slate-400 flex items-center gap-2">
                                <Network className="w-3.5 h-3.5" />
                                Neural not haritası
                            </p>
                        </div>
                    </div>

                    {/* Enhanced Search */}
                    <motion.div
                        className={cn(
                            "relative transition-all duration-300",
                            focusedSearch ? "w-96" : "w-72"
                        )}
                    >
                        <div className={cn(
                            "absolute inset-0 rounded-2xl transition-all duration-300",
                            focusedSearch
                                ? "bg-gradient-to-r from-purple-500/20 via-pink-500/20 to-cyan-500/20 blur-xl"
                                : "bg-transparent"
                        )} />
                        <div className="relative">
                            <Search className={cn(
                                "absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 transition-colors",
                                focusedSearch ? "text-purple-400" : "text-slate-400"
                            )} />
                            <input
                                type="text"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                onFocus={() => setFocusedSearch(true)}
                                onBlur={() => setFocusedSearch(false)}
                                placeholder="Notlarda ara..."
                                className="w-full pl-12 pr-4 py-3 rounded-2xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 focus:bg-white/10 transition-all"
                            />
                            {searchQuery && (
                                <button
                                    onClick={() => setSearchQuery('')}
                                    className="absolute right-4 top-1/2 -translate-y-1/2 p-1 rounded-full hover:bg-white/10 transition-colors"
                                >
                                    <X className="w-4 h-4 text-slate-400" />
                                </button>
                            )}
                        </div>
                    </motion.div>

                    {/* Controls */}
                    <div className="flex items-center gap-3">
                        {/* Path Finding Toggle */}
                        <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={() => pathMode ? resetPathMode() : setPathMode(true)}
                            className={cn(
                                "p-3 rounded-xl transition-all flex items-center gap-2",
                                pathMode
                                    ? "bg-gradient-to-r from-cyan-500/30 to-blue-500/30 text-cyan-400 border border-cyan-500/30"
                                    : "bg-white/5 text-slate-400 hover:bg-white/10 border border-white/10"
                            )}
                            title={pathMode ? "Yol modunu kapat" : "Yol bul"}
                        >
                            <Route className="w-5 h-5" />
                            {pathMode && <span className="text-sm font-medium">Yol Modu</span>}
                        </motion.button>

                        {/* Cluster Toggle */}
                        <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={toggleClusters}
                            className={cn(
                                "p-3 rounded-xl transition-all",
                                showClusters
                                    ? "bg-gradient-to-r from-green-500/30 to-emerald-500/30 text-green-400 border border-green-500/30"
                                    : "bg-white/5 text-slate-400 hover:bg-white/10 border border-white/10"
                            )}
                            title={showClusters ? "Kümeleri gizle" : "Kümeleri göster"}
                        >
                            <Palette className="w-5 h-5" />
                        </motion.button>

                        {/* Minimap Toggle */}
                        <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={() => setShowMinimap(!showMinimap)}
                            className={cn(
                                "p-3 rounded-xl transition-all",
                                showMinimap
                                    ? "bg-gradient-to-r from-amber-500/30 to-orange-500/30 text-amber-400 border border-amber-500/30"
                                    : "bg-white/5 text-slate-400 hover:bg-white/10 border border-white/10"
                            )}
                            title={showMinimap ? "Minimap'i gizle" : "Minimap'i göster"}
                        >
                            <MapIcon className="w-5 h-5" />
                        </motion.button>

                        {/* Export Button */}
                        <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={exportGraph}
                            disabled={exporting}
                            className="p-3 rounded-xl bg-white/5 text-slate-400 hover:bg-white/10 border border-white/10 transition-all disabled:opacity-50"
                            title="SVG olarak dışa aktar"
                        >
                            <Download className={cn("w-5 h-5", exporting && "animate-pulse")} />
                        </motion.button>

                        <div className="w-px h-8 bg-white/10" />

                        <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={() => setShowSettings(!showSettings)}
                            className={cn(
                                "p-3 rounded-xl transition-all",
                                showSettings
                                    ? "bg-gradient-to-r from-purple-500/30 to-pink-500/30 text-purple-400 border border-purple-500/30"
                                    : "bg-white/5 text-slate-400 hover:bg-white/10 border border-white/10"
                            )}
                        >
                            <Settings2 className="w-5 h-5" />
                        </motion.button>
                        <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={fetchGraph}
                            disabled={loading}
                            className="p-3 rounded-xl bg-white/5 text-slate-400 hover:bg-white/10 border border-white/10 transition-all disabled:opacity-50"
                        >
                            <RefreshCw className={cn("w-5 h-5", loading && "animate-spin")} />
                        </motion.button>
                    </div>
                </div>
            </motion.div>

            <div className="flex flex-1 overflow-hidden">
                {/* Main Graph Area */}
                <div className="flex-1 relative">
                    {/* Floating Zoom Controls */}
                    <motion.div
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="absolute top-4 left-4 z-10 flex flex-col gap-2"
                    >
                        {[
                            { icon: ZoomIn, onClick: handleZoomIn, label: 'Yakınlaştır' },
                            { icon: ZoomOut, onClick: handleZoomOut, label: 'Uzaklaştır' },
                            { icon: Maximize2, onClick: handleFit, label: 'Sığdır' }
                        ].map(({ icon: Icon, onClick, label }) => (
                            <motion.button
                                key={label}
                                whileHover={{ scale: 1.1, x: 5 }}
                                whileTap={{ scale: 0.9 }}
                                onClick={onClick}
                                className="p-3 rounded-xl bg-black/40 backdrop-blur-xl border border-white/10 text-white hover:bg-white/10 hover:border-purple-500/30 transition-all group"
                                title={label}
                            >
                                <Icon className="w-5 h-5 group-hover:text-purple-400 transition-colors" />
                            </motion.button>
                        ))}

                        {/* Zoom level indicator */}
                        <div className="mt-2 px-3 py-1.5 rounded-lg bg-black/40 backdrop-blur-xl border border-white/10 text-center">
                            <span className="text-xs font-medium text-slate-400">{Math.round(zoom * 100)}%</span>
                        </div>
                    </motion.div>

                    {/* Stats Badge */}
                    <AnimatePresence>
                        {graphData && !loading && (
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: 20 }}
                                className="absolute bottom-4 left-4 z-10 px-5 py-4 rounded-2xl bg-black/40 backdrop-blur-xl border border-white/10"
                            >
                                <div className="flex items-center gap-8 text-sm">
                                    <div className="flex items-center gap-2">
                                        <div className="w-3 h-3 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 animate-pulse" />
                                        <span className="text-slate-300 font-medium">{graphData.stats.total_nodes}</span>
                                        <span className="text-slate-500">not</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <ArrowRight className="w-4 h-4 text-blue-400" />
                                        <span className="text-slate-300 font-medium">{graphData.stats.total_edges}</span>
                                        <span className="text-slate-500">bağlantı</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <Network className="w-4 h-4 text-emerald-400" />
                                        <span className="text-slate-300 font-medium">{graphData.stats.connected_nodes}</span>
                                        <span className="text-slate-500">bağlı</span>
                                    </div>
                                    {graphData.stats.orphan_nodes > 0 && (
                                        <div className="flex items-center gap-2">
                                            <Circle className="w-3 h-3 text-amber-400" />
                                            <span className="text-slate-300 font-medium">{graphData.stats.orphan_nodes}</span>
                                            <span className="text-slate-500">yalnız</span>
                                        </div>
                                    )}
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>

                    {/* Path Mode Indicator */}
                    <AnimatePresence>
                        {pathMode && (
                            <motion.div
                                initial={{ opacity: 0, y: -20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -20 }}
                                className="absolute top-4 left-1/2 -translate-x-1/2 z-20 px-6 py-4 rounded-2xl bg-gradient-to-r from-cyan-500/20 to-blue-500/20 backdrop-blur-xl border border-cyan-500/30"
                            >
                                <div className="flex items-center gap-4">
                                    <Route className="w-5 h-5 text-cyan-400" />
                                    <div className="text-sm">
                                        {!pathSource && (
                                            <span className="text-slate-300">Başlangıç notunu seçin...</span>
                                        )}
                                        {pathSource && !pathTarget && (
                                            <span className="text-slate-300">Bitiş notunu seçin...</span>
                                        )}
                                        {pathSource && pathTarget && (
                                            <div className="flex items-center gap-2">
                                                {pathLoading ? (
                                                    <span className="text-cyan-400 animate-pulse">Yol hesaplanıyor...</span>
                                                ) : highlightedPath.length > 0 ? (
                                                    <span className="text-emerald-400">✓ {highlightedPath.length} adım</span>
                                                ) : (
                                                    <span className="text-amber-400">Yol bulunamadı</span>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                    <button
                                        onClick={resetPathMode}
                                        className="p-1.5 rounded-lg hover:bg-white/10 text-slate-400 hover:text-white transition-colors"
                                    >
                                        <X className="w-4 h-4" />
                                    </button>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>

                    {/* Minimap */}
                    <AnimatePresence>
                        {showMinimap && graphData && graphData.nodes.length > 0 && (
                            <motion.div
                                initial={{ opacity: 0, scale: 0.8 }}
                                animate={{ opacity: 1, scale: 1 }}
                                exit={{ opacity: 0, scale: 0.8 }}
                                className="absolute bottom-24 left-4 z-10 w-52 h-36 rounded-xl bg-black/60 backdrop-blur-xl border border-white/10 overflow-hidden"
                            >
                                <div className="absolute top-2 left-2 text-xs text-slate-500 flex items-center gap-1">
                                    <MapIcon className="w-3 h-3" />
                                    Minimap
                                </div>
                                <svg width="100%" height="100%" className="p-4">
                                    {/* Render mini nodes */}
                                    {graphData.nodes.slice(0, 100).map((node) => {
                                        const x = ((node.position.x + 500) / 2000) * 180 + 10;
                                        const y = ((node.position.y + 500) / 1500) * 100 + 15;
                                        const clusterColor = getClusterColor(node.id);
                                        return (
                                            <circle
                                                key={node.id}
                                                cx={Math.max(10, Math.min(200, x))}
                                                cy={Math.max(15, Math.min(120, y))}
                                                r={isInPath(node.id) ? 4 : 2}
                                                fill={isInPath(node.id) ? '#06b6d4' : clusterColor || '#a855f7'}
                                                opacity={getHeatMapIntensity(node.id)}
                                            />
                                        );
                                    })}
                                </svg>
                            </motion.div>
                        )}
                    </AnimatePresence>

                    {/* Premium Legend */}
                    <motion.div
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="absolute bottom-4 right-4 z-10 px-5 py-3 rounded-2xl bg-black/40 backdrop-blur-xl border border-white/10"
                    >
                        <div className="flex items-center gap-6 text-xs">
                            <div className="flex items-center gap-2">
                                <div className="w-6 h-0.5 bg-gradient-to-r from-blue-500 to-blue-400 rounded" />
                                <span className="text-slate-400">Wiki Link</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-6 h-0.5 bg-gradient-to-r from-emerald-500 to-emerald-400 rounded" />
                                <span className="text-slate-400">Etiket</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-6 h-0.5 bg-gradient-to-r from-amber-500 to-amber-400 rounded" style={{ backgroundImage: 'repeating-linear-gradient(90deg, #f59e0b 0, #f59e0b 4px, transparent 4px, transparent 8px)' }} />
                                <span className="text-slate-400">Benzerlik</span>
                            </div>
                        </div>
                    </motion.div>

                    {/* Main SVG Canvas */}
                    <div
                        ref={containerRef}
                        className={cn(
                            "w-full h-full transition-cursor",
                            isDragging.current ? "cursor-grabbing" : "cursor-grab"
                        )}
                        onMouseDown={(e) => handleMouseDown(e)}
                        onMouseMove={handleMouseMove}
                        onMouseUp={handleMouseUp}
                        onMouseLeave={handleMouseUp}
                        onWheel={handleWheel}
                    >
                        {loading ? (
                            <div className="flex items-center justify-center h-full">
                                <motion.div
                                    className="flex flex-col items-center gap-6"
                                    initial={{ opacity: 0, scale: 0.9 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                >
                                    <div className="relative">
                                        <div className="w-20 h-20 border-4 border-purple-500/20 border-t-purple-500 rounded-full animate-spin" />
                                        <div className="absolute inset-0 w-20 h-20 border-4 border-pink-500/20 border-b-pink-500 rounded-full animate-spin" style={{ animationDirection: 'reverse', animationDuration: '1.5s' }} />
                                        <Brain className="absolute inset-0 m-auto w-8 h-8 text-purple-400 animate-pulse" />
                                    </div>
                                    <div className="text-center">
                                        <p className="text-slate-300 font-medium">Neural ağ oluşturuluyor...</p>
                                        <p className="text-slate-500 text-sm mt-1">Notlar arasındaki bağlantılar analiz ediliyor</p>
                                    </div>
                                </motion.div>
                            </div>
                        ) : error ? (
                            <div className="flex items-center justify-center h-full">
                                <motion.div
                                    className="text-center max-w-md"
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                >
                                    <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-500/10 flex items-center justify-center">
                                        <X className="w-8 h-8 text-red-400" />
                                    </div>
                                    <p className="text-red-400 font-medium text-lg">{error}</p>
                                    <p className="text-slate-500 text-sm mt-2">Graf yüklenirken bir sorun oluştu</p>
                                    <motion.button
                                        whileHover={{ scale: 1.05 }}
                                        whileTap={{ scale: 0.95 }}
                                        onClick={fetchGraph}
                                        className="mt-6 px-6 py-3 rounded-xl bg-gradient-to-r from-purple-500/20 to-pink-500/20 text-purple-400 hover:from-purple-500/30 hover:to-pink-500/30 border border-purple-500/30 transition-all"
                                    >
                                        Tekrar Dene
                                    </motion.button>
                                </motion.div>
                            </div>
                        ) : graphData && graphData.nodes.length === 0 ? (
                            <div className="flex items-center justify-center h-full">
                                <motion.div
                                    className="text-center"
                                    initial={{ opacity: 0, scale: 0.9 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                >
                                    <div className="relative mb-6">
                                        <div className="absolute inset-0 bg-gradient-to-r from-purple-500/20 to-pink-500/20 blur-3xl" />
                                        <Brain className="relative w-24 h-24 mx-auto text-slate-600" />
                                    </div>
                                    <h3 className="text-xl font-semibold text-slate-300">Henüz not yok</h3>
                                    <p className="text-slate-500 mt-2 max-w-sm">Not oluşturarak bilgi ağını büyütmeye başla</p>
                                    <motion.button
                                        whileHover={{ scale: 1.05 }}
                                        whileTap={{ scale: 0.95 }}
                                        onClick={() => router.push('/notes')}
                                        className="mt-6 px-6 py-3 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 text-white font-medium hover:opacity-90 transition-opacity"
                                    >
                                        İlk Notunu Oluştur
                                    </motion.button>
                                </motion.div>
                            </div>
                        ) : (
                            <svg
                                ref={svgRef}
                                width="100%"
                                height="100%"
                                className="select-none"
                            >
                                {/* Enhanced Gradients & Filters */}
                                <defs>
                                    {/* Node Glow */}
                                    <radialGradient id="nodeGlow" cx="50%" cy="50%" r="50%">
                                        <stop offset="0%" stopColor="rgba(168, 85, 247, 0.6)" />
                                        <stop offset="50%" stopColor="rgba(168, 85, 247, 0.2)" />
                                        <stop offset="100%" stopColor="rgba(168, 85, 247, 0)" />
                                    </radialGradient>

                                    {/* Selected Node Glow */}
                                    <radialGradient id="selectedGlow" cx="50%" cy="50%" r="50%">
                                        <stop offset="0%" stopColor="rgba(236, 72, 153, 0.8)" />
                                        <stop offset="50%" stopColor="rgba(168, 85, 247, 0.4)" />
                                        <stop offset="100%" stopColor="rgba(168, 85, 247, 0)" />
                                    </radialGradient>

                                    {/* Blur filter for glow */}
                                    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
                                        <feGaussianBlur stdDeviation="4" result="coloredBlur" />
                                        <feMerge>
                                            <feMergeNode in="coloredBlur" />
                                            <feMergeNode in="SourceGraphic" />
                                        </feMerge>
                                    </filter>

                                    <filter id="strongGlow" x="-50%" y="-50%" width="200%" height="200%">
                                        <feGaussianBlur stdDeviation="8" result="coloredBlur" />
                                        <feMerge>
                                            <feMergeNode in="coloredBlur" />
                                            <feMergeNode in="coloredBlur" />
                                            <feMergeNode in="SourceGraphic" />
                                        </feMerge>
                                    </filter>

                                    {/* Edge gradients */}
                                    <linearGradient id="wikiLinkGradient" gradientUnits="userSpaceOnUse">
                                        <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.3" />
                                        <stop offset="50%" stopColor="#3b82f6" stopOpacity="1" />
                                        <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.3" />
                                    </linearGradient>

                                    <linearGradient id="tagGradient" gradientUnits="userSpaceOnUse">
                                        <stop offset="0%" stopColor="#10b981" stopOpacity="0.3" />
                                        <stop offset="50%" stopColor="#10b981" stopOpacity="1" />
                                        <stop offset="100%" stopColor="#10b981" stopOpacity="0.3" />
                                    </linearGradient>

                                    <linearGradient id="similarityGradient" gradientUnits="userSpaceOnUse">
                                        <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.3" />
                                        <stop offset="50%" stopColor="#f59e0b" stopOpacity="1" />
                                        <stop offset="100%" stopColor="#f59e0b" stopOpacity="0.3" />
                                    </linearGradient>
                                </defs>

                                <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>
                                    {/* Background Particles */}
                                    {particles.map(p => (
                                        <circle
                                            key={p.id}
                                            cx={p.x}
                                            cy={p.y}
                                            r={p.size}
                                            fill={p.color}
                                            fillOpacity={p.opacity}
                                        />
                                    ))}

                                    {/* Edges with curves */}
                                    {filteredEdges.map((edge, index) => {
                                        const sourceNode = graphData?.nodes.find(n => n.id === edge.source);
                                        const targetNode = graphData?.nodes.find(n => n.id === edge.target);

                                        if (!sourceNode || !targetNode) return null;

                                        const isHighlighted = hoveredNode === edge.source || hoveredNode === edge.target;
                                        const edgeColors = EDGE_COLORS[edge.type] || EDGE_COLORS.default;
                                        const path = getEdgePath(sourceNode, targetNode, index);

                                        return (
                                            <g key={edge.id}>
                                                {/* Edge glow when highlighted */}
                                                {isHighlighted && (
                                                    <path
                                                        d={path}
                                                        fill="none"
                                                        stroke={edgeColors.glow}
                                                        strokeWidth={6}
                                                        strokeLinecap="round"
                                                        filter="url(#glow)"
                                                    />
                                                )}

                                                {/* Main edge */}
                                                <path
                                                    d={path}
                                                    fill="none"
                                                    stroke={edgeColors.stroke}
                                                    strokeWidth={isHighlighted ? 2.5 : 1.5}
                                                    strokeOpacity={isHighlighted ? 0.9 : 0.4}
                                                    strokeLinecap="round"
                                                    strokeDasharray={edge.type === 'similarity' ? '6,4' : undefined}
                                                    className="transition-all duration-300"
                                                />
                                            </g>
                                        );
                                    })}

                                    {/* Nodes */}
                                    {filteredNodes.map((node) => {
                                        const isSelected = selectedNode?.id === node.id;
                                        const isHovered = hoveredNode === node.id;
                                        const isConnected = hoveredNode ? getConnectedNodes(hoveredNode).has(node.id) : false;
                                        const shouldDim = hoveredNode && !isHovered && !isConnected;
                                        const nodeColors = NOTE_COLORS[node.data.color] || NOTE_COLORS.default;
                                        const baseSize = (node.style?.width || 40) / 2;
                                        const size = isHovered ? baseSize * 1.15 : isSelected ? baseSize * 1.1 : baseSize;

                                        // Premium: Heat map intensity
                                        const heatIntensity = getHeatMapIntensity(node.id);
                                        // Premium: Is in highlighted path
                                        const nodeInPath = isInPath(node.id);
                                        // Premium: Cluster color
                                        const clusterColor = getClusterColor(node.id);
                                        // Premium: Is path source or target
                                        const isPathSource = pathSource === node.id;
                                        const isPathTarget = pathTarget === node.id;

                                        return (
                                            <g
                                                key={node.id}
                                                transform={`translate(${node.position.x}, ${node.position.y})`}
                                                onMouseEnter={() => setHoveredNode(node.id)}
                                                onMouseLeave={() => setHoveredNode(null)}
                                                onMouseDown={(e) => handleMouseDown(e, node.id)}
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    handleNodeClick(node.id);
                                                    setSelectedNode(node);
                                                }}
                                                className="cursor-pointer"
                                                style={{
                                                    opacity: shouldDim ? 0.25 : heatIntensity,
                                                    transition: 'opacity 0.3s ease, transform 0.2s ease'
                                                }}
                                            >
                                                {/* Cluster background */}
                                                {clusterColor && (
                                                    <circle
                                                        r={size + 25}
                                                        fill={clusterColor}
                                                        fillOpacity={0.15}
                                                    />
                                                )}

                                                {/* Path highlight ring */}
                                                {nodeInPath && (
                                                    <circle
                                                        r={size + 18}
                                                        fill="none"
                                                        stroke="#06b6d4"
                                                        strokeWidth={3}
                                                        strokeDasharray="5,3"
                                                        className="animate-pulse"
                                                    />
                                                )}

                                                {/* Path source/target indicator */}
                                                {(isPathSource || isPathTarget) && (
                                                    <circle
                                                        r={size + 22}
                                                        fill="none"
                                                        stroke={isPathSource ? "#22c55e" : "#f97316"}
                                                        strokeWidth={4}
                                                        className="animate-ping"
                                                        style={{ animationDuration: '1.5s' }}
                                                    />
                                                )}

                                                {/* Outer glow ring */}
                                                {(isHovered || isSelected) && (
                                                    <>
                                                        <circle
                                                            r={size + 20}
                                                            fill="none"
                                                            stroke={isSelected ? '#ec4899' : '#a855f7'}
                                                            strokeWidth={2}
                                                            strokeOpacity={0.3}
                                                            strokeDasharray="4,4"
                                                            className="animate-spin"
                                                            style={{ animationDuration: '8s' }}
                                                        />
                                                        <circle
                                                            r={size + 12}
                                                            fill={isSelected ? 'url(#selectedGlow)' : 'url(#nodeGlow)'}
                                                            className="animate-pulse"
                                                        />
                                                    </>
                                                )}

                                                {/* Node shadow */}
                                                <circle
                                                    r={size}
                                                    fill="rgba(0,0,0,0.3)"
                                                    transform="translate(2, 2)"
                                                    filter="url(#glow)"
                                                />

                                                {/* Main node circle */}
                                                <circle
                                                    r={size}
                                                    fill={nodeColors.bg}
                                                    stroke={isSelected ? '#ec4899' : isHovered ? '#a855f7' : nodeColors.border}
                                                    strokeWidth={isSelected ? 3 : isHovered ? 2.5 : 1.5}
                                                    filter={isHovered || isSelected ? 'url(#strongGlow)' : undefined}
                                                    className="transition-all duration-200"
                                                />

                                                {/* Inner gradient overlay */}
                                                <circle
                                                    r={size - 2}
                                                    fill="url(#nodeGlow)"
                                                    fillOpacity={0.1}
                                                />

                                                {/* Pin indicator */}
                                                {node.data.pinned && (
                                                    <g transform={`translate(${size * 0.7}, ${-size * 0.7})`}>
                                                        <circle r={6} fill="#f59e0b" stroke="white" strokeWidth={2} />
                                                        <Pin className="w-2 h-2" style={{ transform: 'translate(-4px, -4px)' }} />
                                                    </g>
                                                )}

                                                {/* Node label */}
                                                <text
                                                    y={size + 20}
                                                    textAnchor="middle"
                                                    fill="white"
                                                    fontSize={isHovered || isSelected ? 13 : 12}
                                                    fontWeight={isHovered || isSelected ? 600 : 400}
                                                    className="pointer-events-none"
                                                    style={{
                                                        textShadow: '0 2px 4px rgba(0,0,0,0.5), 0 0 10px rgba(0,0,0,0.3)',
                                                        transition: 'all 0.2s'
                                                    }}
                                                >
                                                    {node.data.label}
                                                </text>

                                                {/* Connection count badge */}
                                                {isHovered && getNodeEdges(node.id).length > 0 && (
                                                    <g transform={`translate(${-size * 0.7}, ${-size * 0.7})`}>
                                                        <circle r={10} fill="#8b5cf6" stroke="white" strokeWidth={1.5} />
                                                        <text
                                                            textAnchor="middle"
                                                            dominantBaseline="central"
                                                            fill="white"
                                                            fontSize={10}
                                                            fontWeight={600}
                                                        >
                                                            {getNodeEdges(node.id).length}
                                                        </text>
                                                    </g>
                                                )}
                                            </g>
                                        );
                                    })}
                                </g>
                            </svg>
                        )}
                    </div>
                </div>

                {/* Premium Settings Panel */}
                <AnimatePresence>
                    {showSettings && (
                        <motion.div
                            initial={{ width: 0, opacity: 0 }}
                            animate={{ width: 360, opacity: 1 }}
                            exit={{ width: 0, opacity: 0 }}
                            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                            className="flex-shrink-0 border-l border-white/10 bg-black/30 backdrop-blur-2xl overflow-hidden"
                        >
                            <div className="w-[360px] p-6 space-y-6">
                                <div className="flex items-center justify-between">
                                    <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                                        <Filter className="w-5 h-5 text-purple-400" />
                                        Filtreler
                                    </h2>
                                    <button
                                        onClick={() => setShowSettings(false)}
                                        className="p-1.5 rounded-lg hover:bg-white/10 transition-colors"
                                    >
                                        <X className="w-4 h-4 text-slate-400" />
                                    </button>
                                </div>

                                {/* Toggle options with premium styling */}
                                <div className="space-y-4">
                                    {[
                                        {
                                            icon: Eye,
                                            label: 'Yalnız notları göster',
                                            value: showOrphans,
                                            onChange: setShowOrphans,
                                            description: 'Bağlantısız notları göster'
                                        },
                                        {
                                            icon: Sparkles,
                                            label: 'Benzerlik bağlantıları',
                                            value: showSimilarity,
                                            onChange: setShowSimilarity,
                                            description: 'İçerik benzerliği bazlı'
                                        },
                                        {
                                            icon: Tag,
                                            label: 'Etiket bağlantıları',
                                            value: showTags,
                                            onChange: setShowTags,
                                            description: 'Ortak etiketler bazlı'
                                        }
                                    ].map(({ icon: Icon, label, value, onChange, description }) => (
                                        <motion.label
                                            key={label}
                                            className="flex items-center justify-between cursor-pointer group p-3 rounded-xl hover:bg-white/5 transition-colors"
                                            whileHover={{ x: 4 }}
                                        >
                                            <div className="flex items-center gap-3">
                                                <div className={cn(
                                                    "p-2 rounded-lg transition-colors",
                                                    value ? "bg-purple-500/20 text-purple-400" : "bg-white/5 text-slate-400"
                                                )}>
                                                    <Icon className="w-4 h-4" />
                                                </div>
                                                <div>
                                                    <span className="text-slate-200 block">{label}</span>
                                                    <span className="text-slate-500 text-xs">{description}</span>
                                                </div>
                                            </div>
                                            <div
                                                className={cn(
                                                    "w-12 h-7 rounded-full transition-all relative cursor-pointer",
                                                    value
                                                        ? "bg-gradient-to-r from-purple-500 to-pink-500"
                                                        : "bg-slate-600"
                                                )}
                                                onClick={() => onChange(!value)}
                                            >
                                                <motion.div
                                                    className="absolute top-1 w-5 h-5 rounded-full bg-white shadow-lg"
                                                    animate={{ x: value ? 26 : 4 }}
                                                    transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                                                />
                                            </div>
                                        </motion.label>
                                    ))}
                                </div>

                                {/* Premium Similarity Slider */}
                                <div className="space-y-3 p-4 rounded-xl bg-white/5">
                                    <div className="flex items-center justify-between">
                                        <span className="text-sm text-slate-300">Benzerlik eşiği</span>
                                        <span className="text-sm font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                                            {Math.round(similarityThreshold * 100)}%
                                        </span>
                                    </div>
                                    <div className="relative">
                                        <div className="absolute inset-0 h-2 rounded-full bg-slate-700 top-1/2 -translate-y-1/2" />
                                        <div
                                            className="absolute h-2 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 top-1/2 -translate-y-1/2"
                                            style={{ width: `${((similarityThreshold - 0.1) / 0.4) * 100}%` }}
                                        />
                                        <input
                                            type="range"
                                            min={0.1}
                                            max={0.5}
                                            step={0.05}
                                            value={similarityThreshold}
                                            onChange={(e) => setSimilarityThreshold(parseFloat(e.target.value))}
                                            className="relative w-full h-2 appearance-none cursor-pointer bg-transparent z-10 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:h-5 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-white [&::-webkit-slider-thumb]:shadow-lg [&::-webkit-slider-thumb]:cursor-pointer"
                                        />
                                    </div>
                                    <p className="text-xs text-slate-500">Daha düşük değer = daha fazla bağlantı</p>
                                </div>

                                {/* Selected node info */}
                                <AnimatePresence>
                                    {selectedNode && (
                                        <motion.div
                                            initial={{ opacity: 0, y: 20 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            exit={{ opacity: 0, y: 20 }}
                                            className="p-5 rounded-2xl bg-gradient-to-br from-purple-500/10 to-pink-500/10 border border-purple-500/20 space-y-4"
                                        >
                                            <div className="flex items-start justify-between">
                                                <h3 className="font-semibold text-white flex items-center gap-2">
                                                    <Info className="w-5 h-5 text-purple-400" />
                                                    Seçili Not
                                                </h3>
                                                <button
                                                    onClick={() => setSelectedNode(null)}
                                                    className="p-1 rounded-lg hover:bg-white/10 transition-colors"
                                                >
                                                    <X className="w-4 h-4 text-slate-400" />
                                                </button>
                                            </div>

                                            <p className="text-slate-200 font-medium text-lg">{selectedNode.data.title}</p>

                                            {selectedNode.data.tags && selectedNode.data.tags.length > 0 && (
                                                <div className="flex flex-wrap gap-2">
                                                    {selectedNode.data.tags.map((tag) => (
                                                        <span
                                                            key={tag}
                                                            className="px-3 py-1 rounded-full text-xs bg-purple-500/20 text-purple-300 border border-purple-500/30"
                                                        >
                                                            #{tag}
                                                        </span>
                                                    ))}
                                                </div>
                                            )}

                                            <div className="flex items-center gap-4 text-sm text-slate-400">
                                                <div className="flex items-center gap-1.5">
                                                    <Link2 className="w-4 h-4" />
                                                    <span>{getNodeEdges(selectedNode.id).length} bağlantı</span>
                                                </div>
                                                {selectedNode.data.pinned && (
                                                    <div className="flex items-center gap-1.5 text-amber-400">
                                                        <Pin className="w-4 h-4" />
                                                        <span>Sabitlenmiş</span>
                                                    </div>
                                                )}
                                            </div>

                                            <motion.button
                                                whileHover={{ scale: 1.02 }}
                                                whileTap={{ scale: 0.98 }}
                                                onClick={() => router.push(`/notes?id=${selectedNode.id}`)}
                                                className="w-full mt-2 px-4 py-3 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 text-white font-medium hover:opacity-90 transition-opacity flex items-center justify-center gap-2"
                                            >
                                                Nota Git
                                                <ExternalLink className="w-4 h-4" />
                                            </motion.button>
                                        </motion.div>
                                    )}
                                </AnimatePresence>

                                {/* Keyboard shortcuts */}
                                <div className="pt-4 border-t border-white/10">
                                    <h4 className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-3">Kısayollar</h4>
                                    <div className="space-y-2 text-sm">
                                        <div className="flex items-center justify-between text-slate-400">
                                            <span>Yakınlaştır/Uzaklaştır</span>
                                            <kbd className="px-2 py-0.5 rounded bg-white/10 text-slate-300 font-mono text-xs">Scroll</kbd>
                                        </div>
                                        <div className="flex items-center justify-between text-slate-400">
                                            <span>Kaydır</span>
                                            <kbd className="px-2 py-0.5 rounded bg-white/10 text-slate-300 font-mono text-xs">Sürükle</kbd>
                                        </div>
                                        <div className="flex items-center justify-between text-slate-400">
                                            <span>Not seç</span>
                                            <kbd className="px-2 py-0.5 rounded bg-white/10 text-slate-300 font-mono text-xs">Tıkla</kbd>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Note Details Sidebar */}
                <AnimatePresence>
                    {sidebarOpen && noteDetails && (
                        <motion.div
                            initial={{ opacity: 0, x: 400 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: 400 }}
                            className="absolute top-0 right-0 h-full w-96 z-30 bg-gradient-to-b from-slate-900/95 to-slate-800/95 backdrop-blur-2xl border-l border-white/10 shadow-2xl overflow-hidden"
                        >
                            <div className="h-full flex flex-col">
                                {/* Header */}
                                <div className="p-6 border-b border-white/10 bg-gradient-to-r from-purple-500/10 to-pink-500/10">
                                    <div className="flex items-start justify-between">
                                        <div className="flex-1">
                                            <h2 className="text-xl font-bold text-white line-clamp-2">{noteDetails.title}</h2>
                                            <div className="flex items-center gap-3 mt-2 text-sm text-slate-400">
                                                <span className="flex items-center gap-1">
                                                    <Link2 className="w-4 h-4" />
                                                    {noteDetails.connections} bağlantı
                                                </span>
                                                {noteDetails.pinned && (
                                                    <span className="flex items-center gap-1 text-amber-400">
                                                        <Pin className="w-4 h-4" />
                                                        Sabit
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                        <button
                                            onClick={() => {
                                                setSidebarOpen(false);
                                                setNoteDetails(null);
                                                setAiSummary(null);
                                            }}
                                            className="p-2 rounded-lg hover:bg-white/10 text-slate-400 hover:text-white transition-colors"
                                        >
                                            <X className="w-5 h-5" />
                                        </button>
                                    </div>
                                </div>

                                {/* Content */}
                                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                                    {/* Tags */}
                                    {noteDetails.tags && noteDetails.tags.length > 0 && (
                                        <div>
                                            <h4 className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">Etiketler</h4>
                                            <div className="flex flex-wrap gap-2">
                                                {noteDetails.tags.map((tag: string) => (
                                                    <span
                                                        key={tag}
                                                        className="px-3 py-1 rounded-full text-xs bg-purple-500/20 text-purple-300 border border-purple-500/30"
                                                    >
                                                        #{tag}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* AI Summary */}
                                    <div className="p-4 rounded-xl bg-gradient-to-br from-cyan-500/10 to-blue-500/10 border border-cyan-500/20">
                                        <div className="flex items-center justify-between mb-3">
                                            <h4 className="text-sm font-medium text-cyan-400 flex items-center gap-2">
                                                <Cpu className="w-4 h-4" />
                                                AI Özet
                                            </h4>
                                            {!aiSummary && !summaryLoading && (
                                                <button
                                                    onClick={() => fetchAISummary(noteDetails.id)}
                                                    className="text-xs px-3 py-1 rounded-lg bg-cyan-500/20 text-cyan-300 hover:bg-cyan-500/30 transition-colors"
                                                >
                                                    Oluştur
                                                </button>
                                            )}
                                        </div>
                                        {summaryLoading ? (
                                            <div className="flex items-center gap-2 text-slate-400">
                                                <div className="w-4 h-4 border-2 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin" />
                                                <span className="text-sm">AI özet oluşturuyor...</span>
                                            </div>
                                        ) : aiSummary ? (
                                            <p className="text-sm text-slate-300 leading-relaxed">{aiSummary}</p>
                                        ) : (
                                            <p className="text-sm text-slate-500 italic">
                                                AI özet için "Oluştur" butonuna tıklayın
                                            </p>
                                        )}
                                    </div>

                                    {/* Preview */}
                                    <div>
                                        <h4 className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">İçerik Önizlemesi</h4>
                                        <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                                            <p className="text-sm text-slate-400 leading-relaxed whitespace-pre-wrap">
                                                {noteDetails.preview || "İçerik yok"}
                                            </p>
                                        </div>
                                    </div>

                                    {/* Timestamps */}
                                    {(noteDetails.created_at || noteDetails.updated_at) && (
                                        <div className="text-xs text-slate-500 space-y-1">
                                            {noteDetails.created_at && (
                                                <div className="flex items-center gap-2">
                                                    <Clock className="w-3 h-3" />
                                                    Oluşturulma: {new Date(noteDetails.created_at).toLocaleDateString('tr-TR')}
                                                </div>
                                            )}
                                            {noteDetails.updated_at && (
                                                <div className="flex items-center gap-2">
                                                    <RefreshCw className="w-3 h-3" />
                                                    Güncelleme: {new Date(noteDetails.updated_at).toLocaleDateString('tr-TR')}
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>

                                {/* Actions */}
                                <div className="p-6 border-t border-white/10 space-y-3">
                                    <motion.button
                                        whileHover={{ scale: 1.02 }}
                                        whileTap={{ scale: 0.98 }}
                                        onClick={() => router.push(`/notes?id=${noteDetails.id}`)}
                                        className="w-full px-4 py-3 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 text-white font-medium hover:opacity-90 transition-opacity flex items-center justify-center gap-2"
                                    >
                                        Nota Git
                                        <ExternalLink className="w-4 h-4" />
                                    </motion.button>
                                    {pathMode && (
                                        <motion.button
                                            whileHover={{ scale: 1.02 }}
                                            whileTap={{ scale: 0.98 }}
                                            onClick={() => {
                                                if (!pathSource) {
                                                    setPathSource(noteDetails.id);
                                                } else if (!pathTarget) {
                                                    setPathTarget(noteDetails.id);
                                                    fetchPath(pathSource, noteDetails.id);
                                                }
                                                setSidebarOpen(false);
                                            }}
                                            className="w-full px-4 py-3 rounded-xl bg-cyan-500/20 text-cyan-400 font-medium hover:bg-cyan-500/30 transition-colors flex items-center justify-center gap-2 border border-cyan-500/30"
                                        >
                                            <Route className="w-4 h-4" />
                                            {!pathSource ? "Başlangıç olarak seç" : "Bitiş olarak seç"}
                                        </motion.button>
                                    )}
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Premium Filter Panel */}
                <AnimatePresence>
                    {showFilterPanel && graphData && (
                        <FilterPanel
                            selectedColors={colorFilters}
                            selectedTags={tagFilters}
                            dateRange={dateRangeFilter}
                            depthLimit={depthLimit}
                            showHeatMap={showHeatMap}
                            layout={layoutType}
                            allTags={Array.from(new Set(graphData.nodes.flatMap(n => n.data.tags || [])))}
                            onColorsChange={setColorFilters}
                            onTagsChange={setTagFilters}
                            onDateRangeChange={setDateRangeFilter}
                            onDepthLimitChange={setDepthLimit}
                            onHeatMapToggle={() => setShowHeatMap(!showHeatMap)}
                            onLayoutChange={setLayoutType}
                            onReset={() => {
                                setColorFilters([]);
                                setTagFilters([]);
                                setDateRangeFilter({});
                                setDepthLimit(0);
                                setShowHeatMap(false);
                            }}
                            onClose={() => setShowFilterPanel(false)}
                            language="tr"
                        />
                    )}
                </AnimatePresence>

                {/* Premium Export Menu */}
                <AnimatePresence>
                    {showExportMenu && graphData && (
                        <GraphExportMenu
                            graphContainerId="mind-graph-container"
                            graphData={{
                                nodes: graphData.nodes.map(n => ({
                                    id: n.id,
                                    title: n.data.title,
                                    color: n.data.color,
                                    tags: n.data.tags || [],
                                    position: n.position
                                })),
                                edges: graphData.edges.map(e => ({
                                    id: e.id,
                                    source: e.source,
                                    target: e.target,
                                    type: e.type
                                }))
                            }}
                            onClose={() => setShowExportMenu(false)}
                            language="tr"
                        />
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
}
