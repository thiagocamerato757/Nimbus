"""Values shared by the profile, pure engine and API boundaries."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

TeamId = Literal["A", "B"]
Position = Literal["first", "second"]
ActionKind = Literal["ban", "pick"]


class Value(BaseModel):
    model_config = ConfigDict(frozen=True)


class Character(Value):
    id: str
    name: str
    aliases: tuple[str, ...] = ()
    retired: bool = False


class Turn(Value):
    position: Position
    kind: ActionKind


class DraftOrder(Value):
    id: str
    name: str
    turns: tuple[Turn, ...]


class RuleSettings(Value):
    banning_locked: Literal["allow", "warn", "reject"]
    same_character_twice: Literal["allow", "reject"]
    voided_games_count: bool


class Fearless(Value):
    id: Literal["hard"] = "hard"
    lock_reach: Literal["both_teams"] = "both_teams"
    lock_sources: Literal["picks"] = "picks"


class SeriesFormat(Value):
    kind: Literal["best_of"] = "best_of"
    games: Literal[5] = 5


class RuleSnapshot(Value):
    draft_order: DraftOrder
    rule_settings: RuleSettings
    fearless: Fearless = Fearless()
    series_format: SeriesFormat = SeriesFormat()


class Team(Value):
    id: TeamId
    name: str


class Assignment(Value):
    team_id: TeamId
    side: str
    position: Position


class DraftAction(Value):
    turn_index: int
    team_id: TeamId
    kind: ActionKind
    character_id: str


class Game(Value):
    id: str
    number: int
    assignments: tuple[Assignment, ...]
    actions: tuple[DraftAction, ...] = ()


class Series(Value):
    id: str
    profile_id: str
    teams: tuple[Team, ...]
    our_team: TeamId | None
    rule_snapshot: RuleSnapshot
    games: tuple[Game, ...] = ()


class NextTurn(Value):
    index: int
    team_id: TeamId
    kind: ActionKind


class DraftState(Value):
    locks: dict[TeamId, tuple[str, ...]]
    available: dict[TeamId, tuple[str, ...]]
    next_turn: NextTurn | None
    complete: bool


class GameView(Game):
    state: DraftState


class SeriesView(Series):
    games: tuple[GameView, ...] = ()
