import os
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime as dt
from yearly_cutoff_updater import YearlyCutoffUpdater

# Initialize updater
updater = YearlyCutoffUpdater()

# Set page config
st.set_page_config(page_title="College Recommendation - Year-wise Updates", layout="wide")

st.title("🎓 College Recommendation System - Yearly Updates")
st.markdown("---")

# Create tabs
tabs = st.tabs([
    "Dashboard",
    "Yearly Updates",
    "Predictions",
    "Analytics",
    "Compare Years",
    "Reports"
])

# ==================== TAB 1: DASHBOARD ====================
with tabs[0]:
    st.subheader("📊 Database Summary")
    
    stats = updater.get_statistics_summary()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("🏫 Colleges", stats['Total Colleges'])
    with col2:
        st.metric("📚 Programs", stats['Total Programs'])
    with col3:
        st.metric("📅 Years", stats['Years Available'])
    with col4:
        st.metric("📈 Latest", int(stats['Latest Year']))
    with col5:
        st.metric("📉 Earliest", int(stats['Earliest Year']))
    
    st.markdown("---")
    
    # Cutoff distribution
    conn = sqlite3.connect('college_data_advanced.db')
    
    latest_year = stats['Latest Year']
    cutoffs = pd.read_sql_query(f'''
        SELECT general, obc, sc, st FROM historical_cutoffs WHERE year = {int(latest_year)}
    ''', conn)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.box(cutoffs, y=['general', 'obc', 'sc', 'st'],
                     title=f"Cutoff Distribution - {int(latest_year)}",
                     labels={'value': 'Percentile', 'variable': 'Category'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Colleges with highest cutoffs
        top_cutoffs = pd.read_sql_query(f'''
            SELECT college_name, general FROM historical_cutoffs 
            WHERE year = {int(latest_year)}
            GROUP BY college_name
            ORDER BY general DESC
            LIMIT 10
        ''', conn)
        
        fig = px.bar(top_cutoffs, y='college_name', x='general', orientation='h',
                    title=f"Top 10 Colleges by General Cutoff - {int(latest_year)}")
        st.plotly_chart(fig, use_container_width=True)
    
    conn.close()

# ==================== TAB 2: YEARLY UPDATES ====================
with tabs[1]:
    st.subheader("📝 Add/Update Yearly Cutoff Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        year_to_add = st.number_input("Year:", min_value=2020, max_value=2030, value=2026)
    
    with col2:
        update_method = st.radio("Add Data Via:", ["CSV Upload", "Manual Entry"])
    
    if update_method == "CSV Upload":
        st.info("CSV should have columns: College, Program, General, OBC, SC, ST")
        
        uploaded_file = st.file_uploader("Upload CSV", type=['csv'])
        
        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)
            
            st.write("Preview:")
            st.dataframe(df.head())
            
            if st.button("✅ Confirm and Upload"):
                try:
                    conn = sqlite3.connect('college_data_advanced.db')
                    cursor = conn.cursor()
                    
                    for _, row in df.iterrows():
                        cursor.execute('''
                            INSERT OR REPLACE INTO historical_cutoffs 
                            (college_name, program, year, general, obc, sc, st)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            row['College'],
                            row['Program'],
                            year_to_add,
                            float(row['General']),
                            float(row['OBC']),
                            float(row['SC']),
                            float(row['ST'])
                        ))
                    
                    conn.commit()
                    conn.close()
                    
                    st.success(f"✓ Updated {len(df)} records for {year_to_add}")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    elif update_method == "Manual Entry":
        st.info("Add cutoff data for a single college program")
        
        col1, col2 = st.columns(2)
        
        with col1:
            college_name = st.text_input("College Name:")
            program = st.text_input("Program:")
        
        with col2:
            col_a, col_b = st.columns(2)
            with col_a:
                general = st.number_input("General:", min_value=0.0, max_value=100.0)
            with col_b:
                obc = st.number_input("OBC:", min_value=0.0, max_value=100.0)
        
        col3, col4 = st.columns(2)
        
        with col3:
            sc = st.number_input("SC:", min_value=0.0, max_value=100.0)
        with col4:
            st = st.number_input("ST:", min_value=0.0, max_value=100.0)
        
        if st.button("➕ Add Entry"):
            try:
                conn = sqlite3.connect('college_data_advanced.db')
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO historical_cutoffs 
                    (college_name, program, year, general, obc, sc, st)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (college_name, program, year_to_add, general, obc, sc, st))
                
                conn.commit()
                conn.close()
                
                st.success(f"✓ Added {college_name} - {program} for {year_to_add}")
            except Exception as e:
                st.error(f"Error: {e}")

# ==================== TAB 3: PREDICTIONS ====================
with tabs[2]:
    st.subheader("🔮 Future Cutoff Predictions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        years_ahead = st.slider("Predict for next X years:", 1, 5, 2)
    
    with col2:
        show_sample = st.number_input("Show top N predictions:", 5, 100, 10)
    
    if st.button("Generate Predictions"):
        predictions = updater.predict_future_cutoffs(years_ahead=years_ahead)
        
        if not predictions.empty:
            st.success(f"Generated {len(predictions)} predictions")
            
            # Show by year
            st.subheader("Predictions by Year")
            
            for year in sorted(predictions['Year'].unique()):
                st.write(f"### {year}")
                
                year_data = predictions[predictions['Year'] == year].head(show_sample)
                st.dataframe(year_data, use_container_width=True)
            
            # Visualization
            st.subheader("Trend Visualization")
            
            sample_colleges = predictions['College'].unique()[:5]
            
            for college in sample_colleges:
                college_pred = predictions[predictions['College'] == college]
                
                fig = px.line(college_pred, x='Year', y='Predicted_Cutoff', color='Category',
                             title=f"Predicted Cutoffs - {college}",
                             markers=True)
                st.plotly_chart(fig, use_container_width=True)
            
            # Download predictions
            csv = predictions.to_csv(index=False)
            st.download_button(
                label="📥 Download All Predictions",
                data=csv,
                file_name=f"predictions_{years_ahead}_years.csv",
                mime="text/csv"
            )

# ==================== TAB 4: ANALYTICS ====================
with tabs[3]:
    st.subheader("📈 Cutoff Trends & Analytics")
    
    conn = sqlite3.connect('college_data_advanced.db')
    colleges = pd.read_sql_query(
        "SELECT DISTINCT college_name FROM historical_cutoffs ORDER BY college_name",
        conn
    )['college_name'].tolist()
    conn.close()
    
    selected_college = st.selectbox("Select College:", colleges)
    
    conn = sqlite3.connect('college_data_advanced.db')
    programs = pd.read_sql_query(
        "SELECT DISTINCT program FROM historical_cutoffs WHERE college_name = ?",
        conn, params=(selected_college,)
    )['program'].tolist()
    conn.close()
    
    selected_program = st.selectbox("Select Program:", programs)
    
    if selected_college and selected_program:
        analytics = updater.get_cutoff_analytics(selected_college, selected_program)
        
        if analytics:
            # Analytics cards
            col1, col2 = st.columns(2)
            
            for idx, (category, data) in enumerate(analytics.items()):
                with col1 if idx % 2 == 0 else col2:
                    st.write(f"### {category}")
                    st.metric("Latest", data['Latest'])
                    st.metric("Average", data['Avg'])
                    st.metric("Trend", data['Trend'])
                    st.metric("Change (5-yr)", f"{data['Change']:+.2f}")
            
            # Trend chart
            conn = sqlite3.connect('college_data_advanced.db')
            history = pd.read_sql_query('''
                SELECT year, general, obc, sc, st
                FROM historical_cutoffs
                WHERE college_name = ? AND program = ?
                ORDER BY year
            ''', conn, params=(selected_college, selected_program))
            conn.close()
            
            if not history.empty:
                fig = go.Figure()
                
                for col in ['general', 'obc', 'sc', 'st']:
                    fig.add_trace(go.Scatter(
                        x=history['year'],
                        y=history[col],
                        name=col.capitalize(),
                        mode='lines+markers'
                    ))
                
                fig.update_layout(
                    title=f"Cutoff Trends - {selected_college} ({selected_program})",
                    xaxis_title="Year",
                    yaxis_title="Percentile",
                    hovermode='x unified',
                    height=500
                )
                st.plotly_chart(fig, use_container_width=True)

# ==================== TAB 5: COMPARE YEARS ====================
with tabs[4]:
    st.subheader("📊 Compare Cutoffs Across Years")
    
    conn = sqlite3.connect('college_data_advanced.db')
    colleges = pd.read_sql_query(
        "SELECT DISTINCT college_name FROM historical_cutoffs ORDER BY college_name",
        conn
    )['college_name'].tolist()
    
    years = sorted(pd.read_sql_query(
        "SELECT DISTINCT year FROM historical_cutoffs ORDER BY year",
        conn
    )['year'].tolist())
    conn.close()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        college = st.selectbox("College:", colleges, key="comp_college")
    with col2:
        year1 = st.selectbox("Year 1:", years, key="comp_year1")
    with col3:
        year2 = st.selectbox("Year 2:", years, key="comp_year2", index=len(years)-1 if len(years) > 1 else 0)
    
    conn = sqlite3.connect('college_data_advanced.db')
    programs = pd.read_sql_query(
        "SELECT DISTINCT program FROM historical_cutoffs WHERE college_name = ?",
        conn, params=(college,)
    )['program'].tolist()
    conn.close()
    
    program = st.selectbox("Program:", programs)
    
    if st.button("Compare"):
        comparison = updater.compare_years(college, program, int(year1), int(year2))
        
        if comparison:
            comp_df = pd.DataFrame(comparison).T
            st.dataframe(comp_df, use_container_width=True)
            
            # Visualization
            categories = list(comparison.keys())
            year1_vals = [comparison[cat][f'{int(year1)}'] for cat in categories]
            year2_vals = [comparison[cat][f'{int(year2)}'] for cat in categories]
            
            fig = go.Figure(data=[
                go.Bar(name=f'{int(year1)}', x=categories, y=year1_vals),
                go.Bar(name=f'{int(year2)}', x=categories, y=year2_vals)
            ])
            
            fig.update_layout(
                title=f"{college} - {program}",
                barmode='group',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

# ==================== TAB 6: REPORTS ====================
with tabs[5]:
    st.subheader("📄 Generate & Export Reports")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        report_year = st.selectbox("Select Year:", 
                                   sorted(pd.read_sql_query(
                                       "SELECT DISTINCT year FROM historical_cutoffs ORDER BY year",
                                       sqlite3.connect('college_data_advanced.db')
                                   )['year'].tolist()))
    
    with col2:
        report_type = st.radio("Report Type:", ["Full Database", "College Specific", "District Specific"])
    
    with col3:
        if st.button("📥 Generate Report"):
            conn = sqlite3.connect('college_data_advanced.db')
            
            if report_type == "Full Database":
                data = updater.export_yearly_report(int(report_year))
                st.success(f"Generated report for {report_year} ({len(data)} records)")
                
                csv = data.to_csv(index=False)
                st.download_button(
                    "Download CSV",
                    csv,
                    f"cutoffs_{int(report_year)}_full.csv",
                    "text/csv"
                )
            
            st.dataframe(data.head(20), use_container_width=True)
            
            conn.close()
    
    st.markdown("---")
    st.write("### 📊 Quick Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        conn = sqlite3.connect('college_data_advanced.db')
        total = len(pd.read_sql_query(
            f"SELECT * FROM historical_cutoffs WHERE year = {int(report_year)}",
            conn
        ))
        conn.close()
        st.metric("Records", total)
    
    with col2:
        conn = sqlite3.connect('college_data_advanced.db')
        colleges_count = pd.read_sql_query(
            f"SELECT COUNT(DISTINCT college_name) FROM historical_cutoffs WHERE year = {int(report_year)}",
            conn
        ).iloc[0, 0]
        conn.close()
        st.metric("Colleges", colleges_count)
    
    with col3:
        conn = sqlite3.connect('college_data_advanced.db')
        programs_count = pd.read_sql_query(
            f"SELECT COUNT(DISTINCT program) FROM historical_cutoffs WHERE year = {int(report_year)}",
            conn
        ).iloc[0, 0]
        conn.close()
        st.metric("Programs", programs_count)

# Footer
st.markdown("---")
st.markdown("🎓 Year-wise College Recommendation System | Tracks cutoff trends & makes predictions")
