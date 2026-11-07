"""
Core data models for LessonForge.
Defines typed schemas for normalized research sources, lesson plans, versions,
and detailed QC review reports with deterministic checks.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Research Sources & Dossier Models (Step 1)
# ---------------------------------------------------------------------------

class AccessLevel(str, Enum):
    FULL_TEXT = "full_text"
    DESCRIPTION_ONLY = "description_only"


class SourceType(str, Enum):
    WEB = "web"
    BOOK = "book"
    VIDEO = "video"


class WebSource(BaseModel):
    id: str
    title: str
    url: str
    snippet: str = ""
    content: str = ""
    published_date: Optional[str] = None
    engine: str = "DuckDuckGo"


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
    video_id: str = ""
    url: str
    description: str = ""
    duration: Optional[str] = None
    transcript_available: bool = False
    transcript_excerpt: str = ""
    full_transcript: Optional[str] = None


class NormalizedSource(BaseModel):
    id: str  # S1, S2, S3...
    type: SourceType
    title: str
    url: str
    author_or_channel: str = ""
    retrieved_text_excerpt: str = ""
    full_content: str = ""
    access_level: AccessLevel
    relevance_note: str = ""  # Grounded LLM note on how it supports the lesson
    published_year: Optional[str] = None
    duration: Optional[str] = None
    transcript_available: bool = False
    engine: str = ""  # e.g. Tavily, DuckDuckGo, Google Books, YouTube API


class ResearchDossier(BaseModel):
    query: str
    objective: str = ""
    retrieved_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    sources: List[NormalizedSource] = Field(default_factory=list)
    has_web: bool = True
    has_books: bool = True
    has_videos: bool = True
    warnings: List[str] = Field(default_factory=list)
    raw_context: str = ""

    def get_source_by_id(self, source_id: str) -> Optional[NormalizedSource]:
        for s in self.sources:
            if s.id.upper() == source_id.upper():
                return s
        return None

    def get_all_ids(self) -> List[str]:
        return [s.id for s in self.sources]

    def get_all_urls(self) -> List[str]:
        return [s.url for s in self.sources if s.url]

    def get_formatted_context(self) -> str:
        """Builds structured research context for LLM prompts with exact S# tags."""
        lines = []
        for s in self.sources:
            access_desc = (
                "FULL TEXT AVAILABLE"
                if s.access_level == AccessLevel.FULL_TEXT
                else "DESCRIPTION ONLY (NOT read or watched in full)"
            )
            type_tag = s.type.value.upper()
            author_tag = f"by {s.author_or_channel}" if s.author_or_channel else ""

            lines.append(
                f"[{s.id}] TYPE: {type_tag} | TITLE: \"{s.title}\" {author_tag}\n"
                f"URL: {s.url}\n"
                f"ACCESS LEVEL: {access_desc}\n"
                f"RELEVANCE: {s.relevance_note}\n"
                f"EXCERPT / CONTENT:\n{s.retrieved_text_excerpt or s.full_content[:1500]}\n"
            )
        return "\n\n".join(lines)


# ---------------------------------------------------------------------------
# Lesson Sections & Timing Budget Models (Step 2)
# ---------------------------------------------------------------------------

class LessonSection(BaseModel):
    title: str
    minutes: int
    content: str
    word_count: int = 0
    timing_feasibility: str = "Good"  # "Good", "Overloaded", "Sparse"
    words_per_minute: float = 130.0


class StructuredLessonPlan(BaseModel):
    title: str
    objective: str
    total_minutes: int = 45
    sections: List[LessonSection] = Field(default_factory=list)
    relevant_videos: List[Dict[str, str]] = Field(default_factory=list)  # Optional video list
    cited_source_ids: List[str] = Field(default_factory=list)
    markdown_content: str = ""
    timing_summary: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# QC Layer 1: Factual Accuracy Models (Step 3)
# ---------------------------------------------------------------------------

class QCIssue(BaseModel):
    id: str  # e.g. qc1-1 or qc2-1
    severity: Literal["high", "medium", "low"]
    location: str  # Section name
    issue_found: str
    evidence: str
    suggested_improvement: str
    applied: bool = False
    source_layer: str = "qc1"  # "qc1" or "qc2"


class QCFactualReport(BaseModel):
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    verdict: str = "Needs revision"  # "Needs revision" or "Looks good"
    confidence_note: str = ""
    issues: List[QCIssue] = Field(default_factory=list)
    what_was_verified: str = ""
    # Deterministic checks
    invalid_citations: List[str] = Field(default_factory=list)
    uncited_paragraphs: List[str] = Field(default_factory=list)
    unverified_urls: List[str] = Field(default_factory=list)
    deterministic_passed: bool = True
    is_stale: bool = False


# ---------------------------------------------------------------------------
# QC Layer 2: Teaching Quality Models (Step 4)
# ---------------------------------------------------------------------------

class ObjectiveCoverageItem(BaseModel):
    objective_part: str
    where_taught: str
    where_tested: str
    covered: bool = True


class QCPedagogicalReport(BaseModel):
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    verdict: str = "Needs revision"  # "Needs revision" or "Looks good"
    confidence_note: str = ""
    issues: List[QCIssue] = Field(default_factory=list)
    objective_coverage: List[ObjectiveCoverageItem] = Field(default_factory=list)
    what_was_verified: str = ""
    is_stale: bool = False


# ---------------------------------------------------------------------------
# Storage, Metadata & Versioning (Step 5)
# ---------------------------------------------------------------------------

class LessonMetadata(BaseModel):
    id: str
    title: str
    objective: str
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
    structured_lesson: Optional[StructuredLessonPlan] = None
    qc_factual: Optional[QCFactualReport] = None
    qc_pedagogical: Optional[QCPedagogicalReport] = None
    versions: List[LessonVersion] = Field(default_factory=list)
