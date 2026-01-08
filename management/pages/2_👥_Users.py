"""
Project Manager User Management - View and Manage Translators
UniOr-PET Management Interface
"""
import streamlit as st
import asyncio
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

# Add parent directory to path to import shared modules
parent_dir = Path(__file__).parent.parent.parent
sys.path.append(str(parent_dir))

from db_manager import get_database_manager

# Page configuration
st.set_page_config(
    page_title="User Management - PM Dashboard",
    page_icon="👥",
    layout="wide"
)


def load_css():
    """Load custom CSS"""
    css_path = Path(__file__).parent.parent / "static" / "styles.css"
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def check_pm_auth():
    """Check if user is authenticated as Project Manager"""
    if not st.session_state.get('authenticated'):
        st.error("Please log in first")
        st.stop()
    if st.session_state.get('role') != 'project_manager':
        st.error("⛔ Access denied: Not a Project Manager")
        st.stop()


def display_project_info(db_manager, project_key):
    """Display project information card"""
    st.markdown("### 📁 Project Information")

    col1, col2 = st.columns([2, 1])

    with col1:
        # Get project metadata
        try:
            project = asyncio.run(db_manager.get_project(project_key))

            # Load project files
            files = None
            segment_count = 0
            try:
                files = asyncio.run(db_manager.load_project_files(project_key))
                if files:
                    source_content = files[2]
                    segment_count = len(source_content.splitlines()) if source_content else 0
            except:
                pass

            with st.container(border=True):
                st.markdown("#### 📋 Project Details")

                # Project Key
                st.markdown(f"**Project Key:** `{project_key}`")

                # Project Manager
                st.markdown(f"**Manager:** {st.session_state.pm_name} {st.session_state.pm_surname}")

                # Created date
                if project:
                    created_at = project.get('created_at', 'N/A')
                    if isinstance(created_at, datetime):
                        created_at = created_at.strftime('%Y-%m-%d %H:%M:%S')
                    st.markdown(f"**Created:** {created_at}")

                    # Database type
                    db_type_display = {
                        'free_supabase': 'Free Supabase',
                        'mongodb': 'MongoDB',
                        'supabase': 'Custom Supabase'
                    }.get(project.get('db_type', st.session_state.db_type), 'Unknown')
                    st.markdown(f"**Database:** {db_type_display}")

                # File information
                if files:
                    st.markdown("---")
                    st.markdown("**📄 Project Files**")
                    st.markdown(f"• **Source:** {files[0]}")
                    st.markdown(f"• **Translation:** {files[1]}")
                    st.markdown(f"• **Total Segments:** {segment_count}")

        except Exception as e:
            st.error(f"Error loading project information: {str(e)}")

    with col2:
        with st.container(border=True):
            st.markdown("#### 🔑 Share Project Key")
            st.code(project_key, language=None)
            st.caption("Share this key with translators to invite them to your project")

            if st.button("📋 Copy to Clipboard", use_container_width=True):
                st.toast("Project key ready to copy!")


def display_translator_list(db_manager, translators):
    """Display list of translators with search and details"""
    st.markdown("---")
    st.markdown("### 👥 Translator Management")

    if not translators:
        st.info("No translators have joined your project yet. Share your project key to get started!")
        return

    # Search bar
    search_query = st.text_input(
        "🔍 Search Translators",
        placeholder="Search by name or surname...",
        help="Filter translators by name"
    )

    # Filter translators based on search
    filtered_translators = translators
    if search_query:
        filtered_translators = [
            t for t in translators
            if search_query.lower() in t['name'].lower() or search_query.lower() in t['surname'].lower()
        ]

    if not filtered_translators:
        st.warning(f"No translators found matching '{search_query}'")
        return

    # Display count
    st.markdown(f"**Found {len(filtered_translators)} translator(s)**")
    st.markdown("")

    # Display translator cards
    for translator in filtered_translators:
        try:
            # Load progress for this translator
            metrics_df, full_text, time_tracker, timer_mode = asyncio.run(
                db_manager.load_progress(translator['name'], translator['surname'])
            )

            segments_completed = len(metrics_df) if not metrics_df.empty else 0
            progress_pct = 0

            # Calculate progress percentage
            if len(full_text) > 0 and segments_completed > 0:
                progress_pct = min((segments_completed / len(full_text)) * 100, 100)

            # Calculate metrics
            total_time = metrics_df['edit_time'].sum() if not metrics_df.empty and 'edit_time' in metrics_df.columns else 0
            total_edits = 0
            if not metrics_df.empty:
                if 'insertions' in metrics_df.columns and 'deletions' in metrics_df.columns:
                    total_edits = metrics_df['insertions'].sum() + metrics_df['deletions'].sum()

            # Determine status
            if segments_completed > 0:
                status = "🟢 Active"
                status_color = "green"
            else:
                status = "⚪ Not Started"
                status_color = "gray"

            # Create translator card
            with st.container(border=True):
                # Header with name and status
                col_header1, col_header2 = st.columns([3, 1])
                with col_header1:
                    st.markdown(f"#### 👤 {translator['name']} {translator['surname']}")
                with col_header2:
                    st.markdown(f"<div style='text-align: right; padding-top: 0.5rem;'>{status}</div>", unsafe_allow_html=True)

                # Metrics row
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric(
                        label="Segments Completed",
                        value=segments_completed,
                        help="Number of segments edited"
                    )

                with col2:
                    st.metric(
                        label="Progress",
                        value=f"{progress_pct:.1f}%",
                        help="Percentage of total segments completed"
                    )

                with col3:
                    st.metric(
                        label="Editing Time",
                        value=f"{total_time:.0f}s" if total_time < 60 else f"{total_time/60:.1f}m",
                        help="Total time spent editing"
                    )

                with col4:
                    st.metric(
                        label="Total Edits",
                        value=int(total_edits),
                        help="Total insertions + deletions"
                    )

                # Expandable detailed view
                if not metrics_df.empty:
                    with st.expander("📊 View Detailed Metrics"):
                        # Show first 10 segments
                        display_df = metrics_df.head(10).copy()

                        # Select relevant columns
                        if 'segment_id' in display_df.columns:
                            columns_to_show = ['segment_id']

                            if 'edit_time' in display_df.columns:
                                columns_to_show.append('edit_time')
                            if 'insertions' in display_df.columns:
                                columns_to_show.append('insertions')
                            if 'deletions' in display_df.columns:
                                columns_to_show.append('deletions')

                            st.dataframe(
                                display_df[columns_to_show],
                                use_container_width=True,
                                hide_index=True
                            )

                            if len(metrics_df) > 10:
                                st.caption(f"Showing first 10 of {len(metrics_df)} segments. Use Analytics page for full view.")

        except Exception as e:
            # Error card
            with st.container(border=True):
                col_header1, col_header2 = st.columns([3, 1])
                with col_header1:
                    st.markdown(f"#### 👤 {translator['name']} {translator['surname']}")
                with col_header2:
                    st.markdown(f"<div style='text-align: right; padding-top: 0.5rem;'>⚪ Not Started</div>", unsafe_allow_html=True)

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Segments Completed", 0)
                with col2:
                    st.metric("Progress", "0%")
                with col3:
                    st.metric("Editing Time", "0s")
                with col4:
                    st.metric("Total Edits", 0)


def main():
    """Main user management page"""
    load_css()
    check_pm_auth()

    st.title("👥 User Management")
    st.markdown(f"Managing project: **{st.session_state.project_key}**")

    # Get database manager
    db_manager = get_database_manager(
        st.session_state.db_type,
        st.session_state.db_connection
    )

    # Get project key
    project_key = st.session_state.project_key

    # Display project information
    display_project_info(db_manager, project_key)

    # Get translators
    try:
        with st.spinner("Loading translator data..."):
            translators = asyncio.run(db_manager.get_project_translators(project_key))

        # Display translator list and details
        display_translator_list(db_manager, translators)

    except Exception as e:
        st.error(f"Error loading translator data: {str(e)}")
        if st.checkbox("Show error details"):
            st.exception(e)


if __name__ == "__main__":
    main()
