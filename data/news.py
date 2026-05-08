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
    """Upcoming earnings using Yahoo Finance — no API key required."""
    import yfinance as yf
    watchlist = [
        "NVDA", "AMD", "TSLA", "META", "MSFT", "AAPL", "GOOGL", "AMZN",
        "PLTR", "COIN", "AVGO", "ARM", "SMCI", "HOOD", "SHOP", "NET",
        "CRWD", "SNOW", "DDOG", "MDB", "SOFI", "RBLX", "SQ", "MSTR"
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
