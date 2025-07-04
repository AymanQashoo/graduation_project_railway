import json
import os
import numpy as np
import scipy.sparse as sps
from eals import ElementwiseAlternatingLeastSquares, load_model

BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, "model2.joblib")
# Global mappings
user_ids = {}
item_ids = {}

def load_ratings(file_name):
    global user_ids, item_ids  # Use the global mappings
    print(f"Loading the data from {file_name}")
    rows, cols, vals = [], [], []
    user_counter, item_counter = len(user_ids), len(item_ids)  # Continue counting from existing mappings
    
    # Construct the full file path
    file_path = os.path.join(BASE_DIR, file_name)
    
    # Open and read the JSON Lines file
    with open(file_path, "r") as f:
        for line in f:
            try:
                # Parse each line as a JSON object
                rating = json.loads(line.strip())
                user_id = rating["user_id"]
                item_id = rating["asin"]
                
                # Map user and item IDs to integer indices
                if user_id not in user_ids:
                    user_ids[user_id] = user_counter
                    user_counter += 1
                if item_id not in item_ids:
                    item_ids[item_id] = item_counter
                    item_counter += 1
                
                # Append to rows, cols, and vals
                rows.append(user_ids[user_id])
                cols.append(item_ids[item_id])
                vals.append(1.0)

                
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                print(f"Skipping invalid line: {line.strip()}. Error: {e}")
                continue
    print(f"Number of users: {len(user_ids)}")
    print(f"Number of items: {len(item_ids)}")

    # Create a sparse matrix
    ratings = sps.csr_matrix((vals, (rows, cols)), shape=(user_counter, item_counter), dtype=np.float32)
    print(f"Loaded {len(vals)} ratings with {user_counter} users and {item_counter} items.")
    return ratings, user_ids, item_ids

def fit_model(train_data, num_iter=5):
    print("Fitting the model")
    model = ElementwiseAlternatingLeastSquares(num_iter=num_iter, factors=32, alpha=0.60, w0=32)
    model.fit(train_data, show_loss=True)
    print(f"Saving the model to {MODEL_PATH}")
    model.save(MODEL_PATH)
    print("Model training complete")
    return model

import numpy as np

import numpy as np

def evaluate_model(model, test_data, k=100):
    print("Evaluating the model")
    hr, ndcg = 0, 0
    
    # Get all test interactions as (user, item) pairs
    test_users, test_items = test_data.nonzero()
    num_tests = len(test_users)  # Total test samples

    for i in range(20000):  # Iterate over test interactions
        user = test_users[i]
        test_item = test_items[i]

        # Ensure the user index exists in the model
        if user >= model.user_factors.shape[0]:
            continue  # Skip users not in the training set

        # Generate predictions
        user_vector = model.user_factors[user]
        pred_ratings = model.item_factors @ user_vector

        # Get the top-k items
        topk_items = np.argsort(pred_ratings)[-k:][::-1]

        # Calculate HR and NDCG
        if test_item in topk_items:
            hr += 1
            rank = np.where(topk_items == test_item)[0][0] + 1
            ndcg += 1 / np.log2(rank + 1)

    # Normalize HR and NDCG
    if num_tests > 0:
        hr /= num_tests
        ndcg /= num_tests

    print(f"HR@{k}: {hr:.4f}, NDCG@{k}: {ndcg:.4f}")



def main():
    # Load training data
    train_ratings, train_user_ids, train_item_ids = load_ratings("home_train.json")
    

    # # Fit the model
    model = fit_model(train_ratings)

    



if __name__ == "__main__":
    main()