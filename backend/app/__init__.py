# Here the routes and auth will plug together to form the machine: Application Factory
#imports
from flask import Flask #Framework used to spin up the web server
from flask_cors import CORS # enables ports to talk to each other so React can fetch data
from app.api.auth import auth_bp #(login and token generation)
from app.api.route import api_bp #(predictions,history,export)

#Factory Function
def create_app():
    app=Flask(__name__) #Initializes server application
    CORS(app) #wraps around the server, tells to listen to requests from frontend
    # The Blueprint registration
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(api_bp, url_prefix='/api')
    return app
