"""
Project Manager Dashboard - Main Page
UniOr-PET Management Interface
"""
import streamlit as st
import asyncio
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add parent directory to path to import shared modules
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

from db_manager import get_database_manager, hash_password

# Page configuration
st.set_page_config(
    page_title="PM Dashboard - UniOr-PET",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)


def load_css():
    """Load custom CSS"""
    css_path = Path(__file__).parent / "static" / "styles.css"
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'pm_name' not in st.session_state:
        st.session_state.pm_name = ""
    if 'pm_surname' not in st.session_state:
        st.session_state.pm_surname = ""
    if 'role' not in st.session_state:
        st.session_state.role = ""
    if 'project_key' not in st.session_state:
        st.session_state.project_key = ""
    if 'db_type' not in st.session_state:
        st.session_state.db_type = None
    if 'db_connection' not in st.session_state:
        st.session_state.db_connection = None


def check_pm_auth():
    """Check if user is authenticated as Project Manager"""
    if not st.session_state.get('authenticated'):
        return False
    if st.session_state.get('role') != 'project_manager':
        st.error("⛔ Access denied: Not a Project Manager")
        st.stop()
    return True


def login_page():
    """Display login page for Project Managers"""
    st.title("🏢 Project Manager Dashboard")
    st.markdown("### Login")
    st.markdown("Access the management interface for your translation project.")

    with st.form("login_form"):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Name", key="login_name")

        with col2:
            surname = st.text_input("Surname", key="login_surname")

        password = st.text_input("Password", type="password", key="login_password")

        submit = st.form_submit_button("Login", use_container_width=True)

        if submit:
            if not name or not surname or not password:
                st.error("Please fill in all fields")
            else:
                # Verify credentials using default database
                db_manager = get_database_manager()

                try:
                    authenticated, role, db_type, db_connection = asyncio.run(
                        db_manager.verify_user(name, surname, password)
                    )

                    if authenticated and role == "project_manager":
                        # Set session state
                        st.session_state.authenticated = True
                        st.session_state.pm_name = name
                        st.session_state.pm_surname = surname
                        st.session_state.role = role
                        st.session_state.project_key = f"{surname}_{name}"
                        st.session_state.db_type = db_type
                        st.session_state.db_connection = db_connection

                        st.success("✅ Login successful!")
                        st.rerun()
                    elif authenticated and role != "project_manager":
                        st.error("⛔ This interface is for Project Managers only. Translators should use the main application.")
                    else:
                        st.error("❌ Invalid credentials. Please try again.")

                except Exception as e:
                    st.error(f"Error during authentication: {str(e)}")
                    st.error("Please check your database connection.")


def dashboard_page():
    """Display main dashboard for Project Managers"""
    check_pm_auth()

    st.title("🏢 Project Manager Dashboard")
    st.markdown(f"### Welcome, {st.session_state.pm_name} {st.session_state.pm_surname}")

    # Get database manager for user's database
    db_manager = get_database_manager(
        st.session_state.db_type,
        st.session_state.db_connection
    )

    # Get project information
    project_key = st.session_state.project_key

    try:
        # Get translators for this project
        translators = asyncio.run(db_manager.get_project_translators(project_key))

        # Get project metadata
        project = asyncio.run(db_manager.get_project(project_key))

        # Display overview metrics
        st.markdown("---")
        st.markdown("### 📊 Quick Overview")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Project Key",
                value=project_key,
                help="Share this key with translators"
            )

        with col2:
            st.metric(
                label="Total Translators",
                value=len(translators),
                help="Number of translators in your project"
            )

        with col3:
            db_type_display = {
                'free_supabase': 'Free Supabase',
                'mongodb': 'MongoDB',
                'supabase': 'Custom Supabase'
            }.get(st.session_state.db_type, 'Unknown')

            st.metric(
                label="Database Type",
                value=db_type_display,
                help="Your chosen database backend"
            )

        with col4:
            # Count total segments with progress
            total_segments = 0
            for translator in translators:
                try:
                    metrics_df, _, _, _ = asyncio.run(
                        db_manager.load_progress(translator['name'], translator['surname'])
                    )
                    if not metrics_df.empty:
                        total_segments += len(metrics_df)
                except:
                    pass

            st.metric(
                label="Total Segments Edited",
                value=total_segments,
                help="Total segments edited by all translators"
            )

        # Display project information
        st.markdown("---")
        st.markdown("### 📁 Project Information")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Project Details**")
            if project:
                st.write(f"**Created:** {project.get('created_at', 'N/A')}")
                st.write(f"**PM Name:** {project.get('pm_name', 'N/A')} {project.get('pm_surname', 'N/A')}")

                # Load project files to get filenames
                try:
                    files = asyncio.run(db_manager.load_project_files(project_key))
                    if files:
                        st.write(f"**Source File:** {files[0]}")
                        st.write(f"**Translation File:** {files[1]}")
                except:
                    st.write("*File information not available*")
            else:
                st.info("No project data found.")

        with col2:
            st.markdown("**Translator List**")
            if translators:
                for translator in translators:
                    st.write(f"• {translator['name']} {translator['surname']}")
            else:
                st.info("No translators have joined yet.")

        # Display translator activity
        st.markdown("---")
        st.markdown("### 🔄 Recent Activity")

        if translators:
            activity_data = []

            for translator in translators:
                try:
                    metrics_df, full_text, time_tracker, _ = asyncio.run(
                        db_manager.load_progress(translator['name'], translator['surname'])
                    )

                    if not metrics_df.empty:
                        activity_data.append({
                            'Translator': f"{translator['name']} {translator['surname']}",
                            'Segments Completed': len(metrics_df),
                            'Total Edit Time (s)': metrics_df['edit_time'].sum() if 'edit_time' in metrics_df else 0,
                            'Total Insertions': metrics_df['insertions'].sum() if 'insertions' in metrics_df else 0,
                            'Total Deletions': metrics_df['deletions'].sum() if 'deletions' in metrics_df else 0,
                            'Status': '✅ Active' if len(full_text) > 0 else '⏸️ Idle'
                        })
                except:
                    continue

            if activity_data:
                df = pd.DataFrame(activity_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No activity data available yet. Translators haven't started working.")
        else:
            st.info("No translators have joined your project yet. Share your project key with translators to get started.")

        # Navigation to other pages
        st.markdown("---")
        st.markdown("### 🧭 Navigation")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.page_link("pages/1_📊_Analytics.py", label="📊 View Analytics", use_container_width=True)

        with col2:
            st.page_link("pages/2_👥_Users.py", label="👥 Manage Users", use_container_width=True)

        with col3:
            st.page_link("pages/3_📁_Export.py", label="📁 Export Data", use_container_width=True)

    except Exception as e:
        st.error(f"Error loading dashboard data: {str(e)}")
        if st.checkbox("Show error details"):
            st.exception(e)


def main():
    """Main application logic"""
    # Load CSS
    load_css()

    # Initialize session state
    init_session_state()

    # Sidebar
    with st.sidebar:
        st.markdown("## 🏢 PM Dashboard")
        st.markdown("---")

        if st.session_state.authenticated:
            st.success(f"Logged in as:\n**{st.session_state.pm_name} {st.session_state.pm_surname}**")
            st.info(f"Project Key:\n`{st.session_state.project_key}`")

            st.markdown("---")

            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.pm_name = ""
                st.session_state.pm_surname = ""
                st.session_state.role = ""
                st.session_state.project_key = ""
                st.session_state.db_type = None
                st.session_state.db_connection = None
                st.rerun()
        else:
            st.info("Please log in to access the dashboard.")

    # Main content
    if not st.session_state.authenticated:
        login_page()
    else:
        dashboard_page()


if __name__ == "__main__":
    main()
