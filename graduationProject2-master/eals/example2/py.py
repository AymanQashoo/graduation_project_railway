import os
import json

# Define file paths
BASE_DIR = os.path.dirname(__file__)
first_file = os.path.join(BASE_DIR, "23.jsonl")
second_file = os.path.join(BASE_DIR, "items.jsonl")
updated_file = os.path.join(BASE_DIR, "updated_items.jsonl")

# Load first file into a dictionary {parent_asin: title}
first_data = {}
with open(first_file, "r", encoding="utf-8") as f1:
    for line in f1:
        try:
            data = json.loads(line.strip())
            if "parent_asin" in data and "title" in data:
                first_data[data["parent_asin"]] = data["title"]
        except json.JSONDecodeError:
            print("Skipping invalid JSON:", line.strip())

# Process second file and update missing titles
updated_records = []
with open(second_file, "r", encoding="utf-8") as f2:
    for line in f2:
        try:
            item = json.loads(line.strip())

            # Check if asin matches any parent_asin from first
            if "asin" in item and item["asin"] in first_data:
                if "title" not in item or not item["title"].strip():
                    item["title"] = first_data[item["asin"]]  # Add title

            updated_records.append(item)

        except json.JSONDecodeError:
            print("Skipping invalid JSON:", line.strip())

# Save the updated records
with open(updated_file, "w", encoding="utf-8") as f3:
    for record in updated_records:
        f3.write(json.dumps(record) + "\n")

print(f"Updated file saved as: {updated_file}")
