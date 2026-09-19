# Coin: context file (read this first)

Any new Claude chat continuing this project should read this file, then the
latest files in `journal/`, before doing anything else.

- Repo: https://github.com/akastudiogdrive-droid/coin
- Dashboard: https://akastudiogdrive-droid.github.io/coin/
- Owner: Gareth. Doesn't edit code; Claude writes all changes, Gareth uploads them.

## What Coin is
A self-running daily research system with two strands, sharing one engine
(daily GitHub Actions run, forecast log with auto-grading, journal, dashboard).

### Strand 1: Markets (intellectual interest only, never trading or advice)
- ~25-asset watchlist: UK stocks, US stocks, crypto, commodities (`config/watchlist.yml`)
- Pluggable context sources (`coin/sources/`): add one module + one line to register
- Composite "meta sentiment" score per asset, −100..+100, with direction and horizon
- Every forecast timestamped, auto-graded, compared with an "always up" baseline
- Planned: correlation analysis with out-of-sample testing and multiple-testing
  correction; Buffett layer (margin of safety, moat, "fearful when others greedy")

### Strand 2: Opportunities (real money, small bets)
Spot low-cost physical items tied to set events or early trends; buy small, sell
before the market floods.
- Bets under £100 each to start; sell on eBay and Amazon; source from
  AliExpress/Temu or whatever's cheapest; mix of self-posting and FBA; UK first
- Gareth's capacity: ~1 hr per weekday + a few hours at weekends → max 3–4 live bets
- Nothing borderline illegal; otherwise suggest everything with risk flags and
  Gareth decides case by case. Hard exclusions: counterfeits, IP-infringing items
- Picks must be granular: specific occasions and niches, never whole seasons
- Three views: Now (short-term picks), Calendar (1–12 months), Planning (>12 months)
- Reliability rule: a pick needs ≥2 independent agreeing signals; otherwise "watch".
  Timing labels are honest about the trade-off (thin evidence early vs strong but late)
- Trend hierarchy wave → trend → item, with lifecycle stage at each level
  (emerging, rising, peak, saturating, fading), item position vs sibling items,
  saturation from eBay listing growth and falling prices
- Gap finder: v1 = "quiet items in rising trends"; phase 2 = attribute
  combinations nobody sells yet, and launching our own mini trends
- Picks are logged as forecasts ("interest higher in ~4 weeks") and graded
- PRIVACY: the repo is public. Gareth's real purchases, costs and profits stay in a
  private Excel sheet in his OneDrive, never in this repo

## Layout
- `config/watchlist.yml`: markets watchlist
- `config/opportunities/trend_map.yml`: waves/trends/items (starter hypotheses, 2026-09-19)
- `config/opportunities/events.yml`: dated events + weather triggers (dates unverified)
- `config/opportunities/fees.yml`: platform fees for the margin model (check rates)
- `coin/run.py`: daily entry point; `coin/signals.py`, `coin/forecasts.py`
- `coin/sources/`: prices (Yahoo via yfinance), fear & greed, London weather
- `coin/opps/`: interest signals, trend analysis, calendar
- `data/`: all collected data (CSV) + `forecasts.csv` + `run_log.csv`
- `journal/`: one auto-written entry per day; Claude adds "why" analysis in chat
- `docs/`: dashboard (GitHub Pages) + `docs/data/dashboard.json`

## Data sources and known limits
- Yahoo Finance (yfinance, unofficial): occasional gaps
- Google Trends (pytrends, unofficial): often rate-limited from cloud servers;
  items are rotated, ~10 per run, each refreshed every 2+ days
- Wikipedia pageviews: reliable; trend-level only
- eBay Browse API: needs free developer keys stored as repo secrets
  EBAY_CLIENT_ID / EBAY_CLIENT_SECRET. Until added, most picks stay "watch"
- No free official source for eBay sold prices or Amazon bestseller ranks

## Status
- 2026-09-19: v0.1 built (both strands, dashboard). Awaiting upload and first run.

## Next steps
1. Upload batch 1, enable Pages, trigger first run, check the Sources tab
2. eBay developer keys → saturation signal and second independent signal
3. Verify event dates; fill unit_cost / sell_price on promising items
4. Batch 2: correlation engine + Buffett layer; trend-map expansion from data
5. Phase 2: attribute gap finder; own mini-trend launches

## Decisions log
- 2026-09-19: GitHub (public) + Actions + Pages chosen; free data first
- 2026-09-19: Opportunities lives inside Coin as its own module
- 2026-09-19: Personal P&L kept off the public repo (OneDrive Excel)
