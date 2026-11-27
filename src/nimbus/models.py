"""Values shared by the profile, pure engine and API boundaries."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

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
    id: Literal["off", "soft", "hard", "custom"] = "hard"
    lock_reach: Literal["none", "picking_team", "both_teams"] = "both_teams"
    lock_sources: Literal["picks", "picks_and_bans"] = "picks"

    @model_validator(mode="after")
    def check_combination(self) -> "Fearless":
        if self.lock_reach == "picking_team" and self.lock_sources == "picks_and_bans":
            raise ValueError(
                "picking_team with picks_and_bans is not a defined Fearless combination"
            )
        preset = {
            ("none", "picks"): "off",
            ("picking_team", "picks"): "soft",
            ("both_teams", "picks"): "hard",
        }.get((self.lock_reach, self.lock_sources), "custom")
        object.__setattr__(self, "id", preset)
        return self


class SeriesFormat(Value):
    kind: Literal["best_of", "fixed_length"] = "best_of"
    games: int = Field(default=5, strict=True, gt=0)

    @model_validator(mode="after")
    def check_odd(self) -> "SeriesFormat":
        if self.kind == "best_of" and self.games % 2 == 0:
            raise ValueError("Best-of requires an odd number of Games")
        return self


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
    patch: str | None = None
    id: str
    number: int
    assignments: tuple[Assignment, ...]
    actions: tuple[DraftAction, ...] = ()


class Series(Value):
    patch: str | None = None
    record_type: Literal["official", "scrim"] = "official"
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
