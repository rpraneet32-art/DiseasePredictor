import os
import io
import time
import numpy as np
import requests
import pandas as pd
from pytrends.request import TrendReq
from db_config import get_database_client 

def fetch_historical_google_trends_looped(keywords, start_year=2016, end_year=2020, geo_map=None):
    print(f"🌐 [1/3 Extract] Contacting Google Trends API for years {start_year} to {end_year}...")
    pytrends = TrendReq(hl='en-US', tz=330, timeout=(10, 25))
    timeframe_window = f"{start_year}-01-01 {end_year}-12-31"
    all_combined_records = []

    for i, (geo_code, state_name) in enumerate(geo_map.items()):
        print(f"📍 Fetching real trends for region: {state_name} ({geo_code})")
        try:
            pytrends.build_payload(keywords, cat=0, timeframe=timeframe_window, geo=geo_code)
            chunk_df = pytrends.interest_over_time()
            if not chunk_df.empty:
                chunk_df = chunk_df.reset_index().rename(columns={'date': 'Date', keywords[0]: 'Search_Trend_Score'})
                chunk_df['Year'] = chunk_df['Date'].dt.isocalendar().year.astype(int)
                chunk_df['Week_Num'] = chunk_df['Date'].dt.isocalendar().week.astype(int)
                chunk_df['Region'] = state_name
                all_combined_records.append(chunk_df[['Year', 'Week_Num', 'Region', 'Search_Trend_Score']])
            if i < len(geo_map) - 1:
                time.sleep(15)
        except Exception as e:
            print(f"   ❌ Error or rate limit hit for {state_name}: {e}")
            continue

    if not all_combined_records:
        return pd.DataFrame()
    return pd.concat(all_combined_records, ignore_index=True).drop_duplicates(subset=['Year', 'Week_Num', 'Region'])

def fetch_multi_region_weather(geo_map, start_year=2016, end_year=2020):
    print("🌦️ [2/3 Extract] Contacting Open-Meteo Archive API endpoint...")
    coordinates = {
        'Maharashtra': {'lat': 19.75, 'lon': 75.71},
        'Karnataka': {'lat': 12.97, 'lon': 77.59},
        'Kerala': {'lat': 10.85, 'lon': 76.27}
    }
    endpoint = "https://archive-api.open-meteo.com/v1/archive"
    all_weather_records = []
    
    for state_name in geo_map.values():
        if state_name not in coordinates:
            continue
        loc = coordinates[state_name]
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
    print("🏥 [3/3 Extract] Downloading global EpiClim open database registry...")
    zenodo_url = "https://zenodo.org/records/14580510/files/Final_data.csv?download=1"
    try:
        response = requests.get(zenodo_url, timeout=30)
        response.raise_for_status()
        return pd.read_csv(io.StringIO(response.text))
    except Exception as e:
        print(f"❌ Failed to extract EpiClim registry baseline: {e}")
        return pd.DataFrame()

def run_etl_pipeline():
    print("🚀 Starting High-Volume Combined Training Data Pipeline...")
    regions_map = {
        'IN-MH': 'Maharashtra',
        'IN-KA': 'Karnataka',
        'IN-KL': 'Kerala'
    }
    START_YEAR = 2016
    END_YEAR = 2020

    trends_weekly = fetch_historical_google_trends_looped(['dengue symptoms'], start_year=START_YEAR, end_year=END_YEAR, geo_map=regions_map)
    weather_weekly = fetch_multi_region_weather(geo_map=regions_map, start_year=START_YEAR, end_year=END_YEAR)
    cases_raw = fetch_epiclim_hospital_records()
    
    if trends_weekly.empty or weather_weekly.empty or cases_raw.empty:
        print("❌ Pipeline aborted: Data extraction incomplete.")
        return

    print("🔄 Standardizing and cleaning multi-source arrays...")
    cases_raw.rename(columns={'state_ut': 'Region', 'Disease': 'Disease_Name', 'Cases': 'Reported_Cases'}, inplace=True)
    target_states = list(regions_map.values())
    cases_filtered = cases_raw[
        (cases_raw['Disease_Name'].str.strip().str.title() == 'Dengue') &
        (cases_raw['Region'].str.strip().str.title().isin(target_states))
    ].copy()

    cases_filtered['Week_Num'] = cases_filtered['week_of_outbreak'].str.extract(r'(\d+)').astype(float).fillna(1).astype(int)
    cases_filtered.rename(columns={'year': 'Year'}, inplace=True)
    cases_weekly = cases_filtered.groupby(['Year', 'Week_Num', 'Region'])['Reported_Cases'].sum().reset_index()

    print("🧩 Executing timeline matching matrix...")
    fused_features = pd.merge(trends_weekly, weather_weekly, on=['Year', 'Week_Num', 'Region'], how='inner')
    final_dataset = pd.merge(fused_features, cases_weekly, on=['Year', 'Week_Num', 'Region'], how='inner')
    final_dataset.sort_values(by=['Region', 'Year', 'Week_Num'], inplace=True, ascending=True)

    print("⚙️ Engineering Time-Lag Features...")
    final_dataset['Cases_Last_Week'] = final_dataset.groupby('Region')['Reported_Cases'].shift(1)
    final_dataset['Rainfall_Lag_1'] = final_dataset.groupby('Region')['Rainfall'].shift(1)
    final_dataset['Temp_Humidity_Index'] = final_dataset['Avg_Temperature_2m'] * final_dataset['Avg_Relative_Humidity_2m']
    final_dataset.dropna(inplace=True)

    print("💾 Syncing data straight to training repository...")
    db = get_database_client()
    collection = db['fused_outbreak_data']
    collection.delete_many({})

    if not final_dataset.empty:
        payload = final_dataset.to_dict(orient='records')
        collection.insert_many(payload)
        print(f"🎉 Success! Database completely loaded:")
        print(f"   📊 [fused_outbreak_data] -> Ingested {len(payload)} rows straight into training.")
    else:
        print("⚠️ Warning: Combined dataset matrix is empty.")

if __name__ == "__main__":
    run_etl_pipeline()