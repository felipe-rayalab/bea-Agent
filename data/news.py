import os
import httpx
from datetime import datetime, timedelta

ALPACA_DATA_BASE = "https://data.alpaca.markets"


def _alpaca_headers() -> dict:
    return {
        "APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"],
        "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"],
    }


def get_company_news(symbol: str, days: int = 3) -> list[dict]:
    """Recent news for a ticker via Alpaca News API."""
    since = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    r = httpx.get(
        f"{ALPACA_DATA_BASE}/v1beta1/news",
        params={"symbols": symbol, "limit": 10, "start": since, "sort": "desc"},
        headers=_alpaca_headers(),
        timeout=15,
    )
    r.raise_for_status()
    items = r.json().get("news", [])
    return [
        {
            "title": n.get("headline"),
            "summary": (n.get("summary") or "")[:300],
            "source": n.get("source"),
            "published_at": n.get("created_at"),
            "url": n.get("url"),
            "symbols": n.get("symbols", []),
        }
        for n in items
    ]


def get_market_news(limit: int = 15) -> list[dict]:
    """General market news via Alpaca News API."""
    r = httpx.get(
        f"{ALPACA_DATA_BASE}/v1beta1/news",
        params={"limit": limit, "sort": "desc"},
        headers=_alpaca_headers(),
        timeout=15,
    )
    r.raise_for_status()
    items = r.json().get("news", [])
    return [
        {
            "title": n.get("headline"),
            "summary": (n.get("summary") or "")[:300],
            "source": n.get("source"),
            "published_at": n.get("created_at"),
            "symbols": n.get("symbols", []),
        }
        for n in items
    ]


def get_sec_filings(symbol: str, limit: int = 5) -> list[dict]:
    """SEC filings via Alpaca News API filtered by keyword."""
    r = httpx.get(
        f"{ALPACA_DATA_BASE}/v1beta1/news",
        params={"symbols": symbol, "limit": limit, "sort": "desc"},
        headers=_alpaca_headers(),
        timeout=15,
    )
    r.raise_for_status()
    items = r.json().get("news", [])
    # Filter for SEC-related headlines
    sec_items = [n for n in items if any(
        kw in (n.get("headline") or "").upper()
        for kw in ["SEC", "10-K", "10-Q", "8-K", "FILING", "ANNUAL REPORT"]
    )]
    return [
        {
            "title": n.get("headline"),
            "published_at": n.get("created_at"),
            "source": n.get("source"),
            "url": n.get("url"),
        }
        for n in (sec_items or items)[:limit]
    ]


def get_insider_trades(symbol: str, limit: int = 10) -> list[dict]:
    """Insider trade news via Alpaca News API."""
    r = httpx.get(
        f"{ALPACA_DATA_BASE}/v1beta1/news",
        params={"symbols": symbol, "limit": limit, "sort": "desc"},
        headers=_alpaca_headers(),
        timeout=15,
    )
    r.raise_for_status()
    items = r.json().get("news", [])
    insider_items = [n for n in items if any(
        kw in (n.get("headline") or "").upper()
        for kw in ["INSIDER", "PURCHASE", "SOLD", "BOUGHT", "STAKE", "ACQUISITION"]
    )]
    return [
        {
            "title": n.get("headline"),
            "published_at": n.get("created_at"),
            "source": n.get("source"),
        }
        for n in (insider_items or items)[:limit]
    ]


def get_earnings_calendar(days_ahead: int = 7) -> list[dict]:
    """Upcoming earnings via Yahoo Finance — no API key required."""
    import yfinance as yf
    watchlist = [
        "NVDA", "AMD", "TSLA", "META", "MSFT", "AAPL", "GOOGL", "AMZN",
        "PLTR", "COIN", "AVGO", "ARM", "SMCI", "HOOD", "SHOP", "NET",
        "CRWD", "SNOW", "DDOG", "MDB", "SOFI", "RBLX", "MSTR"
    ]
    results = []
    cutoff = datetime.utcnow() + timedelta(days=days_ahead)
    for symbol in watchlist:
        try:
            cal = yf.Ticker(symbol).calendar
            if cal is None:
                continue
            date = cal.get("Earnings Date")
            if date and len(date) > 0:
                earnings_date = date[0]
                if hasattr(earnings_date, 'to_pydatetime'):
                    earnings_date = earnings_date.to_pydatetime()
                if earnings_date.replace(tzinfo=None) <= cutoff:
                    results.append({
                        "symbol": symbol,
                        "report_date": str(earnings_date.date()),
                        "eps_estimate": cal.get("EPS Estimate"),
                    })
        except Exception:
            continue
    results.sort(key=lambda x: x["report_date"])
    return results
