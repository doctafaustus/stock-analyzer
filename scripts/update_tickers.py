"""Build tickers.json from Wikipedia: S&P 500 + Nasdaq-100, with GICS sectors.

Run:  python scripts/update_tickers.py   (update_data.py also runs this when the file is >30 days old)
"""
import io
import json
from datetime import date
from pathlib import Path

import pandas as pd
import requests

OUT = Path(__file__).resolve().parent / "tickers.json"
SOURCES = {
    "S&P 500": "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
    "Nasdaq-100": "https://en.wikipedia.org/wiki/List_of_NASDAQ-100_companies",
}
# Nasdaq-100 page uses ICB industries; map them to the same short names.
ICB = {
    "Technology": "Tech", "Telecommunications": "Comm", "Consumer Discretionary": "Cons Disc",
    "Consumer Staples": "Staples", "Financials": "Financials", "Health Care": "Health",
    "Energy": "Energy", "Industrials": "Industrials", "Basic Materials": "Materials",
    "Utilities": "Utilities", "Real Estate": "Real Estate",
}
SECTORS = {
    "Information Technology": "Tech", "Communication Services": "Comm",
    "Consumer Discretionary": "Cons Disc", "Consumer Staples": "Staples",
    "Financials": "Financials", "Health Care": "Health", "Energy": "Energy",
    "Industrials": "Industrials", "Materials": "Materials", "Utilities": "Utilities",
    "Real Estate": "Real Estate",
}


def tables(url):
    html = requests.get(url, headers={"User-Agent": "stock-analyzer/1.0 (personal research script)"},
                        timeout=30).text
    return pd.read_html(io.StringIO(html))


def pick(tbls, sym_cols, sector_prefix, mapping):
    """Find the constituents table; columns may carry footnote markers like 'ICB Industry[2]'."""
    for t in tbls:
        cols = [str(c) for c in t.columns]
        sym = next((c for c in sym_cols if c in cols), None)
        sec = next((c for c in cols if c.startswith(sector_prefix)), None)
        if sym and sec and len(t) > 90:
            return {str(s).strip().replace(".", "-"): mapping.get(str(x).strip(), "Other")
                    for s, x in zip(t[sym], t[sec])}
    raise RuntimeError("Expected table not found; Wikipedia layout may have changed.")


def main():
    sp = pick(tables(SOURCES["S&P 500"]), ["Symbol"], "GICS Sector", SECTORS)
    ndx = pick(tables(SOURCES["Nasdaq-100"]), ["Ticker", "Symbol"], "ICB Industry", ICB)
    merged = {**ndx, **sp}  # S&P sector wins on overlap
    OUT.write_text(json.dumps({"updated": date.today().isoformat(), "count": len(merged),
                               "tickers": dict(sorted(merged.items()))}, indent=1), encoding="utf-8")
    print(f"S&P 500: {len(sp)}  Nasdaq-100: {len(ndx)}  combined: {len(merged)} -> {OUT}")


if __name__ == "__main__":
    main()
