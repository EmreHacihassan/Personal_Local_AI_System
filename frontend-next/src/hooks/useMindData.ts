'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import type { DataSource } from '@/components/mind/DataSourceSelector';

// Types
export interface UnifiedMindNode {
  id: string;
  label: string;
  title: string;
  type: 'note' | 'document' | 'chat' | 'calendar';
  color: string;
  metadata: {
    created_at?: string;
    updated_at?: string;
    folder_id?: string;
    pinned?: boolean;
    tags?: string[];
    category?: string;
    // Chat specific
    message_count?: number;
    last_message?: string;
    // Document specific
    file_type?: string;
    file_size?: number;
    // Calendar specific
    event_date?: string;
    event_time?: string;
  };
  position?: { x: number; y: number; z: number };
  connections: string[];
}

export interface UnifiedMindEdge {
  id: string;
  source: string;
  target: string;
  type: 'wiki_link' | 'tag_based' | 'similarity' | 'temporal' | 'topic' | 'reference';
  label?: string;
  strength: number;
}

export interface UnifiedMindData {
  nodes: UnifiedMindNode[];
  edges: UnifiedMindEdge[];
  stats: {
    total_nodes: number;
    total_edges: number;
    notes_count: number;
    documents_count: number;
    chats_count: number;
    calendar_count: number;
      connected_nodes: number;
    orphan_nodes: number;
  };
}

interface UseMindDataOptions {
  activeSources: DataSource[];
  autoRefresh?: boolean;
  refreshInterval?: number;
}

interface UseMindDataReturn {
  data: UnifiedMindData | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  sourceCounts: Record<string, number>;
}

// Node color mapping
const TYPE_COLORS: Record<string, string> = {
  note: 'purple',
  document: 'blue',
  chat: 'green',
  calendar: 'orange',
};

// API fetchers
const fetchNotes = async (): Promise<UnifiedMindNode[]> => {
  try {
    const response = await fetch('/api/notes/graph');
    if (!response.ok) throw new Error('Failed to fetch notes graph');
    const data = await response.json();
    
    return (data.nodes || []).map((node: any) => ({
      id: `note-${node.id}`,
      label: node.data?.label || node.data?.title?.substring(0, 30) || 'Untitled',
      title: node.data?.title || 'Untitled',
      type: 'note' as const,
      color: node.data?.color || 'purple',
      metadata: {
        created_at: node.data?.created_at,
        updated_at: node.data?.updated_at,
        folder_id: node.data?.folder_id,
        pinned: node.data?.pinned,
        tags: node.data?.tags || [],
      },
      position: node.position,
      connections: [],
    }));
  } catch (error) {
    console.error('Error fetching notes:', error);
    return [];
  }
};

const fetchDocuments = async (): Promise<UnifiedMindNode[]> => {
  try {
    const response = await fetch('/api/documents');
    if (!response.ok) throw new Error('Failed to fetch documents');
    const data = await response.json();
    
    return (data.documents || []).map((doc: any) => ({
      id: `doc-${doc.id || doc.filename}`,
      label: (doc.filename || doc.name || 'Document').substring(0, 30),
      title: doc.filename || doc.name || 'Document',
      type: 'document' as const,
      color: 'blue',
      metadata: {
        created_at: doc.indexed_at || doc.created_at,
        file_type: doc.file_type,
        file_size: doc.size,
        tags: doc.tags || [],
      },
      position: undefined,
      connections: [],
    }));
  } catch (error) {
    console.error('Error fetching documents:', error);
    return [];
  }
};

const fetchChatSessions = async (): Promise<UnifiedMindNode[]> => {
  try {
    const response = await fetch('/api/sessions?limit=50');
    if (!response.ok) throw new Error('Failed to fetch chat sessions');
    const data = await response.json();
    
    return (data.sessions || []).map((session: any) => ({
      id: `chat-${session.id}`,
      label: (session.title || session.id || 'Chat').substring(0, 30),
      title: session.title || session.first_message?.substring(0, 50) || session.id || 'Chat Session',
      type: 'chat' as const,
      color: 'green',
      metadata: {
        created_at: session.created_at,
        updated_at: session.updated_at,
        message_count: session.message_count,
        last_message: session.last_message,
        category: session.category,
        tags: session.tags || [],
      },
      position: undefined,
      connections: [],
    }));
  } catch (error) {
    console.error('Error fetching chat sessions:', error);
    return [];
  }
};

const fetchCalendarEvents = async (): Promise<UnifiedMindNode[]> => {
  try {
    // Calendar events are stored in localStorage for TimelinePlanner
    if (typeof window === 'undefined') return [];
    
    const storedEvents = localStorage.getItem('timeline-events');
    if (!storedEvents) return [];
    
    const events = JSON.parse(storedEvents);
    
    return events.map((event: any) => ({
      id: `cal-${event.id}`,
      label: (event.title || 'Event').substring(0, 30),
      title: event.title || 'Event',
      type: 'calendar' as const,
      color: event.color || 'orange',
      metadata: {
        event_date: event.date,
        event_time: event.time,
        category: event.category,
        tags: event.tags || [],
      },
      position: undefined,
      connections: [],
    }));
  } catch (error) {
    console.error('Error fetching calendar events:', error);
    return [];
  }
};

// Find connections between nodes
const findConnections = (nodes: UnifiedMindNode[]): UnifiedMindEdge[] => {
  const edges: UnifiedMindEdge[] = [];
  const edgeSet = new Set<string>();

  nodes.forEach((node, i) => {
    const nodeTags = node.metadata.tags || [];
    
    nodes.slice(i + 1).forEach(otherNode => {
      const otherTags = otherNode.metadata.tags || [];
      
      // Tag-based connections
      const commonTags = nodeTags.filter(t => otherTags.includes(t));
      if (commonTags.length > 0) {
        const edgeId = `${node.id}-${otherNode.id}-tag`;
        if (!edgeSet.has(edgeId)) {
          edgeSet.add(edgeId);
          edges.push({
            id: edgeId,
            source: node.id,
            target: otherNode.id,
            type: 'tag_based',
            label: commonTags[0],
            strength: Math.min(1, commonTags.length * 0.3),
          });
        }
      }

      // Temporal connections (same day)
      const nodeDate = node.metadata.created_at || node.metadata.event_date;
      const otherDate = otherNode.metadata.created_at || otherNode.metadata.event_date;
      
      if (nodeDate && otherDate) {
        const d1 = new Date(nodeDate).toDateString();
        const d2 = new Date(otherDate).toDateString();
        
        if (d1 === d2 && node.type !== otherNode.type) {
          const edgeId = `${node.id}-${otherNode.id}-temporal`;
          if (!edgeSet.has(edgeId)) {
            edgeSet.add(edgeId);
            edges.push({
              id: edgeId,
              source: node.id,
              target: otherNode.id,
              type: 'temporal',
              label: 'Aynı gün',
              strength: 0.5,
            });
          }
        }
      }

      // Topic similarity (simple word matching)
      const nodeWords = new Set(node.title.toLowerCase().split(/\s+/));
      const otherWords = new Set(otherNode.title.toLowerCase().split(/\s+/));
      const commonWords = Array.from(nodeWords).filter(w => w.length > 3 && otherWords.has(w));
      
      if (commonWords.length >= 2) {
        const edgeId = `${node.id}-${otherNode.id}-topic`;
        if (!edgeSet.has(edgeId)) {
          edgeSet.add(edgeId);
          edges.push({
            id: edgeId,
            source: node.id,
            target: otherNode.id,
            type: 'topic',
            strength: Math.min(1, commonWords.length * 0.2),
          });
        }
      }
    });
  });

  return edges;
};

// Apply force-directed layout for 3D positions
const applyLayout = (nodes: UnifiedMindNode[], edges: UnifiedMindEdge[]): UnifiedMindNode[] => {
  const nodeMap = new Map(nodes.map(n => [n.id, n]));
  
  // Initial positions using golden ratio spiral
  const phi = (1 + Math.sqrt(5)) / 2; // Golden ratio
  nodes.forEach((node, i) => {
    const theta = 2 * Math.PI * i / phi;
    const radius = Math.sqrt(i + 1) * 0.3;
    
    node.position = {
      x: radius * Math.cos(theta),
      y: radius * Math.sin(theta),
      z: (Math.random() - 0.5) * 0.5,
    };
  });

  // Simple force-directed iterations
  const iterations = 50;
  const repulsion = 0.5;
  const attraction = 0.1;

  for (let iter = 0; iter < iterations; iter++) {
    const forces = new Map<string, { x: number; y: number; z: number }>();
    nodes.forEach(n => forces.set(n.id, { x: 0, y: 0, z: 0 }));

    // Repulsion between all nodes
    nodes.forEach((node, i) => {
      nodes.slice(i + 1).forEach(other => {
        const dx = (node.position?.x || 0) - (other.position?.x || 0);
        const dy = (node.position?.y || 0) - (other.position?.y || 0);
        const dz = (node.position?.z || 0) - (other.position?.z || 0);
        const dist = Math.sqrt(dx * dx + dy * dy + dz * dz) + 0.01;
        const force = repulsion / (dist * dist);

        const nodeForce = forces.get(node.id)!;
        const otherForce = forces.get(other.id)!;

        nodeForce.x += dx / dist * force;
        nodeForce.y += dy / dist * force;
        nodeForce.z += dz / dist * force;

        otherForce.x -= dx / dist * force;
        otherForce.y -= dy / dist * force;
        otherForce.z -= dz / dist * force;
      });
    });

    // Attraction along edges
    edges.forEach(edge => {
      const source = nodeMap.get(edge.source);
      const target = nodeMap.get(edge.target);
      if (!source || !target) return;

      const dx = (target.position?.x || 0) - (source.position?.x || 0);
      const dy = (target.position?.y || 0) - (source.position?.y || 0);
      const dz = (target.position?.z || 0) - (source.position?.z || 0);
      const dist = Math.sqrt(dx * dx + dy * dy + dz * dz) + 0.01;
      const force = attraction * edge.strength;

      const sourceForce = forces.get(source.id)!;
      const targetForce = forces.get(target.id)!;

      sourceForce.x += dx * force;
      sourceForce.y += dy * force;
      sourceForce.z += dz * force;

      targetForce.x -= dx * force;
      targetForce.y -= dy * force;
      targetForce.z -= dz * force;
    });

    // Apply forces with damping
    const damping = 0.9 * (1 - iter / iterations);
    nodes.forEach(node => {
      const force = forces.get(node.id)!;
      node.position = {
        x: (node.position?.x || 0) + force.x * damping,
        y: (node.position?.y || 0) + force.y * damping,
        z: (node.position?.z || 0) + force.z * damping,
      };
    });
  }

  // Group nodes by type with offset
  const typeOffsets: Record<string, { x: number; z: number }> = {
    note: { x: 0, z: 0 },
    document: { x: 1.5, z: 0 },
    chat: { x: 0, z: 1.5 },
    calendar: { x: 1.5, z: 1.5 },
  };

  nodes.forEach(node => {
    const offset = typeOffsets[node.type] || { x: 0, z: 0 };
    // Apply slight type-based offset for visual grouping
    node.position = {
      x: (node.position?.x || 0) + offset.x * 0.2,
      y: node.position?.y || 0,
      z: (node.position?.z || 0) + offset.z * 0.2,
    };
  });

  // Update connections list
  nodes.forEach(node => {
    node.connections = edges
      .filter(e => e.source === node.id || e.target === node.id)
      .map(e => e.source === node.id ? e.target : e.source);
  });

  return nodes;
};

export function useMindData({ 
  activeSources, 
  autoRefresh = false, 
  refreshInterval = 30000 
}: UseMindDataOptions): UseMindDataReturn {
  const [data, setData] = useState<UnifiedMindData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sourceCounts, setSourceCounts] = useState<Record<string, number>>({});

  const activeSourceIds = useMemo(() => 
    activeSources.filter(s => s.isActive).map(s => s.id),
    [activeSources]
  );

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const fetchPromises: Promise<UnifiedMindNode[]>[] = [];
      
      if (activeSourceIds.includes('notes')) {
        fetchPromises.push(fetchNotes());
      }
      if (activeSourceIds.includes('documents')) {
        fetchPromises.push(fetchDocuments());
      }
      if (activeSourceIds.includes('chat')) {
        fetchPromises.push(fetchChatSessions());
      }
      if (activeSourceIds.includes('calendar')) {
        fetchPromises.push(fetchCalendarEvents());
      }

      const results = await Promise.all(fetchPromises);
      const allNodes = results.flat();
      
      // Calculate source counts
      const counts: Record<string, number> = {
        notes: allNodes.filter(n => n.type === 'note').length,
        documents: allNodes.filter(n => n.type === 'document').length,
        chat: allNodes.filter(n => n.type === 'chat').length,
        calendar: allNodes.filter(n => n.type === 'calendar').length,
      };
      setSourceCounts(counts);

      // Find connections
      const edges = findConnections(allNodes);
      
      // Apply layout
      const layoutedNodes = applyLayout(allNodes, edges);

      // Calculate stats
      const connectedIds = new Set(edges.flatMap(e => [e.source, e.target]));
      
      setData({
        nodes: layoutedNodes,
        edges,
        stats: {
          total_nodes: layoutedNodes.length,
          total_edges: edges.length,
          notes_count: counts.notes,
          documents_count: counts.documents,
          chats_count: counts.chat,
          calendar_count: counts.calendar,
          connected_nodes: connectedIds.size,
          orphan_nodes: layoutedNodes.length - connectedIds.size,
        },
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch mind data');
    } finally {
      setLoading(false);
    }
  }, [activeSourceIds]);

  // Initial fetch
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Auto refresh
  useEffect(() => {
    if (!autoRefresh) return;
    
    const interval = setInterval(fetchData, refreshInterval);
    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, fetchData]);

  return {
    data,
    loading,
    error,
    refresh: fetchData,
    sourceCounts,
  };
}

export default useMindData;
