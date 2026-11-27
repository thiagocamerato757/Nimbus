# Back up and restore a Workspace

Choose **Back up Workspace** in the sidebar. Nimbus creates a manual backup,
checks it with SQLite's `PRAGMA integrity_check`, and shows its filename after
verification succeeds. A failure appears immediately as an error notice. Backups
are in `backups/` under the data folder (`~/.local/share/nimbus` by default;
`NIMBUS_DATA_DIR` overrides it). Do not rely on a backup that failed verification.

Nimbus also makes a verified automatic backup before migrating an existing
schema. If creating or verifying it fails, startup stops before the migration.
The most recent 10 automatic backups are kept by default. Set
`NIMBUS_BACKUP_RETENTION` to a positive integer before starting Nimbus to choose a
different count. Retention deletes only the oldest automatic backups; manual
backups are never pruned. Automatic import and Source-removal integration is
tracked separately in #18 and #21.

## Restore

1. Close Nimbus completely, including every backend process using the data folder.
2. Keep the current `nimbus.sqlite3` somewhere safe if you may need to undo the restore.
3. Remove leftover `nimbus.sqlite3-wal` and `nimbus.sqlite3-shm` files from the
   data folder. They belong to the previous database and must not be applied to
   the restored copy.
4. Replace `nimbus.sqlite3` with your chosen verified `.sqlite3` file from `backups/`.
5. Restart Nimbus and check your Series. An older supported schema will be backed
   up and migrated automatically on startup.

Never replace a database while Nimbus is running. New backups are consistent
standalone SQLite files, created through the SQLite online backup API; copying a
live database file directly can lose changes still in its WAL.

## API and integration

`POST /api/backups` creates and verifies a manual backup and returns
`{ "name": "manual-…sqlite3", "kind": "manual", "verified": true }` with status 201.
It uses the same local-access and Workspace version headers as other writes.
`GET /api/backups` lists backups that completed verification at creation time;
this is not a fresh verification against subsequent disk changes. Failures return
status 500 with code `backup_failed`; no failed copy is retained or listed.

Other risky operations call `Store.create_backup(reason)` **before changing any
facts**, with a fixed reason such as `migration`, `import`, or `source-removal`.
They must abort when `BackupError` is raised. This interface uses a separate
SQLite connection to snapshot committed data, including WAL contents. It must
be called before any uncommitted operation changes are made; those changes
would not be part of that snapshot. Automatic retention spans all reasons.
