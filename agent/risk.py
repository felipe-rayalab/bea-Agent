import os
from broker.alpaca_client import AlpacaClient


class RiskGuard:
    """Pre-flight risk checks before the agent acts."""

    def __init__(self, client: AlpacaClient):
        self.client = client
        self.max_position_pct = float(os.environ.get("MAX_POSITION_PCT", 0.30))
        self.stop_loss_pct = float(os.environ.get("STOP_LOSS_PCT", 0.15))
        self.max_positions = int(os.environ.get("MAX_OPEN_POSITIONS", 3))

    def max_position_value(self) -> float:
        acct = self.client.get_account()
        return acct["portfolio_value"] * self.max_position_pct

    def can_open_new_position(self) -> tuple[bool, str]:
        positions = self.client.get_positions()
        if len(positions) >= self.max_positions:
            return False, f"Already at max {self.max_positions} open positions"
        return True, "ok"

    def check_stop_losses(self) -> list[dict]:
        """Return positions that breached stop-loss threshold."""
        positions = self.client.get_positions()
        triggered = []
        for p in positions:
            if float(p["unrealized_plpc"]) <= -self.stop_loss_pct:
                triggered.append(p)
        return triggered

    def enforce_stop_losses(self) -> list[dict]:
        """Close any position that hit stop-loss. Returns closed positions."""
        triggered = self.check_stop_losses()
        closed = []
        for p in triggered:
            result = self.client.close_position(p["symbol"])
            closed.append({"symbol": p["symbol"], "plpc": p["unrealized_plpc"], "result": result})
        return closed

    def max_shares_for_symbol(self, symbol: str, price: float) -> int:
        if price <= 0:
            return 0
        max_val = self.max_position_value()
        acct = self.client.get_account()
        affordable = min(max_val, acct["cash"])
        return max(0, int(affordable // price))
