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
        "description": "Check if the US stock market is currently open.",
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

    match name:
        case "get_account":
            return str(client.get_account())
        case "get_positions":
            return str(client.get_positions())
        case "get_open_orders":
            return str(client.get_open_orders())
        case "is_market_open":
            return str(client.is_market_open())
        case "get_market_movers":
            direction = inputs.get("direction", "gainers")
            return str(market.get_market_movers(direction))
        case "get_ticker_snapshot":
            return str(market.get_ticker_snapshot(inputs["symbol"]))
        case "get_ticker_details":
            return str(market.get_ticker_details(inputs["symbol"]))
        case "get_analyst_ratings":
            return str(market.get_analyst_ratings(inputs["symbol"]))
        case "get_recent_bars":
            return str(client.get_recent_bars(inputs["symbol"], inputs.get("days", 10)))
        case "get_latest_quote":
            return str(client.get_latest_quote(inputs["symbol"]))
        case "get_company_news":
            return str(news.get_company_news(inputs["symbol"], inputs.get("days", 3)))
        case "get_market_news":
            return str(news.get_market_news(inputs.get("limit", 15)))
        case "get_earnings_calendar":
            return str(news.get_earnings_calendar(inputs.get("days_ahead", 7)))
        case "get_sec_filings":
            return str(news.get_sec_filings(inputs["symbol"], inputs.get("limit", 5)))
        case "get_insider_trades":
            return str(news.get_insider_trades(inputs["symbol"], inputs.get("limit", 10)))
        case "place_market_order":
            return str(client.place_market_order(inputs["symbol"], inputs["qty"], inputs["side"]))
        case "place_limit_order":
            return str(client.place_limit_order(
                inputs["symbol"], inputs["qty"], inputs["side"], inputs["limit_price"]
            ))
        case "close_position":
            return str(client.close_position(inputs["symbol"]))
        case "log_trade":
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
        case _:
            return f"Unknown tool: {name}"
