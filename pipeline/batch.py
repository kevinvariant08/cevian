"""Message Batches API helper (half price). Any job of more than about 20 independent calls goes through here.

A batch is saved under out/batches/<name>.json as soon as it is created, so a restarted run polls the same batch
instead of paying for a second one. Every result is written to the ledger at the batch discount.

    results = run("rewrite-1", "rewrite", [req(id, model, system, prompt, effort, max_tokens), ...])
    results[id] -> dict(text=..., stop_reason=..., ok=True/False, error=...)
"""
import json
import sys
import time

import anthropic

from . import ledger
from .verify.config import OUT

DIR = OUT / "batches"
SUBMIT_CHUNK = 200  # Requests per batch, well under the API's limits, so one bad request can't sink the whole job.


def req(custom_id, model, system, prompt, effort, max_tokens):
    """One request. The system prompt is marked cacheable, because the style and rules repeat in every request."""
    params = dict(model=model, max_tokens=max_tokens, system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
                  messages=[{"role": "user", "content": prompt}])
    if effort:
        params["output_config"] = {"effort": effort}
    return dict(custom_id=custom_id, params=params)


def run(name, script, requests, poll=60, log=print):
    ledger.check_cap()
    client = anthropic.Anthropic(max_retries=8)  # Reads ANTHROPIC_API_KEY from the environment.
    DIR.mkdir(parents=True, exist_ok=True)
    state = DIR / f"{name}.json"
    if state.exists():
        saved = json.loads(state.read_text(encoding="utf-8"))
        ids = saved["batches"]
    else:
        saved = {"logged": []}
        ids = []
        for i in range(0, len(requests), SUBMIT_CHUNK):
            b = client.messages.batches.create(requests=requests[i:i + SUBMIT_CHUNK])
            ids.append(b.id)
            log(f"{name}: submitted {b.id} ({len(requests[i:i + SUBMIT_CHUNK])} requests)")
            saved.update(batches=ids, script=script)
            state.write_text(json.dumps(saved), encoding="utf-8", newline="\n")
    models = {r["custom_id"]: r["params"]["model"] for r in requests}
    out = {}
    for bid in ids:
        while True:
            try:
                b = client.messages.batches.retrieve(bid)
            except anthropic.APIConnectionError as e:  # The network dropped for a moment. The batch keeps running, so wait and ask again.
                log(f"{name}: connection error, retrying ({str(e)[:60]})")
                time.sleep(poll)
                continue
            if b.processing_status == "ended":
                break
            log(f"{name}: {bid} {b.request_counts.processing} processing, {b.request_counts.succeeded} done")
            sys.stdout.flush()
            time.sleep(poll)
        fresh = bid not in saved.setdefault("logged", [])  # A re-run reads the results again but must not bill them twice in the ledger.
        for r in client.messages.batches.results(bid):
            cid = r.custom_id
            if r.result.type == "succeeded":
                m = r.result.message
                u = m.usage
                if fresh:
                    ledger.record(script, m.model, u.input_tokens, u.output_tokens, getattr(u, "cache_read_input_tokens", 0) or 0,
                                  getattr(u, "cache_creation_input_tokens", 0) or 0, batch=True, note=cid)
                out[cid] = dict(ok=True, text="".join(x.text for x in m.content if x.type == "text"), stop_reason=m.stop_reason, output=u.output_tokens)
            else:
                err = getattr(r.result, "error", None)
                out[cid] = dict(ok=False, error=f"{r.result.type}: {str(err)[:200]}")
        if fresh:
            saved["logged"].append(bid)
            state.write_text(json.dumps(saved), encoding="utf-8", newline="\n")
    for cid in models:
        out.setdefault(cid, dict(ok=False, error="missing from the batch results"))
    return out
