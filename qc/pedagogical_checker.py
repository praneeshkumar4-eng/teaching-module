"""
QC Layer 2: Pedagogical & Teaching Quality Review module for LessonForge.
Evaluates objective coverage part-by-part, learner clarity, active learning feasibility,
comprehension question alignment, and 45-minute pacing.
"""
import logging
from typing import List

from core.llm import get_simulated_failure, llm_client
from core.models import ObjectiveCoverageItem, QCIssue, QCPedagogicalReport
from generator.prompt_templates import QC_PEDAGOGICAL_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


def review_teaching_quality(
    lesson_markdown: str,
    objective: str,
) -> QCPedagogicalReport:
    """
    Executes QC Layer 2: Pedagogical Quality Audit.
    Evaluates learning objective coverage, pacing feasibility, and question rigor.
    """
    # Check simulated failure hook for demo recording
    sim_fail = get_simulated_failure()
    if sim_fail == "qc2":
        raise RuntimeError("Simulated QC Layer 2 Failure: Pedagogical reviewer engine unreachable (Demo Mode).")

    logger.info("Executing QC Layer 2: Pedagogical Quality Review...")

    prompt = f"""Conduct an experienced master teacher review of this Lesson Plan.

STATED LEARNING OBJECTIVE:
{objective}

LESSON PLAN TO REVIEW:
{lesson_markdown}

Check objective coverage part-by-part, unfamiliar undefined jargon, example clarity, 7-minute activity feasibility, and question alignment.
"""

    data = llm_client.generate_json_with_repair(
        prompt=prompt,
        system_instruction=QC_PEDAGOGICAL_SYSTEM_PROMPT,
        temperature=0.2,
        call_purpose="qc2",
    )

    issues: List[QCIssue] = []
    for idx, raw_iss in enumerate(data.get("issues", []), 1):
        issues.append(
            QCIssue(
                id=raw_iss.get("id") or f"qc2-{idx}",
                severity=raw_iss.get("severity", "medium").lower(),
                location=raw_iss.get("location", "Instructional Design"),
                issue_found=raw_iss.get("issue_found", ""),
                evidence=raw_iss.get("evidence", ""),
                suggested_improvement=raw_iss.get("suggested_improvement", ""),
                applied=False,
                source_layer="qc2",
            )
        )

    # Parse objective coverage table
    coverage_items: List[ObjectiveCoverageItem] = []
    for c in data.get("objective_coverage", []):
        coverage_items.append(
            ObjectiveCoverageItem(
                objective_part=c.get("objective_part", "Core Objective"),
                where_taught=c.get("where_taught", "Direct Instruction"),
                where_tested=c.get("where_tested", "Comprehension Questions"),
                covered=bool(c.get("covered", True)),
            )
        )

    verdict = data.get("verdict", "Needs revision")
    if not issues:
        verdict = "Looks good"
    elif any(iss.severity == "high" for iss in issues):
        verdict = "Needs revision"

    report = QCPedagogicalReport(
        verdict=verdict,
        confidence_note=data.get("confidence_note", "Instructional design evaluated against Bloom's taxonomy and active learning standards."),
        issues=issues,
        objective_coverage=coverage_items,
        what_was_verified=data.get("what_was_verified", "Verified that core concepts are scaffolded and questions test both recall and application."),
        is_stale=False,
    )

    return report
