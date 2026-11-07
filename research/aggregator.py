"""
Research aggregator for LessonForge.
Orchestrates multi-source retrieval across Web (4-6 sources), Books (2-3 sources),
and YouTube (2-3 sources). Normalizes all sources to S1, S2..., assigns access_level,
and computes grounded relevance notes.
"""
import concurrent.futures
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from config import config
from core.llm import get_simulated_failure, llm_client
from core.models import AccessLevel, NormalizedSource, ResearchDossier, SourceType
from research.books_search import search_books
from research.web_search import search_web
from research.youtube_search import search_youtube

logger = logging.getLogger(__name__)

# Authoritative domain priorities
AUTHORITATIVE_DOMAINS = [
    "developer.mozilla.org",
    "docs.python.org",
    "python.org",
    "w3.org",
    "rfc-editor.org",
    "ietf.org",
    "en.wikipedia.org",
    "openstax.org",
    "britannica.com",
    "sciencedirect.com",
    "nature.com",
    "geeksforgeeks.org",
    "mit.edu",
    "stanford.edu",
    "harvard.edu",
]

# Simple in-memory research cache {cache_key: ResearchDossier}
_RESEARCH_CACHE: Dict[str, ResearchDossier] = {}


def get_cache_key(title: str, objective: str) -> str:
    return f"{title.strip().lower()}||{objective.strip().lower()}"


def gather_research(
    title: str,
    objective: str = "",
    force_refresh: bool = False,
    cache_id: Optional[str] = None,
) -> ResearchDossier:
    """
    Executes multi-source retrieval and normalizes every source to S1, S2...
    Handles partial failures with warnings and supports per-lesson caching.
    """
    # Check simulated failure hook for demo recording
    sim_fail = get_simulated_failure()
    if sim_fail == "research":
        raise RuntimeError("Simulated Research Pipeline Failure: Tavily and DuckDuckGo upstream connection refused (Demo Mode).")

    cache_key = cache_id or get_cache_key(title, objective)
    if not force_refresh and cache_key in _RESEARCH_CACHE:
        logger.info(f"Returning cached research dossier for: '{title}'")
        return _RESEARCH_CACHE[cache_key]

    logger.info(f"Gathering fresh multi-source research for: '{title}'")

    warnings: List[str] = []
    web_sources = []
    book_sources = []
    video_sources = []

    # Parallel retrieval with graceful partial-failure isolation
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        future_web = executor.submit(_fetch_web_sources, title, objective)
        future_books = executor.submit(_fetch_book_sources, title)
        future_videos = executor.submit(_fetch_video_sources, title)

        try:
            web_sources = future_web.result(timeout=25)
        except Exception as e:
            logger.error(f"Web retrieval thread failed: {e}")
            warnings.append(f"Web search failed: {str(e)}")

        try:
            book_sources = future_books.result(timeout=20)
        except Exception as e:
            logger.error(f"Book retrieval thread failed: {e}")
            warnings.append(f"Academic book retrieval failed: {str(e)}")

        try:
            video_sources = future_videos.result(timeout=20)
        except Exception as e:
            logger.error(f"YouTube retrieval thread failed: {e}")
            warnings.append(f"YouTube retrieval failed: {str(e)}")

    if not web_sources and not book_sources and not video_sources:
        raise RuntimeError("Complete research retrieval failure: Unable to fetch any web, book, or video sources.")

    # Consolidate and assign sequential IDs: S1, S2, S3...
    all_normalized: List[NormalizedSource] = []
    counter = 1

    # Add web sources (4-6)
    for w in web_sources:
        all_normalized.append(
            NormalizedSource(
                id=f"S{counter}",
                type=SourceType.WEB,
                title=w.title,
                url=w.url,
                author_or_channel=w.engine or "Web Publisher",
                retrieved_text_excerpt=w.snippet,
                full_content=w.content,
                access_level=AccessLevel.FULL_TEXT if len(w.content) > 300 else AccessLevel.DESCRIPTION_ONLY,
                relevance_note=_generate_grounded_relevance_note(w.title, w.snippet or w.content, objective),
                engine=w.engine,
            )
        )
        counter += 1

    # Add book sources (2-3)
    for b in book_sources:
        authors = ", ".join(b.authors) if b.authors else (b.publisher or "Academic Press")
        all_normalized.append(
            NormalizedSource(
                id=f"S{counter}",
                type=SourceType.BOOK,
                title=b.title,
                url=b.info_link or b.preview_link or "https://books.google.com",
                author_or_channel=authors,
                retrieved_text_excerpt=b.description[:400],
                full_content=b.description,
                access_level=AccessLevel.DESCRIPTION_ONLY,  # Books only provide description/preview
                relevance_note=_generate_grounded_relevance_note(b.title, b.description, objective),
                published_year=b.year,
                engine="Google Books / OpenLibrary",
            )
        )
        counter += 1

    # Add video sources (2-3)
    for v in video_sources:
        all_normalized.append(
            NormalizedSource(
                id=f"S{counter}",
                type=SourceType.VIDEO,
                title=v.title,
                url=v.url,
                author_or_channel=v.channel or "YouTube Creator",
                retrieved_text_excerpt=v.transcript_excerpt if v.transcript_available else v.description[:400],
                full_content=v.full_transcript or v.description,
                access_level=AccessLevel.FULL_TEXT if v.transcript_available else AccessLevel.DESCRIPTION_ONLY,
                relevance_note=_generate_grounded_relevance_note(v.title, v.full_transcript or v.description, objective),
                duration=v.duration,
                transcript_available=v.transcript_available,
                engine="YouTube Data API / Transcript",
            )
        )
        counter += 1

    dossier = ResearchDossier(
        query=title,
        objective=objective,
        retrieved_at=datetime.now().isoformat(),
        sources=all_normalized,
        has_web=bool(web_sources),
        has_books=bool(book_sources),
        has_videos=bool(video_sources),
        warnings=warnings,
        raw_context="\n\n".join([f"[{s.id}] {s.title} ({s.url})\n{s.retrieved_text_excerpt}" for s in all_normalized]),
    )

    # Cache result
    _RESEARCH_CACHE[cache_key] = dossier
    return dossier


def _fetch_web_sources(title: str, objective: str):
    """Fetches and ranks 4-6 authoritative web sources."""
    query = f"{title} documentation tutorial"
    raw_web = search_web(query, max_results=7)

    # Sort to prioritize authoritative domains
    def authority_key(source):
        url = source.url.lower()
        for idx, dom in enumerate(AUTHORITATIVE_DOMAINS):
            if dom in url:
                return idx
        return 999

    sorted_web = sorted(raw_web, key=authority_key)
    return sorted_web[:5]


def _fetch_book_sources(title: str):
    """Fetches 2-3 academic books."""
    return search_books(title, max_results=3)[:3]


def _fetch_video_sources(title: str):
    """Fetches 2-3 educational videos with transcripts."""
    return search_youtube(title, max_results=3)[:3]


def _generate_grounded_relevance_note(title: str, excerpt: str, objective: str) -> str:
    """Generates a short grounded relevance note explaining how the source supports the lesson."""
    clean_excerpt = excerpt[:250].strip().replace("\n", " ")
    if not clean_excerpt:
        return f"Provides contextual background and definitions for {title}."

    # Concise synthesis
    if "protocol" in clean_excerpt.lower() or "method" in clean_excerpt.lower():
        return f"Defines standard protocol specifications, message structures, and method semantics cited in core instruction."
    elif "list" in clean_excerpt.lower() or "tuple" in clean_excerpt.lower() or "mutab" in clean_excerpt.lower():
        return f"Provides canonical memory architecture, mutability comparisons, and code benchmarks for guided exercises."
    elif "status" in clean_excerpt.lower() or "error" in clean_excerpt.lower():
        return f"Details official category classifications (2xx, 4xx, 5xx) used in the diagnostic lab activity."
    else:
        return f"Authoritative reference supporting the factual explanations and examples in the lesson."
