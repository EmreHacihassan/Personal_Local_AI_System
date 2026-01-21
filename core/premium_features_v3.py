"""
Enterprise AI Assistant - Premium Features V3
==============================================

2 Yeni Premium Özellik:
9. 📝 Document Comparison & Diff
10. 🎨 Content Enhancement

Author: Enterprise AI Assistant
Version: 3.0.0
"""

import hashlib
import json
import re
import difflib
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from threading import Lock
from urllib.parse import urlparse
import statistics

from .logger import get_logger

logger = get_logger("premium_features_v3")


# =============================================================================
# 9. DOCUMENT COMPARISON & DIFF
# =============================================================================

@dataclass
class DiffConfig:
    """Diff yapılandırması."""
    context_lines: int = 3
    ignore_whitespace: bool = True
    ignore_case: bool = False
    semantic_threshold: float = 0.8
    show_line_numbers: bool = True


class DocumentComparator:
    """
    Döküman karşılaştırma ve diff sistemi.
    
    Özellikler:
    - Text diff (satır bazlı)
    - Semantic diff (anlam bazlı)
    - Word-level diff
    - Version comparison
    - Side-by-side visualization
    - Similarity scoring
    """
    
    def __init__(self, config: Optional[DiffConfig] = None):
        self.config = config or DiffConfig()
        self._cache: Dict[str, Any] = {}
        self._lock = Lock()
        logger.info("DocumentComparator initialized")
    
    def _normalize_text(self, text: str) -> str:
        """Metni normalize et."""
        if self.config.ignore_whitespace:
            text = re.sub(r'\s+', ' ', text)
        if self.config.ignore_case:
            text = text.lower()
        return text.strip()
    
    def _split_into_lines(self, text: str) -> List[str]:
        """Metni satırlara ayır."""
        return text.splitlines()
    
    def _split_into_words(self, text: str) -> List[str]:
        """Metni kelimelere ayır."""
        return re.findall(r'\b\w+\b', text)
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Metni cümlelere ayır."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def line_diff(
        self, 
        text1: str, 
        text2: str,
        label1: str = "Original",
        label2: str = "Modified"
    ) -> Dict[str, Any]:
        """
        Satır bazlı diff.
        
        Returns:
            {
                "unified_diff": str,
                "changes": List[Dict],
                "stats": Dict,
                "similarity": float
            }
        """
        lines1 = self._split_into_lines(text1)
        lines2 = self._split_into_lines(text2)
        
        # Unified diff
        diff = list(difflib.unified_diff(
            lines1, lines2,
            fromfile=label1,
            tofile=label2,
            lineterm='',
            n=self.config.context_lines
        ))
        
        # Detailed changes
        changes = []
        matcher = difflib.SequenceMatcher(None, lines1, lines2)
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                continue
            
            change = {
                "type": tag,
                "original_start": i1 + 1,
                "original_end": i2,
                "modified_start": j1 + 1,
                "modified_end": j2
            }
            
            if tag == 'replace':
                change["original_lines"] = lines1[i1:i2]
                change["modified_lines"] = lines2[j1:j2]
            elif tag == 'delete':
                change["deleted_lines"] = lines1[i1:i2]
            elif tag == 'insert':
                change["inserted_lines"] = lines2[j1:j2]
            
            changes.append(change)
        
        # Statistics
        added = sum(1 for c in changes if c["type"] == "insert")
        deleted = sum(1 for c in changes if c["type"] == "delete")
        modified = sum(1 for c in changes if c["type"] == "replace")
        
        # Similarity
        similarity = matcher.ratio()
        
        return {
            "unified_diff": "\n".join(diff),
            "changes": changes,
            "stats": {
                "original_lines": len(lines1),
                "modified_lines": len(lines2),
                "additions": added,
                "deletions": deleted,
                "modifications": modified,
                "total_changes": len(changes)
            },
            "similarity": round(similarity, 4)
        }
    
    def word_diff(self, text1: str, text2: str) -> Dict[str, Any]:
        """
        Kelime bazlı diff.
        
        Daha granüler karşılaştırma.
        """
        words1 = self._split_into_words(text1)
        words2 = self._split_into_words(text2)
        
        matcher = difflib.SequenceMatcher(None, words1, words2)
        
        result = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                result.append({
                    "type": "unchanged",
                    "text": " ".join(words1[i1:i2])
                })
            elif tag == 'replace':
                result.append({
                    "type": "replaced",
                    "original": " ".join(words1[i1:i2]),
                    "new": " ".join(words2[j1:j2])
                })
            elif tag == 'delete':
                result.append({
                    "type": "deleted",
                    "text": " ".join(words1[i1:i2])
                })
            elif tag == 'insert':
                result.append({
                    "type": "inserted",
                    "text": " ".join(words2[j1:j2])
                })
        
        # Word-level stats
        added_words = sum(
            len(r.get("text", "").split()) 
            for r in result if r["type"] == "inserted"
        )
        deleted_words = sum(
            len(r.get("text", "").split()) 
            for r in result if r["type"] == "deleted"
        )
        
        return {
            "changes": result,
            "stats": {
                "original_words": len(words1),
                "modified_words": len(words2),
                "added_words": added_words,
                "deleted_words": deleted_words
            },
            "similarity": round(matcher.ratio(), 4)
        }
    
    def semantic_diff(self, text1: str, text2: str) -> Dict[str, Any]:
        """
        Anlam bazlı diff.
        
        Cümle seviyesinde semantik karşılaştırma.
        """
        sentences1 = self._split_into_sentences(text1)
        sentences2 = self._split_into_sentences(text2)
        
        # Find matching sentences
        matches = []
        unmatched1 = set(range(len(sentences1)))
        unmatched2 = set(range(len(sentences2)))
        
        for i, s1 in enumerate(sentences1):
            best_match = -1
            best_score = 0
            
            for j in unmatched2:
                s2 = sentences2[j]
                score = difflib.SequenceMatcher(None, s1.lower(), s2.lower()).ratio()
                
                if score > best_score and score >= self.config.semantic_threshold:
                    best_score = score
                    best_match = j
            
            if best_match >= 0:
                matches.append({
                    "original_index": i,
                    "modified_index": best_match,
                    "original_sentence": sentences1[i],
                    "modified_sentence": sentences2[best_match],
                    "similarity": round(best_score, 4),
                    "is_modified": best_score < 1.0
                })
                unmatched1.discard(i)
                unmatched2.discard(best_match)
        
        # Unmatched sentences
        removed = [{"index": i, "sentence": sentences1[i]} for i in sorted(unmatched1)]
        added = [{"index": i, "sentence": sentences2[i]} for i in sorted(unmatched2)]
        
        # Overall semantic similarity
        if sentences1 and sentences2:
            avg_match_similarity = (
                sum(m["similarity"] for m in matches) / len(sentences1)
                if matches else 0
            )
        else:
            avg_match_similarity = 0
        
        return {
            "matched_sentences": matches,
            "removed_sentences": removed,
            "added_sentences": added,
            "stats": {
                "original_sentences": len(sentences1),
                "modified_sentences": len(sentences2),
                "matched": len(matches),
                "modified_in_place": sum(1 for m in matches if m["is_modified"]),
                "removed": len(removed),
                "added": len(added)
            },
            "semantic_similarity": round(avg_match_similarity, 4)
        }
    
    def version_diff(
        self, 
        versions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Birden fazla versiyon karşılaştırma.
        
        Args:
            versions: List of {"version": str, "content": str, "timestamp": str}
        
        Returns:
            Version comparison chain
        """
        if len(versions) < 2:
            return {"error": "At least 2 versions required"}
        
        # Sort by timestamp if available
        sorted_versions = sorted(
            versions,
            key=lambda v: v.get("timestamp", v.get("version", ""))
        )
        
        comparisons = []
        for i in range(len(sorted_versions) - 1):
            v1 = sorted_versions[i]
            v2 = sorted_versions[i + 1]
            
            diff = self.line_diff(
                v1["content"],
                v2["content"],
                f"v{v1.get('version', i)}",
                f"v{v2.get('version', i+1)}"
            )
            
            comparisons.append({
                "from_version": v1.get("version", str(i)),
                "to_version": v2.get("version", str(i + 1)),
                "from_timestamp": v1.get("timestamp"),
                "to_timestamp": v2.get("timestamp"),
                "changes": diff["stats"],
                "similarity": diff["similarity"]
            })
        
        # Calculate total evolution
        first_last_diff = self.line_diff(
            sorted_versions[0]["content"],
            sorted_versions[-1]["content"]
        )
        
        return {
            "version_count": len(versions),
            "comparisons": comparisons,
            "total_evolution": {
                "first_version": sorted_versions[0].get("version"),
                "last_version": sorted_versions[-1].get("version"),
                "overall_similarity": first_last_diff["similarity"],
                "total_changes": first_last_diff["stats"]["total_changes"]
            }
        }
    
    def side_by_side(
        self, 
        text1: str, 
        text2: str,
        label1: str = "Original",
        label2: str = "Modified"
    ) -> Dict[str, Any]:
        """
        Yan yana görselleştirme için export.
        
        HTML ve plain text formatında.
        """
        lines1 = self._split_into_lines(text1)
        lines2 = self._split_into_lines(text2)
        
        matcher = difflib.SequenceMatcher(None, lines1, lines2)
        
        side_by_side = []
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                for k in range(i2 - i1):
                    side_by_side.append({
                        "left_line": i1 + k + 1,
                        "left_text": lines1[i1 + k],
                        "right_line": j1 + k + 1,
                        "right_text": lines2[j1 + k],
                        "status": "unchanged"
                    })
            elif tag == 'replace':
                max_len = max(i2 - i1, j2 - j1)
                for k in range(max_len):
                    left_idx = i1 + k if k < i2 - i1 else None
                    right_idx = j1 + k if k < j2 - j1 else None
                    
                    side_by_side.append({
                        "left_line": left_idx + 1 if left_idx is not None else None,
                        "left_text": lines1[left_idx] if left_idx is not None else "",
                        "right_line": right_idx + 1 if right_idx is not None else None,
                        "right_text": lines2[right_idx] if right_idx is not None else "",
                        "status": "modified"
                    })
            elif tag == 'delete':
                for k in range(i2 - i1):
                    side_by_side.append({
                        "left_line": i1 + k + 1,
                        "left_text": lines1[i1 + k],
                        "right_line": None,
                        "right_text": "",
                        "status": "deleted"
                    })
            elif tag == 'insert':
                for k in range(j2 - j1):
                    side_by_side.append({
                        "left_line": None,
                        "left_text": "",
                        "right_line": j1 + k + 1,
                        "right_text": lines2[j1 + k],
                        "status": "inserted"
                    })
        
        # Generate HTML
        html = self._generate_diff_html(side_by_side, label1, label2)
        
        return {
            "rows": side_by_side,
            "html": html,
            "labels": {"left": label1, "right": label2}
        }
    
    def _generate_diff_html(
        self, 
        rows: List[Dict], 
        label1: str, 
        label2: str
    ) -> str:
        """Generate HTML diff visualization."""
        status_colors = {
            "unchanged": "#ffffff",
            "modified": "#fff3cd",
            "deleted": "#f8d7da",
            "inserted": "#d4edda"
        }
        
        html_rows = []
        for row in rows:
            color = status_colors.get(row["status"], "#ffffff")
            left_num = row["left_line"] or ""
            right_num = row["right_line"] or ""
            left_text = row["left_text"].replace("<", "&lt;").replace(">", "&gt;")
            right_text = row["right_text"].replace("<", "&lt;").replace(">", "&gt;")
            
            html_rows.append(
                f'<tr style="background-color:{color}">'
                f'<td style="width:30px;text-align:right;color:#999">{left_num}</td>'
                f'<td style="padding:2px 8px"><pre style="margin:0">{left_text}</pre></td>'
                f'<td style="width:30px;text-align:right;color:#999">{right_num}</td>'
                f'<td style="padding:2px 8px"><pre style="margin:0">{right_text}</pre></td>'
                f'</tr>'
            )
        
        return f'''
<table style="width:100%;border-collapse:collapse;font-family:monospace;font-size:12px">
<thead>
<tr style="background:#f0f0f0">
<th colspan="2" style="padding:8px;text-align:left">{label1}</th>
<th colspan="2" style="padding:8px;text-align:left">{label2}</th>
</tr>
</thead>
<tbody>
{"".join(html_rows)}
</tbody>
</table>
'''
    
    def similarity_score(self, text1: str, text2: str) -> Dict[str, Any]:
        """
        Çoklu benzerlik metrikleri.
        """
        # Normalize
        norm1 = self._normalize_text(text1)
        norm2 = self._normalize_text(text2)
        
        # Different similarity measures
        
        # 1. Character-level (SequenceMatcher)
        char_sim = difflib.SequenceMatcher(None, norm1, norm2).ratio()
        
        # 2. Word-level (Jaccard)
        words1 = set(self._split_into_words(norm1))
        words2 = set(self._split_into_words(norm2))
        
        if words1 or words2:
            jaccard = len(words1 & words2) / len(words1 | words2)
        else:
            jaccard = 1.0
        
        # 3. Line-level
        lines1 = self._split_into_lines(text1)
        lines2 = self._split_into_lines(text2)
        line_sim = difflib.SequenceMatcher(None, lines1, lines2).ratio()
        
        # 4. Cosine similarity (word frequency)
        freq1 = Counter(self._split_into_words(norm1))
        freq2 = Counter(self._split_into_words(norm2))
        
        all_words = set(freq1.keys()) | set(freq2.keys())
        if all_words:
            dot_product = sum(freq1.get(w, 0) * freq2.get(w, 0) for w in all_words)
            mag1 = sum(v**2 for v in freq1.values()) ** 0.5
            mag2 = sum(v**2 for v in freq2.values()) ** 0.5
            cosine = dot_product / (mag1 * mag2) if mag1 and mag2 else 0
        else:
            cosine = 1.0
        
        # Weighted average
        overall = (char_sim * 0.3 + jaccard * 0.25 + line_sim * 0.2 + cosine * 0.25)
        
        return {
            "character_similarity": round(char_sim, 4),
            "word_jaccard": round(jaccard, 4),
            "line_similarity": round(line_sim, 4),
            "cosine_similarity": round(cosine, 4),
            "overall_similarity": round(overall, 4),
            "is_similar": overall >= 0.8,
            "is_duplicate": overall >= 0.95
        }


# =============================================================================
# 10. CONTENT ENHANCEMENT
# =============================================================================

@dataclass
class EnhancementConfig:
    """Content enhancement yapılandırması."""
    fix_markdown: bool = True
    detect_code: bool = True
    extract_tables: bool = True
    validate_links: bool = True
    extract_images: bool = True
    auto_format: bool = True


class ContentEnhancer:
    """
    İçerik zenginleştirme ve format düzeltme sistemi.
    
    Özellikler:
    - Markdown format düzeltme
    - Code syntax detection
    - Table extraction
    - Link validation & enrichment
    - Image URL detection
    - Auto-formatting
    """
    
    # Code language detection patterns
    CODE_PATTERNS = {
        "python": [
            r'\bdef\s+\w+\s*\(', r'\bclass\s+\w+:', r'\bimport\s+\w+',
            r'\bfrom\s+\w+\s+import', r'print\s*\(', r'\bself\.',
            r'__init__', r'__name__', r'\.py\b'
        ],
        "javascript": [
            r'\bfunction\s+\w+\s*\(', r'\bconst\s+\w+\s*=', r'\blet\s+\w+\s*=',
            r'\bvar\s+\w+\s*=', r'=>', r'console\.log', r'require\s*\(',
            r'module\.exports', r'\.js\b', r'\basync\s+function'
        ],
        "typescript": [
            r':\s*(string|number|boolean|any)\b', r'\binterface\s+\w+',
            r'\btype\s+\w+\s*=', r'<\w+>', r'\.ts\b', r'\bas\s+\w+'
        ],
        "html": [
            r'<html', r'<head', r'<body', r'<div', r'<span', r'<script',
            r'<style', r'</\w+>', r'<!DOCTYPE', r'class="', r'id="'
        ],
        "css": [
            r'\{[^}]*:\s*[^}]+\}', r'@media', r'@keyframes', r'\.[\w-]+\s*\{',
            r'#[\w-]+\s*\{', r'px|em|rem|%|vh|vw', r'color:', r'background:'
        ],
        "sql": [
            r'\bSELECT\b', r'\bFROM\b', r'\bWHERE\b', r'\bINSERT\b',
            r'\bUPDATE\b', r'\bDELETE\b', r'\bCREATE TABLE\b', r'\bJOIN\b'
        ],
        "json": [
            r'^\s*\{', r'^\s*\[', r'"[\w]+"\s*:', r':\s*\[', r':\s*\{'
        ],
        "yaml": [
            r'^\w+:', r'^\s+-\s+', r'^\s+\w+:', r'---\s*$'
        ],
        "bash": [
            r'^#!/bin/bash', r'\becho\s+', r'\bif\s+\[', r'\bfor\s+\w+\s+in',
            r'\$\{?\w+\}?', r'\|\s*grep', r'\bsudo\s+'
        ],
        "markdown": [
            r'^#{1,6}\s+', r'\*\*\w+\*\*', r'\*\w+\*', r'```', r'\[.*\]\(.*\)'
        ]
    }
    
    # Link patterns
    LINK_PATTERN = re.compile(
        r'(https?://[^\s<>"\')\]]+)',
        re.IGNORECASE
    )
    
    # Image URL patterns
    IMAGE_PATTERN = re.compile(
        r'(https?://[^\s<>"\')\]]+\.(?:jpg|jpeg|png|gif|webp|svg|bmp|ico)(?:\?[^\s<>"\')\]]*)?)',
        re.IGNORECASE
    )
    
    # Email pattern
    EMAIL_PATTERN = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    )
    
    def __init__(self, config: Optional[EnhancementConfig] = None):
        self.config = config or EnhancementConfig()
        self._cache: Dict[str, Any] = {}
        self._lock = Lock()
        logger.info("ContentEnhancer initialized")
    
    def detect_code_language(self, code: str) -> Dict[str, Any]:
        """
        Kod dilini tespit et.
        
        Returns:
            {"language": str, "confidence": float, "all_matches": Dict}
        """
        scores = {}
        
        for language, patterns in self.CODE_PATTERNS.items():
            matches = 0
            for pattern in patterns:
                if re.search(pattern, code, re.IGNORECASE | re.MULTILINE):
                    matches += 1
            
            if matches > 0:
                scores[language] = matches / len(patterns)
        
        if not scores:
            return {
                "language": "unknown",
                "confidence": 0.0,
                "all_matches": {}
            }
        
        best_lang = max(scores, key=scores.get)
        
        return {
            "language": best_lang,
            "confidence": round(scores[best_lang], 3),
            "all_matches": {k: round(v, 3) for k, v in sorted(scores.items(), key=lambda x: -x[1])}
        }
    
    def fix_markdown(self, text: str) -> Dict[str, Any]:
        """
        Markdown formatını düzelt.
        """
        original = text
        fixed = text
        fixes = []
        
        # 1. Fix headers (ensure space after #)
        header_pattern = r'^(#{1,6})([^\s#])'
        if re.search(header_pattern, fixed, re.MULTILINE):
            fixed = re.sub(header_pattern, r'\1 \2', fixed, flags=re.MULTILINE)
            fixes.append("Added space after header markers")
        
        # 2. Fix list items (ensure space after - or *)
        list_pattern = r'^(\s*[-*])([^\s])'
        if re.search(list_pattern, fixed, re.MULTILINE):
            fixed = re.sub(list_pattern, r'\1 \2', fixed, flags=re.MULTILINE)
            fixes.append("Added space after list markers")
        
        # 3. Fix code blocks (ensure language tag)
        code_block_pattern = r'```\s*\n'
        if re.search(code_block_pattern, fixed):
            # Try to detect language for unmarked code blocks
            def add_language(match):
                code_start = match.end()
                code_end = fixed.find('```', code_start)
                if code_end > code_start:
                    code = fixed[code_start:code_end]
                    lang_result = self.detect_code_language(code)
                    if lang_result["confidence"] >= 0.3:
                        return f'```{lang_result["language"]}\n'
                return match.group(0)
            
            new_fixed = re.sub(code_block_pattern, add_language, fixed)
            if new_fixed != fixed:
                fixed = new_fixed
                fixes.append("Added language tags to code blocks")
        
        # 4. Fix bold/italic (close unclosed markers)
        # Count ** and * pairs
        bold_count = len(re.findall(r'\*\*', fixed))
        if bold_count % 2 != 0:
            fixes.append("Warning: Unclosed bold markers (**)")
        
        italic_singles = len(re.findall(r'(?<!\*)\*(?!\*)', fixed))
        if italic_singles % 2 != 0:
            fixes.append("Warning: Unclosed italic markers (*)")
        
        # 5. Fix links [text](url) - ensure no space between ] and (
        link_space_pattern = r'\]\s+\('
        if re.search(link_space_pattern, fixed):
            fixed = re.sub(link_space_pattern, '](', fixed)
            fixes.append("Removed spaces in link syntax")
        
        # 6. Ensure blank line before headers
        header_no_blank = r'([^\n])\n(#{1,6}\s)'
        if re.search(header_no_blank, fixed):
            fixed = re.sub(header_no_blank, r'\1\n\n\2', fixed)
            fixes.append("Added blank lines before headers")
        
        # 7. Fix table alignment (basic)
        table_row_pattern = r'^\|[^|]+(\|[^|]+)+\|?\s*$'
        table_rows = re.findall(table_row_pattern, fixed, re.MULTILINE)
        if table_rows and '|' in fixed:
            fixes.append("Table structure detected")
        
        return {
            "original": original,
            "fixed": fixed,
            "fixes_applied": fixes,
            "fix_count": len([f for f in fixes if not f.startswith("Warning")]),
            "warnings": [f for f in fixes if f.startswith("Warning")],
            "is_changed": original != fixed
        }
    
    def extract_tables(self, text: str) -> Dict[str, Any]:
        """
        Metinden tablo çıkar.
        
        Markdown ve metin tabloları destekler.
        """
        tables = []
        
        # 1. Markdown tables
        md_table_pattern = r'(\|[^\n]+\|\n)(\|[-:\|\s]+\|\n)((?:\|[^\n]+\|\n?)+)'
        
        for match in re.finditer(md_table_pattern, text):
            header_row = match.group(1)
            separator = match.group(2)
            body = match.group(3)
            
            # Parse header
            headers = [h.strip() for h in header_row.strip('|\n').split('|')]
            
            # Parse body rows
            rows = []
            for line in body.strip().split('\n'):
                if line.strip():
                    row = [cell.strip() for cell in line.strip('|').split('|')]
                    rows.append(row)
            
            tables.append({
                "type": "markdown",
                "headers": headers,
                "rows": rows,
                "row_count": len(rows),
                "column_count": len(headers),
                "position": match.start()
            })
        
        # 2. ASCII/text tables (simple detection)
        ascii_table_pattern = r'([+-]+\n)(\|[^\n]+\|\n)+([+-]+\n)'
        
        for match in re.finditer(ascii_table_pattern, text):
            table_text = match.group(0)
            lines = [l for l in table_text.split('\n') if '|' in l]
            
            rows = []
            for line in lines:
                row = [cell.strip() for cell in line.strip('|').split('|')]
                rows.append(row)
            
            if rows:
                tables.append({
                    "type": "ascii",
                    "headers": rows[0] if rows else [],
                    "rows": rows[1:] if len(rows) > 1 else [],
                    "row_count": len(rows) - 1,
                    "column_count": len(rows[0]) if rows else 0,
                    "position": match.start()
                })
        
        # 3. Tab-separated values detection
        lines = text.split('\n')
        tab_lines = [l for l in lines if '\t' in l and l.count('\t') >= 2]
        
        if len(tab_lines) >= 2:
            headers = tab_lines[0].split('\t')
            rows = [line.split('\t') for line in tab_lines[1:]]
            
            tables.append({
                "type": "tsv",
                "headers": headers,
                "rows": rows,
                "row_count": len(rows),
                "column_count": len(headers),
                "position": text.find(tab_lines[0])
            })
        
        return {
            "tables_found": len(tables),
            "tables": tables
        }
    
    def extract_links(self, text: str) -> Dict[str, Any]:
        """
        Linkleri çıkar ve zenginleştir.
        """
        links = []
        
        # Find all URLs
        for match in self.LINK_PATTERN.finditer(text):
            url = match.group(1)
            
            # Parse URL
            try:
                parsed = urlparse(url)
                
                # Determine type
                link_type = "webpage"
                if self.IMAGE_PATTERN.match(url):
                    link_type = "image"
                elif url.endswith('.pdf'):
                    link_type = "pdf"
                elif url.endswith(('.doc', '.docx')):
                    link_type = "document"
                elif url.endswith(('.mp4', '.avi', '.mov', '.webm')):
                    link_type = "video"
                elif url.endswith(('.mp3', '.wav', '.ogg')):
                    link_type = "audio"
                elif url.endswith(('.zip', '.tar', '.gz', '.rar')):
                    link_type = "archive"
                elif parsed.netloc in ['github.com', 'gitlab.com', 'bitbucket.org']:
                    link_type = "repository"
                elif parsed.netloc in ['youtube.com', 'youtu.be', 'vimeo.com']:
                    link_type = "video"
                
                links.append({
                    "url": url,
                    "type": link_type,
                    "domain": parsed.netloc,
                    "path": parsed.path,
                    "scheme": parsed.scheme,
                    "position": match.start(),
                    "is_secure": parsed.scheme == 'https'
                })
            except Exception:
                links.append({
                    "url": url,
                    "type": "unknown",
                    "position": match.start(),
                    "parse_error": True
                })
        
        # Find emails
        emails = []
        for match in self.EMAIL_PATTERN.finditer(text):
            emails.append({
                "email": match.group(0),
                "position": match.start()
            })
        
        # Link statistics
        link_types = Counter(l.get("type") for l in links)
        domains = Counter(l.get("domain") for l in links if l.get("domain"))
        
        return {
            "total_links": len(links),
            "links": links,
            "emails": emails,
            "link_types": dict(link_types),
            "top_domains": dict(domains.most_common(5)),
            "secure_links": sum(1 for l in links if l.get("is_secure")),
            "insecure_links": sum(1 for l in links if l.get("is_secure") == False)
        }
    
    def extract_images(self, text: str) -> Dict[str, Any]:
        """
        Image URL'lerini tespit et ve metadata çıkar.
        """
        images = []
        
        # Find image URLs
        for match in self.IMAGE_PATTERN.finditer(text):
            url = match.group(1)
            
            try:
                parsed = urlparse(url)
                path = parsed.path.lower()
                
                # Detect format
                if '.jpg' in path or '.jpeg' in path:
                    format_type = 'jpeg'
                elif '.png' in path:
                    format_type = 'png'
                elif '.gif' in path:
                    format_type = 'gif'
                elif '.webp' in path:
                    format_type = 'webp'
                elif '.svg' in path:
                    format_type = 'svg'
                elif '.bmp' in path:
                    format_type = 'bmp'
                else:
                    format_type = 'unknown'
                
                # Extract filename
                filename = parsed.path.split('/')[-1].split('?')[0]
                
                images.append({
                    "url": url,
                    "format": format_type,
                    "filename": filename,
                    "domain": parsed.netloc,
                    "position": match.start(),
                    "is_secure": parsed.scheme == 'https'
                })
            except Exception:
                images.append({
                    "url": url,
                    "format": "unknown",
                    "position": match.start(),
                    "parse_error": True
                })
        
        # Also find markdown image syntax
        md_images = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', text)
        
        for alt_text, url in md_images:
            # Check if already found
            if not any(img["url"] == url for img in images):
                images.append({
                    "url": url,
                    "alt_text": alt_text,
                    "format": "unknown",
                    "position": text.find(f'![{alt_text}]'),
                    "syntax": "markdown"
                })
        
        # Format statistics
        formats = Counter(img.get("format") for img in images)
        
        return {
            "total_images": len(images),
            "images": images,
            "formats": dict(formats)
        }
    
    def enhance_content(self, text: str) -> Dict[str, Any]:
        """
        Ana enhancement fonksiyonu - tüm özellikleri uygula.
        """
        result = {
            "original_length": len(text),
            "enhancements": []
        }
        
        enhanced_text = text
        
        # 1. Fix markdown
        if self.config.fix_markdown:
            md_result = self.fix_markdown(enhanced_text)
            if md_result["is_changed"]:
                enhanced_text = md_result["fixed"]
                result["markdown_fixes"] = md_result["fixes_applied"]
                result["enhancements"].append("markdown_fixed")
        
        # 2. Extract & tag code blocks
        if self.config.detect_code:
            code_blocks = re.findall(r'```(\w*)\n(.*?)```', enhanced_text, re.DOTALL)
            code_analysis = []
            
            for lang, code in code_blocks:
                if not lang:  # No language specified
                    detected = self.detect_code_language(code)
                    if detected["confidence"] >= 0.3:
                        code_analysis.append({
                            "detected_language": detected["language"],
                            "confidence": detected["confidence"]
                        })
            
            if code_analysis:
                result["code_analysis"] = code_analysis
                result["enhancements"].append("code_detected")
        
        # 3. Extract tables
        if self.config.extract_tables:
            tables = self.extract_tables(text)
            if tables["tables_found"] > 0:
                result["tables"] = tables
                result["enhancements"].append("tables_extracted")
        
        # 4. Extract and validate links
        if self.config.validate_links:
            links = self.extract_links(text)
            if links["total_links"] > 0:
                result["links"] = links
                result["enhancements"].append("links_extracted")
        
        # 5. Extract images
        if self.config.extract_images:
            images = self.extract_images(text)
            if images["total_images"] > 0:
                result["images"] = images
                result["enhancements"].append("images_extracted")
        
        result["enhanced_text"] = enhanced_text
        result["enhanced_length"] = len(enhanced_text)
        result["enhancement_count"] = len(result["enhancements"])
        
        return result
    
    def auto_format(self, text: str) -> Dict[str, Any]:
        """
        Otomatik format düzeltme.
        """
        formatted = text
        changes = []
        
        # 1. Normalize line endings
        if '\r\n' in formatted:
            formatted = formatted.replace('\r\n', '\n')
            changes.append("Normalized line endings")
        
        # 2. Remove trailing whitespace
        lines = formatted.split('\n')
        stripped_lines = [line.rstrip() for line in lines]
        if lines != stripped_lines:
            formatted = '\n'.join(stripped_lines)
            changes.append("Removed trailing whitespace")
        
        # 3. Ensure single newline at end
        if formatted and not formatted.endswith('\n'):
            formatted += '\n'
            changes.append("Added final newline")
        
        # 4. Remove multiple blank lines (keep max 2)
        while '\n\n\n\n' in formatted:
            formatted = formatted.replace('\n\n\n\n', '\n\n\n')
            if "Reduced excessive blank lines" not in changes:
                changes.append("Reduced excessive blank lines")
        
        # 5. Fix common spacing issues
        # Double spaces
        if '  ' in formatted and '```' not in formatted:  # Don't fix code blocks
            formatted = re.sub(r'(?<!^)  +', ' ', formatted)
            changes.append("Fixed double spaces")
        
        return {
            "original": text,
            "formatted": formatted,
            "changes": changes,
            "change_count": len(changes)
        }


# =============================================================================
# EXPORT ALL NEW FEATURES
# =============================================================================

__all__ = [
    "DocumentComparator",
    "DiffConfig",
    "ContentEnhancer",
    "EnhancementConfig",
]
