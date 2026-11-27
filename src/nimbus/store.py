"""SQLite persistence stores facts only; all board state comes from the engine."""

import json
import logging
import os
import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from contextvars import ContextVar
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

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
        self.active: ContextVar[sqlite3.Connection | None] = ContextVar("connection", default=None)
        with self.connection() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version == 1:
                self.backup_before_migration(connection)
            if version == 0:
                migration = Path(__file__).with_name("migrations") / "001_initial.sql"
                connection.executescript("BEGIN;\n" + migration.read_text() + "\nCOMMIT;")
                version = 1
            if version == 1:
                migration = Path(__file__).with_name("migrations") / "002_workspace_version.sql"
                connection.executescript("BEGIN;\n" + migration.read_text() + "\nCOMMIT;")
            elif version != 2:
                raise RuntimeError(f"Unsupported Nimbus database schema: {version}")

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        if active := self.active.get():
            yield active
            return
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

    def begin_request(self, writing: bool) -> sqlite3.Connection:
        """Acquire a snapshot or a reserved write lock before checking the version."""
        connection = sqlite3.connect(self.path, check_same_thread=False, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        try:
            connection.execute("BEGIN IMMEDIATE" if writing else "BEGIN")
        except BaseException:
            connection.close()
            raise
        return connection

    def backup_before_migration(self, source: sqlite3.Connection) -> None:
        """ADR-0032: fail startup before changing facts if a checked backup fails."""
        directory = self.path.parent / "backups"
        directory.mkdir(exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        path = directory / f"automatic-migration-{timestamp}-{uuid4().hex}.sqlite3"
        with closing(sqlite3.connect(path)) as backup:
            source.backup(backup)
            if backup.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                raise RuntimeError(f"Migration backup failed its integrity check: {path}")
        for expired in sorted(directory.glob("automatic-migration-*.sqlite3"))[:-10]:
            expired.unlink()
