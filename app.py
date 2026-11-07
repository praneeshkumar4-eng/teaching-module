"""
LessonForge — Autonomous AI Lesson Creation Suite for Teachers.
Main Streamlit application entry point.
"""
import streamlit as st

from config import config, reload_config, update_env_file
from core.llm import get_simulated_failure, llm_client, set_simulated_failure
from core.storage import list_all_lessons, load_lesson
from ui.styles import apply_custom_css
from ui.views.create_view import render_create_view
from ui.views.editor_view import render_editor_view
from ui.views.library_view import render_library_view

# Streamlit Page Configuration
st.set_page_config(
    page_title="LessonForge — AI Lesson Creation Suite",
    page_icon="⚒️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject custom modern SaaS CSS
st.markdown(apply_custom_css(), unsafe_allow_html=True)

# Initialize Session State
if "selected_nav" not in st.session_state:
    st.session_state.selected_nav = "➕ Create New Lesson"

if "active_lesson_id" not in st.session_state:
    recent_lessons = list_all_lessons()
    st.session_state.active_lesson_id = recent_lessons[0].id if recent_lessons else None


# -----------------------------------------------------------------------------
# Sidebar: Navigation, Saved Lessons, Settings & Simulation Mode
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## ⚒️ **LessonForge**")
    st.caption("Research. Teach. Verify. • 45-Minute Lesson Suite")
    st.divider()

    # Primary Navigation
    nav_options = [
        "➕ Create New Lesson",
        "📖 Lesson Workspace",
        "📚 Saved Lessons Library",
    ]
    selected_nav = st.radio(
        "Navigation",
        options=nav_options,
        index=nav_options.index(st.session_state.selected_nav) if st.session_state.selected_nav in nav_options else 0,
        label_visibility="collapsed",
    )
    st.session_state.selected_nav = selected_nav

    st.divider()

    # Saved Lessons Quick Switcher
    st.markdown("#### 📂 Reopen Saved Lesson")
    all_lessons = list_all_lessons()
    if all_lessons:
        lesson_ids = [l.id for l in all_lessons]
        titles_map = {l.id: f"{l.title[:28]}... (v{l.current_version})" for l in all_lessons}

        current_idx = 0
        if st.session_state.active_lesson_id in lesson_ids:
            current_idx = lesson_ids.index(st.session_state.active_lesson_id)

        selected_id = st.selectbox(
            "Select Lesson",
            options=lesson_ids,
            index=current_idx,
            format_func=lambda x: titles_map.get(x, x),
            label_visibility="collapsed",
        )
        if selected_id != st.session_state.active_lesson_id:
            st.session_state.active_lesson_id = selected_id
            st.session_state.selected_nav = "📖 Lesson Workspace"
            st.rerun()
    else:
        st.caption("No lessons saved yet.")

    st.divider()

    # Developer Mode: Failure Simulation Toggle for Demo Video
    with st.expander("🧪 Developer Mode (Simulate Failure)", expanded=False):
        st.caption("Demonstrate error handling and recovery buttons in your demo video.")
        sim_choice = st.selectbox(
            "Simulate Error Condition",
            options=[
                "None (Normal Operation)",
                "Research Pipeline Failure",
                "AI Generation Failure",
                "QC Layer 1 Failure",
                "QC Layer 2 Failure",
                "Malformed LLM JSON",
            ],
            index=0,
            key="sim_failure_select",
        )

        mapping = {
            "None (Normal Operation)": None,
            "Research Pipeline Failure": "research",
            "AI Generation Failure": "generation",
            "QC Layer 1 Failure": "qc1",
            "QC Layer 2 Failure": "qc2",
            "Malformed LLM JSON": "malformed_json",
        }
        set_simulated_failure(mapping[sim_choice])
        if sim_choice != "None (Normal Operation)":
            st.warning(f"⚠️ Active Failure Simulation: {sim_choice}")

    # API Keys & AI Settings Panel
    with st.expander("⚙️ API Keys & AI Settings", expanded=not config.has_gemini_key):
        st.caption("Configure keys for Gemini, Tavily, and YouTube.")

        gemini_input = st.text_input(
            "Gemini API Key",
            value=config.gemini_api_key,
            type="password",
            help="Google Gemini API Key (Get at https://aistudio.google.com/)",
        )

        model_input = st.selectbox(
            "Gemini Model",
            options=["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"],
            index=0,
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
            help="YouTube Data API v3 key. If blank, DuckDuckGo video search is used automatically.",
        )

        col_save, col_test = st.columns(2)
        with col_save:
            if st.button("💾 Save Keys", use_container_width=True):
                update_env_file("GEMINI_API_KEY", gemini_input.strip())
                update_env_file("GEMINI_MODEL", model_input)
                update_env_file("TAVILY_API_KEY", tavily_input.strip())
                update_env_file("YOUTUBE_API_KEY", youtube_input.strip())
                llm_client.update_key_and_model(gemini_input.strip(), model_input)
                st.success("Configuration saved!")
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
            f'● Gemini Active ({config.gemini_model})</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="font-size:0.75rem; color:#b45309; font-weight:600;">'
            '○ Offline Prototype Mode (Set GEMINI_API_KEY to switch to live Gemini)</div>',
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

elif st.session_state.selected_nav == "📚 Saved Lessons Library":
    render_library_view()

elif not active_package:
    st.warning("No active lesson selected. Please create a new lesson or choose one from the library.")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("➕ Create New Lesson", type="primary", use_container_width=True):
            st.session_state.selected_nav = "➕ Create New Lesson"
            st.rerun()
    with c2:
        if st.button("📚 Browse Lesson Library", use_container_width=True):
            st.session_state.selected_nav = "📚 Saved Lessons Library"
            st.rerun()

elif st.session_state.selected_nav == "📖 Lesson Workspace":
    render_editor_view(active_package)
