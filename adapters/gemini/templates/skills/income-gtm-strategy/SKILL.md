---
name: income:gtm-strategy
description: [income] Builds a complete go-to-market asset pack — positioning statement, messaging pillars, feature-to-benefit mapping, and role-specific use cases. Triggers on \"go to market\", \"GTM\", \"market entry\", \"channel strategy\", \"positioning statement\", \"messaging pillars\".
---

# income:gtm-strategy

> Credits and upstream
> - Adapted from the `go-to-market` skill in [pm-claude-skills](https://github.com/mohitagw15856/pm-claude-skills) by Mohit Aggarwal, pinned at commit `b6080ee7a338b4b65a4da490d04c29dd7ca23f1a`.
> - Licensed MIT. Original copyright (c) 2026 Mohit Aggarwal — permission notice retained per license terms.
> - origin=vendored (license=MIT, permissive)
> - Adapted for this repo: dropped the cross-links to upstream's `references/messaging-hierarchy.md`, `templates/gtm-pack.md`, and a sibling `professional-brain` skill, none of which are vendored here. The persistent-memory step below is rephrased to be conditional on whatever project memory store is actually present, rather than naming a specific missing skill.

This skill produces a complete go-to-market asset pack for a product, feature, or initiative. It follows Geoffrey Moore's positioning framework and structures all outputs for use in sales decks, landing pages, launch emails, and internal alignment docs.

## Working from a brief

You will often get a short brief without every detail. **Always deliver the full GTM pack anyway** — do not stop to ask questions and do not leave bracketed placeholders like `[ADD PROOF POINT]` or `[Technical capability]`. Where a detail is missing (differentiators, proof points, features), infer specific, realistic ones from the product description and the target customer, and mark anything inferred as *(assumed — confirm)*. A concrete, labelled assumption is always better than a blank.

## Inputs (infer any not provided — label assumptions)

- **Product/feature name**
- **One-line description** (what it does, technically)
- **Target customer** (role, company size, industry if relevant)
- **Primary problem it solves**
- **Key competitor or alternative** (what people do today without this)
- **Top 3 differentiators**

## Reads from / Writes to project memory (if any)

If this project maintains a persistent memory or "brain" store, check it before asking the user anything:

- **Read first:** product/ICP context, prior market and strategy notes, and any existing entry for the feature being launched.
- **Write after:** save the launch plan and any positioning or channel decision back to that store, provenance-tagged.

If no such store exists, proceed directly from the brief and inferred assumptions.

## Output Structure

Always produce all four sections below in order.

---

### 1. Positioning Statement

Use the Geoffrey Moore format exactly:

> For **[target customer]** who **[has this problem or need]**, **[Product Name]** is a **[product category]** that **[key benefit/outcome]**. Unlike **[primary alternative or competitor]**, our product **[key differentiator]**.

Write one primary positioning statement, then offer a shorter tagline version (10 words or fewer) suitable for a hero headline.

---

### 2. Messaging Pillars

Generate 3–5 messaging pillars. Each pillar must include:

- **Pillar name** (2–4 words, bold)
- **One-sentence summary** of what this pillar claims
- **2–3 proof points** (specific and evidence-backed; if no data was provided, infer a realistic proof point and mark it *(assumed)* — never leave a bare placeholder)
- **Example use in copy** (one sentence as it would appear in a landing page or deck)

Pillars should be distinct — avoid overlap. Each pillar should be defensible against the primary competitor.

---

### 3. Feature & Functionality List

Produce a two-column table:

| Feature / Functionality | Buyer Benefit (what it means for the user) |
|---|---|
| [Technical capability] | [Outcome in plain language — start with a verb: "Reduces...", "Enables...", "Eliminates..."] |

Rules:
- Never list a feature without a corresponding benefit
- Benefits should reference the target customer's workflow or pain point
- Aim for 6–12 rows; if only 1–2 features were given, infer the rest plausibly from the product description
- Avoid jargon in the benefit column — write as if explaining to a buyer, not an engineer

---

### 4. Use Cases

Generate 3–5 role-specific use cases. Each use case must follow this format:

**Use Case [N]: [Role] — [Scenario Title]**

- **Who:** [Job title / role]
- **Situation:** [The specific moment or trigger that leads them to use the product]
- **Before:** [What they had to do without this product — be specific about time, friction, or risk]
- **With [Product Name]:** [What they do now — concrete action, not vague benefit]
- **Outcome:** [Measurable or tangible result]

Use cases should cover different buyer personas if possible (e.g. end user, manager, admin).

---

## Quality Checks

Before delivering output, verify:
- [ ] Positioning statement follows Moore format exactly
- [ ] Tagline is 10 words or fewer
- [ ] Each pillar has at least 2 proof points (or flagged placeholders)
- [ ] Every feature has a benefit — no orphaned features
- [ ] Benefits start with action verbs
- [ ] Use cases include a Before/After structure
- [ ] Language is consistent with the target customer's vocabulary (not internal engineering terms)

## Anti-Patterns

- [ ] Do not write feature descriptions instead of benefits — the GTM pack must translate features into customer value
- [ ] Do not use the same messaging across all buyer personas — each role has different priorities and language
- [ ] Do not create a positioning statement that could apply to any competitor — differentiation must be specific and defensible
- [ ] Do not skip the "not for" section — defining who this is not for sharpens positioning and prevents misdirected sales effort
- [ ] Do not list use cases without tying them to specific job titles or buyer roles

## Example Trigger Phrases

- "Create a positioning statement for [product]"
- "Write a GTM plan for [feature]"
- "Give me key pillars for [product name]"
- "Build a feature and use case list for [product]"
- "We're launching [X] — help me with the messaging"
