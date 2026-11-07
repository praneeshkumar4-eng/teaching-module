"""
Core data models for LessonForge.
Defines typed schemas for research sources, lesson plans, versions, and QC reviews.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Research Sources & Dossier Models
# ---------------------------------------------------------------------------

class WebSource(BaseModel):
    id: str
    title: str
    url: str
    snippet: str = ""
    content: str = ""
    published_date: Optional[str] = None
    engine: str = "Tavily"  # "Tavily" or "DuckDuckGo"


class BookSource(BaseModel):
    id: str
    title: str
    authors: List[str] = Field(default_factory=list)
    publisher: Optional[str] = None
    year: Optional[str] = None
    description: str = ""
    preview_link: Optional[str] = None
    info_link: Optional[str] = None
    isbn: Optional[str] = None


class VideoSource(BaseModel):
    id: str
    title: str
    channel: str = ""
    video_id: str
    url: str
    description: str = ""
    duration: Optional[str] = None
    transcript_available: bool = False
    transcript_excerpt: str = ""
    full_transcript: Optional[str] = None


class ResearchDossier(BaseModel):
    query: str
    retrieved_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    web_sources: List[WebSource] = Field(default_factory=list)
    book_sources: List[BookSource] = Field(default_factory=list)
    video_sources: List[VideoSource] = Field(default_factory=list)
    raw_context: str = ""

    def get_citation_summary(self) -> str:
        """Formats all sources into a reference index with tags like [Web 1], [Book 1]."""
        lines = []
        if self.web_sources:
            lines.append("### Web Sources")
            for idx, w in enumerate(self.web_sources, 1):
                lines.append(f"[{idx}] (Web) **{w.title}** - URL: {w.url}")
                if w.snippet:
                    lines.append(f"    Excerpt: {w.snippet[:300]}...")
        if self.book_sources:
            lines.append("\n### Academic Books")
            for idx, b in enumerate(self.book_sources, 1):
                authors = ", ".join(b.authors) if b.authors else "Unknown Authors"
                lines.append(f"[Book {idx}] **{b.title}** by {authors} ({b.year or 'N/A'}) - {b.info_link or ''}")
                if b.description:
                    lines.append(f"    Summary: {b.description[:300]}...")
        if self.video_sources:
            lines.append("\n### Video & Media Resources")
            for idx, v in enumerate(self.video_sources, 1):
                trans_note = " (Transcript included)" if v.transcript_available else ""
                lines.append(f"[Video {idx}] **{v.title}** (Channel: {v.channel}){trans_note} - URL: {v.url}")
                if v.transcript_excerpt:
                    lines.append(f"    Transcript quote: \"{v.transcript_excerpt[:250]}...\"")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# QC Layer Models
# ---------------------------------------------------------------------------

class QCAccuracyFinding(BaseModel):
    claim: str
    citation_ref: str = "Uncited"
    status: str = "VERIFIED"  # "VERIFIED", "CONTRADICTED", "UNSUPPORTED", "ACCURATE"
    explanation: str
    suggestion: str


class QCFactualReport(BaseModel):
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    overall_score: int = 100  # 0 to 100
    status: str = "PASS"  # "PASS", "NEEDS_MINOR_REVISION", "NEEDS_MAJOR_REVISION"
    summary: str = ""
    findings: List[QCAccuracyFinding] = Field(default_factory=list)
    verified_count: int = 0
    unsupported_count: int = 0
    contradicted_count: int = 0


class QCPedagogicalRecommendation(BaseModel):
    id: str
    area: str  # "Objective Alignment", "Pacing & Timing", "Active Learning", "Cognitive Rigor", "Formative Assessment", "Differentiation"
    current_state: str
    recommendation: str
    concrete_action: str
    severity: str = "MEDIUM"  # "HIGH", "MEDIUM", "LOW"
    applied: bool = False


class QCPedagogicalReport(BaseModel):
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    overall_score: int = 100  # 0 to 100
    status: str = "EXCELLENT"  # "EXCELLENT", "GOOD", "NEEDS_IMPROVEMENT"
    alignment_score: int = 100
    pacing_score: int = 100
    engagement_score: int = 100
    assessment_score: int = 100
    strengths: List[str] = Field(default_factory=list)
    areas_for_growth: List[str] = Field(default_factory=list)
    recommendations: List[QCPedagogicalRecommendation] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Lesson & Versioning Models
# ---------------------------------------------------------------------------

class LessonMetadata(BaseModel):
    id: str
    title: str
    objective: str
    grade_level: str = "Grade 9-10"
    subject: str = "General Science"
    duration_minutes: int = 45
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    current_version: int = 1
    total_versions: int = 1


class LessonVersion(BaseModel):
    version_number: int
    saved_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    note: str = "Initial generation"
    content: str


class LessonPackage(BaseModel):
    metadata: LessonMetadata
    markdown_content: str
    research_dossier: ResearchDossier
    qc_factual: Optional[QCFactualReport] = None
    qc_pedagogical: Optional[QCPedagogicalReport] = None
    versions: List[LessonVersion] = Field(default_factory=list)
