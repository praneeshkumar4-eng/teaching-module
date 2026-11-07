"""
Research aggregator for LessonForge.
Orchestrates web, book, and video retrieval into a structured ResearchDossier.
"""
import concurrent.futures
import logging
from datetime import datetime
from typing import Optional

from core.models import ResearchDossier
from research.books_search import search_books
from research.web_search import search_web
from research.youtube_search import search_youtube

logger = logging.getLogger(__name__)


def gather_research(title: str, objective: str = "", subject: str = "") -> ResearchDossier:
    """
    Executes multi-source retrieval across Web, Academic Books, and YouTube in parallel.
    Consolidates findings into a verified ResearchDossier.
    """
    search_query = title.strip()
    if subject and subject.lower() not in title.lower():
        search_query = f"{title} {subject}".strip()

    logger.info(f"Gathering comprehensive research for query: '{search_query}'")

    web_results = []
    book_results = []
    video_results = []

    # Run searches concurrently to minimize latency
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        future_web = executor.submit(search_web, search_query, 4)
        future_books = executor.submit(search_books, search_query, 3)
        future_youtube = executor.submit(search_youtube, search_query, 3)

        try:
            web_results = future_web.result(timeout=20)
        except Exception as e:
            logger.error(f"Web search thread error: {e}")

        try:
            book_results = future_books.result(timeout=15)
        except Exception as e:
            logger.error(f"Book search thread error: {e}")

        try:
            video_results = future_youtube.result(timeout=15)
        except Exception as e:
            logger.error(f"YouTube search thread error: {e}")

    # Build formatted raw context for strict LLM grounding
    formatted_context_sections = []

    if web_results:
        formatted_context_sections.append("### VERIFIED WEB SOURCES")
        for idx, w in enumerate(web_results, 1):
            sec = f"[Web {idx}] Title: {w.title}\nURL: {w.url}\nExtracted Content:\n{w.content or w.snippet}"
            formatted_context_sections.append(sec)

    if book_results:
        formatted_context_sections.append("### ACADEMIC TEXTS & BOOKS")
        for idx, b in enumerate(book_results, 1):
            authors = ", ".join(b.authors) if b.authors else "Unknown Authors"
            sec = (
                f"[Book {idx}] Title: {b.title}\n"
                f"Authors: {authors} | Published: {b.year or 'N/A'} | Publisher: {b.publisher or 'N/A'}\n"
                f"Reference Link: {b.info_link or b.preview_link or 'N/A'}\n"
                f"Summary & Content:\n{b.description}"
            )
            formatted_context_sections.append(sec)

    if video_results:
        formatted_context_sections.append("### EDUCATIONAL VIDEOS & TRANSCRIPTS")
        for idx, v in enumerate(video_results, 1):
            trans_body = (
                f"Full Transcript Excerpt:\n\"{v.full_transcript or v.transcript_excerpt}\""
                if v.transcript_available
                else f"Description:\n{v.description}"
            )
            sec = (
                f"[Video {idx}] Title: {v.title}\n"
                f"Channel: {v.channel} | Duration: {v.duration or 'N/A'}\n"
                f"URL: {v.url}\n{trans_body}"
            )
            formatted_context_sections.append(sec)

    raw_context = "\n\n".join(formatted_context_sections)

    dossier = ResearchDossier(
        query=search_query,
        retrieved_at=datetime.now().isoformat(),
        web_sources=web_results,
        book_sources=book_results,
        video_sources=video_results,
        raw_context=raw_context,
    )

    logger.info(
        f"Research gathered: {len(web_results)} web sources, "
        f"{len(book_results)} books, {len(video_results)} videos."
    )
    return dossier
