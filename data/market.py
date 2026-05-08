import yfinance as yf
from datetime import datetime, timedelta
import pytz


def get_market_movers(direction: str = "gainers") -> list[dict]:
    """Top movers using a curated watchlist via yfinance."""
    watchlist = [
        "NVDA", "AMD", "TSLA", "META", "MSFT", "AAPL", "GOOGL", "AMZN",
        "PLTR", "COIN", "SMCI", "AVGO", "ARM", "MSTR", "HOOD", "SQ",
        "SOFI", "RBLX", "SHOP", "NET", "CRWD", "SNOW", "DDOG", "MDB"
    ]
    tickers = yf.download(watchlist, period="2d", interval="1d", progress=False, auto_adjust=True)
    results = []
    for symbol in watchlist:
        try:
            closes = tickers["Close"][symbol].dropna()
            if len(closes) < 2:
                continue
            prev, last = float(closes.iloc[-2]), float(closes.iloc[-1])
            change_pct = round((last - prev) / prev * 100, 2)
            results.append({"symbol": symbol, "price": last, "change_pct": change_pct})
        except Exception:
            continue
    results.sort(key=lambda x: x["change_pct"], reverse=(direction == "gainers"))
    return results[:15]


def get_ticker_snapshot(symbol: str) -> dict:
    t = yf.Ticker(symbol)
    info = t.info
    hist = t.history(period="2d")
    price = float(hist["Close"].iloc[-1]) if not hist.empty else info.get("regularMarketPrice", 0)
    prev = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else price
    change_pct = round((price - prev) / prev * 100, 2) if prev else 0
    return {
        "symbol": symbol,
        "price": price,
        "open": float(hist["Open"].iloc[-1]) if not hist.empty else 0,
        "high": float(hist["High"].iloc[-1]) if not hist.empty else 0,
        "low": float(hist["Low"].iloc[-1]) if not hist.empty else 0,
        "volume": int(hist["Volume"].iloc[-1]) if not hist.empty else 0,
        "prev_close": prev,
        "change_pct": change_pct,
    }


def get_ticker_details(symbol: str) -> dict:
    info = yf.Ticker(symbol).info
    return {
        "symbol": symbol,
        "name": info.get("longName"),
        "market_cap": info.get("marketCap"),
        "sector": info.get("sector"),
        "description": (info.get("longBusinessSummary") or "")[:500],
    }


def get_analyst_ratings(symbol: str) -> list[dict]:
    try:
        recs = yf.Ticker(symbol).recommendations
        if recs is None or recs.empty:
            return []
        recent = recs.tail(5).reset_index()
        return [
            {
                "firm": row.get("Firm", ""),
                "action": row.get("Action", ""),
                "rating": row.get("To Grade", ""),
                "date": str(row.get("Date", "")),
            }
            for _, row in recent.iterrows()
        ]
    except Exception:
        return []


def get_premarket_movers() -> list[dict]:
    return get_market_movers("gainers")
