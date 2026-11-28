CREATE TABLE IF NOT EXISTS roster_teams (id TEXT PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS players (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    usual_role TEXT,
    declared_pools TEXT NOT NULL DEFAULT '{}',
    current_team_id TEXT REFERENCES roster_teams(id)
);
CREATE TABLE IF NOT EXISTS lineups (
    game_id TEXT NOT NULL REFERENCES games(id),
    team_id TEXT NOT NULL CHECK(team_id IN ('A', 'B')),
    player_id TEXT NOT NULL REFERENCES players(id),
    PRIMARY KEY(game_id, player_id)
);
CREATE TABLE IF NOT EXISTS player_assignments (
    game_id TEXT NOT NULL,
    turn_index INTEGER NOT NULL,
    player_id TEXT NOT NULL,
    PRIMARY KEY(game_id, turn_index),
    UNIQUE(game_id, player_id),
    FOREIGN KEY(game_id, turn_index) REFERENCES draft_actions(game_id, turn_index) ON DELETE CASCADE,
    FOREIGN KEY(game_id, player_id) REFERENCES lineups(game_id, player_id)
);
PRAGMA user_version = 6;
