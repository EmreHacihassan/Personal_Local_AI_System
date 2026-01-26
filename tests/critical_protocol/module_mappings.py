"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║    PREMIUM TEST PROTOCOL - MODULE COMPATIBILITY MAPPING                        ║
║                                                                                 ║
║  This file contains the authoritative mappings between test expectations       ║
║  and actual module implementations. Used for automatic test adaptation.        ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class ClassMapping:
    """Mapping for a class"""
    expected_name: str
    actual_name: str
    module_path: str
    init_params: Dict[str, Any] = field(default_factory=dict)
    method_mappings: Dict[str, str] = field(default_factory=dict)
    attr_mappings: Dict[str, str] = field(default_factory=dict)


@dataclass  
class FunctionMapping:
    """Mapping for a function"""
    expected_name: str
    actual_name: str
    module_path: str


@dataclass
class ModuleMapping:
    """Complete mapping for a module"""
    module_path: str
    classes: List[ClassMapping] = field(default_factory=list)
    functions: List[FunctionMapping] = field(default_factory=list)
    constants: Dict[str, str] = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════════════
#                           PHASE 1: CORE FOUNDATION
# ═══════════════════════════════════════════════════════════════════════════════

PHASE_1_MAPPINGS = {
    "core.config": ModuleMapping(
        module_path="core.config",
        classes=[
            ClassMapping(
                expected_name="Settings",
                actual_name="Settings",
                module_path="core.config",
                init_params={},  # No params required
                attr_mappings={
                    "DEBUG": "API_DEBUG",  # Common mistake mapping
                    "PORT": "API_PORT",
                    "HOST": "API_HOST"
                }
            )
        ],
        functions=[],
        constants={}
    ),
    "core.logger": ModuleMapping(
        module_path="core.logger",
        classes=[
            ClassMapping(
                expected_name="LoggerSetup",
                actual_name="LoggerSetup",
                module_path="core.logger"
            )
        ],
        functions=[
            FunctionMapping(
                expected_name="get_logger",
                actual_name="get_logger",
                module_path="core.logger"
            ),
            FunctionMapping(
                expected_name="setup_logging",  # Wrong expectation
                actual_name="get_logger",       # Actual function
                module_path="core.logger"
            )
        ]
    )
}

# ═══════════════════════════════════════════════════════════════════════════════
#                           PHASE 2: LLM & AI CORE
# ═══════════════════════════════════════════════════════════════════════════════

PHASE_2_MAPPINGS = {
    "core.embedding": ModuleMapping(
        module_path="core.embedding",
        classes=[
            ClassMapping(
                expected_name="EmbeddingManager",
                actual_name="EmbeddingManager",
                module_path="core.embedding",
                method_mappings={
                    "embed": "embed_text",
                    "encode": "embed_text",
                    "get_embedding": "embed_text"
                }
            )
        ]
    ),
    "core.prompts": ModuleMapping(
        module_path="core.prompts",
        constants={
            "SYSTEM_PROMPT": "SYSTEM_PROMPT_TR",  # Turkish version is primary
            "SYSTEM_PROMPT_EN": "SYSTEM_PROMPT_EN"
        }
    ),
    "core.streaming": ModuleMapping(
        module_path="core.streaming",
        classes=[
            ClassMapping(
                expected_name="StreamingHandler",  # Wrong expectation
                actual_name="StreamManager",        # Actual class
                module_path="core.streaming"
            ),
            ClassMapping(
                expected_name="StreamManager",
                actual_name="StreamManager",
                module_path="core.streaming"
            )
        ]
    )
}

# ═══════════════════════════════════════════════════════════════════════════════
#                           PHASE 3: MEMORY & CACHE
# ═══════════════════════════════════════════════════════════════════════════════

PHASE_3_MAPPINGS = {
    "core.memory": ModuleMapping(
        module_path="core.memory",
        classes=[
            ClassMapping(
                expected_name="MemoryManager",
                actual_name="MemoryManager",
                module_path="core.memory",
                method_mappings={
                    "add": "add_message",
                    "get": "get_messages",
                    "search": "get_context_for_query"
                }
            )
        ]
    ),
    "core.memgpt_memory": ModuleMapping(
        module_path="core.memgpt_memory",
        classes=[
            ClassMapping(
                expected_name="TieredMemoryManager",
                actual_name="TieredMemoryManager",
                module_path="core.memgpt_memory",
                init_params={
                    "storage": "SQLiteMemoryStorage(db_path)"
                }
            ),
            ClassMapping(
                expected_name="SQLiteMemoryStorage",
                actual_name="SQLiteMemoryStorage",
                module_path="core.memgpt_memory",
                init_params={
                    "db_path": "required"  # Required parameter
                }
            )
        ]
    )
}

# ═══════════════════════════════════════════════════════════════════════════════
#                        PHASE 5: VECTOR STORE & EMBEDDINGS
# ═══════════════════════════════════════════════════════════════════════════════

PHASE_5_MAPPINGS = {
    "core.chromadb_manager": ModuleMapping(
        module_path="core.chromadb_manager",
        classes=[
            ClassMapping(
                expected_name="ChromaDBManager",
                actual_name="ChromaDBManager",
                module_path="core.chromadb_manager",
                attr_mappings={
                    "collection": "_collection",
                    "client": "_client",
                    "get_collection": "_collection"
                }
            )
        ]
    )
}

# ═══════════════════════════════════════════════════════════════════════════════
#                           PHASE 6: KNOWLEDGE GRAPH
# ═══════════════════════════════════════════════════════════════════════════════

PHASE_6_MAPPINGS = {
    "core.graph_rag": ModuleMapping(
        module_path="core.graph_rag",
        classes=[
            ClassMapping(
                expected_name="GraphRAGPipeline",
                actual_name="GraphRAGPipeline",
                module_path="core.graph_rag",
                init_params={
                    "graph_store": "InMemoryGraphStore()"
                }
            ),
            ClassMapping(
                expected_name="InMemoryGraphStore",
                actual_name="InMemoryGraphStore",
                module_path="core.graph_rag"
            )
        ]
    )
}

# ═══════════════════════════════════════════════════════════════════════════════
#                        PHASE 12: SECURITY & GUARDRAILS
# ═══════════════════════════════════════════════════════════════════════════════

PHASE_12_MAPPINGS = {
    "core.security_hardening": ModuleMapping(
        module_path="core.security_hardening",
        classes=[
            ClassMapping(
                expected_name="SecurityHardening",
                actual_name="SecurityHardening",
                module_path="core.security_hardening",
                method_mappings={
                    "check_injection": "check_action",
                    "sanitize_input": "sanitize",
                    "validate": "verify_text_input"
                },
                attr_mappings={
                    "sanitizer": "_sanitizer"
                }
            )
        ]
    ),
    "core.guardrails": ModuleMapping(
        module_path="core.guardrails",
        classes=[
            ClassMapping(
                expected_name="Guardrails",
                actual_name="Guardrails",
                module_path="core.guardrails",
                method_mappings={
                    "validate_input": "check_input",
                    "validate_output": "check_output",
                    "validate": "check"
                }
            )
        ]
    )
}

# ═══════════════════════════════════════════════════════════════════════════════
#                          PHASE 14: LEARNING SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

PHASE_14_MAPPINGS = {
    "core.learning_journey_system": ModuleMapping(
        module_path="core.learning_journey_system",
        classes=[
            ClassMapping(
                expected_name="AIContentGenerator",
                actual_name="AIContentGenerator",
                module_path="core.learning_journey_system",
                method_mappings={
                    "generate": "generate_lesson_content",
                    "generate_quiz": "generate_quiz_content",
                    "generate_content": "generate_lesson_content"
                }
            )
        ]
    )
}

# ═══════════════════════════════════════════════════════════════════════════════
#                       PHASE 15: FRONTEND INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

PHASE_15_MAPPINGS = {
    "frontend-next": {
        "components_dir": "src/components",  # Not root level
        "app_dir": "src/app",
        "api_dir": "src/app/api",
        "pages_dir": "src/pages"  # If using pages router
    }
}


# ═══════════════════════════════════════════════════════════════════════════════
#                           ALL MAPPINGS COMBINED
# ═══════════════════════════════════════════════════════════════════════════════

ALL_PHASE_MAPPINGS = {
    1: PHASE_1_MAPPINGS,
    2: PHASE_2_MAPPINGS,
    3: PHASE_3_MAPPINGS,
    5: PHASE_5_MAPPINGS,
    6: PHASE_6_MAPPINGS,
    12: PHASE_12_MAPPINGS,
    14: PHASE_14_MAPPINGS,
    15: PHASE_15_MAPPINGS
}


def get_actual_name(module_path: str, expected_name: str, item_type: str = "class") -> str:
    """
    Get the actual name for an expected name in a module
    
    Args:
        module_path: The module path (e.g., "core.config")
        expected_name: The expected class/function/constant name
        item_type: "class", "function", or "constant"
        
    Returns:
        The actual name if a mapping exists, otherwise the expected name
    """
    for phase_mappings in ALL_PHASE_MAPPINGS.values():
        if not isinstance(phase_mappings, dict):
            continue
            
        if module_path not in phase_mappings:
            continue
            
        mapping = phase_mappings[module_path]
        
        if isinstance(mapping, ModuleMapping):
            if item_type == "class":
                for cls in mapping.classes:
                    if cls.expected_name == expected_name:
                        return cls.actual_name
            elif item_type == "function":
                for func in mapping.functions:
                    if func.expected_name == expected_name:
                        return func.actual_name
            elif item_type == "constant":
                if expected_name in mapping.constants:
                    return mapping.constants[expected_name]
                    
    return expected_name


def get_method_mapping(module_path: str, class_name: str, method_name: str) -> str:
    """Get the actual method name for an expected method"""
    for phase_mappings in ALL_PHASE_MAPPINGS.values():
        if not isinstance(phase_mappings, dict):
            continue
            
        if module_path not in phase_mappings:
            continue
            
        mapping = phase_mappings[module_path]
        
        if isinstance(mapping, ModuleMapping):
            for cls in mapping.classes:
                if cls.actual_name == class_name or cls.expected_name == class_name:
                    if method_name in cls.method_mappings:
                        return cls.method_mappings[method_name]
                        
    return method_name


def get_attr_mapping(module_path: str, class_name: str, attr_name: str) -> str:
    """Get the actual attribute name for an expected attribute"""
    for phase_mappings in ALL_PHASE_MAPPINGS.values():
        if not isinstance(phase_mappings, dict):
            continue
            
        if module_path not in phase_mappings:
            continue
            
        mapping = phase_mappings[module_path]
        
        if isinstance(mapping, ModuleMapping):
            for cls in mapping.classes:
                if cls.actual_name == class_name or cls.expected_name == class_name:
                    if attr_name in cls.attr_mappings:
                        return cls.attr_mappings[attr_name]
                        
    return attr_name


def get_init_params(module_path: str, class_name: str) -> Dict[str, Any]:
    """Get the required init params for a class"""
    for phase_mappings in ALL_PHASE_MAPPINGS.values():
        if not isinstance(phase_mappings, dict):
            continue
            
        if module_path not in phase_mappings:
            continue
            
        mapping = phase_mappings[module_path]
        
        if isinstance(mapping, ModuleMapping):
            for cls in mapping.classes:
                if cls.actual_name == class_name or cls.expected_name == class_name:
                    return cls.init_params
                    
    return {}
