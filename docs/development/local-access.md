# Local requests and concurrent tabs

Nimbus serves one local Workspace. Run the backend on `127.0.0.1:8000` and
Vite on `127.0.0.1:5173` using the commands in the README. Open
`http://localhost:5173` or `http://127.0.0.1:5173`.

## Windows browser with WSL2

Run both commands inside WSL2, keeping `NIMBUS_DATA_DIR` on the Linux filesystem
(for example `~/.local/share/nimbus`). Open `http://localhost:5173` in Windows Edge
or Chrome. WSL2 localhost forwarding connects Windows to the loopback servers;
no LAN address, port proxy, or `0.0.0.0` binding is needed. If localhost forwarding
has explicitly been disabled in `%UserProfile%\.wslconfig`, enable
`localhostForwarding=true` in its `[wsl2]` section, run `wsl --shutdown` from
PowerShell, and restart the two servers. Do not change Nimbus to a LAN binding.

To check the setup, create a Series in the Windows browser, open its board in a
second tab, and record an entry. Both tabs must show the entry without reload.
Preparing a Character selection in the second tab before recording in the first
must produce an outdated-edit notice if submitted afterwards. The analyst can
review the refreshed board, reselect the Character, and submit again.

## Shared API contract

`LocalAccess` checks every HTTP request before handlers run. The only allowed
Hosts are `localhost` and `127.0.0.1`, with no port or ports 5173/8000. When Origin
is present it must be exactly `http://localhost:5173`, `http://127.0.0.1:5173`,
`http://localhost:8000`, or `http://127.0.0.1:8000`. Missing Origin is permitted
for local CLI clients. Every method other than GET, HEAD and OPTIONS requires
`X-Nimbus-App: 1`. There is no CORS middleware; foreign preflights are rejected.
The frontend always uses relative `/api` URLs through the Vite same-origin proxy.

Upgrading an existing v1 Workspace first creates a SQLite online backup under
`backups/automatic-migration-*.sqlite3` and checks its integrity. A failed check
stops startup before migration. The latest ten automatic migration backups are
kept; manual backups are not removed. A fresh empty database needs no migration
backup.

Every API snapshot returns `X-Nimbus-Version`. A mutation sends the version of
the state on which its input was based in that same header. Missing, malformed,
or stale versions receive 409 `stale_version`. This is a Workspace-wide revision:
a change anywhere may require another tab's prepared edit to be reviewed.

The shared `Workspace` middleware starts a SQLite snapshot for reads and an
immediate transaction for writes. It checks the version, runs the handler, and
increments the revision in the same transaction; failed writes roll back. The
response is sent only after commit. Independent server processes sharing the
same database cannot both accept edits based on one version. New API handlers
must use the app's Store, which joins this request transaction; do not open an
independent database connection from a handler. This buffered response contract
is for finite JSON API responses, not streaming endpoints.

Frontend screens use `useLiveQuery` for versioned snapshots, polling once a
second while connected and refreshing on focus. Failed polling displays a
connection error and retries. Timer throttling in a background/suspended browser
may delay updates until the tab runs again. Older responses cannot replace a
newer revision. Prepared input retains its original version even when the board
refreshes, and stale submissions display a notice. New screens should use this
hook and `requestSnapshot`, and capture the snapshot version when preparing input.

## Verification

`tests/test_local_access.py` exercises BS-026 through the real API and temporary
SQLite. Its simultaneous-edit case uses two independent app instances sharing
one database. `frontend/e2e/local-access.spec.ts` checks two real browser tabs,
automatic updates, preservation of prepared input's version, the stale notice,
and successful deliberate resubmission.

On 2026-11-26, Windows Edge 158.0.4370.45 opened `http://localhost:5173`
against the WSL2 servers and rendered the React screen with the API-loaded
League of Legends profile. This verifies opening and API reads from Windows;
the full entry/two-tab/stale-notice journey was verified in Linux Chromium.
To reproduce the Windows opening check after starting both servers, run from
PowerShell in the repository:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows-localhost-smoke.ps1
```

The script uses an isolated temporary Edge profile, prints the UTC timestamp,
browser version and rendered DOM, and fails if the API-loaded profile is absent.
It leaves its temporary DOM and browser diagnostics under `%TEMP%`.
