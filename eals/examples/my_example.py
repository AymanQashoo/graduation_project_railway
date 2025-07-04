import json
import os
import numpy as np
import scipy.sparse as sps
from eals import ElementwiseAlternatingLeastSquares
import csv

BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, "model.joblib")


def load_ratings(file_name):
    print(f"Loading the data from {file_name}")
    
    file_path = os.path.join(BASE_DIR, file_name)
    
    rows, cols, vals = [], [], []
    
    with open(file_path, newline="") as f:
        reader = csv.reader(f, delimiter="\t")  # Use tab as the delimiter
        
        for line in reader:
            try:
                user_id = int(line[0])
                movie_id = int(line[1])
                rating = float(line[2])  
                timestamp = int(line[3]) 
                
                rows.append(user_id)
                cols.append(movie_id)
                vals.append(1.0)  # Store actual ratings
            except ValueError:
                print(f"Skipping invalid line: {line}")
    
    if not rows or not cols:
        print("No valid data found!")
        return None, [], [], []
    
    ratings = sps.csr_matrix((vals, (rows, cols)), shape=(max(rows) + 1, max(cols) + 1), dtype=np.float32)
    
    return ratings, rows, cols, vals

def fit_model(train_data, num_iter=10):
    print("Fitting the model")
    model = ElementwiseAlternatingLeastSquares(num_iter=num_iter, factors=128, alpha=0, w0=512)
    model.fit(train_data, show_loss=True)
    print(f"Saving the model to {MODEL_PATH}")
    model.save(MODEL_PATH)
    print("Model training complete")
    return model


def evaluate_model(model, test_data, k=100):
    print("Evaluating the model")
    hr, ndcg = 0, 0
    for user in range(test_data.shape[0]):
        test_item = test_data[user].nonzero()[1]
        if len(test_item) == 0:
            continue
        test_item = test_item[0]
        
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
    hr /= test_data.shape[0]
    ndcg /= test_data.shape[0]
    print(f"HR@{k}: {hr:.4f}, NDCG@{k}: {ndcg:.4f}")

def main():

    train_ratings, _, _, _ = load_ratings("yelp_train.csv")
    # Load training data
    model = fit_model(train_ratings)
    
    # Save the model
    
    # Load testing data
    test_ratings, _, _, _ = load_ratings("yelp_test.csv")
    
    # Evaluate the model on the testing data
    evaluate_model(model, test_ratings)


if __name__ == "__main__":
    main()