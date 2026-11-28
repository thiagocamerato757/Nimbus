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

from nimbus.models import (
    ActionEdit,
    DraftAction,
    Game,
    Player,
    PlayerAssignment,
    RosterTeam,
    Series,
    TeamId,
)


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
            if version in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10):
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
                version = 3
            if version == 3:
                migration = Path(__file__).with_name("migrations") / "004_rule_entry.sql"
                columns = {row[1] for row in connection.execute("PRAGMA table_info(games)")}
                if "acknowledgements" not in columns:
                    connection.executescript("BEGIN;\n" + migration.read_text() + "\nCOMMIT;")
                else:
                    connection.execute("PRAGMA user_version = 4")
                version = 4
            if version == 4:
                migration = Path(__file__).with_name("migrations") / "005_corrections.sql"
                columns = {row[1] for row in connection.execute("PRAGMA table_info(games)")}
                if "edit_history" not in columns:
                    connection.executescript("BEGIN;\n" + migration.read_text() + "\nCOMMIT;")
                else:
                    connection.execute("PRAGMA user_version = 5")
                version = 5
            if version == 5:
                migration = Path(__file__).with_name("migrations") / "006_rosters.sql"
                connection.executescript("BEGIN;\n" + migration.read_text())
                # Existing Series Teams were local A/B labels, never global identities.
                for row in connection.execute("SELECT id, teams FROM series").fetchall():
                    teams = json.loads(row["teams"])
                    for team in teams:
                        if team.get("roster_id") is not None:
                            continue
                        # Stable across restoring and migrating the same old backup.
                        team["roster_id"] = f"legacy:{row['id']}:{team['id']}"
                        connection.execute(
                            "INSERT INTO roster_teams VALUES (?, ?)",
                            (team["roster_id"], team["name"]),
                        )
                    connection.execute(
                        "UPDATE series SET teams = ? WHERE id = ?", (json.dumps(teams), row["id"])
                    )
                version = 6
            if version == 6:
                migration = Path(__file__).with_name("migrations") / "007_game_lifecycle.sql"
                columns = {row[1] for row in connection.execute("PRAGMA table_info(games)")}
                if "winner" not in columns:
                    connection.executescript("BEGIN;\n" + migration.read_text() + "\nCOMMIT;")
                else:
                    connection.execute("PRAGMA user_version = 7")
                version = 7
            if version == 7:
                columns = {row[1] for row in connection.execute("PRAGMA table_info(games)")}
                if "replay_of" not in columns:
                    migration = Path(__file__).with_name("migrations") / "008_replay_attempts.sql"
                    connection.commit()
                    connection.execute("PRAGMA foreign_keys=OFF")
                    try:
                        connection.executescript("BEGIN;\n" + migration.read_text())
                        if connection.execute("PRAGMA foreign_key_check").fetchone():
                            raise RuntimeError("Replay migration failed foreign-key verification")
                        connection.commit()
                    except BaseException:
                        connection.rollback()
                        raise
                    finally:
                        connection.execute("PRAGMA foreign_keys=ON")
                else:
                    connection.execute("PRAGMA user_version = 8")
                version = 8
            if version == 8:
                columns = {row[1] for row in connection.execute("PRAGMA table_info(games)")}
                if "first_selection_holder" not in columns:
                    migration = Path(__file__).with_name("migrations") / "009_first_selection.sql"
                    connection.executescript("BEGIN;\n" + migration.read_text() + "\nCOMMIT;")
                else:
                    connection.execute("PRAGMA user_version = 9")
                version = 9
            if version == 9:
                self._clear_orphan_choices(connection)
                version = 10
            if version == 10:
                connection.executescript(
                    "BEGIN; CREATE TABLE IF NOT EXISTS workspace_disabled "
                    "(profile_id TEXT PRIMARY KEY, character_ids TEXT NOT NULL); "
                    "PRAGMA user_version = 11; COMMIT;"
                )
                version = 11
            if version != 11:
                raise RuntimeError(f"Unsupported Nimbus database schema: {version}")

    @staticmethod
    def _clear_orphan_choices(connection: sqlite3.Connection) -> None:
        """Schema 10: no stored First Selection choice lacks a holder (ADR-0009)."""
        orphaned = "first_selection_holder IS NULL AND first_selection_choice IS NOT NULL"
        rows = connection.execute(
            f"SELECT id, series_id, number, first_selection_choice FROM games WHERE {orphaned}"
        ).fetchall()
        for row in rows:
            logging.getLogger(__name__).warning(
                "Clearing First Selection choice %r stored without a holder: "
                "Series %s, Game %s (%s)",
                row["first_selection_choice"],
                row["series_id"],
                row["number"],
                row["id"],
            )
        connection.execute(f"UPDATE games SET first_selection_choice = NULL WHERE {orphaned}")
        connection.execute("PRAGMA user_version = 10")

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

    def list_teams(self) -> list[RosterTeam]:
        with self.connection() as connection:
            return [
                RosterTeam(**dict(row))
                for row in connection.execute("SELECT * FROM roster_teams ORDER BY rowid")
            ]

    def add_team(self, name: str) -> RosterTeam:
        team = RosterTeam(id=uuid4().hex, name=name)
        with self.connection() as connection:
            connection.execute("INSERT INTO roster_teams VALUES (?, ?)", (team.id, team.name))
        return team

    def list_players(self) -> list[Player]:
        with self.connection() as connection:
            return [
                Player(**{**dict(row), "declared_pools": json.loads(row["declared_pools"])})
                for row in connection.execute("SELECT * FROM players ORDER BY rowid")
            ]

    def save_player(self, player: Player) -> None:
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO players (id, name, usual_role, current_team_id, declared_pools) "
                "VALUES (?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET "
                "name=excluded.name, usual_role=excluded.usual_role, "
                "current_team_id=excluded.current_team_id, declared_pools=excluded.declared_pools",
                (
                    player.id,
                    player.name,
                    player.usual_role,
                    player.current_team_id,
                    json.dumps(player.declared_pools),
                ),
            )

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
            team_ids: tuple[TeamId, ...] = ("A", "B")
            for game in connection.execute(
                "SELECT * FROM games WHERE series_id = ? ORDER BY attempt_order", (identifier,)
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
                        player_assignments=tuple(
                            PlayerAssignment.model_validate(dict(row))
                            for row in connection.execute(
                                "SELECT turn_index, player_id FROM player_assignments "
                                "WHERE game_id = ? ORDER BY turn_index",
                                (game["id"],),
                            )
                        ),
                        lineups={
                            team: tuple(
                                row["player_id"]
                                for row in connection.execute(
                                    "SELECT player_id FROM lineups WHERE game_id = ? AND team_id = ? "
                                    "ORDER BY rowid",
                                    (game["id"], team),
                                )
                            )
                            for team in team_ids
                        },
                        first_selection_holder=game["first_selection_holder"],
                        first_selection_choice=game["first_selection_choice"],
                        patch=game["patch"],
                        winner=game["winner"],
                        voided=bool(game["voided"]),
                        id=game["id"],
                        number=game["number"],
                        replay_of=game["replay_of"],
                        assignments=json.loads(game["assignments"]),
                        actions=tuple(DraftAction.model_validate(a) for a in actions),
                        acknowledgements=json.loads(game["acknowledgements"]),
                        edit_history=json.loads(game["edit_history"]),
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

    def workspace_disabled(self) -> dict[str, tuple[str, ...]]:
        with self.connection() as connection:
            return {
                row["profile_id"]: tuple(json.loads(row["character_ids"]))
                for row in connection.execute("SELECT * FROM workspace_disabled")
            }

    def set_workspace_disabled(self, profile_id: str, character_ids: tuple[str, ...]) -> None:
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO workspace_disabled VALUES (?, ?) ON CONFLICT(profile_id) "
                "DO UPDATE SET character_ids = excluded.character_ids",
                (profile_id, json.dumps(character_ids)),
            )

    def save_rules(self, series: Series) -> None:
        with self.connection() as connection:
            connection.execute(
                "UPDATE series SET rule_snapshot = ? WHERE id = ?",
                (series.rule_snapshot.model_dump_json(), series.id),
            )

    def add_game(self, series_id: str, game: Game) -> None:
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO games (id, series_id, number, assignments, patch, replay_of, attempt_order) "
                "VALUES (?, ?, ?, ?, ?, ?, (SELECT COALESCE(MAX(attempt_order), 0) + 1 FROM games WHERE series_id = ?))",
                (
                    game.id,
                    series_id,
                    game.number,
                    json.dumps([a.model_dump() for a in game.assignments]),
                    game.patch,
                    game.replay_of,
                    series_id,
                ),
            )

            self.save_first_selection(game)
            for action in game.actions:
                self.add_action(game.id, action, game)
            for team_id, players in game.lineups.items():
                self.save_lineup(game.id, team_id, players)

    def save_first_selection(self, game: Game) -> None:
        with self.connection() as connection:
            connection.execute(
                "UPDATE games SET first_selection_holder = ?, first_selection_choice = ? WHERE id = ?",
                (game.first_selection_holder, game.first_selection_choice, game.id),
            )

    def save_winner(self, game_id: str, winner: str | None) -> None:
        with self.connection() as connection:
            connection.execute("UPDATE games SET winner = ? WHERE id = ?", (winner, game_id))

    def void_game(self, game_id: str) -> None:
        with self.connection() as connection:
            connection.execute("UPDATE games SET voided = 1 WHERE id = ?", (game_id,))

    def save_lineup(self, game_id: str, team_id: str, players: tuple[str, ...]) -> None:
        with self.connection() as connection:
            current = {
                row["player_id"]
                for row in connection.execute(
                    "SELECT player_id FROM lineups WHERE game_id = ? AND team_id = ?",
                    (game_id, team_id),
                )
            }
            connection.executemany(
                "DELETE FROM lineups WHERE game_id = ? AND team_id = ? AND player_id = ?",
                [(game_id, team_id, player) for player in current - set(players)],
            )
            connection.executemany(
                "INSERT INTO lineups VALUES (?, ?, ?)",
                [(game_id, team_id, player) for player in players if player not in current],
            )

    def save_player_assignment(self, game_id: str, turn_index: int, player_id: str | None) -> None:
        with self.connection() as connection:
            connection.execute(
                "DELETE FROM player_assignments WHERE game_id = ? AND turn_index = ?",
                (game_id, turn_index),
            )
            if player_id is not None:
                connection.execute(
                    "INSERT INTO player_assignments VALUES (?, ?, ?)",
                    (game_id, turn_index, player_id),
                )

    def add_action(self, game_id: str, action: DraftAction, game: Game) -> None:
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO draft_actions VALUES (?, ?, ?, ?, ?)",
                (game_id, action.turn_index, action.team_id, action.kind, action.character_id),
            )

            connection.execute(
                "UPDATE games SET acknowledgements = ? WHERE id = ?",
                (json.dumps([a.model_dump() for a in game.acknowledgements]), game_id),
            )

    def save_acknowledgements(self, game: Game) -> None:
        with self.connection() as connection:
            connection.execute(
                "UPDATE games SET acknowledgements = ? WHERE id = ?",
                (json.dumps([a.model_dump() for a in game.acknowledgements]), game.id),
            )

    def save_correction(self, before: DraftAction, game: Game, after: DraftAction | None) -> None:
        edit = ActionEdit(recorded_at=datetime.now(UTC).isoformat(), before=before, after=after)
        with self.connection() as connection:
            if after is None:
                connection.execute(
                    "DELETE FROM draft_actions WHERE game_id = ? AND turn_index = ?",
                    (game.id, before.turn_index),
                )
            else:
                connection.execute(
                    "UPDATE draft_actions SET character_id = ? WHERE game_id = ? AND turn_index = ?",
                    (after.character_id, game.id, before.turn_index),
                )
            connection.execute(
                "UPDATE games SET edit_history = ? WHERE id = ?",
                (json.dumps([e.model_dump() for e in game.edit_history + (edit,)]), game.id),
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
