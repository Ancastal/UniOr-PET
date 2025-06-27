import streamlit as st
import pandas as pd
from typing import List, Tuple
import time
import json
import asyncio
import pytz
from datetime import datetime, timezone

from time_tracker import TimeTracker
from metrics import EditMetrics, save_metrics, verify_time_recorded, calculate_mtqe_score, highlight_differences
from database import load_from_mongodb, save_to_mongodb


def load_segments(source_file, translation_file) -> List[Tuple[str, str]]:
    """Load segments from uploaded files"""
    if source_file is None or translation_file is None:
        return []

    source_content = source_file.getvalue().decode("utf-8")
    translation_content = translation_file.getvalue().decode("utf-8")

    source_lines = [line.strip()
                    for line in source_content.split('\n') if line.strip()]
    translation_lines = [line.strip()
                         for line in translation_content.split('\n') if line.strip()]

    # Ensure both files have same number of lines
    if len(source_lines) != len(translation_lines):
        raise ValueError(
            "Source and translation files must have the same number of lines")

    return list(zip(source_lines, translation_lines))


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


def display_sidebar_settings():
    """Display sidebar settings and controls"""
    with st.sidebar:
        st.write("Welcome to the **MT Post-Editing Tool**.")
        st.markdown("## 🧑‍💻 Tool Settings")

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

                        # Then save everything to MongoDB
                        df = pd.DataFrame([vars(m) for m in st.session_state.edit_metrics])
                        asyncio.run(save_to_mongodb(
                            st.session_state.user_name,
                            st.session_state.user_surname,
                            df))
                        st.session_state.last_saved = datetime.now(timezone.utc)
                        st.success("Progress saved!")

        with col2:
            if st.button("📂 Load", use_container_width=True, disabled=st.session_state.has_loaded_segments):
                with st.spinner("Loading previous work..."):
                    existing_data, full_text = asyncio.run(
                        load_from_mongodb(st.session_state.user_name,
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

                    # Clear from MongoDB
                    asyncio.run(save_to_mongodb(
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

        return context_range


def display_file_upload():
    """Display file upload interface"""
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

    return source_file, translation_file


def display_timer_mode_selection():
    """Display timer mode selection interface"""
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
        return True
    return False


def display_pet_timer_controls():
    """Display PET timer controls"""
    if st.session_state.timer_mode != "pet":
        return

    col1, col2, col3, col4 = st.columns([1, 0.5, 0.5, 1])
    
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

    # MTQE metric
    st.divider()
    st.markdown("### MTQE Metrics", unsafe_allow_html=True)
    bleu, chrf, ter = calculate_mtqe_score(df)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("BLEU Score", bleu)
    with col2:
        st.metric("CHRF Score", chrf)
    with col3:
        st.metric("TER Score", ter)

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
                    <p>Feel free to send me an email for any feedback or suggestions.</p>
                </div>
        """, unsafe_allow_html=True)