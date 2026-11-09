// Tab switching. The active tab lives in the URL hash so auto-reload keeps it.
(function () {
  const tabs = document.querySelectorAll(".tab");
  const panels = { swing: "tab-swing", range: "tab-range", special: "tab-special", discount: "tab-discount" };

  function show(name) {
    if (!panels[name]) name = "swing";
    tabs.forEach((t) => {
      const on = t.dataset.tab === name;
      t.classList.toggle("active", on);
      t.setAttribute("aria-selected", on);
    });
    Object.entries(panels).forEach(([key, id]) => {
      document.getElementById(id).hidden = key !== name;
    });
  }

  tabs.forEach((t) =>
    t.addEventListener("click", () => {
      history.replaceState(null, "", `#${t.dataset.tab}`);
      show(t.dataset.tab);
    })
  );
  show(location.hash.slice(1));
})();
