from flask import Blueprint, request, jsonify, Response
from datetime import datetime
import pandas as pd
import joblib   
import sys
import os
import io
import json
import redis

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'../../..','src')))
from db_config import get_database_client
from app.api.auth import token_required

api_bp = Blueprint('api',__name__)
current_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(current_dir, '..', '..', 'models', 'best_model.pkl')
meta_path = os.path.join(current_dir, '..', '..', 'models', 'model_metadata.json')

# Redis setup
try:
    redis_host = os.getenv('REDIS_HOST', 'localhost')
    redis_client = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True, socket_timeout=1, socket_connect_timeout=1)
except Exception:
    redis_client = None

def get_cached(key):
    return None

def set_cached(key, data):
    pass

try:
    model = joblib.load(model_path)
    db = get_database_client()
    collection = db['fused_outbreak_data']
    predictions_col = db['saved_predictions']
    with open(meta_path, 'r') as f:
        meta = json.load(f)
except Exception as e:
    model = None
    db = None
    meta = {}
    print(f"Startup Error: {e}")

@api_bp.route('/predict',methods=['POST'])
@token_required
def predict_outbreak():
    try:
        req_data = request.get_json()
        target_region = req_data.get('region')
        target_week = req_data.get('week')
        target_disease = req_data.get('disease', 'Dengue') # Default to Dengue if not provided
        
        if not target_region or not target_week:
            return jsonify({'status':'error','message':'Region and week are required.'}), 400
        
        record = collection.find_one(
            {'Region': target_region, 'Week_Num': int(target_week), 'Disease_Name': target_disease},
            sort=[('Year', -1)]
        )
        
        if not record:
            return jsonify({'status':'error','message':'No data found for this period and disease.'}), 404
            
        # Build features array exactly as the model expects
        feature_cols = meta.get("features", [])
        features_dict = {col: 0.0 for col in feature_cols}
        
        # Populate continuous features
        features_dict['Avg_Temperature_2m'] = float(record.get('Avg_Temperature_2m', 0))
        features_dict['Avg_Relative_Humidity_2m'] = float(record.get('Avg_Relative_Humidity_2m', 0))
        features_dict['Search_Trend_Score'] = float(record.get('Search_Trend_Score', 0))
        features_dict['Rainfall'] = float(record.get('Rainfall', 0))
        features_dict['Cases_Last_Week'] = float(record.get('Cases_Last_Week', 0))
        features_dict['Rainfall_Lag_1'] = float(record.get('Rainfall_Lag_1', 0))
        features_dict['Temp_Humidity_Index'] = float(record.get('Temp_Humidity_Index', 0))
        features_dict['Population_Density'] = float(record.get('Population_Density', 0))
        features_dict['Hospital_Beds_Per_1000'] = float(record.get('Hospital_Beds_Per_1000', 0))
        
        # Populate one-hot categorical features
        if f"Region_{target_region}" in features_dict:
            features_dict[f"Region_{target_region}"] = 1.0
        if f"Disease_Name_{target_disease}" in features_dict:
            features_dict[f"Disease_Name_{target_disease}"] = 1.0
            
        features_df = pd.DataFrame([features_dict])[feature_cols] # Ensure strict column ordering
        
        prediction_val = model.predict(features_df)[0]
        risk_map = {0: 'LOW', 1: 'MEDIUM', 2: 'HIGH'}
        prediction = risk_map.get(prediction_val, 'UNKNOWN')
        
        max_prob = round(max(model.predict_proba(features_df)[0]) * 100, 1) 
        active_model_name = meta.get("active_model", "Multi-Disease Forecaster")
        
        result_data = {
            'region': target_region,
            'week': int(target_week),
            'disease': target_disease,
            'risk': prediction, # Note: this is now a FORECAST for t+1
            'probability': max_prob,
            'activeModel': active_model_name,
            'temperature': round(record.get('Avg_Temperature_2m', 0), 1),
            'humidity': round(record.get('Avg_Relative_Humidity_2m', 0), 1),
            'searchTrend': record.get('Search_Trend_Score', 0),
            'dataYear': record.get('Year', 2024),
            'forecastWeek': (int(target_week) % 52) + 1,
            'timestamp': datetime.utcnow()
        }
        
        predictions_col.insert_one(result_data.copy())
        
        if '_id' in result_data: 
            del result_data['_id']
            
        return jsonify({'status':'success','data':result_data}), 200
        
    except Exception as e:
        print(f"PREDICT ERROR: {str(e)}") 
        return jsonify({'status':'failed','error':str(e)}), 500

@api_bp.route('/historical/<region>',methods=['GET'])
@token_required
def get_historical(region):
    disease = request.args.get('disease', 'Dengue')
    cache_key = f"hist_{region}_{disease}"
    
    cached = get_cached(cache_key)
    if cached:
        return jsonify({"status": "success", "data": json.loads(cached)}), 200
        
    try:
        records=list(collection.find({'Region':region, 'Disease_Name': disease},{'_id':0}).sort([('Year',1),('Week_Num',1)]))
        set_cached(cache_key, json.dumps(records))
        return jsonify({"status":"success","data":records}),200
    except Exception as e:
        return jsonify({"status":"failed","error":str(e)}), 500
    
@api_bp.route('/export/<region>',methods=['GET'])
def export_csv(region):
    disease = request.args.get('disease', 'Dengue')
    try:
        records = list(collection.find({"Region":region, "Disease_Name": disease},{'_id':0}))
        if not records:
            return jsonify({"status":"failed","message":"No data found"}), 404
        df = pd.DataFrame(records)
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer,index=False)
        return Response(
            csv_buffer.getvalue(),
            mimetype="text/csv",
            headers={"Content-disposition":f"attachment; filename=outbreak_data_{disease}_{region}.csv"}
        )
    except Exception as e:
        return jsonify({"status":"failed","error":str(e)}),500

@api_bp.route('/heatmap-data', methods=['GET'])
def get_heatmap_data():
    disease = request.args.get('disease', 'Dengue')
    try:
        coords = {
            'Maharashtra': [19.75, 75.71],
            'West Bengal': [22.98, 87.85],
            'Tripura': [23.94, 91.98],
            'Gujarat': [22.25, 71.19],
            'Karnataka': [12.97, 77.59]
        }
        
        heatmap_points = []
        for region, coord in coords.items():
            record = collection.find_one(
                {'Region': region, 'Disease_Name': disease}, 
                sort=[('Year', -1), ('Week_Num', -1)]
            )
            cases = record.get('Reported_Cases', 0) if record else 0
            heatmap_points.append([coord[0], coord[1], cases])
            
        return jsonify(heatmap_points), 200
    except Exception as e:
        return jsonify({'status': 'failed', 'error': str(e)}), 500

@api_bp.route('/regional-summary', methods=['GET'])
@token_required
def get_regional_summary():
    disease = request.args.get('disease', 'Dengue')
    cache_key = f"summary_{disease}"
    
    cached = get_cached(cache_key)
    if cached:
        return jsonify({"status": "success", "data": json.loads(cached)}), 200
        
    try:
        regions = ['Maharashtra', 'West Bengal', 'Tripura', 'Gujarat', 'Karnataka']
        summary = []
        
        for region in regions:
            pipeline = [
                {"$match": {"Region": region, "Disease_Name": disease}},
                {"$group": {"_id": None, "total": {"$sum": "$Reported_Cases"}}}
            ]
            result = list(collection.aggregate(pipeline))
            total_cases = result[0]['total'] if result else 0
            
            if total_cases > 350:
                risk = "high"
            elif total_cases > 220:
                risk = "moderate"
            else:
                risk = "low"
                
            summary.append({
                "region": region,
                "total": total_cases,
                "risk": risk
            })
            
        set_cached(cache_key, json.dumps(summary))
        return jsonify({"status": "success", "data": summary}), 200
    except Exception as e:
        return jsonify({"status": "failed", "error": str(e)}), 500