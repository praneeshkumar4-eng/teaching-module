"""
Lesson synthesis engine for LessonForge.
Generates comprehensive 45-minute lesson plans grounded strictly on retrieved research dossiers.
"""
import logging
from typing import List, Optional

from core.llm import llm_client
from core.models import QCPedagogicalRecommendation, ResearchDossier
from generator.prompt_templates import (
    APPLY_QC_RECOMMENDATIONS_PROMPT,
    LESSON_GENERATION_SYSTEM_PROMPT,
    LESSON_GENERATION_USER_PROMPT,
)

logger = logging.getLogger(__name__)


def generate_lesson_plan(
    title: str,
    objective: str,
    dossier: ResearchDossier,
    grade_level: str = "Grade 9-10",
    subject: str = "General Science",
    extra_instructions: Optional[str] = None,
) -> str:
    """
    Synthesizes a 45-minute lesson plan grounded strictly on the research dossier.
    """
    logger.info(f"Synthesizing 45-minute lesson plan for: '{title}'")

    extra_instructions_block = (
        f"- Additional Teacher Instructions: {extra_instructions}\n"
        if extra_instructions
        else ""
    )

    research_context = (
        dossier.raw_context
        if dossier.raw_context.strip()
        else dossier.get_citation_summary()
    )

    user_prompt = LESSON_GENERATION_USER_PROMPT.format(
        title=title,
        objective=objective,
        grade_level=grade_level,
        subject=subject,
        extra_instructions_block=extra_instructions_block,
        research_context=research_context,
    )

    lesson_markdown = llm_client.generate_text(
        prompt=user_prompt,
        system_instruction=LESSON_GENERATION_SYSTEM_PROMPT,
        temperature=0.4,  # Lower temperature for strict grounding and adherence
        json_mode=False,
    )

    # Clean any accidental markdown fence wrapper
    clean_markdown = _clean_llm_markdown(lesson_markdown)
    return clean_markdown


def apply_recommendations_to_lesson(
    current_lesson_markdown: str,
    recommendations: List[QCPedagogicalRecommendation],
) -> str:
    """
    Applies teacher-selected pedagogical and factual recommendations to the active lesson.
    """
    if not recommendations:
        return current_lesson_markdown

    logger.info(f"Applying {len(recommendations)} QC recommendations to lesson.")

    recs_text = []
    for idx, r in enumerate(recommendations, 1):
        recs_text.append(
            f"{idx}. Area: {r.area}\n"
            f"   Issue: {r.current_state}\n"
            f"   Action to Apply: {r.concrete_action}\n"
        )
    formatted_recs = "\n".join(recs_text)

    prompt = APPLY_QC_RECOMMENDATIONS_PROMPT.format(
        current_lesson=current_lesson_markdown,
        selected_recommendations=formatted_recs,
    )

    updated_lesson = llm_client.generate_text(
        prompt=prompt,
        system_instruction="You are an expert instructional editor. Update the lesson plan to incorporate the requested revisions while keeping verified source citations intact.",
        temperature=0.3,
    )

    return _clean_llm_markdown(updated_lesson)


def _clean_llm_markdown(text: str) -> str:
    """Strips outer markdown fences if the LLM wrapped the entire response in ```markdown."""
    text = text.strip()
    if text.startswith("```markdown"):
        text = text[len("```markdown"):].strip()
    elif text.startswith("```md"):
        text = text[len("```md"):].strip()
    elif text.startswith("```"):
        text = text[len("```"):].strip()

    if text.endswith("```"):
        text = text[:-3].strip()

    return text
