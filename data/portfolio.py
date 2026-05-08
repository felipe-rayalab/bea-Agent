import json
import os
from datetime import datetime
from pathlib import Path

JOURNAL_PATH = Path(__file__).parent.parent / "journal" / "trades.json"


def load_journal() -> list[dict]:
    if not JOURNAL_PATH.exists():
        return []
    with open(JOURNAL_PATH) as f:
        return json.load(f)


def log_trade(
    action: str,
    symbol: str,
    qty: float,
    price: float,
    reasoning: str,
    order_result: dict,
    portfolio_snapshot: dict,
):
    trades = load_journal()
    trades.append({
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "symbol": symbol,
        "qty": qty,
        "price": price,
        "reasoning": reasoning,
        "order": order_result,
        "portfolio": portfolio_snapshot,
    })
    JOURNAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(JOURNAL_PATH, "w") as f:
        json.dump(trades, f, indent=2, default=str)


def get_trade_summary() -> dict:
    trades = load_journal()
    if not trades:
        return {"total_trades": 0, "buys": 0, "sells": 0, "symbols_traded": []}
    buys = [t for t in trades if t["action"].lower() == "buy"]
    sells = [t for t in trades if t["action"].lower() == "sell"]
    symbols = list(set(t["symbol"] for t in trades))
    return {
        "total_trades": len(trades),
        "buys": len(buys),
        "sells": len(sells),
        "symbols_traded": symbols,
        "last_trade_at": trades[-1]["timestamp"],
    }
