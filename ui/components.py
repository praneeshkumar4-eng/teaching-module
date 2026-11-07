"""
Reusable UI components for LessonForge.
Implements the Hero Header, Progress Stepper, Altair Timing Stacked Bar,
Access Level Badges, QC Metric Summaries, and Diff Viewers.
"""
import difflib
from typing import Dict, List, Optional
import altair as alt
import pandas as pd
import streamlit as st

from core.models import AccessLevel


def render_hero_header():
    """Renders the eye-catching SaaS hero header banner."""
    st.markdown(
        """
        <div class="lf-hero-banner">
          <div class="lf-hero-title">
            <span>⚒️</span> LessonForge
          </div>
          <div class="lf-hero-tagline">
            <span>Research. Teach. Verify.</span> — Autonomous AI Lesson Creation Suite for Teachers
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_header(title: str = "LessonForge", subtitle: str = "", badge: Optional[str] = None):
    """Renders a branded page banner for views."""
    sub_text = subtitle if subtitle else "<span>Research. Teach. Verify.</span> — Autonomous AI Lesson Creation Suite"
    st.markdown(
        f"""
        <div class="lf-hero-banner">
          <div class="lf-hero-title">
            <span>⚒️</span> {title}
          </div>
          <div class="lf-hero-tagline">
            {sub_text}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )



def render_progress_stepper(current_step: str = "Input"):
    """
    Renders the 6-stage workflow stepper:
    Input -> Research -> Lesson -> QC Accuracy -> QC Teaching -> Edit & Export
    """
    steps = [
        ("Input", "1"),
        ("Research", "2"),
        ("Lesson", "3"),
        ("QC Accuracy", "4"),
        ("QC Teaching", "5"),
        ("Edit & Export", "6"),
    ]

    # Determine step indices
    step_names = [s[0] for s in steps]
    cur_idx = step_names.index(current_step) if current_step in step_names else 0

    items_html = []
    for idx, (name, num) in enumerate(steps):
        if idx < cur_idx:
            status_class = "completed"
            symbol = "✓"
        elif idx == cur_idx:
            status_class = "active"
            symbol = num
        else:
            status_class = "pending"
            symbol = num

        items_html.append(
            f"""
            <div class="lf-step-item {status_class}">
              <div class="lf-step-circle">{symbol}</div>
              <span>{name}</span>
            </div>
            """
        )
        if idx < len(steps) - 1:
            div_class = "filled" if idx < cur_idx else ""
            items_html.append(f'<div class="lf-step-divider {div_class}"></div>')

    full_stepper = "".join(items_html)
    st.markdown(
        f'<div class="lf-stepper-container">{full_stepper}</div>',
        unsafe_allow_html=True,
    )


def render_timing_visual(sections_data: List[Dict]):
    """
    Renders an Altair horizontal stacked bar representing the 45-minute breakdown
    with colored segments and a '45 / 45 min' badge.
    """
    if not sections_data:
        return

    df = pd.DataFrame(sections_data)
    total_mins = df["minutes"].sum() if "minutes" in df.columns else 45

    col_title, col_badge = st.columns([4, 1])
    with col_title:
        st.markdown("#### ⏱️ Lesson Pacing Timeline (45-Minute Bell-to-Bell Split)")
    with col_badge:
        st.markdown(
            f'<div style="text-align:right;"><span class="lf-timing-badge">⏱️ {total_mins} / 45 Min</span></div>',
            unsafe_allow_html=True,
        )

    # Altair Horizontal Stacked Bar Chart
    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadius=4, height=36)
        .encode(
            x=alt.X("minutes:Q", title="Classroom Minutes", scale=alt.Scale(domain=[0, 45])),
            color=alt.Color(
                "title:N",
                title="Section",
                scale=alt.Scale(scheme="tableau10"),
                legend=alt.Legend(orient="bottom", columns=3, labelLimit=250),
            ),
            tooltip=[
                alt.Tooltip("title:N", title="Section"),
                alt.Tooltip("minutes:Q", title="Minutes"),
                alt.Tooltip("word_count:Q", title="Estimated Words"),
                alt.Tooltip("timing_feasibility:N", title="Feasibility"),
            ],
        )
        .properties(height=70)
        .configure_view(strokeWidth=0)
    )

    st.altair_chart(chart, use_container_width=True)


def render_access_badge(access_level: AccessLevel) -> str:
    """Returns HTML for access badge with mandatory explicit explanation."""
    if access_level == AccessLevel.FULL_TEXT:
        return '<span class="lf-access-badge-full">✓ Full Text Verified</span>'
    else:
        return (
            '<span class="lf-access-badge-desc">⚠️ Description Only</span> '
            '<span style="font-size:0.75rem; color:#b45309; font-style:italic;">'
            '(Only the description was available. This source was NOT read or watched in full.)</span>'
        )


def render_diff_viewer(before_text: str, after_text: str):
    """Renders a visual inline diff comparison between two text versions."""
    diff = list(difflib.ndiff(before_text.splitlines(keepends=True), after_text.splitlines(keepends=True)))

    diff_html_lines = []
    for line in diff:
        clean = line[2:].rstrip("\n").replace("<", "&lt;").replace(">", "&gt;")
        if line.startswith("- "):
            diff_html_lines.append(f'<div class="diff-del">- {clean}</div>')
        elif line.startswith("+ "):
            diff_html_lines.append(f'<div class="diff-add">+ {clean}</div>')
        elif line.startswith("? "):
            continue
        else:
            diff_html_lines.append(f'<div style="color:#64748b; font-size:0.88rem; padding:1px 0;">  {clean}</div>')

    full_diff = "".join(diff_html_lines[:150])  # Cap preview length
    st.markdown(
        f"""
        <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:14px; max-height:400px; overflow-y:auto; font-family:monospace; line-height:1.4;">
          {full_diff}
        </div>
        """,
        unsafe_allow_html=True,
    )
