# Cost is limited per Series, computed from reported usage, with prompts built for caching

- The price table lives in a configuration file, not code. Cost is computed from the token usage the API reports on each response, including cache reads and writes, never estimated.
- Priced models (those with an entry in the table) have a dollar limit per Series, default $10, counting every call including cancelled and retried ones: warn at 80%; at 100% LLM enrichment stops, the Shortlist continues and one click raises the limit. For unpriced (local) models the limit is optional and expressed in tokens per Series.
- Every copilot prompt puts stable content first (profile rules, opponent statistics, pools, Flags, Notes) and changing draft state last, with the stable prefix marked for caching. Anything that changes during a draft, such as Available Now, belongs to the draft state. The same order helps local servers that reuse prompt prefixes.

Caching saves less than the per-call figure suggests in some cases: the default cache lasts 5 minutes from the last use, so it lapses between Games; writing it costs 1.25 times the input price; and each model has its own cache, so an occasional manual refresh will often find it cold.
