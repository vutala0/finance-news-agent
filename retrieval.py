"""
Retrieves similar past news items from the ChromaDB vector index.

Given a query article (new news to classify), returns the top-K most 
semantically similar items from the golden set, along with their labels.

This is the core retrieval module of our RAG pipeline.
"""

import os
import chromadb
from google import genai
from dotenv import load_dotenv


load_dotenv()

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_PATH = os.path.join(SCRIPT_DIR, "chroma_db")
COLLECTION_NAME = "golden_set"
EMBEDDING_MODEL = "gemini-embedding-001"

# Initialize clients once at module load time (efficient — reused across calls)
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env")

_genai_client = genai.Client(api_key=api_key)
_chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
_collection = _chroma_client.get_collection(name=COLLECTION_NAME)


def _embed_query(text: str) -> list[float]:
    """Embed a piece of text for querying the vector DB."""
    response = _genai_client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text
    )
    return response.embeddings[0].values


def _build_query_text(title: str, summary: str, ticker: str) -> str:
    """
    Build the text string used for embedding the query.
    
    Must match the format used during indexing (see build_index.py's 
    build_searchable_text function) — otherwise the embeddings live in 
    different semantic spaces and retrieval quality degrades.
    """
    return f"[{ticker}] {title}\n\n{summary}"


def retrieve_similar(
    title: str,
    summary: str,
    ticker: str,
    k: int = 3,
    exclude_self: bool = True
) -> list[dict]:
    """
    Retrieve the top-K most similar past items from the vector DB.
    
    Args:
        title: Title of the article being classified
        summary: Summary of the article being classified
        ticker: Stock ticker of the article being classified
        k: Number of similar items to retrieve
        exclude_self: If True, exclude any retrieved item whose title matches 
          the query's title (prevents retrieving the same article as its 
          own "similar" example — real data-leakage protection during eval)
    
    Returns:
        A list of dicts, each representing a retrieved item. Each dict has:
          - ticker, title, summary
          - expected_sentiment, expected_relevance
          - labeling_notes
          - similarity_distance (lower = more similar)
    """
    query_text = _build_query_text(title, summary, ticker)
    query_vector = _embed_query(query_text)
    
    # Fetch more than k so we can filter out self-matches and still have k left
    fetch_count = k + 5 if exclude_self else k
    
    results = _collection.query(
        query_embeddings=[query_vector],
        n_results=fetch_count
    )
    
    retrieved = []
    for i in range(len(results["ids"][0])):
        metadata = results["metadatas"][0][i]
        distance = results["distances"][0][i]
        
        # Skip self-matches (when the query item is itself in the corpus)
        if exclude_self and metadata.get("title", "") == title:
            continue
        
        retrieved.append({
            "ticker": metadata.get("ticker", ""),
            "title": metadata.get("title", ""),
            "summary": metadata.get("summary", ""),
            "expected_sentiment": metadata.get("expected_sentiment", ""),
            "expected_relevance": metadata.get("expected_relevance", ""),
            "labeling_notes": metadata.get("labeling_notes", ""),
            "similarity_distance": distance,
        })
        
        if len(retrieved) >= k:
            break
    
    return retrieved


def format_retrieved_for_prompt(retrieved: list[dict]) -> str:
    """
    Format the retrieved items as a string block suitable for inclusion 
    in the classification prompt.
    """
    if not retrieved:
        return "(No similar past items found in the corpus.)"
    
    formatted = []
    for i, item in enumerate(retrieved, 1):
        reasoning = item.get("labeling_notes") or f"Labeled as {item['expected_sentiment']}."
        formatted.append(
            f"Similar past item {i} (distance: {item['similarity_distance']:.3f}):\n"
            f"  Ticker: {item['ticker']}\n"
            f"  Title: {item['title']}\n"
            f"  Summary: {item['summary']}\n"
            f"  Correct classification: sentiment={item['expected_sentiment']}, "
            f"relevance={item['expected_relevance']}\n"
            f"  Reasoning: {reasoning}\n"
        )
    return "\n".join(formatted)


if __name__ == "__main__":
    # Quick test — retrieve similar items for a sample article
    print("Testing retrieval with a sample query...\n")
    
    sample_title = "Tesla reports record Q4 revenue driven by EV demand"
    sample_summary = "Tesla beat Wall Street expectations with record quarterly revenue..."
    sample_ticker = "TSLA"
    
    print(f"Query: {sample_title}\n")
    print(f"Finding top 3 most similar items in the corpus...\n")
    
    results = retrieve_similar(
        title=sample_title,
        summary=sample_summary,
        ticker=sample_ticker,
        k=3
    )
    
    print(f"Retrieved {len(results)} similar items:\n")
    print(format_retrieved_for_prompt(results))