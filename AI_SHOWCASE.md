# AI-Powered Workflow: How Nimbus Was Built

> How Nimbus is built with coding agents, documented as it happens.
> This file is filled in as the project is built.

## The setup

Nimbus was built by a single developer using two kinds of agents with separate roles:

| Role | Tool | What it did |
|---|---|---|
| **Planning & review** | Claude Code (terminal) | Sharpened the idea, wrote specs and split them into tickets on GitHub Issues, explored data, ran code reviews. |
| **Execution** | **Codex** | Implemented tickets in parallel, each in its own Git worktree, with changes reviewed before merging. |

Both agents followed the same process, the [SAIL Skills](https://github.com/SAIL-PUC-Rio/Agentic-Software-Engineering-Skills) from PUC-Rio's Software and AI Engineering Lab:
`/grill-with-docs` → `/to-spec` → `/to-tickets` → `/implement` → `/evidence` → `/code-review`.
Every ticket closes with an evidence pack on its GitHub issue that maps each claim to the command that proved it.

Shared rules for all agents live in [`AGENTS.md`](AGENTS.md).

## Task log

One row per task. Filled in right after each task, not from memory at the end.

| Ticket | Agent | Worked first try? | Review fixes needed | Time | Tokens / credits | Notes |
|---|---|---|---|---|---|---|
| #1 | | | | | | |

## What worked

_TBD_

## What didn't

_TBD_

## Numbers

_TBD: totals by agent (tasks, success rate, tokens/credits, time)._

## Lessons learned

_TBD_

## Sequential implementation #11–#14 — recorded scope

The developer invoked `implement-sequential` for [#11](https://github.com/thiagocamerato757/Nimbus/issues/11), [#12](https://github.com/thiagocamerato757/Nimbus/issues/12), [#13](https://github.com/thiagocamerato757/Nimbus/issues/13) and [#14](https://github.com/thiagocamerato757/Nimbus/issues/14). Coordination started at **2026-11-27 14:23:49 UTC** on `feat/issues-11-14`, based on `36a27a1` (merged PR #33). Existing edits to `AGENTS.md` and this document were preserved. One fresh Codex worker implements each issue; the primary agent owns dependency checks, decisions, evidence publication and this record. Workers do not overlap.

Measurement starts before implementation: the primary counter snapshot at 14:24:44.337 UTC was 142,625 input tokens (110,848 cached, already included) and 1,326 output tokens. This counter snapshot excludes earlier coordination, so its eventual delta is a partial primary measurement. Execution time starts at 14:23:49 UTC and includes decision waits and handoffs. Worker measurements start with each worker's own task. Provider counters are cumulative: use final minus baseline, never add successive snapshots. Monetary cost is unavailable; the provider reports no credit balance, which does not measure the monetary cost of this task.

Initial environment retries: GitHub network calls and branch creation required escalated execution; the installed `gh` rejects combined `--comments --json`, so comments were fetched through `gh api`; the unconfigured `python` shim was replaced by `python3`. The #11 worker encountered the known sandbox TestClient hang and was directed to repeat the run with execution permission. Expected TDD red tests are recorded separately from unplanned fixes.

Pending product decisions were presented for #11 (duplicate Character Violation carrier) and #13 (replay prefill). Claude Code review is **pending**: before merging this subsequent work, run `sail-skills:code-review` in Claude Code against the branch base. The waiver for PRs #31–#33 does not cover this branch.

### #11 closeout — 2026-11-27 14:38 UTC

- Implementation: `afc87d837ae029b014e52dba0ebd1015b8f690e1`, published on the feature branch. [Evidence pack](https://github.com/thiagocamerato757/Nimbus/issues/11#issuecomment-7221029756). Settled BS-010 functionality is implemented; overall issue/evidence status **PARTIAL** because the duplicate Character Violation carrier decision remains pending. #11 stays open.
- Worker interval: 14:25:42.965–14:37:33.422 UTC, **11m 50s**; primary coordination/publication excluded. One worker, no worker handoff or pause; human decision remained pending while settled work progressed.
- Fresh worker counter delta from zero through final sampled response (2026-11-27T14:37:49.009Z): **3,669,342 input + 23,929 output = 3,693,271 total tokens**, including **3,570,816 cached input** already included in input. Source: issue11 worker session `01a21d65-d52e-7b62-9406-2cdc2bcd2f09`; one final cumulative counter used, repeated snapshots excluded. Provider guardian usage is excluded from this worker figure. Credits/cost unavailable as task charges.
- Validation: **174 Python tests**, **7 Playwright journeys**, mypy, Ruff, frontend build/typecheck and whitespace checks passed. 80 reversal examples × 5 Fearless combinations × both profiles include acknowledgements. Schema migration, restart, historical Character references and backup restoration were verified through the API.
- First attempt: **No** for the complete verification run. The first full suite failed collection because new API/engine test modules shared a basename; renaming the engine test fixed it, and the full suite then passed. Sandbox TestClient hangs required escalation; a mistaken npm working directory and Ruff import/formatting issues were corrected. Expected TDD red tests are separate.
- Publication retry: plain HTTPS git push had no credential helper; repeating with the existing authenticated `gh auth git-credential` helper succeeded.
- Claude Code review: **pending**, required reminder before merging this branch.

### #12 closeout — 2026-11-27 14:55 UTC

- Implementation: `b50117afdbd731efdecae0815699d11ebcc70db0`, published on the feature branch. [Evidence pack](https://github.com/thiagocamerato757/Nimbus/issues/12#issuecomment-7221387778). Implementation complete; acceptance evidence **PASS**, issue closed before starting #13.
- One fresh worker, approximately 14:38:10–14:53:44.723 UTC (**15m 35s**, start approximate); first observed clock 14:38:27 gives **15m 18s** measured interval. No worker pauses/subagents; parent coordination/evidence excluded.
- Fresh worker counter from zero to final provider sample (2026-11-27T14:53:56.141Z): **5,018,734 input + 30,007 output = 5,048,741 total**, including **4,927,360 cached input**, already counted in input. Source: `rollout-2026-11-27T11-38-15-01a21d71-50bf-7131-ae4c-6458d304344d`; only final cumulative snapshot counted. Credits/task charges unavailable; provider guardian effort excluded from worker counters.
- Validation: **180 Python tests**, **8 Playwright journeys**, Ruff, strict mypy, TypeScript/build and whitespace passed. Cases include independent same-name Players, one current roster link, membership-change-preserving previous Lineup copy, historical assignments after removal, synthetic six-player profile, migration/backup compatibility and pool-reference protection. Backend full suite preceded final UI-only fixes; browser/build rerun passed after those fixes.
- First attempt: **No**. Migration checks exposed unstable legacy Team IDs and pre-existing additive tables on restore; fixed in scope. Type annotations/imports and browser selectors required corrections. Full browser run exposed stale Player query revisions after Series creation and reused layout selector; refresh coordination/control disabling and a dedicated editor layout fixed them. Expected TDD reds recorded separately.
- Claude Code review remains **pending** before merge.

### #13 settled-scope closeout — 2026-11-27 15:08 UTC

- Commit `7710bc5454438481b7336a7f62a035c3ba1c14b2` published. [Evidence pack](https://github.com/thiagocamerato757/Nimbus/issues/13#issuecomment-7221664981): **PARTIAL**, since replay prefill remains undecided and replay is not implemented. #13 stays open; #14 has not started because #13 is its native blocker.
- One fresh worker, **14:55:13–15:07:07 UTC, 11m54s**. No subagents or worker pauses; primary coordination/publication excluded.
- Fresh-session counter from zero through 2026-11-27T15:07:14.736Z: **4,146,829 input + 20,275 output = 4,167,104 total**, including **4,046,208 cached input** already in input. Source: `rollout-2026-11-27T11-55-09-01a21d80-c9c3-7d81-92e2-bfe3e0297b50`; each provider response counted once via final cumulative counter; guardians excluded. Credits/task charges unavailable.
- Validation: **193 Python tests**, **9 browser journeys**, final focused lifecycle journey, build/typecheck, mypy, Ruff and whitespace passed. The full browser run predates a final current-Voided-label fix; its focused journey and build passed afterward.
- First attempt: **No**. Initial full Python run had 189 passing tests and four restore/migration failures. Preserving pre-existing lifecycle columns fixed the regressions, followed by 25 passing focused checks and 193 passing full tests. Other retries: migration wiring, unsupported test format fixture, module basename collision, callback typing, browser accessibility/working-directory setup, and final Voided heading. Two engine examples shared one red run (minor TDD pacing deviation). No pre-existing migration regression assertions changed.
- Claude Code review: **pending** before merge.

### Sequence status and measured aggregate

[Draft PR #34](https://github.com/thiagocamerato757/Nimbus/pull/34) targets `dev`; no merge was performed. #12 is complete/closed. #11 remains partial pending the duplicate-carrier decision. #13 remains partial pending replay prefill, and #14 is blocked by its open native dependency #13. This follows the requested `implement-sequential` gate: “a subissue is next only once every subissue that blocks it is closed.” Human clarification questions were sent early; no answers arrived during the measured interval. Settled work continued during the wait, with no worker overlap or idle handoff pause.

Measured task interval **2026-11-27T14:23:49+00:00–2026-11-27T15:08:45.763453+00:00**, **2696.763s (44m 56s)** elapsed, including coordination, tool waits, worker handoffs, evidence publication and concurrent waiting on product decisions. Not an active-compute timer. The snapshot excludes final documentation commit/push, final reply and subsequent waiting.

Primary full fresh-session usage through **2026-11-27T15:08:13.331Z**: **7,288,562 input + 23,592 output = 7,312,154 total**, including **7,134,336 cached input** already in input. Recovery confirmed the first primary counter was after task start, with no prior task counters; baseline zero therefore covers the initial coordination omitted by the earlier partial delta snapshot.

Observed primary + three fresh workers: **20,123,467 input + 97,803 output = 20,221,270 total tokens**, including **19,678,720 cached input**, already in input. Each session contributes its final cumulative counter once, a delta from the fresh-session zero baseline. Provider auxiliary guardian counters are excluded, so this is the observed agent total, not all provider effort. Monetary cost/billable credits unavailable; reported credit balance zero does not measure task charges. Exact source/cutoff counters are preserved in [`docs/evidence/issues-11-14-usage.json`](docs/evidence/issues-11-14-usage.json).

Claude Code review remains **pending**. Before merging #34, run `sail-skills:code-review` in Claude Code against `dev` (or the reviewed PR range). Existing user edits to `AGENTS.md` and the earlier sections of this file remain outside the implementation commits; only this task's appended record is staged at closeout.
