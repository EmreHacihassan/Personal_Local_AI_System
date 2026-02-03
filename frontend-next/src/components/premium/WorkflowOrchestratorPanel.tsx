'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Workflow,
  Play,
  Pause,
  Square,
  Plus,
  Trash2,
  Save,
  FolderOpen,
  Copy,
  Settings,
  Zap,
  ArrowRight,
  Circle,
  MessageSquare,
  Code,
  FileText,
  Search,
  Database,
  Image,
  Mic,
  Send,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  Edit,
  Eye,
  Calendar,
  Filter,
  Download,
  Upload,
  GitBranch,
  Layers,
  X,
} from 'lucide-react';

interface WorkflowNode {
  id: string;
  type: string;
  name: string;
  config: Record<string, any>;
  position: { x: number; y: number };
}

interface WorkflowEdge {
  id: string;
  source_node: string;
  source_port: string;
  target_node: string;
  target_port: string;
}

interface Workflow {
  id: string;
  name: string;
  description: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  status: string;
  category: string;
  tags: string[];
  version: string;
  created_at: string;
  updated_at: string;
}

interface Execution {
  id: string;
  workflow_id: string;
  status: string;
  started_at: string;
  completed_at?: string;
  results?: Record<string, any>;
}

interface NodeType {
  id: string;
  name: string;
  description: string;
  category: string;
  icon: string;
  inputs: string[];
  outputs: string[];
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const NODE_ICONS: Record<string, React.ComponentType<any>> = {
  text_input: MessageSquare,
  file_input: FileText,
  llm_chat: Zap,
  llm_complete: Zap,
  rag_query: Database,
  code_execute: Code,
  vision_analyze: Image,
  voice_stt: Mic,
  output: Send,
  condition: GitBranch,
  loop: RefreshCw,
  start: Play,
  end: Square,
};

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-gray-500',
  active: 'bg-green-500',
  running: 'bg-blue-500',
  completed: 'bg-green-500',
  failed: 'bg-red-500',
  paused: 'bg-yellow-500',
};

export function WorkflowOrchestratorPanel() {
  const [activeTab, setActiveTab] = useState<'workflows' | 'builder' | 'executions' | 'templates'>('workflows');
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | null>(null);
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [nodeTypes, setNodeTypes] = useState<NodeType[]>([]);
  const [templates, setTemplates] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [executing, setExecuting] = useState(false);

  // Builder state
  const [nodes, setNodes] = useState<WorkflowNode[]>([]);
  const [edges, setEdges] = useState<WorkflowEdge[]>([]);
  const [selectedNode, setSelectedNode] = useState<WorkflowNode | null>(null);
  const [workflowName, setWorkflowName] = useState('New Workflow');
  const [workflowDescription, setWorkflowDescription] = useState('');

  const canvasRef = useRef<HTMLDivElement>(null);

  // Load data
  const loadWorkflows = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/workflows?limit=50`);
      if (res.ok) {
        const data = await res.json();
        setWorkflows(data.workflows || []);
      }
    } catch (err) {
      setError('Failed to load workflows');
    } finally {
      setLoading(false);
    }
  }, []);

  const loadNodeTypes = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/workflow-orchestrator/nodes/types`);
      if (res.ok) {
        const data = await res.json();
        setNodeTypes(data.node_types || []);
      }
    } catch (err) {
      console.error('Failed to load node types');
    }
  }, []);

  const loadTemplates = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/workflow-orchestrator/templates`);
      if (res.ok) {
        const data = await res.json();
        setTemplates(data.templates || []);
      }
    } catch (err) {
      console.error('Failed to load templates');
    }
  }, []);

  useEffect(() => {
    loadWorkflows();
    loadNodeTypes();
    loadTemplates();
  }, [loadWorkflows, loadNodeTypes, loadTemplates]);

  // Workflow operations
  const createWorkflow = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/workflows`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: workflowName,
          description: workflowDescription,
          nodes: nodes.map(n => ({
            node_type: n.type,
            name: n.name,
            config: n.config,
            position: n.position,
          })),
          edges: edges.map(e => ({
            source_node: e.source_node,
            source_port: e.source_port,
            target_node: e.target_node,
            target_port: e.target_port,
          })),
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setWorkflows([...workflows, data.workflow]);
        setActiveTab('workflows');
      }
    } catch (err) {
      setError('Failed to create workflow');
    }
  };

  const deleteWorkflow = async (id: string) => {
    try {
      await fetch(`${API_BASE}/api/workflows/${id}`, { method: 'DELETE' });
      setWorkflows(workflows.filter(w => w.id !== id));
    } catch (err) {
      setError('Failed to delete workflow');
    }
  };

  const duplicateWorkflow = async (id: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/workflows/${id}/duplicate`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setWorkflows([...workflows, data.workflow]);
      }
    } catch (err) {
      setError('Failed to duplicate workflow');
    }
  };

  const executeWorkflow = async (id: string) => {
    setExecuting(true);
    try {
      const res = await fetch(`${API_BASE}/api/workflows/${id}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ inputs: {}, options: {} }),
      });
      if (res.ok) {
        const data = await res.json();
        setExecutions([data.execution, ...executions]);
      }
    } catch (err) {
      setError('Failed to execute workflow');
    } finally {
      setExecuting(false);
    }
  };

  const loadExecutions = async (workflowId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/workflows/${workflowId}/executions`);
      if (res.ok) {
        const data = await res.json();
        setExecutions(data.executions || []);
      }
    } catch (err) {
      console.error('Failed to load executions');
    }
  };

  // Builder operations
  const addNode = (type: string) => {
    const nodeType = nodeTypes.find(t => t.id === type);
    const newNode: WorkflowNode = {
      id: `node_${Date.now()}`,
      type,
      name: nodeType?.name || type,
      config: {},
      position: { x: 200 + Math.random() * 200, y: 100 + Math.random() * 200 },
    };
    setNodes([...nodes, newNode]);
  };

  const removeNode = (id: string) => {
    setNodes(nodes.filter(n => n.id !== id));
    setEdges(edges.filter(e => e.source_node !== id && e.target_node !== id));
    if (selectedNode?.id === id) setSelectedNode(null);
  };

  const connectNodes = (sourceId: string, targetId: string) => {
    const newEdge: WorkflowEdge = {
      id: `edge_${Date.now()}`,
      source_node: sourceId,
      source_port: 'output',
      target_node: targetId,
      target_port: 'input',
    };
    setEdges([...edges, newEdge]);
  };

  const openWorkflowInBuilder = (workflow: Workflow) => {
    setWorkflowName(workflow.name);
    setWorkflowDescription(workflow.description);
    setNodes(workflow.nodes);
    setEdges(workflow.edges);
    setSelectedWorkflow(workflow);
    setActiveTab('builder');
  };

  const tabs = [
    { id: 'workflows', label: 'My Workflows', icon: Layers },
    { id: 'builder', label: 'Builder', icon: Plus },
    { id: 'executions', label: 'Executions', icon: Play },
    { id: 'templates', label: 'Templates', icon: FolderOpen },
  ];

  return (
    <div className="h-full flex flex-col bg-background">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500">
            <Workflow className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold">Advanced Workflow Orchestration</h2>
            <p className="text-sm text-muted-foreground">
              Design and execute AI pipelines visually
            </p>
          </div>
        </div>

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
            {activeTab === 'workflows' && (
              <motion.div
                key="workflows"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-4"
              >
                {/* Actions */}
                <div className="flex items-center justify-between">
                  <div className="flex gap-2">
                    <button
                      onClick={() => {
                        setNodes([]);
                        setEdges([]);
                        setWorkflowName('New Workflow');
                        setWorkflowDescription('');
                        setSelectedWorkflow(null);
                        setActiveTab('builder');
                      }}
                      className="px-4 py-2 bg-primary text-primary-foreground rounded-lg flex items-center gap-2"
                    >
                      <Plus className="w-4 h-4" /> New Workflow
                    </button>
                    <button
                      onClick={loadWorkflows}
                      className="px-4 py-2 bg-secondary rounded-lg"
                    >
                      <RefreshCw className="w-4 h-4" />
                    </button>
                  </div>
                  <div className="flex gap-2">
                    <select className="px-3 py-2 bg-secondary rounded-lg border border-border text-sm">
                      <option value="">All Categories</option>
                      <option value="data">Data Processing</option>
                      <option value="ai">AI Tasks</option>
                      <option value="automation">Automation</option>
                    </select>
                  </div>
                </div>

                {/* Workflows Grid */}
                {workflows.length === 0 ? (
                  <div className="text-center p-12 bg-secondary rounded-xl">
                    <Workflow className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
                    <h3 className="text-lg font-semibold mb-2">No Workflows Yet</h3>
                    <p className="text-muted-foreground mb-4">
                      Create your first AI workflow to get started
                    </p>
                    <button
                      onClick={() => setActiveTab('builder')}
                      className="px-4 py-2 bg-primary text-primary-foreground rounded-lg"
                    >
                      Create Workflow
                    </button>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {workflows.map(workflow => (
                      <div
                        key={workflow.id}
                        className="bg-card rounded-xl p-4 border border-border hover:border-primary/50 transition-all"
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center gap-2">
                            <div className={`w-2 h-2 rounded-full ${STATUS_COLORS[workflow.status]}`} />
                            <span className="text-xs text-muted-foreground capitalize">
                              {workflow.status}
                            </span>
                          </div>
                          <span className="text-xs text-muted-foreground">v{workflow.version}</span>
                        </div>

                        <h3 className="font-semibold mb-1">{workflow.name}</h3>
                        <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
                          {workflow.description || 'No description'}
                        </p>

                        <div className="flex items-center gap-2 mb-4 text-xs text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <Circle className="w-3 h-3" /> {workflow.nodes?.length || 0} nodes
                          </span>
                          <span className="flex items-center gap-1">
                            <ArrowRight className="w-3 h-3" /> {workflow.edges?.length || 0} edges
                          </span>
                        </div>

                        <div className="flex gap-2">
                          <button
                            onClick={() => executeWorkflow(workflow.id)}
                            disabled={executing}
                            className="flex-1 px-3 py-1.5 bg-primary text-primary-foreground rounded-lg text-sm flex items-center justify-center gap-1"
                          >
                            <Play className="w-3 h-3" /> Run
                          </button>
                          <button
                            onClick={() => openWorkflowInBuilder(workflow)}
                            className="px-3 py-1.5 bg-secondary rounded-lg text-sm"
                          >
                            <Edit className="w-3 h-3" />
                          </button>
                          <button
                            onClick={() => duplicateWorkflow(workflow.id)}
                            className="px-3 py-1.5 bg-secondary rounded-lg text-sm"
                          >
                            <Copy className="w-3 h-3" />
                          </button>
                          <button
                            onClick={() => deleteWorkflow(workflow.id)}
                            className="px-3 py-1.5 bg-destructive/10 text-destructive rounded-lg text-sm"
                          >
                            <Trash2 className="w-3 h-3" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </motion.div>
            )}

            {activeTab === 'builder' && (
              <motion.div
                key="builder"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="h-full flex gap-4"
              >
                {/* Node Palette */}
                <div className="w-64 bg-card rounded-xl p-4 border border-border">
                  <h3 className="font-semibold mb-4">Nodes</h3>
                  <div className="space-y-2">
                    {/* Node categories */}
                    {['input', 'ai', 'processing', 'output', 'control'].map(category => (
                      <div key={category} className="space-y-1">
                        <h4 className="text-xs font-medium text-muted-foreground uppercase">
                          {category}
                        </h4>
                        <div className="space-y-1">
                          {nodeTypes
                            .filter(t => t.category === category)
                            .map(type => {
                              const Icon = NODE_ICONS[type.id] || Circle;
                              return (
                                <button
                                  key={type.id}
                                  onClick={() => addNode(type.id)}
                                  className="w-full px-3 py-2 bg-secondary hover:bg-secondary/80 rounded-lg text-sm flex items-center gap-2 text-left"
                                >
                                  <Icon className="w-4 h-4" />
                                  {type.name}
                                </button>
                              );
                            })}
                        </div>
                      </div>
                    ))}

                    {/* Quick add common nodes */}
                    <div className="border-t border-border pt-3 mt-3">
                      <h4 className="text-xs font-medium text-muted-foreground uppercase mb-2">
                        Quick Add
                      </h4>
                      <div className="grid grid-cols-2 gap-1">
                        {['start', 'llm_chat', 'output', 'condition'].map(type => (
                          <button
                            key={type}
                            onClick={() => addNode(type)}
                            className="px-2 py-1.5 bg-primary/10 hover:bg-primary/20 rounded text-xs"
                          >
                            + {type.replace('_', ' ')}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Canvas */}
                <div className="flex-1 flex flex-col">
                  {/* Toolbar */}
                  <div className="flex items-center justify-between mb-4 bg-card rounded-lg p-3 border border-border">
                    <div className="flex items-center gap-3">
                      <input
                        type="text"
                        value={workflowName}
                        onChange={e => setWorkflowName(e.target.value)}
                        className="bg-transparent text-lg font-semibold outline-none"
                        placeholder="Workflow Name"
                      />
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={createWorkflow}
                        className="px-4 py-1.5 bg-primary text-primary-foreground rounded-lg text-sm flex items-center gap-2"
                      >
                        <Save className="w-4 h-4" /> Save
                      </button>
                      <button
                        onClick={() => executeWorkflow(selectedWorkflow?.id || '')}
                        disabled={!selectedWorkflow || executing}
                        className="px-4 py-1.5 bg-green-600 text-white rounded-lg text-sm flex items-center gap-2 disabled:opacity-50"
                      >
                        <Play className="w-4 h-4" /> Run
                      </button>
                    </div>
                  </div>

                  {/* Canvas Area */}
                  <div
                    ref={canvasRef}
                    className="flex-1 bg-card rounded-xl border border-border relative overflow-auto"
                    style={{
                      backgroundImage: 'radial-gradient(circle, hsl(var(--border)) 1px, transparent 1px)',
                      backgroundSize: '20px 20px',
                    }}
                  >
                    {nodes.length === 0 ? (
                      <div className="absolute inset-0 flex items-center justify-center">
                        <div className="text-center">
                          <Workflow className="w-12 h-12 mx-auto mb-3 text-muted-foreground" />
                          <p className="text-muted-foreground">
                            Drag nodes from the palette to start building
                          </p>
                        </div>
                      </div>
                    ) : (
                      <>
                        {/* Edges */}
                        <svg className="absolute inset-0 w-full h-full pointer-events-none">
                          {edges.map(edge => {
                            const source = nodes.find(n => n.id === edge.source_node);
                            const target = nodes.find(n => n.id === edge.target_node);
                            if (!source || !target) return null;

                            const x1 = source.position.x + 100;
                            const y1 = source.position.y + 30;
                            const x2 = target.position.x;
                            const y2 = target.position.y + 30;

                            return (
                              <path
                                key={edge.id}
                                d={`M ${x1} ${y1} C ${x1 + 50} ${y1}, ${x2 - 50} ${y2}, ${x2} ${y2}`}
                                stroke="hsl(var(--primary))"
                                strokeWidth="2"
                                fill="none"
                                strokeDasharray="5,5"
                              />
                            );
                          })}
                        </svg>

                        {/* Nodes */}
                        {nodes.map(node => {
                          const Icon = NODE_ICONS[node.type] || Circle;
                          return (
                            <div
                              key={node.id}
                              className={`absolute bg-card rounded-lg border-2 p-3 shadow-lg cursor-move min-w-[120px] ${
                                selectedNode?.id === node.id
                                  ? 'border-primary'
                                  : 'border-border'
                              }`}
                              style={{
                                left: node.position.x,
                                top: node.position.y,
                              }}
                              onClick={() => setSelectedNode(node)}
                            >
                              <div className="flex items-center gap-2">
                                <div className="p-1.5 bg-primary/10 rounded">
                                  <Icon className="w-4 h-4 text-primary" />
                                </div>
                                <span className="text-sm font-medium">{node.name}</span>
                              </div>

                              {/* Connection points */}
                              <div className="absolute left-0 top-1/2 -translate-x-1/2 -translate-y-1/2 w-3 h-3 bg-secondary border-2 border-border rounded-full" />
                              <div className="absolute right-0 top-1/2 translate-x-1/2 -translate-y-1/2 w-3 h-3 bg-primary border-2 border-primary rounded-full" />

                              {/* Delete button */}
                              <button
                                onClick={e => {
                                  e.stopPropagation();
                                  removeNode(node.id);
                                }}
                                className="absolute -top-2 -right-2 w-5 h-5 bg-destructive text-destructive-foreground rounded-full flex items-center justify-center text-xs"
                              >
                                ×
                              </button>
                            </div>
                          );
                        })}
                      </>
                    )}
                  </div>
                </div>

                {/* Properties Panel */}
                {selectedNode && (
                  <div className="w-72 bg-card rounded-xl p-4 border border-border">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="font-semibold">Node Properties</h3>
                      <button
                        onClick={() => setSelectedNode(null)}
                        className="p-1 hover:bg-secondary rounded"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>

                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium mb-1">Name</label>
                        <input
                          type="text"
                          value={selectedNode.name}
                          onChange={e => {
                            const updated = nodes.map(n =>
                              n.id === selectedNode.id ? { ...n, name: e.target.value } : n
                            );
                            setNodes(updated);
                            setSelectedNode({ ...selectedNode, name: e.target.value });
                          }}
                          className="w-full p-2 rounded-lg bg-secondary border border-border text-sm"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium mb-1">Type</label>
                        <input
                          type="text"
                          value={selectedNode.type}
                          disabled
                          className="w-full p-2 rounded-lg bg-secondary/50 border border-border text-sm"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium mb-1">Configuration</label>
                        <textarea
                          value={JSON.stringify(selectedNode.config, null, 2)}
                          onChange={e => {
                            try {
                              const config = JSON.parse(e.target.value);
                              const updated = nodes.map(n =>
                                n.id === selectedNode.id ? { ...n, config } : n
                              );
                              setNodes(updated);
                              setSelectedNode({ ...selectedNode, config });
                            } catch {}
                          }}
                          className="w-full p-2 rounded-lg bg-secondary border border-border text-sm font-mono resize-none h-32"
                        />
                      </div>

                      {/* Connect to */}
                      <div>
                        <label className="block text-sm font-medium mb-1">Connect to</label>
                        <select
                          onChange={e => {
                            if (e.target.value) {
                              connectNodes(selectedNode.id, e.target.value);
                            }
                          }}
                          className="w-full p-2 rounded-lg bg-secondary border border-border text-sm"
                          value=""
                        >
                          <option value="">Select node...</option>
                          {nodes
                            .filter(n => n.id !== selectedNode.id)
                            .map(n => (
                              <option key={n.id} value={n.id}>
                                {n.name}
                              </option>
                            ))}
                        </select>
                      </div>
                    </div>
                  </div>
                )}
              </motion.div>
            )}

            {activeTab === 'executions' && (
              <motion.div
                key="executions"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-4"
              >
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold">Recent Executions</h3>
                  <button
                    onClick={() => workflows[0] && loadExecutions(workflows[0].id)}
                    className="px-3 py-1.5 bg-secondary rounded-lg text-sm"
                  >
                    <RefreshCw className="w-4 h-4" />
                  </button>
                </div>

                {executions.length === 0 ? (
                  <div className="text-center p-12 bg-secondary rounded-xl">
                    <Play className="w-12 h-12 mx-auto mb-3 text-muted-foreground" />
                    <p className="text-muted-foreground">No executions yet</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {executions.map(exec => (
                      <div
                        key={exec.id}
                        className="bg-card rounded-xl p-4 border border-border"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            {exec.status === 'completed' && (
                              <CheckCircle className="w-5 h-5 text-green-500" />
                            )}
                            {exec.status === 'failed' && (
                              <XCircle className="w-5 h-5 text-red-500" />
                            )}
                            {exec.status === 'running' && (
                              <RefreshCw className="w-5 h-5 text-blue-500 animate-spin" />
                            )}
                            <div>
                              <p className="font-medium">{exec.id}</p>
                              <p className="text-xs text-muted-foreground">
                                {new Date(exec.started_at).toLocaleString()}
                              </p>
                            </div>
                          </div>
                          <span
                            className={`px-2 py-1 rounded text-xs ${
                              exec.status === 'completed'
                                ? 'bg-green-500/20 text-green-500'
                                : exec.status === 'failed'
                                ? 'bg-red-500/20 text-red-500'
                                : 'bg-blue-500/20 text-blue-500'
                            }`}
                          >
                            {exec.status}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </motion.div>
            )}

            {activeTab === 'templates' && (
              <motion.div
                key="templates"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-4"
              >
                <h3 className="font-semibold">Workflow Templates</h3>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {templates.map((template, i) => (
                    <div
                      key={i}
                      className="bg-gradient-to-br from-primary/10 to-primary/5 rounded-xl p-4 border border-primary/20 hover:border-primary/40 transition-all cursor-pointer"
                      onClick={() => {
                        // Create from template
                      }}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <Workflow className="w-5 h-5 text-primary" />
                        <span className="font-medium">{template.name}</span>
                      </div>
                      <p className="text-sm text-muted-foreground mb-3">
                        {template.description}
                      </p>
                      <button className="w-full px-3 py-1.5 bg-primary/20 hover:bg-primary/30 rounded-lg text-sm text-primary">
                        Use Template
                      </button>
                    </div>
                  ))}

                  {/* Placeholder templates */}
                  {templates.length === 0 && (
                    <>
                      {[
                        { name: 'RAG Pipeline', desc: 'Document ingestion → Chunking → Embedding → Query' },
                        { name: 'Research Agent', desc: 'Web search → Summarize → Report generation' },
                        { name: 'Code Review', desc: 'Code analysis → Security scan → Suggestions' },
                        { name: 'Content Generator', desc: 'Topic research → Outline → Draft → Polish' },
                      ].map((t, i) => (
                        <div
                          key={i}
                          className="bg-gradient-to-br from-primary/10 to-primary/5 rounded-xl p-4 border border-primary/20"
                        >
                          <div className="flex items-center gap-2 mb-2">
                            <Workflow className="w-5 h-5 text-primary" />
                            <span className="font-medium">{t.name}</span>
                          </div>
                          <p className="text-sm text-muted-foreground mb-3">{t.desc}</p>
                          <button className="w-full px-3 py-1.5 bg-primary/20 hover:bg-primary/30 rounded-lg text-sm text-primary">
                            Use Template
                          </button>
                        </div>
                      ))}
                    </>
                  )}
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

export default WorkflowOrchestratorPanel;
