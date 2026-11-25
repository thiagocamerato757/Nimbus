# Nimbus

**From scouting to the last pick of the series: a coaching workspace for competitive Fearless Draft.**

Nimbus helps professional coaching staffs prepare for and run a Fearless Draft series without spreadsheets. It combines a deterministic draft rules engine with AI agents that scout opponents and suggest picks and bans, and every suggestion is checked against the rules before it reaches the coach.

> Built for the **Cloud9 x JetBrains "Sky's The Limit" Hackathon 2026**, Category 2: Macro Scouting & Draft Management System.

---

## Why Nimbus

In Fearless Draft, a champion played in one game of a series is locked for the remaining games. Over a best-of-five, every pick you make today shrinks your options tomorrow, and your opponent's options shrink too. Coaches currently track this by hand in spreadsheets, while also preparing scouting notes in separate documents.

Nimbus brings both moments of the coach's job into one place:

| Phase | Module | What it does |
|---|---|---|
| **Before the series** | **Nimbus Scout** | An AI agent analyzes the opponent's match data and writes a scouting report. |
| **During the series** | **Nimbus Draft** | A Fearless-aware draft board with an AI copilot that suggests picks and bans. |

What Scout learns about the opponent feeds directly into Draft's suggestions.

---

## Features

### Nimbus Draft: Fearless draft room
- **Fearless rules engine.** Tracks picks and bans for every game of a series and shows which champions are locked. Supports configurable rule variants:
  - *Hard Fearless*: a champion picked in an earlier game is locked for **both** teams.
  - *Soft Fearless*: a champion is locked only for the team that picked it.
- **Champion pools.** Each player's pool, with how much of it remains available in the current series (e.g. *mid laner: 6 champions in pool, 3 used, 3 remaining*).
- **Draft copilot.** Suggests the next pick or ban and explains why. The copilot never decides legality itself: it queries the rules engine through tool calls, so it cannot recommend a locked champion.
- **Series timeline.** Game-by-game view of picks, bans, and locked champions.

### Nimbus Scout: opponent scouting
- **Automated scouting report.** Most-picked and most-banned champions, pick priority, and side-specific patterns for a chosen opponent.
- **Ask the report** *(planned)*. Follow-up questions in natural language, answered by an agent that queries the underlying data.

### Planned
- Export the draft plan (PDF/image) for team meetings.
- Opponent pool forecasting: predict what the opponent has left for games 4 and 5.

---

## Architecture

```
┌───────────────────────────┐        ┌──────────────────────────────────────┐
│  Frontend (React)         │  HTTP  │  Backend (Python / FastAPI)          │
│  - Draft board            │◄──────►│  - Fearless rules engine (pure code) │
│  - Series timeline        │        │  - Data layer (GRID / CSV import)    │
│  - Scouting report view   │        │  - AI agents (Scout, Draft copilot)  │
└───────────────────────────┘        │      └─ tools → rules engine, data   │
                                     └──────────────────────────────────────┘
```

**Design principle:** rules are code, judgment is AI. Legality (what can be picked) is decided by a deterministic, unit-tested engine. The language model handles reasoning and explanation, and it can only act through tools that the engine validates.

---

## Data

- **GRID esports data** (official hackathon data, optional) for match history, picks, and bans.
- **CSV import** as a fallback, so pools and match history can be loaded without API access.

---

## Getting started

>Work in progress. Setup instructions will be completed as the project is built.

### Requirements
- Python 3.12+ with [uv](https://docs.astral.sh/uv/)
- Node.js 20+
- An API key for the LLM provider (see `.env.example`)

### Backend
```bash
cd backend
uv sync
cp .env.example .env   # fill in your keys
uv run fastapi dev app/main.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Tests
```bash
cd backend
uv run pytest
```

---

## Built with JetBrains tools

| Tool | How it was used |
|---|---|
| **PyCharm** | Main IDE for the backend and the rules engine. |
| **JetBrains Air** | Agentic development environment: implementation tasks were delegated to coding agents running in parallel, each in an isolated worktree, and reviewed in Air before merging. |

The full story of the AI-assisted workflow, including which agent handled which task and how much it cost, is in [`AI_SHOWCASE.md`](AI_SHOWCASE.md).

---

## Project status

- [ ] Fearless rules engine + tests
- [ ] Champion pools and series tracking
- [ ] Draft board UI
- [ ] Draft copilot (tool-calling agent)
- [ ] GRID data integration / CSV import
- [ ] Scouting report agent
- [ ] Demo video

---

## License

Released under the [MIT License](LICENSE).

## Legal

Nimbus isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games, and all associated properties are trademarks or registered trademarks of Riot Games, Inc.

Nimbus is an independent hackathon project and is not an official product of Cloud9 or JetBrains.
