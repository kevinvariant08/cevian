"""Build the Cevian logo SVGs in assets/ from the brand font.

The mark comes from Euclid's Elements, Book I, Proposition 1: on a segment AB draw the circle centred A through B and
the circle centred B through A. They cross at C, and ABC is equilateral. Two solid discs have their overlap cut out,
and the triangle's corners sit exactly on the two centres and the crossing point.

The wordmark is converted to outlines, so the SVGs render the same everywhere
(an <img> or favicon SVG can't load web fonts).

Usage:
    python tools/brand/build_logos.py path/to/bricolage-800.ttf

Get a static instance of the font (optical size 96, weight 800) from Google Fonts: request
https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@96,800 with an old user agent and it returns a
.ttf link.

Then re-render the PNG icons and OG images with tools/brand/render_png.py.
"""
import math
import sys
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets"

NAME = "cevian"
TRACKING_EM = -0.012  # matches .wordmark in css/site.css

# Colours: see docs/brand.md. Light theme first, dark theme second.
INK, INK_DARK = "#141B33", "#F1EFE9"
SHU, SHU_DARK = "#C4301B", "#F2583F"
BG, BG_DARK = "#F4F3EF", "#0D1322"
S3 = math.sqrt(3) / 2


def wordmark(font_path, size):
    """Return (path_d, width, top, bottom) for NAME at this font size, with the baseline at y=0 and the ink from x=0."""
    font = TTFont(font_path)
    upm = font["head"].unitsPerEm
    cmap = font.getBestCmap()
    glyphs = font.getGlyphSet()
    s = size / upm
    track = TRACKING_EM * upm

    # First pass: find the ink bounds so the wordmark starts exactly at x=0.
    x = 0
    bounds = BoundsPen(glyphs)
    for ch in NAME:
        g = glyphs[cmap[ord(ch)]]
        g.draw(TransformPen(bounds, (1, 0, 0, 1, x, 0)))
        x += g.width + track
    xmin, ymin, xmax, ymax = bounds.bounds

    pen = SVGPathPen(glyphs, ntos=lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
    x = -xmin
    for ch in NAME:
        g = glyphs[cmap[ord(ch)]]
        g.draw(TransformPen(pen, (s, 0, 0, -s, x * s, 0)))
        x += g.width + track
    return pen.getCommands(), (xmax - xmin) * s, -ymax * s, -ymin * s


def x_height(font_path, size):
    font = TTFont(font_path)
    return font["OS/2"].sxHeight * size / font["head"].unitsPerEm


def mark(x, cy, r, ink, red):
    """The mark with its left edge at x and its discs centred on the line cy. It is 3r wide and 2r tall."""
    a, b = x + r, x + 2 * r
    disc = lambda c: f"M{c - r:.2f} {cy:.2f}a{r:.2f} {r:.2f} 0 1 0 {2 * r:.2f} 0a{r:.2f} {r:.2f} 0 1 0 {-2 * r:.2f} 0Z"
    return (
        f'<path fill="{ink}" fill-rule="evenodd" d="{disc(a)}{disc(b)}"/>'
        f'<polygon points="{a:.2f},{cy:.2f} {b:.2f},{cy:.2f} {(a + b) / 2:.2f},{cy - r * S3:.2f}" fill="{red}"/>'
    )


def svg(w, h, body, title, bg=None, radius=0):
    corner = f' rx="{radius:g}"' if radius else ""
    rect = f'<rect width="{w:g}" height="{h:g}"{corner} fill="{bg}"/>' if bg else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:g} {h:g}" '
        f'width="{w:g}" height="{h:g}" role="img" aria-label="{title}">'
        f"<title>{title}</title>{rect}{body}</svg>\n"
    )


def write(name, text):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))
    print("wrote", path.relative_to(ROOT))


def main(font_path):
    themes = (("", INK, SHU, BG), ("-dark", INK_DARK, SHU_DARK, BG_DARK))

    # Horizontal lockup: discs 0.86 em tall, centred on the middle of the x-height.
    size = 100
    d, wm_w, top, bottom = wordmark(font_path, size)
    r = size * 0.43
    gap = size * 0.24
    mid = -x_height(font_path, size) / 2
    y0 = min(top, mid - r)
    y1 = max(bottom, mid + r)
    w, h = 3 * r + gap + wm_w + 2, y1 - y0 + 2
    base = 1 - y0
    for suffix, ink, red, _ in themes:
        body = mark(1, base + mid, r, ink, red) + (
            f'<path transform="translate({1 + 3 * r + gap:.2f} {base:.2f})" fill="{ink}" d="{d}"/>'
        )
        write(f"logo/cevian-horizontal{suffix}.svg", svg(round(w, 1), round(h, 1), body, "Cevian"))

    # Wordmark alone.
    for suffix, ink, _, _ in themes:
        write(f"logo/cevian-wordmark{suffix}.svg",
              svg(round(wm_w + 2, 1), round(bottom - top + 2, 1),
                  f'<path transform="translate(1 {1 - top:.2f})" fill="{ink}" d="{d}"/>', "Cevian"))

    # Square lockup (avatars, link cards): the mark over the wordmark on a solid tile.
    S = 512
    d_sq, wm_sq, top_sq, bottom_sq = wordmark(font_path, 92)
    r_sq = 80
    gap_sq = 40
    block = 2 * r_sq + gap_sq + (bottom_sq - top_sq)
    y = (S - block) / 2
    for suffix, ink, red, bg in themes:
        body = mark((S - 3 * r_sq) / 2, y + r_sq, r_sq, ink, red) + (
            f'<path transform="translate({(S - wm_sq) / 2:.2f} {y + 2 * r_sq + gap_sq - top_sq:.2f})" fill="{ink}" d="{d_sq}"/>'
        )
        write(f"logo/cevian-square{suffix}.svg", svg(S, S, body, "Cevian", bg))

    # The mark on its own (transparent).
    for suffix, ink, red, _ in themes:
        write(f"logo/cevian-mark{suffix}.svg", svg(92, 62, mark(1, 31, 30, ink, red), "Cevian"))

    # Favicon: on a dark tile, because a browser tab can be light or dark and a bare mark would vanish on one of them.
    write("favicon.svg", svg(64, 64, mark(4, 32, 56 / 3, INK_DARK, SHU_DARK), "Cevian", BG_DARK, 14))
    # App icon artwork: the mark inside the maskable safe zone, full bleed on the dark theme's indigo.
    write("icons/app-icon.svg", svg(512, 512, mark(91, 256, 110, INK_DARK, SHU_DARK), "Cevian", BG_DARK))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
