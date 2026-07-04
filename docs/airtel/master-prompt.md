# MASTER PROMPT — Build "Airtel SuperAgent" on an office laptop

> Paste everything between the `=== BEGIN ===` and `=== END ===` markers into whatever
> AI coding agent your office laptop has (Claude Code, Cursor, Copilot, Codex, Gemini, or an
> internal tool). It is self-contained and agent-agnostic. Work through it phase by phase.

---

=== BEGIN MASTER PROMPT ===

## ROLE

You are a senior platform engineer building an internal developer-productivity tool called
**Airtel SuperAgent** from scratch in this repository. It is a local-first governance and
routing layer that sits between any AI coding assistant and the engineer's code. Build it in
small, verifiable increments. After every change, RUN it and show the output — never claim
something works without executing it. Default to plan-before-code for anything touching more
than one file.

## MISSION (what Airtel SuperAgent is)

A single local layer that does five things for every engineer, regardless of which AI tool they use:

1. **Structures intent.** Turns a vague one-line command ("fix the login thing") into a
   structured, rule-bound prompt: goal, constraints, the org rules it must obey, an execution
   plan, and a verification step — *before* any code is written.
2. **Routes.** Classifies the task and selects the right approach/skill chain.
3. **Governs.** Blocks destructive shell actions and scrubs secrets/PII before anything is
   persisted or sent anywhere.
4. **Saves cost.** Tracks token/spend per task and reports what was saved (memory hits, avoided
   retries, cheaper-model routing).
5. **Remembers.** Carries decisions across sessions and across tools via a local memory store.

And it **compiles one source of truth into every tool's native config**, so the same rules apply
whether the engineer is in Cursor, Copilot, Codex, or Claude Code.

## HARD CONSTRAINTS (enterprise / office laptop)

These are non-negotiable. Treat any violation as a build failure.

- **Local-first.** All state lives under `~/.airtel-superagent/`. No telemetry, no phone-home.
- **No admin rights.** Pure user-space. No `sudo`, no system package managers. Use only the
  language runtimes already present (assume Python 3.9+ stdlib and bash/zsh). If you need a
  package, use a project-local venv and document it; never install globally.
- **Offline-tolerant.** Must function with no internet. Any network call (e.g. to an approved
  internal LLM gateway) must be optional, behind a config flag, respect `HTTPS_PROXY`, and
  degrade gracefully when unreachable.
- **Data governance.** Code, prompts, secrets, and PII must never leave the laptop. Scrub
  secrets/PII before writing to memory or logs. Assume telecom-grade sensitivity.
- **Agent-agnostic.** Do not hard-depend on any one assistant's hook system. Core logic is plain
  CLI tools callable from anything. Tool-specific integration is an optional adapter layer.
- **Auditable.** Every meaningful action appends one JSONL line to an audit log suitable for
  later SIEM ingestion (action, timestamp, task hash — never raw code/secrets).
- **Reversible.** Anything destructive (file deletes, git history rewrites) asks first and is logged.

## TECH CHOICES

- Language: **Bash for CLI entrypoints, Python 3 (stdlib only) for logic.** No heavy frameworks.
- Storage: **JSONL files** for logs/patterns; **SQLite (stdlib `sqlite3`) with FTS5** for memory.
- Config: **YAML** for rules (parse with a tiny stdlib-only parser or ship a vendored single-file
  YAML reader — no pip if avoidable).
- Distribution: a single `install.sh` that symlinks CLIs into `~/.local/bin` and is idempotent.

## ARCHITECTURE — modules to build

Build these as independent CLI tools (prefix `asa-`) plus a thin config layer. Each must run
standalone and be independently testable.

1. `asa-classify`  — task string → `{chain, complexity, categories}` JSON via a rules-driven
   regex classifier. Reads `config/rules.yaml`.
2. `asa-structure` — **the headline feature.** Raw command → a structured prompt document:
   `## Goal / ## Constraints / ## Rules in force / ## Plan (numbered) / ## Verification`.
   It composes the classifier output + matched org rules + a planning template. Output is plain
   markdown the engineer pastes into their assistant (or that an adapter injects automatically).
3. `config/rules.yaml` — the org rulebook: Airtel coding standards, git policy (protected
   branches, commit format), security rules, and `signal → chain` routing rows.
4. `asa-safety`   — given a proposed shell command or file op, return allow/ask/deny. Denies
   `rm -rf`, `git push --force`, `git reset --hard`, `DROP`/`TRUNCATE`, edits to `.env`/secrets/
   `*.pem`/`*.key`, and `--dangerously-skip-permissions`-style flags.
5. `asa-cost`     — append per-task token/cost records to `~/.airtel-superagent/cost/calls.jsonl`;
   summarize spend by model and by day; flag at a configurable daily budget.
6. `asa-memory`   — SQLite+FTS5 store. Subcommands: `write`, `recall`, `list`, `pin`, `forget`.
   Namespaced by git-root hash so projects never cross-contaminate. Scrub PII/secrets on write.
   Apply confidence decay to aged records.
7. `asa-compile`  — read the source rules/skills and emit native config for each target:
   Cursor `.mdc`, Copilot `copilot-instructions.md`, Codex `AGENTS.md`, Claude Code skill files,
   and a generic `AGENTS.md` fallback. One source in, N native files out.
8. `asa-report`   — **the artefact compiler.** Read cost + memory + audit + classify logs and
   emit a one-page evidence sheet (markdown): $ spent & saved, tokens saved, one-shot completion
   rate, risky commands blocked, and config-drift eliminated. This is the org pitch.
9. `asa-obs`      — append JSONL spans/metrics for any tool that wants to record timing; a reader
   that prints a trace tree with p50/p95.

## BUILD ORDER (phased — do not skip the verification gate)

For EACH phase: implement → run the verification command → paste the real output → only then
move on. If verification fails, fix before advancing.

**Phase 0 — Scaffold.**
- Create repo layout: `bin/`, `config/`, `adapters/`, `tests/`, `install.sh`, `README.md`.
- `install.sh` creates `~/.airtel-superagent/{brain,cost,memory,obs,audit}` and symlinks `bin/asa-*`.
- VERIFY: `bash install.sh` runs twice with no errors and no duplicates (idempotent).

**Phase 1 — Classifier + Structurer (the differentiator).**
- Build `asa-classify` + `config/rules.yaml` (start with ~15 rules).
- Build `asa-structure` on top of it.
- VERIFY: `asa-structure "fix the login bug"` prints a full structured doc with Goal, Constraints,
  Rules, a numbered Plan, and a Verification step. Show it.

**Phase 2 — Rules + Safety.**
- Expand `rules.yaml` with Airtel git policy + security rules. Build `asa-safety`.
- VERIFY: `asa-safety "git push --force origin main"` → `deny`; `asa-safety "npm test"` → `allow`.

**Phase 3 — Cost + Memory.**
- Build `asa-cost` and `asa-memory`.
- VERIFY: write a memory, recall it, and confirm a secret-looking string is scrubbed.
  `asa-cost today` prints a spend table.

**Phase 4 — Compiler.**
- Build `asa-compile`. Generate configs for at least Cursor, Copilot, Codex, and generic.
- VERIFY: `asa-compile --all` writes the native files; open two and confirm the same rule appears
  in both, in each tool's format.

**Phase 5 — Evidence reporter.**
- Build `asa-report`.
- VERIFY: after running a few real tasks, `asa-report --since 7d` emits the one-page sheet with
  non-zero numbers. THIS IS THE ARTEFACT you will show leadership.

**Phase 6 — Adapters + polish.**
- Add the optional per-tool adapter that auto-injects the structured prompt for whatever assistant
  Airtel standardizes on. Write the README and a 5-minute quickstart.
- VERIFY: a fresh clone + `bash install.sh` + the quickstart works end to end.

## DEFINITION OF DONE

- Every `asa-*` tool runs standalone and prints useful output.
- `asa-structure` turns any one-liner into a structured, rule-bound prompt.
- `asa-compile` produces native config for ≥4 assistants from one source.
- `asa-report` emits a credible one-page evidence sheet with real numbers.
- No network calls on the hot path; nothing leaves the laptop; install is idempotent.
- A short README explains the five capabilities and the quickstart.

## HOW YOU SHOULD WORK

- Plan before coding anything multi-file; show the plan.
- Commit in small, logically-scoped chunks with conventional-commit messages.
- Verify-or-die: never report success without showing the command output that proves it.
- Ask before any destructive action.
- Keep secrets and code on the laptop. If a step would send data anywhere, stop and ask.

## FIRST STEP

Acknowledge the constraints, then propose the Phase 0 scaffold (file tree + `install.sh` outline)
and wait for my go-ahead before writing Phase 1.

=== END MASTER PROMPT ===

---

## Notes for you (not part of the prompt)

- This builds a **clean-room, enterprise-safe reimplementation** — not a copy of your personal
  repo. That's deliberate: the office laptop likely blocks `pip`/`sudo`/public endpoints, and an
  Airtel-owned tool shouldn't carry your personal marketplace/MCP wiring.
- The **`asa-structure` tool is your headline** — it's the "plain command → structured prompt"
  capability you described, made into a visible artefact you can screenshot.
- **`asa-report` is the pitch.** Run real work for a week, then one command produces the evidence
  sheet leadership will believe.
- Swap `~/.airtel-superagent/` and the `asa-` prefix for whatever naming your org prefers before
  you start.
