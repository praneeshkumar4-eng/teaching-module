"""
Web research retrieval module for LessonForge.
Retrieves real website content via Tavily Search API, with seamless fallback
to DuckDuckGo and Trafilatura page extraction. Never invents links.
"""
import logging
import re
from typing import List
import requests
import trafilatura

from config import config
from core.models import WebSource

logger = logging.getLogger(__name__)

# Try ddgs first, fallback to duckduckgo_search
try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        DDGS = None


def search_web(query: str, max_results: int = 4) -> List[WebSource]:
    """
    Searches the web for authoritative educational and factual sources.
    Tries Tavily first if TAVILY_API_KEY is configured; otherwise uses DuckDuckGo + Trafilatura.
    """
    if config.has_tavily_key:
        try:
            results = _search_tavily(query, max_results=max_results)
            if results:
                logger.info(f"Retrieved {len(results)} web sources via Tavily.")
                return results
        except Exception as e:
            logger.warning(f"Tavily search failed: {e}. Falling back to DuckDuckGo.")

    # Fallback to DuckDuckGo + Trafilatura
    return _search_ddg_trafilatura(query, max_results=max_results)


def _search_tavily(query: str, max_results: int = 4) -> List[WebSource]:
    """Queries Tavily Search API with content extraction."""
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": config.tavily_api_key,
        "query": query,
        "search_depth": "basic",
        "include_answer": False,
        "include_raw_content": False,
        "max_results": max_results,
    }
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    data = response.json()

    web_sources = []
    for idx, item in enumerate(data.get("results", []), 1):
        content = (item.get("content") or "").strip()
        web_sources.append(
            WebSource(
                id=f"web-{idx}",
                title=item.get("title", "Untitled Web Resource").strip(),
                url=item.get("url", ""),
                snippet=content[:280],
                content=content[:1500],
                published_date=item.get("published_date"),
                engine="Tavily",
            )
        )
    return web_sources


def _search_ddg_trafilatura(query: str, max_results: int = 4) -> List[WebSource]:
    """Queries DuckDuckGo and extracts page text using Trafilatura."""
    if DDGS is None:
        logger.error("Neither ddgs nor duckduckgo_search package is available.")
        return []

    # Clean punctuation like colons that cause DDG syntax operator errors
    clean_query = re.sub(r"[:\-_/\\#?]", " ", query).strip()
    clean_query = re.sub(r"\s+", " ", clean_query)

    raw_results = []
    try:
        with DDGS() as ddgs:
            raw_results = list(ddgs.text(clean_query, max_results=max_results))
    except Exception as e:
        logger.warning(f"Primary DDG search failed for '{clean_query}': {e}")

    # Fallback to simplified short topic if first query produced no results
    if not raw_results:
        simplified = " ".join(clean_query.split()[:4])
        try:
            with DDGS() as ddgs:
                raw_results = list(ddgs.text(simplified, max_results=max_results))
        except Exception as e:
            logger.error(f"Fallback DDG search failed for '{simplified}': {e}")

    web_sources = []
    for idx, item in enumerate(raw_results, 1):
        title = item.get("title", "").strip() or f"Source {idx}"
        href = item.get("href", "")
        body = item.get("body", "").strip()

        if not href:
            continue

        extracted_text = ""
        try:
            downloaded = trafilatura.fetch_url(href)
            if downloaded:
                extracted = trafilatura.extract(
                    downloaded,
                    include_comments=False,
                    include_tables=True,
                    no_fallback=False
                )
                if extracted:
                    extracted_text = extracted.strip()[:1500]
        except Exception as e:
            logger.debug(f"Trafilatura extraction skipped for {href}: {e}")

        final_content = extracted_text if extracted_text else body

        web_sources.append(
            WebSource(
                id=f"web-{idx}",
                title=title,
                url=href,
                snippet=body[:280] if body else final_content[:280],
                content=final_content,
                engine="DuckDuckGo",
            )
        )

    logger.info(f"Retrieved {len(web_sources)} web sources via DuckDuckGo + Trafilatura.")
    return web_sources
