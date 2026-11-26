"""Pure draft rules: snapshots, catalogs and recorded actions in; derived state out.

No database, profile loader or Title identifiers belong at this seam.
"""

from collections.abc import Sequence

from nimbus.models import Character, DraftAction, DraftState, Game, NextTurn, RuleSnapshot, TeamId


def derive_state(
    settings: RuleSnapshot, catalog: Sequence[Character], games: Sequence[Game], game: Game
) -> DraftState:
    locked = {
        action.character_id
        for earlier in games
        if earlier.number < game.number
        for action in earlier.actions
        if action.kind == "pick"
    }
    used = {action.character_id for action in game.actions}
    available = tuple(
        sorted(
            character.id
            for character in catalog
            if not character.retired and character.id not in locked | used
        )
    )
    index = len(game.actions)
    next_turn = None
    if index < len(settings.draft_order.turns):
        turn = settings.draft_order.turns[index]
        team = next(a.team_id for a in game.assignments if a.position == turn.position)
        next_turn = NextTurn(index=index, team_id=team, kind=turn.kind)
    teams: tuple[TeamId, TeamId] = ("A", "B")
    return DraftState(
        locks={team: tuple(sorted(locked)) for team in teams},
        available={team: available for team in teams},
        next_turn=next_turn,
        complete=next_turn is None,
    )


def validate_action(
    settings: RuleSnapshot,
    catalog: Sequence[Character],
    games: Sequence[Game],
    game: Game,
    action: "DraftAction",
) -> str | None:
    """Return the scoped Game Rule rejection, without recording an action.

    Duplicate and locked-ban policy enforcement are later increments. This
    walking skeleton enforces Fearless Locks on picks (BS-009) only.
    """
    state = derive_state(settings, catalog, games, game)
    if action.kind == "pick" and action.character_id in state.locks[action.team_id]:
        return "fearless_lock"
    return None
