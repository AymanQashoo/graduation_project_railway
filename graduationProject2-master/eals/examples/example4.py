import os
from collections import defaultdict

# Define the base directory and file paths
BASE_DIR = os.path.dirname(__file__)
INPUT_FILE = os.path.join(BASE_DIR, 'yelp.csv')
TRAIN_FILE = os.path.join(BASE_DIR, 'yelp_train.csv')
TEST_FILE = os.path.join(BASE_DIR, 'yelp_test.csv')

# Load the data from the file (assuming TSV format: user_id, movie_id, rating, timestamp)
data = []
with open(INPUT_FILE, 'r') as file:
    for line in file:
        parts = line.strip().split('\t')  # Assuming tab-separated
        if len(parts) == 4:
            user_id = parts[0]
            movie_id = parts[1]  # Assuming movie_id is present
            rating = float(parts[2])
            timestamp = int(parts[3])
            data.append({
                'user_id': user_id,
                'movie_id': movie_id,
                'rating': rating,
                'timestamp': timestamp
            })

# Group reviews by user
user_reviews = defaultdict(list)
for review in data:
    user_reviews[review['user_id']].append(review)

# Split into train and test sets
train_data = []
test_data = []

for user, reviews in user_reviews.items():
    # Sort reviews by timestamp (assuming 'timestamp' key exists)
    reviews.sort(key=lambda x: x['timestamp'])
    
    # Assign the last review as test data, rest as train data
    test_data.append(reviews[-1])
    train_data.extend(reviews[:-1])

# Save train and test data with movie_id
with open(TRAIN_FILE, 'w') as train_file:
    for review in train_data:
        train_file.write(f"{review['user_id']}\t{review['movie_id']}\t{review['rating']}\t{review['timestamp']}\n")

with open(TEST_FILE, 'w') as test_file:
    for review in test_data:
        test_file.write(f"{review['user_id']}\t{review['movie_id']}\t{review['rating']}\t{review['timestamp']}\n")

print("Data split completed: Train and Test files created.")
