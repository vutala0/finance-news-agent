"""
Streamlit UI for the Finance News Intelligence Agent.

Clean, minimal, card-based interface. Theme-aware light/dark mode.
Visualizes the RAG retrieval alongside each article's classification.
"""

import streamlit as st
from pathlib import Path

# ---------- Page config (must be first Streamlit call) ----------
st.set_page_config(
    page_title="Finance News Intelligence Agent",
    page_icon="📰",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ---------- Custom styles ----------
from styles import CUSTOM_CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------- Ensure vector index exists (for fresh deployments) ----------
CHROMA_PATH = Path(__file__).parent / "chroma_db"
if not CHROMA_PATH.exists() or not any(CHROMA_PATH.iterdir()):
    with st.spinner("First-time setup: building vector index..."):
        from build_index import main as build_index_main
        build_index_main()

# ---------- Imports that depend on the index ----------
from news_fetcher import fetch_news
from classifier import classify_news


# ---------- Helper: HTML badge rendering ----------
def sentiment_badge_html(sentiment: str) -> str:
    sentiment = sentiment.lower()
    klass = {
        "bullish": "badge badge-bullish",
        "bearish": "badge badge-bearish",
        "neutral": "badge badge-neutral",
    }.get(sentiment, "badge")
    return f'<span class="{klass}">{sentiment}</span>'


def pill_html(text: str) -> str:
    return f'<span class="badge-pill">{text}</span>'


def sentiment_distribution_bar_html(counts: dict) -> str:
    total = sum(counts.values())
    if total == 0:
        return '<div class="sentiment-bar-container"></div>'
    
    pct_bullish = (counts.get("bullish", 0) / total) * 100
    pct_bearish = (counts.get("bearish", 0) / total) * 100
    pct_neutral = (counts.get("neutral", 0) / total) * 100
    
    return f'''
    <div class="sentiment-bar-container">
        <div class="sentiment-bar-segment seg-bullish" style="width: {pct_bullish}%;"></div>
        <div class="sentiment-bar-segment seg-neutral" style="width: {pct_neutral}%;"></div>
        <div class="sentiment-bar-segment seg-bearish" style="width: {pct_bearish}%;"></div>
    </div>
    '''


def render_article_card(idx: int, item: dict, result: dict) -> None:
    """Render a single article card with classification and precedents expander."""
    
    sentiment = result.get("sentiment", "neutral")
    confidence = result.get("confidence", "medium")
    relevance = result.get("relevance", "medium")
    reasoning = result.get("reasoning", "")
    title = item.get("title", "Untitled")
    publisher = item.get("publisher", "Unknown")
    link = item.get("link", "")
    
    # Card markup
    badges = (
        sentiment_badge_html(sentiment) +
        pill_html(f"conf: {confidence}") +
        pill_html(f"rel: {relevance}")
    )
    
    title_html = f'<a href="{link}" target="_blank" style="color: inherit; text-decoration: none;">{title}</a>' if link else title
    
    card_html = f'''
    <div class="article-card">
        <div class="article-title">{title_html}</div>
        <div class="article-source">{publisher}</div>
        <div>{badges}</div>
        <div class="article-reasoning">{reasoning}</div>
    </div>
    '''
    st.markdown(card_html, unsafe_allow_html=True)
    
    # Precedents expander
    retrieved = result.get("retrieved", [])
    if retrieved:
        with st.expander(f"View the {len(retrieved)} similar precedents used"):
            st.markdown(
                '<div class="section-label">Retrieved via semantic similarity (ChromaDB + Gemini embeddings)</div>',
                unsafe_allow_html=True
            )
            for r in retrieved:
                precedent_html = f'''
                <div class="precedent-card">
                    <div class="precedent-title">[{r['ticker']}] {r['title']}</div>
                    <div class="precedent-meta">
                        {sentiment_badge_html(r['expected_sentiment'])}
                        {pill_html(f"rel: {r['expected_relevance']}")}
                        <span class="distance-mono">distance: {r['similarity_distance']:.3f}</span>
                    </div>
                    {f'<div class="precedent-notes">{r["labeling_notes"]}</div>' if r.get("labeling_notes") else ""}
                </div>
                '''
                st.markdown(precedent_html, unsafe_allow_html=True)


# ============================================================
# Main UI
# ============================================================

# ---------- Header ----------
st.markdown("# Finance News Intelligence")
st.markdown(
    '<div class="subtitle">AI-powered sentiment analysis of recent financial news, '
    'grounded in a RAG pipeline over hand-labeled precedents.</div>',
    unsafe_allow_html=True
)

# ---------- Input section ----------
col_input, col_button = st.columns([4, 1])
with col_input:
    ticker = st.text_input(
        "Stock ticker",
        placeholder="AAPL, TSLA, NVDA, JPM, BEN",
        label_visibility="collapsed"
    )
with col_button:
    analyze_clicked = st.button("Analyze", type="primary", use_container_width=True)

st.markdown(
    '<div style="color: var(--muted-text); font-size: 0.8rem; margin-top: -0.5rem;">'
    'Try: AAPL · TSLA · NVDA · JPM · BEN'
    '</div>',
    unsafe_allow_html=True
)


# ---------- Analysis ----------
if analyze_clicked:
    if not ticker.strip():
        st.warning("Please enter a ticker.")
    else:
        ticker_clean = ticker.strip().upper()
        
        # Fetch news
        with st.spinner(f"Fetching news for {ticker_clean}..."):
            try:
                news_items = fetch_news(ticker_clean, limit=5)
            except Exception as e:
                st.error(f"Could not fetch news for {ticker_clean}: {e}")
                news_items = []
        
        if not news_items:
    st.info(
        f"**No substantive news found for {ticker_clean} right now.**\n\n"
        f"This can happen when Yahoo Finance's feed for this ticker is "
        f"sparse or dominated by tangential coverage. The app uses a two-stage "
        f"relevance filter (keyword heuristic + LLM judgment) to surface only "
        f"articles genuinely about the company.\n\n"
        f"Try another ticker — **AAPL**, **TSLA**, **NVDA**, **MSFT**, **JPM**, "
        f"**BEN**, **META**, and **BRK.B** tend to return good coverage."
    )
        else:
            # Classify all articles (collect results before rendering so we can 
            # compute the summary bar at the top)
            results = []
            progress_placeholder = st.empty()
            for i, item in enumerate(news_items, 1):
                with progress_placeholder.container():
                    st.markdown(
                        f'<div style="color: var(--muted-text); font-size: 0.85rem;">'
                        f'Analyzing article {i} of {len(news_items)}...</div>',
                        unsafe_allow_html=True
                    )
                try:
                    result = classify_news(
                        title=item["title"],
                        summary=item["summary"],
                        ticker=ticker_clean
                    )
                    results.append((item, result))
                except Exception as e:
                    st.error(f"Classification failed for article {i}: {e}")
            progress_placeholder.empty()
            
            # Compute sentiment distribution
            counts = {"bullish": 0, "bearish": 0, "neutral": 0}
            for _, result in results:
                counts[result.get("sentiment", "neutral").lower()] = (
                    counts.get(result.get("sentiment", "neutral").lower(), 0) + 1
                )
            
            # ---------- Summary section ----------
            st.markdown(
                f'<div class="section-label">Summary — {ticker_clean}</div>',
                unsafe_allow_html=True
            )
            
            # Sentiment distribution bar
            st.markdown(
                sentiment_distribution_bar_html(counts),
                unsafe_allow_html=True
            )
            
            # Count metrics
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Bullish", counts["bullish"])
            with c2:
                st.metric("Neutral", counts["neutral"])
            with c3:
                st.metric("Bearish", counts["bearish"])
            
            # ---------- Articles ----------
            st.markdown(
                '<div class="section-label">Articles</div>',
                unsafe_allow_html=True
            )
            
            for i, (item, result) in enumerate(results, 1):
                render_article_card(i, item, result)


# ---------- Footer ----------
st.markdown(
    '''
    <div style="color: var(--muted-text); font-size: 0.75rem; 
                margin-top: 4rem; text-align: center; line-height: 1.6;">
        Built by Prashanth Vutala &middot; 
        Gemini · ChromaDB · yfinance &middot; 
        <a href="https://github.com/vutala0/finance-news-agent" 
           style="color: var(--muted-text); text-decoration: underline;">
           Source code
        </a>
    </div>
    ''',
    unsafe_allow_html=True
)