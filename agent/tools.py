from broker.alpaca_client import AlpacaClient
from data import market, news, portfolio

_client: AlpacaClient | None = None


def get_client() -> AlpacaClient:
    global _client
    if _client is None:
        _client = AlpacaClient()
    return _client


TOOL_DEFINITIONS = [
    {
        "name": "get_account",
        "description": "Get current account state: cash, portfolio value, buying power, today's P&L.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_positions",
        "description": "List all open positions with symbol, quantity, entry price, current price, unrealized P&L.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_open_orders",
        "description": "List pending orders not yet filled.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_market_movers",
        "description": "Get top 20 gainers or losers for the day.",
        "input_schema": {
            "type": "object",
            "properties": {
                "direction": {"type": "string", "enum": ["gainers", "losers"], "description": "gainers or losers"}
            },
            "required": [],
        },
    },
    {
        "name": "get_ticker_snapshot",
        "description": "Real-time price, volume, OHLC and % change for a symbol.",
        "input_schema": {
            "type": "object",
            "properties": {"symbol": {"type": "string", "description": "Stock ticker, e.g. AAPL"}},
            "required": ["symbol"],
        },
    },
    {
        "name": "get_ticker_details",
        "description": "Company info: name, sector, market cap, description.",
        "input_schema": {
            "type": "object",
            "properties": {"symbol": {"type": "string"}},
            "required": ["symbol"],
        },
    },
    {
        "name": "get_analyst_ratings",
        "description": "Recent analyst upgrades or downgrades for a symbol.",
        "input_schema": {
            "type": "object",
            "properties": {"symbol": {"type": "string"}},
            "required": ["symbol"],
        },
    },
    {
        "name": "get_company_news",
        "description": "Recent news articles for a specific ticker with sentiment.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "days": {"type": "integer", "description": "How many days back (default 3)"},
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "get_market_news",
        "description": "General market news, not filtered by ticker.",
        "input_schema": {
            "type": "object",
            "properties": {"limit": {"type": "integer", "description": "Number of articles (default 15)"}},
            "required": [],
        },
    },
    {
        "name": "get_earnings_calendar",
        "description": "Upcoming earnings reports in the next N days.",
        "input_schema": {
            "type": "object",
            "properties": {"days_ahead": {"type": "integer", "description": "Days to look ahead (default 7)"}},
            "required": [],
        },
    },
    {
        "name": "get_sec_filings",
        "description": "Recent SEC filings (10-K, 10-Q, 8-K) for a ticker.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "limit": {"type": "integer", "description": "Max filings (default 5)"},
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "get_insider_trades",
        "description": "Recent insider buy/sell transactions for a ticker.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "limit": {"type": "integer", "description": "Max transactions (default 10)"},
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "get_recent_bars",
        "description": "Historical daily OHLCV bars for a symbol from Alpaca.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "days": {"type": "integer", "description": "Number of days back (default 10)"},
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "get_latest_quote",
        "description": "Real-time bid/ask/mid quote for a symbol.",
        "input_schema": {
            "type": "object",
            "properties": {"symbol": {"type": "string"}},
            "required": ["symbol"],
        },
    },
    {
        "name": "is_market_open",
        "description": "Check if the US stock market regular session is currently open.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_market_session",
        "description": "Returns current trading session: pre-market (4–9:30am ET), regular (9:30am–4pm ET), after-hours (4–8pm ET), or closed.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "place_market_order",
        "description": "Place a market buy or sell order. Executes immediately at current price.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Stock ticker"},
                "qty": {"type": "number", "description": "Number of shares"},
                "side": {"type": "string", "enum": ["buy", "sell"], "description": "buy or sell"},
            },
            "required": ["symbol", "qty", "side"],
        },
    },
    {
        "name": "place_limit_order",
        "description": "Place a limit buy or sell order at a specific price.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "qty": {"type": "number"},
                "side": {"type": "string", "enum": ["buy", "sell"]},
                "limit_price": {"type": "number", "description": "The limit price"},
            },
            "required": ["symbol", "qty", "side", "limit_price"],
        },
    },
    {
        "name": "close_position",
        "description": "Close the entire position in a symbol (sell all shares).",
        "input_schema": {
            "type": "object",
            "properties": {"symbol": {"type": "string"}},
            "required": ["symbol"],
        },
    },
    {
        "name": "log_trade",
        "description": "Record a trade decision in the journal with reasoning. Always call after placing an order.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "buy, sell, or close"},
                "symbol": {"type": "string"},
                "qty": {"type": "number"},
                "price": {"type": "number"},
                "reasoning": {"type": "string", "description": "Why you made this trade"},
                "order_result": {"type": "object"},
            },
            "required": ["action", "symbol", "qty", "price", "reasoning", "order_result"],
        },
    },
]


def dispatch_tool(name: str, inputs: dict) -> str:
    client = get_client()

    if name == "get_account":
        return str(client.get_account())
    elif name == "get_positions":
        return str(client.get_positions())
    elif name == "get_open_orders":
        return str(client.get_open_orders())
    elif name == "is_market_open":
        return str(client.is_market_open())
    elif name == "get_market_session":
        return str(client.get_market_session())
    elif name == "get_market_movers":
        return str(market.get_market_movers(inputs.get("direction", "gainers")))
    elif name == "get_ticker_snapshot":
        return str(market.get_ticker_snapshot(inputs["symbol"]))
    elif name == "get_ticker_details":
        return str(market.get_ticker_details(inputs["symbol"]))
    elif name == "get_analyst_ratings":
        return str(market.get_analyst_ratings(inputs["symbol"]))
    elif name == "get_recent_bars":
        return str(client.get_recent_bars(inputs["symbol"], inputs.get("days", 10)))
    elif name == "get_latest_quote":
        return str(client.get_latest_quote(inputs["symbol"]))
    elif name == "get_company_news":
        return str(news.get_company_news(inputs["symbol"], inputs.get("days", 3)))
    elif name == "get_market_news":
        return str(news.get_market_news(inputs.get("limit", 15)))
    elif name == "get_earnings_calendar":
        return str(news.get_earnings_calendar(inputs.get("days_ahead", 7)))
    elif name == "get_sec_filings":
        return str(news.get_sec_filings(inputs["symbol"], inputs.get("limit", 5)))
    elif name == "get_insider_trades":
        return str(news.get_insider_trades(inputs["symbol"], inputs.get("limit", 10)))
    elif name == "place_market_order":
        return str(client.place_market_order(inputs["symbol"], inputs["qty"], inputs["side"]))
    elif name == "place_limit_order":
        return str(client.place_limit_order(
            inputs["symbol"], inputs["qty"], inputs["side"], inputs["limit_price"]
        ))
    elif name == "close_position":
        return str(client.close_position(inputs["symbol"]))
    elif name == "log_trade":
        acct = client.get_account()
        portfolio.log_trade(
            action=inputs["action"],
            symbol=inputs["symbol"],
            qty=inputs["qty"],
            price=inputs["price"],
            reasoning=inputs["reasoning"],
            order_result=inputs["order_result"],
            portfolio_snapshot=acct,
        )
        return "Trade logged successfully."
    else:
        return f"Unknown tool: {name}"
