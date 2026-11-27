"""The local HTTP boundary for manual draft entry."""

from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from nimbus.engine import derive_state, record_entry
from nimbus.local_access import LocalAccess
from nimbus.models import (
    Assignment,
    DraftAction,
    Fearless,
    Game,
    GameView,
    OverrideReason,
    Series,
    SeriesFormat,
    SeriesView,
    Team,
    TeamId,
)
from nimbus.profiles import ProfileLoadError, TitleProfile, load_profiles
from nimbus.store import Backup, BackupError, Store, default_data_dir
from nimbus.workspace import Workspace


class Request(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CreateSeries(Request):
    profile_id: str
    team_a: str = Field(min_length=1, max_length=100)
    team_b: str = Field(min_length=1, max_length=100)
    our_team: TeamId | None = None
    draft_order_id: str | None = None
    series_format: SeriesFormat | None = None
    fearless: Fearless | None = None
    patch: str | None = Field(default=None, max_length=100)
    record_type: Literal["official", "scrim"] = "official"


class StartGame(Request):
    patch: str | None = Field(default=None, max_length=100)
    team_a_side: str
    first_pick_team: TeamId


class EnterAction(Request):
    character_id: str | None
    override: OverrideReason | None = None


def reject(code: str, message: str, status: int = 409) -> HTTPException:
    return HTTPException(status_code=status, detail={"code": code, "message": message})


def create_app(data_dir: Path | None = None, profile_dir: Path | None = None) -> FastAPI:
    app = FastAPI(title="Nimbus")
    store = Store(data_dir if data_dir is not None else default_data_dir())
    app.add_middleware(Workspace, store=store)
    app.add_middleware(LocalAccess)

    # An application loads one checked set of files. Reloading needs a restart;
    # an edit on disk cannot invalidate a draft already in progress.
    loaded_profiles: dict[str, TitleProfile] = {}
    profile_error: ProfileLoadError | None = None
    try:
        references: dict[str, set[str]] = {}
        for stored_series in store.list_series():
            references.setdefault(stored_series.profile_id, set()).update(
                action.character_id
                for game in stored_series.games
                for action in game.actions
                if action.character_id is not None
            )
        loaded_profiles = load_profiles(profile_dir, references)
    except ProfileLoadError as error:
        profile_error = error

    def profiles() -> dict[str, TitleProfile]:
        if profile_error is not None:
            raise reject("profile_load_failed", str(profile_error), 500)
        return loaded_profiles

    def read(identifier: str) -> Series:
        profiles()
        try:
            return store.read(identifier)
        except KeyError:
            raise reject("series_not_found", "Series not found.", 404) from None

    def view(series: Series) -> SeriesView:
        catalog = profiles()[series.profile_id].catalog
        games = tuple(
            GameView(
                **game.model_dump(),
                state=derive_state(series.rule_snapshot, catalog, series.games, game),
            )
            for game in series.games
        )
        return SeriesView(**series.model_dump(exclude={"games"}), games=games)

    @app.get("/api/backups")
    def get_backups() -> list[Backup]:
        return store.list_backups()

    @app.post("/api/backups", status_code=201)
    def create_backup() -> Backup:
        try:
            return store.create_backup()
        except BackupError as error:
            raise reject("backup_failed", str(error), 500) from error

    @app.get("/api/profiles")
    def get_profiles() -> list[TitleProfile]:
        return list(profiles().values())

    @app.get("/api/series")
    def get_series_list() -> list[SeriesView]:
        profiles()
        return [view(series) for series in store.list_series()]

    @app.post("/api/series", status_code=201)
    def create_series(request: CreateSeries) -> SeriesView:
        profile = profiles().get(request.profile_id)
        if profile is None:
            raise reject("profile_not_found", "Title profile not found.", 404)
        snapshot = profile.snapshot()
        order = next(
            (
                order
                for order in profile.draft_orders
                if order.id == (request.draft_order_id or profile.default_draft_order)
            ),
            None,
        )
        if order is None:
            raise reject("unknown_draft_order", "Choose a Draft Order from the Title profile.", 422)
        if request.series_format and request.series_format not in profile.series_formats:
            raise reject(
                "unknown_series_format", "Choose a Series Format allowed by the Title profile.", 422
            )
        snapshot = snapshot.model_copy(
            update={
                "draft_order": order,
                "series_format": request.series_format or snapshot.series_format,
                "fearless": request.fearless or snapshot.fearless,
            }
        )
        series = Series(
            patch=request.patch,
            record_type=request.record_type,
            id=uuid4().hex,
            profile_id=profile.id,
            teams=(Team(id="A", name=request.team_a), Team(id="B", name=request.team_b)),
            our_team=request.our_team,
            rule_snapshot=snapshot,
        )
        store.create(series)
        return view(series)

    @app.get("/api/series/{identifier}")
    def get_series(identifier: str) -> SeriesView:
        return view(read(identifier))

    @app.post("/api/series/{identifier}/games", status_code=201)
    def start_game(identifier: str, request: StartGame) -> SeriesView:
        series = read(identifier)
        profile = profiles()[series.profile_id]
        if (
            series.games
            and not derive_state(
                series.rule_snapshot, profile.catalog, series.games, series.games[-1]
            ).complete
        ):
            raise reject(
                "draft_incomplete", "Complete the current draft before starting the next Game."
            )
        if len(series.games) >= series.rule_snapshot.series_format.games:
            raise reject("series_full", "All Games in this Series Format have been started.")
        if request.team_a_side not in profile.sides:
            raise reject("unknown_side", "Choose a Side from the Title profile.", 422)
        other_side = next(side for side in profile.sides if side != request.team_a_side)
        assignments = tuple(
            Assignment(
                team_id=team.id,
                side=request.team_a_side if team.id == "A" else other_side,
                position="first" if team.id == request.first_pick_team else "second",
            )
            for team in series.teams
        )
        game = Game(
            id=uuid4().hex,
            number=len(series.games) + 1,
            assignments=assignments,
            patch=request.patch if request.patch is not None else series.patch,
        )
        store.add_game(identifier, game)
        return view(read(identifier))

    @app.post("/api/series/{identifier}/games/{game_id}/actions", status_code=201)
    def enter_action(identifier: str, game_id: str, request: EnterAction) -> SeriesView:
        series = read(identifier)
        if not series.games or series.games[-1].id != game_id:
            raise reject("not_current_game", "Enter Draft Actions in the current Game.")
        game = series.games[-1]
        profile = profiles()[series.profile_id]
        state = derive_state(series.rule_snapshot, profile.catalog, series.games, game)
        turn = state.next_turn
        if turn is None:
            raise reject("draft_complete", "This draft is already complete.")
        action = DraftAction(
            turn_index=turn.index,
            team_id=turn.team_id,
            kind=turn.kind,
            character_id=request.character_id,
        )
        try:
            recorded = record_entry(
                series.rule_snapshot, profile.catalog, series.games, game, action, request.override
            )
        except ValueError as error:
            code = str(error)
            messages = {
                "unknown_character": "Choose an active Character from the Character Catalog.",
                "cannot_skip_pick": "A pick turn cannot be skipped.",
                "duplicate_character": "This Character already appears in this Game.",
                "fearless_lock": "Fearless Lock: this Character was picked in an earlier Game.",
                "wasted_ban": "Wasted ban: the opposing Team cannot pick this Character due to a Fearless Lock.",
            }
            raise reject(
                code,
                messages.get(code, "This Draft Action cannot fill this turn."),
                422 if code == "unknown_character" else 409,
            ) from error
        store.add_action(game.id, action, recorded)
        return view(read(identifier))

    return app
