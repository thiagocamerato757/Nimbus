"""The local HTTP boundary for manual draft entry."""

from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from nimbus.engine import (
    acknowledge_violation,
    clear_action,
    correct_action,
    create_replay,
    derive_progress,
    derive_state,
    first_selection_prefill,
    game_assignments,
    record_entry,
)
from nimbus.local_access import LocalAccess
from nimbus.models import (
    Assignment,
    DraftAction,
    Fearless,
    Game,
    GameView,
    OverrideReason,
    Player,
    RosterTeam,
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
    team_a_id: str | None = None
    team_b_id: str | None = None
    our_team: TeamId | None = None
    draft_order_id: str | None = None
    series_format: SeriesFormat | None = None
    fearless: Fearless | None = None
    patch: str | None = Field(default=None, max_length=100)
    record_type: Literal["official", "scrim"] = "official"


class EditPlayerAssignment(Request):
    turn_index: int = Field(strict=True, ge=0)
    player_id: str | None


class EditLineup(Request):
    team_id: TeamId
    player_ids: tuple[str, ...]


class EditPool(Request):
    character_ids: tuple[str, ...]


class EditPlayer(Request):
    name: str = Field(min_length=1, max_length=100)
    usual_role: str | None = Field(default=None, max_length=100)
    current_team_id: str | None = None


class FirstSelection(Request):
    first_selection_holder: TeamId | None = None
    first_selection_choice: Literal["side", "draft_position"] | None = None


class StartGame(FirstSelection):
    patch: str | None = Field(default=None, max_length=100)
    team_a_side: str
    first_pick_team: TeamId


class ReplayGame(FirstSelection):
    draft_choice: Literal["copy_draft", "new_draft"]
    team_a_side: str | None = None
    first_pick_team: TeamId | None = None
    patch: str | None = Field(default=None, max_length=100)
    lineups: dict[TeamId, tuple[str, ...]] | None = None


class EditWinner(Request):
    winner: TeamId | None


class AcknowledgeViolation(Request):
    rule: str
    reason: OverrideReason


class CorrectAction(Request):
    character_id: str | None


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
            references[stored_series.profile_id].update(
                action.character_id
                for game in stored_series.games
                for edit in game.edit_history
                for action in (edit.before, edit.after)
                if action is not None and action.character_id is not None
            )
        for player in store.list_players():
            for profile_id, character_ids in player.declared_pools.items():
                references.setdefault(profile_id, set()).update(character_ids)
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
                first_selection_prefill=first_selection_prefill(
                    series.rule_snapshot, series.games, game.number
                ),
            )
            for game in series.games
        )
        return SeriesView(
            **series.model_dump(exclude={"games"}),
            games=games,
            progress=derive_progress(series.rule_snapshot, series.games),
            next_first_selection_holder=first_selection_prefill(
                series.rule_snapshot,
                series.games,
                max((g.number for g in series.games), default=0) + 1,
            ),
        )

    def check_team(team_id: str | None) -> None:
        if team_id is not None and not any(t.id == team_id for t in store.list_teams()):
            raise reject("team_not_found", "Roster Team not found.", 404)

    def find_player(player_id: str) -> Player:
        player = next((p for p in store.list_players() if p.id == player_id), None)
        if player is None:
            raise reject("player_not_found", "Player not found.", 404)
        return player

    @app.post("/api/series/{identifier}/teams/{team_id}/players/{player_id}/pool")
    def edit_pool(identifier: str, team_id: TeamId, player_id: str, request: EditPool) -> Player:
        series = read(identifier)
        player = find_player(player_id)
        team = next(t for t in series.teams if t.id == team_id)
        if series.our_team != team_id or player.current_team_id != team.roster_id:
            raise reject("pool_not_ours", "Edit Declared Pools for Players on Our Team's Roster.")
        catalog = profiles()[series.profile_id].catalog
        if set(request.character_ids) - {c.id for c in catalog if not c.retired}:
            raise reject("unknown_character", "Choose active Characters from the Catalog.", 422)
        pools = {
            **player.declared_pools,
            series.profile_id: tuple(dict.fromkeys(request.character_ids)),
        }
        player = player.model_copy(update={"declared_pools": pools})
        store.save_player(player)
        return player

    @app.get("/api/teams")
    def get_teams() -> list[RosterTeam]:
        return store.list_teams()

    @app.get("/api/players")
    def get_players() -> list[Player]:
        return store.list_players()

    @app.post("/api/players", status_code=201)
    def create_player(request: EditPlayer) -> Player:
        check_team(request.current_team_id)
        player = Player(id=uuid4().hex, **request.model_dump())
        store.save_player(player)
        return player

    @app.post("/api/players/{player_id}")
    def edit_player(player_id: str, request: EditPlayer) -> Player:
        original = find_player(player_id)
        check_team(request.current_team_id)
        player = original.model_copy(update=request.model_dump())
        store.save_player(player)
        return player

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
        check_team(request.team_a_id)
        check_team(request.team_b_id)
        if request.team_a_id is not None and request.team_a_id == request.team_b_id:
            raise reject("same_team", "Choose two different Teams.", 422)
        teams_by_id = {team.id: team for team in store.list_teams()}
        roster_a = (
            teams_by_id[request.team_a_id] if request.team_a_id else store.add_team(request.team_a)
        )
        roster_b = (
            teams_by_id[request.team_b_id] if request.team_b_id else store.add_team(request.team_b)
        )
        series = Series(
            patch=request.patch,
            record_type=request.record_type,
            id=uuid4().hex,
            profile_id=profile.id,
            teams=(
                Team(id="A", name=roster_a.name, roster_id=roster_a.id),
                Team(id="B", name=roster_b.name, roster_id=roster_b.id),
            ),
            our_team=request.our_team,
            rule_snapshot=snapshot,
        )
        store.create(series)
        return view(series)

    @app.get("/api/series/{identifier}")
    def get_series(identifier: str) -> SeriesView:
        return view(read(identifier))

    def setup_assignments(series: Series, side: str, first: TeamId) -> tuple[Assignment, ...]:
        settings = series.rule_snapshot
        # Historical snapshots predate configurable Side/First Selection settings.
        if settings.sides is None:
            settings = settings.model_copy(update={"sides": profiles()[series.profile_id].sides})
        try:
            return game_assignments(settings, side, first)
        except ValueError as error:
            raise reject(
                str(error), "Choose Side and Draft Position from the Series rules.", 422
            ) from None

    @app.post("/api/series/{identifier}/games", status_code=201)
    def start_game(identifier: str, request: StartGame) -> SeriesView:
        series = read(identifier)
        profile = profiles()[series.profile_id]
        if (
            series.games
            and not series.games[-1].voided
            and not derive_state(
                series.rule_snapshot, profile.catalog, series.games, series.games[-1]
            ).complete
        ):
            raise reject(
                "draft_incomplete", "Complete the current draft before starting the next Game."
            )
        if sum(not g.voided for g in series.games) >= series.rule_snapshot.series_format.games:
            raise reject("series_full", "All Games in this Series Format have been started.")
        if derive_progress(series.rule_snapshot, series.games).ended:
            raise reject("series_ended", "The Series has reached its deciding Game.")
        assignments = setup_assignments(series, request.team_a_side, request.first_pick_team)
        game = Game(
            id=uuid4().hex,
            number=max((g.number for g in series.games), default=0) + 1,
            lineups=series.games[-1].lineups if series.games else {"A": (), "B": ()},
            assignments=assignments,
            first_selection_holder=(
                request.first_selection_holder
                if "first_selection_holder" in request.model_fields_set
                else first_selection_prefill(
                    series.rule_snapshot,
                    series.games,
                    max((g.number for g in series.games), default=0) + 1,
                )
            ),
            first_selection_choice=request.first_selection_choice,
            patch=request.patch if request.patch is not None else series.patch,
        )
        store.add_game(identifier, game)
        return view(read(identifier))

    def find_game(series: Series, game_id: str) -> Game:
        game = next((g for g in series.games if g.id == game_id), None)
        if game is None:
            raise reject("game_not_found", "Game not found.", 404)
        return game

    def replay_candidate(identifier: str, game_id: str, request: ReplayGame) -> tuple[Series, Game]:
        series = read(identifier)
        source = find_game(series, game_id)
        profile = profiles()[series.profile_id]
        side = request.team_a_side or next(a.side for a in source.assignments if a.team_id == "A")
        first: TeamId = (
            request.first_pick_team
            if request.first_pick_team is not None
            else next(a.team_id for a in source.assignments if a.position == "first")
        )
        lineups = request.lineups if request.lineups is not None else source.lineups
        if set(lineups) != {"A", "B"}:
            raise reject("invalid_lineup_size", "Both Team Lineups are required.", 422)
        seen: set[str] = set()
        for team in series.teams:
            ids = lineups[team.id]
            if len(ids) != len(set(ids)) or len(ids) > profile.team_size:
                raise reject(
                    "invalid_lineup_size",
                    "Choose distinct Players up to the Title's team size.",
                    422,
                )
            for player_id in ids:
                player = find_player(player_id)
                if (
                    player.current_team_id != team.roster_id
                    and player_id not in source.lineups[team.id]
                ):
                    raise reject("player_not_on_roster", "Choose Players from this Team's Roster.")
                if player_id in seen:
                    raise reject(
                        "player_on_other_lineup", "A Player can play for only one Team in a Game."
                    )
                seen.add(player_id)
        assignments = setup_assignments(series, side, first)
        prefill = source.model_copy(
            update={
                "assignments": assignments,
                "lineups": lineups,
                "patch": request.patch if "patch" in request.model_fields_set else source.patch,
            }
        )
        try:
            replay = create_replay(
                series.rule_snapshot,
                profile.catalog,
                series.games,
                source,
                uuid4().hex,
                request.draft_choice,
                prefill,
            )
        except ValueError as error:
            raise reject(
                str(error),
                "Replay must preserve Structural Invariants and follow the latest Voided attempt.",
            ) from None
        replay = replay.model_copy(
            update={
                name: getattr(request, name)
                for name in ("first_selection_holder", "first_selection_choice")
                if name in request.model_fields_set
            }
        )
        return series, replay

    @app.post("/api/series/{identifier}/games/{game_id}/replay-preview")
    def preview_replay(identifier: str, game_id: str, request: ReplayGame) -> GameView:
        series, replay = replay_candidate(identifier, game_id, request)
        return GameView(
            **replay.model_dump(),
            state=derive_state(
                series.rule_snapshot,
                profiles()[series.profile_id].catalog,
                series.games + (replay,),
                replay,
            ),
        )

    @app.post("/api/series/{identifier}/games/{game_id}/replay", status_code=201)
    def replay_game(identifier: str, game_id: str, request: ReplayGame) -> SeriesView:
        _, replay = replay_candidate(identifier, game_id, request)
        store.add_game(identifier, replay)
        return view(read(identifier))

    @app.post("/api/series/{identifier}/games/{game_id}/first-selection")
    def edit_first_selection(identifier: str, game_id: str, request: FirstSelection) -> SeriesView:
        game = find_game(read(identifier), game_id)
        store.save_first_selection(game.model_copy(update=request.model_dump()))
        return view(read(identifier))

    @app.post("/api/series/{identifier}/games/{game_id}/winner")
    def edit_winner(identifier: str, game_id: str, request: EditWinner) -> SeriesView:
        game = find_game(read(identifier), game_id)
        store.save_winner(game.id, request.winner)
        return view(read(identifier))

    @app.post("/api/series/{identifier}/games/{game_id}/void")
    def void_game(identifier: str, game_id: str) -> SeriesView:
        game = find_game(read(identifier), game_id)
        store.void_game(game.id)
        return view(read(identifier))

    @app.post("/api/series/{identifier}/games/{game_id}/lineups")
    def edit_lineup(identifier: str, game_id: str, request: EditLineup) -> SeriesView:
        series = read(identifier)
        game = find_game(series, game_id)
        ids = request.player_ids
        if len(ids) != len(set(ids)) or len(ids) > profiles()[series.profile_id].team_size:
            raise reject(
                "invalid_lineup_size", "Choose distinct Players up to the Title's team size.", 422
            )
        team = next(t for t in series.teams if t.id == request.team_id)
        for player_id in ids:
            player = find_player(player_id)
            if (
                player.current_team_id != team.roster_id
                and player_id not in game.lineups[request.team_id]
            ):
                raise reject("player_not_on_roster", "Choose Players from this Team's Roster.")
            if any(
                player_id in lineup
                for key, lineup in game.lineups.items()
                if key != request.team_id
            ):
                raise reject(
                    "player_on_other_lineup", "A Player can play for only one Team in a Game."
                )
        assigned = {a.player_id for a in game.player_assignments}
        if (set(game.lineups[request.team_id]) - set(ids)) & assigned:
            raise reject(
                "assigned_player",
                "Clear the Player Assignment before removing its Player from the Lineup.",
            )
        store.save_lineup(game.id, request.team_id, ids)
        return view(read(identifier))

    @app.post("/api/series/{identifier}/games/{game_id}/player-assignments")
    def edit_player_assignment(
        identifier: str, game_id: str, request: EditPlayerAssignment
    ) -> SeriesView:
        series = read(identifier)
        game = find_game(series, game_id)
        pick = next(
            (a for a in game.actions if a.turn_index == request.turn_index and a.kind == "pick"),
            None,
        )
        if pick is None:
            raise reject("not_a_pick", "Assign Players only to recorded picks.")
        if request.player_id is not None:
            if request.player_id not in game.lineups[pick.team_id]:
                raise reject(
                    "player_not_in_lineup", "Choose a Player from this Game's Team Lineup."
                )
            if any(
                a.player_id == request.player_id and a.turn_index != pick.turn_index
                for a in game.player_assignments
            ):
                raise reject("player_already_assigned", "Each Player plays one Character per Game.")
        store.save_player_assignment(game.id, request.turn_index, request.player_id)
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

    @app.post("/api/series/{identifier}/games/{game_id}/actions/{turn_index}/correct")
    def correct(
        identifier: str, game_id: str, turn_index: int, request: CorrectAction
    ) -> SeriesView:
        series = read(identifier)
        game = next((g for g in series.games if g.id == game_id), None)
        if game is None:
            raise reject("game_not_found", "Game not found.", 404)
        try:
            corrected = correct_action(
                series.rule_snapshot,
                profiles()[series.profile_id].catalog,
                game,
                turn_index,
                request.character_id,
            )
        except ValueError as error:
            raise reject(
                str(error), "Choose an existing Character and recorded turn.", 422
            ) from error
        before = next(a for a in game.actions if a.turn_index == turn_index)
        after = next(a for a in corrected.actions if a.turn_index == turn_index)
        store.save_correction(before, game, after)
        return view(read(identifier))

    @app.post("/api/series/{identifier}/games/{game_id}/actions/{turn_index}/acknowledge")
    def acknowledge(
        identifier: str,
        game_id: str,
        turn_index: int,
        request: AcknowledgeViolation,
    ) -> SeriesView:
        series = read(identifier)
        game = next((g for g in series.games if g.id == game_id), None)
        if game is None:
            raise reject("game_not_found", "Game not found.", 404)
        try:
            acknowledged = acknowledge_violation(
                series.rule_snapshot,
                profiles()[series.profile_id].catalog,
                series.games,
                game,
                turn_index,
                request.rule,
                request.reason,
            )
        except ValueError as error:
            raise reject(str(error), "This Violation no longer exists.", 404) from error
        store.save_acknowledgements(acknowledged)
        return view(read(identifier))

    @app.post("/api/series/{identifier}/games/{game_id}/actions/{turn_index}/clear")
    def clear(identifier: str, game_id: str, turn_index: int) -> SeriesView:
        series = read(identifier)
        game = next((g for g in series.games if g.id == game_id), None)
        if game is None:
            raise reject("game_not_found", "Game not found.", 404)
        try:
            clear_action(series.games, game, turn_index)
        except ValueError as error:
            raise reject(
                str(error), "Only the latest action of the current Game can be cleared."
            ) from error
        store.save_correction(game.actions[-1], game, None)
        return view(read(identifier))

    return app
