import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

EMBEDDING_FILE = "preprocessing/movie_embeddings.npz"
DEBUG_FILE = "preprocessing/movie_embeddings_debug.csv"

data = np.load(EMBEDDING_FILE)
desc_embeddings = data["description_embeddings"]
cat_embeddings = data["category_embeddings"]
product_ids = data["item_ids"]

embeddings = np.hstack((desc_embeddings, cat_embeddings))

debug_df = pd.read_csv(DEBUG_FILE)

def find_similar_items(product_id: int, top_k: int = 10):
    if product_id not in product_ids:
        raise ValueError(f"Product ID {product_id} not found in embeddings.")
    
    idx = np.where(product_ids == product_id)[0][0]
    query_embedding = embeddings[idx].reshape(1, -1)

    similarities = cosine_similarity(query_embedding, embeddings)[0]

    top_indices = similarities.argsort()[::-1][1:top_k+1]

    # Prepare results
    results = []
    for i in top_indices:
        pid = int(product_ids[i])
        row = debug_df.loc[debug_df["item_id"] == pid]
        desc = row["enhanced_description"].values[0]
        category = row["category"].values[0]
        sim = float(similarities[i])
        results.append({
            "item_id": pid,
            "category": category,
            "description": desc,
            "similarity": sim
        })
    
    return results