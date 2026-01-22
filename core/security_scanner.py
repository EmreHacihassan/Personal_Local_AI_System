"""
AI Security Scanner
Code vulnerability detection, secret scanning, and security analysis
100% Local Processing
"""

import os
import re
import ast
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class SeverityLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class VulnerabilityType(Enum):
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    HARDCODED_SECRET = "hardcoded_secret"
    INSECURE_CRYPTO = "insecure_crypto"
    SSRF = "ssrf"
    INSECURE_DESERIALIZATION = "insecure_deserialization"
    XXE = "xxe"
    OPEN_REDIRECT = "open_redirect"
    WEAK_PASSWORD = "weak_password"
    DEBUG_CODE = "debug_code"
    INSECURE_RANDOM = "insecure_random"
    MISSING_AUTH = "missing_auth"
    SENSITIVE_DATA_EXPOSURE = "sensitive_data_exposure"
    DEPENDENCY_VULN = "dependency_vulnerability"


@dataclass
class Vulnerability:
    """Represents a security vulnerability"""
    id: str
    type: VulnerabilityType
    severity: SeverityLevel
    title: str
    description: str
    file_path: str
    line_number: int
    code_snippet: str
    recommendation: str
    cwe_id: Optional[str] = None
    owasp_category: Optional[str] = None
    confidence: float = 0.8


@dataclass
class ScanResult:
    """Results from a security scan"""
    id: str
    scan_type: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    files_scanned: int = 0
    vulnerabilities: List[Vulnerability] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)
    status: str = "running"


class SecurityScanner:
    """
    AI-Powered Security Scanner
    
    Features:
    - Static code analysis for common vulnerabilities
    - Secret and credential detection
    - Dependency vulnerability checking
    - AI-powered code review
    - OWASP Top 10 coverage
    """
    
    def __init__(self):
        self.scans: Dict[str, ScanResult] = {}
        self.scan_counter = 0
        
        # Secret patterns
        self.secret_patterns = [
            # API Keys
            (r'["\']?(?:api[_-]?key|apikey)["\']?\s*[:=]\s*["\']([a-zA-Z0-9_\-]{20,})["\']', "API Key"),
            (r'["\']?(?:secret[_-]?key|secretkey)["\']?\s*[:=]\s*["\']([a-zA-Z0-9_\-]{20,})["\']', "Secret Key"),
            
            # AWS
            (r'(?:AKIA|A3T|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}', "AWS Access Key ID"),
            (r'["\']?(?:aws[_-]?secret|secret[_-]?access[_-]?key)["\']?\s*[:=]\s*["\']([a-zA-Z0-9/+=]{40})["\']', "AWS Secret Key"),
            
            # Database
            (r'(?:mysql|postgres|mongodb|redis)://[^:]+:([^@]+)@', "Database Password"),
            (r'["\']?(?:db[_-]?password|database[_-]?password)["\']?\s*[:=]\s*["\']([^"\']+)["\']', "Database Password"),
            
            # Tokens
            (r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*', "JWT Token"),
            (r'ghp_[a-zA-Z0-9]{36}', "GitHub Personal Access Token"),
            (r'gho_[a-zA-Z0-9]{36}', "GitHub OAuth Token"),
            (r'sk-[a-zA-Z0-9]{48}', "OpenAI API Key"),
            
            # Private Keys
            (r'-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----', "Private Key"),
            (r'-----BEGIN OPENSSH PRIVATE KEY-----', "SSH Private Key"),
            
            # Generic passwords
            (r'["\']?password["\']?\s*[:=]\s*["\']([^"\']{8,})["\']', "Hardcoded Password"),
        ]
        
        # Vulnerability patterns for Python
        self.python_vuln_patterns = [
            # SQL Injection
            {
                "pattern": r'(?:execute|executemany)\s*\(\s*["\'].*%[sd].*["\'].*%',
                "type": VulnerabilityType.SQL_INJECTION,
                "severity": SeverityLevel.CRITICAL,
                "title": "Potential SQL Injection",
                "description": "String formatting in SQL query may allow SQL injection",
                "recommendation": "Use parameterized queries with placeholders",
                "cwe_id": "CWE-89",
                "owasp": "A03:2021-Injection"
            },
            {
                "pattern": r'(?:execute|executemany)\s*\(\s*f["\']',
                "type": VulnerabilityType.SQL_INJECTION,
                "severity": SeverityLevel.CRITICAL,
                "title": "SQL Injection via f-string",
                "description": "Using f-strings in SQL queries allows injection",
                "recommendation": "Use parameterized queries",
                "cwe_id": "CWE-89",
                "owasp": "A03:2021-Injection"
            },
            
            # Command Injection
            {
                "pattern": r'(?:os\.system|os\.popen|subprocess\.call|subprocess\.run)\s*\([^)]*(?:\+|%|\.format|f["\'])',
                "type": VulnerabilityType.COMMAND_INJECTION,
                "severity": SeverityLevel.CRITICAL,
                "title": "Command Injection",
                "description": "User input in shell command may allow command injection",
                "recommendation": "Use subprocess with shell=False and pass arguments as list",
                "cwe_id": "CWE-78",
                "owasp": "A03:2021-Injection"
            },
            {
                "pattern": r'shell\s*=\s*True',
                "type": VulnerabilityType.COMMAND_INJECTION,
                "severity": SeverityLevel.HIGH,
                "title": "Shell=True in subprocess",
                "description": "Using shell=True can enable command injection",
                "recommendation": "Use shell=False and pass command as list",
                "cwe_id": "CWE-78",
                "owasp": "A03:2021-Injection"
            },
            
            # Path Traversal
            {
                "pattern": r'(?:open|Path)\s*\([^)]*(?:request\.|user_|input)',
                "type": VulnerabilityType.PATH_TRAVERSAL,
                "severity": SeverityLevel.HIGH,
                "title": "Path Traversal",
                "description": "User input in file path may allow directory traversal",
                "recommendation": "Sanitize and validate file paths",
                "cwe_id": "CWE-22",
                "owasp": "A01:2021-Broken Access Control"
            },
            
            # Insecure Deserialization
            {
                "pattern": r'pickle\.(?:load|loads)\s*\(',
                "type": VulnerabilityType.INSECURE_DESERIALIZATION,
                "severity": SeverityLevel.HIGH,
                "title": "Insecure Pickle Deserialization",
                "description": "Unpickling untrusted data can execute arbitrary code",
                "recommendation": "Use safe serialization formats like JSON",
                "cwe_id": "CWE-502",
                "owasp": "A08:2021-Software and Data Integrity Failures"
            },
            {
                "pattern": r'yaml\.load\s*\([^)]*(?:Loader\s*=\s*None)?[^)]*\)',
                "type": VulnerabilityType.INSECURE_DESERIALIZATION,
                "severity": SeverityLevel.HIGH,
                "title": "Insecure YAML Load",
                "description": "Using yaml.load without safe_load can execute arbitrary code",
                "recommendation": "Use yaml.safe_load() instead",
                "cwe_id": "CWE-502",
                "owasp": "A08:2021-Software and Data Integrity Failures"
            },
            
            # Insecure Crypto
            {
                "pattern": r'(?:md5|sha1)\s*\(',
                "type": VulnerabilityType.INSECURE_CRYPTO,
                "severity": SeverityLevel.MEDIUM,
                "title": "Weak Hash Algorithm",
                "description": "MD5/SHA1 are cryptographically weak",
                "recommendation": "Use SHA-256 or stronger algorithms",
                "cwe_id": "CWE-328",
                "owasp": "A02:2021-Cryptographic Failures"
            },
            {
                "pattern": r'random\.[^s]',
                "type": VulnerabilityType.INSECURE_RANDOM,
                "severity": SeverityLevel.MEDIUM,
                "title": "Insecure Random Number Generator",
                "description": "Python's random module is not cryptographically secure",
                "recommendation": "Use secrets module for security-sensitive randomness",
                "cwe_id": "CWE-330",
                "owasp": "A02:2021-Cryptographic Failures"
            },
            
            # Debug Code
            {
                "pattern": r'(?:DEBUG\s*=\s*True|app\.debug\s*=\s*True)',
                "type": VulnerabilityType.DEBUG_CODE,
                "severity": SeverityLevel.MEDIUM,
                "title": "Debug Mode Enabled",
                "description": "Debug mode should be disabled in production",
                "recommendation": "Set DEBUG=False in production",
                "cwe_id": "CWE-489",
                "owasp": "A05:2021-Security Misconfiguration"
            },
            {
                "pattern": r'print\s*\([^)]*(?:password|secret|token|key)',
                "type": VulnerabilityType.SENSITIVE_DATA_EXPOSURE,
                "severity": SeverityLevel.MEDIUM,
                "title": "Sensitive Data in Print Statement",
                "description": "Printing sensitive information may expose secrets",
                "recommendation": "Remove debug prints containing sensitive data",
                "cwe_id": "CWE-200",
                "owasp": "A02:2021-Cryptographic Failures"
            },
            
            # XSS (in template contexts)
            {
                "pattern": r'render_template_string\s*\([^)]*(?:\+|%|\.format|f["\'])',
                "type": VulnerabilityType.XSS,
                "severity": SeverityLevel.HIGH,
                "title": "Template Injection / XSS",
                "description": "User input in template string may allow XSS or SSTI",
                "recommendation": "Use parameterized templates",
                "cwe_id": "CWE-79",
                "owasp": "A03:2021-Injection"
            },
            
            # SSRF
            {
                "pattern": r'requests\.(?:get|post|put|delete)\s*\([^)]*(?:request\.|user_|input)',
                "type": VulnerabilityType.SSRF,
                "severity": SeverityLevel.HIGH,
                "title": "Server-Side Request Forgery (SSRF)",
                "description": "User-controlled URL in HTTP request",
                "recommendation": "Validate and whitelist allowed URLs",
                "cwe_id": "CWE-918",
                "owasp": "A10:2021-Server-Side Request Forgery"
            },
            
            # XXE
            {
                "pattern": r'(?:etree\.parse|etree\.fromstring|minidom\.parse)',
                "type": VulnerabilityType.XXE,
                "severity": SeverityLevel.HIGH,
                "title": "Potential XXE Vulnerability",
                "description": "XML parsing may be vulnerable to XXE attacks",
                "recommendation": "Disable external entity processing",
                "cwe_id": "CWE-611",
                "owasp": "A05:2021-Security Misconfiguration"
            },
        ]
        
        # JavaScript/TypeScript patterns
        self.js_vuln_patterns = [
            {
                "pattern": r'eval\s*\(',
                "type": VulnerabilityType.COMMAND_INJECTION,
                "severity": SeverityLevel.CRITICAL,
                "title": "Eval Usage",
                "description": "eval() can execute arbitrary code",
                "recommendation": "Avoid eval; use JSON.parse for data",
                "cwe_id": "CWE-94",
                "owasp": "A03:2021-Injection"
            },
            {
                "pattern": r'innerHTML\s*=',
                "type": VulnerabilityType.XSS,
                "severity": SeverityLevel.HIGH,
                "title": "innerHTML Assignment",
                "description": "Direct innerHTML assignment may cause XSS",
                "recommendation": "Use textContent or sanitize HTML",
                "cwe_id": "CWE-79",
                "owasp": "A03:2021-Injection"
            },
            {
                "pattern": r'document\.write\s*\(',
                "type": VulnerabilityType.XSS,
                "severity": SeverityLevel.HIGH,
                "title": "document.write Usage",
                "description": "document.write can cause XSS",
                "recommendation": "Use DOM manipulation methods",
                "cwe_id": "CWE-79",
                "owasp": "A03:2021-Injection"
            },
            {
                "pattern": r'dangerouslySetInnerHTML',
                "type": VulnerabilityType.XSS,
                "severity": SeverityLevel.MEDIUM,
                "title": "React dangerouslySetInnerHTML",
                "description": "May cause XSS if not properly sanitized",
                "recommendation": "Sanitize HTML before rendering",
                "cwe_id": "CWE-79",
                "owasp": "A03:2021-Injection"
            },
        ]
    
    def _generate_scan_id(self) -> str:
        self.scan_counter += 1
        return f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.scan_counter}"
    
    def _generate_vuln_id(self, scan_id: str, index: int) -> str:
        return f"{scan_id}_vuln_{index}"
    
    async def scan_file(self, filepath: str) -> List[Vulnerability]:
        """Scan a single file for vulnerabilities"""
        vulnerabilities = []
        path = Path(filepath)
        
        if not path.exists():
            return vulnerabilities
        
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception as e:
            logger.error(f"Failed to read file {filepath}: {e}")
            return vulnerabilities
        
        # Determine file type
        ext = path.suffix.lower()
        
        # Scan for secrets
        for line_num, line in enumerate(lines, 1):
            for pattern, secret_type in self.secret_patterns:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    vuln = Vulnerability(
                        id=f"secret_{line_num}_{match.start()}",
                        type=VulnerabilityType.HARDCODED_SECRET,
                        severity=SeverityLevel.CRITICAL,
                        title=f"Hardcoded {secret_type}",
                        description=f"Found potential {secret_type} in source code",
                        file_path=str(path),
                        line_number=line_num,
                        code_snippet=line.strip()[:100] + "..." if len(line) > 100 else line.strip(),
                        recommendation="Move secrets to environment variables or a secure vault",
                        cwe_id="CWE-798",
                        owasp_category="A02:2021-Cryptographic Failures"
                    )
                    vulnerabilities.append(vuln)
        
        # Language-specific scanning
        patterns = []
        if ext in ['.py']:
            patterns = self.python_vuln_patterns
        elif ext in ['.js', '.ts', '.jsx', '.tsx']:
            patterns = self.js_vuln_patterns
        
        for line_num, line in enumerate(lines, 1):
            for vuln_pattern in patterns:
                if re.search(vuln_pattern["pattern"], line, re.IGNORECASE):
                    vuln = Vulnerability(
                        id=f"vuln_{line_num}",
                        type=vuln_pattern["type"],
                        severity=vuln_pattern["severity"],
                        title=vuln_pattern["title"],
                        description=vuln_pattern["description"],
                        file_path=str(path),
                        line_number=line_num,
                        code_snippet=line.strip()[:100] + "..." if len(line) > 100 else line.strip(),
                        recommendation=vuln_pattern["recommendation"],
                        cwe_id=vuln_pattern.get("cwe_id"),
                        owasp_category=vuln_pattern.get("owasp")
                    )
                    vulnerabilities.append(vuln)
        
        return vulnerabilities
    
    async def scan_directory(
        self, 
        directory: str,
        extensions: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> ScanResult:
        """Scan an entire directory for vulnerabilities"""
        scan_id = self._generate_scan_id()
        scan = ScanResult(
            id=scan_id,
            scan_type="directory",
            started_at=datetime.now()
        )
        self.scans[scan_id] = scan
        
        if extensions is None:
            extensions = ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rb', '.php']
        
        if exclude_patterns is None:
            exclude_patterns = ['node_modules', 'venv', '.venv', '__pycache__', '.git', 'dist', 'build']
        
        path = Path(directory)
        files_to_scan = []
        
        # Collect files
        for ext in extensions:
            for file_path in path.rglob(f"*{ext}"):
                # Check exclusions
                skip = False
                for exclude in exclude_patterns:
                    if exclude in str(file_path):
                        skip = True
                        break
                if not skip:
                    files_to_scan.append(file_path)
        
        # Scan files
        vuln_counter = 0
        for file_path in files_to_scan:
            vulns = await self.scan_file(str(file_path))
            for vuln in vulns:
                vuln.id = self._generate_vuln_id(scan_id, vuln_counter)
                vuln_counter += 1
            scan.vulnerabilities.extend(vulns)
            scan.files_scanned += 1
        
        # Generate summary
        scan.summary = {
            "critical": len([v for v in scan.vulnerabilities if v.severity == SeverityLevel.CRITICAL]),
            "high": len([v for v in scan.vulnerabilities if v.severity == SeverityLevel.HIGH]),
            "medium": len([v for v in scan.vulnerabilities if v.severity == SeverityLevel.MEDIUM]),
            "low": len([v for v in scan.vulnerabilities if v.severity == SeverityLevel.LOW]),
            "info": len([v for v in scan.vulnerabilities if v.severity == SeverityLevel.INFO]),
        }
        
        scan.completed_at = datetime.now()
        scan.status = "completed"
        
        return scan
    
    async def scan_code_snippet(self, code: str, language: str = "python") -> List[Vulnerability]:
        """Scan a code snippet for vulnerabilities"""
        vulnerabilities = []
        lines = code.split('\n')
        
        # Select patterns based on language
        patterns = []
        if language.lower() in ['python', 'py']:
            patterns = self.python_vuln_patterns
        elif language.lower() in ['javascript', 'js', 'typescript', 'ts']:
            patterns = self.js_vuln_patterns
        
        # Scan for secrets
        for line_num, line in enumerate(lines, 1):
            for pattern, secret_type in self.secret_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    vuln = Vulnerability(
                        id=f"snippet_secret_{line_num}",
                        type=VulnerabilityType.HARDCODED_SECRET,
                        severity=SeverityLevel.CRITICAL,
                        title=f"Hardcoded {secret_type}",
                        description=f"Found potential {secret_type}",
                        file_path="<snippet>",
                        line_number=line_num,
                        code_snippet=line.strip()[:100],
                        recommendation="Remove hardcoded secrets",
                        cwe_id="CWE-798"
                    )
                    vulnerabilities.append(vuln)
        
        # Scan for vulnerabilities
        for line_num, line in enumerate(lines, 1):
            for vuln_pattern in patterns:
                if re.search(vuln_pattern["pattern"], line, re.IGNORECASE):
                    vuln = Vulnerability(
                        id=f"snippet_vuln_{line_num}",
                        type=vuln_pattern["type"],
                        severity=vuln_pattern["severity"],
                        title=vuln_pattern["title"],
                        description=vuln_pattern["description"],
                        file_path="<snippet>",
                        line_number=line_num,
                        code_snippet=line.strip()[:100],
                        recommendation=vuln_pattern["recommendation"],
                        cwe_id=vuln_pattern.get("cwe_id")
                    )
                    vulnerabilities.append(vuln)
        
        return vulnerabilities
    
    async def ai_code_review(self, code: str, language: str = "python") -> Dict:
        """
        Use AI to perform a comprehensive code review
        """
        try:
            import httpx
            
            prompt = f"""You are a senior security engineer. Analyze the following {language} code for:

1. Security vulnerabilities (OWASP Top 10)
2. Code quality issues
3. Best practice violations
4. Potential bugs

Code:
```{language}
{code}
```

Provide a structured analysis with:
- List of issues found (severity, description, line reference)
- Recommendations for each issue
- Overall security score (0-100)

Format as JSON."""

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "llama3.2",
                        "prompt": prompt,
                        "stream": False
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    analysis = result.get("response", "")
                    
                    # Try to parse as JSON
                    try:
                        # Find JSON in response
                        json_match = re.search(r'\{[\s\S]*\}', analysis)
                        if json_match:
                            return json.loads(json_match.group())
                    except:
                        pass
                    
                    return {"raw_analysis": analysis}
                else:
                    return {"error": "AI review failed"}
                    
        except Exception as e:
            logger.error(f"AI code review failed: {e}")
            return {"error": str(e)}
    
    async def check_dependencies(self, requirements_file: str) -> List[Dict]:
        """
        Check dependencies for known vulnerabilities
        """
        vulnerabilities = []
        path = Path(requirements_file)
        
        if not path.exists():
            return vulnerabilities
        
        try:
            with open(path, 'r') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Failed to read requirements: {e}")
            return vulnerabilities
        
        # Known vulnerable packages (simplified - in production use a CVE database)
        known_vulns = {
            "django<2.2.28": {"cve": "CVE-2022-28347", "severity": "high", "desc": "SQL Injection"},
            "flask<2.0.0": {"cve": "CVE-2019-1010083", "severity": "high", "desc": "DoS vulnerability"},
            "requests<2.20.0": {"cve": "CVE-2018-18074", "severity": "medium", "desc": "Information exposure"},
            "pyyaml<5.4": {"cve": "CVE-2020-14343", "severity": "critical", "desc": "Arbitrary code execution"},
            "pillow<8.1.2": {"cve": "CVE-2021-25293", "severity": "high", "desc": "Buffer overflow"},
            "urllib3<1.26.5": {"cve": "CVE-2021-33503", "severity": "medium", "desc": "ReDoS"},
            "jinja2<2.11.3": {"cve": "CVE-2020-28493", "severity": "medium", "desc": "ReDoS"},
            "cryptography<3.3.2": {"cve": "CVE-2020-36242", "severity": "high", "desc": "Integer overflow"},
        }
        
        # Parse requirements
        for line in content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Extract package name and version
            match = re.match(r'([a-zA-Z0-9_-]+)\s*([<>=!]+\s*[\d.]+)?', line)
            if match:
                pkg_name = match.group(1).lower()
                version_spec = match.group(2) or ""
                
                # Check against known vulnerabilities (simplified)
                for vuln_spec, vuln_info in known_vulns.items():
                    if vuln_spec.startswith(pkg_name):
                        vulnerabilities.append({
                            "package": pkg_name,
                            "installed_version": version_spec,
                            "vulnerable_version": vuln_spec,
                            "cve": vuln_info["cve"],
                            "severity": vuln_info["severity"],
                            "description": vuln_info["desc"]
                        })
        
        return vulnerabilities
    
    def get_scan(self, scan_id: str) -> Optional[ScanResult]:
        """Get scan results"""
        return self.scans.get(scan_id)
    
    def list_scans(self) -> List[Dict]:
        """List all scans"""
        return [
            {
                "id": scan.id,
                "type": scan.scan_type,
                "status": scan.status,
                "files_scanned": scan.files_scanned,
                "vulnerability_count": len(scan.vulnerabilities),
                "summary": scan.summary,
                "started_at": scan.started_at.isoformat(),
                "completed_at": scan.completed_at.isoformat() if scan.completed_at else None
            }
            for scan in self.scans.values()
        ]
    
    def generate_report(self, scan_id: str, format: str = "json") -> Optional[str]:
        """Generate a security report"""
        scan = self.scans.get(scan_id)
        if not scan:
            return None
        
        if format == "json":
            return json.dumps({
                "scan_id": scan.id,
                "scan_type": scan.scan_type,
                "status": scan.status,
                "started_at": scan.started_at.isoformat(),
                "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
                "files_scanned": scan.files_scanned,
                "summary": scan.summary,
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
            }, indent=2)
        
        elif format == "markdown":
            md = f"""# Security Scan Report

**Scan ID:** {scan.id}  
**Type:** {scan.scan_type}  
**Status:** {scan.status}  
**Files Scanned:** {scan.files_scanned}  
**Started:** {scan.started_at.isoformat()}  
**Completed:** {scan.completed_at.isoformat() if scan.completed_at else 'N/A'}

## Summary

| Severity | Count |
|----------|-------|
| Critical | {scan.summary.get('critical', 0)} |
| High | {scan.summary.get('high', 0)} |
| Medium | {scan.summary.get('medium', 0)} |
| Low | {scan.summary.get('low', 0)} |
| Info | {scan.summary.get('info', 0)} |

## Vulnerabilities

"""
            for v in scan.vulnerabilities:
                md += f"""### [{v.severity.value.upper()}] {v.title}

- **Type:** {v.type.value}
- **File:** `{v.file_path}` (line {v.line_number})
- **CWE:** {v.cwe_id or 'N/A'}
- **OWASP:** {v.owasp_category or 'N/A'}

**Description:** {v.description}

**Code:**
```
{v.code_snippet}
```

**Recommendation:** {v.recommendation}

---

"""
            return md
        
        return None


# Singleton
_scanner = None

def get_security_scanner() -> SecurityScanner:
    global _scanner
    if _scanner is None:
        _scanner = SecurityScanner()
    return _scanner
