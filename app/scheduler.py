"""Scheduler for daily digest - runs full pipeline at 1:30 PM EST"""

import os
import sys
import time
from zoneinfo import ZoneInfo
from datetime import datetime, timezone

TARGET_HOUR = 13
TARGET_MINUTE = 30
TZ = ZoneInfo("America/New_York")


def _log(msg: str) -> None:
    """Print with flush so Railway shows logs immediately"""
    print(f"[{datetime.now(timezone.utc).isoformat()}] {msg}", flush=True)


def run_daily_digest():
    """Job to run the full pipeline"""
    _log("Starting daily digest job...")
    try:
        from app.run import run
        run()
        _log("Daily digest job completed.")
    except Exception as e:
        _log(f"Daily digest job FAILED: {e}")
        import traceback
        traceback.print_exc(file=sys.stdout)
        sys.stdout.flush()
        raise


def start_scheduler():
    """Poll every minute - run digest at 1:30 PM EST"""
    _log("Scheduler starting (runs at 1:30 PM EST)...")
    if os.getenv("RUN_ON_STARTUP", "").lower() in ("1", "true", "yes"):
        _log("RUN_ON_STARTUP=true: running digest now...")
        run_daily_digest()

    last_run_date = None
    while True:
        now = datetime.now(TZ)
        if now.hour == TARGET_HOUR and now.minute == TARGET_MINUTE:
            today = now.date()
            if last_run_date != today:
                _log("It's 1:30 PM EST - triggering digest...")
                run_daily_digest()
                last_run_date = today
        time.sleep(60)
