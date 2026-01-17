"""
📊 Code Analysis Plugin
=======================

Kod analizi ve kalite değerlendirmesi plugin'i.
"""

import logging
import re
from typing import Any, Dict, List, Optional
from plugins.base import PluginBase, PluginResult

logger = logging.getLogger(__name__)


class CodeAnalysisPlugin(PluginBase):
    """
    Kod analizi plugin'i.
    
    Kod kalitesi, complexity, potansiyel sorunlar gibi
    analiz yetenekleri ekler.
    """
    
    name = "code_analysis"
    version = "1.0.0"
    description = "Kod analizi ve kalite değerlendirmesi"
    author = "Enterprise AI Team"
    
    # Language patterns
    LANGUAGE_PATTERNS = {
        "python": {
            "extension": ".py",
            "comment": "#",
            "multiline_start": '"""',
            "multiline_end": '"""',
            "function": r"def\s+(\w+)\s*\(",
            "class": r"class\s+(\w+)\s*[:\(]",
            "import": r"^(?:from\s+\S+\s+)?import\s+",
        },
        "javascript": {
            "extension": ".js",
            "comment": "//",
            "multiline_start": "/*",
            "multiline_end": "*/",
            "function": r"(?:function\s+(\w+)|(\w+)\s*=\s*(?:async\s+)?(?:function|\([^)]*\)\s*=>))",
            "class": r"class\s+(\w+)",
            "import": r"^(?:import|require)\s*",
        },
        "typescript": {
            "extension": ".ts",
            "comment": "//",
            "multiline_start": "/*",
            "multiline_end": "*/",
            "function": r"(?:function\s+(\w+)|(\w+)\s*(?::\s*\w+)?\s*=\s*(?:async\s+)?(?:\([^)]*\)\s*=>))",
            "class": r"class\s+(\w+)",
            "import": r"^import\s+",
        },
    }
    
    async def execute(self, input_data: Dict[str, Any]) -> PluginResult:
        """
        Kod analizi yap.
        
        Args:
            input_data: {
                "code": str,  # Analiz edilecek kod
                "language": str,  # python, javascript, typescript
                "operation": str,  # analyze, complexity, security, quality
            }
        """
        code = input_data.get("code")
        language = input_data.get("language", "python")
        operation = input_data.get("operation", "analyze")
        
        if not code:
            return PluginResult(
                success=False,
                error="Code is required"
            )
        
        try:
            if operation == "analyze":
                result = self._full_analysis(code, language)
            elif operation == "complexity":
                result = self._complexity_analysis(code, language)
            elif operation == "security":
                result = self._security_scan(code, language)
            elif operation == "quality":
                result = self._quality_score(code, language)
            elif operation == "stats":
                result = self._code_stats(code, language)
            else:
                return PluginResult(
                    success=False,
                    error=f"Unknown operation: {operation}"
                )
            
            return PluginResult(
                success=True,
                data=result
            )
            
        except Exception as e:
            logger.error(f"Code analysis error: {e}")
            return PluginResult(
                success=False,
                error=str(e)
            )
    
    def _full_analysis(self, code: str, language: str) -> Dict[str, Any]:
        """Tam kod analizi"""
        return {
            "stats": self._code_stats(code, language),
            "complexity": self._complexity_analysis(code, language),
            "security": self._security_scan(code, language),
            "quality": self._quality_score(code, language),
        }
    
    def _code_stats(self, code: str, language: str) -> Dict[str, Any]:
        """Kod istatistikleri"""
        lines = code.split('\n')
        patterns = self.LANGUAGE_PATTERNS.get(language, self.LANGUAGE_PATTERNS["python"])
        
        # Satır sayımları
        total_lines = len(lines)
        blank_lines = sum(1 for line in lines if not line.strip())
        comment_lines = sum(1 for line in lines if line.strip().startswith(patterns["comment"]))
        code_lines = total_lines - blank_lines - comment_lines
        
        # Fonksiyon ve class sayımları
        functions = re.findall(patterns["function"], code, re.MULTILINE)
        classes = re.findall(patterns["class"], code, re.MULTILINE)
        imports = re.findall(patterns["import"], code, re.MULTILINE)
        
        return {
            "language": language,
            "total_lines": total_lines,
            "code_lines": code_lines,
            "blank_lines": blank_lines,
            "comment_lines": comment_lines,
            "comment_ratio": round(comment_lines / max(code_lines, 1), 2),
            "function_count": len(functions) if isinstance(functions[0] if functions else "", str) else sum(len([f for f in func if f]) for func in functions),
            "class_count": len(classes),
            "import_count": len(imports),
        }
    
    def _complexity_analysis(self, code: str, language: str) -> Dict[str, Any]:
        """Cyclomatic complexity analizi"""
        # Basit complexity hesaplama (branching sayısı)
        complexity_keywords = {
            "python": ['if', 'elif', 'else', 'for', 'while', 'try', 'except', 'with', 'and', 'or'],
            "javascript": ['if', 'else', 'for', 'while', 'switch', 'case', 'try', 'catch', '&&', '||', '?'],
            "typescript": ['if', 'else', 'for', 'while', 'switch', 'case', 'try', 'catch', '&&', '||', '?'],
        }
        
        keywords = complexity_keywords.get(language, complexity_keywords["python"])
        
        complexity = 1  # Base complexity
        for keyword in keywords:
            complexity += len(re.findall(rf'\b{re.escape(keyword)}\b', code))
        
        # Nesting depth
        max_depth = 0
        current_depth = 0
        for char in code:
            if char in '{(':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char in '})':
                current_depth = max(0, current_depth - 1)
        
        # Python için indentation-based depth
        if language == "python":
            max_depth = 0
            for line in code.split('\n'):
                if line.strip():
                    indent = len(line) - len(line.lstrip())
                    depth = indent // 4
                    max_depth = max(max_depth, depth)
        
        # Complexity rating
        if complexity <= 5:
            rating = "low"
        elif complexity <= 10:
            rating = "moderate"
        elif complexity <= 20:
            rating = "high"
        else:
            rating = "very_high"
        
        return {
            "cyclomatic_complexity": complexity,
            "max_nesting_depth": max_depth,
            "rating": rating,
            "recommendation": self._get_complexity_recommendation(complexity, max_depth),
        }
    
    def _get_complexity_recommendation(self, complexity: int, depth: int) -> str:
        """Complexity için öneri"""
        recommendations = []
        
        if complexity > 10:
            recommendations.append("Fonksiyonu daha küçük parçalara bölmeyi düşünün")
        if depth > 4:
            recommendations.append("Derin iç içe yapıları azaltmak için early return kullanın")
        if complexity > 20:
            recommendations.append("Bu kod bloğu refactoring gerektiriyor")
        
        return "; ".join(recommendations) if recommendations else "Kod complexity uygun seviyede"
    
    def _security_scan(self, code: str, language: str) -> Dict[str, Any]:
        """Güvenlik taraması"""
        issues = []
        
        # Common security patterns
        security_patterns = {
            "hardcoded_secret": (
                r'(?:password|secret|api_key|token|key)\s*=\s*["\'][^"\']+["\']',
                "Hardcoded secret detected"
            ),
            "sql_injection": (
                r'(?:execute|query)\s*\([^)]*%s|\.format\s*\(',
                "Potential SQL injection vulnerability"
            ),
            "eval_usage": (
                r'\beval\s*\(',
                "Dangerous eval() usage"
            ),
            "exec_usage": (
                r'\bexec\s*\(',
                "Dangerous exec() usage"
            ),
            "shell_injection": (
                r'(?:os\.system|subprocess\.call|subprocess\.run)\s*\([^)]*\+',
                "Potential shell injection"
            ),
            "debug_code": (
                r'(?:print\s*\(|console\.log|debugger)',
                "Debug code found"
            ),
        }
        
        for issue_name, (pattern, message) in security_patterns.items():
            matches = re.findall(pattern, code, re.IGNORECASE)
            if matches:
                issues.append({
                    "type": issue_name,
                    "message": message,
                    "count": len(matches),
                    "severity": "high" if issue_name in ["sql_injection", "eval_usage", "shell_injection"] else "medium",
                })
        
        return {
            "issues": issues,
            "issue_count": len(issues),
            "high_severity_count": sum(1 for i in issues if i["severity"] == "high"),
            "security_score": max(0, 100 - len(issues) * 10),
        }
    
    def _quality_score(self, code: str, language: str) -> Dict[str, Any]:
        """Kod kalite skoru"""
        stats = self._code_stats(code, language)
        complexity = self._complexity_analysis(code, language)
        security = self._security_scan(code, language)
        
        # Scoring (100 max)
        score = 100
        
        # Comment ratio penalty/bonus
        if stats["comment_ratio"] < 0.1:
            score -= 10  # Yetersiz yorum
        elif stats["comment_ratio"] > 0.3:
            score += 5  # İyi dokümantasyon
        
        # Complexity penalty
        if complexity["cyclomatic_complexity"] > 10:
            score -= (complexity["cyclomatic_complexity"] - 10) * 2
        
        # Nesting penalty
        if complexity["max_nesting_depth"] > 3:
            score -= (complexity["max_nesting_depth"] - 3) * 5
        
        # Security penalty
        score -= security["high_severity_count"] * 15
        score -= (security["issue_count"] - security["high_severity_count"]) * 5
        
        # Line length penalty
        long_lines = sum(1 for line in code.split('\n') if len(line) > 100)
        score -= long_lines * 2
        
        score = max(0, min(100, score))
        
        # Grade
        if score >= 90:
            grade = "A"
        elif score >= 80:
            grade = "B"
        elif score >= 70:
            grade = "C"
        elif score >= 60:
            grade = "D"
        else:
            grade = "F"
        
        return {
            "score": score,
            "grade": grade,
            "breakdown": {
                "documentation": "good" if stats["comment_ratio"] >= 0.1 else "needs_improvement",
                "complexity": complexity["rating"],
                "security": "good" if security["issue_count"] == 0 else "needs_review",
            },
        }
