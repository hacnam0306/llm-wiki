# llm-wiki

An LLM-maintained personal knowledge base, inspired by [Andrej Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f). You drop raw sources (articles, conversation logs) into the project; Claude compiles them into a structured, interlinked wiki of markdown files.

## How it works

```
raw/articles/   →  LLM compiler  →  knowledge/concepts/
daily/logs/     →               →  knowledge/connections/
                                →  knowledge/qa/
```

- **Raw sources are immutable** — you write to `raw/` and `daily/`, the LLM writes to `knowledge/`
- **Index-guided retrieval** — no embeddings or vector DB needed under ~500 articles
- **Hooks = automatic capture** — session hooks snapshot long conversations before context compression

## Installation

```bash
# Add this marketplace
/plugin marketplace add hacnam0306/llm-wiki

# Install the plugin
/plugin install llm-wiki@llm-wiki
```

## Usage (via Claude Code)

Invoke with the `llm-wiki` skill:

```
/llm-wiki setup              # Scaffold a new project
/llm-wiki compile            # Compile raw + daily sources → wiki (incremental)
/llm-wiki compile --all      # Force recompile everything
/llm-wiki compile --file <p> # Compile one specific file
/llm-wiki query "question"   # Ask the knowledge base a question
/llm-wiki query "q" --file-back  # Query + file the answer back into the KB
/llm-wiki ingest <file>      # Ingest one raw article
/llm-wiki lint               # Run 7 health checks (~$0.15–0.25)
/llm-wiki lint --structural-only  # Structural checks only (free)
/llm-wiki status             # Show article counts, costs, build log
```

## Project layout (after setup)

```
<project>/
├── AGENTS.md                     ← compiler schema / specification
├── pyproject.toml                ← Python dependencies (uv)
├── .claude/settings.local.json   ← hooks wired to hooks/
├── scripts/                      ← compile.py, query.py, lint.py, etc.
├── hooks/                        ← session-start.py, session-end.py, pre-compact.py
├── knowledge/
│   ├── index.md                  ← article index (injected at session start)
│   ├── log.md                    ← append-only build log
│   ├── concepts/                 ← core concept articles
│   ├── connections/              ← cross-concept relationship articles
│   └── qa/                       ← filed Q&A answers (from --file-back)
├── raw/articles/                 ← drop sources here (markdown, Obsidian clips)
├── daily/                        ← conversation logs (YYYY-MM-DD.md)
└── reports/                      ← lint output
```

## Lint checks

| Check | Cost | Detects |
|-------|------|---------|
| Broken links | Free | `[[wikilinks]]` pointing to missing articles |
| Orphan pages | Free | Articles with zero inbound links |
| Orphan sources | Free | Source files not yet compiled |
| Stale articles | Free | Source changed since last compile |
| Missing backlinks | Free | A→B exists but B doesn't link back to A |
| Sparse articles | Free | Articles under 200 words |
| Contradictions | ~$0.20 | Conflicting claims across articles |

## Requirements

- [uv](https://docs.astral.sh/uv/) — Python package manager
- Claude API key (set as `ANTHROPIC_API_KEY`)

Install uv if missing:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: claude_agent_sdk` | `uv add claude-agent-sdk` |
| `uv: command not found` | Install uv (see above) |
| Hook not firing | Restart Claude Code; check `.claude/settings.local.json` |
| compile finds nothing | Use `--file` for `raw/articles/`; default scans `daily/` |
| Empty knowledge after compile | Check `scripts/compile.log` for API errors |
| Index too large for context | >500 articles — consider adding a search layer |

## Skill layout

```
skills/llm-wiki/
├── SKILL.md                  ← skill instructions (loaded by Claude Code)
├── README.md                 ← this file
├── scripts/
│   ├── compile.py            ← incremental source → wiki compiler
│   ├── query.py              ← index-guided question answering
│   ├── lint.py               ← 7 health checks
│   ├── flush.py              ← flush session logs
│   ├── config.py             ← project config
│   ├── utils.py              ← shared utilities
│   ├── setup_hooks.py        ← idempotent hook installer
│   └── hooks/
│       ├── session-start.py  ← injects index at session start
│       ├── session-end.py    ← captures session log on exit
│       └── pre-compact.py    ← snapshots context before compression
├── references/
│   └── AGENTS.md             ← compiler specification / schema
└── assets/
    ├── pyproject.toml        ← dependency template
    └── settings-hooks.json   ← hooks config template
```
