# Graph Report - victoria  (2026-09-22)

## Corpus Check
- Corpus is ~12,187 words - fits in a single context window. You may not need a graph.

## Summary
- 141 nodes · 259 edges · 9 communities (8 shown, 1 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 39 edges (avg confidence: 0.92)
- Token cost: 118,480 input · 0 output

## Community Hubs (Navigation)
- Scoring, Metrics and Routing
- Claude Runner and Split Ablation
- Benchmark Fairness Corrections
- Triage Rubric and Typed Questions
- Jev API Client
- Dataset and Benchmark Harness
- Step 6 Email Generation
- Results and Caveats
- Segment Enum

## God Nodes (most connected - your core abstractions)
1. `ClaudeRunner` - 15 edges
2. `build_questions()` - 13 edges
3. `input_cost()` - 12 edges
4. `score_file()` - 12 edges
5. `route()` - 12 edges
6. `main()` - 11 edges
7. `JevRunner` - 10 edges
8. `ClaudeSplitRunner` - 10 edges
9. `run_one()` - 9 edges
10. `QUESTIONS (shared typed question definitions)` - 9 edges

## Surprising Connections (you probably didn't know these)
- `House rule: publish the failures` --conceptually_related_to--> `results.json (scored benchmark output)`  [INFERRED]
  README.md → week-01-lead-triage/results/results.json
- `Jev typed decision model` --references--> `USD_PER_INPUT_TOKEN ($42 per billion, input only)`  [INFERRED]
  README.md → week-01-lead-triage/src/jev_runner.py
- `House rule: both sides get the same words` --rationale_for--> `QUESTIONS (shared typed question definitions)`  [EXTRACTED]
  README.md → week-01-lead-triage/src/spec.py
- `Sample-size caveat (60 leads, one laptop, one afternoon)` --rationale_for--> `results.json (scored benchmark output)`  [INFERRED]
  README.md → week-01-lead-triage/results/results.json
- `Jev's half-level intent optimism bias` --semantically_similar_to--> `Correlated-error hypothesis (Haiku conflates disqualify and icp_fit)`  [INFERRED] [semantically similar]
  week-01-lead-triage/README.md → week-01-lead-triage/src/split_runner.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Four typed judgments feed the deterministic routing rule** — src_spec_disqualify_question, src_spec_icp_fit_question, src_spec_segment_question, src_spec_intent_question, week_01_lead_triage_src_spec_route [EXTRACTED 1.00]
- **Benchmark fairness corrections applied before publishing** — week_01_lead_triage_readme_thinking_disabled_correction, week_01_lead_triage_readme_prompt_cache_pricing_correction, week_01_lead_triage_readme_cli_overhead_calibration_correction, readme_fix_the_unfair_thing, readme_measure_the_network [EXTRACTED 1.00]
- **Benchmark run pipeline: build, run, ablate, write, score** — week_01_lead_triage_src_build_dataset_main, week_01_lead_triage_src_bench_main, week_01_lead_triage_src_split_runner_main, week_01_lead_triage_src_step6_email_main, week_01_lead_triage_src_score_main, results_results [EXTRACTED 1.00]

## Communities (9 total, 1 thin omitted)

### Community 0 - "Scoring, Metrics and Routing"
Cohesion: 0.10
Nodes (26): Path, Result record: jev, _intent_label() score-to-level mapping, noul probability with a 0.5 decision threshold, JevRunner.run(), Business error metric: funded buyers binned, Business error metric: disqualified leads leaked, Route accuracy (the end-to-end workflow metric) (+18 more)

### Community 1 - "Claude Runner and Split Ablation"
Cohesion: 0.14
Nodes (18): build_system_prompt(), build_user_prompt(), ClaudeRunner, _coerce(), _parse_json(), Claude side of the benchmark. The rubric text is generated from spec.QUESTIONS,…, Measures the input tokens the CLI adds on top of our own prompt. Sends an empty…, Claude was told to return bare JSON. Tolerate a fence anyway. (+10 more)

### Community 2 - "Benchmark Fairness Corrections"
Cohesion: 0.18
Nodes (18): House rule: fix the unfair thing even when it helps the other side, House rules for the benchmarks, House rule: measure the network, not just the model, House rule: publish the failures, House rule: both sides get the same words, _coerce() near-miss label normaliser, ClaudeRunner._invoke() CLI subprocess call, _parse_json() fence-tolerant parser (+10 more)

### Community 3 - "Triage Rubric and Typed Questions"
Cohesion: 0.17
Nodes (16): Jev Playground (weekly benchmark repo), Typed judgment: disqualify (noul / probability), Typed judgment: icp_fit (noul / probability), Typed judgment: intent (score over an ordered ladder), PRODUCT_CONTEXT, QUESTIONS (shared typed question definitions), Typed judgment: segment (choice), Correlated-error hypothesis (Haiku conflates disqualify and icp_fit) (+8 more)

### Community 4 - "Jev API Client"
Cohesion: 0.15
Nodes (10): Jev typed decision model, TypeSafe AI (Jev vendor), USD_PER_INPUT_TOKEN ($42 per billion, input only), build_state(), _intent_label(), JevRunner, Jev side of the benchmark. One HTTP request per lead carrying all four typed…, Jev returns a continuous score plus a legend. Round to the nearest level. (+2 more)

### Community 5 - "Dataset and Benchmark Harness"
Cohesion: 0.17
Nodes (13): House rule: the answer key is written by hand, RUNNERS registry, Sequential runs preserve latency validity, LEADS (60 hand-labelled lead records), Deliberately awkward lead set, 60-lead label distribution, Lead triage rubric and answer key, load_leads() (+5 more)

### Community 6 - "Step 6 Email Generation"
Cohesion: 0.24
Nodes (10): House rule: say where the other thing wins, Jev has no text primitive (HTTP 400), Emails written only for ae_now and sdr_sequence leads, SYSTEM email-writing prompt, CLI environment leak in generated emails, Step 6: write the first-touch email, main(), prove_jev_cannot_write() (+2 more)

### Community 7 - "Results and Caveats"
Cohesion: 0.25
Nodes (8): Sample-size caveat (60 leads, one laptop, one afternoon), results.json (scored benchmark output), Result record: claude-haiku-4-5, Result record: claude-haiku-4-5-split, Result record: claude-sonnet-5, End-to-end cost per 1,000 inbound leads, Do not read the partial run, Split-call ablation (one Claude call per question)

## Knowledge Gaps
- **7 isolated node(s):** `TypeSafe AI (Jev vendor)`, `Rubric: segment rule`, `Rubric: intent rule`, `60-lead label distribution`, `PRODUCT_CONTEXT` (+2 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 40 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `route()` connect `Scoring, Metrics and Routing` to `Claude Runner and Split Ablation`, `Triage Rubric and Typed Questions`, `Dataset and Benchmark Harness`, `Step 6 Email Generation`?**
  _High betweenness centrality (0.182) - this node is a cross-community bridge._
- **Why does `ClaudeRunner` connect `Claude Runner and Split Ablation` to `Dataset and Benchmark Harness`, `Step 6 Email Generation`, `Results and Caveats`?**
  _High betweenness centrality (0.135) - this node is a cross-community bridge._
- **Why does `JevRunner` connect `Jev API Client` to `Scoring, Metrics and Routing`, `Triage Rubric and Typed Questions`, `Dataset and Benchmark Harness`?**
  _High betweenness centrality (0.127) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `ClaudeRunner` (e.g. with `Result record: claude-haiku-4-5` and `Result record: claude-sonnet-5`) actually correct?**
  _`ClaudeRunner` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `score_file()` (e.g. with `ClaudeRunner.run()` and `JevRunner.run()`) actually correct?**
  _`score_file()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `TypeSafe AI (Jev vendor)`, `Rubric: segment rule`, `Rubric: intent rule` to the rest of the system?**
  _7 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Scoring, Metrics and Routing` be split into smaller, more focused modules?**
  _Cohesion score 0.10317460317460317 - nodes in this community are weakly interconnected._