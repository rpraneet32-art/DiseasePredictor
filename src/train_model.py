# Setting up tools
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib 
import os
from db_config import get_database_client
import json

os.makedirs('backend/models', exist_ok=True)

# Ingesting Data
db = get_database_client()
collection = db['fused_outbreak_data']
cursor = collection.find({}, {'_id': 0})
data = pd.DataFrame(list(cursor))

if data.empty:
    print('Database is empty. Execute pipeline.py first.')
    exit(1)

# Ensure numeric columns
numeric_cols = [
    'Avg_Temperature_2m', 'Avg_Relative_Humidity_2m', 'Search_Trend_Score', 
    'Rainfall', 'Cases_Last_Week', 'Rainfall_Lag_1', 'Temp_Humidity_Index', 
    'Reported_Cases', 'Population_Density', 'Hospital_Beds_Per_1000'
]
for col in numeric_cols:
    if col in data.columns:
        data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0)

# Creating the answer key for supervised learning (t+1 Forecasting)
def assign_risk(cases):
    if cases > 150: return 2 # High
    if cases > 50: return 1  # Medium
    return 0                 # Low

data['Risk_Level_Current'] = data['Reported_Cases'].apply(assign_risk)

# Shift target to predict NEXT week
data.sort_values(by=['Disease_Name', 'Region', 'Year', 'Week_Num'], inplace=True)
data['Target_Risk_Next_Week'] = data.groupby(['Disease_Name', 'Region'])['Risk_Level_Current'].shift(-1)

# Drop rows where we don't have next week's data (the last week of each region/disease)
data.dropna(subset=['Target_Risk_Next_Week'], inplace=True)

# Encoding Categorical Variables
# We use one-hot encoding for Region and Disease_Name
data_encoded = pd.get_dummies(data, columns=['Region', 'Disease_Name'], drop_first=False)

# Define Features
feature_cols = [
    'Avg_Temperature_2m', 'Avg_Relative_Humidity_2m', 'Search_Trend_Score', 
    'Rainfall', 'Cases_Last_Week', 'Rainfall_Lag_1', 'Temp_Humidity_Index',
    'Population_Density', 'Hospital_Beds_Per_1000'
]
# Add the one-hot encoded columns to features
for col in data_encoded.columns:
    if col.startswith('Region_') or col.startswith('Disease_Name_'):
        feature_cols.append(col)

X = data_encoded[feature_cols]
y = data_encoded['Target_Risk_Next_Week'].astype(int)

# Splitting Data (Time-Based to prevent leakage)
train_mask = data_encoded['Year'] <= 2019
test_mask = data_encoded['Year'] > 2019

X_train, X_test = X[train_mask], X[test_mask]
y_train, y_test = y[train_mask], y[test_mask]

if len(X_train) == 0 or len(X_test) == 0:
    print("Not enough data to split by year (<=2019 train, >2019 test). Defaulting to random split.")
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print(f"Training on {len(X_train)} samples, testing on {len(X_test)} samples.")

# Training the brain
rf_model = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42)
xgb_model = XGBClassifier(eval_metric='mlogloss', random_state=42)

voting_model = VotingClassifier(estimators=[('rf', rf_model), ('xgb', xgb_model)], voting='soft')
voting_model.fit(X_train, y_train)

# Testing
y_pred = voting_model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Forecasting Model Training Complete. Validation Accuracy (on future data): {accuracy*100:.2f}%")

# Save model and metadata
metadata = {
    "active_model": "Multi-Disease Forecaster",
    "accuracy": round(accuracy * 100, 2),
    "features": feature_cols
}

joblib.dump(voting_model, 'backend/models/best_model.pkl')
with open("backend/models/model_metadata.json", "w") as f:
    json.dump(metadata, f)
print("\nModel and metadata saved successfully to backend/models/!")