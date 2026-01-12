"""
Enterprise AI Assistant - Custom Exceptions
============================================

Endüstri standartlarında özel hata sınıfları.
Tüm hata türleri için merkezi yönetim.
"""

from typing import Optional, Dict, Any
from datetime import datetime
import traceback
import uuid


class BaseAppException(Exception):
    """
    Tüm uygulama hatalarının temel sınıfı.
    
    Features:
    - Unique error ID (tracking için)
    - Timestamp
    - Context data
    - Severity level
    - Retry bilgisi
    """
    
    # Severity levels
    SEVERITY_LOW = "low"
    SEVERITY_MEDIUM = "medium"
    SEVERITY_HIGH = "high"
    SEVERITY_CRITICAL = "critical"
    
    def __init__(
        self,
        message: str,
        code: str = "UNKNOWN_ERROR",
        severity: str = SEVERITY_MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
        retryable: bool = False,
        user_message: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.severity = severity
        self.details = details or {}
        self.cause = cause
        self.retryable = retryable
        self.user_message = user_message or message
        
        # Auto-generated
        self.error_id = str(uuid.uuid4())[:8]
        self.timestamp = datetime.now()
        self.traceback = traceback.format_exc() if cause else None
    
    def to_dict(self) -> Dict[str, Any]:
        """Hata bilgilerini dictionary olarak döndür."""
        return {
            "error_id": self.error_id,
            "code": self.code,
            "message": self.message,
            "user_message": self.user_message,
            "severity": self.severity,
            "retryable": self.retryable,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "cause": str(self.cause) if self.cause else None,
        }
    
    def __str__(self) -> str:
        return f"[{self.code}:{self.error_id}] {self.message}"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self.code}, message={self.message})"


# =============================================================================
# LLM EXCEPTIONS
# =============================================================================

class LLMException(BaseAppException):
    """LLM ile ilgili tüm hatalar."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            code=kwargs.pop("code", "LLM_ERROR"),
            severity=kwargs.pop("severity", self.SEVERITY_HIGH),
            **kwargs
        )


class LLMConnectionError(LLMException):
    """Ollama bağlantı hatası."""
    
    def __init__(self, message: str = "Ollama servisine bağlanılamadı", **kwargs):
        super().__init__(
            message=message,
            code="LLM_CONNECTION_ERROR",
            retryable=True,
            user_message="AI servisi şu anda erişilemez. Lütfen birkaç saniye sonra tekrar deneyin.",
            **kwargs
        )


class LLMModelNotFoundError(LLMException):
    """Model bulunamadı hatası."""
    
    def __init__(self, model_name: str, **kwargs):
        super().__init__(
            message=f"Model bulunamadı: {model_name}",
            code="LLM_MODEL_NOT_FOUND",
            details={"model_name": model_name},
            user_message=f"İstenen AI modeli ({model_name}) yüklü değil.",
            **kwargs
        )


class LLMGenerationError(LLMException):
    """Yanıt üretme hatası."""
    
    def __init__(self, message: str = "Yanıt üretilemedi", **kwargs):
        super().__init__(
            message=message,
            code="LLM_GENERATION_ERROR",
            retryable=True,
            **kwargs
        )


class LLMTimeoutError(LLMException):
    """Zaman aşımı hatası."""
    
    def __init__(self, timeout_seconds: int = 0, **kwargs):
        super().__init__(
            message=f"LLM yanıtı zaman aşımına uğradı ({timeout_seconds}s)",
            code="LLM_TIMEOUT",
            retryable=True,
            details={"timeout_seconds": timeout_seconds},
            user_message="Yanıt süresi çok uzun sürdü. Lütfen tekrar deneyin.",
            **kwargs
        )


# =============================================================================
# RAG EXCEPTIONS
# =============================================================================

class RAGException(BaseAppException):
    """RAG ile ilgili tüm hatalar."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            code=kwargs.pop("code", "RAG_ERROR"),
            severity=kwargs.pop("severity", self.SEVERITY_MEDIUM),
            **kwargs
        )


class DocumentNotFoundError(RAGException):
    """Döküman bulunamadı hatası."""
    
    def __init__(self, doc_id: str = None, filename: str = None, **kwargs):
        identifier = doc_id or filename or "bilinmeyen"
        super().__init__(
            message=f"Döküman bulunamadı: {identifier}",
            code="DOCUMENT_NOT_FOUND",
            details={"doc_id": doc_id, "filename": filename},
            user_message=f"İstenen döküman bulunamadı.",
            **kwargs
        )


class DocumentProcessingError(RAGException):
    """Döküman işleme hatası."""
    
    def __init__(self, filename: str, reason: str = None, **kwargs):
        super().__init__(
            message=f"Döküman işlenemedi: {filename}",
            code="DOCUMENT_PROCESSING_ERROR",
            details={"filename": filename, "reason": reason},
            user_message=f"Döküman ({filename}) işlenirken bir hata oluştu.",
            **kwargs
        )


class UnsupportedFileTypeError(RAGException):
    """Desteklenmeyen dosya tipi."""
    
    def __init__(self, file_type: str, supported_types: list = None, **kwargs):
        super().__init__(
            message=f"Desteklenmeyen dosya tipi: {file_type}",
            code="UNSUPPORTED_FILE_TYPE",
            severity=self.SEVERITY_LOW,
            details={"file_type": file_type, "supported_types": supported_types},
            user_message=f"Bu dosya tipi ({file_type}) desteklenmiyor.",
            **kwargs
        )


class EmbeddingError(RAGException):
    """Embedding üretme hatası."""
    
    def __init__(self, message: str = "Embedding oluşturulamadı", **kwargs):
        super().__init__(
            message=message,
            code="EMBEDDING_ERROR",
            retryable=True,
            **kwargs
        )


class VectorStoreError(RAGException):
    """Vector store hatası."""
    
    def __init__(self, message: str, operation: str = None, **kwargs):
        super().__init__(
            message=message,
            code="VECTOR_STORE_ERROR",
            details={"operation": operation},
            **kwargs
        )


class RetrievalError(RAGException):
    """Bilgi getirme hatası."""
    
    def __init__(self, query: str = None, **kwargs):
        super().__init__(
            message="Bilgi getirme işlemi başarısız",
            code="RETRIEVAL_ERROR",
            retryable=True,
            details={"query": query[:100] if query else None},
            user_message="Arama yapılırken bir hata oluştu.",
            **kwargs
        )


# =============================================================================
# AGENT EXCEPTIONS
# =============================================================================

class AgentException(BaseAppException):
    """Agent ile ilgili tüm hatalar."""
    
    def __init__(self, message: str, agent_name: str = None, **kwargs):
        details = kwargs.pop("details", {})
        details["agent_name"] = agent_name
        super().__init__(
            message=message,
            code=kwargs.pop("code", "AGENT_ERROR"),
            details=details,
            **kwargs
        )


class AgentExecutionError(AgentException):
    """Agent yürütme hatası."""
    
    def __init__(self, agent_name: str, task: str = None, **kwargs):
        super().__init__(
            message=f"Agent görevi tamamlayamadı: {agent_name}",
            agent_name=agent_name,
            code="AGENT_EXECUTION_ERROR",
            retryable=True,
            details={"task": task[:200] if task else None},
            user_message="Görev işlenirken bir hata oluştu.",
            **kwargs
        )


class AgentTimeoutError(AgentException):
    """Agent zaman aşımı."""
    
    def __init__(self, agent_name: str, timeout_seconds: int = 0, **kwargs):
        super().__init__(
            message=f"Agent zaman aşımına uğradı: {agent_name} ({timeout_seconds}s)",
            agent_name=agent_name,
            code="AGENT_TIMEOUT",
            retryable=True,
            details={"timeout_seconds": timeout_seconds},
            **kwargs
        )


class AgentRoutingError(AgentException):
    """Yanlış agent yönlendirmesi."""
    
    def __init__(self, task: str = None, **kwargs):
        super().__init__(
            message="Uygun agent bulunamadı",
            code="AGENT_ROUTING_ERROR",
            details={"task": task[:200] if task else None},
            **kwargs
        )


# =============================================================================
# API EXCEPTIONS
# =============================================================================

class APIException(BaseAppException):
    """API ile ilgili hatalar."""
    
    def __init__(self, message: str, status_code: int = 500, **kwargs):
        details = kwargs.pop("details", {})
        details["status_code"] = status_code
        super().__init__(
            message=message,
            code=kwargs.pop("code", "API_ERROR"),
            details=details,
            **kwargs
        )
        self.status_code = status_code


class ValidationError(APIException):
    """Validasyon hatası."""
    
    def __init__(self, field: str, message: str, **kwargs):
        super().__init__(
            message=f"Validasyon hatası: {field} - {message}",
            code="VALIDATION_ERROR",
            status_code=422,
            severity=self.SEVERITY_LOW,
            details={"field": field, "error": message},
            user_message=f"Geçersiz değer: {message}",
            **kwargs
        )


class RateLimitError(APIException):
    """Rate limit aşıldı."""
    
    def __init__(self, limit: int = None, window_seconds: int = None, **kwargs):
        super().__init__(
            message="Rate limit aşıldı",
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            severity=self.SEVERITY_LOW,
            retryable=True,
            details={"limit": limit, "window_seconds": window_seconds},
            user_message="Çok fazla istek gönderdiniz. Lütfen biraz bekleyin.",
            **kwargs
        )


class AuthenticationError(APIException):
    """Kimlik doğrulama hatası."""
    
    def __init__(self, message: str = "Kimlik doğrulaması başarısız", **kwargs):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=401,
            severity=self.SEVERITY_HIGH,
            **kwargs
        )


class AuthorizationError(APIException):
    """Yetkilendirme hatası."""
    
    def __init__(self, resource: str = None, **kwargs):
        super().__init__(
            message=f"Bu kaynağa erişim yetkiniz yok: {resource or 'bilinmeyen'}",
            code="AUTHORIZATION_ERROR",
            status_code=403,
            severity=self.SEVERITY_HIGH,
            details={"resource": resource},
            user_message="Bu işlem için yetkiniz bulunmuyor.",
            **kwargs
        )


# =============================================================================
# SESSION & MEMORY EXCEPTIONS
# =============================================================================

class SessionException(BaseAppException):
    """Session ile ilgili hatalar."""
    
    def __init__(self, message: str, session_id: str = None, **kwargs):
        details = kwargs.pop("details", {})
        details["session_id"] = session_id
        super().__init__(
            message=message,
            code=kwargs.pop("code", "SESSION_ERROR"),
            details=details,
            **kwargs
        )


class SessionNotFoundError(SessionException):
    """Session bulunamadı."""
    
    def __init__(self, session_id: str, **kwargs):
        super().__init__(
            message=f"Session bulunamadı: {session_id}",
            session_id=session_id,
            code="SESSION_NOT_FOUND",
            severity=self.SEVERITY_LOW,
            user_message="Oturum bulunamadı veya süresi dolmuş.",
            **kwargs
        )


class SessionExpiredError(SessionException):
    """Session süresi dolmuş."""
    
    def __init__(self, session_id: str, **kwargs):
        super().__init__(
            message=f"Session süresi doldu: {session_id}",
            session_id=session_id,
            code="SESSION_EXPIRED",
            severity=self.SEVERITY_LOW,
            user_message="Oturum süreniz doldu. Lütfen yeni bir oturum başlatın.",
            **kwargs
        )


# =============================================================================
# CONFIGURATION EXCEPTIONS
# =============================================================================

class ConfigurationError(BaseAppException):
    """Konfigürasyon hatası."""
    
    def __init__(self, message: str, config_key: str = None, **kwargs):
        super().__init__(
            message=message,
            code="CONFIGURATION_ERROR",
            severity=self.SEVERITY_CRITICAL,
            details={"config_key": config_key},
            **kwargs
        )


class MissingConfigError(ConfigurationError):
    """Eksik konfigürasyon değeri."""
    
    def __init__(self, config_key: str, **kwargs):
        super().__init__(
            message=f"Zorunlu konfigürasyon eksik: {config_key}",
            config_key=config_key,
            **kwargs
        )


# =============================================================================
# EXTERNAL SERVICE EXCEPTIONS
# =============================================================================

class ExternalServiceError(BaseAppException):
    """Harici servis hatası."""
    
    def __init__(self, service_name: str, message: str = None, **kwargs):
        super().__init__(
            message=message or f"Harici servis hatası: {service_name}",
            code="EXTERNAL_SERVICE_ERROR",
            retryable=True,
            details={"service_name": service_name},
            user_message=f"{service_name} servisi şu anda erişilemez.",
            **kwargs
        )


class CircuitBreakerOpenError(ExternalServiceError):
    """Circuit breaker açık - servis geçici olarak devre dışı."""
    
    def __init__(self, service_name: str, retry_after_seconds: int = 30, **kwargs):
        super().__init__(
            service_name=service_name,
            message=f"Servis geçici olarak devre dışı: {service_name}",
            code="CIRCUIT_BREAKER_OPEN",
            details={"retry_after_seconds": retry_after_seconds},
            user_message=f"Servis geçici olarak kullanılamıyor. {retry_after_seconds} saniye sonra tekrar deneyin.",
            **kwargs
        )


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def handle_exception(exc: Exception) -> BaseAppException:
    """
    Standart exception'ı BaseAppException'a dönüştür.
    
    Args:
        exc: Herhangi bir exception
        
    Returns:
        BaseAppException türünde hata
    """
    if isinstance(exc, BaseAppException):
        return exc
    
    # Bilinen exception türlerini eşle
    exc_type = type(exc).__name__
    
    mapping = {
        "ConnectionError": LLMConnectionError,
        "TimeoutError": LLMTimeoutError,
        "FileNotFoundError": DocumentNotFoundError,
        "PermissionError": AuthorizationError,
        "ValueError": ValidationError,
    }
    
    if exc_type in mapping:
        return mapping[exc_type](str(exc), cause=exc)
    
    # Varsayılan: genel hata
    return BaseAppException(
        message=str(exc),
        code="UNHANDLED_ERROR",
        severity=BaseAppException.SEVERITY_HIGH,
        cause=exc,
    )


__all__ = [
    # Base
    "BaseAppException",
    "handle_exception",
    
    # LLM
    "LLMException",
    "LLMConnectionError",
    "LLMModelNotFoundError",
    "LLMGenerationError",
    "LLMTimeoutError",
    
    # RAG
    "RAGException",
    "DocumentNotFoundError",
    "DocumentProcessingError",
    "UnsupportedFileTypeError",
    "EmbeddingError",
    "VectorStoreError",
    "RetrievalError",
    
    # Agent
    "AgentException",
    "AgentExecutionError",
    "AgentTimeoutError",
    "AgentRoutingError",
    
    # API
    "APIException",
    "ValidationError",
    "RateLimitError",
    "AuthenticationError",
    "AuthorizationError",
    
    # Session
    "SessionException",
    "SessionNotFoundError",
    "SessionExpiredError",
    
    # Config
    "ConfigurationError",
    "MissingConfigError",
    
    # External
    "ExternalServiceError",
    "CircuitBreakerOpenError",
]
