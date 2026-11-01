"""The shared API call ledger. Every paid call, live or batched, is recorded in pipeline/api-ledger.jsonl.

The ledger is git-ignored. It never holds the API key, only the script, the model, token counts and an estimated cost.
Batch calls are half price. Call check_cap() before spending: it raises SpendCap once the logged total reaches the cap.
"""
import json
import os
import threading
import time
from pathlib import Path

LEDGER = Path(__file__).resolve().parent / "api-ledger.jsonl"
CAP_USD = float(os.environ.get("KYUCLID_SPEND_CAP", "40"))
BATCH_DISCOUNT = 0.5
_lock = threading.Lock()


class SpendCap(Exception):
    """The logged spend reached the cap. Stop, write the report and end."""


def prices():
    from .verify.config import PRICES  # (input, cache read, cache write, output) per million tokens
    return PRICES


def cost(model, input=0, output=0, cache_read=0, cache_write=0, batch=False):
    p = prices().get(model) or prices()["claude-opus-5-5"]  # An unknown model is priced as the dearest, so the estimate errs high.
    usd = (input * p[0] + cache_read * p[1] + cache_write * p[2] + output * p[3]) / 1e6
    return usd * (BATCH_DISCOUNT if batch else 1)


def record(script, model, input=0, output=0, cache_read=0, cache_write=0, batch=False, note=""):
    """Appends one call and returns its estimated cost in dollars."""
    usd = cost(model, input, output, cache_read, cache_write, batch)
    row = dict(ts=time.strftime("%Y-%m-%dT%H:%M:%S%z"), script=script, model=model, input=input, output=output,
               cache_read=cache_read, cache_write=cache_write, batch=batch, usd=round(usd, 6))
    if note:
        row["note"] = note
    with _lock, LEDGER.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(row) + "\n")
    return usd


def rows():
    if not LEDGER.exists():
        return []
    return [json.loads(x) for x in LEDGER.read_text(encoding="utf-8").splitlines() if x.strip()]


def total():
    return sum(r["usd"] for r in rows())


def check_cap(extra=0.0):
    """Raises SpendCap if the logged spend plus an estimate for the work about to start would reach the cap."""
    spent = total()
    if spent + extra >= CAP_USD:
        raise SpendCap(f"logged spend ${spent:.2f} plus ${extra:.2f} planned reaches the ${CAP_USD:.0f} cap")


def summary():
    """Spend by script and model, for the end-of-session report."""
    out = {}
    for r in rows():
        k = (r["script"], r["model"], "batch" if r["batch"] else "live")
        a = out.setdefault(k, dict(calls=0, input=0, output=0, cache_read=0, cache_write=0, usd=0.0))
        a["calls"] += 1
        for f in ("input", "output", "cache_read", "cache_write", "usd"):
            a[f] += r[f]
    return out


def api_key():
    """The key comes only from the environment. It is never stored."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")
    return key


if __name__ == "__main__":
    for (script, model, mode), a in sorted(summary().items()):
        print(f"{script:24} {model:20} {mode:5} calls={a['calls']:4} in={a['input']:8} out={a['output']:8} cache_r={a['cache_read']:8} usd={a['usd']:.4f}")
    print(f"total ${total():.4f} of ${CAP_USD:.0f}")
