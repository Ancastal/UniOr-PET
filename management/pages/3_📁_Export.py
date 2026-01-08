"""
Project Manager Data Export - Export Translation Data and Metrics
UniOr-PET Management Interface
"""
import streamlit as st
import asyncio
import sys
from pathlib import Path
import pandas as pd
import json
from io import BytesIO
from datetime import datetime

# Add parent directory to path to import shared modules
parent_dir = Path(__file__).parent.parent.parent
sys.path.append(str(parent_dir))

from db_manager import get_database_manager

# Page configuration
st.set_page_config(
    page_title="Data Export - PM Dashboard",
    page_icon="📁",
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


def collect_export_data(db_manager, translators, selected_translators):
    """Collect data for export based on selections"""
    export_data = []

    for translator in translators:
        # Skip if not selected
        translator_name = f"{translator['name']} {translator['surname']}"
        if selected_translators != ['All'] and translator_name not in selected_translators:
            continue

        try:
            metrics_df, full_text, time_tracker, timer_mode = asyncio.run(
                db_manager.load_progress(translator['name'], translator['surname'])
            )

            if not metrics_df.empty:
                # Add translator identification
                metrics_df['translator_name'] = translator_name
                metrics_df['translator_first_name'] = translator['name']
                metrics_df['translator_last_name'] = translator['surname']
                export_data.append(metrics_df)

        except Exception as e:
            st.warning(f"Could not load data for {translator_name}: {str(e)}")
            continue

    if export_data:
        return pd.concat(export_data, ignore_index=True)
    else:
        return pd.DataFrame()


def export_to_csv(df):
    """Convert dataframe to CSV"""
    return df.to_csv(index=False).encode('utf-8')


def export_to_json(df):
    """Convert dataframe to JSON"""
    return df.to_json(orient='records', indent=2).encode('utf-8')


def export_to_excel(df):
    """Convert dataframe to Excel with multiple sheets"""
    output = BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Main data sheet
        df.to_excel(writer, sheet_name='All Data', index=False)

        # Summary sheet
        if 'translator_name' in df.columns:
            summary = df.groupby('translator_name').agg({
                'segment_id': 'count',
                'edit_time': ['sum', 'mean'],
                'insertions': 'sum',
                'deletions': 'sum'
            }).reset_index()

            summary.columns = ['Translator', 'Segments', 'Total Time (s)', 'Avg Time (s)', 'Insertions', 'Deletions']
            summary.to_excel(writer, sheet_name='Summary', index=False)

    return output.getvalue()


def create_aggregate_report(df):
    """Create an aggregated summary report"""
    if df.empty:
        return pd.DataFrame()

    # Overall statistics
    overall_stats = {
        'Metric': [
            'Total Segments Edited',
            'Total Translators',
            'Total Editing Time (s)',
            'Average Time per Segment (s)',
            'Total Insertions',
            'Total Deletions',
            'Total Edits'
        ],
        'Value': [
            len(df),
            df['translator_name'].nunique() if 'translator_name' in df.columns else 0,
            df['edit_time'].sum() if 'edit_time' in df.columns else 0,
            df['edit_time'].mean() if 'edit_time' in df.columns else 0,
            df['insertions'].sum() if 'insertions' in df.columns else 0,
            df['deletions'].sum() if 'deletions' in df.columns else 0,
            (df['insertions'].sum() + df['deletions'].sum()) if 'insertions' in df.columns and 'deletions' in df.columns else 0
        ]
    }

    return pd.DataFrame(overall_stats)


def main():
    """Main export page"""
    load_css()
    check_pm_auth()

    st.title("📁 Data Export")
    st.markdown(f"Export data from project: **{st.session_state.project_key}**")

    # Get database manager
    db_manager = get_database_manager(
        st.session_state.db_type,
        st.session_state.db_connection
    )

    # Get translators
    project_key = st.session_state.project_key

    try:
        translators = asyncio.run(db_manager.get_project_translators(project_key))

        if not translators:
            st.warning("No translators have joined your project yet.")
            return

        # Export options
        st.markdown("### ⚙️ Export Options")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Select Translators**")
            translator_names = [f"{t['name']} {t['surname']}" for t in translators]
            selected_translators = st.multiselect(
                "Choose translators to include",
                ['All'] + translator_names,
                default=['All'],
                help="Select specific translators or 'All' for everyone"
            )

        with col2:
            st.markdown("**Export Format**")
            export_format = st.radio(
                "Choose format",
                ['CSV', 'JSON', 'Excel'],
                help="Select the output format for your data"
            )

        # Export type
        st.markdown("**Export Type**")
        export_type = st.radio(
            "What would you like to export?",
            [
                'Complete Data (all metrics)',
                'Summary Report (aggregated statistics)',
                'Both'
            ],
            help="Choose what data to include in the export"
        )

        # Collect data
        st.markdown("---")
        st.markdown("### 📊 Data Preview")

        with st.spinner("Loading data..."):
            export_df = collect_export_data(db_manager, translators, selected_translators)

        if export_df.empty:
            st.warning("No data available for the selected translators.")
            return

        # Show preview
        st.markdown(f"**Total records to export:** {len(export_df)}")

        # Display preview
        preview_df = export_df.head(10)

        # Select columns to show in preview
        columns_to_preview = []
        for col in ['segment_id', 'translator_name', 'edit_time', 'insertions', 'deletions', 'original', 'edited']:
            if col in preview_df.columns:
                columns_to_preview.append(col)

        if columns_to_preview:
            st.dataframe(
                preview_df[columns_to_preview],
                use_container_width=True,
                hide_index=True
            )

        if len(export_df) > 10:
            st.info(f"Showing first 10 of {len(export_df)} records")

        # Summary statistics
        if export_type in ['Summary Report (aggregated statistics)', 'Both']:
            st.markdown("---")
            st.markdown("### 📈 Summary Statistics")

            summary_df = create_aggregate_report(export_df)
            st.dataframe(summary_df, use_container_width=True, hide_index=True)

        # Export buttons
        st.markdown("---")
        st.markdown("### 💾 Download")

        col1, col2, col3 = st.columns(3)

        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_filename = f"{project_key}_export_{timestamp}"

        # Export complete data
        if export_type in ['Complete Data (all metrics)', 'Both']:
            with col1:
                if export_format == 'CSV':
                    csv_data = export_to_csv(export_df)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv_data,
                        file_name=f"{base_filename}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                elif export_format == 'JSON':
                    json_data = export_to_json(export_df)
                    st.download_button(
                        label="📥 Download JSON",
                        data=json_data,
                        file_name=f"{base_filename}.json",
                        mime="application/json",
                        use_container_width=True
                    )
                elif export_format == 'Excel':
                    excel_data = export_to_excel(export_df)
                    st.download_button(
                        label="📥 Download Excel",
                        data=excel_data,
                        file_name=f"{base_filename}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

        # Export summary
        if export_type in ['Summary Report (aggregated statistics)', 'Both']:
            with col2:
                summary_df = create_aggregate_report(export_df)

                if export_format == 'CSV':
                    csv_summary = export_to_csv(summary_df)
                    st.download_button(
                        label="📥 Download Summary CSV",
                        data=csv_summary,
                        file_name=f"{base_filename}_summary.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                elif export_format == 'JSON':
                    json_summary = export_to_json(summary_df)
                    st.download_button(
                        label="📥 Download Summary JSON",
                        data=json_summary,
                        file_name=f"{base_filename}_summary.json",
                        mime="application/json",
                        use_container_width=True
                    )
                elif export_format == 'Excel':
                    # Excel already includes summary sheet
                    st.info("Summary included in Excel file")

        # Export by translator (individual files)
        with col3:
            if 'All' not in selected_translators and len(selected_translators) > 0:
                st.markdown("**Individual Exports**")

                for translator_name in selected_translators:
                    translator_df = export_df[export_df['translator_name'] == translator_name]

                    if not translator_df.empty:
                        filename = f"{translator_name.replace(' ', '_')}_{timestamp}"

                        if export_format == 'CSV':
                            csv_data = export_to_csv(translator_df)
                            st.download_button(
                                label=f"📥 {translator_name}",
                                data=csv_data,
                                file_name=f"{filename}.csv",
                                mime="text/csv",
                                use_container_width=True,
                                key=f"download_{translator_name}"
                            )

        # Export information
        st.markdown("---")
        st.info("""
        **Export Information:**
        - CSV: Best for importing into spreadsheet software
        - JSON: Best for programmatic processing
        - Excel: Includes summary sheet with aggregated statistics
        - Individual exports available when specific translators are selected
        """)

    except Exception as e:
        st.error(f"Error during export: {str(e)}")
        if st.checkbox("Show error details"):
            st.exception(e)


if __name__ == "__main__":
    main()
