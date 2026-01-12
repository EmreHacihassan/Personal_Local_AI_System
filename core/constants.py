"""
Enterprise AI Assistant - Sabitler
===================================

Uygulama genelinde kullanılan sabit değerler.
Magic number'ları ortadan kaldırarak kod okunabilirliğini artırır.
"""


# =============================================================================
# ZAMAN SABİTLERİ (saniye cinsinden)
# =============================================================================
CACHE_TTL_HEALTH_CHECK = 30          # Sağlık kontrolü cache süresi
CACHE_TTL_SESSION_LIST = 5           # Oturum listesi cache süresi
CACHE_TTL_ONE_HOUR = 3600           # 1 saat
CACHE_TTL_ONE_DAY = 86400           # 24 saat
CACHE_TTL_ONE_WEEK = 604800         # 7 gün

REQUEST_TIMEOUT_DEFAULT = 30         # Varsayılan istek zaman aşımı
REQUEST_TIMEOUT_LONG = 120           # Uzun işlemler için zaman aşımı
REQUEST_TIMEOUT_STREAMING = 300      # Streaming için zaman aşımı

HEALTH_CHECK_INTERVAL = 30           # Sağlık kontrolü aralığı
METRICS_COLLECTION_INTERVAL = 60     # Metrik toplama aralığı


# =============================================================================
# BOYUT SABİTLERİ
# =============================================================================
MAX_MESSAGE_LENGTH = 10000           # Maksimum mesaj uzunluğu (karakter)
MAX_DOCUMENT_SIZE_MB = 50            # Maksimum doküman boyutu (MB)
MAX_DOCUMENT_SIZE_BYTES = MAX_DOCUMENT_SIZE_MB * 1024 * 1024

MAX_CHUNK_SIZE = 1000                # Varsayılan chunk boyutu (karakter)
CHUNK_OVERLAP = 200                  # Chunk örtüşme miktarı

EMBEDDING_CACHE_MAX_SIZE = 2000      # Embedding cache'indeki maksimum giriş
LRU_CACHE_MAX_SIZE = 1000            # Genel LRU cache boyutu


# =============================================================================
# BAĞLANTI SABİTLERİ
# =============================================================================
CONNECTION_POOL_SIZE = 10            # Bağlantı havuzu boyutu
CONNECTION_POOL_MAX_SIZE = 20        # Maksimum bağlantı havuzu boyutu
MAX_RETRIES = 3                      # Maksimum yeniden deneme sayısı
RETRY_BACKOFF_FACTOR = 0.5           # Yeniden deneme gecikme faktörü


# =============================================================================
# RATE LIMITING SABİTLERİ
# =============================================================================
RATE_LIMIT_REQUESTS_PER_MINUTE = 60  # Dakikada maksimum istek
RATE_LIMIT_WINDOW_SECONDS = 60       # Rate limit penceresi


# =============================================================================
# API SABİTLERİ
# =============================================================================
API_VERSION = "v1"                   # API versiyonu
API_PREFIX = f"/api/{API_VERSION}"   # API yolu öneki
API_TITLE = "Enterprise AI Assistant API"
API_DESCRIPTION = "Kurumsal AI Asistan REST API"


# =============================================================================
# RAG SABİTLERİ
# =============================================================================
RAG_TOP_K_DEFAULT = 5                # Varsayılan döndürülecek sonuç sayısı
RAG_TOP_K_MAX = 20                   # Maksimum döndürülecek sonuç sayısı
RAG_SIMILARITY_THRESHOLD = 0.5       # Benzerlik eşiği
RAG_RERANK_TOP_K = 10                # Reranking için top-k


# =============================================================================
# LLM SABİTLERİ
# =============================================================================
LLM_MAX_TOKENS = 4096                # Maksimum token sayısı
LLM_TEMPERATURE_DEFAULT = 0.7        # Varsayılan sıcaklık
LLM_TEMPERATURE_CREATIVE = 0.9       # Yaratıcı mod sıcaklığı
LLM_TEMPERATURE_PRECISE = 0.3        # Hassas mod sıcaklığı

CONTEXT_WINDOW_SIZE = 65536          # LLM context penceresi (karakter)
MAX_CONTEXT_TOKENS = 8192            # Maksimum context token'ı


# =============================================================================
# DOSYA TİPLERİ
# =============================================================================
SUPPORTED_EXTENSIONS = {
    "text": [".txt", ".md", ".rst", ".log"],
    "code": [".py", ".js", ".ts", ".java", ".c", ".cpp", ".go", ".rs"],
    "document": [".pdf", ".docx", ".doc", ".pptx", ".xlsx"],
    "data": [".json", ".yaml", ".yml", ".xml", ".csv"],
}

# Tüm desteklenen uzantılar
ALL_SUPPORTED_EXTENSIONS = []
for exts in SUPPORTED_EXTENSIONS.values():
    ALL_SUPPORTED_EXTENSIONS.extend(exts)


# =============================================================================
# HTTP DURUM KODLARI
# =============================================================================
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_NO_CONTENT = 204
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_CONFLICT = 409
HTTP_UNPROCESSABLE_ENTITY = 422
HTTP_TOO_MANY_REQUESTS = 429
HTTP_INTERNAL_SERVER_ERROR = 500
HTTP_SERVICE_UNAVAILABLE = 503


# =============================================================================
# LOG SEVİYELERİ
# =============================================================================
LOG_LEVEL_DEBUG = "DEBUG"
LOG_LEVEL_INFO = "INFO"
LOG_LEVEL_WARNING = "WARNING"
LOG_LEVEL_ERROR = "ERROR"
LOG_LEVEL_CRITICAL = "CRITICAL"


# =============================================================================
# PAGINATION SABİTLERİ
# =============================================================================
PAGE_SIZE_DEFAULT = 20               # Varsayılan sayfa boyutu
PAGE_SIZE_MAX = 100                  # Maksimum sayfa boyutu
PAGE_SIZE_MIN = 1                    # Minimum sayfa boyutu
