import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
from sklearn.ensemble import RandomForestClassifier
import joblib

# Load dataset

data = pd.read_csv('../data/outbreak_data.csv')

# Features
X = data[[
    'temperature',
    'humidity',
    'rainfall',
    'search_trend',
    'cases'
]]

# Target
encoder = LabelEncoder()
y = encoder.fit_transform(data['risk'])

# Split dataset
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

# Train professional model
model = RandomForestClassifier(
    n_estimators=200,
    random_state=42
)
model.fit(X_train, y_train)

# Accuracy
predictions = model.predict(X_test)
accuracy = accuracy_score(y_test, predictions)

print(f'Accuracy: {accuracy}')

# Save model
joblib.dump(model, '../models/outbreak_model.pkl')

# Save encoder
joblib.dump(encoder, '../models/label_encoder.pkl')

print('Model saved successfully')