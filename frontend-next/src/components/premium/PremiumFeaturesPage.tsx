'use client';

import React, { useState } from 'react';
import { 
  Mic, 
  Code2, 
  Bot, 
  Shield, 
  BarChart3,
  Workflow,
  Network,
  Video,
  FileStack,
  Crown,
  Sparkles,
  Brain,
  Store,
  GraduationCap
} from 'lucide-react';

import { VoiceAIPanel } from './VoiceAIPanel';
import { CodeInterpreterPanel } from './CodeInterpreterPanel';
import { AutonomousAgentPanel } from './AutonomousAgentPanel';
import { SecurityScannerPanel } from './SecurityScannerPanel';
import { AnalyticsDashboard } from './AnalyticsDashboard';
import { AIMemoryPanel } from './AIMemoryPanel';
import { WorkflowOrchestratorPanel } from './WorkflowOrchestratorPanel';
import { KnowledgeGraphPanel } from './KnowledgeGraphPanel';
import { AgentMarketplacePanel } from './AgentMarketplacePanel';
import FullMetaPanel from './FullMetaPanel';

interface PremiumFeaturesPageProps {
  className?: string;
}

type FeatureTab = 'voice' | 'code' | 'agent' | 'security' | 'analytics' | 'workflow' | 'graph' | 'recording' | 'multimodal' | 'memory' | 'marketplace' | 'fullmeta';

interface Feature {
  id: FeatureTab;
  name: string;
  description: string;
  icon: React.ElementType;
  color: string;
  bgGradient: string;
  available: boolean;
  isNew?: boolean;
}

const features: Feature[] = [
  {
    id: 'fullmeta',
    name: 'AI ile Öğren',
    description: 'Nöro-adaptif mastery sistemi',
    icon: GraduationCap,
    color: 'text-violet-400',
    bgGradient: 'from-violet-500/20 to-purple-500/20',
    available: true,
    isNew: true,
  },
  {
    id: 'memory',
    name: 'AI Memory',
    description: 'Kişiselleştirilmiş AI hafızası',
    icon: Brain,
    color: 'text-pink-400',
    bgGradient: 'from-pink-500/20 to-rose-500/20',
    available: true,
    isNew: true,
  },
  {
    id: 'workflow',
    name: 'Workflow Orchestrator',
    description: 'Gelişmiş görsel iş akışları',
    icon: Workflow,
    color: 'text-yellow-400',
    bgGradient: 'from-yellow-500/20 to-amber-500/20',
    available: true,
    isNew: true,
  },
  {
    id: 'graph',
    name: 'Enterprise Knowledge Graph',
    description: 'LLM destekli varlık çıkarma',
    icon: Network,
    color: 'text-emerald-400',
    bgGradient: 'from-emerald-500/20 to-teal-500/20',
    available: true,
    isNew: true,
  },
  {
    id: 'marketplace',
    name: 'Agent Marketplace',
    description: 'AI agentları oluşturun ve paylaşın',
    icon: Store,
    color: 'text-purple-400',
    bgGradient: 'from-purple-500/20 to-violet-500/20',
    available: true,
    isNew: true,
  },
  {
    id: 'voice',
    name: 'Sesli AI Asistan',
    description: 'Konuşarak etkileşim kurun (STT + TTS)',
    icon: Mic,
    color: 'text-blue-400',
    bgGradient: 'from-blue-500/20 to-indigo-500/20',
    available: true,
  },
  {
    id: 'code',
    name: 'Code Interpreter',
    description: 'Güvenli sandbox\'ta kod çalıştırın',
    icon: Code2,
    color: 'text-green-400',
    bgGradient: 'from-green-500/20 to-emerald-500/20',
    available: true,
  },
  {
    id: 'agent',
    name: 'Otonom Agent',
    description: 'Hedef belirle, agent çalışsın',
    icon: Bot,
    color: 'text-cyan-400',
    bgGradient: 'from-cyan-500/20 to-blue-500/20',
    available: true,
  },
  {
    id: 'security',
    name: 'Güvenlik Tarayıcı',
    description: 'Kod güvenlik açıklarını tespit edin',
    icon: Shield,
    color: 'text-red-400',
    bgGradient: 'from-red-500/20 to-orange-500/20',
    available: true,
  },
  {
    id: 'analytics',
    name: 'Kişisel Analitik',
    description: 'Verimlilik ve kullanım istatistikleri',
    icon: BarChart3,
    color: 'text-indigo-400',
    bgGradient: 'from-indigo-500/20 to-purple-500/20',
    available: true,
  },
  {
    id: 'recording',
    name: 'Ekran Kaydı + AI',
    description: 'Kayıt ve AI analizi',
    icon: Video,
    color: 'text-rose-400',
    bgGradient: 'from-rose-500/20 to-pink-500/20',
    available: true,
  },
  {
    id: 'multimodal',
    name: 'Multi-Modal RAG',
    description: 'PDF, görsel, ses, video indeksleme',
    icon: FileStack,
    color: 'text-orange-400',
    bgGradient: 'from-orange-500/20 to-red-500/20',
    available: true,
  },
];

export function PremiumFeaturesPage({ className = '' }: PremiumFeaturesPageProps) {
  const [activeTab, setActiveTab] = useState<FeatureTab>('fullmeta');

  const renderContent = () => {
    switch (activeTab) {
      case 'fullmeta':
        return <FullMetaPanel />;
      case 'memory':
        return <AIMemoryPanel />;
      case 'workflow':
        return <WorkflowOrchestratorPanel />;
      case 'graph':
        return <KnowledgeGraphPanel />;
      case 'marketplace':
        return <AgentMarketplacePanel />;
      case 'voice':
        return <VoiceAIPanel />;
      case 'code':
        return <CodeInterpreterPanel />;
      case 'agent':
        return <AutonomousAgentPanel />;
      case 'security':
        return <SecurityScannerPanel />;
      case 'analytics':
        return <AnalyticsDashboard />;
      case 'recording':
        return (
          <div className="bg-white/5 rounded-xl p-8 text-center">
            <Video className="w-16 h-16 text-rose-400 mx-auto mb-4" />
            <h3 className="text-xl font-bold text-white mb-2">Ekran Kaydı + AI Analiz</h3>
            <p className="text-gray-400 mb-4">
              Ekranınızı kaydedin ve AI ile analiz edin.
              Otomatik tutorial oluşturma ve sahne tespiti.
            </p>
            <p className="text-sm text-rose-400">API: /api/screen-recording</p>
          </div>
        );
      case 'multimodal':
        return (
          <div className="bg-white/5 rounded-xl p-8 text-center">
            <FileStack className="w-16 h-16 text-orange-400 mx-auto mb-4" />
            <h3 className="text-xl font-bold text-white mb-2">Multi-Modal RAG</h3>
            <p className="text-gray-400 mb-4">
              PDF, görsel, ses ve video dosyalarını indeksleyin.
              Tüm medya türlerinde semantik arama yapın.
            </p>
            <p className="text-sm text-orange-400">API: /api/multimodal</p>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className={`min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 ${className}`}>
      {/* Header */}
      <div className="border-b border-white/10 bg-black/20 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-gradient-to-br from-yellow-500/30 to-orange-500/30 rounded-xl">
              <Crown className="w-8 h-8 text-yellow-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                Premium Özellikler
                <Sparkles className="w-5 h-5 text-yellow-400" />
              </h1>
              <p className="text-gray-400">%100 Yerel • Gizlilik Öncelikli • Sınırsız Kullanım</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="flex gap-6">
          {/* Sidebar */}
          <div className="w-64 flex-shrink-0">
            <nav className="space-y-2 sticky top-6">
              {features.map((feature) => {
                const Icon = feature.icon;
                const isActive = activeTab === feature.id;
                
                return (
                  <button
                    key={feature.id}
                    onClick={() => setActiveTab(feature.id)}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-left transition-all ${
                      isActive
                        ? `bg-gradient-to-r ${feature.bgGradient} border border-white/20`
                        : 'hover:bg-white/5 border border-transparent'
                    }`}
                  >
                    <div className={`p-2 rounded-lg ${isActive ? 'bg-white/10' : 'bg-white/5'}`}>
                      <Icon className={`w-5 h-5 ${feature.color}`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className={`font-medium truncate flex items-center gap-2 ${isActive ? 'text-white' : 'text-gray-300'}`}>
                        {feature.name}
                        {feature.isNew && (
                          <span className="px-1.5 py-0.5 text-[10px] font-bold bg-gradient-to-r from-pink-500 to-purple-500 text-white rounded-full">
                            NEW
                          </span>
                        )}
                      </p>
                      <p className="text-xs text-gray-500 truncate">{feature.description}</p>
                    </div>
                  </button>
                );
              })}
            </nav>

            {/* Info Box */}
            <div className="mt-6 p-4 bg-gradient-to-br from-indigo-500/10 to-purple-500/10 rounded-xl border border-indigo-500/20">
              <div className="flex items-center gap-2 mb-2">
                <Sparkles className="w-4 h-4 text-indigo-400" />
                <span className="text-sm font-medium text-indigo-400">%100 Yerel</span>
              </div>
              <p className="text-xs text-gray-400">
                Tüm işlemler cihazınızda gerçekleşir. 
                Verileriniz asla dışarı çıkmaz.
              </p>
            </div>
          </div>

          {/* Main Content */}
          <div className="flex-1 min-w-0">
            {renderContent()}
          </div>
        </div>
      </div>
    </div>
  );
}

export default PremiumFeaturesPage;
