import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="BEA Trading Agent")


@app.get("/api/portfolio")
def portfolio_state():
    from broker.alpaca_client import AlpacaClient
    client = AlpacaClient()
    return {
        "account": client.get_account(),
        "positions": client.get_positions(),
        "open_orders": client.get_open_orders(),
        "market_open": client.is_market_open(),
    }


@app.get("/api/journal")
def journal():
    from data.portfolio import load_journal, get_trade_summary
    return {
        "summary": get_trade_summary(),
        "trades": load_journal()[-50:],  # last 50
    }


@app.get("/", response_class=HTMLResponse)
def dashboard():
    with open(Path(__file__).parent / "templates" / "index.html") as f:
        return f.read()


if __name__ == "__main__":
    uvicorn.run("dashboard.app:app", host="0.0.0.0", port=8000, reload=True)
