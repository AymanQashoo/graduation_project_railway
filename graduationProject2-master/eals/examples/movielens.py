import json
import os
import numpy as np
import scipy.sparse as sps

from eals import ElementwiseAlternatingLeastSquares, load_model

BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, "model.joblib")
DATA_FILE = os.path.join(BASE_DIR, "Health_and_Personal_Care.jsonl")

def load_ratings():
    print("Loading the training data")
    user_map = {}
    item_map = {}
    user_counts = {}
    item_counts = {}

    # First pass: Count interactions
    with open(DATA_FILE, "r") as f:
        for line in f:
            entry = json.loads(line)
            if float(entry["rating"]) > 3:
                user_id = entry["user_id"]
                item_id = entry["parent_asin"]
                user_counts[user_id] = user_counts.get(user_id, 0) + 1
                item_counts[item_id] = item_counts.get(item_id, 0) + 1

    # Filter users and items with at least 10 interactions
    filtered_users = {user for user, count in user_counts.items() if count >= 10}
    filtered_items = {item for item, count in item_counts.items() if count >= 10}

    rows, cols, vals = [], [], []
    user_counter, item_counter = 0, 0

    # Second pass: Create mappings and store interactions
    with open(DATA_FILE, "r") as f:
        for line in f:
            entry = json.loads(line)
            if float(entry["rating"]) > 3:
                user_id = entry["user_id"]
                item_id = entry["parent_asin"]

                if user_id in filtered_users and item_id in filtered_items:
                    if user_id not in user_map:
                        user_map[user_id] = user_counter
                        user_counter += 1
                    if item_id not in item_map:
                        item_map[item_id] = item_counter
                        item_counter += 1
                    
                    rows.append(user_map[user_id])
                    cols.append(item_map[item_id])
                    vals.append(1.0)

    ratings = sps.csr_matrix(
        (vals, (rows, cols)), shape=(len(user_map), len(item_map)), dtype=np.float32
    )
    return ratings, user_map, item_map

def fit():
    ratings, user_map, item_map = load_ratings()
    print("Fitting the model")
    model = ElementwiseAlternatingLeastSquares(num_iter=50)
    model.fit(ratings, show_loss=True)
    print(f"Saving the model to {MODEL_PATH}")
    model.save(MODEL_PATH)
    print("Done")
    return user_map, item_map

def update(user_id, item_id):
    print(f"Loading the model from {MODEL_PATH}")
    model = load_model(MODEL_PATH)
    ratings, user_map, item_map = load_ratings()
    
    if user_id in user_map and item_id in item_map:
        mapped_user_id = user_map[user_id]
        mapped_item_id = item_map[item_id]
        print("Updating the model")
        model.update_model(mapped_user_id, mapped_item_id)
        print(f"Saving the model to {MODEL_PATH}")
        model.save(MODEL_PATH)
        print("Done")
    else:
        print("User ID or Item ID not found in training data.")

def recommend(user_id, k=20):
    print(f"Loading the model from {MODEL_PATH}")
    model = load_model(MODEL_PATH)
    ratings, user_map, item_map = load_ratings()
    
    if user_id in user_map:
        mapped_user_id = user_map[user_id]
        print(f"Searching Top {k} recommended items for user_id={user_id}")
        user_vector = model.user_factors[mapped_user_id]
        pred_ratings = model.item_factors @ user_vector
        topk_item_ids = reversed(np.argsort(pred_ratings)[-k:])
        print("Done\n")
        print(f"Recommendations for user_id={user_id}")
        print("rank (score): item ID (original item ID)")
        item_id_reverse_map = {v: k for k, v in item_map.items()}
        for rank, id_ in enumerate(topk_item_ids, start=1):
            original_item_id = item_id_reverse_map.get(id_, "Unknown")
            print(f"{rank:4d} ( {pred_ratings[id_]:3.2f}): {id_} ({original_item_id})")
    else:
        print("User ID not found in training data.")

def main():
    # update("AHKIMFUXMLOUN7SBXHEDD2K2AN7Q","B0722XRH4C")
    # update("AHKIMFUXMLOUN7SBXHEDD2K2AN7Q","B0B3947PL9")
    # update("AHKIMFUXMLOUN7SBXHEDD2K2AN7Q","B09C8BY2W4")
    # update("AHKIMFUXMLOUN7SBXHEDD2K2AN7Q","B07X74QW3Q")
    recommend("AHKIMFUXMLOUN7SBXHEDD2K2AN7Q")

if __name__ == "__main__":
    main()