"""
🎯 Instructor - Structured LLM Outputs
======================================

Instructor ile garantili yapısal çıktılar:
- Pydantic model validasyonu
- Otomatik retry ve self-correction
- Streaming desteği
- Partial responses
- Multiple model support (OpenAI, Ollama, Anthropic)

Instructor: https://github.com/jxnl/instructor
"""

import asyncio
import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import (
    Any, Callable, Dict, Generic, List, Literal, Optional, 
    Type, TypeVar, Union, get_args, get_origin
)
from pydantic import BaseModel, Field, ValidationError, field_validator
import logging

# Optional instructor import
try:
    import instructor
    from instructor import patch as instructor_patch
    INSTRUCTOR_AVAILABLE = True
except ImportError:
    INSTRUCTOR_AVAILABLE = False
    instructor = None

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


# ============ RESPONSE MODELS ============

class Confidence(str, Enum):
    """Confidence levels for responses"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNCERTAIN = "uncertain"


class Citation(BaseModel):
    """Source citation"""
    source: str = Field(..., description="Source document or URL")
    page: Optional[int] = Field(None, description="Page number if applicable")
    quote: Optional[str] = Field(None, description="Relevant quote from source")
    relevance_score: float = Field(0.0, ge=0.0, le=1.0, description="Relevance score 0-1")


class ExtractedEntity(BaseModel):
    """Named entity extraction result"""
    text: str = Field(..., description="Entity text")
    entity_type: str = Field(..., description="Entity type (person, org, location, etc.)")
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    start_position: Optional[int] = None
    end_position: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SentimentResult(BaseModel):
    """Sentiment analysis result"""
    sentiment: Literal["positive", "negative", "neutral", "mixed"]
    confidence: float = Field(..., ge=0.0, le=1.0)
    positive_score: float = Field(0.0, ge=0.0, le=1.0)
    negative_score: float = Field(0.0, ge=0.0, le=1.0)
    neutral_score: float = Field(0.0, ge=0.0, le=1.0)
    aspects: List[Dict[str, Any]] = Field(default_factory=list, description="Aspect-based sentiment")


class Classification(BaseModel):
    """Classification result"""
    label: str = Field(..., description="Classification label")
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: Optional[str] = Field(None, description="Reasoning for classification")
    alternative_labels: List[Dict[str, float]] = Field(
        default_factory=list, 
        description="Alternative labels with scores"
    )


class QuestionAnswer(BaseModel):
    """Question answering response"""
    question: str = Field(..., description="Original question")
    answer: str = Field(..., description="Generated answer")
    confidence: Confidence = Field(Confidence.MEDIUM)
    citations: List[Citation] = Field(default_factory=list)
    reasoning_steps: List[str] = Field(default_factory=list)
    follow_up_questions: List[str] = Field(default_factory=list)
    
    @field_validator('answer')
    @classmethod
    def answer_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Answer cannot be empty")
        return v.strip()


class Summary(BaseModel):
    """Document summary"""
    title: Optional[str] = Field(None, description="Suggested title")
    summary: str = Field(..., description="Main summary")
    key_points: List[str] = Field(default_factory=list, description="Key takeaways")
    topics: List[str] = Field(default_factory=list, description="Main topics")
    word_count: int = Field(0, description="Original document word count")
    compression_ratio: float = Field(0.0, description="Summary/original ratio")


class CodeExplanation(BaseModel):
    """Code explanation result"""
    language: str = Field(..., description="Programming language")
    purpose: str = Field(..., description="What the code does")
    explanation: str = Field(..., description="Detailed explanation")
    key_concepts: List[str] = Field(default_factory=list)
    complexity: Literal["simple", "moderate", "complex"] = "moderate"
    potential_issues: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class ToolCall(BaseModel):
    """Function/tool call specification"""
    name: str = Field(..., description="Tool name to call")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")
    reasoning: Optional[str] = Field(None, description="Why this tool was chosen")


class MultiStepPlan(BaseModel):
    """Multi-step task plan"""
    goal: str = Field(..., description="Overall goal")
    steps: List[Dict[str, Any]] = Field(..., description="Ordered steps")
    estimated_duration: Optional[str] = Field(None)
    dependencies: List[Dict[str, Any]] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)


class ConversationIntent(BaseModel):
    """User intent classification for conversation"""
    primary_intent: str = Field(..., description="Main user intent")
    secondary_intents: List[str] = Field(default_factory=list)
    entities: List[ExtractedEntity] = Field(default_factory=list)
    requires_tool: bool = Field(False, description="Does this require a tool call?")
    tool_suggestion: Optional[ToolCall] = None
    requires_rag: bool = Field(False, description="Should we search knowledge base?")
    rag_query: Optional[str] = Field(None, description="Suggested RAG query")
    clarification_needed: bool = Field(False)
    clarification_question: Optional[str] = None


class RAGResponse(BaseModel):
    """RAG-enhanced response"""
    answer: str = Field(..., description="Generated answer")
    citations: List[Citation] = Field(default_factory=list)
    confidence: Confidence = Field(Confidence.MEDIUM)
    source_documents: List[str] = Field(default_factory=list)
    related_topics: List[str] = Field(default_factory=list)
    knowledge_gaps: List[str] = Field(
        default_factory=list, 
        description="Information not found in sources"
    )


class ChainOfThought(BaseModel):
    """Chain-of-thought reasoning"""
    question: str
    thought_process: List[str] = Field(..., description="Step-by-step reasoning")
    intermediate_conclusions: List[str] = Field(default_factory=list)
    final_answer: str
    confidence: Confidence = Field(Confidence.MEDIUM)
    assumptions_made: List[str] = Field(default_factory=list)


# ============ STRUCTURED OUTPUT CLIENT ============

class StructuredOutputClient:
    """
    Structured Output Client
    
    Garantili yapısal LLM çıktıları için unified interface.
    Instructor ile veya manuel JSON parsing ile çalışır.
    """
    
    def __init__(
        self,
        llm_client: Any = None,
        model: str = "llama3.2",
        max_retries: int = 3,
        use_instructor: bool = True
    ):
        self.base_client = llm_client
        self.model = model
        self.max_retries = max_retries
        self.use_instructor = use_instructor and INSTRUCTOR_AVAILABLE
        
        # Patch client with instructor if available
        if self.use_instructor and self.base_client:
            try:
                self.client = instructor_patch(self.base_client)
                logger.info("✅ Instructor patching successful")
            except Exception as e:
                logger.warning(f"Instructor patching failed: {e}")
                self.client = self.base_client
                self.use_instructor = False
        else:
            self.client = self.base_client
    
    async def generate(
        self,
        response_model: Type[T],
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2000,
        **kwargs
    ) -> T:
        """
        Generate structured output
        
        Args:
            response_model: Pydantic model for response structure
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: LLM temperature (lower = more deterministic)
            max_tokens: Maximum response tokens
            
        Returns:
            Validated Pydantic model instance
        """
        # Build schema instruction
        schema_json = response_model.model_json_schema()
        schema_instruction = self._build_schema_instruction(response_model, schema_json)
        
        # Combine prompts
        full_system = (system_prompt or "") + "\n\n" + schema_instruction
        
        # Try generation with retries
        last_error = None
        for attempt in range(self.max_retries):
            try:
                if self.use_instructor and hasattr(self.client, 'chat'):
                    # Use instructor
                    result = await self._instructor_generate(
                        response_model=response_model,
                        prompt=prompt,
                        system_prompt=full_system,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        **kwargs
                    )
                else:
                    # Manual JSON extraction
                    result = await self._manual_generate(
                        response_model=response_model,
                        prompt=prompt,
                        system_prompt=full_system,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        **kwargs
                    )
                
                return result
                
            except ValidationError as e:
                last_error = e
                logger.warning(f"Validation error (attempt {attempt + 1}): {e}")
                
                # Add correction instruction for retry
                prompt = f"{prompt}\n\n[Previous attempt had validation errors: {str(e)[:200]}. Please fix and try again.]"
                
            except Exception as e:
                last_error = e
                logger.error(f"Generation error (attempt {attempt + 1}): {e}")
        
        raise ValueError(f"Failed after {self.max_retries} attempts. Last error: {last_error}")
    
    async def _instructor_generate(
        self,
        response_model: Type[T],
        prompt: str,
        system_prompt: str,
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> T:
        """Generate using instructor library"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        result = self.client.chat.completions.create(
            model=self.model,
            response_model=response_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        return result
    
    async def _manual_generate(
        self,
        response_model: Type[T],
        prompt: str,
        system_prompt: str,
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> T:
        """Generate and parse JSON manually"""
        # This is a fallback - in real implementation, call your LLM
        # For now, we'll use a simple Ollama call
        
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": self.model,
                        "prompt": f"{system_prompt}\n\nUser: {prompt}",
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens
                        }
                    },
                    timeout=120.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    text = data.get("response", "")
                    
                    # Extract JSON from response
                    json_obj = self._extract_json(text)
                    
                    # Validate with Pydantic
                    return response_model.model_validate(json_obj)
        
        except Exception as e:
            logger.error(f"Manual generation failed: {e}")
            raise
    
    def _build_schema_instruction(self, model: Type[BaseModel], schema: Dict) -> str:
        """Build instruction for JSON schema"""
        # Get field descriptions
        fields_desc = []
        for field_name, field_info in schema.get("properties", {}).items():
            desc = field_info.get("description", "")
            field_type = field_info.get("type", "any")
            required = field_name in schema.get("required", [])
            req_str = "(required)" if required else "(optional)"
            fields_desc.append(f"  - {field_name}: {field_type} {req_str} - {desc}")
        
        fields_text = "\n".join(fields_desc)
        
        return f"""
You MUST respond with a valid JSON object matching this exact schema:

Model: {model.__name__}
{model.__doc__ or ""}

Fields:
{fields_text}

CRITICAL RULES:
1. Output ONLY valid JSON - no markdown, no explanations before/after
2. All required fields MUST be present
3. Field types MUST match exactly (strings, numbers, arrays, etc.)
4. Use null for optional fields you don't fill
5. Arrays must be proper JSON arrays []
6. Nested objects must be proper JSON objects {{}}

Example format:
{json.dumps(self._generate_example(schema), indent=2)}
"""
    
    def _generate_example(self, schema: Dict) -> Dict:
        """Generate example JSON from schema"""
        example = {}
        for field_name, field_info in schema.get("properties", {}).items():
            field_type = field_info.get("type", "string")
            if field_type == "string":
                example[field_name] = "example_value"
            elif field_type == "integer":
                example[field_name] = 0
            elif field_type == "number":
                example[field_name] = 0.0
            elif field_type == "boolean":
                example[field_name] = True
            elif field_type == "array":
                example[field_name] = []
            elif field_type == "object":
                example[field_name] = {}
            else:
                example[field_name] = None
        return example
    
    def _extract_json(self, text: str) -> Dict:
        """Extract JSON from LLM response"""
        # Try direct parse first
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass
        
        # Try to find JSON block
        json_patterns = [
            r'```json\s*([\s\S]*?)\s*```',
            r'```\s*([\s\S]*?)\s*```',
            r'\{[\s\S]*\}'
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            for match in matches:
                try:
                    if isinstance(match, str):
                        # Clean up common issues
                        cleaned = match.strip()
                        cleaned = re.sub(r',\s*}', '}', cleaned)  # Trailing commas
                        cleaned = re.sub(r',\s*]', ']', cleaned)
                        return json.loads(cleaned)
                except json.JSONDecodeError:
                    continue
        
        raise ValueError(f"Could not extract valid JSON from response: {text[:200]}...")


# ============ SPECIALIZED EXTRACTORS ============

class IntentExtractor:
    """Extract user intent with structured output"""
    
    def __init__(self, client: StructuredOutputClient):
        self.client = client
    
    async def extract(self, user_message: str, conversation_history: Optional[str] = None) -> ConversationIntent:
        """Extract intent from user message"""
        history_context = f"\n\nConversation history:\n{conversation_history}" if conversation_history else ""
        
        prompt = f"""Analyze this user message and extract the intent:

User message: "{user_message}"{history_context}

Determine:
1. Primary intent (what does the user want to do?)
2. Any secondary intents
3. Named entities mentioned
4. Whether a tool/function call is needed
5. Whether RAG search is needed
6. If clarification is needed"""

        return await self.client.generate(
            response_model=ConversationIntent,
            prompt=prompt,
            system_prompt="You are an intent classification system. Be precise and accurate."
        )


class EntityExtractor:
    """Extract named entities with structured output"""
    
    def __init__(self, client: StructuredOutputClient):
        self.client = client
    
    async def extract(
        self, 
        text: str, 
        entity_types: Optional[List[str]] = None
    ) -> List[ExtractedEntity]:
        """Extract entities from text"""
        types_str = ", ".join(entity_types) if entity_types else "person, organization, location, date, number, product, event"
        
        prompt = f"""Extract all named entities from this text:

Text: "{text}"

Entity types to look for: {types_str}

For each entity, provide:
- The exact text
- Entity type
- Confidence score (0-1)
- Start and end positions if possible"""

        class EntityList(BaseModel):
            entities: List[ExtractedEntity]
        
        result = await self.client.generate(
            response_model=EntityList,
            prompt=prompt
        )
        
        return result.entities


class QuestionAnswerer:
    """RAG-enhanced question answering with structured output"""
    
    def __init__(self, client: StructuredOutputClient):
        self.client = client
    
    async def answer(
        self,
        question: str,
        context: str,
        require_citations: bool = True
    ) -> QuestionAnswer:
        """Answer question with context and citations"""
        citation_instruction = """
You MUST cite your sources using the format [Source: document_name, Page: X].
Include at least one citation for each claim you make.""" if require_citations else ""

        prompt = f"""Answer this question based on the provided context:

Question: {question}

Context:
{context}

{citation_instruction}

Provide:
1. A clear, accurate answer
2. Citations for each claim
3. Your confidence level
4. Reasoning steps
5. Suggested follow-up questions"""

        return await self.client.generate(
            response_model=QuestionAnswer,
            prompt=prompt,
            system_prompt="You are a precise Q&A system. Only answer based on provided context. Never make up information."
        )


class Summarizer:
    """Document summarization with structured output"""
    
    def __init__(self, client: StructuredOutputClient):
        self.client = client
    
    async def summarize(
        self,
        text: str,
        max_length: int = 500,
        style: Literal["bullet", "paragraph", "tldr"] = "paragraph"
    ) -> Summary:
        """Summarize text with structure"""
        style_instructions = {
            "bullet": "Use bullet points for the summary",
            "paragraph": "Write flowing paragraphs",
            "tldr": "Write a single TL;DR sentence"
        }
        
        word_count = len(text.split())
        
        prompt = f"""Summarize this text ({word_count} words):

Text:
{text[:10000]}{"..." if len(text) > 10000 else ""}

Requirements:
- Maximum length: {max_length} words
- Style: {style_instructions[style]}
- Extract key points
- Identify main topics"""

        return await self.client.generate(
            response_model=Summary,
            prompt=prompt
        )


class ChainOfThoughtReasoner:
    """Chain-of-thought reasoning with structured output"""
    
    def __init__(self, client: StructuredOutputClient):
        self.client = client
    
    async def reason(self, question: str, context: Optional[str] = None) -> ChainOfThought:
        """Perform chain-of-thought reasoning"""
        context_section = f"\n\nContext:\n{context}" if context else ""
        
        prompt = f"""Solve this step-by-step:

Question: {question}{context_section}

Think through this carefully:
1. Break down the problem
2. Consider each step
3. Draw intermediate conclusions
4. Arrive at final answer

Show your complete thought process."""

        return await self.client.generate(
            response_model=ChainOfThought,
            prompt=prompt,
            system_prompt="You are a careful logical reasoner. Show all your work."
        )


# ============ CONVENIENCE FUNCTIONS ============

_default_client: Optional[StructuredOutputClient] = None


def get_structured_client() -> StructuredOutputClient:
    """Get or create default structured output client"""
    global _default_client
    if _default_client is None:
        _default_client = StructuredOutputClient()
    return _default_client


async def extract_intent(message: str, history: Optional[str] = None) -> ConversationIntent:
    """Quick intent extraction"""
    extractor = IntentExtractor(get_structured_client())
    return await extractor.extract(message, history)


async def answer_question(question: str, context: str) -> QuestionAnswer:
    """Quick question answering"""
    answerer = QuestionAnswerer(get_structured_client())
    return await answerer.answer(question, context)


async def summarize_text(text: str, style: str = "paragraph") -> Summary:
    """Quick summarization"""
    summarizer = Summarizer(get_structured_client())
    return await summarizer.summarize(text, style=style)


# ============ EXPORTS ============

__all__ = [
    # Client
    "StructuredOutputClient",
    # Response models
    "Confidence",
    "Citation",
    "ExtractedEntity",
    "SentimentResult",
    "Classification",
    "QuestionAnswer",
    "Summary",
    "CodeExplanation",
    "ToolCall",
    "MultiStepPlan",
    "ConversationIntent",
    "RAGResponse",
    "ChainOfThought",
    # Extractors
    "IntentExtractor",
    "EntityExtractor",
    "QuestionAnswerer",
    "Summarizer",
    "ChainOfThoughtReasoner",
    # Convenience
    "get_structured_client",
    "extract_intent",
    "answer_question",
    "summarize_text",
]
