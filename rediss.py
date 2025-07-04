import os
import pandas as pd
import numpy as np
from typing import Optional
from sentence_transformers import SentenceTransformer
from docarray import BaseDoc, DocList
import redis
from docarray.typing import NdArray

# ---------- Config ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, "filtered_outputm.tsv")

# ---------- Load TSV File ----------
df = pd.read_csv(FILE_PATH, sep="\t")
df.dropna(subset=["ProductId", "title"], inplace=True)
df["ProductId"] = df["ProductId"].astype(int)
df["title"] = df["title"].astype(str)

print("📄 Loaded data:")
print(df.head())
print(df.dtypes)

# ---------- Raw Redis Connection ----------
r = redis.Redis(
    host='redis-10187.c228.us-central1-1.gce.redns.redis-cloud.com',
    port=10187,
    decode_responses=True,
    username="default",
    password="z5YF6AkEmV7Ousk3iyzPMkRx0PwAxcTa",
)

print("🌐 Redis connection test:")
try:
    r.set("test_key_connection", "ok")
    print("✅ Redis connected")
    print("🔍 Modules loaded:", r.execute_command("MODULE LIST"))
except Exception as e:
    print("❌ Redis connection failed:", e)
    exit()

# ---------- Schema ----------
class MovieDoc(BaseDoc):
    id: str
    title: str
    embedding: NdArray[512]

# ---------- Load Model ----------
print("⚡ Loading local CLIP model...")
model = SentenceTransformer("clip-ViT-B-32")

# ---------- Generate Embeddings ----------
print("⚙️ Generating embeddings...")
titles = df["title"].tolist()
embeddings = model.encode(titles, show_progress_bar=True)
embeddings = np.array(embeddings, dtype=np.float32)

# ---------- Build DocList ----------
docs = DocList[MovieDoc]([
    MovieDoc(
        id=str(row["ProductId"]),
        title=str(row["title"]),
        embedding=embeddings[idx]
    )
    for idx, (_, row) in enumerate(df.iterrows())
])

print(f"📦 Prepared {len(docs)} documents")

# ---------- Save All Docs in One Redis Key ----------
try:
    serialized = docs.to_json()
    r.set("all_movie_docs", serialized)
    print(f"✅ Saved all {len(docs)} docs into Redis key 'all_movie_docs'")
except Exception as e:
    print("❌ Saving to Redis failed:", e)
    exit()

# ---------- Optional: Load Back for Verification ----------
try:
    raw = r.get("all_movie_docs")
    loaded_docs = DocList[MovieDoc].from_json(raw)
    print(f"📥 Successfully loaded {len(loaded_docs)} docs from Redis")

    # Print a sample
    for doc in loaded_docs[:3]:
        print(f"🧾 ID: {doc.id}, Title: {doc.title}")
except Exception as e:
    print("❌ Loading from Redis failed:", e)
  