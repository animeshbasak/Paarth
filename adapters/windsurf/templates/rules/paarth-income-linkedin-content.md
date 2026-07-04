# income:linkedin-content

> [income] Turns expertise, articles, or video transcripts into engaging LinkedIn posts with hooks and CTAs. Triggers on \"linkedin post\", \"repurpose for linkedin\", \"linkedin content\".

# LinkedIn Content

Turn source material — a YouTube transcript, blog article, guide, or raw insight — into a LinkedIn post that sounds like the user, not like AI. This is a **step-by-step, interactive process**: never output a finished post immediately. Each step presents options, waits for the user's decision, then moves on.

> Adapted from the `linkedin-writer` skill in [naveedharri/benai-skills](https://github.com/naveedharri/benai-skills) (MIT). Works standalone from pasted content; supercharged if a web-scraping or transcript MCP is already connected.

## Connectors (Optional)

| If Connected | What It Adds |
|-----------|--------------|
| **Transcript/YouTube MCP** | Pull a transcript directly from a video URL instead of asking the user to paste it |
| **Web-fetch/scraping MCP** | Pull article text directly from a blog URL |

> **No MCPs connected?** Ask the user to paste the transcript or article text directly — that's the default path and works just as well.

Why this process exists: great LinkedIn posts aren't summaries of content — they're built around a specific audience outcome, the right structural framework, and a hook that stops the scroll. Rushing to a finished post skips the thinking that makes a post perform.

## Step 0: Source Intake

Figure out what the source material is and get the full content.

**Always use provided content first.** If the user pastes a transcript, article text, notes, or a document, read it directly — don't try to fetch anything externally.

- **User provides content directly (most common):** read it, give a 1-2 sentence summary of what it covers, and move on.
- **User provides just an insight or idea (no source doc):** acknowledge it and summarize it back to confirm understanding — that's valid input on its own.
- **User provides only a URL, no pasted text:** if a relevant MCP is connected (transcript/YouTube or web-fetch), use it to retrieve the content. If no such MCP is connected, ask the user to paste the transcript or article text directly rather than guessing at the content.

Never scrape LinkedIn profiles or posts directly — if LinkedIn content is the source, ask the user to paste the text.

Confirm the source material with a brief summary before moving to Step 1.

## Step 1: Content Analysis (Internal)

Before suggesting outcomes, analyze the source material silently:

- Core themes and ideas
- Specific stories, data points, or examples that stand out
- Angles that could resonate with the target audience
- Personal experiences or unique perspectives worth surfacing

Don't dump this analysis on the user — use it to inform Step 2's options. Just confirm you've read it and are ready to suggest directions.

## Step 2: Define the Main Outcome for the Audience

Decide *what the reader should take away from this post*. Every good post changes how the reader thinks, feels, or acts — and source material usually supports several different angles. Picking the right one is what separates a forgettable post from one that resonates.

**Present 10 genuinely different options**, each with:
- **Main outcome** (1 sentence) — what the reader walks away thinking, feeling, or doing
- **Angle** (1 sentence) — the specific lens to get there
- **Secondary outcome** (optional, 1 sentence) — an additional benefit

Pull from different themes in the source material and different audience segments/pain points — don't just rephrase the same idea 10 ways.

**One post = one idea with depth.** If the user picks a main outcome plus a secondary, weave the secondary in as an undertone, not an explicit section — giving equal weight to 4-5 ideas turns a punchy post into a shallow blog post.

**Wait for the user to choose before continuing.**

## Step 3: Define the Writing Framework

Present all four frameworks below, each with 3-5 bullets describing how *this specific post* would flow under that structure — a skeleton, not a draft.

| Framework | Best for |
|---|---|
| **PAS** — Problem, Agitation, Solution | A clear pain point that needs surfacing and intensifying before the resolution lands. |
| **AIDA** — Attention, Interest, Desire, Action | Building momentum toward a specific action — announcements, discoveries, calls to try something. |
| **CPF** — Context, Problem, Framework | Topics that need scene-setting before the problem makes sense — educational, nuanced posts. |
| **BAB** — Before, After, Bridge | Transformation stories — where the reader is now, where they could be, and the bridge between. |

**Wait for the user to choose before continuing.**

## Step 4: Define the Hook

The hook is the single most important element — on LinkedIn only the first ~2 lines show before "see more." It has to earn that click.

**Brevity is everything.** Great hooks are short — often under 15 words for the first line. If a hook needs a paragraph to land, it's not a hook.

**Present exactly 10 hook options.** Each should:
- Be short and punchy — 1-2 lines max
- Serve the outcome chosen in Step 2, each from a different angle
- Be ready to use as-is

Draw from proven hook shapes, filling in specifics from the source material rather than writing something only "loosely inspired." A few reliable shapes to pull from:

- **Result-in-time**: "I [achieved outcome] in [time frame]. I also [related outcome]."
- **Contrarian claim**: "Everyone tells you to [common advice]. Here's why that's wrong."
- **Confession**: "I made a [size] mistake with [topic]. Here's what it taught me."
- **Question hook**: "Why do most [audience] struggle with [problem]?"
- **Number list tease**: "[N] things I wish I knew before [experience]."
- **Direct address**: "If you're a [audience segment], stop doing [common behavior]."
- **Before/after snapshot**: "[State before]. Now [state after]. Here's what changed."

Match the shape to the outcome (Step 2), the framework (Step 3), and the audience's real pain points — not a generic template filled with placeholders.

**Wait for the user to choose before continuing.**

## Step 5: Write the Post

Now write the full post. Present it as a clean, standalone block of text the user can copy or iterate on.

### The Hook-to-Body Connection

Posts most commonly fail here. The hook and body must read as one continuous thought.

The hook delivers the "what." The very next line should be the natural next thought a reader would have — ask "if someone just read this hook out loud, what would I say next?"

Avoid: re-explaining the hook in different words, abruptly jumping topics, or opening the body with backstory the hook already implied.

### Writing Rules

**Sentence length and rhythm — the #1 tell between human and AI writing:**
- Average sentence length: 7-12 words. Break up anything over 20.
- Every new thought gets its own line — no exceptions.
- Rhythm: short statement → line break → expansion → line break → contrast → line break → insight.
- Fragments are fine and often stronger: "Node by node." "In real time." "That was still true a year later."

**Structure & formatting:**
- Short paragraphs — 1-2 sentences, then a line break.
- Use arrow bullets (`↳` or `➝`) for lists, never plain dashes or bullet points.
- Total length 150-300 words (the LinkedIn sweet spot).
- End with a soft CTA or a question to drive engagement.

**Tone:**
- Direct and confident — no hedging.
- Conversational — write like explaining something to a smart friend, not structuring an argument.
- Use "I" and "you" freely.
- Specific examples over generic advice; lead with insight, not information.
- No corporate jargon or buzzword soup.

**What NOT to do:**
- No hashtags in the body (optional 3-5 at the very bottom, on their own line).
- No more than 1-2 emojis, and only if they add something.
- No LinkedIn clichés: "I'm excited to share...", "In today's fast-paced world", "Let's dive in", "game-changer", "landscape".
- No walls of text — if a paragraph runs past 2 sentences, split it.
- No cramming 4-5 ideas into sections — one idea, with depth.

### After Writing

Present the draft, then ask:
- How does this feel — want to adjust tone, length, or emphasis?
- Should any section be sharpened?
- Want to try a different hook from Step 4?

Be ready to iterate — the first draft is a starting point.

## Quick Reference

| Step | What happens | User chooses from |
|---|---|---|
| 0 | Get source material | — |
| 1 | Analyze content internally | — |
| 2 | Suggest audience outcomes | 10 options |
| 3 | Suggest writing frameworks | 4 frameworks with skeletons |
| 4 | Suggest hooks | 10 options |
| 5 | Write the post | Iterate with the user |

**Golden rule:** never skip a step, never combine steps, never output a finished post before Step 5. Each decision builds on the last — rushing produces generic content.
