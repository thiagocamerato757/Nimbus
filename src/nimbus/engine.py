"""Pure draft rules: snapshots, catalogs and recorded actions in; derived state out.

No database, profile loader or Title identifiers belong at this seam.
"""

from collections.abc import Sequence

from nimbus.models import Character, DraftAction, DraftState, Game, NextTurn, RuleSnapshot, TeamId


def derive_state(
    settings: RuleSnapshot, catalog: Sequence[Character], games: Sequence[Game], game: Game
) -> DraftState:
    teams: tuple[TeamId, TeamId] = ("A", "B")
    locked: dict[TeamId, set[str]] = {team: set() for team in teams}
    variant = settings.fearless
    for earlier in games:
        if earlier.number >= game.number:
            continue
        for action in earlier.actions:
            if action.kind == "ban" and variant.lock_sources != "picks_and_bans":
                continue
            for team in teams:
                if variant.lock_reach == "both_teams" or (
                    variant.lock_reach == "picking_team" and action.team_id == team
                ):
                    locked[team].add(action.character_id)
    used = {action.character_id for action in game.actions}
    available = {
        team: tuple(
            sorted(c.id for c in catalog if not c.retired and c.id not in locked[team] | used)
        )
        for team in teams
    }
    index = len(game.actions)
    next_turn = None
    if index < len(settings.draft_order.turns):
        turn = settings.draft_order.turns[index]
        team = next(a.team_id for a in game.assignments if a.position == turn.position)
        next_turn = NextTurn(index=index, team_id=team, kind=turn.kind)
    return DraftState(
        locks={team: tuple(sorted(locked[team])) for team in teams},
        available=available,
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
    """Return a Fearless rejection without recording an action."""
    state = derive_state(settings, catalog, games, game)
    if action.kind == "pick" and action.character_id in state.locks[action.team_id]:
        return "fearless_lock"
    opponent: TeamId = "B" if action.team_id == "A" else "A"
    if (
        action.kind == "ban"
        and action.character_id in state.locks[opponent]
        and settings.rule_settings.banning_locked == "reject"
    ):
        return "wasted_ban"
    return None
