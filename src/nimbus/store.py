"""SQLite persistence stores facts only; all board state comes from the engine."""

import json
import logging
import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from nimbus.models import DraftAction, Game, Series


def default_data_dir() -> Path:
    if override := os.environ.get("NIMBUS_DATA_DIR"):
        return Path(override).expanduser()
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "nimbus"


class Store:
    def __init__(self, directory: Path):
        directory = directory.expanduser().resolve()
        if directory.is_relative_to("/mnt"):
            logging.getLogger(__name__).warning(
                "Nimbus data folder %s is under /mnt/: SQLite locking may be unreliable on "
                "Windows drives under WSL. Prefer a Linux filesystem.",
                directory,
            )
        directory.mkdir(parents=True, exist_ok=True)
        self.path = directory / "nimbus.sqlite3"
        with self.connection() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version == 0:
                migration = Path(__file__).with_name("migrations") / "001_initial.sql"
                connection.executescript("BEGIN;\n" + migration.read_text() + "\nCOMMIT;")
            elif version != 1:
                raise RuntimeError(f"Unsupported Nimbus database schema: {version}")

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def list_series(self) -> list[Series]:
        with self.connection() as connection:
            identifiers = [
                row["id"] for row in connection.execute("SELECT id FROM series ORDER BY rowid DESC")
            ]
        return [self.read(identifier) for identifier in identifiers]

    def read(self, identifier: str) -> Series:
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM series WHERE id = ?", (identifier,)).fetchone()
            if row is None:
                raise KeyError(identifier)
            games = []
            for game in connection.execute(
                "SELECT * FROM games WHERE series_id = ? ORDER BY number", (identifier,)
            ):
                actions = [
                    dict(a)
                    for a in connection.execute(
                        "SELECT turn_index, team_id, kind, character_id FROM draft_actions "
                        "WHERE game_id = ? ORDER BY turn_index",
                        (game["id"],),
                    )
                ]
                games.append(
                    Game(
                        id=game["id"],
                        number=game["number"],
                        assignments=json.loads(game["assignments"]),
                        actions=tuple(DraftAction.model_validate(a) for a in actions),
                    )
                )
            return Series(
                id=row["id"],
                profile_id=row["profile_id"],
                teams=json.loads(row["teams"]),
                our_team=row["our_team"],
                rule_snapshot=json.loads(row["rule_snapshot"]),
                games=tuple(games),
            )

    def create(self, series: Series) -> None:
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO series VALUES (?, ?, ?, ?, ?)",
                (
                    series.id,
                    series.profile_id,
                    json.dumps([t.model_dump() for t in series.teams]),
                    series.our_team,
                    series.rule_snapshot.model_dump_json(),
                ),
            )

    def add_game(self, series_id: str, game: Game) -> None:
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO games VALUES (?, ?, ?, ?)",
                (
                    game.id,
                    series_id,
                    game.number,
                    json.dumps([a.model_dump() for a in game.assignments]),
                ),
            )

    def add_action(self, game_id: str, action: DraftAction) -> None:
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO draft_actions VALUES (?, ?, ?, ?, ?)",
                (game_id, action.turn_index, action.team_id, action.kind, action.character_id),
            )
