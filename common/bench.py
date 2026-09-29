"""The loop every week's benchmark runs, one request at a time.

Sequential on purpose. Run the requests together and every latency number
measures the queue instead of the model.
"""

import json
import pathlib
import time


def run(name, items, step, out_dir, batch=1, meta=None):
    """Feed items to step() a batch at a time and write one line per request.

    step(batch) returns (labels_by_id, calls), where each call is a dict of
    ms, tokens in, tokens out and usd. A request that fails is written down
    with its error instead of stopping the run.
    """
    path = pathlib.Path(out_dir) / f"{name}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    head = {"run": name, "batch": batch, "started": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    t0 = time.perf_counter()

    with path.open("w") as fh:
        fh.write(json.dumps({"_meta": {**head, **(meta or {})}}) + "\n")
        for i in range(0, len(items), batch):
            chunk = items[i:i + batch]
            try:
                labels, calls = step(chunk)
                error = None
            except Exception as exc:
                labels, calls, error = {}, [], f"{type(exc).__name__}: {exc}"
            fh.write(json.dumps({"ids": [x["id"] for x in chunk], "labels": labels,
                                 "calls": calls, "error": error}) + "\n")
            fh.flush()
            done = min(i + batch, len(items))
            if done % 10 == 0 or done == len(items):
                print(f"[{name}] {done}/{len(items)} ({time.perf_counter() - t0:.0f}s)", flush=True)
    return path


def load(path):
    """Per-item labels and every call, from a run file."""
    labels, calls, failed = {}, [], []
    for line in pathlib.Path(path).open():
        rec = json.loads(line)
        if "_meta" in rec:
            continue
        calls += rec["calls"]
        if rec["error"]:
            failed += rec["ids"]
        labels.update(rec["labels"] or {})
    return labels, calls, failed
