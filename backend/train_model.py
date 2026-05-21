import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib
import os

# Ensure the models directory exists
os.makedirs('backend/models', exist_ok=True)

print("Loading master training data...")
data = pd.read_csv('backend/data/master_training_data.csv')

# Features (The Clues)
# Notice we DO NOT include 'Cases' or 'Risk' here!
X = data[[
    'Temperature', 
    'Humidity', 
    'Rainfall', 
    'Search_Trend'
]]

# Target (The Answer Key)
y = data['Risk']

# Split the data: 80% for studying, 20% for taking a test
X_train, X_test, y_train, y_test = train_test_split(
    X, 
    y, 
    test_size=0.2, 
    random_state=42
)

print("Training the Random Forest model...")
# Initialize and train the model
model = RandomForestClassifier(
    n_estimators=100, 
    random_state=42
)
model.fit(X_train, y_train)

# Test the model to see how well it learned
accuracy = model.score(X_test, y_test)
print(f"Model trained successfully! Validation Accuracy: {accuracy * 100:.2f}%")

# Save the trained 'brain' to a file so our API can use it later
joblib.dump(model, 'backend/models/baseline_model.pkl')
print("Model saved to backend/models/baseline_model.pkl")