# Graph Report - victoria  (2026-09-29)

## Corpus Check
- 57 files · ~42,707 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 49 file(s) not represented in the graph (top: .jsonl 35, .log 11, (none) 2)

## Summary
- 437 nodes · 831 edges · 15 communities (14 shown, 1 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 36 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `3a7db0ed`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Week 02: which deals are at risk, from an AckDB activity ledger
- jev_server.py
- week-02-deal-risk/src/bench.py
- json
- claude_runner.py
- week-01-lead-triage/src/score.py
- week-03-reply-triage/src/bench.py
- Claude
- Week 01: inbound lead triage and routing
- Week 03: triaging replies to outbound sequences
- Week 05: duplicate accounts in a CRM
- Week 04: filling in MEDDPICC from call summaries
- check.py
- Working in this repo
- README.md

## God Nodes (most connected - your core abstractions)
1. `Claude` - 18 edges
2. `load()` - 14 edges
3. `decode()` - 14 edges
4. `Claude` - 13 edges
5. `Week 02: which deals are at risk, from an AckDB activity ledger` - 13 edges
6. `Jev` - 12 edges
7. `read()` - 12 edges
8. `ClaudeRunner` - 12 edges
9. `deals_at_risk()` - 10 edges
10. `run()` - 9 edges

## Surprising Connections (you probably didn't know these)
- `From events to a verdict` --references--> `assess()`  [INFERRED]
  week-02-deal-risk/rubric.md → week-02-deal-risk/src/spec.py
- `The forecast rule` --references--> `forecast_ready()`  [INFERRED]
  week-04-meddpicc/rubric.md → week-04-meddpicc/src/spec.py
- `The three labels` --references--> `action()`  [INFERRED]
  week-05-account-dedup/rubric.md → week-05-account-dedup/src/spec.py
- `run()` --uses--> `Claude`  [INFERRED]
  week-02-deal-risk/src/bench.py → common/claude.py
- `main()` --uses--> `Claude`  [INFERRED]
  week-02-deal-risk/src/brief.py → common/claude.py

## Import Cycles
- None detected.

## Communities (15 total, 1 thin omitted)

### Community 0 - "Week 02: which deals are at risk, from an AckDB activity ledger"
Cohesion: 0.09
Nodes (21): At the volume AckDB is drawn for, Caveats, Claude applying the rule is worse than code applying it, Results, Running it, The last step, and the mistake it made first, The trap that caught Sonnet, Three models, the same four misses (+13 more)

### Community 1 - "jev_server.py"
Cohesion: 0.07
Nodes (46): concurrent_futures, importlib_util, ask(), deal_risk(), DealRisk, deals_at_risk(), one(), dedup_pair() (+38 more)

### Community 2 - "week-02-deal-risk/src/bench.py"
Cohesion: 0.07
Nodes (34): datetime, The six setups, judged(), load(), main(), Runs every configuration over the ledger, one after another. python3…, run(), facts() (+26 more)

### Community 3 - "json"
Cohesion: 0.06
Nodes (49): collections, load(), The loop every week's benchmark runs, one request at a time. Sequential on…, Per-item labels and every call, from a run file., brier(), pct(), The two numbers every week's scorer needs., Mean squared gap between a stated probability and what happened. pairs is… (+41 more)

### Community 4 - "claude_runner.py"
Cohesion: 0.07
Nodes (38): time, load_leads(), main(), Runs the benchmark and writes results/raw/<runner>.jsonl. Sequential on…, run_one(), build_system_prompt(), build_user_prompt(), ClaudeRunner (+30 more)

### Community 5 - "week-01-lead-triage/src/score.py"
Cohesion: 0.11
Nodes (21): Path, statistics, brier(), ece(), main(), pct(), Scores results/raw/*.jsonl into results/results.json and a printed table.…, Nearest-rank percentile. n=60, so interpolation would be false precision. (+13 more)

### Community 6 - "week-03-reply-triage/src/bench.py"
Cohesion: 0.08
Nodes (46): Feed items to step() a batch at a time and write one line per request.…, run(), decode(), Jev, levels(), Jev over HTTP, with the connection kept warm between calls. Weeks 01 and 02…, One request. Returns the parsed body and the round trip in ms., Pay the TLS handshake before anything is timed. (+38 more)

### Community 7 - "Claude"
Cohesion: 0.13
Nodes (10): Claude, parse(), Claude through the `claude` CLI, with the corrections from week 01. There's no…, Claude is asked for bare JSON. Tolerate a fence or a stray sentence., Tokens the CLI adds before our prompt, as the median of n empty calls., Dollars for one call and the input tokens our prompt accounts for., Send a JSON payload. Returns the parsed answer, ms, dollars and tokens., Refuses a commit if any staged text file contains an em or en dash. git config… (+2 more)

### Community 8 - "Week 01: inbound lead triage and routing"
Cohesion: 0.11
Nodes (17): Caveats, Running it, Step 6, which Jev cannot do, The result, Week 01: inbound lead triage and routing, What I had to fix before any of this was fair, What I would ship, Where Jev loses (+9 more)

### Community 9 - "Week 03: triaging replies to outbound sequences"
Cohesion: 0.11
Nodes (16): Batching unrelated replies costs a little accuracy, Both opt-out mistakes scored between 0.4 and 0.6, Haiku answered the wrong question six times, Jev's score answers run high, third week running, Pulling out return dates and new contacts, Results, Running it, Week 03: triaging replies to outbound sequences (+8 more)

### Community 10 - "Week 05: duplicate accounts in a CRM"
Cohesion: 0.12
Nodes (14): Haiku and Sonnet knew too, Jev knew who owns whom, Results, Running it, Thinking fixed it, at about 470 times the price, Week 05: duplicate accounts in a CRM, What I'd ship, Whose confidence can gate a merge (+6 more)

### Community 11 - "Week 04: filling in MEDDPICC from call summaries"
Cohesion: 0.13
Nodes (13): A second opinion on the deals Jev marks ready, Everyone reads MEDDPICC too generously, It didn't fix Pinecrest, Results, Running it, The bias correction worked, on a week it had never seen, Week 04: filling in MEDDPICC from call summaries, What I'd ship (+5 more)

### Community 12 - "check.py"
Cohesion: 0.32
Nodes (7): asyncio, mcp, mcp_client_stdio, find(), main(), Starts the server the way an agent would and calls each tool once. uv run mcp-…, show()

### Community 13 - "Working in this repo"
Cohesion: 0.29
Nodes (6): House rules, Secrets, The MCP server, Use the graph before reading files, Working in this repo, Writing

## Knowledge Gaps
- **79 isolated node(s):** `Use the graph before reading files`, `House rules`, `The MCP server`, `Writing`, `Secrets` (+74 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 201 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **1 thin communities (<3 nodes) omitted from report**: run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `assess()` connect `week-02-deal-risk/src/bench.py` to `Week 02: which deals are at risk, from an AckDB activity ledger`?**
  _High betweenness centrality (0.098) - this node is a cross-community bridge._
- **Why does `action()` connect `json` to `Week 05: duplicate accounts in a CRM`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Why does `forecast_ready()` connect `json` to `Week 04: filling in MEDDPICC from call summaries`?**
  _High betweenness centrality (0.060) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `Claude` (e.g. with `run()` and `main()`) actually correct?**
  _`Claude` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Use the graph before reading files`, `House rules`, `The MCP server` to the rest of the system?**
  _79 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Week 02: which deals are at risk, from an AckDB activity ledger` be split into smaller, more focused modules?**
  _Cohesion score 0.08695652173913043 - nodes in this community are weakly interconnected._
- **Should `jev_server.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07312925170068027 - nodes in this community are weakly interconnected._