# src/db_config.py
from pymongo import MongoClient
import sys

# Connection Configurations
# Local default: 'mongodb://localhost:27017/'
# Cloud Atlas default will look like: 'mongodb+srv://<user>:<password>@cluster.mongodb.net/'
MONGO_URI = 'mongodb://localhost:27017/' 
DB_NAME = 'disease_predictor'

def get_database_client():
    """
    Establishes and returns a connection to the MongoDB database instance.
    """
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # Trigger a quick connection check
        client.server_info()
        print("🔌 Successfully connected to the MongoDB server.")
        return client[DB_NAME]
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)