"""
setup_hooks.py — Install llm-wiki hooks into .claude/settings.local.json

Safe merge: preserves all existing keys; only adds/replaces the three
llm-wiki hook entries (SessionStart, PreCompact, SessionEnd).

Usage:
    uv run python scripts/setup_hooks.py
    uv run python scripts/setup_hooks.py --remove   # uninstall hooks
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SETTINGS_FILE = ROOT / ".claude" / "settings.local.json"

# The three hooks this script manages. Keys must match exactly.
LLM_WIKI_HOOKS: dict[str, list[dict]] = {
    "SessionStart": [
        {
            "matcher": "",
            "hooks": [
                {
                    "type": "command",
                    "command": "uv run python hooks/session-start.py",
                    "timeout": 15,
                }
            ],
        }
    ],
    "PreCompact": [
        {
            "matcher": "",
            "hooks": [
                {
                    "type": "command",
                    "command": "uv run python hooks/pre-compact.py",
                    "timeout": 10,
                }
            ],
        }
    ],
    "SessionEnd": [
        {
            "matcher": "",
            "hooks": [
                {
                    "type": "command",
                    "command": "uv run python hooks/session-end.py",
                    "timeout": 10,
                }
            ],
        }
    ],
}

LLM_WIKI_COMMANDS = {
    entry["hooks"][0]["command"]
    for entries in LLM_WIKI_HOOKS.values()
    for entry in entries
}


def load_settings() -> dict:
    if SETTINGS_FILE.exists():
        try:
            return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"ERROR: {SETTINGS_FILE} is not valid JSON: {e}", file=sys.stderr)
            sys.exit(1)
    return {}


def save_settings(settings: dict) -> None:
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")


def install(settings: dict) -> dict:
    """Merge llm-wiki hooks into settings, preserving all other hooks."""
    hooks = settings.get("hooks", {})

    for event, new_entries in LLM_WIKI_HOOKS.items():
        existing = hooks.get(event, [])
        # Remove any stale llm-wiki entries (old skill-dir paths or project paths)
        cleaned = [
            entry
            for entry in existing
            if not any(
                h.get("command", "") in LLM_WIKI_COMMANDS
                or ".claude/skills/llm-wiki" in h.get("command", "")
                for h in entry.get("hooks", [])
            )
        ]
        hooks[event] = cleaned + new_entries

    return {**settings, "hooks": hooks}


def remove(settings: dict) -> dict:
    """Remove all llm-wiki hook entries from settings."""
    hooks = settings.get("hooks", {})

    for event in list(hooks.keys()):
        hooks[event] = [
            entry
            for entry in hooks[event]
            if not any(
                h.get("command", "") in LLM_WIKI_COMMANDS
                or ".claude/skills/llm-wiki" in h.get("command", "")
                for h in entry.get("hooks", [])
            )
        ]
        if not hooks[event]:
            del hooks[event]

    result = {**settings}
    if hooks:
        result["hooks"] = hooks
    else:
        result.pop("hooks", None)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Install or remove llm-wiki hooks")
    parser.add_argument("--remove", action="store_true", help="Uninstall hooks")
    args = parser.parse_args()

    settings = load_settings()

    if args.remove:
        updated = remove(settings)
        save_settings(updated)
        print(f"Removed llm-wiki hooks from {SETTINGS_FILE}")
    else:
        updated = install(settings)
        save_settings(updated)
        print(f"Installed llm-wiki hooks in {SETTINGS_FILE}")
        print("  SessionStart  → hooks/session-start.py")
        print("  PreCompact    → hooks/pre-compact.py")
        print("  SessionEnd    → hooks/session-end.py")
        print()
        print("Restart Claude Code to activate the hooks.")


if __name__ == "__main__":
    main()
