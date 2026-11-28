# Agents

## Agent skills

### Issue tracker

Issues are tracked in GitHub Issues for thiagocamerato757/Nimbus, using the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one root `CONTEXT.md` plus `docs/adr/`. See `docs/agents/domain.md`.

## Implementation and review records

For every implementation or code review, start recording UTC timestamps and usage counters before work begins. Track elapsed execution time, pauses and handoffs, primary-agent and subagent usage, input/output/cache tokens, available credits or cost, verification commands/results, and unplanned retries or fixes. Preserve the scope and source of each measurement; mark unavailable billing data explicitly.

Before reporting completion, update `AI_SHOWCASE.md` with the task, agent roles, first-attempt outcome, fixes, measured time and usage, validation results, and issue/PR/evidence links. Use counter deltas for the task, count each provider response once, and identify cached input already included in token totals. Distinguish worker-only measurements from total task effort.

At implementation closeout and after a Codex code review, remind the developer to run `sail-skills:code-review` in Claude Code against the branch's base or the reviewed PR range before merging. Record the Claude review status in `AI_SHOWCASE.md` when results are available.

The developer waived an additional Claude Code review for the completed PRs #31 and #32 and their correction in #33, accepting the recorded Codex review. Apply the reminder to subsequent work.
