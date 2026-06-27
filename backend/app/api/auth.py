from flask import Blueprint, request, jsonify
import jwt
from datetime import datetime, timedelta
from functools import wraps
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import sys

# Ensure we can import db_config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'../../..','src')))
from db_config import get_database_client

load_dotenv()
auth_bp = Blueprint('auth', __name__)
SECRET_KEY = os.getenv('SECRET_KEY', 'fallback_secret')

def get_user_collection():
    db = get_database_client()
    return db['users']

# Initialize default admin if none exists
try:
    users_col = get_user_collection()
    if users_col.count_documents({"username": "admin"}) == 0:
        admin_pass = os.getenv('ADMIN_PASSWORD', 'admin123')
        users_col.insert_one({
            "username": "admin",
            "password_hash": generate_password_hash(admin_pass)
        })
except Exception as e:
    print(f"Auth init error: {e}")

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except Exception as e:
            return jsonify({'message':'Token is invalid!','error':str(e)}), 401
        return f(*args, **kwargs)
    return decorated

@auth_bp.route('/login', methods=['POST'])
def login():
    auth = request.get_json()
    if not auth or not auth.get('username') or not auth.get('password'):
        return jsonify({'message': 'Missing credentials'}), 401
    
    users_col = get_user_collection()
    user = users_col.find_one({"username": auth.get('username')})
    
    if user and check_password_hash(user['password_hash'], auth.get('password')):
        token = jwt.encode({
            'user': user['username'], 
            'exp': datetime.utcnow() + timedelta(hours=12)
        }, SECRET_KEY, algorithm='HS256')
        return jsonify({'token': token})
        
    return jsonify({'message':'Could not verify'}), 401
