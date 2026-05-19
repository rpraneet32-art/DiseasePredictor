from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import numpy as np

app = Flask(__name__)
CORS(app)

# Load trained model
model = joblib.load('models/outbreak_model.pkl')
encoder = joblib.load('models/label_encoder.pkl')

@app.route('/')
def home():
    return jsonify({
        'message': 'Disease Outbreak Prediction API Running'
    })

@app.route('/predict', methods=['POST'])
def predict():
     try:
        data = request.get_json()

        temperature = data['temperature']
        humidity = data['humidity']
        rainfall = data['rainfall']
        search_trend = data['search_trend']
        cases = data['cases']

        input_data = np.array([[
            temperature,
            humidity,
            rainfall,
            search_trend,
            cases
        ]])

        prediction = model.predict(input_data)

        risk = encoder.inverse_transform(prediction)

        return jsonify({
            'predicted_risk': risk[0],
            'status': 'success'
        })
     except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'failed'
        })

if __name__ == '__main__':
    app.run(debug=True)