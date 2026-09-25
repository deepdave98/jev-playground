# Graph Report - victoria  (2026-09-25)

## Corpus Check
- Corpus is ~25,306 words - fits in a single context window. You may not need a graph.

## Summary
- 289 nodes · 692 edges · 9 communities (8 shown, 1 thin omitted)
- Extraction: 83% EXTRACTED · 17% INFERRED · 0% AMBIGUOUS · INFERRED: 116 edges (avg confidence: 0.9)
- Token cost: 649,590 input · 0 output

## Community Hubs (Navigation)
- Week 02 Findings and Design Rules
- Repo Setup and MCP Check
- Week 02 Harness and Setups
- Shared Specs and Benchmark Rules
- Week 01 Claude Runs and Fairness
- Jev Model, Cost and Results
- House Rules and Writing
- Week 02 Ledger and Answer Key
- Segment Enum

## God Nodes (most connected - your core abstractions)
1. `assess()` - 25 edges
2. `build_questions()` - 19 edges
3. `run()` - 18 edges
4. `triage_lead()` - 16 edges
5. `deals_at_risk()` - 15 edges
6. `ClaudeRunner` - 15 edges
7. `route()` - 14 edges
8. `Claude` - 13 edges
9. `judge_deal()` - 12 edges
10. `score_file()` - 12 edges

## Surprising Connections (you probably didn't know these)
- `judge_deal()` --implements--> `Batch by deal (per-entity batching)`  [INFERRED]
  mcp-server/jev_server.py → week-02-deal-risk/README.md
- `triage_lead()` --conceptually_related_to--> `Jev's half-level intent optimism bias`  [INFERRED]
  mcp-server/jev_server.py → week-01-lead-triage/README.md
- `Finding: Sonnet applying the risk rule itself scored 70%, 100% when code applied it` --references--> `route()`  [INFERRED]
  week-02-deal-risk/README.md → week-01-lead-triage/src/spec.py
- `Review step: Claude checks Jev's flags and writes the deal-owner note` --references--> `prove_jev_cannot_write()`  [INFERRED]
  week-02-deal-risk/README.md → week-01-lead-triage/src/step6_email.py
- `Ledger JSONL input shape (one deal per line with its events)` --shares_data_with--> `main()`  [INFERRED]
  mcp-server/README.md → week-02-deal-risk/src/ledger.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Four typed judgments feed the deterministic routing rule**: src_spec_disqualify_question, src_spec_icp_fit_question, src_spec_segment_question, src_spec_intent_question, week_01_lead_triage_src_spec_route [EXTRACTED 1.00]
- **Three per-event judgments feed the spec.assess risk rule**: week_02_deal_risk_src_spec_signal_judgment, week_02_deal_risk_src_spec_severity_judgment, week_02_deal_risk_src_spec_exec_engaged_judgment, week_02_deal_risk_src_spec_assess [EXTRACTED 1.00]
- **Jev, Haiku and Sonnet per event miss the same four exec events**: week_02_deal_risk_readme_setup_jev, week_02_deal_risk_readme_setup_claude_haiku_4_5, week_02_deal_risk_readme_setup_claude_sonnet_5, week_02_deal_risk_readme_same_four_misses, week_02_deal_risk_src_spec_exec_engaged_judgment [EXTRACTED 1.00]
- **Date and threshold arithmetic moved out of prompts into code**: week_02_deal_risk_readme_claude_applying_rule, week_02_deal_risk_readme_datacore_date_error, week_02_deal_risk_readme_keep_arithmetic_out_of_prompts, week_02_deal_risk_src_spec_reason_no_exec_30d, week_02_deal_risk_src_brief_facts, week_02_deal_risk_src_spec_assess [EXTRACTED 1.00]
- **Claude-favouring fairness corrections applied before publishing**: week_01_lead_triage_readme_thinking_disabled_correction, week_01_lead_triage_readme_prompt_cache_pricing_correction, week_01_lead_triage_readme_cli_overhead_calibration_correction, week_01_lead_triage_readme_cli_instead_of_api_caveat, readme_fix_the_unfair_thing [EXTRACTED 1.00]
- **Inbound lead agent workflow: CRM, enrichment, triage_lead, route in code, Slack**: mcp_server_readme_crm_server, mcp_server_readme_enrichment_server, mcp_server_jev_server_triage_lead, week_01_lead_triage_src_spec_route, mcp_server_readme_slack_server [EXTRACTED 1.00]
- **Monday risk sweep: ledger export, deals_at_risk, week 02 rule, Slack**: week_02_deal_risk_readme_ackdb, mcp_server_jev_server_ledger_dir, mcp_server_jev_server_deals_at_risk, week_02_deal_risk_src_spec_assess, mcp_server_readme_slack_server [EXTRACTED 1.00]

## Communities (9 total, 1 thin omitted)

### Community 0 - "Week 02 Findings and Design Rules"
Cohesion: 0.10
Nodes (45): House rule: keep arithmetic out of prompts, Hand the agent day counts instead of date arithmetic, Week 02 rule thresholds ($100K exec rule, 30 days, 7 days to close), AckDB (activity ledger and at-risk deals screen), Batch by deal (per-entity batching), Check the category before the magnitude, Finding: Sonnet applying the risk rule itself scored 70%, 100% when code applied it, Review step's date-arithmetic error on Datacore, fixed by passing computed facts (+37 more)

### Community 1 - "Repo Setup and MCP Check"
Cohesion: 0.10
Nodes (41): Query the graphify graph before reading files, TYPESAFE_API_KEY (kept in gitignored .env.local), Working in this repo (CLAUDE.md), main(), Starts the server the way an agent would and calls each tool once. uv run mcp-…, show(), ask(), deal_risk() (+33 more)

### Community 2 - "Week 02 Harness and Setups"
Cohesion: 0.10
Nodes (26): judge_deal(), Setup claude-sonnet-5-ledger: Sonnet 5 reads the whole ledger and applies the rule itself (20 calls), judged(), Label-leak guard: the answer lives next to the deal, never inside it, load(), main(), run(), main() (+18 more)

### Community 3 - "Shared Specs and Benchmark Rules"
Cohesion: 0.08
Nodes (37): load(), Tools load their questions from each week's spec.py, House rule: the answer key is written by hand, House rule: both sides get the same words, RUNNERS registry, Sequential runs preserve latency validity, COMPETITOR_CLARIFICATION (v2 prompt delta), Typed judgment: disqualify (noul / probability) (+29 more)

### Community 4 - "Week 01 Claude Runs and Fairness"
Cohesion: 0.10
Nodes (31): House rule: fix the unfair thing even when it helps the other side, Result record: claude-haiku-4-5-split, Result record: claude-sonnet-5, Correlated-error hypothesis (Haiku conflates disqualify and icp_fit), Emails written only for ae_now and sdr_sequence leads, Claude through the CLI instead of the API (duration_api_ms, scaffolding subtracted), Fairness correction: CLI token-overhead calibration, Do not read the partial run (+23 more)

### Community 5 - "Jev Model, Cost and Results"
Cohesion: 0.07
Nodes (33): Competitor list in the prompt (Hexline, Corvid, Tallyworks), Per-call cost, Jev against Sonnet 5, Path, Jev typed decision model, TypeSafe AI (Jev vendor), Result record: jev, noul probability with a 0.5 decision threshold, USD_PER_INPUT_TOKEN ($42 per billion, input only) (+25 more)

### Community 6 - "House Rules and Writing"
Cohesion: 0.12
Nodes (18): House rule: README numbers come from a committed run in results/raw/, Writing rules (plain English, no em dashes), Warm connection latency (979 ms first call, 360 ms median), House rules for the benchmarks, House rule: measure the network, not just the model, House rule: publish the failures, Sample-size caveat (60 leads, 20 deals, one laptop), House rule: say where the other thing wins (+10 more)

### Community 7 - "Week 02 Ledger and Answer Key"
Cohesion: 0.17
Nodes (12): Ledger JSONL input shape (one deal per line with its events), Answer key: eight at-risk deals ($1.145M of $2.79M), Answer key self-check: hand labels must reproduce each deal's intended verdict, main(), The ledger: 20 open deals, 73 events, every label written by hand. Events…, Deals with events as dicts, labels split out from what a model sees., rows(), main() (+4 more)

## Knowledge Gaps
- **7 isolated node(s):** `Route accuracy (the end-to-end workflow metric)`, `SEGMENTS`, `Risk reason: competitor`, `Risk reason: escalations`, `Risk reason: stalled` (+2 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 55 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **1 thin communities (<3 nodes) omitted from report**: run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `assess()` connect `Week 02 Findings and Design Rules` to `Repo Setup and MCP Check`, `Week 02 Harness and Setups`, `Week 02 Ledger and Answer Key`?**
  _High betweenness centrality (0.106) - this node is a cross-community bridge._
- **Why does `build_questions()` connect `Shared Specs and Benchmark Rules` to `Repo Setup and MCP Check`, `Week 01 Claude Runs and Fairness`, `Jev Model, Cost and Results`?**
  _High betweenness centrality (0.104) - this node is a cross-community bridge._
- **Why does `triage_lead()` connect `Repo Setup and MCP Check` to `Shared Specs and Benchmark Rules`, `Week 01 Claude Runs and Fairness`, `Jev Model, Cost and Results`?**
  _High betweenness centrality (0.104) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `assess()` (e.g. with `House rule: keep arithmetic out of prompts` and `Week 02 rule thresholds ($100K exec rule, 30 days, 7 days to close)`) actually correct?**
  _`assess()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `build_questions()` (e.g. with `build_system_prompt()` and `JevRunner`) actually correct?**
  _`build_questions()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `triage_lead()` (e.g. with `ask()` and `Jev's half-level intent optimism bias`) actually correct?**
  _`triage_lead()` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Route accuracy (the end-to-end workflow metric)`, `SEGMENTS`, `Risk reason: competitor` to the rest of the system?**
  _7 weakly-connected nodes found - possible documentation gaps or missing edges._