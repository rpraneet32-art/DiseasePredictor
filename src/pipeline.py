import os
import io
import time
import numpy as np
import requests
import pandas as pd
from pytrends.request import TrendReq
from pymongo import UpdateOne
from db_config import get_database_client

DISEASES = {
    'Dengue': 'dengue symptoms',
    'Malaria': 'malaria symptoms',
    'Chikungunya': 'chikungunya symptoms'
}

REGIONS_MAP = {
    'IN-MH': 'Maharashtra',
    'IN-WB': 'West Bengal',
    'IN-TR': 'Tripura',
    'IN-GJ': 'Gujarat',
    'IN-KA': 'Karnataka'
}

WEATHER_COORDS = {
    'Maharashtra': {'lat': 19.75, 'lon': 75.71},
    'West Bengal': {'lat': 22.98, 'lon': 87.85},
    'Tripura': {'lat': 23.94, 'lon': 91.98},
    'Gujarat': {'lat': 22.25, 'lon': 71.19},
    'Karnataka': {'lat': 12.97, 'lon': 77.59}
}

def fetch_historical_google_trends(disease_name, keyword, start_year, end_year):
    print(f"🌐 [Extract] Google Trends API for {disease_name}...")
    pytrends = TrendReq(hl='en-US', tz=330, timeout=(10, 25))
    timeframe_window = f"{start_year}-01-01 {end_year}-12-31"
    all_combined_records = []

    for i, (geo_code, state_name) in enumerate(REGIONS_MAP.items()):
        try:
            pytrends.build_payload([keyword], cat=0, timeframe=timeframe_window, geo=geo_code)
            chunk_df = pytrends.interest_over_time()
            if not chunk_df.empty:
                chunk_df = chunk_df.reset_index().rename(columns={'date': 'Date', keyword: 'Search_Trend_Score'})
                chunk_df['Year'] = chunk_df['Date'].dt.isocalendar().year.astype(int)
                chunk_df['Week_Num'] = chunk_df['Date'].dt.isocalendar().week.astype(int)
                chunk_df['Region'] = state_name
                chunk_df['Disease_Name'] = disease_name
                all_combined_records.append(chunk_df[['Year', 'Week_Num', 'Region', 'Disease_Name', 'Search_Trend_Score']])
            if i < len(REGIONS_MAP) - 1:
                time.sleep(15)
        except Exception as e:
            print(f"   ❌ Error or rate limit hit for {state_name}: {e}")
            continue

    if not all_combined_records:
        return pd.DataFrame()
    return pd.concat(all_combined_records, ignore_index=True).drop_duplicates(subset=['Year', 'Week_Num', 'Region', 'Disease_Name'])

def fetch_multi_region_weather(start_year, end_year):
    print("🌦️ [Extract] Contacting Open-Meteo Archive API endpoint...")
    endpoint = "https://archive-api.open-meteo.com/v1/archive"
    all_weather_records = []
    
    for state_name, loc in WEATHER_COORDS.items():
        params = {
            "latitude": loc['lat'],
            "longitude": loc['lon'],
            "start_date": f"{start_year}-01-01",
            "end_date": f"{end_year}-12-31",
            "daily": ["temperature_2m_mean", "relative_humidity_2m_mean", "precipitation_sum"],
            "timezone": "Asia/Kolkata"
        }
        try:
            response = requests.get(endpoint, params=params, timeout=15)
            response.raise_for_status()
            daily_data = response.json()["daily"]
            state_weather_df = pd.DataFrame({
                "Date": pd.to_datetime(daily_data["time"]),
                "Avg_Temperature_2m": daily_data["temperature_2m_mean"],
                "Avg_Relative_Humidity_2m": daily_data["relative_humidity_2m_mean"],
                "Rainfall": daily_data["precipitation_sum"]
            })
            state_weather_df['Year'] = state_weather_df['Date'].dt.isocalendar().year.astype(int)
            state_weather_df['Week_Num'] = state_weather_df['Date'].dt.isocalendar().week.astype(int)
            state_weather_df['Region'] = state_name
            weekly_grouped = state_weather_df.groupby(['Year', 'Week_Num', 'Region']).agg({
                'Avg_Temperature_2m': 'mean',
                'Avg_Relative_Humidity_2m': 'mean',
                'Rainfall': 'sum'
            }).reset_index()
            all_weather_records.append(weekly_grouped)
            time.sleep(1) 
        except Exception as e:
            print(f"   ⚠️ Skipping weather for {state_name}: {e}")
            continue
            
    if not all_weather_records:
        return pd.DataFrame()
    return pd.concat(all_weather_records, ignore_index=True)

def fetch_epiclim_hospital_records():
    print("🏥 [Extract] Downloading global EpiClim open database registry...")
    zenodo_url = "https://zenodo.org/records/14580510/files/Final_data.csv?download=1"
    try:
        response = requests.get(zenodo_url, timeout=30)
        response.raise_for_status()
        return pd.read_csv(io.StringIO(response.text))
    except Exception as e:
        print(f"❌ Failed to extract EpiClim registry baseline: {e}")
        return pd.DataFrame()

def run_etl_pipeline():
    print("🚀 Starting Multi-Disease High-Volume ETL Pipeline...")
    START_YEAR = 2016
    END_YEAR = 2020

    # 1. Fetch Weather
    weather_weekly = fetch_multi_region_weather(start_year=START_YEAR, end_year=END_YEAR)
    
    # 2. Fetch Hospital Records
    cases_raw = fetch_epiclim_hospital_records()
    cases_raw.rename(columns={'state_ut': 'Region', 'Disease': 'Disease_Name', 'Cases': 'Reported_Cases'}, inplace=True)
    cases_raw['Disease_Name'] = cases_raw['Disease_Name'].str.strip().str.title()
    cases_raw['Region'] = cases_raw['Region'].str.strip().str.title()
    # CRITICAL FIX: Convert strings with commas into strict integers
    cases_raw['Reported_Cases'] = pd.to_numeric(cases_raw['Reported_Cases'].astype(str).str.replace(',', ''), errors='coerce').fillna(0).astype(int)
    
    # 3. Process each disease
    all_fused_data = []
    
    for disease_name, keyword in DISEASES.items():
        print(f"\n--- Processing {disease_name} ---")
        trends_weekly = fetch_historical_google_trends(disease_name, keyword, START_YEAR, END_YEAR)
        
        if trends_weekly.empty or weather_weekly.empty or cases_raw.empty:
            print(f"❌ Data extraction incomplete for {disease_name}. Skipping.")
            continue
            
        target_states = list(REGIONS_MAP.values())
        cases_filtered = cases_raw[
            (cases_raw['Disease_Name'] == disease_name) &
            (cases_raw['Region'].isin(target_states))
        ].copy()

        cases_filtered['Week_Num'] = cases_filtered['week_of_outbreak'].str.extract(r'(\d+)').astype(float).fillna(1).astype(int)
        cases_filtered.rename(columns={'year': 'Year'}, inplace=True)
        cases_weekly = cases_filtered.groupby(['Year', 'Week_Num', 'Region', 'Disease_Name'])['Reported_Cases'].sum().reset_index()

        fused_features = pd.merge(trends_weekly, weather_weekly, on=['Year', 'Week_Num', 'Region'], how='inner')
        final_dataset = pd.merge(fused_features, cases_weekly, on=['Year', 'Week_Num', 'Region', 'Disease_Name'], how='inner')
        all_fused_data.append(final_dataset)
        
    if not all_fused_data:
        print("❌ Pipeline aborted: Combined dataset matrix is empty.")
        return
        
    combined_disease_data = pd.concat(all_fused_data, ignore_index=True)
    combined_disease_data.sort_values(by=['Disease_Name', 'Region', 'Year', 'Week_Num'], inplace=True, ascending=True)

    print("⚙️ Engineering Time-Lag Features...")
    combined_disease_data['Cases_Last_Week'] = combined_disease_data.groupby(['Disease_Name', 'Region'])['Reported_Cases'].shift(1)
    combined_disease_data['Rainfall_Lag_1'] = combined_disease_data.groupby(['Disease_Name', 'Region'])['Rainfall'].shift(1)
    combined_disease_data['Temp_Humidity_Index'] = combined_disease_data['Avg_Temperature_2m'] * combined_disease_data['Avg_Relative_Humidity_2m']
    
    print("📈 Merging Static Features (Population & Healthcare)...")
    static_features_path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'data', 'static_features.csv')
    if os.path.exists(static_features_path):
        static_df = pd.read_csv(static_features_path)
        combined_disease_data = pd.merge(combined_disease_data, static_df, on='Region', how='left')
    else:
        print("⚠️ Warning: static_features.csv not found. Continuing without static features.")

    combined_disease_data.dropna(inplace=True)

    print("💾 Syncing data straight to training repository...")
    db = get_database_client()
    collection = db['fused_outbreak_data']
    
    if not combined_disease_data.empty:
        payload = combined_disease_data.to_dict(orient='records')
        operations = []
        for record in payload:
            filter_query = {
                'Disease_Name': record['Disease_Name'],
                'Region': record['Region'],
                'Year': record['Year'],
                'Week_Num': record['Week_Num']
            }
            operations.append(UpdateOne(filter_query, {'$set': record}, upsert=True))
            
        if operations:
            result = collection.bulk_write(operations)
            print(f"🎉 Success! Database completely synchronized:")
            print(f"   📊 [fused_outbreak_data] -> Inserted: {result.upserted_count}, Modified: {result.modified_count}")
    else:
        print("⚠️ Warning: Final dataset matrix is empty after dropna.")

if __name__ == "__main__":
    run_etl_pipeline()