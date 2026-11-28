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

## Claude Code review of PR #34 — 2026-11-27

`sail-skills:code-review` ran in Claude Code against `origin/dev...e0eb1b7` (merge base `36a27a1`, 9 commits, 47 files). The Standards and Spec reviewers ran in parallel. Spec sources were #2 (BS-010, BS-011, BS-012) and tickets #11–#14. Claude review status: **completed, with changes requested**.

- Agents: a Claude Code primary agent and two parallel Claude reviewer subagents, Standards and Spec.
- First attempt: **No**.
  - The first try started at 19:30:29Z on Sonnet 5.5 and also began a full local check run.
  - The developer stopped it, switched to Opus 5.5 and invoked the review again at 19:32:23Z.
  - The first try produced no results. Its usage counters are unavailable.
- Time: 19:32:23Z–19:39:16Z UTC, **6m 53s** elapsed, including tool waits. The interrupted first try (19:30:29Z–about 19:32Z) is excluded.
- Usage, reviewers only, reported by the harness:
  - Standards: 96,043 tokens, 99s.
  - Spec: 143,743 tokens, 369s.
  - Total: **239,786 tokens**. The input/output/cache split and the primary agent's tokens are unavailable. Billing and credits are unavailable.
- Validation:
  - The full test suite was not re-run, because the developer stopped that run.
  - The Spec reviewer ran four scratch API probes against temporary databases. All four reproduced their defects.
  - The primary agent re-read the cited code for findings 1 and 2.
- Spec findings, worst first:
  1. Clearing after a voided later Game leaves the earlier Game stuck in Drafting, and a new Game can then start (BS-010, BS-011). Reproduced.
  2. A winner on a Game still in Drafting counts toward the Series score. Reproduced.
  3. A non-Replay Game after a void takes a new number, which the spec does not settle. Reproduced.
  4. Draft Positions cannot be edited when the draft is copied. Reproduced.
  5. Nit: the winner prompt's "Record and start" applies a holder prefill the analyst did not see.
- Standards findings: no hard breaches.
  - One undocumented revision exemption for `/replay-preview` in `workspace.py`.
  - Judgement-call smells: duplicated Lineup and structural checks, primitive and data-clump parameters, and a `RosterTeam` term that is missing from the glossary.
- Fixes: none applied; the review only reports.

## PR #34 review fixes — 2026-11-27

The developer decided how to resolve the Claude Code review findings above and asked for test-first fixes in this order:

1. One definition of "current Game".
2. Winner only on Drafted or Closed Games.
3. Numbering after a void.
4. A specific error for a copied draft with changed Draft Positions.
5. A display-only First Selection pre-fill.
6. Merged Structural Invariant checks.

- **Agents:** a Claude Code primary agent (Opus 5.5) with no subagents.
- **Time:** 19:41:52Z–2026-11-27T20:07:19Z UTC, elapsed, including test and tool waits.
- **Usage:** primary-agent token counters are unavailable in this session, and no subagent ran. Billing and credits are unavailable.
- **First attempt: No.**
  - One new API test corrected a pick to "skipped", which is structurally invalid. It was fixed to use another Character.
  - A scripted test edit spliced at stale offsets; the two seams were repaired by hand and checked in the diff.
- **Planned test changes.** Seven pre-existing Python tests and one browser journey encoded behavior the developer reversed: a winner on an incomplete Game, an ordinary Game after a void, a generic `invalid_turn` for a copied draft with changed positions, and the server applying the pre-fill. They were updated to the decided rules.
  - The Azir HTTP example was rebuilt with completed Games 1 and 2, because the old "voided Games 1 and 2 → Game 3" sequence is no longer possible.
- **Retired Characters.** The merged check keeps Retired Characters structurally valid, as ADR 0009 and #11 require ("a correction can deliberately choose a Retired Character"). Only live entry refuses them, and a test pins the difference.
- **Pre-fill.** The server never applies one; an omitted holder records none, so the field was not made required.
- **Validation:**
  - Python: 269 tests passed, 248 before plus 21 new runs counting parametrized cases. Both engine profiles were covered.
  - Browser: 16 Playwright journeys passed (15 before plus 1 new). The three changed or new journeys failed against the previous `App.tsx` and passed with the fix.
  - Static checks: Ruff lint and format, strict mypy, whitespace, and the frontend build passed.
- **Docs and tracker:**
  - ADR 0008 and ADR 0034 have dated amendments.
  - Design notes and `docs/first-selection.md` are updated.
  - #2 and #13 bodies have dated decision sections.
  - The remaining smells are listed in [#35](https://github.com/thiagocamerato757/Nimbus/issues/35).
- **Committed later.** These changes were committed after the third round, in `2632f51` (code and tests), `a3ec9dd` (docs and the spec move) and `c5f33d5` (this record), and pushed to PR #34.
- **Claude Code review:** run `sail-skills:code-review` again against `dev` before merging PR #34.

## PR #34 second round and Claude review — 2026-11-27

**Developer decisions applied:**
- Clearing a winner is allowed in any status. Only setting one is restricted to Drafted or Closed Games.
- Only the current Game can be voided (`void_not_current`), recorded as an ADR 0034 amendment.
- Copied Replay drafts accept Retired Characters, following the correction rule. The omitted holder means "none", as decided.
- The MVP spec moved from issue #2 to `docs/spec/mvp.md`. #2 now holds a short summary and a link.

**Fix run (20:10:00Z–20:16:17Z UTC, elapsed):**
- First attempt: **Yes**. The new tests failed first as intended and passed after the change.
- Python: 272 tests passed.
- Browser: 17 Playwright journeys passed, 1 new, for clearing a stored winner.
- Static checks: Ruff, strict mypy, whitespace and the build passed.
- Agents and usage: the Claude Code primary agent (Opus 5.5) only. Primary-agent tokens and billing are unavailable.

**Review run (`sail-skills:code-review` against `dev`, 20:16:17Z–20:22:03Z UTC, elapsed):**
- Scope:
  - The working tree against merge base `36a27a1`, so the uncommitted fixes are included.
  - `AGENTS.md` and `AI_SHOWCASE.md` are excluded, and the untracked `docs/spec/mvp.md` is included.
- Agents and usage:
  - Standards reviewer: 67,735 tokens.
  - Spec reviewer: 131,721 tokens.
  - Total: 199,456 tokens, reviewers only, as reported by the harness. The split and billing are unavailable.
- Status: **changes requested**. The primary agent checked the ADR 0010 conflict, the weakened test and the missing gate in the code.
- Spec findings:
  1. A Replay is created after the Series has ended, with no `series_ended` gate (reproduced). This is a spec gap, so the developer decides.
  2. The BS-011 API test "voiding creates no locks in later Games" now checks only the same-number Replay, so it passes either way (reproduced). The primary agent weakened it in the second round.
  3. The stored-winner note shows on Voided Games with the wrong reason.
  4. Live entry on a Voided current Game returns "draft complete".
- Standards findings:
  - Hard: ADR 0010 still says the next Game may follow a Voided one, with no amendment.
  - Judgement:
    - ADR 0034 line 13 is not marked as replaced.
    - "Current Game" is missing from CONTEXT.md.
    - Smells: repeated "Drafted or Closed" test; contiguity check outside `structural_error`; inline message switch; `void_game` return value unused; nested ternary in `App.tsx`.
- Fixes: none applied yet; awaiting developer decisions.

## PR #34 third round — 2026-11-27

**Developer decisions applied:**
- A Replay follows the same `series_ended` gate as an ordinary next Game, tested in both directions.
- BS-011 lock coverage is restored at the API and browser level.
- ADR 0010 and ADR 0034 are amended.
- The Voided-Game stored-winner note is corrected, and live entry on a Voided Game returns `game_voided`.
- "Drafted or Closed" is one function (`is_drafted_or_closed`), and the one-action-per-turn invariant is folded into `structural_error`.
- "Current Game" is added to `CONTEXT.md`.
- The remaining smells are added to #35.

**Run:**
- Time: 20:25:13Z–2026-11-27T20:40:26Z UTC, elapsed, including test waits.
- Agents and usage: the Claude Code primary agent (Opus 5.5) only. Primary-agent tokens and billing are unavailable.
- **First attempt: No.**
  - One new browser journey used a Series Format the profile does not allow (Fixed-length 3).
  - The same journey did not open the collapsed current Game before clicking Void.
  - Both were fixed in the journey; no product code changed.
- **Planned test changes:** two existing correction engine tests built drafts with gaps, which the folded one-action-per-turn invariant now rejects. They now record skipped bans before the pick, as live entry does, and one now asserts that a gap is rejected.

**Validation:**
- Python: 277 tests passed.
- Browser: 19 Playwright journeys passed.
- Static checks: Ruff, strict mypy, whitespace and the build passed.
- Mutation checks:
  - The restored BS-011 API test fails when voided Games lock later Games.
  - The Replay-gate journey fails without its UI guard.

## Claude Code review of PR #34 after the third round — 2026-11-27

[PR #34](https://github.com/thiagocamerato757/Nimbus/pull/34) was pushed at `c5f33d5` (`git push origin feat/issues-11-14`, using `gh` as a one-off credential helper). `sail-skills:code-review` then ran against `origin/dev...c5f33d5`: merge base `36a27a1`, 12 commits, 51 files. The developer's uncommitted `AGENTS.md`/`AI_SHOWCASE.md` edits were outside the diff.

- **Agents and usage:**
  - Claude Code primary agent (Opus 5.5), plus two parallel Claude reviewers.
  - Standards reviewer: 86,939 tokens, 111s.
  - Spec reviewer: 149,759 tokens, 380s.
  - Total: 236,698 tokens, reviewers only, as reported by the harness. The split, primary-agent tokens and billing are unavailable.
- **Time:** 20:44:20Z–20:51:32Z UTC, elapsed.
- **Verification:**
  - The Spec reviewer reproduced finding 1 with one scratch TestClient script against a temporary database.
  - The primary agent re-read `api.py:340-356` and this file's third-round section.
  - No suites were re-run. The last full runs (277 Python tests and 19 Playwright journeys, plus Ruff, strict mypy and the build) are recorded above.
- **Claude review status: completed, changes requested.**
- **Spec findings:**
  1. Starting a Game in an ended Series whose current Game is Voided returns `replay_required`, while `/replay` returns `series_ended` (reproduced). `replay_required` is checked before the ended gate.
  2. The Replay `series_ended` gate exists only at the API, not at the engine seam.
  3. A Game sent back to Drafting with a stored winner lists only "draft" as missing (nit).
  4. The Replay panel keeps the version captured when it opened, so another save while it is open makes every retry return `stale_version`. This dates from `7aee070`; it was read only.
  5. Minor: `replay-preview` never bumps the version, and an edit with only a holder clears the stored First Selection choice.
- **Standards findings:**
  - Hard: the third-round section above lacks PR, evidence and review-status links and its verification commands. This section supplies them. The "Not committed" line in the review-fixes section is out of date: those changes are in `2632f51`/`a3ec9dd`/`c5f33d5`.
  - Judgement calls:
    - `create_replay` checks the latest attempt by hand instead of using `current_game`.
    - `check_entry` has `game_voided`/`draft_complete` branches the API pre-empts.
    - `start_game` restates the `can_start_next` parts.
    - The UI copies `is_drafted_or_closed` and the Draft Position comparison.
    - In `derive_progress`, the list named `drafted` also holds Closed Games.
    - A Retired Character returns `unknown_character`.
    - `from error` and `from None` are mixed.
- **Fixes:** none applied; awaiting the developer.

## PR #34 fourth round — 2026-11-27

[PR #34](https://github.com/thiagocamerato757/Nimbus/pull/34). Developer decisions on the third review:

- **Spec 1, fixed at the root.**
  - The engine's ordered gate is `next_game_block`: `series_ended`, `replay_required`, `draft_incomplete`, then `series_full`.
  - `can_start_next` and `start_game` both use it.
  - `create_replay` uses `current_game` through `replay_block`.
  - The ADR 0010 wording is corrected.
- **Spec 2.** The ended gate holds at the engine seam for both starting and replaying.
- **Spec 3.** The missing list shows everything still needed to reach Closed. A stored winner that does not count yet is a note.
- **Spec 4.** A stale Replay setup reloads, rebases its version, lists what changed, and saves on the next try.
- **Spec 5.** Holder and choice go together: keeping the holder keeps the stored choice, and changing it clears the choice. The timeline form sends the choice only when changed.
- **Other.** The out-of-date "Not committed" line is corrected. The UI copies of server rules and the remaining judgement calls are in [#35](https://github.com/thiagocamerato757/Nimbus/issues/35).

**Run:**
- Time: 20:54:26Z–21:06:07Z UTC, elapsed.
- Agents and usage: the Claude Code primary agent (Opus 5.5) only. Primary-agent tokens and billing are unavailable.
- **First attempt: No.** A scripted edit dropped the `is_drafted_or_closed` import still used by the winner route. Ruff and mypy caught it before any test run, and it was restored.

**Validation:**
- `uv run --frozen pytest -q tests`: 285 passed.
- `npx playwright test`: 20 passed.
- `ruff check` and `ruff format --check`, `mypy`, `git diff --check` and `npm run build`: passed.
- Mutation check: the stale-Replay journey fails without the rebase.
- The new tests failed before their fixes, including the reproduced conflicting-rejection case.

**Claude review:** pending. Per the developer's stopping rule, the next review covers only this round's diff. If it has no reproduced Spec finding, PR #34 is merged and anything else goes to #35.

## Claude Code review of PR #34 fourth round — 2026-11-27

`sail-skills:code-review` ran on this round's diff only, `c5f33d5...e799c56`: commits `d521109`, `fd1b9e2` and `e799c56` of [PR #34](https://github.com/thiagocamerato757/Nimbus/pull/34). The fix issues are [#13](https://github.com/thiagocamerato757/Nimbus/issues/13) and [#14](https://github.com/thiagocamerato757/Nimbus/issues/14). The reviewers ran from 21:06:27Z to 21:10:27Z (session transcript); there was no handoff pause between the push and the review.

- **Agents and usage:**
  - Claude Code primary agent (Opus 5.5), plus two parallel Claude reviewers.
  - Standards reviewer: 63,631 tokens, 97s.
  - Spec reviewer: 82,266 tokens, 227s.
  - Total: 145,897 tokens, reviewers only, as reported by the harness. The split, primary-agent tokens and billing are unavailable.
- **Verification:**
  - The Spec reviewer reproduced findings 1–3, using a scratch Playwright config and a scratch pytest with temporary data.
  - The primary agent re-read `App.tsx` `rebaseReplay`, the 1-second poll in `useLiveQuery.ts`, and `api.py` `edit_first_selection`.
- **Claude review status: completed, changes requested.**
- **Stopping rule:** there are reproduced Spec findings, so PR #34 was **not** merged.
- **Spec findings:**
  1. **Stale Replay panel (reproduced).** It usually shows no changes. Its baseline is the current render's Series, which the 1-second poll has already updated. The committed journey passes only because it clicks within about a second, so it is timing-dependent.
  2. **Timeline First Selection form (reproduced).** It still shows the old choice after the holder changes, but the save stores no choice. The analyst can't record "B chose side" in one save.
  3. **Choice saved with no holder (reproduced).** It is accepted, then cleared when a holder is first added.
  4. Read only: the spec says "one engine gate", but `replay_block` repeats the ended check.
  5. Read only: no engine test pins the `series_full` position in the gate order.
- **Standards findings:**
  - Hard: the fourth-round record lacks issue links (#13/#14), commit evidence and the pause/handoff note; this section supplies them. The time formats are also mixed.
  - Judgement calls:
    - `replay_block` duplicates the ended check, and `next_game_block` computes the gate twice.
    - `GATE_MESSAGES` also holds a copy rule.
    - The `replay_unavailable` text differs between the API and `i18n.ts`, and the i18n text uses the non-glossary word "attempt".
    - The holder/choice rule lives in the route.
    - `save()` grew a fifth positional parameter.
- **Fixes:** none applied; awaiting the developer.

## PR #34 fifth round — 2026-11-27

[PR #34](https://github.com/thiagocamerato757/Nimbus/pull/34). The fix issues are [#13](https://github.com/thiagocamerato757/Nimbus/issues/13) and [#14](https://github.com/thiagocamerato757/Nimbus/issues/14). Remaining smells are in [#35](https://github.com/thiagocamerato757/Nimbus/issues/35).

**Pause and handoff:** the fourth-round reviewers finished at 21:10:27Z. The developer's decisions arrived, and this round started at 21:14:16Z. No agent ran in between.

**Developer decisions applied:**
- **Finding 3, option A.** A choice always belongs to a holder. `record_first_selection` is one engine rule used by Start Game, Replay and timeline edits, and a choice without a holder is rejected everywhere with `choice_without_holder`.
- **Finding 2.** The UI disables the choice until a holder is selected and clears it when the holder changes.
- **Finding 1.** The stale Replay setup compares against its own baseline, the Series as it was when the setup opened or last rebased. Its journey waits until the live refresh shows the other edit.
- **Gate.** `replay_block` reuses the ordered next-Game gate, the Series outcome is computed once, and an engine test pins `series_full` last.
- **Text.** The `replay_unavailable` text uses glossary terms in both the API and the UI.

**Run:**
- Time: 21:14:16Z–21:26:13Z UTC, elapsed.
- Agents and usage: the Claude Code primary agent (Opus 5.5) only. Primary-agent tokens and billing are unavailable.
- **First attempt: No.** My new stale-panel assertion expected the generic stale-edit error. The successful preview reload clears that error, and the panel's change notice replaces it, so the assertion now checks the notice.
- **Planned test change:** the First Selection journey no longer selects a choice after clearing the holder, because that field is now disabled.

**Validation:**
- `uv run --frozen pytest -q tests`: 290 passed.
- `npx playwright test`: 20 passed.
- `ruff check` and `ruff format --check`, `mypy`, `git diff --check` and `npm run build`: passed.
- Mutation check: with the screen's Series as the baseline, the stale-panel journey fails.
- The new tests failed first.

**Evidence:** commits [`0a536d8`](https://github.com/thiagocamerato757/Nimbus/commit/0a536d8), [`c0d8133`](https://github.com/thiagocamerato757/Nimbus/commit/c0d8133) and [`8162e0e`](https://github.com/thiagocamerato757/Nimbus/commit/8162e0e).

**Claude review:** pending; it covers this round's diff only, under the same stopping rule.

## Claude Code review of PR #34 fifth round — 2026-11-27

`sail-skills:code-review` ran on this round's diff only, `e799c56...8162e0e`: commits [`0a536d8`](https://github.com/thiagocamerato757/Nimbus/commit/0a536d8), [`c0d8133`](https://github.com/thiagocamerato757/Nimbus/commit/c0d8133) and [`8162e0e`](https://github.com/thiagocamerato757/Nimbus/commit/8162e0e) of [PR #34](https://github.com/thiagocamerato757/Nimbus/pull/34), for issues #13 and #14.

- **Time:** 21:26:32Z–21:30:12Z UTC, about 3m 40s elapsed. There was no pause between the push and the review.
- **Agents and usage:**
  - Claude Code primary agent (Opus 5.5), plus two parallel Claude reviewers.
  - Standards reviewer: 59,680 tokens, 73s.
  - Spec reviewer: 78,921 tokens, 199s.
  - Total: 138,601 tokens, reviewers only, as reported by the harness. The split, primary-agent tokens and billing are unavailable.
- **Verification:**
  - The Spec reviewer ran the 3 new pytest tests (5 passed) and two scratch Playwright journeys with their own temporary data directory. These reproduced findings 1 and 2.
  - The primary agent re-read `App.tsx:76-78` and `App.tsx:487`.
- **Claude review status: completed, changes requested.** There are reproduced Spec findings, so PR #34 was **not** merged.
- **Spec findings:**
  1. **"B chose side" still cannot be recorded in one save when A had chosen side (reproduced).** The timeline form sends the choice only when it differs from the stored one, so the engine sees a new holder and clears it.
  2. **A choice survives when a pre-filled holder changes (reproduced, setup form).** A live refresh changes the shown holder without the analyst's input, so the setup could record "A chose side", which nobody entered. The Replay setup has the same pattern (read only).
  3. Read only: a legacy holderless choice makes an empty API edit fail with `choice_without_holder`.
- **Standards findings:**
  - Hard: the fifth-round record names its evidence without commit links, and the fourth review lacks an end time with seconds.
  - Judgement calls:
    - `choice_without_holder` is an absolute rule without an ADR note (ADR 0010: "Only Structural Invariants are absolute").
    - The spec bullet has no "(amends …)" tag.
    - `_Outcome` mirrors `SeriesProgress` under other names.
    - `record_first_selection` takes a field-name dict.
    - `except ValueError` maps every error to one message.
    - The controlled/uncontrolled branching in `FirstSelectionFields` is repeated per field.
- **Fixes:** none applied; awaiting the developer.

## PR #34 sixth round — 2026-11-27 to 2026-11-28

[PR #34](https://github.com/thiagocamerato757/Nimbus/pull/34), issues [#13](https://github.com/thiagocamerato757/Nimbus/issues/13) and [#14](https://github.com/thiagocamerato757/Nimbus/issues/14); remaining smells in [#35](https://github.com/thiagocamerato757/Nimbus/issues/35).

**Developer decisions applied:**
- The UI sends holder and choice exactly as displayed.
- The setup and Replay forms take their pre-fill once, when they open. A later result is offered with Apply, and only Apply or the analyst changes a field.
- An edit is rejected only when it would create a choice without a holder. Migration 10 clears stored ones, logging each, after a verified backup.
- "Choice without holder" is a Structural Invariant (ADR 0009 and 0010 amendments). The spec bullet has its "(amends …)" tag.

**Run:**
- Time: 2026-11-27T21:32:52Z to the review start, UTC.
- **Pause:** 2026-11-27T21:32:52Z–2026-11-28T02:23:41Z (4h 50m 48s), with no commands, until the developer sent "continue".
- Agents: the Claude Code primary agent only (Sonnet 5.5).
- **First attempt: No.** A scripted engine edit did not match the formatted source and wrote nothing, so it was redone. Lint then asked for combined `with` statements in the new migration test.
- Planned test change: the coupled-profile journey expected a background result to change the holder, which this round reverses. It now expects the offer and applies it.

**Validation:**
- `uv run --frozen pytest -q tests`: 293 passed.
- `npx playwright test`: 22 passed.
- `ruff check`, `ruff format --check`, `mypy`, `git diff --check` and `npm run build`: passed.
- The new engine, migration and journey tests failed first. The new journeys also fail against the previous `App.tsx`.

## Primary-agent usage for the PR #34 review and fix rounds

Source: session transcript `08b0379a-9ce6-4010-9823-48089e53b9dc`, with each provider response counted once by message id. This replaces the "primary-agent tokens unavailable" notes above. Subagent figures stay as reported in each section, and billing and credits are unavailable. Input is uncached input plus cache writes plus cache reads.

| Interval (UTC, 2026-11-27) | Work | Input | of which cache read | Output |
|---|---|---|---|---|
| 19:30:00–19:41:52 | First review (includes the interrupted attempt) | 1,021,744 | 874,870 | 17,433 |
| 19:41:52–20:10:00 | Fix round 1 | 10,289,213 | 10,114,199 | 77,850 |
| 20:10:00–20:25:13 | Fix round 2 and review | 4,222,886 | 4,186,420 | 28,611 |
| 20:25:13–20:44:20 | Fix round 3 | 7,348,335 | 7,310,185 | 30,255 |
| 20:44:20–20:54:26 | Review after round 3 | 2,387,802 | 2,372,039 | 15,669 |
| 20:54:26–21:06:07 | Fix round 4 | 5,168,943 | 5,134,809 | 29,347 |
| 21:06:07–21:14:16 | Review of round 4 | 1,955,488 | 1,941,096 | 10,943 |
| 21:14:16–21:26:14 | Fix round 5 | 4,477,419 | 4,456,755 | 19,478 |
| 21:26:14–21:32:52 | Review of round 5 | 2,049,425 | 1,679,494 | 13,954 |

## Claude Code review of PR #34 sixth round — 2026-11-28

`sail-skills:code-review` ran on this round's diff only, `8162e0e...36fb724`: commits [`bb85bf2`](https://github.com/thiagocamerato757/Nimbus/commit/bb85bf2), [`06d67fd`](https://github.com/thiagocamerato757/Nimbus/commit/06d67fd) and [`36fb724`](https://github.com/thiagocamerato757/Nimbus/commit/36fb724) of [PR #34](https://github.com/thiagocamerato757/Nimbus/pull/34), for issues #13 and #14.

**Completion of the sixth-round record:**
- Elapsed: 2026-11-27T21:32:52Z–2026-11-28T02:37:12Z (5h 4m 20s). Excluding the 4h 50m 48s pause, 13m 32s.
- Primary-agent usage: 5,441,684 input tokens, of which 5,048,785 cache read, and 22,943 output (session transcript, each response once). No subagents. Billing and credits are unavailable.
- Evidence: the three commits above.

**Review run:**
- Time: 02:37:20Z–02:40:54Z UTC, about 3m 34s.
- Reviewers (session transcript):
  - Standards: 308,013 input, of which 220,655 cache read, and 5,656 output.
  - Spec: 735,188 input, of which 639,252 cache read, and 14,947 output.
- Primary agent during the review, up to this record: 816,976 input, of which 808,620 cache read, and 4,248 output. Billing and credits are unavailable.
- Verification: the Spec reviewer ran a two-test scratch Playwright probe with its own data directory and ports, reproducing both findings. The primary agent re-read `App.tsx` `launchGame` and the Apply handler. No suites were re-run.
- **Claude review status: completed, changes requested.** There are reproduced Spec findings, so PR #34 was **not** merged.

**Spec findings:**
1. "Record winner and start" can change the shown holder without clearing the choice, so a choice the other Team's holder never made is saved (reproduced).
2. After Apply, "Record winner and start" treats the holder as a manual pick, so it starts at once without showing the new pre-fill (reproduced; depends on interpretation).
- The primary agent also notes that the spec sentence letting "Record winner and start" take the new pre-fill by itself was its own interpretation, not a developer decision.

**Standards findings:**
- Hard: the sixth-round record lacked elapsed time, usage, evidence links and review status; supplied above.
- Judgement calls:
  - "Suggestion" is a glossary term for Copilot options and is reused here for the pre-fill.
  - The two forms repeat the offer-and-apply logic.
  - The setup form's reset is split between render and an effect.

**Fixes:** none applied; awaiting the developer.

## PR #34 seventh round — 2026-11-28

[PR #34](https://github.com/thiagocamerato757/Nimbus/pull/34), issues [#13](https://github.com/thiagocamerato757/Nimbus/issues/13) and [#14](https://github.com/thiagocamerato757/Nimbus/issues/14); remaining smells in [#35](https://github.com/thiagocamerato757/Nimbus/issues/35).

**Developer decision (option A):** only the analyst's own change or Apply moves the holder. A different First Selection pre-fill from "Record winner and start" starts no draft and is offered. The spec sentence about an automatic update, which the primary agent had added without a decision, is removed.

**Changes:**
- One reducer (`frontend/src/firstSelectionForm.ts`) holds the logic of the setup, Replay and timeline forms. The timeline form uses it too, so the choice-clearing rule exists once.
- Vitest added with 15 unit tests (`npm run test:unit`).
- "Suggestion" renamed to "First Selection pre-fill"; the term is added to `CONTEXT.md`.
- The sixth review record was committed first, in `f2bf985`.

**Run:**
- Time: 2026-11-28T02:45:07Z–2026-11-28T02:54:19Z, 9m 12s elapsed. No pause.
- Agents: the Claude Code primary agent only (Sonnet 5.5).
- Usage: 4,783,484 input tokens, of which 4,756,742 cache read, and 18,983 output (session transcript, up to this record). Billing and credits are unavailable.
- **First attempt: No.** One new journey changed a winner from outside after the analyst had edited the form, so the save was correctly rejected as stale; the journey's step order was fixed.
- Planned test change: the "Record winner and start" journey expected the automatic holder update, which this round removes.

**Validation:**
- `npm run test:unit`: 15 passed. They failed before the module existed, and three planted reducer bugs are each caught.
- `npx playwright test`: 24 passed.
- `uv run --frozen pytest -q tests`: 293 passed.
- `ruff check`, `mypy`, `git diff --check` and `npm run build`: passed.

**Claude review:** pending; it covers this round's diff only, under the same stopping rule.

## Claude Code review of PR #34 seventh round — 2026-11-28

`sail-skills:code-review` ran on this round's diff only, `36fb724...027ff52`: commits [`f2bf985`](https://github.com/thiagocamerato757/Nimbus/commit/f2bf985), [`0a651dd`](https://github.com/thiagocamerato757/Nimbus/commit/0a651dd), [`40065a7`](https://github.com/thiagocamerato757/Nimbus/commit/40065a7) and [`027ff52`](https://github.com/thiagocamerato757/Nimbus/commit/027ff52) of [PR #34](https://github.com/thiagocamerato757/Nimbus/pull/34). `0a651dd` and `40065a7` are the evidence for the seventh round.

- **Time:** 02:54:32Z–02:57:21Z UTC, about 2m 49s.
- **Usage (session transcript):**
  - Standards reviewer: 305,349 input, of which 235,236 cache read, and 5,459 output.
  - Spec reviewer: 515,818 input, of which 423,917 cache read, and 16,128 output.
  - Primary agent from the review start to this record: 901,201 input, of which 891,306 cache read, and 5,269 output.
  - Billing and credits are unavailable.
- **Verification:** the Spec reviewer ran a four-test scratch Playwright probe with temporary data (4 passed). The primary agent re-read the notice reset in `App.tsx`.
- **Claude review status: completed. No reproduced Spec violation**, so the developer's stopping rule allows the merge.
- **Sent to [#35](https://github.com/thiagocamerato757/Nimbus/issues/35):**
  - One reproduced cosmetic issue: the "draft has not started" notice stays after the analyst picks the offered holder by hand.
  - Two interpretation-dependent Spec observations and the Standards findings.
