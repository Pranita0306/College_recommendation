import os
import csv
import datetime
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime as dt
import numpy as np

# Set page config
st.set_page_config(page_title="Advanced College Recommendation System", layout="wide")

# ==================== DATABASE SETUP ====================
def init_advanced_database():
    """Initialize SQLite database with all features"""
    conn = sqlite3.connect('college_data_advanced.db')
    cursor = conn.cursor()
    
    # Colleges table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS colleges (
            id INTEGER PRIMARY KEY,
            college_name TEXT,
            program TEXT,
            location TEXT,
            district TEXT,
            college_type TEXT,
            general REAL,
            obc REAL,
            sc REAL,
            st REAL
        )
    ''')
    
    # Historical cutoffs (2021-2025)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historical_cutoffs (
            id INTEGER PRIMARY KEY,
            college_name TEXT,
            program TEXT,
            year INTEGER,
            general REAL,
            obc REAL,
            sc REAL,
            st REAL
        )
    ''')
    
    # Placement statistics
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS placements (
            id INTEGER PRIMARY KEY,
            college_name TEXT,
            program TEXT,
            placement_percentage REAL,
            avg_package REAL,
            max_package REAL,
            min_package REAL,
            companies_count INTEGER,
            year INTEGER
        )
    ''')
    
    # NIRF Rankings
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS nirf_rankings (
            id INTEGER PRIMARY KEY,
            college_name TEXT,
            ranking INTEGER,
            category TEXT,
            score REAL,
            year INTEGER
        )
    ''')
    
    # Recommendations history
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
    
    conn.commit()
    conn.close()

def load_college_data():
    """Load college data from CSV to database"""
    conn = sqlite3.connect('college_data_advanced.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM colleges")
    if cursor.fetchone()[0] == 0:
        try:
            df = pd.read_csv('college_cutoff_data_updated.csv')
            for _, row in df.iterrows():
                cursor.execute('''
                    INSERT INTO colleges (college_name, program, location, district, college_type, general, obc, sc, st)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row.get('College', 'Unknown'),
                    row.get('Program', 'Unknown'),
                    row.get('Location', 'Unknown'),
                    row.get('District', 'Unknown'),
                    row.get('Type', 'Private'),
                    float(row.get('General', 0)),
                    float(row.get('OBC', 0)),
                    float(row.get('SC', 0)),
                    float(row.get('ST', 0))
                ))
            conn.commit()
            print("✓ College data loaded")
        except Exception as e:
            print(f"Error loading data: {e}")
    
    conn.close()

def generate_historical_data():
    """Generate historical cutoff trends (2021-2025)"""
    conn = sqlite3.connect('college_data_advanced.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM historical_cutoffs")
    if cursor.fetchone()[0] == 0:
        df = pd.read_sql_query("SELECT * FROM colleges", conn)
        
        for _, college in df.iterrows():
            for year in range(2021, 2026):
                # Simulate cutoff trends (slight yearly variation)
                variation = (2025 - year) * 0.5  # Gradual increase
                
                cursor.execute('''
                    INSERT INTO historical_cutoffs (college_name, program, year, general, obc, sc, st)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    college['college_name'],
                    college['program'],
                    year,
                    max(0, college['general'] - variation + np.random.uniform(-2, 2)),
                    max(0, college['obc'] - variation + np.random.uniform(-2, 2)),
                    max(0, college['sc'] - variation + np.random.uniform(-2, 2)),
                    max(0, college['st'] - variation + np.random.uniform(-2, 2))
                ))
        
        conn.commit()
        print("✓ Historical data generated")
    
    conn.close()

def generate_placement_data():
    """Generate placement statistics"""
    conn = sqlite3.connect('college_data_advanced.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM placements")
    if cursor.fetchone()[0] == 0:
        df = pd.read_sql_query("SELECT DISTINCT college_name, program FROM colleges", conn)
        
        for _, row in df.iterrows():
            college = row['college_name']
            program = row['program']
            
            for year in range(2023, 2026):
                placement_pct = np.random.uniform(75, 100)
                avg_pkg = np.random.uniform(5, 15)  # in LPA
                
                cursor.execute('''
                    INSERT INTO placements (college_name, program, placement_percentage, avg_package, max_package, min_package, companies_count, year)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    college,
                    program,
                    round(placement_pct, 2),
                    round(avg_pkg, 2),
                    round(avg_pkg + 5, 2),
                    round(avg_pkg - 3, 2),
                    np.random.randint(20, 100),
                    year
                ))
        
        conn.commit()
        print("✓ Placement data generated")
    
    conn.close()

def generate_nirf_rankings():
    """Generate NIRF rankings"""
    conn = sqlite3.connect('college_data_advanced.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM nirf_rankings")
    if cursor.fetchone()[0] == 0:
        colleges = pd.read_sql_query("SELECT DISTINCT college_name FROM colleges", conn)
        
        ranking = 1
        for _, row in colleges.iterrows():
            score = np.random.uniform(40, 100)
            
            cursor.execute('''
                INSERT INTO nirf_rankings (college_name, ranking, category, score, year)
                VALUES (?, ?, ?, ?, ?)
            ''', (row['college_name'], ranking, 'Engineering', round(score, 2), 2024))
            
            ranking += 1
        
        conn.commit()
        print("✓ NIRF rankings generated")
    
    conn.close()

# Initialize everything
init_advanced_database()
load_college_data()
generate_historical_data()
generate_placement_data()
generate_nirf_rankings()

# ==================== HELPER FUNCTIONS ====================

def get_colleges_for_comparison():
    """Get list of colleges"""
    conn = sqlite3.connect('college_data_advanced.db')
    df = pd.read_sql_query("SELECT DISTINCT college_name FROM colleges ORDER BY college_name", conn)
    conn.close()
    return df['college_name'].tolist()

def get_college_details(college_name):
    """Get full details of a college"""
    conn = sqlite3.connect('college_data_advanced.db')
    
    college = pd.read_sql_query(
        "SELECT * FROM colleges WHERE college_name = ? LIMIT 1",
        conn, params=(college_name,)
    )
    
    programs = pd.read_sql_query(
        "SELECT program, general, obc, sc, st FROM colleges WHERE college_name = ?",
        conn, params=(college_name,)
    )
    
    placements = pd.read_sql_query(
        "SELECT * FROM placements WHERE college_name = ? AND year = 2024",
        conn, params=(college_name,)
    )
    
    ranking = pd.read_sql_query(
        "SELECT * FROM nirf_rankings WHERE college_name = ? AND year = 2024",
        conn, params=(college_name,)
    )
    
    conn.close()
    
    return college, programs, placements, ranking

def predict_eligibility(user_score, user_category, college_name, program):
    """Predict if user is eligible and in which round"""
    conn = sqlite3.connect('college_data_advanced.db')
    
    cutoff = pd.read_sql_query(
        "SELECT * FROM colleges WHERE college_name = ? AND program = ?",
        conn, params=(college_name, program)
    )
    
    conn.close()
    
    if cutoff.empty:
        return None, None
    
    category_col = user_category.lower()
    cutoff_val = cutoff[category_col].values[0]
    
    diff = user_score - cutoff_val
    
    if diff >= 5:
        round_num = 1
        eligibility = "✓ Highly Likely in Round 1"
        confidence = 95
    elif diff >= 0:
        round_num = 1
        eligibility = "✓ Likely in Round 1"
        confidence = 75
    elif diff >= -3:
        round_num = 2
        eligibility = "⚠️ Possible in Round 2"
        confidence = 50
    elif diff >= -8:
        round_num = 3
        eligibility = "⚠️ Possible in Round 3"
        confidence = 30
    else:
        round_num = None
        eligibility = "✗ Unlikely"
        confidence = 5
    
    return {
        "eligibility": eligibility,
        "round": round_num,
        "confidence": confidence,
        "difference": round(diff, 2),
        "your_score": user_score,
        "college_cutoff": round(cutoff_val, 2)
    }

# ==================== STREAMLIT UI ====================

st.title("🎓 Advanced College Recommendation System")
st.markdown("---")

# Create tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Find Colleges",
    "Cutoff Trends",
    "College Comparison",
    "Placements",
    "Eligibility Checker",
    "Counseling Predictor"
])

# ==================== TAB 1: FIND COLLEGES ====================
with tab1:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        score = st.number_input("CET Percentile:", min_value=0.0, max_value=100.0, step=0.01)
    
    with col2:
        category = st.selectbox("Category:", ["General", "OBC", "SC", "ST"])
    
    with col3:
        max_results = st.number_input("Max Results:", min_value=5, max_value=100, value=20)
    
    if score > 0:
        conn = sqlite3.connect('college_data_advanced.db')
        category_col = category.lower()
        
        recommendations = pd.read_sql_query(f'''
            SELECT college_name, program, {category_col} as cutoff, location, district
            FROM colleges
            WHERE {category_col} <= ?
            ORDER BY {category_col} DESC
            LIMIT ?
        ''', conn, params=(score, max_results))
        
        conn.close()
        
        if recommendations.empty:
            st.warning("No colleges available")
        else:
            st.success(f"Found {len(recommendations)} colleges")
            st.dataframe(recommendations, use_container_width=True)

# ==================== TAB 2: CUTOFF TRENDS ====================
with tab2:
    st.subheader("📈 Historical Cutoff Trends (2021-2025)")
    
    colleges = get_colleges_for_comparison()
    selected_college = st.selectbox("Select College:", colleges, key="trend_college")
    selected_program = st.selectbox("Select Program:", ["All"] + 
                                    pd.read_sql_query(
                                        "SELECT DISTINCT program FROM colleges WHERE college_name = ?",
                                        sqlite3.connect('college_data_advanced.db'),
                                        params=(selected_college,)
                                    )['program'].tolist(),
                                    key="trend_program")
    
    if selected_college:
        conn = sqlite3.connect('college_data_advanced.db')
        
        if selected_program == "All":
            trends = pd.read_sql_query('''
                SELECT year, general, obc, sc, st
                FROM historical_cutoffs
                WHERE college_name = ?
                ORDER BY year
            ''', conn, params=(selected_college,))
            
            if not trends.empty:
                # Aggregate by year
                trends_agg = trends.groupby('year')[['general', 'obc', 'sc', 'st']].mean()
                
                fig = go.Figure()
                for col in ['general', 'obc', 'sc', 'st']:
                    fig.add_trace(go.Scatter(
                        x=trends_agg.index,
                        y=trends_agg[col],
                        name=col.capitalize(),
                        mode='lines+markers'
                    ))
                
                fig.update_layout(
                    title=f"Cutoff Trends - {selected_college}",
                    xaxis_title="Year",
                    yaxis_title="Cutoff Percentile",
                    hovermode='x unified'
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            trends = pd.read_sql_query('''
                SELECT year, general, obc, sc, st
                FROM historical_cutoffs
                WHERE college_name = ? AND program = ?
                ORDER BY year
            ''', conn, params=(selected_college, selected_program))
            
            if not trends.empty:
                fig = go.Figure()
                for col in ['general', 'obc', 'sc', 'st']:
                    fig.add_trace(go.Scatter(
                        x=trends['year'],
                        y=trends[col],
                        name=col.capitalize(),
                        mode='lines+markers'
                    ))
                
                fig.update_layout(
                    title=f"Cutoff Trends - {selected_college} ({selected_program})",
                    xaxis_title="Year",
                    yaxis_title="Cutoff Percentile"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        conn.close()

# ==================== TAB 3: COLLEGE COMPARISON ====================
with tab3:
    st.subheader("⚖️ Compare Colleges Side-by-Side")
    
    colleges = get_colleges_for_comparison()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        college1 = st.selectbox("College 1:", colleges, key="comp1")
    with col2:
        college2 = st.selectbox("College 2:", colleges, key="comp2", index=1 if len(colleges) > 1 else 0)
    with col3:
        college3 = st.selectbox("College 3 (Optional):", ["None"] + colleges, key="comp3")
    
    # Get data for comparison
    colleges_to_compare = [college1, college2]
    if college3 != "None":
        colleges_to_compare.append(college3)
    
    conn = sqlite3.connect('college_data_advanced.db')
    
    # Comparison table
    comparison_data = []
    for college in colleges_to_compare:
        college_info = pd.read_sql_query(
            "SELECT * FROM colleges WHERE college_name = ? LIMIT 1",
            conn, params=(college,)
        )
        
        nirf = pd.read_sql_query(
            "SELECT ranking FROM nirf_rankings WHERE college_name = ? AND year = 2024",
            conn, params=(college,)
        )
        
        placements = pd.read_sql_query(
            "SELECT AVG(avg_package) as avg_pkg, AVG(placement_percentage) as placement FROM placements WHERE college_name = ? AND year = 2024",
            conn, params=(college,)
        )
        
        comparison_data.append({
            "College": college,
            "Location": college_info.iloc[0]['location'] if not college_info.empty else "N/A",
            "Type": college_info.iloc[0]['college_type'] if not college_info.empty else "N/A",
            "Programs": len(pd.read_sql_query("SELECT DISTINCT program FROM colleges WHERE college_name = ?", conn, params=(college,))),
            "NIRF Rank": nirf.iloc[0]['ranking'] if not nirf.empty else "N/A",
            "Avg Package (LPA)": round(placements.iloc[0]['avg_pkg'], 2) if not placements.empty and placements.iloc[0]['avg_pkg'] else "N/A",
            "Placement %": round(placements.iloc[0]['placement'], 2) if not placements.empty and placements.iloc[0]['placement'] else "N/A"
        })
    
    comp_df = pd.DataFrame(comparison_data)
    st.dataframe(comp_df, use_container_width=True)
    
    # Cutoff comparison
    st.subheader("Cutoff Comparison")
    cutoffs_comparison = []
    for college in colleges_to_compare:
        cutoffs = pd.read_sql_query(
            "SELECT program, general, obc, sc, st FROM colleges WHERE college_name = ?",
            conn, params=(college,)
        )
        cutoffs['college'] = college
        cutoffs_comparison.append(cutoffs)
    
    all_cutoffs = pd.concat(cutoffs_comparison, ignore_index=True)
    
    fig = px.bar(all_cutoffs, x='program', y=['general', 'obc', 'sc', 'st'],
                 color='college', barmode='group',
                 title="Cutoff Comparison by Program",
                 height=500)
    st.plotly_chart(fig, use_container_width=True)
    
    conn.close()

# ==================== TAB 4: PLACEMENTS ====================
with tab4:
    st.subheader("💼 Placement Statistics")
    
    colleges = get_colleges_for_comparison()
    selected_colleges = st.multiselect("Select Colleges:", colleges, default=colleges[:5])
    
    if selected_colleges:
        conn = sqlite3.connect('college_data_advanced.db')
        
        placements_data = pd.read_sql_query(f'''
            SELECT college_name, program, avg_package, placement_percentage, companies_count
            FROM placements
            WHERE college_name IN ({','.join(['?' for _ in selected_colleges])})
            AND year = 2024
        ''', conn, params=selected_colleges)
        
        conn.close()
        
        if not placements_data.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.bar(placements_data.groupby('college_name')['avg_package'].mean().reset_index(),
                            x='college_name', y='avg_package',
                            title="Average Package by College",
                            labels={'college_name': 'College', 'avg_package': 'Avg Package (LPA)'})
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.bar(placements_data.groupby('college_name')['placement_percentage'].mean().reset_index(),
                            x='college_name', y='placement_percentage',
                            title="Placement Percentage",
                            labels={'college_name': 'College', 'placement_percentage': 'Placement %'})
                st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(placements_data, use_container_width=True)

# ==================== TAB 5: ELIGIBILITY CHECKER ====================
with tab5:
    st.subheader("✅ Check Your Eligibility")
    
    col1, col2 = st.columns(2)
    
    with col1:
        user_score = st.number_input("Your CET Percentile:", min_value=0.0, max_value=100.0)
        user_category = st.selectbox("Your Category:", ["General", "OBC", "SC", "ST"])
    
    with col2:
        colleges = get_colleges_for_comparison()
        selected_college = st.selectbox("Select College:", colleges)
        
        conn = sqlite3.connect('college_data_advanced.db')
        programs = pd.read_sql_query(
            "SELECT DISTINCT program FROM colleges WHERE college_name = ?",
            conn, params=(selected_college,)
        )['program'].tolist()
        conn.close()
        
        selected_program = st.selectbox("Select Program:", programs)
    
    if st.button("Check Eligibility"):
        result = predict_eligibility(user_score, user_category, selected_college, selected_program)
        
        if result:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Your Score", f"{result['your_score']:.2f}")
            with col2:
                st.metric("College Cutoff", f"{result['college_cutoff']:.2f}")
            with col3:
                st.metric("Difference", f"{result['difference']:+.2f}")
            with col4:
                st.metric("Confidence", f"{result['confidence']}%")
            
            st.success(result['eligibility'], icon="✅" if result['round'] else "❌")
            
            if result['round']:
                st.info(f"Expected in **Counseling Round {result['round']}**")

# ==================== TAB 6: COUNSELING PREDICTOR ====================
with tab6:
    st.subheader("🎯 Counseling Round Predictor")
    
    col1, col2 = st.columns(2)
    
    with col1:
        pred_score = st.slider("Your Percentile:", 0.0, 100.0, 75.0)
        pred_category = st.radio("Category:", ["General", "OBC", "SC", "ST"], horizontal=True)
    
    with col2:
        colleges = get_colleges_for_comparison()
        pred_colleges = st.multiselect("Select Top 5 Colleges:", colleges, max_selections=5)
    
    if pred_colleges:
        predictions = []
        
        for college in pred_colleges:
            conn = sqlite3.connect('college_data_advanced.db')
            programs = pd.read_sql_query(
                "SELECT DISTINCT program FROM colleges WHERE college_name = ?",
                conn, params=(college,)
            )['program'].tolist()
            conn.close()
            
            top_program = programs[0]  # Top program
            
            result = predict_eligibility(pred_score, pred_category, college, top_program)
            
            if result:
                predictions.append({
                    "College": college,
                    "Program": top_program,
                    "Status": result['eligibility'],
                    "Round": result['round'] if result['round'] else "-",
                    "Confidence": f"{result['confidence']}%"
                })
        
        pred_df = pd.DataFrame(predictions)
        st.dataframe(pred_df, use_container_width=True)
        
        # Visualization
        round_counts = pd.Series([p['Round'] for p in predictions if p['Round'] != "-"]).value_counts()
        
        if not round_counts.empty:
            fig = px.pie(values=round_counts.values, names=[f"Round {int(x)}" for x in round_counts.index],
                         title="Expected Counseling Rounds Distribution")
            st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("🎓 Advanced College Recommendation System | Built with Streamlit")
