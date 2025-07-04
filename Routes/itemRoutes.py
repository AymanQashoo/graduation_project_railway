from platform import release
from fastapi import APIRouter, HTTPException
from pymongo import MongoClient
from typing import List, Union, Dict, Any, Optional
from pydantic import BaseModel
from database import get_db
from pymongo import ReturnDocument
from fastapi import APIRouter, HTTPException, Query



from fastapi import UploadFile, File, Form
import os
import shutil
from uuid import uuid4




categories = ["Kids & Family", "Drama", "Action & Adventure", "Comedy", "Animation", "Science Fiction"]


class Item(BaseModel):
    itemId: str
    title: str
    genere: str or None  
    release_date: str or None 
    description: Optional[Union[str, List[str]]] = None
    images: Optional[Union[str, List[Union[str, Dict[str, Any]]]]] = None

    class Config:
        arbitrary_types_allowed = True

db = get_db()
collection = db["Item"]
from datetime import datetime

watched_collection = db["Watched"]
review_collection = db["Reviews"]


class WatchedItem(BaseModel):
    userId: str
    itemId: str
    watched_at: Optional[datetime] = None

router = APIRouter(prefix="/items")


@router.get("/title/{itemId}")
async def get_title_by_item_id(itemId: str):
    item = collection.find_one({"itemId": itemId}, {"_id": 0, "title": 1})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"itemId": itemId, "title": item["title"]}



@router.put("/watch/{userId}/{itemId}")
async def mark_movie_as_watched(userId: str, itemId: str):
    item = collection.find_one({"itemId": itemId})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Optional: prevent duplicates
    if watched_collection.find_one({"userId": userId, "itemId": itemId}):
        return {"message": "Already marked as watched", "itemId": itemId}

    watched_entry = {
        "userId": userId,
        "itemId": itemId,
        "watched_at": datetime.utcnow()
    }
    watched_collection.insert_one(watched_entry)

    return {"message": "Movie marked as watched", "itemId": itemId}



@router.get("/watch/{userId}")
async def get_watched_for_user(userId: str):
    watched = list(
        watched_collection.find(
            {"userId": userId},
            {"_id": 0, "watched_at": 0, "userId": 0}
        )
    )
    if not watched:
        return []

    item_ids = list({w["itemId"] for w in watched})     

    movies = list(
        collection.find(
            {"itemId": {"$in": item_ids}},
            {"_id": 0}
        )
    )

    unique_movies = {}
    for movie in movies:
        unique_movies[movie["itemId"]] = movie  

    return list(unique_movies.values())



@router.delete("/watch/{userId}/{itemId}")
async def remove_watched_item(userId: str, itemId: str):
    result = watched_collection.delete_one({"userId": userId, "itemId": itemId})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found in watchlist")

    return {"message": "Item removed from watchlist"}



@router.get("/popular")
async def get_items_from_category_popular():
    return list(collection.find({}, {"_id": 0}).skip(13020).limit(30))


@router.get("/kids")
async def get_items_from_category_kids():
    items = list(collection.find({"category.2": "Kids & Family"}, {"_id": 0}).limit(30))
    print(items)
    return items

@router.get("/sci")
async def get_items_from_category_sci():
    items = list(collection.find({"category.2": "Science Fiction"}, {"_id": 0}).skip(1020).limit(30))
    return items

@router.get("/action")
async def get_items_from_category_action():
    items = list(collection.find({"category.2": "Action & Adventure"}, {"_id": 0}).skip(1020).limit(30))
    return items
    
@router.get("/comedy")
async def get_items_from_category_comedy():
    items = list(collection.find({"category.2": "Comedy"}, {"_id": 0}).limit(30))
    return items


@router.get("/search")
async def search_items(query: str = Query(..., min_length=1, description="Search keyword")):
    search_filter = {
        "$or": [
            {"title": {"$regex": query, "$options": "i"}}]
    }
    results = list(collection.find(search_filter, {"_id": 0}).limit(50))
    return results
    
index_coll = db["index"] 

UPLOAD_DIR = "uploaded_posters"
os.makedirs(UPLOAD_DIR, exist_ok=True)
@router.post("/add")
async def add_movie_item(
    title: str = Form(...),
    genere: Optional[str] = Form(None),
    release_date: Optional[str] = Form(None),
    poster: UploadFile = File(...)
):
    ext = poster.filename.rsplit(".", 1)[-1]
    filename = f"{uuid4().hex}.{ext}"
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, "wb") as out:
        shutil.copyfileobj(poster.file, out)

    counter_doc = index_coll.find_one_and_update(
        {}, 
        {"$inc": {"current_item_number": 1}},
        return_document=ReturnDocument.AFTER,
        projection={"_id": False, "current_item_number": True}
    )
    if not counter_doc:
        raise HTTPException(500, "Counter document missing or malformed")

    new_id = counter_doc["current_item_number"]

    item = {
        "itemId": new_id,
        "title": title,
        "genere": genere,
        "release_date": release_date,
        "images": f"/{filename}"
    }

    result = collection.insert_one(item)

    item["_id"] = str(result.inserted_id)
    return {
        "message": "Movie item added successfully.",
        "item": item
    }


from datetime import datetime

class Review(BaseModel):
    itemId: str
    userId: str
    rating: float
    title: str
    review: str
    highlight: str
    created_at: Optional[datetime] = None


@router.post("/review/add")
async def add_review(review: Review):

    item = collection.find_one({"itemId": review.itemId}, {"_id": 0})

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    review_data = review.model_dump()
    review_data["created_at"] = datetime.utcnow()

    insert_result = review_collection.insert_one(review_data)

    # Add _id to response if you want
    review_data["_id"] = str(insert_result.inserted_id)

    return {"message": "Review added successfully", "review": review_data}


@router.get("/review/{itemId}")
async def get_reviews_for_item(itemId: str):
    reviews = list(review_collection.find({"itemId": itemId}, {"_id": 0}))
    return {"itemId": itemId, "reviews": reviews}
