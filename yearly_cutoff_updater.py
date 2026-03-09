"""
Yearly Cutoff Data Updater
Automatically updates cutoffs year-by-year and predicts future trends
"""

import pandas as pd
import sqlite3
import numpy as np
from datetime import datetime

class YearlyCutoffUpdater:
    
    def __init__(self, db_name='college_data_advanced.db'):
        self.db_name = db_name
        self.current_year = datetime.now().year
    
    def add_yearly_cutoff(self, year, csv_file=None, data_dict=None):
        """
        Add cutoff data for a specific year
        
        Args:
            year: Year for which data is being added
            csv_file: Path to CSV with cutoff data (College, Program, General, OBC, SC, ST)
            data_dict: Dictionary with college data
        """
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        if csv_file:
            df = pd.read_csv(csv_file)
            
            for _, row in df.iterrows():
                cursor.execute('''
                    INSERT OR REPLACE INTO historical_cutoffs 
                    (college_name, program, year, general, obc, sc, st)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row['College'],
                    row['Program'],
                    year,
                    float(row['General']),
                    float(row['OBC']),
                    float(row['SC']),
                    float(row['ST'])
                ))
            
            conn.commit()
            print(f"✓ Updated {len(df)} records for {year}")
        
        elif data_dict:
            for college, programs in data_dict.items():
                for program, cutoffs in programs.items():
                    cursor.execute('''
                        INSERT OR REPLACE INTO historical_cutoffs 
                        (college_name, program, year, general, obc, sc, st)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        college,
                        program,
                        year,
                        cutoffs['General'],
                        cutoffs['OBC'],
                        cutoffs['SC'],
                        cutoffs['ST']
                    ))
            
            conn.commit()
            print(f"✓ Updated data for {year}")
        
        conn.close()
    
    def predict_future_cutoffs(self, years_ahead=1):
        """
        Predict future cutoffs based on historical trend
        Uses linear regression on past data
        
        Args:
            years_ahead: How many years to predict
        """
        
        conn = sqlite3.connect(self.db_name)
        
        # Get all historical data
        historical = pd.read_sql_query('''
            SELECT college_name, program, year, general, obc, sc, st
            FROM historical_cutoffs
            ORDER BY college_name, program, year
        ''', conn)
        
        conn.close()
        
        predictions = []
        
        for college in historical['college_name'].unique():
            for program in historical['program'].unique():
                college_prog_data = historical[
                    (historical['college_name'] == college) & 
                    (historical['program'] == program)
                ].sort_values('year')
                
                if len(college_prog_data) >= 2:
                    # Linear trend for each category
                    for category in ['general', 'obc', 'sc', 'st']:
                        x = college_prog_data['year'].values
                        y = college_prog_data[category].values
                        
                        # Calculate trend
                        coeffs = np.polyfit(x, y, 1)  # Linear fit
                        poly = np.poly1d(coeffs)
                        
                        # Predict for next years
                        for i in range(1, years_ahead + 1):
                            future_year = self.current_year + i
                            predicted_val = max(0, poly(future_year))
                            
                            predictions.append({
                                'College': college,
                                'Program': program,
                                'Year': future_year,
                                'Category': category.capitalize(),
                                'Predicted_Cutoff': round(predicted_val, 2),
                                'Trend': 'Increasing' if coeffs[0] > 0 else 'Decreasing'
                            })
        
        pred_df = pd.DataFrame(predictions)
        return pred_df
    
    def get_cutoff_analytics(self, college_name, program):
        """Get detailed analytics for a college program"""
        
        conn = sqlite3.connect(self.db_name)
        
        history = pd.read_sql_query('''
            SELECT year, general, obc, sc, st
            FROM historical_cutoffs
            WHERE college_name = ? AND program = ?
            ORDER BY year
        ''', conn, params=(college_name, program))
        
        conn.close()
        
        if history.empty:
            return None
        
        analytics = {}
        
        for category in ['general', 'obc', 'sc', 'st']:
            values = history[category].values
            
            analytics[category.capitalize()] = {
                'Latest': values[-1],
                'Min': values.min(),
                'Max': values.max(),
                'Avg': round(values.mean(), 2),
                'Trend': 'Increasing' if values[-1] > values[0] else 'Decreasing',
                'Change': round(values[-1] - values[0], 2)
            }
        
        return analytics
    
    def export_yearly_report(self, year, output_file=None):
        """Export cutoff data for a specific year"""
        
        conn = sqlite3.connect(self.db_name)
        
        data = pd.read_sql_query('''
            SELECT college_name, program, general, obc, sc, st
            FROM historical_cutoffs
            WHERE year = ?
            ORDER BY college_name, program
        ''', conn, params=(year,))
        
        conn.close()
        
        if output_file is None:
            output_file = f"cutoffs_{year}.csv"
        
        data.to_csv(output_file, index=False)
        print(f"✓ Exported {len(data)} records to {output_file}")
        
        return data
    
    def compare_years(self, college_name, program, year1, year2):
        """Compare cutoffs between two years"""
        
        conn = sqlite3.connect(self.db_name)
        
        data_y1 = pd.read_sql_query('''
            SELECT general, obc, sc, st
            FROM historical_cutoffs
            WHERE college_name = ? AND program = ? AND year = ?
        ''', conn, params=(college_name, program, year1))
        
        data_y2 = pd.read_sql_query('''
            SELECT general, obc, sc, st
            FROM historical_cutoffs
            WHERE college_name = ? AND program = ? AND year = ?
        ''', conn, params=(college_name, program, year2))
        
        conn.close()
        
        if data_y1.empty or data_y2.empty:
            return None
        
        comparison = {}
        for category in ['general', 'obc', 'sc', 'st']:
            val1 = data_y1[category].values[0]
            val2 = data_y2[category].values[0]
            change = val2 - val1
            
            comparison[category.capitalize()] = {
                f'{year1}': round(val1, 2),
                f'{year2}': round(val2, 2),
                'Change': round(change, 2),
                'Change_%': round((change / val1 * 100) if val1 != 0 else 0, 2)
            }
        
        return comparison
    
    def get_statistics_summary(self):
        """Get overall statistics"""
        
        conn = sqlite3.connect(self.db_name)
        
        stats = {
            'Total Colleges': pd.read_sql_query(
                "SELECT COUNT(DISTINCT college_name) as count FROM historical_cutoffs", conn
            )['count'].values[0],
            
            'Total Programs': pd.read_sql_query(
                "SELECT COUNT(DISTINCT program) as count FROM historical_cutoffs", conn
            )['count'].values[0],
            
            'Years Available': pd.read_sql_query(
                "SELECT COUNT(DISTINCT year) as count FROM historical_cutoffs", conn
            )['count'].values[0],
            
            'Latest Year': pd.read_sql_query(
                "SELECT MAX(year) as max_year FROM historical_cutoffs", conn
            )['max_year'].values[0],
            
            'Earliest Year': pd.read_sql_query(
                "SELECT MIN(year) as min_year FROM historical_cutoffs", conn
            )['min_year'].values[0],
        }
        
        conn.close()
        
        return stats

# Example usage
if __name__ == "__main__":
    updater = YearlyCutoffUpdater()
    
    # Get statistics
    print("\n📊 Database Statistics:")
    stats = updater.get_statistics_summary()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Predict future cutoffs
    print("\n🔮 Predicting cutoffs for next 2 years...")
    predictions = updater.predict_future_cutoffs(years_ahead=2)
    
    if not predictions.empty:
        # Save predictions
        predictions.to_csv('predicted_cutoffs_future.csv', index=False)
        print(f"✓ Saved {len(predictions)} predictions to 'predicted_cutoffs_future.csv'")
        print("\nSample Predictions:")
        print(predictions.head(10))
    
    # Get analytics for a college
    print("\n📈 Analytics for a College Program:")
    analytics = updater.get_cutoff_analytics('DKTE', 'Computer Science Engineering')
    if analytics:
        for category, data in analytics.items():
            print(f"\n{category}:")
            for metric, value in data.items():
                print(f"  {metric}: {value}")
    
    print("\n✅ Updater ready for yearly data updates!")
