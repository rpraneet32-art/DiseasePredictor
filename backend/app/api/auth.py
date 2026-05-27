# imports
from flask import Blueprint, request, jsonify
#Blueprint: Flask tool to organize routes into different files
#request: Allows access of incoming HTTP request from frontend
#jsonify: converts python dictionaries into proper JSON formats
import jwt #PyJWT lib to create and read JSON web tokens
from datetime import datetime #will use to set exact expiration time of token
from functools import wraps #keeps original function's name and metadata preserved

#Initial Setup
auth_bp=Blueprint('auth',__name__) #creates auth blueprint and groups all routes attached to the auth_bp
SECRET_KEY='super_secret_production_key' #cryptographic key is signed with this string when token is created

#security decorator
def token_required(f):#defines the decorator(wraps around f, running some code before f is executed) function 
    @wraps(f)
    def decorated(*args, **kwargs): # actual wrapper logic, takes arguments (args, kwargs) that original route might need
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message':'Token is missing'}), 401
        try:
            token=token.split([1]) #Cuts the string at space and grabs the actual token
            data=jwt.decode(token,SECRET_KEY, algorithms=["HS256"]) #takes the token checks signature against SECRET_KEY and expects HS256 encryption
        except Exception as e:
            return jsonify({'message':'Token is invalid!','error':str(e)}), 401
        return f(*args, **kwargs)#if try succeeds f will execute
    return decorated #returns wrapper function so it can used on routes

# The login Route
@auth_bp.route('/login',methods=['POST']) #creates endpoint at '/login' to only accept post request
def login():
    auth=request.get_json() #gets the json body sent from frontend
    if auth and auth.get('username') == 'admin' and auth.get('password') == 'Project_no_10':
        #if credentials match it starts creating JWT
        token=jwt.encode({'user': auth.get('username'), 'exp':datetime.utcnow() + datetime.timedelta(hours=12)}, SECRET_KEY, algorithm='HS256')
        return jsonify({'token':token})
    return jsonify({'message':'Could not verify'}),401
