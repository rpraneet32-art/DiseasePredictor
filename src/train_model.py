# Setting up tools
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split # ML Library
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib #To save trained python object, Flask API will load it later
import os
from db_config import get_database_client
import json
os.makedirs('backend/models',exist_ok=True)

# Ingesting Data
db=get_database_client()
collection=db['fused_outbreak_data']
cursor = collection.find({},{'_id':0})
data=pd.DataFrame(list(cursor))
if data.empty:
    print('Database is empty. Execute pipeline.py first.')
    exit(1)

# Creating the answer key for supervised learning
numeric_cols = [
    'Avg_Temperature_2m', 'Avg_Relative_Humidity_2m', 'Search_Trend_Score', 
    'Rainfall', 'Cases_Last_Week', 'Rainfall_Lag_1', 'Temp_Humidity_Index', 'Reported_Cases'
]
for col in numeric_cols:
    data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0)
def assign_risk(cases):
    if cases > 150: return 2
    if cases > 50: return 1
    return 0
data['Risk_Level']=data['Reported_Cases'].apply(assign_risk)

# Splitting Inputs and Outputs
X = data[['Avg_Temperature_2m', 'Avg_Relative_Humidity_2m', 'Search_Trend_Score', 'Rainfall', 'Cases_Last_Week', 'Rainfall_Lag_1', 'Temp_Humidity_Index']] # This is Feature, Frontend will send to backend
y=data['Risk_Level'] # This is Target, answer which we want the model to predict

# Splitting the data for training and testing
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
#random_state=42 is to make sure data is shuffled the same way every time the script is run

# Training the brain
rf_model = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42)
xgb_model = XGBClassifier(eval_metric='mlogloss', random_state=42)
#n_estimators to define how many t]decision trees at a time
#max_depth to allow each decision tree to ask 10 y/n questions before making decision
voting_model = VotingClassifier(estimators=[('rf', rf_model), ('xgb', xgb_model)],voting='soft')
voting_model.fit(X_train,y_train)
#Algo. looks at input output and adjusts internal math to figure out correlations
#Testing
y_pred = voting_model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Voting Ensemble Training Complete. Validation Accuracy: {accuracy*100:.2f}%")
metadata = {
    "active_model": "Voting Ensemble",
    "accuracy": round(accuracy * 100, 2)
}
# Save the model
joblib.dump(voting_model, 'backend/models/best_model.pkl')
# Save the metadata
with open("backend/models/model_metadata.json", "w") as f:
    json.dump(metadata, f)
print("\nModel and metadata saved successfully to backend/models/!")
#This file will be loaded by Flask API to serve live predictions