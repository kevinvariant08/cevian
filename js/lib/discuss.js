// Per-problem discussion threads, hosted by giscus on the repo's GitHub Discussions. One thread per problem id.
// Until repoId and categoryId are filled in from giscus.app, the panel says discussion opens soon and loads nothing.
export const GISCUS = {
  repo: "kevinvariant08/cevian",
  repoId: "",        // data-repo-id from giscus.app
  category: "Problems",
  categoryId: ""     // data-category-id from giscus.app
};
export const giscusReady = () => !!(GISCUS.repoId && GISCUS.categoryId);

const ORIGIN = "https://giscus.app";
const theme = () => (document.documentElement.dataset.theme === "light" ? "light" : "dark");

// Keep an open thread in step with the theme button. Registered once; it does nothing while no thread is on the page.
new MutationObserver(() => {
  const f = document.querySelector("iframe.giscus-frame");
  if (f && f.contentWindow) f.contentWindow.postMessage({ giscus: { setConfig: { theme: theme() } } }, ORIGIN);
}).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });

// Loads giscus into el once it's nearly on screen, so a reader who never scrolls down never fetches it.
export function mountDiscussion(el, id) {
  if (!giscusReady()) return;
  const load = () => {
    const s = document.createElement("script");
    s.src = `${ORIGIN}/client.js`;
    s.async = true;
    s.crossOrigin = "anonymous";
    const attrs = {
      repo: GISCUS.repo, "repo-id": GISCUS.repoId, category: GISCUS.category, "category-id": GISCUS.categoryId,
      mapping: "specific", term: id, strict: "1", "reactions-enabled": "1", "emit-metadata": "0",
      "input-position": "top", theme: theme(), lang: "en", loading: "lazy"
    };
    for (const [k, v] of Object.entries(attrs)) s.setAttribute("data-" + k, v);
    s.onerror = () => { el.innerHTML = `<p class="locked">The discussion didn't load. Check your connection, or open the thread on GitHub.</p>`; };
    el.append(s);
  };
  if (!("IntersectionObserver" in window)) return load();
  const io = new IntersectionObserver((seen) => {
    if (seen.some((e) => e.isIntersecting)) { io.disconnect(); load(); }
  }, { rootMargin: "300px" });
  io.observe(el);
}
