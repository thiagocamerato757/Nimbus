# All statistics go through one parameterised query layer

Every figure in Nimbus (statistics pages, copilot, and later reports and "Ask the report") comes from one query layer parameterised by Team, Side, Draft Position, scope filters and conditions, returning each result with a statistic id, sample size and the Games behind it. Separate one-off calculations would block "Ask the report" and let figures disagree. Conditions include the opponent ("Games against Team X" and opponent-side conditions generally), so a question stays about one Team while asking how it drafts against us.

A fixed sample history with hand-computed expected results is kept as golden tests, so a broken formula is caught before it reaches a page, the copilot or a report.

Limits for "Ask the report": one Team per question; only what the query tools express, otherwise it says it cannot answer; read only; a cap on tool calls per question; no SQL written by the LLM.
