-- Rebuild instead of renaming the old table so child foreign keys keep games(id).
CREATE TABLE replay_games (
    id TEXT PRIMARY KEY,
    series_id TEXT NOT NULL REFERENCES series(id),
    number INTEGER NOT NULL,
    assignments TEXT NOT NULL,
    patch TEXT,
    acknowledgements TEXT NOT NULL DEFAULT '[]',
    edit_history TEXT NOT NULL DEFAULT '[]',
    winner TEXT CHECK(winner IN ('A', 'B')),
    voided INTEGER NOT NULL DEFAULT 0,
    attempt_order INTEGER NOT NULL,
    replay_of TEXT REFERENCES games(id),
    UNIQUE(series_id, attempt_order)
);
INSERT INTO replay_games (id, series_id, number, assignments, patch, acknowledgements,
                          edit_history, winner, voided, attempt_order)
SELECT id, series_id, number, assignments, patch, acknowledgements,
       edit_history, winner, voided, number FROM games;
DROP TABLE games;
ALTER TABLE replay_games RENAME TO games;
PRAGMA user_version = 8;
