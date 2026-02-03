'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Network,
  Search,
  Plus,
  Trash2,
  Edit,
  Eye,
  Link2,
  Unlink,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Filter,
  Download,
  Upload,
  RefreshCw,
  Sparkles,
  FileText,
  Users,
  Building,
  MapPin,
  Calendar,
  Lightbulb,
  ArrowRight,
  Circle,
  Target,
  GitMerge,
  BarChart3,
  AlertCircle,
  CheckCircle,
  X,
} from 'lucide-react';

interface Entity {
  id: string;
  name: string;
  type: string;
  properties: Record<string, any>;
  description?: string;
  connection_count?: number;
}

interface Relationship {
  id: string;
  source_id: string;
  target_id: string;
  type: string;
  weight: number;
}

interface GraphStats {
  total_entities: number;
  total_relationships: number;
  entity_types: Record<string, number>;
  relationship_types: Record<string, number>;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const ENTITY_ICONS: Record<string, React.ComponentType<any>> = {
  person: Users,
  organization: Building,
  location: MapPin,
  event: Calendar,
  concept: Lightbulb,
  document: FileText,
  default: Circle,
};

const ENTITY_COLORS: Record<string, string> = {
  person: '#3B82F6',
  organization: '#10B981',
  location: '#F59E0B',
  event: '#8B5CF6',
  concept: '#EC4899',
  document: '#6366F1',
  default: '#6B7280',
};

export function KnowledgeGraphPanel() {
  const [activeTab, setActiveTab] = useState<'graph' | 'entities' | 'extract' | 'analyze'>('graph');
  const [entities, setEntities] = useState<Entity[]>([]);
  const [relationships, setRelationships] = useState<Relationship[]>([]);
  const [stats, setStats] = useState<GraphStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Graph view state
  const [selectedEntity, setSelectedEntity] = useState<Entity | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<string>('');
  const [zoom, setZoom] = useState(1);

  // Entity form state
  const [showEntityForm, setShowEntityForm] = useState(false);
  const [entityForm, setEntityForm] = useState({
    name: '',
    type: 'concept',
    description: '',
    properties: '{}',
  });

  // Extraction state
  const [extractText, setExtractText] = useState('');
  const [extracting, setExtracting] = useState(false);
  const [extractionResult, setExtractionResult] = useState<any>(null);

  // Query state
  const [nlQuery, setNlQuery] = useState('');
  const [queryResult, setQueryResult] = useState<any>(null);

  const canvasRef = useRef<HTMLDivElement>(null);

  // Load data
  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      // Load entities
      const entitiesRes = await fetch(`${API_BASE}/api/knowledge-graph/entities?limit=100`);
      if (entitiesRes.ok) {
        const data = await entitiesRes.json();
        setEntities(data.entities || []);
      }

      // Load relationships
      const relRes = await fetch(`${API_BASE}/api/knowledge-graph/relationships?limit=200`);
      if (relRes.ok) {
        const data = await relRes.json();
        setRelationships(data.relationships || []);
      }

      // Load stats
      const statsRes = await fetch(`${API_BASE}/api/knowledge-graph/stats`);
      if (statsRes.ok) {
        const data = await statsRes.json();
        setStats(data.stats);
      }
    } catch (err) {
      setError('Failed to load knowledge graph data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Entity operations
  const createEntity = async () => {
    try {
      let properties = {};
      try {
        properties = JSON.parse(entityForm.properties);
      } catch {}

      const res = await fetch(`${API_BASE}/api/knowledge-graph/entities`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: entityForm.name,
          entity_type: entityForm.type,
          description: entityForm.description,
          properties,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setEntities([...entities, data.entity]);
        setShowEntityForm(false);
        setEntityForm({ name: '', type: 'concept', description: '', properties: '{}' });
      }
    } catch (err) {
      setError('Failed to create entity');
    }
  };

  const deleteEntity = async (id: string) => {
    try {
      await fetch(`${API_BASE}/api/knowledge-graph/entities/${id}`, {
        method: 'DELETE',
      });
      setEntities(entities.filter(e => e.id !== id));
      setRelationships(relationships.filter(r => r.source_id !== id && r.target_id !== id));
      if (selectedEntity?.id === id) setSelectedEntity(null);
    } catch (err) {
      setError('Failed to delete entity');
    }
  };

  // Extraction
  const extractFromText = async () => {
    if (!extractText.trim()) return;
    setExtracting(true);
    setExtractionResult(null);
    try {
      const res = await fetch(`${API_BASE}/api/knowledge-graph/extract/text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: extractText,
          extract_relationships: true,
          min_confidence: 0.5,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setExtractionResult(data.extraction);
        // Reload to show new entities
        loadData();
      }
    } catch (err) {
      setError('Failed to extract entities');
    } finally {
      setExtracting(false);
    }
  };

  // Natural language query
  const queryGraph = async () => {
    if (!nlQuery.trim()) return;
    try {
      const res = await fetch(`${API_BASE}/api/knowledge-graph/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: nlQuery,
          max_hops: 2,
          include_paths: true,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setQueryResult(data.result);
      }
    } catch (err) {
      setError('Failed to query graph');
    }
  };

  // Find central entities
  const findCentralEntities = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/knowledge-graph/analyze/central-entities?metric=degree&limit=10`);
      if (res.ok) {
        const data = await res.json();
        return data.entities;
      }
    } catch (err) {
      console.error('Failed to find central entities');
    }
    return [];
  };

  // Filter entities
  const filteredEntities = entities.filter(e => {
    const matchesSearch = !searchQuery || 
      e.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      e.type.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = !filterType || e.type === filterType;
    return matchesSearch && matchesType;
  });

  const entityTypes = Array.from(new Set(entities.map(e => e.type)));

  const tabs = [
    { id: 'graph', label: 'Graph View', icon: Network },
    { id: 'entities', label: 'Entities', icon: Circle },
    { id: 'extract', label: 'Extract', icon: Sparkles },
    { id: 'analyze', label: 'Analyze', icon: BarChart3 },
  ];

  return (
    <div className="h-full flex flex-col bg-background">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500">
            <Network className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold">Enterprise Knowledge Graph</h2>
            <p className="text-sm text-muted-foreground">
              LLM-powered entity extraction and relationship mapping
            </p>
          </div>
        </div>

        {/* Stats */}
        {stats && (
          <div className="grid grid-cols-4 gap-4 mb-4">
            <div className="bg-card rounded-lg p-3 border border-border">
              <div className="text-2xl font-bold text-primary">{stats.total_entities}</div>
              <div className="text-xs text-muted-foreground">Entities</div>
            </div>
            <div className="bg-card rounded-lg p-3 border border-border">
              <div className="text-2xl font-bold text-green-500">{stats.total_relationships}</div>
              <div className="text-xs text-muted-foreground">Relationships</div>
            </div>
            <div className="bg-card rounded-lg p-3 border border-border">
              <div className="text-2xl font-bold text-purple-500">
                {Object.keys(stats.entity_types || {}).length}
              </div>
              <div className="text-xs text-muted-foreground">Entity Types</div>
            </div>
            <div className="bg-card rounded-lg p-3 border border-border">
              <div className="text-2xl font-bold text-orange-500">
                {Object.keys(stats.relationship_types || {}).length}
              </div>
              <div className="text-xs text-muted-foreground">Relationship Types</div>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-2">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === tab.id
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-secondary hover:bg-secondary/80 text-secondary-foreground'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-4">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <RefreshCw className="w-8 h-8 animate-spin text-primary" />
          </div>
        ) : (
          <AnimatePresence mode="wait">
            {activeTab === 'graph' && (
              <motion.div
                key="graph"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="h-full flex gap-4"
              >
                {/* Graph Canvas */}
                <div className="flex-1 flex flex-col">
                  {/* Toolbar */}
                  <div className="flex items-center justify-between mb-4 bg-card rounded-lg p-3 border border-border">
                    <div className="flex items-center gap-2">
                      <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                        <input
                          type="text"
                          value={searchQuery}
                          onChange={e => setSearchQuery(e.target.value)}
                          placeholder="Search entities..."
                          className="pl-10 pr-4 py-1.5 bg-secondary rounded-lg border border-border text-sm w-64"
                        />
                      </div>
                      <select
                        value={filterType}
                        onChange={e => setFilterType(e.target.value)}
                        className="px-3 py-1.5 bg-secondary rounded-lg border border-border text-sm"
                      >
                        <option value="">All Types</option>
                        {entityTypes.map(type => (
                          <option key={type} value={type}>{type}</option>
                        ))}
                      </select>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setZoom(z => Math.max(0.5, z - 0.1))}
                        className="p-1.5 bg-secondary rounded hover:bg-secondary/80"
                      >
                        <ZoomOut className="w-4 h-4" />
                      </button>
                      <span className="text-sm">{Math.round(zoom * 100)}%</span>
                      <button
                        onClick={() => setZoom(z => Math.min(2, z + 0.1))}
                        className="p-1.5 bg-secondary rounded hover:bg-secondary/80"
                      >
                        <ZoomIn className="w-4 h-4" />
                      </button>
                      <button
                        onClick={loadData}
                        className="p-1.5 bg-secondary rounded hover:bg-secondary/80"
                      >
                        <RefreshCw className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  {/* Canvas */}
                  <div
                    ref={canvasRef}
                    className="flex-1 bg-card rounded-xl border border-border relative overflow-auto"
                    style={{
                      backgroundImage: 'radial-gradient(circle, hsl(var(--border)) 1px, transparent 1px)',
                      backgroundSize: '20px 20px',
                    }}
                  >
                    {filteredEntities.length === 0 ? (
                      <div className="absolute inset-0 flex items-center justify-center">
                        <div className="text-center">
                          <Network className="w-12 h-12 mx-auto mb-3 text-muted-foreground" />
                          <p className="text-muted-foreground">
                            No entities yet. Extract from text or add manually.
                          </p>
                        </div>
                      </div>
                    ) : (
                      <div style={{ transform: `scale(${zoom})`, transformOrigin: 'top left' }}>
                        {/* Edges */}
                        <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ minWidth: '2000px', minHeight: '1000px' }}>
                          {relationships.map(rel => {
                            const source = filteredEntities.find(e => e.id === rel.source_id);
                            const target = filteredEntities.find(e => e.id === rel.target_id);
                            if (!source || !target) return null;

                            const sourceIdx = filteredEntities.indexOf(source);
                            const targetIdx = filteredEntities.indexOf(target);
                            
                            const cols = 5;
                            const x1 = 100 + (sourceIdx % cols) * 200 + 60;
                            const y1 = 80 + Math.floor(sourceIdx / cols) * 120 + 30;
                            const x2 = 100 + (targetIdx % cols) * 200 + 60;
                            const y2 = 80 + Math.floor(targetIdx / cols) * 120 + 30;

                            return (
                              <g key={rel.id}>
                                <line
                                  x1={x1}
                                  y1={y1}
                                  x2={x2}
                                  y2={y2}
                                  stroke="hsl(var(--primary))"
                                  strokeWidth={rel.weight * 2}
                                  strokeOpacity={0.5}
                                  markerEnd="url(#arrowhead)"
                                />
                                <text
                                  x={(x1 + x2) / 2}
                                  y={(y1 + y2) / 2 - 5}
                                  fontSize="10"
                                  fill="hsl(var(--muted-foreground))"
                                  textAnchor="middle"
                                >
                                  {rel.type}
                                </text>
                              </g>
                            );
                          })}
                          <defs>
                            <marker
                              id="arrowhead"
                              markerWidth="10"
                              markerHeight="7"
                              refX="9"
                              refY="3.5"
                              orient="auto"
                            >
                              <polygon
                                points="0 0, 10 3.5, 0 7"
                                fill="hsl(var(--primary))"
                              />
                            </marker>
                          </defs>
                        </svg>

                        {/* Nodes */}
                        {filteredEntities.map((entity, idx) => {
                          const Icon = ENTITY_ICONS[entity.type] || ENTITY_ICONS.default;
                          const color = ENTITY_COLORS[entity.type] || ENTITY_COLORS.default;
                          const cols = 5;
                          const x = 100 + (idx % cols) * 200;
                          const y = 80 + Math.floor(idx / cols) * 120;

                          return (
                            <div
                              key={entity.id}
                              className={`absolute bg-card rounded-xl border-2 p-3 shadow-lg cursor-pointer transition-all hover:scale-105 ${
                                selectedEntity?.id === entity.id
                                  ? 'border-primary ring-2 ring-primary/20'
                                  : 'border-border'
                              }`}
                              style={{ left: x, top: y, minWidth: '120px' }}
                              onClick={() => setSelectedEntity(entity)}
                            >
                              <div className="flex items-center gap-2">
                                <div
                                  className="p-1.5 rounded-lg"
                                  style={{ backgroundColor: `${color}20` }}
                                >
                                  <Icon className="w-4 h-4" style={{ color }} />
                                </div>
                                <div className="flex-1 min-w-0">
                                  <p className="text-sm font-medium truncate">{entity.name}</p>
                                  <p className="text-xs text-muted-foreground">{entity.type}</p>
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                </div>

                {/* Details Panel */}
                {selectedEntity && (
                  <div className="w-80 bg-card rounded-xl p-4 border border-border">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="font-semibold">Entity Details</h3>
                      <button
                        onClick={() => setSelectedEntity(null)}
                        className="p-1 hover:bg-secondary rounded"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>

                    <div className="space-y-4">
                      <div className="flex items-center gap-3">
                        {(() => {
                          const Icon = ENTITY_ICONS[selectedEntity.type] || ENTITY_ICONS.default;
                          const color = ENTITY_COLORS[selectedEntity.type] || ENTITY_COLORS.default;
                          return (
                            <div
                              className="p-3 rounded-xl"
                              style={{ backgroundColor: `${color}20` }}
                            >
                              <Icon className="w-6 h-6" style={{ color }} />
                            </div>
                          );
                        })()}
                        <div>
                          <h4 className="font-semibold">{selectedEntity.name}</h4>
                          <span className="text-sm text-muted-foreground capitalize">
                            {selectedEntity.type}
                          </span>
                        </div>
                      </div>

                      {selectedEntity.description && (
                        <div>
                          <label className="text-xs font-medium text-muted-foreground">
                            Description
                          </label>
                          <p className="text-sm">{selectedEntity.description}</p>
                        </div>
                      )}

                      {Object.keys(selectedEntity.properties || {}).length > 0 && (
                        <div>
                          <label className="text-xs font-medium text-muted-foreground">
                            Properties
                          </label>
                          <div className="mt-1 space-y-1">
                            {Object.entries(selectedEntity.properties).map(([key, value]) => (
                              <div key={key} className="flex justify-between text-sm">
                                <span className="text-muted-foreground">{key}</span>
                                <span>{String(value)}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Related entities */}
                      <div>
                        <label className="text-xs font-medium text-muted-foreground">
                          Related Entities
                        </label>
                        <div className="mt-2 space-y-2">
                          {relationships
                            .filter(r => r.source_id === selectedEntity.id || r.target_id === selectedEntity.id)
                            .slice(0, 5)
                            .map(rel => {
                              const otherId = rel.source_id === selectedEntity.id ? rel.target_id : rel.source_id;
                              const other = entities.find(e => e.id === otherId);
                              if (!other) return null;
                              
                              return (
                                <div
                                  key={rel.id}
                                  className="flex items-center gap-2 p-2 bg-secondary rounded-lg cursor-pointer"
                                  onClick={() => setSelectedEntity(other)}
                                >
                                  <ArrowRight className="w-3 h-3" />
                                  <span className="text-xs text-muted-foreground">{rel.type}</span>
                                  <span className="text-sm">{other.name}</span>
                                </div>
                              );
                            })}
                        </div>
                      </div>

                      <div className="flex gap-2 pt-4 border-t border-border">
                        <button
                          onClick={() => deleteEntity(selectedEntity.id)}
                          className="flex-1 px-3 py-1.5 bg-destructive/10 text-destructive rounded-lg text-sm"
                        >
                          <Trash2 className="w-4 h-4 inline mr-1" /> Delete
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </motion.div>
            )}

            {activeTab === 'entities' && (
              <motion.div
                key="entities"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-4"
              >
                {/* Actions */}
                <div className="flex items-center justify-between">
                  <button
                    onClick={() => setShowEntityForm(true)}
                    className="px-4 py-2 bg-primary text-primary-foreground rounded-lg flex items-center gap-2"
                  >
                    <Plus className="w-4 h-4" /> Add Entity
                  </button>
                  <div className="flex gap-2">
                    <select
                      value={filterType}
                      onChange={e => setFilterType(e.target.value)}
                      className="px-3 py-2 bg-secondary rounded-lg border border-border text-sm"
                    >
                      <option value="">All Types</option>
                      {entityTypes.map(type => (
                        <option key={type} value={type}>{type}</option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Entity Form Modal */}
                {showEntityForm && (
                  <div className="bg-card rounded-xl p-6 border border-border">
                    <h3 className="text-lg font-semibold mb-4">Create Entity</h3>
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium mb-1">Name</label>
                        <input
                          type="text"
                          value={entityForm.name}
                          onChange={e => setEntityForm({ ...entityForm, name: e.target.value })}
                          className="w-full p-2 rounded-lg bg-secondary border border-border"
                          placeholder="Entity name"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium mb-1">Type</label>
                        <select
                          value={entityForm.type}
                          onChange={e => setEntityForm({ ...entityForm, type: e.target.value })}
                          className="w-full p-2 rounded-lg bg-secondary border border-border"
                        >
                          <option value="person">Person</option>
                          <option value="organization">Organization</option>
                          <option value="location">Location</option>
                          <option value="event">Event</option>
                          <option value="concept">Concept</option>
                          <option value="document">Document</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium mb-1">Description</label>
                        <textarea
                          value={entityForm.description}
                          onChange={e => setEntityForm({ ...entityForm, description: e.target.value })}
                          className="w-full p-2 rounded-lg bg-secondary border border-border resize-none h-20"
                          placeholder="Description..."
                        />
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={createEntity}
                          disabled={!entityForm.name.trim()}
                          className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-lg disabled:opacity-50"
                        >
                          Create
                        </button>
                        <button
                          onClick={() => setShowEntityForm(false)}
                          className="px-4 py-2 bg-secondary rounded-lg"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {/* Entities Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {filteredEntities.map(entity => {
                    const Icon = ENTITY_ICONS[entity.type] || ENTITY_ICONS.default;
                    const color = ENTITY_COLORS[entity.type] || ENTITY_COLORS.default;

                    return (
                      <div
                        key={entity.id}
                        className="bg-card rounded-xl p-4 border border-border hover:border-primary/50 transition-all"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex items-center gap-3">
                            <div
                              className="p-2 rounded-lg"
                              style={{ backgroundColor: `${color}20` }}
                            >
                              <Icon className="w-5 h-5" style={{ color }} />
                            </div>
                            <div>
                              <h4 className="font-medium">{entity.name}</h4>
                              <span className="text-sm text-muted-foreground capitalize">
                                {entity.type}
                              </span>
                            </div>
                          </div>
                          <button
                            onClick={() => deleteEntity(entity.id)}
                            className="p-1.5 hover:bg-destructive/10 rounded text-destructive"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                        {entity.description && (
                          <p className="mt-2 text-sm text-muted-foreground line-clamp-2">
                            {entity.description}
                          </p>
                        )}
                      </div>
                    );
                  })}
                </div>
              </motion.div>
            )}

            {activeTab === 'extract' && (
              <motion.div
                key="extract"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-6"
              >
                {/* Text Extraction */}
                <div className="bg-gradient-to-r from-emerald-500/10 to-teal-500/10 rounded-xl p-6 border border-emerald-500/20">
                  <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <Sparkles className="w-5 h-5" /> LLM-Powered Entity Extraction
                  </h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    Paste text and let AI automatically extract entities and relationships
                  </p>
                  <textarea
                    value={extractText}
                    onChange={e => setExtractText(e.target.value)}
                    placeholder="Paste your text here... AI will extract entities and relationships automatically."
                    className="w-full p-4 rounded-lg bg-background border border-border resize-none h-48"
                  />
                  <button
                    onClick={extractFromText}
                    disabled={!extractText.trim() || extracting}
                    className="mt-4 px-6 py-2 bg-primary text-primary-foreground rounded-lg flex items-center gap-2 disabled:opacity-50"
                  >
                    {extracting ? (
                      <>
                        <RefreshCw className="w-4 h-4 animate-spin" /> Extracting...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4" /> Extract Entities
                      </>
                    )}
                  </button>
                </div>

                {/* Extraction Results */}
                {extractionResult && (
                  <div className="bg-card rounded-xl p-6 border border-border">
                    <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                      <CheckCircle className="w-5 h-5 text-green-500" /> Extraction Results
                    </h3>
                    <div className="grid grid-cols-2 gap-6">
                      <div>
                        <h4 className="font-medium mb-2">
                          Entities Found ({extractionResult.entities?.length || 0})
                        </h4>
                        <div className="space-y-2 max-h-64 overflow-auto">
                          {extractionResult.entities?.map((e: any, i: number) => (
                            <div key={i} className="p-2 bg-secondary rounded-lg text-sm">
                              <span className="font-medium">{e.name}</span>
                              <span className="text-muted-foreground ml-2">({e.type})</span>
                            </div>
                          ))}
                        </div>
                      </div>
                      <div>
                        <h4 className="font-medium mb-2">
                          Relationships Found ({extractionResult.relationships?.length || 0})
                        </h4>
                        <div className="space-y-2 max-h-64 overflow-auto">
                          {extractionResult.relationships?.map((r: any, i: number) => (
                            <div key={i} className="p-2 bg-secondary rounded-lg text-sm flex items-center gap-2">
                              <span>{r.source}</span>
                              <ArrowRight className="w-3 h-3" />
                              <span className="text-primary">{r.type}</span>
                              <ArrowRight className="w-3 h-3" />
                              <span>{r.target}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Natural Language Query */}
                <div className="bg-card rounded-xl p-6 border border-border">
                  <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <Search className="w-5 h-5" /> Query Knowledge Graph
                  </h3>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={nlQuery}
                      onChange={e => setNlQuery(e.target.value)}
                      onKeyDown={e => e.key === 'Enter' && queryGraph()}
                      placeholder="Ask a question about your knowledge graph..."
                      className="flex-1 p-3 rounded-lg bg-secondary border border-border"
                    />
                    <button
                      onClick={queryGraph}
                      disabled={!nlQuery.trim()}
                      className="px-6 py-3 bg-primary text-primary-foreground rounded-lg disabled:opacity-50"
                    >
                      Query
                    </button>
                  </div>

                  {queryResult && (
                    <div className="mt-4 p-4 bg-secondary rounded-lg">
                      <h4 className="font-medium mb-2">Answer:</h4>
                      <p className="text-sm">{queryResult.answer || JSON.stringify(queryResult)}</p>
                    </div>
                  )}
                </div>
              </motion.div>
            )}

            {activeTab === 'analyze' && (
              <motion.div
                key="analyze"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-6"
              >
                {/* Entity Types Distribution */}
                <div className="bg-card rounded-xl p-6 border border-border">
                  <h3 className="text-lg font-semibold mb-4">Entity Type Distribution</h3>
                  <div className="space-y-3">
                    {Object.entries(stats?.entity_types || {}).map(([type, count]) => {
                      const total = stats?.total_entities || 1;
                      const percentage = (count / total) * 100;
                      const color = ENTITY_COLORS[type] || ENTITY_COLORS.default;

                      return (
                        <div key={type}>
                          <div className="flex justify-between text-sm mb-1">
                            <span className="capitalize">{type}</span>
                            <span>{count} ({percentage.toFixed(1)}%)</span>
                          </div>
                          <div className="w-full h-2 bg-secondary rounded-full overflow-hidden">
                            <div
                              className="h-full rounded-full"
                              style={{ width: `${percentage}%`, backgroundColor: color }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Quick Actions */}
                <div className="grid grid-cols-2 gap-4">
                  <button
                    onClick={findCentralEntities}
                    className="bg-card rounded-xl p-6 border border-border hover:border-primary/50 transition-all text-left"
                  >
                    <Target className="w-8 h-8 mb-3 text-primary" />
                    <h4 className="font-semibold mb-1">Find Central Entities</h4>
                    <p className="text-sm text-muted-foreground">
                      Identify the most connected and important entities
                    </p>
                  </button>

                  <button
                    onClick={() => {/* Find orphans */}}
                    className="bg-card rounded-xl p-6 border border-border hover:border-primary/50 transition-all text-left"
                  >
                    <AlertCircle className="w-8 h-8 mb-3 text-orange-500" />
                    <h4 className="font-semibold mb-1">Find Orphan Entities</h4>
                    <p className="text-sm text-muted-foreground">
                      Entities with no relationships
                    </p>
                  </button>

                  <button
                    onClick={() => {/* Detect clusters */}}
                    className="bg-card rounded-xl p-6 border border-border hover:border-primary/50 transition-all text-left"
                  >
                    <GitMerge className="w-8 h-8 mb-3 text-purple-500" />
                    <h4 className="font-semibold mb-1">Detect Clusters</h4>
                    <p className="text-sm text-muted-foreground">
                      Find groups of related entities
                    </p>
                  </button>

                  <button
                    onClick={() => {/* Find gaps */}}
                    className="bg-card rounded-xl p-6 border border-border hover:border-primary/50 transition-all text-left"
                  >
                    <Lightbulb className="w-8 h-8 mb-3 text-yellow-500" />
                    <h4 className="font-semibold mb-1">Knowledge Gaps</h4>
                    <p className="text-sm text-muted-foreground">
                      Identify missing relationships and entities
                    </p>
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        )}

        {error && (
          <div className="mt-4 p-4 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive text-sm">
            {error}
          </div>
        )}
      </div>
    </div>
  );
}

export default KnowledgeGraphPanel;
