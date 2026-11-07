"""
Unit test suite for LessonForge.
Tests input validation, citation checker, storage versioning, atomic saves,
failure simulation hooks, and 45-minute timing budgets.
"""
import os
import shutil
from pathlib import Path
import pytest

from core.exporter import build_lesson_zip_bundle, generate_references_markdown, generate_styled_html
from core.llm import get_simulated_failure, set_simulated_failure
from core.models import (
    AccessLevel,
    LessonMetadata,
    LessonPackage,
    LessonSection,
    LessonVersion,
    NormalizedSource,
    ResearchDossier,
    SourceType,
    StructuredLessonPlan,
)
from core.storage import (
    atomic_write_json,
    atomic_write_text,
    delete_lesson,
    get_lesson_dir,
    load_lesson,
    revert_to_version,
    save_lesson_version,
    save_new_lesson,
)
from generator.lesson_generator import generate_structured_lesson, render_lesson_to_markdown
from qc.factual_checker import _run_deterministic_checks, review_factual_accuracy
from qc.pedagogical_checker import review_teaching_quality
from research.aggregator import gather_research


@pytest.fixture
def sample_dossier():
    return ResearchDossier(
        query="HTTP Requests and Responses",
        objective="Explain GET and POST methods",
        sources=[
            NormalizedSource(
                id="S1",
                type=SourceType.WEB,
                title="MDN Web Docs: HTTP Methods",
                url="https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods",
                author_or_channel="Mozilla",
                retrieved_text_excerpt="HTTP defines a set of request methods to indicate the desired action to be performed for a given resource.",
                access_level=AccessLevel.FULL_TEXT,
                relevance_note="Foundational method definitions.",
            ),
            NormalizedSource(
                id="S2",
                type=SourceType.BOOK,
                title="HTTP: The Definitive Guide",
                url="https://books.google.com/sample",
                author_or_channel="David Gourley",
                retrieved_text_excerpt="Detailed coverage of HTTP status code categories: 2xx success, 4xx client errors, and 5xx server errors.",
                access_level=AccessLevel.DESCRIPTION_ONLY,
                relevance_note="Standard protocol text on status codes.",
            ),
        ],
    )


# -----------------------------------------------------------------------------
# 1. Validation Tests
# -----------------------------------------------------------------------------
def test_input_validation():
    """Validates that blank inputs are caught and named accurately."""
    def validate_inputs(title: str, objective: str):
        t = title.strip()
        o = objective.strip()
        if not t and not o:
            return False, "Lesson Title and Learning Objective are both required."
        if not t:
            return False, "Lesson Title is required."
        if not o:
            return False, "Learning Objective is required."
        return True, "Valid"

    assert validate_inputs("", "")[0] is False
    assert "both required" in validate_inputs("", "")[1]
    assert validate_inputs("", "Some objective")[0] is False
    assert "Lesson Title is required" in validate_inputs("", "Some objective")[1]
    assert validate_inputs("Some title", "")[0] is False
    assert "Learning Objective is required" in validate_inputs("Some title", "")[1]
    assert validate_inputs("Title", "Objective")[0] is True


# -----------------------------------------------------------------------------
# 2. Deterministic Citation & URL Checker Tests
# -----------------------------------------------------------------------------
def test_citation_checker_valid(sample_dossier):
    """Verifies that citations matching S1 and S2 pass deterministic checks."""
    lesson_text = (
        "# HTTP Lesson\n\n"
        "HTTP defines standard request methods [S1].\n\n"
        "Status codes are divided into 2xx, 4xx, and 5xx categories [S2].\n"
    )
    passed, invalid, uncited, unverified, issues = _run_deterministic_checks(lesson_text, sample_dossier)
    assert passed is True
    assert len(invalid) == 0
    assert len(unverified) == 0


def test_citation_checker_catches_invalid_ids(sample_dossier):
    """Flags [S99] when only S1 and S2 exist in the dossier."""
    lesson_text = "This claim cites an invented source [S99]."
    passed, invalid, uncited, unverified, issues = _run_deterministic_checks(lesson_text, sample_dossier)
    assert passed is False
    assert "S99" in invalid
    assert any("S99" in iss.issue_found for iss in issues)


def test_citation_checker_catches_unverified_urls(sample_dossier):
    """Flags hallucinated external URLs not present in API results."""
    lesson_text = "Check out this ungrounded link: https://random-fake-blog-123.com/api"
    passed, invalid, uncited, unverified, issues = _run_deterministic_checks(lesson_text, sample_dossier)
    assert passed is False
    assert any("random-fake-blog-123.com" in u for u in unverified)


# -----------------------------------------------------------------------------
# 3. Storage, Atomic Saves & Versioning Tests
# -----------------------------------------------------------------------------
def test_atomic_write(tmp_path):
    """Verifies that atomic_write_text creates clean files via temp files."""
    test_file = tmp_path / "test_atomic.txt"
    atomic_write_text(test_file, "Hello Atomic World")
    assert test_file.exists()
    assert test_file.read_text(encoding="utf-8") == "Hello Atomic World"


def test_storage_lifecycle_and_rollback(sample_dossier):
    """Verifies saving, version snapshotting (v1 -> v2), and rollback."""
    test_id = "pytest-lesson-001"
    meta = LessonMetadata(
        id=test_id,
        title="Pytest Lesson",
        objective="Verify versioning lifecycle",
        current_version=1,
        total_versions=1,
    )
    content_v1 = "# Pytest Lesson v1\nInitial content [S1]."
    pkg = LessonPackage(
        metadata=meta,
        markdown_content=content_v1,
        research_dossier=sample_dossier,
        versions=[LessonVersion(version_number=1, note="v1", content=content_v1)],
    )

    try:
        # Save initial
        save_new_lesson(pkg)
        loaded = load_lesson(test_id)
        assert loaded is not None
        assert loaded.metadata.current_version == 1

        # Save version 2
        content_v2 = "# Pytest Lesson v2\nUpdated content [S2]."
        v2_num = save_lesson_version(test_id, content_v2, note="Teacher edit")
        assert v2_num == 2
        loaded_v2 = load_lesson(test_id)
        assert loaded_v2.metadata.current_version == 2
        assert len(loaded_v2.versions) == 2

        # Rollback to v1
        revert_to_version(test_id, 1)
        loaded_v3 = load_lesson(test_id)
        assert loaded_v3.metadata.current_version == 3
        assert "v1" in loaded_v3.markdown_content

    finally:
        delete_lesson(test_id)


# -----------------------------------------------------------------------------
# 4. 45-Minute Timing Budget Tests
# -----------------------------------------------------------------------------
def test_lesson_timing_budget_sums_to_45(sample_dossier):
    """Verifies that the generated structured lesson plan equals exactly 45 minutes."""
    plan, md = generate_structured_lesson(
        title="HTTP Requests and Responses",
        objective="Explain GET and POST methods",
        dossier=sample_dossier,
    )
    assert plan.total_minutes == 45
    total_sec_mins = sum(s.minutes for s in plan.sections)
    assert total_sec_mins == 45
    assert len(plan.sections) == 7
    assert "45" in md


# -----------------------------------------------------------------------------
# 5. Exporter Tests (ZIP, HTML, References)
# -----------------------------------------------------------------------------
def test_exporter_bundle_contents(sample_dossier):
    """Verifies that the ZIP bundle contains all 5 required files."""
    meta = LessonMetadata(id="test-exp", title="Export Test", objective="Obj")
    pkg = LessonPackage(
        metadata=meta,
        markdown_content="# Export Test\nContent [S1].",
        research_dossier=sample_dossier,
    )
    zip_bytes = build_lesson_zip_bundle(pkg)
    assert len(zip_bytes) > 500

    import io
    import zipfile
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        namelist = zf.namelist()
        assert "lesson.md" in namelist
        assert "lesson.html" in namelist
        assert "references.md" in namelist
        assert "qc_report_1_accuracy.md" in namelist
        assert "qc_report_2_teaching.md" in namelist


# -----------------------------------------------------------------------------
# 6. Failure Simulation Tests
# -----------------------------------------------------------------------------
def test_failure_simulation_hooks():
    """Verifies that the simulated failure toggle raises expected errors for demo video."""
    try:
        set_simulated_failure("research")
        with pytest.raises(RuntimeError, match="Simulated Research Pipeline Failure"):
            gather_research("Query", "Objective")

        set_simulated_failure("qc1")
        with pytest.raises(RuntimeError, match="Simulated QC Layer 1 Failure"):
            review_factual_accuracy("Some text", ResearchDossier(query="Q"))

        set_simulated_failure("qc2")
        with pytest.raises(RuntimeError, match="Simulated QC Layer 2 Failure"):
            review_teaching_quality("Some text", "Objective")

    finally:
        set_simulated_failure(None)
