"""
AI Security Scanner API Endpoints
Code vulnerability detection and security analysis
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/security", tags=["Security Scanner"])

_scanner = None

def get_scanner():
    global _scanner
    if _scanner is None:
        from core.security_scanner import get_security_scanner
        _scanner = get_security_scanner()
    return _scanner


class ScanCodeRequest(BaseModel):
    code: str
    language: str = "python"


class ScanDirectoryRequest(BaseModel):
    directory: str
    extensions: Optional[List[str]] = None
    exclude_patterns: Optional[List[str]] = None


class AIReviewRequest(BaseModel):
    code: str
    language: str = "python"


@router.get("/status")
async def get_status():
    """Get security scanner status"""
    scanner = get_scanner()
    return {
        "status": "available",
        "total_scans": len(scanner.scans),
        "supported_languages": ["python", "javascript", "typescript"],
        "features": ["static_analysis", "secret_detection", "dependency_check", "ai_review"]
    }


@router.post("/scan/code")
async def scan_code(request: ScanCodeRequest):
    """Scan a code snippet for vulnerabilities"""
    try:
        scanner = get_scanner()
        vulnerabilities = await scanner.scan_code_snippet(
            code=request.code,
            language=request.language
        )
        
        return {
            "success": True,
            "vulnerability_count": len(vulnerabilities),
            "vulnerabilities": [
                {
                    "id": v.id,
                    "type": v.type.value,
                    "severity": v.severity.value,
                    "title": v.title,
                    "description": v.description,
                    "line": v.line_number,
                    "code": v.code_snippet,
                    "recommendation": v.recommendation,
                    "cwe_id": v.cwe_id
                }
                for v in vulnerabilities
            ]
        }
        
    except Exception as e:
        logger.error(f"Code scan failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scan/file")
async def scan_file(filepath: str = Form(...)):
    """Scan a single file for vulnerabilities"""
    try:
        scanner = get_scanner()
        vulnerabilities = await scanner.scan_file(filepath)
        
        return {
            "success": True,
            "file": filepath,
            "vulnerability_count": len(vulnerabilities),
            "vulnerabilities": [
                {
                    "id": v.id,
                    "type": v.type.value,
                    "severity": v.severity.value,
                    "title": v.title,
                    "description": v.description,
                    "line": v.line_number,
                    "code": v.code_snippet,
                    "recommendation": v.recommendation,
                    "cwe_id": v.cwe_id,
                    "owasp": v.owasp_category
                }
                for v in vulnerabilities
            ]
        }
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.error(f"File scan failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scan/directory")
async def scan_directory(request: ScanDirectoryRequest):
    """Scan an entire directory for vulnerabilities"""
    try:
        scanner = get_scanner()
        result = await scanner.scan_directory(
            directory=request.directory,
            extensions=request.extensions,
            exclude_patterns=request.exclude_patterns
        )
        
        return {
            "success": True,
            "scan_id": result.id,
            "status": result.status,
            "files_scanned": result.files_scanned,
            "vulnerability_count": len(result.vulnerabilities),
            "summary": result.summary,
            "duration": (result.completed_at - result.started_at).total_seconds() if result.completed_at else None
        }
        
    except Exception as e:
        logger.error(f"Directory scan failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scan/upload")
async def scan_upload(file: UploadFile = File(...)):
    """Upload and scan a file"""
    try:
        scanner = get_scanner()
        
        content = await file.read()
        
        # Save temporarily
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(
            mode='wb',
            suffix=os.path.splitext(file.filename)[1],
            delete=False
        ) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            vulnerabilities = await scanner.scan_file(temp_path)
        finally:
            os.unlink(temp_path)
        
        return {
            "success": True,
            "filename": file.filename,
            "vulnerability_count": len(vulnerabilities),
            "vulnerabilities": [
                {
                    "id": v.id,
                    "type": v.type.value,
                    "severity": v.severity.value,
                    "title": v.title,
                    "description": v.description,
                    "line": v.line_number,
                    "code": v.code_snippet,
                    "recommendation": v.recommendation
                }
                for v in vulnerabilities
            ]
        }
        
    except Exception as e:
        logger.error(f"Upload scan failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/review/ai")
async def ai_code_review(request: AIReviewRequest):
    """Get AI-powered code review"""
    try:
        scanner = get_scanner()
        result = await scanner.ai_code_review(
            code=request.code,
            language=request.language
        )
        
        return {
            "success": True,
            "review": result
        }
        
    except Exception as e:
        logger.error(f"AI review failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dependencies/check")
async def check_dependencies(filepath: str = Form(...)):
    """Check dependencies for vulnerabilities"""
    try:
        scanner = get_scanner()
        vulnerabilities = await scanner.check_dependencies(filepath)
        
        return {
            "success": True,
            "file": filepath,
            "vulnerability_count": len(vulnerabilities),
            "vulnerabilities": vulnerabilities
        }
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.error(f"Dependency check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scans")
async def list_scans():
    """List all security scans"""
    scanner = get_scanner()
    return {"scans": scanner.list_scans()}


@router.get("/scans/{scan_id}")
async def get_scan(scan_id: str):
    """Get scan details"""
    scanner = get_scanner()
    scan = scanner.get_scan(scan_id)
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    return {
        "id": scan.id,
        "type": scan.scan_type,
        "status": scan.status,
        "files_scanned": scan.files_scanned,
        "summary": scan.summary,
        "started_at": scan.started_at.isoformat(),
        "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
        "vulnerabilities": [
            {
                "id": v.id,
                "type": v.type.value,
                "severity": v.severity.value,
                "title": v.title,
                "description": v.description,
                "file": v.file_path,
                "line": v.line_number,
                "code": v.code_snippet,
                "recommendation": v.recommendation,
                "cwe_id": v.cwe_id,
                "owasp": v.owasp_category
            }
            for v in scan.vulnerabilities
        ]
    }


@router.get("/scans/{scan_id}/report")
async def get_scan_report(scan_id: str, format: str = "json"):
    """Generate scan report"""
    scanner = get_scanner()
    report = scanner.generate_report(scan_id, format)
    
    if not report:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    if format == "markdown":
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(report, media_type="text/markdown")
    
    import json
    return json.loads(report)
