# PAARTH Agent — from skill-set to standalone agent

**Date:** 2026-07-07 · **Status:** PROPOSED
**One-liner:** Merge friday's Python agent runtime with paarth's routing brain into one local-first, LLM-agnostic personal agent — installable on macOS, usable from any IDE via MCP, reachable from Chrome and Telegram.

---

## 0. The reframe that makes this work

Today paarth is *prose interpreted by Claude Code* — its intelligence rides on the host model and dies outside a Claude Code session. friday is *code that runs a loop* — but with a brittle keyword brain and no skill system.

The product is the combination, split along one line:

| Layer | Lives in | Why |
|---|---|---|
| **Kernel** — the loop: perceive → recall → classify → plan → act → verify → learn. Plus safety gate, scheduler, budget governor, memory, pattern learning. | **Deterministic code (Python)** | "Its own thinking capabilities." The discipline (fable-parity gates, verify-or-die, safety) is enforced by code, so output quality no longer depends on which LLM is plugged in. This is the exact thesis of the existing fable-parity skill — promoted from prose to runtime. |
| **Brain** — reasoning, planning, text generation, tool-argument filling | **Pluggable LLM** | "Brain of any LLM it is used on." Anthropic / OpenAI / Gemini / Groq / Ollama / LM Studio behind one provider interface. |
| **Hands** — shell, files, browser, IDE, Telegram, calendar | **Tool adapters** | Each surface is just a tool bundle + a face. |

An LLM-agnostic agent is only as good as its harness — weaker models in a strong harness beat strong models freestyle. paarth's tier-dial system (S/A/B/C/local) already encodes this; it becomes kernel config, not prose.

## 1. What already exists (leverage map — ~70% of the kernel is built)

**From friday (the runtime):**
- `core/orchestrator.py` — the loop skeleton (840 lines, tested, mine_turn bug fixed 2026-07-07)
- `foundation/brain.py` + `api_fallback.py` + `ollama/client.py` — tiered model selection + provider cascade (needs provider interface generalization)
- `core/governor.py` — light/build/heavy runtime modes with anti-flap cooldown
- `memory/` — SQLite memory graph + mempalace adapter
- `scheduler/` — SQLite job store + background runner + delivery (proactive tasks)
- `interfaces/telegram/` — working bot (a face, done)
- `arena/` — multi-model scoring (model selection per task type)
- `gateway/` — FastAPI + WebSocket (feeds the Chrome extension and dashboard)
- `agents/verifier/` — policy + shadow-sim safety layer

**From paarth (the brain policy):**
- `skills/paarth/brain/rules.yaml` (63 rules) + `bin/paarth-classify` — routing (port bash→Python)
- `~/.paarth/brain/patterns.jsonl` + promote/decay learning loop — self-improvement
- `hooks/paarth-safety.py` — reversibility gate (already Python; drop in)
- 52 skills as markdown — become **playbooks**: structured prompts+checklists the kernel injects per task type. Skills stay markdown = editable without redeploying.
- `bin/paarth-memory-mcp/` — Memory-OS MCP server (already speaks MCP!)
- fable-parity gates — become kernel verification states, not prose

**Known debt to fix during absorption (from 2026-07-07 audit):**
- friday's `_classify_intent` keyword matching → replaced by ported rules.yaml classifier + LLM fallback (kills two birds)
- Hardcoded stale model IDs in `brain.py` → move to a versioned model registry
- Sync gateway POST on hot path → async/opt-in
- Dead shell dirs (`orchestrator/`, `runtime/`, `voice/`, `integrations/`) → delete
- Memory-OS compressor stubs → implement or de-market

## 2. Target architecture

```
                    ┌─────────────── FACES ───────────────┐
                    │ CLI  ·  Mac daemon (launchd/menubar) │
                    │ MCP server (any IDE)  ·  Chrome ext  │
                    │ Telegram  ·  (later: voice)          │
                    └──────────────────┬───────────────────┘
                                       │
   ┌───────────────────────── KERNEL (Python, deterministic) ─────────────────────────┐
   │  Loop: perceive → recall → classify → plan → act → verify → learn                │
   │  · Router (rules.yaml + patterns.jsonl + LLM fallback)                           │
   │  · Safety gate (paarth-safety: reversibility-aware, allowlists)                  │
   │  · Verifier (fable-parity gates as code: reproduce/verify/self-critique/evidence)│
   │  · Governor (runtime modes) + Budget (token/cost caps per provider)              │
   │  · Memory (graph + episodic + patterns)  · Scheduler (proactive jobs)            │
   │  · Playbook loader (skills/*.md)  · Route log + learning loop                    │
   └──────────┬───────────────────────────────────────────────┬──────────────────────┘
              │                                                │
   ┌──────── BRAIN (pluggable) ────────┐          ┌────────── HANDS ──────────┐
   │ Provider interface:               │          │ shell (gated) · files     │
   │ anthropic · openai · gemini ·     │          │ browser (via Chrome ext)  │
   │ groq · ollama · lmstudio          │          │ IDE workspace (via MCP)   │
   │ + normalized tool-calling schema  │          │ telegram · web fetch      │
   │ + tier detection → kernel dials   │          │ (later: mail/calendar)    │
   └───────────────────────────────────┘          └───────────────────────────┘
```

**Key decisions (made, with rationale):**
1. **Python is the base; friday's repo is the seed.** The runtime, tests (178), and every hard subsystem already exist there. paarth's bash tools port INTO it. The Claude Code plugin remains one face — not deprecated.
2. **MCP is the IDE strategy.** One MCP server exposes paarth as tools + memory to Claude Code, Cursor, Zed, Continue, VS Code — every major IDE speaks MCP now. Zero per-IDE adapters to maintain (the existing 9-IDE adapter compiler stays for rules-file users, but MCP is the live integration).
3. **Tool-calling normalization is the hard technical problem.** Providers differ in function-calling quality/format; local models are worst. Mitigation: one internal tool schema, per-provider marshalling, and a JSON-repair + retry layer in the kernel. For C/local tiers, kernel falls back to constrained "choose from menu" prompting instead of free-form tool calls.
4. **Chrome extension talks to the daemon via native messaging** (Chrome's sanctioned channel to a local process), falling back to `localhost` WebSocket to friday's existing gateway. The extension is thin: page context in, gated actions out.
5. **Security is non-negotiable:** every act passes the safety gate; shell/browser actions use allowlists; Chrome actions are simulate-first (friday's verifier shadow-sim pattern); secrets never enter LLM context. A standalone agent with shell + browser access without this is malware with extra steps.

## 3. Phases (each independently shippable)

### Phase 1 — Kernel consolidation (the merge)
Fork friday → `paarth-agent`. Port `paarth-classify` + rules.yaml + patterns loop + safety gate into Python kernel modules. Replace friday's keyword `_classify_intent` with the ported router. Playbook loader for skills/*.md. Provider interface v1: anthropic + ollama + groq (reuse api_fallback), normalized tool schema, tier detection wired to kernel dials. Verification states from fable-parity.
**Exit test:** `paarth do "summarize my day and remind me at 6pm"` works CLI-only against BOTH claude-haiku and a local Qwen — same behavior, different brains. Full pytest green.

### Phase 2 — MCP face (IDE-ready, highest leverage per hour)
Expose kernel as an MCP server: `route_task`, `run_playbook`, `memory_recall/write`, `safety_check`, `schedule`. Extend the existing Memory-OS MCP server rather than starting fresh.
**Exit test:** From Cursor (non-Claude model) and Claude Code: call paarth tools, get routed playbooks + memory. Same brain state across both IDEs.

### Phase 3 — Mac residency (daemon + proactive)
launchd service wrapping the kernel + scheduler; Telegram becomes the notification channel (already built). Morning digest, reminders with real NL time parsing, long-run build pings. Menu bar app (rumps/SwiftUI) is a stretch goal — the daemon matters, the chrome doesn't.
**Exit test:** MacBook reboots; paarth comes back; a scheduled reminder fires to Telegram without any session open.

### Phase 4 — Chrome extension
Native-messaging host → daemon. v1 capabilities: read current page → summarize/extract to memory, save-to-memory hotkey, job-posting → lakshya evaluate handoff. Action-taking (clicking/filling) only after simulate-gate proves out.
**Exit test:** On a job posting, one click sends it through lakshya's evaluate flow and files the result in memory.

### Phase 5 — Day-to-day pack + learning flywheel
Gmail/GCal via existing MCP connectors (hands, not new code). Route log → pattern promotion → per-task-type model selection using arena scores ("Qwen handles summaries fine; escalate planning to Claude"). This is where "evolve yourself" becomes literal: the agent's routing measurably improves from its own history.

### Explicit non-goals (v1)
Voice. Windows. Multi-user/team. Auto-acting in Chrome beyond simulate-gated actions. Replacing Claude Code for heavy coding — paarth *routes and remembers*; IDE agents still execute big builds.

## 4. Risks — honest ledger

| Risk | Reality check | Mitigation |
|---|---|---|
| Local models are weak at tool-calling | They are. This kills naive LLM-agnostic agents. | Kernel-side constrained prompting for low tiers; verify-in-code; arena scores decide which tasks a model is *allowed* to take. |
| Scope explosion (this is a product, not a feature) | Correct. | Phases 1–2 alone are useful forever. Ship thin; each phase has a hard exit test. |
| Security of shell+browser agent | Biggest real risk. | Safety gate on every act, allowlists, simulate-first browser, no secrets in context, kill switch. |
| Two-repo drift during migration (paarth plugin vs agent) | Likely. | rules.yaml, patterns.jsonl, and skills/*.md stay the single shared source; both read the same `~/.paarth/` state. |
| Maintainer bandwidth (solo, plus lakshya income work) | The binding constraint. | Lakshya WTP validation stays priority #1; this runs as the evenings-project. Phase 1+2 ≈ 2–3 focused weekends given the reuse map. |

## 5. First concrete slice (when greenlit)

1. `git clone friday paarth-agent` (fresh repo), delete dead shells, carry the 178-test suite.
2. Port `paarth-classify` → `kernel/router.py` reading the same `rules.yaml`; wire into orchestrator replacing `_classify_intent`; tests proving parity with the bash classifier on the 59-prompt bench.
3. Drop `hooks/paarth-safety.py` in as `kernel/safety.py` gating the tool registry.
4. Provider interface: extract friday's fallback into `brain/providers/{anthropic,groq,ollama}.py` with the normalized tool schema.

That slice alone gives friday a real brain and paarth a real body — everything after compounds.
