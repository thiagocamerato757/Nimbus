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
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel

from nimbus.models import DraftAction, Game, Series


def default_data_dir() -> Path:
    if override := os.environ.get("NIMBUS_DATA_DIR"):
        return Path(override).expanduser()
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "nimbus"


class BackupError(RuntimeError):
    """No verified backup was produced; the protected operation must stop."""


class Backup(BaseModel):
    name: str
    kind: Literal["manual", "automatic"]
    verified: bool = True


class Store:
    def __init__(self, directory: Path):
        self.backup_retention = int(os.environ.get("NIMBUS_BACKUP_RETENTION", "10"))
        if self.backup_retention < 1:
            raise ValueError("NIMBUS_BACKUP_RETENTION must be at least 1")
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
            if version in (1, 2):
                self.create_backup("migration")
            if version == 0:
                migration = Path(__file__).with_name("migrations") / "001_initial.sql"
                connection.executescript("BEGIN;\n" + migration.read_text() + "\nCOMMIT;")
                version = 1
            if version == 1:
                migration = Path(__file__).with_name("migrations") / "002_workspace_version.sql"
                connection.executescript("BEGIN;\n" + migration.read_text() + "\nCOMMIT;")
                version = 2
            if version == 2:
                migration = Path(__file__).with_name("migrations") / "003_series_settings.sql"
                # Compatibility with an older-schema restore that retains additive columns.
                columns = {row[1] for row in connection.execute("PRAGMA table_info(series)")}
                if "patch" not in columns:
                    connection.executescript("BEGIN;\n" + migration.read_text() + "\nCOMMIT;")
                else:
                    connection.execute("PRAGMA user_version = 3")
            elif version != 3:
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
                        patch=game["patch"],
                        id=game["id"],
                        number=game["number"],
                        assignments=json.loads(game["assignments"]),
                        actions=tuple(DraftAction.model_validate(a) for a in actions),
                    )
                )
            return Series(
                patch=row["patch"],
                record_type=row["record_type"],
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
                "INSERT INTO series (id, profile_id, teams, our_team, rule_snapshot, patch, record_type) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    series.id,
                    series.profile_id,
                    json.dumps([t.model_dump() for t in series.teams]),
                    series.our_team,
                    series.rule_snapshot.model_dump_json(),
                    series.patch,
                    series.record_type,
                ),
            )

    def add_game(self, series_id: str, game: Game) -> None:
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO games (id, series_id, number, assignments, patch) VALUES (?, ?, ?, ?, ?)",
                (
                    game.id,
                    series_id,
                    game.number,
                    json.dumps([a.model_dump() for a in game.assignments]),
                    game.patch,
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

    def create_backup(self, reason: str | None = None) -> Backup:
        """Preserve committed facts through SQLite, before the caller changes them.

        Use a dedicated read connection: backing up the request's connection while
        it holds BEGIN IMMEDIATE would wait on its own write transaction.
        """
        directory = self.path.parent / "backups"
        kind: Literal["manual", "automatic"] = "automatic" if reason else "manual"
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        label = f"automatic-{reason}" if reason else "manual"
        path = directory / f"{label}-{timestamp}-{uuid4().hex}.sqlite3"
        pending = path.with_suffix(".pending")
        try:
            directory.mkdir(exist_ok=True)
            with (
                closing(sqlite3.connect(self.path)) as source,
                closing(sqlite3.connect(pending)) as backup,
            ):
                source.backup(backup)
                if backup.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                    raise BackupError(f"Backup failed its integrity check: {path}")
            pending.rename(path)
        except (sqlite3.Error, OSError, BackupError) as error:
            pending.unlink(missing_ok=True)
            raise BackupError(f"Could not create a verified backup: {error}") from error
        if reason:
            for expired in sorted(
                directory.glob("automatic-*.sqlite3"),
                key=lambda item: item.name.rsplit("-", 2)[-2],
            )[: -self.backup_retention]:
                expired.unlink()
        return Backup(name=path.name, kind=kind)

    def list_backups(self) -> list[Backup]:
        directory = self.path.parent / "backups"
        return [
            Backup(
                name=path.name, kind="manual" if path.name.startswith("manual-") else "automatic"
            )
            for path in sorted(directory.glob("*.sqlite3"), reverse=True)
            if path.name.startswith(("manual-", "automatic-"))
        ]
