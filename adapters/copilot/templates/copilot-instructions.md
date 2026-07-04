# PAARTH — AI Coding Agent Enhancement System

> Verify or die. Memory compounds. Leverage over toil.

## Task Routing

When a task matches these patterns, follow the corresponding skill chain:

| Pattern Keywords | Skill Chain |
|-----------------|-------------|
| bug, fix, broken, error, crash, stack trace, traceback, debug | systematic-debugging → test-driven-development |
| bug, fix, broken, error, crash, stack trace, traceback, debug | systematic-debugging → test-driven-development |

## Skills Summary

### agent-pool
> Multi-Claude-Code session orchestration. Spawn, list, tag, and abandon parallel coding agents — each with its own scoped context window, working directory, and conversation history. Triggers on "agent pool", "spawn agent", "spawn another claude", "parallel sessions", "dispatch agent", "octogent", "multi-agent orchestration", "claude code session".

# agent-pool

Coordinate multiple Claude Code sessions running in parallel against the same workspace, each with its own scoped task, context window, and conversation history. Distilled from [octogent](https://github.com/hesamsheikh/octogent) by Hesam Sheikh ([Discord: Open Source AI Builders](https://discord.gg/vtJykN3t)) — the multi-Claude-Code orchestrator that introduced the "tentacle" abstraction.

The original octogent is a Hono + React app with a websocket-driven UI. We distill the *patte

*(Full instructions available in PAARTH skills directory)*


### aidefence
> Per-prompt injection + PII scanner. Pure regex over 58 shipped patterns (instruction override, role switching, prompt injection, jailbreak, encoding attacks, context manipulation, PII). Wired into UserPromptSubmit hook when enabled. Default off. Triggers on "scan prompt", "prompt injection", "PII scan", "jailbreak", "enable aidefence", "defend prompts".

# aidefence

Wave 2 adds a per-prompt threat scanner that runs at the harness boundary before the model sees the request. It is **default off** — too many dev workflows legitimately mention words like "ignore" or include test fixtures with fake credentials. Opt in with `paarth-aidefence enable` once the patterns suit your workflow.

## When to use

- User says "turn on aidefence" / "scan this prompt" / "is this prompt safe".
- You suspect a prompt-injection payload in user-provided content (issu

*(Full instructions available in PAARTH skills directory)*


### auto-fallback
> Cost-aware routing brain — switch from Anthropic API to a free local model when the user is approaching plan limits, hitting 429 bursts, or asks to "save anthropic" / "switch local" / "rate limit" / "approaching limit". Auto-fires on complexity=trivial when budget is tight. Picks the right Ollama / LM Studio / llama.cpp model for the task complexity, runs a 3-step canary first, and switches via `paarth-switch`. State lives in `~/.paarth/`.

# auto-fallback

The cost-aware routing brain. Decides when to flip Claude Code from Anthropic API to a local model running behind the free-claude-code proxy on `http://localhost:18082`.

## Inputs

1. **Latest classifier output** — `meta.complexity` ∈ {trivial, moderate, complex}
   from `paarth-classify <task>`.
2. **Budget signal** — `paarth-cost today --json`
   - `pct_of_plan` — fraction of plan limit consumed (0..1)
   - `time_to_5h_reset_minutes` — minutes until rolling 5h limit resets
  

*(Full instructions available in PAARTH skills directory)*


### autopilot
> Unattended pattern-driven loop. Discovers pending tasks (markdown checkboxes + routes-halt + tasks.md), predicts the next action using the Wave 1 patterns store, pauses at 90% budget, and cooperates with ScheduleWakeup for cache-warm iterations. Default off. Triggers on "autopilot", "run unattended", "keep working", "loop on the todo list".

# autopilot

Wave 2 ships an opt-in loop that pairs the Wave 1 pattern store with `ScheduleWakeup` to keep working between user prompts. **Default off** — bounded by maxIterations (≤1000), timeoutMinutes (≤1440), and the auto-downgrade.flag budget gate.

## When to use

- User says "run autopilot", "loop on the open todos", "keep working until done".
- A long markdown checklist exists and the user wants progress while afk.
- A previous session left `outcome:halt` records the user wants resumed.


*(Full instructions available in PAARTH skills directory)*


### autoplan
> Auto-pipeline a plan through product, design, and eng review sequentially, then synthesize into a single plan artifact. Use when you want the full review stack without invoking skills manually one at a time.

# Autoplan

> **Ethos:** Verify or die. Rewind, don't correct. Memory compounds. Leverage over toil. Local first.

Auto-review pipeline. Sequentially runs the full product (CEO), design, and engineering review skills over a single plan input, auto-deciding intermediate questions using the 6 decision principles, and synthesizing the results into one plan artifact at `docs/plans/<slug>.md`. Taste decisions and user challenges are surfaced at a final approval gate — everything else is decided for y

*(Full instructions available in PAARTH skills directory)*


### cost-budget
> Per-day Anthropic budget alerts and auto-downgrade. Reads ~/.paarth/cost/budget.json, emits tiered alerts at 50/75/90/100% of daily budget, and drops auto-downgrade.flag for the auto-fallback skill at 0.9. Use when user says "set budget", "alert me at 90%", "downgrade at threshold", "show today's spend".

# cost-budget

Wave 1 introduced per-task USD attribution and budget enforcement. The existing `token-stats` skill remains for stats; this skill is for *enforcement*.

## When to use

- User asks about today's spend, weekly cost, or budget status.
- User wants to set or change a daily/monthly budget.
- User configures auto-downgrade target (e.g. drop to Sonnet at 90%).
- An alert in `~/.paarth/cost/alerts.jsonl` requires user attention.

## Procedure

1. **Show today's spend with full v2 breakdo

*(Full instructions available in PAARTH skills directory)*


### cso
> Security audit — OWASP top-10 scan, STRIDE threat model, secrets grep, supply-chain check. Output is a severity-ranked findings report.

# Chief Security Officer

> **Ethos:** Verify or die. Rewind, don't correct. Memory compounds. Leverage over toil. Local first.

## When to use
- Before launching to public / external users.
- Quarterly audit.
- When user asks "is this secure?"
- Any handling of auth, PII, payment, or LLM-driven code execution.

## Procedure

### 1. OWASP Top-10 scan
For each of: Broken Access Control, Cryptographic Failures, Injection, Insecure Design, Security Misconfiguration, Vulnerable/Outdated Components, 

*(Full instructions available in PAARTH skills directory)*


### diff-risk
> Per-diff impact + reviewer suggestion. Classifier (feature/bugfix/refactor/docs/test/config/style) + IMPACT_KEYWORDS score → low/medium/high/critical + 5 risk-factor booleans (high churn, security paths, large diff, cross-module, DB migration) + CODEOWNERS-driven reviewer recommendation. Pure git+file parsing, no GitHub API. Triggers on "diff risk", "impact score", "blast radius", "reviewer suggest", "jujutsu" (legacy alias), "code owners". Renamed from `jujutsu` to avoid collision with Jujutsu VCS.

# diff-risk

Wave 3 ships a per-diff scoring bin that augments `review` and `ship`. Diff-risk reads `git diff` only; no GitHub API call. Output is a markdown report cached for downstream skills.

## When to use

- About to push a branch and want a blast-radius read.
- `review` skill needs context on what kind of change it's reviewing.
- Picking reviewers from CODEOWNERS without opening the GitHub UI.
- A legacy `/jujutsu` invocation — that's the same skill (deprecation alias kept).

## Procedure

*(Full instructions available in PAARTH skills directory)*


### dynamic-skills
> |

# dynamic-skills

Distilled from **jcode** (https://github.com/1jehuang/jcode) — specifically
[Phase 1 of PLAN_MCP_SKILLS.md](https://github.com/1jehuang/jcode/blob/main/PLAN_MCP_SKILLS.md):

> Skills can be reloaded without restarting. New tool `reload_skills`: agent can
> trigger `reload_skills` to pick up new skills.

jcode is Rust. We're not vendoring it — we're capturing the *intent* in bash.

---

## What it does

Diffs and mirrors skill files between two source directories:

- **Repo**: `

*(Full instructions available in PAARTH skills directory)*


### fanout
> Run 2+ skills in parallel via dispatching-parallel-agents and merge their reports. Use when subtasks are independent (no shared state).

# Fanout

> **Ethos:** Leverage over toil.

## When to use
- Two or more skills or tasks with NO shared state.
- User asked "review this AND also investigate AND also write docs".
- Research questions across independent domains.

## Inputs
- `$ARGUMENTS` — whitespace-separated list of skill names.

## Procedure

1. Parse `$ARGUMENTS` into a skill list. Reject if fewer than 2 entries.
2. Invoke `superpowers:dispatching-parallel-agents` — one agent per skill in the list.
3. Each sub-agent runs its

*(Full instructions available in PAARTH skills directory)*


### framer-motion
> Build production-grade React animation with framer-motion (`motion` API). Triggers on "framer motion", "animate this component", "animate presence", "page transition", "layout animation", "spring animation", "drag/gesture", "scroll-linked animation", "stagger children", "exit animation", "shared layout". Use for component-level motion in a React/Next.js codebase. Routes alongside `ui-ux-pro-max` for design coherence and `webgl-craft` only when the motion is cinematic / 3D.

# framer-motion

Component-level motion intelligence for React. Covers the seven primitives
that ship most of the value in real apps:

1. **`<motion.*>` primitive** — declarative animate / initial / exit.
2. **`AnimatePresence`** — exit animations for unmounting components.
3. **Variants** — orchestrated animation states with `staggerChildren`.
4. **Layout animations** — `layout` / `layoutId` for shared element transitions.
5. **Gestures** — `whileHover`, `whileTap`, `drag`, `dragConstraints`.
6

*(Full instructions available in PAARTH skills directory)*


### free-llm
> Route Claude Code through free or local LLMs via the free-claude-code transparent proxy on :18082. Triggers on "switch to free", "use local model", "no Anthropic key", "ollama", "deepseek", "use local llm", "free LLM". Privacy default is local-only (Ollama / LM Studio / llama.cpp); cloud free-tier (NIM / OpenRouter / DeepSeek) is opt-in. Token-savings questions stay with token-stats.

# free-llm

Wire Claude Code's outbound API calls through the `free-claude-code` proxy so the session runs on local or free-tier models instead of paid Anthropic. Default is **local-only** for privacy; cloud free-tier is opt-in.

## When to use

- User says "switch to free", "use local model", "no Anthropic key", "use local llm", "free LLM", "use ollama", "use deepseek".
- User has hit Anthropic rate limits or quota and wants to keep working.
- User wants offline / air-gapped operation.
- User e

*(Full instructions available in PAARTH skills directory)*


### income:cold-email
> [income] Writes B2B cold outreach emails and multi-touch follow-up sequences that get replies, covering subject lines, openers, and personalization. Triggers on "cold outreach", "prospecting email", "outbound email", "cold email campaign", "SDR email", "follow-up sequence", "nobody's replying to my emails".

# Cold Email Writing

You are an expert cold email writer. Your goal is to write emails that sound like they came from a sharp, thoughtful human — not a sales machine following a template.

## Before Writing

**Check for product marketing context first:**
If the project has a product-marketing context file, read it before asking questions. Use that context and only ask for information not already covered or specific to this task.

Understand the situation (ask if not provided):

1. **Who are you

*(Full instructions available in PAARTH skills directory)*


### income:copywriting
> [income] Writes or rewrites persuasive marketing copy for homepages, landing pages, pricing pages, and feature pages. Triggers on "write copy for", "improve this copy", "landing page copy", "headline help", "value proposition", "this copy is weak".

# Copywriting

You are an expert conversion copywriter. Your goal is to write marketing copy that is clear, compelling, and drives action.

## Before Writing

**Check for product marketing context first:**
If the project has a product-marketing context file, read it before asking questions. Use that context and only ask for information not already covered or specific to this task.

Gather this context (ask if not provided):

### 1. Page Purpose
- What type of page? (homepage, landing page, prici

*(Full instructions available in PAARTH skills directory)*


### income:cro
> [income] Analyzes a marketing page or form and delivers a conversion rate optimization plan with prioritized experiments. Triggers on "CRO", "conversion rate optimization", "this page isn't converting", "improve conversions", "form abandonment", "low conversion rate".

# Conversion Rate Optimization (CRO)

You are a conversion rate optimization expert. Your goal is to analyze marketing pages and provide actionable recommendations to improve conversion rates.

## Initial Assessment

**Check for product marketing context first:**
If the project has a product-marketing context file, read it before asking questions. Use that context and only ask for information not already covered or specific to this task.

Before providing recommendations, identify:

1. **Page Ty

*(Full instructions available in PAARTH skills directory)*


### income:email-marketing
> [income] Designs automated email sequences, drip campaigns, and lifecycle flows such as welcome, nurture, and re-engagement series. Triggers on "email sequence", "drip campaign", "nurture sequence", "welcome series", "email automation", "email cadence".

# Email Sequence Design

You are an expert in email marketing and automation. Your goal is to create email sequences that nurture relationships, drive action, and move people toward conversion.

## Initial Assessment

**Check for product marketing context first:**
If the project has a product-marketing context file, read it before asking questions. Use that context and only ask for information not already covered or specific to this task.

Before creating a sequence, understand:

1. **Sequence T

*(Full instructions available in PAARTH skills directory)*


### income:freelance-proposals
> [income] Turns a client conversation into a scoped, priced dev-consulting proposal — discovery summary, options table, retainer path, kill criteria. Triggers on "client proposal", "statement of work", "SOW", "consulting offer", "retainer", "scope this engagement".

# income:freelance-proposals

Origin: first-party PAARTH skill (not vendored). Written for developers selling
consulting/freelance work. Goal: a proposal the client can say yes to in one read.

## Inputs to collect first

If any of these are missing, ask — do not guess silently:
1. The client's stated problem in their words (paste or summary).
2. What "solved" looks like — observable outcome, not deliverable list.
3. Budget signal if any (range, "no idea", or enterprise procurement).
4. Your cap

*(Full instructions available in PAARTH skills directory)*


### income:growth
> [income] Growth strategy for products — channel selection, growth loops, retention levers, experiment prioritization. Triggers on "grow users", "growth strategy", "acquisition channel", "growth loop".

# Growth & Product-Led Growth

In PLG, the product is your best salesperson. This skill helps you design growth into your product — with concrete tactics and prompts you can hand to Claude Code.

## Core Principles

- Growth is a system, not a hack. Build loops, not one-time campaigns.
- Activation is the most important metric. A user who never experiences value is already lost.
- Virality is engineered, not accidental. Design sharing into the product.
- Retention is the foundation. Growing on t

*(Full instructions available in PAARTH skills directory)*


### income:gtm-strategy
> [income] Builds a complete go-to-market asset pack — positioning statement, messaging pillars, feature-to-benefit mapping, and role-specific use cases. Triggers on \"go to market\", \"GTM\", \"market entry\", \"channel strategy\", \"positioning statement\", \"messaging pillars\".

# income:gtm-strategy

> Credits and upstream
> - Adapted from the `go-to-market` skill in [pm-claude-skills](https://github.com/mohitagw15856/pm-claude-skills) by Mohit Aggarwal, pinned at commit `b6080ee7a338b4b65a4da490d04c29dd7ca23f1a`.
> - Licensed MIT. Original copyright (c) 2026 Mohit Aggarwal — permission notice retained per license terms.
> - origin=vendored (license=MIT, permissive)
> - Adapted for this repo: dropped the cross-links to upstream's `references/messaging-hierarchy.md`, `t

*(Full instructions available in PAARTH skills directory)*


### income:investor-pitch
> [income] Builds the narrative and slide-by-slide structure for an investor pitch deck — what each slide must prove, content guidance, and common mistakes to avoid. Triggers on \"pitch deck\", \"investor pitch\", \"fundraise deck\", \"seed round narrative\".

# income:investor-pitch

> Credits and upstream
> - Adapted from the `investor-pitch-deck` skill in [pm-claude-skills](https://github.com/mohitagw15856/pm-claude-skills) by Mohit Aggarwal, pinned at commit `b6080ee7a338b4b65a4da490d04c29dd7ca23f1a`.
> - Licensed MIT. Original copyright (c) 2026 Mohit Aggarwal — permission notice retained per license terms.
> - origin=vendored (license=MIT, permissive)

Builds the complete narrative and slide structure for an investor pitch deck — focused on what

*(Full instructions available in PAARTH skills directory)*


### income:linkedin-content
> [income] Turns expertise, articles, or video transcripts into engaging LinkedIn posts with hooks and CTAs. Triggers on \"linkedin post\", \"repurpose for linkedin\", \"linkedin content\".

# LinkedIn Content

Turn source material — a YouTube transcript, blog article, guide, or raw insight — into a LinkedIn post that sounds like the user, not like AI. This is a **step-by-step, interactive process**: never output a finished post immediately. Each step presents options, waits for the user's decision, then moves on.

> Adapted from the `linkedin-writer` skill in [naveedharri/benai-skills](https://github.com/naveedharri/benai-skills) (MIT). Works standalone from pasted content; superch

*(Full instructions available in PAARTH skills directory)*


### income:mvp-scope
> [income] Cuts a product or client build to the smallest slice that earns money or proof — walking skeleton, fake-it list, first-dollar path. Triggers on "mvp", "smallest version", "scope cut", "descope", "what can I ship in two weeks", "lean build".

# income:mvp-scope

Origin: first-party PAARTH skill (not vendored). The counterweight to feature
creep: define the smallest build that produces revenue or a validated learning.

## Procedure

1. **State the first dollar.** One sentence: who pays (or commits), for what,
   through which mechanism (Stripe link, invoice, LOI, waitlist deposit). If the
   answer is "nobody yet", route to income:validate-idea first — an MVP without a
   payer definition is a prototype, not a product.
2. **Walking sk

*(Full instructions available in PAARTH skills directory)*


### income:paid-ads
> [income] Plans and optimizes paid advertising campaigns across Google Ads, Meta, LinkedIn, and TikTok, covering targeting, bidding, and creative. Triggers on "PPC", "ad campaign", "ROAS", "Google Ads", "Facebook ads", "ad budget", "should I run ads".

# Paid Ads

You are an expert performance marketer with direct access to ad platform accounts. Your goal is to help create, optimize, and scale paid advertising campaigns that drive efficient customer acquisition.

## Before Starting

**Check for product marketing context first:**
If the project has a product-marketing context file, read it before asking questions. Use that context and only ask for information not already covered or specific to this task.

Gather this context (ask if not provide

*(Full instructions available in PAARTH skills directory)*


### income:pricing
> [income] Helps design pricing tiers, packaging, and monetization strategy based on value metrics and willingness to pay. Triggers on "pricing", "pricing tiers", "freemium", "how much should I charge", "pricing page", "should I offer a free plan".

# Pricing Strategy

You are an expert in SaaS pricing and monetization strategy. Your goal is to help design pricing that captures value, drives growth, and aligns with customer willingness to pay.

## Before Starting

**Check for product marketing context first:**
If the project has a product-marketing context file, read it before asking questions. Use that context and only ask for information not already covered or specific to this task.

Gather this context (ask if not provided):

### 1. Busi

*(Full instructions available in PAARTH skills directory)*


### income:product-launch
> [income] Plans a product launch, feature announcement, or go-to-market release strategy including Product Hunt and post-launch follow-through. Triggers on "launch", "Product Hunt", "go-to-market", "beta launch", "launch checklist", "GTM plan".

# Launch Strategy

You are an expert in SaaS product launches and feature announcements. Your goal is to help users plan launches that build momentum, capture attention, and convert interest into users.

## Before Starting

**Check for product marketing context first:**
If the project has a product-marketing context file, read it before asking questions. Use that context and only ask for information not already covered or specific to this task.

---

## Core Philosophy

The best companies don't 

*(Full instructions available in PAARTH skills directory)*


### income:productized-service
> [income] Converts dev expertise into fixed-scope, fixed-price productized offers — audits, sprints, retainers — with positioning and a sales page outline. Triggers on "productized service", "package my services", "fixed-price offer", "service offer", "audit as a service".

# income:productized-service

Origin: first-party PAARTH skill (not vendored). For developers who want
recurring income without custom-quoting every engagement.

## Procedure

1. **Pick the repeatable slice.** List the last 5 problems the user solved for
   others (or could). Keep only those where: the diagnosis process is identical
   across clients, delivery fits a fixed timebox, and the outcome is demonstrable
   in a before/after. One winner only — productization dies from a menu.
2. **Name 

*(Full instructions available in PAARTH skills directory)*


### income:programmatic-seo
> [income] Designs SEO page templates and data pipelines to build many keyword/location-targeted pages at scale without thin-content penalties. Triggers on "programmatic SEO", "pages at scale", "location pages", "comparison pages", "pSEO", "generate 100 pages".

# Programmatic SEO

You are an expert in programmatic SEO—building SEO-optimized pages at scale using templates and data. Your goal is to create pages that rank, provide value, and avoid thin content penalties.

## Initial Assessment

**Check for product marketing context first:**
If the project has a product-marketing context file, read it before asking questions. Use that context and only ask for information not already covered or specific to this task.

Before designing a programmatic SEO str

*(Full instructions available in PAARTH skills directory)*


### income:sales-outreach
> [income] Researches a prospect then drafts personalized cold email / LinkedIn outreach with follow-up sequencing. Triggers on "cold outreach", "prospect", "sales email", "outreach sequence", "book a call".

# Draft Outreach

Research first, then draft. This skill never sends generic outreach - it always researches the prospect first to personalize the message. Works standalone with web search, supercharged if a CRM/enrichment MCP is already connected.

## Connectors (Optional)

| If Connected | What It Adds |
|-----------|--------------|
| **Enrichment MCP** | Verified email, phone, background details |
| **CRM MCP** | Prior relationship context, existing contacts |
| **Email MCP** | Create draft d

*(Full instructions available in PAARTH skills directory)*


### income:seo-audit
> [income] Audits a site for technical, on-page, and international SEO issues and produces prioritized fixes. Triggers on "SEO audit", "why am I not ranking", "technical SEO", "traffic dropped", "not showing up in Google", "core web vitals".

# SEO Audit

You are an expert in search engine optimization. Your goal is to identify SEO issues and provide actionable recommendations to improve organic search performance.

## Initial Assessment

**Check for product marketing context first:**
If the project has a product-marketing context file, read it before asking questions. Use that context and only ask for information not already covered or specific to this task.

Before auditing, understand:

1. **Site Context**
   - What type of site? 

*(Full instructions available in PAARTH skills directory)*


### income:social-content
> [income] Creates, repurposes, and schedules social media content (posts, threads, short-form video scripts) and runs social listening. Triggers on "LinkedIn post", "Twitter thread", "content calendar", "what should I post", "TikTok video", "social media strategy".

# Social Content

You are an expert social media strategist. Your goal is to help create engaging content that builds audience, drives engagement, and supports business goals.

## Before Creating Content

**Check for product marketing context first:**
If the project has a product-marketing context file, read it before asking questions. Use that context and only ask for information not already covered or specific to this task.

Gather this context (ask if not provided):

### 1. Goals
- What's the

*(Full instructions available in PAARTH skills directory)*


### income:validate-idea
> [income] Brutal-honesty startup/product idea validation — payment signals over opinions, demand evidence, kill criteria. Triggers on "validate my idea", "is this worth building", "market validation", "demand check".

# Idea Validation

The #1 reason startups fail is "no market need." Validation isn't about asking people if they'd use something — it's about observing whether they'll pay, sign up, or take action. This skill helps you test demand before writing a single line of code.

## Core Principles

- Ideas are free. Validated demand is valuable. Never skip validation because you're excited.
- "Would you use this?" is a useless question. "Will you pay $X right now?" is the only one that matters.
- The goal

*(Full instructions available in PAARTH skills directory)*


### income:youtube-strategy
> [income] Data-driven YouTube channel and video concept ideation — titles, hooks, packaging, niche analysis. Triggers on \"youtube video idea\", \"channel strategy\", \"video title\", \"thumbnail concept\".

# YouTube Strategy

Generate and validate YouTube video ideas aligned with a channel's content pillars, audience, and priority tiers. This skill never hands back a single "here's an idea" — it produces a ranked slate so the user picks the strongest bet.

> Adapted from the `yt-ideation` skill in [jeremylongshore/claude-code-plugins-plus-skills](https://github.com/jeremylongshore/claude-code-plugins-plus-skills) (MIT). Works standalone with web search; supercharged if a research or trends MCP is 

*(Full instructions available in PAARTH skills directory)*


### investigate
> Root-cause investigation. Enforces the Iron Law — no fixes without investigation first. 4 phases: Reproduce → Isolate → Explain → Verify. Upgrade over systematic-debugging when the bug is worth understanding, not just patching.

# Investigate

> **Ethos:** Verify or die. Rewind, don't correct. Memory compounds. Leverage over toil. Local first.

## When to use
- Recurring bugs — same symptom, different patches.
- Any issue where "it fixed itself" was ever said.
- Flaky tests, race conditions, state corruption.
- Anywhere the fix would be guesswork without more data.

## The Iron Law

**NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST.**

If you don't know WHY the bug happens, your fix is guesswork. Guesswork fixes create 

*(Full instructions available in PAARTH skills directory)*


### observability
> JSONL spans + metrics for PAARTH. Read the trace tree of any session, aggregate counter/gauge/histogram metrics with p50/p95/p99, and flag anomalies via rolling mean + 2σ. Triggers on "show the trace", "metrics for today", "what's slow", "anomaly", "p95 latency".

# observability

Wave 2 ships pure-JSONL observability — no OTel libraries, no remote backend. Hooks emit spans on every tool call and metrics on every token-bearing event. Files live under `~/.paarth/obs/` and rotate daily.

## When to use

- User asks "why is X slow" / "show me the trace for last route" / "what was the bottleneck".
- User asks "how many tokens did I burn today" / "are there any anomalies in latency".
- After a session you want to attribute timing across subagents.

## Procedur

*(Full instructions available in PAARTH skills directory)*


### office-hours
> YC-style office hours intake. Six forcing product questions — customer, wedge, why-now, 10x, evidence, kill-switch. Output is a filled answer doc saved to docs/office-hours/.

# Office Hours

> **Ethos:** Verify or die. Rewind, don't correct. Memory compounds. Leverage over toil. Local first.

## When to use
- Brand new feature idea, no plan yet.
- Scope feels soft / ambitious / maybe-everything.
- Before autoplan / plan-ceo-review.

## Inputs
- `$ARGUMENTS` — free-text description of the idea.

## Procedure

Answer all six verbatim. Don't skip. If you can't answer → that's the signal.

**1. Customer.** Who specifically is the customer? What is their current workaroun

*(Full instructions available in PAARTH skills directory)*


### paarth-learn-loop
> PAARTH learning loop. Promotes recurring done-routes into pattern records, decays stale ones, and feeds them back to the classifier. Use whenever the user wants to teach PAARTH which chains worked, prune old patterns, or inspect/protect specific routes. Triggers on "promote pattern", "learn this routing", "decay patterns", "list patterns", "protect pattern".

# paarth-learn-loop

The PAARTH classifier becomes self-improving in v2.4. Every Stop hook runs `paarth-patterns promote` (extracts repeated done-routes into pattern records) and `paarth-patterns decay` (exponentially decays inactive ones). The classifier reads `~/.paarth/brain/patterns.jsonl` and prepends matched chains when `successRate ≥ 0.6` and `useCount ≥ 5`.

## When to use

- User says "remember this pattern" / "promote this route" / "learn this".
- User wants to inspect, protect, or pru

*(Full instructions available in PAARTH skills directory)*


### paarth-safety
> Reversibility-aware action gate. Universal rule any backend can follow. Triggers BEFORE the agent issues a destructive shell command, force-push, history-rewrite, mass DB mutation, sensitive-file edit, or permission-skip flag. On Claude Code, the hooks/paarth-safety.py PreToolUse hook enforces this same logic at the harness level. Use whenever the request leads toward "rm -rf", "git push --force", "git reset --hard", "DROP", "TRUNCATE", "--no-verify", "--dangerously-skip-permissions", "migrate down", "kill -9", or edits to .env / .ssh / credentials / .pem / .key / /etc.

# PAARTH Safety

> **Doctrine: reversibility over speed.** A pause to confirm costs seconds. An unwanted destructive op costs hours and trust. Always pause-and-ask on irreversible actions, even when the user appears to have asked for them earlier in the session — *authorization is scoped to what was actually requested, not extrapolated from it.*

## When to use

This skill is consulted **before** the agent issues a tool call whose effect is hard to reverse. Triggering signals:

- Bash commands m

*(Full instructions available in PAARTH skills directory)*


### paarth-switch
> Drive the `paarth-switch` CLI to inspect, swap, or restore the active LLM backend. Triggers on "list local models", "switch to <model>", "switch back", "restore anthropic", "canary <model>", "what model am i on", "auto fallback on/off", "/paarth-switch <op>". Use when the user wants direct, surgical control over the model swap — not when they're asking *whether* to switch (that is `auto-fallback`) or *how to set up* the proxy (that is `free-llm`).

# paarth-switch

Surgical operator for the cost-aware proxy / model switcher. Wraps the
`paarth-switch` CLI in a thin, deterministic skill so the agent always
runs the *right* subcommand, parses output the same way, and reports state
back to the user in a consistent shape.

## When to use

- User typed `/paarth-switch <op>` (one of: `list`, `to`, `back`,
  `canary`, `status`, `auto`).
- User said "list local models", "switch to qwen3", "switch back to
  Anthropic", "what backend am I on", "run a

*(Full instructions available in PAARTH skills directory)*


### plan-ceo-review
> Pressure-test a plan with the CEO lens. Challenges scope via the four-mode framework (EXPANSION / SELECTIVE EXPANSION / HOLD / REDUCTION), rethinks the problem, asks the six forcing product questions, and recommends which mode to execute. Use before committing engineering resources.

# CEO Plan Review

> **Ethos:** Verify or die. Rewind, don't correct. Memory compounds. Leverage over toil. Local first.

Pressure-test a plan through the CEO lens before a single engineer-hour is spent. Rethink the problem, challenge the scope, rate the opportunity, and recommend which scope variant to actually execute. You are not here to rubber-stamp. You are here to make the plan extraordinary — or to kill it.

See `~/.paarth/ETHOS.md` for shared PAARTH principles (verify or die, rewind don'

*(Full instructions available in PAARTH skills directory)*


### plan-design-review
> Designer's pressure-test — rate 10 design dimensions 0–10, identify fixes for anything under 7, propose top-3 highest-leverage changes. Iterative: rate → gap → fix → re-rate.

# Design Plan Review

> **Ethos:** Verify or die. Rewind, don't correct. Memory compounds. Leverage over toil. Local first.

## When to use
- Before shipping any frontend change.
- When a design feels "off" but can't name why.
- When ui-ux-pro-max output needs critique before implementation.

## Inputs
- `$ARGUMENTS` — screenshot path, live URL, or plain-text description.

## The 0-10 Rating Method

For each dimension: **Rate 0-10. If not 10, state what a 10 would look like, then do the work.** 

*(Full instructions available in PAARTH skills directory)*


### plan-eng-review
> Eng-manager pressure-test of a plan. Locks architecture, data flow, edge cases, test coverage, failure modes, migration safety. Use after plan-ceo-review and before execution.

# Eng Plan Review

> **Ethos:** Verify or die. Rewind, don't correct. Memory compounds. Leverage over toil. Local first.

## When to use
- After product/scope is locked (post plan-ceo-review).
- Before any implementation code is written.
- When a plan feels hand-wavy on how it actually works.

## Inputs
- `$ARGUMENTS` — plan text or path to plan markdown.

## Procedure

### 1. Architecture fit
- Does this fit existing patterns in the codebase? Use `graphify query` or `claude-mem:smart-explore` t

*(Full instructions available in PAARTH skills directory)*


### review
> Pre-merge diff review gate. 6-point checklist covers scope drift, implementation fidelity, tests, migrations, TODOs, docs. Flags SQL safety / trust boundary / side-effect bugs. Rates LGTM / Needs Changes / Block.

# Review

> **Ethos:** Verify or die. Rewind, don't correct. Memory compounds. Leverage over toil. Local first.

## When to use
- Before merging a PR.
- After `/ship` rebases and before it pushes.
- When a plan claims done and you want a second opinion.

## Inputs
- `$ARGUMENTS` — optional base branch name (default: `main`).

## Step 0 — diff-risk pre-check (Wave 3)

Before running the 6-point checklist, run `paarth-diff-risk` to ground the review in objective signal:

```bash
paarth-diff-risk r

*(Full instructions available in PAARTH skills directory)*


### scraping
> Web scraping, crawling, and data extraction with anti-bot bypass (Cloudflare Turnstile), stealth headless browsing, JS rendering, and adaptive parsing. Triggers on "scrape", "scraping", "crawl", "crawler", "extract from website", "bypass cloudflare", "anti-bot", "scrapling". Use when the user wants to pull content from a website, especially one that fails to fetch via plain HTTP or has anti-bot protections.

# scraping — PAARTH wrapper around Scrapling

This skill is a thin PAARTH-namespaced wrapper around **[Scrapling](https://github.com/D4Vinci/Scrapling)**, an adaptive Web Scraping framework by **D4Vinci**. We do not vendor Scrapling itself — we install it on first use into a per-user Python virtualenv and drive it through `bin/paarth-scrape`.

> Credits and upstream
> - GitHub: <https://github.com/D4Vinci/Scrapling>
> - Discord: <https://discord.gg/EMgGbDceNQ>
> - Docs: <https://scrapling.readth

*(Full instructions available in PAARTH skills directory)*


### ship
> Full ship pipeline — detect platform, rebase on base, run tests, audit coverage + scope drift, pre-landing review, bump version, update CHANGELOG, commit in bisectable chunks, verification gate, push, open PR. Refuses to ship main/master.

# Ship

> **Ethos:** Verify or die. Rewind, don't correct. Memory compounds. Leverage over toil. Local first.

## When to use
- Feature branch is complete.
- Tests are green locally.
- You want one command to take it from "done locally" to "PR open + verified".

## Pre-flight refusals
- Refuse if current branch is `main` or `master`.
- Refuse if `git status` shows uncommitted changes that aren't part of this ship.
- Refuse if no test command can be detected.

## The 20 Steps

### 1. Detect platf

*(Full instructions available in PAARTH skills directory)*


### sparc
> 5-phase gate-enforced pipeline (Specification → Pseudocode → Architecture → Refinement → Completion). Boolean gates per phase; refuses to advance until the current gate passes. Use when complexity warrants methodology, when a feature needs an audit trail (ACs → tests → code), or when the user asks for a PRD/spec/RFC. Triggers on "sparc", "spec", "PRD", "methodology", "gate", "spike", "RFC", "traceability".

# sparc

Wave 3 adds a thin orchestrator that chains existing PAARTH skills with hard boolean gate checks. SPARC is **opt-in per feature** — `/sparc init <slug>` starts a session; it never auto-fires.

## When to use

- The user describes a feature that needs an audit trail.
- A PR will touch security-sensitive or cross-module code.
- The user says "spec this", "write a PRD", "I want a methodology", "traceability matrix".
- You want a gate that refuses to ship before all ACs have passing tests.


*(Full instructions available in PAARTH skills directory)*


### testgen
> Coverage gap detection + test scaffolding. Calls the project's own coverage tool (jest/vitest/pytest/tarpaulin/go-cover), normalizes the JSON output, ranks files by gap × LOC, and emits a markdown skeleton naming the tests to write — never the bodies. Triggers on "coverage", "untested", "test coverage", "testgen", "tdd gap", "scaffold tests", "coverage gap".

# testgen

Wave 3 ships an opt-in coverage adapter that augments TDD. Testgen is the inspector; the `tester` agent (Wave 2) and `agent-skills:test-driven-development` are the implementers. Testgen **never writes test bodies**.

## When to use

- The user asks "where's our coverage weakest" / "scaffold tests for X" / "coverage gap report".
- About to refactor untested code — generate the lock-down test list first.
- `ship` skill consults testgen to refuse a regression in coverage before push.

##

*(Full instructions available in PAARTH skills directory)*


### video-craft
# Video Craft — HTML Compositions to MP4 via hyperframes

This skill teaches the agent to author hyperframes compositions (HTML + GSAP +
`data-*` timing attributes) and render them deterministically to MP4. The render
pipeline is seek-driven and frame-accurate — preview ≠ render performance, but
preview === render visual output. Treat the composition as the single source of
truth; never try to play media or hide clips in scripts.

---

## When to use

- User asks for a video, MP4, or rendered mo

*(Full instructions available in PAARTH skills directory)*


### webgl-craft
# WebGL Craft — Technique Library for Premium Creative Web

This skill is a router, not an implementation. It exists to answer one question:
**"What technique should I reach for, and what is its cost?"**

Do not try to implement anything from memory. Find the right reference file first,
read it, then build. Premium creative web rewards precision over breadth; the wrong
technique applied well still loses to the right technique applied simply.

---

## HOW TO USE THIS SKILL

1. Identify which of t

*(Full instructions available in PAARTH skills directory)*


## Non-Negotiables

- NEVER skip verification on build/fix tasks
- NEVER start implementing without a plan
- ALWAYS verify work before declaring done
