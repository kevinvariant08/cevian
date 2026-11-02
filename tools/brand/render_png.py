"""Render Cevian's PNG icons and Open Graph images with a headless Chromium browser.

Usage:
    python tools/brand/render_png.py icons      # favicon-32, apple-touch-icon, icon-192/512, maskable
    python tools/brand/render_png.py og         # assets/og/og-home.png
    python tools/brand/render_png.py problem --id circle-in-the-square --title "Circle in the square" \
        --kyu 6 --topic Geometry --mode Answer [--out assets/og/problems/circle-in-the-square.png]

It uses Chrome, or Edge if Chrome is missing (set BROWSER to override; headless Edge
on Windows sometimes exits without writing the screenshot), and Pillow. The OG pages load
IBM Plex and Bricolage Grotesque from Google Fonts, so rendering needs a network.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlencode

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "assets"

CANDIDATES = [
    os.environ.get("BROWSER", ""),
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "google-chrome", "chromium", "chromium-browser", "microsoft-edge",
]


def browser():
    for c in CANDIDATES:
        if c and (Path(c).exists() or shutil.which(c)):
            return c
    sys.exit("No Chromium browser found; set BROWSER to its path.")


def screenshot(url, out, w, h, wait_ms=6000):
    """Screenshot url at w×h CSS px (device scale 1) into out."""
    out = Path(out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as profile:
        subprocess.run([
            browser(), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
            "--force-device-scale-factor=1", f"--user-data-dir={profile}",
            f"--window-size={w},{h}", f"--virtual-time-budget={wait_ms}",
            f"--screenshot={out}", url,
        ], check=True, capture_output=True, timeout=120)
    img = Image.open(out)
    if img.size != (w, h):  # some builds add a few px; crop to the requested size
        img.crop((0, 0, w, h)).save(out)
    print("wrote", out.relative_to(ROOT) if out.is_relative_to(ROOT) else out)


def svg_page(svg, size, bg="transparent"):
    """A throwaway HTML page that shows an SVG filling a size×size viewport."""
    tmp = Path(tempfile.mkdtemp()) / "icon.html"
    tmp.write_text(
        f'<!doctype html><meta charset="utf-8"><style>html,body{{margin:0;background:{bg}}}'
        f'img{{display:block;width:{size}px;height:{size}px}}</style><img src="{svg.as_uri()}">',
        encoding="utf-8")
    return tmp.as_uri()


def icon(svg, out, px, render=512, transparent=True):
    """Render svg at `render` px, then downscale to px with Lanczos (sharper than tiny renders)."""
    tmp = Path(tempfile.mkdtemp())
    if transparent:
        # Headless screenshots are opaque, so render on black and on white and recover alpha.
        screenshot(svg_page(svg, render, "#000"), tmp / "k.png", render, render, 1500)
        screenshot(svg_page(svg, render, "#fff"), tmp / "w.png", render, render, 1500)
        img = unblend(Image.open(tmp / "k.png").convert("RGB"), Image.open(tmp / "w.png").convert("RGB"))
    else:
        screenshot(svg_page(svg, render), tmp / "o.png", render, render, 1500)
        img = Image.open(tmp / "o.png").convert("RGB")
    img.resize((px, px), Image.LANCZOS).save(ASSETS / out, optimize=True)
    print("  ->", out, f"{px}x{px}")


def unblend(on_black, on_white):
    """alpha = 1 - (white - black); colour = black / alpha."""
    out = Image.new("RGBA", on_black.size)
    b, w, o = on_black.load(), on_white.load(), out.load()
    for y in range(out.height):
        for x in range(out.width):
            kb, kw = b[x, y], w[x, y]
            a = 1 - sum(cw - cb for cb, cw in zip(kb, kw)) / (3 * 255)
            if a <= 0.004:
                o[x, y] = (0, 0, 0, 0)
            else:
                o[x, y] = (*(min(255, round(c / a)) for c in kb), round(a * 255))
    return out


def cmd_icons(_):
    fav, app = ASSETS / "favicon.svg", ASSETS / "icons" / "app-icon.svg"
    icon(fav, "icons/favicon-32.png", 32)
    icon(fav, "icons/favicon-16.png", 16)
    icon(fav, "icons/icon-192.png", 192)
    icon(fav, "icons/icon-512.png", 512)
    icon(app, "icons/icon-maskable-512.png", 512, transparent=False)
    icon(app, "icons/icon-maskable-192.png", 192, transparent=False)
    icon(app, "icons/apple-touch-icon.png", 180, transparent=False)


def cmd_og(_):
    screenshot((ASSETS / "og" / "og-home.html").as_uri(), ASSETS / "og" / "og-home.png", 1200, 630)


def cmd_problem(a):
    q = urlencode({"title": a.title, "kyu": a.kyu, "topic": a.topic, "mode": a.mode, "id": a.id})
    out = Path(a.out) if a.out else ASSETS / "og" / "problems" / f"{a.id}.png"
    screenshot((ASSETS / "og" / "problem-template.html").as_uri() + "?" + q, out, 1200, 630)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("icons").set_defaults(fn=cmd_icons)
    sub.add_parser("og").set_defaults(fn=cmd_og)
    pr = sub.add_parser("problem")
    pr.add_argument("--id", required=True)
    pr.add_argument("--title", required=True)
    pr.add_argument("--kyu", required=True, type=int, help="8..1, or 0 for dan / boss")
    pr.add_argument("--topic", default="")
    pr.add_argument("--mode", default="Answer", choices=["Answer", "Proof"])
    pr.add_argument("--out")
    pr.set_defaults(fn=cmd_problem)
    a = p.parse_args()
    a.fn(a)
