"""
Reusable UI components for LessonForge.
"""
import streamlit as st
from typing import Optional


def render_header(
    title: str = "LessonForge",
    subtitle: str = "AI-Powered Research & Lesson Creation Engine for Teachers",
    badge: Optional[str] = None
):
    """Renders the top branded hero header."""
    badge_html = f'<span style="background:rgba(255,255,255,0.2); padding:3px 10px; border-radius:12px; font-size:0.75rem; margin-left:12px; vertical-align:middle;">{badge}</span>' if badge else ""
    st.markdown(
        f"""
        <div class="lf-header-card">
          <h1 class="lf-header-title">⚒️ {title} {badge_html}</h1>
          <p class="lf-header-sub">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_score_card(score: int, label: str, status: str = "PASS", color: Optional[str] = None):
    """Renders a metric score card with color coding."""
    if not color:
        if score >= 90:
            color = "#10b981"  # Emerald
        elif score >= 75:
            color = "#f59e0b"  # Amber
        else:
            color = "#ef4444"  # Rose

    st.markdown(
        f"""
        <div class="lf-metric-card">
          <div class="lf-metric-score" style="color: {color};">{score}%</div>
          <div class="lf-metric-label">{label}</div>
          <div style="margin-top: 6px;">
            <span class="lf-badge {'lf-badge-pass' if score>=85 else 'lf-badge-warn'}">{status}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_source_badge(source_type: str, count: int):
    """Renders small badge indicating count of sources."""
    badge_class = {
        "web": "lf-badge-web",
        "book": "lf-badge-book",
        "video": "lf-badge-video"
    }.get(source_type.lower(), "lf-badge-web")

    icon = {
        "web": "🌐",
        "book": "📚",
        "video": "▶️"
    }.get(source_type.lower(), "📄")

    st.markdown(
        f"""
        <span class="lf-badge {badge_class}">
          {icon} {count} {source_type.title()} Sources
        </span>
        """,
        unsafe_allow_html=True,
    )
