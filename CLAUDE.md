# Working in this repo

## Code

Run `/Users/deepdave/.local/bin/graphify-repo sync .` at the start of work
and after validation. Query the checkout's graph before tracing code:

```bash
graphify query "how is the Claude side kept fair?"
graphify path "JevRunner" "route"
```

Verify the returned paths against source. Keep `graphify-out/` local and
untracked.

## Benchmarks

- Trace published numbers to committed runs in `results/raw/`. Change a
  result by rerunning and rescoring, never by editing its table.
- Give models the same evidence and rubric. Record fixes that affect a
  comparison, including cost, timing and token accounting.
- Keep thresholds, date arithmetic and counts in code.
- MCP tools load each week's `spec.py`. Rerun the affected benchmark when
  a prompt changes. `uv run mcp-server/check.py` checks the live tools.

## Writing and commits

Keep the root README short. Include setup, results and limits where needed;
cut repeated conclusions, promotional claims and development diaries.
Preserve measured prompts and raw model responses when editing prose.

Enable the punctuation check with `git config core.hooksPath .githooks`.
Use the user's git identity. Do not add co-author or generated-by trailers.

Keep API keys in the gitignored `.env.local`; `.env.example` contains names
and empty values only.
