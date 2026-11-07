"""
QC Layer 1: Factual Accuracy Review module for LessonForge.
Performs adversarial fact-checking against the Research Dossier and executes
deterministic (non-AI) verification for citation integrity, uncited paragraphs, and unverified URLs.
"""
import logging
import re
from typing import List, Set, Tuple

from core.llm import get_simulated_failure, llm_client
from core.models import QCFactualReport, QCIssue, ResearchDossier
from generator.prompt_templates import QC_FACTUAL_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


def review_factual_accuracy(
    lesson_markdown: str,
    dossier: ResearchDossier,
) -> QCFactualReport:
    """
    Executes QC Layer 1: Factual Accuracy Audit.
    Runs both an AI fact-checking reviewer and deterministic code checks.
    """
    # Check simulated failure hook for demo recording
    sim_fail = get_simulated_failure()
    if sim_fail == "qc1":
        raise RuntimeError("Simulated QC Layer 1 Failure: Fact-checking review engine timeout (Demo Mode).")

    logger.info("Executing QC Layer 1: Factual Accuracy Review...")

    prompt = f"""Conduct an adversarial, skeptical factual accuracy audit of this Lesson Plan against the Research Dossier.

RESEARCH DOSSIER:
{dossier.get_formatted_context()}

LESSON PLAN TO REVIEW:
{lesson_markdown}

Identify subtle inaccuracies, unsupported claims, oversimplifications, and verify whether cited sources support the text.
"""

    data = llm_client.generate_json_with_repair(
        prompt=prompt,
        system_instruction=QC_FACTUAL_SYSTEM_PROMPT,
        temperature=0.1,
        call_purpose="qc1",
    )

    # Parse AI issues
    ai_issues: List[QCIssue] = []
    for idx, raw_iss in enumerate(data.get("issues", []), 1):
        ai_issues.append(
            QCIssue(
                id=raw_iss.get("id") or f"qc1-{idx}",
                severity=raw_iss.get("severity", "medium").lower(),
                location=raw_iss.get("location", "Core Concept"),
                issue_found=raw_iss.get("issue_found", ""),
                evidence=raw_iss.get("evidence", ""),
                suggested_improvement=raw_iss.get("suggested_improvement", ""),
                applied=False,
                source_layer="qc1",
            )
        )

    # Run Deterministic (non-AI) code checks
    det_passed, invalid_cites, uncited_paras, unverified_urls, det_issues = _run_deterministic_checks(
        lesson_markdown=lesson_markdown,
        dossier=dossier,
        start_index=len(ai_issues) + 1,
    )

    all_issues = ai_issues + det_issues

    verdict = data.get("verdict", "Needs revision")
    if not all_issues:
        verdict = "Looks good"
    elif any(iss.severity == "high" for iss in all_issues):
        verdict = "Needs revision"

    report = QCFactualReport(
        verdict=verdict,
        confidence_note=data.get("confidence_note", "Audited thoroughly against verified external research excerpts."),
        what_was_verified=data.get("what_was_verified", f"Cross-examined factual claims against {len(dossier.sources)} retrieved sources."),
        issues=all_issues,
        invalid_citations=invalid_cites,
        uncited_paragraphs=uncited_paras,
        unverified_urls=unverified_urls,
        deterministic_passed=det_passed,
        is_stale=False,
    )

    return report


def _run_deterministic_checks(
    lesson_markdown: str,
    dossier: ResearchDossier,
    start_index: int = 1,
) -> Tuple[bool, List[str], List[str], List[str], List[QCIssue]]:
    """
    Executes non-AI deterministic code checks:
    1. Every [S#] citation exists in the source list.
    2. Flag uncited factual paragraphs (containing empirical/technical claims without [S#]).
    3. Flag any URL in the lesson that is not in the retrieved sources.
    """
    valid_source_ids = set(dossier.get_all_ids())
    valid_urls = set(dossier.get_all_urls())

    det_issues: List[QCIssue] = []
    invalid_cites: List[str] = []
    uncited_paras: List[str] = []
    unverified_urls: List[str] = []

    # 1. Citation check: Every [S#] exists
    found_citations = re.findall(r"\[(S\d+)\]", lesson_markdown)
    for c in found_citations:
        if c not in valid_source_ids and c not in invalid_cites:
            invalid_cites.append(c)
            det_issues.append(
                QCIssue(
                    id=f"qc1-det-{len(det_issues)+start_index}",
                    severity="high",
                    location="Lesson Citations",
                    issue_found=f"Citation [{c}] does not exist in the retrieved Research Dossier.",
                    evidence=f"Valid sources in dossier are: {', '.join(sorted(list(valid_source_ids)))}.",
                    suggested_improvement=f"Replace [{c}] with a valid source reference from the research set.",
                    applied=False,
                    source_layer="qc1",
                )
            )

    # 2. URL check: No invented URLs
    # Match markdown links: [text](url) and raw URLs
    urls_found = re.findall(r"https?://[^\s\)\"\'>]+", lesson_markdown)
    for u in urls_found:
        u_clean = u.rstrip(".,;")
        # Check against valid URLs
        matched = False
        for valid_u in valid_urls:
            if u_clean.startswith(valid_u) or valid_u.startswith(u_clean):
                matched = True
                break
        if not matched and "google.com" not in u_clean and u_clean not in unverified_urls:
            unverified_urls.append(u_clean)
            det_issues.append(
                QCIssue(
                    id=f"qc1-det-{len(det_issues)+start_index}",
                    severity="high",
                    location="Lesson References & Links",
                    issue_found=f"Unverified external URL detected: {u_clean}",
                    evidence="All lesson links must originate strictly from API research results.",
                    suggested_improvement="Remove the unverified URL or replace it with an official source from the Research Dossier.",
                    applied=False,
                    source_layer="qc1",
                )
            )

    # 3. Uncited paragraphs check
    paragraphs = [p.strip() for p in lesson_markdown.split("\n\n") if p.strip()]
    for p in paragraphs:
        # Ignore headers, tables, code fences, and reference sections
        if (
            p.startswith("#")
            or p.startswith("|")
            or p.startswith("```")
            or "References" in p
            or "Class Duration" in p
            or "Timing Budget" in p
        ):
            continue

        # Check if paragraph makes strong technical/numerical claims but has no [S#]
        has_citation = bool(re.search(r"\[S\d+\]", p))
        has_technical_claim = bool(re.search(r"\b(protocol|method|function|complexity|RFC|algorithm|status|memory|mutab|HTTP)\b", p, re.I))

        if has_technical_claim and not has_citation and len(p.split()) > 20:
            para_snippet = p[:90] + "..."
            uncited_paras.append(para_snippet)
            if len(uncited_paras) <= 2:  # Cap at 2 issues to avoid cluttering
                det_issues.append(
                    QCIssue(
                        id=f"qc1-det-{len(det_issues)+start_index}",
                        severity="medium",
                        location="Instructional Text",
                        issue_found=f"Uncited technical assertion: \"{para_snippet}\"",
                        evidence="Every technical claim must cite an authoritative source.",
                        suggested_improvement="Append the corresponding source citation tag [S#] to substantiate this paragraph.",
                        applied=False,
                        source_layer="qc1",
                    )
                )

    det_passed = len(invalid_cites) == 0 and len(unverified_urls) == 0
    return det_passed, invalid_cites, uncited_paras, unverified_urls, det_issues
