# income:youtube-strategy

> [income] Data-driven YouTube channel and video concept ideation — titles, hooks, packaging, niche analysis. Triggers on \"youtube video idea\", \"channel strategy\", \"video title\", \"thumbnail concept\".

# YouTube Strategy

Generate and validate YouTube video ideas aligned with a channel's content pillars, audience, and priority tiers. This skill never hands back a single "here's an idea" — it produces a ranked slate so the user picks the strongest bet.

> Adapted from the `yt-ideation` skill in [jeremylongshore/claude-code-plugins-plus-skills](https://github.com/jeremylongshore/claude-code-plugins-plus-skills) (MIT). Works standalone with web search; supercharged if a research or trends MCP is already connected.

## Connectors (Optional)

| If Connected | What It Adds |
|-----------|--------------|
| **Web search / trends MCP** | Live search-demand and trend-direction signal per idea |
| **YouTube data / analytics MCP** | Real channel history, past-video performance, competitor uploads |

> **No MCPs connected?** Web search plus general knowledge of the niche works fine — validation just leans more on judgment than live data.

## Before You Start

Get from the user:

1. **Focus area** — the tool, niche, or topic to ideate around (e.g. "AI tools for professionals", "recent software updates", "productivity workflows").
2. **Research data** (optional) — any existing niche analysis, competitor notes, or audience research to ground the ideation in data rather than gut feel.
3. **Constraints** (optional) — anything that shapes what's makeable (e.g. "only short-form", "needs to be filmable this week", "must tie to a launch").

If the focus is already given, confirm and proceed — don't re-ask what's already answered.

## Step 1: Load Context

Before generating ideas, understand:

- **Content pillars** — the channel's core recurring topics.
- **Audience** — who watches, and their skill/experience level.
- **Content types** — which formats already work (tutorials, reviews, updates, comparisons).
- **Trending vs. evergreen balance** — how much of the channel leans timely vs. long-lasting.

## Step 2: Generate 15-20 Raw Ideas

Use these four ideation methods together:

**Gap Analysis** (if research data is available)
- Content gaps versus competitors
- High-demand, low-competition topics
- Complex concepts that need an accessible translation

**Trend Riding**
- Recent tool updates or feature launches
- Industry developments relevant to the audience
- Viral topics that can be made practical

**Format Innovation**
- Existing topics reframed into a new format (comparison, mega-guide, use-case compilation)
- Formats competitors in the niche aren't using
- Series potential (multi-part tutorials)

**Audience Needs**
- Questions the audience is actually asking (comments, communities, forums)
- Problems viewers hit with the tools/topics in question
- "How do I..." queries specific to the niche

For each idea, capture:

- **Working title**
- **Content tier** — Tier 1 (growth content) or Tier 2 (supporting content)
- **Content type** — full tutorial, feature tutorial, update video, use-case video, comparison, etc.
- **One-line angle** — what makes this take unique
- **Timeliness** — trending/urgent or evergreen

**Priority distribution:** aim for 60-70% Tier 1 (the growth engine) and 30-40% Tier 2 (supporting content).

## Step 3: Quick Self-Filter

Before validating, run every idea through:

- Does it serve the target audience? (must be yes)
- Can it be practically demonstrated? (prefer yes)
- Does it support the content funnel — is there an asset to give away?
- Is it filmable in the channel's current format?

Drop ideas that fail, and note why for transparency.

## Step 4: Validate Ideas

For each surviving idea, assess:

- **Search demand** — via web search / trends MCP if connected, otherwise informed estimate
- **Competition level** — existing videos and the quality bar to beat
- **Trend direction** — rising, stable, or declining
- **Audience fit** — accessibility and practical value

Score each idea 1-10 on opportunity. If a Task-style sub-agent capability is available, split validation into small batches (e.g. 5 ideas at a time) rather than doing it all serially.

## Step 5: Present Ranked Results

```markdown
Here are your validated video ideas, ranked by opportunity:

| # | Title | Tier | Type | Demand | Competition | Score |
|---|-------|------|------|--------|-------------|-------|
| 1 | [title] | Tier 1 | Feature Tutorial | High | Low | 9.2 |
| 2 | [title] | Tier 1 | Update Video | High | Medium | 8.5 |
...

Top recommendation: [title] - [1 sentence why]

Which ideas do you want to develop further (title/hook/packaging pass)?
```

Offer the user the option to: pick 1-3 ideas to develop further, generate more ideas in a different direction, refine a specific idea, or go back to research.

## Key Principles

- **Tier 1 first** — always prioritize growth content (tutorials, use cases, updates); it drives channel growth.
- **Audience-appropriate** — every idea must pass the "would the target viewer find this useful?" test.
- **Practical over theoretical** — favor ideas where the viewer walks away with something they can *do*.
- **CTA-ready** — strong ideas include a natural asset giveaway (template, workflow, resource) tying back to the creator's business.
- **Data-informed** — use research data when it exists; gut-feel ideation is the fallback, not the default.
