'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Bot,
  Plus,
  Search,
  Star,
  Download,
  Trash2,
  Play,
  Pause,
  Settings,
  Users,
  Code,
  Sparkles,
  Briefcase,
  MessageSquare,
  FileSearch,
  PenTool,
  Calculator,
  Database,
  Globe,
  Image,
  Mic,
  Shield,
  Zap,
  RefreshCw,
  Copy,
  Check,
  X,
  ChevronRight,
  Filter,
  Grid3X3,
  List,
  BarChart3,
  Clock,
  Heart,
  Share2,
  GitBranch,
} from 'lucide-react';

interface AgentTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  capabilities: string[];
  parameters: Record<string, any>;
  icon?: string;
  rating?: number;
  downloads?: number;
  is_featured?: boolean;
}

interface CustomAgent {
  id: string;
  name: string;
  description: string;
  base_template: string;
  custom_instructions: string;
  capabilities: string[];
  parameters: Record<string, any>;
  status: 'active' | 'paused' | 'draft';
  created_at: string;
  usage_count?: number;
}

interface AgentTeam {
  id: string;
  name: string;
  description: string;
  agents: string[];
  orchestration_strategy: string;
  status: 'active' | 'inactive';
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

const CATEGORY_ICONS: Record<string, React.ComponentType<any>> = {
  research: FileSearch,
  writing: PenTool,
  analysis: Calculator,
  coding: Code,
  data: Database,
  web: Globe,
  vision: Image,
  voice: Mic,
  security: Shield,
  assistant: MessageSquare,
  default: Bot,
};

const CATEGORY_COLORS: Record<string, string> = {
  research: '#3B82F6',
  writing: '#10B981',
  analysis: '#F59E0B',
  coding: '#8B5CF6',
  data: '#EC4899',
  web: '#6366F1',
  vision: '#14B8A6',
  voice: '#F97316',
  security: '#EF4444',
  assistant: '#0EA5E9',
  default: '#6B7280',
};

export function AgentMarketplacePanel() {
  const [activeTab, setActiveTab] = useState<'marketplace' | 'my-agents' | 'teams' | 'builder'>('marketplace');
  const [templates, setTemplates] = useState<AgentTemplate[]>([]);
  const [myAgents, setMyAgents] = useState<CustomAgent[]>([]);
  const [teams, setTeams] = useState<AgentTeam[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filter & View
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  // Agent Builder State
  const [builderStep, setBuilderStep] = useState(1);
  const [selectedTemplate, setSelectedTemplate] = useState<AgentTemplate | null>(null);
  const [agentForm, setAgentForm] = useState({
    name: '',
    description: '',
    instructions: '',
    capabilities: [] as string[],
    temperature: 0.7,
    maxTokens: 2048,
    model: 'qwen3:4b',
  });

  // Team Builder
  const [showTeamBuilder, setShowTeamBuilder] = useState(false);
  const [teamForm, setTeamForm] = useState({
    name: '',
    description: '',
    agents: [] as string[],
    strategy: 'sequential',
  });

  // Selected Item
  const [selectedAgent, setSelectedAgent] = useState<CustomAgent | null>(null);
  const [showAgentDetails, setShowAgentDetails] = useState(false);

  // Load data
  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      // Load templates
      const templatesRes = await fetch(`${API_BASE}/api/agents/templates`);
      if (templatesRes.ok) {
        const data = await templatesRes.json();
        setTemplates(data.templates || []);
      }

      // Load my agents
      const agentsRes = await fetch(`${API_BASE}/api/agents/custom`);
      if (agentsRes.ok) {
        const data = await agentsRes.json();
        setMyAgents(data.agents || []);
      }

      // Load teams
      const teamsRes = await fetch(`${API_BASE}/api/agents/teams`);
      if (teamsRes.ok) {
        const data = await teamsRes.json();
        setTeams(data.teams || []);
      }
    } catch (err) {
      setError('Failed to load data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Create agent
  const createAgent = async () => {
    if (!agentForm.name.trim() || !selectedTemplate) return;
    try {
      const res = await fetch(`${API_BASE}/api/agents/custom`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: agentForm.name,
          description: agentForm.description,
          base_template: selectedTemplate.id,
          custom_instructions: agentForm.instructions,
          capabilities: agentForm.capabilities,
          parameters: {
            temperature: agentForm.temperature,
            max_tokens: agentForm.maxTokens,
            model: agentForm.model,
          },
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setMyAgents([...myAgents, data.agent]);
        setActiveTab('my-agents');
        resetBuilder();
      }
    } catch (err) {
      setError('Failed to create agent');
    }
  };

  // Delete agent
  const deleteAgent = async (id: string) => {
    try {
      await fetch(`${API_BASE}/api/agents/custom/${id}`, {
        method: 'DELETE',
      });
      setMyAgents(myAgents.filter(a => a.id !== id));
    } catch (err) {
      setError('Failed to delete agent');
    }
  };

  // Toggle agent status
  const toggleAgentStatus = async (agent: CustomAgent) => {
    try {
      const newStatus = agent.status === 'active' ? 'paused' : 'active';
      const res = await fetch(`${API_BASE}/api/agents/custom/${agent.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      });

      if (res.ok) {
        setMyAgents(myAgents.map(a => 
          a.id === agent.id ? { ...a, status: newStatus } : a
        ));
      }
    } catch (err) {
      setError('Failed to update agent');
    }
  };

  // Create team
  const createTeam = async () => {
    if (!teamForm.name.trim() || teamForm.agents.length < 2) return;
    try {
      const res = await fetch(`${API_BASE}/api/agents/teams`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: teamForm.name,
          description: teamForm.description,
          agent_ids: teamForm.agents,
          orchestration_strategy: teamForm.strategy,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setTeams([...teams, data.team]);
        setShowTeamBuilder(false);
        setTeamForm({ name: '', description: '', agents: [], strategy: 'sequential' });
      }
    } catch (err) {
      setError('Failed to create team');
    }
  };

  // Reset builder
  const resetBuilder = () => {
    setBuilderStep(1);
    setSelectedTemplate(null);
    setAgentForm({
      name: '',
      description: '',
      instructions: '',
      capabilities: [],
      temperature: 0.7,
      maxTokens: 2048,
      model: 'qwen3:4b',
    });
  };

  // Categories for filter
  const categories = Array.from(new Set(templates.map(t => t.category)));

  // Filtered templates
  const filteredTemplates = templates.filter(t => {
    const matchesSearch = !searchQuery || 
      t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = !selectedCategory || t.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  // Available capabilities
  const allCapabilities = [
    'text_generation', 'code_execution', 'web_search', 'file_analysis',
    'image_analysis', 'voice_processing', 'data_analysis', 'rag_query',
    'memory_access', 'tool_usage', 'multi_turn', 'planning',
  ];

  const tabs = [
    { id: 'marketplace', label: 'Marketplace', icon: Grid3X3 },
    { id: 'my-agents', label: 'My Agents', icon: Bot },
    { id: 'teams', label: 'Agent Teams', icon: Users },
    { id: 'builder', label: 'Agent Builder', icon: Plus },
  ];

  return (
    <div className="h-full flex flex-col bg-background">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500">
            <Bot className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold">AI Agent Marketplace</h2>
            <p className="text-sm text-muted-foreground">
              Build, customize, and deploy intelligent agents
            </p>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-4 gap-4 mb-4">
          <div className="bg-card rounded-lg p-3 border border-border">
            <div className="text-2xl font-bold text-primary">{templates.length}</div>
            <div className="text-xs text-muted-foreground">Templates</div>
          </div>
          <div className="bg-card rounded-lg p-3 border border-border">
            <div className="text-2xl font-bold text-green-500">{myAgents.length}</div>
            <div className="text-xs text-muted-foreground">My Agents</div>
          </div>
          <div className="bg-card rounded-lg p-3 border border-border">
            <div className="text-2xl font-bold text-purple-500">{teams.length}</div>
            <div className="text-xs text-muted-foreground">Teams</div>
          </div>
          <div className="bg-card rounded-lg p-3 border border-border">
            <div className="text-2xl font-bold text-orange-500">
              {myAgents.filter(a => a.status === 'active').length}
            </div>
            <div className="text-xs text-muted-foreground">Active Agents</div>
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
            {activeTab === 'marketplace' && (
              <motion.div
                key="marketplace"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-4"
              >
                {/* Search & Filters */}
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-2 flex-1">
                    <div className="relative flex-1 max-w-md">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                      <input
                        type="text"
                        value={searchQuery}
                        onChange={e => setSearchQuery(e.target.value)}
                        placeholder="Search templates..."
                        className="w-full pl-10 pr-4 py-2 bg-secondary rounded-lg border border-border text-sm"
                      />
                    </div>
                    <select
                      value={selectedCategory}
                      onChange={e => setSelectedCategory(e.target.value)}
                      className="px-3 py-2 bg-secondary rounded-lg border border-border text-sm"
                    >
                      <option value="">All Categories</option>
                      {categories.map(cat => (
                        <option key={cat} value={cat}>{cat}</option>
                      ))}
                    </select>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setViewMode('grid')}
                      className={`p-2 rounded-lg ${viewMode === 'grid' ? 'bg-primary text-primary-foreground' : 'bg-secondary'}`}
                    >
                      <Grid3X3 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => setViewMode('list')}
                      className={`p-2 rounded-lg ${viewMode === 'list' ? 'bg-primary text-primary-foreground' : 'bg-secondary'}`}
                    >
                      <List className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Featured Banner */}
                <div className="bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-xl p-6 border border-purple-500/30">
                  <div className="flex items-center gap-2 mb-2">
                    <Sparkles className="w-5 h-5 text-purple-500" />
                    <span className="text-sm font-medium text-purple-500">Featured Templates</span>
                  </div>
                  <h3 className="text-lg font-semibold mb-2">Build Your Perfect AI Assistant</h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    Choose from our curated collection of agent templates, customize them to your needs,
                    and deploy instantly.
                  </p>
                  <button
                    onClick={() => setActiveTab('builder')}
                    className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm"
                  >
                    Start Building
                  </button>
                </div>

                {/* Templates Grid */}
                <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4' : 'space-y-3'}>
                  {filteredTemplates.map(template => {
                    const Icon = CATEGORY_ICONS[template.category] || CATEGORY_ICONS.default;
                    const color = CATEGORY_COLORS[template.category] || CATEGORY_COLORS.default;

                    return viewMode === 'grid' ? (
                      <motion.div
                        key={template.id}
                        className="bg-card rounded-xl p-5 border border-border hover:border-primary/50 transition-all group cursor-pointer"
                        whileHover={{ scale: 1.02 }}
                        onClick={() => {
                          setSelectedTemplate(template);
                          setActiveTab('builder');
                          setBuilderStep(2);
                        }}
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div
                            className="p-3 rounded-xl"
                            style={{ backgroundColor: `${color}20` }}
                          >
                            <Icon className="w-6 h-6" style={{ color }} />
                          </div>
                          {template.is_featured && (
                            <span className="px-2 py-1 bg-yellow-500/20 text-yellow-500 rounded text-xs font-medium">
                              Featured
                            </span>
                          )}
                        </div>

                        <h4 className="font-semibold mb-1">{template.name}</h4>
                        <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
                          {template.description}
                        </p>

                        <div className="flex flex-wrap gap-1 mb-3">
                          {template.capabilities.slice(0, 3).map(cap => (
                            <span
                              key={cap}
                              className="px-2 py-0.5 bg-secondary rounded text-xs"
                            >
                              {cap}
                            </span>
                          ))}
                          {template.capabilities.length > 3 && (
                            <span className="px-2 py-0.5 bg-secondary rounded text-xs">
                              +{template.capabilities.length - 3}
                            </span>
                          )}
                        </div>

                        <div className="flex items-center justify-between text-sm text-muted-foreground">
                          <div className="flex items-center gap-1">
                            <Star className="w-4 h-4 fill-yellow-500 text-yellow-500" />
                            <span>{template.rating?.toFixed(1) || '4.5'}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Download className="w-4 h-4" />
                            <span>{template.downloads || 0}</span>
                          </div>
                        </div>
                      </motion.div>
                    ) : (
                      <div
                        key={template.id}
                        className="bg-card rounded-xl p-4 border border-border hover:border-primary/50 transition-all cursor-pointer flex items-center gap-4"
                        onClick={() => {
                          setSelectedTemplate(template);
                          setActiveTab('builder');
                          setBuilderStep(2);
                        }}
                      >
                        <div
                          className="p-2 rounded-lg"
                          style={{ backgroundColor: `${color}20` }}
                        >
                          <Icon className="w-5 h-5" style={{ color }} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h4 className="font-medium">{template.name}</h4>
                          <p className="text-sm text-muted-foreground truncate">{template.description}</p>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-muted-foreground">
                          <div className="flex items-center gap-1">
                            <Star className="w-4 h-4 fill-yellow-500 text-yellow-500" />
                            <span>{template.rating?.toFixed(1) || '4.5'}</span>
                          </div>
                          <ChevronRight className="w-4 h-4" />
                        </div>
                      </div>
                    );
                  })}
                </div>

                {filteredTemplates.length === 0 && (
                  <div className="text-center py-12 text-muted-foreground">
                    <Bot className="w-12 h-12 mx-auto mb-3" />
                    <p>No templates found</p>
                  </div>
                )}
              </motion.div>
            )}

            {activeTab === 'my-agents' && (
              <motion.div
                key="my-agents"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-4"
              >
                {myAgents.length === 0 ? (
                  <div className="text-center py-12">
                    <Bot className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
                    <h3 className="text-lg font-semibold mb-2">No Agents Yet</h3>
                    <p className="text-muted-foreground mb-4">
                      Create your first custom AI agent to get started
                    </p>
                    <button
                      onClick={() => setActiveTab('builder')}
                      className="px-4 py-2 bg-primary text-primary-foreground rounded-lg"
                    >
                      Create Agent
                    </button>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {myAgents.map(agent => {
                      const template = templates.find(t => t.id === agent.base_template);
                      const Icon = CATEGORY_ICONS[template?.category || 'default'] || CATEGORY_ICONS.default;
                      const color = CATEGORY_COLORS[template?.category || 'default'] || CATEGORY_COLORS.default;

                      return (
                        <div
                          key={agent.id}
                          className="bg-card rounded-xl p-5 border border-border hover:border-primary/50 transition-all"
                        >
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex items-center gap-3">
                              <div
                                className="p-2 rounded-lg"
                                style={{ backgroundColor: `${color}20` }}
                              >
                                <Icon className="w-5 h-5" style={{ color }} />
                              </div>
                              <div>
                                <h4 className="font-semibold">{agent.name}</h4>
                                <span className="text-xs text-muted-foreground">
                                  Based on {template?.name || 'Unknown'}
                                </span>
                              </div>
                            </div>
                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                              agent.status === 'active' ? 'bg-green-500/20 text-green-500' :
                              agent.status === 'paused' ? 'bg-yellow-500/20 text-yellow-500' :
                              'bg-gray-500/20 text-gray-500'
                            }`}>
                              {agent.status}
                            </span>
                          </div>

                          <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
                            {agent.description || agent.custom_instructions}
                          </p>

                          <div className="flex flex-wrap gap-1 mb-4">
                            {agent.capabilities.slice(0, 4).map(cap => (
                              <span
                                key={cap}
                                className="px-2 py-0.5 bg-secondary rounded text-xs"
                              >
                                {cap}
                              </span>
                            ))}
                          </div>

                          <div className="flex items-center justify-between pt-3 border-t border-border">
                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                              <Clock className="w-4 h-4" />
                              <span>{new Date(agent.created_at).toLocaleDateString()}</span>
                            </div>
                            <div className="flex items-center gap-1">
                              <button
                                onClick={() => toggleAgentStatus(agent)}
                                className={`p-1.5 rounded ${
                                  agent.status === 'active' ? 'bg-yellow-500/10 text-yellow-500' : 'bg-green-500/10 text-green-500'
                                }`}
                                title={agent.status === 'active' ? 'Pause' : 'Activate'}
                              >
                                {agent.status === 'active' ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                              </button>
                              <button
                                onClick={() => {
                                  setSelectedAgent(agent);
                                  setShowAgentDetails(true);
                                }}
                                className="p-1.5 bg-secondary rounded"
                                title="Details"
                              >
                                <Settings className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => deleteAgent(agent.id)}
                                className="p-1.5 bg-destructive/10 text-destructive rounded"
                                title="Delete"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </motion.div>
            )}

            {activeTab === 'teams' && (
              <motion.div
                key="teams"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-4"
              >
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">Agent Teams</h3>
                  <button
                    onClick={() => setShowTeamBuilder(true)}
                    className="px-4 py-2 bg-primary text-primary-foreground rounded-lg flex items-center gap-2"
                  >
                    <Plus className="w-4 h-4" /> Create Team
                  </button>
                </div>

                {/* Team Builder Modal */}
                {showTeamBuilder && (
                  <div className="bg-card rounded-xl p-6 border border-border">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold">Create Agent Team</h3>
                      <button onClick={() => setShowTeamBuilder(false)}>
                        <X className="w-5 h-5" />
                      </button>
                    </div>

                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium mb-1">Team Name</label>
                        <input
                          type="text"
                          value={teamForm.name}
                          onChange={e => setTeamForm({ ...teamForm, name: e.target.value })}
                          className="w-full p-2 rounded-lg bg-secondary border border-border"
                          placeholder="My Agent Team"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium mb-1">Description</label>
                        <textarea
                          value={teamForm.description}
                          onChange={e => setTeamForm({ ...teamForm, description: e.target.value })}
                          className="w-full p-2 rounded-lg bg-secondary border border-border resize-none h-20"
                          placeholder="What does this team do?"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium mb-1">Select Agents</label>
                        <div className="grid grid-cols-2 gap-2">
                          {myAgents.map(agent => (
                            <label
                              key={agent.id}
                              className={`flex items-center gap-2 p-3 rounded-lg cursor-pointer transition-all ${
                                teamForm.agents.includes(agent.id)
                                  ? 'bg-primary/20 border border-primary'
                                  : 'bg-secondary border border-border'
                              }`}
                            >
                              <input
                                type="checkbox"
                                checked={teamForm.agents.includes(agent.id)}
                                onChange={e => {
                                  if (e.target.checked) {
                                    setTeamForm({ ...teamForm, agents: [...teamForm.agents, agent.id] });
                                  } else {
                                    setTeamForm({ ...teamForm, agents: teamForm.agents.filter(a => a !== agent.id) });
                                  }
                                }}
                                className="hidden"
                              />
                              <Bot className="w-4 h-4" />
                              <span className="text-sm">{agent.name}</span>
                            </label>
                          ))}
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-medium mb-1">Orchestration Strategy</label>
                        <select
                          value={teamForm.strategy}
                          onChange={e => setTeamForm({ ...teamForm, strategy: e.target.value })}
                          className="w-full p-2 rounded-lg bg-secondary border border-border"
                        >
                          <option value="sequential">Sequential (one after another)</option>
                          <option value="parallel">Parallel (all at once)</option>
                          <option value="hierarchical">Hierarchical (leader delegates)</option>
                          <option value="debate">Debate (agents discuss)</option>
                        </select>
                      </div>

                      <button
                        onClick={createTeam}
                        disabled={!teamForm.name.trim() || teamForm.agents.length < 2}
                        className="w-full px-4 py-2 bg-primary text-primary-foreground rounded-lg disabled:opacity-50"
                      >
                        Create Team
                      </button>
                    </div>
                  </div>
                )}

                {/* Teams List */}
                {teams.length === 0 && !showTeamBuilder ? (
                  <div className="text-center py-12">
                    <Users className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
                    <h3 className="text-lg font-semibold mb-2">No Teams Yet</h3>
                    <p className="text-muted-foreground mb-4">
                      Create a team to combine multiple agents for complex tasks
                    </p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {teams.map(team => (
                      <div
                        key={team.id}
                        className="bg-card rounded-xl p-5 border border-border"
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-purple-500/20">
                              <Users className="w-5 h-5 text-purple-500" />
                            </div>
                            <div>
                              <h4 className="font-semibold">{team.name}</h4>
                              <span className="text-xs text-muted-foreground capitalize">
                                {team.orchestration_strategy} orchestration
                              </span>
                            </div>
                          </div>
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            team.status === 'active' ? 'bg-green-500/20 text-green-500' : 'bg-gray-500/20 text-gray-500'
                          }`}>
                            {team.status}
                          </span>
                        </div>

                        {team.description && (
                          <p className="text-sm text-muted-foreground mb-3">{team.description}</p>
                        )}

                        <div className="flex items-center gap-2">
                          <span className="text-xs text-muted-foreground">Agents:</span>
                          <div className="flex -space-x-2">
                            {team.agents.slice(0, 4).map((agentId, i) => {
                              const agent = myAgents.find(a => a.id === agentId);
                              return (
                                <div
                                  key={agentId}
                                  className="w-6 h-6 rounded-full bg-secondary border border-background flex items-center justify-center"
                                  title={agent?.name}
                                >
                                  <Bot className="w-3 h-3" />
                                </div>
                              );
                            })}
                            {team.agents.length > 4 && (
                              <div className="w-6 h-6 rounded-full bg-secondary border border-background flex items-center justify-center text-xs">
                                +{team.agents.length - 4}
                              </div>
                            )}
                          </div>
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
                className="space-y-6"
              >
                {/* Progress Steps */}
                <div className="flex items-center justify-between mb-6">
                  {[1, 2, 3].map(step => (
                    <div
                      key={step}
                      className={`flex items-center gap-2 ${
                        step <= builderStep ? 'text-primary' : 'text-muted-foreground'
                      }`}
                    >
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        step <= builderStep ? 'bg-primary text-primary-foreground' : 'bg-secondary'
                      }`}>
                        {step < builderStep ? <Check className="w-4 h-4" /> : step}
                      </div>
                      <span className="text-sm font-medium">
                        {step === 1 ? 'Choose Template' : step === 2 ? 'Customize' : 'Review & Create'}
                      </span>
                      {step < 3 && <ChevronRight className="w-4 h-4 text-muted-foreground" />}
                    </div>
                  ))}
                </div>

                {/* Step 1: Choose Template */}
                {builderStep === 1 && (
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold">Choose a Template</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {templates.map(template => {
                        const Icon = CATEGORY_ICONS[template.category] || CATEGORY_ICONS.default;
                        const color = CATEGORY_COLORS[template.category] || CATEGORY_COLORS.default;

                        return (
                          <div
                            key={template.id}
                            className={`bg-card rounded-xl p-5 border-2 cursor-pointer transition-all ${
                              selectedTemplate?.id === template.id
                                ? 'border-primary bg-primary/5'
                                : 'border-border hover:border-primary/50'
                            }`}
                            onClick={() => setSelectedTemplate(template)}
                          >
                            <div className="flex items-center gap-3 mb-3">
                              <div
                                className="p-2 rounded-lg"
                                style={{ backgroundColor: `${color}20` }}
                              >
                                <Icon className="w-5 h-5" style={{ color }} />
                              </div>
                              <div>
                                <h4 className="font-medium">{template.name}</h4>
                                <span className="text-xs text-muted-foreground capitalize">
                                  {template.category}
                                </span>
                              </div>
                            </div>
                            <p className="text-sm text-muted-foreground line-clamp-2">
                              {template.description}
                            </p>
                          </div>
                        );
                      })}
                    </div>
                    <div className="flex justify-end">
                      <button
                        onClick={() => selectedTemplate && setBuilderStep(2)}
                        disabled={!selectedTemplate}
                        className="px-6 py-2 bg-primary text-primary-foreground rounded-lg disabled:opacity-50"
                      >
                        Continue
                      </button>
                    </div>
                  </div>
                )}

                {/* Step 2: Customize */}
                {builderStep === 2 && (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-semibold">Customize Your Agent</h3>
                      <button
                        onClick={() => setBuilderStep(1)}
                        className="text-sm text-muted-foreground hover:text-foreground"
                      >
                        ← Back
                      </button>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium mb-1">Agent Name *</label>
                          <input
                            type="text"
                            value={agentForm.name}
                            onChange={e => setAgentForm({ ...agentForm, name: e.target.value })}
                            className="w-full p-3 rounded-lg bg-secondary border border-border"
                            placeholder="My Custom Agent"
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium mb-1">Description</label>
                          <textarea
                            value={agentForm.description}
                            onChange={e => setAgentForm({ ...agentForm, description: e.target.value })}
                            className="w-full p-3 rounded-lg bg-secondary border border-border resize-none h-24"
                            placeholder="What does this agent do?"
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium mb-1">Custom Instructions</label>
                          <textarea
                            value={agentForm.instructions}
                            onChange={e => setAgentForm({ ...agentForm, instructions: e.target.value })}
                            className="w-full p-3 rounded-lg bg-secondary border border-border resize-none h-32"
                            placeholder="Add specific instructions for this agent..."
                          />
                        </div>
                      </div>

                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium mb-2">Capabilities</label>
                          <div className="grid grid-cols-2 gap-2">
                            {allCapabilities.map(cap => (
                              <label
                                key={cap}
                                className={`flex items-center gap-2 p-2 rounded-lg cursor-pointer text-sm ${
                                  agentForm.capabilities.includes(cap)
                                    ? 'bg-primary/20 border border-primary'
                                    : 'bg-secondary border border-border'
                                }`}
                              >
                                <input
                                  type="checkbox"
                                  checked={agentForm.capabilities.includes(cap)}
                                  onChange={e => {
                                    if (e.target.checked) {
                                      setAgentForm({ ...agentForm, capabilities: [...agentForm.capabilities, cap] });
                                    } else {
                                      setAgentForm({ ...agentForm, capabilities: agentForm.capabilities.filter(c => c !== cap) });
                                    }
                                  }}
                                  className="hidden"
                                />
                                <span className="truncate">{cap.replace(/_/g, ' ')}</span>
                              </label>
                            ))}
                          </div>
                        </div>

                        <div>
                          <label className="block text-sm font-medium mb-1">
                            Temperature: {agentForm.temperature}
                          </label>
                          <input
                            type="range"
                            min="0"
                            max="1"
                            step="0.1"
                            value={agentForm.temperature}
                            onChange={e => setAgentForm({ ...agentForm, temperature: parseFloat(e.target.value) })}
                            className="w-full"
                          />
                          <div className="flex justify-between text-xs text-muted-foreground">
                            <span>Precise</span>
                            <span>Creative</span>
                          </div>
                        </div>

                        <div>
                          <label className="block text-sm font-medium mb-1">Model</label>
                          <select
                            value={agentForm.model}
                            onChange={e => setAgentForm({ ...agentForm, model: e.target.value })}
                            className="w-full p-3 rounded-lg bg-secondary border border-border"
                          >
                            <option value="qwen3:4b">Qwen3 4B (Fast)</option>
                            <option value="qwen3-vl:8b">Qwen3 VL 8B (Vision)</option>
                            <option value="llama3:8b">LLaMA3 8B</option>
                            <option value="mistral:7b">Mistral 7B</option>
                          </select>
                        </div>
                      </div>
                    </div>

                    <div className="flex justify-end gap-2">
                      <button
                        onClick={() => setBuilderStep(1)}
                        className="px-6 py-2 bg-secondary rounded-lg"
                      >
                        Back
                      </button>
                      <button
                        onClick={() => agentForm.name.trim() && setBuilderStep(3)}
                        disabled={!agentForm.name.trim()}
                        className="px-6 py-2 bg-primary text-primary-foreground rounded-lg disabled:opacity-50"
                      >
                        Review
                      </button>
                    </div>
                  </div>
                )}

                {/* Step 3: Review & Create */}
                {builderStep === 3 && (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-semibold">Review & Create</h3>
                      <button
                        onClick={() => setBuilderStep(2)}
                        className="text-sm text-muted-foreground hover:text-foreground"
                      >
                        ← Back
                      </button>
                    </div>

                    <div className="bg-card rounded-xl p-6 border border-border space-y-4">
                      <div className="flex items-center gap-3">
                        {(() => {
                          const Icon = CATEGORY_ICONS[selectedTemplate?.category || 'default'];
                          const color = CATEGORY_COLORS[selectedTemplate?.category || 'default'];
                          return (
                            <div className="p-3 rounded-xl" style={{ backgroundColor: `${color}20` }}>
                              <Icon className="w-6 h-6" style={{ color }} />
                            </div>
                          );
                        })()}
                        <div>
                          <h4 className="text-xl font-bold">{agentForm.name}</h4>
                          <span className="text-sm text-muted-foreground">
                            Based on {selectedTemplate?.name}
                          </span>
                        </div>
                      </div>

                      {agentForm.description && (
                        <div>
                          <label className="text-xs font-medium text-muted-foreground">Description</label>
                          <p className="text-sm">{agentForm.description}</p>
                        </div>
                      )}

                      {agentForm.instructions && (
                        <div>
                          <label className="text-xs font-medium text-muted-foreground">Custom Instructions</label>
                          <p className="text-sm bg-secondary p-3 rounded-lg">{agentForm.instructions}</p>
                        </div>
                      )}

                      <div>
                        <label className="text-xs font-medium text-muted-foreground">Capabilities</label>
                        <div className="flex flex-wrap gap-2 mt-1">
                          {agentForm.capabilities.map(cap => (
                            <span key={cap} className="px-2 py-1 bg-primary/20 text-primary rounded text-xs">
                              {cap.replace(/_/g, ' ')}
                            </span>
                          ))}
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="text-xs font-medium text-muted-foreground">Temperature</label>
                          <p className="text-sm">{agentForm.temperature}</p>
                        </div>
                        <div>
                          <label className="text-xs font-medium text-muted-foreground">Model</label>
                          <p className="text-sm">{agentForm.model}</p>
                        </div>
                      </div>
                    </div>

                    <div className="flex justify-end gap-2">
                      <button
                        onClick={resetBuilder}
                        className="px-6 py-2 bg-secondary rounded-lg"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={createAgent}
                        className="px-6 py-2 bg-primary text-primary-foreground rounded-lg flex items-center gap-2"
                      >
                        <Sparkles className="w-4 h-4" /> Create Agent
                      </button>
                    </div>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        )}

        {/* Agent Details Modal */}
        {showAgentDetails && selectedAgent && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-background rounded-xl p-6 w-full max-w-lg border border-border">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Agent Details</h3>
                <button onClick={() => setShowAgentDetails(false)}>
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Name</label>
                  <p className="font-medium">{selectedAgent.name}</p>
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Status</label>
                  <p className="capitalize">{selectedAgent.status}</p>
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Instructions</label>
                  <p className="text-sm bg-secondary p-3 rounded-lg">{selectedAgent.custom_instructions || 'No custom instructions'}</p>
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Parameters</label>
                  <pre className="text-xs bg-secondary p-3 rounded-lg overflow-auto">
                    {JSON.stringify(selectedAgent.parameters, null, 2)}
                  </pre>
                </div>
              </div>

              <div className="flex justify-end gap-2 mt-6">
                <button
                  onClick={() => setShowAgentDetails(false)}
                  className="px-4 py-2 bg-secondary rounded-lg"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
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

export default AgentMarketplacePanel;
