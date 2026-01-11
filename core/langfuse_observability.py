"""
📊 Langfuse Observability - Enterprise-Grade LLM Monitoring
===========================================================

Langfuse entegrasyonu ile full-stack LLM observability:
- Trace & Span tracking
- Token usage & cost monitoring
- Latency analysis
- Quality metrics
- Prompt versioning
- A/B testing support

Langfuse Cloud veya Self-hosted destekler.
"""

import asyncio
import hashlib
import json
import os
import time
import uuid
from abc import ABC, abstractmethod
from contextlib import contextmanager, asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
import threading

# Optional Langfuse import
try:
    from langfuse import Langfuse
    from langfuse.decorators import langfuse_context, observe
    from langfuse.model import CreateScore
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    Langfuse = None
    observe = lambda *args, **kwargs: lambda f: f  # No-op decorator

from core.config import settings


# ============ ENUMS & TYPES ============

class ObservationType(str, Enum):
    """Observation types"""
    SPAN = "span"
    GENERATION = "generation"
    EVENT = "event"


class SpanLevel(str, Enum):
    """Log levels for spans"""
    DEBUG = "DEBUG"
    DEFAULT = "DEFAULT"
    WARNING = "WARNING"
    ERROR = "ERROR"


class ModelProvider(str, Enum):
    """LLM providers for cost calculation"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"
    OLLAMA = "ollama"
    LOCAL = "local"
    CUSTOM = "custom"


# ============ DATA CLASSES ============

@dataclass
class TokenUsage:
    """Token usage tracking"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    
    @property
    def cost_estimate_usd(self) -> float:
        """Rough cost estimate (GPT-4 pricing as baseline)"""
        input_cost = self.prompt_tokens * 0.00003  # $0.03/1K
        output_cost = self.completion_tokens * 0.00006  # $0.06/1K
        return input_cost + output_cost


@dataclass
class GenerationMetadata:
    """Generation call metadata"""
    model: str
    provider: ModelProvider
    model_parameters: Dict[str, Any] = field(default_factory=dict)
    prompt: Optional[str] = None
    prompt_template: Optional[str] = None
    prompt_template_version: Optional[str] = None
    completion: Optional[str] = None
    usage: Optional[TokenUsage] = None
    latency_ms: float = 0
    finish_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TraceMetadata:
    """Full trace metadata"""
    trace_id: str
    name: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    version: Optional[str] = None
    release: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    public: bool = False
    input: Optional[Any] = None
    output: Optional[Any] = None
    level: SpanLevel = SpanLevel.DEFAULT
    status_message: Optional[str] = None


@dataclass
class Score:
    """Quality/evaluation score"""
    name: str
    value: float
    trace_id: str
    observation_id: Optional[str] = None
    comment: Optional[str] = None
    data_type: str = "NUMERIC"  # NUMERIC, BOOLEAN, CATEGORICAL


# ============ ABSTRACT OBSERVER ============

class ObservabilityBackend(ABC):
    """Abstract observability backend"""
    
    @abstractmethod
    def start_trace(self, name: str, **kwargs) -> str:
        """Start a new trace"""
        pass
    
    @abstractmethod
    def end_trace(self, trace_id: str, **kwargs):
        """End a trace"""
        pass
    
    @abstractmethod
    def start_span(self, name: str, trace_id: str, **kwargs) -> str:
        """Start a new span within a trace"""
        pass
    
    @abstractmethod
    def end_span(self, span_id: str, **kwargs):
        """End a span"""
        pass
    
    @abstractmethod
    def log_generation(self, trace_id: str, generation: GenerationMetadata, **kwargs):
        """Log an LLM generation"""
        pass
    
    @abstractmethod
    def log_event(self, trace_id: str, name: str, **kwargs):
        """Log an event"""
        pass
    
    @abstractmethod
    def add_score(self, score: Score):
        """Add a quality score"""
        pass
    
    @abstractmethod
    def flush(self):
        """Flush any pending data"""
        pass


# ============ LANGFUSE BACKEND ============

class LangfuseBackend(ObservabilityBackend):
    """
    Langfuse observability backend
    
    Production-grade LLM monitoring with:
    - Full tracing
    - Token/cost tracking
    - Quality scores
    - Prompt management
    """
    
    def __init__(
        self,
        public_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        host: Optional[str] = None,
        release: Optional[str] = None,
        debug: bool = False
    ):
        if not LANGFUSE_AVAILABLE:
            raise ImportError("langfuse package not installed. Run: pip install langfuse")
        
        self.public_key = public_key or os.getenv("LANGFUSE_PUBLIC_KEY")
        self.secret_key = secret_key or os.getenv("LANGFUSE_SECRET_KEY")
        self.host = host or os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
        self.release = release or os.getenv("LANGFUSE_RELEASE", "1.0.0")
        self.debug = debug
        
        # Initialize Langfuse client
        self.client = Langfuse(
            public_key=self.public_key,
            secret_key=self.secret_key,
            host=self.host,
            release=self.release,
            debug=debug
        )
        
        # Active traces and spans
        self._traces: Dict[str, Any] = {}
        self._spans: Dict[str, Any] = {}
        self._lock = threading.Lock()
    
    def start_trace(
        self,
        name: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        input: Optional[Any] = None,
        metadata: Optional[Dict] = None,
        tags: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """Start a new trace in Langfuse"""
        trace = self.client.trace(
            name=name,
            user_id=user_id,
            session_id=session_id,
            input=input,
            metadata=metadata or {},
            tags=tags or [],
            release=self.release
        )
        
        trace_id = trace.id
        
        with self._lock:
            self._traces[trace_id] = trace
        
        return trace_id
    
    def end_trace(
        self,
        trace_id: str,
        output: Optional[Any] = None,
        level: Optional[SpanLevel] = None,
        status_message: Optional[str] = None,
        **kwargs
    ):
        """End a trace"""
        with self._lock:
            trace = self._traces.get(trace_id)
        
        if trace:
            trace.update(
                output=output,
                level=level.value if level else None,
                status_message=status_message
            )
    
    def start_span(
        self,
        name: str,
        trace_id: str,
        parent_span_id: Optional[str] = None,
        input: Optional[Any] = None,
        metadata: Optional[Dict] = None,
        **kwargs
    ) -> str:
        """Start a new span within a trace"""
        with self._lock:
            trace = self._traces.get(trace_id)
        
        if not trace:
            raise ValueError(f"Trace not found: {trace_id}")
        
        span = trace.span(
            name=name,
            input=input,
            metadata=metadata or {},
            parent_observation_id=parent_span_id
        )
        
        span_id = span.id
        
        with self._lock:
            self._spans[span_id] = span
        
        return span_id
    
    def end_span(
        self,
        span_id: str,
        output: Optional[Any] = None,
        level: Optional[SpanLevel] = None,
        status_message: Optional[str] = None,
        **kwargs
    ):
        """End a span"""
        with self._lock:
            span = self._spans.get(span_id)
        
        if span:
            span.end(
                output=output,
                level=level.value if level else None,
                status_message=status_message
            )
    
    def log_generation(
        self,
        trace_id: str,
        generation: GenerationMetadata,
        parent_span_id: Optional[str] = None,
        **kwargs
    ):
        """Log an LLM generation to Langfuse"""
        with self._lock:
            trace = self._traces.get(trace_id)
            parent = self._spans.get(parent_span_id) if parent_span_id else trace
        
        if not parent:
            return
        
        # Build usage dict
        usage_dict = None
        if generation.usage:
            usage_dict = {
                "input": generation.usage.prompt_tokens,
                "output": generation.usage.completion_tokens,
                "total": generation.usage.total_tokens
            }
        
        gen = parent.generation(
            name=generation.model,
            model=generation.model,
            model_parameters=generation.model_parameters,
            input=generation.prompt,
            output=generation.completion,
            usage=usage_dict,
            metadata={
                "provider": generation.provider.value,
                "latency_ms": generation.latency_ms,
                "finish_reason": generation.finish_reason,
                "prompt_template": generation.prompt_template,
                "prompt_template_version": generation.prompt_template_version,
                **generation.metadata
            }
        )
        
        gen.end()
    
    def log_event(
        self,
        trace_id: str,
        name: str,
        input: Optional[Any] = None,
        output: Optional[Any] = None,
        level: Optional[SpanLevel] = None,
        metadata: Optional[Dict] = None,
        parent_span_id: Optional[str] = None,
        **kwargs
    ):
        """Log an event"""
        with self._lock:
            trace = self._traces.get(trace_id)
            parent = self._spans.get(parent_span_id) if parent_span_id else trace
        
        if parent:
            parent.event(
                name=name,
                input=input,
                output=output,
                level=level.value if level else None,
                metadata=metadata or {}
            )
    
    def add_score(self, score: Score):
        """Add a quality score to Langfuse"""
        self.client.score(
            trace_id=score.trace_id,
            observation_id=score.observation_id,
            name=score.name,
            value=score.value,
            comment=score.comment,
            data_type=score.data_type
        )
    
    def flush(self):
        """Flush pending data to Langfuse"""
        self.client.flush()
    
    def shutdown(self):
        """Shutdown the client"""
        self.flush()
        self.client.shutdown()


# ============ LOCAL/FALLBACK BACKEND ============

class LocalObservabilityBackend(ObservabilityBackend):
    """
    Local observability backend (SQLite + JSON logs)
    
    Fallback when Langfuse is not configured.
    Still provides useful debugging and analysis.
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or (settings.DATA_DIR / "observability")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.traces_file = self.data_dir / "traces.jsonl"
        self.generations_file = self.data_dir / "generations.jsonl"
        self.scores_file = self.data_dir / "scores.jsonl"
        
        self._traces: Dict[str, Dict] = {}
        self._spans: Dict[str, Dict] = {}
        self._lock = threading.Lock()
        
        # Initialize SQLite for querying
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database"""
        import sqlite3
        
        db_path = self.data_dir / "observability.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Create tables
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS traces (
                id TEXT PRIMARY KEY,
                name TEXT,
                user_id TEXT,
                session_id TEXT,
                input TEXT,
                output TEXT,
                metadata TEXT,
                tags TEXT,
                level TEXT,
                status_message TEXT,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                duration_ms REAL
            );
            
            CREATE TABLE IF NOT EXISTS spans (
                id TEXT PRIMARY KEY,
                trace_id TEXT,
                parent_id TEXT,
                name TEXT,
                input TEXT,
                output TEXT,
                metadata TEXT,
                level TEXT,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                duration_ms REAL,
                FOREIGN KEY (trace_id) REFERENCES traces(id)
            );
            
            CREATE TABLE IF NOT EXISTS generations (
                id TEXT PRIMARY KEY,
                trace_id TEXT,
                span_id TEXT,
                model TEXT,
                provider TEXT,
                prompt TEXT,
                completion TEXT,
                prompt_tokens INTEGER,
                completion_tokens INTEGER,
                total_tokens INTEGER,
                latency_ms REAL,
                cost_usd REAL,
                metadata TEXT,
                timestamp TIMESTAMP,
                FOREIGN KEY (trace_id) REFERENCES traces(id)
            );
            
            CREATE TABLE IF NOT EXISTS scores (
                id TEXT PRIMARY KEY,
                trace_id TEXT,
                observation_id TEXT,
                name TEXT,
                value REAL,
                comment TEXT,
                data_type TEXT,
                timestamp TIMESTAMP,
                FOREIGN KEY (trace_id) REFERENCES traces(id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_traces_user ON traces(user_id);
            CREATE INDEX IF NOT EXISTS idx_traces_session ON traces(session_id);
            CREATE INDEX IF NOT EXISTS idx_spans_trace ON spans(trace_id);
            CREATE INDEX IF NOT EXISTS idx_generations_trace ON generations(trace_id);
            CREATE INDEX IF NOT EXISTS idx_scores_trace ON scores(trace_id);
        """)
        
        conn.commit()
        conn.close()
    
    def _get_db(self):
        """Get database connection"""
        import sqlite3
        db_path = self.data_dir / "observability.db"
        return sqlite3.connect(str(db_path))
    
    def start_trace(
        self,
        name: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        input: Optional[Any] = None,
        metadata: Optional[Dict] = None,
        tags: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        trace_id = str(uuid.uuid4())
        
        trace_data = {
            "id": trace_id,
            "name": name,
            "user_id": user_id,
            "session_id": session_id,
            "input": input,
            "metadata": metadata or {},
            "tags": tags or [],
            "start_time": datetime.now().isoformat(),
            "spans": [],
            "generations": [],
            "events": []
        }
        
        with self._lock:
            self._traces[trace_id] = trace_data
        
        return trace_id
    
    def end_trace(
        self,
        trace_id: str,
        output: Optional[Any] = None,
        level: Optional[SpanLevel] = None,
        status_message: Optional[str] = None,
        **kwargs
    ):
        with self._lock:
            trace = self._traces.get(trace_id)
        
        if trace:
            end_time = datetime.now()
            start_time = datetime.fromisoformat(trace["start_time"])
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            trace["end_time"] = end_time.isoformat()
            trace["duration_ms"] = duration_ms
            trace["output"] = output
            trace["level"] = level.value if level else "DEFAULT"
            trace["status_message"] = status_message
            
            # Save to files and DB
            self._save_trace(trace)
    
    def start_span(
        self,
        name: str,
        trace_id: str,
        parent_span_id: Optional[str] = None,
        input: Optional[Any] = None,
        metadata: Optional[Dict] = None,
        **kwargs
    ) -> str:
        span_id = str(uuid.uuid4())
        
        span_data = {
            "id": span_id,
            "trace_id": trace_id,
            "parent_id": parent_span_id,
            "name": name,
            "input": input,
            "metadata": metadata or {},
            "start_time": datetime.now().isoformat()
        }
        
        with self._lock:
            self._spans[span_id] = span_data
            if trace_id in self._traces:
                self._traces[trace_id]["spans"].append(span_data)
        
        return span_id
    
    def end_span(
        self,
        span_id: str,
        output: Optional[Any] = None,
        level: Optional[SpanLevel] = None,
        status_message: Optional[str] = None,
        **kwargs
    ):
        with self._lock:
            span = self._spans.get(span_id)
        
        if span:
            end_time = datetime.now()
            start_time = datetime.fromisoformat(span["start_time"])
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            span["end_time"] = end_time.isoformat()
            span["duration_ms"] = duration_ms
            span["output"] = output
            span["level"] = level.value if level else "DEFAULT"
    
    def log_generation(
        self,
        trace_id: str,
        generation: GenerationMetadata,
        parent_span_id: Optional[str] = None,
        **kwargs
    ):
        gen_id = str(uuid.uuid4())
        
        gen_data = {
            "id": gen_id,
            "trace_id": trace_id,
            "span_id": parent_span_id,
            "model": generation.model,
            "provider": generation.provider.value,
            "prompt": generation.prompt,
            "completion": generation.completion,
            "prompt_tokens": generation.usage.prompt_tokens if generation.usage else 0,
            "completion_tokens": generation.usage.completion_tokens if generation.usage else 0,
            "total_tokens": generation.usage.total_tokens if generation.usage else 0,
            "latency_ms": generation.latency_ms,
            "cost_usd": generation.usage.cost_estimate_usd if generation.usage else 0,
            "metadata": generation.metadata,
            "timestamp": datetime.now().isoformat()
        }
        
        with self._lock:
            if trace_id in self._traces:
                self._traces[trace_id]["generations"].append(gen_data)
        
        # Append to JSONL file
        with open(self.generations_file, "a") as f:
            f.write(json.dumps(gen_data) + "\n")
    
    def log_event(
        self,
        trace_id: str,
        name: str,
        input: Optional[Any] = None,
        output: Optional[Any] = None,
        level: Optional[SpanLevel] = None,
        metadata: Optional[Dict] = None,
        **kwargs
    ):
        event_data = {
            "id": str(uuid.uuid4()),
            "trace_id": trace_id,
            "name": name,
            "input": input,
            "output": output,
            "level": level.value if level else "DEFAULT",
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }
        
        with self._lock:
            if trace_id in self._traces:
                self._traces[trace_id]["events"].append(event_data)
    
    def add_score(self, score: Score):
        score_data = {
            "id": str(uuid.uuid4()),
            "trace_id": score.trace_id,
            "observation_id": score.observation_id,
            "name": score.name,
            "value": score.value,
            "comment": score.comment,
            "data_type": score.data_type,
            "timestamp": datetime.now().isoformat()
        }
        
        # Append to JSONL file
        with open(self.scores_file, "a") as f:
            f.write(json.dumps(score_data) + "\n")
        
        # Save to DB
        conn = self._get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO scores (id, trace_id, observation_id, name, value, comment, data_type, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            score_data["id"], score.trace_id, score.observation_id,
            score.name, score.value, score.comment, score.data_type,
            score_data["timestamp"]
        ))
        conn.commit()
        conn.close()
    
    def _save_trace(self, trace: Dict):
        """Save completed trace to storage"""
        # Append to JSONL
        with open(self.traces_file, "a") as f:
            f.write(json.dumps(trace) + "\n")
        
        # Save to SQLite
        conn = self._get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO traces 
            (id, name, user_id, session_id, input, output, metadata, tags, level, status_message, start_time, end_time, duration_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trace["id"], trace["name"], trace.get("user_id"), trace.get("session_id"),
            json.dumps(trace.get("input")), json.dumps(trace.get("output")),
            json.dumps(trace.get("metadata", {})), json.dumps(trace.get("tags", [])),
            trace.get("level"), trace.get("status_message"),
            trace.get("start_time"), trace.get("end_time"), trace.get("duration_ms")
        ))
        
        # Save spans
        for span in trace.get("spans", []):
            cursor.execute("""
                INSERT OR REPLACE INTO spans
                (id, trace_id, parent_id, name, input, output, metadata, level, start_time, end_time, duration_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                span["id"], span["trace_id"], span.get("parent_id"), span["name"],
                json.dumps(span.get("input")), json.dumps(span.get("output")),
                json.dumps(span.get("metadata", {})), span.get("level"),
                span.get("start_time"), span.get("end_time"), span.get("duration_ms")
            ))
        
        # Save generations
        for gen in trace.get("generations", []):
            cursor.execute("""
                INSERT OR REPLACE INTO generations
                (id, trace_id, span_id, model, provider, prompt, completion, prompt_tokens, completion_tokens, total_tokens, latency_ms, cost_usd, metadata, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                gen["id"], gen["trace_id"], gen.get("span_id"), gen["model"], gen["provider"],
                gen.get("prompt"), gen.get("completion"),
                gen.get("prompt_tokens", 0), gen.get("completion_tokens", 0), gen.get("total_tokens", 0),
                gen.get("latency_ms", 0), gen.get("cost_usd", 0),
                json.dumps(gen.get("metadata", {})), gen["timestamp"]
            ))
        
        conn.commit()
        conn.close()
    
    def flush(self):
        """Flush all pending traces"""
        with self._lock:
            for trace_id, trace in list(self._traces.items()):
                if "end_time" not in trace:
                    trace["end_time"] = datetime.now().isoformat()
                    self._save_trace(trace)
            self._traces.clear()
            self._spans.clear()
    
    def get_trace_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get observability statistics"""
        conn = self._get_db()
        cursor = conn.cursor()
        
        # Total counts
        cursor.execute("SELECT COUNT(*) FROM traces")
        total_traces = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM generations")
        total_generations = cursor.fetchone()[0]
        
        # Token usage
        cursor.execute("SELECT SUM(total_tokens), SUM(cost_usd) FROM generations")
        row = cursor.fetchone()
        total_tokens = row[0] or 0
        total_cost = row[1] or 0
        
        # Average latency
        cursor.execute("SELECT AVG(latency_ms) FROM generations")
        avg_latency = cursor.fetchone()[0] or 0
        
        # Top models
        cursor.execute("""
            SELECT model, COUNT(*), SUM(total_tokens) 
            FROM generations 
            GROUP BY model 
            ORDER BY COUNT(*) DESC 
            LIMIT 5
        """)
        top_models = [{"model": r[0], "count": r[1], "tokens": r[2]} for r in cursor.fetchall()]
        
        conn.close()
        
        return {
            "total_traces": total_traces,
            "total_generations": total_generations,
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 4),
            "avg_latency_ms": round(avg_latency, 2),
            "top_models": top_models
        }


# ============ UNIFIED OBSERVABILITY CLIENT ============

class Observability:
    """
    Unified Observability Client
    
    Provides a single interface for LLM observability.
    Automatically uses Langfuse if configured, otherwise local backend.
    """
    
    _instance: Optional['Observability'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._backend: Optional[ObservabilityBackend] = None
        self._current_trace_id: Optional[str] = None
        self._current_span_id: Optional[str] = None
        self._trace_stack: List[str] = []
        self._span_stack: List[str] = []
        
        # Auto-initialize
        self._init_backend()
        self._initialized = True
    
    def _init_backend(self):
        """Initialize the appropriate backend"""
        # Try Langfuse first
        langfuse_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        
        if LANGFUSE_AVAILABLE and langfuse_key:
            try:
                self._backend = LangfuseBackend()
                print("📊 Langfuse observability initialized")
            except Exception as e:
                print(f"⚠️ Langfuse init failed: {e}, using local backend")
                self._backend = LocalObservabilityBackend()
        else:
            self._backend = LocalObservabilityBackend()
            print("📊 Local observability backend initialized")
    
    @property
    def backend(self) -> ObservabilityBackend:
        return self._backend
    
    @contextmanager
    def trace(
        self,
        name: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        input: Optional[Any] = None,
        metadata: Optional[Dict] = None,
        tags: Optional[List[str]] = None
    ):
        """Context manager for tracing"""
        trace_id = self._backend.start_trace(
            name=name,
            user_id=user_id,
            session_id=session_id,
            input=input,
            metadata=metadata,
            tags=tags
        )
        
        self._trace_stack.append(trace_id)
        self._current_trace_id = trace_id
        
        try:
            yield trace_id
        except Exception as e:
            self._backend.end_trace(
                trace_id,
                level=SpanLevel.ERROR,
                status_message=str(e)
            )
            raise
        finally:
            self._backend.end_trace(trace_id)
            self._trace_stack.pop()
            self._current_trace_id = self._trace_stack[-1] if self._trace_stack else None
    
    @contextmanager
    def span(
        self,
        name: str,
        trace_id: Optional[str] = None,
        input: Optional[Any] = None,
        metadata: Optional[Dict] = None
    ):
        """Context manager for spans"""
        tid = trace_id or self._current_trace_id
        if not tid:
            raise ValueError("No active trace. Use 'with observability.trace()' first.")
        
        span_id = self._backend.start_span(
            name=name,
            trace_id=tid,
            parent_span_id=self._current_span_id,
            input=input,
            metadata=metadata
        )
        
        self._span_stack.append(span_id)
        self._current_span_id = span_id
        
        try:
            yield span_id
        except Exception as e:
            self._backend.end_span(
                span_id,
                level=SpanLevel.ERROR,
                status_message=str(e)
            )
            raise
        finally:
            self._backend.end_span(span_id)
            self._span_stack.pop()
            self._current_span_id = self._span_stack[-1] if self._span_stack else None
    
    def log_generation(
        self,
        model: str,
        provider: ModelProvider,
        prompt: str,
        completion: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        latency_ms: float = 0,
        metadata: Optional[Dict] = None,
        trace_id: Optional[str] = None
    ):
        """Log an LLM generation"""
        tid = trace_id or self._current_trace_id
        if not tid:
            return
        
        usage = TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens
        )
        
        gen = GenerationMetadata(
            model=model,
            provider=provider,
            prompt=prompt,
            completion=completion,
            usage=usage,
            latency_ms=latency_ms,
            metadata=metadata or {}
        )
        
        self._backend.log_generation(
            trace_id=tid,
            generation=gen,
            parent_span_id=self._current_span_id
        )
    
    def log_event(
        self,
        name: str,
        input: Optional[Any] = None,
        output: Optional[Any] = None,
        metadata: Optional[Dict] = None,
        trace_id: Optional[str] = None
    ):
        """Log an event"""
        tid = trace_id or self._current_trace_id
        if tid:
            self._backend.log_event(
                trace_id=tid,
                name=name,
                input=input,
                output=output,
                metadata=metadata,
                parent_span_id=self._current_span_id
            )
    
    def add_score(
        self,
        name: str,
        value: float,
        trace_id: Optional[str] = None,
        observation_id: Optional[str] = None,
        comment: Optional[str] = None
    ):
        """Add a quality score"""
        tid = trace_id or self._current_trace_id
        if not tid:
            return
        
        self._backend.add_score(Score(
            name=name,
            value=value,
            trace_id=tid,
            observation_id=observation_id or self._current_span_id,
            comment=comment
        ))
    
    def flush(self):
        """Flush pending data"""
        self._backend.flush()


# ============ DECORATORS ============

F = TypeVar('F', bound=Callable)


def traced(name: Optional[str] = None, tags: Optional[List[str]] = None):
    """
    Decorator for tracing functions
    
    Usage:
        @traced("my_function", tags=["important"])
        def my_function(x, y):
            return x + y
    """
    def decorator(func: F) -> F:
        trace_name = name or func.__name__
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            obs = Observability()
            with obs.trace(trace_name, tags=tags, input={"args": str(args), "kwargs": str(kwargs)}):
                result = func(*args, **kwargs)
                return result
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            obs = Observability()
            with obs.trace(trace_name, tags=tags, input={"args": str(args), "kwargs": str(kwargs)}):
                result = await func(*args, **kwargs)
                return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def spanned(name: Optional[str] = None):
    """
    Decorator for spanning functions within a trace
    
    Usage:
        @spanned("process_data")
        def process_data(data):
            return data.upper()
    """
    def decorator(func: F) -> F:
        span_name = name or func.__name__
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            obs = Observability()
            if obs._current_trace_id:
                with obs.span(span_name, input={"args": str(args)[:200]}):
                    return func(*args, **kwargs)
            return func(*args, **kwargs)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            obs = Observability()
            if obs._current_trace_id:
                with obs.span(span_name, input={"args": str(args)[:200]}):
                    return await func(*args, **kwargs)
            return await func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# ============ GLOBAL INSTANCE ============

observability = Observability()


# ============ EXPORTS ============

__all__ = [
    # Main client
    "Observability",
    "observability",
    # Backends
    "LangfuseBackend",
    "LocalObservabilityBackend",
    # Data classes
    "TokenUsage",
    "GenerationMetadata",
    "TraceMetadata",
    "Score",
    # Enums
    "ObservationType",
    "SpanLevel",
    "ModelProvider",
    # Decorators
    "traced",
    "spanned",
]
