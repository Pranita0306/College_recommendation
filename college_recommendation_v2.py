import os
import csv
import datetime
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime as dt

# Set page config
st.set_page_config(page_title="College Recommendation System", layout="wide")

# ==================== DATABASE SETUP ====================
def init_database():
    """Initialize SQLite database with college data"""
    conn = sqlite3.connect('college_data.db')
    cursor = conn.cursor()
    
    # Create colleges table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS colleges (
            id INTEGER PRIMARY KEY,
            college_name TEXT,
            program TEXT,
            general REAL,
            obc REAL,
            sc REAL,
            st REAL
        )
    ''')
    
    # Create recommendations history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recommendations_history (
            id INTEGER PRIMARY KEY,
            percentile REAL,
            category TEXT,
            college_name TEXT,
            program TEXT,
            timestamp DATETIME
        )
    ''')
    
    # Check if data already loaded
    cursor.execute("SELECT COUNT(*) FROM colleges")
    if cursor.fetchone()[0] == 0:
        # Load from CSV
        df = pd.read_csv('college_cutoff_data_updated.csv')
        for _, row in df.iterrows():
            cursor.execute('''
                INSERT INTO colleges (college_name, program, general, obc, sc, st)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (row['College'], row['Program'], row['General'], row['OBC'], row['SC'], row['ST']))
        conn.commit()
    
    conn.close()

def get_all_colleges():
    """Fetch all colleges from database"""
    conn = sqlite3.connect('college_data.db')
    df = pd.read_sql_query("SELECT college_name, program, general, obc, sc, st FROM colleges", conn)
    conn.close()
    return df

def recommend_colleges(score, category):
    """Recommend colleges based on percentile and category"""
    conn = sqlite3.connect('college_data.db')
    category_lower = category.lower()
    
    query = f'''
        SELECT college_name, program, {category_lower} as cutoff
        FROM colleges
        WHERE {category_lower} <= ?
        ORDER BY {category_lower} DESC
    '''
    
    df = pd.read_sql_query(query, conn, params=(score,))
    conn.close()
    return df

def save_recommendation(score, category, college, program):
    """Save recommendation to database"""
    conn = sqlite3.connect('college_data.db')
    cursor = conn.cursor()
    timestamp = dt.now()
    
    cursor.execute('''
        INSERT INTO recommendations_history (percentile, category, college_name, program, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (score, category, college, program, timestamp))
    
    conn.commit()
    conn.close()

def get_history():
    """Fetch recommendation history"""
    conn = sqlite3.connect('college_data.db')
    df = pd.read_sql_query('''
        SELECT percentile, category, college_name, program, timestamp
        FROM recommendations_history
        ORDER BY timestamp DESC
    ''', conn)
    conn.close()
    return df

# Initialize database
init_database()

# ==================== STREAMLIT UI ====================
st.title("🎓 College Recommendation System")
st.markdown("---")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["Find Colleges", "Analytics", "Search", "History"])

# ==================== TAB 1: FIND COLLEGES ====================
with tab1:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        score = st.number_input("Enter your CET Percentile:", min_value=0.0, max_value=100.0, step=0.01, key="score")
    
    with col2:
        category = st.selectbox("Select your Category:", ["General", "OBC", "SC", "ST"], key="category")
    
    with col3:
        branch_filter = st.multiselect("Filter by Branch (optional):", 
                                       ["All Branches"] + list(get_all_colleges()['program'].unique()),
                                       default=["All Branches"],
                                       key="branch")
    
    # Live filtering - results update as user types
    if score > 0:
        recommendations = recommend_colleges(score, category)
        
        # Apply branch filter
        if "All Branches" not in branch_filter and branch_filter:
            recommendations = recommendations[recommendations['program'].isin(branch_filter)]
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader(f"Available Colleges for {score} percentile ({category}):")
            st.info(f"Found {len(recommendations)} colleges matching your criteria")
        
        with col2:
            if st.button("📥 Export to CSV"):
                csv = recommendations.to_csv(index=False)
                st.download_button("Download", csv, "recommendations.csv", "text/csv")
        
        if recommendations.empty:
            st.warning("❌ No colleges available for your percentile and category.")
        else:
            # Display recommendations with formatting
            st.dataframe(recommendations, use_container_width=True)
            
            # Save selected recommendations
            st.subheader("Save Recommendations")
            cols = st.columns(len(recommendations))
            for idx, (_, row) in enumerate(recommendations.iterrows()):
                with cols[idx % len(cols)]:
                    if st.button(f"💾 Save {row['college_name']}", key=f"save_{idx}"):
                        save_recommendation(score, category, row['college_name'], row['program'])
                        st.success(f"Saved: {row['college_name']}")

# ==================== TAB 2: ANALYTICS ====================
with tab2:
    st.subheader("📊 Analytics Dashboard")
    
    df_all = get_all_colleges()
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Colleges by cutoff distribution
        fig = px.box(df_all, y=['general', 'obc', 'sc', 'st'],
                     title="Cutoff Distribution by Category",
                     labels={'value': 'Percentile', 'variable': 'Category'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Top colleges by General cutoff
        top_colleges = df_all.groupby('college_name')['general'].max().sort_values(ascending=False).head(10)
        fig = px.bar(x=top_colleges.values, y=top_colleges.index,
                     orientation='h', title="Top 10 Colleges by General Cutoff",
                     labels={'x': 'General Cutoff %', 'y': 'College'})
        st.plotly_chart(fig, use_container_width=True)
    
    # Recommendations over time
    history_df = get_history()
    if not history_df.empty:
        history_df['timestamp'] = pd.to_datetime(history_df['timestamp'])
        daily_recommendations = history_df.groupby(history_df['timestamp'].dt.date).size()
        
        fig = px.line(x=daily_recommendations.index, y=daily_recommendations.values,
                      title="Recommendations Over Time",
                      labels={'x': 'Date', 'y': 'Number of Recommendations'})
        st.plotly_chart(fig, use_container_width=True)

# ==================== TAB 3: SEARCH ====================
with tab3:
    st.subheader("🔍 Search College")
    
    df_all = get_all_colleges()
    college_names = sorted(df_all['college_name'].unique())
    
    selected_college = st.selectbox("Select a College:", college_names)
    
    if selected_college:
        college_data = df_all[df_all['college_name'] == selected_college]
        
        st.subheader(f"Programs at {selected_college}")
        st.dataframe(college_data[['program', 'general', 'obc', 'sc', 'st']], use_container_width=True)
        
        # Cutoff comparison
        fig = px.bar(college_data, x='program', y=['general', 'obc', 'sc', 'st'],
                     title=f"Cutoff by Category - {selected_college}",
                     barmode='group')
        st.plotly_chart(fig, use_container_width=True)

# ==================== TAB 4: HISTORY ====================
with tab4:
    st.subheader("📋 Recommendation History")
    
    history_df = get_history()
    
    if history_df.empty:
        st.info("No recommendations saved yet.")
    else:
        col1, col2 = st.columns([3, 1])
        
        with col2:
            if st.button("🗑️ Clear History"):
                conn = sqlite3.connect('college_data.db')
                cursor = conn.cursor()
                cursor.execute("DELETE FROM recommendations_history")
                conn.commit()
                conn.close()
                st.success("History cleared!")
                st.rerun()
        
        # Display history with filters
        col1, col2 = st.columns(2)
        
        with col1:
            filter_category = st.multiselect("Filter by Category:", history_df['category'].unique())
        
        with col2:
            filter_college = st.multiselect("Filter by College:", history_df['college_name'].unique())
        
        filtered_history = history_df.copy()
        
        if filter_category:
            filtered_history = filtered_history[filtered_history['category'].isin(filter_category)]
        if filter_college:
            filtered_history = filtered_history[filtered_history['college_name'].isin(filter_college)]
        
        st.dataframe(filtered_history, use_container_width=True)
        
        # Statistics
        if not filtered_history.empty:
            st.subheader("Statistics")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Searches", len(filtered_history))
            with col2:
                st.metric("Unique Colleges", filtered_history['college_name'].nunique())
            with col3:
                st.metric("Avg Percentile", f"{filtered_history['percentile'].mean():.2f}")

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using Streamlit | Database: SQLite")
