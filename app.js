(function () {
  const data = window.STOCK_DATA;
  const tbody = document.getElementById("rows");
  const meta = document.getElementById("meta");
  const empty = document.getElementById("empty");
  const setupFilter = document.getElementById("setupFilter");
  const hideEarnings = document.getElementById("hideEarnings");
  const headers = document.querySelectorAll("#tab-swing th[data-key]");

  if (!data) {
    meta.textContent = "No data yet. Run: python scripts/update_data.py";
    return;
  }

  const generated = new Date(data.generatedAt);
  const ageHours = (Date.now() - generated) / 36e5;
  const candidates = data.rows.filter((r) => r.setup).length;
  meta.innerHTML =
    `Prices as of close/last trade on <strong>${data.lastBar}</strong> · ` +
    `updated ${generated.toLocaleString()} · ${candidates} candidates from ${data.scanned} stocks` +
    (ageHours > 12 ? ' · <span class="stale">Data is over 12 hours old</span>' : "");

  data.rows.forEach((r, i) => (r.rank = i + 1));

  let sortKey = "rank";
  let sortAsc = true;

  const fmtPct = (v) => `${v > 0 ? "+" : ""}${v.toFixed(1)}%`;
  const cls = (v) => (v > 0 ? "up" : v < 0 ? "down" : "");

  function visibleRows() {
    const mode = setupFilter.value;
    return data.rows.filter((r) => {
      if (mode === "candidates" && !r.setup) return false;
      if (mode !== "candidates" && mode !== "all" && r.setup !== mode) return false;
      if (hideEarnings.checked && r.earningsSoon) return false;
      return true;
    });
  }

  function compare(a, b) {
    let x = a[sortKey], y = b[sortKey];
    if (x == null && y == null) return 0;
    if (x == null) return 1;
    if (y == null) return -1;
    if (typeof x === "string") return sortAsc ? x.localeCompare(y) : y.localeCompare(x);
    return sortAsc ? x - y : y - x;
  }

  function chartUrl(r) {
    return r.exchange
      ? `https://www.google.com/finance/quote/${r.sym}:${r.exchange}`
      : `https://www.google.com/search?q=${encodeURIComponent(r.sym + " stock")}`;
  }

  function setupTag(setup) {
    if (!setup) return "";
    const c = { "Volume Momentum": "momentum", "Pullback in Uptrend": "pullback", "Range Bounce": "range" }[setup] || "";
    return `<span class="tag ${c}">${setup}</span>`;
  }

  function render() {
    const rows = visibleRows().sort(compare);
    tbody.innerHTML = rows
      .map(
        (r) => `<tr class="${r.earningsSoon ? "earn-row" : ""}">
          <td>${r.rank}</td>
          <td class="sym"><a href="${chartUrl(r)}" target="_blank" rel="noopener">${r.sym}</a></td>
          <td>${r.sector}</td>
          <td>${setupTag(r.setup)}</td>
          <td class="num">${r.score}</td>
          <td class="num">${r.price.toFixed(2)}</td>
          <td class="num ${cls(r.chg1d)}">${fmtPct(r.chg1d)}</td>
          <td class="num ${cls(r.ret5d)}">${fmtPct(r.ret5d)}</td>
          <td class="num ${cls(r.ret1m)}">${fmtPct(r.ret1m)}</td>
          <td class="num ${cls(r.ret6m)}">${fmtPct(r.ret6m)}</td>
          <td class="num">${r.relvol.toFixed(2)}&times;</td>
          <td class="num">${r.rsi.toFixed(0)}</td>
          <td class="num">${fmtPct(r.offHigh)}</td>
          <td>${r.earnings ? `<span class="${r.earningsSoon ? "earn-soon" : ""}">${r.earnings}</span>` : ""}</td>
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
        sortAsc = ["rank", "sym", "sector", "setup", "earnings"].includes(key);
      }
      render();
    })
  );
  [setupFilter, hideEarnings].forEach((el) => el.addEventListener("change", render));
  render();

  // Custom tooltips for headers with data-tip.
  const tip = document.createElement("div");
  tip.className = "tooltip";
  document.body.appendChild(tip);

  document.querySelectorAll("[data-tip]").forEach((el) => {
    el.addEventListener("mouseenter", () => {
      const title = el.dataset.tipTitle ? `<strong>${el.dataset.tipTitle}</strong>` : "";
      tip.innerHTML = title + el.dataset.tip;
      const r = el.getBoundingClientRect();
      const w = tip.offsetWidth;
      const center = r.left + r.width / 2;
      const left = Math.min(Math.max(8, center - w / 2), window.innerWidth - w - 8);
      tip.style.left = `${left}px`;
      tip.style.top = `${r.bottom + 8}px`;
      tip.style.setProperty("--arrow-x", `${center - left}px`);
      tip.classList.add("show");
    });
    el.addEventListener("mouseleave", () => tip.classList.remove("show"));
  });
  window.addEventListener("scroll", () => tip.classList.remove("show"), true);

  // Auto-reload when served by scripts/serve.py and a file changes.
  if (location.protocol.startsWith("http")) {
    let current = null;
    setInterval(async () => {
      try {
        const { v } = await (await fetch("/__version", { cache: "no-store" })).json();
        if (current !== null && v !== current) location.reload();
        current = v;
      } catch (_) {}
    }, 1000);
  }
})();
