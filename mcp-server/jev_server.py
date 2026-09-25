# /// script
# requires-python = ">=3.11"
# dependencies = ["mcp>=2.2,<3"]
# ///
"""An MCP server that puts the playground's Jev workflows behind three tools.

    uv run mcp-server/jev_server.py

The tools load their questions straight from each week's spec.py, so what
an agent gets here is exactly what the benchmarks measured. If you tune a
prompt, tune it in the week folder and re-run the benchmark first.
"""

import asyncio
import http.client
import importlib.util
import json
import os
import pathlib
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from typing import TypedDict

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

REPO = pathlib.Path(__file__).resolve().parents[1]


def load(name, path):
    # Both weeks call their module spec.py, so a plain import would hand back
    # whichever one loaded first.
    s = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(s)
    s.loader.exec_module(mod)
    return mod


w1 = load("week01", REPO / "week-01-lead-triage/src/spec.py")
w2 = load("week02", REPO / "week-02-deal-risk/src/spec.py")

LEDGER_DIR = pathlib.Path(os.environ.get("JEV_LEDGER_DIR", REPO / "week-02-deal-risk/data")).resolve()

_local = threading.local()


# Typed returns give each tool an output schema. With a bare dict the SDK
# sends the result as JSON text and clients get no structured content.
class Lead(TypedDict):
    disqualify: bool
    icp_fit: bool
    segment: str
    intent: str
    route: str
    p_disqualify: float
    p_icp_fit: float
    ms: int


class EventLabel(TypedDict):
    id: str
    signal: str
    severity: str
    exec_engaged: bool


class DealRisk(TypedDict):
    deal: str
    arr: int | None
    at_risk: bool
    reasons: list[str]
    summary: str
    events: list[EventLabel]
    ms: int


class Flag(TypedDict):
    deal: str
    arr: int | None
    why: str


class Sweep(TypedDict):
    checked: int
    events: int
    at_risk: list[Flag]
    arr_at_risk: int
    ms: int


def ask(state, questions):
    """One Jev request. Each thread keeps its own warm connection."""
    conn = getattr(_local, "conn", None)
    if conn is None:
        conn = _local.conn = http.client.HTTPSConnection("api.typesafe.ai", timeout=60)
    body = json.dumps({"model": "jev-latest", "state": state, "questions": questions})
    headers = {"authorization": f"Bearer {os.environ['TYPESAFE_API_KEY']}",
               "content-type": "application/json"}
    for attempt in range(3):
        try:
            conn.request("POST", "/v1/systemone", body=body, headers=headers)
            resp = conn.getresponse()
            raw = resp.read()
            if resp.status != 200:
                raise RuntimeError(f"Jev returned {resp.status}: {raw[:200]!r}")
            return json.loads(raw)
        except (http.client.HTTPException, OSError):
            conn.close()
            conn = _local.conn = http.client.HTTPSConnection("api.typesafe.ai", timeout=60)
            if attempt == 2:
                raise


def judge_deal(deal, events, today):
    questions = {}
    for e in events:
        for name, q in w2.EVENT_QUESTIONS.items():
            questions[f"{e['id']}_{name}"] = {
                **q, "instructions": f"About event {e['id']} only. " + q["instructions"]}
    state = {"deal": {**deal, "today": today},
             "events": [{k: e.get(k) for k in ("id", "ts", "source", "text")} for e in events]}
    answers = ask(state, questions)["answers"]

    judged = []
    for e in events:
        a = lambda k: answers[f"{e['id']}_{k}"]  # noqa: E731
        judged.append({**e,
                       "signal": a("signal")["choice"],
                       "severity": w2.SEV[max(0, min(3, round(a("severity")["score"])))],
                       "exec_engaged": a("exec_engaged")["noul"] >= 0.5})

    reasons = w2.assess(deal, judged, as_of=today)
    return {
        "deal": deal.get("account", deal.get("id")),
        "arr": deal.get("arr"),
        "at_risk": bool(reasons),
        "reasons": reasons,
        "summary": w2.describe(reasons, deal, judged, as_of=today),
        "events": [{"id": e["id"], "signal": e["signal"], "severity": e["severity"],
                    "exec_engaged": e["exec_engaged"]} for e in judged],
    }


server = MCPServer(
    name="jev-gtm",
    instructions=(
        "Typed GTM decisions backed by Jev. They return labels and probabilities, "
        "never prose, so write any email or summary yourself from what comes back. "
        "Use triage_lead on a new inbound lead, deal_risk on one deal's activity, and "
        "deals_at_risk to sweep a whole ledger export without reading it yourself."
    ),
)


@server.tool()
async def triage_lead(company: str, title: str, message: str, headcount: int | None = None,
                      email: str = "", recent_activity: str = "", form: str = "") -> Lead:
    """Decide what to do with one inbound lead.

    Returns the four judgments from week 01 of the playground (disqualify,
    icp_fit, segment, intent) with Jev's probabilities, and the queue the lead
    should go to: reject, ae_now, sdr_sequence, self_serve or nurture. About
    360 ms once warm. Fill in headcount if you have it from enrichment, since
    segment reads it directly.
    """
    state = {"company": company, "employee_headcount": headcount, "job_title": title,
             "email": email, "form": form, "message": message,
             "recent_activity": recent_activity}
    t = time.perf_counter()
    a = (await asyncio.to_thread(ask, state, w1.build_questions("v1")))["answers"]

    level = max(0, min(3, round(a["intent"]["score"])))
    decision = {
        "disqualify": a["disqualify"]["noul"] >= 0.5,
        "icp_fit": a["icp_fit"]["noul"] >= 0.5,
        "segment": a["segment"]["choice"],
        "intent": w1.INTENT_LEVELS[level],
    }
    return {**decision, "route": w1.route(**decision),
            "p_disqualify": a["disqualify"]["noul"], "p_icp_fit": a["icp_fit"]["noul"],
            "ms": round((time.perf_counter() - t) * 1000)}


@server.tool()
async def deal_risk(deal: dict, events: list[dict], today: str = "") -> DealRisk:
    """Check one open deal for risk from its activity ledger.

    deal needs arr, close_date and champion (for example "Dana Whitfield,
    Director of RevOps"); account and stage help. Each event needs id, ts,
    source and text, the way an activity database exports them. Every event is
    judged in a single Jev request, then the week 02 rule turns those judgments
    into reasons such as competitor, escalations, champion_left, stalled,
    no_exec_30d and closing_with_issues. today defaults to the real date.
    """
    t = time.perf_counter()
    out = await asyncio.to_thread(judge_deal, deal, events, today or date.today().isoformat())
    return {**out, "ms": round((time.perf_counter() - t) * 1000)}


@server.tool()
async def deals_at_risk(ledger_file: str, today: str = "") -> Sweep:
    """Sweep a whole ledger export and return only the deals at risk.

    Pass just the file name, like "ledger.jsonl". This server opens it from
    its own ledger folder, so there's no need to find, open or check the
    file first, and reading it yourself defeats the point of the tool. Deals
    are checked in parallel and only the ones that need attention come back,
    biggest first, each with the reason.
    """
    path = (LEDGER_DIR / ledger_file).resolve()
    if not path.is_relative_to(LEDGER_DIR) or not path.is_file():
        # ToolError, so the agent sees why and can fix the path. Anything else
        # reaches it as a blank failure.
        raise ToolError(f"{ledger_file} is not a file under {LEDGER_DIR}")

    rows = [json.loads(line) for line in path.open() if line.strip()]
    day = today or date.today().isoformat()
    t = time.perf_counter()

    def one(row):
        return judge_deal(row["deal"], row["events"], day)

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = await asyncio.to_thread(lambda: list(pool.map(one, rows)))

    risky = sorted((r for r in results if r["at_risk"]), key=lambda r: -(r["arr"] or 0))
    return {
        "checked": len(results),
        "events": sum(len(r["events"]) for r in rows),
        "at_risk": [{"deal": r["deal"], "arr": r["arr"], "why": r["summary"]} for r in risky],
        "arr_at_risk": sum(r["arr"] or 0 for r in risky),
        "ms": round((time.perf_counter() - t) * 1000),
    }


if __name__ == "__main__":
    server.run("stdio")
