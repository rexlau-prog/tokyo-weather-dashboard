#!/usr/bin/env python3
"""
generate_data.py — emits data.json for the Tokyo Weather dashboard from the live
paper record in hk_temp.db (table: tokyo_late).

Tokyo late-entry pilot: buy the entered bucket 10-45 min AFTER the RJTT METAR print
(deliberately late, no race), first crossing >=13:00 JST, no-rain filter. Record mode.

Run on the box that owns hk_temp.db, or pass --db:

    python generate_data.py                       # writes ./data.json
    python generate_data.py --stdout              # print JSON (for piping over ssh)
    python generate_data.py --db /path/hk_temp.db

If the DB isn't found it leaves data.json untouched. Schema documented in README.md.
NOTE: DB stores per-trade P&L, not a bankroll → equity curve is BOOK_BASE + cumulative
realized P&L; $ P&L = recorded per-share pnl × recorded position size (shares).
"""

from __future__ import annotations
import argparse, json, sqlite3, sys
from datetime import datetime, timezone
from pathlib import Path

BOOK_BASE  = 1000.0
SOURCE_BOX = "aws-dublin"
CURRENCY   = "USD"
DEFAULT_DB = Path.home() / "pm_crypto_trend" / "hk_temp" / "hk_temp.db"
OUT_PATH   = Path(__file__).with_name("data.json")


def _usd(r: dict):
    if r["pnl"] is None or r["shares"] is None:
        return None
    return r["pnl"] * r["shares"]


def build(db_path: Path) -> dict:
    c = sqlite3.connect(str(db_path)); c.row_factory = sqlite3.Row
    T = [dict(r) for r in c.execute("select * from tokyo_late order by ts")]

    trades_r = [r for r in T if r["decision"] == "late_paper" and r["resolved"]]
    open_r   = [r for r in T if r["decision"] == "late_paper" and not r["resolved"]]
    usd      = {id(r): _usd(r) for r in trades_r}
    total    = sum(v for v in usd.values() if v is not None)
    wins     = sum(1 for v in usd.values() if v and v > 0)

    wins_sum = sum(v for v in usd.values() if v and v > 0)
    loss_sum = sum(-v for v in usd.values() if v and v < 0)
    pf = round(wins_sum / loss_sum, 2) if loss_sum > 0 else None

    kpis = {
        "book_equity":    round(BOOK_BASE + total, 2),
        "start_equity":   BOOK_BASE,
        "realized_pnl":   round(total, 2),
        "return_pct":     round(100 * total / BOOK_BASE, 2),
        "open_positions": len(open_r),
        "closed_trades":  len(trades_r),
        "win_rate_pct":   round(100 * wins / len(trades_r)) if trades_r else 0,
        "note":           "late-entry pilot · record mode · nominal $1k book",
    }

    # equity curve: nominal base, then cumulative realized by date
    by_date: dict[str, float] = {}
    for r in trades_r:
        by_date[r["date"]] = by_date.get(r["date"], 0.0) + (usd[id(r)] or 0.0)
    labels, values, cum = ["base"], [BOOK_BASE], BOOK_BASE
    for d in sorted(by_date):
        cum += by_date[d]
        labels.append(d[5:]); values.append(round(cum, 2))

    sleeves = [{
        "name": "Tokyo late-entry", "trades": len(trades_r),
        "win_pct": round(100 * wins / len(trades_r)) if trades_r else 0,
        "pnl": round(total, 2), "pf": pf,
    }]

    open_positions = [{
        "market": f'Tokyo {r["bucket"]} {r["date"][5:]}', "side": "yes",
        "notional": f'${(r["exec_cost"] or 0) * (r["shares"] or 0):.0f}',
        "opened": f'{r["date"][5:]} {r["tau_jst"]} JST',
    } for r in open_r]

    trades = []
    for r in trades_r:
        v = usd[id(r)]
        trades.append({"_ts": r["ts"], "time": r["date"][5:],
            "market": f'Tokyo {r["bucket"]}', "side": "yes",
            "reason": f'won · {r["winner"]}' if (v and v > 0) else f'lost · {r["winner"]}',
            "return_pct": round(100 * r["pnl"] / r["exec_cost"], 1) if r["exec_cost"] else None,
            "pnl": round(v, 2) if v is not None else None})
    trades.sort(key=lambda x: x["_ts"], reverse=True)
    for t in trades:
        t.pop("_ts")

    signals = []
    for r in T:
        signals.append({"_ts": r["ts"], "time": r["date"][5:], "market": "Tokyo late",
            "side": ("enter" if r["decision"] == "late_paper" else r["decision"]),
            "detail": f'{r["bucket"]} @ {r["exec_cost"]} ×{r["shares"]:.0f}sh '
                      f'(print +{r["print_age_min"]:.0f}min, book ${r["book_usd"]:.0f})'})
    signals.sort(key=lambda x: x["_ts"], reverse=True)
    for s in signals:
        s.pop("_ts")

    return {
        "display_name":   "Tokyo Weather",
        "status":         "paper",
        "generated_utc":  datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_box":     SOURCE_BOX,
        "currency":       CURRENCY,
        "kpis":           kpis,
        "equity_curve":   {"labels": labels, "values": values},
        "sleeves":        sleeves,
        "open_positions": open_positions,
        "recent_trades":  trades[:15],
        "recent_signals": signals[:12],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--stdout", action="store_true")
    a = ap.parse_args()
    if not Path(a.db).exists():
        print(f"[generate_data] DB not found at {a.db}; leaving data.json untouched", file=sys.stderr)
        sys.exit(0)
    payload = build(Path(a.db))
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if a.stdout:
        sys.stdout.write(text)
    else:
        OUT_PATH.write_text(text)
        print(f"wrote {OUT_PATH}  (closed={payload['kpis']['closed_trades']}, "
              f"pnl={payload['kpis']['realized_pnl']}, gen={payload['generated_utc']})")


if __name__ == "__main__":
    main()
