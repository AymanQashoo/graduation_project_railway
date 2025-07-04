import pandas as pd
import random
import os

# Debug info
cwd = os.getcwd()
print("📂 Current Working Directory:", cwd)

# Load your TSV file
try:
    df = pd.read_csv("filtered_outputm.tsv", sep="\t")
except FileNotFoundError:
    print("❌ 'filtered_output.tsv' not found in the current directory.")
    exit()

# ✅ Keep only unique 'title' rows
df = df.drop_duplicates(subset="title", keep="first")

# Add 'user_id' column
df["user_id"] = [f"{random.randint(1000, 1300)}" for _ in range(len(df))]

# Move 'user_id' to the first column
df = df[["user_id"] + [col for col in df.columns if col != "user_id"]]

# Save with absolute path to ensure visibility
output_path = os.path.join(cwd, "updated_file.tsv")

try:
    df.to_csv(output_path, sep="\t", index=False)
    if os.path.exists(output_path):
        print(f"✅ File saved successfully at:\n   {output_path}")
    else:
        print("❌ File write operation ran but file is not found.")
except Exception as e:
    print("❌ Error saving file:", e)
