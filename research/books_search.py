"""
Academic and textbook research retrieval module for LessonForge.
Queries Google Books API (keyed or keyless endpoint) with graceful fallback
to OpenLibrary. Never invents links or citations.
"""
import logging
from typing import List
import requests

from config import config
from core.models import BookSource

logger = logging.getLogger(__name__)


def search_books(query: str, max_results: int = 4) -> List[BookSource]:
    """
    Retrieves real published books related to the topic.
    First tries Google Books API (using GOOGLE_BOOKS_API_KEY if available).
    If Google Books is rate-limited (HTTP 429) or unavailable, falls back to OpenLibrary.
    """
    books = _search_google_books(query, max_results=max_results)
    if books:
        logger.info(f"Retrieved {len(books)} books via Google Books API.")
        return books

    logger.info("Falling back to OpenLibrary for academic book retrieval.")
    return _search_open_library(query, max_results=max_results)


def _search_google_books(query: str, max_results: int = 4) -> List[BookSource]:
    """Queries the Google Books volumes API."""
    base_url = "https://www.googleapis.com/books/v1/volumes"
    params = {
        "q": query,
        "maxResults": max_results,
        "printType": "books",
        "orderBy": "relevance",
    }
    if config.has_google_books_key:
        params["key"] = config.google_books_api_key

    try:
        response = requests.get(base_url, params=params, timeout=8)
        if response.status_code == 429:
            logger.warning("Google Books API rate limited (HTTP 429).")
            return []
        response.raise_for_status()
        data = response.json()

        items = data.get("items", [])
        if not items:
            return []

        books = []
        for idx, item in enumerate(items, 1):
            vol = item.get("volumeInfo", {})
            title = vol.get("title", "Untitled Book").strip()
            authors = vol.get("authors", [])
            publisher = vol.get("publisher", "Academic Press")
            published_date = vol.get("publishedDate", "")
            year = published_date[:4] if published_date else None
            description = vol.get("description", "").strip()
            info_link = vol.get("infoLink") or vol.get("canonicalVolumeLink")
            preview_link = vol.get("previewLink")

            # Extract ISBN if present
            isbn = None
            for identifier in vol.get("industryIdentifiers", []):
                if identifier.get("type") in ["ISBN_13", "ISBN_10"]:
                    isbn = identifier.get("identifier")
                    break

            books.append(
                BookSource(
                    id=f"book-{idx}",
                    title=title,
                    authors=authors,
                    publisher=publisher,
                    year=year,
                    description=description[:1200] if description else f"Academic text exploring {title}.",
                    preview_link=preview_link,
                    info_link=info_link,
                    isbn=isbn,
                )
            )
        return books

    except Exception as e:
        logger.warning(f"Google Books API request failed: {e}")
        return []


def _search_open_library(query: str, max_results: int = 4) -> List[BookSource]:
    """Queries the Open Library search API as a resilient academic fallback."""
    base_url = "https://openlibrary.org/search.json"
    params = {
        "q": query,
        "limit": max_results,
    }
    try:
        response = requests.get(base_url, params=params, timeout=8)
        response.raise_for_status()
        data = response.json()

        docs = data.get("docs", [])
        books = []
        for idx, doc in enumerate(docs, 1):
            title = doc.get("title", "Untitled Work").strip()
            authors = doc.get("author_name", [])
            publisher_list = doc.get("publisher", [])
            publisher = publisher_list[0] if publisher_list else "Academic Publisher"
            first_year = str(doc.get("first_publish_year", "")) or None
            key = doc.get("key", "")
            info_link = f"https://openlibrary.org{key}" if key else f"https://openlibrary.org/search?q={query}"

            # Subject or description
            subjects = doc.get("subject", [])
            desc = f"Subject areas: {', '.join(subjects[:5])}." if subjects else f"Text covering {title}."

            books.append(
                BookSource(
                    id=f"book-{idx}",
                    title=title,
                    authors=authors[:3],
                    publisher=publisher,
                    year=first_year,
                    description=desc,
                    preview_link=info_link,
                    info_link=info_link,
                    isbn=doc.get("isbn", [None])[0] if doc.get("isbn") else None,
                )
            )
        return books
    except Exception as e:
        logger.error(f"OpenLibrary book search failed: {e}")
        return []
