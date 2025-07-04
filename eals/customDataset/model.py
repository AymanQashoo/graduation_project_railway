import os
import numpy as np
import pandas as pd
import scipy.sparse as sps
from eals import ElementwiseAlternatingLeastSquares, load_model

BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, "amazonMovies.joblib")

def load_ratings(dataset_filename):
    dataset_path = os.path.join("datasets", dataset_filename)
    print(f"Loading dataset from {dataset_path}")
    
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")

    df = pd.read_csv(dataset_path)

    if "userID" not in df.columns or "itemID" not in df.columns:
        raise ValueError("Dataset must contain 'userID' and 'itemID' columns")

    rows = df["userID"].values
    cols = df["itemID"].values
    vals = np.ones_like(rows, dtype=np.float32)  # Implicit feedback

    num_users = df["userID"].max() + 1
    num_items = df["itemID"].max() + 1

    ratings = sps.csr_matrix((vals, (rows, cols)), shape=(num_users, num_items), dtype=np.float32)
    return ratings

def fit_model(train_data, num_iter=5):
    print("Training model on custom dataset...")
    model = ElementwiseAlternatingLeastSquares(num_iter=num_iter, alpha=0, w0=160)
    model.fit(train_data, show_loss=True)
    model.save(MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")
    return model

def update_model(user_id, item_id):
    print(f"Loading model from {MODEL_PATH}")
    model = load_model(MODEL_PATH)

    if user_id >= model.user_factors.shape[0]:
        raise IndexError("User ID out of range")
    if item_id >= model.item_factors.shape[0]:
        raise IndexError("Item ID out of range")

    print(f"Updating model for user {user_id}, item {item_id}")
    model.update_model(user_id, item_id)
    model.save(MODEL_PATH)
    print("Model updated and saved.")

def recommend(user_id, k=20):
    print(f"Loading model from {MODEL_PATH}")
    model = load_model(MODEL_PATH)

    if user_id >= model.user_factors.shape[0]:
        raise IndexError("User ID out of range")

    user_vector = model.user_factors[user_id]
    pred_ratings = model.item_factors @ user_vector
    top_k = np.argsort(pred_ratings)[-k:][::-1]
    print(f"Top {k} recommendations for user {user_id}: {top_k.tolist()}")
    return top_k.tolist()

def main(dataset_filename):
    ratings = load_ratings(dataset_filename)
    fit_model(ratings)