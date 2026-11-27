"""Pure draft rules: snapshots, catalogs and recorded actions in; derived state out.

No database, profile loader or Title identifiers belong at this seam.
"""

import hashlib
import json
from collections.abc import Sequence

from nimbus.models import (
    Acknowledgement,
    Character,
    DraftAction,
    DraftState,
    Game,
    NextTurn,
    Notice,
    OverrideReason,
    RuleSnapshot,
    TeamId,
    Violation,
)


def _base_state(
    settings: RuleSnapshot, catalog: Sequence[Character], games: Sequence[Game], game: Game
) -> DraftState:
    teams: tuple[TeamId, TeamId] = ("A", "B")
    locked: dict[TeamId, set[str]] = {team: set() for team in teams}
    variant = settings.fearless
    for earlier in games:
        if earlier.number >= game.number:
            continue
        for action in earlier.actions:
            if action.character_id is None:
                continue
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
    """Return the first Game Rule rejection without recording an action."""
    rules = _rules(settings, catalog, games, game, action)
    return rules[0] if rules else None


def check_entry(
    settings: RuleSnapshot,
    catalog: Sequence[Character],
    games: Sequence[Game],
    game: Game,
    action: DraftAction,
) -> str | None:
    """Structural checks always precede overridable Game Rules."""
    turn = _base_state(settings, catalog, games, game).next_turn
    if turn is None:
        return "draft_complete"
    if (action.turn_index, action.team_id, action.kind) != (turn.index, turn.team_id, turn.kind):
        return "invalid_turn"
    if action.character_id is None:
        return "cannot_skip_pick" if action.kind == "pick" else None
    if not any(c.id == action.character_id and not c.retired for c in catalog):
        return "unknown_character"
    return validate_action(settings, catalog, games, game, action)


GAME_RULES = {"fearless_lock", "wasted_ban", "duplicate_character"}


def _fingerprint(
    settings: RuleSnapshot, rule: str, games: Sequence[Game], game: Game, action: DraftAction
) -> str:
    if rule == "duplicate_character":
        causes = [
            (game.id, a.model_dump()) for a in game.actions if a.character_id == action.character_id
        ]
    else:
        causes = [
            (g.id, a.model_dump())
            for g in games
            if g.number < game.number
            for a in g.actions
            if a.character_id == action.character_id
            and (a.kind == "pick" or settings.fearless.lock_sources == "picks_and_bans")
            and (
                settings.fearless.lock_reach == "both_teams"
                or a.team_id
                == (
                    action.team_id
                    if rule == "fearless_lock"
                    else "B"
                    if action.team_id == "A"
                    else "A"
                )
            )
        ]
    payload = {"rule": rule, "action": action.model_dump(), "causes": causes}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def _rules(
    settings: RuleSnapshot,
    catalog: Sequence[Character],
    games: Sequence[Game],
    game: Game,
    action: DraftAction,
) -> tuple[str, ...]:
    if action.character_id is None:
        return ()
    rules = []
    state = _base_state(settings, catalog, games, game)
    if action.kind == "pick" and action.character_id in state.locks[action.team_id]:
        rules.append("fearless_lock")
    opponent: TeamId = "B" if action.team_id == "A" else "A"
    if (
        action.kind == "ban"
        and settings.rule_settings.banning_locked == "reject"
        and action.character_id in state.locks[opponent]
    ):
        rules.append("wasted_ban")
    if settings.rule_settings.same_character_twice == "reject" and any(
        a.character_id == action.character_id for a in game.actions
    ):
        rules.append("duplicate_character")
    return tuple(rules)


def record_entry(
    settings: RuleSnapshot,
    catalog: Sequence[Character],
    games: Sequence[Game],
    game: Game,
    action: DraftAction,
    reason: OverrideReason | None = None,
) -> Game:
    error = check_entry(settings, catalog, games, game, action)
    if error and (error not in GAME_RULES or reason is None):
        raise ValueError(error)
    acknowledgements = game.acknowledgements
    for rule in _rules(settings, catalog, games, game, action):
        if reason is not None:
            acknowledgements += (
                Acknowledgement(
                    turn_index=action.turn_index,
                    rule=rule,
                    fingerprint=_fingerprint(settings, rule, games, game, action),
                    reason=reason,
                ),
            )
    return game.model_copy(
        update={"actions": game.actions + (action,), "acknowledgements": acknowledgements}
    )


def derive_state(
    settings: RuleSnapshot, catalog: Sequence[Character], games: Sequence[Game], game: Game
) -> DraftState:
    state = _base_state(settings, catalog, games, game)
    violations = []
    notices = []
    for index, action in enumerate(game.actions):
        prefix = game.model_copy(update={"actions": game.actions[:index]})
        for rule in _rules(settings, catalog, games, prefix, action):
            acknowledgement = next(
                (
                    a
                    for a in game.acknowledgements
                    if a.turn_index == action.turn_index
                    and a.rule == rule
                    and a.fingerprint == _fingerprint(settings, rule, games, prefix, action)
                ),
                None,
            )
            violations.append(
                Violation(
                    turn_index=action.turn_index,
                    rule=rule,
                    status="acknowledged" if acknowledgement else "open",
                    reason=acknowledgement.reason if acknowledgement else None,
                )
            )
        opponent: TeamId = "B" if action.team_id == "A" else "A"
        if (
            action.kind == "ban"
            and action.character_id is not None
            and settings.rule_settings.banning_locked == "warn"
            and action.character_id in state.locks[opponent]
        ):
            notices.append(Notice(turn_index=action.turn_index, rule="wasted_ban"))
    counts: dict[str, int] = {}
    for recorded in games:
        for ack in recorded.acknowledgements:
            if ack.reason.category == "profile_mismatch":
                counts[ack.rule] = counts.get(ack.rule, 0) + 1
    return state.model_copy(
        update={
            "violations": tuple(violations),
            "notices": tuple(notices),
            "profile_update_hints": tuple(
                sorted(rule for rule, count in counts.items() if count >= 2)
            ),
        }
    )


def correct_action(
    settings: RuleSnapshot,
    catalog: Sequence[Character],
    game: Game,
    turn_index: int,
    character_id: str | None,
) -> Game:
    """Replace one recorded Character; Game Rules never block corrections."""
    action = next((a for a in game.actions if a.turn_index == turn_index), None)
    if action is None:
        raise ValueError("action_not_found")
    if turn_index < 0 or turn_index >= len(settings.draft_order.turns):
        raise ValueError("invalid_turn")
    if character_id is None and action.kind == "pick":
        raise ValueError("cannot_skip_pick")
    if character_id is not None and not any(c.id == character_id for c in catalog):
        raise ValueError("unknown_character")
    replacement = action.model_copy(update={"character_id": character_id})
    return game.model_copy(
        update={"actions": tuple(replacement if a == action else a for a in game.actions)}
    )


def acknowledge_violation(
    settings: RuleSnapshot,
    catalog: Sequence[Character],
    games: Sequence[Game],
    game: Game,
    turn_index: int,
    rule: str,
    reason: OverrideReason,
) -> Game:
    """Remember the currently broken rule, action and cause without changing it."""
    for index, action in enumerate(game.actions):
        if action.turn_index != turn_index:
            continue
        prefix = game.model_copy(update={"actions": game.actions[:index]})
        if rule not in _rules(settings, catalog, games, prefix, action):
            break
        acknowledgement = Acknowledgement(
            turn_index=turn_index,
            rule=rule,
            fingerprint=_fingerprint(settings, rule, games, prefix, action),
            reason=reason,
        )
        return game.model_copy(
            update={
                "acknowledgements": (acknowledgement,) + game.acknowledgements,
            }
        )
    raise ValueError("violation_not_found")


def clear_action(games: Sequence[Game], game: Game, turn_index: int) -> Game:
    """Remove only the most recent action of the current Game."""
    if (
        not games
        or games[-1].id != game.id
        or not game.actions
        or game.actions[-1].turn_index != turn_index
    ):
        raise ValueError("cannot_clear_action")
    return game.model_copy(update={"actions": game.actions[:-1]})
