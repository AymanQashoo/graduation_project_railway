import os
import csv
import numpy as np
import scipy.sparse as sps
from eals import ElementwiseAlternatingLeastSquares, load_model

from evaluate_ml import evaluate_model
BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, "model_ml.joblib")


       
def load_rating_file_as_list( filename):
        ratingList = []
        file_path = os.path.join(BASE_DIR, filename)

        with open(file_path, "r") as f:
            line = f.readline()
            while line != None and line != "":
                arr = line.split("\t")
                user, item = int(arr[0]), int(arr[1])
                ratingList.append([user, item])
                line = f.readline()
        return ratingList
    
def load_negative_file(filename):
        negativeList = []
        file_path = os.path.join(BASE_DIR, filename)

        with open(file_path, "r") as f:
            line = f.readline()
            while line != None and line != "":
                arr = line.split("\t")
                negatives = []
                for x in arr[1: ]:
                    negatives.append(int(x))
                negativeList.append(negatives)
                line = f.readline()
        return negativeList



def load_ratings(file_name):
    """Loads ratings from a file and converts them into a sparse matrix."""
    print(f"Loading the data from {file_name}")
    rows, cols, vals = [], [], []
    
    file_path = os.path.join(BASE_DIR, file_name)
    with open(file_path, newline="", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 4:
                print(f"Skipping invalid line: {line}")
                continue
            
            try:
                user_id, item_id, rating, _ = map(int, parts)
                rows.append(user_id)
                cols.append(item_id)
                vals.append(1.0)  # Use the actual rating for explicit feedback
                
            except ValueError:
                print(f"Skipping invalid line: {line}")

    if not rows or not cols:
        raise ValueError(f"Error: No valid data in {file_name}")

    num_users = max(rows) + 1
    num_items = max(cols) + 1
    ratings = sps.csr_matrix((vals, (rows, cols)), shape=(num_users, num_items), dtype=np.float32)
    return ratings

def fit_model(train_data, num_iter=5):
    print("Fitting the model")
    model = ElementwiseAlternatingLeastSquares(num_iter=num_iter,alpha=0,w0=160)
    model.fit(train_data, show_loss=True)
    
    print(f"Saving the model to {MODEL_PATH}")
    model.save(MODEL_PATH)
    print("Model training complete")
    return model




def main():
    """Main pipeline for training and evaluation."""
    train_file = "ml-1m_train.csv"
    test_file = "ml-1m_test.csv"
    negative_file = "ml-1m_test_negative.csv"
        
  
    # Load test ratings
    testRatings = load_rating_file_as_list(test_file)
    # Load test negatives
    testNegatives = load_negative_file(negative_file)
    
    # Fit the model
    model = load_model(MODEL_PATH)


    K=10
    num_thread = 1
    
    (hits, ndcgs) = evaluate_model(model, testRatings, testNegatives, K, num_thread)
    hr, ndcg = np.array(hits).mean(), np.array(ndcgs).mean()
    print('Init: HR = %.4f, NDCG = %.4f' % (hr, ndcg))


if __name__ == "__main__":
    main()
