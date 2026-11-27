# Open questions before the spec

## 1. Decide before the spec (changes scope or data model)

- [x] 1.1 Scope: MVP spec for milestones 1-3, see [mvp-scope.md](mvp-scope.md). 1.2-1.4 only need to confirm the MVP data model does not block them
- [x] 1.2 External data API: MVP model not blocked (ADR 0027). Provider, free-tier contents and eligibility go to the milestone 6 spec; dropping milestone 6 is acceptable
- [x] 1.3 Forecasting: MVP model not blocked, given the optional Fearless variant and tournament mapping. Code computes it, labelled as an estimate
- [x] 1.4 "Ask the report": MVP model not blocked; the MVP builds one parameterised query layer with golden tests (ADR 0028)
- [x] 1.5 Coach input: Flags and short Notes, in the MVP (ADR 0029)
- [x] 1.6 LLM: Claude and OpenAI-compatible adapters, limits, caching, privacy (ADR 0030, 0031)
- [x] 1.7 Storage: SQLite, backups and retention (ADR 0032)
- [x] 1.8 Single user and local: loopback only, request checks (ADR 0033)

## 2. Decide during implementation, in the ticket that needs it

- Exact CSV column names, date format, encoding and delimiter
- Initial League of Legends Character Catalog: where it comes from and how it is updated
- Default values: minimum sample size, material-change rate, Role majority, shortlist bands, report Game count, timer seconds
- Exact formulas: presence, pick rate, win rate, pick priority, recency, "comparable options"
- Which Games feed the copilot's statistics for each Team (scrims included or not)
- LLM timeouts and retry limit, and what the coach sees when retries run out
- Integration test against a local OpenAI-compatible server: in CI if feasible, otherwise a manual check
- Handling a model refusal response, and fallback behaviour
- `max_tokens` value per Model Role (tight, but leaving room for the model's thinking), and how the input upper bound is computed from the prompt
- Verify the minimum cacheable prompt length and cache prices in the provider's docs; measure real cache hit rate
- Cost limit for report generation, which is not tied to a Series (milestone 4)
- Check provider data retention terms before real team data is used
- Whether removing a Source must also clear Suggestion Log entries and saved report content derived from it
- Spelled-out number lists and Observation templates in English and pt-BR; digit allowlist
- [x] Override reasons (#10): Official ruling, Profile mismatch, Earlier entry was wrong, Other. A note is optional except for Other, which requires a nonblank note. Two Profile mismatch Overrides for the same rule within one Series show advice to update the Title profile.
- Timer start, reset and display
- What is pre-filled when replaying a Voided Game
- Changing a Series Format after Games exist
- Undoing a wrong alias, "same Player" or "same Game" answer
- Recording live a Game that was already imported
- Which Flag wins when several apply to one Character; evaluating "until patch X" when the Series has no patch
- Confirm the built-in live Source cannot be removed as a whole
- Available Now when a profile allows the same Character twice in a Game
- The turn budget the milestone 3 latency prototype measures against
- Verify First Selection default against league rulebooks (unconfirmed)
- README "Getting started" commands once code exists
- AGENTS.md has no architecture or agent rules yet, although AI_SHOWCASE.md says it does

## For the milestone 4 spec (report and "Ask the report")

- List of query tools and conditions, tool-call cap value, whether conversations are saved, whether follow-ups keep context, use during a live Series

## For the milestone 5 spec (forecasting)

- Outputs per opponent Player: Remaining Pool for a future Game ranked by frequency and recency, optionally assuming picks in between. Code only, labelled an estimate with sample sizes
- Ranking formula, use of likely bans, how far ahead to project
- Log every forecast made during a live Series, like the Suggestion Log, and check forecasts against what happened
- Games without a variant or Game number are used without lock context, and counted

## For the milestone 6 spec (external data API)

- Provider, whether its free tier includes picks and bans, eligibility. Dropping the milestone is acceptable

## 3. Future ideas, out of scope

See [future-ideas.md](future-ideas.md), plus: Deadlock profile (and its presets), plan export (PDF/image), accounts and multiple users.
