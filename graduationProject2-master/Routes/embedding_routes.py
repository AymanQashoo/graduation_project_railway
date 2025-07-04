from fastapi import APIRouter, HTTPException
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from database import get_db
from typing import List
from fastapi import Query


router = APIRouter(prefix="/content", tags=["content"])
db = get_db()
collection = db["Item"]

EMBEDDING_FILE = "preprocessing/movie_embeddings.npz"
DEBUG_FILE = "preprocessing/movie_embeddings_debug.csv"

data = np.load(EMBEDDING_FILE)
desc_embeddings = data["description_embeddings"]
cat_embeddings = data["category_embeddings"]
item_ids = data["item_ids"]

embeddings = np.hstack((desc_embeddings, cat_embeddings))

id_to_index = {int(item_id): idx for idx, item_id in enumerate(item_ids)}

df_debug = pd.read_csv(DEBUG_FILE)

@router.get("/similar/{item_id}")
def get_similar_movies(item_id: int, top_k: int = 10):
    if item_id not in id_to_index:
        raise HTTPException(status_code=404, detail="Item ID not found.")

    idx = id_to_index[item_id]
    target_embedding = embeddings[idx].reshape(1, -1)

    similarities = cosine_similarity(target_embedding, embeddings)[0]

    sorted_indices = np.argsort(similarities)[::-1]
    filtered_indices = [i for i in sorted_indices if i != idx and similarities[i] < 1.0]

    top_indices = filtered_indices[:top_k]

    results = []
    for i in top_indices:
        item_doc = collection.find_one({"itemId": str(item_ids[i])}, {"_id": 0})
        if item_doc:
            item_doc["similarity"] = float(similarities[i])
            item_doc["title"] = str(item_doc["title"])
            results.append(item_doc)

    return results


@router.get("/similar_batch")
def get_similar_movies_batch(query_ids: List[int] = Query(...), top_k: int = 10):
    results = {}    

    for item_id in query_ids:
        if item_id not in id_to_index:
            results[item_id] = {"error": "Item ID not found."}
            continue

        idx = id_to_index[item_id]
        target_embedding = embeddings[idx].reshape(1, -1)
        similarities = cosine_similarity(target_embedding, embeddings)[0]

        sorted_indices = np.argsort(similarities)[::-1]
        filtered_indices = [i for i in sorted_indices if i != idx and similarities[i] < 1.0]
        top_indices = filtered_indices[:top_k]

        similar_items = []
        for i in top_indices:
            item_doc = collection.find_one({"itemId": str(item_ids[i])}, {"_id": 0})
            if item_doc:
                item_doc["similarity"] = float(similarities[i])
                item_doc["title"] = str(item_doc["title"])
                similar_items.append(item_doc)

        results[item_id] = similar_items

    return results
