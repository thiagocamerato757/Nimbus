# Data lives in one SQLite file, backed up through SQLite itself

One local user needs no database server, and a single file is easy to copy. Title profiles stay as YAML files.

- Everything the app writes is in the database: Series and Draft Actions with edit history, Rosters and pools, imported records, aliases and identity answers, Flags and Notes, the Suggestion Log and Workspace settings.
- Imported values are kept as received beside what they were mapped to, so a wrong alias or "same Player" answer can be remapped without re-importing. Derived data is not stored ([ADR 0008](0008-draft-state-derived-from-draft-actions.md)); any later cache must be safe to delete.
- Schema migrations from the first milestone, since real data is kept while the schema still changes. WAL mode.
- The data folder is outside the repository, by default `~/.local/share/nimbus` (XDG data directory). SQLite locking is unreliable on Windows drives under WSL, so the app warns at startup if the folder is under `/mnt/`.
- Backups are made with `VACUUM INTO` or the online backup API, never a raw file copy: on demand, and automatically before every migration, Source removal and import. The last N automatic copies are kept (default 10); manual ones are never deleted automatically. Each new copy is checked with `PRAGMA integrity_check` and a failure is reported at once.
- Restoring is replacing the database file with the app closed, also removing any leftover `-wal` and `-shm` files so they are not applied to the restored copy.
- No encryption in the first release: protection relies on the machine's disk encryption.
- Removing a Source also compacts the database, so deleted rows do not linger in the file, and offers to delete older backups that still contain them.

## Considered Options

- PostgreSQL: pays off only with several users.
