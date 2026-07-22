#!/usr/bin/env python3
"""
generate_data.py — emits data.json for the Tokyo Weather dashboard.

The dashboard shell (index.html) fetches ./data.json every 60s and renders it.
Fill in the collect_* functions below with your strategy's real source (DB query,
log parse, Polymarket API, ...), flip STATUS to "paper", then:

    python generate_data.py                                  # writes ./data.json
    git commit -am "data $(date -u +%FT%TZ)" && git push     # publish

Run as-is and it reproduces the current "awaiting first data push" state with a
real timestamp. Field-by-field schema is documented in README.md.
Any numeric field left as None renders as "—", so partial fills are safe.
"""

from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
STATUS     = "awaiting"          # "awaiting" -> amber banner. Flip to "paper" once wired.
SOURCE_BOX = "aws-dublin"
CURRENCY   = "USD"
OUT_PATH   = Path(__file__).with_name("data.json")


# ---------------------------------------------------------------------------
# Data collectors — replace the bodies with your real source
# ---------------------------------------------------------------------------
def collect_kpis() -> dict:
    # TODO: pull from your book / ledger.
    return {
        "book_equity":    None,
        "start_equity":   None,
        "realized_pnl":   None,   # signed; colours green/red
        "return_pct":     None,   # percent
        "open_positions": None,   # int
        "closed_trades":  None,   # int
        "win_rate_pct":   None,   # 0..100
        "note":           None,   # short free text
    }


def collect_equity_curve() -> dict:
    # TODO: (label, equity) points, oldest first.
    return {"labels": [], "values": []}


def collect_sleeves() -> list[dict]:
    # Per-sleeve breakdown (rendered under "Per-sleeve").
    return [
        # {"name": "Tokyo-high cross", "trades": 0, "win_pct": 0, "pnl": 0, "pf": 0.0},
    ]


def collect_open_positions() -> list[dict]:
    return [
        # {"market": "Tokyo-high-≥35C 07-22", "side": "yes", "notional": "$60", "opened": "07-22 03:10"},
    ]


def collect_recent_trades(limit: int = 15) -> list[dict]:
    # Newest first, capped at `limit`.
    return [
        # {"time": "07-21 06:00", "market": "Tokyo-high-≥34C", "side": "no",
        #  "reason": "settle", "return_pct": -1.4, "pnl": -2},
    ]


def collect_recent_signals(limit: int = 15) -> list[dict]:
    # Newest first, capped at `limit`.
    return [
        # {"time": "07-22 02:00", "market": "Tokyo-high-≥35C", "side": "yes", "detail": "cross @ 0.58"},
    ]


# ---------------------------------------------------------------------------
def build_payload() -> dict:
    return {
        "display_name":   "Tokyo Weather",
        "status":         STATUS,
        "generated_utc":  datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_box":     SOURCE_BOX,
        "currency":       CURRENCY,
        "kpis":           collect_kpis(),
        "equity_curve":   collect_equity_curve(),
        "sleeves":        collect_sleeves(),
        "open_positions": collect_open_positions(),
        "recent_trades":  collect_recent_trades(),
        "recent_signals": collect_recent_signals(),
    }


def main() -> None:
    p = build_payload()
    OUT_PATH.write_text(json.dumps(p, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {OUT_PATH}  (status={p['status']}, generated={p['generated_utc']})")


if __name__ == "__main__":
    main()
