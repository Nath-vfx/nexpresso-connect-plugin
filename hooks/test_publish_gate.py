#!/usr/bin/env python3
"""Vérifie le garde-fou : ask sur publication et suppression, silence ailleurs."""
import json
import subprocess
import sys
from pathlib import Path

GATE = Path(__file__).with_name("publish-gate.py")


def run(event):
    proc = subprocess.run(
        [sys.executable, str(GATE)],
        input=json.dumps(event),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout) if proc.stdout.strip() else None


def decision(out):
    return out["hookSpecificOutput"]["permissionDecision"]


published = run(
    {
        "tool_name": "mcp__nexpresso__posts_create",
        "tool_input": {"title": "Essai", "status": "published"},
    }
)
assert decision(published) == "ask", published
assert "Essai" in published["hookSpecificOutput"]["permissionDecisionReason"]

promoted = run(
    {
        "tool_name": "mcp__plugin_nexpresso-connect_nexpresso__posts_update",
        "tool_input": {"id": "abc123", "status": "published"},
    }
)
assert decision(promoted) == "ask", promoted

removed = run(
    {"tool_name": "mcp__nexpresso__media_delete", "tool_input": {"id": "abc123"}}
)
assert decision(removed) == "ask", removed

assert (
    run(
        {
            "tool_name": "mcp__nexpresso__posts_create",
            "tool_input": {"title": "Essai", "status": "draft"},
        }
    )
    is None
)
assert (
    run(
        {
            "tool_name": "mcp__nexpresso__posts_update",
            "tool_input": {"id": "abc123", "excerpt": "corrigé"},
        }
    )
    is None
)
assert run({"tool_name": "mcp__nexpresso__settings_update", "tool_input": {}}) is None
assert run({"pas": "un event"}) is None

print("ok")
