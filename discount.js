// Discount tab: undervalued vs sector, healthy, liquid.
(function () {
  const data = window.DISCOUNT_DATA;
  const tbody = document.getElementById("discount-rows");
  const meta = document.getElementById("discount-meta");
  const empty = document.getElementById("discount-empty");
  const headers = document.querySelectorAll("#discount-table th[data-key]");
  const picks = (data && data.picks) || [];

  meta.textContent = data
    ? `Stocks priced well below their sector peers that are still healthy and heavily traded · ` +
      `updated ${new Date(data.generatedAt).toLocaleString()} · ${picks.length} picks from ` +
      `${data.passedQuality} healthy stocks (${data.screened} screened)`
    : "Stocks priced well below their sector peers that are still healthy and heavily traded";

  picks.forEach((p, i) => (p.rank = i + 1));
  let sortKey = "rank";
  let sortAsc = true;

  const pct = (v, digits = 1) => (v == null ? "&ndash;" : `${v > 0 ? "+" : ""}${v.toFixed(digits)}%`);
  const ratio = (v) => (v == null ? "&ndash;" : v.toFixed(1));
  const frac = (v) => (v == null ? "&ndash;" : `${(v * 100).toFixed(0)}%`);
  const fracSigned = (v) => (v == null ? "&ndash;" : pct(v * 100, 0));
  const cls = (v) => (v == null ? "" : v > 0 ? "up" : v < 0 ? "down" : "");
  const money = (v) => (v >= 1e9 ? `$${(v / 1e9).toFixed(1)}B` : `$${(v / 1e6).toFixed(0)}M`);
  const chartUrl = (p) =>
    p.exchange
      ? `https://www.google.com/finance/quote/${p.sym}:${p.exchange}`
      : `https://www.google.com/search?q=${encodeURIComponent(p.sym + " stock")}`;

  function compare(a, b) {
    const x = a[sortKey], y = b[sortKey];
    if (x == null && y == null) return 0;
    if (x == null) return 1;
    if (y == null) return -1;
    if (typeof x === "string") return sortAsc ? x.localeCompare(y) : y.localeCompare(x);
    return sortAsc ? x - y : y - x;
  }

  function render() {
    const rows = [...picks].sort(compare);
    tbody.innerHTML = rows
      .map(
        (p) => `<tr>
          <td>${p.rank}</td>
          <td class="sym"><a href="${chartUrl(p)}" target="_blank" rel="noopener">${p.sym}</a>
            <span class="co-name">${p.name || ""}</span></td>
          <td>${p.sector}</td>
          <td class="num">${p.price.toFixed(2)}</td>
          <td class="num"><strong>${p.valueScore}</strong></td>
          <td class="num">${ratio(p.fpe)}</td>
          <td class="num up">${pct(p.peDiscount, 0)}</td>
          <td class="num">${ratio(p.evEbitda)}</td>
          <td class="num">${p.fcfYield ? pct(p.fcfYield).replace("+", "") : "&ndash;"}</td>
          <td class="num">${p.roe ? frac(p.roe) : "&ndash;"}</td>
          <td class="num ${cls(p.epsGrowth)}">${fracSigned(p.epsGrowth)}</td>
          <td class="num ${cls(p.upside)}">${pct(p.upside, 0)}</td>
          <td class="num">${money(p.dollarVol)}</td>
          <td class="num">${p.relvol.toFixed(2)}&times;</td>
          <td class="num ${cls(p.ret6m)}">${pct(p.ret6m, 0)}</td>
        </tr>`
      )
      .join("");
    empty.hidden = rows.length > 0;
    headers.forEach((th) => {
      th.classList.toggle("sorted", th.dataset.key === sortKey);
      th.classList.toggle("asc", th.dataset.key === sortKey && sortAsc);
    });
  }

  headers.forEach((th) =>
    th.addEventListener("click", () => {
      const key = th.dataset.key;
      if (key === sortKey) sortAsc = !sortAsc;
      else {
        sortKey = key;
        // Cheaper-first for valuation ratios; biggest-first for the rest.
        sortAsc = ["rank", "sym", "sector", "fpe", "evEbitda", "peDiscount"].includes(key);
      }
      render();
    })
  );

  render();
})();
