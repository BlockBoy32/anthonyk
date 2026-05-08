(function () {
  const btn = document.getElementById("themeBtn");
  const saved = localStorage.getItem("theme") || "light";
  if (saved === "dark") document.body.classList.add("dark-theme");
  btn.addEventListener("click", () => {
    document.body.classList.toggle("dark-theme");
    localStorage.setItem(
      "theme",
      document.body.classList.contains("dark-theme") ? "dark" : "light"
    );
  });

  const updated = document.getElementById("updated");
  updated.textContent = new Date().toLocaleString("en-US", {
    month: "long",
    year: "numeric",
  });

  const writingsEl = document.getElementById("writings");
  const FEED = "https://newontheblock.substack.com/feed";
  fetch("https://api.allorigins.win/raw?url=" + encodeURIComponent(FEED))
    .then((r) => (r.ok ? r.text() : Promise.reject(r.status)))
    .then((xml) => {
      const doc = new DOMParser().parseFromString(xml, "text/xml");
      const items = Array.from(doc.querySelectorAll("item")).slice(0, 5);
      if (!items.length) throw new Error("empty");
      writingsEl.innerHTML = items
        .map((item) => {
          const title = item.querySelector("title")?.textContent || "Untitled";
          const link = item.querySelector("link")?.textContent || "#";
          const pub = item.querySelector("pubDate")?.textContent;
          const year = pub ? new Date(pub).getFullYear() : "";
          return `• <a href="${link}">${title}</a>${year ? ` (${year})` : ""}`;
        })
        .join("<br />");
    })
    .catch(() => {
      writingsEl.innerHTML =
        'Read at <a href="https://newontheblock.substack.com">newontheblock.substack.com</a> →';
    });
})();
