"""
Personal Analytics API Endpoints
User behavior tracking and productivity insights
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["Personal Analytics"])

_analytics = None

def get_analytics():
    global _analytics
    if _analytics is None:
        from core.analytics_engine import get_analytics_engine
        _analytics = get_analytics_engine()
    return _analytics


class TrackEventRequest(BaseModel):
    event_type: str
    data: Optional[dict] = None
    duration_ms: Optional[int] = None
    success: bool = True


@router.get("/status")
async def get_status():
    """Get analytics status"""
    analytics = get_analytics()
    return {
        "status": "available",
        "total_events": len(analytics.events),
        "total_insights": len(analytics.insights),
        "current_session": analytics.current_session
    }


@router.post("/session/start")
async def start_session(user_id: str = "default"):
    """Start a new analytics session"""
    analytics = get_analytics()
    session_id = analytics.start_session(user_id)
    
    return {
        "success": True,
        "session_id": session_id
    }


@router.post("/session/end")
async def end_session(session_id: Optional[str] = None):
    """End an analytics session"""
    analytics = get_analytics()
    analytics.end_session(session_id)
    
    return {"success": True}


@router.post("/track")
async def track_event(request: TrackEventRequest):
    """Track an analytics event"""
    try:
        analytics = get_analytics()
        
        from core.analytics_engine import EventType
        
        try:
            event_type = EventType(request.event_type)
        except ValueError:
            event_type = EventType.CHAT_MESSAGE  # Default
        
        event = analytics.track_event(
            event_type=event_type,
            data=request.data,
            duration_ms=request.duration_ms,
            success=request.success
        )
        
        return {
            "success": True,
            "event_id": event.id,
            "timestamp": event.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Event tracking failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events")
async def get_events(
    event_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(100, le=1000)
):
    """Get analytics events"""
    analytics = get_analytics()
    
    from core.analytics_engine import EventType
    
    et = None
    if event_type:
        try:
            et = EventType(event_type)
        except ValueError:
            pass
    
    sd = None
    if start_date:
        sd = datetime.fromisoformat(start_date)
    
    ed = None
    if end_date:
        ed = datetime.fromisoformat(end_date)
    
    events = analytics.get_events(
        event_type=et,
        start_date=sd,
        end_date=ed,
        limit=limit
    )
    
    return {"events": events, "count": len(events)}


@router.get("/summary")
async def get_summary(days: int = Query(7, ge=1, le=365)):
    """Get analytics summary"""
    analytics = get_analytics()
    return analytics.get_summary(days)


@router.get("/productivity")
async def get_productivity(days: int = Query(7, ge=1, le=365)):
    """Get productivity metrics"""
    analytics = get_analytics()
    return analytics.get_productivity_metrics(days)


@router.get("/trends")
async def get_trends(days: int = Query(30, ge=1, le=365)):
    """Get usage trends"""
    analytics = get_analytics()
    return analytics.get_usage_trends(days)


@router.post("/insights/generate")
async def generate_insights(days: int = Query(7, ge=1, le=30)):
    """Generate AI-powered insights"""
    try:
        analytics = get_analytics()
        insight = await analytics.generate_insights(days)
        
        return {
            "id": insight.id,
            "generated_at": insight.generated_at.isoformat(),
            "period": insight.period,
            "summary": insight.summary,
            "highlights": insight.highlights,
            "recommendations": insight.recommendations
        }
        
    except Exception as e:
        logger.error(f"Insights generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights")
async def get_insights(limit: int = Query(10, le=100)):
    """Get recent insights"""
    analytics = get_analytics()
    return {"insights": analytics.get_insights(limit)}


@router.get("/dashboard")
async def get_dashboard():
    """Get complete dashboard data"""
    analytics = get_analytics()
    
    return {
        "summary_7d": analytics.get_summary(7),
        "productivity": analytics.get_productivity_metrics(7),
        "trends": analytics.get_usage_trends(30),
        "recent_insights": analytics.get_insights(3),
        "recent_events": analytics.get_events(limit=20)
    }


@router.get("/export")
async def export_data(format: str = "json"):
    """Export all analytics data"""
    analytics = get_analytics()
    data = analytics.export_data(format)
    
    from fastapi.responses import Response
    
    if format == "json":
        return Response(
            content=data,
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=analytics_export.json"}
        )
    
    return {"data": data}


@router.delete("/clear")
async def clear_data(before_date: Optional[str] = None):
    """Clear analytics data"""
    analytics = get_analytics()
    
    bd = None
    if before_date:
        bd = datetime.fromisoformat(before_date)
    
    analytics.clear_data(bd)
    
    return {
        "success": True,
        "message": "Analytics data cleared"
    }


# Event type reference
@router.get("/event-types")
async def get_event_types():
    """Get available event types"""
    from core.analytics_engine import EventType
    
    return {
        "event_types": [
            {"value": et.value, "name": et.name}
            for et in EventType
        ]
    }
