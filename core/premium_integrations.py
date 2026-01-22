"""
Premium Integrations Module v1.0
================================

Daha önce kullanılmayan modülleri premium şekilde entegre eder:
- TaskQueue → Background işlemler, batch RAG, DeepScholar queue
- Workflow → Agent orchestration, multi-step pipelines
- QueryExpansion → RAG search enhancement
- Guardrails → API security, input/output validation
- RAGEvaluator → Quality assurance

Bu modül tüm entegrasyonları merkezi olarak yönetir.
"""

import asyncio
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from functools import wraps

from core.logger import get_logger

logger = get_logger("premium_integrations")


# ============================================================================
# 1. TASK QUEUE INTEGRATION - Background Jobs & Batch Processing
# ============================================================================

class PremiumTaskManager:
    """
    Premium task management - background processing için.
    
    Kullanım alanları:
    - DeepScholar document generation (queue)
    - Batch RAG indexing
    - Analytics report generation
    - Knowledge graph updates
    """
    
    def __init__(self):
        self._initialized = False
        self._task_queue = None
        self._task_registry = None
    
    def _lazy_init(self):
        """Lazy initialization."""
        if self._initialized:
            return
        
        from core.task_queue import task_queue, task_registry
        self._task_queue = task_queue
        self._task_registry = task_registry
        self._initialized = True
        
        # Register premium tasks
        self._register_premium_tasks()
        
        logger.info("PremiumTaskManager initialized")
    
    def _register_premium_tasks(self):
        """Premium task'ları kaydet."""
        
        @self._task_registry.register("deep_scholar_generate")
        async def deep_scholar_generate_task(
            document_id: str,
            workspace_id: str,
            config: Dict[str, Any]
        ) -> Dict:
            """DeepScholar döküman oluşturma task'ı."""
            from core.deep_scholar import deep_scholar_orchestrator
            
            try:
                result = await deep_scholar_orchestrator.generate_document(
                    workspace_id=workspace_id,
                    document_id=document_id,
                    **config
                )
                return {"status": "completed", "document_id": document_id, "result": result}
            except Exception as e:
                return {"status": "failed", "document_id": document_id, "error": str(e)}
        
        @self._task_registry.register("batch_rag_index")
        async def batch_rag_index_task(
            file_paths: List[str],
            workspace_id: Optional[str] = None
        ) -> Dict:
            """Toplu RAG indexleme task'ı."""
            from rag.async_processor import batch_processor
            
            results = []
            for file_path in file_paths:
                try:
                    result = await batch_processor.process_file(file_path)
                    results.append({"file": file_path, "status": "success", **result})
                except Exception as e:
                    results.append({"file": file_path, "status": "error", "error": str(e)})
            
            return {
                "total": len(file_paths),
                "success": sum(1 for r in results if r["status"] == "success"),
                "failed": sum(1 for r in results if r["status"] == "error"),
                "results": results
            }
        
        @self._task_registry.register("analytics_report")
        async def analytics_report_task(
            report_type: str = "daily",
            days: int = 7
        ) -> Dict:
            """Analytics raporu oluştur."""
            from core.analytics import analytics
            
            return {
                "type": report_type,
                "days": days,
                "stats": analytics.get_stats(days=days),
                "generated_at": datetime.now().isoformat()
            }
        
        @self._task_registry.register("rag_quality_check")
        async def rag_quality_check_task(
            sample_queries: List[str]
        ) -> Dict:
            """RAG kalite kontrolü task'ı."""
            from rag.evaluation import rag_evaluator
            from core.vector_store import vector_store
            from core.llm_manager import llm_manager
            
            results = []
            for query in sample_queries:
                # Retrieve
                docs = vector_store.search_with_scores(query, n_results=5)
                contexts = [d.get("document", "") for d in docs]
                
                # Generate
                context_text = "\n\n".join(contexts)
                answer = llm_manager.generate(
                    f"Bağlam:\n{context_text}\n\nSoru: {query}\n\nCevap:"
                )
                
                # Evaluate
                report = rag_evaluator.evaluate_full(
                    query=query,
                    contexts=contexts,
                    answer=answer
                )
                
                results.append({
                    "query": query,
                    "score": report.overall_score,
                    "metrics": {k: v.score for k, v in report.metrics.items()}
                })
            
            avg_score = sum(r["score"] for r in results) / len(results) if results else 0
            
            return {
                "samples": len(sample_queries),
                "average_score": avg_score,
                "results": results
            }
        
        logger.info("Premium tasks registered: deep_scholar_generate, batch_rag_index, analytics_report, rag_quality_check")
    
    async def submit_task(
        self,
        task_name: str,
        *args,
        priority: str = "normal",
        **kwargs
    ) -> str:
        """Task'ı kuyruğa ekle."""
        self._lazy_init()
        
        from core.task_queue import TaskPriority
        
        priority_map = {
            "low": TaskPriority.LOW,
            "normal": TaskPriority.NORMAL,
            "high": TaskPriority.HIGH,
            "critical": TaskPriority.CRITICAL
        }
        
        task_id = await self._task_queue.submit(
            task_name,
            *args,
            priority=priority_map.get(priority, TaskPriority.NORMAL),
            **kwargs
        )
        
        logger.info(f"Task submitted: {task_name} -> {task_id}")
        return task_id
    
    async def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Task durumunu al."""
        self._lazy_init()
        
        task = self._task_queue.get_task(task_id)
        if task:
            return task.to_dict()
        return None
    
    async def wait_for_task(self, task_id: str, timeout: float = None) -> Optional[Dict]:
        """Task'ın tamamlanmasını bekle."""
        self._lazy_init()
        
        result = await self._task_queue.wait_for_task(task_id, timeout=timeout)
        if result:
            return result.to_dict()
        return None
    
    def get_queue_stats(self) -> Dict:
        """Queue istatistiklerini al."""
        self._lazy_init()
        return self._task_queue.get_stats()
    
    async def start_workers(self):
        """Worker'ları başlat."""
        self._lazy_init()
        await self._task_queue.start()
        logger.info("Task queue workers started")
    
    async def stop_workers(self, wait: bool = True):
        """Worker'ları durdur."""
        if self._task_queue:
            await self._task_queue.stop(wait=wait)
            logger.info("Task queue workers stopped")


# ============================================================================
# 2. WORKFLOW INTEGRATION - Agent Orchestration & Pipelines
# ============================================================================

class PremiumWorkflowEngine:
    """
    Premium workflow engine - multi-step agent orchestration.
    
    Kullanım alanları:
    - RAG pipeline execution
    - Multi-agent task routing
    - Complex query processing
    """
    
    def __init__(self):
        self._rag_workflow = None
        self._agent_workflow = None
        self._custom_workflows = {}
    
    def _lazy_init(self):
        """Lazy initialization."""
        if self._rag_workflow is not None:
            return
        
        from core.workflow import rag_workflow, agent_workflow, WorkflowBuilder, NodeType
        
        self._rag_workflow = rag_workflow
        self._agent_workflow = agent_workflow
        self._WorkflowBuilder = WorkflowBuilder
        self._NodeType = NodeType
        
        logger.info("PremiumWorkflowEngine initialized with RAG and Agent workflows")
    
    async def run_rag_workflow(
        self,
        query: str,
        **kwargs
    ) -> Dict[str, Any]:
        """RAG workflow'u çalıştır."""
        self._lazy_init()
        
        initial_state = {"query": query, **kwargs}
        result = await self._rag_workflow.run(initial_state)
        
        return {
            "query": query,
            "response": result.get("response"),
            "retrieved_docs": result.get("retrieved_docs", []),
            "history": result.history,
            "is_complete": result.is_complete,
            "errors": result.errors
        }
    
    async def run_agent_workflow(
        self,
        query: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Agent routing workflow'u çalıştır."""
        self._lazy_init()
        
        initial_state = {"query": query, **kwargs}
        result = await self._agent_workflow.run(initial_state)
        
        return {
            "query": query,
            "agent_type": result.get("agent_type"),
            "response": result.get("response"),
            "history": result.history,
            "is_complete": result.is_complete
        }
    
    def create_custom_workflow(
        self,
        name: str,
        steps: List[Dict[str, Any]]
    ) -> str:
        """Custom workflow oluştur."""
        self._lazy_init()
        
        builder = self._WorkflowBuilder(name)
        
        for i, step in enumerate(steps):
            node_name = step.get("name", f"step_{i}")
            node_type = self._NodeType.AGENT
            handler = step.get("handler")
            
            builder.add_node(node_name, node_type, handler)
            
            if i == 0:
                builder.set_entry_point(node_name)
            elif i == len(steps) - 1:
                builder.set_finish_point(node_name)
            else:
                prev_node = steps[i-1].get("name", f"step_{i-1}")
                builder.add_edge(prev_node, node_name)
        
        workflow = builder.build()
        self._custom_workflows[name] = workflow
        
        logger.info(f"Custom workflow created: {name}")
        return name
    
    async def run_custom_workflow(
        self,
        name: str,
        initial_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Custom workflow çalıştır."""
        if name not in self._custom_workflows:
            raise ValueError(f"Workflow not found: {name}")
        
        result = await self._custom_workflows[name].run(initial_state)
        
        return {
            "workflow": name,
            "data": result.data,
            "history": result.history,
            "is_complete": result.is_complete,
            "errors": result.errors
        }


# ============================================================================
# 3. QUERY EXPANSION INTEGRATION - Enhanced RAG Search
# ============================================================================

class PremiumQueryExpander:
    """
    Premium query expansion - RAG search enhancement.
    
    Kullanım alanları:
    - Multi-query search
    - Synonym expansion
    - HyDE (Hypothetical Document Embeddings)
    - Keyword extraction
    """
    
    def __init__(self):
        self._manager = None
        self._llm_func = None
    
    def _lazy_init(self):
        """Lazy initialization."""
        if self._manager is not None:
            return
        
        from rag.query_expansion import QueryExpansionManager, ExpansionStrategy
        from core.llm_manager import llm_manager
        
        # LLM wrapper for async
        async def llm_wrapper(prompt: str) -> str:
            return llm_manager.generate(prompt, max_tokens=200)
        
        self._llm_func = llm_wrapper
        
        self._manager = QueryExpansionManager(
            llm_func=llm_wrapper,
            strategies=[
                ExpansionStrategy.SYNONYM,
                ExpansionStrategy.KEYWORD,
                ExpansionStrategy.MULTI_QUERY
            ],
            max_total_queries=8
        )
        
        self._ExpansionStrategy = ExpansionStrategy
        
        logger.info("PremiumQueryExpander initialized with SYNONYM, KEYWORD, MULTI_QUERY strategies")
    
    async def expand_query(
        self,
        query: str,
        strategies: List[str] = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Sorguyu genişlet."""
        self._lazy_init()
        
        strategy_objs = None
        if strategies:
            strategy_objs = [
                getattr(self._ExpansionStrategy, s.upper())
                for s in strategies
                if hasattr(self._ExpansionStrategy, s.upper())
            ]
        
        result = await self._manager.expand(query, strategies=strategy_objs, context=context)
        
        return result
    
    async def search_with_expansion(
        self,
        query: str,
        retrieval_func: Callable,
        top_k: int = 5
    ) -> List[Any]:
        """Genişletilmiş sorgularla arama yap."""
        self._lazy_init()
        
        results = await self._manager.expand_for_retrieval(
            query=query,
            retrieval_func=retrieval_func,
            top_k=top_k
        )
        
        return results


# ============================================================================
# 4. GUARDRAILS INTEGRATION - API Security & Validation
# ============================================================================

class PremiumGuardrails:
    """
    Premium guardrails - input/output security.
    
    Kullanım alanları:
    - Prompt injection detection
    - PII masking
    - Output hallucination check
    - Content safety
    """
    
    def __init__(self):
        self._guardrails = None
        self._level = None
    
    def _lazy_init(self, level: str = "medium"):
        """Lazy initialization."""
        if self._guardrails is not None and self._level == level:
            return
        
        from core.guardrails import Guardrails, GuardLevel
        
        level_map = {
            "low": GuardLevel.LOW,
            "medium": GuardLevel.MEDIUM,
            "high": GuardLevel.HIGH,
            "strict": GuardLevel.STRICT
        }
        
        self._guardrails = Guardrails(level_map.get(level, GuardLevel.MEDIUM))
        self._level = level
        
        logger.info(f"PremiumGuardrails initialized with level: {level}")
    
    def check_input(
        self,
        text: str,
        level: str = "medium"
    ) -> Dict[str, Any]:
        """Girişi kontrol et."""
        self._lazy_init(level)
        
        result = self._guardrails.check_input(text)
        
        return {
            "is_safe": result.is_safe,
            "violations": result.violations,
            "filtered_content": result.filtered_content,
            "confidence": result.confidence
        }
    
    def check_output(
        self,
        output: str,
        context: str = None,
        expected_format: str = None,
        level: str = "medium"
    ) -> Dict[str, Any]:
        """Çıkışı kontrol et."""
        self._lazy_init(level)
        
        result = self._guardrails.check_output(output, context, expected_format)
        
        return {
            "is_safe": result.is_safe,
            "violations": result.violations,
            "confidence": result.confidence
        }
    
    def safe_generate(
        self,
        llm_func: Callable,
        prompt: str,
        context: str = None,
        level: str = "medium",
        **kwargs
    ) -> Tuple[str, Dict, Dict]:
        """Güvenli LLM çağrısı."""
        self._lazy_init(level)
        
        output, input_result, output_result = self._guardrails.safe_generate(
            llm_func=llm_func,
            prompt=prompt,
            context=context,
            **kwargs
        )
        
        return output, input_result.to_dict(), output_result.to_dict()
    
    def add_custom_validator(
        self,
        validator: Callable[[str], Optional[Dict]]
    ):
        """Özel validator ekle."""
        self._lazy_init()
        self._guardrails.add_validator(validator)


# ============================================================================
# 5. RAG EVALUATION INTEGRATION - Quality Assurance
# ============================================================================

class PremiumRAGEvaluator:
    """
    Premium RAG evaluation - quality assurance.
    
    Kullanım alanları:
    - Context relevance scoring
    - Faithfulness checking
    - Answer quality metrics
    - Batch evaluation
    """
    
    def __init__(self):
        self._evaluator = None
        self._batch_evaluator = None
    
    def _lazy_init(self):
        """Lazy initialization."""
        if self._evaluator is not None:
            return
        
        from rag.evaluation import RAGEvaluator, BatchEvaluator
        
        self._evaluator = RAGEvaluator()
        self._batch_evaluator = BatchEvaluator()
        
        logger.info("PremiumRAGEvaluator initialized")
    
    def evaluate_context_relevance(
        self,
        query: str,
        contexts: List[str]
    ) -> Dict[str, Any]:
        """Context relevance değerlendir."""
        self._lazy_init()
        
        result = self._evaluator.evaluate_context_relevance(query, contexts)
        
        return {
            "metric": result.metric,
            "score": result.score,
            "details": result.details
        }
    
    def evaluate_faithfulness(
        self,
        answer: str,
        contexts: List[str]
    ) -> Dict[str, Any]:
        """Faithfulness değerlendir."""
        self._lazy_init()
        
        result = self._evaluator.evaluate_faithfulness(answer, contexts)
        
        return {
            "metric": result.metric,
            "score": result.score,
            "details": result.details
        }
    
    def evaluate_answer_relevance(
        self,
        query: str,
        answer: str
    ) -> Dict[str, Any]:
        """Answer relevance değerlendir."""
        self._lazy_init()
        
        result = self._evaluator.evaluate_answer_relevance(query, answer)
        
        return {
            "metric": result.metric,
            "score": result.score,
            "details": result.details
        }
    
    def evaluate_full(
        self,
        query: str,
        contexts: List[str],
        answer: str,
        ground_truth: str = None
    ) -> Dict[str, Any]:
        """Tam RAG değerlendirmesi."""
        self._lazy_init()
        
        report = self._evaluator.evaluate_full(query, contexts, answer, ground_truth)
        
        return {
            "query": report.query,
            "overall_score": report.overall_score,
            "metrics": {k: {"score": v.score, "details": v.details} for k, v in report.metrics.items()},
            "retrieved_docs_count": len(report.retrieved_docs),
            "answer_length": len(report.generated_answer)
        }
    
    def add_evaluation_sample(
        self,
        query: str,
        contexts: List[str],
        answer: str,
        ground_truth: str = None
    ):
        """Batch evaluation'a örnek ekle."""
        self._lazy_init()
        self._batch_evaluator.add_sample(query, contexts, answer, ground_truth)
    
    def get_batch_summary(self) -> Dict[str, Any]:
        """Batch evaluation özeti."""
        self._lazy_init()
        return self._batch_evaluator.get_summary()


# ============================================================================
# 6. UNIFIED PREMIUM INTEGRATION MANAGER
# ============================================================================

class PremiumIntegrationManager:
    """
    Tüm premium entegrasyonları yöneten merkezi manager.
    
    Kullanım:
        from core.premium_integrations import premium_manager
        
        # Task Queue
        task_id = await premium_manager.tasks.submit_task("batch_rag_index", file_paths)
        
        # Workflow
        result = await premium_manager.workflows.run_rag_workflow(query)
        
        # Query Expansion
        expanded = await premium_manager.query_expander.expand_query(query)
        
        # Guardrails
        check = premium_manager.guardrails.check_input(user_input)
        
        # RAG Evaluation
        score = premium_manager.evaluator.evaluate_full(query, contexts, answer)
    """
    
    def __init__(self):
        self._tasks = None
        self._workflows = None
        self._query_expander = None
        self._guardrails = None
        self._evaluator = None
    
    @property
    def tasks(self) -> PremiumTaskManager:
        """Task queue manager."""
        if self._tasks is None:
            self._tasks = PremiumTaskManager()
        return self._tasks
    
    @property
    def workflows(self) -> PremiumWorkflowEngine:
        """Workflow engine."""
        if self._workflows is None:
            self._workflows = PremiumWorkflowEngine()
        return self._workflows
    
    @property
    def query_expander(self) -> PremiumQueryExpander:
        """Query expansion manager."""
        if self._query_expander is None:
            self._query_expander = PremiumQueryExpander()
        return self._query_expander
    
    @property
    def guardrails(self) -> PremiumGuardrails:
        """Guardrails manager."""
        if self._guardrails is None:
            self._guardrails = PremiumGuardrails()
        return self._guardrails
    
    @property
    def evaluator(self) -> PremiumRAGEvaluator:
        """RAG evaluator."""
        if self._evaluator is None:
            self._evaluator = PremiumRAGEvaluator()
        return self._evaluator
    
    async def initialize_all(self):
        """Tüm modülleri önceden yükle."""
        self.tasks._lazy_init()
        self.workflows._lazy_init()
        self.query_expander._lazy_init()
        self.guardrails._lazy_init()
        self.evaluator._lazy_init()
        
        # Task workers'ı başlat
        await self.tasks.start_workers()
        
        logger.info("All premium integrations initialized")
    
    async def shutdown(self):
        """Tüm modülleri kapat."""
        await self.tasks.stop_workers()
        logger.info("Premium integrations shut down")
    
    def get_status(self) -> Dict[str, Any]:
        """Tüm modüllerin durumunu al."""
        return {
            "tasks": {
                "initialized": self._tasks is not None and self._tasks._initialized,
                "stats": self._tasks.get_queue_stats() if self._tasks and self._tasks._initialized else None
            },
            "workflows": {
                "initialized": self._workflows is not None and self._workflows._rag_workflow is not None,
                "custom_workflows": list(self._workflows._custom_workflows.keys()) if self._workflows else []
            },
            "query_expander": {
                "initialized": self._query_expander is not None and self._query_expander._manager is not None
            },
            "guardrails": {
                "initialized": self._guardrails is not None and self._guardrails._guardrails is not None,
                "level": self._guardrails._level if self._guardrails else None
            },
            "evaluator": {
                "initialized": self._evaluator is not None and self._evaluator._evaluator is not None
            }
        }


# Singleton instance
premium_manager = PremiumIntegrationManager()


# ============================================================================
# DECORATORS - Easy Integration
# ============================================================================

def with_guardrails(level: str = "medium"):
    """
    Decorator: Fonksiyona guardrails ekle.
    
    Kullanım:
        @with_guardrails("high")
        async def process_user_input(text: str):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # İlk argüman text olarak kabul et
            if args:
                text = args[0]
                check = premium_manager.guardrails.check_input(text, level)
                
                if not check["is_safe"]:
                    return {
                        "error": "Input validation failed",
                        "violations": check["violations"]
                    }
                
                # Filtered content varsa onu kullan
                if check["filtered_content"]:
                    args = (check["filtered_content"],) + args[1:]
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def with_query_expansion():
    """
    Decorator: Sorgu genişletme ekle.
    
    Kullanım:
        @with_query_expansion()
        async def search(query: str, top_k: int = 5):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(query: str, *args, **kwargs):
            # Sorguyu genişlet
            expansion = await premium_manager.query_expander.expand_query(query)
            
            # Tüm sorgularla arama yap
            all_results = []
            for q in expansion.get("all_queries", [query]):
                results = await func(q, *args, **kwargs)
                if isinstance(results, list):
                    all_results.extend(results)
            
            # Duplicate'ları kaldır
            seen = set()
            unique_results = []
            for r in all_results:
                r_hash = hash(str(r)[:200])
                if r_hash not in seen:
                    seen.add(r_hash)
                    unique_results.append(r)
            
            return unique_results
        return wrapper
    return decorator


def as_background_task(task_name: str, priority: str = "normal"):
    """
    Decorator: Fonksiyonu background task olarak çalıştır.
    
    Kullanım:
        @as_background_task("my_heavy_task", priority="high")
        async def heavy_computation(...):
            ...
    """
    def decorator(func: Callable):
        # Task'ı kaydet
        premium_manager.tasks._lazy_init()
        premium_manager.tasks._task_registry.register(task_name)(func)
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Task olarak submit et
            task_id = await premium_manager.tasks.submit_task(
                task_name,
                *args,
                priority=priority,
                **kwargs
            )
            return {"task_id": task_id, "status": "submitted"}
        
        return wrapper
    return decorator


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Managers
    "PremiumTaskManager",
    "PremiumWorkflowEngine",
    "PremiumQueryExpander",
    "PremiumGuardrails",
    "PremiumRAGEvaluator",
    "PremiumIntegrationManager",
    # Singleton
    "premium_manager",
    # Decorators
    "with_guardrails",
    "with_query_expansion",
    "as_background_task",
]
