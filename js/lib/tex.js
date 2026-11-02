// MathJax loads the first time a view has maths to show, so the list, ranks and profile views never pay for it.
// startup.js fetches the parts below separately. That is far less than tex-svg.js (a 1 MB SVG font and a 400 KB menu),
// and it parses in several short tasks rather than one long one.
const CDN = "https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/";

let loading = null;
export function loadMathJax() {
  if (!loading) loading = new Promise((resolve, reject) => {
    window.MathJax = {
      tex: { inlineMath: [["$", "$"], ["\\(", "\\)"]], displayMath: [["$$", "$$"], ["\\[", "\\]"]] },
      loader: { load: ["input/tex", "output/chtml", "a11y/assistive-mml"] },
      // The menu component isn't loaded: it would make every formula a tab stop. Assistive MathML is what screen readers read.
      options: { enableAssistiveMml: true, skipHtmlTags: ["script", "noscript", "style", "textarea", "pre", "code", "input"] },
      startup: { typeset: false }
    };
    const s = document.createElement("script");
    s.src = `${CDN}startup.js`; s.async = true;
    s.onload = () => window.MathJax.startup.promise.then(resolve, reject);
    s.onerror = () => { loading = null; reject(new Error("MathJax didn't load")); };
    document.head.append(s);
  });
  return loading;
}

const hasMaths = (el) => /[$\\]/.test(el.textContent);

// Let the page paint before the first MathJax download starts, so the statement isn't kept waiting.
// The timeout covers background tabs, where animation frames don't fire.
const afterPaint = () => new Promise((resolve) => {
  if (loading) return resolve();
  requestAnimationFrame(() => setTimeout(resolve));
  setTimeout(resolve, 200);
});

// Typesetting is chained because MathJax can't run two passes at once.
let chain = Promise.resolve();
export function tex(el) {
  if (!hasMaths(el)) return chain;
  el.classList.add("tex-pending");
  chain = chain.then(afterPaint).then(loadMathJax).then(() => {
    const MJ = window.MathJax;
    MJ.typesetClear([el]);
    return MJ.typesetPromise([el]);
  }).catch(() => {
    if (el.querySelector(".tex-failed")) return;
    el.insertAdjacentHTML("afterbegin", `<p class="faint tex-failed">The maths renderer didn't load, so formulas are showing as raw LaTeX.</p>`);
  }).finally(() => el.classList.remove("tex-pending"));
  return chain;
}

// For maths below the fold: wait until it's nearly on screen.
export function texWhenVisible(el) {
  if (!("IntersectionObserver" in window)) return tex(el);
  const io = new IntersectionObserver((seen) => {
    if (seen.some((e) => e.isIntersecting)) { io.disconnect(); tex(el); }
  }, { rootMargin: "120px" });
  io.observe(el);
}

// Blank lines separate paragraphs.
export const paras = (s) => s.split(/\n\s*\n/).map((x) => `<p>${x}</p>`).join("");

// Problem text is plain text with $...$ maths and a few tags (<b>, <i>, <code>). It is escaped first, and only those
// tags are put back, outside maths, so "$a<b<c$" can't be read as HTML. MathJax reads the escaped maths correctly.
const MATH = /(\$\$[\s\S]*?\$\$|\$[^$]*\$|\\\([\s\S]*?\\\)|\\\[[\s\S]*?\\\])/;
const escHtml = (s) => s.replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
export const safeText = (s) => String(s ?? "").split(MATH)
  .map((part, i) => (i % 2 ? escHtml(part) : escHtml(part).replace(/&lt;(\/?)(b|i|code)&gt;/g, "<$1$2>"))).join("");
export const texParas = (s) => paras(safeText(s));
