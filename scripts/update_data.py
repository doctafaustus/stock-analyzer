"""Refresh swing-trade candidates and write ../data.js for the web page.

Run:  python scripts/update_data.py
Data: Yahoo Finance via yfinance (about 15 min delayed during market hours).

Setups:
  Volume Momentum      strong 1-month gain on heavy volume, above 50-day avg
                       (short-term momentum + high turnover research)
  Pullback in Uptrend  strong 6-month trend, above 200-day avg, 5-day dip of 3-12%, RSI < 45
  Range Bounce         sideways 8-25% channel over ~30 days, 4+ crosses of 20-day avg,
                       3-month change within +/-10%, now in bottom 25% of range, RSI < 40
                       (scored separately as rangeScore; shown on its own Range Bounce tab)
"""
import json
import math
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from pathlib import Path

import yfinance as yf

SCRIPTS = Path(__file__).resolve().parent
TICKERS = SCRIPTS / "tickers.json"
EARN_CACHE = SCRIPTS / ".cache" / "earnings.json"

# Liquidity filter: skip stocks that are hard to get in and out of.
MIN_PRICE = 10
MIN_DOLLAR_VOL = 20e6


def load_universe():
    """S&P 500 + Nasdaq-100 from tickers.json; rebuild it if missing or over 30 days old."""
    fresh = TICKERS.exists() and (
        date.today() - date.fromisoformat(json.loads(TICKERS.read_text())["updated"])).days <= 30
    if not fresh:
        import update_tickers
        update_tickers.main()
    return json.loads(TICKERS.read_text())["tickers"]


def load_earn_cache():
    try:
        d = json.loads(EARN_CACHE.read_text())
        return d["dates"] if d.get("day") == date.today().isoformat() else {}
    except Exception:
        return {}


EARN = {}

# Yahoo exchange codes -> Google Finance exchange names.
EXCHANGES = {"NMS": "NASDAQ", "NGM": "NASDAQ", "NCM": "NASDAQ", "NYQ": "NYSE",
             "ASE": "NYSEAMERICAN", "PCX": "NYSEARCA", "BTS": "BATS"}

OUT = Path(__file__).resolve().parent.parent / "data.js"


def sma(xs, n):
    return sum(xs[-n:]) / n


def rsi(closes, n=14):
    gains = losses = 0.0
    for i in range(len(closes) - n, len(closes)):
        d = closes[i] - closes[i - 1]
        gains += max(d, 0)
        losses += max(-d, 0)
    if losses == 0:
        return 100.0
    return 100 - 100 / (1 + gains / losses)


def pct(a, b):
    return (a / b - 1) * 100


def range_stats(c):
    """Trading range over the 30 sessions before the last 3, and where price sits in it now."""
    window = c[-33:-3]
    lo, hi = min(window), max(window)
    # How many times price crossed its 20-day average over the last 30 sessions.
    sides = [c[i] > sum(c[i - 19:i + 1]) / 20 for i in range(len(c) - 30, len(c))]
    crosses = sum(1 for a, b in zip(sides, sides[1:]) if a != b)
    return dict(rangeLo=lo, rangeHi=hi, rangeWidth=pct(hi, lo),
                rangePos=(c[-1] - lo) / (hi - lo) if hi > lo else None, crosses=crosses)


def history(t):
    for attempt in range(3):
        try:
            return t.history(period="1y", auto_adjust=True).dropna()
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))


def earnings_date(t, sym):
    if sym in EARN:
        return EARN[sym]
    d = None
    try:
        e = ((t.calendar or {}).get("Earnings Date") or [None])[0]
        d = e.isoformat() if e and e >= date.today() else None
    except Exception:
        pass
    EARN[sym] = d
    return d


def fetch(sym, sector):
    try:
        t = yf.Ticker(sym)
        h = history(t)
        if len(h) < 200:
            return None
        c, v = list(h["Close"]), list(h["Volume"])
        price = c[-1]
        vol21 = sum(v[-21:]) / 21
        vol_base = sum(v[-147:-21]) / 126
        row = dict(
            sym=sym, sector=sector, price=price,
            chg1d=pct(c[-1], c[-2]), ret5d=pct(c[-1], c[-6]), ret1m=pct(c[-1], c[-22]),
            ret6m=pct(c[-1], c[-127]),
            relvol=vol21 / vol_base if vol_base else None,
            relvol1d=v[-1] / (sum(v[-51:-1]) / 50),
            above50=price > sma(c, 50), above200=price > sma(c, 200),
            rsi=rsi(c), offHigh=pct(price, max(c[-252:])),
            dollarVol=price * vol21, lastBar=h.index[-1].date().isoformat(), earnings=None,
            exchange=EXCHANGES.get((t.history_metadata or {}).get("exchangeName")),
            ret3m=pct(c[-1], c[-64]),
            **range_stats(c),
        )
        # Only look up earnings for liquid stocks; saves requests.
        if price >= MIN_PRICE and row["dollarVol"] >= MIN_DOLLAR_VOL:
            row["earnings"] = earnings_date(t, sym)
        return row
    except Exception as e:
        print(f"  skip {sym}: {e}", file=sys.stderr)
        return None


def pct_rank(rows, key):
    vals = sorted(r[key] for r in rows)
    n = len(vals) - 1 or 1
    return {r["sym"]: vals.index(r[key]) / n for r in rows}


def main():
    started = time.time()
    EARN.update(load_earn_cache())
    jobs = list(load_universe().items())
    with ThreadPoolExecutor(max_workers=8) as ex:
        fetched = [r for r in ex.map(lambda j: fetch(*j), jobs) if r and r["relvol"]]
    rows = [r for r in fetched if r["price"] >= MIN_PRICE and r["dollarVol"] >= MIN_DOLLAR_VOL]

    EARN_CACHE.parent.mkdir(exist_ok=True)
    EARN_CACHE.write_text(json.dumps({"day": date.today().isoformat(), "dates": EARN}))

    r1m, rv, r6m, r5d = (pct_rank(rows, k) for k in ("ret1m", "relvol", "ret6m", "ret5d"))
    today = date.today()
    for r in rows:
        s = r["sym"]
        mom = (r1m[s] + rv[s] + r6m[s]) / 3
        pull = (r6m[s] + (1 - r5d[s])) / 2
        setups = []
        if r["ret1m"] > 8 and r["relvol"] > 1.25 and r["above50"]:
            setups.append(("Volume Momentum", mom))
        # Dip of 3-12%: bigger drops look like breakdowns, not pullbacks.
        if r["ret6m"] > 15 and r["above200"] and -12 < r["ret5d"] < -3 and r["rsi"] < 45:
            setups.append(("Pullback in Uptrend", pull))
        # Range Bounce: sideways stock swinging in a steady channel, now near the bottom.
        pos = r["rangePos"]
        if (pos is not None and 8 <= r["rangeWidth"] <= 25 and r["crosses"] >= 4
                and -10 <= r["ret3m"] <= 10 and pos <= 0.25 and r["rsi"] < 40
                and r["price"] >= r["rangeLo"] * 0.98):
            rng = (0.4 * (1 - max(pos, 0) / 0.25) + 0.3 * min(r["crosses"] / 8, 1)
                   + 0.3 * min((40 - r["rsi"]) / 20, 1))
            # Own tab on the page, scored separately from the swing setups.
            r["rangeScore"] = round((0.5 + rng / 2) * 100)
        else:
            r["rangeScore"] = None
        if setups:
            name, score = max(setups, key=lambda x: x[1])
            r["setup"], r["score"] = name, round(score * 100)
        else:
            r["setup"], r["score"] = None, round(max(mom, pull) * 100)
        r["earningsSoon"] = bool(r["earnings"] and (date.fromisoformat(r["earnings"]) - today).days <= 10)

    rows.sort(key=lambda r: (r["setup"] is None, -r["score"]))
    payload = dict(
        generatedAt=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        lastBar=max(r["lastBar"] for r in rows),
        scanned=len(rows), universe=len(jobs), universeName="S&P 500 + Nasdaq-100", rows=rows,
    )
    OUT.write_text("window.STOCK_DATA = " + json.dumps(payload, indent=1, default=float) + ";\n",
                   encoding="utf-8")
    n = sum(1 for r in rows if r["setup"])
    print(f"Fetched {len(fetched)}/{len(jobs)}, {len(fetched) - len(rows)} dropped as illiquid, "
          f"{len(rows)} kept. {n} candidates in {time.time() - started:.0f}s. Wrote {OUT}")
    from collections import Counter
    print("  by setup:", dict(Counter(r["setup"] for r in rows if r["setup"])))
    print(f"  range bounce: {sum(1 for r in rows if r['rangeScore'])}")
    for r in rows[:n][:25]:
        print(f"  {r['sym']:6} {r['setup']:20} score {r['score']:3}  1M {r['ret1m']:+6.1f}%  "
              f"relvol {r['relvol']:.2f}  5D {r['ret5d']:+5.1f}%  {'EARN ' + r['earnings'] if r['earningsSoon'] else ''}")


if __name__ == "__main__":
    main()
