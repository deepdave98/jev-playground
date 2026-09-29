"""Claude through the `claude` CLI, with the corrections from week 01.

There's no ANTHROPIC_API_KEY on the benchmark machine, so calls go through
the CLI, and three things keep that fair: thinking is off, the CLI's own
scaffolding is measured and subtracted from token counts, and cache reads
are billed at the cache rate. week-01-lead-triage/README.md has how each one
was found, and what the numbers looked like before.
"""

import json
import os
import re
import statistics
import subprocess
import time

PRICE = {  # per token at list price: (input, output)
    "claude-haiku-4-5": (1.00e-6, 5.00e-6),
    "claude-sonnet-5": (2.00e-6, 10.00e-6),
}


def parse(text):
    """Claude is asked for bare JSON. Tolerate a fence or a stray sentence."""
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0) if m else text)


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
        # duration_api_ms leaves out process startup, which isn't the model's time
        return data, float(data.get("duration_api_ms", wall))

    def calibrate(self, n=5):
        """Tokens the CLI adds before our prompt, as the median of n empty calls."""
        counts = []
        for _ in range(n):
            u = self.call("", ".")[0]["usage"]
            counts.append(u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
                          + u.get("cache_read_input_tokens", 0))
        self.overhead = int(statistics.median(counts))
        return counts

    def cost(self, usage):
        """Dollars for one call and the input tokens our prompt accounts for."""
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

    def ask(self, system, payload):
        """Send a JSON payload. Returns the parsed answer, ms, dollars and tokens."""
        data, ms = self.call(system, json.dumps(payload))
        usd, tokens_in = self.cost(data["usage"])
        return parse(data.get("result", "")), ms, usd, tokens_in, data["usage"]["output_tokens"]
