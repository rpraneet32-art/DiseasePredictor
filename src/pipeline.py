import os
import io
import time
import numpy as np
import requests
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from pytrends.request import TrendReq

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report
)

from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import (
    RandomForestClassifier,
    GradientBoostingClassifier,
    VotingClassifier
)

from sklearn.svm import SVC

from xgboost import XGBClassifier

from db_config import get_database_client


# ==========================================================
# GOOGLE TRENDS
# ==========================================================

def fetch_historical_google_trends_looped(
    keywords,
    start_year=2016,
    end_year=2020,
    geo_map=None
):

    pytrends = TrendReq(
        hl='en-US',
        tz=330,
        timeout=(10, 25)
    )

    timeframe_window = (
        f"{start_year}-01-01 "
        f"{end_year}-12-31"
    )

    all_combined_records = []

    for i, (geo_code, state_name) in enumerate(
        geo_map.items()
    ):

        try:

            pytrends.build_payload(
                keywords,
                cat=0,
                timeframe=timeframe_window,
                geo=geo_code
            )

            chunk_df = pytrends.interest_over_time()

            if not chunk_df.empty:

                chunk_df = chunk_df.reset_index().rename(
                    columns={
                        'date': 'Date',
                        keywords[0]:
                            'Search_Trend_Score'
                    }
                )

                chunk_df['Year'] = (
                    chunk_df['Date']
                    .dt.isocalendar()
                    .year
                    .astype(int)
                )

                chunk_df['Week_Num'] = (
                    chunk_df['Date']
                    .dt.isocalendar()
                    .week
                    .astype(int)
                )

                chunk_df['Region'] = state_name

                all_combined_records.append(
                    chunk_df[
                        [
                            'Year',
                            'Week_Num',
                            'Region',
                            'Search_Trend_Score'
                        ]
                    ]
                )

            if i < len(geo_map) - 1:
                time.sleep(10)

        except Exception as e:
            print(f"Trend Error: {e}")

    return pd.concat(
        all_combined_records,
        ignore_index=True
    )


# ==========================================================
# WEATHER DATA
# ==========================================================

def fetch_multi_region_weather(
    geo_map,
    start_year=2016,
    end_year=2020
):

    coordinates = {
        'Maharashtra': {'lat': 19.75, 'lon': 75.71},
        'Karnataka': {'lat': 12.97, 'lon': 77.59},
        'Kerala': {'lat': 10.85, 'lon': 76.27}
    }

    endpoint = (
        "https://archive-api.open-meteo.com/v1/archive"
    )

    all_weather_records = []

    for state_name in geo_map.values():

        loc = coordinates[state_name]

        params = {

            "latitude": loc['lat'],
            "longitude": loc['lon'],

            "start_date":
                f"{start_year}-01-01",

            "end_date":
                f"{end_year}-12-31",

            "daily": [
                "temperature_2m_mean",
                "relative_humidity_2m_mean",
                "precipitation_sum"
            ],

            "timezone": "Asia/Kolkata"
        }

        response = requests.get(
            endpoint,
            params=params
        )

        daily_data = response.json()["daily"]

        state_weather_df = pd.DataFrame({

            "Date":
                pd.to_datetime(daily_data["time"]),

            "Avg_Temperature_2m":
                daily_data["temperature_2m_mean"],

            "Avg_Relative_Humidity_2m":
                daily_data[
                    "relative_humidity_2m_mean"
                ],

            "Rainfall":
                daily_data["precipitation_sum"]
        })

        state_weather_df['Year'] = (
            state_weather_df['Date']
            .dt.isocalendar()
            .year
            .astype(int)
        )

        state_weather_df['Week_Num'] = (
            state_weather_df['Date']
            .dt.isocalendar()
            .week
            .astype(int)
        )

        state_weather_df['Region'] = state_name

        weekly_grouped = (

            state_weather_df

            .groupby(
                ['Year', 'Week_Num', 'Region']
            )

            .agg({
                'Avg_Temperature_2m': 'mean',
                'Avg_Relative_Humidity_2m': 'mean',
                'Rainfall': 'sum'
            })

            .reset_index()
        )

        all_weather_records.append(
            weekly_grouped
        )

    return pd.concat(
        all_weather_records,
        ignore_index=True
    )


# ==========================================================
# EPI DATA
# ==========================================================

def fetch_epiclim_hospital_records():

    zenodo_url = (
        "https://zenodo.org/records/14580510/"
        "files/Final_data.csv?download=1"
    )

    response = requests.get(zenodo_url)

    return pd.read_csv(
        io.StringIO(response.text)
    )


# ==========================================================
# MAIN PIPELINE
# ==========================================================

def run_pipeline():

    regions_map = {
        'IN-MH': 'Maharashtra',
        'IN-KA': 'Karnataka',
        'IN-KL': 'Kerala'
    }

    START_YEAR = 2016
    END_YEAR = 2020

    # ======================================================
    # EXTRACT
    # ======================================================

    trends_weekly = (
        fetch_historical_google_trends_looped(
            ['dengue symptoms'],
            start_year=START_YEAR,
            end_year=END_YEAR,
            geo_map=regions_map
        )
    )

    weather_weekly = (
        fetch_multi_region_weather(
            geo_map=regions_map,
            start_year=START_YEAR,
            end_year=END_YEAR
        )
    )

    cases_raw = (
        fetch_epiclim_hospital_records()
    )

    # ======================================================
    # CLEAN
    # ======================================================

    cases_raw.rename(
        columns={
            'state_ut': 'Region',
            'Disease': 'Disease_Name',
            'Cases': 'Reported_Cases'
        },
        inplace=True
    )

    target_states = list(
        regions_map.values()
    )

    cases_filtered = cases_raw[
        (
            cases_raw['Disease_Name']
            .str.strip()
            .str.title() == 'Dengue'
        )
        &
        (
            cases_raw['Region']
            .str.strip()
            .str.title()
            .isin(target_states)
        )
    ].copy()

    cases_filtered['Week_Num'] = (
        cases_filtered['week_of_outbreak']
        .str.extract(r'(\d+)')
        .astype(float)
        .fillna(1)
        .astype(int)
    )

    cases_filtered.rename(
        columns={'year': 'Year'},
        inplace=True
    )
    # Convert reported cases to numeric
    cases_filtered['Reported_Cases'] = pd.to_numeric(
        cases_filtered['Reported_Cases'],
        errors='coerce'
    )

    cases_filtered.dropna(
        subset=['Reported_Cases'],
        inplace=True
    )

    # Convert to integer
    cases_filtered['Reported_Cases'] = (
        cases_filtered['Reported_Cases']
        .astype(int)
    )

    cases_weekly = (
        cases_filtered
        .groupby(
            ['Year', 'Week_Num', 'Region']
        )['Reported_Cases']
        .sum()
        .reset_index()
    )

    # ======================================================
    # MERGE
    # ======================================================

    fused_features = pd.merge(
        trends_weekly,
        weather_weekly,
        on=['Year', 'Week_Num', 'Region'],
        how='inner'
    )

    final_dataset = pd.merge(
        fused_features,
        cases_weekly,
        on=['Year', 'Week_Num', 'Region'],
        how='inner'
    )

    final_dataset.sort_values(
        by=['Region', 'Year', 'Week_Num'],
        inplace=True
    )

    # ======================================================
    # FEATURE ENGINEERING
    # ======================================================

    final_dataset['Cases_Last_Week'] = (
        final_dataset
        .groupby('Region')['Reported_Cases']
        .shift(1)
    )

    final_dataset['Cases_2_Weeks_Back'] = (
        final_dataset
        .groupby('Region')['Reported_Cases']
        .shift(2)
    )

    final_dataset['Trend_Last_Week'] = (
        final_dataset
        .groupby('Region')
        ['Search_Trend_Score']
        .shift(1)
    )

    final_dataset['Rainfall_Lag_1'] = (
        final_dataset
        .groupby('Region')['Rainfall']
        .shift(1)
    )

    final_dataset['Cases_MA_3'] = (
        final_dataset
        .groupby('Region')
        ['Reported_Cases']
        .rolling(3)
        .mean()
        .reset_index(0, drop=True)
    )

    final_dataset['Trend_MA_3'] = (
        final_dataset
        .groupby('Region')
        ['Search_Trend_Score']
        .rolling(3)
        .mean()
        .reset_index(0, drop=True)
    )

    final_dataset['Temp_Humidity_Index'] = (
        final_dataset['Avg_Temperature_2m']
        *
        final_dataset[
            'Avg_Relative_Humidity_2m'
        ]
    )

    final_dataset['Week_Sin'] = np.sin(
        2 * np.pi *
        final_dataset['Week_Num'] / 52
    )

    final_dataset['Week_Cos'] = np.cos(
        2 * np.pi *
        final_dataset['Week_Num'] / 52
    )

    final_dataset['Month'] = (
        final_dataset['Week_Num'] / 4
    ).astype(int)

    final_dataset['Is_Monsoon'] = (
        final_dataset['Month']
        .isin([6, 7, 8, 9])
        .astype(int)
    )

    # ======================================================
    # TARGET LABEL
    # ======================================================

    # Ensure numeric dtype again
    final_dataset['Reported_Cases'] = pd.to_numeric(
        final_dataset['Reported_Cases'],
        errors='coerce'
    )

    outbreak_threshold = (
        final_dataset['Reported_Cases']
        .median()
    )

    final_dataset['Outbreak'] = (
        final_dataset['Reported_Cases']
        > outbreak_threshold
    ).astype(int)

    # ======================================================
    # DROP MISSING
    # ======================================================

    final_dataset.dropna(inplace=True)

    # ======================================================
    # CORRELATION ANALYSIS
    # ======================================================

    correlation_df = final_dataset.select_dtypes(
        include=np.number
    )

    correlation_matrix = correlation_df.corr()

    print("\nCorrelation Matrix:\n")
    print(correlation_matrix)

    plt.figure(figsize=(14, 10))

    sns.heatmap(
        correlation_matrix,
        annot=True,
        cmap='coolwarm'
    )

    plt.title(
        "Feature Correlation Heatmap"
    )

    plt.show()

    # ======================================================
    # ML FEATURES
    # ======================================================

    feature_columns = [

        'Search_Trend_Score',
        'Avg_Temperature_2m',
        'Avg_Relative_Humidity_2m',
        'Rainfall',
        'Cases_Last_Week',
        'Cases_2_Weeks_Back',
        'Trend_Last_Week',
        'Rainfall_Lag_1',
        'Cases_MA_3',
        'Trend_MA_3',
        'Temp_Humidity_Index',
        'Week_Sin',
        'Week_Cos',
        'Is_Monsoon'
    ]

    X = final_dataset[feature_columns]

    y = final_dataset['Outbreak']

    X_train, X_test, y_train, y_test = (
        train_test_split(
            X,
            y,
            test_size=0.2,
            random_state=42
        )
    )

    # ======================================================
    # MODELS
    # ======================================================

    models = {

        "Logistic Regression":
            LogisticRegression(max_iter=1000),

        "Decision Tree":
            DecisionTreeClassifier(),

        "Random Forest":
            RandomForestClassifier(),

        "Gradient Boosting":
            GradientBoostingClassifier(),

        "SVM":
            SVC(),

        "XGBoost":
            XGBClassifier(
                eval_metric='logloss'
            )
    }

    # ======================================================
    # TRAIN + EVALUATE
    # ======================================================

    results = []

    for name, model in models.items():

        print(f"\n====================")
        print(f"{name}")
        print(f"====================")

        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)

        accuracy = accuracy_score(
            y_test,
            y_pred
        )

        precision = precision_score(
            y_test,
            y_pred
        )

        recall = recall_score(
            y_test,
            y_pred
        )

        f1 = f1_score(
            y_test,
            y_pred
        )

        print(
            classification_report(
                y_test,
                y_pred
            )
        )

        results.append({
            'Model': name,
            'Accuracy': accuracy,
            'Precision': precision,
            'Recall': recall,
            'F1 Score': f1
        })

    # ======================================================
    # ENSEMBLE MODEL
    # ======================================================

    voting_model = VotingClassifier(

        estimators=[

            (
                'rf',
                RandomForestClassifier()
            ),

            (
                'gb',
                GradientBoostingClassifier()
            ),

            (
                'xgb',
                XGBClassifier(
                    eval_metric='logloss'
                )
            )
        ],

        voting='hard'
    )

    voting_model.fit(X_train, y_train)

    voting_pred = voting_model.predict(
        X_test
    )

    voting_f1 = f1_score(
        y_test,
        voting_pred
    )

    results.append({

        'Model': 'Voting Ensemble',

        'Accuracy':
            accuracy_score(
                y_test,
                voting_pred
            ),

        'Precision':
            precision_score(
                y_test,
                voting_pred
            ),

        'Recall':
            recall_score(
                y_test,
                voting_pred
            ),

        'F1 Score':
            voting_f1
    })

    # ======================================================
    # FINAL RESULTS
    # ======================================================

    results_df = pd.DataFrame(results)

    print("\nFINAL MODEL COMPARISON\n")

    print(
        results_df.sort_values(
            by='F1 Score',
            ascending=False
        )
    )

    # ======================================================
    # SAVE TO DATABASE
    # ======================================================

    db = get_database_client()

    collection = db['fused_outbreak_data']

    collection.delete_many({})

    payload = final_dataset.to_dict(
        orient='records'
    )

    collection.insert_many(payload)

    print("\nDataset saved successfully.")


if __name__ == "__main__":

    run_pipeline()