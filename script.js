(function () {
  const writingsList = document.getElementById("writings-list");

  function render(items) {
    if (!items || !items.length) {
      writingsList.innerHTML =
        '<li>Read at <a href="https://newontheblock.substack.com">newontheblock.substack.com</a></li>';
      return;
    }
    writingsList.innerHTML = "";
    items.forEach((it) => {
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.href = it.link;
      a.textContent = it.title + (it.year ? ` (${it.year})` : "");
      li.appendChild(a);
      writingsList.appendChild(li);
    });
  }

  // Prefer the JSON baked at deploy time; fall back to the RSS proxy if missing.
  fetch("writings.json", { cache: "no-store" })
    .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
    .then(render)
    .catch(() => {
      const FEED = "https://newontheblock.substack.com/feed";
      return fetch("https://api.allorigins.win/raw?url=" + encodeURIComponent(FEED))
        .then((r) => (r.ok ? r.text() : Promise.reject(r.status)))
        .then((xml) => {
          const doc = new DOMParser().parseFromString(xml, "text/xml");
          const items = Array.from(doc.querySelectorAll("item"))
            .slice(0, 8)
            .map((item) => {
              const title = item.querySelector("title")?.textContent || "Untitled";
              const link = item.querySelector("link")?.textContent || "#";
              const pub = item.querySelector("pubDate")?.textContent;
              const year = pub ? new Date(pub).getFullYear() : "";
              return { title, link, year };
            });
          render(items);
        })
        .catch(() => render(null));
    });
})();
