# Cost is limited per Series, computed from reported usage, with prompts built for caching

- The price table lives in a configuration file, not code. Cost is computed from the token usage the API reports on each response, including cache reads and writes, never estimated.
- Priced models (those with an entry in the table) have a dollar limit per Series, default $10, counting every call including cancelled and retried ones: warn at 80%; at 100% LLM enrichment stops, the Shortlist continues and one click raises the limit. For unpriced (local) models the limit is optional and expressed in tokens per Series.
- Every copilot prompt puts stable content first (profile rules, opponent statistics, pools, Flags, Notes) and changing draft state last, with the stable prefix marked for caching. Anything that changes during a draft, such as Available Now, belongs to the draft state. The same order helps local servers that reuse prompt prefixes.

Caching saves less than the per-call figure suggests in some cases: the default cache lasts 5 minutes from the last use, so it lapses between Games; writing it costs 1.25 times the input price; and each model has its own cache, so an occasional manual refresh will often find it cold.

## Amendment (2026-11-26): costing requests with missing usage

This is the one exception to "never estimated". The limit may overcount but must never undercount, and cancellation is never delayed for the sake of accounting.

- Requests are streamed. Reported usage is used whenever it arrives.
- Before sending, Nimbus computes a conservative upper bound for input tokens from the prompt itself. A request cancelled before the provider reports its input usage is charged that bound; one cancelled without reporting its output usage is charged `max_tokens` of output. Both are labelled as upper bounds. An attempt that fails after being sent without reporting usage is charged the same way.
- Automatic retries in client libraries are disabled. Nimbus retries itself and records every attempt in the cost ledger.
- `max_tokens` is set per Model Role and kept tight.
- An input bound is priced at the highest input rate that could apply to it (cache writes cost more than plain input).

This holds for any provider, so the OpenAI-compatible adapter needs no special case. Each adapter's actual reporting is checked in the adapter ticket.
