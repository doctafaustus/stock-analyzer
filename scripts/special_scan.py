"""Deeper look at swing candidates to help pick the Special Collection.

Prints market context, sector strength, and per-candidate chart details + recent headlines.
Claude reads this output and writes special-data.js by hand.
Run:  python scripts/special_scan.py
"""
import json
import statistics as st
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yfinance as yf

ROOT = Path(__file__).resolve().parent.parent
SECTOR_ETF = {"Tech": "XLK", "Comm": "XLC", "Cons Disc": "XLY", "Staples": "XLP", "Financials": "XLF",
              "Health": "XLV", "Energy": "XLE", "Industrials": "XLI", "Materials": "XLB",
              "Utilities": "XLU", "Real Estate": "XLRE"}


def load_rows():
    t = (ROOT / "data.js").read_text(encoding="utf-8")
    return json.loads(t[t.index("=") + 1:].rstrip().rstrip(";"))


def closes(sym, period="1y"):
    h = yf.Ticker(sym).history(period=period, auto_adjust=True).dropna()
    return h


def trend(sym):
    h = closes(sym)
    c = list(h["Close"])
    sma = lambda n: sum(c[-n:]) / n
    return dict(sym=sym, price=c[-1], r5=(c[-1] / c[-6] - 1) * 100, r1m=(c[-1] / c[-22] - 1) * 100,
                a20=c[-1] > sma(20), a50=c[-1] > sma(50), a200=c[-1] > sma(200))


def detail(r):
    t = yf.Ticker(r["sym"])
    h = t.history(period="3mo", auto_adjust=True).dropna()
    c, hi, lo, v = list(h["Close"]), list(h["High"]), list(h["Low"]), list(h["Volume"])
    sma20 = sum(c[-20:]) / 20
    trs = [max(hi[i] - lo[i], abs(hi[i] - c[i - 1]), abs(lo[i] - c[i - 1])) for i in range(len(c) - 14, len(c))]
    atr = sum(trs) / 14
    up_days = sum(1 for i in range(len(c) - 10, len(c)) if c[i] > c[i - 1])
    # Accumulation: volume on up days vs down days over last 20 sessions
    upv = sum(v[i] for i in range(len(c) - 20, len(c)) if c[i] > c[i - 1])
    dnv = sum(v[i] for i in range(len(c) - 20, len(c)) if c[i] <= c[i - 1]) or 1
    gaps = [(c[i] / c[i - 1] - 1) * 100 for i in range(len(c) - 20, len(c))]
    big = max(gaps, key=abs)
    try:
        news = [n.get("content", n).get("title") for n in (t.news or [])[:3]]
    except Exception:
        news = []
    return dict(r, vs20=(c[-1] / sma20 - 1) * 100, atrPct=atr / c[-1] * 100, upDays10=up_days,
                udVol=upv / dnv, biggestMove20=big, news=[n for n in news if n])


def main():
    d = load_rows()
    rows = d["rows"]

    print("=== MARKET ===")
    with ThreadPoolExecutor(8) as ex:
        mk = list(ex.map(trend, ["SPY", "QQQ", "IWM", "^VIX"]))
    for m in mk:
        print(f"{m['sym']:5} {m['price']:9.2f}  5D {m['r5']:+5.1f}%  1M {m['r1m']:+5.1f}%  "
              f">20d {m['a20']}  >50d {m['a50']}  >200d {m['a200']}")

    print("\n=== SECTORS (ETF 1M vs SPY, breadth = % of sector stocks above 50d) ===")
    spy1m = mk[0]["r1m"]
    with ThreadPoolExecutor(8) as ex:
        secs = dict(zip(SECTOR_ETF, ex.map(trend, SECTOR_ETF.values())))
    for name, s in sorted(secs.items(), key=lambda kv: -kv[1]["r1m"]):
        members = [r for r in rows if r["sector"] == name]
        breadth = 100 * sum(r["above50"] for r in members) / max(len(members), 1)
        print(f"{name:12} {s['sym']:5} 1M {s['r1m']:+5.1f}% (rel {s['r1m'] - spy1m:+5.1f})  5D {s['r5']:+5.1f}%  "
              f"breadth {breadth:3.0f}%")

    print("\n=== CANDIDATES ===")
    cands = [r for r in rows if r["setup"]]
    with ThreadPoolExecutor(8) as ex:
        det = list(ex.map(detail, cands))
    for r in sorted(det, key=lambda r: -r["score"]):
        print(f"\n{r['sym']:5} {r['sector']:11} {r['setup']:20} score {r['score']:3}  ${r['price']:.2f}  "
              f"1D {r['chg1d']:+.1f}  5D {r['ret5d']:+.1f}  1M {r['ret1m']:+.1f}  6M {r['ret6m']:+.1f}  "
              f"RSI {r['rsi']:.0f}  offHi {r['offHigh']:.1f}  relvol {r['relvol']:.2f}  relvol1d {r['relvol1d']:.2f}")
        print(f"      vs20d {r['vs20']:+.1f}%  ATR {r['atrPct']:.1f}%  up days/10 {r['upDays10']}  "
              f"up/down vol {r['udVol']:.2f}  biggest 1-day move 20d {r['biggestMove20']:+.1f}%  "
              f"earnings {r['earnings']}  exch {r['exchange']}")
        for n in r["news"]:
            print(f"      - {n}")


if __name__ == "__main__":
    main()
