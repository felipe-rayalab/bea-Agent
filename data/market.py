import os
import httpx
from datetime import datetime, timedelta
import pytz


POLYGON_BASE = "https://api.polygon.io"


def _polygon(path: str, params: dict = {}) -> dict:
    params["apiKey"] = os.environ["POLYGON_API_KEY"]
    r = httpx.get(f"{POLYGON_BASE}{path}", params=params, timeout=15)
    r.raise_for_status()
    return r.json()


def get_market_movers(direction: str = "gainers") -> list[dict]:
    """Top gainers or losers for the day."""
    data = _polygon(f"/v2/snapshot/locale/us/markets/stocks/{direction}")
    tickers = data.get("tickers", [])[:20]
    return [
        {
            "symbol": t["ticker"],
            "price": t["day"].get("c", 0),
            "change_pct": round(t.get("todaysChangePerc", 0), 2),
            "volume": t["day"].get("v", 0),
        }
        for t in tickers
    ]


def get_ticker_snapshot(symbol: str) -> dict:
    data = _polygon(f"/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}")
    t = data.get("ticker", {})
    day = t.get("day", {})
    prev = t.get("prevDay", {})
    return {
        "symbol": symbol,
        "price": day.get("c", 0),
        "open": day.get("o", 0),
        "high": day.get("h", 0),
        "low": day.get("l", 0),
        "volume": day.get("v", 0),
        "prev_close": prev.get("c", 0),
        "change_pct": round(t.get("todaysChangePerc", 0), 2),
        "vwap": day.get("vw", 0),
    }


def get_ticker_details(symbol: str) -> dict:
    data = _polygon(f"/v3/reference/tickers/{symbol}")
    r = data.get("results", {})
    return {
        "symbol": symbol,
        "name": r.get("name"),
        "market_cap": r.get("market_cap"),
        "sector": r.get("sic_description"),
        "description": r.get("description", "")[:500],
    }


def get_analyst_ratings(symbol: str) -> list[dict]:
    """Recent analyst upgrades/downgrades from Polygon."""
    data = _polygon("/v2/reference/analysts", {"ticker": symbol})
    results = data.get("results", [])[:5]
    return [
        {
            "analyst": r.get("analyst"),
            "action": r.get("action"),
            "rating": r.get("rating"),
            "price_target": r.get("price_target"),
            "date": r.get("date"),
        }
        for r in results
    ]


def get_premarket_movers() -> list[dict]:
    """Pre-market snapshot — returns gainers sorted by change_pct."""
    data = _polygon("/v2/snapshot/locale/us/markets/stocks/gainers", {"include_otc": False})
    tickers = data.get("tickers", [])[:15]
    return [
        {
            "symbol": t["ticker"],
            "price": t.get("lastTrade", {}).get("p", 0),
            "change_pct": round(t.get("todaysChangePerc", 0), 2),
            "volume": t["day"].get("v", 0),
        }
        for t in tickers
    ]
