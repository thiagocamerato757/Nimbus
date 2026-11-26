# Nimbus listens on 127.0.0.1 only, with no login and defences against other websites

This bounds [ADR 0005](0005-local-single-user-app.md). There are no accounts: a coach watches the analyst's screen or a mirrored display.

- Bind `127.0.0.1` explicitly, never `0.0.0.0`. Under WSL2 the browser is usually on Windows, where localhost forwarding reaches `127.0.0.1`, while `0.0.0.0` can expose the port to the local network in some WSL networking modes. "Open from the Windows browser" is documented and tested as part of the supported setup.
- Any web page open in the user's browser can try to call a local server, so requests are checked for `Host` and `Origin`, every state-changing request (draft entry, import, LLM call) also requires a custom application header that a cross-site page cannot send without a preflight the server rejects, and there is no wildcard CORS.
- LLM API keys stay server-side and are never sent to the frontend; settings only show whether one is configured.
- One Workspace per data folder. Several tabs or windows on the machine are fine: the server holds the truth, tabs update, and an edit from an outdated tab is rejected rather than overwriting.
- Everything except a hosted LLM works offline. Nimbus is run from source, with no installer; Linux including WSL with a current browser is supported, other systems are untested.

## Considered Options

- Access from the local network: needs authentication and encrypted connections.
