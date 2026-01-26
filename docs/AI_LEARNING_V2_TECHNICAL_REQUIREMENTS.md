# 🔬 AI ile Öğren V2 - Teknik Gereksinimler

> **Versiyon:** 2.0  
> **Son Güncelleme:** 23 Ocak 2026  
> **Amaç:** Premium Test Protokolü için Teknik Referans

---

## 📋 İçindekiler

1. [Backend Mimarisi](#1-backend-mimarisi)
2. [API Spesifikasyonları](#2-api-spesifikasyonları)
3. [Data Model Detayları](#3-data-model-detayları)
4. [Frontend Mimarisi](#4-frontend-mimarisi)
5. [Sınav Değerlendirme Sistemi](#5-sınav-değerlendirme-sistemi)
6. [WebSocket Protokolü](#6-websocket-protokolü)
7. [Error Handling](#7-error-handling)
8. [Test Gereksinimleri](#8-test-gereksinimleri)

---

## 1. Backend Mimarisi

### 1.1 Modül Yapısı

```
core/learning_journey_v2/
├── __init__.py              # Exports
├── models.py                # Data classes & enums
├── curriculum_planner.py    # AI müfredat planlama
├── content_generator.py     # İçerik üretimi
├── exam_system.py           # Sınav değerlendirme
├── certificate_system.py    # Sertifika yönetimi
└── orchestrator.py          # Ana koordinatör
```

### 1.2 Singleton Instances

```python
# Beklenen singleton'lar
_orchestrator_instance: Optional[LearningJourneyOrchestrator] = None
_exam_system_instance: Optional[ExamSystem] = None
_certificate_generator_instance: Optional[CertificateGenerator] = None
_curriculum_planner_instance: Optional[CurriculumPlannerAgent] = None
_content_generator_instance: Optional[ContentGeneratorAgent] = None
```

### 1.3 Import Chain

```python
# __init__.py'de export edilmesi gerekenler
from .models import (
    LearningGoal, CurriculumPlan, Stage, Package, Exam, Exercise,
    Certificate, UserProgress, ContentBlock, ExamQuestion,
    DifficultyLevel, ContentType, ExamType, ExerciseType,
    PackageType, StageStatus, PackageStatus
)

from .curriculum_planner import (
    CurriculumPlannerAgent, AgentThought, get_curriculum_planner
)

from .content_generator import (
    ContentGeneratorAgent, RAGContentEnhancer, get_content_generator
)

from .exam_system import (
    ExamSystem, ExamResult, FeynmanExamEvaluator,
    MultipleChoiceEvaluator, ProblemSolvingEvaluator,
    TeachBackEvaluator, ConceptMapEvaluator, get_exam_system
)

from .certificate_system import (
    CertificateGenerator, CertificateAnalytics, CertificateStats,
    get_certificate_generator, get_certificate_analytics
)

from .orchestrator import (
    LearningJourneyOrchestrator, OrchestrationEvent, EventType,
    JourneyState, get_learning_orchestrator, stream_journey_creation
)
```

---

## 2. API Spesifikasyonları

### 2.1 Endpoint Detayları

#### POST /journey/v2/create

**Request:**
```json
{
  "title": "AYT Matematik Hazırlığı",
  "subject": "Matematik",
  "target_outcome": "AYT'de 35+ net yapmak",
  "motivation": "Tıp fakültesi kazanmak",
  "prior_knowledge": "Temel seviye",
  "weak_areas": ["Türev", "İntegral"],
  "focus_areas": ["Limit", "Türev Uygulamaları"],
  "daily_hours": 2.0,
  "deadline": "2026-06-15",
  "content_preferences": ["text", "video"],
  "exam_preferences": ["multiple_choice", "feynman"]
}
```

**Response:**
```json
{
  "journey_id": "abc12345",
  "status": "created",
  "plan": {
    "total_stages": 12,
    "total_packages": 130,
    "total_exams": 98,
    "total_exercises": 158,
    "estimated_total_hours": 88.5,
    "total_xp_possible": 12500
  },
  "events": [
    {"type": "thinking_step", "agent": "Goal Analyzer", "output": {...}},
    {"type": "journey_started", "journey_id": "abc12345"}
  ]
}
```

#### GET /journey/v2/{id}/map

**Response:**
```json
{
  "journey_id": "abc12345",
  "title": "AYT Matematik",
  "current_stage": 1,
  "total_stages": 12,
  "total_xp": 12500,
  "earned_xp": 450,
  "total_packages": 130,
  "completed_packages": 5,
  "total_exams": 98,
  "completed_exams": 2,
  "stages": [
    {
      "id": "stage_001",
      "number": 1,
      "title": "Temel Kavramlar",
      "status": "in_progress",
      "theme_color": "#3B82F6",
      "icon": "📐",
      "xp_total": 1000,
      "xp_earned": 450,
      "completion_percentage": 45,
      "packages": [
        {
          "id": "pkg_001",
          "number": 1,
          "title": "Giriş",
          "type": "intro",
          "status": "completed",
          "xp_reward": 100,
          "xp_earned": 100,
          "content_blocks": [...],
          "exercises": [...],
          "exams": [...]
        }
      ]
    }
  ]
}
```

#### POST /journey/v2/{id}/packages/{pkg}/start

**Response:**
```json
{
  "success": true,
  "package_id": "pkg_001",
  "content_blocks": [
    {
      "id": "cb_001",
      "type": "text",
      "title": "Türev Nedir?",
      "content": "# Türev\n\nTürev, bir fonksiyonun...",
      "media_url": null,
      "completed": false
    },
    {
      "id": "cb_002",
      "type": "video",
      "title": "Türev Görselleştirme",
      "content": "Video açıklaması...",
      "media_url": "https://...",
      "completed": false
    }
  ],
  "events": [...]
}
```

#### POST /journey/v2/{id}/exams/{exam}/submit

**Request:**
```json
{
  "exam_type": "feynman",
  "explanation": "Türev, bir fonksiyonun belirli bir noktadaki...",
  "time_taken_seconds": 180
}
```

**Response:**
```json
{
  "success": true,
  "score": 85,
  "passed": true,
  "feedback": {
    "accuracy": 90,
    "depth": 80,
    "clarity": 85,
    "examples": 90,
    "completeness": 80,
    "overall_feedback": "Türev kavramını iyi açıkladınız..."
  },
  "result": {
    "exam_id": "exam_001",
    "exam_type": "feynman",
    "total_score": 85.0,
    "percentage": 85.0,
    "passed": true,
    "criteria_scores": [
      {"criteria_name": "accuracy", "score": 90, "max_score": 100},
      {"criteria_name": "depth", "score": 80, "max_score": 100}
    ],
    "detailed_feedback": "...",
    "suggestions": ["Daha fazla örnek verin", "..."]
  }
}
```

### 2.2 Validation Rules

| Field | Validation | Error Message |
|-------|------------|---------------|
| `title` | Required, min 3 chars | "Başlık gerekli" |
| `subject` | Required | "Konu gerekli" |
| `target_outcome` | Required | "Hedef gerekli" |
| `daily_hours` | 0.5 - 8.0 | "Günlük saat 0.5-8 arası olmalı" |
| `exam_type` | Required in submit | "Sınav türü gerekli" |
| `deadline` | ISO format if provided | "Geçersiz tarih formatı" |

---

## 3. Data Model Detayları

### 3.1 Enum Değerleri

#### PackageStatus (Kritik!)
```python
class PackageStatus(str, Enum):
    LOCKED = "locked"           # Kilitli
    AVAILABLE = "available"     # Açık
    IN_PROGRESS = "in_progress" # Devam ediyor
    COMPLETED = "completed"     # Tamamlandı ✅ (Bu eklendi)
    PASSED = "passed"           # Geçti
    FAILED = "failed"           # Kaldı
    MASTERED = "mastered"       # Mükemmel
    NEEDS_REVIEW = "needs_review" # Tekrar gerekli ✅ (Bu eklendi)
```

#### StageStatus
```python
class StageStatus(str, Enum):
    LOCKED = "locked"
    AVAILABLE = "available"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    MASTERED = "mastered"
```

#### PackageType
```python
class PackageType(str, Enum):
    LEARNING = "learning"   # Öğrenme paketi
    PRACTICE = "practice"   # Pratik paketi
    EXAM = "exam"           # Sınav paketi
    REVIEW = "review"       # Tekrar paketi
    CLOSURE = "closure"     # Kapanış paketi
    INTRO = "intro"         # Giriş paketi
```

#### ExamType
```python
class ExamType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    FILL_BLANK = "fill_blank"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"
    FEYNMAN = "feynman"               # 🔴 Kritik
    TEACH_BACK = "teach_back"
    CONCEPT_MAP = "concept_map"
    PROBLEM_SOLVING = "problem_solving"
    CODE_CHALLENGE = "code_challenge"
    ORAL_PRESENTATION = "oral_presentation"
    PEER_REVIEW = "peer_review"
    SELF_ASSESSMENT = "self_assessment"
    PRACTICAL = "practical"
    SIMULATION_BASED = "simulation_based"
```

### 3.2 Dataclass to_dict Methods

Her dataclass'ın `to_dict()` metodu olmalı:

```python
@dataclass
class Package:
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "stage_id": self.stage_id,
            "number": self.number,
            "title": self.title,
            "type": self.type.value if isinstance(self.type, PackageType) else self.type,
            "status": self.status.value if isinstance(self.status, PackageStatus) else self.status,
            "content_blocks": [c.to_dict() for c in self.content_blocks],
            "exercises": [e.to_dict() for e in self.exercises],
            "exams": [e.to_dict() for e in self.exams],
            # ...
        }
```

---

## 4. Frontend Mimarisi

### 4.1 Component Files

| File | Purpose | Dependencies |
|------|---------|--------------|
| `JourneyCreationWizard.tsx` | 5-step wizard | framer-motion, lucide-react |
| `AIThinkingView.tsx` | Thinking animation | framer-motion |
| `StageMapV2.tsx` | Stage map display | framer-motion, lucide-react |
| `PackageView.tsx` | Content display | markdown-it/react |
| `ExamView.tsx` | Exam interface | Timer, Voice support |
| `CertificateView.tsx` | Certificate display | Share buttons |

### 4.2 TypeScript Interfaces

```typescript
// Essential interfaces
interface LearningGoal {
  title: string;
  subject: string;
  target_outcome: string;
  motivation: string;
  prior_knowledge: string;
  weak_areas: string[];
  focus_areas: string[];
  daily_hours: number;
  deadline: string | null;
  content_preferences: string[];
  exam_preferences: string[];
}

interface JourneyProgressData {
  journey_id: string;
  title: string;
  current_stage: number;
  total_stages: number;
  total_xp: number;
  earned_xp: number;
  stages: StageData[];
}

interface StageData {
  id: string;
  number: number;
  title: string;
  status: 'locked' | 'available' | 'in_progress' | 'completed';
  theme_color: string;
  packages: PackagePreview[];
  xp_total: number;
  xp_earned: number;
}

interface PackagePreview {
  id: string;
  number: number;
  title: string;
  type: 'intro' | 'learning' | 'practice' | 'review' | 'exam' | 'closure';
  status: 'locked' | 'available' | 'in_progress' | 'completed';
  xp_reward: number;
  exams?: ExamPreview[];
}

interface ExamData {
  id: string;
  title: string;
  type: ExamType;
  topic: string;
  questions?: Question[];
  time_limit_minutes?: number;
  passing_score: number;
}

interface ExamResult {
  passed: boolean;
  score: number;
  percentage: number;
  feedback: FeynmanCriteria;
  xp_earned: number;
}
```

### 4.3 API Fetch Functions

```typescript
// services/learningApi.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export const learningApi = {
  listJourneys: async () => {
    const res = await fetch(`${API_BASE}/journey/v2/list`);
    return res.json();
  },
  
  createJourney: async (goal: LearningGoal) => {
    const res = await fetch(`${API_BASE}/journey/v2/create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(goal)
    });
    return res.json();
  },
  
  getJourneyMap: async (journeyId: string) => {
    const res = await fetch(`${API_BASE}/journey/v2/${journeyId}/map`);
    return res.json();
  },
  
  startPackage: async (journeyId: string, packageId: string) => {
    const res = await fetch(`${API_BASE}/journey/v2/${journeyId}/packages/${packageId}/start`, {
      method: 'POST'
    });
    return res.json();
  },
  
  submitExam: async (journeyId: string, examId: string, submission: ExamSubmission) => {
    const res = await fetch(`${API_BASE}/journey/v2/${journeyId}/exams/${examId}/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(submission)
    });
    return res.json();
  }
};
```

---

## 5. Sınav Değerlendirme Sistemi

### 5.1 Evaluator Classes

```python
# exam_system.py
class ExamSystem:
    evaluators: Dict[ExamType, BaseEvaluator]
    
    def __init__(self):
        self.evaluators = {
            ExamType.MULTIPLE_CHOICE: MultipleChoiceEvaluator(),
            ExamType.FEYNMAN: FeynmanExamEvaluator(),
            ExamType.PROBLEM_SOLVING: ProblemSolvingEvaluator(),
            ExamType.TEACH_BACK: TeachBackEvaluator(),
            ExamType.CONCEPT_MAP: ConceptMapEvaluator(),
            # ...
        }
    
    async def evaluate_exam(self, exam: Exam, submission: Dict, ...) -> ExamResult:
        evaluator = self.evaluators.get(exam.type)
        return await evaluator.evaluate(exam, submission)
```

### 5.2 Feynman Evaluator

```python
class FeynmanExamEvaluator:
    CRITERIA = {
        "accuracy": {"weight": 0.20, "description": "Bilgi doğruluğu"},
        "depth": {"weight": 0.20, "description": "Konu derinliği"},
        "clarity": {"weight": 0.20, "description": "Açıklık"},
        "examples": {"weight": 0.20, "description": "Örnek kullanımı"},
        "completeness": {"weight": 0.20, "description": "Bütünlük"}
    }
    
    async def evaluate(self, exam: Exam, submission: Dict) -> ExamResult:
        explanation = submission.get("explanation", "")
        
        # LLM ile değerlendirme
        prompt = self._build_evaluation_prompt(exam.feynman_config, explanation)
        response = await self.llm_service.generate(prompt)
        
        # Parse scores
        criteria_scores = self._parse_scores(response)
        
        # Calculate total
        total = sum(s.score * s.weight for s in criteria_scores)
        
        return ExamResult(
            exam_id=exam.id,
            exam_type=ExamType.FEYNMAN,
            total_score=total,
            percentage=total,
            passed=total >= exam.passing_score,
            criteria_scores=criteria_scores,
            detailed_feedback=response.feedback
        )
```

### 5.3 Multiple Choice Evaluator

```python
class MultipleChoiceEvaluator:
    async def evaluate(self, exam: Exam, submission: Dict) -> ExamResult:
        answers = submission.get("answers", {})
        
        correct = 0
        total = len(exam.questions)
        
        for q in exam.questions:
            user_answer = answers.get(q.id)
            if user_answer == q.correct_answer:
                correct += 1
        
        percentage = (correct / total) * 100 if total > 0 else 0
        
        return ExamResult(
            exam_id=exam.id,
            exam_type=ExamType.MULTIPLE_CHOICE,
            total_score=correct,
            max_possible_score=total,
            percentage=percentage,
            passed=percentage >= exam.passing_score,
            detailed_feedback=f"{correct}/{total} soru doğru."
        )
```

---

## 6. WebSocket Protokolü

### 6.1 Connection

```javascript
const ws = new WebSocket('ws://localhost:8001/ws/journey/v2/{journey_id}');
```

### 6.2 Message Types

```typescript
type WSMessageType = 
  | 'journey_started'
  | 'thinking_step'
  | 'package_ready'
  | 'content_generated'
  | 'exam_started'
  | 'exam_graded'
  | 'xp_earned'
  | 'stage_completed'
  | 'journey_completed'
  | 'error';

interface WSMessage {
  type: WSMessageType;
  data: any;
  timestamp: string;
}
```

### 6.3 Event Payloads

```typescript
// thinking_step
{
  type: 'thinking_step',
  data: {
    agent_name: 'Goal Analyzer',
    action: 'analyze_learning_goal',
    reasoning: 'Kullanıcının hedefi analiz ediliyor...',
    output: {...}
  }
}

// exam_graded
{
  type: 'exam_graded',
  data: {
    exam_id: 'exam_001',
    passed: true,
    score: 85,
    xp_earned: 100
  }
}

// xp_earned
{
  type: 'xp_earned',
  data: {
    amount: 100,
    reason: 'Paket tamamlandı',
    new_total: 550
  }
}
```

---

## 7. Error Handling

### 7.1 HTTP Error Codes

| Code | Situation | Response |
|------|-----------|----------|
| 400 | Invalid request body | `{"detail": "..."}` |
| 404 | Resource not found | `{"detail": "... bulunamadı"}` |
| 422 | Validation error | `{"detail": [...]}` |
| 500 | Server error | `{"detail": "Internal error"}` |

### 7.2 Error Response Format

```json
{
  "detail": "Journey bulunamadı",
  "error_code": "JOURNEY_NOT_FOUND",
  "timestamp": "2026-01-23T12:00:00Z"
}

// Validation error (422)
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "exam_type"],
      "msg": "Field required",
      "input": {...}
    }
  ]
}
```

### 7.3 Backend Exception Handling

```python
@router.post("/{journey_id}/exams/{exam_id}/submit")
async def submit_exam(...):
    try:
        result = await orchestrator.submit_exam(...)
        return {"success": True, "result": result.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 8. Test Gereksinimleri

### 8.1 Unit Test Coverage

| Module | Min Coverage | Focus Areas |
|--------|--------------|-------------|
| models.py | 90% | Enum values, to_dict |
| orchestrator.py | 85% | create_journey, submit_exam |
| exam_system.py | 90% | All evaluators |
| curriculum_planner.py | 80% | Stage/package creation |
| certificate_system.py | 85% | Generation, verification |

### 8.2 Integration Tests

```python
# Beklenen test senaryoları
async def test_complete_journey_flow():
    # 1. Create journey
    # 2. Get map
    # 3. Start first package
    # 4. Complete package
    # 5. Submit exam
    # 6. Complete journey
    # 7. Verify certificate
```

### 8.3 API Tests

| Test | Endpoint | Expected |
|------|----------|----------|
| List journeys | GET /list | 200, journeys array |
| Create journey | POST /create | 200, journey_id |
| Get map | GET /{id}/map | 200, stages array |
| Start package | POST /packages/{id}/start | 200, content |
| Submit exam | POST /exams/{id}/submit | 200, result |
| Invalid journey | GET /invalid/map | 404 |
| Invalid package | POST /{id}/packages/invalid/start | 404 |
| Missing exam_type | POST /exams/{id}/submit | 422 |

### 8.4 Frontend Tests

```typescript
// Component tests
describe('JourneyCreationWizard', () => {
  it('should render all 5 steps');
  it('should validate required fields');
  it('should call onComplete with valid goal');
});

describe('StageMapV2', () => {
  it('should render all stages');
  it('should expand stage on click');
  it('should call onPackageClick');
});

describe('ExamView', () => {
  it('should render timer when time_limit set');
  it('should submit answers on complete');
  it('should show result after submission');
});
```

---

## 📊 Technical Checklist

### Backend
- [ ] Tüm models.py enum değerleri eksiksiz
- [ ] Tüm to_dict() metotları çalışıyor
- [ ] Singleton pattern doğru uygulanmış
- [ ] API endpoints doğru prefix kullanıyor (/journey/v2)
- [ ] ExamSubmission validation doğru (exam_type required)
- [ ] Error handling tutarlı

### Frontend  
- [ ] TypeScript interfaces backend ile uyumlu
- [ ] API calls doğru endpoint'leri kullanıyor
- [ ] Component props doğru typed
- [ ] Error states handle ediliyor
- [ ] Loading states mevcut

### Integration
- [ ] WebSocket connection çalışıyor
- [ ] Real-time updates frontend'e ulaşıyor
- [ ] State senkronizasyonu doğru

---

*Son güncelleme: 23 Ocak 2026*
