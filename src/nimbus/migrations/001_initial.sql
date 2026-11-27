CREATE TABLE series (
    id TEXT PRIMARY KEY,
    profile_id TEXT NOT NULL,
    teams TEXT NOT NULL,
    our_team TEXT,
    rule_snapshot TEXT NOT NULL
);
CREATE TABLE games (
    id TEXT PRIMARY KEY,
    series_id TEXT NOT NULL REFERENCES series(id),
    number INTEGER NOT NULL,
    assignments TEXT NOT NULL,
    UNIQUE(series_id, number)
);
CREATE TABLE draft_actions (
    game_id TEXT NOT NULL REFERENCES games(id),
    turn_index INTEGER NOT NULL,
    team_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    character_id TEXT NOT NULL,
    PRIMARY KEY(game_id, turn_index)
);
PRAGMA user_version = 1;
