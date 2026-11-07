"""
Lesson Creation View for LessonForge.
Handles Step 1 (Inputs and Research) and Step 2 (Lesson Generation),
with validation, example loading, retry hooks, and real-time status updates.
"""
import time
import uuid
import streamlit as st

from core.models import LessonMetadata, LessonPackage, LessonVersion
from core.storage import save_new_lesson, slugify
from generator.lesson_generator import generate_structured_lesson
from qc.factual_checker import review_factual_accuracy
from qc.pedagogical_checker import review_teaching_quality
from research.aggregator import gather_research
from ui.components import render_access_badge, render_hero_header, render_progress_stepper

# Test example presets for quick demo
DEMO_EXAMPLES = {
    "Test 1: HTTP Protocols": {
        "title": "HTTP Requests and Responses",
        "objective": "Explain GET and POST methods and distinguish between 2xx, 4xx, and 5xx response status categories.",
    },
    "Test 2: Python Collections": {
        "title": "Python Lists and Tuples",
        "objective": "Explain the differences between lists and tuples and choose the appropriate collection for simple situations.",
    },
}


def render_create_view():
    """Renders Step 1 inputs, example pre-fillers, and pipeline coordinator."""
    render_hero_header()
    render_progress_stepper("Input")

    # Example pre-loaders for demo
    st.markdown("#### ⚡ Quick Demo Pre-Loaders")
    col_e1, col_e2, _ = st.columns([1.5, 1.5, 3])

    # Streamlit widget keys must match session_state keys directly so that
    # setting session_state before st.rerun() correctly pre-fills the widgets.
    if "input_title_key" not in st.session_state:
        st.session_state.input_title_key = ""
    if "input_obj_key" not in st.session_state:
        st.session_state.input_obj_key = ""

    with col_e1:
        if st.button("📋 Load Test 1: HTTP Protocol", use_container_width=True):
            # Set the SAME keys that the widgets below use — Streamlit will
            # read these on the next run and display them as the widget value.
            st.session_state.input_title_key = DEMO_EXAMPLES["Test 1: HTTP Protocols"]["title"]
            st.session_state.input_obj_key = DEMO_EXAMPLES["Test 1: HTTP Protocols"]["objective"]
            st.rerun()

    with col_e2:
        if st.button("📋 Load Test 2: Python Lists & Tuples", use_container_width=True):
            st.session_state.input_title_key = DEMO_EXAMPLES["Test 2: Python Collections"]["title"]
            st.session_state.input_obj_key = DEMO_EXAMPLES["Test 2: Python Collections"]["objective"]
            st.rerun()

    st.write("")

    # Lesson inputs form — keys match session_state keys so pre-loading works
    with st.container():
        title = st.text_input(
            "Lesson Title *",
            placeholder="e.g. HTTP Requests and Responses",
            help="A specific, clear title for your 45-minute lesson.",
            key="input_title_key",
        )

        objective = st.text_area(
            "Learning Objective *",
            placeholder="e.g. Explain GET and POST methods and distinguish between 2xx, 4xx, and 5xx response status categories.",
            help="Measurable SWBAT objective stating what students will master.",
            height=110,
            key="input_obj_key",
        )

        col_btn, _ = st.columns([2, 3])
        with col_btn:
            generate_clicked = st.button("🚀 Generate 45-Minute Grounded Lesson", type="primary", use_container_width=True)

    if generate_clicked:
        # STRICT VALIDATION: Do not call any API if blank
        title_stripped = title.strip()
        obj_stripped = objective.strip()

        if not title_stripped and not obj_stripped:
            st.error("❌ Validation Error: Lesson Title and Learning Objective are both required.")
            return
        elif not title_stripped:
            st.error("❌ Validation Error: Lesson Title is required.")
            return
        elif not obj_stripped:
            st.error("❌ Validation Error: Learning Objective is required.")
            return

        # Proceed to generation pipeline
        _execute_generation_pipeline(title_stripped, obj_stripped)


def _execute_generation_pipeline(title: str, objective: str):
    """Coordinates Step 1 research and Step 2 generation with independent retry buttons."""
    status_box = st.status("🔍 Step 1/5: Researching topic across Web, Books, and YouTube...", expanded=True)

    # -------------------------------------------------------------------------
    # Step 1: Research Retrieval
    # -------------------------------------------------------------------------
    dossier = None
    try:
        status_box.write("🌐 **Querying authoritative websites (MDN, W3C, RFCs, educational portals)...**")
        status_box.write("📚 **Querying academic books (Google Books / OpenLibrary)...**")
        status_box.write("▶️ **Searching YouTube and extracting real spoken transcripts...**")

        dossier = gather_research(title=title, objective=objective)

        if dossier.warnings:
            for w in dossier.warnings:
                status_box.warning(f"⚠️ Partial Research Warning: {w}")

        status_box.write(
            f"✅ **Research Complete:** Retrieved {len(dossier.sources)} normalized sources "
            f"(Full text: {sum(1 for s in dossier.sources if s.access_level.value == 'full_text')}, "
            f"Description only: {sum(1 for s in dossier.sources if s.access_level.value == 'description_only')})."
        )
    except Exception as e:
        status_box.update(label="❌ Step 1 (Research) Failed", state="error", expanded=True)
        st.error(f"Research Pipeline Error: {str(e)}")
        st.info("Your inputs have been preserved. You can retry research below.")
        if st.button("🔄 Retry Research", type="primary"):
            st.rerun()
        return

    # -------------------------------------------------------------------------
    # Step 2: Lesson Generation
    # -------------------------------------------------------------------------
    structured_plan = None
    lesson_markdown = None
    try:
        status_box.write("✍️ **Step 2/5: Drafting 45-minute lesson plan...**")
        status_box.caption("Enforcing exact 45-minute budget (3, 7, 10, 8, 5, 7, 5 min) and citation integrity [S#]...")

        structured_plan, lesson_markdown = generate_structured_lesson(
            title=title,
            objective=objective,
            dossier=dossier,
        )
        status_box.write("✅ **Lesson Generated:** 7 required sections drafted with exact 45-minute budget.")
    except Exception as e:
        status_box.update(label="❌ Step 2 (Lesson Generation) Failed", state="error", expanded=True)
        st.error(f"Generation Error: {str(e)}")
        st.info("Research is already cached. You can retry lesson generation without re-fetching sources.")
        if st.button("🔄 Retry Generation", type="primary"):
            st.rerun()
        return

    # -------------------------------------------------------------------------
    # Step 3: QC Layer 1 (Factual Accuracy)
    # -------------------------------------------------------------------------
    qc_factual = None
    try:
        status_box.write("🔍 **Step 3/5: Running QC Layer 1 (Factual Accuracy Audit)...**")
        status_box.caption("Auditing claims against retrieved research and running deterministic URL/citation checks...")
        qc_factual = review_factual_accuracy(lesson_markdown, dossier)
        status_box.write(f"✅ **QC Layer 1 Complete:** Verdict: {qc_factual.verdict} ({len(qc_factual.issues)} issues identified).")
    except Exception as e:
        status_box.update(label="❌ Step 3 (QC 1) Failed", state="error", expanded=True)
        st.error(f"QC Layer 1 Error: {str(e)}")
        if st.button("🔄 Retry QC 1"):
            st.rerun()
        return

    # -------------------------------------------------------------------------
    # Step 4: QC Layer 2 (Teaching Quality)
    # -------------------------------------------------------------------------
    qc_pedagogical = None
    try:
        status_box.write("🎓 **Step 4/5: Running QC Layer 2 (Teaching Quality & Pedagogy)...**")
        status_box.caption("Evaluating objective coverage part-by-part, activity feasibility, and question alignment...")
        qc_pedagogical = review_teaching_quality(lesson_markdown, objective)
        status_box.write(f"✅ **QC Layer 2 Complete:** Verdict: {qc_pedagogical.verdict} ({len(qc_pedagogical.issues)} recommendations).")
    except Exception as e:
        status_box.update(label="❌ Step 4 (QC 2) Failed", state="error", expanded=True)
        st.error(f"QC Layer 2 Error: {str(e)}")
        if st.button("🔄 Retry QC 2"):
            st.rerun()
        return

    # -------------------------------------------------------------------------
    # Step 5: Packaging & Persistence
    # -------------------------------------------------------------------------
    try:
        status_box.write("💾 **Step 5/5: Assembling package and atomic disk save...**")
        lesson_id = f"{slugify(title)}-{uuid.uuid4().hex[:6]}"
        metadata = LessonMetadata(
            id=lesson_id,
            title=title,
            objective=objective,
            current_version=1,
            total_versions=1,
        )
        package = LessonPackage(
            metadata=metadata,
            markdown_content=lesson_markdown,
            research_dossier=dossier,
            structured_lesson=structured_plan,
            qc_factual=qc_factual,
            qc_pedagogical=qc_pedagogical,
            versions=[LessonVersion(version_number=1, note="Initial generation", content=lesson_markdown)],
        )

        save_new_lesson(package)
        status_box.update(label="🎉 Complete Lesson Package Created Successfully!", state="complete", expanded=False)

        st.session_state.active_lesson_id = lesson_id
        st.session_state.active_tab = "Lesson"
        st.session_state.selected_nav = "📖 Lesson Workspace"
        st.success(f"Lesson '{title}' saved to data/lessons/{lesson_id}/. Opening workspace...")
        st.rerun()

    except Exception as e:
        status_box.update(label="❌ Step 5 (Save) Failed", state="error", expanded=True)
        st.error(f"Storage Error: {str(e)}")
