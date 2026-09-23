"""One Claude call per question, instead of one call for all four.

This exists to answer the obvious objection to the headline result. In the
main benchmark Claude answers all four questions in a single JSON response,
and Haiku's errors turned out to be correlated: it decides a lead is bad,
sets disqualify high, and then collapses icp_fit to match. Every one of its
29 icp_fit errors ran in that direction.

That could be an artifact of the format rather than the model, so this runner
removes the format. Each question goes in its own call with its own system
prompt and no knowledge of the others, which is the most favourable
arrangement Claude can get. It is also 4x the calls, 4x the prompt overhead
and 4x the latency, which is the part nobody mentions when they suggest it.

  python3 src/split_runner.py claude-haiku-4-5
  python3 src/split_runner.py claude-haiku-4-5 --resume   # finish a part-done run
"""

import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from claude_runner import PRICING, ClaudeRunner, _coerce, _parse_json, input_cost  # noqa: E402
from spec import INTENT_LEVELS, SEGMENTS, build_questions  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]


def single_question_prompt(key: str, q: dict) -> str:
    """One question, same criteria strings as everywhere else."""
    head = ("You triage inbound leads for a B2B SaaS company. Answer exactly "
            "one question about the lead. Answer only with JSON.")
    body = [head, "", q["instructions"]]

    if q["type"] == "noul":
        body += [
            f"  true when: {q['criteria']['true']}",
            f"  false when: {q['criteria']['false']}",
            "",
            'Return only: {"answer": <probability between 0 and 1>}',
            "The probability must be calibrated: 0.9 means you expect to be "
            "right about nine times in ten.",
        ]
    elif q["type"] == "choice":
        for name, desc in q["criteria"].items():
            body.append(f"  {name}: {desc}")
        body += ["", 'Return only: {"answer": "<one of: '
                 + ", ".join(SEGMENTS) + '>", "confidence": <0-1>}']
    else:  # score
        body += [f"  {c}" for c in q["criteria"]]
        body += ["", 'Return only: {"answer": "<one of: '
                 + ", ".join(INTENT_LEVELS) + '>", "confidence": <0-1>}']
    return "\n".join(body)


class ClaudeSplitRunner(ClaudeRunner):
    def __init__(self, model: str, variant: str = "v1"):
        super().__init__(model, variant)
        self.name = f"{model}-split"
        questions = build_questions(variant)
        self.prompts = {k: single_question_prompt(k, q) for k, q in questions.items()}

    def run(self, lead: dict) -> dict:
        from claude_runner import build_user_prompt

        user = build_user_prompt(lead)
        price = PRICING[self.model]
        pred, conf = {}, {}
        total_ms, total_usd, in_tok, out_tok = 0.0, 0.0, 0, 0

        for key, system in self.prompts.items():
            data, wall = self._invoke(system, user)
            total_ms += float(data.get("duration_api_ms", wall))
            u = data["usage"]
            usd, adj = input_cost(u, self.model, self.overhead_tokens)
            total_usd += usd + u["output_tokens"] * price["output"]
            in_tok += adj
            out_tok += u["output_tokens"]

            parsed = _parse_json(data.get("result", ""))
            ans = parsed["answer"]
            if key in ("disqualify", "icp_fit"):
                pred[key] = float(ans) >= 0.5
                conf[key] = float(ans)
            elif key == "segment":
                pred[key] = _coerce(ans, SEGMENTS)
                conf[key] = float(parsed.get("confidence", 0.5))
            else:
                pred[key] = _coerce(ans, INTENT_LEVELS)
                conf[key] = float(parsed.get("confidence", 0.5))

        return {
            "runner": self.name, "model": self.model,
            "latency_ms": total_ms, "requests": len(self.prompts),
            "input_tokens": in_tok, "output_tokens": out_tok,
            "billed_usd": total_usd,
            "prediction": pred, "confidence": conf,
            "raw": {"note": "4 separate calls, see latency_ms for the sum"},
        }


def main() -> None:
    argv = [a for a in sys.argv[1:] if not a.startswith("--")]
    resume = "--resume" in sys.argv
    model = argv[0] if argv else "claude-haiku-4-5"
    leads = [json.loads(l) for l in (ROOT / "data" / "leads.jsonl").open()]

    runner = ClaudeSplitRunner(model)
    out = ROOT / "results" / "raw" / f"{runner.name}.jsonl"

    # 4 calls per lead is slow enough that losing a part-done run hurts.
    done: set[str] = set()
    if resume and out.exists():
        for line in out.open():
            d = json.loads(line)
            if "_meta" not in d:
                done.add(d["id"])
        leads = [l for l in leads if l["id"] not in done]
        print(f"[{runner.name}] resuming: {len(done)} done, {len(leads)} left")
        if not leads:
            print("nothing to do")
            return

    meta = {"runner": runner.name, "variant": "v1-split",
            "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    print(f"[{runner.name}] calibrating...")
    meta["calibration"] = runner.calibrate()
    print(f"[{runner.name}] overhead = {meta['calibration']['overhead_tokens']} tokens")

    t0 = time.perf_counter()
    with out.open("a" if done else "w") as fh:
        if not done:
            fh.write(json.dumps({"_meta": meta}) + "\n")
        for i, lead in enumerate(leads, 1):
            try:
                res = runner.run(lead["lead"])
                res.update(id=lead["id"], labels=lead["labels"], error=None)
            except Exception as exc:
                res = {"id": lead["id"], "labels": lead["labels"],
                       "runner": runner.name, "error": f"{type(exc).__name__}: {exc}"}
            fh.write(json.dumps(res) + "\n")
            fh.flush()
            if i % 10 == 0 or i == len(leads):
                print(f"[{runner.name}] {i}/{len(leads)} "
                      f"({time.perf_counter() - t0:.0f}s)")
    print(f"[{runner.name}] done in {time.perf_counter() - t0:.0f}s -> {out}")


if __name__ == "__main__":
    main()
