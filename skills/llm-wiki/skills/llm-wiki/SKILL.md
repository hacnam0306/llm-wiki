---
name: llm-wiki
description: Bootstrap or operate a Karpathy-style LLM-maintained personal knowledge base. Scaffolds folder structure, hooks, scripts, and AGENTS.md from bundled templates. Operations: setup (new project), compile (raw→wiki), query (ask questions), lint (health check), ingest (specific file), status (KB stats).
author: Victor Nam Hac 
---

# llm-wiki — LLM Knowledge Base Skill

You are running the `llm-wiki` skill. This implements **Andrej Karpathy's LLM Wiki pattern** — an LLM-maintained knowledge base where raw sources are compiled into a persistent, interlinked wiki of markdown files.

**IMPORTANT:** At skill load time, Claude Code prints `Base directory for this skill: /path/to/skill`.
Extract that path and set it as `SKILL_DIR` before running any scaffold commands.
All bundled files (scripts, hooks, templates) live inside `$SKILL_DIR`.

**Bundled layout:**
```
$SKILL_DIR/
├── SKILL.md
├── scripts/              ← compile.py, query.py, lint.py, flush.py, config.py, utils.py, setup_hooks.py
│   └── hooks/            ← session-start.py, session-end.py, pre-compact.py
├── references/
│   └── AGENTS.md         ← schema / compiler specification
└── assets/
    ├── pyproject.toml    ← dependency template
    └── settings-hooks.json ← Claude hooks config template (points to project hooks/)
```

**Target project layout after setup:**
```
<project>/
├── AGENTS.md                     ← copied from $SKILL_DIR/references/AGENTS.md
├── pyproject.toml
├── .claude/settings.local.json   ← hooks point to project hooks/ (NOT skill dir)
├── scripts/                      ← copied from $SKILL_DIR/scripts/
├── hooks/                        ← copied from $SKILL_DIR/scripts/hooks/
├── knowledge/
│   ├── index.md
│   ├── log.md
│   ├── concepts/
│   ├── connections/
│   └── qa/
├── raw/articles/                 ← drop sources here
├── daily/                        ← conversation logs
└── reports/                      ← lint output
```

**Why project-owned hooks and scripts:**
- Hooks use `Path(__file__).resolve().parent.parent` to find the project root
- This only resolves correctly when the hook lives in `<project>/hooks/` (one level below root)
- Running hooks from the skill dir would compute the wrong root and fail silently
- Scripts in `<project>/scripts/` are project-owned — edit them without touching the skill

---

## BEFORE YOU BEGIN

**Step 1 — Capture SKILL_DIR**

The skill load message shows: `Base directory for this skill: /some/path`
Set that as `SKILL_DIR` for all subsequent commands.

**Step 2 — Detect the operation** from the arguments:

| Argument | Operation |
|----------|-----------|
| `setup` or no args in new dir | Scaffold new LLM Wiki project |
| `compile` | Compile raw/daily sources → knowledge articles |
| `compile --file <path>` | Compile one specific source file |
| `compile --all` | Force recompile everything |
| `query "<question>"` | Query the knowledge base |
| `query "<question>" --file-back` | Query + file answer back into KB |
| `lint` | Run all 7 health checks |
| `lint --structural-only` | Structural checks only (free) |
| `ingest <file>` | Ingest a raw article from raw/articles/ |
| `status` | KB stats: article counts, costs, log |

Create tasks for the detected operations, then proceed to the relevant STATE.

---

## STATE 0: DETECT CONTEXT

```bash
ls knowledge/ 2>/dev/null && echo "HAS_KB" || echo "NO_KB"
ls scripts/   2>/dev/null && echo "HAS_SCRIPTS" || echo "NO_SCRIPTS"
ls AGENTS.md  2>/dev/null && echo "HAS_AGENTS" || echo "NO_AGENTS"
```

- `knowledge/` + `AGENTS.md` both exist → **existing wiki**, go to the requested operation STATE
- Neither exists → **new project**, go to STATE 1: SCAFFOLD
- Partial → **incomplete**, go to STATE 1 to fill gaps only

---

## STATE 1: SCAFFOLD

**Mark task in_progress.**

### Step 1 — Confirm SKILL_DIR

```bash
echo "SKILL_DIR: $SKILL_DIR"
ls "$SKILL_DIR/scripts/"
ls "$SKILL_DIR/hooks/"
ls "$SKILL_DIR/templates/"
```

If any listing fails, STOP and tell the user: "Could not find bundled files in $SKILL_DIR — please check the skill installation."

### Step 2 — Create directory structure

```bash
mkdir -p knowledge/concepts knowledge/connections knowledge/qa
mkdir -p raw/articles raw/assets
mkdir -p daily reports hooks scripts
mkdir -p .claude
```

### Step 3 — Copy scripts

```bash
cp "$SKILL_DIR/scripts/compile.py"     scripts/compile.py
cp "$SKILL_DIR/scripts/query.py"       scripts/query.py
cp "$SKILL_DIR/scripts/lint.py"        scripts/lint.py
cp "$SKILL_DIR/scripts/flush.py"       scripts/flush.py
cp "$SKILL_DIR/scripts/config.py"      scripts/config.py
cp "$SKILL_DIR/scripts/utils.py"       scripts/utils.py
cp "$SKILL_DIR/scripts/setup_hooks.py" scripts/setup_hooks.py
```

### Step 4 — Copy hooks

```bash
cp "$SKILL_DIR/scripts/hooks/session-start.py" hooks/session-start.py
cp "$SKILL_DIR/scripts/hooks/session-end.py"   hooks/session-end.py
cp "$SKILL_DIR/scripts/hooks/pre-compact.py"   hooks/pre-compact.py
```

### Step 5 — Copy assets (templates)

```bash
cp "$SKILL_DIR/references/AGENTS.md"      AGENTS.md
cp "$SKILL_DIR/assets/pyproject.toml"     pyproject.toml
```

### Step 6 — Create knowledge/index.md and log.md

Write `knowledge/index.md`:
```markdown
# Knowledge Base Index

| Article | Summary | Compiled From | Updated |
|---------|---------|---------------|---------|
```

Write `knowledge/log.md`:
```markdown
# Build Log

<!-- Append-only. Format: ## [ISO-TIMESTAMP] operation | description -->
```

### Step 7 — Wire hooks in .claude/settings.local.json

Run the bundled setup script — it safely merges the three llm-wiki hooks into
`.claude/settings.local.json` without touching any other keys:

```bash
uv run python scripts/setup_hooks.py
```

Expected output:
```
Installed llm-wiki hooks in .claude/settings.local.json
  SessionStart  → hooks/session-start.py
  PreCompact    → hooks/pre-compact.py
  SessionEnd    → hooks/session-end.py

Restart Claude Code to activate the hooks.
```

To uninstall hooks later: `uv run python scripts/setup_hooks.py --remove`

**Why a script instead of manual editing:** The script handles the JSON merge
correctly, strips stale skill-dir paths from previous installs, and is idempotent
(safe to run multiple times).

### Step 8 — Add .gitignore entries

Append to `.gitignore` (or create it):
```
# LLM Wiki runtime state
scripts/state.json
scripts/last-flush.json
scripts/*.log
reports/
__pycache__/
*.pyc
.env
```

### Step 9 — Verify

```bash
uv run python scripts/config.py && echo "Scripts OK"
```

If `uv` is not found:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Report what was created and next steps:
1. Drop sources into `raw/articles/` (markdown, Obsidian clips)
2. Or write conversation logs to `daily/YYYY-MM-DD.md`
3. Run `/llm-wiki compile` to build the knowledge base
4. Run `/llm-wiki query "your question"` to search it

**Mark task completed.**

---

## STATE 2: COMPILE

**Mark task in_progress.**

### Step 1 — Check what needs compiling

```bash
uv run python scripts/compile.py --dry-run
```

Then run the appropriate command:

```bash
# Specific file:
uv run python scripts/compile.py --file <path>

# Force all:
uv run python scripts/compile.py --all

# Incremental (default — skips unchanged):
uv run python scripts/compile.py
```

**Note:** The default compile scans both `daily/*.md` and all `raw/**/*.md` recursively. Use `--file` only when you want to target one specific file.

### Step 2 — Handle errors

`ModuleNotFoundError: claude_agent_sdk` → run `uv add claude-agent-sdk` first.

### Step 3 — Report results

```bash
echo "concepts: $(ls knowledge/concepts/ 2>/dev/null | wc -l)"
echo "connections: $(ls knowledge/connections/ 2>/dev/null | wc -l)"
echo "qa: $(ls knowledge/qa/ 2>/dev/null | wc -l)"
cat knowledge/index.md
```

Show the user how many articles were created and the updated index.

**Mark task completed.**

---

## STATE 3: QUERY

**Mark task in_progress.**

Index-guided retrieval — no RAG, no embeddings. The LLM reads the index and selects relevant articles.

```bash
# Without filing back:
uv run python scripts/query.py "<question>"

# With --file-back (saves answer as knowledge/qa/article.md):
uv run python scripts/query.py "<question>" --file-back
```

Display the full answer. If `--file-back`, show the path of the filed article.

**Scale note:** Under ~500 articles, index-guided retrieval outperforms vector search. Over ~2000 articles, consider adding `qmd` (hybrid BM25+vector).

**Mark task completed.**

---

## STATE 4: LINT

**Mark task in_progress.**

### 7 health checks

| Check | Type | Detects |
|-------|------|---------|
| Broken links | Structural | `[[wikilinks]]` to non-existent articles |
| Orphan pages | Structural | Articles with zero inbound links |
| Orphan sources | Structural | Source files not yet compiled |
| Stale articles | Structural | Source changed since last compile |
| Missing backlinks | Structural | A→B but B doesn't link back to A |
| Sparse articles | Structural | Under 200 words |
| Contradictions | LLM | Conflicting claims across articles |

```bash
# All checks (~$0.15-0.25):
uv run python scripts/lint.py

# Structural only (free):
uv run python scripts/lint.py --structural-only
```

Read and summarize the report:
```bash
cat reports/lint-$(date +%Y-%m-%d).md
```

Group by severity: **error** → fix now, **warning** → fix soon, **suggestion** → consider.

**Mark task completed.**

---

## STATE 5: INGEST

**Mark task in_progress.**

Shorthand for `compile --file raw/articles/<name>.md`.

```bash
ls raw/articles/
uv run python scripts/compile.py --file raw/articles/<filename>.md
```

After compile, show the new concept articles:
```bash
ls -lt knowledge/concepts/ | head -5
```

**Mark task completed.**

---

## STATE 6: STATUS

```bash
echo "=== Knowledge Base Status ==="
echo "Articles:"
echo "  concepts/:    $(ls knowledge/concepts/ 2>/dev/null | wc -l)"
echo "  connections/: $(ls knowledge/connections/ 2>/dev/null | wc -l)"
echo "  qa/:          $(ls knowledge/qa/ 2>/dev/null | wc -l)"
echo ""
echo "Sources:"
echo "  raw/articles/: $(ls raw/articles/ 2>/dev/null | wc -l)"
echo "  daily/:        $(ls daily/ 2>/dev/null | wc -l)"
echo ""
echo "Index (last 20 lines):"
tail -20 knowledge/index.md 2>/dev/null || echo "(empty)"
echo ""
echo "Build log (last 5 entries):"
grep "^## \[" knowledge/log.md 2>/dev/null | tail -5 || echo "(empty)"
echo ""
echo "State:"
python3 -c "
import json, sys
try:
    s = json.load(open('scripts/state.json'))
    print(f'  Total cost:    \${s.get(\"total_cost\", 0):.2f}')
    print(f'  Queries run:   {s.get(\"query_count\", 0)}')
    print(f'  Last lint:     {s.get(\"last_lint\", \"never\")}')
    print(f'  Compiled logs: {len(s.get(\"ingested\", {}))}')
except: print('  (state.json not found)')
"
```

---

## Key Design Principles

1. **Raw sources are immutable** — never modify `raw/` or `daily/`. LLM reads, never writes.
2. **The wiki is LLM-owned** — `knowledge/` belongs to the compiler. Humans read, LLM writes.
3. **Index-guided retrieval** — at <500 articles, a structured index beats cosine similarity.
4. **Compounding answers** — `--file-back` turns every query into a permanent wiki article.
5. **Hooks = automatic capture** — `session-end.py` and `pre-compact.py` capture long sessions; `session-start.py` injects the index at startup.
6. **The wiki is a git repo** — commit `knowledge/` for version history and diffs.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: claude_agent_sdk` | `uv add claude-agent-sdk` |
| `uv: command not found` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Hook not firing | Restart Claude Code; check `.claude/settings.local.json` has `SessionStart` |
| compile.py finds nothing | Use `--file` for `raw/articles/`; default scans `daily/` only |
| Empty knowledge after compile | Check `scripts/compile.log` for API errors |
| Index too large for context | >500 articles — add `qmd` search layer |
