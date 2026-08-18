#!/usr/bin/env python3
"""PreToolUse Nexpresso : impose une confirmation utilisateur avant publication ou suppression.

Silencieux (exit 0, pas de stdout) pour tout le reste : les brouillons et les
corrections passent sans friction.
"""
import json
import sys


def _ask(reason):
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": reason,
        }
    }


def gate(event):
    """Retourne la décision à écrire sur stdout, ou None si le hook n'a rien à dire."""
    name = event.get("tool_name") or ""
    args = event.get("tool_input") or {}
    if not isinstance(args, dict):
        return None
    if name.endswith("_delete"):
        return _ask(
            f"Suppression Nexpresso ({name}, id={args.get('id', '?')}) : "
            "confirmer la suppression définitive."
        )
    if args.get("status") == "published":
        label = (
            args.get("title")
            or args.get("question")
            or args.get("author_name")
            or args.get("id")
            or "?"
        )
        return _ask(
            f"Publication Nexpresso ({name} : {label}) : confirmer la mise en ligne. "
            "Refuser laisse le contenu en brouillon."
        )
    return None


def main():
    try:
        event = json.load(sys.stdin)
    except ValueError:  # JSONDecodeError hérite de ValueError
        return 0
    if not isinstance(event, dict):
        return 0
    decision = gate(event)
    if decision is not None:
        json.dump(decision, sys.stdout, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
