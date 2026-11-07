"""
YouTube video and transcript research module for LessonForge.
Queries YouTube Data API v3 when YOUTUBE_API_KEY is present (with resilient DDG video fallback),
and extracts spoken transcripts using youtube-transcript-api. Never invents links.
"""
import logging
import re
from typing import List, Optional
import requests
from youtube_transcript_api import YouTubeTranscriptApi

from config import config
from core.models import VideoSource

logger = logging.getLogger(__name__)

# Try ddgs first, fallback to duckduckgo_search
try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        DDGS = None


def search_youtube(query: str, max_results: int = 3) -> List[VideoSource]:
    """
    Retrieves educational videos and extracts spoken transcripts.
    Tries YouTube Data API v3 first if YOUTUBE_API_KEY is provided;
    otherwise uses DuckDuckGo video search.
    """
    if config.has_youtube_key:
        try:
            videos = _search_youtube_api(query, max_results=max_results)
            if videos:
                logger.info(f"Retrieved {len(videos)} videos via YouTube Data API v3.")
                return _enrich_with_transcripts(videos)
        except Exception as e:
            logger.warning(f"YouTube Data API failed: {e}. Falling back to DuckDuckGo videos.")

    # Fallback to DuckDuckGo video search
    videos = _search_youtube_ddg(query, max_results=max_results)
    return _enrich_with_transcripts(videos)


def _search_youtube_api(query: str, max_results: int = 3) -> List[VideoSource]:
    """Queries YouTube Data API v3."""
    search_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": f"{query} lesson explanation",
        "type": "video",
        "maxResults": max_results,
        "key": config.youtube_api_key,
        "safeSearch": "moderate",
    }
    response = requests.get(search_url, params=params, timeout=8)
    response.raise_for_status()
    data = response.json()

    items = data.get("items", [])
    if not items:
        return []

    video_ids = [item["id"]["videoId"] for item in items if "videoId" in item.get("id", {})]

    # Fetch duration from contentDetails
    durations = {}
    if video_ids:
        try:
            video_url = "https://www.googleapis.com/youtube/v3/videos"
            v_params = {
                "part": "contentDetails",
                "id": ",".join(video_ids),
                "key": config.youtube_api_key,
            }
            v_resp = requests.get(video_url, params=v_params, timeout=8)
            if v_resp.ok:
                for v_item in v_resp.json().get("items", []):
                    dur_iso = v_item.get("contentDetails", {}).get("duration", "")
                    durations[v_item["id"]] = _format_iso_duration(dur_iso)
        except Exception as e:
            logger.debug(f"Could not fetch video durations: {e}")

    results = []
    for idx, item in enumerate(items, 1):
        vid_id = item.get("id", {}).get("videoId")
        if not vid_id:
            continue
        snippet = item.get("snippet", {})
        title = snippet.get("title", "Educational Video")
        channel = snippet.get("channelTitle", "YouTube Educator")
        desc = snippet.get("description", "")
        url = f"https://www.youtube.com/watch?v={vid_id}"

        results.append(
            VideoSource(
                id=f"video-{idx}",
                title=title,
                channel=channel,
                video_id=vid_id,
                url=url,
                description=desc[:500],
                duration=durations.get(vid_id, "10:00"),
            )
        )
    return results


def _search_youtube_ddg(query: str, max_results: int = 3) -> List[VideoSource]:
    """Extracts YouTube video candidates using DuckDuckGo search."""
    if DDGS is None:
        return []

    results = []
    # Try DDG videos first
    try:
        with DDGS() as ddgs:
            raw_videos = list(ddgs.videos(f"{query} educational", max_results=max_results + 2))
            for item in raw_videos:
                content_url = item.get("content", "")
                vid_id = _extract_video_id(content_url)
                if not vid_id:
                    continue
                results.append(
                    VideoSource(
                        id=f"video-{len(results) + 1}",
                        title=item.get("title", f"Video {len(results) + 1}").strip(),
                        channel=item.get("publisher", "YouTube Educator"),
                        video_id=vid_id,
                        url=f"https://www.youtube.com/watch?v={vid_id}",
                        description=item.get("description", "")[:500],
                        duration=item.get("duration", "10:00"),
                    )
                )
                if len(results) >= max_results:
                    break
    except Exception as e:
        logger.debug(f"DDGS.videos failed or yielded empty: {e}")

    # If no videos found yet, search DDGS text for site:youtube.com
    if not results:
        try:
            with DDGS() as ddgs:
                raw_text_hits = list(ddgs.text(f"site:youtube.com {query} educational lesson", max_results=max_results + 3))
                for item in raw_text_hits:
                    href = item.get("href", "")
                    vid_id = _extract_video_id(href)
                    if not vid_id:
                        continue
                    results.append(
                        VideoSource(
                            id=f"video-{len(results) + 1}",
                            title=item.get("title", f"Educational Video {len(results) + 1}").strip(),
                            channel="YouTube Educator",
                            video_id=vid_id,
                            url=f"https://www.youtube.com/watch?v={vid_id}",
                            description=item.get("body", "")[:500],
                            duration="10:00",
                        )
                    )
                    if len(results) >= max_results:
                        break
        except Exception as e:
            logger.error(f"DDGS site:youtube.com search failed: {e}")

    return results


def _enrich_with_transcripts(videos: List[VideoSource]) -> List[VideoSource]:
    """Fetches real transcripts for video IDs using youtube-transcript-api."""
    for video in videos:
        try:
            # Check available transcript
            transcript_list = YouTubeTranscriptApi.get_transcript(
                video.video_id,
                languages=["en", "en-US", "en-GB", "es", "auto"]
            )
            full_text = " ".join([t["text"].strip() for t in transcript_list if t.get("text")])
            if full_text:
                video.transcript_available = True
                video.transcript_excerpt = full_text[:400]
                video.full_transcript = full_text[:3500]  # Cap to keep context compact
                logger.info(f"Successfully retrieved transcript for video {video.video_id}")
        except Exception as e:
            logger.debug(f"Transcript unavailable for video {video.video_id}: {e}")
            video.transcript_available = False
            video.transcript_excerpt = ""
            video.full_transcript = None
    return videos


def _extract_video_id(url: str) -> Optional[str]:
    """Extracts 11-character YouTube video ID from URL."""
    if not url:
        return None
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"youtu\.be\/([0-9A-Za-z_-]{11})",
        r"youtube\.com\/embed\/([0-9A-Za-z_-]{11})"
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def _format_iso_duration(iso_duration: str) -> str:
    """Converts ISO 8601 duration (e.g. PT14M32S) to mm:ss."""
    if not iso_duration.startswith("PT"):
        return "10:00"
    duration = iso_duration[2:]
    hours, minutes, seconds = 0, 0, 0
    if "H" in duration:
        hours_part, duration = duration.split("H")
        hours = int(hours_part)
    if "M" in duration:
        mins_part, duration = duration.split("M")
        minutes = int(mins_part)
    if "S" in duration:
        secs_part = duration.replace("S", "")
        seconds = int(secs_part)

    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"
