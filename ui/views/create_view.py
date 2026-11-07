"""
Lesson Creation View for LessonForge.
Teacher enters Title and Learning Objective; pipeline researches topic across
Web, Books, and YouTube, generates 45-minute grounded lesson, and runs QC 1 & 2.
"""
import time
import uuid
import streamlit as st

from core.models import LessonMetadata, LessonPackage, LessonVersion
from core.storage import save_new_lesson, slugify
from generator.lesson_generator import generate_lesson_plan
from qc.factual_checker import review_factual_accuracy
from qc.pedagogical_checker import review_teaching_quality
from research.aggregator import gather_research
from ui.components import render_header


def render_create_view():
    """Renders the lesson input form and coordinates the generation pipeline."""
    render_header(
        title="Create New Lesson",
        subtitle="Provide a topic and objective. LessonForge retrieves real sources, authors a 45-minute lesson, and audits accuracy and pedagogy.",
    )

    with st.form("lesson_creation_form"):
        st.subheader("1. Lesson Objectives & Core Topic")
        col1, col2 = st.columns([3, 2])

        with col1:
            title = st.text_input(
                "Lesson Title *",
                placeholder="e.g. Photosynthesis: Light-Dependent Reactions & Cellular Energy",
                help="A clear, specific title for your 45-minute classroom lesson.",
            )

        with col2:
            subject = st.selectbox(
                "Subject / Discipline",
                options=[
                    "General Science",
                    "Biology & Life Sciences",
                    "Physics",
                    "Chemistry",
                    "History & Social Studies",
                    "Mathematics",
                    "Computer Science & AI",
                    "English & Literature",
                    "Economics & Civics",
                    "Environmental Science",
                    "Other / Interdisciplinary",
                ],
                index=1,
            )

        objective = st.text_area(
            "Learning Objective (SWBAT - Students Will Be Able To) *",
            placeholder="e.g. SWBAT explain how photons excite chlorophyll electrons in Photosystem II, trace the flow of electrons through the thylakoid membrane, and predict how light deprivation halts ATP synthesis.",
            help="Specify a measurable outcome using action verbs from Bloom's Taxonomy.",
            height=100,
        )

        st.subheader("2. Classroom Parameters & Scaffolds")
        col3, col4 = st.columns(2)

        with col3:
            grade_level = st.selectbox(
                "Target Grade Level",
                options=[
                    "Grade 6-8 (Middle School)",
                    "Grade 9-10 (Early High School)",
                    "Grade 11-12 (Advanced / AP)",
                    "Undergraduate / Introductory College",
                    "Adult & Vocational Education",
                ],
                index=1,
            )

        with col4:
            duration = st.selectbox(
                "Class Duration",
                options=["45 Minutes (Standard Class Period)"],
                index=0,
                disabled=True,
                help="LessonForge specializes in rigorous 45-minute bell-to-bell lesson design.",
            )

        extra_instructions = st.text_input(
            "Curriculum Standard or Special Instructions (Optional)",
            placeholder="e.g. NGSS HS-LS1-5; include an active 15-minute hands-on card-sort activity.",
        )

        submitted = st.form_submit_button("🚀 Generate 45-Minute Grounded Lesson", use_container_width=True)

    if submitted:
        if not title.strip():
            st.error("Please enter a Lesson Title.")
            return
        if not objective.strip():
            st.error("Please enter a measurable Learning Objective.")
            return

        _execute_generation_pipeline(
            title=title.strip(),
            objective=objective.strip(),
            subject=subject,
            grade_level=grade_level,
            extra_instructions=extra_instructions.strip(),
        )


def _execute_generation_pipeline(
    title: str,
    objective: str,
    subject: str,
    grade_level: str,
    extra_instructions: str,
):
    """Executes the autonomous 5-step lesson synthesis & QC pipeline with live status updates."""
    status_container = st.status("🛠️ Assembling your grounded lesson package...", expanded=True)

    try:
        # Step 1: Research Retrieval
        status_container.write("🌐 **Step 1/5: Retrieving external research...**")
        status_container.caption("Querying Web sources (Tavily/DDG + Trafilatura), Academic Books (Google Books/OpenLibrary), and YouTube transcripts...")
        start_time = time.time()
        dossier = gather_research(title=title, objective=objective, subject=subject)
        status_container.write(
            f"✅ Retrieved {len(dossier.web_sources)} web sources, "
            f"{len(dossier.book_sources)} academic books, "
            f"{len(dossier.video_sources)} educational videos."
        )

        # Step 2: Grounded Lesson Generation
        status_container.write("✍️ **Step 2/5: Authoring 45-minute lesson plan...**")
        status_container.caption("Enforcing strict grounding on retrieved research dossier with inline citations [Web X], [Book Y], [Video Z]...")
        lesson_markdown = generate_lesson_plan(
            title=title,
            objective=objective,
            dossier=dossier,
            grade_level=grade_level,
            subject=subject,
            extra_instructions=extra_instructions,
        )
        status_container.write("✅ 45-minute structured agenda, teacher script, and activities drafted.")

        # Step 3: QC Layer 1 - Factual Accuracy Review
        status_container.write("🔍 **Step 3/5: Running QC Layer 1 (Factual Accuracy & Hallucination Audit)...**")
        status_container.caption("Cross-examining all factual claims and definitions against the research dossier...")
        qc_factual = review_factual_accuracy(lesson_markdown=lesson_markdown, dossier=dossier)
        status_container.write(
            f"✅ QC Layer 1 Complete: Score {qc_factual.overall_score}/100 ({qc_factual.status}) — "
            f"{qc_factual.verified_count} verified, {qc_factual.unsupported_count} unsupported claims."
        )

        # Step 4: QC Layer 2 - Pedagogical Review
        status_container.write("🎓 **Step 4/5: Running QC Layer 2 (Pedagogical & Instructional Review)...**")
        status_container.caption("Evaluating 45-minute pacing, Bloom's objective alignment, active learning ratio, and differentiation...")
        qc_pedagogical = review_teaching_quality(
            lesson_markdown=lesson_markdown,
            objective=objective,
            grade_level=grade_level,
        )
        status_container.write(
            f"✅ QC Layer 2 Complete: Score {qc_pedagogical.overall_score}/100 ({qc_pedagogical.status}) — "
            f"{len(qc_pedagogical.recommendations)} actionable recommendations generated."
        )

        # Step 5: Persistence & Packaging
        status_container.write("💾 **Step 5/5: Persisting lesson bundle and version v1...**")
        lesson_id = f"{slugify(title)}-{uuid.uuid4().hex[:6]}"
        metadata = LessonMetadata(
            id=lesson_id,
            title=title,
            objective=objective,
            grade_level=grade_level,
            subject=subject,
            duration_minutes=45,
            current_version=1,
            total_versions=1,
        )
        package = LessonPackage(
            metadata=metadata,
            markdown_content=lesson_markdown,
            research_dossier=dossier,
            qc_factual=qc_factual,
            qc_pedagogical=qc_pedagogical,
            versions=[
                LessonVersion(
                    version_number=1,
                    note="Initial generation",
                    content=lesson_markdown,
                )
            ],
        )

        save_new_lesson(package)
        status_container.update(
            label=f"🎉 Lesson Successfully Created in {int(time.time() - start_time)}s!",
            state="complete",
            expanded=False,
        )

        # Save to session state and trigger rerun to active view
        st.session_state.active_lesson_id = lesson_id
        st.session_state.selected_nav = "📖 Lesson Workspace"
        st.success("Your complete lesson package is ready! Opening Lesson Workspace...")
        st.rerun()

    except Exception as e:
        status_container.update(label="❌ Generation Failed", state="error", expanded=True)
        st.error(f"Error during lesson generation: {str(e)}")
