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
