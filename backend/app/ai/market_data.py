"""
market_data.py — Live Indian market data via yfinance with in-memory TTL cache.

Fetches: Nifty 50, Sensex, Midcap 100, Smallcap 100, India VIX,
         MCX Gold (GOLDBEES proxy), USD/INR, and static RBI rates.

Cache TTL: 15 minutes — balances freshness vs Yahoo Finance rate limits.
Falls back gracefully to last cached data (or demo values) on fetch failure.

Dependencies: yfinance, tenacity (already in requirements.txt)
"""

import asyncio
import time
from datetime import date, datetime, timezone
from typing import Any

import yfinance as yf
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

from app.core.logging_config import get_logger

logger = get_logger(__name__)

# ─── Cache ────────────────────────────────────────────────────────────────────

_CACHE_TTL_SECONDS = 900  # 15 minutes
_cache: dict[str, Any] | None = None
_cache_timestamp: float = 0.0

# ─── Ticker Symbols ───────────────────────────────────────────────────────────

_TICKERS = {
    "NIFTY_50":           "^NSEI",
    "SENSEX":             "^BSESN",
    "NIFTY_MIDCAP_100":   "^NSMIDCP",
    "NIFTY_SMALLCAP_100": "^CNXSC",
    "INDIA_VIX":          "^INDIAVIX",
    "GOLD_ETF":           "GOLDBEES.NS",   # Nippon Gold BeES (INR proxy)
    "USD_INR":            "USDINR=X",
}

# Static rates — updated quarterly from RBI announcements
_STATIC_RATES = {
    "repo_rate_pct": 6.00,                 # RBI MPC cut Apr 2025
    "10yr_gsec_yield_pct": 6.60,
    "liquid_fund_7d_yield_pct": 6.60,
    "corporate_bond_aaa_pct": 7.20,
}

# ─── Fallback demo data (used if yfinance fails AND no cache available) ────────

_FALLBACK = {
    "indices": {
        "NIFTY_50": {
            "name": "Nifty 50",
            "value": 23_215.0,
            "change_1d_pct": 0.0,
            "change_1w_pct": 0.0,
            "change_1m_pct": 0.0,
            "change_1y_pct": 0.0,
            "52w_high": 26_373.0,
            "52w_low": 22_183.0,
            "pe_ratio": None,
        },
        "SENSEX": {"name": "BSE Sensex", "value": 73_983.0, "change_1d_pct": 0.0, "change_1y_pct": 0.0},
        "NIFTY_MIDCAP_100": {"name": "Nifty Midcap 100", "value": 69_155.0, "change_1d_pct": 0.0, "change_1y_pct": 0.0},
        "NIFTY_SMALLCAP_100": {"name": "Nifty Smallcap 100", "value": 17_823.0, "change_1d_pct": 0.0, "change_1y_pct": 0.0},
        "INDIA_VIX": {
            "name": "India VIX (Volatility Index)",
            "value": 15.6,
            "change_1d_pct": 0.0,
            "note": "VIX < 15 = low volatility (favorable for equities)",
        },
    },
    "debt_rates": _STATIC_RATES,
    "gold": {"mcx_gold_per_10g": None, "goldbees_price": None, "change_1d_pct": 0.0, "change_1y_pct": 0.0},
    "currency": {"USD_INR": 84.0},
    "market_context": {
        "as_of_date": date.today().isoformat(),
        "data_source": "fallback_demo",
        "market_sentiment": "data_unavailable",
    },
}

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _pct_change(new: float, old: float) -> float | None:
    if old and old != 0:
        return round((new - old) / old * 100, 2)
    return None


def _fetch_ticker(symbol: str, period: str = "13mo") -> dict:
    """Fetch ticker history. Returns empty dict on error."""
    try:
        t = yf.Ticker(symbol)
        hist = t.history(period=period)
        if hist.empty:
            return {}
        return {"hist": hist, "ticker": t}
    except Exception as exc:
        logger.warning("yfinance_fetch_failed", symbol=symbol, error=str(exc))
        return {}


def _build_index_entry(name: str, symbol: str, note: str | None = None) -> dict:
    data = _fetch_ticker(symbol)
    if not data:
        return {}
    hist = data["hist"]
    close = hist["Close"]
    high_col = hist["High"]
    low_col = hist["Low"]
    current = float(close.iloc[-1])
    entry: dict = {
        "name": name,
        "value": round(current, 2),
        "change_1d_pct": _pct_change(current, float(close.iloc[-2])) if len(close) >= 2 else None,
        "change_1w_pct": _pct_change(current, float(close.iloc[-6])) if len(close) >= 6 else None,
        "change_1m_pct": _pct_change(current, float(close.iloc[-22])) if len(close) >= 22 else None,
        "change_1y_pct": _pct_change(current, float(close.iloc[0])) if len(close) >= 52 else None,
        "52w_high": round(float(high_col.max()), 2),
        "52w_low": round(float(low_col.min()), 2),
    }
    if note:
        entry["note"] = note
    return entry


def _fetch_live_data() -> dict:
    """Fetch all live data from Yahoo Finance. Called synchronously in thread."""
    logger.info("market_data_fetch_start")
    indices: dict = {}

    # Nifty 50 (include PE from info)
    nifty_data = _build_index_entry("Nifty 50", "^NSEI")
    if nifty_data:
        try:
            info = yf.Ticker("^NSEI").info
            nifty_data["pe_ratio"] = info.get("trailingPE") or info.get("forwardPE")
        except Exception:
            nifty_data["pe_ratio"] = None
        indices["NIFTY_50"] = nifty_data

    sensex = _build_index_entry("BSE Sensex", "^BSESN")
    if sensex:
        # Sensex doesn't need 52w fields in condensed form
        indices["SENSEX"] = {k: sensex[k] for k in ["name", "value", "change_1d_pct", "change_1w_pct", "change_1m_pct", "change_1y_pct", "52w_high", "52w_low"] if k in sensex}

    midcap = _build_index_entry("Nifty Midcap 100", "^NSMIDCP")
    if midcap:
        indices["NIFTY_MIDCAP_100"] = {k: midcap[k] for k in ["name", "value", "change_1d_pct", "change_1y_pct"] if k in midcap}

    smallcap = _build_index_entry("Nifty Smallcap 100", "^CNXSC")
    if smallcap:
        indices["NIFTY_SMALLCAP_100"] = {k: smallcap[k] for k in ["name", "value", "change_1d_pct", "change_1y_pct"] if k in smallcap}

    vix_data = _fetch_ticker("^INDIAVIX")
    if vix_data:
        vix_hist = vix_data["hist"]["Close"]
        cur = float(vix_hist.iloc[-1])
        indices["INDIA_VIX"] = {
            "name": "India VIX (Volatility Index)",
            "value": round(cur, 2),
            "change_1d_pct": _pct_change(cur, float(vix_hist.iloc[-2])) if len(vix_hist) >= 2 else None,
            "note": "VIX < 15 = low volatility (favorable for equities)",
        }

    # Gold (GOLDBEES ETF price per unit ≈ 1g gold)
    gold_entry: dict = {}
    gold_data = _fetch_ticker("GOLDBEES.NS")
    if gold_data:
        g_hist = gold_data["hist"]["Close"]
        g_cur = float(g_hist.iloc[-1])
        gold_entry = {
            "goldbees_price": round(g_cur, 2),
            "goldbees_note": "Nippon Gold BeES NAV (INR per unit ≈ ~1g gold)",
            "change_1d_pct": _pct_change(g_cur, float(g_hist.iloc[-2])) if len(g_hist) >= 2 else None,
            "change_1y_pct": _pct_change(g_cur, float(g_hist.iloc[0])) if len(g_hist) >= 52 else None,
        }

    # USD/INR
    currency: dict = {}
    fx_data = _fetch_ticker("USDINR=X", period="5d")
    if fx_data:
        fx_close = fx_data["hist"]["Close"]
        currency["USD_INR"] = round(float(fx_close.iloc[-1]), 2)

    # Market sentiment heuristic
    sentiment = "neutral"
    if indices.get("NIFTY_50"):
        change = indices["NIFTY_50"].get("change_1d_pct") or 0
        vix_val = indices.get("INDIA_VIX", {}).get("value") or 15
        if change > 0.5 and vix_val < 15:
            sentiment = "bullish"
        elif change < -0.5 or vix_val > 20:
            sentiment = "cautious"
        else:
            sentiment = "cautiously_bullish"

    result = {
        "indices": indices if indices else _FALLBACK["indices"],
        "debt_rates": _STATIC_RATES,
        "gold": gold_entry if gold_entry else _FALLBACK["gold"],
        "currency": currency if currency else _FALLBACK["currency"],
        "market_context": {
            "as_of_date": date.today().isoformat(),
            "as_of_time_utc": datetime.now(timezone.utc).strftime("%H:%M UTC"),
            "data_source": "yahoo_finance_live",
            "market_sentiment": sentiment,
            "key_events": [
                "RBI MPC — next review scheduled",
                "Monitor Q4 FY25 earnings season",
            ],
            "note": "Live data via Yahoo Finance. 15-minute cache. Gold via GOLDBEES ETF.",
        },
    }
    logger.info("market_data_fetch_complete", indices=list(indices.keys()))
    return result


# ─── Public async API ─────────────────────────────────────────────────────────

async def get_market_data(indices_filter: list[str] | None = None) -> dict:
    """
    Return live market data. Fetches from Yahoo Finance if cache is stale.
    Falls back to stale cache (or demo values) on error.
    Thread-safe: fetch runs in executor to avoid blocking event loop.
    """
    global _cache, _cache_timestamp

    now = time.monotonic()
    if _cache is not None and (now - _cache_timestamp) < _CACHE_TTL_SECONDS:
        data = _cache
    else:
        try:
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, _fetch_live_data)
            _cache = data
            _cache_timestamp = now
        except Exception as exc:
            logger.error("market_data_fetch_error", error=str(exc))
            data = _cache if _cache is not None else _FALLBACK

    # Apply index filter if requested
    if indices_filter:
        filtered = {k: v for k, v in data["indices"].items() if k in [i.upper() for i in indices_filter]}
        return {**data, "indices": filtered}

    return data
