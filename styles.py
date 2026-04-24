"""
Custom CSS for the Finance News Intelligence Agent.
Aesthetic direction: minimal, refined, Linear/Vercel-adjacent.
Theme-aware: adapts to light/dark via CSS variables.
"""

CUSTOM_CSS = """
<style>
/* ---------- Font import ---------- */
@import url('https://rsms.me/inter/inter.css');
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap');

/* ---------- Base typography overrides ---------- */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, sans-serif !important;
    font-feature-settings: 'cv11', 'ss01', 'ss03';
}

/* Tabular numbers feel for metrics */
.stMetric [data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 500 !important;
    font-variant-numeric: tabular-nums;
}

/* ---------- Theme-agnostic color variables ---------- */
:root {
    --accent: #5e5ce6;
    --bullish-fg: #047857;
    --bullish-bg: #d1fae5;
    --bearish-fg: #b91c1c;
    --bearish-bg: #fee2e2;
    --neutral-fg: #92400e;
    --neutral-bg: #fef3c7;
    --card-border: rgba(0, 0, 0, 0.08);
    --card-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    --card-shadow-hover: 0 4px 12px rgba(0, 0, 0, 0.08);
    --muted-text: #6b7280;
}

/* Dark mode overrides */
@media (prefers-color-scheme: dark) {
    :root {
        --bullish-fg: #6ee7b7;
        --bullish-bg: rgba(16, 185, 129, 0.15);
        --bearish-fg: #fca5a5;
        --bearish-bg: rgba(239, 68, 68, 0.15);
        --neutral-fg: #fcd34d;
        --neutral-bg: rgba(245, 158, 11, 0.15);
        --card-border: rgba(255, 255, 255, 0.08);
        --card-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
        --card-shadow-hover: 0 4px 12px rgba(0, 0, 0, 0.4);
        --muted-text: #9ca3af;
    }
}

/* ---------- Page layout ---------- */
.block-container {
    max-width: 900px !important;
    padding-top: 3rem !important;
    padding-bottom: 4rem !important;
}

/* ---------- Typography hierarchy ---------- */
h1 {
    font-weight: 600 !important;
    letter-spacing: -0.03em !important;
    font-size: 2rem !important;
    margin-bottom: 0.25rem !important;
}

h2 {
    font-weight: 600 !important;
    letter-spacing: -0.02em !important;
    font-size: 1.25rem !important;
    margin-top: 2rem !important;
    margin-bottom: 1rem !important;
}

h3 {
    font-weight: 500 !important;
    font-size: 1rem !important;
    margin-bottom: 0.5rem !important;
}

/* ---------- Article card styling ---------- */
.article-card {
    border: 1px solid var(--card-border);
    border-radius: 10px;
    padding: 1.25rem;
    box-shadow: var(--card-shadow);
    transition: box-shadow 0.15s ease;
    margin-bottom: 1rem;
    background-color: var(--background-color, transparent);
}

.article-card:hover {
    box-shadow: var(--card-shadow-hover);
}

.article-title {
    font-weight: 600;
    font-size: 0.95rem;
    line-height: 1.4;
    margin-bottom: 0.5rem;
}

.article-source {
    color: var(--muted-text);
    font-size: 0.8rem;
    margin-bottom: 0.75rem;
}

.article-reasoning {
    color: var(--muted-text);
    font-size: 0.85rem;
    line-height: 1.5;
    margin-top: 0.5rem;
}

/* ---------- Badges ---------- */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 500;
    margin-right: 0.4rem;
}

.badge-bullish { color: var(--bullish-fg); background-color: var(--bullish-bg); }
.badge-bearish { color: var(--bearish-fg); background-color: var(--bearish-bg); }
.badge-neutral { color: var(--neutral-fg); background-color: var(--neutral-bg); }

.badge-pill {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 0.7rem;
    font-weight: 500;
    background-color: var(--card-border);
    color: var(--muted-text);
    margin-right: 0.4rem;
}

/* ---------- Sentiment distribution bar ---------- */
.sentiment-bar-container {
    display: flex;
    width: 100%;
    height: 8px;
    border-radius: 4px;
    overflow: hidden;
    margin: 0.75rem 0 1.5rem 0;
    background-color: var(--card-border);
}

.sentiment-bar-segment {
    transition: width 0.3s ease;
}

.seg-bullish { background-color: #10b981; }
.seg-bearish { background-color: #ef4444; }
.seg-neutral { background-color: #f59e0b; }

/* ---------- Precedent sub-card ---------- */
.precedent-card {
    border-left: 2px solid var(--card-border);
    padding-left: 1rem;
    margin-bottom: 0.75rem;
}

.precedent-title {
    font-weight: 500;
    font-size: 0.85rem;
    margin-bottom: 0.25rem;
}

.precedent-meta {
    color: var(--muted-text);
    font-size: 0.75rem;
    margin-bottom: 0.25rem;
}

.precedent-notes {
    color: var(--muted-text);
    font-size: 0.8rem;
    font-style: italic;
}

.distance-mono {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: var(--muted-text);
}

/* ---------- Clean up Streamlit defaults ---------- */
[data-testid="stSidebar"] { display: none; }

div[data-testid="stToolbar"] { visibility: hidden; }

footer { visibility: hidden; }

.stButton > button {
    font-weight: 500 !important;
    border-radius: 8px !important;
    transition: all 0.15s ease;
}

/* Input field refinement */
.stTextInput > div > div > input {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.95rem !important;
    border-radius: 8px !important;
}

/* Expander refinement */
details {
    border: 1px solid var(--card-border) !important;
    border-radius: 8px !important;
    margin-top: 0.75rem !important;
}

/* Tighter divider */
hr {
    margin: 1.5rem 0 !important;
    opacity: 0.5;
}

.subtitle {
    color: var(--muted-text);
    font-size: 0.95rem;
    margin-bottom: 2rem;
    line-height: 1.5;
}

.section-label {
    color: var(--muted-text);
    font-size: 0.75rem;
    font-weight: 500;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
    margin-top: 1.5rem;
}
</style>
"""