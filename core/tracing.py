"""
Observability & Tracing System
==============================

Endüstri standartlarında gözlemlenebilirlik ve izleme sistemi.
Distributed tracing, metrics collection ve monitoring.

Features:
- Distributed tracing (OpenTelemetry compatible)
- Metrics collection
- Span tracking
- Performance monitoring
- Error tracking
- Request/Response logging
"""

import asyncio
import contextvars
import functools
import json
import sqlite3
import time
import uuid
from abc import ABC, abstractmethod
from contextlib import contextmanager, asynccontextmanager
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

from .logger import get_logger

logger = get_logger("tracing")

T = TypeVar("T")

# Context variable for current span
_current_span: contextvars.ContextVar[Optional["Span"]] = contextvars.ContextVar(
    "current_span", default=None
)


class SpanKind(Enum):
    """Span türleri (OpenTelemetry uyumlu)"""
    INTERNAL = "internal"
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"


class SpanStatus(Enum):
    """Span durumları"""
    UNSET = "unset"
    OK = "ok"
    ERROR = "error"


@dataclass
class SpanContext:
    """Span context - distributed tracing için"""
    trace_id: str
    span_id: str
    parent_id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_id": self.parent_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "SpanContext":
        return cls(
            trace_id=data["trace_id"],
            span_id=data["span_id"],
            parent_id=data.get("parent_id")
        )
    
    def to_header(self) -> str:
        """W3C traceparent header formatı"""
        return f"00-{self.trace_id}-{self.span_id}-01"
    
    @classmethod
    def from_header(cls, header: str) -> Optional["SpanContext"]:
        """W3C traceparent header'dan parse et"""
        try:
            parts = header.split("-")
            if len(parts) >= 3:
                return cls(
                    trace_id=parts[1],
                    span_id=parts[2],
                    parent_id=None
                )
        except Exception:
            pass
        return None


@dataclass
class SpanEvent:
    """Span içindeki event"""
    name: str
    timestamp: float = field(default_factory=time.time)
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Span:
    """
    Trace span - bir işlem birimini temsil eder
    
    OpenTelemetry Span konseptine uyumlu.
    """
    name: str
    context: SpanContext
    kind: SpanKind = SpanKind.INTERNAL
    status: SpanStatus = SpanStatus.UNSET
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[SpanEvent] = field(default_factory=list)
    error: Optional[str] = None
    
    def set_attribute(self, key: str, value: Any):
        """Attribute ekle"""
        self.attributes[key] = value
    
    def add_event(self, name: str, attributes: Optional[Dict] = None):
        """Event ekle"""
        self.events.append(SpanEvent(
            name=name,
            attributes=attributes or {}
        ))
    
    def set_status(self, status: SpanStatus, description: Optional[str] = None):
        """Status ayarla"""
        self.status = status
        if description:
            self.error = description
    
    def end(self, end_time: Optional[float] = None):
        """Span'ı sonlandır"""
        self.end_time = end_time or time.time()
    
    @property
    def duration(self) -> float:
        """Span süresi (ms)"""
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0.0
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "context": self.context.to_dict(),
            "kind": self.kind.value,
            "status": self.status.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration,
            "attributes": self.attributes,
            "events": [
                {"name": e.name, "timestamp": e.timestamp, "attributes": e.attributes}
                for e in self.events
            ],
            "error": self.error
        }


class SpanExporter(ABC):
    """Span exporter base class"""
    
    @abstractmethod
    def export(self, spans: List[Span]) -> bool:
        """Span'ları export et"""
        pass


class ConsoleExporter(SpanExporter):
    """Console'a span yazdır (debug için)"""
    
    def export(self, spans: List[Span]) -> bool:
        for span in spans:
            logger.debug(f"SPAN: {span.name} ({span.duration:.2f}ms) [{span.status.value}]")
        return True


class SQLiteExporter(SpanExporter):
    """SQLite'a span kaydet"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS spans (
                id TEXT PRIMARY KEY,
                trace_id TEXT NOT NULL,
                parent_id TEXT,
                name TEXT NOT NULL,
                kind TEXT,
                status TEXT,
                start_time REAL,
                end_time REAL,
                duration_ms REAL,
                attributes TEXT,
                events TEXT,
                error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trace_id ON spans(trace_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_start_time ON spans(start_time)")
        
        conn.commit()
        conn.close()
    
    def export(self, spans: List[Span]) -> bool:
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            for span in spans:
                cursor.execute("""
                    INSERT OR REPLACE INTO spans
                    (id, trace_id, parent_id, name, kind, status,
                     start_time, end_time, duration_ms, attributes, events, error)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    span.context.span_id,
                    span.context.trace_id,
                    span.context.parent_id,
                    span.name,
                    span.kind.value,
                    span.status.value,
                    span.start_time,
                    span.end_time,
                    span.duration,
                    json.dumps(span.attributes),
                    json.dumps([asdict(e) for e in span.events]),
                    span.error
                ))
            
            conn.commit()
            conn.close()
            
            return True
        
        except Exception as e:
            logger.error(f"SQLite export error: {e}")
            return False


class Tracer:
    """
    Tracer - span oluşturma ve yönetim
    
    Usage:
        tracer = Tracer("my-service")
        
        with tracer.start_span("operation") as span:
            span.set_attribute("key", "value")
            # do work
    """
    
    def __init__(
        self,
        service_name: str,
        exporters: Optional[List[SpanExporter]] = None
    ):
        self.service_name = service_name
        self.exporters = exporters or []
        self._spans: List[Span] = []
        self._batch_size = 100
    
    def _generate_id(self, length: int = 16) -> str:
        """Random ID oluştur"""
        return uuid.uuid4().hex[:length]
    
    def start_span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[Dict] = None,
        parent: Optional[Span] = None
    ) -> "SpanContextManager":
        """Yeni span başlat"""
        # Get parent from context if not provided
        if parent is None:
            parent = _current_span.get()
        
        # Create context
        if parent:
            context = SpanContext(
                trace_id=parent.context.trace_id,
                span_id=self._generate_id(),
                parent_id=parent.context.span_id
            )
        else:
            context = SpanContext(
                trace_id=self._generate_id(32),
                span_id=self._generate_id()
            )
        
        span = Span(
            name=name,
            context=context,
            kind=kind,
            attributes=attributes or {}
        )
        
        # Add service name
        span.set_attribute("service.name", self.service_name)
        
        return SpanContextManager(self, span)
    
    def _end_span(self, span: Span):
        """Span'ı bitir ve export et"""
        span.end()
        self._spans.append(span)
        
        # Export if batch full
        if len(self._spans) >= self._batch_size:
            self.flush()
    
    def flush(self):
        """Bekleyen span'ları export et"""
        if not self._spans:
            return
        
        spans_to_export = self._spans.copy()
        self._spans.clear()
        
        for exporter in self.exporters:
            try:
                exporter.export(spans_to_export)
            except Exception as e:
                logger.error(f"Export error: {e}")
    
    def add_exporter(self, exporter: SpanExporter):
        """Exporter ekle"""
        self.exporters.append(exporter)


class SpanContextManager:
    """Span context manager (with statement için)"""
    
    def __init__(self, tracer: Tracer, span: Span):
        self._tracer = tracer
        self._span = span
        self._token: Optional[contextvars.Token] = None
    
    def __enter__(self) -> Span:
        self._token = _current_span.set(self._span)
        return self._span
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self._span.set_status(SpanStatus.ERROR, str(exc_val))
        else:
            self._span.set_status(SpanStatus.OK)
        
        _current_span.reset(self._token)
        self._tracer._end_span(self._span)
        
        return False
    
    async def __aenter__(self) -> Span:
        return self.__enter__()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return self.__exit__(exc_type, exc_val, exc_tb)


# ========================
# Metrics System
# ========================

@dataclass
class MetricValue:
    """Metrik değeri"""
    value: float
    timestamp: float = field(default_factory=time.time)
    labels: Dict[str, str] = field(default_factory=dict)


class MetricType(Enum):
    """Metrik türleri"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


class Metric:
    """Base metric class"""
    
    def __init__(
        self,
        name: str,
        description: str = "",
        labels: Optional[List[str]] = None
    ):
        self.name = name
        self.description = description
        self.labels = labels or []
        self._values: List[MetricValue] = []
    
    def _get_label_key(self, label_values: Dict[str, str]) -> str:
        return json.dumps(sorted(label_values.items()))


class Counter(Metric):
    """Sayaç metriği - sadece artabilir"""
    
    def __init__(self, name: str, description: str = "", labels: Optional[List[str]] = None):
        super().__init__(name, description, labels)
        self._counters: Dict[str, float] = {}
    
    def inc(self, value: float = 1, labels: Optional[Dict[str, str]] = None):
        """Sayacı artır"""
        key = self._get_label_key(labels or {})
        self._counters[key] = self._counters.get(key, 0) + value
        self._values.append(MetricValue(value=self._counters[key], labels=labels or {}))
    
    def get(self, labels: Optional[Dict[str, str]] = None) -> float:
        """Değeri al"""
        key = self._get_label_key(labels or {})
        return self._counters.get(key, 0)


class Gauge(Metric):
    """Gauge metriği - artabilir veya azalabilir"""
    
    def __init__(self, name: str, description: str = "", labels: Optional[List[str]] = None):
        super().__init__(name, description, labels)
        self._values_dict: Dict[str, float] = {}
    
    def set(self, value: float, labels: Optional[Dict[str, str]] = None):
        """Değeri ayarla"""
        key = self._get_label_key(labels or {})
        self._values_dict[key] = value
        self._values.append(MetricValue(value=value, labels=labels or {}))
    
    def inc(self, value: float = 1, labels: Optional[Dict[str, str]] = None):
        """Değeri artır"""
        key = self._get_label_key(labels or {})
        self._values_dict[key] = self._values_dict.get(key, 0) + value
    
    def dec(self, value: float = 1, labels: Optional[Dict[str, str]] = None):
        """Değeri azalt"""
        self.inc(-value, labels)
    
    def get(self, labels: Optional[Dict[str, str]] = None) -> float:
        key = self._get_label_key(labels or {})
        return self._values_dict.get(key, 0)


class Histogram(Metric):
    """Histogram metriği - değer dağılımı"""
    
    def __init__(
        self,
        name: str,
        description: str = "",
        labels: Optional[List[str]] = None,
        buckets: Optional[List[float]] = None
    ):
        super().__init__(name, description, labels)
        self.buckets = buckets or [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
        self._observations: Dict[str, List[float]] = {}
    
    def observe(self, value: float, labels: Optional[Dict[str, str]] = None):
        """Değer gözlemle"""
        key = self._get_label_key(labels or {})
        if key not in self._observations:
            self._observations[key] = []
        self._observations[key].append(value)
        self._values.append(MetricValue(value=value, labels=labels or {}))
    
    def get_stats(self, labels: Optional[Dict[str, str]] = None) -> Dict:
        """İstatistikleri al"""
        key = self._get_label_key(labels or {})
        observations = self._observations.get(key, [])
        
        if not observations:
            return {"count": 0, "sum": 0, "avg": 0, "min": 0, "max": 0}
        
        return {
            "count": len(observations),
            "sum": sum(observations),
            "avg": sum(observations) / len(observations),
            "min": min(observations),
            "max": max(observations)
        }


class MetricsRegistry:
    """Metrik registry"""
    
    def __init__(self):
        self._metrics: Dict[str, Metric] = {}
    
    def counter(self, name: str, description: str = "", labels: Optional[List[str]] = None) -> Counter:
        """Counter oluştur veya al"""
        if name not in self._metrics:
            self._metrics[name] = Counter(name, description, labels)
        return self._metrics[name]  # type: ignore
    
    def gauge(self, name: str, description: str = "", labels: Optional[List[str]] = None) -> Gauge:
        """Gauge oluştur veya al"""
        if name not in self._metrics:
            self._metrics[name] = Gauge(name, description, labels)
        return self._metrics[name]  # type: ignore
    
    def histogram(
        self,
        name: str,
        description: str = "",
        labels: Optional[List[str]] = None,
        buckets: Optional[List[float]] = None
    ) -> Histogram:
        """Histogram oluştur veya al"""
        if name not in self._metrics:
            self._metrics[name] = Histogram(name, description, labels, buckets)
        return self._metrics[name]  # type: ignore
    
    def get_all(self) -> Dict[str, Metric]:
        """Tüm metrikleri al"""
        return self._metrics.copy()


# ========================
# Decorators
# ========================

def trace(
    name: Optional[str] = None,
    kind: SpanKind = SpanKind.INTERNAL,
    record_args: bool = False,
    record_result: bool = False
):
    """
    Fonksiyon trace decorator
    
    Usage:
        @trace("my-operation")
        def my_function():
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        span_name = name or func.__name__
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            with global_tracer.start_span(span_name, kind=kind) as span:
                if record_args:
                    span.set_attribute("args", str(args)[:200])
                    span.set_attribute("kwargs", str(kwargs)[:200])
                
                try:
                    result = func(*args, **kwargs)
                    
                    if record_result:
                        span.set_attribute("result", str(result)[:200])
                    
                    return result
                except Exception as e:
                    span.set_status(SpanStatus.ERROR, str(e))
                    raise
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            async with global_tracer.start_span(span_name, kind=kind) as span:
                if record_args:
                    span.set_attribute("args", str(args)[:200])
                    span.set_attribute("kwargs", str(kwargs)[:200])
                
                try:
                    result = await func(*args, **kwargs)
                    
                    if record_result:
                        span.set_attribute("result", str(result)[:200])
                    
                    return result
                except Exception as e:
                    span.set_status(SpanStatus.ERROR, str(e))
                    raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def timed(metric: Histogram):
    """
    Fonksiyon timing decorator
    
    Usage:
        request_duration = registry.histogram("request_duration_seconds")
        
        @timed(request_duration)
        def my_function():
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            start = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                metric.observe(time.time() - start)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            start = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                metric.observe(time.time() - start)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# ========================
# Global Instances
# ========================

# Global tracer
global_tracer = Tracer(
    "enterprise-ai-assistant",
    exporters=[
        ConsoleExporter(),
        SQLiteExporter(Path("data/traces.db"))
    ]
)

# Global metrics registry
metrics_registry = MetricsRegistry()

# Pre-defined metrics
request_counter = metrics_registry.counter(
    "requests_total",
    "Total number of requests",
    ["endpoint", "method", "status"]
)

request_duration = metrics_registry.histogram(
    "request_duration_seconds",
    "Request duration in seconds",
    ["endpoint"]
)

llm_tokens = metrics_registry.counter(
    "llm_tokens_total",
    "Total LLM tokens used",
    ["model", "type"]  # type: input/output
)

active_sessions = metrics_registry.gauge(
    "active_sessions",
    "Number of active sessions"
)


def get_current_span() -> Optional[Span]:
    """Current span'ı al"""
    return _current_span.get()


__all__ = [
    "Tracer",
    "Span",
    "SpanContext",
    "SpanKind",
    "SpanStatus",
    "SpanEvent",
    "SpanExporter",
    "ConsoleExporter",
    "SQLiteExporter",
    "MetricsRegistry",
    "Counter",
    "Gauge",
    "Histogram",
    "trace",
    "timed",
    "global_tracer",
    "metrics_registry",
    "request_counter",
    "request_duration",
    "llm_tokens",
    "active_sessions",
    "get_current_span"
]
