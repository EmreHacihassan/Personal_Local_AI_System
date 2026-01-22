"""
Autonomous Agent - Goal-driven AI agent that plans and executes tasks
Self-correcting with reflection and memory
100% Local execution
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class AgentStatus(str, Enum):
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    REFLECTING = "reflecting"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class ActionType(str, Enum):
    SEARCH = "search"
    READ = "read"
    WRITE = "write"
    CODE = "code"
    THINK = "think"
    ASK = "ask"
    BROWSE = "browse"
    COMPLETE = "complete"


@dataclass
class Action:
    """A single action the agent can take"""
    id: str
    type: ActionType
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    result: Optional[str] = None
    status: str = "pending"  # pending, executing, completed, failed
    duration: float = 0
    error: Optional[str] = None


@dataclass
class Plan:
    """Execution plan for a goal"""
    id: str
    goal: str
    actions: List[Action] = field(default_factory=list)
    current_step: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    reasoning: str = ""


@dataclass
class Memory:
    """Agent memory for context"""
    short_term: List[Dict] = field(default_factory=list)  # Recent actions
    long_term: Dict[str, Any] = field(default_factory=dict)  # Learned facts
    working: Dict[str, Any] = field(default_factory=dict)  # Current task context
    max_short_term: int = 50


@dataclass
class AgentSession:
    """An autonomous agent session"""
    id: str
    goal: str
    status: AgentStatus = AgentStatus.IDLE
    plan: Optional[Plan] = None
    memory: Memory = field(default_factory=Memory)
    history: List[Dict] = field(default_factory=list)
    iterations: int = 0
    max_iterations: int = 20
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    final_result: Optional[str] = None
    error: Optional[str] = None


class AutonomousAgent:
    """
    Goal-driven autonomous agent
    Plans, executes, and self-corrects
    """
    
    def __init__(self, storage_dir: str = "data/autonomous_agent"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.sessions: Dict[str, AgentSession] = {}
        self.active_session: Optional[str] = None
        self._stop_requested = False
        
        # Available tools/actions
        self.tools = {
            ActionType.SEARCH: self._tool_search,
            ActionType.READ: self._tool_read,
            ActionType.WRITE: self._tool_write,
            ActionType.CODE: self._tool_code,
            ActionType.THINK: self._tool_think,
            ActionType.ASK: self._tool_ask,
            ActionType.BROWSE: self._tool_browse,
            ActionType.COMPLETE: self._tool_complete,
        }
    
    async def create_session(
        self,
        goal: str,
        context: Optional[Dict] = None,
        max_iterations: int = 20
    ) -> AgentSession:
        """Create a new autonomous agent session"""
        session_id = str(uuid.uuid4())[:8]
        
        session = AgentSession(
            id=session_id,
            goal=goal,
            max_iterations=max_iterations,
            memory=Memory(
                working=context or {}
            )
        )
        
        self.sessions[session_id] = session
        logger.info(f"Created autonomous session: {session_id} - {goal[:50]}")
        
        return session
    
    async def run_session(
        self,
        session_id: str,
        on_update: Optional[Callable] = None
    ) -> AgentSession:
        """Run an autonomous agent session until completion"""
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError("Session not found")
        
        session.status = AgentStatus.PLANNING
        session.start_time = datetime.now()
        self.active_session = session_id
        self._stop_requested = False
        
        try:
            # Initial planning
            await self._plan(session)
            
            if on_update:
                await on_update({
                    "phase": "planned",
                    "plan": self._serialize_plan(session.plan)
                })
            
            # Execute loop
            while (
                session.iterations < session.max_iterations and
                session.status not in (AgentStatus.COMPLETED, AgentStatus.FAILED) and
                not self._stop_requested
            ):
                session.iterations += 1
                
                # Execute next action
                session.status = AgentStatus.EXECUTING
                await self._execute_next(session)
                
                if on_update:
                    await on_update({
                        "phase": "executed",
                        "iteration": session.iterations,
                        "action": self._serialize_action(session.plan.actions[session.plan.current_step - 1]) if session.plan else None
                    })
                
                # Reflect and potentially replan
                session.status = AgentStatus.REFLECTING
                should_continue = await self._reflect(session)
                
                if on_update:
                    await on_update({
                        "phase": "reflected",
                        "continue": should_continue
                    })
                
                if not should_continue:
                    break
            
            # Finalize
            if session.status not in (AgentStatus.COMPLETED, AgentStatus.FAILED):
                session.status = AgentStatus.COMPLETED
                session.final_result = await self._generate_final_result(session)
            
        except Exception as e:
            session.status = AgentStatus.FAILED
            session.error = str(e)
            logger.error(f"Autonomous agent failed: {e}")
        
        session.end_time = datetime.now()
        self.active_session = None
        
        return session
    
    async def _plan(self, session: AgentSession):
        """Create initial plan for the goal"""
        try:
            from core.llm_client import get_llm_client
            llm = await get_llm_client()
            
            # Build context from memory
            context_str = ""
            if session.memory.working:
                context_str = f"\nContext:\n{json.dumps(session.memory.working, indent=2)}"
            
            planning_prompt = f"""You are an autonomous AI agent. Create a detailed plan to achieve this goal.

Goal: {session.goal}
{context_str}

Available actions:
- SEARCH: Search for information (parameters: query)
- READ: Read a file or document (parameters: path)
- WRITE: Write content to a file (parameters: path, content)
- CODE: Execute Python code (parameters: code)
- THINK: Analyze and reason about something (parameters: topic)
- ASK: Ask a question to get clarification (parameters: question)
- BROWSE: Fetch information from a URL (parameters: url)
- COMPLETE: Mark goal as complete (parameters: summary)

Create a step-by-step plan. For each step specify:
1. Action type
2. Description of what to do
3. Parameters needed

Return as JSON:
{{
    "reasoning": "Your reasoning for this plan",
    "steps": [
        {{"type": "SEARCH", "description": "...", "parameters": {{"query": "..."}}}},
        ...
    ]
}}

Plan (JSON only):"""
            
            response = await llm.chat(planning_prompt)
            
            # Parse plan
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                plan_data = json.loads(json_match.group())
                
                actions = []
                for i, step in enumerate(plan_data.get("steps", [])):
                    action = Action(
                        id=f"action_{i}",
                        type=ActionType(step.get("type", "THINK").upper()),
                        description=step.get("description", ""),
                        parameters=step.get("parameters", {})
                    )
                    actions.append(action)
                
                session.plan = Plan(
                    id=str(uuid.uuid4())[:8],
                    goal=session.goal,
                    actions=actions,
                    reasoning=plan_data.get("reasoning", "")
                )
            else:
                # Fallback simple plan
                session.plan = Plan(
                    id=str(uuid.uuid4())[:8],
                    goal=session.goal,
                    actions=[
                        Action(id="action_0", type=ActionType.THINK, description="Analyze the goal", parameters={"topic": session.goal}),
                        Action(id="action_1", type=ActionType.COMPLETE, description="Complete the task", parameters={"summary": "Task completed"})
                    ],
                    reasoning="Simple fallback plan"
                )
                
        except Exception as e:
            logger.error(f"Planning failed: {e}")
            session.plan = Plan(
                id=str(uuid.uuid4())[:8],
                goal=session.goal,
                actions=[
                    Action(id="action_0", type=ActionType.THINK, description="Error during planning", parameters={"topic": str(e)})
                ],
                reasoning=f"Planning error: {e}"
            )
    
    async def _execute_next(self, session: AgentSession):
        """Execute the next action in the plan"""
        if not session.plan or session.plan.current_step >= len(session.plan.actions):
            session.status = AgentStatus.COMPLETED
            return
        
        action = session.plan.actions[session.plan.current_step]
        action.status = "executing"
        
        start_time = time.time()
        
        try:
            # Get tool and execute
            tool = self.tools.get(action.type)
            if tool:
                result = await tool(action.parameters, session)
                action.result = result
                action.status = "completed"
            else:
                action.result = f"Unknown action type: {action.type}"
                action.status = "failed"
                
        except Exception as e:
            action.error = str(e)
            action.status = "failed"
            logger.error(f"Action execution failed: {e}")
        
        action.duration = time.time() - start_time
        
        # Update memory
        session.memory.short_term.append({
            "action": action.type.value,
            "description": action.description,
            "result": action.result[:500] if action.result else None,
            "status": action.status,
            "timestamp": datetime.now().isoformat()
        })
        
        # Trim short-term memory
        if len(session.memory.short_term) > session.memory.max_short_term:
            session.memory.short_term = session.memory.short_term[-session.memory.max_short_term:]
        
        # Move to next step
        session.plan.current_step += 1
        
        # Check if complete action was executed
        if action.type == ActionType.COMPLETE:
            session.status = AgentStatus.COMPLETED
            session.final_result = action.result
    
    async def _reflect(self, session: AgentSession) -> bool:
        """Reflect on progress and decide whether to continue or replan"""
        try:
            from core.llm_client import get_llm_client
            llm = await get_llm_client()
            
            # Get recent actions
            recent = session.memory.short_term[-5:]
            actions_summary = "\n".join([
                f"- {a['action']}: {a['description'][:100]} -> {a['status']}"
                for a in recent
            ])
            
            # Remaining steps
            remaining = session.plan.actions[session.plan.current_step:] if session.plan else []
            remaining_summary = "\n".join([
                f"- {a.type.value}: {a.description[:100]}"
                for a in remaining[:5]
            ])
            
            reflection_prompt = f"""Reflect on the agent's progress:

Goal: {session.goal}

Recent actions:
{actions_summary}

Remaining steps:
{remaining_summary if remaining_summary else "No more steps"}

Iterations: {session.iterations}/{session.max_iterations}

Analyze:
1. Are we making progress toward the goal?
2. Should we continue with the plan, replan, or are we done?
3. Any adjustments needed?

Return JSON:
{{
    "progress_assessment": "...",
    "decision": "continue" | "replan" | "complete" | "fail",
    "reason": "...",
    "learned_facts": {{"key": "value"}}
}}

Reflection (JSON only):"""
            
            response = await llm.chat(reflection_prompt)
            
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                reflection = json.loads(json_match.group())
                
                decision = reflection.get("decision", "continue")
                
                # Update long-term memory with learned facts
                if "learned_facts" in reflection:
                    session.memory.long_term.update(reflection["learned_facts"])
                
                # Add to history
                session.history.append({
                    "iteration": session.iterations,
                    "reflection": reflection,
                    "timestamp": datetime.now().isoformat()
                })
                
                if decision == "complete":
                    session.status = AgentStatus.COMPLETED
                    return False
                elif decision == "fail":
                    session.status = AgentStatus.FAILED
                    session.error = reflection.get("reason", "Agent decided to fail")
                    return False
                elif decision == "replan":
                    # Create new plan
                    await self._plan(session)
                    return True
                else:  # continue
                    return len(session.plan.actions) > session.plan.current_step if session.plan else False
            
            # Default: continue if there are more steps
            return len(session.plan.actions) > session.plan.current_step if session.plan else False
            
        except Exception as e:
            logger.error(f"Reflection failed: {e}")
            return len(session.plan.actions) > session.plan.current_step if session.plan else False
    
    async def _generate_final_result(self, session: AgentSession) -> str:
        """Generate final summary of what was accomplished"""
        try:
            from core.llm_client import get_llm_client
            llm = await get_llm_client()
            
            actions_summary = "\n".join([
                f"- {a['action']}: {a['result'][:200] if a.get('result') else 'No result'}"
                for a in session.memory.short_term
            ])
            
            summary_prompt = f"""Summarize what was accomplished:

Goal: {session.goal}

Actions taken:
{actions_summary}

Learned facts: {json.dumps(session.memory.long_term)}

Provide a clear summary of:
1. What was accomplished
2. Key findings
3. Any remaining work

Summary:"""
            
            return await llm.chat(summary_prompt)
            
        except Exception as e:
            return f"Session completed with {session.iterations} iterations. Error generating summary: {e}"
    
    # Tool implementations
    
    async def _tool_search(self, params: Dict, session: AgentSession) -> str:
        """Search for information"""
        query = params.get("query", "")
        
        try:
            # Try RAG search first
            from rag.rag_engine import get_rag_engine
            engine = await get_rag_engine()
            results = await engine.query(query, top_k=3)
            
            if results.get("sources"):
                return f"Found {len(results['sources'])} relevant sources. Answer: {results.get('answer', '')[:500]}"
            
            # Fallback to LLM
            from core.llm_client import get_llm_client
            llm = await get_llm_client()
            return await llm.chat(f"Search query: {query}")
            
        except Exception as e:
            return f"Search failed: {e}"
    
    async def _tool_read(self, params: Dict, session: AgentSession) -> str:
        """Read a file"""
        path = params.get("path", "")
        
        try:
            file_path = Path(path)
            if file_path.exists() and file_path.is_file():
                content = file_path.read_text(encoding='utf-8')
                return content[:2000]  # Limit size
            return f"File not found: {path}"
        except Exception as e:
            return f"Read failed: {e}"
    
    async def _tool_write(self, params: Dict, session: AgentSession) -> str:
        """Write to a file"""
        path = params.get("path", "")
        content = params.get("content", "")
        
        try:
            # Only allow writing to specific directories
            file_path = Path(path)
            if not str(file_path).startswith(("data/", "output/")):
                return "Write restricted to data/ and output/ directories"
            
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding='utf-8')
            return f"Written {len(content)} characters to {path}"
        except Exception as e:
            return f"Write failed: {e}"
    
    async def _tool_code(self, params: Dict, session: AgentSession) -> str:
        """Execute Python code"""
        code = params.get("code", "")
        
        try:
            from core.code_interpreter import get_code_interpreter
            interpreter = get_code_interpreter()
            result = await interpreter.execute_python(code)
            
            return f"Output: {result.stdout[:500]}\nResult: {result.return_value}"
        except Exception as e:
            return f"Code execution failed: {e}"
    
    async def _tool_think(self, params: Dict, session: AgentSession) -> str:
        """Analyze and reason"""
        topic = params.get("topic", "")
        
        try:
            from core.llm_client import get_llm_client
            llm = await get_llm_client()
            
            context = json.dumps(session.memory.working)
            prompt = f"Analyze this topic:\n{topic}\n\nContext: {context}\n\nAnalysis:"
            
            return await llm.chat(prompt)
        except Exception as e:
            return f"Thinking failed: {e}"
    
    async def _tool_ask(self, params: Dict, session: AgentSession) -> str:
        """Ask a question (simulated - would need user interaction)"""
        question = params.get("question", "")
        
        # In a real implementation, this would pause and wait for user input
        return f"Question asked: {question} (User interaction not implemented)"
    
    async def _tool_browse(self, params: Dict, session: AgentSession) -> str:
        """Fetch information from URL"""
        url = params.get("url", "")
        
        try:
            import aiohttp
            async with aiohttp.ClientSession() as client:
                async with client.get(url, timeout=10) as resp:
                    text = await resp.text()
                    return text[:2000]  # Limit size
        except Exception as e:
            return f"Browse failed: {e}"
    
    async def _tool_complete(self, params: Dict, session: AgentSession) -> str:
        """Mark task as complete"""
        summary = params.get("summary", "Task completed")
        return summary
    
    # Helper methods
    
    def _serialize_plan(self, plan: Optional[Plan]) -> Optional[Dict]:
        """Serialize plan for output"""
        if not plan:
            return None
        return {
            "id": plan.id,
            "goal": plan.goal,
            "reasoning": plan.reasoning,
            "steps": [self._serialize_action(a) for a in plan.actions],
            "current_step": plan.current_step
        }
    
    def _serialize_action(self, action: Action) -> Dict:
        """Serialize action for output"""
        return {
            "id": action.id,
            "type": action.type.value,
            "description": action.description,
            "parameters": action.parameters,
            "status": action.status,
            "result": action.result[:500] if action.result else None,
            "duration": action.duration,
            "error": action.error
        }
    
    def stop_session(self, session_id: str):
        """Request stop of running session"""
        self._stop_requested = True
        if session_id in self.sessions:
            self.sessions[session_id].status = AgentStatus.PAUSED
    
    def get_session(self, session_id: str) -> Optional[AgentSession]:
        """Get session by ID"""
        return self.sessions.get(session_id)
    
    def list_sessions(self) -> List[Dict]:
        """List all sessions"""
        return [
            {
                "id": s.id,
                "goal": s.goal[:100],
                "status": s.status.value,
                "iterations": s.iterations,
                "start_time": s.start_time.isoformat() if s.start_time else None
            }
            for s in self.sessions.values()
        ]


# Global instance
autonomous_agent = AutonomousAgent()


def get_autonomous_agent() -> AutonomousAgent:
    """Get autonomous agent instance"""
    return autonomous_agent
