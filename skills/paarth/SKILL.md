---
name: paarth
description: Master entrypoint. Takes a task, classifies it, composes a skill chain, announces the plan, executes. Use whenever the user types /paarth <task> or says "use paarth for X".
argument-hint: "<task description>"
---

# PAARTH Router

> **Ethos:** Verify or die. Rewind, don't correct. Memory compounds. Leverage over toil. Local first.

## When to use
- User invokes `/paarth <task>`.
- User says "paarth this", "full power mode", "activate all agents".
- Any complex task where you're unsure which skills to chain.

## Procedure

**1. Detect backend + model tier (always).** First call only:
```bash
backend=$(paarth-switch status 2>/dev/null | awk '/^mode:/ {print $2}')
[ -z "$backend" ] && backend="anthropic"
```
Then determine your **model tier** from your own system prompt's model id (you are told what model you are):

| Model id contains | Tier |
|---|---|
| `fable`, `mythos` | S |
| `opus` | A |
| `sonnet` | B |
| `haiku` | C |
| `backend=local` (any local model) | local |
| unknown / can't tell | treat as B |

Apply the **Model-tier rules** section below for every tier except S. If `backend=local`, also run in **lite mode**: skip step 2 context load, shorter announce format. Weaker models handle structured checklists better than free-form reasoning — the tier rules exist to convert judgment into checklists.

**2. Load context (cloud only).** Skip on local backend. Otherwise run once per session:
```bash
command -v mempalace >/dev/null 2>&1 && mempalace wake-up 2>/dev/null | head -n "${PAARTH_WAKE_LINES:-40}" || true
```

**3. Optimize (brain step 0).** Rewrite the raw task into a tight directive before classifying. Strip the `? ` confirm prefix first if present (see step 6), then:
```bash
if command -v paarth-optimize >/dev/null 2>&1; then
  paarth-optimize "$TASK"
fi
```
Output is JSON `{original, optimized, notes, changed}`. If `changed` is true, use `optimized` as the working task for every later step — classify, announce, execute — and show it in the announce block. If the optimizer is missing, errors, or returns `changed: false`, continue with the raw task. Kill switch: `PAARTH_OPTIMIZE=0`. Never silently swap intent — the optimizer only strips filler and restructures; if its output looks semantically different from what the user asked, fall back to the raw task and say so.

**4. Classify.** Run the classifier on the (optimized) task:
```bash
if command -v paarth-classify >/dev/null 2>&1; then
  paarth-classify "$TASK"
else
  echo '{"chain":[],"hint":null}'
fi
```
Output is JSON `{chain: [...], hint: [...|null]}`. **If classifier missing or chain empty:** fall back to keyword matching against the available skills list shown in your system reminders — including the `agent-skills:*` namespace (16 skills imported from agent-skills covering define → plan → build → verify → ship). Pick top-3 by description overlap and ask user.

**5. Announce.** Print to the user:
```
PAARTH routing plan for: "<task>"
Optimized: <optimized task — only when the optimizer changed it>
Backend: <anthropic|local:model-name> (tier <S|A|B|C|local>)
Chain: skill1 → skill2 → skill3
Rationale: <one line why each skill was selected>
Estimated effort: <rough>
Proceed? (yes / edit / skip N / run-only N)
```
On local backend, omit Rationale and Estimated effort lines — keep announce ≤4 lines total.

**6. Auto-execute (default).** Do NOT ask "Proceed?". The user opted in by invoking PAARTH. Skip the confirmation gate and start running the chain immediately.

**Opt-in confirm prefix.** If `$ARGUMENTS` starts with `? ` (literal question mark + space), strip the prefix before classifying and run in **confirm mode** for this call only — show the chain and wait for `yes/edit/skip N/run-only N`. Pre-process (works in bash and zsh):
```bash
TASK="$ARGUMENTS"
CONFIRM="auto"
if [ "${TASK:0:2}" = "? " ]; then
  CONFIRM="yes"
  TASK="${TASK#? }"
fi
```

**Force-confirm (override auto, even without `?` prefix):**
- Task or chain contains a destructive op: `ship`, `deploy`, `push`, `force`, `delete`, `drop`, `rm`, `migrate down`, `revert`, `reset --hard`.
- Chain includes `cso` or `security-review` (findings should be reviewed first).
- Chain length exceeds the tier's max (see Model-tier rules) — offer to trim or confirm full plan.
- Classifier returned empty/`mempalace-wake` only AND keyword-match has no high-confidence single skill.

**7. Execute.** For each skill in the chain, invoke via the Skill tool in order, working from the optimized task. Between skills, summarize the artifact produced in one sentence. If a skill fails or user says "stop", halt and report.

**8. Log.** After completion (or halt), append to `~/.paarth/brain/routes.jsonl` (auto-create if missing):
```bash
mkdir -p ~/.paarth/brain
# then append the route record
```
```json
{"ts": "<iso>", "task_hash": "<sha256-12>", "task": "<first 120 chars>", "chain": [...], "outcome": "done|halt|fail", "user_override": "yes|no", "backend": "<anthropic|local>", "optimized": true|false}
```

## Skill namespaces

The roster is organized into namespaces. Pick from any:

- **Bare names** — core PAARTH skills (`ship`, `review`, `cso`, `simplify`, `investigate`, `learn`, plan-* family, `auto-fallback`, `paarth-switch`, `free-llm`, etc.)
- **`agent-skills:*`** — Addy Osmani's production engineering skills (16 skills): `idea-refine`, `spec-driven-development`, `planning-and-task-breakdown`, `incremental-implementation`, `test-driven-development`, `context-engineering`, `source-driven-development`, `frontend-ui-engineering`, `api-and-interface-design`, `browser-testing-with-devtools`, `debugging-and-error-recovery`, `performance-optimization`, `git-workflow-and-versioning`, `ci-cd-and-automation`, `deprecation-and-migration`, `documentation-and-adrs`. Step-by-step + verifiable; preferred when a process must be followed exactly (especially on local models).
- **`superpowers:*`** — Claude Code superpowers (TDD, debugging, brainstorming, plan execution).
- **`claude-mem:*`, `caveman:*`, `vercel:*`, `ui-ux-pro-max:*`** — domain plugins.

When a core skill and an `agent-skills:*` skill overlap (e.g. `simplify` vs `agent-skills:incremental-implementation` for refactor work), the bare-name PAARTH skill wins by default. Prefer the `agent-skills:*` version explicitly when the user wants step-by-step rigor or when running on a local model.

## Model-tier rules (any tier below S)

The gap between a top-tier model and a weaker one is mostly *discipline*, not knowledge: reproducing before fixing, verifying wider than asked, self-critiquing before claiming done. These rules externalize that discipline so the output quality does not depend on model strength.

**Universal (tiers A, B, C, local) — the parity core:**

- **Load `fable-parity` on every build/fix/refactor chain.** Its five gates (reproduce → confirm diagnosis → full-suite verify → self-critique → evidence block) are mandatory; a done claim without the evidence block is not done.
- **One extra hypothesis, always.** Before acting on a diagnosis (yours or one handed to you), write down one alternative explanation and say why you ruled it out.
- **Verify wider than asked.** Scope limits apply to what you change, never to what you check — run the full suite/build even when pointed at one test.
- **Externalize state.** Keep a running task file or TaskCreate list for anything ≥3 steps; re-read it before each step instead of trusting recall.
- **Cite before claiming.** Any API/flag/method you are not 100% sure exists: grep the codebase or check docs (`context7`) before using it. Never ship a guessed identifier.

**Per-tier dials:**

| Dial | A (opus) | B (sonnet) | C (haiku) | local |
|---|---|---|---|---|
| Max chain length | 5 | 4 | 3 | 3 |
| Prefer `agent-skills:*` checklists | no | on build/ship | yes | yes |
| Self-critique passes before done | 1 | 1 | 2 | 2 |
| mempalace pre-load | yes | yes | head -20 | skip |
| Decompose task into ≤n-step slices | n=7 | n=5 | n=3 | n=3 |

**C/local extras:**

- **Skip `claude-api` skill** on local — Anthropic-SDK-specific; suggest `free-llm` instead.
- **Single-skill route by default** for trivial questions — don't chain just to chain.
- **Don't promise tool reliability.** If a skill needs a specific MCP (Chrome DevTools, Notion, etc.), tell the user to verify it's connected before running.
- **Restate the task in one line before each chain step** — weak models drift; the restatement is the anchor.

## Fallback — classifier uncertain
If classifier is missing or returns an empty chain:
1. Read the available skills list from your system reminders.
2. Match user's task keywords against skill descriptions (prefer exact verb matches: "build" → builds, "fix" → debugging, "ship" → ship).
3. Show top-3 candidates and let user pick.
4. Never invent a skill name not in the list.

## What stays manual
- Plan Mode (Shift+Tab twice) — user's call.
- Rewind (Esc Esc) — user's call.
- Permission grants — `/permissions`.
- Backend switch — user runs `/paarth-switch to <model>` or `back`.

## Verification
After each skill runs, require the skill's own output. For build/fix chains, the final `verification-before-completion` (or `agent-skills:test-driven-development` Verification block on local backend) must pass before declaring done. On any tier below S, done additionally means the `fable-parity` evidence block (VERDICT / FIXED / VERIFIED / NOT VERIFIED / FOUND ALONG THE WAY) is present in the final report.
