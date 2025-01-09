import streamlit as st
import pandas as pd
from pymongo import MongoClient
from datetime import datetime
import plotly.express as px
import json

# Page configuration
st.set_page_config(
    page_title="MTPE Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_css():
    """Load custom CSS from the static/styles.css file."""
    with open("static/styles.css", "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def connect_to_mongodb():
    """Establish connection to MongoDB."""
    connection_string = st.secrets["MONGO_CONNECTION_STRING"]
    client = MongoClient(connection_string, tlsAllowInvalidCertificates=True)
    return client['mtpe_database']

def get_user_metrics() -> pd.DataFrame:
    """Retrieve and process user metrics from MongoDB."""
    db = connect_to_mongodb()
    collection = db['user_progress']
    user_data = list(collection.find())
    
    if not user_data:
        return pd.DataFrame()
    
    processed_data = []
    for doc in user_data:
        if 'metrics' in doc:
            for metric in doc['metrics']:
                metric['user_name'] = doc['user_name']
                metric['user_surname'] = doc['user_surname']
                metric['timestamp'] = doc.get('last_updated', datetime.now())
                processed_data.append(metric)
    
    return pd.DataFrame(processed_data)

def format_number(num: float) -> str:
    """Format numbers for better readability."""
    if num >= 1000:
        return f"{num/1000:.1f}k"
    return f"{num:.0f}"

def main():
    load_css()
    
    # Dashboard Header with improved styling
    st.markdown("""
        <div class="dashboard-header">
            <h1 style='text-align: center; margin-bottom: 0.75rem;'>📊 MTPE Analytics Dashboard</h1>
            <p class="section-subtitle">
                Monitor translator performance, analyze segments, and manage user data in one unified interface.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Fetch data
    df = get_user_metrics()
    if df.empty:
        st.markdown("""
            <div class="empty-state">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-bottom: 1rem; color: #94a3b8;">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="8" x2="12" y2="12"></line>
                    <line x1="12" y1="16" x2="12.01" y2="16"></line>
                </svg>
                <h3 style="color: #374151; margin-bottom: 0.5rem;">No MTPE Data Available</h3>
                <p style="color: #6b7280;">Users need to complete some translations first.</p>
            </div>
        """, unsafe_allow_html=True)
        return
    
    # Create tabs with improved styling
    tabs = st.tabs([
        "📈  Performance Analytics",
        "🔍  Segment Analysis",
        "👥  User Management"
    ])
    
    # =================== TAB 1: Performance Analytics ===================
    with tabs[0]:
        st.markdown("""
            <div class="section-header">
                <h2 style="margin-bottom: 0.5rem;">Translator Performance Overview</h2>
                <p style="color: #4a5568;">Compare productivity metrics and efficiency across all translators.</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Quick Stats Row
        col1, col2, col3, col4 = st.columns(4)
        total_segments = df['segment_id'].nunique()
        total_words = sum(len(text.split()) for text in df['original'])
        avg_time = df['edit_time'].mean()
        total_edits = df['insertions'].sum() + df['deletions'].sum()
        
        metrics = [
            {"value": format_number(total_segments), "label": "Total Segments", "icon": "📝"},
            {"value": format_number(total_words), "label": "Total Words", "icon": "📚"},
            {"value": f"{avg_time:.1f}s", "label": "Avg. Time per Segment", "icon": "⏱️"},
            {"value": format_number(total_edits), "label": "Total Edits", "icon": "✏️"}
        ]
        
        for col, metric in zip([col1, col2, col3, col4], metrics):
            with col:
                st.markdown(f"""
                    <div class="metric-card">
                        <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                            <span style="font-size: 1.5rem; margin-right: 0.5rem;">{metric['icon']}</span>
                            <span style="color: #4a5568; font-size: 0.875rem;">{metric['label']}</span>
                        </div>
                        <h3 style="font-size: 2rem; color: #1a2333; margin: 0;">{metric['value']}</h3>
                    </div>
                """, unsafe_allow_html=True)
        
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # Performance Metrics Section
        st.markdown("""
            <div class="metrics-section">
                <h3 style="font-size: 1.25rem; margin-bottom: 1rem;">Detailed Performance Metrics</h3>
            </div>
        """, unsafe_allow_html=True)
        
        # Compute user statistics with improved presentation
        user_stats = df.groupby(['user_name', 'user_surname']).agg({
            'edit_time': ['mean', 'sum'],
            'insertions': ['mean', 'sum'],
            'deletions': ['mean', 'sum'],
            'segment_id': 'count',
            'original': lambda x: sum(len(text.split()) for text in x)
        }).reset_index()

        user_stats.columns = [
            'Name',
            'Surname',
            'Avg Time/Segment (s)',
            'Total Time (s)',
            'Avg Insertions',
            'Total Insertions',
            'Avg Deletions',
            'Total Deletions',
            'Segments Completed',
            'Words Processed'
        ]
        
        user_stats['Words/Hour'] = (
            user_stats['Words Processed'] / (user_stats['Total Time (s)'] / 3600)
        ).round(1)
        
        user_stats['Edits/Segment'] = (
            (user_stats['Total Insertions'] + user_stats['Total Deletions']) /
            user_stats['Segments Completed']
        ).round(1)
        
        st.dataframe(
            user_stats.style
            .format({
                'Avg Time/Segment (s)': '{:.1f}',
                'Total Time (s)': '{:.1f}',
                'Avg Insertions': '{:.1f}',
                'Avg Deletions': '{:.1f}',
                'Words/Hour': '{:.1f}',
                'Edits/Segment': '{:.1f}'
            })
            .background_gradient(subset=['Words/Hour'], cmap='Greys')
            .background_gradient(subset=['Segments Completed'], cmap='Greys'),
            use_container_width=True
        )
    
        
        # Export Section
        st.markdown("<hr>", unsafe_allow_html=True)
        
        st.markdown("""
            <div class="export-section">
                <h3 style="font-size: 1.25rem; margin-bottom: 0.5rem;">Export Individual Data</h3>
                <p style="color: #4a5568; margin-bottom: 1.5rem;">Download detailed metrics for each translator in your preferred format.</p>
            </div>
        """, unsafe_allow_html=True)

        for _, user_row in user_stats.iterrows():
            user_name = user_row['Name']
            user_surname = user_row['Surname']
            
            user_data = df[
                (df['user_name'] == user_name) &
                (df['user_surname'] == user_surname)
            ].copy()
            
            st.markdown(
                f"""
                <div class="export-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h4 style="margin: 0;">{user_name} {user_surname}</h4>
                            <p style="margin: 0.5rem 0 0 0; color: #4a5568;">
                                {len(user_data)} segments | {user_row['Words Processed']:.0f} words
                            </p>
                        </div>
                        <div style="display: flex; gap: 1rem;">
                """,
                unsafe_allow_html=True
            )
            
            col1, col2 = st.columns([1, 1])
            with col1:
                csv_data = user_data.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv_data,
                    file_name=f"{user_name}_{user_surname}_metrics.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col2:
                json_data = []
                for _, row in user_data.iterrows():
                    json_data.append({
                        "segment_id": row['segment_id'],
                        "source": row.get('source', ''),
                        "original_translation": row['original'],
                        "post_edited": row['edited'],
                        "edit_time_seconds": round(row['edit_time'], 2),
                        "insertions": row['insertions'],
                        "deletions": row['deletions']
                    })
                json_str = json.dumps(json_data, indent=2, ensure_ascii=False)
                
                st.download_button(
                    label="📥 Download JSON",
                    data=json_str,
                    file_name=f"{user_name}_{user_surname}_segments.json",
                    mime="application/json",
                    use_container_width=True
                )
            
            st.markdown("</div></div></div>", unsafe_allow_html=True)

    # =================== TAB 2: Segment Analysis ===================
    with tabs[1]:
        st.markdown("""
            <div class="section-header">
                <h2 style="margin-bottom: 0.5rem;">Segment Analysis</h2>
                <p style="color: #4a5568;">Search and analyze individual translation segments and their modifications.</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Search and Filter Section
        st.markdown("""
            <div class="search-section">
                <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                    <span style="font-size: 1.5rem; margin-right: 0.75rem;">🔍</span>
                    <h3 style="margin: 0; font-size: 1.25rem;">Search and Filter</h3>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            search_term = st.text_input("Search in segments", placeholder="Enter text to search...")
        with col2:
            min_edits = st.number_input("Minimum edits", value=0, min_value=0)
        with col3:
            if st.button("Reset Filters", type="secondary", use_container_width=True):
                search_term = ""
                min_edits = 0
                st.experimental_rerun()
        
        # Filter and display segments
        filtered_df = df.copy()
        if search_term:
            segment_mask = (
                filtered_df['original'].str.contains(search_term, case=False, na=False) |
                filtered_df['edited'].str.contains(search_term, case=False, na=False)
            )
            filtered_df = filtered_df[segment_mask]
        if min_edits > 0:
            filtered_df = filtered_df[
                (filtered_df['insertions'] + filtered_df['deletions']) >= min_edits
            ]
        
        # Display segments with improved styling
        if not filtered_df.empty:
            for _, row in filtered_df.iterrows():
                st.markdown(f"""
                    <div class="segment-card">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem;">
                            <div style="display: flex; align-items: center;">
                                <span style="color: #4a5568; font-weight: 500;">Segment ID: {row['segment_id']}</span>
                            </div>
                            <span style="color: #4a5568;">Translator: {row['user_name']} {row['user_surname']}</span>
                        </div>
                        <div class="segment-content">
                            <div style="margin-bottom: 1.25rem;">
                                <p style="color: #1a2333; font-weight: 500; margin-bottom: 0.75rem;">Original Text</p>
                                <div class="segment-text">
                                    {row['original']}
                                </div>
                            </div>
                            <div style="margin-bottom: 1.25rem;">
                                <p style="color: #1a2333; font-weight: 500; margin-bottom: 0.75rem;">Edited Text</p>
                                <div class="segment-text" style="border-left: 3px solid #1a2333;">
                                    {row['edited']}
                                </div>
                            </div>
                            <div style="display: flex; gap: 2rem; color: #4a5568; font-size: 0.875rem;">
                                <div style="display: flex; align-items: center;">
                                    <span style="margin-right: 0.5rem;">⏱️</span>
                                    <span>Edit Time: {row['edit_time']:.1f}s</span>
                                </div>
                                <div style="display: flex; align-items: center;">
                                    <span style="margin-right: 0.5rem;">➕</span>
                                    <span>Insertions: {row['insertions']}</span>
                                </div>
                                <div style="display: flex; align-items: center;">
                                    <span style="margin-right: 0.5rem;">➖</span>
                                    <span>Deletions: {row['deletions']}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class="empty-state">
                    <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-bottom: 1rem; color: #94a3b8;">
                        <circle cx="12" cy="12" r="10"></circle>
                        <path d="M8 12h8"></path>
                    </svg>
                    <h3 style="color: #374151; margin-bottom: 0.5rem;">No matching segments found</h3>
                    <p style="color: #6b7280;">Try adjusting your search criteria</p>
                </div>
            """, unsafe_allow_html=True)

    # =================== TAB 3: User Management ===================
    with tabs[2]:
        st.markdown("""
            <div class="section-header">
                <h2 style="margin-bottom: 0.5rem;">User Management</h2>
                <p style="color: #4a5568;">Manage translator accounts and their associated data.</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Warning Card
        st.markdown("""
            <div class="warning-card">
                <div style="display: flex; align-items: center; margin-bottom: 0.75rem;">
                    <span style="font-size: 1.5rem; margin-right: 0.75rem;">⚠️</span>
                    <h4 style="margin: 0; color: #92400e;">Data Deletion Warning</h4>
                </div>
                <p style="color: #92400e; margin: 0;">
                    Deleting user data is a permanent action and cannot be undone.
                    Make sure you have the necessary backups before proceeding.
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        users = df[['user_name', 'user_surname']].drop_duplicates().to_dict('records')
        if not users:
            st.markdown("""
                <div class="empty-state">
                    <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-bottom: 1rem; color: #94a3b8;">
                        <circle cx="12" cy="12" r="10"></circle>
                        <path d="M8 15l8-8"></path>
                        <path d="M16 15l-8-8"></path>
                    </svg>
                    <h3 style="color: #374151; margin-bottom: 0.5rem;">No Users Found</h3>
                    <p style="color: #6b7280;">No users are currently registered in the database.</p>
                </div>
            """, unsafe_allow_html=True)
            return

        if 'confirm_delete' not in st.session_state:
            st.session_state.confirm_delete = None

        # User Cards Grid
        for i in range(0, len(users), 2):
            col1, col2 = st.columns(2)
            
            with col1:
                if i < len(users):
                    user = users[i]
                    user_id = f"{user['user_name']}_{user['user_surname']}"
                    
                    st.markdown(f"""
                        <div class="user-card">
                            <div style="display: flex; align-items: center; margin-bottom: 1.25rem;">
                                <div style="width: 40px; height: 40px; background: #e2e8f0; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 1rem;">
                                    <span style="font-size: 1.25rem;">👤</span>
                                </div>
                                <h4 style="margin: 0;">{user['user_name']} {user['user_surname']}</h4>
                            </div>
                    """, unsafe_allow_html=True)
                    
                    if st.session_state.confirm_delete == user_id:
                        if st.button("⚠️ Confirm Deletion",
                                   key=f"confirm_{user_id}",
                                   type="primary"):
                            db = connect_to_mongodb()
                            collection = db['user_progress']
                            result = collection.delete_one({
                                'user_name': user['user_name'],
                                'user_surname': user['user_surname']
                            })
                            
                            if result.deleted_count > 0:
                                st.success(f"Data for {user['user_name']} {user['user_surname']} deleted successfully!")
                                st.session_state.confirm_delete = None
                                st.experimental_rerun()
                            else:
                                st.error("Failed to delete user data. Please try again.")
                                st.session_state.confirm_delete = None
                    else:
                        if st.button("🗑️ Delete User Data",
                                   key=f"delete_{user_id}",
                                   type="secondary"):
                            st.session_state.confirm_delete = user_id
                            st.experimental_rerun()
                    
                    st.markdown("</div>", unsafe_allow_html=True)
            
            with col2:
                if i + 1 < len(users):
                    user = users[i + 1]
                    user_id = f"{user['user_name']}_{user['user_surname']}"
                    
                    st.markdown(f"""
                        <div class="user-card">
                            <div style="display: flex; align-items: center; margin-bottom: 1.25rem;">
                                <div style="width: 40px; height: 40px; background: #e2e8f0; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 1rem;">
                                    <span style="font-size: 1.25rem;">👤</span>
                                </div>
                                <h4 style="margin: 0;">{user['user_name']} {user['user_surname']}</h4>
                            </div>
                    """, unsafe_allow_html=True)
                    
                    if st.session_state.confirm_delete == user_id:
                        if st.button("⚠️ Confirm Deletion",
                                   key=f"confirm_{user_id}",
                                   type="primary"):
                            db = connect_to_mongodb()
                            collection = db['user_progress']
                            result = collection.delete_one({
                                'user_name': user['user_name'],
                                'user_surname': user['user_surname']
                            })
                            
                            if result.deleted_count > 0:
                                st.success(f"Data for {user['user_name']} {user['user_surname']} deleted successfully!")
                                st.session_state.confirm_delete = None
                                st.experimental_rerun()
                            else:
                                st.error("Failed to delete user data. Please try again.")
                                st.session_state.confirm_delete = None
                    else:
                        if st.button("🗑️ Delete User Data",
                                   key=f"delete_{user_id}",
                                   type="secondary"):
                            st.session_state.confirm_delete = user_id
                            st.experimental_rerun()
                    
                    st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
