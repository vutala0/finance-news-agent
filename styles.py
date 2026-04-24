"""
Custom CSS for the Finance News Intelligence Agent.
Aesthetic: Tickertape-inspired — financial-data dense, informational, 
with blue accent and green/red sentiment signaling.
"""

CUSTOM_CSS = """
<style>
/* ---------- Font import ---------- */
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

/* ---------- Base typography ---------- */
html, body, [class*="css"], .stMarkdown, .stText {
    font-family: 'Manrope', -apple-system, sans-serif !important;
}

/* Numbers in metrics — tabular monospace */
.stMetric [data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 600 !important;
    font-variant-numeric: tabular-nums;
}

.stMetric [data-testid="stMetricLabel"] {
    font-size: 0.7rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    color: #6b7280 !important;
}

/* ---------- Theme-aware color variables ---------- */
:root {
    --accent-blue: #0066CC;
    --accent-blue-hover: #004C99;
    --bullish: #059669;
    --bullish-bg: #d1fae5;
    --bearish: #DC2626;
    --bearish-bg: #fee2e2;
    --neutral: #6B7280;
    --neutral-bg: #f3f4f6;
    --bg-canvas: #FAFBFC;
    --bg-card: #FFFFFF;
    --text-primary: #111827;
    --text-secondary: #6B7280;
    --text-tertiary: #9CA3AF;
    --border: #E5E7EB;
    --shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
    --shadow-md: 0 2px 8px rgba(0, 0, 0, 0.06);
}

@media (prefers-color-scheme: dark) {
    :root {
        --bg-canvas: #0B0D0F;
        --bg-card: #16181C;
        --text-primary: #F3F4F6;
        --text-secondary: #9CA3AF;
        --text-tertiary: #6B7280;
        --border: #2A2D33;
        --bullish-bg: rgba(5, 150, 105, 0.15);
        --bearish-bg: rgba(220, 38, 38, 0.15);
        --neutral-bg: rgba(107, 114, 128, 0.15);
        --shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
        --shadow-md: 0 2px 12px rgba(0, 0, 0, 0.4);
    }
}

/* ---------- Page layout ---------- */
.block-container {
    max-width: 1100px !important;
    padding-top: 2rem !important;
    padding-bottom: 4rem !important;
}

/* Remove Streamlit chrome */
[data-testid="stSidebar"] { display: none; }
div[data-testid="stToolbar"] { visibility: hidden; }
footer { visibility: hidden; }
header[data-testid="stHeader"] { display: none; }

/* ---------- Typography ---------- */
h1 {
    font-family: 'Manrope', sans-serif !important;
    font-weight: 800 !important;
    letter-spacing: -0.025em !important;
    font-size: 1.75rem !important;
    margin-bottom: 0.25rem !important;
    color: var(--text-primary) !important;
}

h2, h3 {
    font-family: 'Manrope', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.015em !important;
}

.subtitle {
    color: var(--text-secondary);
    font-size: 0.95rem;
    margin-bottom: 2rem;
    line-height: 1.5;
}

.section-label {
    color: var(--text-secondary);
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 0.75rem;
    margin-top: 1.5rem;
}

/* ---------- Input + button ---------- */
.stTextInput > div > div > input {
    font-family: 'Manrope', sans-serif !important;
    font-size: 1rem !important;
    font-weight: 500 !important;
    border-radius: 8px !important;
    border: 1.5px solid var(--border) !important;
    padding: 0.6rem 1rem !important;
    height: 48px !important;
}

.stTextInput > div > div > input:focus {
    border-color: var(--accent-blue) !important;
    box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.1) !important;
}

.stButton > button {
    font-family: 'Manrope', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    height: 48px !important;
    font-size: 0.95rem !important;
    background-color: var(--accent-blue) !important;
    border: none !important;
    color: white !important;
    transition: background-color 0.15s ease !important;
}

.stButton > button:hover {
    background-color: var(--accent-blue-hover) !important;
}

/* ---------- Article card styling ---------- */
.article-card {
    background-color: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.25rem 1.5rem;
    box-shadow: var(--shadow);
    margin-bottom: 0.75rem;
    transition: box-shadow 0.15s ease, border-color 0.15s ease;
}

.article-card:hover {
    box-shadow: var(--shadow-md);
    border-color: var(--accent-blue);
}

.article-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 1rem;
    margin-bottom: 0.5rem;
}

.article-title {
    font-weight: 600;
    font-size: 0.98rem;
    line-height: 1.4;
    color: var(--text-primary);
    flex: 1;
}

.article-title a {
    color: inherit;
    text-decoration: none;
}

.article-title a:hover {
    color: var(--accent-blue);
}

.article-source {
    color: var(--text-tertiary);
    font-size: 0.75rem;
    font-weight: 500;
    letter-spacing: 0.02em;
    text-transform: uppercase;
    margin-bottom: 0.75rem;
}

.article-reasoning {
    color: var(--text-secondary);
    font-size: 0.875rem;
    line-height: 1.55;
    margin-top: 0.75rem;
    padding-top: 0.75rem;
    border-top: 1px dashed var(--border);
}

/* ---------- Sentiment signal (big, prominent) ---------- */
.sentiment-signal {
    font-family: 'JetBrains Mono', monospace;
    font-weight: 600;
    font-size: 0.85rem;
    padding: 4px 12px;
    border-radius: 999px;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    white-space: nowrap;
}

.sentiment-bullish {
    color: var(--bullish);
    background-color: var(--bullish-bg);
}

.sentiment-bearish {
    color: var(--bearish);
    background-color: var(--bearish-bg);
}

.sentiment-neutral {
    color: var(--neutral);
    background-color: var(--neutral-bg);
}

.meta-pill {
    font-size: 0.72rem;
    color: var(--text-tertiary);
    padding: 2px 8px;
    background-color: var(--neutral-bg);
    border-radius: 4px;
    font-weight: 500;
    margin-right: 0.4rem;
    display: inline-block;
}

/* ---------- Precedent sub-card ---------- */
.precedent-card {
    border-left: 3px solid var(--accent-blue);
    padding: 0.5rem 1rem;
    margin-bottom: 0.75rem;
    background-color: var(--bg-canvas);
    border-radius: 0 6px 6px 0;
}

.precedent-title {
    font-weight: 600;
    font-size: 0.85rem;
    margin-bottom: 0.25rem;
    color: var(--text-primary);
}

.precedent-meta {
    color: var(--text-tertiary);
    font-size: 0.75rem;
    margin-top: 0.25rem;
}

.precedent-notes {
    color: var(--text-secondary);
    font-size: 0.8rem;
    font-style: italic;
    margin-top: 0.4rem;
}

.distance-mono {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: var(--text-tertiary);
    margin-left: 0.5rem;
}

/* ---------- Expander refinement ---------- */
details {
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    margin-top: 0.5rem !important;
    background-color: var(--bg-canvas) !important;
}

details summary {
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    color: var(--text-secondary) !important;
    padding: 0.6rem 1rem !important;
}

/* ---------- Ticker header (shown after analysis) ---------- */
.ticker-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 0.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--border);
}

.ticker-symbol {
    font-family: 'Manrope', sans-serif;
    font-size: 1.75rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    color: var(--text-primary);
}

.ticker-article-count {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    color: var(--text-tertiary);
    font-weight: 500;
}

/* Tighten dividers */
hr {
    margin: 1.25rem 0 !important;
    opacity: 0.5;
}
/* ---------- Mobile responsive: verdict first on small screens ---------- */
@media (max-width: 768px) {
    /* Streamlit columns use horizontal blocks as wrappers. On mobile they 
       wrap to vertical stacks. Reverse the order of the main two-column 
       layout so the mood summary appears before the articles list. */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: column !important;
    }
    
    /* The mood summary column is second in declaration order but should 
       appear first on mobile — bump its visual order to -1 (before default 0) */
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(2) {
        order: -1 !important;
    }
    
    /* Tighten the max-width and padding on mobile */
    .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    
    /* Make the ticker symbol heading smaller on mobile */
    .ticker-symbol {
        font-size: 1.5rem !important;
    }
}
</style>
"""