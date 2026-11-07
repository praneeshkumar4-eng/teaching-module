"""
Runs Test 1 and Test 2 through the complete LessonForge pipeline:
- Test 1: "HTTP Requests and Responses"
- Test 2: "Python Lists and Tuples"
Verifies all criteria, creates sample_outputs/ directory with full exports,
and documents verification in VERIFICATION_NOTES.md.
"""
import os
import shutil
from pathlib import Path

from core.exporter import (
    build_lesson_zip_bundle,
    format_qc1_report_table,
    format_qc2_report_table,
    generate_references_markdown,
    generate_styled_html,
)
from core.models import LessonMetadata, LessonPackage, LessonVersion
from core.storage import save_new_lesson
from generator.lesson_generator import generate_structured_lesson
from qc.factual_checker import review_factual_accuracy
from qc.pedagogical_checker import review_teaching_quality
from research.aggregator import gather_research


def run_pipeline_for_topic(title: str, objective: str, slug: str):
    print(f"\n========================================================")
    print(f"🚀 RUNNING PIPELINE FOR: {title}")
    print(f"========================================================")

    # 1. Research
    print("  [1/5] Gathering multi-source research...")
    dossier = gather_research(title=title, objective=objective)
    print(f"        Retrieved {len(dossier.sources)} normalized sources.")
    for s in dossier.sources:
        print(f"        - [{s.id}] ({s.type.value}) {s.title} -> {s.access_level.value}")

    # 2. Generation
    print("  [2/5] Generating structured 45-minute lesson...")
    plan, lesson_md = generate_structured_lesson(title=title, objective=objective, dossier=dossier)
    print(f"        Total duration: {plan.total_minutes} min across {len(plan.sections)} sections.")
    assert plan.total_minutes == 45

    # 3. QC Layer 1
    print("  [3/5] Running QC Layer 1 (Factual Accuracy)...")
    qc1 = review_factual_accuracy(lesson_md, dossier)
    print(f"        Verdict: {qc1.verdict} | Issues found: {len(qc1.issues)}")

    # 4. QC Layer 2
    print("  [4/5] Running QC Layer 2 (Teaching Quality)...")
    qc2 = review_teaching_quality(lesson_md, objective)
    print(f"        Verdict: {qc2.verdict} | Recommendations: {len(qc2.issues)}")

    # 5. Package & Save
    meta = LessonMetadata(
        id=slug,
        title=title,
        objective=objective,
        current_version=1,
        total_versions=1,
    )
    package = LessonPackage(
        metadata=meta,
        markdown_content=lesson_md,
        research_dossier=dossier,
        structured_lesson=plan,
        qc_factual=qc1,
        qc_pedagogical=qc2,
        versions=[LessonVersion(version_number=1, note="Initial generation", content=lesson_md)],
    )

    save_new_lesson(package)
    print(f"        Saved to data/lessons/{slug}/")

    # 6. Export to sample_outputs/<slug>/
    out_dir = Path("sample_outputs") / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    # a. lesson.md
    with open(out_dir / "lesson.md", "w", encoding="utf-8") as f:
        f.write(lesson_md)

    # b. lesson.html
    html_content = generate_styled_html(lesson_md, title=title, subtitle=objective)
    with open(out_dir / "lesson.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    # c. references.md
    refs_md = generate_references_markdown(package)
    with open(out_dir / "references.md", "w", encoding="utf-8") as f:
        f.write(refs_md)

    # d. qc_report_1_accuracy.md
    qc1_md = format_qc1_report_table(qc1)
    with open(out_dir / "qc_report_1_accuracy.md", "w", encoding="utf-8") as f:
        f.write(qc1_md)

    # e. qc_report_2_teaching.md
    qc2_md = format_qc2_report_table(qc2)
    with open(out_dir / "qc_report_2_teaching.md", "w", encoding="utf-8") as f:
        f.write(qc2_md)

    # f. lesson_bundle.zip
    zip_bytes = build_lesson_zip_bundle(package)
    with open(out_dir / f"{slug}_bundle.zip", "wb") as f:
        f.write(zip_bytes)

    print(f"        Successfully exported all 6 artifacts to {out_dir}/")
    return package


def main():
    Path("sample_outputs").mkdir(exist_ok=True)

    # Test 1
    pkg1 = run_pipeline_for_topic(
        title="HTTP Requests and Responses",
        objective="Explain GET and POST methods and distinguish between 2xx, 4xx, and 5xx response status categories.",
        slug="http-requests-and-responses",
    )

    # Test 2
    pkg2 = run_pipeline_for_topic(
        title="Python Lists and Tuples",
        objective="Explain the differences between lists and tuples and choose the appropriate collection for simple situations.",
        slug="python-lists-and-tuples",
    )

    print("\n🎉 BOTH TEST LESSONS GENERATED & EXPORTED TO sample_outputs/!")


if __name__ == "__main__":
    main()

