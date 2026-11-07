"""
Comprehensive end-to-end integration test for LessonForge.
Tests research retrieval, lesson synthesis, QC layers 1 & 2, recommendation application,
version control snapshots, and ZIP/HTML exports.
"""
import os
import sys
from pathlib import Path

# Add project root to sys.path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from core.models import LessonMetadata, LessonPackage, LessonVersion
from core.storage import (
    delete_lesson,
    list_all_lessons,
    load_lesson,
    revert_to_version,
    save_lesson_version,
    save_new_lesson,
)
from core.exporter import build_lesson_zip_bundle, generate_styled_html
from generator.lesson_generator import apply_recommendations_to_lesson, generate_lesson_plan
from qc.factual_checker import review_factual_accuracy
from qc.pedagogical_checker import review_teaching_quality
from research.aggregator import gather_research


def run_all_tests():
    print("=" * 60)
    print("🚀 STARTING LESSONFORGE INTEGRATION & UNIT TESTS")
    print("=" * 60)

    # 1. Test Research Retrieval
    print("\n[TEST 1] Testing Multi-Source Research Retrieval...")
    title = "Photosynthesis: Light Reactions"
    objective = "Students will be able to explain how light energy excites electrons in photosystems and drives ATP synthesis."
    dossier = gather_research(title=title, objective=objective, subject="Biology")

    print(f"  -> Web Sources retrieved: {len(dossier.web_sources)}")
    print(f"  -> Academic Books retrieved: {len(dossier.book_sources)}")
    print(f"  -> Video Sources retrieved: {len(dossier.video_sources)}")
    assert len(dossier.web_sources) > 0, "Expected at least 1 web source."
    assert len(dossier.book_sources) > 0, "Expected at least 1 book source."
    assert len(dossier.video_sources) > 0, "Expected at least 1 video source."
    print("  ✅ [TEST 1 PASSED]: All 3 research channels retrieved verified sources.")

    # 2. Test Lesson Generation
    print("\n[TEST 2] Testing Grounded 45-Minute Lesson Generation...")
    lesson_md = generate_lesson_plan(
        title=title,
        objective=objective,
        dossier=dossier,
        grade_level="Grade 9-10 (Early High School)",
        subject="Biology & Life Sciences",
    )
    print(f"  -> Generated lesson length: {len(lesson_md)} chars")
    assert len(lesson_md) > 200, "Lesson markdown too short."
    assert "45" in lesson_md or "Minute" in lesson_md, "Expected 45-minute structure in lesson."
    print("  ✅ [TEST 2 PASSED]: 45-minute lesson plan synthesized successfully.")

    # 3. Test QC Layer 1 (Factual Accuracy)
    print("\n[TEST 3] Testing QC Layer 1: Factual Accuracy Audit...")
    qc1 = review_factual_accuracy(lesson_markdown=lesson_md, dossier=dossier)
    print(f"  -> Overall Factual Score: {qc1.overall_score}/100, Status: {qc1.status}")
    print(f"  -> Findings count: {len(qc1.findings)}, Verified: {qc1.verified_count}")
    assert qc1.overall_score >= 0 and qc1.overall_score <= 100
    assert len(qc1.summary) > 10
    print("  ✅ [TEST 3 PASSED]: QC Layer 1 audit completed with structured report.")

    # 4. Test QC Layer 2 (Pedagogical Review)
    print("\n[TEST 4] Testing QC Layer 2: Teaching Quality & Pedagogy...")
    qc2 = review_teaching_quality(
        lesson_markdown=lesson_md,
        objective=objective,
        grade_level="Grade 9-10",
    )
    print(f"  -> Overall Pedagogy Score: {qc2.overall_score}/100, Rating: {qc2.status}")
    print(f"  -> Recommendations count: {len(qc2.recommendations)}")
    assert qc2.overall_score >= 0 and qc2.overall_score <= 100
    assert len(qc2.recommendations) > 0
    print("  ✅ [TEST 4 PASSED]: QC Layer 2 review generated actionable recommendations.")

    # 5. Test Packaging & Local Storage
    print("\n[TEST 5] Testing Local Storage & Versioning...")
    test_id = "test-photosynthesis-001"
    meta = LessonMetadata(
        id=test_id,
        title=title,
        objective=objective,
        grade_level="Grade 9-10",
        subject="Biology",
        duration_minutes=45,
        current_version=1,
        total_versions=1,
    )
    pkg = LessonPackage(
        metadata=meta,
        markdown_content=lesson_md,
        research_dossier=dossier,
        qc_factual=qc1,
        qc_pedagogical=qc2,
        versions=[LessonVersion(version_number=1, note="Initial creation", content=lesson_md)],
    )

    saved_id = save_new_lesson(pkg)
    assert saved_id == test_id
    print(f"  -> Saved new lesson with ID: {saved_id}")

    # Verify loading
    loaded_pkg = load_lesson(test_id)
    assert loaded_pkg is not None
    assert loaded_pkg.metadata.title == title
    assert loaded_pkg.qc_factual is not None
    assert loaded_pkg.qc_pedagogical is not None
    print("  -> Successfully loaded full lesson package from disk.")

    # Test saving version 2
    updated_md = lesson_md + "\n\n<!-- Teacher edit note: Scaffolding added -->"
    v2_num = save_lesson_version(test_id, updated_md, note="Added scaffolding note")
    assert v2_num == 2
    loaded_v2 = load_lesson(test_id)
    assert loaded_v2.metadata.current_version == 2
    assert len(loaded_v2.versions) == 2
    print(f"  -> Successfully created version v{v2_num}.")

    # Test rollback to version 1
    revert_ok = revert_to_version(test_id, 1)
    assert revert_ok is True
    loaded_v3 = load_lesson(test_id)
    assert loaded_v3.metadata.current_version == 3  # Rolled back snapshot saved as v3
    print("  -> Rollback to version snapshot verified.")

    # 6. Test Exporter (HTML & ZIP)
    print("\n[TEST 6] Testing Exporters (HTML & ZIP bundle)...")
    html_output = generate_styled_html(lesson_md, title=title)
    assert "<!DOCTYPE html>" in html_output
    assert title in html_output
    assert "@media print" in html_output
    print("  -> HTML generator produced valid document with print stylesheet.")

    zip_bytes = build_lesson_zip_bundle(loaded_v3)
    assert len(zip_bytes) > 1000
    print(f"  -> In-memory ZIP package generated ({len(zip_bytes)} bytes).")

    # 7. Test Apply QC Recommendations
    print("\n[TEST 7] Testing Selective QC Recommendation Application...")
    recs_to_apply = qc2.recommendations[:1]
    revised_md = apply_recommendations_to_lesson(lesson_md, recs_to_apply)
    assert len(revised_md) > 200
    print(f"  -> Successfully applied recommendation to lesson ({len(revised_md)} chars).")

    # Clean up test lesson
    delete_lesson(test_id)
    print(f"  -> Cleaned up test lesson {test_id}.")

    print("\n" + "=" * 60)
    print("🎉 ALL 7 TEST SUITES PASSED FLAWLESSLY!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
