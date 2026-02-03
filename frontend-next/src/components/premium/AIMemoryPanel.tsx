'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Brain,
  User,
  Settings,
  MessageSquare,
  Sparkles,
  Save,
  RefreshCw,
  Heart,
  BookOpen,
  Lightbulb,
  Target,
  Sliders,
  PenTool,
  Clock,
  TrendingUp,
  Trash2,
  Plus,
  Edit,
  Check,
  X,
  Search,
  Tags,
  Globe,
} from 'lucide-react';

interface UserProfile {
  user_id: string;
  name: string;
  profession: string;
  expertise_level: string;
  interests: string[];
  preferred_language: string;
  timezone: string;
}

interface Preference {
  category: string;
  preferences: Record<string, any>;
}

interface Memory {
  id: string;
  content: string;
  memory_type: string;
  importance: number;
  tags: string[];
  created_at: string;
}

interface WritingStyle {
  formality: number;
  complexity: number;
  emoji_usage: number;
  avg_sentence_length: number;
  vocabulary_richness: number;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function AIMemoryPanel() {
  const [activeTab, setActiveTab] = useState<'profile' | 'preferences' | 'memories' | 'style'>('profile');
  const [userId, setUserId] = useState('default');
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [preferences, setPreferences] = useState<Record<string, any>>({});
  const [memories, setMemories] = useState<Memory[]>([]);
  const [writingStyle, setWritingStyle] = useState<WritingStyle | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  // Profile form state
  const [editingProfile, setEditingProfile] = useState(false);
  const [profileForm, setProfileForm] = useState<Partial<UserProfile>>({});

  // Memory form state
  const [newMemory, setNewMemory] = useState({ content: '', memory_type: 'fact', importance: 0.5, tags: '' });

  // Load profile and data
  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Load profile
      const profileRes = await fetch(`${API_BASE}/api/memory/profiles/${userId}`);
      if (profileRes.ok) {
        const data = await profileRes.json();
        setProfile(data.profile);
        setProfileForm(data.profile);
      }

      // Load preferences
      const prefsRes = await fetch(`${API_BASE}/api/memory/profiles/${userId}/preferences`);
      if (prefsRes.ok) {
        const data = await prefsRes.json();
        setPreferences(data.preferences || {});
      }

      // Load memories
      const memRes = await fetch(`${API_BASE}/api/memory/profiles/${userId}/memories?limit=50`);
      if (memRes.ok) {
        const data = await memRes.json();
        setMemories(data.memories || []);
      }

      // Load writing style
      const styleRes = await fetch(`${API_BASE}/api/memory/profiles/${userId}/writing-style`);
      if (styleRes.ok) {
        const data = await styleRes.json();
        setWritingStyle(data.writing_style);
      }
    } catch (err) {
      setError('Failed to load data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const createProfile = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/memory/profiles`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          name: profileForm.name || 'User',
          profession: profileForm.profession,
          expertise_level: profileForm.expertise_level || 'intermediate',
          interests: profileForm.interests || [],
          preferred_language: profileForm.preferred_language || 'auto',
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setProfile(data.profile);
        setEditingProfile(false);
      }
    } catch (err) {
      setError('Failed to create profile');
    }
  };

  const updateProfile = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/memory/profiles/${userId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(profileForm),
      });
      if (res.ok) {
        const data = await res.json();
        setProfile(data.profile);
        setEditingProfile(false);
      }
    } catch (err) {
      setError('Failed to update profile');
    }
  };

  const addMemory = async () => {
    if (!newMemory.content.trim()) return;
    try {
      const res = await fetch(`${API_BASE}/api/memory/profiles/${userId}/memories`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: newMemory.content,
          memory_type: newMemory.memory_type,
          importance: newMemory.importance,
          tags: newMemory.tags.split(',').map(t => t.trim()).filter(Boolean),
        }),
      });
      if (res.ok) {
        setNewMemory({ content: '', memory_type: 'fact', importance: 0.5, tags: '' });
        loadData();
      }
    } catch (err) {
      setError('Failed to add memory');
    }
  };

  const deleteMemory = async (memoryId: string) => {
    try {
      await fetch(`${API_BASE}/api/memory/profiles/${userId}/memories/${memoryId}`, {
        method: 'DELETE',
      });
      setMemories(memories.filter(m => m.id !== memoryId));
    } catch (err) {
      setError('Failed to delete memory');
    }
  };

  const searchMemories = async () => {
    if (!searchQuery.trim()) return;
    try {
      const res = await fetch(
        `${API_BASE}/api/memory/profiles/${userId}/memories/search?query=${encodeURIComponent(searchQuery)}`,
        { method: 'POST' }
      );
      if (res.ok) {
        const data = await res.json();
        setMemories(data.results || []);
      }
    } catch (err) {
      setError('Failed to search memories');
    }
  };

  const updatePreference = async (category: string, key: string, value: any) => {
    try {
      await fetch(`${API_BASE}/api/memory/profiles/${userId}/preferences`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          category,
          preferences: { [key]: value },
        }),
      });
      setPreferences(prev => ({
        ...prev,
        [category]: { ...(prev[category] || {}), [key]: value },
      }));
    } catch (err) {
      setError('Failed to update preference');
    }
  };

  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'preferences', label: 'Preferences', icon: Sliders },
    { id: 'memories', label: 'Memories', icon: Brain },
    { id: 'style', label: 'Writing Style', icon: PenTool },
  ];

  return (
    <div className="h-full flex flex-col bg-background">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500">
            <Brain className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold">AI Memory & Personalization</h2>
            <p className="text-sm text-muted-foreground">
              Your AI remembers and adapts to you
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
            {activeTab === 'profile' && (
              <motion.div
                key="profile"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-6"
              >
                {!profile ? (
                  <div className="text-center p-8 bg-secondary rounded-xl">
                    <User className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
                    <h3 className="text-lg font-semibold mb-2">Create Your Profile</h3>
                    <p className="text-muted-foreground mb-4">
                      Set up your profile so AI can personalize responses for you
                    </p>
                    <button
                      onClick={() => setEditingProfile(true)}
                      className="px-4 py-2 bg-primary text-primary-foreground rounded-lg"
                    >
                      Create Profile
                    </button>
                  </div>
                ) : (
                  <div className="space-y-6">
                    {/* Profile Card */}
                    <div className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 rounded-xl p-6 border border-purple-500/20">
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-4">
                          <div className="w-16 h-16 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center">
                            <span className="text-2xl font-bold text-white">
                              {profile.name?.[0]?.toUpperCase() || 'U'}
                            </span>
                          </div>
                          <div>
                            <h3 className="text-xl font-bold">{profile.name || 'User'}</h3>
                            <p className="text-muted-foreground">{profile.profession || 'Not specified'}</p>
                            <div className="flex items-center gap-2 mt-1">
                              <span className="px-2 py-0.5 bg-primary/20 rounded text-xs">
                                {profile.expertise_level}
                              </span>
                              <span className="px-2 py-0.5 bg-secondary rounded text-xs flex items-center gap-1">
                                <Globe className="w-3 h-3" />
                                {profile.preferred_language}
                              </span>
                            </div>
                          </div>
                        </div>
                        <button
                          onClick={() => setEditingProfile(true)}
                          className="p-2 hover:bg-secondary rounded-lg"
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                      </div>

                      {/* Interests */}
                      {profile.interests?.length > 0 && (
                        <div className="mt-4">
                          <h4 className="text-sm font-medium mb-2 flex items-center gap-1">
                            <Heart className="w-4 h-4" /> Interests
                          </h4>
                          <div className="flex flex-wrap gap-2">
                            {profile.interests.map((interest, i) => (
                              <span key={i} className="px-3 py-1 bg-secondary rounded-full text-sm">
                                {interest}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Edit Profile Modal */}
                    {editingProfile && (
                      <div className="bg-card rounded-xl p-6 border border-border">
                        <h3 className="text-lg font-semibold mb-4">Edit Profile</h3>
                        <div className="space-y-4">
                          <div>
                            <label className="block text-sm font-medium mb-1">Name</label>
                            <input
                              type="text"
                              value={profileForm.name || ''}
                              onChange={e => setProfileForm({ ...profileForm, name: e.target.value })}
                              className="w-full p-2 rounded-lg bg-secondary border border-border"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium mb-1">Profession</label>
                            <input
                              type="text"
                              value={profileForm.profession || ''}
                              onChange={e => setProfileForm({ ...profileForm, profession: e.target.value })}
                              className="w-full p-2 rounded-lg bg-secondary border border-border"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium mb-1">Expertise Level</label>
                            <select
                              value={profileForm.expertise_level || 'intermediate'}
                              onChange={e => setProfileForm({ ...profileForm, expertise_level: e.target.value })}
                              className="w-full p-2 rounded-lg bg-secondary border border-border"
                            >
                              <option value="beginner">Beginner</option>
                              <option value="intermediate">Intermediate</option>
                              <option value="advanced">Advanced</option>
                              <option value="expert">Expert</option>
                            </select>
                          </div>
                          <div>
                            <label className="block text-sm font-medium mb-1">Language</label>
                            <select
                              value={profileForm.preferred_language || 'auto'}
                              onChange={e => setProfileForm({ ...profileForm, preferred_language: e.target.value })}
                              className="w-full p-2 rounded-lg bg-secondary border border-border"
                            >
                              <option value="auto">Auto-detect</option>
                              <option value="en">English</option>
                              <option value="tr">Türkçe</option>
                              <option value="de">Deutsch</option>
                              <option value="fr">Français</option>
                            </select>
                          </div>
                          <div className="flex gap-2">
                            <button
                              onClick={profile ? updateProfile : createProfile}
                              className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-lg flex items-center justify-center gap-2"
                            >
                              <Save className="w-4 h-4" /> Save
                            </button>
                            <button
                              onClick={() => setEditingProfile(false)}
                              className="px-4 py-2 bg-secondary rounded-lg"
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </motion.div>
            )}

            {activeTab === 'preferences' && (
              <motion.div
                key="preferences"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-6"
              >
                {/* Response Style */}
                <div className="bg-card rounded-xl p-6 border border-border">
                  <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <MessageSquare className="w-5 h-5" /> Response Style
                  </h3>
                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span>Formality</span>
                        <span>{preferences.response_style?.formality || 50}%</span>
                      </div>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={preferences.response_style?.formality || 50}
                        onChange={e => updatePreference('response_style', 'formality', parseInt(e.target.value))}
                        className="w-full"
                      />
                      <div className="flex justify-between text-xs text-muted-foreground">
                        <span>Casual</span>
                        <span>Formal</span>
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span>Detail Level</span>
                        <span>{preferences.response_style?.detail || 50}%</span>
                      </div>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={preferences.response_style?.detail || 50}
                        onChange={e => updatePreference('response_style', 'detail', parseInt(e.target.value))}
                        className="w-full"
                      />
                      <div className="flex justify-between text-xs text-muted-foreground">
                        <span>Concise</span>
                        <span>Detailed</span>
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span>Technical Depth</span>
                        <span>{preferences.response_style?.technical || 50}%</span>
                      </div>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={preferences.response_style?.technical || 50}
                        onChange={e => updatePreference('response_style', 'technical', parseInt(e.target.value))}
                        className="w-full"
                      />
                      <div className="flex justify-between text-xs text-muted-foreground">
                        <span>Simple</span>
                        <span>Technical</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Communication */}
                <div className="bg-card rounded-xl p-6 border border-border">
                  <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <Sparkles className="w-5 h-5" /> Communication
                  </h3>
                  <div className="grid grid-cols-2 gap-4">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={preferences.communication?.use_emojis ?? true}
                        onChange={e => updatePreference('communication', 'use_emojis', e.target.checked)}
                        className="w-4 h-4 rounded"
                      />
                      <span className="text-sm">Use Emojis 😊</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={preferences.communication?.use_markdown ?? true}
                        onChange={e => updatePreference('communication', 'use_markdown', e.target.checked)}
                        className="w-4 h-4 rounded"
                      />
                      <span className="text-sm">Use Markdown</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={preferences.communication?.show_reasoning ?? true}
                        onChange={e => updatePreference('communication', 'show_reasoning', e.target.checked)}
                        className="w-4 h-4 rounded"
                      />
                      <span className="text-sm">Show Reasoning</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={preferences.communication?.cite_sources ?? true}
                        onChange={e => updatePreference('communication', 'cite_sources', e.target.checked)}
                        className="w-4 h-4 rounded"
                      />
                      <span className="text-sm">Cite Sources</span>
                    </label>
                  </div>
                </div>
              </motion.div>
            )}

            {activeTab === 'memories' && (
              <motion.div
                key="memories"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-6"
              >
                {/* Add Memory */}
                <div className="bg-card rounded-xl p-6 border border-border">
                  <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <Plus className="w-5 h-5" /> Add Memory
                  </h3>
                  <div className="space-y-4">
                    <textarea
                      value={newMemory.content}
                      onChange={e => setNewMemory({ ...newMemory, content: e.target.value })}
                      placeholder="What should AI remember about you?"
                      className="w-full p-3 rounded-lg bg-secondary border border-border resize-none h-24"
                    />
                    <div className="flex gap-4">
                      <select
                        value={newMemory.memory_type}
                        onChange={e => setNewMemory({ ...newMemory, memory_type: e.target.value })}
                        className="px-3 py-2 rounded-lg bg-secondary border border-border"
                      >
                        <option value="fact">Fact</option>
                        <option value="preference">Preference</option>
                        <option value="context">Context</option>
                        <option value="episode">Episode</option>
                      </select>
                      <input
                        type="text"
                        value={newMemory.tags}
                        onChange={e => setNewMemory({ ...newMemory, tags: e.target.value })}
                        placeholder="Tags (comma separated)"
                        className="flex-1 px-3 py-2 rounded-lg bg-secondary border border-border"
                      />
                      <button
                        onClick={addMemory}
                        disabled={!newMemory.content.trim()}
                        className="px-4 py-2 bg-primary text-primary-foreground rounded-lg disabled:opacity-50"
                      >
                        Add
                      </button>
                    </div>
                  </div>
                </div>

                {/* Search */}
                <div className="flex gap-2">
                  <div className="flex-1 relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={e => setSearchQuery(e.target.value)}
                      onKeyDown={e => e.key === 'Enter' && searchMemories()}
                      placeholder="Search memories..."
                      className="w-full pl-10 pr-4 py-2 rounded-lg bg-secondary border border-border"
                    />
                  </div>
                  <button
                    onClick={searchMemories}
                    className="px-4 py-2 bg-secondary rounded-lg"
                  >
                    Search
                  </button>
                  <button
                    onClick={loadData}
                    className="px-4 py-2 bg-secondary rounded-lg"
                  >
                    <RefreshCw className="w-4 h-4" />
                  </button>
                </div>

                {/* Memories List */}
                <div className="space-y-3">
                  {memories.length === 0 ? (
                    <div className="text-center p-8 bg-secondary rounded-xl">
                      <Brain className="w-12 h-12 mx-auto mb-3 text-muted-foreground" />
                      <p className="text-muted-foreground">No memories yet</p>
                    </div>
                  ) : (
                    memories.map(memory => (
                      <div
                        key={memory.id}
                        className="bg-card rounded-xl p-4 border border-border"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <p className="text-sm">{memory.content}</p>
                            <div className="flex items-center gap-2 mt-2">
                              <span className="px-2 py-0.5 bg-primary/20 rounded text-xs">
                                {memory.memory_type}
                              </span>
                              {memory.tags?.map((tag, i) => (
                                <span key={i} className="px-2 py-0.5 bg-secondary rounded text-xs">
                                  #{tag}
                                </span>
                              ))}
                              <span className="text-xs text-muted-foreground ml-auto">
                                {new Date(memory.created_at).toLocaleDateString()}
                              </span>
                            </div>
                          </div>
                          <button
                            onClick={() => deleteMemory(memory.id)}
                            className="p-1 hover:bg-destructive/20 rounded text-destructive"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </motion.div>
            )}

            {activeTab === 'style' && (
              <motion.div
                key="style"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-6"
              >
                <div className="bg-gradient-to-r from-blue-500/10 to-cyan-500/10 rounded-xl p-6 border border-blue-500/20">
                  <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <PenTool className="w-5 h-5" /> Your Writing Style Profile
                  </h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    AI learns your writing patterns to generate responses that match your style
                  </p>

                  {writingStyle ? (
                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-card/50 rounded-lg p-4">
                        <div className="flex justify-between text-sm mb-2">
                          <span>Formality</span>
                          <span>{Math.round((writingStyle.formality || 0.5) * 100)}%</span>
                        </div>
                        <div className="w-full h-2 bg-secondary rounded-full overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-blue-500 to-cyan-500"
                            style={{ width: `${(writingStyle.formality || 0.5) * 100}%` }}
                          />
                        </div>
                      </div>
                      <div className="bg-card/50 rounded-lg p-4">
                        <div className="flex justify-between text-sm mb-2">
                          <span>Complexity</span>
                          <span>{Math.round((writingStyle.complexity || 0.5) * 100)}%</span>
                        </div>
                        <div className="w-full h-2 bg-secondary rounded-full overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-purple-500 to-pink-500"
                            style={{ width: `${(writingStyle.complexity || 0.5) * 100}%` }}
                          />
                        </div>
                      </div>
                      <div className="bg-card/50 rounded-lg p-4">
                        <div className="flex justify-between text-sm mb-2">
                          <span>Vocabulary</span>
                          <span>{Math.round((writingStyle.vocabulary_richness || 0.5) * 100)}%</span>
                        </div>
                        <div className="w-full h-2 bg-secondary rounded-full overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-green-500 to-emerald-500"
                            style={{ width: `${(writingStyle.vocabulary_richness || 0.5) * 100}%` }}
                          />
                        </div>
                      </div>
                      <div className="bg-card/50 rounded-lg p-4">
                        <div className="flex justify-between text-sm mb-2">
                          <span>Avg Sentence Length</span>
                          <span>{writingStyle.avg_sentence_length || 15} words</span>
                        </div>
                        <div className="w-full h-2 bg-secondary rounded-full overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-orange-500 to-yellow-500"
                            style={{ width: `${Math.min((writingStyle.avg_sentence_length || 15) / 30 * 100, 100)}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center p-8">
                      <Lightbulb className="w-12 h-12 mx-auto mb-3 text-muted-foreground" />
                      <p className="text-muted-foreground">
                        Send more messages to help AI learn your writing style
                      </p>
                    </div>
                  )}
                </div>

                {/* Sample Analysis */}
                <div className="bg-card rounded-xl p-6 border border-border">
                  <h3 className="text-lg font-semibold mb-4">Analyze Writing Sample</h3>
                  <textarea
                    placeholder="Paste a sample of your writing to analyze..."
                    className="w-full p-3 rounded-lg bg-secondary border border-border resize-none h-32"
                  />
                  <button className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded-lg">
                    Analyze Style
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

export default AIMemoryPanel;
