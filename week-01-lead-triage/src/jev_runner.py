"""Jev side of the benchmark.

One HTTP request per lead carrying all four typed questions. The connection is
reused across leads, because opening a fresh TLS session costs about 600ms from
this machine and that has nothing to do with the model.
"""

import http.client
import json
import os
import time

HOST = "api.typesafe.ai"
PATH = "/v1/systemone"
MODEL = "jev-latest"

# Published rate, input only. Output tokens are not billed.
# https://www.typesafe.ai/  ("$42 per billion input tokens")
USD_PER_INPUT_TOKEN = 42.0 / 1_000_000_000


def build_state(lead: dict) -> dict:
    """The lead record, passed as structured state rather than prose."""
    return {
        "company": lead["company"],
        "employee_headcount": lead["headcount"],
        "job_title": lead["title"],
        "email": lead["email"],
        "form": lead["source"],
        "message": lead["message"],
        "recent_activity": lead["recent_activity"],
    }


class JevRunner:
    name = "jev"

    def __init__(self, questions: dict, api_key: str | None = None, variant: str = "v1"):
        self.questions = questions
        self.variant = variant
        self.key = api_key or os.environ["TYPESAFE_API_KEY"]
        self.conn = None

    def _connect(self):
        self.conn = http.client.HTTPSConnection(HOST, timeout=60)

    def measure_connect_cost(self, samples: int = 5) -> float:
        """Median wall time of a cold TCP+TLS handshake, in ms.

        Reported alongside the results so the network floor is visible instead
        of being quietly folded into the model's number.
        """
        import socket
        import ssl
        import statistics

        out = []
        ctx = ssl.create_default_context()
        for _ in range(samples):
            t = time.perf_counter()
            sock = socket.create_connection((HOST, 443), timeout=15)
            ctx.wrap_socket(sock, server_hostname=HOST).close()
            out.append((time.perf_counter() - t) * 1000)
        return statistics.median(out)

    def run(self, lead: dict) -> dict:
        body = json.dumps({
            "model": MODEL,
            "state": build_state(lead),
            "questions": self.questions,
        })
        headers = {"authorization": f"Bearer {self.key}", "content-type": "application/json"}

        last_err = None
        for attempt in range(3):
            if self.conn is None:
                self._connect()
            try:
                t = time.perf_counter()
                self.conn.request("POST", PATH, body=body, headers=headers)
                resp = self.conn.getresponse()
                raw = resp.read()
                elapsed_ms = (time.perf_counter() - t) * 1000
                if resp.status != 200:
                    raise RuntimeError(f"HTTP {resp.status}: {raw[:200]!r}")
                data = json.loads(raw)
                break
            except Exception as exc:  # dropped keep-alive, transient 5xx
                last_err = exc
                try:
                    self.conn.close()
                except Exception:
                    pass
                self.conn = None
                if attempt == 2:
                    raise
                time.sleep(1.0 + attempt)
        else:  # pragma: no cover
            raise last_err

        answers = data["answers"]
        usage = data.get("usage", {})
        input_tokens = usage.get("input_tokens", 0)

        return {
            "runner": self.name,
            "model": data.get("model"),
            "latency_ms": elapsed_ms,
            "requests": 1,
            "input_tokens": input_tokens,
            "output_tokens": usage.get("output_tokens", 0),
            "billed_usd": input_tokens * USD_PER_INPUT_TOKEN,
            "prediction": {
                # noul answers are probabilities; 0.5 is the decision threshold.
                "disqualify": answers["disqualify"]["noul"] >= 0.5,
                "icp_fit": answers["icp_fit"]["noul"] >= 0.5,
                "segment": answers["segment"]["choice"],
                "intent": _intent_label(answers["intent"]),
            },
            # Kept separately so calibration can be scored without re-running.
            "confidence": {
                "disqualify": answers["disqualify"]["noul"],
                "icp_fit": answers["icp_fit"]["noul"],
                "segment": answers["segment"]["confidence"],
                "intent": answers["intent"]["confidence"],
            },
            "raw": data,
        }

    def close(self):
        if self.conn is not None:
            self.conn.close()
            self.conn = None


def _intent_label(answer: dict) -> str:
    """Jev returns a continuous score plus a legend. Round to the nearest level."""
    from spec import INTENT_LEVELS

    legend = answer.get("legend")
    idx = int(round(answer["score"]))
    idx = max(0, min(len(INTENT_LEVELS) - 1, idx))
    if legend:
        # The legend maps index to the criteria string we sent; prefer it so a
        # future reordering on their side cannot silently shift the mapping.
        label = legend.get(str(idx), "")
        for level in INTENT_LEVELS:
            if label.startswith(level):
                return level
    return INTENT_LEVELS[idx]
