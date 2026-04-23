"""
Streamlit UI for the Finance News Intelligence Agent.

Live demo of the RAG-based classification pipeline:
- User enters a ticker
- System fetches recent news from Yahoo Finance
- Each article is classified using Gemini + retrieved precedents
- Results displayed with color-coded sentiment, confidence, reasoning,
  and a collapsible view of the retrieved similar past items
"""

import streamlit as st
from news_fetcher import fetch_news
from classifier import classify_news


# ---------- Page config ----------
st.set_page_config(
    page_title="Finance News Intelligence Agent",
    page_icon="📈",
    layout="wide"
)


# ---------- Header ----------
st.title("📈 Finance News Intelligence Agent")

st.markdown(
    "An AI-powered tool that analyzes recent financial news for a given stock ticker "
    "and classifies each article by its likely impact on the stock price. "
    "Uses a Retrieval-Augmented Generation (RAG) pipeline over a hand-labeled "
    "corpus of precedent articles."
)

st.markdown(
    "**How it works:** Enter a stock ticker → the system fetches recent news from "
    "Yahoo Finance → each article is embedded and compared to a corpus of labeled "
    "precedents → Gemini classifies each article using the retrieved precedents as "
    "reasoning anchors."
)

st.divider()


# ---------- Input ----------
col_input, col_button = st.columns([3, 1])

with col_input:
    ticker = st.text_input(
        "Enter a stock ticker",
        placeholder="e.g. AAPL, TSLA, NVDA, JPM, BEN",
        label_visibility="collapsed"
    )

with col_button:
    analyze_clicked = st.button("Analyze", type="primary", use_container_width=True)


# ---------- Example tickers ----------
st.caption(
    "Try: **AAPL** (Apple) · **TSLA** (Tesla) · **NVDA** (Nvidia) · "
    "**JPM** (JPMorgan) · **BEN** (Franklin Templeton)"
)


# ---------- Sentiment badge styling ----------
def sentiment_badge(sentiment: str) -> str:
    """Return a colored HTML badge for a sentiment label."""
    sentiment = sentiment.lower()
    colors = {
        "bullish": ("#065f46", "#d1fae5"),     # dark green on light green
        "bearish": ("#991b1b", "#fee2e2"),     # dark red on light red
        "neutral": ("#92400e", "#fef3c7"),     # dark amber on light amber
    }
    fg, bg = colors.get(sentiment, ("#374151", "#f3f4f6"))
    return (
        f'<span style="background-color:{bg};color:{fg};padding:2px 10px;'
        f'border-radius:12px;font-weight:600;font-size:0.85em;">'
        f'{sentiment.upper()}</span>'
    )


def relevance_badge(relevance: str) -> str:
    relevance = relevance.lower()
    colors = {
        "high": ("#1e3a8a", "#dbeafe"),
        "medium": ("#78350f", "#fef3c7"),
        "low": ("#374151", "#f3f4f6"),
    }
    fg, bg = colors.get(relevance, ("#374151", "#f3f4f6"))
    return (
        f'<span style="background-color:{bg};color:{fg};padding:2px 10px;'
        f'border-radius:12px;font-weight:500;font-size:0.85em;">'
        f'relevance: {relevance}</span>'
    )


def confidence_badge(confidence: str) -> str:
    return (
        f'<span style="color:#6b7280;font-size:0.85em;">'
        f'confidence: {confidence}</span>'
    )


# ---------- Analysis ----------
if analyze_clicked:
    if not ticker:
        st.warning("Please enter a ticker.")
    else:
        ticker_clean = ticker.strip().upper()
        
        with st.spinner(f"Fetching news for {ticker_clean}..."):
            try:
                news_items = fetch_news(ticker_clean, limit=5)
            except Exception as e:
                st.error(f"Could not fetch news for {ticker_clean}: {e}")
                news_items = []
        
        if not news_items:
            st.warning(f"No recent news found for {ticker_clean}. Try a different ticker.")
        else:
            st.success(f"Found {len(news_items)} recent news items for {ticker_clean}.")
            st.divider()
            
            # Track sentiment counts for the summary
            sentiment_counts = {"bullish": 0, "bearish": 0, "neutral": 0}
            
            # Classify each article
            for i, item in enumerate(news_items, 1):
                with st.spinner(f"Analyzing article {i} of {len(news_items)}..."):
                    try:
                        result = classify_news(
                            title=item["title"],
                            summary=item["summary"],
                            ticker=ticker_clean
                        )
                    except Exception as e:
                        st.error(f"Classification failed for article {i}: {e}")
                        continue
                
                # Display the article
                st.subheader(f"Article {i}: {item['title']}")
                
                # Badges row
                st.markdown(
                    sentiment_badge(result["sentiment"]) + "  " +
                    relevance_badge(result.get("relevance", "unknown")) + "  " +
                    confidence_badge(result["confidence"]),
                    unsafe_allow_html=True
                )
                
                # Metadata
                st.caption(f"Source: {item['publisher']}")
                
                # Article summary
                if item["summary"]:
                    st.markdown(f"_{item['summary'][:300]}..._")
                
                # AI reasoning
                st.markdown(f"**AI reasoning:** {result['reasoning']}")
                
                # Retrieved precedents (the RAG showstopper)
                retrieved = result.get("retrieved", [])
                if retrieved:
                    with st.expander(
                        f"🔍 See the {len(retrieved)} similar past articles "
                        f"the model used as precedents"
                    ):
                        st.caption(
                            "These articles were retrieved from a hand-labeled corpus "
                            "using semantic similarity search (vector embeddings via "
                            "Google's gemini-embedding-001, stored in ChromaDB). "
                            "The classifier used them as reasoning anchors."
                        )
                        for j, r in enumerate(retrieved, 1):
                            st.markdown(
                                f"**{j}. [{r['ticker']}] {r['title']}** "
                                f"(distance: {r['similarity_distance']:.3f})"
                            )
                            st.markdown(
                                f"{sentiment_badge(r['expected_sentiment'])}  "
                                f"{relevance_badge(r['expected_relevance'])}",
                                unsafe_allow_html=True
                            )
                            if r.get("labeling_notes"):
                                st.caption(f"Labeled because: {r['labeling_notes']}")
                            st.markdown("---")
                
                # Count for summary
                sentiment_counts[result["sentiment"].lower()] = (
                    sentiment_counts.get(result["sentiment"].lower(), 0) + 1
                )
                
                st.divider()
            
            # ---------- Summary ----------
            st.header(f"Summary for {ticker_clean}")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Bullish articles", sentiment_counts.get("bullish", 0))
            with col2:
                st.metric("Bearish articles", sentiment_counts.get("bearish", 0))
            with col3:
                st.metric("Neutral articles", sentiment_counts.get("neutral", 0))


# ---------- Footer ----------
st.divider()
st.caption(
    "Built by Prashanth Vutala. Powered by Google Gemini, ChromaDB, and yfinance. "
    "This is a demonstration project — not investment advice. "
    "[Source code on GitHub](https://github.com/vutala0/finance-news-agent)"
)