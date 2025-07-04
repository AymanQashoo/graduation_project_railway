from pymongo import MongoClient

def get_db():
    uri = "mongodb+srv://samueltannous174:mKVnK6B2nvPERsrr@cluster1.jxl34.mongodb.net/?retryWrites=true&w=majority&appName=Cluster1"
    try:
        client = MongoClient(uri)
        client.admin.command("ping")  # Test connection
        print("MongoDB connection successful")
        db = client["ecommerce_project"]
        return db
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        return None



