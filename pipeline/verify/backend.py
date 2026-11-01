"""The model backends. All checks call Backend.call(), and nothing else knows how a model is reached.

cli (default): `claude -p`, which runs on Kevin's plan.
api: the Anthropic API. Used only with --backend api and ANTHROPIC_API_KEY set. It costs money.
"""
import base64
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from .. import ledger
from .config import MODEL_TIMEOUT, OUT, PRICES


class ModelError(Exception):
    """A model call failed. The draft gets ERROR, not a verdict."""


class PlanLimit(ModelError):
    """The plan or rate limit was hit. A batch stops here; cached calls make the re-run resume."""


@dataclass
class Reply:
    text: str
    model: str
    input: int = 0
    cache_read: int = 0
    cache_write: int = 0
    output: int = 0
    thinking: int = 0
    usd: float = 0.0
    cached: bool = False
    truncated: bool = False


class Usage:
    """Adds up one draft's calls. Cached calls cost nothing now, so they're counted apart."""

    def __init__(self):
        self.lock = threading.Lock()
        self.by_model = {}
        self.fresh_usd = 0.0
        self.total_usd = 0.0

    def add(self, r):
        with self.lock:
            m = self.by_model.setdefault(r.model, dict(calls=0, cached_calls=0, input=0, cache_read=0, cache_write=0, output=0, thinking=0, usd=0.0))
            m["calls"] += 1
            m["cached_calls"] += r.cached
            for k in ("input", "cache_read", "cache_write", "output", "thinking", "usd"):
                m[k] += getattr(r, k)
            self.total_usd += r.usd
            if not r.cached:
                self.fresh_usd += r.usd

    def summary(self):
        return {
            "by_model": self.by_model,
            "calls": sum(m["calls"] for m in self.by_model.values()),
            "output_tokens": sum(m["output"] for m in self.by_model.values()),
            "api_equivalent_usd": round(self.total_usd, 4),
            "api_equivalent_usd_this_run": round(self.fresh_usd, 4),
        }


@dataclass
class Backend:
    """Handles the cache and the concurrency limit. Subclasses make the actual call."""
    concurrency: int = 4
    name: str = "base"
    use_cache: bool = True
    _slots: threading.Semaphore = field(init=False, repr=False)

    def __post_init__(self):
        self._slots = threading.Semaphore(self.concurrency)

    def call(self, model, system, prompt, effort, max_tokens, salt="", cacheable=True, role="", draft_id="", images=None):
        path = None
        if self.use_cache and cacheable:
            pictures = [hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in images or []]
            key = hashlib.sha256(json.dumps([model, effort, max_tokens, system, prompt, salt, *pictures]).encode()).hexdigest()
            path = OUT / "cache" / f"{key}.json"
            if path.exists():
                d = json.loads(path.read_text(encoding="utf-8"))
                return Reply(**{**d, "cached": True})
        with self._slots:
            r = self._send_images(model, system, prompt, effort, max_tokens, role, draft_id, salt, images) if images else self._send(model, system, prompt, effort, max_tokens, role, draft_id, salt)
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(r.__dict__), encoding="utf-8")
        return r

    def _send(self, model, system, prompt, effort, max_tokens, role, draft_id, salt):
        raise NotImplementedError

    def _send_images(self, model, system, prompt, effort, max_tokens, role, draft_id, salt, images):
        return self._send(model, system, prompt, effort, max_tokens, role, draft_id, salt)


class CliBackend(Backend):
    """Each call runs from an empty temp folder with no tools, no settings and no session, so a blind
    solver can't see this repo, its memory or the written solution. The API key is removed from the
    child's environment so a stray key can't turn a plan run into a paid one."""
    FLAGS = ["--output-format", "json", "--no-session-persistence", "--tools", "", "--strict-mcp-config", "--setting-sources", ""]

    def __init__(self, concurrency=4):
        super().__init__(concurrency=concurrency, name="cli")
        self.exe = shutil.which("claude")
        if not self.exe:
            raise ModelError("the claude CLI isn't on PATH")

    def _send_images(self, model, system, prompt, effort, max_tokens, role, draft_id, salt, images):
        """The CLI takes images only through its Read tool, so this one call gets that tool and a folder holding just the images."""
        return self._send(model, system, prompt, effort, max_tokens, role, draft_id, salt, images=images)

    def _send(self, model, system, prompt, effort, max_tokens, role, draft_id, salt, images=None):
        env = {k: v for k, v in os.environ.items() if k not in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")}
        env["CLAUDE_CODE_MAX_OUTPUT_TOKENS"] = str(max_tokens)
        # A capped reply makes the CLI retry up to four times. A budget of exactly one capped reply stops that.
        budget = max_tokens * PRICES.get(model, PRICES["claude-opus-5-5"])[3] / 1e6
        flags = self.FLAGS
        if images:
            # Reading each image is a model turn of its own, and each turn pays for the images again.
            budget *= 2 + len(images)
            flags = [*self.FLAGS]
            flags[flags.index("--tools") + 1] = "Read"
            flags += ["--allowedTools", "Read"]
            names = [f"figure-{i + 1}.png" for i in range(len(images))]
            prompt = f"First use the Read tool on each of these images in the current folder: {', '.join(names)}. Read nothing else.\n\n{prompt}"
        args = [self.exe, "-p", "--model", model, "--effort", effort, "--system-prompt", system, "--max-budget-usd", f"{budget:.4f}", *flags]
        last = None
        for attempt in range(3):
            with tempfile.TemporaryDirectory(prefix="kyuclid-call-") as cwd:
                for i, image in enumerate(images or []):
                    shutil.copy(image, Path(cwd) / f"figure-{i + 1}.png")
                try:
                    p = subprocess.run(args, input=prompt, capture_output=True, text=True, encoding="utf-8", cwd=cwd, env=env, timeout=MODEL_TIMEOUT)
                except subprocess.TimeoutExpired:
                    last = f"timed out after {MODEL_TIMEOUT}s"
                    continue
            try:
                d = json.loads(p.stdout)
            except json.JSONDecodeError:
                last = f"unreadable CLI output (exit {p.returncode}): {(p.stdout + p.stderr)[:200]}"
                time.sleep(5 * (attempt + 1))
                continue
            result = str(d.get("result") or "")
            if d.get("subtype") == "error_max_budget_usd":
                r = self._reply(d, model, truncated=True)
                r.output = max(r.output, max_tokens)
                return r
            if d.get("api_error_status") == 429 or (d.get("is_error") and "limit" in result.lower()):
                raise PlanLimit(result[:200] or "rate limited")
            if d.get("is_error"):
                # The output cap can show up as an error result. That's a usable "no answer", not a failure.
                if d.get("stop_reason") == "max_tokens" or "max_tokens" in result or "output token maximum" in result:
                    return self._reply(d, model, truncated=True)
                last = (result or str(d.get("subtype")))[:200]
                time.sleep(5 * (attempt + 1))
                continue
            return self._reply(d, model, truncated=d.get("stop_reason") == "max_tokens")
        raise ModelError(f"{model}: {last}")

    @staticmethod
    def _reply(d, model, truncated):
        u = d.get("usage") or {}
        return Reply(
            text=str(d.get("result") or ""), model=model, input=u.get("input_tokens", 0),
            cache_read=u.get("cache_read_input_tokens", 0), cache_write=u.get("cache_creation_input_tokens", 0),
            output=u.get("output_tokens", 0), thinking=(u.get("output_tokens_details") or {}).get("thinking_tokens", 0),
            usd=float(d.get("total_cost_usd") or 0), truncated=truncated)


class ApiBackend(Backend):
    """Pay-per-token. Off unless asked for, and it refuses to start without a key."""

    def __init__(self, concurrency=4):
        super().__init__(concurrency=concurrency, name="api")
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise ModelError("--backend api needs ANTHROPIC_API_KEY")
        try:
            import anthropic
        except ImportError as e:
            raise ModelError("--backend api needs the anthropic package: pip install anthropic") from e
        self.anthropic = anthropic
        self.client = anthropic.Anthropic()

    def _send_images(self, model, system, prompt, effort, max_tokens, role, draft_id, salt, images):
        pictures = [{"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": base64.b64encode(Path(p).read_bytes()).decode()}} for p in images]
        return self._send(model, system, [*pictures, {"type": "text", "text": prompt}], effort, max_tokens, role, draft_id, salt)

    def _send(self, model, system, prompt, effort, max_tokens, role, draft_id, salt):
        ledger.check_cap()
        kw = dict(model=model, max_tokens=max_tokens, system=system, output_config={"effort": effort},
                  messages=[{"role": "user", "content": prompt}])
        # Haiku has no server-side refusal fallback.
        if model in ("claude-opus-5-5", "claude-sonnet-5-5"):
            kw.update(betas=["server-side-fallback-2026-07-01"], fallbacks="default")
        try:
            m = self.client.beta.messages.create(**kw)
        except self.anthropic.RateLimitError as e:
            raise PlanLimit(str(e)[:200]) from e
        except self.anthropic.APIError as e:
            raise ModelError(str(e)[:200]) from e
        u = m.usage
        tokens = dict(input=u.input_tokens, cache_read=getattr(u, "cache_read_input_tokens", 0) or 0,
                      cache_write=getattr(u, "cache_creation_input_tokens", 0) or 0, output=u.output_tokens)
        price = PRICES.get(model, PRICES["claude-opus-5-5"])
        usd = (tokens["input"] * price[0] + tokens["cache_read"] * price[1] + tokens["cache_write"] * price[2] + tokens["output"] * price[3]) / 1e6
        ledger.record(f"gate:{role or 'call'}", model, tokens["input"], tokens["output"], tokens["cache_read"], tokens["cache_write"])
        text = "".join(b.text for b in m.content if b.type == "text")
        details = getattr(u, "output_tokens_details", None)
        return Reply(text=text, model=m.model, usd=usd, thinking=getattr(details, "thinking_tokens", 0) or 0,
                     truncated=m.stop_reason == "max_tokens", **tokens)


def make_backend(name="cli", concurrency=4):
    return {"cli": CliBackend, "api": ApiBackend}[name](concurrency=concurrency)


def last_json(text):
    """The last parseable {...} in a reply. Models sometimes put prose before it."""
    dec = json.JSONDecoder()
    found = None
    i = text.find("{")
    while i != -1:
        try:
            obj, end = dec.raw_decode(text, i)
            if isinstance(obj, dict):
                found = obj
            i = text.find("{", end)
        except json.JSONDecodeError:
            i = text.find("{", i + 1)
    return found
