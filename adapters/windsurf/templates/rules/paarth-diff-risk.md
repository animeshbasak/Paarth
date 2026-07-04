# diff-risk

> Per-diff impact + reviewer suggestion. Classifier (feature/bugfix/refactor/docs/test/config/style) + IMPACT_KEYWORDS score → low/medium/high/critical + 5 risk-factor booleans (high churn, security paths, large diff, cross-module, DB migration) + CODEOWNERS-driven reviewer recommendation. Pure git+file parsing, no GitHub API. Triggers on "diff risk", "impact score", "blast radius", "reviewer suggest", "jujutsu" (legacy alias), "code owners". Renamed from `jujutsu` to avoid collision with Jujutsu VCS.

# diff-risk

Wave 3 ships a per-diff scoring bin that augments `review` and `ship`. Diff-risk reads `git diff` only; no GitHub API call. Output is a markdown report cached for downstream skills.

## When to use

- About to push a branch and want a blast-radius read.
- `review` skill needs context on what kind of change it's reviewing.
- Picking reviewers from CODEOWNERS without opening the GitHub UI.
- A legacy `/jujutsu` invocation — that's the same skill (deprecation alias kept).

## Procedure

1. **One-shot report** (most common):
   ```bash
   paarth-diff-risk report --base origin/main
   ```
   Composes classifier + impact + risk + reviewers and caches `~/.paarth/diff/last.json`.

2. **Drill into a single dimension:**
   ```bash
   paarth-diff-risk classify --commit-msg "$(git log -1 --pretty=%s)" --files "$(git diff --name-only --cached | paste -sd,)"
   paarth-diff-risk impact --branch "$(git rev-parse --abbrev-ref HEAD)"
   paarth-diff-risk reviewers --files "$(git diff --name-only HEAD~1...HEAD | paste -sd,)"
   ```

3. **JSON mode** for `ship` / `review` integration:
   ```bash
   paarth-diff-risk report --base origin/main --json
   ```

## Classifier

Verbatim regex map from spec §8.3:

| Type | Patterns |
|---|---|
| feature  | `^feat`, `add.*feature`, `implement`, `new.*functionality` |
| bugfix   | `^fix`, `bug`, `patch`, `resolve.*issue`, `hotfix` |
| refactor | `^refactor`, `restructure`, `reorganize`, `cleanup`, `rename` |
| docs     | `^docs?`, `documentation`, `readme`, `\.md$` |
| test     | `^test`, `spec`, `\.test\.[jt]sx?$`, `__tests__` |
| config   | `^config`, `\.config\.`, `package\.json`, `\.env` |
| style    | `^style`, `format`, `lint`, `prettier`, `eslint` |

Multi-label scoring: every type whose patterns match commit msg or file paths contributes a count. Primary = highest count; secondary = the rest (alphabetical tiebreak for determinism).

## Impact score

`IMPACT_KEYWORDS` from spec:

| Keyword | Score |
|---|---|
| security | 3 |
| auth | 3 |
| payment | 3 |
| database | 2 |
| api | 2 |
| core | 2 |
| util | 1 |
| helper | 1 |
| test, mock, fixture | 0 |

Sum scores across branch name + file paths. Map to `low (0)`, `medium (≥1)`, `high (≥3)`, `critical (≥5)`.

## Risk factors

Boolean flags appended to the report:

1. **high_churn_files** — files with `git log --oneline <file> | wc -l > 20`.
2. **security_paths** — paths matching `auth/`, `crypto/`, `permissions/`, `.env`.
3. **large_diff** — total lines added+deleted > 500.
4. **cross_module** — ≥3 top-level dirs touched.
5. **db_migration** — `migrations/` paths or `.sql` files.

## Reviewers

Reads `.github/CODEOWNERS` → `docs/CODEOWNERS` → root `CODEOWNERS` (first found wins). Each `<glob> @owner1 @owner2` line is matched against changed paths via `fnmatch`. Returns the union of owners. No GitHub API call.

## Integration

- `review` skill: calls `diff-risk report` before its 6-point checklist; folds the classification into the verdict.
- `ship` skill: calls `diff-risk report --json` before push. When `impact == "high"` or `"critical"`, the ship procedure force-confirms.

## Legacy alias

`/jujutsu` is kept as a deprecation alias. Both slash commands route here. The alias prints a one-line note to stderr but still runs.

## Ethos

Verify or die. The score is not a quality judgment — it's a blast-radius prediction. A 5/5 critical score on a database migration is not bad; it's the signal to ask whoever owns the DB before push. Pure file parsing keeps this fast and offline.
