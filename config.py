"""
Centralized configuration loader.
Reads API keys from either Streamlit secrets (production) or .env (local dev).
"""

import os
from dotenv import load_dotenv

load_dotenv()


def _get_secret(key_name: str) -> str | None:
    """Try Streamlit secrets first, fall back to environment variable."""
    try:
        import streamlit as st
        value = st.secrets.get(key_name)
        if value:
            return value
    except Exception:
        pass
    return os.getenv(key_name)


def get_api_key() -> str:
    """Return the Gemini API key."""
    key = _get_secret("GEMINI_API_KEY")
    if not key:
        raise ValueError(
            "GEMINI_API_KEY not found. "
            "Set it in .env (local) or Streamlit Secrets (production)."
        )
    return key


def get_finnhub_api_key() -> str:
    """Return the Finnhub API key."""
    key = _get_secret("FINNHUB_API_KEY")
    if not key:
        raise ValueError(
            "FINNHUB_API_KEY not found. "
            "Set it in .env (local) or Streamlit Secrets (production). "
            "Get a free key at https://finnhub.io/register"
        )
    return key