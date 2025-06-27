import streamlit as st
import pandas as pd
import asyncio
import time
from datetime import datetime

# Import modular components
from config import init_session_state, load_css, setup_page_config, display_header, display_welcome_message, display_instructions, display_footer_info
from auth import display_auth_page, display_user_info
from ui_components import (
    load_segments, display_review_page, display_sidebar_settings, 
    display_file_upload, display_timer_mode_selection, display_pet_timer_controls,
    display_results
)
from metrics import EditMetrics, save_metrics, verify_time_recorded, display_editing_statistics
from time_tracker import TimeTracker


def display_editing_interface(context_range: int):
    """Display the main editing interface"""
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
                    display_horizontal_view(start_idx, end_idx, current_source, current_translation, initial_value)
                else:
                    display_vertical_view(start_idx, end_idx, current_source, current_translation, initial_value)

            # Navigation buttons and timer controls
            display_navigation_controls(current_source, current_translation)

            # Show editing statistics
            edited_text = st.session_state.get(f"edit_area_{st.session_state.current_segment}", initial_value)
            display_editing_statistics(current_source, current_translation, edited_text)

    else:
        # We've completed all segments, show the results
        display_post_edit_review()


def display_horizontal_view(start_idx: int, end_idx: int, current_source: str, current_translation: str, initial_value: str):
    """Display horizontal editing view"""
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


def display_vertical_view(start_idx: int, end_idx: int, current_source: str, current_translation: str, initial_value: str):
    """Display vertical editing view"""
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
    st.warning(f"`{current_source}`")

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


def display_navigation_controls(current_source: str, current_translation: str):
    """Display navigation buttons and timer controls"""
    col1, col2, col3, col4 = st.columns([1, 0.5, 0.5, 1])
    
    with col1:
        if st.button("🔄 Previous",
                     key="prev_segment",
                     disabled=st.session_state.current_segment == 0):
            handle_navigation(-1, current_source, current_translation)

    # Add PET Timer controls if in PET mode
    if st.session_state.timer_mode == "pet":
        display_pet_timer_controls()

    with col4:
        # Check if we're on the last segment
        is_last_segment = st.session_state.current_segment == len(st.session_state.segments) - 1

        if is_last_segment:
            if st.button("🏁 Finish", key="finish_button", type="primary"):
                handle_navigation(1, current_source, current_translation)
        else:
            if st.button("Next ➡️", key="next_segment"):
                handle_navigation(1, current_source, current_translation)


def handle_navigation(direction: int, current_source: str, current_translation: str):
    """Handle navigation between segments"""
    # Verify time was recorded if segment was edited
    current_text = st.session_state[f"edit_area_{st.session_state.current_segment}"]
    original_text = st.session_state.original_texts.get(st.session_state.current_segment, current_translation)

    if current_text != original_text and not verify_time_recorded(st.session_state.current_segment):
        st.error("⚠️ No editing time was recorded for this segment. If you're using PET mode, make sure to wait a bit before moving to the next segment.")
        return

    save_metrics(current_source, current_translation, current_text)
    st.session_state.time_tracker.pause_segment(st.session_state.current_segment)
    st.session_state.current_segment += direction
    
    # Ensure new segment starts paused in PET mode
    if st.session_state.timer_mode == "pet":
        st.session_state.time_tracker.pause_pet_timer(st.session_state.current_segment)
        # Reset waiting time for the new segment
        if 'remaining_wait_time' in st.session_state:
            del st.session_state.remaining_wait_time
    
    st.session_state.active_segment = None  # Reset active segment
    st.rerun()


def display_post_edit_review():
    """Display post-edit review and final results"""
    st.markdown("## 📝 Review Post-Edits")
    st.markdown("Review and search through all your post-edited segments below.")

    # Convert metrics to DataFrame for the review
    if not st.session_state.edit_metrics:
        st.info("No segments have been edited yet.")
        return
    
    review_df = pd.DataFrame([vars(m) for m in st.session_state.edit_metrics])
    
    # Ensure it's a DataFrame
    if not isinstance(review_df, pd.DataFrame):
        st.error("Error creating review DataFrame")
        return

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
                    from metrics import highlight_differences
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


def main():
    """Main application function"""
    # Initialize session state first
    asyncio.run(init_session_state())
    
    # Setup page configuration
    setup_page_config()
    
    # Load CSS
    asyncio.run(load_css())
    
    # Display header
    display_header()

    if not st.session_state.authenticated:
        display_auth_page()
        return

    # If authenticated, show sidebar and main content
    display_user_info()
    context_range = display_sidebar_settings()

    # If authenticated, show either the review page or the main editing interface
    if st.session_state.show_review_page:
        display_review_page()
    else:
        # Display welcome message and instructions
        display_welcome_message()
        display_instructions()
        display_footer_info()
        
        # File upload with styled container - only show if no segments are loaded
        if len(st.session_state.segments) == 0:
            st.info("If you have a previous project, load it by clicking on the '📂 Load' button in the sidebar!")
            source_file, translation_file = display_file_upload()

            if source_file and translation_file:
                # Add timer mode selection before loading segments
                if st.session_state.timer_mode is None:
                    if display_timer_mode_selection():
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

        # Display the main editing interface
        display_editing_interface(context_range)


if __name__ == "__main__":
    main()