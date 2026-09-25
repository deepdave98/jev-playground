"""Claude calls for week 02, through the `claude` CLI.

Same three corrections as week 01, since the CLI hasn't changed: thinking off,
the CLI's own scaffolding measured and subtracted from token counts, and cache
reads billed at the cache rate. week-01-lead-triage/README.md has the story of
how each one was found.

Three shapes:
  per_event  one call per event, same three judgments Jev makes
  per_deal   one call per deal, every event judged in a single response
  ledger     one call per deal, the whole ledger, asked straight out whether
             the deal is at risk and why. This is how most people would use
             Claude for this, so it gets its own run.
"""

import json
import os
import re
import statistics
import subprocess
import time

from spec import AS_OF, EVENT_QUESTIONS, REASON_KEYS, RISK_RULES, SEV, SIGNALS

PRICE = {  # per token, list price
    "claude-haiku-4-5": (1.00e-6, 5.00e-6),
    "claude-sonnet-5": (2.00e-6, 10.00e-6),
}


def criteria_text():
    q = EVENT_QUESTIONS
    lines = ["signal, one of:"]
    lines += [f"  {k}: {v}" for k, v in SIGNALS.items()]
    lines += ["", "severity. " + q["severity"]["instructions"] + " One of:"]
    lines += [f"  {s}" for s in q["severity"]["criteria"]]
    lines += ["", "exec_engaged, a probability from 0 to 1. " + q["exec_engaged"]["instructions"]]
    return "\n".join(lines)


PER_EVENT = f"""You review activity on open B2B deals. You get the deal record and one
event from its activity ledger. Judge that event on three things.

{criteria_text()}

Answer with JSON only, no fence:
{{"signal": "...", "severity": "...", "exec_engaged": 0.0}}"""

PER_DEAL = f"""You review activity on open B2B deals. You get the deal record and every
event in its activity ledger. Judge each event on three things, one event at a
time.

{criteria_text()}

Answer with JSON only, no fence, one entry per event id:
{{"E001": {{"signal": "...", "severity": "...", "exec_engaged": 0.0}}, ...}}"""

LEDGER = f"""You review open B2B deals. You get the deal record and every event in its
activity ledger. Today is {AS_OF}. Decide whether the deal is at risk.

{RISK_RULES}

Answer with JSON only, no fence:
{{"at_risk": 0.0, "reasons": ["..."]}}
at_risk is your probability that the deal is at risk under these rules.
reasons lists every key that applies, and is empty if none do."""


def parse(text):
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0) if m else text)


def pick(value, allowed):
    """Accept a near miss like "Momentum" or "champion exit"."""
    v = str(value).strip().lower().replace(" ", "_").replace("-", "_")
    if v in allowed:
        return v
    return next((a for a in allowed if v.startswith(a) or a.startswith(v)), v)


def labels_from(obj):
    p = float(obj["exec_engaged"])
    return {
        "signal": pick(obj["signal"], list(SIGNALS)),
        "severity": pick(obj["severity"], SEV),
        "exec_engaged": p >= 0.5,
        "p_exec": p,
    }


class Claude:
    def __init__(self, model):
        self.model = model
        self.overhead = 0

    def call(self, system, user):
        cmd = ["claude", "-p", user, "--model", self.model, "--output-format", "json",
               "--system-prompt", system, "--exclude-dynamic-system-prompt-sections",
               "--disallowedTools", "*", "--effort", "low"]
        env = {**os.environ, "MAX_THINKING_TOKENS": "0"}
        t = time.perf_counter()
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300, env=env)
        wall = (time.perf_counter() - t) * 1000
        if proc.returncode:
            raise RuntimeError(f"claude exited {proc.returncode}: {proc.stderr[:300]}")
        data = json.loads(proc.stdout)
        return data, float(data.get("duration_api_ms", wall))

    def calibrate(self, n=5):
        """Tokens the CLI adds before our prompt. Median of n empty calls."""
        counts = []
        for _ in range(n):
            u = self.call("", ".")[0]["usage"]
            counts.append(u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
                          + u.get("cache_read_input_tokens", 0))
        self.overhead = int(statistics.median(counts))
        return counts

    def cost(self, usage):
        rate_in, rate_out = PRICE[self.model]
        plain = usage.get("input_tokens", 0)
        wrote = usage.get("cache_creation_input_tokens", 0)
        read = usage.get("cache_read_input_tokens", 0)
        total = plain + wrote + read
        if not total:
            return 0.0, 0
        # cache writes cost 1.25x, reads 0.1x. Blend, then drop the CLI's share.
        blended = (plain + wrote * 1.25 + read * 0.10) * rate_in / total
        ours = max(0, total - self.overhead)
        return ours * blended + usage["output_tokens"] * rate_out, ours

    def run(self, system, payload):
        data, ms = self.call(system, json.dumps(payload))
        usd, tokens = self.cost(data["usage"])
        return parse(data.get("result", "")), ms, usd, tokens, data["usage"]["output_tokens"]

    def per_event(self, deal, event):
        out, ms, usd, tin, tout = self.run(
            PER_EVENT, {"deal": {**deal, "today": AS_OF}, "event": event})
        return labels_from(out), ms, usd, tin, tout

    def per_deal(self, deal, events):
        out, ms, usd, tin, tout = self.run(
            PER_DEAL, {"deal": {**deal, "today": AS_OF}, "events": events})
        return {e["id"]: labels_from(out[e["id"]]) for e in events}, ms, usd, tin, tout

    def ledger(self, deal, events):
        out, ms, usd, tin, tout = self.run(LEDGER, {"deal": deal, "events": events})
        reasons = [r for r in (pick(x, REASON_KEYS) for x in out.get("reasons", []))
                   if r in REASON_KEYS]
        return {"p_at_risk": float(out["at_risk"]), "reasons": reasons}, ms, usd, tin, tout
