# Income Pack — Attribution & Provenance

The `income:*` skills (v3.6.0) are a curated mix of vendored community skills and
first-party originals. Every vendored file was fetched at a pinned commit SHA,
adapted (frontmatter rewritten to the `income:` namespace; references to
tools/files/skills not present in this repo removed or made conditional), and
screened with `superagent-aidefence scan` plus a dangerous-pattern grep before
inclusion. All vendored sources are MIT or Apache-2.0 licensed.

| Skill | Origin | Upstream | Commit | License |
|---|---|---|---|---|
| income:cold-email | vendored | coreyhaines31/marketingskills `skills/cold-email` | 30dbd7f7 | MIT |
| income:copywriting | vendored | coreyhaines31/marketingskills `skills/copywriting` | 30dbd7f7 | MIT |
| income:seo-audit | vendored | coreyhaines31/marketingskills `skills/seo-audit` | 30dbd7f7 | MIT |
| income:programmatic-seo | vendored | coreyhaines31/marketingskills `skills/programmatic-seo` | 30dbd7f7 | MIT |
| income:cro | vendored | coreyhaines31/marketingskills `skills/cro` | 30dbd7f7 | MIT |
| income:pricing | vendored | coreyhaines31/marketingskills `skills/pricing` | 30dbd7f7 | MIT |
| income:social-content | vendored | coreyhaines31/marketingskills `skills/social` | 30dbd7f7 | MIT |
| income:product-launch | vendored | coreyhaines31/marketingskills `skills/launch` | 30dbd7f7 | MIT |
| income:email-marketing | vendored | coreyhaines31/marketingskills `skills/emails` | 30dbd7f7 | MIT |
| income:paid-ads | vendored | coreyhaines31/marketingskills `skills/ads` | 30dbd7f7 | MIT |
| income:sales-outreach | vendored | anthropics/knowledge-work-plugins `sales/skills/draft-outreach` | b4aadd53 | Apache-2.0 |
| income:validate-idea | vendored | whawkinsiv/solo-founder-superpowers `skills/validate` | 3eeadb87 | MIT |
| income:growth | vendored | whawkinsiv/solo-founder-superpowers `skills/growth` | 3eeadb87 | MIT |
| income:investor-pitch | vendored | mohitagw15856/pm-claude-skills `skills/investor-pitch-deck` | b6080ee7 | MIT |
| income:gtm-strategy | vendored | mohitagw15856/pm-claude-skills `skills/go-to-market` | b6080ee7 | MIT |
| income:youtube-strategy | vendored | jeremylongshore/claude-code-plugins-plus-skills `plugins/productivity/youtube-strategy/skills/yt-ideation` | 2cafb238 | MIT |
| income:linkedin-content | vendored | naveedharri/benai-skills `shared-skills/linkedin-writer` | 946a3d76 | MIT |
| income:freelance-proposals | original | — (first-party; no suitable upstream existed) | — | repo license |
| income:productized-service | original | — (first-party) | — | repo license |
| income:mvp-scope | original | — (first-party) | — | repo license |

Excluded from import after screening: linkedin-scan (ronancodes/ronan-skills —
scrapes LinkedIn via authenticated session cookies; ToS and credential-handling
risk), all sub-1-star unproven repos, and every mirror that deduped to the
canonical upstreams above.

Discovery: skillfish registry (mcpmarket API) + GitHub tracing, 2026-07-04.
Full adaptation notes per skill live in the Wave 4 PR description.
