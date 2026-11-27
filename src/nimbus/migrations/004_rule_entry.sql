ALTER TABLE draft_actions RENAME TO old_draft_actions;
CREATE TABLE draft_actions (
    game_id TEXT NOT NULL REFERENCES games(id),
    turn_index INTEGER NOT NULL,
    team_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    character_id TEXT,
    PRIMARY KEY(game_id, turn_index)
);
INSERT INTO draft_actions SELECT * FROM old_draft_actions;
DROP TABLE old_draft_actions;
ALTER TABLE games ADD COLUMN acknowledgements TEXT NOT NULL DEFAULT '[]';
PRAGMA user_version = 4;
