# Tokyo Weather · dashboard

Read-only paper-trading dashboard for the **Tokyo daily-temperature** Polymarket strategy — the Hong Kong
temperature-prediction approach ported to Tokyo as a forward test. Live at
**https://rexlau-prog.github.io/tokyo-weather-dashboard/**.

The page (`index.html`) is a fixed shell that fetches **`data.json`** every 60 s and renders it. To update the
dashboard, the strategy box overwrites `data.json` and pushes — no HTML regeneration needed.

Part of the strategy hub: **https://rexlau-prog.github.io/**

The `data.json` contract is identical to the other dashboards in this hub — see
[`hk-weather-dashboard`](https://github.com/rexlau-prog/hk-weather-dashboard/blob/main/README.md) for the full
field-by-field schema. In short:

```jsonc
{
  "display_name": "Tokyo Weather",
  "status": "paper",                 // "awaiting" | "paper" | "live" | "archived"
  "generated_utc": "2026-07-22T14:00:00Z",   // null => amber "awaiting data" banner
  "source_box": "aws-dublin",
  "currency": "USD",
  "kpis": { "book_equity": null, "start_equity": null, "realized_pnl": null, "return_pct": null,
            "open_positions": null, "closed_trades": null, "win_rate_pct": null, "note": "" },
  "equity_curve": { "labels": [], "values": [] },
  "sleeves":        [ /* { name, trades, win_pct, pnl, pf } */ ],
  "open_positions": [ /* { market, side, notional, opened } */ ],
  "recent_trades":  [ /* { time, market, side, reason, return_pct, pnl } */ ],
  "recent_signals": [ /* { time, market, side, detail } */ ]
}
```

Any numeric field set to `null` (or omitted) renders as `—`, so partial pushes are safe.
