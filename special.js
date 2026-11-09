// Special Collection tab.
(function () {
  const data = window.SPECIAL_DATA;
  const tbody = document.getElementById("special-rows");
  const meta = document.getElementById("special-meta");
  const empty = document.getElementById("special-empty");
  const picks = (data && data.picks) || [];

  if (data && data.generatedAt) {
    meta.textContent = `Picked ${new Date(data.generatedAt).toLocaleString()} · stocks most likely to swing up over the next week`;
    if (data.note) {
      const note = document.createElement("p");
      note.className = "special-note";
      note.textContent = data.note;
      meta.after(note);
    }
  } else {
    meta.textContent = "Stocks most likely to swing up over the next week";
  }

  const stars = (n) =>
    `<span class="stars" aria-label="${n} of 5 stars">` +
    `<span class="on">${"★".repeat(n)}</span><span class="off">${"☆".repeat(5 - n)}</span></span>`;

  const chartUrl = (p) =>
    p.exchange
      ? `https://www.google.com/finance/quote/${p.sym}:${p.exchange}`
      : `https://www.google.com/search?q=${encodeURIComponent(p.sym + " stock")}`;

  const fmtPct = (v) => (v == null ? "" : `${v > 0 ? "+" : ""}${v.toFixed(1)}%`);
  const cls = (v) => (v > 0 ? "up" : v < 0 ? "down" : "");

  const sorted = [...picks].sort((a, b) => b.stars - a.stars);
  tbody.innerHTML = sorted
    .map(
      (p, i) => `<tr>
        <td>${i + 1}</td>
        <td>${stars(p.stars)}</td>
        <td class="sym"><a href="${chartUrl(p)}" target="_blank" rel="noopener">${p.sym}</a></td>
        <td>${p.sector || ""}</td>
        <td class="num">${p.price != null ? p.price.toFixed(2) : ""}</td>
        <td class="num ${cls(p.ret5d)}">${fmtPct(p.ret5d)}</td>
        <td class="why">${p.why || ""}</td>
      </tr>`
    )
    .join("");
  empty.hidden = sorted.length > 0;
})();
