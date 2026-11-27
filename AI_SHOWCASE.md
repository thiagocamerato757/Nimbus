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

## Confirmed-decision implementation follow-up — started 2026-11-27 15:22:25 UTC

The developer completed the `grill-with-docs` interview and explicitly confirmed the shared understanding for #11/#13. Confirmed documentation captures duplicate attribution and immediate correction impact, linked same-number Replays, explicit copy/new-draft choice, editable metadata, nonblocking Game Rule validation, scoped acknowledgement carryover with provenance, latest-attempt eligibility, and Fearless Locks only for higher Game numbers (including the requested Azir acceptance example). Implementation resumes sequentially with a fresh worker per issue and a new evidence pack before the next worker. The original #11–#14 request remains in scope; #14 becomes eligible after #13 closes.

Measurements restart at 15:22:25 UTC; primary counters use the last provider snapshot before this interval as baseline, workers use fresh-session zero baselines. Interview effort and earlier implementation are separate intervals. Counter sources, end deltas, handoffs, validation and unplanned fixes will be filled at closeout; billing charges are unavailable. Existing developer edits to AGENTS.md and earlier AI_SHOWCASE text remain unstaged. Claude Code review remains pending before merging PR #34.

### #11 completed after confirmation

- Commit `791c7f1d299020b622bad90aeeadef9c1f3edad6`; [new evidence PASS](https://github.com/thiagocamerato757/Nimbus/issues/11#issuecomment-7222190970); issue closed before the #13 worker started. Canonical #11/#13/spec #2 amendments and confirmed ADR/glossary/example changes were published first (docs commit `73ced90`). Historical partial packs retain their earlier revision scope.
- One fresh worker: **2026-11-27T15:24:50Z–2026-11-27T15:31:51.351475+00:00**, **421.351s (7m 1s)** worker-only. No worker pauses or child agents; primary work excluded.
- Worker delta from fresh-session zero through 2026-11-27T15:32:02.313Z: **1,789,911 input + 14,059 output = 1,803,970 total**, including **1,734,144 cached input**, already included in input. Source `rollout-2026-11-27T12-24-43-01a21d9b-dcfd-7c51-84a7-1ff28a20bca6`; final cumulative counter counted once, provider guardians excluded, monetary cost unavailable.
- Validation: **217 Python tests**, **12 browser journeys**, types/build/mypy/Ruff/whitespace passed. 18 new engine cases across both profiles and 6 API cases proved existing duplicate derivation; no engine/API production changes were needed. Four focused browser journeys cover same-Game duplicate feedback and cross-Game pick/ban impacts.
- First attempt: **No** for the initial new browser setup, which needed to open a collapsed Game detail. Then the intended missing-feedback red was established, implementation passed, and both complete suites passed on their first final run. No outstanding functional limitation; Claude Code review remains pending before merge.

### #13 completed after confirmation and provider-limit handoff

- Parent committed `7aee0701b1952ce1bf590a7eae748ed813c3752d` after the worker's usage-limit interruption. [New evidence PASS](https://github.com/thiagocamerato757/Nimbus/issues/13#issuecomment-7226219207); #13 closed before #14 started. All original lifecycle and confirmed replay claims have passing evidence, including the Azir HTTP/shared-engine example.
- Worker observed execution interval: **15:33:26–15:44:43.268 UTC**, **677.268s (11m17s)** through its last recorded command. One fresh worker, no child agents. It hit the provider usage limit before committing/reporting, so this is **not a first-attempt worker closeout**. Primary completed typing provenance, commit and evidence after the user's continuation. The known command gap **15:44:43.268–19:05:53 UTC** includes the provider-limit/continuation wait; it is not reported as active execution. Exact stop instant inside that gap is unavailable.
- Worker counter delta from fresh-session zero through 2026-11-27T15:44:43.698Z: **2,805,879 input + 22,885 output = 2,828,764 total**, including **2,736,640 cached input**, already in input. Source `rollout-2026-11-27T12-33-21-01a21da3-c475-7542-b8de-fa0d5d0dd8a6`; final cumulative counter once, primary handoff and provider guardians excluded. Monetary cost unavailable.
- Validation: **235 Python tests**, **13 browser journeys**, TypeScript/build, strict mypy, Ruff lint/global format and whitespace passed. Coverage includes schemas 1/4/5/6/7 backup/restore with child facts, no-default mode, editable prefill, immediate copy with Open/carried Violations, max-length reasons/provenance chains, stale writes, structural atomic rejection, replay eligibility and higher-number-only Locks. Full suites preceded a formatting-only correction in the task-owned #11 test; assertions were unchanged, no semantic suite repeat. Parent filled the post-handoff typing provenance gap with a successful strict mypy check.
- Unplanned fixes: read-only preview initially advanced Workspace version; fixed after a red test. Cwd/import/format retries retained in command records. No migration/assertion regressions remain. Parent-authorized format-only cleanup of #11 test included. Expected feature reds remain distinct from these retries and provider failure.
- Claude Code review remains pending before merging PR #34.

### #14 completed — sequence complete

- Commit `405ab7a1d0d2c3fa42ae4591ce31befcfc369e63`; [evidence PASS](https://github.com/thiagocamerato757/Nimbus/issues/14#issuecomment-7226507505). Optional First Selection recording/correction, default holder policy, explicit coupled first-pick Side mapping and snapshots implemented. #14 closed; #11–#14 are complete with individual PASS evidence packs.
- Fresh worker measured **2026-11-27T19:08:39+00:00–2026-11-27T19:23:45.183211+00:00**, **906.183s (15m06s)** worker-only. Initial read-only discovery roughly one minute before the worker's timer is excluded; do not treat this as total task effort. No worker pauses/child agents.
- Fresh-session usage through 2026-11-27T19:24:02.038Z: **5,694,676 input + 30,051 output = 5,724,727 total**, including **5,562,880 cached input**, already in input. Source `rollout-2026-11-27T16-08-25-01a21e68-aaf2-7840-8223-d967b5d1b43f`; final cumulative counter once, guardians excluded, monetary cost unavailable. This usage includes the worker's earlier discovery excluded by its elapsed timer.
- Final validation: **248 Python tests**, **15 Playwright journeys**, build/TypeScript, strict mypy (11 sources), Ruff, formatting (29 files) and whitespace passed. Full suites ran once after implementation. Added 6 shared-engine cases across both profiles, 7 API cases and 2 browser journeys; Replay regressions remain passing.
- First attempt: **No** for intermediate checks. Expected behavior reds separated from cwd/type/import/format corrections, accessible-label and reload/reselection fixture retries. No full-suite failure at final validation. Default-policy research used official Riot NACL26.6 sections 2.3.3.1 and 2.6.5.1 (league-specific previous-loser policy); generic LoL neutral `none` is expressly not a league-rule assertion. Official PDF/HTML extraction overcame web rendering failures; no secondary snippet used as authority. [Policy/source documentation](docs/first-selection.md).
- Claude Code review remains **pending** before merging [PR #34](https://github.com/thiagocamerato757/Nimbus/pull/34).

### Follow-up measurement cutoff and final state

All requested implementation is complete: #11, #12, #13 and #14 are closed with individual PASS evidence linked in [draft PR #34](https://github.com/thiagocamerato757/Nimbus/pull/34), targeting `dev`. No merge was performed. Final complete suites: **248 Python tests and 15 Chromium journeys**, plus build/types, strict mypy, Ruff lint/format and whitespace. Claude Code review is **pending**; run `sail-skills:code-review` in Claude Code against `dev` or the reviewed PR range before merging.

Resumed implementation measurement: **2026-11-27T15:22:25Z–2026-11-27T19:26:57.817066+00:00**, **14672.817s (4h 4m 32s)** elapsed. Observed no-command gap **2026-11-27T15:44:43.268452+00:00–2026-11-27T19:05:53+00:00**, **12069.732s**, includes the provider usage-limit/continuation wait and is excluded from the separate **2603.086s (43m 23s)** elapsed outside that gap. The latter still includes tool waits, coordination and handoffs; it is not an active-compute timer. The exact provider stop instant is unavailable. Final documentation commit/push and final reply fall after the measurement cutoff.

Primary task counter delta from the last provider snapshot before the resumed interval: **14,300,322 input + 43,593 output = 14,343,915 total**, including **14,192,896 cached input** already counted in input. The baseline excludes the earlier implementation and interview. Primary + the three fresh follow-up worker deltas total **24,590,788 input + 110,588 output = 24,701,376 total tokens**, including **24,226,560 cached input** already included in input. Each cumulative provider counter contributes one end-minus-baseline delta; worker baseline is zero, no overlapping snapshots are summed. Auxiliary provider guardians are excluded, so this is measured agent effort rather than all provider effort. Billing charges/credits spent are unavailable; a reported zero credit balance is not a cost measurement. [Exact counters, cutoff/source paths and provider limits](docs/evidence/issues-11-14-followup-usage.json).

The #13 worker's verification succeeded but its closeout failed on provider limit; primary completed commit/evidence. This handoff and its measurement scope are recorded above. Existing developer changes to AGENTS.md and earlier AI_SHOWCASE sections were preserved outside the task commits.
