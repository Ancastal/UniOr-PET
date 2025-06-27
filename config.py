import streamlit as st
import asyncio
from time_tracker import TimeTracker


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
    if 'layout_preference' not in st.session_state:
        st.session_state.layout_preference = 'centered'
    if 'show_review_page' not in st.session_state:
        st.session_state.show_review_page = False


async def load_css():
    """Load and apply custom CSS styles"""
    with open("static/styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def setup_page_config():
    """Setup Streamlit page configuration"""
    st.set_page_config(
        page_title="MT Post-Editing Tool",
        page_icon="🌍",
        layout=st.session_state.get('layout_preference', 'centered')
    )


def display_header():
    """Display application header"""
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


def display_welcome_message():
    """Display welcome message for authenticated users"""
    st.markdown("""
        <div class="card pt-serif">
            <p><strong>Hi, I'm Antonio. 👋</strong></p>
            <p>I'm a PhD candidate in Artificial Intelligence at the University of Pisa, working on Creative Machine Translation with LLMs.</p>
            <p>My goal is to develop translation systems that can preserve style, tone, and creative elements while accurately conveying meaning across languages.</p>
            <p>Learn more about me at <a href="https://www.ancastal.com" target="_blank">www.ancastal.com</a></p>
        </div>
    """, unsafe_allow_html=True)


def display_instructions():
    """Display instructions expander"""
    with st.expander("Instructions", expanded=False):
        st.markdown("##### Getting Started")
        st.markdown("""
        1. Enter your name and surname in the sidebar to enable progress tracking
        2. Upload a text file containing one translation per line
        3. Edit each segment to improve the translation quality
        """)

        st.markdown("##### Navigation")
        st.markdown("""
        - Use the segment selector dropdown to jump to any segment
        - Use the Previous/Next buttons to move between segments
        - The progress bar shows your overall completion status
        """)

        st.markdown("##### Features")
        st.markdown("""
        - 🔄 **Auto-save:** Your progress is automatically saved as you edit (when enabled)
        - 📊 **Real-time metrics:** Track editing time, insertions, and deletions
        - 👀 **Visual diff:** See your changes highlighted in real-time
        - 💾 **Progress tracking:** Resume your work at any time
        """)


def display_footer_info():
    """Display footer information"""
    st.markdown("""
                <div class="info-card">
                    <p class="pt-serif text-sm"><strong>Thanks for using my tool! 😊</strong></p>
                    <p class="text-center text-muted">Feel free to send me an email for any feedback or suggestions.</p>
                </div>
                """, unsafe_allow_html=True)
    st.warning("⚠️ Copy-paste operations are not allowed. Please type your edits manually.")