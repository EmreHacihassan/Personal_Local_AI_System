"""
📜 Certificate System
Öğrenme Yolculuğu Sertifika Sistemi

Bu modül:
1. Yolculuk tamamlandığında sertifika oluşturur
2. Benzersiz doğrulama kodu üretir
3. PDF/görsel sertifika oluşturur
4. Sosyal medya paylaşım linkleri sağlar
5. Sertifika doğrulama endpoint'i sunar
"""

import asyncio
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from .models import (
    Certificate, CurriculumPlan, Stage, UserProgress,
    DifficultyLevel
)


# ==================== CERTIFICATE TEMPLATES ====================

CERTIFICATE_TEMPLATES = {
    "mathematics": {
        "title": "Matematik Başarı Sertifikası",
        "icon": "📐",
        "background_color": "#1E40AF",
        "accent_color": "#3B82F6",
        "pattern": "geometric"
    },
    "physics": {
        "title": "Fizik Başarı Sertifikası",
        "icon": "⚛️",
        "background_color": "#7C3AED",
        "accent_color": "#A855F7",
        "pattern": "wave"
    },
    "chemistry": {
        "title": "Kimya Başarı Sertifikası",
        "icon": "🧪",
        "background_color": "#059669",
        "accent_color": "#10B981",
        "pattern": "molecules"
    },
    "biology": {
        "title": "Biyoloji Başarı Sertifikası",
        "icon": "🧬",
        "background_color": "#22C55E",
        "accent_color": "#4ADE80",
        "pattern": "organic"
    },
    "programming": {
        "title": "Programlama Başarı Sertifikası",
        "icon": "💻",
        "background_color": "#EA580C",
        "accent_color": "#F97316",
        "pattern": "code"
    },
    "default": {
        "title": "Öğrenme Başarı Sertifikası",
        "icon": "🎓",
        "background_color": "#6366F1",
        "accent_color": "#818CF8",
        "pattern": "stars"
    }
}

BADGE_LEVELS = [
    {"name": "Bronz", "min_score": 60, "color": "#CD7F32", "icon": "🥉"},
    {"name": "Gümüş", "min_score": 75, "color": "#C0C0C0", "icon": "🥈"},
    {"name": "Altın", "min_score": 90, "color": "#FFD700", "icon": "🥇"},
    {"name": "Platin", "min_score": 95, "color": "#E5E4E2", "icon": "💎"},
    {"name": "Elmas", "min_score": 99, "color": "#B9F2FF", "icon": "💠"}
]


# ==================== CERTIFICATE GENERATOR ====================

class CertificateGenerator:
    """
    Sertifika Oluşturucu
    
    Features:
    - Benzersiz doğrulama kodu
    - QR kod oluşturma (doğrulama için)
    - PDF sertifika
    - Sosyal medya paylaşım
    - Blockchain kaydı (opsiyonel)
    """
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.certificates_db: Dict[str, Certificate] = {}
    
    def generate_verification_code(
        self,
        user_id: str,
        journey_id: str,
        completion_date: str
    ) -> str:
        """Benzersiz doğrulama kodu oluştur"""
        
        # Hash oluştur
        data = f"{user_id}:{journey_id}:{completion_date}:{datetime.now().isoformat()}"
        hash_obj = hashlib.sha256(data.encode())
        full_hash = hash_obj.hexdigest()
        
        # Okunabilir formata çevir: XXXX-XXXX-XXXX
        code = f"{full_hash[:4].upper()}-{full_hash[4:8].upper()}-{full_hash[8:12].upper()}"
        
        return code
    
    def calculate_badge_level(self, average_score: float) -> Dict[str, Any]:
        """Başarı rozeti seviyesi hesapla"""
        
        badge = BADGE_LEVELS[0]  # Bronz default
        
        for level in BADGE_LEVELS:
            if average_score >= level["min_score"]:
                badge = level
        
        return badge
    
    async def create_certificate(
        self,
        plan: CurriculumPlan,
        user_progress: UserProgress,
        user_name: str,
        user_id: str
    ) -> Certificate:
        """Sertifika oluştur"""
        
        # Template seç
        subject_key = plan.goal.subject.lower()
        template = CERTIFICATE_TEMPLATES.get(subject_key, CERTIFICATE_TEMPLATES["default"])
        
        # Ortalama puan hesapla
        all_scores = []
        for stage_id, stage_progress in user_progress.stage_progress.items():
            for package_id, package_progress in stage_progress.items():
                if "exam_scores" in package_progress:
                    all_scores.extend(package_progress["exam_scores"].values())
        
        average_score = sum(all_scores) / len(all_scores) if all_scores else 70
        
        # Rozet seviyesi
        badge = self.calculate_badge_level(average_score)
        
        # Doğrulama kodu
        completion_date = datetime.now().isoformat()
        verification_code = self.generate_verification_code(
            user_id, plan.id, completion_date
        )
        
        # Kazanılan yetenekler
        skills_acquired = []
        for stage in plan.stages:
            skills_acquired.append(stage.main_topic)
            skills_acquired.extend(stage.covered_topics[:3])
        skills_acquired = list(set(skills_acquired))[:10]  # Max 10 yetenek
        
        # Toplam süre
        total_hours = user_progress.total_time_spent / 3600  # saniyeden saate
        
        # Sertifika oluştur
        certificate = Certificate(
            journey_id=plan.id,
            user_id=user_id,
            user_name=user_name,
            journey_title=plan.title,
            subject=plan.goal.subject,
            completion_date=completion_date,
            verification_code=verification_code,
            total_xp_earned=user_progress.xp_earned,
            total_hours_spent=round(total_hours, 1),
            stages_completed=user_progress.completed_stages,
            packages_completed=user_progress.completed_packages,
            exams_passed=len(all_scores),
            average_exam_score=round(average_score, 1),
            badge_level=badge["name"],
            skills_acquired=skills_acquired
        )
        
        # Görsel metadata
        certificate.visual_metadata = {
            "template": template,
            "badge": badge,
            "certificate_id": certificate.id,
            "qr_data": f"{self.base_url}/api/certificates/verify/{verification_code}"
        }
        
        # Paylaşım linkleri
        share_text = f"🎓 {plan.goal.subject} yolculuğumu tamamladım! {badge['icon']} {badge['name']} rozeti kazandım. Sertifikamı doğrula: {self.base_url}/certificates/{verification_code}"
        
        certificate.share_links = {
            "twitter": f"https://twitter.com/intent/tweet?text={share_text}",
            "linkedin": f"https://www.linkedin.com/sharing/share-offsite/?url={self.base_url}/certificates/{verification_code}",
            "facebook": f"https://www.facebook.com/sharer/sharer.php?u={self.base_url}/certificates/{verification_code}",
            "whatsapp": f"https://wa.me/?text={share_text}"
        }
        
        # Veritabanına kaydet
        self.certificates_db[verification_code] = certificate
        
        return certificate
    
    def verify_certificate(self, verification_code: str) -> Optional[Dict[str, Any]]:
        """Sertifika doğrula"""
        
        certificate = self.certificates_db.get(verification_code)
        
        if certificate:
            return {
                "valid": True,
                "certificate": certificate.to_dict(),
                "verified_at": datetime.now().isoformat()
            }
        else:
            return {
                "valid": False,
                "message": "Sertifika bulunamadı veya geçersiz kod."
            }
    
    def generate_certificate_html(self, certificate: Certificate) -> str:
        """HTML sertifika oluştur (PDF dönüşümü için)"""
        
        metadata = certificate.visual_metadata or {}
        template = metadata.get("template", CERTIFICATE_TEMPLATES["default"])
        badge = metadata.get("badge", BADGE_LEVELS[0])
        
        html = f"""
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;600&display=swap');
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, {template['background_color']} 0%, {template['accent_color']} 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }}
        
        .certificate {{
            background: white;
            width: 800px;
            padding: 60px;
            border-radius: 20px;
            box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25);
            position: relative;
            overflow: hidden;
        }}
        
        .certificate::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 8px;
            background: linear-gradient(90deg, {template['background_color']}, {template['accent_color']}, {template['background_color']});
        }}
        
        .icon {{
            font-size: 64px;
            text-align: center;
            margin-bottom: 20px;
        }}
        
        .title {{
            font-family: 'Playfair Display', serif;
            font-size: 36px;
            color: {template['background_color']};
            text-align: center;
            margin-bottom: 10px;
        }}
        
        .subtitle {{
            font-size: 16px;
            color: #6B7280;
            text-align: center;
            margin-bottom: 40px;
        }}
        
        .recipient {{
            font-family: 'Playfair Display', serif;
            font-size: 32px;
            color: #1F2937;
            text-align: center;
            margin-bottom: 10px;
        }}
        
        .journey {{
            font-size: 18px;
            color: #4B5563;
            text-align: center;
            margin-bottom: 40px;
        }}
        
        .stats {{
            display: flex;
            justify-content: center;
            gap: 40px;
            margin-bottom: 40px;
        }}
        
        .stat {{
            text-align: center;
        }}
        
        .stat-value {{
            font-size: 28px;
            font-weight: 600;
            color: {template['background_color']};
        }}
        
        .stat-label {{
            font-size: 12px;
            color: #9CA3AF;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .badge {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 10px;
            margin-bottom: 40px;
        }}
        
        .badge-icon {{
            font-size: 48px;
        }}
        
        .badge-name {{
            font-size: 24px;
            font-weight: 600;
            color: {badge['color']};
        }}
        
        .skills {{
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 10px;
            margin-bottom: 40px;
        }}
        
        .skill {{
            background: {template['accent_color']}20;
            color: {template['background_color']};
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
        }}
        
        .footer {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-top: 20px;
            border-top: 1px solid #E5E7EB;
        }}
        
        .date {{
            font-size: 14px;
            color: #9CA3AF;
        }}
        
        .verification {{
            font-family: monospace;
            font-size: 14px;
            color: #6B7280;
            background: #F3F4F6;
            padding: 8px 16px;
            border-radius: 8px;
        }}
    </style>
</head>
<body>
    <div class="certificate">
        <div class="icon">{template['icon']}</div>
        <h1 class="title">{template['title']}</h1>
        <p class="subtitle">Bu sertifika aşağıdaki kişinin başarıyla tamamladığını onaylar</p>
        
        <h2 class="recipient">{certificate.user_name}</h2>
        <p class="journey">{certificate.journey_title}</p>
        
        <div class="stats">
            <div class="stat">
                <div class="stat-value">{certificate.stages_completed}</div>
                <div class="stat-label">Aşama</div>
            </div>
            <div class="stat">
                <div class="stat-value">{certificate.packages_completed}</div>
                <div class="stat-label">Paket</div>
            </div>
            <div class="stat">
                <div class="stat-value">{certificate.total_hours_spent:.1f}</div>
                <div class="stat-label">Saat</div>
            </div>
            <div class="stat">
                <div class="stat-value">{certificate.total_xp_earned}</div>
                <div class="stat-label">XP</div>
            </div>
        </div>
        
        <div class="badge">
            <span class="badge-icon">{badge['icon']}</span>
            <span class="badge-name">{badge['name']} Seviyesi</span>
        </div>
        
        <div class="skills">
            {''.join(f'<span class="skill">{skill}</span>' for skill in certificate.skills_acquired[:6])}
        </div>
        
        <div class="footer">
            <span class="date">Tarih: {certificate.completion_date[:10]}</span>
            <span class="verification">Doğrulama: {certificate.verification_code}</span>
        </div>
    </div>
</body>
</html>
"""
        return html
    
    async def generate_pdf(self, certificate: Certificate) -> bytes:
        """PDF sertifika oluştur (placeholder - gerçek uygulamada wkhtmltopdf veya puppeteer kullanılır)"""
        
        html = self.generate_certificate_html(certificate)
        
        # Bu kısım gerçek uygulamada:
        # - wkhtmltopdf
        # - puppeteer/playwright
        # - WeasyPrint
        # gibi kütüphanelerle PDF'e dönüştürülür
        
        return html.encode('utf-8')  # Şimdilik HTML döndür


# ==================== CERTIFICATE STATISTICS ====================

@dataclass
class CertificateStats:
    """Sertifika istatistikleri"""
    total_certificates: int = 0
    by_badge_level: Dict[str, int] = field(default_factory=dict)
    by_subject: Dict[str, int] = field(default_factory=dict)
    average_completion_time: float = 0.0
    average_score: float = 0.0
    top_skills: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_certificates": self.total_certificates,
            "by_badge_level": self.by_badge_level,
            "by_subject": self.by_subject,
            "average_completion_time": round(self.average_completion_time, 1),
            "average_score": round(self.average_score, 1),
            "top_skills": self.top_skills
        }


class CertificateAnalytics:
    """Sertifika analitiği"""
    
    def __init__(self, generator: CertificateGenerator):
        self.generator = generator
    
    def get_user_stats(self, user_id: str) -> CertificateStats:
        """Kullanıcının sertifika istatistikleri"""
        
        user_certs = [
            c for c in self.generator.certificates_db.values()
            if c.user_id == user_id
        ]
        
        if not user_certs:
            return CertificateStats()
        
        stats = CertificateStats(
            total_certificates=len(user_certs),
            by_badge_level={},
            by_subject={},
            average_completion_time=0,
            average_score=0,
            top_skills=[]
        )
        
        # Badge dağılımı
        for cert in user_certs:
            level = cert.badge_level
            stats.by_badge_level[level] = stats.by_badge_level.get(level, 0) + 1
            
            subject = cert.subject
            stats.by_subject[subject] = stats.by_subject.get(subject, 0) + 1
        
        # Ortalamalar
        stats.average_completion_time = sum(c.total_hours_spent for c in user_certs) / len(user_certs)
        stats.average_score = sum(c.average_exam_score for c in user_certs) / len(user_certs)
        
        # En çok kazanılan yetenekler
        all_skills = []
        for cert in user_certs:
            all_skills.extend(cert.skills_acquired)
        
        skill_counts = {}
        for skill in all_skills:
            skill_counts[skill] = skill_counts.get(skill, 0) + 1
        
        stats.top_skills = sorted(skill_counts.keys(), key=lambda x: skill_counts[x], reverse=True)[:10]
        
        return stats
    
    def get_leaderboard(self, subject: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Liderlik tablosu"""
        
        certs = list(self.generator.certificates_db.values())
        
        if subject:
            certs = [c for c in certs if c.subject.lower() == subject.lower()]
        
        # Kullanıcıya göre grupla ve en iyi skorları al
        user_best = {}
        for cert in certs:
            user_id = cert.user_id
            if user_id not in user_best or cert.average_exam_score > user_best[user_id].average_exam_score:
                user_best[user_id] = cert
        
        # Sırala
        sorted_certs = sorted(user_best.values(), key=lambda x: x.average_exam_score, reverse=True)
        
        leaderboard = []
        for i, cert in enumerate(sorted_certs[:limit]):
            leaderboard.append({
                "rank": i + 1,
                "user_name": cert.user_name,
                "score": cert.average_exam_score,
                "badge": cert.badge_level,
                "journey": cert.journey_title,
                "xp": cert.total_xp_earned
            })
        
        return leaderboard


# ==================== SINGLETON ====================

_certificate_generator: Optional[CertificateGenerator] = None

def get_certificate_generator() -> CertificateGenerator:
    global _certificate_generator
    if _certificate_generator is None:
        _certificate_generator = CertificateGenerator()
    return _certificate_generator

def get_certificate_analytics() -> CertificateAnalytics:
    return CertificateAnalytics(get_certificate_generator())
