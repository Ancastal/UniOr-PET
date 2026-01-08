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

            st.markdown("**Project Details**")

            # Display in a nice card format
            info_html = f"""
            <div style="background-color: #f8f9fa; padding: 1.5rem; border-radius: 10px; border: 1px solid #dee2e6;">
                <p><strong>Project Key:</strong> <code>{project_key}</code></p>
                <p><strong>Project Manager:</strong> {st.session_state.pm_name} {st.session_state.pm_surname}</p>
            """

            if project:
                created_at = project.get('created_at', 'N/A')
                if isinstance(created_at, datetime):
                    created_at = created_at.strftime('%Y-%m-%d %H:%M:%S')
                info_html += f"<p><strong>Created:</strong> {created_at}</p>"

                # Get database type
                db_type_display = {
                    'free_supabase': 'Free Supabase',
                    'mongodb': 'MongoDB',
                    'supabase': 'Custom Supabase'
                }.get(project.get('db_type', st.session_state.db_type), 'Unknown')
                info_html += f"<p><strong>Database:</strong> {db_type_display}</p>"

            # Load project files
            try:
                files = asyncio.run(db_manager.load_project_files(project_key))
                if files:
                    source_filename, translation_filename, source_content, translation_content = files

                    info_html += f"<p><strong>Source File:</strong> {source_filename}</p>"
                    info_html += f"<p><strong>Translation File:</strong> {translation_filename}</p>"

                    # Count segments
                    segment_count = len(source_content.splitlines()) if source_content else 0
                    info_html += f"<p><strong>Total Segments:</strong> {segment_count}</p>"
            except:
                pass

            info_html += "</div>"
            st.markdown(info_html, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error loading project information: {str(e)}")

    with col2:
        st.markdown("**Share Project Key**")
        st.info(f"Share this key with translators:\n\n`{project_key}`")

        if st.button("📋 Copy to Clipboard", use_container_width=True):
            st.toast("Project key copied! (Please use browser copy function)")


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

    # Create translator summary table
    translator_summary = []

    for translator in filtered_translators:
        try:
            # Load progress for this translator
            metrics_df, full_text, time_tracker, timer_mode = asyncio.run(
                db_manager.load_progress(translator['name'], translator['surname'])
            )

            segments_completed = len(metrics_df) if not metrics_df.empty else 0
            progress_pct = 0

            # Calculate progress percentage if we know total segments
            # We can estimate from full_text length
            if len(full_text) > 0 and segments_completed > 0:
                progress_pct = min((segments_completed / len(full_text)) * 100, 100)

            # Calculate last active (from most recent segment edit)
            last_active = "Never"
            if not metrics_df.empty and 'edit_time' in metrics_df.columns:
                # Use current time as proxy (in production, store timestamps)
                last_active = "Recently"

            status = "✅ Active" if segments_completed > 0 else "⏸️ Not Started"

            translator_summary.append({
                'Name': translator['name'],
                'Surname': translator['surname'],
                'Segments Completed': segments_completed,
                'Progress': f"{progress_pct:.1f}%",
                'Status': status,
                'Last Active': last_active
            })

        except Exception as e:
            translator_summary.append({
                'Name': translator['name'],
                'Surname': translator['surname'],
                'Segments Completed': 0,
                'Progress': "0%",
                'Status': "⏸️ Not Started",
                'Last Active': "Never"
            })

    # Display summary table
    if translator_summary:
        summary_df = pd.DataFrame(translator_summary)
        st.dataframe(
            summary_df,
            use_container_width=True,
            hide_index=True
        )

        # Detailed view for each translator
        st.markdown("---")
        st.markdown("### 📋 Translator Details")

        for translator in filtered_translators:
            with st.expander(f"👤 {translator['name']} {translator['surname']}"):
                try:
                    # Load progress
                    metrics_df, full_text, time_tracker, timer_mode = asyncio.run(
                        db_manager.load_progress(translator['name'], translator['surname'])
                    )

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric("Segments Completed", len(metrics_df) if not metrics_df.empty else 0)

                    with col2:
                        total_time = metrics_df['edit_time'].sum() if not metrics_df.empty and 'edit_time' in metrics_df.columns else 0
                        st.metric("Total Editing Time", f"{total_time:.1f}s")

                    with col3:
                        total_edits = 0
                        if not metrics_df.empty:
                            if 'insertions' in metrics_df.columns and 'deletions' in metrics_df.columns:
                                total_edits = metrics_df['insertions'].sum() + metrics_df['deletions'].sum()
                        st.metric("Total Edits", int(total_edits))

                    # Display detailed metrics if available
                    if not metrics_df.empty:
                        st.markdown("**Segment-Level Metrics**")

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
                                st.info(f"Showing first 10 of {len(metrics_df)} segments. Use Analytics page for full view.")
                    else:
                        st.info("This translator hasn't started editing yet.")

                except Exception as e:
                    st.error(f"Error loading data for this translator: {str(e)}")


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
