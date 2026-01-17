import os
import sys

# Ensure project root is on sys.path when running directly
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.llm_manager import llm_manager
from core.embedding import embedding_manager
from core.vector_store import VectorStore
from core.config import settings

def main():
    print("cwd:", os.getcwd())
    print("OLLAMA_BASE_URL:", settings.OLLAMA_BASE_URL)
    print("Primary model:", settings.OLLAMA_PRIMARY_MODEL, "available?", llm_manager.check_model_available(settings.OLLAMA_PRIMARY_MODEL))
    print("Backup model:", settings.OLLAMA_BACKUP_MODEL, "available?", llm_manager.check_model_available(settings.OLLAMA_BACKUP_MODEL))
    print("Embedding model:", embedding_manager.model_name, "available?", embedding_manager.check_model_available())
    vs = VectorStore()
    print("Chroma path exists:", os.path.isdir(str(settings.CHROMA_PERSIST_DIR)))
    print("VectorStore collection:", vs.collection_name)
    try:
        print("Trying short LLM generate...")
        out = llm_manager.generate(prompt="Merhaba, kısa bir yanıt ver.", temperature=0.1)
        print(out[:200])
    except Exception as e:
        print("LLM generate failed:", e)

if __name__ == "__main__":
    main()
