# /// script
# requires-python = ">=3.11"
# dependencies = ["mcp>=2.2,<3"]
# ///
"""Starts the server the way an agent would and calls each tool once.

    uv run mcp-server/check.py

Talks to the live Jev API, so it needs TYPESAFE_API_KEY set.
"""

import asyncio
import json
import os
import pathlib
import sys

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

HERE = pathlib.Path(__file__).resolve().parent
LEDGER = HERE.parent / "week-02-deal-risk/data/ledger.jsonl"


def show(result):
    # Every tool declares an output schema, so structured content should
    # always be there. Falling back to the text would hide it if it wasn't.
    if result.structured_content is None:
        sys.exit("no structured content, check the tool's return annotation")
    return json.dumps(result.structured_content, indent=2)


async def main():
    params = StdioServerParameters(
        command="uv", args=["run", "--quiet", str(HERE / "jev_server.py")],
        env={**os.environ})

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as s:
            await s.initialize()
            tools = (await s.list_tools()).tools
            print("tools:", ", ".join(t.name for t in tools))

            print("\ntriage_lead, the Siemens lead from week 01")
            print(show(await s.call_tool("triage_lead", {
                "company": "Siemens", "headcount": 320000,
                "title": "Director of Revenue Operations", "email": "k.brandt@siemens.com",
                "form": "demo_request",
                "message": "We've shortlisted three vendors and need to close by end of Q1. "
                           "400 seats. Our security team needs SOC 2 Type II and a completed "
                           "VPAT before we can move to paper. Who handles procurement?",
            })))

            row = json.loads(LEDGER.read_text().splitlines()[2])  # Ironbridge
            print("\ndeal_risk, Ironbridge on the benchmark date")
            print(show(await s.call_tool("deal_risk", {
                "deal": row["deal"], "events": row["events"], "today": "2026-09-25"})))

            print("\ndeals_at_risk, the whole week 02 ledger")
            print(show(await s.call_tool("deals_at_risk", {
                "ledger_file": "ledger.jsonl", "today": "2026-09-25"})))

            bad = await s.call_tool("deals_at_risk", {"ledger_file": "../../.env.local"})
            print("\nasking for a file outside the ledger dir is refused:", bad.is_error)
            if not bad.is_error:
                sys.exit("path check failed")


asyncio.run(main())
