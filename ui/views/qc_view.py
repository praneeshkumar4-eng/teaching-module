"""
Quality Control (QC) Dashboard for LessonForge.
Presents detailed independent reports for QC Layer 1 (Factual Accuracy) and
QC Layer 2 (Teaching Quality), and enables teachers to selectively apply recommendations.
"""
import streamlit as st

from core.models import LessonPackage, QCPedagogicalRecommendation
from core.storage import save_lesson_version, update_qc_reports
from generator.lesson_generator import apply_recommendations_to_lesson
from qc.factual_checker import review_factual_accuracy
from qc.pedagogical_checker import review_teaching_quality
from ui.components import render_score_card


def render_qc_view(package: LessonPackage):
    """Renders the comprehensive QC audit suite with interactive recommendation applier."""
    st.markdown(f"## Quality Control Suite — *{package.metadata.title}*")
    st.caption("LessonForge executes two independent AI verification layers to guarantee academic rigor and classroom readiness.")

    tab_qc1, tab_qc2 = st.tabs([
        "🔍 QC Layer 1: Factual Accuracy Audit",
        "🎓 QC Layer 2: Teaching Quality & Pedagogy",
    ])

    # -------------------------------------------------------------------------
    # QC Layer 1: Factual Accuracy Audit
    # -------------------------------------------------------------------------
    with tab_qc1:
        report1 = package.qc_factual
        if not report1:
            st.warning("Factual accuracy report not found for this lesson.")
            if st.button("Run QC Layer 1 Now"):
                with st.spinner("Auditing factual claims against research dossier..."):
                    new_rep1 = review_factual_accuracy(package.markdown_content, package.research_dossier)
                    package.qc_factual = new_rep1
                    update_qc_reports(package.metadata.id, qc_factual=new_rep1)
                    st.rerun()
            return

        # Top Metric Row
        mcol1, mcol2, mcol3, mcol4 = st.columns(4)
        with mcol1:
            render_score_card(report1.overall_score, "Factual Accuracy", report1.status)
        with mcol2:
            st.metric("Verified Claims", report1.verified_count)
        with mcol3:
            st.metric("Unsupported Claims", report1.unsupported_count)
        with mcol4:
            st.metric("Contradicted Claims", report1.contradicted_count)

        st.subheader("Audit Summary")
        st.info(report1.summary)

        st.subheader("Claim-by-Claim Verification")
        if not report1.findings:
            st.write("All evaluated statements passed with zero hallucination flags.")
        else:
            for idx, f in enumerate(report1.findings, 1):
                status_color = {
                    "VERIFIED": "#10b981",
                    "ACCURATE": "#10b981",
                    "UNSUPPORTED": "#f59e0b",
                    "CONTRADICTED": "#ef4444",
                }.get(f.status.upper(), "#3b82f6")

                with st.container():
                    st.markdown(
                        f"""
                        <div style="border-left: 4px solid {status_color}; background:#ffffff; border:1px solid #e2e8f0; border-left-color:{status_color}; border-radius:8px; padding:14px 18px; margin-bottom:12px;">
                          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                            <strong>Claim #{idx} ({f.citation_ref})</strong>
                            <span style="background:{status_color}22; color:{status_color}; font-size:0.75rem; font-weight:700; padding:2px 8px; border-radius:12px;">
                              {f.status}
                            </span>
                          </div>
                          <div style="font-size:0.95rem; color:#1e293b; margin-bottom:6px;">
                            <em>"{f.claim}"</em>
                          </div>
                          <div style="font-size:0.88rem; color:#475569;">
                            <strong>Assessment:</strong> {f.explanation}
                          </div>
                          {f'<div style="font-size:0.88rem; color:#b45309; margin-top:4px;"><strong>Suggested Fix:</strong> {f.suggestion}</div>' if f.suggestion and f.suggestion.lower() != 'no change needed.' else ''}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

        st.divider()
        if st.button("🔄 Re-run Factual Accuracy Audit on Current Lesson", key="rerun_qc1_btn"):
            with st.spinner("Re-auditing factual claims against research dossier..."):
                new_rep1 = review_factual_accuracy(package.markdown_content, package.research_dossier)
                package.qc_factual = new_rep1
                update_qc_reports(package.metadata.id, qc_factual=new_rep1)
                st.success("QC Layer 1 updated!")
                st.rerun()

    # -------------------------------------------------------------------------
    # QC Layer 2: Teaching Quality & Pedagogy
    # -------------------------------------------------------------------------
    with tab_qc2:
        report2 = package.qc_pedagogical
        if not report2:
            st.warning("Pedagogical quality report not found for this lesson.")
            if st.button("Run QC Layer 2 Now"):
                with st.spinner("Reviewing teaching quality and alignment..."):
                    new_rep2 = review_teaching_quality(
                        package.markdown_content,
                        package.metadata.objective,
                        package.metadata.grade_level,
                    )
                    package.qc_pedagogical = new_rep2
                    update_qc_reports(package.metadata.id, qc_pedagogical=new_rep2)
                    st.rerun()
            return

        # Top Metric Row
        pcol1, pcol2, pcol3, pcol4 = st.columns(4)
        with pcol1:
            render_score_card(report2.overall_score, "Pedagogy Score", report2.status)
        with pcol2:
            st.metric("Objective Alignment", f"{report2.alignment_score}%")
        with pcol3:
            st.metric("45-Min Pacing", f"{report2.pacing_score}%")
        with pcol4:
            st.metric("Active Engagement", f"{report2.engagement_score}%")

        col_str, col_gro = st.columns(2)
        with col_str:
            st.subheader("🌟 Instructional Strengths")
            for s in report2.strengths:
                st.markdown(f"- {s}")

        with col_gro:
            st.subheader("🎯 Areas for Growth")
            for a in report2.areas_for_growth:
                st.markdown(f"- {a}")

        st.divider()
        st.subheader("Actionable Recommendations (Select & Apply)")
        st.caption("Check the recommendations you want to adopt, then click **Apply Selected Recommendations** to synthesize an updated version of your lesson plan.")

        selected_recs = []
        if not report2.recommendations:
            st.success("No critical pedagogical interventions flagged. Your lesson meets high instructional standards!")
        else:
            for idx, rec in enumerate(report2.recommendations):
                checked = st.checkbox(
                    f"**[{rec.severity} Priority] {rec.area}**: {rec.recommendation}",
                    value=True,
                    key=f"rec_check_{rec.id}_{idx}",
                )
                with st.expander(f"View Details: {rec.area}"):
                    st.markdown(f"**Current State:** {rec.current_state}")
                    st.markdown(f"**Proposed Concrete Action:** {rec.concrete_action}")

                if checked:
                    selected_recs.append(rec)

            st.write("")
            col_apply, _ = st.columns([2, 3])
            with col_apply:
                if st.button(
                    f"✨ Apply {len(selected_recs)} Selected Recommendation(s) to Lesson",
                    type="primary",
                    disabled=len(selected_recs) == 0,
                    use_container_width=True,
                ):
                    with st.spinner("Synthesizing updated lesson with selected QC recommendations..."):
                        updated_markdown = apply_recommendations_to_lesson(
                            current_lesson_markdown=package.markdown_content,
                            recommendations=selected_recs,
                        )
                        # Save as new version
                        new_ver = save_lesson_version(
                            lesson_id=package.metadata.id,
                            new_content=updated_markdown,
                            note=f"Applied {len(selected_recs)} pedagogical QC recommendations",
                        )
                        package.markdown_content = updated_markdown
                        package.metadata.current_version = new_ver
                        package.metadata.total_versions = new_ver

                        st.success(f"Applied! Saved new version v{new_ver}. Check the Lesson Workspace tab.")
                        st.rerun()

        st.divider()
        if st.button("🔄 Re-run Pedagogical Quality Review on Current Lesson", key="rerun_qc2_btn"):
            with st.spinner("Re-evaluating instructional alignment and pedagogy..."):
                new_rep2 = review_teaching_quality(
                    package.markdown_content,
                    package.metadata.objective,
                    package.metadata.grade_level,
                )
                package.qc_pedagogical = new_rep2
                update_qc_reports(package.metadata.id, qc_pedagogical=new_rep2)
                st.success("QC Layer 2 updated!")
                st.rerun()
