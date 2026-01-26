"""
SVGChartGenerator - SVG Grafik Oluşturma Modülü
===============================================

Desteklenen Grafik Türleri:
1. Bar chart (Çubuk grafik)
2. Line chart (Çizgi grafik)
3. Pie chart (Pasta grafik)
4. Donut chart
5. Area chart (Alan grafik)
6. Scatter plot
7. Heatmap
8. Radar chart
"""

import math
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class ChartType(str, Enum):
    """Grafik türleri."""
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    DONUT = "donut"
    AREA = "area"
    SCATTER = "scatter"
    RADAR = "radar"
    HORIZONTAL_BAR = "horizontal_bar"


@dataclass
class DataSeries:
    """Veri serisi."""
    name: str
    values: List[float]
    color: Optional[str] = None


@dataclass
class ChartConfig:
    """Grafik konfigürasyonu."""
    width: int = 600
    height: int = 400
    margin_top: int = 40
    margin_right: int = 40
    margin_bottom: int = 60
    margin_left: int = 60
    
    # Renkler
    colors: List[str] = field(default_factory=lambda: [
        "#4C78A8", "#F58518", "#E45756", "#72B7B2",
        "#54A24B", "#EECA3B", "#B279A2", "#FF9DA6",
        "#9D755D", "#BAB0AC"
    ])
    
    # Stil
    background_color: str = "#FFFFFF"
    text_color: str = "#333333"
    grid_color: str = "#E0E0E0"
    font_family: str = "Arial, sans-serif"
    font_size: int = 12
    title_font_size: int = 16
    
    # Özellikler
    show_grid: bool = True
    show_legend: bool = True
    show_labels: bool = True
    animate: bool = False


@dataclass
class Chart:
    """SVG Grafik."""
    chart_type: ChartType
    svg_code: str
    width: int
    height: int
    title: Optional[str] = None
    
    def to_html(self) -> str:
        """HTML olarak döndür."""
        return f'<div class="chart-container">{self.svg_code}</div>'
    
    def to_file(self, filepath: str):
        """Dosyaya kaydet."""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.svg_code)


class SVGChartGenerator:
    """
    SVG Grafik Oluşturma Modülü
    
    Saf Python ile SVG grafikleri oluşturur.
    """
    
    def __init__(self, config: Optional[ChartConfig] = None):
        self.config = config or ChartConfig()
    
    def create_bar_chart(
        self,
        labels: List[str],
        series: List[DataSeries],
        title: Optional[str] = None
    ) -> Chart:
        """
        Çubuk grafik oluştur.
        
        Args:
            labels: X ekseni etiketleri
            series: Veri serileri
            title: Grafik başlığı
            
        Returns:
            SVG grafik
        """
        cfg = self.config
        chart_width = cfg.width - cfg.margin_left - cfg.margin_right
        chart_height = cfg.height - cfg.margin_top - cfg.margin_bottom
        
        # Maksimum değer
        all_values = [v for s in series for v in s.values]
        max_val = max(all_values) if all_values else 1
        
        # Çubuk genişliği
        n_groups = len(labels)
        n_series = len(series)
        group_width = chart_width / n_groups
        bar_width = (group_width * 0.8) / n_series
        
        svg_parts = [self._create_svg_header(cfg.width, cfg.height)]
        
        # Arka plan
        svg_parts.append(f'<rect width="{cfg.width}" height="{cfg.height}" fill="{cfg.background_color}"/>')
        
        # Grid
        if cfg.show_grid:
            svg_parts.append(self._create_y_grid(chart_width, chart_height, max_val))
        
        # Eksenler
        svg_parts.append(self._create_axes(chart_width, chart_height))
        
        # Çubuklar
        for si, s in enumerate(series):
            color = s.color or cfg.colors[si % len(cfg.colors)]
            
            for i, value in enumerate(s.values):
                x = cfg.margin_left + i * group_width + si * bar_width + (group_width - bar_width * n_series) / 2
                bar_height = (value / max_val) * chart_height
                y = cfg.margin_top + chart_height - bar_height
                
                svg_parts.append(
                    f'<rect x="{x}" y="{y}" width="{bar_width * 0.9}" '
                    f'height="{bar_height}" fill="{color}" rx="2"/>'
                )
                
                # Değer etiketi
                if cfg.show_labels:
                    svg_parts.append(
                        f'<text x="{x + bar_width * 0.45}" y="{y - 5}" '
                        f'text-anchor="middle" font-size="{cfg.font_size - 2}" '
                        f'fill="{cfg.text_color}">{value:.1f}</text>'
                    )
        
        # X ekseni etiketleri
        for i, label in enumerate(labels):
            x = cfg.margin_left + (i + 0.5) * group_width
            y = cfg.height - cfg.margin_bottom + 20
            svg_parts.append(
                f'<text x="{x}" y="{y}" text-anchor="middle" '
                f'font-size="{cfg.font_size}" fill="{cfg.text_color}">{label}</text>'
            )
        
        # Başlık
        if title:
            svg_parts.append(self._create_title(title))
        
        # Legend
        if cfg.show_legend and len(series) > 1:
            svg_parts.append(self._create_legend(series))
        
        svg_parts.append('</svg>')
        
        return Chart(
            chart_type=ChartType.BAR,
            svg_code='\n'.join(svg_parts),
            width=cfg.width,
            height=cfg.height,
            title=title
        )
    
    def create_line_chart(
        self,
        labels: List[str],
        series: List[DataSeries],
        title: Optional[str] = None,
        smooth: bool = False
    ) -> Chart:
        """Çizgi grafik oluştur."""
        cfg = self.config
        chart_width = cfg.width - cfg.margin_left - cfg.margin_right
        chart_height = cfg.height - cfg.margin_top - cfg.margin_bottom
        
        all_values = [v for s in series for v in s.values]
        max_val = max(all_values) if all_values else 1
        min_val = min(0, min(all_values)) if all_values else 0
        value_range = max_val - min_val
        
        svg_parts = [self._create_svg_header(cfg.width, cfg.height)]
        svg_parts.append(f'<rect width="{cfg.width}" height="{cfg.height}" fill="{cfg.background_color}"/>')
        
        if cfg.show_grid:
            svg_parts.append(self._create_y_grid(chart_width, chart_height, max_val))
        
        svg_parts.append(self._create_axes(chart_width, chart_height))
        
        for si, s in enumerate(series):
            color = s.color or cfg.colors[si % len(cfg.colors)]
            points = []
            
            for i, value in enumerate(s.values):
                x = cfg.margin_left + (i / (len(s.values) - 1)) * chart_width if len(s.values) > 1 else cfg.margin_left
                y = cfg.margin_top + chart_height - ((value - min_val) / value_range) * chart_height
                points.append((x, y))
            
            # Çizgi
            if smooth and len(points) > 2:
                path_d = self._create_smooth_path(points)
            else:
                path_d = "M " + " L ".join(f"{p[0]},{p[1]}" for p in points)
            
            svg_parts.append(
                f'<path d="{path_d}" fill="none" stroke="{color}" '
                f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
            )
            
            # Noktalar
            for x, y in points:
                svg_parts.append(
                    f'<circle cx="{x}" cy="{y}" r="4" fill="{color}"/>'
                )
        
        # X ekseni etiketleri
        step = max(1, len(labels) // 8)
        for i, label in enumerate(labels[::step]):
            actual_i = i * step
            x = cfg.margin_left + (actual_i / (len(labels) - 1)) * chart_width if len(labels) > 1 else cfg.margin_left
            y = cfg.height - cfg.margin_bottom + 20
            svg_parts.append(
                f'<text x="{x}" y="{y}" text-anchor="middle" '
                f'font-size="{cfg.font_size}" fill="{cfg.text_color}">{label}</text>'
            )
        
        if title:
            svg_parts.append(self._create_title(title))
        
        if cfg.show_legend and len(series) > 1:
            svg_parts.append(self._create_legend(series))
        
        svg_parts.append('</svg>')
        
        return Chart(
            chart_type=ChartType.LINE,
            svg_code='\n'.join(svg_parts),
            width=cfg.width,
            height=cfg.height,
            title=title
        )
    
    def create_pie_chart(
        self,
        labels: List[str],
        values: List[float],
        title: Optional[str] = None,
        donut: bool = False
    ) -> Chart:
        """Pasta grafik oluştur."""
        cfg = self.config
        
        center_x = cfg.width / 2
        center_y = cfg.height / 2 + (20 if title else 0)
        radius = min(cfg.width, cfg.height) / 2 - 60
        inner_radius = radius * 0.6 if donut else 0
        
        total = sum(values)
        if total == 0:
            total = 1
        
        svg_parts = [self._create_svg_header(cfg.width, cfg.height)]
        svg_parts.append(f'<rect width="{cfg.width}" height="{cfg.height}" fill="{cfg.background_color}"/>')
        
        start_angle = -90  # Saat 12'den başla
        
        for i, (label, value) in enumerate(zip(labels, values)):
            percentage = value / total
            angle = percentage * 360
            end_angle = start_angle + angle
            
            color = cfg.colors[i % len(cfg.colors)]
            
            # Arc path
            path = self._create_arc_path(
                center_x, center_y, radius, inner_radius,
                start_angle, end_angle
            )
            
            svg_parts.append(f'<path d="{path}" fill="{color}"/>')
            
            # Etiket
            if cfg.show_labels and percentage > 0.03:
                label_angle = math.radians(start_angle + angle / 2)
                label_radius = radius * (0.7 if not donut else 0.85)
                label_x = center_x + label_radius * math.cos(label_angle)
                label_y = center_y + label_radius * math.sin(label_angle)
                
                svg_parts.append(
                    f'<text x="{label_x}" y="{label_y}" text-anchor="middle" '
                    f'dominant-baseline="middle" font-size="{cfg.font_size}" '
                    f'fill="#FFFFFF" font-weight="bold">{percentage*100:.1f}%</text>'
                )
            
            start_angle = end_angle
        
        if title:
            svg_parts.append(self._create_title(title))
        
        # Legend
        if cfg.show_legend:
            legend_x = cfg.width - 150
            legend_y = 60
            
            svg_parts.append(f'<g transform="translate({legend_x}, {legend_y})">')
            for i, (label, value) in enumerate(zip(labels, values)):
                color = cfg.colors[i % len(cfg.colors)]
                y_offset = i * 20
                
                svg_parts.append(f'<rect x="0" y="{y_offset}" width="15" height="15" fill="{color}"/>')
                svg_parts.append(
                    f'<text x="20" y="{y_offset + 12}" font-size="{cfg.font_size - 1}" '
                    f'fill="{cfg.text_color}">{label[:15]}</text>'
                )
            svg_parts.append('</g>')
        
        svg_parts.append('</svg>')
        
        return Chart(
            chart_type=ChartType.DONUT if donut else ChartType.PIE,
            svg_code='\n'.join(svg_parts),
            width=cfg.width,
            height=cfg.height,
            title=title
        )
    
    def create_horizontal_bar_chart(
        self,
        labels: List[str],
        values: List[float],
        title: Optional[str] = None
    ) -> Chart:
        """Yatay çubuk grafik oluştur."""
        cfg = self.config
        chart_width = cfg.width - cfg.margin_left - cfg.margin_right - 100
        chart_height = cfg.height - cfg.margin_top - cfg.margin_bottom
        
        max_val = max(values) if values else 1
        bar_height = min(30, chart_height / len(labels) * 0.8)
        
        svg_parts = [self._create_svg_header(cfg.width, cfg.height)]
        svg_parts.append(f'<rect width="{cfg.width}" height="{cfg.height}" fill="{cfg.background_color}"/>')
        
        for i, (label, value) in enumerate(zip(labels, values)):
            color = cfg.colors[i % len(cfg.colors)]
            
            y = cfg.margin_top + i * (chart_height / len(labels)) + (chart_height / len(labels) - bar_height) / 2
            bar_width = (value / max_val) * chart_width
            
            # Etiket
            svg_parts.append(
                f'<text x="{cfg.margin_left - 5}" y="{y + bar_height / 2 + 4}" '
                f'text-anchor="end" font-size="{cfg.font_size}" '
                f'fill="{cfg.text_color}">{label[:20]}</text>'
            )
            
            # Çubuk
            svg_parts.append(
                f'<rect x="{cfg.margin_left}" y="{y}" width="{bar_width}" '
                f'height="{bar_height}" fill="{color}" rx="3"/>'
            )
            
            # Değer
            svg_parts.append(
                f'<text x="{cfg.margin_left + bar_width + 5}" y="{y + bar_height / 2 + 4}" '
                f'font-size="{cfg.font_size}" fill="{cfg.text_color}">{value:.1f}</text>'
            )
        
        if title:
            svg_parts.append(self._create_title(title))
        
        svg_parts.append('</svg>')
        
        return Chart(
            chart_type=ChartType.HORIZONTAL_BAR,
            svg_code='\n'.join(svg_parts),
            width=cfg.width,
            height=cfg.height,
            title=title
        )
    
    def _create_svg_header(self, width: int, height: int) -> str:
        """SVG başlığı."""
        return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
    
    def _create_axes(self, chart_width: float, chart_height: float) -> str:
        """Eksenler."""
        cfg = self.config
        return f'''<g class="axes">
    <line x1="{cfg.margin_left}" y1="{cfg.margin_top + chart_height}" 
          x2="{cfg.margin_left + chart_width}" y2="{cfg.margin_top + chart_height}" 
          stroke="{cfg.text_color}" stroke-width="1"/>
    <line x1="{cfg.margin_left}" y1="{cfg.margin_top}" 
          x2="{cfg.margin_left}" y2="{cfg.margin_top + chart_height}" 
          stroke="{cfg.text_color}" stroke-width="1"/>
</g>'''
    
    def _create_y_grid(self, chart_width: float, chart_height: float, max_val: float) -> str:
        """Y ekseni grid."""
        cfg = self.config
        lines = ['<g class="grid">']
        
        n_lines = 5
        for i in range(n_lines + 1):
            y = cfg.margin_top + (i / n_lines) * chart_height
            val = max_val * (1 - i / n_lines)
            
            lines.append(
                f'<line x1="{cfg.margin_left}" y1="{y}" '
                f'x2="{cfg.margin_left + chart_width}" y2="{y}" '
                f'stroke="{cfg.grid_color}" stroke-width="1" stroke-dasharray="3,3"/>'
            )
            
            lines.append(
                f'<text x="{cfg.margin_left - 5}" y="{y + 4}" '
                f'text-anchor="end" font-size="{cfg.font_size - 2}" '
                f'fill="{cfg.text_color}">{val:.0f}</text>'
            )
        
        lines.append('</g>')
        return '\n'.join(lines)
    
    def _create_title(self, title: str) -> str:
        """Başlık."""
        cfg = self.config
        return f'<text x="{cfg.width / 2}" y="{cfg.margin_top / 2}" text-anchor="middle" ' \
               f'font-size="{cfg.title_font_size}" font-weight="bold" ' \
               f'fill="{cfg.text_color}">{title}</text>'
    
    def _create_legend(self, series: List[DataSeries]) -> str:
        """Legend."""
        cfg = self.config
        parts = [f'<g class="legend" transform="translate({cfg.width - 120}, {cfg.margin_top})">']
        
        for i, s in enumerate(series):
            color = s.color or cfg.colors[i % len(cfg.colors)]
            y_offset = i * 20
            
            parts.append(f'<rect x="0" y="{y_offset}" width="15" height="15" fill="{color}"/>')
            parts.append(
                f'<text x="20" y="{y_offset + 12}" font-size="{cfg.font_size - 1}" '
                f'fill="{cfg.text_color}">{s.name[:15]}</text>'
            )
        
        parts.append('</g>')
        return '\n'.join(parts)
    
    def _create_arc_path(
        self,
        cx: float, cy: float,
        outer_r: float, inner_r: float,
        start_angle: float, end_angle: float
    ) -> str:
        """Arc path oluştur."""
        start_rad = math.radians(start_angle)
        end_rad = math.radians(end_angle)
        
        x1 = cx + outer_r * math.cos(start_rad)
        y1 = cy + outer_r * math.sin(start_rad)
        x2 = cx + outer_r * math.cos(end_rad)
        y2 = cy + outer_r * math.sin(end_rad)
        
        large_arc = 1 if (end_angle - start_angle) > 180 else 0
        
        if inner_r > 0:  # Donut
            x3 = cx + inner_r * math.cos(end_rad)
            y3 = cy + inner_r * math.sin(end_rad)
            x4 = cx + inner_r * math.cos(start_rad)
            y4 = cy + inner_r * math.sin(start_rad)
            
            return f"M {x1} {y1} A {outer_r} {outer_r} 0 {large_arc} 1 {x2} {y2} " \
                   f"L {x3} {y3} A {inner_r} {inner_r} 0 {large_arc} 0 {x4} {y4} Z"
        else:  # Pie
            return f"M {cx} {cy} L {x1} {y1} A {outer_r} {outer_r} 0 {large_arc} 1 {x2} {y2} Z"
    
    def _create_smooth_path(self, points: List[Tuple[float, float]]) -> str:
        """Smooth path (bezier)."""
        if len(points) < 2:
            return ""
        
        path = f"M {points[0][0]},{points[0][1]}"
        
        for i in range(1, len(points)):
            p0 = points[i - 1]
            p1 = points[i]
            
            cp1x = p0[0] + (p1[0] - p0[0]) * 0.5
            cp1y = p0[1]
            cp2x = p0[0] + (p1[0] - p0[0]) * 0.5
            cp2y = p1[1]
            
            path += f" C {cp1x},{cp1y} {cp2x},{cp2y} {p1[0]},{p1[1]}"
        
        return path
