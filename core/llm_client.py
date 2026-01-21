"""
LLM Client Module
==================

Bu modül geriye uyumluluk için llm_manager'a bir alias sağlar.
Tüm işlevsellik core.llm_manager modülünden sağlanır.
"""

# Re-export from llm_manager for backwards compatibility
from core.llm_manager import (
    llm_manager,
    LLMManager,
)

# Alias'lar
llm_client = llm_manager
LLMClient = LLMManager

__all__ = [
    "llm_manager",
    "LLMManager",
    "llm_client",
    "LLMClient",
]
