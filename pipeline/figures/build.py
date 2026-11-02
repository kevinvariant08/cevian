"""Compiles a figure with pdflatex and dvisvgm into the theme-aware SVG the site inlines, and checks its layout."""
import hashlib
import math
import re
import shutil
import signal
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from .source import Figure, FigureError

ROOT = Path(__file__).resolve().parents[2]
FIGURES = ROOT / "figures"
PREAMBLE = FIGURES / "preamble.tex"
TIMEOUT = 25
MAX_WIDTH_PT = 270
MAX_HEIGHT_PT = 300
MIN_LABEL_PX = 10.5
PHONE_WIDTH_PX = 288
LABEL_PT = 10
POINT_PT = 3.09
PX_PER_PT = 1.6

# The colours in preamble.tex, mapped to paint that follows the page. Anything else fails the build.
INK = 'currentColor'
PAINT = {
    "#000": (INK, None), "#000000": (INK, None), "#555": (INK, ".62"), "#555555": (INK, ".62"),
    "#c0392b": ("var(--fig-accent,currentColor)", None), "#ddd": (INK, ".1"), "#dddddd": (INK, ".1"),
    "#f5d5d0": ("var(--fig-accent,currentColor)", ".16"),
}


class ToolchainError(Exception):
    """TeX isn't usable here. That is this machine's fault, not the figure's, so it must not fail a draft."""


def _kill_tree(p):
    # On Windows a timeout only kills the immediate process, and pdflatex can leave helpers running.
    if shutil.which("taskkill"):
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True)
    else:
        p.send_signal(signal.SIGKILL)
    p.wait()


def _run(args, cwd, timeout=TIMEOUT):
    """Returns (exit code or None on timeout, output). The exit code decides success: MiKTeX prints a nag to stderr every time."""
    p = subprocess.Popen(args, cwd=cwd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    try:
        out, _ = p.communicate(timeout=timeout)
        return p.returncode, out
    except subprocess.TimeoutExpired:
        _kill_tree(p)
        return None, ""


_installer_flag = None


def _latex_args():
    """MiKTeX would otherwise offer to install a missing package, in a dialog nobody is there to answer."""
    global _installer_flag
    if _installer_flag is None:
        code, out = _run(["pdflatex", "--version"], None, 20)
        _installer_flag = ["--disable-installer"] if code == 0 and "MiKTeX" in out else []
    return ["pdflatex", *_installer_flag, "--no-shell-escape", "-interaction=nonstopmode", "-halt-on-error"]


def _first_error(log):
    lines = log.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("!"):
            where = next((x for x in lines[i + 1:i + 6] if x.startswith("l.")), "")
            return f"{line[1:].strip()} {where.strip()}".strip()
    return "pdflatex failed with no error line in its log"


_preflight_ok = False


def preflight():
    """One plain message for a missing tool, tried on a tiny real figure so a broken install is found here."""
    global _preflight_ok
    if _preflight_ok:
        return
    missing = [t for t in ("pdflatex", "dvisvgm") if not shutil.which(t)]
    if missing:
        raise ToolchainError(f"{' and '.join(missing)} not found on PATH. Install MiKTeX (or TeX Live) with tkz-euclide and dvisvgm to build figures. The site itself doesn't need them.")
    with tempfile.TemporaryDirectory(prefix="cevian-fig-") as d:
        tiny = "\\documentclass{standalone}\\usepackage{tkz-euclide}\\begin{document}\\begin{tikzpicture}\\tkzDefPoint(0,0){A}\\tkzDefPoint(1,0){B}\\tkzDrawSegment(A,B)\\tkzLabelPoint(A){$A$}\\end{tikzpicture}\\end{document}\n"
        (Path(d) / "t.tex").write_text(tiny, encoding="utf-8")
        code, out = _run([*_latex_args(), "t.tex"], d, 60)
        if code != 0 or not (Path(d) / "t.pdf").exists():
            log = (Path(d) / "t.log").read_text(encoding="utf-8", errors="replace") if (Path(d) / "t.log").exists() else out
            raise ToolchainError(f"pdflatex can't compile a tiny tkz-euclide figure ({_first_error(log)}). Check that tkz-euclide is installed: run `miktex packages install tkz-euclide` once by hand.")
        code, out = _run(["dvisvgm", "--pdf", "--no-fonts=1", "t.pdf"], d, 60)
        if code != 0 or not (Path(d) / "t.svg").exists():
            raise ToolchainError(f"dvisvgm can't convert a PDF ({out.strip()[:200]}). It needs Ghostscript or mutool, which MiKTeX provides as mgs.")
    _preflight_ok = True


def _compile(fig, workdir):
    d = Path(workdir)
    (d / "preamble.tex").write_text(PREAMBLE.read_text(encoding="utf-8"), encoding="utf-8")
    (d / "fig.tex").write_text(fig.tex, encoding="utf-8")
    code, _ = _run([*_latex_args(), "fig.tex"], d)
    if code is None:
        raise FigureError(f"pdflatex was still running after {TIMEOUT} seconds, so it was stopped. Old tkz-euclide syntax can loop forever")
    log = (d / "fig.log").read_text(encoding="utf-8", errors="replace") if (d / "fig.log").exists() else ""
    if code != 0 or not (d / "fig.pdf").exists():
        raise FigureError(f"doesn't compile: {_first_error(log)}")
    code, out = _run(["dvisvgm", "--pdf", "--no-fonts=1", "--exact-bbox", "--precision=3", "--output=fig.svg", "fig.pdf"], d)
    if code != 0 or not (d / "fig.svg").exists():
        raise FigureError(f"dvisvgm failed: {out.strip()[:200]}")
    return (d / "fig.svg").read_text(encoding="utf-8"), d / "fig.pdf"


def theme_svg(raw, name):
    """Turns dvisvgm's output into something safe to inline: page colours, unique ids and no fixed size."""
    svg = re.sub(r"<\?xml.*?\?>\s*|<!--.*?-->\s*", "", raw, flags=re.S).strip()
    svg = re.sub(r"\s+id='page\d+'", "", svg)
    svg = re.sub(r"id='([^']+)'", lambda m: f"id='{name}-{m.group(1)}'", svg)
    svg = re.sub(r"(xlink:href|href)='#([^']+)'", lambda m: f"{m.group(1)}='#{name}-{m.group(2)}'", svg)
    svg = re.sub(r"url\(#([^)]+)\)", lambda m: f"url(#{name}-{m.group(1)})", svg)

    def paint(m):
        attr, value = m.group(1), m.group(2).lower()
        if value == "none":
            return m.group(0)
        if value not in PAINT:
            raise FigureError(f"the colour {value} isn't one of the preamble's: it wouldn't follow the page theme")
        colour, opacity = PAINT[value]
        return f"{attr}='{colour}'" + (f" {attr}-opacity='{opacity}'" if opacity else "")

    svg = re.sub(r"\b(stroke|fill)='([^']*)'", paint, svg)
    root = re.search(r"<svg\b[^>]*>", svg).group()
    viewbox = re.search(r"viewBox='([^']+)'", root).group(1)
    needs_xlink = "xlink:" in svg[len(root):]
    # A fixed size per point keeps labels and strokes the same from figure to figure; CSS only ever shrinks it to fit a phone.
    w, h = [float(v) for v in viewbox.split()[2:]]
    xlink = " xmlns:xlink='http://www.w3.org/1999/xlink'" if needs_xlink else ""
    new_root = f"<svg xmlns='http://www.w3.org/2000/svg'{xlink} viewBox='{viewbox}' width='{w * PX_PER_PT:.0f}' height='{h * PX_PER_PT:.0f}' fill='currentColor'>"
    svg = svg.replace(root, new_root, 1)
    if re.search(r"<script|<foreignObject|\son\w+=|<image", svg):
        raise FigureError("the SVG holds active or embedded content")
    return svg + "\n"


NUMBER = r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?"
SVG_NS = "{http://www.w3.org/2000/svg}"


def _parse_transform(text):
    a, b, c, d, e, f = 1.0, 0.0, 0.0, 1.0, 0.0, 0.0
    for kind, args in re.findall(r"(\w+)\(([^)]*)\)", text or ""):
        v = [float(x) for x in re.findall(NUMBER, args)]
        if kind == "matrix":
            m = v
        elif kind == "translate":
            m = [1, 0, 0, 1, v[0], v[1] if len(v) > 1 else 0]
        elif kind == "scale":
            m = [v[0], 0, 0, v[1] if len(v) > 1 else v[0], 0, 0]
        else:
            raise FigureError(f"unexpected transform {kind} in the SVG")
        a, b, c, d, e, f = a * m[0] + c * m[1], b * m[0] + d * m[1], a * m[2] + c * m[3], b * m[2] + d * m[3], a * m[4] + c * m[5] + e, b * m[4] + d * m[5] + f
    return a, b, c, d, e, f


def _compose(t, u):
    a, b, c, d, e, f = t
    return a * u[0] + c * u[1], b * u[0] + d * u[1], a * u[2] + c * u[3], b * u[2] + d * u[3], a * u[4] + c * u[5] + e, b * u[4] + d * u[5] + f


def _flatten(d):
    """Points along a path's outline. Curves become short runs of points, which is plenty for a bounding box."""
    tokens = re.findall(rf"[A-Za-z]|{NUMBER}", d)
    pts, i, cmd, cur, start, last_ctrl = [], 0, None, (0.0, 0.0), (0.0, 0.0), None

    def take(n):
        nonlocal i
        out = [float(x) for x in tokens[i:i + n]]
        i += n
        return out

    subpaths = []
    while i < len(tokens):
        if tokens[i].isalpha():
            cmd = tokens[i]
            i += 1
            if cmd in "Zz":
                pts.append(start)
                cur = start
                continue
        rel = cmd.islower()
        c = cmd.upper()
        if c not in "CS":
            last_ctrl = None
        base = cur if rel else (0.0, 0.0)
        if c == "M":
            x, y = take(2)
            cur = start = (base[0] + x, base[1] + y)
            if pts:
                subpaths.append(pts)
            pts = [cur]
            cmd = "l" if rel else "L"
        elif c == "L":
            x, y = take(2)
            cur = (base[0] + x, base[1] + y)
            pts.append(cur)
        elif c == "H":
            x, = take(1)
            cur = (base[0] + x, cur[1])
            pts.append(cur)
        elif c == "V":
            y, = take(1)
            cur = (cur[0], base[1] + y)
            pts.append(cur)
        elif c in "CS":
            n = 6 if c == "C" else 4
            v = take(n)
            ctrl = [(base[0] + v[j], base[1] + v[j + 1]) for j in range(0, n, 2)]
            # S reflects the previous curve's second control point through the current point.
            first = ctrl[0] if c == "C" else (2 * cur[0] - last_ctrl[0], 2 * cur[1] - last_ctrl[1]) if last_ctrl else cur
            second, end, p0 = ctrl[-2], ctrl[-1], cur
            for step in range(1, 13):
                t = step / 12
                pts.append(tuple((1 - t) ** 3 * p0[k] + 3 * (1 - t) ** 2 * t * first[k] + 3 * (1 - t) * t ** 2 * second[k] + t ** 3 * end[k] for k in (0, 1)))
            cur, last_ctrl = end, second
            continue
        else:
            raise FigureError(f"unexpected path command {cmd} in the SVG")
    if pts:
        subpaths.append(pts)
    return subpaths


def _shapes(svg):
    """Returns (glyph boxes, stroke polylines, filled dot boxes) in viewBox coordinates."""
    root = ET.fromstring(svg)
    glyphs, strokes, dots = [], [], []
    identity = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)

    def walk(node, t, stroke, fill):
        t = _compose(t, _parse_transform(node.get("transform")))
        stroke, fill = node.get("stroke", stroke), node.get("fill", fill)
        if node.tag == SVG_NS + "path":
            subs = _flatten(node.get("d", ""))
            mapped = [[(t[0] * x + t[2] * y + t[4], t[1] * x + t[3] * y + t[5]) for x, y in s] for s in subs]
            if stroke not in (None, "none"):
                strokes.extend(mapped)
            elif node.get("fill-opacity") is None and fill != "none":
                # Unstroked and opaque means a glyph outline from --no-fonts, or a point marker: a round dot of a known size.
                box = _box([p for s in mapped for p in s])
                is_dot = abs((box[2] - box[0]) - (box[3] - box[1])) < .02 and abs(box[2] - box[0] - POINT_PT) < .15
                (dots if is_dot else glyphs).append(box)
        for child in node:
            walk(child, t, stroke, fill)

    walk(root, identity, None, root.get("fill"))
    return glyphs, strokes, dots


def _box(pts):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def _overlap_area(a, b):
    w, h = min(a[2], b[2]) - max(a[0], b[0]), min(a[3], b[3]) - max(a[1], b[1])
    return w * h if w > 0 and h > 0 else 0.0


def check_layout(svg):
    """Returns the problems: oversize figures, labels that overlap each other, and lines through a label."""
    problems = []
    x0, y0, w, h = [float(v) for v in re.search(r"viewBox='([^']+)'", svg).group(1).split()]
    if w > MAX_WIDTH_PT or h > MAX_HEIGHT_PT:
        problems.append(f"the figure is {w:.0f} by {h:.0f}pt, over the {MAX_WIDTH_PT} by {MAX_HEIGHT_PT}pt that keeps labels readable on a phone: lower %! scale")
    label_px = LABEL_PT * PHONE_WIDTH_PX / max(w, 1)
    if label_px < MIN_LABEL_PX:
        problems.append(f"labels would be {label_px:.1f}px at phone width: lower %! scale")

    glyphs, strokes, dots = _shapes(svg)
    if not glyphs:
        problems.append("the figure has no labels")
    # Glyphs of one label sit side by side, so count only a real overlap of ink boxes.
    for i, a in enumerate(glyphs):
        for b in glyphs[i + 1:]:
            smaller = min((a[2] - a[0]) * (a[3] - a[1]), (b[2] - b[0]) * (b[3] - b[1]))
            if smaller > 0 and _overlap_area(a, b) > 0.2 * smaller:
                problems.append(f"two labels overlap near ({a[0] - x0:.0f}, {a[1] - y0:.0f})pt")
    for g in glyphs:
        # Shrunk, because a glyph's box has empty corners and a line may pass close by without touching any ink.
        inner = (g[0] + .7, g[1] + .7, g[2] - .7, g[3] - .7)
        if inner[0] >= inner[2] or inner[1] >= inner[3]:
            continue
        if any(_segment_hits_box(a, b, inner) for line in strokes for a, b in zip(line, line[1:])):
            problems.append(f"a line runs through a label near ({g[0] - x0:.0f}, {g[1] - y0:.0f})pt")
        if any(_overlap_area(g, d) > 0 for d in dots):
            problems.append(f"a point marker touches a label near ({g[0] - x0:.0f}, {g[1] - y0:.0f})pt")
    return sorted(set(problems))


def _segment_hits_box(a, b, box):
    steps = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / .5))
    return any(box[0] <= a[0] + (b[0] - a[0]) * s / steps <= box[2] and box[1] <= a[1] + (b[1] - a[1]) * s / steps <= box[3] for s in range(steps + 1))


@dataclass
class Built:
    name: str
    svg: str
    alt: str
    after_paragraph: int
    facts: int
    layout: list

    @property
    def version(self):
        return svg_version(self.svg)

    @property
    def src(self):
        return f"figures/{self.name}.svg?v={self.version}"


def svg_version(svg):
    return hashlib.sha256(svg.replace("\r\n", "\n").encode("utf-8")).hexdigest()[:8]


def build_source(name, tex, render_png=None):
    """Checks one figure and compiles it. Raises FigureError if it is wrong and ToolchainError if TeX is missing."""
    preflight()
    fig = Figure(name, tex)
    if not fig.alt:
        raise FigureError("no %! alt line: a figure needs a text alternative")
    if fig.after_paragraph is None:
        raise FigureError("no %! after_paragraph line")
    fig.check_decimals()
    if not fig.facts:
        raise FigureError("no %! fact lines: a figure must state what it shows, so it can be checked")
    count = fig.check_facts()
    with tempfile.TemporaryDirectory(prefix="cevian-fig-") as d:
        raw, pdf = _compile(fig, d)
        svg = theme_svg(raw, name)
        if render_png:
            _render(pdf, render_png)
    return Built(name, svg, fig.alt, fig.after_paragraph, count, check_layout(svg))


def _render(pdf, out_png):
    """A black-on-white PNG, for the critic and the review notes."""
    tool = shutil.which("pdftoppm") or shutil.which("miktex-pdftoppm")
    if not tool:
        raise ToolchainError("pdftoppm not found, so a figure can't be rendered for the critic")
    out = Path(out_png)
    code, text = _run([tool, "-png", "-r", "200", "-singlefile", str(pdf), str(out.with_suffix(""))], None, 60)
    if code != 0:
        raise ToolchainError(f"pdftoppm failed: {text[:200]}")


def figure_paths(name):
    return FIGURES / f"{name}.tex", FIGURES / f"{name}.svg"


def all_names():
    return sorted(p.stem for p in FIGURES.glob("*.tex") if p.name != "preamble.tex")


def problem_id(name):
    return re.sub(r"-solution(-\d+)?$", "", name)
