import os
import time
import pandas as pd
import openai
from tqdm import tqdm

# —— Configuration —— #

# Path to your input and output files
INPUT_CSV  = "nMovies.csv"
OUTPUT_CSV = "enriched_movies_with_descriptions_filled.csv"

# OpenAI settings
MODEL        = "gpt-4"       # or "gpt-3.5-turbo"
MAX_TOKENS   = 60
TEMPERATURE  = 0.7
RETRY_DELAY  = 5             # seconds between retries on rate-limit

# —— End configuration —— #

def get_api_key():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("Please set the OPENAI_API_KEY environment variable.")
    return key

def generate_description(title: str) -> str:
    prompt = (
        f"Provide a concise, engaging, and informative movie description "
        f"for the film titled \"{title}\". No more than 2–3 sentences."
    )
    for attempt in range(5):
        try:
            resp = openai.ChatCompletion.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user",   "content": prompt}
                ],
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
            )
            return resp.choices[0].message.content.strip()
        except openai.error.RateLimitError:
            print(f"Rate limit hit; retrying in {RETRY_DELAY}s…")
            time.sleep(RETRY_DELAY)
    raise RuntimeError("Failed to generate description after multiple retries.")

def main():
    # Initialize API key
    openai.api_key = get_api_key()

    # Load data
    df = pd.read_csv(INPUT_CSV)
    if 'title' not in df.columns or 'description' not in df.columns:
        raise RuntimeError("CSV must have 'title' and 'description' columns.")

    # Find missing descriptions
    mask = df['description'].isna() | (df['description'].str.strip() == "")
    missing_count = mask.sum()
    print(f"Found {missing_count} movies without descriptions.")

    if missing_count == 0:
        print("No missing descriptions—nothing to do.")
        return

    # Generate descriptions
    for idx in tqdm(df[mask].index, desc="Generating descriptions"):
        title = df.at[idx, 'title']
        try:
            df.at[idx, 'description'] = generate_description(title)
        except Exception as e:
            print(f"Error on '{title}': {e}")
            df.at[idx, 'description'] = ""  # leave blank on failure

    # Save results
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"All done! Filled CSV saved to: {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
