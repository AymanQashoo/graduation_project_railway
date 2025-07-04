import os
import csv
import requests

# TMDB API Configuration
TMDB_API_KEY = "dcd36d10874a8624c1b850c3b8071932"
TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"

def get_tmdb_id(title):
    if not title.strip():
        return ""  # Skip empty titles
    
    params = {
        "api_key": TMDB_API_KEY,
        "query": title,
        "language": "en-US"
    }
    
    response = requests.get(TMDB_SEARCH_URL, params=params)
    if response.status_code == 200:
        results = response.json().get("results", [])
        if results:
            return results[0].get("id", "")  # Return the first matched movie's ID
    return ""  # Return empty if no match found

# File Path
BASE_DIR = os.path.dirname(__file__)
csv_file_path = os.path.join(BASE_DIR, "filtered_reviews2copy.csv")

# Read and update the CSV file
updated_data = []
with open(csv_file_path, newline='', encoding='utf-8') as infile:
    reader = csv.reader(infile, delimiter='\t')
    headers = next(reader)  # Read header row

    # Ensure "tmdbId" column exists
    if "tmdbId" not in headers:
        headers.append("tmdbId")

    updated_data.append(headers)  # Add updated header

    for row in reader:
        title_index = headers.index("title")
        tmdb_index = headers.index("tmdbId") if "tmdbId" in headers else -1

        title = row[title_index]
        tmdb_id = row[tmdb_index] if tmdb_index >= 0 and len(row) > tmdb_index else ""

        # Only fetch TMDB ID if it's missing
        if not tmdb_id:
            tmdb_id = get_tmdb_id(title)

        # Ensure row has the correct length (in case tmdbId is missing initially)
        if tmdb_index == -1:
            row.append(tmdb_id)
        else:
            row[tmdb_index] = tmdb_id

        updated_data.append(row)

# Write back to the same file
with open(csv_file_path, mode='w', newline='', encoding='utf-8') as outfile:
    writer = csv.writer(outfile, delimiter='\t')
    writer.writerows(updated_data)

print(f"Updated data saved to {csv_file_path}")
