"""
API Routers
===========

Modüler API endpoint yapısı.
Her router belirli bir işlevsellik grubunu yönetir.
"""

from .health import router as health_router
from .documents import router as documents_router
from .notes import router as notes_router
from .rag import router as rag_router
from .plugins import router as plugins_router
from .admin import router as admin_router
from .advanced_rag import router as advanced_rag_router
from .voice_router import voice_router  # Voice & Multimodal (LOCAL)
from .screen_router import router as screen_router  # Screen Capture (LOCAL)

__all__ = [
    "health_router",
    "documents_router",
    "notes_router",
    "rag_router",
    "plugins_router",
    "admin_router",
    "advanced_rag_router",
    "voice_router",
    "screen_router",
]
