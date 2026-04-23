"""
Build a ChromaDB index from the golden set.

Each news item in the golden set gets:
1. Embedded using Google's text-embedding-004 model
2. Stored in ChromaDB with its metadata (ticker, sentiment, relevance, etc.)

Run this once to create the index. Re-run whenever the golden set changes.

Usage:
    python build_index.py
"""

import json
import os
import time

import chromadb
from chromadb.config import Settings
from google import genai
from dotenv import load_dotenv


load_dotenv()

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GOLDEN_SET_PATH = os.path.join(SCRIPT_DIR, "data", "golden_set.json")
CHROMA_PATH = os.path.join(SCRIPT_DIR, "chroma_db")
COLLECTION_NAME = "golden_set"

EMBEDDING_MODEL = "gemini-embedding-001"

# Initialize the Gemini client (for embeddings)
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env")

client = genai.Client(api_key=api_key)


def embed_text(text: str) -> list[float]:
    """
    Generate an embedding vector for a piece of text.
    
    Returns a list of ~768 floats representing the semantic meaning of the text.
    """
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text
    )
    return response.embeddings[0].values


def build_searchable_text(item: dict) -> str:
    """
    Combine ticker, title, and summary into a single text string for embedding.
    
    Design decision: we include the ticker explicitly so that articles about 
    different companies embed differently even if the titles look similar.
    """
    return f"[{item['ticker']}] {item['title']}\n\n{item['summary']}"


def main():
    # Load the golden set
    with open(GOLDEN_SET_PATH, "r", encoding="utf-8") as f:
        items = json.load(f)
    print(f"Loaded {len(items)} items from golden set\n")
    
    # Filter out any unlabeled items
    labeled = [
        item for item in items
        if item.get("expected_sentiment") not in ("FILL_ME_IN", "", None)
    ]
    print(f"{len(labeled)} items are labeled and will be indexed\n")
    
    # Initialize ChromaDB client
    # PersistentClient means data is written to disk (not just in-memory)
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    
    # Delete existing collection if it exists (clean rebuild every time)
    # This is the simplest pattern while we're iterating. In production you'd
    # do incremental updates instead of full rebuilds.
    existing = [c.name for c in chroma_client.list_collections()]
    if COLLECTION_NAME in existing:
        print(f"Deleting existing '{COLLECTION_NAME}' collection...\n")
        chroma_client.delete_collection(COLLECTION_NAME)
    
    collection = chroma_client.create_collection(name=COLLECTION_NAME)
    
    # Embed and index each item
    for i, item in enumerate(labeled, 1):
        text = build_searchable_text(item)
        print(f"[{i}/{len(labeled)}] Embedding: {item['title'][:60]}...")
        
        # Gently pace our calls — embedding API has its own rate limits
        if i > 1:
            time.sleep(0.5)
        
        embedding = embed_text(text)
        
        # ChromaDB needs a unique ID per item. We use the title (truncated) 
        # as a semi-human-readable ID. Good enough for our use case.
        item_id = f"{item['ticker']}_{item['title'][:40]}".replace(" ", "_")
        
        collection.add(
            ids=[item_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[{
                "ticker": item["ticker"],
                "title": item["title"],
                "summary": item["summary"],
                "expected_sentiment": item["expected_sentiment"],
                "expected_relevance": item["expected_relevance"],
                "labeling_notes": item.get("labeling_notes", "")
            }]
        )
    
    # Verify
    count = collection.count()
    print(f"\n✓ Index built successfully. {count} items stored in ChromaDB.")
    print(f"  Location: {CHROMA_PATH}")
    print(f"  Collection: {COLLECTION_NAME}")


if __name__ == "__main__":
    main()