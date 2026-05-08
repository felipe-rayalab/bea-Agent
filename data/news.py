import os
import httpx
from datetime import datetime, timedelta


FD_BASE = "https://api.financialdatasets.ai"
EODHD_BASE = "https://eodhd.com/api"


def _fd_headers() -> dict:
    return {"X-API-KEY": os.environ["FINANCIAL_DATASETS_API_KEY"]}


def get_company_news(symbol: str, days: int = 3) -> list[dict]:
    """Recent news for a ticker from Financial Datasets."""
    since = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
    r = httpx.get(
        f"{FD_BASE}/news",
        params={"ticker": symbol, "start_date": since, "limit": 10},
        headers=_fd_headers(),
        timeout=15,
    )
    r.raise_for_status()
    items = r.json().get("news", [])
    return [
        {
            "title": n.get("title"),
            "summary": n.get("summary", "")[:300],
            "source": n.get("source"),
            "published_at": n.get("published_at"),
            "sentiment": n.get("sentiment"),
        }
        for n in items
    ]


def get_market_news(limit: int = 15) -> list[dict]:
    """General market news (no ticker filter)."""
    r = httpx.get(
        f"{FD_BASE}/news",
        params={"limit": limit},
        headers=_fd_headers(),
        timeout=15,
    )
    r.raise_for_status()
    items = r.json().get("news", [])
    return [
        {
            "title": n.get("title"),
            "summary": n.get("summary", "")[:300],
            "source": n.get("source"),
            "published_at": n.get("published_at"),
            "tickers": n.get("tickers", []),
        }
        for n in items
    ]


def get_sec_filings(symbol: str, limit: int = 5) -> list[dict]:
    """Recent SEC filings for a ticker."""
    r = httpx.get(
        f"{FD_BASE}/sec-filings",
        params={"ticker": symbol, "limit": limit},
        headers=_fd_headers(),
        timeout=15,
    )
    r.raise_for_status()
    filings = r.json().get("filings", [])
    return [
        {
            "form": f.get("form_type"),
            "filed_at": f.get("filed_at"),
            "description": f.get("description", "")[:200],
        }
        for f in filings
    ]


def get_insider_trades(symbol: str, limit: int = 10) -> list[dict]:
    """Recent insider transactions."""
    r = httpx.get(
        f"{FD_BASE}/insider-transactions",
        params={"ticker": symbol, "limit": limit},
        headers=_fd_headers(),
        timeout=15,
    )
    r.raise_for_status()
    trades = r.json().get("transactions", [])
    return [
        {
            "name": t.get("name"),
            "role": t.get("role"),
            "transaction_type": t.get("transaction_type"),
            "shares": t.get("shares"),
            "price": t.get("price"),
            "date": t.get("date"),
        }
        for t in trades
    ]


def get_earnings_calendar(days_ahead: int = 7) -> list[dict]:
    """Upcoming earnings releases from EODHD."""
    from_date = datetime.utcnow().strftime("%Y-%m-%d")
    to_date = (datetime.utcnow() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
    r = httpx.get(
        f"{EODHD_BASE}/calendar/earnings",
        params={
            "api_token": os.environ["EODHD_API_KEY"],
            "fmt": "json",
            "from": from_date,
            "to": to_date,
        },
        timeout=15,
    )
    r.raise_for_status()
    earnings = r.json().get("earnings", [])
    return [
        {
            "symbol": e.get("code", "").replace(".US", ""),
            "report_date": e.get("report_date"),
            "estimate": e.get("estimate"),
            "actual": e.get("actual"),
            "difference": e.get("difference"),
            "surprise_pct": e.get("percent"),
        }
        for e in earnings[:30]
    ]
