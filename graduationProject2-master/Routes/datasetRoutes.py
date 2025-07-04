from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Union, List, Dict, Any
import pandas as pd
from io import StringIO
import numpy as np
import os
from eals import ElementwiseAlternatingLeastSquares, load_model

BASE_DIR = os.path.dirname(__file__)
DEFAULT_MODEL_PATH = os.path.join(BASE_DIR, "amazonMovies.joblib")

from customDataset import model as custom_model
from items.database import get_db

router = APIRouter(prefix="/dataset", tags=["dataset"])

db = get_db()
if db is None:
    raise RuntimeError("Failed to connect to MongoDB.")

mapping_collection = db["ItemMap"]
user_mapping_collection = db["UserMap"]
new = db["New"]
customer_collection = db["CustomerInfo"]


class Item(BaseModel):
    itemId: Optional[str]
    title: Optional[str] = None
    description: Optional[Union[str, List[str]]] = None
    images: Optional[Union[str, List[Union[str, Dict[str, Any]]]]] = None


def get_next_customer_id():
    result = customer_collection.find_one_and_update(
        {"_id": "customer_id"},
        {"$inc": {"sequence_value": 1}},
        upsert=True,
        return_document=True
    )
    return result["sequence_value"]


@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    contents = await file.read()

    try:
        df = pd.read_csv(StringIO(contents.decode("utf-8-sig")), sep="\t")
        df.columns = df.columns.str.strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid TSV format: {str(e)}")

    if not {'userID', 'itemTitle'}.issubset(df.columns):
        raise HTTPException(status_code=422, detail="File must contain 'userID' and 'itemTitle' columns.")

    df = df.dropna(subset=['itemTitle'])

    item_map_docs = list(mapping_collection.find({}, {"_id": 0, "title": 1, "newProductId": 1}))
    title_to_id = {doc["title"].strip(): doc["newProductId"] for doc in item_map_docs}
    max_item_id = max(title_to_id.values(), default=-1)

    new_item_docs = []
    item_ids = []
    for title in df['itemTitle']:
        title_clean = str(title).strip()
        if not title_clean:
            item_ids.append(None)
            continue
        if title_clean not in title_to_id:
            max_item_id += 1
            title_to_id[title_clean] = max_item_id
            new_item_docs.append({
                "title": title_clean,
                "newProductId": max_item_id
            })
        item_ids.append(title_to_id[title_clean])

    if new_item_docs:
        mapping_collection.insert_many(new_item_docs)

    try:
        df['itemID'] = [int(i) if pd.notna(i) else -1 for i in item_ids]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Item ID conversion failed: {str(e)}")

    try:
        model = load_model(DEFAULT_MODEL_PATH)
        model_user_count = model.user_factors.shape[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model load failed: {str(e)}")

    user_map_docs = list(mapping_collection.find({"type": "user"}))
    user_str_to_id = {doc["original_id"]: doc["mapped_id"] for doc in user_map_docs}
    max_user_id = max(model_user_count - 1, max(user_str_to_id.values(), default=-1))

    new_user_mapping = {}
    user_mapped_ids = []
    for user in df['userID']:
        if user not in user_str_to_id:
            max_user_id += 1
            user_str_to_id[user] = max_user_id
            new_user_mapping[user] = max_user_id
        user_mapped_ids.append(user_str_to_id[user])
    df['userID'] = user_mapped_ids

    new_user_docs = [
        {"type": "user", "original_id": u, "mapped_id": i}
        for u, i in new_user_mapping.items()
    ]
    if new_user_docs:
        new.insert_many(new_user_docs)

    if new_user_mapping:
        user_mapping_collection.insert_many([
            {"original_userID": orig, "mapped_userID": mapped}
            for orig, mapped in new_user_mapping.items()
        ])

    os.makedirs("datasets", exist_ok=True)
    dataset_name = file.filename
    dataset_path = os.path.join("datasets", dataset_name)
    df[['userID', 'itemID']].to_csv(dataset_path, index=False)

    try:
        for _, row in df.iterrows():
            model.update_model(int(row['userID']), int(row['itemID']))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model update failed: {str(e)}")

    customer_id = get_next_customer_id()
    os.makedirs("models", exist_ok=True)
    customer_model_path = os.path.join("models", f"{customer_id}.joblib")

    try:
        model.save(customer_model_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save model: {str(e)}")

    new_user_ids = list(new_user_mapping.values())
    new_user_range = (
        min(new_user_ids),
        max(new_user_ids)
    ) if new_user_ids else (None, None)

    customer_collection.insert_one({
        "customer_id": customer_id,
        "model_path": customer_model_path,
        "dataset_name": dataset_name,
        "user_range": new_user_range
    })

    return {
        "your_customer_id": customer_id,
        "your_user_range": new_user_range
    }


@router.get("/recommend")
async def recommend_items(
    customer_id: int = Query(...),
    user_id: int = Query(...)
):
    model_path = os.path.join("models", f"{customer_id}.joblib")
    if not os.path.exists(model_path):
        raise HTTPException(status_code=404, detail="Model not found for given customer ID")

    try:
        model = load_model(model_path)
        print(f"User id: {user_id}")

        if user_id >= model.user_factors.shape[0]:
            print(f"No recommendations: user_id {user_id} not found in model.")
            return {"message": f"No recommendations: user_id {user_id} not found in model."}

        # Calculate recommendation scores
        user_vector = model.user_factors[user_id]
        pred_ratings = model.item_factors @ user_vector
        topk_items = np.argsort(pred_ratings)[-20:][::-1]
        recommendations = topk_items.tolist()
        print(f"Top 20 Recommendations (item IDs): {recommendations}")

        if not recommendations:
            return {"message": "No recommendations available."}

        # Fetch item documents from DB using integer IDs
        item_docs = mapping_collection.find(
            {"newProductId": {"$in": recommendations}},
            {"_id": 0, "title": 1}
        )

        # Extract titles and remove duplicates
        seen_titles = set()
        unique_titles = []
        for doc in item_docs:
            title = doc.get("title")
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_titles.append(title)

        return {"recommended_titles": unique_titles} if unique_titles else {"message": "No matching item titles found."}

    except Exception as e:
        print(f"Error during recommendation: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while generating recommendations.")
