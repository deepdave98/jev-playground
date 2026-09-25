# Working in this repo

## Use the graph before reading files

There is a graphify knowledge graph in `graphify-out/`. Query it before
opening files. It is there so you do not burn a context window rediscovering
how the benchmark fits together.

```bash
graphify query "how is the Claude side kept fair?"
graphify path "JevRunner" "route"
graphify explain "input_cost"
```

Answers come back with `file:line`, so go straight to the line the graph
gives you rather than reading the file from the top. `graphify-out/GRAPH_REPORT.md`
has the community map and the most connected nodes.

After changing code, refresh it:

```bash
graphify update
python3 .githooks/pre-commit --fix graphify-out/GRAPH_REPORT.md graphify-out/graph.html
```

The second line is not optional. graphify's report and HTML templates write
em dashes into every regenerated graph, and the first push of this repo
shipped eight of them that way.

## House rules

The repo is a set of benchmarks. Two rules matter more than the code.

**Numbers in a README must come from a committed run in `results/raw/`.**
Never hand-edit a results table. If a number changes, re-run and re-score.

**When you find something that makes one side look unfairly bad, fix it and
write down that you fixed it.** Week 01 has three of these in its README.
That section is the reason to trust the rest of the file.

**Keep arithmetic out of prompts.** Thresholds, date windows and counts go in
code. Week 02 measured what happens otherwise: the same model scored 100%
when code applied the rule and 70% when it applied the rule itself.

## The MCP server

`mcp-server/jev_server.py` loads its questions from each week's `spec.py`, so
changing a prompt changes the tool. Re-run that week's benchmark afterwards
or the README numbers stop describing the tool. `uv run mcp-server/check.py`
starts it and calls every tool against the live API.

## Writing

Plain English, the way an engineer writes notes for another engineer.

`.githooks/pre-commit` refuses any commit with an em or en dash in a staged
file. Turn it on once per clone with `git config core.hooksPath .githooks`.

No em dashes. No "it is not X, it is Y". No "unlock", "leverage", "seamless",
"robust", "comprehensive", "game changer", "dive in". No section that exists
only to restate the section above it. Short sentences are fine. Say the
number, say what it means, move on.

## Secrets

`TYPESAFE_API_KEY` lives in `.env.local`, which is gitignored. It has never
been committed and must not be. `.env.example` documents the shape.
