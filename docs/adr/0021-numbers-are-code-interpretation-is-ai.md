# Numbers are code, interpretation is AI

A report with an invented figure is worse than no report, so Scout extends [ADR 0002](0002-rules-are-code-judgment-is-ai.md) to statistics: code computes every count, rate, ranking and sample size, and the LLM never calculates or types a figure. This is enforced by structure rather than by checking claims in prose.

- A report is a list of blocks. In an **Observation** block the LLM only selects statistic ids and a code template renders the sentence. An **Interpretation** block is LLM free text that must cite at least one supporting statistic.
- Free text contains no digits: figures and Games are placeholders (`{stat:<id>}`, `{game:<id>}`) that Nimbus renders, with a small allowlist in the Title profile for game terms such as "level 6".
- Spelled-out numbers from two upwards are rejected like digits, in every language a report can be written in, not only English. Vague quantifiers cannot be caught by code, so each interpretation shows its cited statistics beside it.
- An unknown statistic id, an unsupported interpretation or a stray number rejects the output, which is retried.
- Code flags statistics below a minimum sample size (a profile setting); an interpretation supported only by those is marked low confidence for the coach.
- "Ask the report" answers uncovered questions through predefined, parameterised query tools (Team, Side, Draft Position, conditions such as "after losing the previous Game"). Results get statistic ids like any other; the LLM may combine queries but never computes.
- Every cited statistic shows its value and sample size and opens to the Games behind it. Statistics pages work without any LLM.

## Considered Options

- The LLM computes from match rows: unreliable arithmetic.
- Code computes and the LLM writes prose with figures: nothing stops a wrong figure reaching the coach.
