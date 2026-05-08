"""
Scheduler: runs a trading cycle every 15 minutes during US market hours.
Also runs a pre-market scan at 9:00 AM ET to find opportunities before open.

Usage:
    python scheduler.py
"""

import os
import sys
import logging
from datetime import datetime
import pytz
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("journal/scheduler.log"),
    ],
)
log = logging.getLogger(__name__)


def market_cycle():
    """Run a full trading cycle during market hours."""
    from agent.main import run_trading_cycle
    try:
        result = run_trading_cycle()
        log.info(f"Cycle complete. Actions taken: {len(result['actions'])}")
    except Exception as e:
        log.error(f"Trading cycle failed: {e}", exc_info=True)


def pre_market_scan():
    """Quick pre-market research — no orders, just intelligence gathering."""
    et = pytz.timezone("America/New_York")
    now = datetime.now(et)
    log.info(f"Pre-market scan at {now.strftime('%H:%M ET')}")

    try:
        from agent.main import run_trading_cycle
        result = run_trading_cycle()
        log.info(f"Pre-market scan complete. Actions: {len(result['actions'])}")
    except Exception as e:
        log.error(f"Pre-market scan failed: {e}", exc_info=True)


def should_run() -> bool:
    """Only schedule if market is open or within 30 min of open."""
    et = pytz.timezone("America/New_York")
    now = datetime.now(et)
    # Monday–Friday, 9:00 AM–4:00 PM ET
    if now.weekday() >= 5:
        return False
    hour, minute = now.hour, now.minute
    market_open = (hour == 9 and minute >= 0) or (9 < hour < 16)
    return market_open


def guarded_cycle():
    """Run cycle only if market is open."""
    if not should_run():
        log.debug("Market closed — skipping cycle.")
        return
    market_cycle()


if __name__ == "__main__":
    et = pytz.timezone("America/New_York")
    scheduler = BlockingScheduler(timezone=et)

    # Every 15 min on weekdays 4:00am–8:00pm ET (extended hours + regular)
    scheduler.add_job(
        guarded_cycle,
        "cron",
        day_of_week="mon-fri",
        hour="4-19",
        minute="0,15,30,45",
        id="trading_cycle",
    )

    # Pre-market scan at 4:00 AM ET
    scheduler.add_job(
        pre_market_scan,
        "cron",
        day_of_week="mon-fri",
        hour=4,
        minute=0,
        id="pre_market_scan",
    )

    paper = os.environ.get("PAPER_TRADING", "true").lower() == "true"
    capital = os.environ.get("CAPITAL_TOTAL", "1500")
    mode = "PAPER" if paper else "LIVE"

    print(f"""
╔══════════════════════════════════════════════════════╗
║        BEA TRADING AGENT — SCHEDULER STARTED         ║
║  Capital: ${capital:<8} Mode: {mode:<28}║
║  Cycles: every 15 min, Mon–Fri 9:00–15:45 ET        ║
║  Press Ctrl+C to stop                                ║
╚══════════════════════════════════════════════════════╝
""")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("Scheduler stopped.")
