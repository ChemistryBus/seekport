"""Optional daily spend ledger. Standard library only.

Append-only: one line per billed call. Short appends are atomic on POSIX, so
concurrent CLI processes cannot lose updates or corrupt the file. The ledger is
best-effort on write; an unreadable file blocks calls (fail closed), while a
torn line is ignored so it cannot lock the user out forever.
"""
from __future__ import annotations

import math
import os
from datetime import date
from pathlib import Path

from errors import ConfigError

PRICE_RMB_PER_CALL = 0.005      # ¥5 per 1,000 successful requests


def _file():
    base = os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache")
    return Path(base) / "seekport" / "spend.log"


def _cap():
    raw = os.environ.get("SEEKPORT_BUDGET", "").strip()
    if not raw:
        return None
    try:
        cap = float(raw)
    except ValueError:
        raise ConfigError("SEEKPORT_BUDGET must be a number of RMB, e.g. 0.05") from None
    if not math.isfinite(cap) or cap < 0:
        raise ConfigError("SEEKPORT_BUDGET must be a finite, non-negative number")
    return cap


def spent_today():
    try:
        text = _file().read_text()
    except FileNotFoundError:
        return 0.0
    except OSError:
        raise ConfigError(f"spend ledger {_file()} is unreadable") from None
    today = str(date.today())
    total = 0.0
    for line in text.splitlines():
        try:
            day, amount = line.split()
            value = float(amount)
        except ValueError:
            continue  # ignore a torn line rather than blocking every call
        if day == today and math.isfinite(value) and value >= 0:
            total += value
    return total


def check():
    cap = _cap()
    if cap is None:
        return
    spent = spent_today()
    if spent + PRICE_RMB_PER_CALL > cap + 1e-9:
        raise ConfigError(
            f"daily budget ¥{cap:.3f} reached (spent ¥{spent:.3f}); "
            "raise SEEKPORT_BUDGET or wait for tomorrow"
        )


def record():
    try:
        path = _file()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(f"{date.today()} {PRICE_RMB_PER_CALL}\n")
    except OSError:
        pass  # never fail a paid call over the ledger
