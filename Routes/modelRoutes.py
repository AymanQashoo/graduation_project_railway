from fastapi import APIRouter
from eals.amazonMovies.model import recommend, load_model
from database import get_db
from pymongo import MongoClient
from pydantic import BaseModel
from typing import Optional, List, Union, Dict, Any
from functools import lru_cache
import os
import numpy as np
import json
from  my_redis_test import r  # Import the Redis client

BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, "amazonMovies.joblib")

router = APIRouter(prefix="/model", tags=["model"])

db = get_db()
collection = db["Item"]

class Item(BaseModel):
    itemId: Optional[str]
    title: Optional[str] = None
    description: Optional[Union[str, List[str]]] = None
    images: Optional[Union[str, List[Union[str, Dict[str, Any]]]]] = None    

def get_model():
    print(f"Loading the model from {MODEL_PATH}")
    return load_model(MODEL_PATH)

@router.put("/update/{user_id}/{item_id}")
def update_route(user_id: int, item_id: int):
    model = get_model()
    print("Updating model...")
    model.update_model(user_id, item_id)
    print(f"Saving the model to {MODEL_PATH}")
    model.save(MODEL_PATH)
    
    r.delete(f"recommend:{user_id}")
    
    print("Update complete and cache invalidated.")
    return {"message": "Model updated and cache invalidated"}

@router.get("/recommend/{user_id}")
def recommend_route(user_id: int):
    model = get_model()
    print(f"Generating recommendations for user_id: {user_id}")

    if user_id >= len(model.user_factors):
        return {"message": f"No recommendations: user_id {user_id} not found in model."}

    try:
        user_vector = model.user_factors[user_id]
        pred_ratings = model.item_factors @ user_vector
        topk_items = np.argsort(pred_ratings)[-30:][::-1]
        recommendations = topk_items.tolist()

        if not recommendations:
            return {"message": "No recommendations available."}

        items = collection.find({"itemId": {"$in": [str(i) for i in recommendations]}})
        raw_items = [Item(**item) for item in items]

        # Remove duplicates by title
        seen_titles = set()
        unique_items = []
        for item in raw_items:
            if item.title and item.title not in seen_titles:
                seen_titles.add(item.title)
                unique_items.append(item)

        result = [item.dict() for item in unique_items]


        return result if result else {"message": "No matching items found in database."}

    except Exception as e:
        print(f"Error: {e}")
        return {"message": "An error occurred while generating recommendations."}
