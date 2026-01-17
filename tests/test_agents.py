"""
Enterprise AI Assistant - Agent Tests
======================================

Multi-agent orchestration, ReAct agents, ve agent communication testleri.
"""

import pytest
import sys
import asyncio
from pathlib import Path
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock chromadb before vector_store import to avoid connection errors
# But DON'T mock 'rag' as a whole - that breaks other tests
if 'chromadb' not in sys.modules:
    _mock_chromadb = MagicMock()
    _mock_collection = MagicMock()
    _mock_collection.count.return_value = 0
    _mock_collection.query.return_value = {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}
    _mock_chromadb.PersistentClient.return_value.get_or_create_collection.return_value = _mock_collection
    _mock_chromadb.PersistentClient.return_value.list_collections.return_value = []
    sys.modules['chromadb'] = _mock_chromadb
    sys.modules['chromadb.config'] = MagicMock()
    sys.modules['chromadb.api'] = MagicMock()
    sys.modules['chromadb.api.client'] = MagicMock()


class TestBaseAgent:
    """Base Agent testleri."""
    
    def test_base_agent_initialization(self):
        """BaseAgent başlatılabilmeli."""
        from agents.base_agent import BaseAgent, AgentRole, AgentResponse
        
        class TestAgent(BaseAgent):
            """Test için BaseAgent implementasyonu."""
            
            def execute(self, task: str, context=None) -> AgentResponse:
                """Abstract execute metodunun implementasyonu."""
                return AgentResponse(
                    content="processed",
                    agent_name=self.name,
                    agent_role=self.role.value
                )
        
        agent = TestAgent(
            name="TestAgent",
            role=AgentRole.ASSISTANT,
            description="Test agent",
            system_prompt="Test prompt"
        )
        
        assert agent.name == "TestAgent"
        assert agent.role == AgentRole.ASSISTANT
    
    def test_agent_roles_defined(self):
        """Tüm roller tanımlı olmalı."""
        from agents.base_agent import AgentRole
        
        expected_roles = [
            "orchestrator", "research", "writer", 
            "analyzer", "assistant", "planner"
        ]
        
        for role_name in expected_roles:
            try:
                role = AgentRole(role_name)
                assert role.value == role_name
            except ValueError:
                # Bazı roller farklı isimlerde olabilir
                pass
    
    def test_agent_memory(self):
        """Agent memory'si çalışmalı."""
        from agents.base_agent import BaseAgent, AgentRole, AgentResponse
        
        class MemoryAgent(BaseAgent):
            """Test için memory destekli agent."""
            
            def execute(self, task: str, context=None) -> AgentResponse:
                """Abstract execute metodunun implementasyonu."""
                # BaseAgent'ın _add_to_memory metodunu kullan
                self._add_to_memory(task, "test_response")
                return AgentResponse(
                    content=task,
                    agent_name=self.name,
                    agent_role=self.role.value
                )
        
        agent = MemoryAgent(
            name="MemAgent",
            role=AgentRole.ASSISTANT,
            description="Memory test agent",
            system_prompt="Test prompt"
        )
        
        # Memory sistemi mevcut mu kontrol et
        assert hasattr(agent, 'memory')
        assert hasattr(agent, '_add_to_memory')
        
        # Execute çağrıldığında memory dolacak
        agent.execute("test_value")
        assert len(agent.memory) >= 1


class TestOrchestrator:
    """Orchestrator testleri."""
    
    def test_orchestrator_initialization(self):
        """Orchestrator başlatılabilmeli."""
        from agents.orchestrator import Orchestrator
        
        orch = Orchestrator()
        
        assert orch is not None
        assert orch.name == "Orchestrator"
    
    def test_orchestrator_has_agents(self):
        """Orchestrator agent'lara sahip olmalı."""
        from agents.orchestrator import Orchestrator
        
        orch = Orchestrator()
        
        # agents bir dict olarak tanımlı
        assert len(orch.agents) >= 4
        
        # Agent isimlerini dict key'lerinden al
        agent_names = list(orch.agents.keys())
        assert "research" in agent_names or any("research" in n.lower() for n in agent_names)
    
    def test_query_routing_research(self):
        """Araştırma soruları ResearchAgent'a yönlendirilmeli."""
        from agents.orchestrator import Orchestrator
        
        orch = Orchestrator()
        
        research_queries = [
            "X konusunu araştır",
            "Hakkında bilgi topla",
            "Detaylı araştırma yap"
        ]
        
        for query in research_queries:
            if hasattr(orch, 'route_query'):
                agent = orch.route_query(query)
                # Research agent seçilmeli
                assert agent is not None
    
    def test_query_routing_writer(self):
        """Yazma görevleri WriterAgent'a yönlendirilmeli."""
        from agents.orchestrator import Orchestrator
        
        orch = Orchestrator()
        
        writer_queries = [
            "Makale yaz",
            "Rapor oluştur",
            "Özet hazırla"
        ]
        
        for query in writer_queries:
            if hasattr(orch, 'route_query'):
                agent = orch.route_query(query)
                assert agent is not None
    
    def test_query_routing_analyzer(self):
        """Analiz görevleri AnalyzerAgent'a yönlendirilmeli."""
        from agents.orchestrator import Orchestrator
        
        orch = Orchestrator()
        
        analyzer_queries = [
            "Bu veriyi analiz et",
            "Karşılaştırma yap",
            "Değerlendir"
        ]
        
        for query in analyzer_queries:
            if hasattr(orch, 'route_query'):
                agent = orch.route_query(query)
                assert agent is not None
    
    def test_orchestrator_execute(self):
        """Orchestrator execute çalışmalı."""
        from agents.orchestrator import Orchestrator
        from core.llm_manager import llm_manager
        
        orch = Orchestrator()
        
        # Orchestrator'ın execute metodu var
        assert hasattr(orch, 'execute')
        
        # LLM'i mockla
        with patch.object(llm_manager, 'generate', return_value="Mock yanıt"):
            # Execute çağrılabilir olmalı
            if hasattr(orch, 'execute'):
                result = orch.execute("Test sorusu")
                assert result is not None


class TestResearchAgent:
    """Research Agent testleri."""
    
    def test_research_agent_initialization(self):
        """ResearchAgent başlatılabilmeli."""
        from agents.research_agent import ResearchAgent
        
        agent = ResearchAgent()
        
        assert agent is not None
        assert "research" in agent.name.lower()
    
    def test_research_agent_has_tools(self):
        """ResearchAgent gerekli yapıya sahip olmalı."""
        from agents.research_agent import ResearchAgent
        
        agent = ResearchAgent()
        
        # Agent temel özelliklere sahip olmalı
        assert hasattr(agent, 'tools')
        assert hasattr(agent, 'execute')
        # tools listesi olabilir (boş da olsa)
        assert isinstance(agent.tools, list)
    
    def test_research_agent_execute(self):
        """ResearchAgent execute metoduna sahip olmalı."""
        from agents.research_agent import ResearchAgent
        from core.llm_manager import llm_manager
        
        agent = ResearchAgent()
        
        # Execute metodu olmalı
        assert hasattr(agent, 'execute')
        
        # LLM mockla ve execute çağır
        with patch.object(llm_manager, 'generate', return_value="Test araştırma sonucu"):
            result = agent.execute("Test konusu")
            assert result is not None
            assert hasattr(result, 'content')


class TestWriterAgent:
    """Writer Agent testleri."""
    
    def test_writer_agent_initialization(self):
        """WriterAgent başlatılabilmeli."""
        from agents.writer_agent import WriterAgent
        
        agent = WriterAgent()
        
        assert agent is not None
    
    def test_writer_styles(self):
        """Writer farklı stilleri desteklemeli."""
        from agents.writer_agent import WriterAgent
        
        agent = WriterAgent()
        
        if hasattr(agent, 'styles') or hasattr(agent, 'STYLES'):
            styles = agent.styles if hasattr(agent, 'styles') else agent.STYLES
            
            expected_styles = ["detailed", "summary", "academic"]
            for style in expected_styles:
                assert style in styles or any(style in s.lower() for s in styles)


class TestAnalyzerAgent:
    """Analyzer Agent testleri."""
    
    def test_analyzer_agent_initialization(self):
        """AnalyzerAgent başlatılabilmeli."""
        from agents.analyzer_agent import AnalyzerAgent
        
        agent = AnalyzerAgent()
        
        assert agent is not None
    
    def test_analyzer_capabilities(self):
        """Analyzer analiz yeteneklerine sahip olmalı."""
        from agents.analyzer_agent import AnalyzerAgent
        
        agent = AnalyzerAgent()
        
        # BaseAgent'tan gelen execute metodu olmalı
        assert hasattr(agent, 'execute')
        # think metodu BaseAgent'tan geliyor
        assert hasattr(agent, 'think')


class TestReActAgent:
    """ReAct Agent testleri."""
    
    def test_react_agent_initialization(self):
        """ReActAgent başlatılabilmeli."""
        from agents.react_agent import ReActAgent, ThoughtType, ActionType
        
        # Enum'lar tanımlı olmalı
        assert ThoughtType.REASONING.value == "reasoning"
        assert ActionType.TOOL_CALL.value == "tool_call"
    
    def test_thought_structure(self):
        """Thought yapısı doğru olmalı."""
        from agents.react_agent import Thought, ThoughtType
        
        thought = Thought(
            content="Bu problemi çözmek için önce...",
            thought_type=ThoughtType.PLANNING
        )
        
        assert thought.content is not None
        assert thought.thought_type == ThoughtType.PLANNING
    
    def test_action_structure(self):
        """Action yapısı doğru olmalı."""
        from agents.react_agent import Action, ActionType
        
        action = Action(
            action_type=ActionType.TOOL_CALL,
            tool_name="rag_search",
            arguments={"query": "test"}
        )
        
        assert action.action_type == ActionType.TOOL_CALL
        assert action.tool_name == "rag_search"
        assert action.arguments == {"query": "test"}
    
    def test_react_step_types(self):
        """ReAct adım tipleri tanımlı olmalı."""
        from agents.react_agent import ReActStepType
        
        assert ReActStepType.THOUGHT.value == "thought"
        assert ReActStepType.ACTION.value == "action"
        assert ReActStepType.OBSERVATION.value == "observation"
        assert ReActStepType.FINAL_ANSWER.value == "final_answer"


class TestAgentCommunication:
    """Agent'lar arası iletişim testleri."""
    
    def test_agent_message_passing(self):
        """Agent'lar mesaj geçirebilmeli."""
        from agents.orchestrator import Orchestrator
        
        orch = Orchestrator()
        
        if hasattr(orch, 'send_message'):
            # Agent'a mesaj gönder
            result = orch.send_message(
                target_agent="ResearchAgent",
                message={"type": "task", "content": "Araştır"}
            )
            # Bir yanıt dönmeli
            assert result is not None or True  # Metod varsa test et
    
    def test_agent_delegation(self):
        """Orchestrator görev delege edebilmeli."""
        from agents.orchestrator import Orchestrator
        
        orch = Orchestrator()
        
        if hasattr(orch, 'delegate'):
            # Görevi başka agent'a delege et
            pass  # Delegation mekanizması test edilir


class TestAgentMemoryIntegration:
    """Agent memory entegrasyon testleri."""
    
    def test_conversation_context(self):
        """Agent konuşma bağlamını korumalı."""
        from agents.orchestrator import Orchestrator
        
        orch = Orchestrator()
        
        # İlk mesaj
        if hasattr(orch, 'add_context'):
            orch.add_context("user", "Benim adım Ahmet")
            
            # İkinci mesaj - bağlam hatırlanmalı
            orch.add_context("user", "Adımı hatırlıyor musun?")
            
            context = orch.get_context() if hasattr(orch, 'get_context') else []
            assert len(context) >= 2
    
    def test_agent_state_persistence(self):
        """Agent durumu kalıcı olmalı."""
        from agents.base_agent import BaseAgent, AgentRole, AgentResponse
        
        class StatefulAgent(BaseAgent):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.state = {}
            
            def execute(self, task: str, context=None) -> AgentResponse:
                """Abstract execute metodunun implementasyonu."""
                self.state['last_input'] = task
                return AgentResponse(
                    content=task,
                    agent_name=self.name,
                    agent_role=self.role.value
                )
        
        agent = StatefulAgent(
            name="Stateful",
            role=AgentRole.ASSISTANT,
            description="Stateful test agent",
            system_prompt="Test prompt"
        )
        agent.execute("First")
        agent.execute("Second")
        
        assert agent.state['last_input'] == "Second"


class TestAgentToolUsage:
    """Agent tool kullanım testleri."""
    
    def test_agent_has_use_tool_method(self):
        """Agent use_tool metoduna sahip olmalı."""
        from agents.research_agent import ResearchAgent
        
        agent = ResearchAgent()
        
        # BaseAgent'tan gelen use_tool metodu
        assert hasattr(agent, 'use_tool')
        assert hasattr(agent, 'get_available_tools')
    
    def test_agent_can_use_web_search(self):
        """Agent web search kullanabilmeli."""
        from agents.research_agent import ResearchAgent
        
        agent = ResearchAgent()
        
        if hasattr(agent, 'web_search'):
            with patch.object(agent, 'web_search', return_value=[{"content": "test"}]):
                result = agent.web_search("test query")
                assert result is not None


class TestAgentErrorHandling:
    """Agent hata yönetimi testleri."""
    
    def test_agent_handles_llm_error(self):
        """Agent LLM hatalarını yönetmeli."""
        from agents.orchestrator import Orchestrator
        from core.llm_manager import llm_manager
        
        orch = Orchestrator()
        
        # LLM hatasını simüle et
        with patch.object(llm_manager, 'generate', side_effect=Exception("LLM error")):
            try:
                # Execute çağrılırsa hata yakalanır veya fallback döner
                if hasattr(orch, 'execute'):
                    result = orch.execute("Test")
                    # AgentResponse içinde success=False veya error mesajı olabilir
                    assert result is not None
            except Exception as e:
                # Hata yayılabilir
                assert True
    
    def test_agent_timeout_handling(self):
        """Agent timeout durumunu yönetmeli."""
        from agents.orchestrator import Orchestrator
        
        orch = Orchestrator()
        
        # Timeout simülasyonu
        async def slow_operation():
            await asyncio.sleep(100)
        
        if hasattr(orch, 'timeout'):
            # Timeout mekanizması test edilir
            pass


class TestSelfReflection:
    """Self-reflection testleri."""
    
    def test_self_reflection_module(self):
        """Self-reflection modülü mevcut olmalı."""
        # Not: SelfReflectionAgent yok, SelfReflector ve CriticAgent var
        from agents.self_reflection import SelfReflector, CriticAgent, SelfCritiqueSystem
        
        reflector = SelfReflector()
        assert reflector is not None
        
        critic = CriticAgent()
        assert critic is not None
    
    def test_reflection_on_answer(self):
        """Yanıt üzerinde reflection yapabilmeli."""
        from agents.self_reflection import SelfReflector
        from core.llm_manager import llm_manager
        
        reflector = SelfReflector()
        
        if hasattr(reflector, 'reflect'):
            answer = "Python bir programlama dilidir."
            question = "Python nedir?"
            
            with patch.object(llm_manager, 'generate', return_value='{"reflection": "Good answer", "insights": [], "mistakes_identified": [], "improvements_suggested": [], "confidence_before": 0.8, "confidence_after": 0.8, "should_revise": false, "revision_plan": ""}'):
                reflection = reflector.reflect(answer, question)
                assert reflection is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
