import os
import io
import time
import logging
from datetime import datetime
import requests
import pandas as pd
from pytrends.request import TrendReq
from db_config import get_database_client

# ─────────────────────────────────────────────
# LOGGING SETUP
# Writes to both console AND a persistent log file
# ─────────────────────────────────────────────
os.makedirs('logs', exist_ok=True)
log_filename = f"logs/pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# CHECKPOINT HELPERS
# Saves each fetch result as a CSV so if the
# pipeline crashes midway, it resumes from
# where it left off instead of re-fetching everything
# ─────────────────────────────────────────────
CHECKPOINT_DIR = "pipeline_checkpoints"
os.makedirs(CHECKPOINT_DIR, exist_ok=True)

def save_checkpoint(df: pd.DataFrame, name: str):
    path = os.path.join(CHECKPOINT_DIR, f"{name}.csv")
    df.to_csv(path, index=False)
    logger.info(f"✅ Checkpoint saved: {path}")

def load_checkpoint(name: str) -> pd.DataFrame:
    path = os.path.join(CHECKPOINT_DIR, f"{name}.csv")
    if os.path.exists(path):
        logger.info(f"♻️  Resuming from checkpoint: {path}")
        return pd.read_csv(path)
    return pd.DataFrame()

def clear_checkpoints():
    """Call this after a fully successful pipeline run."""
    for f in os.listdir(CHECKPOINT_DIR):
        os.remove(os.path.join(CHECKPOINT_DIR, f))
    logger.info("🧹 Checkpoints cleared after successful run.")

# ─────────────────────────────────────────────
# RETRY DECORATOR
# Wraps any API call: retries up to max_retries
# times with exponential backoff before giving up
# ─────────────────────────────────────────────
def with_retry(func, *args, max_retries=3, base_delay=10, **kwargs):
    for attempt in range(1, max_retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            wait = base_delay * (2 ** (attempt - 1))  # 10s, 20s, 40s
            logger.warning(f"⚠️  Attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                logger.info(f"⏳ Retrying in {wait}s...")
                time.sleep(wait)
            else:
                logger.error(f"❌ All {max_retries} attempts failed for {func.__name__}.")
                raise


# ─────────────────────────────────────────────
# DATA VALIDATION
# Checks the final merged dataset before it
# ever touches the database
# ─────────────────────────────────────────────
REQUIRED_COLUMNS = [
    'Year', 'Week_Num', 'Region',
    'Search_Trend_Score',
    'Avg_Temperature_2m',
    'Avg_Relative_Humidity_2m',
    'Reported_Cases'
]

def validate_dataset(df: pd.DataFrame) -> bool:
    logger.info("🔍 Running data validation checks...")

    # Check 1: Not empty
    if df.empty:
        logger.error("Validation FAILED: Dataset is empty.")
        return False

    # Check 2: All required columns present
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        logger.error(f"Validation FAILED: Missing columns: {missing_cols}")
        return False

    # Check 3: No fully null rows
    null_rows = df[REQUIRED_COLUMNS].isnull().all(axis=1).sum()
    if null_rows > 0:
        logger.warning(f"Validation WARNING: {null_rows} completely null rows found. Dropping them.")
        df.dropna(subset=REQUIRED_COLUMNS, how='all', inplace=True)

    # Check 4: Numeric columns are actually numeric
    numeric_cols = ['Search_Trend_Score', 'Avg_Temperature_2m', 'Avg_Relative_Humidity_2m', 'Reported_Cases']
    for col in numeric_cols:
        non_numeric = pd.to_numeric(df[col], errors='coerce').isna().sum()
        if non_numeric > 0:
            logger.warning(f"Validation WARNING: {non_numeric} non-numeric values in '{col}'. Coercing to 0.")
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Check 5: Year and Week_Num are in sane ranges
    invalid_years = df[(df['Year'] < 2000) | (df['Year'] > 2030)]
    if not invalid_years.empty:
        logger.warning(f"Validation WARNING: {len(invalid_years)} rows with suspicious Year values. Dropping.")
        df.drop(invalid_years.index, inplace=True)

    invalid_weeks = df[(df['Week_Num'] < 1) | (df['Week_Num'] > 53)]
    if not invalid_weeks.empty:
        logger.warning(f"Validation WARNING: {len(invalid_weeks)} rows with invalid Week_Num. Dropping.")
        df.drop(invalid_weeks.index, inplace=True)

    # Check 6: Minimum viable row count
    if len(df) < 10:
        logger.error(f"Validation FAILED: Only {len(df)} rows after cleaning. Too few to train on.")
        return False

    logger.info(f"✅ Validation passed. {len(df)} clean rows ready for DB load.")
    return True


# ─────────────────────────────────────────────
# EXTRACT FUNCTIONS (with retry + checkpointing)
# ─────────────────────────────────────────────

def _fetch_trends_for_state(pytrends, keywords, timeframe_window, geo_code, state_name):
    """Inner function — isolated so retry wrapper can target just this call."""
    pytrends.build_payload(keywords, cat=0, timeframe=timeframe_window, geo=geo_code)
    chunk_df = pytrends.interest_over_time()
    return chunk_df


def fetch_historical_google_trends_looped(keywords, start_year=2016, end_year=2020, geo_map=None):
    logger.info(f"🌐 [1/3 Extract] Contacting Google Trends API for {start_year}–{end_year}...")

    # Resume from checkpoint if available
    cached = load_checkpoint("trends_weekly")
    if not cached.empty:
        return cached

    pytrends = TrendReq(hl='en-US', tz=330, timeout=(10, 25))
    timeframe_window = f"{start_year}-01-01 {end_year}-12-31"
    all_combined_records = []

    for i, (geo_code, state_name) in enumerate(geo_map.items()):
        logger.info(f"📍 Fetching trends for: {state_name} ({geo_code})")
        try:
            chunk_df = with_retry(
                _fetch_trends_for_state,
                pytrends, keywords, timeframe_window, geo_code, state_name,
                max_retries=3, base_delay=15
            )
            if not chunk_df.empty:
                chunk_df = chunk_df.reset_index().rename(
                    columns={'date': 'Date', keywords[0]: 'Search_Trend_Score'}
                )
                chunk_df['Year'] = chunk_df['Date'].dt.isocalendar().year.astype(int)
                chunk_df['Week_Num'] = chunk_df['Date'].dt.isocalendar().week.astype(int)
                chunk_df['Region'] = state_name
                all_combined_records.append(chunk_df[['Year', 'Week_Num', 'Region', 'Search_Trend_Score']])
                logger.info(f"   ✅ {state_name}: {len(chunk_df)} weeks fetched.")
            else:
                logger.warning(f"   ⚠️  {state_name}: Empty response from Trends API.")

            if i < len(geo_map) - 1:
                logger.info("⏳ Sleeping 15s to avoid Google rate limits...")
                time.sleep(15)

        except Exception as e:
            logger.error(f"❌ Permanently skipping {state_name} after retries: {e}")
            continue

    if not all_combined_records:
        return pd.DataFrame()

    result = pd.concat(all_combined_records, ignore_index=True).drop_duplicates(
        subset=['Year', 'Week_Num', 'Region']
    )
    save_checkpoint(result, "trends_weekly")
    return result


def fetch_multi_region_weather(geo_map, start_year=2016, end_year=2020):
    logger.info("🌦️ [2/3 Extract] Contacting Open-Meteo Archive API...")

    cached = load_checkpoint("weather_weekly")
    if not cached.empty:
        return cached

    coordinates = {
        'Maharashtra': {'lat': 19.75, 'lon': 75.71},
        'Karnataka':  {'lat': 12.97, 'lon': 77.59},
        'Kerala':     {'lat': 10.85, 'lon': 76.27}
    }
    endpoint = "https://archive-api.open-meteo.com/v1/archive"
    all_weather_records = []

    for state_name in geo_map.values():
        if state_name not in coordinates:
            logger.warning(f"⚠️  No coordinates defined for {state_name}. Skipping.")
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
            def _fetch():
                r = requests.get(endpoint, params=params, timeout=15)
                r.raise_for_status()
                return r.json()

            data_json = with_retry(_fetch, max_retries=3, base_delay=5)
            daily_data = data_json["daily"]

            state_weather_df = pd.DataFrame({
                "Date": pd.to_datetime(daily_data["time"]),
                "Avg_Temperature_2m": daily_data["temperature_2m_mean"],
                "Avg_Relative_Humidity_2m": daily_data["relative_humidity_2m_mean"]
            })
            state_weather_df['Year'] = state_weather_df['Date'].dt.isocalendar().year.astype(int)
            state_weather_df['Week_Num'] = state_weather_df['Date'].dt.isocalendar().week.astype(int)
            state_weather_df['Region'] = state_name

            weekly_grouped = state_weather_df.groupby(['Year', 'Week_Num', 'Region']).agg({
                'Avg_Temperature_2m': 'mean',
                'Avg_Relative_Humidity_2m': 'mean'
            }).reset_index()

            all_weather_records.append(weekly_grouped)
            logger.info(f"   ✅ {state_name}: {len(weekly_grouped)} weekly weather records fetched.")
            time.sleep(1)

        except Exception as e:
            logger.error(f"❌ Permanently skipping weather for {state_name} after retries: {e}")
            continue

    if not all_weather_records:
        return pd.DataFrame()

    result = pd.concat(all_weather_records, ignore_index=True)
    save_checkpoint(result, "weather_weekly")
    return result


def fetch_epiclim_hospital_records():
    logger.info("🏥 [3/3 Extract] Downloading EpiClim dataset from Zenodo...")

    cached = load_checkpoint("epiclim_raw")
    if not cached.empty:
        return cached

    zenodo_url = "https://zenodo.org/records/14580510/files/Final_data.csv?download=1"

    def _fetch():
        r = requests.get(zenodo_url, timeout=30)
        r.raise_for_status()
        return r.text

    try:
        csv_text = with_retry(_fetch, max_retries=3, base_delay=5)
        result = pd.read_csv(io.StringIO(csv_text))
        logger.info(f"   ✅ EpiClim: {len(result)} raw records downloaded.")
        save_checkpoint(result, "epiclim_raw")
        return result
    except Exception as e:
        logger.error(f"❌ EpiClim download failed after all retries: {e}")
        return pd.DataFrame()


# ─────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────

def run_etl_pipeline():
    logger.info("🚀 Starting Hardened ETL Pipeline...")
    pipeline_start = datetime.now()

    regions_map = {
        'IN-MH': 'Maharashtra',
        'IN-KA': 'Karnataka',
        'IN-KL': 'Kerala'
    }
    START_YEAR = 2016
    END_YEAR = 2020

    # ── 1. EXTRACT ────────────────────────────
    trends_weekly = fetch_historical_google_trends_looped(
        ['dengue symptoms'], start_year=START_YEAR, end_year=END_YEAR, geo_map=regions_map
    )
    weather_weekly = fetch_multi_region_weather(geo_map=regions_map, start_year=START_YEAR, end_year=END_YEAR)
    cases_raw = fetch_epiclim_hospital_records()

    if trends_weekly.empty or weather_weekly.empty or cases_raw.empty:
        logger.error("❌ Pipeline aborted: One or more data sources returned empty. Check logs above.")
        return

    # ── 2. TRANSFORM ──────────────────────────
    logger.info("🔄 Transforming and cleaning data...")
    cases_raw.rename(columns={
        'state_ut': 'Region',
        'Disease': 'Disease_Name',
        'Cases': 'Reported_Cases'
    }, inplace=True)

    target_states = list(regions_map.values())
    cases_filtered = cases_raw[
        (cases_raw['Disease_Name'].str.strip().str.title() == 'Dengue') &
        (cases_raw['Region'].str.strip().str.title().isin(target_states))
    ].copy()

    if cases_filtered.empty:
        logger.error("❌ No Dengue records found for target states after filtering. Aborting.")
        return

    cases_filtered['Week_Num'] = (
        cases_filtered['week_of_outbreak'].str.extract(r'(\d+)')
        .astype(float).fillna(1).astype(int)
    )
    cases_filtered.rename(columns={'year': 'Year'}, inplace=True)
    cases_weekly = (
        cases_filtered.groupby(['Year', 'Week_Num', 'Region'])['Reported_Cases']
        .sum().reset_index()
    )

    # ── 3. FUSION MERGE ───────────────────────
    logger.info("🧩 Merging all data sources...")
    fused_features = pd.merge(trends_weekly, weather_weekly, on=['Year', 'Week_Num', 'Region'], how='inner')
    final_dataset = pd.merge(fused_features, cases_weekly, on=['Year', 'Week_Num', 'Region'], how='inner')
    final_dataset.sort_values(by=['Region', 'Year', 'Week_Num'], inplace=True)

    logger.info(f"📐 Merge result: {len(final_dataset)} rows across {final_dataset['Region'].nunique()} regions.")

    # ── 4. VALIDATE ───────────────────────────
    if not validate_dataset(final_dataset):
        logger.error("❌ Pipeline aborted: Data validation failed. Nothing written to DB.")
        return

    # ── 5. LOAD ───────────────────────────────
    logger.info("💾 Loading data into MongoDB...")
    try:
        db = get_database_client()
        collection = db['fused_outbreak_data']
        collection.delete_many({})

        payload = final_dataset.to_dict(orient='records')
        collection.insert_many(payload)

        duration = (datetime.now() - pipeline_start).seconds
        logger.info(f"🎉 Pipeline complete in {duration}s.")
        logger.info(f"   📊 [fused_outbreak_data] → {len(payload)} rows loaded.")

        # Clear checkpoints only after confirmed success
        clear_checkpoints()

    except Exception as e:
        logger.error(f"❌ Database load failed: {e}")
        logger.info("💡 Checkpoints preserved — re-run pipeline to retry DB load without re-fetching.")


if __name__ == "__main__":
    run_etl_pipeline()