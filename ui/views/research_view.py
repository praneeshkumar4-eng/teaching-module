"""
Research Dossier View for LessonForge.
Displays the retrieved source materials across Web, Academic Books,
and YouTube (with embedded players and spoken transcripts) that strictly ground the lesson.
"""
import streamlit as st

from core.models import LessonPackage


def render_research_view(package: LessonPackage):
    """Renders the comprehensive research evidence dossier."""
    dossier = package.research_dossier

    st.markdown(f"## Research Dossier — *{package.metadata.title}*")
    st.caption(
        f"Retrieved at {dossier.retrieved_at[:19].replace('T', ' ')} • "
        f"Search Query: `{dossier.query}` • "
        f"Zero invented links. All sources are verified external materials."
    )

    # Top summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Web Sources", len(dossier.web_sources), f"via {dossier.web_sources[0].engine if dossier.web_sources else 'N/A'}")
    with col2:
        st.metric("Academic Books", len(dossier.book_sources), "Google Books / OpenLibrary")
    with col3:
        st.metric("YouTube Media", len(dossier.video_sources), f"{sum(1 for v in dossier.video_sources if v.transcript_available)} transcripts")

    st.divider()

    tab_web, tab_books, tab_videos, tab_raw = st.tabs([
        f"🌐 Web Sources ({len(dossier.web_sources)})",
        f"📚 Academic Books ({len(dossier.book_sources)})",
        f"▶️ YouTube Videos & Transcripts ({len(dossier.video_sources)})",
        "📄 Grounding Index & Raw Context",
    ])

    # 1. Web Sources Tab
    with tab_web:
        if not dossier.web_sources:
            st.info("No web sources recorded for this dossier.")
        else:
            for idx, w in enumerate(dossier.web_sources, 1):
                with st.container():
                    st.markdown(
                        f"""
                        <div style="border:1px solid #e2e8f0; border-radius:10px; padding:16px 20px; margin-bottom:14px; background:#ffffff;">
                          <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                            <div>
                              <span style="background:#dbeafe; color:#1d4ed8; font-weight:700; font-size:0.75rem; padding:2px 8px; border-radius:12px;">
                                [Web {idx}]
                              </span>
                              <strong style="font-size:1.05rem; margin-left:8px;">{w.title}</strong>
                            </div>
                            <span style="font-size:0.75rem; color:#64748b;">Engine: {w.engine}</span>
                          </div>
                          <div style="margin-top:6px; font-size:0.85rem;">
                            🔗 <a href="{w.url}" target="_blank" rel="noopener noreferrer">{w.url}</a>
                          </div>
                          <div style="margin-top:8px; font-size:0.92rem; color:#334155;">
                            {w.snippet}
                          </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    with st.expander(f"Read Extracted Webpage Content ({len(w.content)} chars)"):
                        st.markdown(w.content if w.content else "No extended text extracted.")

    # 2. Books Tab
    with tab_books:
        if not dossier.book_sources:
            st.info("No academic book entries found.")
        else:
            for idx, b in enumerate(dossier.book_sources, 1):
                authors_str = ", ".join(b.authors) if b.authors else "Unknown Authors"
                with st.container():
                    st.markdown(
                        f"""
                        <div style="border:1px solid #e2e8f0; border-radius:10px; padding:16px 20px; margin-bottom:14px; background:#ffffff;">
                          <div>
                            <span style="background:#fef3c7; color:#b45309; font-weight:700; font-size:0.75rem; padding:2px 8px; border-radius:12px;">
                              [Book {idx}]
                            </span>
                            <strong style="font-size:1.05rem; margin-left:8px;">{b.title}</strong>
                          </div>
                          <div style="margin-top:6px; font-size:0.88rem; color:#475569;">
                            <strong>Authors:</strong> {authors_str} | 
                            <strong>Publisher:</strong> {b.publisher or 'Academic'} | 
                            <strong>Year:</strong> {b.year or 'N/A'}
                            {f' | <strong>ISBN:</strong> {b.isbn}' if b.isbn else ''}
                          </div>
                          <div style="margin-top:8px; font-size:0.92rem; color:#334155;">
                            {b.description}
                          </div>
                          {f'<div style="margin-top:8px; font-size:0.85rem;">📖 <a href="{b.info_link or b.preview_link}" target="_blank" rel="noopener noreferrer">View Volume & Preview Link</a></div>' if (b.info_link or b.preview_link) else ''}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    # 3. YouTube Videos Tab
    with tab_videos:
        if not dossier.video_sources:
            st.info("No educational video entries found.")
        else:
            for idx, v in enumerate(dossier.video_sources, 1):
                with st.container():
                    vcol1, vcol2 = st.columns([1, 1])
                    with vcol1:
                        st.markdown(
                            f"""
                            <div style="border:1px solid #e2e8f0; border-radius:10px; padding:16px; background:#ffffff;">
                              <div>
                                <span style="background:#fee2e2; color:#b91c1c; font-weight:700; font-size:0.75rem; padding:2px 8px; border-radius:12px;">
                                  [Video {idx}]
                                </span>
                                <strong style="font-size:1.02rem; margin-left:8px;">{v.title}</strong>
                              </div>
                              <div style="margin-top:6px; font-size:0.85rem; color:#64748b;">
                                <strong>Channel:</strong> {v.channel} • <strong>Duration:</strong> {v.duration or 'N/A'}
                              </div>
                              <div style="margin-top:6px; font-size:0.85rem;">
                                🔗 <a href="{v.url}" target="_blank" rel="noopener noreferrer">{v.url}</a>
                              </div>
                              <div style="margin-top:8px; font-size:0.9rem; color:#334155;">
                                {v.description[:280]}...
                              </div>
                              <div style="margin-top:8px;">
                                <span style="font-size:0.8rem; font-weight:600; color:{'#15803d' if v.transcript_available else '#64748b'};">
                                  {'🎙️ Transcript Available' if v.transcript_available else '🔇 Captions Not Available'}
                                </span>
                              </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        if v.transcript_available:
                            with st.expander(f"View Spoken Transcript ({len(v.full_transcript or v.transcript_excerpt)} chars)"):
                                st.write(v.full_transcript or v.transcript_excerpt)

                    with vcol2:
                        try:
                            st.video(v.url)
                        except Exception:
                            st.markdown(f"[Watch Video on YouTube]({v.url})")

    # 4. Grounding Context Tab
    with tab_raw:
        st.subheader("Synthesized Citation Reference Index")
        st.markdown(dossier.get_citation_summary())

        with st.expander("View Full Unprocessed Context Fed to AI"):
            st.text_area("Raw Context", value=dossier.raw_context, height=350, disabled=True)
