# Repository Guidelines

## Project Overview

Claude Code plugin `nexpresso-connect` (0.1.0) that drives the external **Nexpresso** headless CMS through *that CMS's own MCP server* (`posts_*`, `projects_*`, `reviews_*`, `faqs_*`, `categories_*`, `tags_*`, `media_*`, `settings_*`, `users_*`).

This repo ships **no application code**: a skill (instructions), one `PreToolUse` hook (Python, stdlib only), two JSON manifests, a README. 8 tracked files, ~435 lines.

Two product rules it exists to enforce:

1. Nothing is published without review — content is always created `status: "draft"`, then reviewed, then approved by the user.
2. The user is always asked "keep as draft" vs "publish now" (`AskUserQuestion`); never publish by default.

The plugin bundles **no MCP config**. It assumes a Nexpresso MCP server already wired user-side.

## Architecture & Data Flow

Two independent layers of defense — prompt-side (persuasion) and hook-side (determinism):

| Layer | File | Nature |
|---|---|---|
| Perimeter | `hooks/hooks.json:6` | unanchored **JavaScript** regex on the full tool name; decides whether a process is spawned at all |
| Policy | `hooks/publish-gate.py` | pure `gate(event)` + I/O-only `main()`; decides `ask` vs silence |
| Instructions | `skills/nexpresso/SKILL.md` | always-loaded rules, access gate, 7-step cycle, 8-row checklist |
| Detail | `skills/nexpresso/reference.md` | on-demand field catalogue, kept out of always-on context |

Flow:

```
tool intent → matcher regex vs "mcp__<server>__<tool>"
  → no match: nothing happens (reads cost zero spawns)
  → match: spawn `python3 ${CLAUDE_PLUGIN_ROOT}/hooks/publish-gate.py`, event JSON on stdin
      → gate() → {"hookSpecificOutput":{…,"permissionDecision":"ask",…}} on stdout → [Plugin] permission prompt, even in auto mode
      → gate() → None → no stdout → normal permission flow, call proceeds
```

`gate()` asks in exactly two cases: tool name ends `_delete`, or `tool_input.status == "published"`. Everything else is silent. **`gate()` does no server-name check** — the matcher alone encodes "this is Nexpresso" and "this is a write".

Design is **fail-open everywhere**: bad JSON, non-dict event, non-dict `tool_input` → exit 0, no output. A crashed gate must never block legitimate drafting. Cost of that choice: a mis-cased or renamed server key makes the guard vanish silently.

`SKILL.md` inverts the relationship deliberately: if the hook's prompt appears without the agent having asked first, that is evidence the prompt-side rule was broken.

## Key Directories

| Path | Purpose |
|---|---|
| `.claude-plugin/` | `plugin.json` + `marketplace.json`; the only manifests |
| `hooks/` | the deterministic gate: manifest, script, its test |
| `skills/nexpresso/` | `SKILL.md` (always loaded) + `reference.md` (loaded on demand) |

No `src/`, no build output, no vendored deps.

## Development Commands

```bash
python3 hooks/test_publish_gate.py                    # the only test suite → prints "ok"
claude plugin validate .                              # marketplace.json
claude plugin validate .claude-plugin/plugin.json     # plugin manifest
claude plugin details nexpresso-connect               # component inventory + token cost

# single-case probes against the gate
echo '{"tool_name":"mcp__nexpresso__posts_update","tool_input":{"id":"abc","status":"published"}}' | python3 hooks/publish-gate.py   # → JSON, "permissionDecision": "ask"
echo '{"tool_name":"mcp__nexpresso__posts_create","tool_input":{"title":"x","status":"draft"}}'    | python3 hooks/publish-gate.py   # → no output

# release: tag must match both manifests
claude plugin tag .                                   # creates nexpresso-connect--v<version>
git push origin refs/tags/nexpresso-connect--v0.1.0
```

No build, no lint, no formatter, no CI. `pytest.ini`, `pyproject.toml`, `tox.ini`, `setup.cfg`, `Makefile`, `package.json`, `.github/` are all **absent** by design — do not add one without a manifest to back it.

## Code Conventions & Common Patterns

**Python (`hooks/`)**

- Stdlib only (`json`, `sys`, `subprocess`, `pathlib`). No dependency manifest exists, so anything else is uninstallable. Do not import `re` to "improve" matching.
- Target `python3` 3.9 syntax: f-strings, no walrus, no `match`, no builtin generics, no annotations. Nested quotes inside f-strings must differ in type (`f"…{args.get('id', '?')}…"`).
- Decision logic stays pure in `gate(event)`; `main()` owns stdin/stdout exclusively. That split is what makes the hook subprocess-testable.
- Silence = `gate()` returns `None` and `main()` writes nothing. Never an empty JSON object, never `permissionDecision: "allow"`. Never `"deny"` — `ask` is what lets the user consciously approve.
- Every unexpected path returns `None`/`0`. `except ValueError` (not `json.JSONDecodeError`, which subclasses it) also swallows empty stdin.
- Label extraction is one `or` chain, most specific → most generic: `title` → `question` → `author_name` → `id` → `"?"`. Extend by inserting a rung, never by adding a second `if`.
- Reason strings: French, adjacent-string concatenation (no `+`, no `\`), and always name operation + object + consequence ("Refuser laisse le contenu en brouillon."). Keep `ensure_ascii=False` so accents reach the prompt.
- Black-style by hand: double quotes, trailing commas, two blank lines between top-level defs.

**Markdown (`skills/`, `README.md`)**

- Everything is **French**, with French typography: « guillemets », narrow no-break space before `:` and `;`, U+2019 apostrophes, `≤` for limits, `—` for dashes.
- Compact Markdown tables for every enumerable list (`| Champ | Contrainte |`, `| Étape | Action |`). Backticked identifiers. Bold on the single load-bearing token per line.
- Every prohibition carries its rationale inline.
- Cross-file duplication is intentional (no-bypass bans, OAuth-scope rule, media-id rule appear 2–3×) so each file is correct read alone — edit all occurrences together.
- `SKILL.md` frontmatter has exactly `name` + a folded `>` `description`. That description **is** the activation mechanism: product name, tool families, quoted French trigger utterances, the two rules, and a `Ne pas utiliser pour …` boundary. Rewording it changes when the skill fires.
- Reference paths inside the skill use `${CLAUDE_PLUGIN_ROOT}/skills/nexpresso/reference.md`, never relative.

**CMS-domain rules encoded in the docs** (get these wrong and content breaks): `content` is **HTML** (TipTap stores `editor.getHTML()`; markdown renders literally) · `status` ∈ `draft|published|archived`, default `draft` · `published_at` auto-fills on promotion · `*_update` is a **PATCH** — omitted field untouched, empty field overwrites · `cover_image`/`site_logo`/`site_favicon`/`author_avatar` are **media record ids**, never URLs · `categories`/`tags` accept ids/slugs/names with auto-creation in a single `*_create` · FAQs have no `status` · `users_*` is read-only.

## Important Files

| File | Why it matters |
|---|---|
| `hooks/hooks.json:6` | the matcher — the entire perimeter, in one regex line |
| `hooks/publish-gate.py` | `_ask` (sole output shape), `gate()` (policy), `main()` (all I/O) |
| `hooks/test_publish_gate.py` | the only runnable proof; `print("ok")` must stay the last line |
| `.claude-plugin/plugin.json` | `name`, `version`, `description`, `author`, 7 `keywords` |
| `.claude-plugin/marketplace.json` | marketplace `banan-nexpresso`, `plugins[0].source: "./"` |
| `README.md:29` | `### Contrainte de nommage` — the only place the server-key constraint is documented; its regex is a hand copy of `hooks.json:6` with nothing keeping them in sync |

Manifest invariant: `plugin.json.version` and `marketplace.json.plugins[0].version` move in **lockstep** (`claude plugin tag` validates it). Marketplace name is `banan-nexpresso`, deliberately distinct from the already-registered `banan-agency` (which ships `exocortex`).

## Runtime/Tooling Preferences

- **`python3` only** for the hook — invoked by PATH name from `hooks.json`, script path interpolated from `${CLAUDE_PLUGIN_ROOT}`, so no executable bit and no absolute path are needed. No Node, no Bun, no package manager in this repo. (`bun run mcp:stdio` in the README belongs to the *Nexpresso* repo, not this one.)
- Consumed as-is from the git tree: `/plugin marketplace add Nath-vfx/nexpresso-connect-plugin`, then `/plugin install nexpresso-connect@banan-nexpresso`; `/reload-plugins` when installed mid-session.
- Release tags follow `<plugin-name>--v<version>` (`nexpresso-connect--v0.1.0`), produced by `claude plugin tag`.
- Git: `main`, remote `git@github.com:Nath-vfx/nexpresso-connect-plugin.git` (private, SSH).

## Testing & QA

`hooks/test_publish_gate.py` — no framework: module-level `assert`s, run top to bottom, `print("ok")` as the only success signal. It black-boxes the gate through `subprocess.run([sys.executable, str(GATE)], input=json.dumps(event), …)`, exactly as Claude Code will. `GATE = Path(__file__).with_name("publish-gate.py")` makes it CWD-independent. Subprocess is forced, not chosen: the hyphen in `publish-gate.py` makes it unimportable.

7 cases: publish → `ask` (+ the only reason-string assertion), draft promotion via `posts_update` → `ask`, `media_delete` → `ask`, draft / partial PATCH / empty `settings_update` / malformed event → silence.

Invariants locked in: exit code always 0 (even on a malformed event) · empty stdout means "no decision" · non-empty stdout must parse as JSON · the `hookSpecificOutput.permissionDecision` key path.

Adding a case — bind when you expect a decision, inline when you expect silence, insert before `print("ok")`:

```python
promoted = run({"tool_name": "mcp__nexpresso__faqs_update",
                "tool_input": {"id": "abc123", "status": "published"}})
assert decision(promoted) == "ask", promoted

assert run({"tool_name": "mcp__nexpresso__faqs_update",
            "tool_input": {"id": "abc123", "answer": "…"}}) is None
```

Known gaps: the matcher regex is never tested here (Claude Code evaluates it in JS) · `status: "archived"` unasserted · delete reason string unasserted · `hookEventName` unasserted · the `except ValueError` branch is unreachable from the suite (every payload is `json.dumps`-ed).

## Traps

- **A green suite does not prove the hook fires.** If the user's MCP server key lacks `nexpresso`/`Nexpresso`, the matcher never matches, the gate never runs, publication proceeds with no prompt, no error, no log — and `python3 hooks/test_publish_gate.py` still prints `ok`. Highest false-confidence risk in the repo. Real key observed in the wild: `mcp__claude_ai_Nexpresso_test__posts_create` (matches).
- `[Nn]expresso` covers two spellings only. `NEXPRESSO`, `NexPresso` → guard silently gone. Renaming the MCP server key is an incident: edit `hooks/hooks.json:6` in the same commit.
- **Never widen the matcher.** `mcp__.*` turns this into a global delete-confirmation hook for every MCP server in the session, because `gate()` keys `_delete` on the tool-name suffix alone.
- Deliberately ungated, keep it that way: `*_list`, `*_get`, `users_*`, `media_upload_ticket`. A generic `media_.*` would start prompting on every upload ticket.
- **No stray stdout in `publish-gate.py`.** A debug `print()` breaks 4 of 7 test cases and makes the hook unparseable to Claude Code. Debug goes to `sys.stderr`.
- Never run the suite under `python3 -O`: asserts are stripped, `ok` still prints, nothing is verified.
- `json.load(sys.stdin)` blocks until EOF — anything holding stdin open hangs the hook.
- Renaming `publish-gate.py` breaks two references at once: `GATE` in the test and `args` in `hooks/hooks.json`.
- `settings_create`/`settings_delete` in the matcher alternation are dead branches (the CMS exposes only `settings_get`/`settings_update`) — harmless, not evidence those tools exist.
