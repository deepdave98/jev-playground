"""Jev over HTTP, with the connection kept warm between calls.

Weeks 01 and 02 keep their own copies of this, so their published numbers
reproduce exactly as they were run. Week 03 onward use this one.
"""

import http.client
import json
import os
import time

HOST, PATH = "api.typesafe.ai", "/v1/systemone"
USD_PER_TOKEN = 42 / 1_000_000_000  # input only, output isn't billed


class Jev:
    def __init__(self, key=None):
        self.key = key or os.environ["TYPESAFE_API_KEY"]
        self.conn = None

    def ask(self, state, questions):
        """One request. Returns the parsed body and the round trip in ms."""
        body = json.dumps({"model": "jev-latest", "state": state, "questions": questions})
        headers = {"authorization": f"Bearer {self.key}", "content-type": "application/json"}
        for attempt in range(3):
            if self.conn is None:
                self.conn = http.client.HTTPSConnection(HOST, timeout=60)
            try:
                t = time.perf_counter()
                self.conn.request("POST", PATH, body=body, headers=headers)
                resp = self.conn.getresponse()
                raw = resp.read()
                ms = (time.perf_counter() - t) * 1000
                if resp.status != 200:
                    raise RuntimeError(f"HTTP {resp.status}: {raw[:200]!r}")
                return json.loads(raw), ms
            except (http.client.HTTPException, OSError, RuntimeError):
                # keep-alive connections get dropped now and then
                self.conn.close()
                self.conn = None
                if attempt == 2:
                    raise
                time.sleep(1 + attempt)

    def warm(self):
        """Pay the TLS handshake before anything is timed."""
        self.ask({"warm": True}, {"q": {"type": "noul", "instructions": "Is this a warmup?"}})

    def close(self):
        if self.conn:
            self.conn.close()


def levels(q):
    """The level names of a score question, from criteria like "none: ..."."""
    return [c.split(":")[0].strip() for c in q["criteria"]]


def decode(answers, questions, prefix=""):
    """Jev's typed answers, in the shape the scorers compare against.

    noul comes back as a probability, choice as the chosen key, score as the
    nearest level name. Keep the raw score too if you care about the bias.
    """
    out = {}
    for name, q in questions.items():
        a = answers[prefix + name]
        if q["type"] == "noul":
            out[name] = a["noul"]
        elif q["type"] == "choice":
            out[name] = a["choice"]
        else:
            names = levels(q)
            out[name] = names[max(0, min(len(names) - 1, round(a["score"])))]
            out[name + "_score"] = a["score"]
    return out
