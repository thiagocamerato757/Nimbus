CREATE TABLE workspace_version (id INTEGER PRIMARY KEY CHECK (id = 1), version INTEGER NOT NULL);
INSERT INTO workspace_version VALUES (1, 0);
PRAGMA user_version = 2;
