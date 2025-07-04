import os
import numpy as np
import scipy.sparse as sps

from eals import ElementwiseAlternatingLeastSquares, load_model


import csv

BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, "amazonMovies.joblib")


def load_ratings(file_name):
    print(f"Loading the data from {file_name}")

    file_path = os.path.join(BASE_DIR, file_name)
    
    rows, cols, vals = [], [], []
    
    with open(file_path, newline="") as f:
        reader = csv.reader(f, delimiter="\t")  # Use tab as the delimiter
        
        for line in reader:
            try:
                user_id = int(line[1])
                movie_id = int(line[3])
                rating = float(line[4])  
                
                rows.append(user_id)
                cols.append(movie_id)
                vals.append(1.0)  
            except ValueError:
                print(f"Skipping invalid line: {line}")
    
    if not rows or not cols:
        print("No valid data found!")
        return None, [], [], []
    
    ratings = sps.csr_matrix((vals, (rows, cols)), shape=(max(rows) + 1, max(cols) + 1), dtype=np.float32)
    
    return ratings, rows, cols, vals


def update_model(user_id, movie_id):
    print(f"Loading the model from {MODEL_PATH}")
    model = load_model(MODEL_PATH)
    print("Updating the model")
    model.update_model(user_id, movie_id)
    print(f"Saving the model to {MODEL_PATH}")
    model.save(MODEL_PATH)
    print("Done")


def recommend(user_id, k=20):
    print(f"Loading the model from {MODEL_PATH}")
    model = load_model(MODEL_PATH)
    user_vector = model.user_factors[user_id]
    pred_ratings = model.item_factors @ user_vector
    topk_items = np.argsort(pred_ratings)[-k:][::-1]
    print(f"Recommended {k} items for user {user_id}")
    print(topk_items)
    return topk_items.tolist()

def fit_model(train_data, num_iter=5):
    print("Fitting the model")
    model = ElementwiseAlternatingLeastSquares(num_iter=num_iter,alpha=0,w0=160)
    model.fit(train_data, show_loss=True)
    
    print(f"Saving the model to {MODEL_PATH}")
    model.save(MODEL_PATH)
    print("Model training complete")
    return model

def main():

    train_ratings, _, _, _ = load_ratings("filtered_reviews2copy.csv")
    model = fit_model(train_ratings)


if __name__ == "__main__":
    main()