# Characters are retired, never deleted, and the catalog is not snapshotted

Unlike rule settings ([ADR 0013](0013-series-snapshots-rule-settings.md)), the Character Catalog is read live by every Series, because new Characters are harmless to old ones. To keep old records valid, each Character has a stable id separate from its display name and is marked Retired instead of being deleted; loading a Title profile fails if a Character used by stored data is missing.
