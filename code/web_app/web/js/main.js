// THEME SWITCHER
const key = "theme";
const btn = document.getElementById("themeBtn");

function apply(theme) {
  document.documentElement.dataset.theme = theme || "";
  if (theme) localStorage.setItem(key, theme);
  else localStorage.removeItem(key);
}

const saved = localStorage.getItem(key);
if (saved) apply(saved);

btn?.addEventListener("click", () => {
  const cur = localStorage.getItem(key);
  const next = cur === "dark" ? "light" : cur === "light" ? null : "dark";
  apply(next);
});

// SERVICE STATUS CHECK
async function check(url, timeoutMs = 1800) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), timeoutMs);

  try {
    await fetch(url, { method: "HEAD", mode: "no-cors", signal: ctrl.signal });
    clearTimeout(t);
    return true;
  } catch {
    clearTimeout(t);
    return false;
  }
}

(async () => {
  const cards = [...document.querySelectorAll(".card[data-check]")];

  await Promise.all(
    cards.map(async (c) => {
      const url = c.getAttribute("data-check");
      const ok = await check(url);
      c.dataset.status = ok ? "up" : "down";
    }),
  );
})();
