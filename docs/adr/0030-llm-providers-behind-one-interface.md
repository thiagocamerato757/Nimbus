# Claude and OpenAI-compatible providers sit behind one internal LLM interface

Real team data is sensitive and live turns are latency-bound, so Nimbus must not depend on one hosted provider.

- Two adapters: **Anthropic** (official Python SDK) for Claude, and **OpenAI-compatible HTTP** (base URL and model name), which covers Ollama, llama.cpp server and NVIDIA NIM with one integration. Claude is not called through the compatible adapter. Tests use a fake model.
- Provider and model are chosen per **Model Role**, per Workspace: prepared suggestions (default Claude Haiku 5.5, fast and cheap), manual refresh (default Claude Opus 5.5 at low effort) and reports. Latency is the binding constraint on a live turn; the Suggestion Log shows which pairing works.
- Each configured model **declares** tool calling, structured (JSON schema) output and context length, verified by a small test call at startup. Without reliable tool calling or structured output, LLM enrichment and "Ask the report" are disabled for that model and the code Shortlist continues. A failed check never blocks the app.
- Settings state per provider whether data leaves the machine, and exactly what is sent. This follows from the **base URL, not the adapter**, because an OpenAI-compatible endpoint (including NIM) can be hosted remotely: only a loopback address counts as staying on the machine. A local model is the recommended setup for real team data.
- Only what a request needs is sent (draft state, computed statistics, pools, Flags, Notes, Team and Player names), never import files or the database. Names are not anonymised, since statistics and pools usually identify a team anyway. An "LLM off" switch leaves the Shortlist working.
- API keys are read from the environment, never stored in the database or the repository.
