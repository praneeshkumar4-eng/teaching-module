"""
LessonForge - AI-Powered Lesson Creation Workstation for Teachers.
Main Streamlit application entry point.
"""
import streamlit as st

from config import config, reload_config, update_env_file
from core.llm import llm_client
from core.storage import list_all_lessons, load_lesson
from ui.styles import apply_custom_css
from ui.views.create_view import render_create_view
from ui.views.editor_view import render_editor_view
from ui.views.library_view import render_library_view
from ui.views.qc_view import render_qc_view
from ui.views.research_view import render_research_view

# Streamlit Page Configuration
st.set_page_config(
    page_title="LessonForge — AI Lesson Creation Suite",
    page_icon="⚒️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply global styling
st.markdown(apply_custom_css(), unsafe_allow_html=True)

# Initialize Session State
if "selected_nav" not in st.session_state:
    st.session_state.selected_nav = "➕ Create New Lesson"

if "active_lesson_id" not in st.session_state:
    # Auto-load most recent lesson if available
    recent_lessons = list_all_lessons()
    st.session_state.active_lesson_id = recent_lessons[0].id if recent_lessons else None


# -----------------------------------------------------------------------------
# Sidebar Navigation & Settings Panel
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## ⚒️ **LessonForge**")
    st.caption("Autonomous AI Lesson Creation Engine for Teachers")
    st.divider()

    # Active Lesson Quick Switcher
    all_lessons = list_all_lessons()
    if all_lessons:
        lesson_ids = [l.id for l in all_lessons]
        titles_map = {l.id: f"{l.title[:32]}... (v{l.current_version})" for l in all_lessons}

        current_idx = 0
        if st.session_state.active_lesson_id in lesson_ids:
            current_idx = lesson_ids.index(st.session_state.active_lesson_id)

        selected_id = st.selectbox(
            "Active Lesson",
            options=lesson_ids,
            index=current_idx,
            format_func=lambda x: titles_map.get(x, x),
            help="Select an existing lesson to view or edit.",
        )
        if selected_id != st.session_state.active_lesson_id:
            st.session_state.active_lesson_id = selected_id
            st.rerun()

    # Navigation Menu
    nav_options = [
        "➕ Create New Lesson",
        "📖 Lesson Workspace",
        "🔍 QC Verification Suite",
        "🌐 Research Dossier",
        "📚 Lesson Library",
    ]

    selected_nav = st.radio(
        "Navigation",
        options=nav_options,
        index=nav_options.index(st.session_state.selected_nav) if st.session_state.selected_nav in nav_options else 0,
        label_visibility="collapsed",
    )
    st.session_state.selected_nav = selected_nav

    st.divider()

    # AI & API Configuration
    with st.expander("⚙️ API Keys & AI Settings", expanded=not config.has_gemini_key):
        st.caption("Configure API keys for AI generation and research retrieval.")

        gemini_input = st.text_input(
            "Gemini API Key",
            value=config.gemini_api_key,
            type="password",
            help="Google Gemini API Key (Get at https://aistudio.google.com/)",
        )

        model_input = st.selectbox(
            "Gemini Model",
            options=["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"],
            index=0 if config.gemini_model == "gemini-2.5-flash" else 0,
        )

        tavily_input = st.text_input(
            "Tavily Search Key (Optional)",
            value=config.tavily_api_key,
            type="password",
            help="Web search API. If blank, DuckDuckGo + Trafilatura is used automatically.",
        )

        youtube_input = st.text_input(
            "YouTube API Key (Optional)",
            value=config.youtube_api_key,
            type="password",
            help="YouTube Data API v3 key for educational video search.",
        )

        col_save, col_test = st.columns(2)
        with col_save:
            if st.button("💾 Save Keys", use_container_width=True):
                update_env_file("GEMINI_API_KEY", gemini_input.strip())
                update_env_file("GEMINI_MODEL", model_input)
                update_env_file("TAVILY_API_KEY", tavily_input.strip())
                update_env_file("YOUTUBE_API_KEY", youtube_input.strip())
                llm_client.update_key_and_model(gemini_input.strip(), model_input)
                st.success("Configuration saved to .env!")
                st.rerun()

        with col_test:
            if st.button("🔌 Test AI", use_container_width=True):
                if not gemini_input.strip():
                    st.warning("Please enter a Gemini API Key first.")
                else:
                    llm_client.update_key_and_model(gemini_input.strip(), model_input)
                    success, msg = llm_client.test_connection()
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)

    # Status Footer
    st.write("")
    if config.has_gemini_key:
        st.markdown(
            f'<div style="font-size:0.75rem; color:#16a34a; font-weight:600;">'
            f'● Gemini Connected ({config.gemini_model})</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="font-size:0.75rem; color:#b45309; font-weight:600;">'
            '○ Offline Prototype Mode (Set GEMINI_API_KEY in Settings)</div>',
            unsafe_allow_html=True,
        )


# -----------------------------------------------------------------------------
# Main Application Content Router
# -----------------------------------------------------------------------------
active_package = None
if st.session_state.active_lesson_id:
    active_package = load_lesson(st.session_state.active_lesson_id)

if st.session_state.selected_nav == "➕ Create New Lesson":
    render_create_view()

elif st.session_state.selected_nav == "📚 Lesson Library":
    render_library_view()

elif not active_package:
    st.warning("No active lesson selected. Create a new lesson or choose one from the library.")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("➕ Create New Lesson", type="primary", use_container_width=True):
            st.session_state.selected_nav = "➕ Create New Lesson"
            st.rerun()
    with c2:
        if st.button("📚 Browse Lesson Library", use_container_width=True):
            st.session_state.selected_nav = "📚 Lesson Library"
            st.rerun()

elif st.session_state.selected_nav == "📖 Lesson Workspace":
    render_editor_view(active_package)

elif st.session_state.selected_nav == "🔍 QC Verification Suite":
    render_qc_view(active_package)

elif st.session_state.selected_nav == "🌐 Research Dossier":
    render_research_view(active_package)
