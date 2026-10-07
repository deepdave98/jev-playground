# /// script
# requires-python = ">=3.11"
# dependencies = ["mcp>=2.2,<3"]
# ///
"""MCP tools backed by the weekly Jev specs. Run with uv run."""

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
    # Give each week's spec.py a distinct module name.
    s = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(s)
    s.loader.exec_module(mod)
    return mod


w1 = load("week01", REPO / "week-01-lead-triage/src/spec.py")
w2 = load("week02", REPO / "week-02-deal-risk/src/spec.py")
w3 = load("week03", REPO / "week-03-reply-triage/src/spec.py")
w4 = load("week04", REPO / "week-04-meddpicc/src/spec.py")
w5 = load("week05", REPO / "week-05-account-dedup/src/spec.py")
w6 = load("week06", REPO / "week-06-deal-reactivation/src/reactivation.py")
jev = load("jev", REPO / "common/jev.py")

LEDGER_DIR = pathlib.Path(os.environ.get("JEV_LEDGER_DIR", REPO / "week-02-deal-risk/data")).resolve()

_local = threading.local()


# TypedDict returns provide MCP output schemas.
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


class Reply(TypedDict):
    category: str
    opt_out: bool
    meeting_intent: str
    route: str
    p_opt_out: float
    ms: int


class Meddpicc(TypedDict):
    elements: dict[str, str]
    forecast_ready: bool
    confirm: list[str]
    gaps: list[str]
    ms: int


class Match(TypedDict):
    relationship: str
    p_same: float
    action: str
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


class ReactivationQueue(TypedDict):
    as_of: str
    checked: int
    queue: list[dict]
    decisions: list[dict]


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
        "GTM decisions backed by Jev. Review the returned evidence before acting. "
        "Use triage_lead on a new inbound lead, deal_risk on one deal's activity, "
        "deals_at_risk to sweep a whole ledger export without reading it yourself, "
        "triage_reply on a reply to outbound, meddpicc on a call summary, and "
        "dedup_pair on two CRM accounts that might be one company, and "
        "reactivation_queue on closed-lost opportunities and recent product releases."
    ),
)


@server.tool()
async def triage_lead(company: str, title: str, message: str, headcount: int | None = None,
                      email: str = "", recent_activity: str = "", form: str = "") -> Lead:
    """Classify an inbound lead and return reject, ae_now, sdr_sequence,
    self_serve or nurture. Pass enriched headcount to determine segment.
    Includes disqualification and ICP-fit probabilities.
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
    """Check one deal's activity for risk. deal needs arr, close_date and
    champion; events need id, ts, source and text. Returns event labels and
    risk reasons computed by week 02's rules. today defaults to the current
    date; pass YYYY-MM-DD to review a historical export.
    """
    t = time.perf_counter()
    out = await asyncio.to_thread(judge_deal, deal, events, today or date.today().isoformat())
    return {**out, "ms": round((time.perf_counter() - t) * 1000)}


@server.tool()
async def deals_at_risk(ledger_file: str, today: str = "") -> Sweep:
    """Return risky deals from a ledger export, sorted by ARR with reasons.
    Pass just the filename, such as "ledger.jsonl"; the server opens it from
    its configured folder. Do not search for or read the file first.
    today accepts YYYY-MM-DD and defaults to the current date.
    """
    path = (LEDGER_DIR / ledger_file).resolve()
    if not path.is_relative_to(LEDGER_DIR) or not path.is_file():
        # ToolError exposes the refusal to the client.
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


@server.tool()
async def triage_reply(text: str, sender: str = "", subject: str = "", received: str = "") -> Reply:
    """Classify an outbound reply and return its route. Bare opt-out phrases
    such as "STOP" are suppressed without a model call. An opt-out probability
    from 0.4 to 0.6 routes to review. sender is the From line; include title
    and company when known.
    """
    if w3.only_stop_word(text):
        return {"category": "objection", "opt_out": True, "meeting_intent": "none",
                "route": "suppress", "p_opt_out": 1.0, "ms": 0}
    state = {"from": sender, "received": received, "in_reply_to": subject, "text": text}
    t = time.perf_counter()
    a = jev.decode((await asyncio.to_thread(ask, state, w3.QUESTIONS))["answers"], w3.QUESTIONS)
    p = a["opt_out"]
    lo, hi = w3.UNSURE
    where = "review" if lo <= p <= hi else w3.route(a["category"], p >= 0.5, a["meeting_intent"])
    return {"category": a["category"], "opt_out": p >= 0.5, "meeting_intent": a["meeting_intent"],
            "route": where, "p_opt_out": p, "ms": round((time.perf_counter() - t) * 1000)}


@server.tool()
async def meddpicc(summary: str, account: str = "", stage: str = "") -> Meddpicc:
    """Score eight MEDDPICC elements as none, mentioned or established.
    forecast_ready requires established metrics, economic_buyer and
    decision_process. Check the fields in confirm against the summary
    before accepting a forecast-ready result. gaps lists missing evidence.
    """
    state = {"account": account, "stage": stage, "summary": summary}
    t = time.perf_counter()
    a = jev.decode((await asyncio.to_thread(ask, state, w4.QUESTIONS))["answers"], w4.QUESTIONS,
                   shift=jev.SCORE_BIAS)
    card = {e: a[e] for e in w4.ELEMENTS}
    ready = w4.forecast_ready(card)
    return {"elements": card, "forecast_ready": ready,
            "confirm": list(w4.FORECAST_NEEDS) if ready else [], "gaps": w4.gaps(card),
            "ms": round((time.perf_counter() - t) * 1000)}


@server.tool()
async def dedup_pair(record_a: dict, record_b: dict) -> Match:
    """Compare two CRM accounts using available name, domain, country,
    industry, employees and source. Returns same, related or different and
    a suggested action. merge requires same with p_same >= 0.9; lower scores
    go to review. Related accounts, including parent/subsidiary pairs,
    should stay separate.
    """
    state = {"record_a": record_a, "record_b": record_b}
    t = time.perf_counter()
    a = jev.decode((await asyncio.to_thread(ask, state, w5.QUESTIONS))["answers"], w5.QUESTIONS)
    return {"relationship": a["relationship"], "p_same": a["same_company"],
            "action": w5.action(a["relationship"], a["same_company"]),
            "ms": round((time.perf_counter() - t) * 1000)}


@server.tool()
async def reactivation_queue(records: list[dict], as_of: str) -> ReactivationQueue:
    """Find closed-lost deals whose product blocker may have cleared.

    Each record needs id, account_id, owner, stage, lost_on, loss_reason,
    customer, open_opportunity, opt_out, and updates (id, published_on, text).
    last_contacted_on is optional. Dates use YYYY-MM-DD. Use current CRM
    flags for every account. Returns a review queue with source text and
    every excluded or uncertain decision. Sends no messages or CRM writes.
    """
    if len(records) > 100:
        raise ToolError("Pass at most 100 opportunities per call")
    def judge(state, questions):
        return jev.decode(ask(state, questions)["answers"], questions)
    try:
        return await asyncio.to_thread(w6.build_queue, records, as_of, judge)
    except (ValueError, TypeError, KeyError) as exc:
        raise ToolError(str(exc)) from exc


if __name__ == "__main__":
    server.run("stdio")
