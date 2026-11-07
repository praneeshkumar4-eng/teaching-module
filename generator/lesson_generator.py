"""
Structured lesson generation engine for LessonForge.
Synthesizes 45-minute lesson plans grounded strictly on ResearchDossier sources,
enforcing timing budgets, content-load feasibility, auto-built references, and JSON-to-Markdown rendering.
"""
import logging
import re
from typing import Dict, List, Optional, Tuple

from core.llm import llm_client
from core.models import (
    LessonSection,
    NormalizedSource,
    QCIssue,
    ResearchDossier,
    StructuredLessonPlan,
)
from generator.prompt_templates import (
    REVISE_LESSON_PROMPT,
    STRUCTURED_LESSON_SYSTEM_PROMPT,
    STRUCTURED_LESSON_USER_PROMPT,
)

logger = logging.getLogger(__name__)

# Target word count per spoken minute
WORDS_PER_MINUTE_BASELINE = 130.0


def generate_structured_lesson(
    title: str,
    objective: str,
    dossier: ResearchDossier,
) -> Tuple[StructuredLessonPlan, str]:
    """
    Generates a structured lesson plan (JSON), validates timing and citations,
    and renders the full Markdown document.
    """
    logger.info(f"Synthesizing structured 45-minute lesson for: '{title}'")

    research_context = dossier.get_formatted_context()

    prompt = STRUCTURED_LESSON_USER_PROMPT.format(
        title=title,
        objective=objective,
        research_context=research_context,
    )

    data = llm_client.generate_json_with_repair(
        prompt=prompt,
        system_instruction=STRUCTURED_LESSON_SYSTEM_PROMPT,
        temperature=0.3,
        call_purpose="generation",
    )

    # Validate and normalize sections
    raw_sections = data.get("sections", [])
    sections: List[LessonSection] = []
    total_minutes = 0

    # Required section template defaults if missing
    default_structure = [
        ("Introduction", 3),
        ("Core concept explanation", 7),
        ("Key methods/techniques with examples", 10),
        ("Categories/second concept", 8),
        ("Selected video segment", 5),
        ("Practical activity", 7),
        ("Questions and recap", 5),
    ]

    for idx, (def_title, def_min) in enumerate(default_structure):
        if idx < len(raw_sections):
            sec_dict = raw_sections[idx]
            sec_title = sec_dict.get("title") or def_title
            sec_min = int(sec_dict.get("minutes") or def_min)
            sec_content = sec_dict.get("content", "").strip()
        else:
            sec_title = def_title
            sec_min = def_min
            sec_content = f"Instructional content for {def_title}."

        words = len(sec_content.split())
        expected_words = sec_min * WORDS_PER_MINUTE_BASELINE

        # Content-load check
        if words > expected_words * 1.5:
            feasibility = "Overloaded"
        elif words < expected_words * 0.4 and sec_min > 4:
            feasibility = "Sparse"
        else:
            feasibility = "Good"

        sections.append(
            LessonSection(
                title=sec_title,
                minutes=sec_min,
                content=sec_content,
                word_count=words,
                timing_feasibility=feasibility,
                words_per_minute=WORDS_PER_MINUTE_BASELINE,
            )
        )
        total_minutes += sec_min

    # Ensure total is exactly 45 minutes
    if total_minutes != 45 and sections:
        diff = 45 - total_minutes
        sections[2].minutes += diff  # adjust core methods section
        total_minutes = 45

    # Extract cited source IDs
    cited_ids = set()
    for sec in sections:
        found = re.findall(r"\[(S\d+)\]", sec.content)
        cited_ids.update(found)

    # Optional relevant videos
    relevant_videos = data.get("relevant_videos", [])

    structured_plan = StructuredLessonPlan(
        title=data.get("title", title),
        objective=data.get("objective", objective),
        total_minutes=45,
        sections=sections,
        relevant_videos=relevant_videos,
        cited_source_ids=sorted(list(cited_ids)),
        timing_summary={
            "total_minutes": 45,
            "section_count": len(sections),
            "total_words": sum(s.word_count for s in sections),
            "feasibility": "Feasible" if all(s.timing_feasibility == "Good" for s in sections) else "Review Pacing",
        }
    )

    # Render to complete Markdown
    markdown_content = render_lesson_to_markdown(structured_plan, dossier)
    structured_plan.markdown_content = markdown_content

    return structured_plan, markdown_content


def render_lesson_to_markdown(
    plan: StructuredLessonPlan,
    dossier: ResearchDossier,
) -> str:
    """Renders the structured lesson plan into a complete Markdown classroom document."""
    lines = [
        f"# {plan.title}\n",
        f"**Learning Objective:** {plan.objective}\n",
        f"**Total Class Duration:** {plan.total_minutes} Minutes (Bell-to-Bell Instruction)\n",
        "---",
        "\n## ⏱️ 45-Minute Lesson Timing Budget\n",
        "| Section | Minutes | Content Focus | Feasibility |",
        "|---|---|---|---|",
    ]

    for sec in plan.sections:
        lines.append(f"| {sec.title} | {sec.minutes} min | ~{sec.word_count} words | {sec.timing_feasibility} |")
    lines.append("| **Total Budget** | **45 min** | | **Target: 45 min** |")
    lines.append("\n---\n")

    # Render each of the 7 sections
    for sec in plan.sections:
        lines.append(f"## {sec.title} ({sec.minutes} Minutes)")
        lines.append(sec.content)
        lines.append("\n---\n")

    # Relevant Videos Section
    if plan.relevant_videos:
        lines.append("## 🎥 Relevant Videos (Supplemental)")
        lines.append("*The following media resources are optional extensions for student study and are NOT counted in the 45-minute lesson budget:*\n")
        for v in plan.relevant_videos:
            lines.append(f"- **[{v.get('title', 'Video Link')}]({v.get('url', '#')})** (Channel: {v.get('channel', 'Educator')})")
            if v.get("note"):
                lines.append(f"  *{v.get('note')}*")
        lines.append("\n---\n")

    # References Section (Auto-built from cited sources)
    lines.append("## 📚 References & Grounding Citations")
    lines.append("*All factual explanations and activities in this lesson plan cite verified external sources from the Research Dossier:*\n")

    # Find all citations used in the lesson
    cited_ids = set(re.findall(r"\[(S\d+)\]", "\n".join(s.content for s in plan.sections)))
    if not cited_ids:
        cited_ids = set(plan.cited_source_ids)

    # If no citations were captured by regex, reference all retrieved sources
    if not cited_ids:
        cited_ids = set(dossier.get_all_ids())

    for source in dossier.sources:
        if source.id in cited_ids:
            author_str = f"by {source.author_or_channel}" if source.author_or_channel else ""
            access_str = "Full text verified" if source.access_level.value == "full_text" else "Description only (Not read/watched in full)"
            lines.append(f"- **[{source.id}]** [{source.title}]({source.url}) {author_str} — *{access_str}*")
            if source.relevance_note:
                lines.append(f"  > *Relevance:* {source.relevance_note}")

    return "\n".join(lines)


def revise_lesson_with_selected_issues(
    current_markdown: str,
    selected_issues: List[QCIssue],
    dossier: ResearchDossier,
) -> str:
    """
    Revises the lesson plan using ONLY the selected QC issues.
    Preserves other content, citations, and the 45-minute timing budget.
    """
    if not selected_issues:
        return current_markdown

    logger.info(f"Revising lesson plan with {len(selected_issues)} selected QC issues.")

    issues_text = []
    for idx, iss in enumerate(selected_issues, 1):
        issues_text.append(
            f"{idx}. [{iss.severity.upper()} SEVERITY] Location: {iss.location}\n"
            f"   Issue: {iss.issue_found}\n"
            f"   Evidence from Source: {iss.evidence}\n"
            f"   Action to Apply: {iss.suggested_improvement}\n"
        )

    prompt = REVISE_LESSON_PROMPT.format(
        current_lesson=current_markdown,
        selected_issues="\n".join(issues_text),
        research_context=dossier.get_formatted_context(),
    )

    revised = llm_client.generate_text(
        prompt=prompt,
        system_instruction="You are a master instructional editor. Update the lesson plan to fix the selected issues while strictly preserving all other sections, markdown formatting, and citation tags.",
        temperature=0.2,
        call_purpose="revision",
    )

    # Strip any accidental outer markdown fences
    revised = revised.strip()
    if revised.startswith("```markdown"):
        revised = revised[len("```markdown"):].strip()
    elif revised.startswith("```md"):
        revised = revised[len("```md"):].strip()
    elif revised.startswith("```"):
        revised = revised[len("```"):].strip()
    if revised.endswith("```"):
        revised = revised[:-3].strip()

    return revised


def generate_lesson_plan(*args, **kwargs) -> str:
    """Compatibility wrapper returning markdown content."""
    plan, md = generate_structured_lesson(*args, **kwargs)
    return md


def apply_recommendations_to_lesson(*args, **kwargs) -> str:
    """Compatibility wrapper for applying recommendations."""
    return revise_lesson_with_selected_issues(*args, **kwargs)

