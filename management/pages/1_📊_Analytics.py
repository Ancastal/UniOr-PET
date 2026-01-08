"""
Project Manager Analytics - Performance Metrics & Visualizations
UniOr-PET Management Interface
"""
import streamlit as st
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Add parent directory to path to import shared modules
parent_dir = Path(__file__).parent.parent.parent
sys.path.append(str(parent_dir))

from db_manager import get_database_manager

# Page configuration
st.set_page_config(
    page_title="Analytics - PM Dashboard",
    page_icon="📊",
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


def collect_all_progress_data(db_manager, translators):
    """Collect progress data from all translators"""
    all_data = []

    for translator in translators:
        try:
            metrics_df, full_text, time_tracker, timer_mode = asyncio.run(
                db_manager.load_progress(translator['name'], translator['surname'])
            )

            if not metrics_df.empty:
                # Add translator identification
                metrics_df['translator_name'] = f"{translator['name']} {translator['surname']}"
                metrics_df['translator_first'] = translator['name']
                metrics_df['translator_last'] = translator['surname']
                all_data.append(metrics_df)

        except Exception as e:
            st.warning(f"Could not load data for {translator['name']} {translator['surname']}: {str(e)}")
            continue

    if all_data:
        return pd.concat(all_data, ignore_index=True)
    else:
        return pd.DataFrame()


def display_overview_metrics(df):
    """Display overview metrics cards"""
    st.markdown("### 📈 Performance Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_segments = len(df) if not df.empty else 0
        st.metric(
            label="Total Segments Completed",
            value=total_segments,
            help="Total number of segments edited across all translators"
        )

    with col2:
        avg_time = df['edit_time'].mean() if not df.empty and 'edit_time' in df.columns else 0
        st.metric(
            label="Avg Time per Segment",
            value=f"{avg_time:.2f}s",
            help="Average editing time per segment"
        )

    with col3:
        total_edits = (
            (df['insertions'].sum() + df['deletions'].sum())
            if not df.empty and 'insertions' in df.columns and 'deletions' in df.columns
            else 0
        )
        st.metric(
            label="Total Edits",
            value=f"{int(total_edits):,}",
            help="Total insertions + deletions"
        )

    with col4:
        total_words = 0
        if not df.empty and 'original' in df.columns:
            total_words = sum(len(str(text).split()) for text in df['original'])

        st.metric(
            label="Words Processed",
            value=f"{total_words:,}",
            help="Total words in all edited segments"
        )


def display_translator_comparison(df):
    """Display translator comparison table"""
    st.markdown("---")
    st.markdown("### 👥 Translator Comparison")

    if df.empty:
        st.info("No data available for comparison.")
        return

    # Group by translator
    translator_stats = df.groupby('translator_name').agg({
        'segment_id': 'count',
        'edit_time': 'mean',
        'insertions': 'sum',
        'deletions': 'sum'
    }).reset_index()

    translator_stats.columns = ['Translator', 'Segments Completed', 'Avg Time (s)', 'Total Insertions', 'Total Deletions']

    # Calculate edits per segment
    translator_stats['Edits per Segment'] = (
        (translator_stats['Total Insertions'] + translator_stats['Total Deletions']) /
        translator_stats['Segments Completed']
    ).round(2)

    # Calculate words per hour
    translator_stats['Words per Hour'] = 0
    for idx, row in translator_stats.iterrows():
        translator_data = df[df['translator_name'] == row['Translator']]
        if not translator_data.empty and 'original' in translator_data.columns:
            total_words = sum(len(str(text).split()) for text in translator_data['original'])
            total_time_hours = translator_data['edit_time'].sum() / 3600
            if total_time_hours > 0:
                translator_stats.at[idx, 'Words per Hour'] = round(total_words / total_time_hours, 2)

    # Sort by segments completed
    translator_stats = translator_stats.sort_values('Segments Completed', ascending=False)

    # Display table
    st.dataframe(
        translator_stats,
        use_container_width=True,
        hide_index=True,
        column_config={
            'Avg Time (s)': st.column_config.NumberColumn(format="%.2f"),
            'Edits per Segment': st.column_config.NumberColumn(format="%.2f"),
            'Words per Hour': st.column_config.NumberColumn(format="%.2f")
        }
    )


def display_visualizations(df):
    """Display Plotly visualizations"""
    st.markdown("---")
    st.markdown("### 📊 Visualizations")

    if df.empty:
        st.info("No data available for visualizations.")
        return

    # Create tabs for different charts
    tab1, tab2, tab3, tab4 = st.tabs([
        "Segments Over Time",
        "Editing Time Comparison",
        "Edits vs Time",
        "Distribution"
    ])

    with tab1:
        st.markdown("#### Segments Completed Over Time")

        # Add a timestamp column if not present (use segment_id as proxy)
        if 'segment_id' in df.columns:
            # Group by translator and count cumulative segments
            translator_progress = []

            for translator in df['translator_name'].unique():
                translator_data = df[df['translator_name'] == translator].sort_values('segment_id')
                translator_data['cumulative_segments'] = range(1, len(translator_data) + 1)

                for idx, row in translator_data.iterrows():
                    translator_progress.append({
                        'Translator': translator,
                        'Segment': row['segment_id'],
                        'Cumulative Segments': row['cumulative_segments']
                    })

            if translator_progress:
                progress_df = pd.DataFrame(translator_progress)

                fig = px.line(
                    progress_df,
                    x='Segment',
                    y='Cumulative Segments',
                    color='Translator',
                    title='Cumulative Segments Completed by Translator',
                    markers=True
                )
                fig.update_layout(
                    xaxis_title='Segment ID',
                    yaxis_title='Cumulative Segments Completed',
                    hovermode='x unified'
                )
                st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.markdown("#### Average Editing Time by Translator")

        if 'edit_time' in df.columns:
            avg_time_df = df.groupby('translator_name')['edit_time'].mean().reset_index()
            avg_time_df.columns = ['Translator', 'Average Time (s)']

            fig = px.bar(
                avg_time_df,
                x='Translator',
                y='Average Time (s)',
                title='Average Editing Time per Segment',
                color='Average Time (s)',
                color_continuous_scale='Blues'
            )
            fig.update_layout(
                xaxis_title='Translator',
                yaxis_title='Average Time (seconds)',
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.markdown("#### Edits vs. Time per Segment")

        if 'edit_time' in df.columns and 'insertions' in df.columns and 'deletions' in df.columns:
            scatter_df = df.copy()
            scatter_df['Total Edits'] = scatter_df['insertions'] + scatter_df['deletions']

            fig = px.scatter(
                scatter_df,
                x='edit_time',
                y='Total Edits',
                color='translator_name',
                title='Relationship between Editing Time and Number of Edits',
                hover_data=['segment_id'],
                labels={
                    'edit_time': 'Editing Time (s)',
                    'Total Edits': 'Total Edits (Insertions + Deletions)',
                    'translator_name': 'Translator'
                }
            )
            fig.update_layout(hovermode='closest')
            st.plotly_chart(fig, use_container_width=True)

    with tab4:
        st.markdown("#### Distribution of Segment Completion")

        segments_by_translator = df.groupby('translator_name').size().reset_index(name='Segments')

        fig = px.pie(
            segments_by_translator,
            values='Segments',
            names='translator_name',
            title='Distribution of Completed Segments by Translator'
        )
        st.plotly_chart(fig, use_container_width=True)


def display_filters(df):
    """Display filter controls"""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔍 Filters")

    filters = {}

    # Translator filter
    if not df.empty and 'translator_name' in df.columns:
        translators = ['All'] + list(df['translator_name'].unique())
        selected_translator = st.sidebar.selectbox(
            "Select Translator",
            translators,
            help="Filter data by translator"
        )
        filters['translator'] = selected_translator

    # Segment range filter
    if not df.empty and 'segment_id' in df.columns:
        min_segment = int(df['segment_id'].min())
        max_segment = int(df['segment_id'].max())

        segment_range = st.sidebar.slider(
            "Segment Range",
            min_value=min_segment,
            max_value=max_segment,
            value=(min_segment, max_segment),
            help="Filter by segment ID range"
        )
        filters['segment_range'] = segment_range

    return filters


def apply_filters(df, filters):
    """Apply filters to dataframe"""
    if df.empty:
        return df

    filtered_df = df.copy()

    # Translator filter
    if filters.get('translator') and filters['translator'] != 'All':
        filtered_df = filtered_df[filtered_df['translator_name'] == filters['translator']]

    # Segment range filter
    if filters.get('segment_range'):
        min_seg, max_seg = filters['segment_range']
        filtered_df = filtered_df[
            (filtered_df['segment_id'] >= min_seg) &
            (filtered_df['segment_id'] <= max_seg)
        ]

    return filtered_df


def main():
    """Main analytics page"""
    load_css()
    check_pm_auth()

    st.title("📊 Performance Analytics")
    st.markdown(f"Project: **{st.session_state.project_key}**")

    # Get database manager
    db_manager = get_database_manager(
        st.session_state.db_type,
        st.session_state.db_connection
    )

    # Get translators
    project_key = st.session_state.project_key
    translators = asyncio.run(db_manager.get_project_translators(project_key))

    if not translators:
        st.warning("No translators have joined your project yet.")
        return

    # Collect all progress data
    with st.spinner("Loading analytics data..."):
        all_data_df = collect_all_progress_data(db_manager, translators)

    if all_data_df.empty:
        st.info("No activity data available yet. Translators haven't started working.")
        return

    # Display filters in sidebar
    filters = display_filters(all_data_df)

    # Apply filters
    filtered_df = apply_filters(all_data_df, filters)

    # Display metrics and visualizations
    display_overview_metrics(filtered_df)
    display_translator_comparison(filtered_df)
    display_visualizations(filtered_df)


if __name__ == "__main__":
    main()
