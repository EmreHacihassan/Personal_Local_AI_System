"""
Weakness Detection Package

Otomatik zayıflık tespiti ve adaptif içerik sistemi.
"""

from .weakness_detector import (
    WeaknessDetector,
    WeaknessType,
    WeaknessSignal,
    WeaknessCluster,
    AdaptiveContent,
    TrendDirection,
    weakness_detector
)

__all__ = [
    "WeaknessDetector",
    "WeaknessType",
    "WeaknessSignal",
    "WeaknessCluster",
    "AdaptiveContent",
    "TrendDirection",
    "weakness_detector"
]
