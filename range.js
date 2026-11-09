// Range Bounce tab: sideways stocks near the bottom of a steady channel.
(function () {
  const data = window.STOCK_DATA;
  const tbody = document.getElementById("range-rows");
  const meta = document.getElementById("range-meta");
  const empty = document.getElementById("range-empty");
  const hideEarnings = document.getElementById("rangeHideEarnings");
  const headers = document.querySelectorAll("#range-table th[data-key]");

  if (!data) {
    meta.textContent = "No data yet. Run: python scripts/update_data.py";
    return;
  }

  const rows = data.rows
    .filter((r) => r.rangeScore != null)
    .map((r) => ({ ...r, upside: ((r.rangeHi - r.price) / r.price) * 100 }))
    .sort((a, b) => b.rangeScore - a.rangeScore);
  rows.forEach((r, i) => (r.rank = i + 1));

  meta.innerHTML =
    `Prices as of close/last trade on <strong>${data.lastBar}</strong> · ` +
    `updated ${new Date(data.generatedAt).toLocaleString()} · ${rows.length} stocks from ${data.scanned} scanned`;

  let sortKey = "rank";
  let sortAsc = true;

  const fmtPct = (v) => `${v > 0 ? "+" : ""}${v.toFixed(1)}%`;
  const cls = (v) => (v > 0 ? "up" : v < 0 ? "down" : "");
  const chartUrl = (r) =>
    r.exchange
      ? `https://www.google.com/finance/quote/${r.sym}:${r.exchange}`
      : `https://www.google.com/search?q=${encodeURIComponent(r.sym + " stock")}`;

  function compare(a, b) {
    let x = a[sortKey], y = b[sortKey];
    if (x == null && y == null) return 0;
    if (x == null) return 1;
    if (y == null) return -1;
    if (typeof x === "string") return sortAsc ? x.localeCompare(y) : y.localeCompare(x);
    return sortAsc ? x - y : y - x;
  }

  function render() {
    const shown = rows.filter((r) => !(hideEarnings.checked && r.earningsSoon)).sort(compare);
    tbody.innerHTML = shown
      .map(
        (r) => `<tr class="${r.earningsSoon ? "earn-row" : ""}">
          <td>${r.rank}</td>
          <td class="sym"><a href="${chartUrl(r)}" target="_blank" rel="noopener">${r.sym}</a></td>
          <td>${r.sector}</td>
          <td class="num">${r.rangeScore}</td>
          <td class="num">${r.price.toFixed(2)}</td>
          <td class="num ${cls(r.chg1d)}">${fmtPct(r.chg1d)}</td>
          <td class="num ${cls(r.ret5d)}">${fmtPct(r.ret5d)}</td>
          <td class="num ${cls(r.ret3m)}">${fmtPct(r.ret3m)}</td>
          <td class="num">${r.rangeLo.toFixed(2)}</td>
          <td class="num">${r.rangeHi.toFixed(2)}</td>
          <td class="num">${r.rangeWidth.toFixed(1)}%</td>
          <td class="num">${Math.round(r.rangePos * 100)}%</td>
          <td class="num up">${fmtPct(r.upside)}</td>
          <td class="num">${r.crosses}</td>
          <td class="num">${r.rsi.toFixed(0)}</td>
          <td>${r.earnings ? `<span class="${r.earningsSoon ? "earn-soon" : ""}">${r.earnings}</span>` : ""}</td>
        </tr>`
      )
      .join("");
    empty.hidden = shown.length > 0;

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
        sortAsc = ["rank", "sym", "sector", "earnings", "rangePos"].includes(key);
      }
      render();
    })
  );
  hideEarnings.addEventListener("change", render);
  render();
})();
