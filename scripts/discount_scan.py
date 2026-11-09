"""Discount scan: stocks cheap vs their sector peers, still healthy, with good volume.

Writes ../discount-data.js. Run after update_data.py (reuses its price/volume data).
Run:  python scripts/discount_scan.py

Valuation (vs same-sector peers, lower = cheaper):  forward P/E, EV/EBITDA, free-cash-flow yield
Quality gates (to avoid value traps): profitable, positive free cash flow, ROE >= 8%,
  earnings not collapsing, debt/equity < 2.5 (skipped for Financials/Real Estate)
Volume gate: >= $50M traded per day
"""
import json
import statistics as st
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from pathlib import Path

import yfinance as yf

ROOT = Path(__file__).resolve().parent.parent
CACHE = Path(__file__).resolve().parent / ".cache" / "fundamentals.json"
OUT = ROOT / "discount-data.js"
MIN_DOLLAR_VOL = 50e6
FIELDS = ["forwardPE", "trailingPE", "enterpriseToEbitda", "freeCashflow", "marketCap", "returnOnEquity",
          "debtToEquity", "earningsGrowth", "revenueGrowth", "profitMargins", "targetMeanPrice",
          "numberOfAnalystOpinions", "recommendationKey", "trailingEps", "forwardEps", "shortName"]


def load_rows():
    t = (ROOT / "data.js").read_text(encoding="utf-8")
    return json.loads(t[t.index("=") + 1:].rstrip().rstrip(";"))["rows"]


def load_cache():
    try:
        d = json.loads(CACHE.read_text())
        return d["data"] if d.get("day") == date.today().isoformat() else {}
    except Exception:
        return {}


def info(sym):
    for attempt in range(3):
        try:
            i = yf.Ticker(sym).info or {}
            return {k: i.get(k) for k in FIELDS}
        except Exception:
            time.sleep(2 * (attempt + 1))
    print(f"  skip {sym}", file=sys.stderr)
    return None


def cheapness(rows, key, lower_is_cheaper=True):
    """Percentile within sector: 1.0 = cheapest in its sector."""
    out = {}
    by_sec = {}
    for r in rows:
        if r.get(key) is not None:
            by_sec.setdefault(r["sector"], []).append(r)
    for sec, rs in by_sec.items():
        vals = sorted(r[key] for r in rs)
        n = max(len(vals) - 1, 1)
        for r in rs:
            p = vals.index(r[key]) / n
            out[r["sym"]] = 1 - p if lower_is_cheaper else p
    return out


def main():
    started = time.time()
    rows = [r for r in load_rows() if r["dollarVol"] >= MIN_DOLLAR_VOL]
    cache = load_cache()
    todo = [r["sym"] for r in rows if r["sym"] not in cache]
    with ThreadPoolExecutor(max_workers=8) as ex:
        for sym, f in zip(todo, ex.map(info, todo)):
            if f:
                cache[sym] = f
    CACHE.parent.mkdir(exist_ok=True)
    CACHE.write_text(json.dumps({"day": date.today().isoformat(), "data": cache}))

    stocks = []
    for r in rows:
        f = cache.get(r["sym"])
        if not f:
            continue
        fcf, mcap = f["freeCashflow"], f["marketCap"]
        fpe, ev = f["forwardPE"], f["enterpriseToEbitda"]
        s = dict(sym=r["sym"], name=f["shortName"], sector=r["sector"], price=r["price"],
                 exchange=r.get("exchange"), dollarVol=r["dollarVol"], relvol=r["relvol"],
                 ret6m=r["ret6m"], offHigh=r["offHigh"],
                 fpe=fpe if fpe and 0 < fpe < 200 else None,
                 evEbitda=ev if ev and 0 < ev < 200 else None,
                 fcfYield=fcf / mcap * 100 if fcf and mcap else None,
                 roe=f["returnOnEquity"], debtEq=f["debtToEquity"], epsGrowth=f["earningsGrowth"],
                 revGrowth=f["revenueGrowth"], margin=f["profitMargins"],
                 upside=(f["targetMeanPrice"] / r["price"] - 1) * 100 if f["targetMeanPrice"] else None,
                 analysts=f["numberOfAnalystOpinions"], rating=f["recommendationKey"])

        # Quality gates
        fin = r["sector"] in ("Financials", "Real Estate")
        if not s["fpe"] or (f["trailingEps"] or 0) <= 0:
            continue
        if not fin and (s["fcfYield"] is None or s["fcfYield"] <= 0):
            continue
        if s["roe"] is not None and s["roe"] < 0.08:
            continue
        if s["epsGrowth"] is not None and s["epsGrowth"] < -0.15:
            continue
        if not fin and s["debtEq"] is not None and s["debtEq"] > 250:
            continue
        stocks.append(s)

    c_pe = cheapness(stocks, "fpe")
    c_ev = cheapness([s for s in stocks if s["sector"] not in ("Financials", "Real Estate")], "evEbitda")
    c_fcf = cheapness([s for s in stocks if s["sector"] not in ("Financials", "Real Estate")], "fcfYield", False)
    sec_pe = {sec: st.median(s["fpe"] for s in stocks if s["sector"] == sec)
              for sec in {s["sector"] for s in stocks}}

    for s in stocks:
        parts = [p[s["sym"]] for p in (c_pe, c_ev, c_fcf) if s["sym"] in p]
        s["valueScore"] = round(100 * sum(parts) / len(parts))
        s["sectorPE"] = sec_pe[s["sector"]]
        s["peDiscount"] = (s["fpe"] / s["sectorPE"] - 1) * 100

    # "Criminally undervalued": top of sector on valuation AND P/E well below sector median.
    picks = [s for s in stocks if s["valueScore"] >= 70 and s["peDiscount"] <= -25]
    picks.sort(key=lambda s: (-s["valueScore"], s["peDiscount"]))
    picks = picks[:30]

    OUT.write_text("window.DISCOUNT_DATA = " + json.dumps(dict(
        generatedAt=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        screened=len(rows), passedQuality=len(stocks), picks=picks), indent=1) + ";\n", encoding="utf-8")

    print(f"{len(rows)} liquid stocks, {len(stocks)} passed quality, {len(picks)} discount picks "
          f"in {time.time() - started:.0f}s -> {OUT}")
    for s in picks:
        print(f"  {s['sym']:5} {s['sector']:11} score {s['valueScore']:3}  fPE {s['fpe']:5.1f} "
              f"(sector {s['sectorPE']:5.1f}, {s['peDiscount']:+.0f}%)  EV/EBITDA {s['evEbitda'] or 0:5.1f}  "
              f"FCF yld {s['fcfYield'] or 0:5.1f}%  ROE {100 * (s['roe'] or 0):4.0f}%  "
              f"EPS gr {100 * (s['epsGrowth'] or 0):+4.0f}%  upside {s['upside'] or 0:+4.0f}%  "
              f"6M {s['ret6m']:+.0f}%  relvol {s['relvol']:.2f}")


if __name__ == "__main__":
    main()
