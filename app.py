"""
Streamlit UI for the Finance News Intelligence Agent.
Tickertape-inspired aesthetic: information-dense, financial-data feel,
with a sentiment mood gauge and richer article cards.
"""

import streamlit as st
import plotly.graph_objects as go
from pathlib import Path

# ---------- Page config ----------
st.set_page_config(
    page_title="Finance News Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------- Custom styles ----------
from styles import CUSTOM_CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------- Ensure vector index exists ----------
CHROMA_PATH = Path(__file__).parent / "chroma_db"
if not CHROMA_PATH.exists() or not any(CHROMA_PATH.iterdir()):
    with st.spinner("First-time setup: building vector index..."):
        from build_index import main as build_index_main
        build_index_main()

from news_fetcher import fetch_news
from classifier import classify_news


# ---------- Helper: sentiment signal HTML ----------
def sentiment_signal_html(sentiment: str) -> str:
    sentiment = sentiment.lower()
    if sentiment == "bullish":
        return '<span class="sentiment-signal sentiment-bullish">▲ BULLISH</span>'
    elif sentiment == "bearish":
        return '<span class="sentiment-signal sentiment-bearish">▼ BEARISH</span>'
    else:
        return '<span class="sentiment-signal sentiment-neutral">● NEUTRAL</span>'


def meta_pill_html(label: str, value: str) -> str:
    return f'<span class="meta-pill">{label}: {value}</span>'


# ---------- Sentiment mood gauge (the showstopper) ----------
def render_mood_gauge(counts: dict) -> None:
    """
    Render a segmented proportional bar with prominent mood callout.
    
    Shows the bullish/bearish/neutral distribution as a horizontal bar,
    with a large mood label ("Mildly Bullish") and mood score (+40) 
    above it. More honest than a gauge for small-N categorical data.
    """
    total = sum(counts.values())
    if total == 0:
        return
    
    bullish = counts.get("bullish", 0)
    bearish = counts.get("bearish", 0)
    neutral = counts.get("neutral", 0)
    
    # Mood score from -100 (all bearish) to +100 (all bullish)
    net = bullish - bearish
    mood_score = int((net / total) * 100) if total > 0 else 0
    
    # Mood label tiers — calibrated to the data size
    # With 5 articles, a score of ±40 (2 of 5 leaning one way) is already meaningful
    if mood_score >= 60:
        mood_label = "Strongly Bullish"
        mood_color = "#059669"
    elif mood_score >= 20:
        mood_label = "Mildly Bullish"
        mood_color = "#059669"
    elif mood_score > -20:
        mood_label = "Neutral"
        mood_color = "#6B7280"
    elif mood_score > -60:
        mood_label = "Mildly Bearish"
        mood_color = "#DC2626"
    else:
        mood_label = "Strongly Bearish"
        mood_color = "#DC2626"
    
    # Percentages for the segmented bar
    pct_bullish = (bullish / total) * 100
    pct_neutral = (neutral / total) * 100
    pct_bearish = (bearish / total) * 100
    
    # Mood score format — always show sign
    score_display = f"{mood_score:+d}"
    
    # Assemble the whole visualization as one HTML block
    visualization_html = f'''
    <div style="
        padding: 1.25rem 0;
        text-align: center;
    ">
        <div style="
            font-family: 'Manrope', sans-serif;
            font-size: 1.5rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            color: {mood_color};
            margin-bottom: 0.25rem;
        ">{mood_label}</div>
        
        <div style="
            font-family: 'JetBrains Mono', monospace;
            font-size: 2.25rem;
            font-weight: 500;
            color: {mood_color};
            line-height: 1;
            margin-bottom: 0.25rem;
            font-variant-numeric: tabular-nums;
        ">{score_display}</div>
        
        <div style="
            font-family: 'Manrope', sans-serif;
            font-size: 0.7rem;
            font-weight: 600;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--text-tertiary);
            margin-bottom: 1.5rem;
        ">Mood Score</div>
        
        <div style="
            display: flex;
            width: 100%;
            height: 10px;
            border-radius: 999px;
            overflow: hidden;
            background-color: var(--border);
            margin-bottom: 0.75rem;
        ">
            <div style="
                width: {pct_bullish}%; 
                background: linear-gradient(90deg, #10b981, #059669);
                transition: width 0.4s ease;
            "></div>
            <div style="
                width: {pct_neutral}%; 
                background-color: #9CA3AF;
                transition: width 0.4s ease;
            "></div>
            <div style="
                width: {pct_bearish}%; 
                background: linear-gradient(90deg, #DC2626, #B91C1C);
                transition: width 0.4s ease;
            "></div>
        </div>
        
        <div style="
            display: flex;
            justify-content: space-between;
            font-family: 'Manrope', sans-serif;
            font-size: 0.75rem;
            color: var(--text-tertiary);
            font-weight: 500;
        ">
            <span style="color: #059669;">▲ {bullish} Bullish</span>
            <span>● {neutral} Neutral</span>
            <span style="color: #DC2626;">▼ {bearish} Bearish</span>
        </div>
    </div>
    '''
    
    # Strip leading whitespace from each line to prevent Streamlit 
    # from misinterpreting as a markdown code block
    visualization_html = "\n".join(
        line.lstrip() for line in visualization_html.split("\n")
    )
    st.markdown(visualization_html, unsafe_allow_html=True)


def render_article_card(item: dict, result: dict) -> None:
    sentiment = result.get("sentiment", "neutral")
    confidence = result.get("confidence", "medium")
    relevance = result.get("relevance", "medium")
    reasoning = result.get("reasoning", "")
    title = item.get("title", "Untitled")
    publisher = item.get("publisher", "Unknown")
    link = item.get("link", "")
    
    title_html = (
        f'<a href="{link}" target="_blank">{title}</a>'
        if link else title
    )
    
    card_html = f'''
    <div class="article-card">
        <div class="article-source">{publisher}</div>
        <div class="article-header">
            <div class="article-title">{title_html}</div>
            {sentiment_signal_html(sentiment)}
        </div>
        <div style="margin-top: 0.5rem;">
            {meta_pill_html("confidence", confidence)}
            {meta_pill_html("relevance", relevance)}
        </div>
        <div class="article-reasoning">{reasoning}</div>
    </div>
    '''
    st.markdown(card_html, unsafe_allow_html=True)
    
    # Precedents expander
    retrieved = result.get("retrieved", [])
    if retrieved:
        with st.expander(f"Retrieved {len(retrieved)} similar precedents from the RAG corpus"):
            st.markdown(
                '<div style="font-size: 0.75rem; color: var(--text-tertiary); '
                'margin-bottom: 0.5rem;">Semantic similarity search via Gemini embeddings + ChromaDB</div>',
                unsafe_allow_html=True
            )
            for r in retrieved:
                precedent_html = f'''
                <div class="precedent-card">
                    <div class="precedent-title">[{r['ticker']}] {r['title']}</div>
                    <div class="precedent-meta">
                        {sentiment_signal_html(r['expected_sentiment'])}
                        <span class="distance-mono">distance: {r['similarity_distance']:.3f}</span>
                    </div>
                    {f'<div class="precedent-notes">"{r["labeling_notes"]}"</div>' if r.get("labeling_notes") else ""}
                </div>
                '''
                st.markdown(precedent_html, unsafe_allow_html=True)


# ============================================================
# HEADER
# ============================================================

st.markdown('# Finance News Intelligence')
st.markdown(
    '<div class="subtitle">'
    'Real-time sentiment analysis of financial news, grounded in a RAG pipeline '
    'over hand-labeled precedents. Enter a ticker to see the market mood.'
    '</div>',
    unsafe_allow_html=True
)

# ---------- Input row ----------
col_input, col_button = st.columns([4, 1])
with col_input:
    ticker = st.text_input(
        "Ticker",
        placeholder="Enter a ticker  —  e.g., AAPL, TSLA, NVDA, JPM, BEN",
        label_visibility="collapsed"
    )
with col_button:
    analyze_clicked = st.button("Analyze", type="primary", use_container_width=True)

st.markdown(
    '<div style="color: var(--text-tertiary); font-size: 0.8rem; margin-top: -0.5rem;">'
    'Popular: AAPL · TSLA · NVDA · MSFT · JPM · BEN · META · BRK.B'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# ANALYSIS
# ============================================================

if analyze_clicked:
    st.write(f"DEBUG: button clicked, ticker value = '{ticker}'")
    if not ticker.strip():
        st.warning("Please enter a ticker.")
    else:
        ticker_clean = ticker.strip().upper()
        st.write(f"DEBUG: ticker cleaned to '{ticker_clean}', about to fetch news")
        
        with st.spinner(f"Fetching news for {ticker_clean}..."):
            try:
                news_items = fetch_news(ticker_clean, limit=5)
            except Exception as e:
                st.error(f"Could not fetch news for {ticker_clean}: {e}")
                news_items = []
        
        if not news_items:
            st.info(
                f"**No substantive news found for {ticker_clean} right now.**\n\n"
                f"This can happen when Yahoo Finance's feed for this ticker is sparse "
                f"or dominated by tangential coverage. The app uses a two-stage relevance "
                f"filter (keyword heuristic + LLM judgment) to surface only articles "
                f"genuinely about the company.\n\n"
                f"Try another ticker — **AAPL**, **TSLA**, **NVDA**, **MSFT**, **JPM**, "
                f"**BEN**, **META**, and **BRK.B** tend to return good coverage."
            )
        else:
            # Classify all articles
            results = []
            progress_placeholder = st.empty()
            for i, item in enumerate(news_items, 1):
                with progress_placeholder.container():
                    st.markdown(
                        f'<div style="color: var(--text-tertiary); font-size: 0.85rem;">'
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
                s = result.get("sentiment", "neutral").lower()
                counts[s] = counts.get(s, 0) + 1
            
            # ---------- Ticker header ----------
            st.markdown(
                f'<div class="ticker-header">'
                f'<div class="ticker-symbol">{ticker_clean}</div>'
                f'<div class="ticker-article-count">{len(results)} articles · just analyzed</div>'
                f'</div>',
                unsafe_allow_html=True
            )
            
            # ---------- Two-column layout: articles + mood gauge ----------
            col_articles, col_summary = st.columns([2, 1], gap="large")
            
            with col_summary:
                st.markdown(
                    '<div class="section-label">Market Mood</div>',
                    unsafe_allow_html=True
                )
                render_mood_gauge(counts)
                
                st.markdown('<div style="height: 1rem;"></div>', unsafe_allow_html=True)
                
                # Mini-metrics
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("Bullish", counts["bullish"])
                with c2:
                    st.metric("Neutral", counts["neutral"])
                with c3:
                    st.metric("Bearish", counts["bearish"])
            
            with col_articles:
                st.markdown(
                    '<div class="section-label">Recent Articles</div>',
                    unsafe_allow_html=True
                )
                for item, result in results:
                    render_article_card(item, result)


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    '''
    <div style="color: var(--text-tertiary); font-size: 0.75rem; 
                margin-top: 5rem; padding-top: 2rem; 
                border-top: 1px solid var(--border); text-align: center; line-height: 1.8;">
        Built by <strong>Prashanth Vutala</strong><br/>
        Gemini · ChromaDB · yfinance · Streamlit<br/>
        <a href="https://github.com/vutala0/finance-news-agent" 
           style="color: var(--accent-blue); text-decoration: none;">
           View source on GitHub →
        </a>
    </div>
    ''',
    unsafe_allow_html=True
)