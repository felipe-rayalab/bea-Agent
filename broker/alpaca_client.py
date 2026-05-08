import os
from decimal import Decimal
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta
import pytz


class AlpacaClient:
    def __init__(self):
        api_key = os.environ["ALPACA_API_KEY"]
        secret_key = os.environ["ALPACA_SECRET_KEY"]
        paper = os.environ.get("PAPER_TRADING", "true").lower() == "true"

        self.trading = TradingClient(api_key, secret_key, paper=paper)
        self.data = StockHistoricalDataClient(api_key, secret_key)

    def get_account(self) -> dict:
        acct = self.trading.get_account()
        return {
            "cash": float(acct.cash),
            "portfolio_value": float(acct.portfolio_value),
            "buying_power": float(acct.buying_power),
            "equity": float(acct.equity),
            "pnl_today": float(acct.equity) - float(acct.last_equity),
        }

    def get_positions(self) -> list[dict]:
        positions = self.trading.get_all_positions()
        return [
            {
                "symbol": p.symbol,
                "qty": float(p.qty),
                "market_value": float(p.market_value),
                "avg_entry_price": float(p.avg_entry_price),
                "current_price": float(p.current_price),
                "unrealized_pl": float(p.unrealized_pl),
                "unrealized_plpc": float(p.unrealized_plpc),
                "side": p.side.value,
            }
            for p in positions
        ]

    def get_open_orders(self) -> list[dict]:
        orders = self.trading.get_orders()
        return [
            {
                "id": str(o.id),
                "symbol": o.symbol,
                "qty": float(o.qty or 0),
                "side": o.side.value,
                "type": o.type.value,
                "status": o.status.value,
                "submitted_at": str(o.submitted_at),
            }
            for o in orders
        ]

    def place_market_order(self, symbol: str, qty: float, side: str) -> dict:
        order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
        req = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=order_side,
            time_in_force=TimeInForce.DAY,
        )
        order = self.trading.submit_order(req)
        return {
            "id": str(order.id),
            "symbol": order.symbol,
            "qty": float(order.qty or qty),
            "side": order.side.value,
            "status": order.status.value,
        }

    def place_limit_order(self, symbol: str, qty: float, side: str, limit_price: float) -> dict:
        order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
        req = LimitOrderRequest(
            symbol=symbol,
            qty=qty,
            side=order_side,
            time_in_force=TimeInForce.DAY,
            limit_price=limit_price,
        )
        order = self.trading.submit_order(req)
        return {
            "id": str(order.id),
            "symbol": order.symbol,
            "qty": float(order.qty or qty),
            "limit_price": limit_price,
            "side": order.side.value,
            "status": order.status.value,
        }

    def close_position(self, symbol: str) -> dict:
        result = self.trading.close_position(symbol)
        return {"symbol": symbol, "status": "closed", "order_id": str(result.id)}

    def close_all_positions(self) -> list[dict]:
        results = self.trading.close_all_positions(cancel_orders=True)
        return [{"symbol": r.symbol, "status": r.status} for r in (results or [])]

    def get_recent_bars(self, symbol: str, days: int = 10) -> list[dict]:
        start = datetime.now(pytz.UTC) - timedelta(days=days)
        req = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Day,
            start=start,
        )
        bars = self.data.get_stock_bars(req)
        result = []
        for bar in bars[symbol]:
            result.append({
                "timestamp": str(bar.timestamp),
                "open": float(bar.open),
                "high": float(bar.high),
                "low": float(bar.low),
                "close": float(bar.close),
                "volume": int(bar.volume),
            })
        return result

    def get_latest_quote(self, symbol: str) -> dict:
        req = StockLatestQuoteRequest(symbol_or_symbols=symbol)
        quote = self.data.get_stock_latest_quote(req)[symbol]
        return {
            "symbol": symbol,
            "ask_price": float(quote.ask_price),
            "bid_price": float(quote.bid_price),
            "mid": round((float(quote.ask_price) + float(quote.bid_price)) / 2, 2),
        }

    def is_market_open(self) -> bool:
        clock = self.trading.get_clock()
        return clock.is_open
