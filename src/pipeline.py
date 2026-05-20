import os
import pandas as pd
from db_config import get_database_client 

def run_etl_pipeline():
    print("🚀 Starting the Custom Weekly Outbreak Fusion Pipeline...")

    # ==========================================
    # 1. EXTRACT
    # ==========================================
    try:
        trends_df = pd.read_csv('data/raw/google_trends.csv', skiprows=2)
        # Kept the 'on_bad_lines' patch to avoid line 43854 crashing
        weather_df = pd.read_csv('data/raw/weather_data.csv', skiprows=3, on_bad_lines='skip')
        cases_df = pd.read_csv('data/raw/hospital_cases.csv')
        print("📥 Raw datasets successfully loaded into memory.")
    except FileNotFoundError as e:
        print(f"❌ Extraction failed. Check data/raw/ directory. Error: {e}")
        return

    # ==========================================
    # 2. TRANSFORM & ALIGNMENT
    # ==========================================
    print("🔄 Processing and cleaning datasets...")

    # --- Step A: Clean and Filter Hospital Data ---
    # 1. Rename core columns safely
    cases_df.rename(columns={'state_ut': 'Region', 'Disease': 'Disease_Name', 'Cases': 'Reported_Cases'}, inplace=True)
    
    # 2. Slice and isolate target space (Maharashtra + Dengue + Years 2021/2022)
    cases_df = cases_df[
        (cases_df['Region'].str.strip().str.title() == 'Maharashtra') & 
        (cases_df['Disease_Name'].str.strip().str.title() == 'Dengue') &
        (cases_df['year'].isin([2021, 2022]))
    ].copy()

    # 📍 FIX: Extract week number from string (e.g., '6th week' -> 6) instead of using file-date math
    cases_df['Week_Num'] = cases_df['week_of_outbreak'].str.extract(r'(\d+)').astype(float).fillna(1).astype(int)
    cases_df.rename(columns={'year': 'Year'}, inplace=True)

    # 5. Group by Year and Week Number to sum up all district metrics into a state total
    cases_weekly = cases_df.groupby(['Year', 'Week_Num', 'Region'])['Reported_Cases'].sum().reset_index()
    print(f"📌 Hospital records aligned. Weekly data points for Maharashtra: {len(cases_weekly)}")


    # --- Step B: Clean and Aggregate Weather Data ---
    if 'time' in weather_df.columns:
        weather_df.rename(columns={'time': 'Date'}, inplace=True)
        
    # Strip hourly timestamps, parse to datetime, and isolate 2021-2022
    weather_df['Date'] = pd.to_datetime(weather_df['Date'].str.split('T').str[0])
    weather_df = weather_df[weather_df['Date'].dt.year.isin([2021, 2022])].copy()
    
    # Extract structural time anchors
    weather_df['Year'] = weather_df['Date'].dt.isocalendar().year.astype(int)
    weather_df['Week_Num'] = weather_df['Date'].dt.isocalendar().week.astype(int)
    weather_df['Region'] = 'Maharashtra'

    # Dynamically find columns for temp and humidity to compute averages
    temp_col = [c for c in weather_df.columns if 'temperature' in c.lower()][0]
    humid_col = [c for c in weather_df.columns if 'humidity' in c.lower()][0]

    # Group daily records into weekly averages
    weather_weekly = weather_df.groupby(['Year', 'Week_Num', 'Region']).agg({
        temp_col: 'mean',
        humid_col: 'mean'
    }).reset_index()
    
    # Clean up column spaces for database delivery
    weather_weekly.rename(columns={temp_col: 'Avg_Temperature_2m', humid_col: 'Avg_Relative_Humidity_2m'}, inplace=True)


    # --- Step C: Clean Google Trends Data ---
    if 'Week' in trends_df.columns:
        trends_df.rename(columns={'Week': 'Date'}, inplace=True)
    
    trend_val_col = [c for c in trends_df.columns if 'dengue symptoms' in c.lower()][0]
    trends_df.rename(columns={trend_val_col: 'Search_Trend_Score'}, inplace=True)
    
    trends_df['Date'] = pd.to_datetime(trends_df['Date'])
    trends_df = trends_df[trends_df['Date'].dt.year.isin([2021, 2022])].copy()
    
    trends_df['Year'] = trends_df['Date'].dt.isocalendar().year.astype(int)
    trends_df['Week_Num'] = trends_df['Date'].dt.isocalendar().week.astype(int)
    trends_df['Region'] = 'Maharashtra'
    
    trends_weekly = trends_df[['Year', 'Week_Num', 'Region', 'Search_Trend_Score']].copy()


    # ==========================================
    # 3. DATA FUSION MERGE
    # ==========================================
    print("🧩 Fusing structural weekly intersections...")
    
    # Merge Trends data matrix with computed Climate parameters
    fused_features = pd.merge(trends_weekly, weather_weekly, on=['Year', 'Week_Num', 'Region'], how='inner')
    
    # Merge with Target Hospital Matrix
    final_dataset = pd.merge(fused_features, cases_weekly, on=['Year', 'Week_Num', 'Region'], how='inner')

    # Sort sequentially by timeline for ML sequence tracking
    final_dataset.sort_values(by=['Year', 'Week_Num'], inplace=True, ascending=True)


    # ==========================================
    # 4. LOAD
    # ==========================================
    print("💾 Syncing clean collection matrix to MongoDB...")
    
    payload = final_dataset.to_dict(orient='records')

    db = get_database_client()
    collection = db['fused_outbreak_data']

    # Flush old structural formats
    collection.delete_many({})

    if payload:
        collection.insert_many(payload)
        print(f"🎉 Success! Ingested {len(payload)} perfectly cleaned weekly training entries into MongoDB.")
    else:
        print("⚠️ Pipeline warning: The joined dataset is empty.")
        print("Checking data overlaps:")
        print(f" - Trends weeks available: {list(trends_weekly['Week_Num'].unique()[:5])} for Year {list(trends_weekly['Year'].unique()[:1])}")
        print(f" - Cases weeks available: {list(cases_weekly['Week_Num'].unique()[:5])} for Year {list(cases_weekly['Year'].unique()[:1])}")

if __name__ == "__main__":
    run_etl_pipeline()