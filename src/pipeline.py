import os
import io
import time
from datetime import datetime
import requests
import pandas as pd
from pytrends.request import TrendReq
from db_config import get_database_client 

def fetch_historical_google_trends_looped(keywords, start_year=2015, end_year=2025, geo_map=None):
    """
    Bypasses Google's 5-year weekly data limit by looping through time in 3-year chunks
    and iterating across multiple geographic regions.
    """
    print(f"🌐 [1/3 Extract] Initiating rolling-chunk Google Trends extraction from {start_year} to {end_year}...")
    pytrends = TrendReq(hl='en-US', tz=330, timeout=(10, 25))
    
    # Break down the timeline into safe 3-year windows to guarantee weekly resolution
    time_chunks = []
    for yr in range(start_year, end_year + 1, 3):
        chunk_end = min(yr + 2, end_year)
        time_chunks.append(f"{yr}-01-01 {chunk_end}-12-31")
    
    all_combined_records = []

    # Loop through each state region
    for geo_code, state_name in geo_map.items():
        print(f"📍 Fetching trends for region: {state_name} ({geo_code})")
        
        # Loop through each time chunk for this specific state
        for chunk in time_chunks:
            print(f"   ⏱️ Pulling weekly chunk window: {chunk}")
            try:
                pytrends.build_payload(keywords, cat=0, timeframe=chunk, geo=geo_code)
                chunk_df = pytrends.interest_over_time()
                
                if not chunk_df.empty:
                    chunk_df = chunk_df.reset_index().rename(columns={'date': 'Date', keywords[0]: 'Search_Trend_Score'})
                    chunk_df['Year'] = chunk_df['Date'].dt.isocalendar().year.astype(int)
                    chunk_df['Week_Num'] = chunk_df['Date'].dt.isocalendar().week.astype(int)
                    chunk_df['Region'] = state_name
                    
                    all_combined_records.append(chunk_df[['Year', 'Week_Num', 'Region', 'Search_Trend_Score']])
                
                # Anti-blocking mechanism: sleep to prevent Google from hitting us with a 429 error
                time.sleep(4)
                
            except Exception as e:
                print(f"   ⚠️ Rate limit or connection hiccup for {state_name} during chunk {chunk}: {e}")
                time.sleep(10) # Sleep longer if an error occurs to let the IP cool down
                continue

    if not all_combined_records:
        return pd.DataFrame()
        
    return pd.concat(all_combined_records, ignore_index=True).drop_duplicates(subset=['Year', 'Week_Num', 'Region'])


def fetch_multi_region_weather(geo_map, start_year=2015, end_year=2025):
    """Coordinates batch weather requests across multiple regional coordinates."""
    print("🌦️ [2/3 Extract] Contacting Open-Meteo Archive API endpoint for regional climates...")
    
    # Representative coordinates for regional capital/center areas
    coordinates = {
        'Maharashtra': {'lat': 19.75, 'lon': 75.71},
        'Delhi': {'lat': 28.61, 'lon': 77.20},
        'Karnataka': {'lat': 12.97, 'lon': 77.59},
        'Tamil Nadu': {'lat': 13.08, 'lon': 80.27}
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
            "daily": ["temperature_2m_mean", "relative_humidity_2m_mean"],
            "timezone": "Asia/Kolkata"
        }
        
        try:
            response = requests.get(endpoint, params=params, timeout=15)
            response.raise_for_status()
            daily_data = response.json()["daily"]
            
            state_weather_df = pd.DataFrame({
                "Date": pd.to_datetime(daily_data["time"]),
                "Avg_Temperature_2m": daily_data["temperature_2m_mean"],
                "Avg_Relative_Humidity_2m": daily_data["relative_humidity_2m_mean"]
            })
            
            state_weather_df['Year'] = state_weather_df['Date'].dt.isocalendar().year.astype(int)
            state_weather_df['Week_Num'] = state_weather_df['Date'].dt.isocalendar().week.astype(int)
            state_weather_df['Region'] = state_name
            
            # Aggregate down to weekly increments
            weekly_grouped = state_weather_df.groupby(['Year', 'Week_Num', 'Region']).agg({
                'Avg_Temperature_2m': 'mean',
                'Avg_Relative_Humidity_2m': 'mean'
            }).reset_index()
            
            all_weather_records.append(weekly_grouped)
            time.sleep(1) # Graceful request spacing
            
        except Exception as e:
            print(f"   ⚠️ Could not pull weather metrics for {state_name}: {e}")
            
    if not all_weather_records:
        return pd.DataFrame()
    return pd.concat(all_weather_records, ignore_index=True)


def fetch_epiclim_hospital_records():
    """Streams the complete historical EpiClim database directly into memory."""
    print("🏥 [3/3 Extract] Downloading global EpiClim open database package...")
    zenodo_download_url = "https://zenodo.org/records/14580510/files/EpiClim_Dataset.csv?download=1"
    try:
        response = requests.get(zenodo_download_url, timeout=30)
        response.raise_for_status()
        return pd.read_csv(io.StringIO(response.text))
    except Exception as e:
        print(f"❌ Failed to extract EpiClim registry baseline: {e}")
        return pd.DataFrame()


def run_etl_pipeline():
    print("🚀 Initializing Dynamic Multi-Year / Multi-Region Outbreak Pipeline...")

    # 1. Map out our cross-regional spatial framework
    regions_map = {
        'IN-MH': 'Maharashtra',
        'IN-DL': 'Delhi',
        'IN-KA': 'Karnataka',
        'IN-TN': 'Tamil Nadu'
    }
    
    START_YEAR = 2016
    CURRENT_YEAR = datetime.now().year  # 2026

    # 2. Extract Phase
    trends_weekly = fetch_historical_google_trends_looped(['dengue symptoms'], start_year=START_YEAR, end_year=CURRENT_YEAR, geo_map=regions_map)
    weather_weekly = fetch_multi_region_weather(geo_map=regions_map, start_year=START_YEAR, end_year=CURRENT_YEAR)
    cases_raw = fetch_epiclim_hospital_records()
    
    if trends_weekly.empty or weather_weekly.empty or cases_raw.empty:
        print("❌ Pipeline aborted: One or more data extraction layers returned empty dataframes.")
        return

    # 3. Transform Phase (Completely dropped hardcoded state and year constraints!)
    print("🔄 Cleaning and intersecting metrics across all available targets...")
    
    cases_raw.rename(columns={'state_ut': 'Region', 'Disease': 'Disease_Name', 'Cases': 'Reported_Cases'}, inplace=True)
    
    # Filter only by structural target variables (Dengue, and regions present in our mapping)
    target_states = list(regions_map.values())
    cases_filtered = cases_raw[
        (cases_raw['Disease_Name'].str.strip().str.title() == 'Dengue') &
        (cases_raw['Region'].str.strip().str.title().isin(target_states))
    ].copy()

    cases_filtered['Week_Num'] = cases_filtered['week_of_outbreak'].str.extract(r'(\d+)').astype(float).fillna(1).astype(int)
    cases_filtered.rename(columns={'year': 'Year'}, inplace=True)

    # Group metrics into unified weekly state totals across all years
    cases_weekly = cases_filtered.groupby(['Year', 'Week_Num', 'Region'])['Reported_Cases'].sum().reset_index()

    # 4. Data Fusion Intersection
    print("🧩 Executing multi-source timeline alignment matrix...")
    fused_features = pd.merge(trends_weekly, weather_weekly, on=['Year', 'Week_Num', 'Region'], how='inner')
    
    # The inner join handles mismatched timelines perfectly. 
    # If hospital entries stop at 2024 but weather reaches 2026, it safely drops 2025/2026 rows without losing historical data.
    final_dataset = pd.merge(fused_features, cases_weekly, on=['Year', 'Week_Num', 'Region'], how='inner')
    final_dataset.sort_values(by=['Region', 'Year', 'Week_Num'], inplace=True, ascending=True)

    # 5. Load Phase
    print(f"💾 Ingesting massive consolidated matrix into MongoDB...")
    payload = final_dataset.to_dict(orient='records')

    db = get_database_client()
    collection = db['fused_outbreak_data']

    collection.delete_many({})

    if payload:
        collection.insert_many(payload)
        print(f"🎉 Success! Ingested {len(payload)} total multi-regional dataset records into MongoDB.")
    else:
        print("⚠️ Warning: Data join resulted in zero overlapping data points.")

if __name__ == "__main__":
    run_etl_pipeline()