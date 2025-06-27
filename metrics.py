import streamlit as st
import pandas as pd
from typing import List, Tuple
import difflib
import string
from dataclasses import dataclass
from evaluate import load
import asyncio
from datetime import datetime, timezone

from database import save_to_mongodb


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


def verify_time_recorded(segment_id: int) -> bool:
    """Verify that time was recorded for the segment"""
    if segment_id not in st.session_state.time_tracker.sessions:
        return False

    edit_time = st.session_state.time_tracker.get_editing_time(segment_id)

    return edit_time > 1


def save_metrics(source: str, original: str, edited: str):
    """Save metrics for the current segment"""
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

    # Auto-save if enabled and user info is available
    if (st.session_state.get('auto_save', False) and
        st.session_state.get('user_name') and
            st.session_state.get('user_surname')):
        df = pd.DataFrame([vars(m) for m in st.session_state.edit_metrics])
        asyncio.run(save_to_mongodb(st.session_state.user_name,
                    st.session_state.user_surname, df))
        st.session_state.last_saved = datetime.now(timezone.utc)


def calculate_mtqe_score(df: pd.DataFrame) -> Tuple[float, float, float]:
    """Calculate MTQE scores for the post-edited segments"""
    
    # Initialize MTQE scorer
    bleu = load("bleu")
    chrf = load("chrf")
    ter = load("ter")

    # Calculate scores
    bleu_score = round(bleu.compute(predictions=df['edited'], references=df['original'])['bleu'], 2)
    chrf_score = round(chrf.compute(predictions=df['edited'], references=df['original'])['score'], 2)
    ter_score = round(ter.compute(predictions=df['edited'], references=df['original'])['score'], 2)

    return bleu_score, chrf_score, ter_score


def display_editing_statistics(current_source: str, current_translation: str, edited_text: str):
    """Display editing statistics in expander"""
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
                current_translation, edited_text)
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
                current_translation, edited_text), unsafe_allow_html=True)