import streamlit as st
import pandas as pd
from typing import List, Tuple
import time
from dataclasses import dataclass
from pathlib import Path
import difflib
import json
from pymongo import AsyncMongoClient
from datetime import datetime, timezone, timedelta
import pytz
from time_tracker import TimeTracker
import asyncio
import hashlib
import string

# Initialize session state for layout preference if not exists
if 'layout_preference' not in st.session_state:
    st.session_state['layout_preference'] = 'centered'

st.set_page_config(
    page_title="MT Post-Editing Tool",
    page_icon="🌍",
    layout=st.session_state['layout_preference']
)

st.title("🌍 UniOr Post-Editing MT Tool")

# Inline HTML/CSS for a badge-like label
badge_html = f"""
<span style="
    display: inline-block;
    background-color: #ECF9EC;
    color: #1B7F1B;
    border: 1px solid #1B7F1B;
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 0.85em;">
  v{st.secrets["VERSION"]}
</span>
"""

st.markdown(badge_html, unsafe_allow_html=True)

st.logo("static/logo.png", size="large",
        link=None, icon_image="static/icon.png")

#  hide_st_style = """
#     <style>
#     #MainMenu {visibility: hidden;}
#     header {visibility: hidden;}
#     footer {visibility: hidden;}
#     </style>
#  """
#
# st.markdown(hide_st_style, unsafe_allow_html=True)

# Inject custom CSS to adjust the logo size
st.markdown(
    """
    <style>
    div[data-testid="stSidebarHeader"] > img {
        height: 150px; /* Set your desired height */
    }
    </style>
    """,
    unsafe_allow_html=True
)

@dataclass
class EditMetrics:
    """Class to store metrics for each segment edit"""
    segment_id: int
    source: str
    original: str
    edited: str
    edit_time: float
    insertions: int
    deletions: int


def calculate_edit_distance(original: str, edited: str) -> Tuple[int, int]:
    """Calculate insertions and deletions between original and edited text, ignoring punctuation"""
    # Remove punctuation and split
    translator = str.maketrans('', '', string.punctuation)
    original_words = original.translate(translator).split()
    edited_words = edited.translate(translator).split()

    d = difflib.Differ()
    diff = list(d.compare(original_words, edited_words))

    insertions = len([d for d in diff if d.startswith('+')])
    deletions = len([d for d in diff if d.startswith('-')])

    return insertions, deletions


def load_segments(source_file, translation_file) -> List[Tuple[str, str]]:
    """Return 1-to-1 tuples of (source_line, translation_line), preserving blanks."""
    if source_file is None or translation_file is None:
        return []

    source_lines      = source_file.getvalue().decode("utf-8").splitlines()
    translation_lines = translation_file.getvalue().decode("utf-8").splitlines()

    source_lines      = [line.rstrip('\r') for line in source_lines]
    translation_lines = [line.rstrip('\r') for line in translation_lines]

    if source_lines and translation_lines and source_lines[-1] == translation_lines[-1] == '':
        source_lines.pop(); translation_lines.pop()

    if len(source_lines) != len(translation_lines):
        raise ValueError(
            f"Line count mismatch: source has {len(source_lines)}, "
            f"translation has {len(translation_lines)}"
        )

    return list(zip(source_lines, translation_lines))


async def init_session_state():
    """Initialize session state variables"""
    if 'current_segment' not in st.session_state:
        st.session_state.current_segment = 0
    if 'segments' not in st.session_state:
        st.session_state.segments = []
    if 'edit_metrics' not in st.session_state:
        st.session_state.edit_metrics = []
    if 'segment_start_times' not in st.session_state:
        st.session_state.segment_start_times = {}
    if 'original_texts' not in st.session_state:
        st.session_state.original_texts = {}
    if 'user_name' not in st.session_state:
        st.session_state.user_name = ""
    if 'user_surname' not in st.session_state:
        st.session_state.user_surname = ""
    if 'role' not in st.session_state:
        st.session_state.role = ""
    if 'time_tracker' not in st.session_state:
        st.session_state.time_tracker = TimeTracker()
    if 'active_segment' not in st.session_state:
        st.session_state.active_segment = None
    if 'last_saved' not in st.session_state:
        st.session_state.last_saved = None
    if 'auto_save' not in st.session_state:
        st.session_state.auto_save = True
    if 'idle_timer_enabled' not in st.session_state:
        st.session_state.idle_timer_enabled = True
    if 'horizontal_view' not in st.session_state:
        st.session_state.horizontal_view = False
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'timer_mode' not in st.session_state:
        st.session_state.timer_mode = None
    if 'has_loaded_segments' not in st.session_state:
        st.session_state.has_loaded_segments = False
    if 'db_type' not in st.session_state:
        st.session_state.db_type = None
    if 'db_connection' not in st.session_state:
        st.session_state.db_connection = None


async def load_css():
    """Load and apply custom CSS styles"""
    with open("static/styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def highlight_differences(original: str, edited: str) -> str:
    """Create HTML with highlighted differences, ignoring punctuation"""
    # Remove punctuation and split
    translator = str.maketrans('', '', string.punctuation)
    original_words = original.translate(translator).split()
    edited_words = edited.translate(translator).split()

    d = difflib.Differ()
    diff = list(d.compare(original_words, edited_words))

    html_parts = []
    for word in diff:
        if word.startswith('  '):
            html_parts.append(f'<span>{word[2:]}</span>')
        elif word.startswith('- '):
            html_parts.append(
                f'<span style="background-color: #ffcdd2">{word[2:]}</span>')
        elif word.startswith('+ '):
            html_parts.append(
                f'<span style="background-color: #c8e6c9">{word[2:]}</span>')

    return ' '.join(html_parts)


async def save_to_database(user_name: str, user_surname: str, metrics_df: pd.DataFrame):
    """Save metrics and full text to database"""
    from db_manager import get_database_manager

    # Get the user's database manager
    db_manager = get_database_manager(
        st.session_state.get('db_type'),
        st.session_state.get('db_connection')
    )

    # Save progress
    await db_manager.save_progress(
        user_name,
        user_surname,
        metrics_df,
        st.session_state.segments,
        st.session_state.time_tracker.to_dict(),
        st.session_state.timer_mode
    )


async def load_from_database(user_name: str, user_surname: str) -> Tuple[pd.DataFrame, List[str]]:
    """Load metrics and full text from database"""
    from db_manager import get_database_manager

    # Get the user's database manager
    db_manager = get_database_manager(
        st.session_state.get('db_type'),
        st.session_state.get('db_connection')
    )

    # Load progress
    metrics_df, full_text, time_tracker_dict, timer_mode = await db_manager.load_progress(
        user_name,
        user_surname
    )

    # Update session state with loaded data
    if timer_mode:
        st.session_state.timer_mode = timer_mode
        # Create TimeTracker with the correct timer mode
        st.session_state.time_tracker = TimeTracker()
        st.session_state.time_tracker.set_timer_mode(timer_mode)

    # Load time tracker data
    if time_tracker_dict:
        st.session_state.time_tracker = TimeTracker.from_dict(
            time_tracker_dict,
            timer_mode=timer_mode
        )

    return metrics_df, full_text




def verify_time_recorded(segment_id: int) -> bool:
    """Verify that time was recorded for the segment"""
    if segment_id not in st.session_state.time_tracker.sessions:
        return False

    edit_time = st.session_state.time_tracker.get_editing_time(segment_id)

    return edit_time > 1


@st.dialog("📖 How to Use UniOr-PET", width="large")
def show_instructions():
    """Display instructions modal"""

    # Two columns for different user types
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 👨‍💻 For Translators")
        st.markdown("""
        1. First, please obtain a **project key** from your Project Manager.
        2. **Register** your account using the project key you received.
        3. **Login** to your workspace, and your assigned files will load automatically.
        4. You can now edit segments one by one while the tool tracks your time.
        5. Don't worry about saving - your progress automatically saves to your PM's database.
        """)

    with col2:
        st.markdown("#### 👔 For Project Managers")
        st.markdown("""
        1. Please **register** your account and upload both your source and translation files.
        2. Choose your database: we recommend **Free Supabase**, or you can use your own MongoDB/Supabase.
        3. You'll receive a unique **project key** after registration.
        4. Share this key with your translators, and they'll automatically receive your files.
        5. All translators will use your chosen data, so you can monitor their progress.
        """)

    st.divider()

    # Key features with a cooler layout
    st.markdown("### ✨Key Features")
    # Empty line for spacing
    st.markdown("")

    # Create 3 columns for a grid layout
    row1_col1, row1_col2, row1_col3 = st.columns(3)

    with row1_col1:
        with st.container(border=True):
            st.markdown("### ⏱️")
            st.markdown("**Time Tracking**")
            st.caption("Automatic editing time recording per segment")

    with row1_col2:
        with st.container(border=True):
            st.markdown("### 📊")
            st.markdown("**Quality Metrics**")
            st.caption("Track insertions, deletions & editing patterns")

    with row1_col3:
        with st.container(border=True):
            st.markdown("### 💾")
            st.markdown("**Auto-Save**")
            st.caption("Cloud backup of your work in real-time")

    row2_col1, row2_col2, row2_col3 = st.columns(3)

    with row2_col1:
        with st.container(border=True):
            st.markdown("### 📖")
            st.markdown("**Context View**")
            st.caption("See surrounding segments while editing")

    with row2_col2:
        with st.container(border=True):
            st.markdown("### 👀")
            st.markdown("**Review mode**")
            st.caption("Review and search all your edits at once")

    with row2_col3:
        with st.container(border=True):
            st.markdown("### 🔒")
            st.markdown("**Data Security**")
            st.caption("Your data is encrypted and protected")

    st.divider()

    # Contact info at the bottom
    st.info("💬 **Need Help?** Contact antonio.castaldo@phd.unipi.it")

def display_review_page():
    """Display the review page for all segments"""
    st.markdown("## 👀 Review All Segments")

    # Back button
    if st.button("← Back to Editing"):
        st.session_state.show_review_page = False
        st.rerun()

    if not st.session_state.segments:
        st.info("No segments loaded yet.")
        return

    # Create a DataFrame with all segments first
    all_segments = []
    for idx, (source, translation) in enumerate(st.session_state.segments):
        # Find if there's an edit for this segment
        edit_metric = next(
            (m for m in st.session_state.edit_metrics if m.segment_id == idx),
            None
        )

        if edit_metric:
            # Use the edited version
            segment_data = vars(edit_metric)
        else:
            # Create an entry for unedited segment
            segment_data = {
                'segment_id': idx,
                'source': source,
                'original': translation,
                'edited': translation,  # Same as original for unedited
                'edit_time': 0,
                'insertions': 0,
                'deletions': 0
            }
        all_segments.append(segment_data)

    # Convert to DataFrame
    review_df = pd.DataFrame(all_segments)

    # Add computed columns for better display
    review_df['total_edits'] = review_df['insertions'] + review_df['deletions']
    review_df['time_formatted'] = review_df['edit_time'].apply(
        lambda x: f"{int(x // 60)}m {int(x % 60)}s"
    )
    review_df['status'] = review_df.apply(
        lambda row: "Modified" if (row['insertions'] > 0 or row['deletions'] > 0) else "Unchanged",
        axis=1
    )

    # Create a display DataFrame with selected columns
    display_df = pd.DataFrame()
    display_df['Segment'] = review_df['segment_id'] + 1  # 1-based indexing for display
    display_df['Source Text'] = review_df['source']
    display_df['Original Translation'] = review_df['original']
    display_df['Post-Edited'] = review_df['edited']
    display_df['Edit Time'] = review_df['time_formatted']
    display_df['Total Edits'] = review_df['total_edits']
    display_df['Status'] = review_df['status']

    # Add filters above the table
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        search = st.text_input("🔍 Search in any field")
    with col2:
        status_filter = st.multiselect(
            "Filter by Status",
            ["Modified", "Unchanged"],
            default=["Modified", "Unchanged"]
        )
    with col3:
        sort_by = st.selectbox(
            "Sort by",
            ["Segment", "Edit Time", "Total Edits"]
        )

    # Apply filters
    filtered_df = display_df.copy()
    if search:
        mask = filtered_df.astype(str).apply(
            lambda x: x.str.contains(search, case=False)
        ).any(axis=1)
        filtered_df = filtered_df[mask]

    # Fix status filtering
    if status_filter:
        filtered_df = filtered_df[filtered_df['Status'].isin(status_filter)]

    # Apply sorting
    if sort_by == "Segment":
        filtered_df = filtered_df.sort_values("Segment")
    elif sort_by == "Edit Time":
        filtered_df = filtered_df.sort_values("Edit Time", ascending=False)
    elif sort_by == "Total Edits":
        filtered_df = filtered_df.sort_values("Total Edits", ascending=False)

    # Display the table
    st.dataframe(
        filtered_df,
        hide_index=True,
        use_container_width=True
    )

    # Add segment selection below the table
    st.divider()
    selected_segment = st.number_input(
        "Enter segment number to edit",
        min_value=1,
        max_value=len(st.session_state.segments),
        value=1,
        help="Enter the segment number you want to edit"
    )
    if st.button("Jump to Segment", type="primary", use_container_width=True):
        st.session_state.current_segment = selected_segment - 1  # Convert to 0-based index
        st.session_state.show_review_page = False
        st.rerun()

def main():
    asyncio.run(load_css())
    asyncio.run(init_session_state())

    # Initialize review page state if not exists
    if 'show_review_page' not in st.session_state:
        st.session_state.show_review_page = False

    if not st.session_state.authenticated:

        # Welcome message with improved styling
        st.markdown("""
            <div class="welcome-card">
                <p>Access your personalized post-editing workspace by logging in or creating a new account.</p>
            </div>
            """, unsafe_allow_html=True)

        # Button to open instructions modal
        if st.button("📖 How to Use UniOr-PET", type="secondary"):
            show_instructions()

        # Login/Register tabs with improved styling
        tabs = st.tabs(["🔑 Login", "✨ Register"])

        with tabs[0]:
            with st.form("login_form"):
                st.subheader("Welcome Back!")
                name = st.text_input("Name", key="login_name", placeholder="Enter your name")
                surname = st.text_input("Surname", key="login_surname", placeholder="Enter your surname")
                password = st.text_input("Password", type="password", key="login_password",
                                      placeholder="Enter your password")

                submit_button = st.form_submit_button("Sign In", use_container_width=True)

                # Add this new block to handle login
                if submit_button:
                    if name and surname and password:
                        with st.spinner("Verifying credentials..."):
                            from db_manager import get_database_manager

                            # First, verify with default database (where user accounts are stored)
                            db_manager = get_database_manager()
                            authenticated, role, db_type, db_connection = asyncio.run(
                                db_manager.verify_user(name, surname, password)
                            )

                            if authenticated:
                                st.session_state.authenticated = True
                                st.session_state.user_name = name
                                st.session_state.user_surname = surname
                                st.session_state.role = role
                                st.session_state.db_type = db_type
                                st.session_state.db_connection = db_connection

                                # Redirect Project Managers to management interface
                                if role == "project_manager":
                                    st.error("⛔ Project Managers cannot access the editing interface.")
                                    st.info("""
                                    ### Please use the Project Manager Dashboard

                                    Run the management interface:
                                    ```bash
                                    streamlit run management/0_🏢_Manager.py --server.port 8502
                                    ```

                                    Or access it at: http://localhost:8502
                                    """)
                                    st.stop()

                                # Auto-load for translators: prioritize saved progress, fallback to project files
                                if role == "translator":
                                    try:
                                        # Get user's database manager
                                        user_db_manager = get_database_manager(db_type, db_connection)

                                        # First, try to load saved progress
                                        try:
                                            metrics_df, full_text, time_tracker_dict, timer_mode = asyncio.run(
                                                user_db_manager.load_progress(name, surname)
                                            )

                                            if full_text and len(full_text) > 0:
                                                # Saved progress exists - load it
                                                st.session_state.segments = full_text
                                                st.session_state.has_loaded_segments = True
                                                st.session_state.auto_loaded_from_project = False

                                                # Load edit metrics
                                                if not metrics_df.empty:
                                                    st.session_state.edit_metrics = [
                                                        EditMetrics(**row) for row in metrics_df.to_dict('records')
                                                    ]

                                                # Load timer data
                                                if timer_mode:
                                                    st.session_state.timer_mode = timer_mode
                                                if time_tracker_dict:
                                                    from time_tracker import TimeTracker
                                                    st.session_state.time_tracker = TimeTracker.from_dict(
                                                        time_tracker_dict,
                                                        timer_mode=timer_mode
                                                    )
                                            else:
                                                # No saved progress, load fresh project files
                                                raise ValueError("No saved progress")
                                        except:
                                            # No saved progress, load fresh project files
                                            project_key = asyncio.run(user_db_manager.get_user_project_key(name, surname))

                                            if project_key:
                                                # Load project files
                                                file_data = asyncio.run(user_db_manager.load_project_files(project_key))

                                                if file_data:
                                                    source_filename, translation_filename, source_content, translation_content = file_data

                                                    # Convert content to segments
                                                    from io import BytesIO

                                                    source_file_obj = BytesIO(source_content.encode('utf-8'))
                                                    translation_file_obj = BytesIO(translation_content.encode('utf-8'))

                                                    # Set names for the objects
                                                    source_file_obj.name = source_filename
                                                    translation_file_obj.name = translation_filename

                                                    # Load segments
                                                    segments = load_segments(source_file_obj, translation_file_obj)
                                                    st.session_state.segments = segments
                                                    st.session_state.has_loaded_segments = True
                                                    st.session_state.auto_loaded_from_project = True
                                                else:
                                                    st.session_state.auto_loaded_from_project = False
                                            else:
                                                st.session_state.auto_loaded_from_project = False
                                    except Exception as e:
                                        st.warning(f"Could not auto-load files: {str(e)}")
                                        st.session_state.auto_loaded_from_project = False

                                st.success("Login successful!")
                                st.rerun()
                            else:
                                st.error("Invalid credentials. Please try again.")
                    else:
                        st.error("Please fill in all fields")

            st.markdown("""
                        </form>
                    </div>
                    <div class="info-sidebar">
                        <h4>Why Sign In?</h4>
                        <ul>
                            <li>Save your progress automatically</li>
                            <li>Resume your work anytime</li>
                            <li>Track your editing statistics</li>
                            <li>Access advanced features</li>
                        </ul>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with tabs[1]:
            st.subheader("Create Account")

            # Role selection outside form for reactive UI
            role = st.selectbox(
                "I am a...",
                ["Translator", "Project Manager"],
                key="reg_role"
            )

            # File upload for PM - must be outside form
            if role == "Project Manager":
                st.markdown("**Project Files**")
                st.info("Upload your source and translation files. These will be automatically loaded for all translators in your project.")

                pm_source_file = st.file_uploader(
                    "Source text file (one sentence per line)",
                    type=['txt'],
                    key="pm_source_upload",
                    help="This file will be stored and shared with all translators"
                )
                pm_translation_file = st.file_uploader(
                    "Translation file (one sentence per line)",
                    type=['txt'],
                    key="pm_translation_upload",
                    help="This file will be stored and shared with all translators"
                )

                # Validate files if uploaded
                if pm_source_file and pm_translation_file:
                    try:
                        # Store in session state for use in form
                        st.session_state.pm_files_validated = True
                        st.session_state.pm_source_file = pm_source_file
                        st.session_state.pm_translation_file = pm_translation_file

                        # Validate files can be loaded
                        test_segments = load_segments(pm_source_file, pm_translation_file)
                        st.success(f"✅ Files validated: {len(test_segments)} segments found")
                    except ValueError as e:
                        st.error(f"❌ File validation error: {str(e)}")
                        st.session_state.pm_files_validated = False
                else:
                    st.session_state.pm_files_validated = False

            with st.form("register_form"):
                new_name = st.text_input("Name", key="reg_name", placeholder="Enter your name")
                new_surname = st.text_input("Surname", key="reg_surname", placeholder="Enter your surname")

                # Password fields in columns for better layout
                pass_col1, pass_col2 = st.columns(2)
                with pass_col1:
                    new_password = st.text_input("Password", type="password",
                                               key="reg_password",
                                               placeholder="Choose password")
                with pass_col2:
                    confirm_password = st.text_input("Confirm Password",
                                                   type="password",
                                                   placeholder="Repeat password")

                # Password requirements hint
                st.caption("""
                    Password requirements:
                    - At least 8 characters
                    - Mix of letters and numbers
                    """)

                # Initialize variables that may not be defined depending on role
                db_choice = None
                db_connection = None
                project_key = None

                # Show different configuration based on role
                if role == "Project Manager":
                    # Database selection - only for Project Managers
                    st.markdown("**Database Configuration**")
                    db_choice = st.selectbox(
                        "Database Option",
                        ["Free Supabase (Recommended)", "My Own MongoDB", "My Own Supabase"],
                        help="Choose where to store your project data"
                    )

                    # Show connection string input based on choice
                    db_connection = None
                    if db_choice == "My Own MongoDB":
                        db_connection = st.text_input(
                            "MongoDB Connection String",
                            type="password",
                            help="Enter your MongoDB connection string: mongodb+srv://username:password@cluster.domain/database",
                            placeholder="mongodb+srv://..."
                        )
                    elif db_choice == "My Own Supabase":
                        supabase_url = st.text_input(
                            "Supabase Project URL",
                            placeholder="https://yourproject.supabase.co",
                            help="Your Supabase project URL"
                        )
                        supabase_key = st.text_input(
                            "Supabase API Key",
                            type="password",
                            placeholder="Your API key",
                            help="Your Supabase anon/public API key"
                        )
                        # Combine URL and key with | separator
                        if supabase_url and supabase_key:
                            db_connection = f"{supabase_url}|{supabase_key}"
                else:
                    # Project key input - only for Translators
                    st.markdown("**Project Access**")
                    project_key = st.text_input(
                        "Project Key",
                        placeholder="Enter your project key",
                        help="Ask your Project Manager for the project key"
                    )

                register_button = st.form_submit_button("Create Account", use_container_width=True)

                if register_button:
                    if new_name and new_surname and new_password:
                        if len(new_password) < 8:
                            st.error("Password must be at least 8 characters long")
                            return

                        if new_password != confirm_password:
                            st.error("Passwords do not match")
                            return

                        from db_manager import get_database_manager, validate_database_connection

                        # Convert role selection to database value
                        db_role = "project_manager" if role == "Project Manager" else "translator"

                        db_type = None
                        db_connection = None
                        project_key_value = None

                        if role == "Project Manager":
                            # Validate files are uploaded
                            if not st.session_state.get('pm_files_validated', False):
                                st.error("❌ Both source and translation files are required for Project Managers")
                                return

                            # Get files from session state
                            pm_source_file = st.session_state.pm_source_file
                            pm_translation_file = st.session_state.pm_translation_file

                            # Determine database type for Project Managers
                            if db_choice == "Free Supabase (Recommended)":
                                db_type = "free_supabase"
                            elif db_choice == "My Own MongoDB":
                                db_type = "mongodb"
                                if not db_connection:
                                    st.error("MongoDB connection string is required")
                                    return
                            elif db_choice == "My Own Supabase":
                                db_type = "supabase"
                                if not db_connection:
                                    st.error("Supabase URL and API key are required")
                                    return

                            # Validate custom database connections
                            if db_type in ["mongodb", "supabase"]:
                                is_valid, error_msg = validate_database_connection(db_type, db_connection)
                                if not is_valid:
                                    st.error(f"Invalid database connection: {error_msg}")
                                    return
                        else:
                            # For Translators, validate project key
                            if not project_key:
                                st.error("Project key is required for Translators")
                                return

                            # Validate project key and get PM's database settings
                            from db_manager import validate_project_key_and_get_pm_settings
                            is_valid, pm_db_type, pm_db_connection, error_msg = asyncio.run(
                                validate_project_key_and_get_pm_settings(project_key)
                            )

                            if not is_valid:
                                st.error(f"Invalid project key: {error_msg}")
                                return

                            # Store the project key (for reference), but the translator will use PM's db settings
                            project_key_value = project_key
                            # Translators inherit PM's database settings
                            db_type = pm_db_type
                            db_connection = pm_db_connection

                        with st.spinner("Creating your account..."):
                            # Get the appropriate database manager (always use default for user creation)
                            db_manager = get_database_manager()

                            # Create user with database preferences
                            # Note: db_type and db_connection are set for both PMs and translators
                            # For translators, they inherit PM's settings
                            if asyncio.run(db_manager.create_user(
                                new_name,
                                new_surname,
                                new_password,
                                db_role,
                                db_type,
                                db_connection,
                                project_key_value
                            )):
                                st.success("✅ Registration successful!")

                                if role == "Project Manager":
                                    # Create project and save files
                                    project_key = f"{new_surname}_{new_name}"

                                    try:
                                        # Get PM's database manager (where project data will be stored)
                                        pm_db_manager = get_database_manager(db_type, db_connection)

                                        # Create project record
                                        asyncio.run(pm_db_manager.create_project(
                                            project_key,
                                            new_name,
                                            new_surname,
                                            db_type,
                                            db_connection
                                        ))

                                        # Save project files
                                        source_content = pm_source_file.getvalue().decode("utf-8")
                                        translation_content = pm_translation_file.getvalue().decode("utf-8")

                                        # Re-validate to get segment count
                                        segments = load_segments(pm_source_file, pm_translation_file)

                                        asyncio.run(pm_db_manager.save_project_files(
                                            project_key,
                                            pm_source_file.name,
                                            pm_translation_file.name,
                                            source_content,
                                            translation_content,
                                            len(segments)
                                        ))

                                        st.success("✅ Project files uploaded successfully!")
                                        st.info("Your project key is: **" + project_key + "**")
                                        st.info("Share this key with your translators so they can join your project")
                                    except Exception as e:
                                        st.error(f"❌ Error saving project files: {str(e)}")
                                        st.warning("Your account was created but files were not saved. Please contact support.")
                                else:
                                    st.info("Please proceed to login with your credentials")

                                # Clear registration fields and file state
                                st.session_state.pop('reg_name', None)
                                st.session_state.pop('reg_surname', None)
                                st.session_state.pop('reg_password', None)
                                st.session_state.pop('pm_files_validated', None)
                                st.session_state.pop('pm_source_file', None)
                                st.session_state.pop('pm_translation_file', None)
                            else:
                                st.error("An account with these details already exists")
                    else:
                        st.error("Please fill in all fields")

            st.markdown("""
                <div class="info-sidebar">
                    <h4>Benefits of Registration</h4>
                    <ul>
                        <li>Free access to all features</li>
                        <li>Secure data storage</li>
                        <li>Progress tracking</li>
                        <li>Cloud backup of your work</li>
                    </ul>
                </div>
            """, unsafe_allow_html=True)

        # Footer with additional information
        st.markdown("""
            <div class="login-footer">
                <p>By using this tool, you agree to our Terms of Service and Privacy Policy</p>
                <p>Need help? Contact <a href="mailto:antonio.castaldo@phd.unipi.it">antonio.castaldo@phd.unipi.it</a></p>
            </div>
            """, unsafe_allow_html=True)

        return

    # If authenticated, show sidebar and main content
    with st.sidebar:
        st.write("Welcome to the **MT Post-Editing Tool**.")
        st.markdown("## 🧑‍💻 Tool Settings")

        # Show user info and logout button
        st.write(f"Logged in as: **{st.session_state.user_name} {st.session_state.user_surname}**")
        if st.button("🚪 Logout", use_container_width=True):
            # Clear session state
            st.session_state.authenticated = False
            st.session_state.user_name = ""
            st.session_state.user_surname = ""
            st.rerun()

        # Settings section only shown when logged in
        st.divider()

        # Add Review All button at the top of settings
        if st.button("👀 Review All Segments", use_container_width=True):
            st.session_state.show_review_page = True
            st.rerun()

        st.write("💾 **Save and Load**")

        # Auto-save toggle

        st.session_state.auto_save = st.toggle(
            "Auto-Save", value=st.session_state.auto_save, help="Automatically save your progress as you edit")

        # Idle timer toggle
        st.session_state.idle_timer_enabled = st.toggle(
            "Idle Timer",
            value=False if st.session_state.timer_mode == "pet" else st.session_state.idle_timer_enabled,
            help="When enabled, time spent idle (no activity for 30+ seconds) will be tracked separately",
            disabled=st.session_state.timer_mode == "pet"
        )

        # Show last saved time if available
        if st.session_state.last_saved:
            local_tz = pytz.timezone('Europe/Rome')
            local_time = st.session_state.last_saved.astimezone(local_tz)
            st.caption(
                f"Last saved: {local_time.strftime('%Y-%m-%d %H:%M:%S')}")

        col1, col2 = st.columns(2)
        with col1:
            # Save/Load buttons
            if st.button("💾 Save",  use_container_width=True, disabled=True):
                if st.session_state.segments:
                    with st.spinner("Saving progress..."):
                    # Save current segment's metrics first
                        current_source, current_translation = st.session_state.segments[st.session_state.current_segment]
                        edited_text = st.session_state[f"edit_area_{st.session_state.current_segment}"]
                        save_metrics(current_source, current_translation, edited_text)

                        # Then save everything to database
                        df = pd.DataFrame([vars(m) for m in st.session_state.edit_metrics])
                        asyncio.run(save_to_database(
                            st.session_state.user_name,
                            st.session_state.user_surname,
                            df))
                        st.session_state.last_saved = datetime.now(timezone.utc)
                        st.success("Progress saved!")

        with col2:
            if st.button("📂 Load", use_container_width=True, disabled=st.session_state.has_loaded_segments):
                with st.spinner("Loading previous work..."):
                    existing_data, full_text = asyncio.run(
                        load_from_database(st.session_state.user_name,
                                        st.session_state.user_surname))

                if not existing_data.empty and full_text:
                    # Create edit metrics from loaded data
                    st.session_state.edit_metrics = [
                        EditMetrics(
                            segment_id=row['segment_id'],
                            source=row['source'],
                            original=row['original'],
                            edited=row['edited'],
                            edit_time=row['edit_time'],
                            insertions=row['insertions'],
                            deletions=row['deletions']
                        )
                        for _, row in existing_data.iterrows()
                    ]

                    # Set segments and current segment
                    st.session_state.segments = full_text
                    st.session_state.has_loaded_segments = True

                    # Find the last edited segment
                    if st.session_state.edit_metrics:
                        last_edited_segment = max(
                            m.segment_id for m in st.session_state.edit_metrics)
                        st.session_state.current_segment = last_edited_segment
                    else:
                        st.session_state.current_segment = 0

                    # Reset timer states for all segments
                    if st.session_state.timer_mode == "pet":
                        # Clear all waiting time states
                        keys_to_remove = [key for key in st.session_state.keys() if key.startswith('remaining_wait_time_')]
                        for key in keys_to_remove:
                            del st.session_state[key]
                        # Reset timer states in TimeTracker
                        for segment_id in range(len(full_text)):
                            if segment_id in st.session_state.time_tracker.sessions:
                                st.session_state.time_tracker.pause_pet_timer(segment_id)
                                st.session_state.time_tracker.sessions[segment_id].segment_view_time = None

                    st.success("Previous work loaded!")
                    st.rerun()
                else:
                    st.warning("No previous work found.")

        # Add Clear Progress button with confirmation
        if st.button("🗑️ Clear Progress", type="secondary", use_container_width=True):
            # Show confirmation dialog
            if 'show_clear_confirm' not in st.session_state:
                st.session_state.show_clear_confirm = True
                st.rerun()

        # Show confirmation dialog
        if st.session_state.get('show_clear_confirm', False):
            st.warning("⚠️ Are you sure you want to clear all progress? This cannot be undone!")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yes, Clear Everything", type="primary", use_container_width=True):
                    # Clear all progress
                    st.session_state.edit_metrics = []
                    st.session_state.segments = []
                    st.session_state.current_segment = 0
                    st.session_state.original_texts = {}
                    st.session_state.time_tracker = TimeTracker()
                    st.session_state.active_segment = None
                    st.session_state.last_saved = None
                    st.session_state.timer_mode = None  # Reset timer mode
                    st.session_state.has_loaded_segments = False  # Reset loaded segments flag

                    # Clear from database
                    asyncio.run(save_to_database(
                        st.session_state.user_name,
                        st.session_state.user_surname,
                        pd.DataFrame()  # Empty DataFrame to clear progress
                    ))

                    # Reset confirmation dialog state
                    st.session_state.show_clear_confirm = False
                    st.success("Progress cleared successfully!")
                    st.rerun()

            with col2:
                if st.button("No, Keep My Progress", type="secondary", use_container_width=True):
                    # Reset confirmation dialog state
                    st.session_state.show_clear_confirm = False
                    st.rerun()

    # If authenticated, show either the review page or the main editing interface
    if st.session_state.show_review_page:
        display_review_page()
    else:
        # Only show main content if authenticated
        if st.session_state.authenticated:
            # Instructions
            st.markdown("""
                <div class="card pt-serif">
                    <p><strong>Hi, I'm Antonio. 👋</strong></p>
                    <p>I'm a PhD candidate in Artificial Intelligence at the University of Pisa, working on Creative Machine Translation with LLMs.</p>
                    <p>My goal is to develop translation systems that can preserve style, tone, and creative elements while accurately conveying meaning across languages.</p>
                    <p>Learn more about me at <a href="https://www.ancastal.com" target="_blank">www.ancastal.com</a></p>
                </div>
            """, unsafe_allow_html=True)

            with st.expander("Instructions", expanded=False):
                st.image("static/pet_infographic.png")

            st.markdown("""
                        <div class="info-card">
                            <p class="pt-serif text-sm"><strong>Thanks for using my tool! 😊</strong></p>
                            <p class="text-center text-muted">Feel free to send me an email for any feedback or suggestions.</p>
                        </div>
                        """, unsafe_allow_html=True)
            st.warning("⚠️ Copy-paste operations are not allowed. Please type your edits manually.")
            asyncio.run(init_session_state())

            # File upload with styled container - only show if no segments are loaded
            if len(st.session_state.segments) == 0:
                # Check if files were auto-loaded from project
                if st.session_state.get('auto_loaded_from_project', False):
                    st.info("✅ Project files have been automatically loaded from your project.")
                    st.info("If you need to reload, use the '📂 Load' button in the sidebar.")
                else:
                    st.info("If you have a previous project, load it by clicking on the '📂 Load' button in the sidebar!")
                    with st.container():
                        source_file = st.file_uploader(
                            "Upload source text file (one sentence per line)",
                            type=['txt'],
                            key="source_upload"
                        )
                        translation_file = st.file_uploader(
                            "Upload translation file (one sentence per line)",
                            type=['txt'],
                            key="translation_upload"
                        )

                    if source_file and translation_file:
                        # Add timer mode selection before loading segments
                        if st.session_state.timer_mode is None:
                            st.divider()
                            st.write("### 🕒 Timer Mode")
                            timer_mode = st.radio(
                                "Choose your preferred timer mode:",
                                ["Current Timer", "PET Timer"],
                                help="""
                                **Current Timer**: Automatically tracks time as you edit.\n
                                **PET Timer**: Manual start/pause control with editing disabled while paused.
                                """,
                                horizontal=True
                            )

                            if st.button("Start Project", type="primary"):
                                st.session_state.timer_mode = "current" if timer_mode == "Current Timer" else "pet"
                                st.session_state.time_tracker.set_timer_mode(st.session_state.timer_mode)
                                try:
                                    st.session_state.segments = load_segments(source_file, translation_file)
                                    st.rerun()
                                except ValueError as e:
                                    st.error(str(e))
                            return
                        else:
                            try:
                                st.session_state.segments = load_segments(source_file, translation_file)
                                st.rerun()
                            except ValueError as e:
                                st.error(str(e))

            if not st.session_state.segments:
                return

            # Only show segment selection and editing interface if we haven't completed all segments
            if st.session_state.current_segment < len(st.session_state.segments):
                # Add segment selection dropdown
                segment_idx = st.selectbox(
                    "Select segment to edit",
                    range(len(st.session_state.segments)),
                    index=st.session_state.current_segment,
                    format_func=lambda x: f"Segment {x + 1}",
                    key='segment_select'
                )
                st.session_state.current_segment = segment_idx

                # Display progress
                st.progress(st.session_state.current_segment /
                            len(st.session_state.segments))

                # After the progress bar and before displaying segments, add context control
                with st.sidebar:
                    st.divider()
                    st.write("🔎 **Layout Settings**")

                    # Add layout preference radio
                    layout_preference = st.radio(
                        "Layout Mode:",
                        ('centered', 'wide'),
                        index=0 if st.session_state['layout_preference'] == 'centered' else 1,
                        help="Choose between centered or wide layout",
                        horizontal=True
                    )

                    # Update session state if layout preference changed
                    if layout_preference != st.session_state['layout_preference']:
                        st.session_state['layout_preference'] = layout_preference
                        st.rerun()

                    st.write("**📖 Editing Settings**")
                    # Add horizontal view toggle
                    if 'horizontal_view' not in st.session_state:
                        st.session_state.horizontal_view = False

                    st.session_state.horizontal_view = st.toggle(
                        "Horizontal Editing",
                        value=False if st.session_state.timer_mode == "pet" else st.session_state.horizontal_view,
                        help="Display source and translation segments side by side",
                        disabled=st.session_state.timer_mode == "pet"
                    )

                    context_range = st.slider(
                        "Context Size",
                        min_value=0,
                        max_value=5,
                        value=2,
                        help="Number of segments to show before and after the current segment"
                    )


                # Display current segment with improved styling
                if st.session_state.segments:
                    start_idx = max(0, st.session_state.current_segment - context_range)
                    end_idx = min(len(st.session_state.segments), st.session_state.current_segment + context_range + 1)

                    with st.container(border=True):
                        # Initialize the initial value for the current segment
                        existing_edit = next(
                            (m for m in st.session_state.edit_metrics
                             if m.segment_id == st.session_state.current_segment),
                            None
                        )

                        most_recent_edit = None
                        for metric in reversed(st.session_state.edit_metrics):
                            if metric.segment_id == st.session_state.current_segment:
                                most_recent_edit = metric
                                break

                        current_source, current_translation = st.session_state.segments[st.session_state.current_segment]

                        # Get the original translation (for View Changes comparison)
                        # If there's an edit metric, use its original field; otherwise use current_translation
                        original_translation = (most_recent_edit.original if most_recent_edit
                                              else (existing_edit.original if existing_edit
                                                    else current_translation))

                        initial_value = (most_recent_edit.edited if most_recent_edit
                                        else (existing_edit.edited if existing_edit
                                              else current_translation))

                        if st.session_state.current_segment not in st.session_state.original_texts:
                            st.session_state.original_texts[st.session_state.current_segment] = initial_value

                        if st.session_state.current_segment != st.session_state.active_segment:
                            if st.session_state.active_segment is not None:
                                st.session_state.time_tracker.pause_segment(
                                    st.session_state.active_segment)
                            st.session_state.time_tracker.start_segment(
                                st.session_state.current_segment)
                            if st.session_state.timer_mode != "pet" or not st.session_state.time_tracker.is_pet_timer_paused(st.session_state.current_segment):
                                st.session_state.time_tracker.resume_segment(
                                    st.session_state.current_segment)
                            st.session_state.active_segment = st.session_state.current_segment

                        if st.session_state.horizontal_view:
                            # Horizontal view with two columns
                            source_col, translation_col = st.columns(2)

                            with source_col:
                                # Previous context merged
                                if start_idx < st.session_state.current_segment:
                                    previous_segments = []
                                    for idx in range(start_idx, st.session_state.current_segment):
                                        source, _ = st.session_state.segments[idx]
                                        previous_segments.append(f"[{idx + 1}] {source}")

                                    if previous_segments:
                                        st.text_area(
                                            label="Previous Context",
                                            value="\n\n".join(previous_segments),
                                            disabled=True,
                                            height=150,
                                            key="source_prev_merged",
                                            label_visibility="collapsed"
                                        )

                                # Current segment (highlighted)
                                st.markdown("**🔍 Current Segment**")
                                st.text_area(
                                    f"Source [{st.session_state.current_segment + 1}]",
                                    value=current_source,
                                    disabled=True,
                                    height=150,
                                    key=f"source_current",
                                    help="Current source segment"
                                )

                                # Following context merged
                                if end_idx > st.session_state.current_segment + 1:
                                    following_segments = []
                                    for idx in range(st.session_state.current_segment + 1, end_idx):
                                        source, _ = st.session_state.segments[idx]
                                        following_segments.append(f"[{idx + 1}] {source}")

                                    if following_segments:
                                        st.text_area(
                                            label="Following Context",
                                            value="\n\n".join(following_segments),
                                            disabled=True,
                                            height=150,
                                            key="source_next_merged",
                                            label_visibility="collapsed"
                                        )

                            with translation_col:
                                # Previous translations merged
                                if start_idx < st.session_state.current_segment:
                                    previous_translations = []
                                    for idx in range(start_idx, st.session_state.current_segment):
                                        _, translation = st.session_state.segments[idx]
                                        # Get the most recent edit if available
                                        context_text = next(
                                            (m.edited for m in reversed(st.session_state.edit_metrics)
                                             if m.segment_id == idx),
                                            translation
                                        )
                                        previous_translations.append(f"[{idx + 1}] {context_text}")

                                    if previous_translations:
                                        st.text_area(
                                            label="Previous Translations",
                                            value="\n\n".join(previous_translations),
                                            disabled=True,
                                            height=150,
                                            key="trans_prev_merged",
                                            label_visibility="collapsed"
                                        )

                                # Current translation (editable)
                                st.markdown("**✏️ Current Translation**")
                                is_pet_disabled = (st.session_state.timer_mode == "pet" and
                                               st.session_state.time_tracker.is_pet_timer_paused(st.session_state.current_segment))
                                edited_text = st.text_area(
                                    f"Edit Translation [{st.session_state.current_segment + 1}]",
                                    value=initial_value,
                                    height=150,
                                    key=f"edit_area_{st.session_state.current_segment}",
                                    on_change=lambda: st.session_state.time_tracker.update_activity(st.session_state.current_segment),
                                    disabled=is_pet_disabled,
                                    help="Edit this translation" + (" (Timer paused)" if is_pet_disabled else "")
                                )

                                # Following translations merged
                                if end_idx > st.session_state.current_segment + 1:
                                    following_translations = []
                                    for idx in range(st.session_state.current_segment + 1, end_idx):
                                        _, translation = st.session_state.segments[idx]
                                        # Get the most recent edit if available
                                        context_text = next(
                                            (m.edited for m in reversed(st.session_state.edit_metrics)
                                             if m.segment_id == idx),
                                            translation
                                        )
                                        following_translations.append(f"[{idx + 1}] {context_text}")

                                    if following_translations:
                                        st.text_area(
                                            label="Following Translations",
                                            value="\n\n".join(following_translations),
                                            disabled=True,
                                            height=150,
                                            key="trans_next_merged",
                                            label_visibility="collapsed"
                                        )
                        else:
                            # Previous context merged into one text area
                            if start_idx < st.session_state.current_segment:
                                previous_segments = []
                                for idx in range(start_idx, st.session_state.current_segment):
                                    source, _ = st.session_state.segments[idx]
                                    previous_segments.append(f"[{idx + 1}] {source}")

                                if previous_segments:
                                    st.write("**Previous segments:**")
                                    st.info("\n\n".join(previous_segments))

                            # Current segment (highlighted)
                            st.markdown(f"**Current Segment [{st.session_state.current_segment + 1}]:**")
                            st.warning(current_source)

                            # Current translation (editable)
                            is_pet_disabled = (st.session_state.timer_mode == "pet" and
                                               st.session_state.time_tracker.is_pet_timer_paused(st.session_state.current_segment))
                            edited_text = st.text_area(
                                "Translation:",
                                value=initial_value,
                                key=f"edit_area_{st.session_state.current_segment}",
                                on_change=lambda: st.session_state.time_tracker.update_activity(st.session_state.current_segment),
                                disabled=is_pet_disabled,
                                help="Edit this translation" + (" (Timer paused)" if is_pet_disabled else "")
                            )

                            # Following context merged into one text area
                            if end_idx > st.session_state.current_segment + 1:
                                following_segments = []
                                for idx in range(st.session_state.current_segment + 1, end_idx):
                                    source, _ = st.session_state.segments[idx]
                                    following_segments.append(f"[{idx + 1}] {source}")

                                if following_segments:
                                    st.markdown("**Following segments:**")
                                    st.info("\n\n".join(following_segments))

                            # Remove duplicate initialization code
                            if st.session_state.current_segment not in st.session_state.original_texts:
                                st.session_state.original_texts[st.session_state.current_segment] = initial_value

                    # Navigation buttons with emojis and improved layout
                    col1, col2, col3, col4 = st.columns([1, 0.5, 0.5, 1])
                    with col1:
                        if st.button("🔄 Previous",
                                     key="prev_segment",
                                     disabled=st.session_state.current_segment == 0):
                            # Verify time was recorded if segment was edited
                            current_text = st.session_state[f"edit_area_{st.session_state.current_segment}"]
                            original_text = st.session_state.original_texts.get(st.session_state.current_segment, current_translation)

                            if current_text != original_text and not verify_time_recorded(st.session_state.current_segment):
                                st.error("⚠️ No editing time was recorded for this segment. If you're using PET mode, make sure to wait a bit before moving to the next segment.")
                                return

                            save_metrics(current_source, current_translation, edited_text)
                            st.session_state.time_tracker.pause_segment(st.session_state.current_segment)
                            st.session_state.current_segment -= 1
                            # Ensure new segment starts paused in PET mode
                            if st.session_state.timer_mode == "pet":
                                st.session_state.time_tracker.pause_pet_timer(st.session_state.current_segment)
                                # Reset waiting time for the new segment
                                if 'remaining_wait_time' in st.session_state:
                                    del st.session_state.remaining_wait_time
                            st.session_state.active_segment = None  # Reset active segment
                            st.rerun()

                    # Add PET Timer controls if in PET mode
                    if st.session_state.timer_mode == "pet":
                        is_paused = st.session_state.time_tracker.is_pet_timer_paused(st.session_state.current_segment)
                        can_start = st.session_state.time_tracker.can_start_pet_timer(st.session_state.current_segment)

                        with col2:
                            if st.button("⏸️", key="pause_timer", disabled=is_paused, use_container_width=True):
                                st.session_state.time_tracker.pause_pet_timer(st.session_state.current_segment)
                                st.rerun()

                        with col3:
                            session = st.session_state.time_tracker.sessions[st.session_state.current_segment]
                            if not can_start and session and session.segment_view_time:
                                time_since_view = (datetime.now() - session.segment_view_time).total_seconds()
                                remaining_time = max(0, st.session_state.time_tracker.MINIMUM_VIEW_TIME - time_since_view)

                                # Store the remaining time in session state with segment-specific key
                                wait_time_key = f'remaining_wait_time_{st.session_state.current_segment}'
                                if wait_time_key not in st.session_state:
                                    st.session_state[wait_time_key] = remaining_time

                                if remaining_time <= 0 or st.session_state[wait_time_key] <= 0:
                                    # Time is up, show the play button
                                    if st.button("▶️", key="start_timer", disabled=not is_paused, use_container_width=True):
                                        st.session_state.time_tracker.start_pet_timer(st.session_state.current_segment)
                                        st.rerun()
                                else:
                                    # Still waiting, show hourglass
                                    st.button("⏳ Waiting...", key="waiting_timer", disabled=True,
                                            help=f"Please wait {remaining_time:.1f} seconds before starting",
                                            use_container_width=True)
                                    # Update the remaining time in session state
                                    st.session_state[wait_time_key] = remaining_time
                                    # Force a rerun after a short delay if still waiting
                                    time.sleep(0.1)  # Small delay to prevent too frequent reruns
                                    st.rerun()
                            elif st.button("▶️", key="start_timer", disabled=not is_paused, use_container_width=True):
                                st.session_state.time_tracker.start_pet_timer(st.session_state.current_segment)
                                st.rerun()

                    with col4:
                        # Check if we're on the last segment
                        is_last_segment = st.session_state.current_segment == len(st.session_state.segments) - 1

                        if is_last_segment:
                            if st.button("🏁 Finish", key="finish_button", type="primary"):
                                # Verify time was recorded if segment was edited
                                current_text = st.session_state[f"edit_area_{st.session_state.current_segment}"]
                                original_text = st.session_state.original_texts.get(st.session_state.current_segment, original_translation)

                                if current_text != original_text and not verify_time_recorded(st.session_state.current_segment):
                                    st.error("⚠️ No editing time was recorded for this segment. If you're using PET mode, make sure to wait a bit before moving to the next segment.")
                                    return

                                save_metrics(current_source, original_translation, edited_text)
                                st.session_state.time_tracker.pause_segment(st.session_state.current_segment)
                                st.session_state.current_segment += 1
                                # Ensure new segment starts paused in PET mode
                                if st.session_state.timer_mode == "pet":
                                    st.session_state.time_tracker.pause_pet_timer(st.session_state.current_segment)
                                st.session_state.active_segment = None  # Reset active segment
                                st.rerun()
                        else:
                            if st.button("Next ➡️", key="next_segment"):
                                # Verify time was recorded if segment was edited
                                current_text = st.session_state[f"edit_area_{st.session_state.current_segment}"]
                                original_text = st.session_state.original_texts.get(st.session_state.current_segment, original_translation)

                                if current_text != original_text and not verify_time_recorded(st.session_state.current_segment):
                                    st.error("⚠️ No editing time was recorded for this segment. If you're using PET mode, make sure to wait a bit before moving to the next segment.")
                                    return

                                # Update final stats for current segment
                                st.session_state.time_tracker.update_activity(st.session_state.current_segment)
                                # Save metrics and pause tracking
                                save_metrics(current_source, original_translation, edited_text)
                                st.session_state.time_tracker.pause_segment(st.session_state.current_segment)
                                # Move to next segment
                                st.session_state.current_segment += 1
                                # Ensure new segment starts paused in PET mode
                                if st.session_state.timer_mode == "pet":
                                    st.session_state.time_tracker.pause_pet_timer(st.session_state.current_segment)
                                st.session_state.active_segment = None  # Reset active segment
                                st.rerun()

                    # Show editing statistics in expander
                    if st.session_state.current_segment in st.session_state.time_tracker.sessions:
                        st.divider()
                        with st.expander("📊 Post-Editing Statistics", expanded=True):
                            col1, col2, col3, col4 = st.columns(4)

                            with col1:
                                edit_time = st.session_state.time_tracker.get_editing_time(
                                    st.session_state.current_segment)
                                minutes = int(edit_time // 60)
                                seconds = int(edit_time % 60)
                                st.metric(
                                    "Editing Time",
                                    f"{minutes}m {seconds}s",
                                    help="Time spent editing this segment"
                                )

                            with col2:
                                if st.session_state.current_segment in st.session_state.time_tracker.sessions:
                                    idle_time = st.session_state.time_tracker.sessions[st.session_state.current_segment].idle_time
                                    idle_minutes = int(idle_time // 60)
                                    idle_seconds = int(idle_time % 60)
                                    st.metric(
                                        "Idle Time",
                                        f"{idle_minutes}m {idle_seconds}s",
                                        help="Time spent idle (>30s without activity)"
                                    )

                            insertions, deletions = calculate_edit_distance(
                                original_translation, edited_text)
                            with col3:
                                st.metric(
                                    "Insertions",
                                    f"{insertions}",
                                    help="Number of inserted words"
                                )

                            with col4:
                                st.metric(
                                    "Deletions",
                                    f"{deletions}",
                                    help="Number of deleted words"
                                )

                        with st.expander("View Changes", expanded=True):
                            st.markdown(highlight_differences(
                                original_translation, edited_text), unsafe_allow_html=True)

            else:
                # We've completed all segments, show the results
                # Add Post-Edits Review section before displaying final results
                st.markdown("## 📝 Review Post-Edits")
                st.markdown("Review and search through all your post-edited segments below.")

                # Convert metrics to DataFrame for the review
                review_df = pd.DataFrame([vars(m) for m in st.session_state.edit_metrics])

                # Add search functionality
                search_term = st.text_input("🔍 Search in segments",
                                          help="Search in source text, original translation, or post-edited text")

                # Add filter options
                col1, col2 = st.columns([1, 3])
                with col1:
                    sort_by = st.selectbox(
                        "Sort by",
                        ["Segment ID", "Edit Time", "Number of Edits"],
                        help="Choose how to sort the segments"
                    )

                with col2:
                    filter_edited = st.multiselect(
                        "Filter segments",
                        ["Show Only Modified", "Show Only Unmodified"],
                        help="Filter segments based on whether they were modified"
                    )

                # Process the DataFrame based on filters
                if search_term:
                    mask = (review_df['source'].str.contains(search_term, case=False, na=False) |
                           review_df['original'].str.contains(search_term, case=False, na=False) |
                           review_df['edited'].str.contains(search_term, case=False, na=False))
                    review_df = review_df[mask]

                if "Show Only Modified" in filter_edited:
                    review_df = review_df[review_df['original'] != review_df['edited']]
                elif "Show Only Unmodified" in filter_edited:
                    review_df = review_df[review_df['original'] == review_df['edited']]

                # Sort the DataFrame
                if sort_by == "Segment ID":
                    review_df = review_df.sort_values('segment_id')
                elif sort_by == "Edit Time":
                    review_df = review_df.sort_values('edit_time', ascending=False)
                elif sort_by == "Number of Edits":
                    review_df['total_edits'] = review_df['insertions'] + review_df['deletions']
                    review_df = review_df.sort_values('total_edits', ascending=False)

                # Display segments in an expandable format
                for _, row in review_df.iterrows():
                    with st.expander(f"Segment {row['segment_id'] + 1}"):
                        col1, col2 = st.columns(2)

                        with col1:
                            st.markdown("**Source Text:**")
                            st.info(row['source'])

                            st.markdown("**Original Translation:**")
                            st.warning(row['original'])

                        with col2:
                            st.markdown("**Post-Edited Translation:**")
                            if row['original'] != row['edited']:
                                st.success(row['edited'])
                                # Show differences
                                st.markdown("**Changes:**")
                                st.markdown(highlight_differences(row['original'], row['edited']), unsafe_allow_html=True)
                            else:
                                st.info("No changes made")

                        # Show metrics
                        m1, m2, m3 = st.columns(3)
                        with m1:
                            edit_time = row['edit_time']
                            minutes = int(edit_time // 60)
                            seconds = int(edit_time % 60)
                            st.metric("Edit Time", f"{minutes}m {seconds}s")
                        with m2:
                            st.metric("Insertions", row['insertions'])
                        with m3:
                            st.metric("Deletions", row['deletions'])

                        # Add button to jump back to this segment for editing
                        if st.button("✏️ Edit this segment", key=f"edit_btn_{row['segment_id']}"):
                            st.session_state.current_segment = row['segment_id']
                            st.rerun()

                st.divider()
                display_results()
                return

        else:
            # Show welcome message for non-authenticated users
            st.markdown("""
                <div class="card pt-serif">
                    <p><strong>Welcome to the MT Post-Editing Tool! 👋</strong></p>
                    <p>Please login using the button in the sidebar to get started.</p>
                </div>
            """, unsafe_allow_html=True)


def save_metrics(source: str, original: str, edited: str):
    """Save metrics for the current segment"""
    #if edited == st.session_state.original_texts.get(st.session_state.current_segment, original):
    #    return

    edit_time = st.session_state.time_tracker.get_editing_time(
        st.session_state.current_segment)
    insertions, deletions = calculate_edit_distance(original, edited)

    metrics = EditMetrics(
        segment_id=st.session_state.current_segment,
        source=source,
        original=original,
        edited=edited,
        edit_time=edit_time,
        insertions=insertions,
        deletions=deletions
    )

    st.session_state.edit_metrics = [m for m in st.session_state.edit_metrics
                                     if m.segment_id != st.session_state.current_segment]
    st.session_state.edit_metrics.append(metrics)

    # Update the segments list with the edited text
    current_idx = st.session_state.current_segment
    if 0 <= current_idx < len(st.session_state.segments):
        # Update the segment tuple with the edited translation
        st.session_state.segments[current_idx] = (source, edited)

    # Auto-save if enabled and user info is available
    if (st.session_state.get('auto_save', False) and
        st.session_state.get('user_name') and
            st.session_state.get('user_surname')):
        df = pd.DataFrame([vars(m) for m in st.session_state.edit_metrics])
        asyncio.run(save_to_database(st.session_state.user_name,
                    st.session_state.user_surname, df))
        st.session_state.last_saved = datetime.now(timezone.utc)


def display_results():
    """Display final results and statistics"""
    # Convert metrics to DataFrame for easy analysis
    df = pd.DataFrame([vars(m) for m in st.session_state.edit_metrics])

    # Display statistics in a metrics container
    st.markdown("### Editing Statistics", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Segments", len(df))
    with col2:
        st.metric("Total Time", f"{df['edit_time'].sum():.1f}s")
    with col3:
        st.metric("Avg. Time/Segment", f"{df['edit_time'].mean():.1f}s")

    col4, col5, col6 = st.columns(3)
    with col4:
        st.metric("Total Insertions", int(df['insertions'].sum()))
    with col5:
        st.metric("Total Deletions", int(df['deletions'].sum()))
    with col6:
        st.metric("Total Edits", int(
            df['insertions'].sum() + df['deletions'].sum()))

    # Display detailed metrics
    st.divider()
    st.markdown("### Detailed Metrics", unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True)

    # Download buttons
    st.divider()
    st.markdown("### Download Results", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download metrics as CSV",
            data=csv,
            file_name="post_editing_metrics.csv",
            mime="text/csv",
            use_container_width=True
        )

    with col2:
        # Prepare JSON data
        json_data = []
        for metric in st.session_state.edit_metrics:
            json_data.append({
                "segment_id": metric.segment_id,
                "source": metric.source,
                "original_translation": metric.original,
                "post_edited": metric.edited,
                "edit_time_seconds": round(metric.edit_time, 2),
                "insertions": metric.insertions,
                "deletions": metric.deletions
            })

        json_str = json.dumps(json_data, indent=2, ensure_ascii=False)
        st.download_button(
            label="📥 Download segments as JSON",
            data=json_str,
            file_name="post_edited_segments.json",
            mime="application/json",
            use_container_width=True
        )

    st.divider()
    st.markdown("""
                <div class="info-card">
                    <p><strong>Thanks for using my tool! </strong></p>
                    <p>Feel free to send me an email at antonio.castaldo@phd.unipi.it for any feedback or suggestions.</p>
                </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
