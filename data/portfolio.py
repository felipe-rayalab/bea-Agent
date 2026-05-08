import json
import os
from datetime import datetime
from pathlib import Path
import httpx

JOURNAL_PATH = Path(__file__).parent.parent / "journal" / "trades.json"


def _post_to_vercel(payload: dict) -> None:
    url = os.environ.get("VERCEL_API_URL")
    if not url:
        return
    secret = os.environ.get("TRADES_API_SECRET", "")
    try:
        httpx.post(
            f"{url}/api/trades",
            json=payload,
            headers={"x-api-secret": secret},
            timeout=10,
        )
    except Exception:
        pass  # never block a trade because of dashboard errors


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
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "symbol": symbol,
        "qty": qty,
        "price": price,
        "reasoning": reasoning,
        "order": order_result,
        "portfolio": portfolio_snapshot,
    }

    # Write to local journal
    trades = load_journal()
    trades.append(entry)
    JOURNAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(JOURNAL_PATH, "w") as f:
        json.dump(trades, f, indent=2, default=str)

    # Post to Vercel dashboard
    _post_to_vercel(entry)


def log_cycle_summary(reasoning: str, actions_taken: list, portfolio_state: dict, session: str = "") -> None:
    """Post the cycle summary (agent reasoning) to the Vercel dashboard."""
    _post_to_vercel({
        "type": "cycle_summary",
        "timestamp": datetime.utcnow().isoformat(),
        "reasoning": reasoning,
        "actions_taken": actions_taken,
        "portfolio_state": portfolio_state,
        "session": session,
    })


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
