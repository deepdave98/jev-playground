"""Runs the benchmark and writes results/raw/<runner>.jsonl.

Sequential on purpose. Running the calls concurrently would finish sooner and
make every latency number meaningless, because they would all be queued behind
each other.

  python3 src/bench.py                 # all runners
  python3 src/bench.py jev             # one runner
"""

import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from claude_runner import ClaudeRunner  # noqa: E402
from jev_runner import JevRunner  # noqa: E402
from spec import build_questions  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "results" / "raw"

RUNNERS = {
    "jev": lambda v: JevRunner(build_questions(v), variant=v),
    "claude-haiku-4-5": lambda v: ClaudeRunner("claude-haiku-4-5", variant=v),
    "claude-sonnet-5": lambda v: ClaudeRunner("claude-sonnet-5", variant=v),
}


def load_leads() -> list[dict]:
    with (ROOT / "data" / "leads.jsonl").open() as fh:
        return [json.loads(line) for line in fh]


def run_one(name: str, leads: list[dict], variant: str = "v1") -> None:
    runner = RUNNERS[name](variant)
    meta: dict = {"runner": name, "variant": variant,
                  "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}

    if isinstance(runner, ClaudeRunner):
        print(f"[{name}] calibrating CLI token overhead...")
        meta["calibration"] = runner.calibrate()
        print(f"[{name}] overhead = {meta['calibration']['overhead_tokens']} input tokens "
              f"(subtracted from every call)")
    else:
        print(f"[{name}] measuring TCP+TLS handshake cost...")
        meta["tls_connect_ms"] = runner.measure_connect_cost()
        print(f"[{name}] cold connect = {meta['tls_connect_ms']:.0f} ms "
              f"(paid once, connection is reused)")
        runner.run(leads[0]["lead"])  # warm the socket, result discarded

    suffix = "" if variant == "v1" else f".{variant}"
    out_path = RAW / f"{name}{suffix}.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    errors = 0
    t0 = time.perf_counter()

    with out_path.open("w") as fh:
        fh.write(json.dumps({"_meta": meta}) + "\n")
        for i, lead in enumerate(leads, 1):
            try:
                res = runner.run(lead["lead"])
                res["id"] = lead["id"]
                res["labels"] = lead["labels"]
                res["error"] = None
            except Exception as exc:
                errors += 1
                res = {"id": lead["id"], "labels": lead["labels"], "runner": name,
                       "error": f"{type(exc).__name__}: {exc}"}
            fh.write(json.dumps(res) + "\n")
            fh.flush()
            if i % 10 == 0 or i == len(leads):
                print(f"[{name}] {i}/{len(leads)}  ({time.perf_counter() - t0:.0f}s elapsed)")

    runner.close()
    print(f"[{name}] done in {time.perf_counter() - t0:.0f}s, {errors} errors -> {out_path}")


def main() -> None:
    args = sys.argv[1:]
    variant = "v1"
    for a in list(args):
        if a.startswith("--variant="):
            variant = a.split("=", 1)[1]
            args.remove(a)
    which = args or list(RUNNERS)
    unknown = [w for w in which if w not in RUNNERS]
    if unknown:
        sys.exit(f"unknown runner(s): {unknown}. choose from {list(RUNNERS)}")
    leads = load_leads()
    print(f"{len(leads)} leads, prompt variant {variant}\n")
    for name in which:
        run_one(name, leads, variant)
        print()


if __name__ == "__main__":
    main()
