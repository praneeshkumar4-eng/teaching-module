"""
Comprehensive Lesson Workspace for LessonForge.
Implements the 7 required tabs:
Lesson | Sources | QC 1: Accuracy | QC 2: Teaching | Edit | Versions | Preview & Export
Includes checkbox issue selection, before/after diff comparison, version rollback,
and single-click ZIP and individual file downloads.
"""
import streamlit as st

from core.exporter import (
    build_lesson_zip_bundle,
    format_qc1_report_table,
    format_qc2_report_table,
    generate_references_markdown,
    generate_styled_html,
)
from core.models import AccessLevel, LessonPackage
from core.storage import (
    load_lesson,
    mark_qc_stale,
    revert_to_version,
    save_lesson_version,
    update_qc_reports,
)
from generator.lesson_generator import revise_lesson_with_selected_issues
from qc.factual_checker import review_factual_accuracy
from qc.pedagogical_checker import review_teaching_quality
from ui.components import (
    render_access_badge,
    render_diff_viewer,
    render_hero_header,
    render_progress_stepper,
    render_timing_visual,
)


def render_editor_view(package: LessonPackage):
    """Renders the comprehensive 7-tab instructional workspace."""
    render_hero_header()
    render_progress_stepper("Edit & Export")

    # Header title and quick metadata
    st.markdown(f"### {package.metadata.title}")
    st.caption(f"**Objective:** {package.metadata.objective} • **Active Version:** `v{package.metadata.current_version}`")

    # 7 Required Tabs
    tab_lesson, tab_sources, tab_qc1, tab_qc2, tab_edit, tab_versions, tab_export = st.tabs([
        "📖 Lesson",
        f"🌐 Sources ({len(package.research_dossier.sources)})",
        "🔍 QC 1: Accuracy",
        "🎓 QC 2: Teaching",
        "✏️ Edit",
        f"🕒 Versions (v{package.metadata.current_version})",
        "📦 Preview & Export",
    ])

    # -------------------------------------------------------------------------
    # TAB 1: LESSON
    # -------------------------------------------------------------------------
    with tab_lesson:
        if package.structured_lesson and package.structured_lesson.sections:
            sec_data = [
                {
                    "title": s.title,
                    "minutes": s.minutes,
                    "word_count": s.word_count,
                    "timing_feasibility": s.timing_feasibility,
                }
                for s in package.structured_lesson.sections
            ]
            render_timing_visual(sec_data)
        st.markdown(package.markdown_content)

    # -------------------------------------------------------------------------
    # TAB 2: SOURCES
    # -------------------------------------------------------------------------
    with tab_sources:
        st.subheader("Normalized Research Dossier Sources")
        st.caption("Every source was retrieved via real API endpoints. Sources with description-only access were NOT read or watched in full.")

        for s in package.research_dossier.sources:
            icon = {"web": "🌐", "book": "📚", "video": "▶️"}.get(s.type.value, "📄")
            with st.container():
                st.markdown(
                    f"""
                    <div class="lf-source-card">
                      <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                        <div>
                          <strong style="font-size:1.1rem; color:#1e1b4b;">[{s.id}] {icon} {s.title}</strong>
                          <div style="font-size:0.85rem; color:#64748b; margin-top:2px;">
                            Author/Channel: <strong>{s.author_or_channel or 'N/A'}</strong> • Engine: {s.engine}
                            {f' • Published: {s.published_year}' if s.published_year else ''}
                            {f' • Duration: {s.duration}' if s.duration else ''}
                          </div>
                        </div>
                        <div>
                          {render_access_badge(s.access_level)}
                        </div>
                      </div>
                      <div style="margin-top:8px; font-size:0.85rem;">
                        🔗 <a href="{s.url}" target="_blank" rel="noopener noreferrer">{s.url}</a>
                      </div>
                      <div style="margin-top:8px; font-size:0.9rem; color:#334155; background:#f8fafc; padding:8px 12px; border-radius:6px;">
                        <strong>Grounded Relevance Note:</strong> {s.relevance_note}
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                with st.expander(f"View Retrieved Excerpt for [{s.id}]"):
                    st.write(s.retrieved_text_excerpt or s.full_content[:1500])

    # -------------------------------------------------------------------------
    # TAB 3: QC 1 (FACTUAL ACCURACY)
    # -------------------------------------------------------------------------
    with tab_qc1:
        st.subheader("QC Layer 1: Factual Accuracy & Grounding Audit")

        qc1 = package.qc_factual
        if not qc1:
            st.warning("No QC Layer 1 report found.")
            if st.button("Run QC 1 Audit", type="primary"):
                _run_qc1_step(package)
        else:
            if qc1.is_stale:
                st.warning("⚠️ This report is STALE because the lesson was edited since the last audit.")

            # Verdict Banner
            if qc1.verdict == "Looks good":
                st.markdown(
                    f'<div class="lf-verdict-banner-pass">✅ <strong>Verdict: Looks Good</strong> — {qc1.confidence_note}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="lf-verdict-banner-warn">⚠️ <strong>Verdict: Needs Revision</strong> — {qc1.confidence_note}</div>',
                    unsafe_allow_html=True,
                )

            # Metric row
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1:
                st.metric("Total Issues Found", len(qc1.issues))
            with col_m2:
                high_count = sum(1 for i in qc1.issues if i.severity == "high")
                st.metric("High Severity", high_count)
            with col_m3:
                resolved_count = sum(1 for i in qc1.issues if i.applied)
                st.metric("Resolved / Applied", resolved_count)
            with col_m4:
                st.metric("Deterministic Checks", "Passed" if qc1.deterministic_passed else "Flags Found")

            st.markdown(f"**What Was Verified:** *{qc1.what_was_verified}*")
            st.divider()

            # Interactive issue cards with checkboxes
            _render_qc_issues_interactive(package, qc1.issues, layer_name="qc1")

            col_retry, _ = st.columns([2, 3])
            with col_retry:
                if st.button("🔄 Re-run QC 1 (Audit Accuracy)", key="rerun_qc1_btn"):
                    _run_qc1_step(package)

    # -------------------------------------------------------------------------
    # TAB 4: QC 2 (TEACHING QUALITY)
    # -------------------------------------------------------------------------
    with tab_qc2:
        st.subheader("QC Layer 2: Teaching Quality & Instructional Design Review")

        qc2 = package.qc_pedagogical
        if not qc2:
            st.warning("No QC Layer 2 report found.")
            if st.button("Run QC 2 Review", type="primary"):
                _run_qc2_step(package)
        else:
            if qc2.is_stale:
                st.warning("⚠️ This report is STALE because the lesson was edited since the last review.")

            # Verdict Banner
            if qc2.verdict == "Looks good":
                st.markdown(
                    f'<div class="lf-verdict-banner-pass">✅ <strong>Verdict: Looks Good</strong> — {qc2.confidence_note}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="lf-verdict-banner-warn">⚠️ <strong>Verdict: Needs Revision</strong> — {qc2.confidence_note}</div>',
                    unsafe_allow_html=True,
                )

            # Objective Coverage Table
            st.markdown("#### 🎯 Learning Objective Coverage Breakdown")
            if qc2.objective_coverage:
                cov_data = [
                    {
                        "Objective Component": c.objective_part,
                        "Where Taught": c.where_taught,
                        "Where Tested": c.where_tested,
                        "Covered": "Yes ✅" if c.covered else "No ❌",
                    }
                    for c in qc2.objective_coverage
                ]
                st.table(cov_data)

            # Metric row
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                st.metric("Total Recommendations", len(qc2.issues))
            with col_m2:
                high_count = sum(1 for i in qc2.issues if i.severity == "high")
                st.metric("High Priority", high_count)
            with col_m3:
                resolved_count = sum(1 for i in qc2.issues if i.applied)
                st.metric("Resolved / Applied", resolved_count)

            st.markdown(f"**What Was Verified:** *{qc2.what_was_verified}*")
            st.divider()

            # Interactive issue cards with checkboxes
            _render_qc_issues_interactive(package, qc2.issues, layer_name="qc2")

            col_retry, _ = st.columns([2, 3])
            with col_retry:
                if st.button("🔄 Re-run QC 2 (Review Pedagogy)", key="rerun_qc2_btn"):
                    _run_qc2_step(package)

    # -------------------------------------------------------------------------
    # TAB 5: EDIT
    # -------------------------------------------------------------------------
    with tab_edit:
        st.subheader("Direct Lesson Plan Markdown Editor")
        st.info("You have full control to edit any section. Saving an edited version creates an immutable snapshot in your version history.")

        edited_text = st.text_area(
            "Lesson Markdown Content",
            value=package.markdown_content,
            height=580,
            key=f"lesson_edit_area_{package.metadata.id}_{package.metadata.current_version}",
        )

        col_note, col_save = st.columns([3, 1])
        with col_note:
            edit_note = st.text_input(
                "Version Changelog Note",
                value="Teacher manual edits",
                key="manual_edit_note_key",
            )
        with col_save:
            st.write("")
            if st.button("💾 Save Edited Version", type="primary", use_container_width=True):
                new_v = save_lesson_version(package.metadata.id, edited_text, note=edit_note)
                mark_qc_stale(package.metadata.id)
                st.toast(f"Saved version v{new_v} successfully!")
                st.rerun()

    # -------------------------------------------------------------------------
    # TAB 6: VERSIONS
    # -------------------------------------------------------------------------
    with tab_versions:
        st.subheader(f"Version History ({len(package.versions)} Saved Snapshots)")
        st.caption("Every manual save and AI revision creates an immutable version snapshot. You can roll back to any point in time.")

        for v in reversed(package.versions):
            is_active = v.version_number == package.metadata.current_version
            with st.expander(f"Version v{v.version_number} — {v.note} ({v.saved_at[:19].replace('T', ' ')}){' (Active)' if is_active else ''}"):
                st.caption(f"Timestamp: {v.saved_at}")
                if not is_active:
                    if st.button(f"⏪ Restore Version v{v.version_number}", key=f"restore_btn_{v.version_number}"):
                        revert_to_version(package.metadata.id, v.version_number)
                        st.toast(f"Restored version v{v.version_number} as active!")
                        st.rerun()
                st.markdown("---")
                st.markdown(v.content)

    # -------------------------------------------------------------------------
    # TAB 7: PREVIEW & EXPORT
    # -------------------------------------------------------------------------
    with tab_export:
        st.subheader("Preview & Export Package")
        st.caption("Download your lesson as a unified ZIP archive containing all required files, or download individual artifacts.")

        # Top Action Bar with Single ZIP and Individual Downloads
        st.markdown("#### 📥 Export Downloads")
        zcol1, zcol2, zcol3, zcol4, zcol5 = st.columns(5)

        # 1. Single ZIP Bundle
        zip_bytes = build_lesson_zip_bundle(package)
        with zcol1:
            st.download_button(
                label="📦 Download ZIP Bundle",
                data=zip_bytes,
                file_name=f"{package.metadata.id}_bundle.zip",
                mime="application/zip",
                type="primary",
                use_container_width=True,
                help="Single ZIP containing lesson.md, lesson.html, references.md, qc_report_1_accuracy.md, and qc_report_2_teaching.md",
            )

        # 2. lesson.md
        with zcol2:
            st.download_button(
                label="📄 lesson.md",
                data=package.markdown_content,
                file_name="lesson.md",
                mime="text/markdown",
                use_container_width=True,
            )

        # 3. lesson.html
        with zcol3:
            html_content = generate_styled_html(package.markdown_content, package.metadata.title, package.metadata.objective)
            st.download_button(
                label="🌐 lesson.html",
                data=html_content,
                file_name="lesson.html",
                mime="text/html",
                use_container_width=True,
            )

        # 4. references.md
        with zcol4:
            refs_md = generate_references_markdown(package)
            st.download_button(
                label="📚 references.md",
                data=refs_md,
                file_name="references.md",
                mime="text/markdown",
                use_container_width=True,
            )

        # 5. QC Reports
        with zcol5:
            combined_qc_md = (
                format_qc1_report_table(package.qc_factual) + "\n\n---\n\n" + format_qc2_report_table(package.qc_pedagogical)
            )
            st.download_button(
                label="🔍 QC Reports (.md)",
                data=combined_qc_md,
                file_name="qc_reports.md",
                mime="text/markdown",
                use_container_width=True,
            )

        st.divider()

        # Formatted HTML Preview
        st.markdown("#### 👁️ Print-Ready HTML Preview")
        html_preview = generate_styled_html(package.markdown_content, package.metadata.title, package.metadata.objective)
        st.components.v1.html(html_preview, height=600, scrolling=True)


# -----------------------------------------------------------------------------
# Interactive QC Issue Selection & AI Revision with Before/After Diff
# -----------------------------------------------------------------------------

def _render_qc_issues_interactive(package: LessonPackage, issues: list, layer_name: str):
    """Renders issue cards with checkboxes and diff-reviewed AI revision."""
    if not issues:
        st.success("🎉 No issues identified! All criteria satisfied.")
        return

    # Checkbox state container
    select_all = st.checkbox("Select All Issues", value=True, key=f"sel_all_{layer_name}")

    selected_issues = []
    for iss in issues:
        sev_class = f"lf-sev-{iss.severity}"
        with st.container():
            st.markdown(
                f"""
                <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:10px; padding:14px 18px; margin-bottom:10px;">
                  <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                      <span class="{sev_class}">{iss.severity}</span>
                      <strong style="margin-left:8px; font-size:1.0rem;">[{iss.location}]</strong>
                    </div>
                    <span style="font-size:0.8rem; color:#64748b;">ID: {iss.id}</span>
                  </div>
                  <div style="font-size:0.92rem; color:#1e293b; margin-top:8px;">
                    <strong>Issue:</strong> {iss.issue_found}
                  </div>
                  <div style="font-size:0.88rem; color:#475569; margin-top:4px;">
                    <strong>Evidence:</strong> {iss.evidence}
                  </div>
                  <div style="font-size:0.88rem; color:#15803d; margin-top:4px;">
                    <strong>Suggested Improvement:</strong> {iss.suggested_improvement}
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            checked = st.checkbox(
                f"Apply fix for [{iss.id}]",
                value=select_all,
                key=f"check_{layer_name}_{iss.id}",
            )
            if checked:
                selected_issues.append(iss)

    st.write("")

    # Revision Action
    col_rev, _ = st.columns([2, 3])
    with col_rev:
        revise_btn = st.button(
            f"✨ Revise Using {len(selected_issues)} Selected Suggestion(s)",
            type="primary",
            disabled=len(selected_issues) == 0,
            key=f"btn_revise_{layer_name}",
            use_container_width=True,
        )

    if revise_btn:
        with st.spinner("AI is revising the lesson plan using selected suggestions..."):
            revised_text = revise_lesson_with_selected_issues(
                current_markdown=package.markdown_content,
                selected_issues=selected_issues,
                dossier=package.research_dossier,
            )
            st.session_state[f"pending_revision_{layer_name}"] = revised_text
            st.session_state[f"pending_issues_{layer_name}"] = [i.id for i in selected_issues]
            st.rerun()

    # Show Diff and Accept/Discard prompt if a revision is pending
    pending_key = f"pending_revision_{layer_name}"
    if pending_key in st.session_state:
        st.divider()
        st.markdown("### 🔍 Proposed Revision: Before & After Diff Review")
        st.caption("Review the changes made by the AI revision before accepting or discarding.")

        revised_candidate = st.session_state[pending_key]
        render_diff_viewer(package.markdown_content, revised_candidate)

        col_accept, col_discard = st.columns(2)
        with col_accept:
            if st.button("✅ Accept Revision & Save Version", type="primary", use_container_width=True, key=f"acc_{layer_name}"):
                applied_ids = st.session_state.get(f"pending_issues_{layer_name}", [])
                note_str = f"AI revision: applied {len(applied_ids)} suggestions ({', '.join(applied_ids)})"

                new_v = save_lesson_version(package.metadata.id, revised_candidate, note=note_str)
                package.markdown_content = revised_candidate
                package.metadata.current_version = new_v

                # Mark applied issues
                for iss in issues:
                    if iss.id in applied_ids:
                        iss.applied = True

                # Mark QC reports as stale
                mark_qc_stale(package.metadata.id)

                del st.session_state[pending_key]
                st.toast(f"Revision accepted and saved as version v{new_v}!")
                st.rerun()

        with col_discard:
            if st.button("❌ Discard Revision", use_container_width=True, key=f"disc_{layer_name}"):
                del st.session_state[pending_key]
                st.toast("Revision discarded. Original lesson preserved.")
                st.rerun()


def _run_qc1_step(package: LessonPackage):
    """Executes QC Layer 1 independently."""
    with st.spinner("Auditing factual accuracy against Research Dossier..."):
        qc1 = review_factual_accuracy(package.markdown_content, package.research_dossier)
        package.qc_factual = qc1
        update_qc_reports(package.metadata.id, qc_factual=qc1)
        st.toast("QC Layer 1 audit completed!")
        st.rerun()


def _run_qc2_step(package: LessonPackage):
    """Executes QC Layer 2 independently."""
    with st.spinner("Reviewing teaching quality and objective alignment..."):
        qc2 = review_teaching_quality(package.markdown_content, package.metadata.objective)
        package.qc_pedagogical = qc2
        update_qc_reports(package.metadata.id, qc_pedagogical=qc2)
        st.toast("QC Layer 2 review completed!")
        st.rerun()
