# Setting up tools
import pandas as pd
from sklearn.model_selection import train_test_split # ML Library
from sklearn.ensemble import RandomForestClassifier
import joblib #To save trained python object, Flask API will load it later
import os
from db_config import get_database_client
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
data['Reported_Cases']=pd.to_numeric(data['Reported_Cases'],errors='coerce').fillna(0)
def assign_risk(cases):
    if cases > 150: return 'High'
    if cases > 50: return 'Medium'
    return 'Low'
data['Risk_Level']=data['Reported_Cases'].apply(assign_risk)

# Splitting Inputs and Outputs
X = data[['Avg_Temperature_2m','Avg_Relative_Humidity_2m','Search_Trend_Score']] # This is Feature, Frontend will send to backend
y=data['Risk_Level'] # This is Target, answer which we want the model to predict

# Splitting the data for training and testing
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
#random_state=42 is to make sure data is shuffled the same way every time the script is run

# Training the brain
model=RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42) 
#n_estimators to define how many t]decision trees at a time
#max_depth to allow each decision tree to ask 10 y/n questions before making decision
model.fit(X_train,y_train)
#Algo. looks at input output and adjusts internal math to figure out correlations
#Testing
accuracy=model.score(X_test,y_test)
print(f"Model Training Complete. Validation Accuracy: {accuracy*100:.2f}%")
joblib.dump(model,'backend/models/baseline_model.pkl')
#This file will be loaded by Flask API to serve live predictions