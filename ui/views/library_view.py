"""
Lesson Library & Catalog View for LessonForge.
Enables teachers to browse, search, re-open, download, and manage all saved lessons.
"""
import streamlit as st

from core.exporter import build_lesson_zip_bundle
from core.storage import delete_lesson, list_all_lessons, load_lesson
from ui.components import render_header


def render_library_view():
    """Renders the saved lessons catalog."""
    render_header(
        title="Saved Lesson Library",
        subtitle="Manage, re-open, export, or audit all previously synthesized lessons.",
    )

    all_lessons = list_all_lessons()

    if not all_lessons:
        st.info("No lessons created yet. Start by generating your first lesson!")
        if st.button("➕ Create a Lesson Now", type="primary"):
            st.session_state.selected_nav = "➕ Create New Lesson"
            st.rerun()
        return

    # Search and Filter
    col_search, col_filter = st.columns([3, 2])
    with col_search:
        search_query = st.text_input(
            "🔍 Search Lessons",
            placeholder="Search by title or topic...",
        ).lower().strip()

    with col_filter:
        subjects = ["All Subjects"] + sorted(list({l.subject for l in all_lessons if l.subject}))
        selected_subject = st.selectbox("Filter by Subject", options=subjects)

    # Filter lessons
    filtered = []
    for l in all_lessons:
        if search_query and (search_query not in l.title.lower() and search_query not in l.objective.lower()):
            continue
        if selected_subject != "All Subjects" and l.subject != selected_subject:
            continue
        filtered.append(l)

    st.write(f"Showing **{len(filtered)}** of {len(all_lessons)} saved lessons")
    st.divider()

    for item in filtered:
        with st.container():
            col_info, col_actions = st.columns([3, 1])

            with col_info:
                st.markdown(f"#### {item.title}")
                st.caption(
                    f"**Subject:** {item.subject} • "
                    f"**Grade:** {item.grade_level} • "
                    f"**Versions:** `v{item.current_version}` • "
                    f"**Updated:** {item.updated_at[:19].replace('T', ' ')}"
                )
                st.markdown(f"> *{item.objective[:180]}...*")

            with col_actions:
                st.write("")
                # Open button
                if st.button("📖 Open Workspace", key=f"open_btn_{item.id}", use_container_width=True):
                    st.session_state.active_lesson_id = item.id
                    st.session_state.selected_nav = "📖 Lesson Workspace"
                    st.rerun()

                # Quick Download ZIP
                pkg = load_lesson(item.id)
                if pkg:
                    zip_bytes = build_lesson_zip_bundle(pkg)
                    st.download_button(
                        label="📦 Export ZIP",
                        data=zip_bytes,
                        file_name=f"{item.id}.zip",
                        mime="application/zip",
                        key=f"zip_btn_{item.id}",
                        use_container_width=True,
                    )

                # Delete button
                if st.button("🗑️ Delete", key=f"del_btn_{item.id}", use_container_width=True):
                    delete_lesson(item.id)
                    if st.session_state.get("active_lesson_id") == item.id:
                        st.session_state.active_lesson_id = None
                    st.success(f"Deleted lesson '{item.title}'")
                    st.rerun()

            st.markdown("---")

