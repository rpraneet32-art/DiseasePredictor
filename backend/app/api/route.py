# The database, ML model and Frontend all connect here
#imports
from flask import Blueprint, request, jsonify, Response #response is used to send files(like CVs) directly to browser instead of sending JSON data
from datetime import datetime
import pandas as pd
import joblib   
import sys
import os #both sys and os used to manipulate server's file path
import io #use to create fake file in server so our RAM doesn't clutter
# Since Flask app is farther inside then the db.config it won't be able to find it normally. line below will force python to search file tree to import the database connection
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'../../..','src')))
from db_config import get_database_client
from app.api.auth import token_required

#Global State Initialization 
# We are putting this block outside of any route function
api_bp = Blueprint('api',__name__)
try:
    model=joblib.load('backend/models/baseline_model.pkl')
    # if joblib.load() was put inside /predict route, the server would have to read the .pkl file from hard drive every time user clicked the button
    # By putting it here the DB and model connect once when server starts and stays in RAM for instant access
    db = get_database_client()
    collection=db['fused_outbreak_data']
    predictions_col=db['saved_predictions']
except Exception as e:
    model=None
    db=None
    print(f"Startup Error: {e}")

#Endpoint1: The prediction engine
@api_bp.route('/predict',methods=['POST']) #Creates /api/predict endpoint 
@token_required #Protects the route if frontend dosen't send a valid JWT token
def predict_outbreak():
    try:
        req_data = request.get_json()
        target_region = req_data.get('region')
        date_str = req_data.get('date')
        target_disease = req_data.get('disease', 'Unknown') # Added this so it doesn't crash on line 42!
        
        # This extracts the exact state and date user selects in the UI
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
        
        record = collection.find_one({
            'Region': target_region,
            'Year': target_date.isocalendar().year,
            'Week_Num': target_date.isocalendar().week 
        }) # pipeline.py groups the data by Week Number 
        
        if not record:
            return jsonify({'status':'error','message':'No data found for this period.'}), 404
            
        #scikit-learn/XGBoost expects a Pandas DataFrame with exact column names, not a 2D array.
        #Force every single value to be a float so XGBoost doesn't crash on strings
        features_df = pd.DataFrame([{
            'Avg_Temperature_2m': float(record.get('Avg_Temperature_2m', 0)),
            'Avg_Relative_Humidity_2m': float(record.get('Avg_Relative_Humidity_2m', 0)),
            'Search_Trend_Score': float(record.get('Search_Trend_Score', 0)),
            'Rainfall': float(record.get('Rainfall', 0)),
            'Cases_Last_Week': float(record.get('Cases_Last_Week', 0)),
            'Rainfall_Lag_1': float(record.get('Rainfall_Lag_1', 0)),
            'Temp_Humidity_Index': float(record.get('Temp_Humidity_Index', 0))
        }])
        
        # Pass the DataFrame to the model instead of the 2D array
        prediction_val = model.predict(features_df)[0] # Returns the actual label(0, 1 or 2)
        
        risk_map = {0: 'LOW', 1: 'MEDIUM', 2: 'HIGH'}
        prediction = risk_map.get(prediction_val, 'UNKNOWN')
        
        # Pass the DataFrame here too
        max_prob = round(max(model.predict_proba(features_df)[0]) * 100, 1) 
        import json
        active_model_name = "Voting Ensemble" # Fallback default
        try:
            with open('backend/models/model_metadata.json', 'r') as f:
                meta = json.load(f)
                active_model_name = meta.get("active_model", "Voting Ensemble")
        except Exception:
            pass # Fails gracefully if the file hasn't been generated yet
        # Now packing the database and ML's prediction into a clean dictionary
        result_data = {
            'region': target_region,
            'date': date_str,
            'disease': target_disease,
            'risk': prediction,
            'probability': max_prob,
            'activeModel': active_model_name,
            'temperature': round(record.get('Avg_Temperature_2m', 0), 1),
            'humidity': round(record.get('Avg_Relative_Humidity_2m', 0), 1),
            'searchTrend': record.get('Search_Trend_Score', 0),
            'timestamp': datetime.utcnow()
        }
        
        predictions_col.insert_one(result_data.copy()) #Saves exact prediction to saved_prediction MongoDB collection
        
        if '_id' in result_data: 
            del result_data['_id'] #prevents the server from crashing 
            
        return jsonify({'status':'success','data':result_data}), 200
        
    except Exception as e:
        print(f"PREDICT ERROR: {str(e)}") # Prints exact crash reason to terminal
        return jsonify({'status':'failed','error':str(e)}), 500
#Endpoint2: Historical Timeline
#Fronted uses this to draw line chart
@api_bp.route('/historical/<region>',methods=['GET'])
@token_required
def get_historical(region):
    try:
        #find() takes arguments: (The Query:what to look for) AND (The Projection:What Columns to hide)
        records=list(collection.find({'Region':region},{'_id':0}).sort([('Year',1),('Week_Num',1)])) #1 ensures the data is in ascending order so the line chart draws perfectly
        return jsonify({"status":"success","data":records}),200
    except Exception as e:
        return jsonify({"status":"failed","error":str(e)}), 500
    
#Endpoint3: CSV export
@api_bp.route('/export/<region>',methods=['GET'])
def export_csv(region):
    try:
        records = list(collection.find({"Region":region},{'_id':0}))
        if not records:
            return jsonify({"status":"failed","message":"No data found"}), 404
        df = pd.DataFrame(records) #converts database records in dataframe
        csv_buffer = io.StringIO() #Pandas saves the data directly in string format in server's Ram.
        df.to_csv(csv_buffer,index=False)
        return Response(
            csv_buffer.getvalue(),
            mimetype="text/csv",
            headers={"Content-disposition":f"attachment; filename=outbreak_data_{region}.csv"} #triggers a file download popup for the user.
        )
    except Exception as e:
        return jsonify({"status":"failed","error":str(e)}),500

# Endpoint 4: Live Heatmap Data 
@api_bp.route('/heatmap-data', methods=['GET'])
def get_heatmap_data():
    try:
        # Hardcoded geographic coordinates to bypass the slow Nominatim API.
        # This reduces API latency from ~2 seconds down to ~0.01 seconds.
        coords = {
            'Maharashtra': [19.75, 75.71],
            'Karnataka': [12.97, 77.59],
            'Kerala': [10.85, 76.27],
            'Delhi': [28.70, 77.10]
        }
        
        heatmap_points = []
        for region, (lat, lon) in coords.items():
            # Query MongoDB for the absolute most recent record for this state (-1 sort)
            record = collection.find_one({'Region': region}, sort=[('Year', -1), ('Week_Num', -1)])
            cases = record.get('Reported_Cases', 0) if record else 0
            
            # Pack it into the format Leaflet.js expects
            heatmap_points.append([lat, lon, cases])
            
        return jsonify(heatmap_points), 200
    except Exception as e:
        return jsonify({'status': 'failed', 'error': str(e)}), 500

# Endpoint 5: Regional Comparison Summary
@api_bp.route('/regional-summary', methods=['GET'])
@token_required
def get_regional_summary():
    try:
        # We grab the active regions from your pipeline
        regions = ['Maharashtra', 'Karnataka', 'Kerala']
        summary = []
        
        for region in regions:
            # Ask MongoDB to sum up all reported cases for this region
            pipeline = [
                {"$match": {"Region": region}},
                {"$group": {"_id": None, "total": {"$sum": "$Reported_Cases"}}}
            ]
            result = list(collection.aggregate(pipeline))
            total_cases = result[0]['total'] if result else 0
            
            #risk styling logic mathematically
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
            
        return jsonify({"status": "success", "data": summary}), 200
    except Exception as e:
        return jsonify({"status": "failed", "error": str(e)}), 500