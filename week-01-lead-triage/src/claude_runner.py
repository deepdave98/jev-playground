"""Run shared lead questions through the Claude CLI with thinking disabled."""

import json
import os
import re
import subprocess
import time

from spec import INTENT_LEVELS, SEGMENTS, build_questions

# https://docs.claude.com/en/docs/about-claude/pricing
# Recorded benchmark rates: cache writes 1.25x input, reads 0.1x.
PRICING = {
    "claude-haiku-4-5": {"input": 1.00 / 1_000_000, "output": 5.00 / 1_000_000},
    "claude-sonnet-5": {"input": 2.00 / 1_000_000, "output": 10.00 / 1_000_000},
}
CACHE_WRITE_MULTIPLIER = 1.25
CACHE_READ_MULTIPLIER = 0.10


def input_cost(usage: dict, model: str, overhead_tokens: int) -> tuple[float, int]:
    """Blend input and cache rates, then subtract measured CLI overhead."""
    base = PRICING[model]["input"]
    plain = usage.get("input_tokens", 0)
    written = usage.get("cache_creation_input_tokens", 0)
    read = usage.get("cache_read_input_tokens", 0)
    total = plain + written + read
    if total == 0:
        return 0.0, 0
    blended = (plain * base
               + written * base * CACHE_WRITE_MULTIPLIER
               + read * base * CACHE_READ_MULTIPLIER) / total
    billable = max(0, total - overhead_tokens)
    return billable * blended, billable


def build_system_prompt(questions: dict | None = None) -> str:
    """Renders the shared spec as prose. Criteria strings are copied verbatim."""
    q = questions or build_questions("v1")
    lines = [
        "You triage inbound leads for a B2B SaaS company. For each lead you "
        "return four judgments. Answer only with JSON.",
        "",
        "1. disqualify (probability between 0 and 1)",
        q["disqualify"]["instructions"],
        f"  true when: {q['disqualify']['criteria']['true']}",
        f"  false when: {q['disqualify']['criteria']['false']}",
        "",
        "2. icp_fit (probability between 0 and 1)",
        q["icp_fit"]["instructions"],
        f"  true when: {q['icp_fit']['criteria']['true']}",
        f"  false when: {q['icp_fit']['criteria']['false']}",
        "",
        "3. segment (one of: " + ", ".join(SEGMENTS) + ")",
        q["segment"]["instructions"],
    ]
    for name, desc in q["segment"]["criteria"].items():
        lines.append(f"  {name}: {desc}")
    lines += [
        "",
        "4. intent (one of: " + ", ".join(INTENT_LEVELS) + ")",
        q["intent"]["instructions"],
    ]
    for c in q["intent"]["criteria"]:
        lines.append(f"  {c}")
    lines += [
        "",
        "Return exactly this JSON and nothing else, no markdown fence, no "
        "explanation:",
        '{"disqualify": <float 0-1>, "icp_fit": <float 0-1>, '
        '"segment": "<segment>", "intent": "<intent>", '
        '"segment_confidence": <float 0-1>, "intent_confidence": <float 0-1>}',
        "",
        "The two probabilities and the two confidence values must be calibrated: "
        "0.9 means you expect to be right about nine times in ten.",
    ]
    return "\n".join(lines)


def build_user_prompt(lead: dict) -> str:
    return json.dumps({
        "company": lead["company"],
        "employee_headcount": lead["headcount"],
        "job_title": lead["title"],
        "email": lead["email"],
        "form": lead["source"],
        "message": lead["message"],
        "recent_activity": lead["recent_activity"],
    }, indent=None)


class ClaudeRunner:
    def __init__(self, model: str, variant: str = "v1"):
        self.model = model
        self.name = model
        self.variant = variant
        self.system = build_system_prompt(build_questions(variant))
        self.overhead_tokens = 0  # set by calibrate()

    def _invoke(self, system: str, user: str) -> tuple[dict, float]:
        cmd = [
            "claude", "-p", user,
            "--model", self.model,
            "--output-format", "json",
            "--system-prompt", system,
            "--exclude-dynamic-system-prompt-sections",
            "--disallowedTools", "*",
            "--effort", "low",
        ]
        env = {**os.environ, "MAX_THINKING_TOKENS": "0"}
        t = time.perf_counter()
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300, env=env)
        wall_ms = (time.perf_counter() - t) * 1000
        if proc.returncode != 0:
            raise RuntimeError(f"claude exited {proc.returncode}: {proc.stderr[:300]}")
        return json.loads(proc.stdout), wall_ms

    def calibrate(self, samples: int = 5) -> dict:
        """Measure median input overhead with an empty system prompt."""
        import statistics

        counts = []
        for _ in range(samples):
            data, _ = self._invoke("", ".")
            u = data["usage"]
            # Cached tokens also contribute to CLI overhead.
            counts.append(u.get("input_tokens", 0)
                          + u.get("cache_creation_input_tokens", 0)
                          + u.get("cache_read_input_tokens", 0))
        self.overhead_tokens = int(statistics.median(counts))
        return {"samples": counts, "overhead_tokens": self.overhead_tokens}

    def run(self, lead: dict) -> dict:
        data, wall_ms = self._invoke(self.system, build_user_prompt(lead))

        usage = data["usage"]
        raw_in = usage["input_tokens"] + usage.get("cache_creation_input_tokens", 0) \
            + usage.get("cache_read_input_tokens", 0)
        out_tok = usage["output_tokens"]
        thinking = usage.get("output_tokens_details", {}).get("thinking_tokens", 0)
        in_usd, adj_in = input_cost(usage, self.model, self.overhead_tokens)

        price = PRICING[self.model]
        parsed = _parse_json(data.get("result", ""))

        return {
            "runner": self.name,
            "model": self.model,
            # duration_api_ms excludes CLI process startup.
            "latency_ms": float(data.get("duration_api_ms", wall_ms)),
            "wall_ms": wall_ms,
            "requests": 1,
            "input_tokens": adj_in,
            "input_tokens_raw": raw_in,
            "output_tokens": out_tok,
            "thinking_tokens": thinking,
            "billed_usd": in_usd + out_tok * price["output"],
            "prediction": {
                "disqualify": float(parsed["disqualify"]) >= 0.5,
                "icp_fit": float(parsed["icp_fit"]) >= 0.5,
                "segment": _coerce(parsed["segment"], SEGMENTS),
                "intent": _coerce(parsed["intent"], INTENT_LEVELS),
            },
            "confidence": {
                "disqualify": float(parsed["disqualify"]),
                "icp_fit": float(parsed["icp_fit"]),
                "segment": float(parsed.get("segment_confidence", 0.5)),
                "intent": float(parsed.get("intent_confidence", 0.5)),
            },
            "raw": {"result": data.get("result"), "usage": usage},
        }

    def close(self):
        pass


def _parse_json(text: str) -> dict:
    """Claude was told to return bare JSON. Tolerate a fence anyway."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    if fence:
        text = fence.group(1)
    else:
        brace = re.search(r"\{.*\}", text, re.S)
        if brace:
            text = brace.group(0)
    return json.loads(text)


def _coerce(value: str, allowed: list[str]) -> str:
    """Accept a near-miss label rather than scoring a formatting slip as wrong."""
    v = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    if v in allowed:
        return v
    for a in allowed:
        if v.startswith(a) or a.startswith(v):
            return a
    return v
