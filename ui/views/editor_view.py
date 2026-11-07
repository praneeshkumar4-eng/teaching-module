"""
Interactive Lesson Workspace & Editor View for LessonForge.
Provides live formatted preview, direct Markdown editing, version rollback,
and one-click downloads in Markdown, HTML, and ZIP.
"""
import streamlit as st

from core.exporter import build_lesson_zip_bundle, generate_styled_html
from core.models import LessonPackage
from core.storage import load_lesson, revert_to_version, save_lesson_version


def render_editor_view(package: LessonPackage):
    """Renders the comprehensive workspace for reading, editing, and exporting a lesson."""
    # Top Action Toolbar
    col_meta, col_actions = st.columns([3, 2])

    with col_meta:
        st.markdown(f"### {package.metadata.title}")
        st.caption(
            f"**Subject:** {package.metadata.subject} • "
            f"**Grade:** {package.metadata.grade_level} • "
            f"**Duration:** {package.metadata.duration_minutes} Mins • "
            f"**Active Version:** `v{package.metadata.current_version}`"
        )

    with col_actions:
        # Download buttons row
        btn_col1, btn_col2, btn_col3 = st.columns(3)

        # 1. Download Markdown
        with btn_col1:
            st.download_button(
                label="📄 .md",
                data=package.markdown_content,
                file_name=f"{package.metadata.id}.md",
                mime="text/markdown",
                help="Download plain Markdown file",
                use_container_width=True,
            )

        # 2. Download Styled HTML
        with btn_col2:
            html_content = generate_styled_html(
                lesson_markdown=package.markdown_content,
                title=package.metadata.title,
                subtitle=f"{package.metadata.grade_level} • {package.metadata.subject}",
            )
            st.download_button(
                label="🌐 .html",
                data=html_content,
                file_name=f"{package.metadata.id}.html",
                mime="text/html",
                help="Download print-formatted HTML page",
                use_container_width=True,
            )

        # 3. Download Full ZIP bundle
        with btn_col3:
            zip_bytes = build_lesson_zip_bundle(package)
            st.download_button(
                label="📦 .zip Bundle",
                data=zip_bytes,
                file_name=f"{package.metadata.id}_package.zip",
                mime="application/zip",
                help="Download complete ZIP containing Markdown, HTML, research dossier, and QC reports",
                use_container_width=True,
            )

    # QC Quick Metric Pill Bar
    if package.qc_factual or package.qc_pedagogical:
        pcol1, pcol2, pcol3, pcol4 = st.columns(4)
        if package.qc_factual:
            with pcol1:
                st.metric(
                    label="QC 1: Factual Accuracy",
                    value=f"{package.qc_factual.overall_score}%",
                    delta=package.qc_factual.status,
                    delta_color="normal" if package.qc_factual.overall_score >= 85 else "inverse",
                )
            with pcol2:
                st.metric(
                    label="Verified Claims",
                    value=f"{package.qc_factual.verified_count}",
                    delta=f"{package.qc_factual.unsupported_count} uncited",
                    delta_color="off",
                )
        if package.qc_pedagogical:
            with pcol3:
                st.metric(
                    label="QC 2: Teaching Quality",
                    value=f"{package.qc_pedagogical.overall_score}%",
                    delta=package.qc_pedagogical.status,
                    delta_color="normal" if package.qc_pedagogical.overall_score >= 85 else "inverse",
                )
            with pcol4:
                st.metric(
                    label="Pedagogical Fixes",
                    value=f"{len(package.qc_pedagogical.recommendations)}",
                    delta="Available in QC tab",
                    delta_color="off",
                )
        st.divider()

    # Workspace Tabs: Preview, Direct Edit, Version History
    tab_preview, tab_edit, tab_history = st.tabs([
        "📖 Classroom Guide (Preview)",
        "✏️ Direct Markdown Editor",
        f"🕒 Version History ({len(package.versions)} Saved)",
    ])

    with tab_preview:
        st.markdown(package.markdown_content)

    with tab_edit:
        st.info("💡 You can refine any portion of the lesson plan below. Clicking **Save as New Version** will snapshot the current version into your version history.")

        edited_content = st.text_area(
            "Lesson Plan Markdown Content",
            value=package.markdown_content,
            height=580,
            key=f"editor_text_{package.metadata.id}_{package.metadata.current_version}",
        )

        col_save_note, col_save_btn = st.columns([3, 1])
        with col_save_note:
            save_note = st.text_input(
                "Version Changelog Note",
                value="Teacher manual edits",
                placeholder="e.g. Scaffolds added to guided practice",
                key="version_note_input",
            )
        with col_save_btn:
            st.write("")  # Spacing
            if st.button("💾 Save as New Version", type="primary", use_container_width=True):
                new_ver = save_lesson_version(
                    lesson_id=package.metadata.id,
                    new_content=edited_content,
                    note=save_note,
                )
                st.success(f"Version v{new_ver} saved successfully!")
                st.rerun()

    with tab_history:
        st.subheader("Historical Version Snapshots")
        st.caption("Every edit and applied QC recommendation creates an immutable snapshot. You can preview or roll back to any historical version at any time.")

        if not package.versions:
            st.write("No historical versions found.")
        else:
            for v in reversed(package.versions):
                with st.expander(f"Version v{v.version_number} — {v.note} ({v.saved_at[:19].replace('T', ' ')})"):
                    st.caption(f"Snapshot Timestamp: {v.saved_at}")
                    if v.version_number == package.metadata.current_version:
                        st.badge("Active Version", type="primary") if hasattr(st, "badge") else st.info("Current Active Version")

                    col_rev, _ = st.columns([1, 4])
                    with col_rev:
                        if v.version_number != package.metadata.current_version:
                            if st.button(f"⏪ Revert to v{v.version_number}", key=f"revert_btn_{v.version_number}"):
                                revert_to_version(package.metadata.id, v.version_number)
                                st.success(f"Restored version v{v.version_number} as active!")
                                st.rerun()

                    st.markdown("---")
                    st.markdown(v.content)
