"""
Personal Analytics Engine
User behavior tracking, productivity insights, and AI usage analytics
100% Local Processing - No data leaves your machine
"""

import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import asyncio
import statistics

logger = logging.getLogger(__name__)


class EventType(Enum):
    CHAT_MESSAGE = "chat_message"
    TASK_CREATED = "task_created"
    TASK_COMPLETED = "task_completed"
    DOCUMENT_INDEXED = "document_indexed"
    SEARCH_QUERY = "search_query"
    CODE_EXECUTION = "code_execution"
    AGENT_RUN = "agent_run"
    WORKFLOW_RUN = "workflow_run"
    VISION_ANALYSIS = "vision_analysis"
    VOICE_INTERACTION = "voice_interaction"
    ERROR = "error"
    SESSION_START = "session_start"
    SESSION_END = "session_end"


@dataclass
class AnalyticsEvent:
    """Represents an analytics event"""
    id: str
    type: EventType
    timestamp: datetime
    data: Dict[str, Any] = field(default_factory=dict)
    duration_ms: Optional[int] = None
    success: bool = True
    user_id: str = "default"


@dataclass
class SessionInfo:
    """User session information"""
    id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    events: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InsightReport:
    """AI-generated insights"""
    id: str
    generated_at: datetime
    period: str
    summary: str
    highlights: List[str]
    recommendations: List[str]
    metrics: Dict[str, Any]


class AnalyticsEngine:
    """
    Personal Analytics Engine
    
    Features:
    - Event tracking for all AI interactions
    - Productivity metrics and insights
    - Usage pattern analysis
    - AI-generated recommendations
    - Privacy-first: all data stays local
    """
    
    def __init__(self, storage_dir: str = "data/analytics"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.events: List[AnalyticsEvent] = []
        self.sessions: Dict[str, SessionInfo] = {}
        self.insights: List[InsightReport] = []
        
        self.current_session: Optional[str] = None
        self.event_counter = 0
        
        self._load_data()
    
    def _generate_event_id(self) -> str:
        self.event_counter += 1
        return f"evt_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self.event_counter}"
    
    def _generate_session_id(self) -> str:
        return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def _load_data(self):
        """Load analytics data from disk"""
        events_file = self.storage_dir / "events.json"
        if events_file.exists():
            try:
                with open(events_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for evt_data in data.get("events", [])[-10000:]:  # Keep last 10k events
                        event = AnalyticsEvent(
                            id=evt_data["id"],
                            type=EventType(evt_data["type"]),
                            timestamp=datetime.fromisoformat(evt_data["timestamp"]),
                            data=evt_data.get("data", {}),
                            duration_ms=evt_data.get("duration_ms"),
                            success=evt_data.get("success", True),
                            user_id=evt_data.get("user_id", "default")
                        )
                        self.events.append(event)
                    self.event_counter = data.get("counter", 0)
                logger.info(f"Loaded {len(self.events)} analytics events")
            except Exception as e:
                logger.error(f"Failed to load analytics: {e}")
        
        insights_file = self.storage_dir / "insights.json"
        if insights_file.exists():
            try:
                with open(insights_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for ins_data in data.get("insights", []):
                        insight = InsightReport(
                            id=ins_data["id"],
                            generated_at=datetime.fromisoformat(ins_data["generated_at"]),
                            period=ins_data["period"],
                            summary=ins_data["summary"],
                            highlights=ins_data.get("highlights", []),
                            recommendations=ins_data.get("recommendations", []),
                            metrics=ins_data.get("metrics", {})
                        )
                        self.insights.append(insight)
            except Exception as e:
                logger.error(f"Failed to load insights: {e}")
    
    def _save_data(self):
        """Save analytics data to disk"""
        try:
            events_file = self.storage_dir / "events.json"
            with open(events_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "events": [
                        {
                            "id": e.id,
                            "type": e.type.value,
                            "timestamp": e.timestamp.isoformat(),
                            "data": e.data,
                            "duration_ms": e.duration_ms,
                            "success": e.success,
                            "user_id": e.user_id
                        }
                        for e in self.events[-10000:]  # Keep last 10k
                    ],
                    "counter": self.event_counter,
                    "saved_at": datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
            
            insights_file = self.storage_dir / "insights.json"
            with open(insights_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "insights": [
                        {
                            "id": i.id,
                            "generated_at": i.generated_at.isoformat(),
                            "period": i.period,
                            "summary": i.summary,
                            "highlights": i.highlights,
                            "recommendations": i.recommendations,
                            "metrics": i.metrics
                        }
                        for i in self.insights[-100:]  # Keep last 100 insights
                    ]
                }, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save analytics: {e}")
    
    def start_session(self, user_id: str = "default") -> str:
        """Start a new analytics session"""
        session_id = self._generate_session_id()
        session = SessionInfo(
            id=session_id,
            start_time=datetime.now()
        )
        self.sessions[session_id] = session
        self.current_session = session_id
        
        self.track_event(
            event_type=EventType.SESSION_START,
            data={"session_id": session_id},
            user_id=user_id
        )
        
        return session_id
    
    def end_session(self, session_id: Optional[str] = None):
        """End an analytics session"""
        sid = session_id or self.current_session
        if sid and sid in self.sessions:
            session = self.sessions[sid]
            session.end_time = datetime.now()
            
            self.track_event(
                event_type=EventType.SESSION_END,
                data={
                    "session_id": sid,
                    "duration_minutes": (session.end_time - session.start_time).total_seconds() / 60
                }
            )
            
            if sid == self.current_session:
                self.current_session = None
    
    def track_event(
        self,
        event_type: EventType,
        data: Optional[Dict] = None,
        duration_ms: Optional[int] = None,
        success: bool = True,
        user_id: str = "default"
    ) -> AnalyticsEvent:
        """Track an analytics event"""
        event = AnalyticsEvent(
            id=self._generate_event_id(),
            type=event_type,
            timestamp=datetime.now(),
            data=data or {},
            duration_ms=duration_ms,
            success=success,
            user_id=user_id
        )
        
        self.events.append(event)
        
        # Add to current session
        if self.current_session and self.current_session in self.sessions:
            self.sessions[self.current_session].events.append(event.id)
        
        # Auto-save periodically
        if len(self.events) % 100 == 0:
            self._save_data()
        
        return event
    
    def get_events(
        self,
        event_type: Optional[EventType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get filtered events"""
        events = self.events
        
        if event_type:
            events = [e for e in events if e.type == event_type]
        
        if start_date:
            events = [e for e in events if e.timestamp >= start_date]
        
        if end_date:
            events = [e for e in events if e.timestamp <= end_date]
        
        events = sorted(events, key=lambda x: x.timestamp, reverse=True)
        
        return [
            {
                "id": e.id,
                "type": e.type.value,
                "timestamp": e.timestamp.isoformat(),
                "data": e.data,
                "duration_ms": e.duration_ms,
                "success": e.success
            }
            for e in events[:limit]
        ]
    
    def get_summary(self, days: int = 7) -> Dict:
        """Get analytics summary for the specified period"""
        cutoff = datetime.now() - timedelta(days=days)
        recent_events = [e for e in self.events if e.timestamp >= cutoff]
        
        # Count by type
        by_type = defaultdict(int)
        for event in recent_events:
            by_type[event.type.value] += 1
        
        # Success rate
        successful = len([e for e in recent_events if e.success])
        total = len(recent_events)
        success_rate = (successful / total * 100) if total > 0 else 100
        
        # Average duration by type
        durations_by_type = defaultdict(list)
        for event in recent_events:
            if event.duration_ms:
                durations_by_type[event.type.value].append(event.duration_ms)
        
        avg_durations = {
            k: statistics.mean(v) if v else 0
            for k, v in durations_by_type.items()
        }
        
        # Daily activity
        daily_counts = defaultdict(int)
        for event in recent_events:
            day = event.timestamp.strftime("%Y-%m-%d")
            daily_counts[day] += 1
        
        # Hourly distribution
        hourly_counts = defaultdict(int)
        for event in recent_events:
            hour = event.timestamp.hour
            hourly_counts[hour] += 1
        
        return {
            "period_days": days,
            "total_events": len(recent_events),
            "success_rate": round(success_rate, 2),
            "events_by_type": dict(by_type),
            "avg_duration_ms": avg_durations,
            "daily_activity": dict(sorted(daily_counts.items())),
            "hourly_distribution": dict(sorted(hourly_counts.items())),
            "most_active_hour": max(hourly_counts.items(), key=lambda x: x[1])[0] if hourly_counts else None
        }
    
    def get_productivity_metrics(self, days: int = 7) -> Dict:
        """Calculate productivity metrics"""
        cutoff = datetime.now() - timedelta(days=days)
        recent_events = [e for e in self.events if e.timestamp >= cutoff]
        
        # Tasks completed
        tasks_created = len([e for e in recent_events if e.type == EventType.TASK_CREATED])
        tasks_completed = len([e for e in recent_events if e.type == EventType.TASK_COMPLETED])
        completion_rate = (tasks_completed / tasks_created * 100) if tasks_created > 0 else 0
        
        # Chat interactions
        chat_count = len([e for e in recent_events if e.type == EventType.CHAT_MESSAGE])
        
        # Code executions
        code_runs = len([e for e in recent_events if e.type == EventType.CODE_EXECUTION])
        code_success = len([
            e for e in recent_events 
            if e.type == EventType.CODE_EXECUTION and e.success
        ])
        code_success_rate = (code_success / code_runs * 100) if code_runs > 0 else 0
        
        # Agent runs
        agent_runs = len([e for e in recent_events if e.type == EventType.AGENT_RUN])
        
        # Documents processed
        docs_indexed = len([e for e in recent_events if e.type == EventType.DOCUMENT_INDEXED])
        
        # Calculate productivity score (0-100)
        factors = [
            min(tasks_completed / max(days, 1) * 10, 25),  # Task completion
            min(chat_count / max(days, 1) * 2, 25),  # Engagement
            min(code_success_rate / 4, 25),  # Code quality
            min(agent_runs / max(days, 1) * 5, 25)  # Automation
        ]
        productivity_score = sum(factors)
        
        return {
            "period_days": days,
            "productivity_score": round(productivity_score, 1),
            "tasks": {
                "created": tasks_created,
                "completed": tasks_completed,
                "completion_rate": round(completion_rate, 1)
            },
            "chat": {
                "total_messages": chat_count,
                "avg_per_day": round(chat_count / max(days, 1), 1)
            },
            "code": {
                "executions": code_runs,
                "success_rate": round(code_success_rate, 1)
            },
            "automation": {
                "agent_runs": agent_runs,
                "workflow_runs": len([e for e in recent_events if e.type == EventType.WORKFLOW_RUN])
            },
            "documents": {
                "indexed": docs_indexed
            }
        }
    
    def get_usage_trends(self, days: int = 30) -> Dict:
        """Analyze usage trends over time"""
        cutoff = datetime.now() - timedelta(days=days)
        recent_events = [e for e in self.events if e.timestamp >= cutoff]
        
        # Weekly trends
        weeks = defaultdict(lambda: defaultdict(int))
        for event in recent_events:
            week = event.timestamp.strftime("%Y-W%W")
            weeks[week][event.type.value] += 1
            weeks[week]["total"] += 1
        
        # Calculate growth
        sorted_weeks = sorted(weeks.keys())
        if len(sorted_weeks) >= 2:
            current_week = weeks[sorted_weeks[-1]]["total"]
            prev_week = weeks[sorted_weeks[-2]]["total"]
            growth = ((current_week - prev_week) / max(prev_week, 1)) * 100
        else:
            growth = 0
        
        # Feature adoption
        feature_usage = {
            "voice_ai": len([e for e in recent_events if e.type == EventType.VOICE_INTERACTION]),
            "vision_ai": len([e for e in recent_events if e.type == EventType.VISION_ANALYSIS]),
            "code_execution": len([e for e in recent_events if e.type == EventType.CODE_EXECUTION]),
            "autonomous_agents": len([e for e in recent_events if e.type == EventType.AGENT_RUN]),
            "workflows": len([e for e in recent_events if e.type == EventType.WORKFLOW_RUN]),
            "search": len([e for e in recent_events if e.type == EventType.SEARCH_QUERY])
        }
        
        # Most used features
        sorted_features = sorted(feature_usage.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "period_days": days,
            "weekly_trends": {k: dict(v) for k, v in weeks.items()},
            "week_over_week_growth": round(growth, 1),
            "feature_usage": feature_usage,
            "top_features": [{"feature": f, "count": c} for f, c in sorted_features[:5] if c > 0],
            "total_events": len(recent_events)
        }
    
    async def generate_insights(self, days: int = 7) -> InsightReport:
        """Generate AI-powered insights"""
        summary = self.get_summary(days)
        productivity = self.get_productivity_metrics(days)
        trends = self.get_usage_trends(days)
        
        # Prepare context for AI
        context = f"""
Analytics Summary ({days} days):
- Total events: {summary['total_events']}
- Success rate: {summary['success_rate']}%
- Most active hour: {summary.get('most_active_hour', 'N/A')}

Productivity Metrics:
- Productivity score: {productivity['productivity_score']}/100
- Tasks completed: {productivity['tasks']['completed']}
- Task completion rate: {productivity['tasks']['completion_rate']}%
- Chat messages: {productivity['chat']['total_messages']}
- Code executions: {productivity['code']['executions']} (success: {productivity['code']['success_rate']}%)
- Agent runs: {productivity['automation']['agent_runs']}

Feature Usage:
{json.dumps(trends['feature_usage'], indent=2)}

Week-over-week growth: {trends['week_over_week_growth']}%
"""
        
        # Generate insights with AI
        try:
            import httpx
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "llama3.2",
                        "prompt": f"""Analyze these AI assistant usage analytics and provide:

{context}

1. A brief summary (2-3 sentences)
2. 3-5 key highlights (positive observations)
3. 3-5 recommendations for improving productivity

Format as JSON with keys: summary, highlights (array), recommendations (array)""",
                        "stream": False
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    ai_response = result.get("response", "")
                    
                    # Parse AI response
                    import re
                    json_match = re.search(r'\{[\s\S]*\}', ai_response)
                    if json_match:
                        ai_insights = json.loads(json_match.group())
                    else:
                        ai_insights = {
                            "summary": ai_response[:500],
                            "highlights": ["AI analysis completed"],
                            "recommendations": ["Continue using AI tools regularly"]
                        }
                else:
                    ai_insights = self._generate_basic_insights(productivity)
                    
        except Exception as e:
            logger.warning(f"AI insights generation failed: {e}")
            ai_insights = self._generate_basic_insights(productivity)
        
        insight = InsightReport(
            id=f"insight_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            generated_at=datetime.now(),
            period=f"last_{days}_days",
            summary=ai_insights.get("summary", ""),
            highlights=ai_insights.get("highlights", []),
            recommendations=ai_insights.get("recommendations", []),
            metrics={
                "summary": summary,
                "productivity": productivity,
                "trends": trends
            }
        )
        
        self.insights.append(insight)
        self._save_data()
        
        return insight
    
    def _generate_basic_insights(self, productivity: Dict) -> Dict:
        """Generate basic insights without AI"""
        highlights = []
        recommendations = []
        
        score = productivity['productivity_score']
        if score >= 75:
            highlights.append("Excellent productivity score!")
        elif score >= 50:
            highlights.append("Good productivity level")
        else:
            recommendations.append("Try to increase AI tool usage for better productivity")
        
        if productivity['tasks']['completion_rate'] >= 80:
            highlights.append(f"High task completion rate: {productivity['tasks']['completion_rate']}%")
        
        if productivity['code']['success_rate'] >= 90:
            highlights.append(f"Excellent code execution success rate")
        elif productivity['code']['success_rate'] < 70:
            recommendations.append("Review failed code executions to improve success rate")
        
        if productivity['automation']['agent_runs'] > 0:
            highlights.append(f"Using autonomous agents ({productivity['automation']['agent_runs']} runs)")
        else:
            recommendations.append("Try autonomous agents to automate repetitive tasks")
        
        return {
            "summary": f"Productivity score: {score}/100. {len(highlights)} positive observations.",
            "highlights": highlights or ["Keep using AI tools regularly"],
            "recommendations": recommendations or ["Continue your current workflow"]
        }
    
    def get_insights(self, limit: int = 10) -> List[Dict]:
        """Get recent insights"""
        recent = sorted(self.insights, key=lambda x: x.generated_at, reverse=True)
        
        return [
            {
                "id": i.id,
                "generated_at": i.generated_at.isoformat(),
                "period": i.period,
                "summary": i.summary,
                "highlights": i.highlights,
                "recommendations": i.recommendations
            }
            for i in recent[:limit]
        ]
    
    def export_data(self, format: str = "json") -> str:
        """Export all analytics data"""
        data = {
            "exported_at": datetime.now().isoformat(),
            "events": [
                {
                    "id": e.id,
                    "type": e.type.value,
                    "timestamp": e.timestamp.isoformat(),
                    "data": e.data,
                    "duration_ms": e.duration_ms,
                    "success": e.success
                }
                for e in self.events
            ],
            "insights": [
                {
                    "id": i.id,
                    "generated_at": i.generated_at.isoformat(),
                    "period": i.period,
                    "summary": i.summary,
                    "highlights": i.highlights,
                    "recommendations": i.recommendations
                }
                for i in self.insights
            ]
        }
        
        if format == "json":
            return json.dumps(data, indent=2, ensure_ascii=False)
        
        return json.dumps(data)
    
    def clear_data(self, before_date: Optional[datetime] = None):
        """Clear analytics data"""
        if before_date:
            self.events = [e for e in self.events if e.timestamp >= before_date]
        else:
            self.events = []
            self.insights = []
        
        self._save_data()


# Singleton
_analytics = None

def get_analytics_engine() -> AnalyticsEngine:
    global _analytics
    if _analytics is None:
        _analytics = AnalyticsEngine()
    return _analytics
