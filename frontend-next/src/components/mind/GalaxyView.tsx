'use client';

import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { motion, AnimatePresence, useMotionValue, useTransform, useSpring } from 'framer-motion';
import dynamic from 'next/dynamic';
import type { ComponentType } from 'react';
import { cn } from '@/lib/utils';

// Dynamic icon imports
const Orbit = dynamic(() => import('lucide-react').then(mod => mod.Orbit), { ssr: false }) as ComponentType<any>;
const Box = dynamic(() => import('lucide-react').then(mod => mod.Box), { ssr: false }) as ComponentType<any>;
const RotateCcw = dynamic(() => import('lucide-react').then(mod => mod.RotateCcw), { ssr: false }) as ComponentType<any>;
const Maximize2 = dynamic(() => import('lucide-react').then(mod => mod.Maximize2), { ssr: false }) as ComponentType<any>;
const ZoomIn = dynamic(() => import('lucide-react').then(mod => mod.ZoomIn), { ssr: false }) as ComponentType<any>;
const ZoomOut = dynamic(() => import('lucide-react').then(mod => mod.ZoomOut), { ssr: false }) as ComponentType<any>;
const Play = dynamic(() => import('lucide-react').then(mod => mod.Play), { ssr: false }) as ComponentType<any>;
const Pause = dynamic(() => import('lucide-react').then(mod => mod.Pause), { ssr: false }) as ComponentType<any>;
const Sparkles = dynamic(() => import('lucide-react').then(mod => mod.Sparkles), { ssr: false }) as ComponentType<any>;
const Star = dynamic(() => import('lucide-react').then(mod => mod.Star), { ssr: false }) as ComponentType<any>;

// Types
interface GalaxyNode {
  id: string;
  x: number;
  y: number;
  z: number;
  size: number;
  color: string;
  glow: string;
  label: string;
  type: 'note' | 'document' | 'chat' | 'calendar';
  connections: string[];
}

interface GalaxyEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  strength: number;
}

// Projected edge with full node references (source and target are nodes, not strings)
interface ProjectedGalaxyEdge {
  id: string;
  type: string;
  strength: number;
  source: {
    id: string;
    x: number;
    y: number;
    z: number;
    size: number;
    color: string;
    glow: string;
    label: string;
    type: 'note' | 'document' | 'chat' | 'calendar';
    connections: string[];
    projected: { x: number; y: number; scale: number };
    depth: number;
  };
  target: {
    id: string;
    x: number;
    y: number;
    z: number;
    size: number;
    color: string;
    glow: string;
    label: string;
    type: 'note' | 'document' | 'chat' | 'calendar';
    connections: string[];
    projected: { x: number; y: number; scale: number };
    depth: number;
  };
}

interface Particle3D {
  id: number;
  x: number;
  y: number;
  z: number;
  size: number;
  opacity: number;
  speed: number;
  color: string;
}

interface GalaxyViewProps {
  nodes: GalaxyNode[];
  edges: GalaxyEdge[];
  onNodeClick?: (nodeId: string) => void;
  onNodeHover?: (nodeId: string | null) => void;
  selectedNodeId?: string | null;
  hoveredNodeId?: string | null;
  className?: string;
  autoRotate?: boolean;
}

// Premium star colors for different node types
const TYPE_COLORS: Record<string, { color: string; glow: string; gradient: string }> = {
  note: { 
    color: '#a855f7', 
    glow: 'rgba(168, 85, 247, 0.6)',
    gradient: 'from-violet-400 to-purple-600'
  },
  document: { 
    color: '#3b82f6', 
    glow: 'rgba(59, 130, 246, 0.6)',
    gradient: 'from-blue-400 to-cyan-600'
  },
  chat: { 
    color: '#10b981', 
    glow: 'rgba(16, 185, 129, 0.6)',
    gradient: 'from-emerald-400 to-teal-600'
  },
  calendar: { 
    color: '#f59e0b', 
    glow: 'rgba(245, 158, 11, 0.6)',
    gradient: 'from-amber-400 to-orange-600'
  },
};

// Generate cosmic particles
const generateParticles = (count: number): Particle3D[] => {
  return Array.from({ length: count }, (_, i) => ({
    id: i,
    x: (Math.random() - 0.5) * 2000,
    y: (Math.random() - 0.5) * 2000,
    z: (Math.random() - 0.5) * 1000,
    size: Math.random() * 2 + 0.5,
    opacity: Math.random() * 0.5 + 0.2,
    speed: Math.random() * 0.5 + 0.1,
    color: ['#ffffff', '#a855f7', '#3b82f6', '#10b981', '#f59e0b'][Math.floor(Math.random() * 5)],
  }));
};

// 3D projection utilities
const project3D = (
  x: number, 
  y: number, 
  z: number, 
  centerX: number, 
  centerY: number, 
  focalLength: number = 800
): { x: number; y: number; scale: number } => {
  const scale = focalLength / (focalLength + z);
  return {
    x: centerX + x * scale,
    y: centerY + y * scale,
    scale: Math.max(0.1, Math.min(2, scale)),
  };
};

// Rotate point in 3D space
const rotate3D = (
  x: number, 
  y: number, 
  z: number, 
  angleX: number, 
  angleY: number
): { x: number; y: number; z: number } => {
  // Rotate around Y axis
  const cosY = Math.cos(angleY);
  const sinY = Math.sin(angleY);
  const x1 = x * cosY - z * sinY;
  const z1 = x * sinY + z * cosY;

  // Rotate around X axis
  const cosX = Math.cos(angleX);
  const sinX = Math.sin(angleX);
  const y1 = y * cosX - z1 * sinX;
  const z2 = y * sinX + z1 * cosX;

  return { x: x1, y: y1, z: z2 };
};

export const GalaxyView: React.FC<GalaxyViewProps> = ({
  nodes,
  edges,
  onNodeClick,
  onNodeHover,
  selectedNodeId,
  hoveredNodeId,
  className = '',
  autoRotate = true,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const animationRef = useRef<number>(0);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [rotation, setRotation] = useState({ x: 0, y: 0 });
  const [isPaused, setIsPaused] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [particles] = useState(() => generateParticles(150));
  const [isDragging, setIsDragging] = useState(false);
  const dragStart = useRef({ x: 0, y: 0, rotX: 0, rotY: 0 });

  // Spring animations for smooth rotation
  const rotationX = useSpring(rotation.x, { stiffness: 100, damping: 30 });
  const rotationY = useSpring(rotation.y, { stiffness: 100, damping: 30 });

  // Update dimensions on resize
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight,
        });
      }
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  // Auto-rotation animation
  useEffect(() => {
    if (!autoRotate || isPaused || isDragging) {
      cancelAnimationFrame(animationRef.current);
      return;
    }

    let lastTime = performance.now();
    const animate = (time: number) => {
      const delta = (time - lastTime) / 1000;
      lastTime = time;

      setRotation(prev => ({
        x: prev.x,
        y: prev.y + delta * 0.1, // Slow rotation
      }));

      animationRef.current = requestAnimationFrame(animate);
    };

    animationRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animationRef.current);
  }, [autoRotate, isPaused, isDragging]);

  // Mouse drag handlers
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    setIsDragging(true);
    dragStart.current = {
      x: e.clientX,
      y: e.clientY,
      rotX: rotation.x,
      rotY: rotation.y,
    };
  }, [rotation]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!isDragging) return;

    const deltaX = (e.clientX - dragStart.current.x) * 0.005;
    const deltaY = (e.clientY - dragStart.current.y) * 0.005;

    setRotation({
      x: dragStart.current.rotX + deltaY,
      y: dragStart.current.rotY + deltaX,
    });
  }, [isDragging]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  // Calculate projected positions
  const projectedNodes = useMemo(() => {
    const centerX = dimensions.width / 2;
    const centerY = dimensions.height / 2;

    return nodes.map(node => {
      const rotated = rotate3D(
        node.x * zoom * 200,
        node.y * zoom * 200,
        node.z * zoom * 200,
        rotation.x,
        rotation.y
      );
      const projected = project3D(rotated.x, rotated.y, rotated.z, centerX, centerY);

      return {
        ...node,
        projected,
        depth: rotated.z,
      };
    }).sort((a, b) => b.depth - a.depth); // Sort by depth for proper layering
  }, [nodes, rotation, dimensions, zoom]);

  // Project particles
  const projectedParticles = useMemo(() => {
    const centerX = dimensions.width / 2;
    const centerY = dimensions.height / 2;

    return particles.map(particle => {
      const rotated = rotate3D(
        particle.x,
        particle.y,
        particle.z,
        rotation.x * 0.3, // Particles rotate slower
        rotation.y * 0.3
      );
      const projected = project3D(rotated.x, rotated.y, rotated.z, centerX, centerY, 1200);

      return {
        ...particle,
        projected,
      };
    });
  }, [particles, rotation, dimensions]);

  // Project edges with proper type narrowing
  const projectedEdges = useMemo((): ProjectedGalaxyEdge[] => {
    const results: ProjectedGalaxyEdge[] = [];
    
    for (const edge of edges) {
      const sourceNode = projectedNodes.find(n => n.id === edge.source);
      const targetNode = projectedNodes.find(n => n.id === edge.target);

      if (sourceNode && targetNode) {
        results.push({
          id: edge.id,
          type: edge.type,
          strength: edge.strength,
          source: sourceNode,
          target: targetNode,
        });
      }
    }
    
    return results;
  }, [edges, projectedNodes]);

  const resetView = () => {
    setRotation({ x: 0, y: 0 });
    setZoom(1);
  };

  return (
    <div
      ref={containerRef}
      className={cn(
        "relative w-full h-full overflow-hidden",
        "bg-gradient-to-br from-slate-950 via-indigo-950 to-slate-950",
        isDragging ? "cursor-grabbing" : "cursor-grab",
        className
      )}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      {/* Cosmic Background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Nebula gradients */}
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-[100px] animate-pulse" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-[100px] animate-pulse" style={{ animationDelay: '1s' }} />
        <div className="absolute top-1/2 left-1/2 w-64 h-64 bg-cyan-500/10 rounded-full blur-[80px] animate-pulse" style={{ animationDelay: '2s' }} />
      </div>

      {/* SVG Canvas */}
      <svg
        className="absolute inset-0 w-full h-full"
        viewBox={`0 0 ${dimensions.width} ${dimensions.height}`}
      >
        <defs>
          {/* Glow filters for each type */}
          {Object.entries(TYPE_COLORS).map(([type, colors]) => (
            <React.Fragment key={type}>
              <radialGradient id={`star-gradient-${type}`} cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor={colors.color} stopOpacity="1" />
                <stop offset="50%" stopColor={colors.color} stopOpacity="0.5" />
                <stop offset="100%" stopColor={colors.color} stopOpacity="0" />
              </radialGradient>
              <filter id={`glow-${type}`} x="-100%" y="-100%" width="300%" height="300%">
                <feGaussianBlur stdDeviation="4" result="blur" />
                <feFlood floodColor={colors.color} floodOpacity="0.5" result="color" />
                <feComposite in="color" in2="blur" operator="in" result="shadow" />
                <feMerge>
                  <feMergeNode in="shadow" />
                  <feMergeNode in="shadow" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </React.Fragment>
          ))}

          {/* Edge gradient */}
          <linearGradient id="edge-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="white" stopOpacity="0" />
            <stop offset="50%" stopColor="white" stopOpacity="0.3" />
            <stop offset="100%" stopColor="white" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* Background stars/particles */}
        {projectedParticles.map(particle => (
          <circle
            key={particle.id}
            cx={particle.projected.x}
            cy={particle.projected.y}
            r={particle.size * particle.projected.scale}
            fill={particle.color}
            opacity={particle.opacity * particle.projected.scale}
          />
        ))}

        {/* Edges */}
        {projectedEdges.map((edge, index) => {
          const isHighlighted = hoveredNodeId === edge.source.id || hoveredNodeId === edge.target.id;
          
          return (
            <g key={edge.id || index}>
              <line
                x1={edge.source.projected.x}
                y1={edge.source.projected.y}
                x2={edge.target.projected.x}
                y2={edge.target.projected.y}
                stroke={isHighlighted ? '#a855f7' : 'rgba(255,255,255,0.1)'}
                strokeWidth={isHighlighted ? 2 : 1}
                strokeOpacity={isHighlighted ? 0.8 : 0.3}
              />
              
              {/* Animated particle along edge */}
              {isHighlighted && (
                <circle r="3" fill="#a855f7">
                  <animateMotion
                    dur="2s"
                    repeatCount="indefinite"
                    path={`M${edge.source.projected.x},${edge.source.projected.y} L${edge.target.projected.x},${edge.target.projected.y}`}
                  />
                </circle>
              )}
            </g>
          );
        })}

        {/* Nodes as stars */}
        {projectedNodes.map(node => {
          const typeColor = TYPE_COLORS[node.type] || TYPE_COLORS.note;
          const isSelected = selectedNodeId === node.id;
          const isHovered = hoveredNodeId === node.id;
          const baseSize = (node.size || 1) * 15 * node.projected.scale;
          const size = isHovered ? baseSize * 1.3 : isSelected ? baseSize * 1.2 : baseSize;

          return (
            <g
              key={node.id}
              transform={`translate(${node.projected.x}, ${node.projected.y})`}
              onClick={() => onNodeClick?.(node.id)}
              onMouseEnter={() => onNodeHover?.(node.id)}
              onMouseLeave={() => onNodeHover?.(null)}
              style={{ cursor: 'pointer' }}
            >
              {/* Outer glow */}
              <circle
                r={size * 2}
                fill={`url(#star-gradient-${node.type})`}
                opacity={isHovered || isSelected ? 0.8 : 0.3}
              />

              {/* Selection ring */}
              {isSelected && (
                <circle
                  r={size * 1.5}
                  fill="none"
                  stroke={typeColor.color}
                  strokeWidth="2"
                  strokeDasharray="4 2"
                  opacity="0.8"
                >
                  <animateTransform
                    attributeName="transform"
                    type="rotate"
                    from="0"
                    to="360"
                    dur="4s"
                    repeatCount="indefinite"
                  />
                </circle>
              )}

              {/* Core star */}
              <circle
                r={size}
                fill={typeColor.color}
                filter={`url(#glow-${node.type})`}
              />

              {/* Inner highlight */}
              <circle
                r={size * 0.5}
                fill="white"
                opacity="0.5"
              />

              {/* Label */}
              {(isHovered || isSelected) && (
                <g>
                  <rect
                    x={size + 8}
                    y={-12}
                    width={node.label.length * 7 + 16}
                    height={24}
                    rx="4"
                    fill="rgba(0,0,0,0.8)"
                    stroke={typeColor.color}
                    strokeWidth="1"
                  />
                  <text
                    x={size + 16}
                    y={4}
                    fill="white"
                    fontSize="12"
                    fontWeight="500"
                  >
                    {node.label}
                  </text>
                </g>
              )}
            </g>
          );
        })}
      </svg>

      {/* Control Panel */}
      <motion.div
        className="absolute top-4 right-4 flex flex-col gap-2"
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
      >
        <div className="backdrop-blur-xl bg-black/40 rounded-xl p-2 border border-white/10 flex flex-col gap-1">
          {/* Play/Pause */}
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={() => setIsPaused(!isPaused)}
            className="p-2 rounded-lg hover:bg-white/10 transition-colors text-white"
            title={isPaused ? 'Başlat' : 'Durdur'}
          >
            {isPaused ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
          </motion.button>

          {/* Reset view */}
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={resetView}
            className="p-2 rounded-lg hover:bg-white/10 transition-colors text-white"
            title="Görünümü sıfırla"
          >
            <RotateCcw className="w-4 h-4" />
          </motion.button>

          {/* Zoom controls */}
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={() => setZoom(z => Math.min(2, z + 0.2))}
            className="p-2 rounded-lg hover:bg-white/10 transition-colors text-white"
            title="Yakınlaştır"
          >
            <ZoomIn className="w-4 h-4" />
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={() => setZoom(z => Math.max(0.3, z - 0.2))}
            className="p-2 rounded-lg hover:bg-white/10 transition-colors text-white"
            title="Uzaklaştır"
          >
            <ZoomOut className="w-4 h-4" />
          </motion.button>
        </div>
      </motion.div>

      {/* Mode Indicator */}
      <motion.div
        className="absolute top-4 left-4 flex items-center gap-2 backdrop-blur-xl bg-black/40 rounded-xl px-3 py-2 border border-white/10"
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
      >
        <Orbit className="w-4 h-4 text-purple-400" />
        <span className="text-sm font-medium text-white">3D Galaxy View</span>
        <Sparkles className="w-3 h-3 text-yellow-400 animate-pulse" />
      </motion.div>

      {/* Legend */}
      <motion.div
        className="absolute bottom-4 left-4 backdrop-blur-xl bg-black/40 rounded-xl p-3 border border-white/10"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="flex flex-wrap gap-3 text-xs">
          {Object.entries(TYPE_COLORS).map(([type, colors]) => (
            <div key={type} className="flex items-center gap-1.5">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: colors.color, boxShadow: `0 0 8px ${colors.glow}` }}
              />
              <span className="text-slate-300 capitalize">{type === 'note' ? 'Notlar' : type === 'document' ? 'Dökümanlar' : type === 'chat' ? 'Sohbet' : 'Takvim'}</span>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Stats */}
      <motion.div
        className="absolute bottom-4 right-4 backdrop-blur-xl bg-black/40 rounded-xl px-3 py-2 border border-white/10"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="flex items-center gap-4 text-xs text-slate-300">
          <div className="flex items-center gap-1">
            <Star className="w-3 h-3 text-purple-400" />
            <span>{nodes.length} düğüm</span>
          </div>
          <div className="flex items-center gap-1">
            <Box className="w-3 h-3 text-blue-400" />
            <span>{edges.length} bağlantı</span>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default GalaxyView;
