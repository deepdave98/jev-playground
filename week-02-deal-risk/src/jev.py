"""Jev calls for week 02, in two shapes.

per_event: one request per event, three questions each.
per_deal:  one request per deal. The whole ledger goes in as state and every
           event gets its own three questions, keyed by event id. 73 events
           become 20 round trips.
"""

import http.client
import json
import os
import time

from spec import AS_OF, EVENT_QUESTIONS, SEV

HOST, PATH = "api.typesafe.ai", "/v1/systemone"
USD_PER_TOKEN = 42 / 1_000_000_000  # input only, output is not billed


def deal_context(deal):
    return {**deal, "today": AS_OF}


def visible(e):
    return {k: e[k] for k in ("id", "ts", "source", "text")}


def read(answers, prefix=""):
    """Turn Jev's typed answers back into the three labels."""
    sig = answers[prefix + "signal"]
    sev = answers[prefix + "severity"]
    ex = answers[prefix + "exec_engaged"]
    level = max(0, min(3, round(sev["score"])))
    return {
        "signal": sig["choice"],
        "severity": SEV[level],
        "exec_engaged": ex["noul"] >= 0.5,
        "p_exec": ex["noul"],
        "severity_score": sev["score"],
    }


class Jev:
    def __init__(self):
        self.key = os.environ["TYPESAFE_API_KEY"]
        self.conn = None

    def ask(self, state, questions):
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
            except Exception:
                # keep-alive connections get dropped now and then, reconnect
                self.conn.close()
                self.conn = None
                if attempt == 2:
                    raise
                time.sleep(1 + attempt)

    def per_event(self, deal, event):
        state = {"deal": deal_context(deal), "event": visible(event)}
        data, ms = self.ask(state, EVENT_QUESTIONS)
        tokens = data["usage"]["input_tokens"]
        return read(data["answers"]), ms, tokens

    def per_deal(self, deal, events):
        questions = {}
        for e in events:
            for name, q in EVENT_QUESTIONS.items():
                questions[f"{e['id']}_{name}"] = {
                    **q, "instructions": f"About event {e['id']} only. " + q["instructions"]}
        state = {"deal": deal_context(deal), "events": [visible(e) for e in events]}
        data, ms = self.ask(state, questions)
        tokens = data["usage"]["input_tokens"]
        labels = {e["id"]: read(data["answers"], f"{e['id']}_") for e in events}
        return labels, ms, tokens

    def close(self):
        if self.conn:
            self.conn.close()
