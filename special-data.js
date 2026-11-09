// Special Collection picks. Written by Claude when you ask for the Special scan.
// Each pick: { sym, sector, price, ret5d, stars (1-5), why, exchange }
window.SPECIAL_DATA = {
  generatedAt: "2026-11-09T07:40:00Z",
  note: "Based on Friday 11/6 close. Risk-off market: S&P 500 below its 50-day, Nasdaq-100 -12% in a month, VIX 25.6. Picks lean to the defensive sectors money is rotating into (Health, Staples, Utilities, Real Estate). No 5-star picks while the overall market is this weak.",
  picks: [
    {
      sym: "KDP", sector: "Staples", price: 36.63, ret5d: 2.2, stars: 4, exchange: "NASDAQ",
      why: "At its 52-week high in the strongest sector (91% of staples above 50-day). Up 7 of last 10 days with 2.4&times; more volume on up days than down days, so buyers are steadily accumulating. Low volatility, no earnings until next year."
    },
    {
      sym: "VRTX", sector: "Health", price: 547.09, ret5d: -2.1, stars: 4, exchange: "NASDAQ",
      why: "Health is the #1 sector (+10% this month, 90% breadth). 2% off its high, not overbought (RSI 65), steady accumulation (1.5&times; up/down volume). Last week&rsquo;s small dip on normal volume is a reasonable entry. No earnings soon."
    },
    {
      sym: "MDT", sector: "Health", price: 101.80, ret5d: 5.4, stars: 4, exchange: "NYSE",
      why: "Strong sector, volume 1.6&times; normal for a month with heavy buying on up days (1.9&times;). Friday&rsquo;s -2.9% came on very light volume, a benign dip. Low volatility. Earnings Nov 24, after the one-week window; stocks often run up into a report."
    },
    {
      sym: "WEC", sector: "Utilities", price: 115.87, ret5d: -0.2, stars: 4, exchange: "NYSE",
      why: "Defensive utility near its high with raised guidance. Up 7 of last 10 days, 2.2&times; up/down volume, and the lowest volatility on the list (about 2% a day). Exactly what tends to hold up in a nervous market. RSI 71 is a little warm."
    },
    {
      sym: "CRL", sector: "Health", price: 337.52, ret5d: -6.1, stars: 3, exchange: "NYSE",
      why: "Post-earnings drift setup: jumped 7.8% Friday after beating and raising guidance. Stocks often keep drifting up for weeks after a beat-and-raise. Volatile (6% daily range), so size smaller."
    },
    {
      sym: "EXPD", sector: "Industrials", price: 184.61, ret5d: -7.2, stars: 3, exchange: "NYSE",
      why: "Pullback in an uptrend where buyers kept showing up during the dip (1.5&times; volume on up days vs down days). Oversold (RSI 33). Industrials are only middling, which keeps it at 3 stars."
    },
    {
      sym: "OTIS", sector: "Industrials", price: 78.96, ret5d: 4.2, stars: 3, exchange: "NYSE",
      why: "Steady recurring-revenue name up 19% this month with 1.7&times; up/down volume and low volatility. RSI 72 is getting stretched, so a brief pause is possible before the next leg."
    },
    {
      sym: "KIM", sector: "Real Estate", price: 25.52, ret5d: 4.1, stars: 3, exchange: "NYSE",
      why: "Raised guidance, strong sector, near its high with steady buying. But RSI 79 is overbought and it&rsquo;s 7% above its 20-day average, so it may consolidate before moving higher."
    }
  ]
};
