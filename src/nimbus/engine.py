"""Pure draft rules: snapshots, catalogs and recorded actions in; derived state out.

No database, profile loader or Title identifiers belong at this seam.
"""

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import NamedTuple

from nimbus.models import (
    Acknowledgement,
    Assignment,
    CarriedAcknowledgement,
    Character,
    DraftAction,
    DraftState,
    Game,
    NextTurn,
    Notice,
    OverrideReason,
    RuleSnapshot,
    SeriesProgress,
    TeamId,
    Violation,
)


def game_assignments(
    settings: RuleSnapshot, team_a_side: str, first_pick_team: TeamId
) -> tuple[Assignment, ...]:
    """Record the two results independently unless the snapshot couples them."""
    if settings.sides is None or team_a_side not in settings.sides:
        raise ValueError("unknown_side")
    if settings.sides_coupled:
        expected = "A" if team_a_side == settings.first_pick_side else "B"
        if first_pick_team != expected:
            raise ValueError("coupled_position")
    teams: tuple[TeamId, TeamId] = ("A", "B")
    return tuple(
        Assignment(
            team_id=team,
            side=team_a_side
            if team == "A"
            else next(s for s in settings.sides if s != team_a_side),
            position="first" if team == first_pick_team else "second",
        )
        for team in teams
    )


def first_selection_prefill(
    settings: RuleSnapshot, games: Sequence[Game], number: int
) -> TeamId | None:
    """Offer editable metadata from the previous logical Game, never a ruling."""
    previous = next((g for g in reversed(games) if g.number == number - 1 and not g.voided), None)
    if previous is None or previous.winner is None:
        return None
    policy = settings.default_first_selection_holder
    if policy == "winner":
        return previous.winner
    if policy == "loser":
        return "B" if previous.winner == "A" else "A"
    if policy == "alternate" and previous.first_selection_holder is not None:
        return "B" if previous.first_selection_holder == "A" else "A"
    return None


def current_game(games: Sequence[Game]) -> Game | None:
    """The last Game of the Series, voided or not (ADR-0008, amended 2026-11-27).

    Live entry, clearing and starting the next Game all use this one definition;
    earlier Games are fixed only by replacement.
    """
    return games[-1] if games else None


def draft_complete(settings: RuleSnapshot, game: Game) -> bool:
    return len(game.actions) == len(settings.draft_order.turns)


def is_drafted_or_closed(settings: RuleSnapshot, game: Game) -> bool:
    """The one rule for a Game that has a result: Drafted or Closed.

    Setting a winner, counting it in Series progress and starting the next Game
    all use it (#13, Q11; ADR-0034, amended 2026-11-27).
    """
    return not game.voided and draft_complete(settings, game)


class _Outcome(NamedTuple):
    score: dict[TeamId, int]
    pending: tuple[int, ...]
    ended: bool
    deciding: int | None
    past: tuple[int, ...]


def _outcome(settings: RuleSnapshot, games: Sequence[Game]) -> _Outcome:
    counted = [g for g in games if not g.voided]
    # Only a Drafted or Closed Game has a result; a winner left on a Game that
    # returned to Drafting is ignored until its draft is complete again.
    with_result = [g for g in games if is_drafted_or_closed(settings, g)]
    score: dict[TeamId, int] = {"A": 0, "B": 0}
    pending = tuple(g.number for g in with_result if g.winner is None)
    deciding = None
    for game in with_result:
        if game.winner is not None:
            score[game.winner] += 1
            if deciding is None and score[game.winner] >= settings.series_format.games // 2 + 1:
                deciding = game.number
    if settings.series_format.kind == "best_of":
        ended = deciding is not None and not pending
        past = tuple(g.number for g in counted if deciding is not None and g.number > deciding)
        return _Outcome(score, pending, ended, deciding, past)
    return _Outcome(score, pending, len(with_result) >= settings.series_format.games, None, ())


def derive_progress(settings: RuleSnapshot, games: Sequence[Game]) -> SeriesProgress:
    """Recompute score and completion without changing or discarding Games."""
    outcome = _outcome(settings, games)
    return SeriesProgress(
        score=outcome.score,
        pending_results=outcome.pending,
        ended=outcome.ended,
        deciding_game=outcome.deciding,
        games_past_decision=outcome.past,
        can_start_next=_next_game_block(settings, games, outcome.ended) is None,
    )


def next_game_block(settings: RuleSnapshot, games: Sequence[Game]) -> str | None:
    """Why the next ordinary Game cannot start, or None when it can.

    This one ordered gate gives ``can_start_next``, the start route and the
    Replay gate their answer (ADR-0010, ADR-0034, amended 2026-11-27). An ended
    Series comes first, so it is never told to replay.
    """
    return _next_game_block(settings, games, _outcome(settings, games).ended)


def _next_game_block(settings: RuleSnapshot, games: Sequence[Game], ended: bool) -> str | None:
    if ended:
        return "series_ended"
    current = current_game(games)
    if current is not None and current.voided:
        return "replay_required"
    if current is not None and not is_drafted_or_closed(settings, current):
        return "draft_incomplete"
    if sum(not g.voided for g in games) >= settings.series_format.games:
        return "series_full"
    return None


def replay_block(settings: RuleSnapshot, games: Sequence[Game], source: Game) -> str | None:
    """Why ``source`` cannot be replayed now, or None when it can.

    A Replay is how the next Game starts after a void, so it passes the same
    gate: the gate must answer "replay required", and ``source`` must be that
    Voided current Game.
    """
    block = next_game_block(settings, games)
    if block == "series_ended":
        return block
    current = current_game(games)
    if block != "replay_required" or current is None or current.id != source.id:
        return "replay_unavailable"
    return None


def record_first_selection(game: Game, sent: Mapping[str, str | None]) -> Game:
    """The one First Selection rule for Start Game, Replay and edits (#14).

    ``sent`` holds only the fields the analyst sent. Unsent fields are kept,
    except a stored choice when the holder changes, because it belonged to the
    other Team. A choice always belongs to a holder (amended 2026-11-27).
    """
    holder = sent.get("first_selection_holder", game.first_selection_holder)
    same_holder = holder == game.first_selection_holder
    choice = sent.get(
        "first_selection_choice", game.first_selection_choice if same_holder else None
    )
    if choice is not None and holder is None:
        raise ValueError("choice_without_holder")
    return game.model_copy(
        update={"first_selection_holder": holder, "first_selection_choice": choice}
    )


def _base_state(
    settings: RuleSnapshot, catalog: Sequence[Character], games: Sequence[Game], game: Game
) -> DraftState:
    teams: tuple[TeamId, TeamId] = ("A", "B")
    locked: dict[TeamId, set[str]] = {team: set() for team in teams}
    variant = settings.fearless
    for earlier in games:
        if earlier.number >= game.number or (
            earlier.voided and not settings.rule_settings.voided_games_count
        ):
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
    complete = draft_complete(settings, game)
    # Everything still needed to reach Closed: every pick turn in the Draft
    # Order, recorded or not, needs its Player Assignment. A stored winner that
    # does not count yet is shown as a note, not as missing (amended 2026-11-27).
    assigned = {a.turn_index for a in game.player_assignments}
    recorded_picks = {a.turn_index for a in game.actions if a.kind == "pick"}
    pick_turns = {i for i, t in enumerate(settings.draft_order.turns) if t.kind == "pick"}
    missing = []
    if not complete:
        missing.append("draft")
    if game.winner is None:
        missing.append("winner")
    if not pick_turns <= assigned & recorded_picks:
        missing.append("player_assignments")
    next_turn = None
    if index < len(settings.draft_order.turns) and not game.voided:
        turn = settings.draft_order.turns[index]
        team = next(a.team_id for a in game.assignments if a.position == turn.position)
        next_turn = NextTurn(index=index, team_id=team, kind=turn.kind)
    return DraftState(
        status=(
            "Voided"
            if game.voided
            else "Drafting"
            if not complete
            else "Drafted"
            if missing
            else "Closed"
        ),
        result_pending=complete and game.winner is None and not game.voided,
        missing=() if game.voided else tuple(missing),
        locks={team: tuple(sorted(locked[team])) for team in teams},
        available=available,
        next_turn=next_turn,
        complete=complete,
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


def structural_error(
    settings: RuleSnapshot, catalog: Sequence[Character], game: Game, action: DraftAction
) -> str | None:
    """The Structural Invariants of one Draft Action in its turn (ADR-0009).

    Live entry, corrections and copied Replay drafts share this check, and it is
    never overridden. ``game`` holds the Draft Actions recorded before this one.
    The action fills the next turn (one Draft Action per turn), the turn exists
    in the Draft Order and belongs to the action's Team and kind, a pick is not
    skipped, and the Character is in the Character Catalog. A Retired Character
    is in the Catalog, so it passes here; only a new entry refuses it (see
    ``check_entry``).
    """
    turns = settings.draft_order.turns
    if action.turn_index != len(game.actions) or not 0 <= action.turn_index < len(turns):
        return "invalid_turn"
    turn = turns[action.turn_index]
    owners = [a.team_id for a in game.assignments if a.position == turn.position]
    if owners != [action.team_id] or action.kind != turn.kind:
        return "invalid_turn"
    if action.character_id is None:
        return "cannot_skip_pick" if action.kind == "pick" else None
    if not any(c.id == action.character_id for c in catalog):
        return "unknown_character"
    return None


def check_entry(
    settings: RuleSnapshot,
    catalog: Sequence[Character],
    games: Sequence[Game],
    game: Game,
    action: DraftAction,
) -> str | None:
    """Structural checks always precede overridable Game Rules."""
    if game.voided:
        return "game_voided"
    if draft_complete(settings, game):
        return "draft_complete"
    error = structural_error(settings, catalog, game, action)
    if error is not None or action.character_id is None:
        return error
    # A Retired Character is never offered for a new entry (BS-015, CONTEXT.md).
    if any(c.id == action.character_id and c.retired for c in catalog):
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
            and (not g.voided or settings.rule_settings.voided_games_count)
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
                    carried_from=acknowledgement.carried_from if acknowledgement else (),
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
    index = next((i for i, a in enumerate(game.actions) if a.turn_index == turn_index), None)
    if index is None:
        raise ValueError("action_not_found")
    action = game.actions[index]
    replacement = action.model_copy(update={"character_id": character_id})
    earlier = game.model_copy(update={"actions": game.actions[:index]})
    error = structural_error(settings, catalog, earlier, replacement)
    if error is not None:
        raise ValueError(error)
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
    """Remove only the most recent action of the current Game.

    A voided current Game has nothing to clear; earlier Games are corrected by
    replacement (ADR-0008, amended 2026-11-27).
    """
    current = current_game(games)
    if (
        current is None
        or current.id != game.id
        or game.voided
        or not game.actions
        or game.actions[-1].turn_index != turn_index
    ):
        raise ValueError("cannot_clear_action")
    return game.model_copy(update={"actions": game.actions[:-1]})


def void_game(games: Sequence[Game], game: Game) -> Game:
    """Void only the current Game (ADR-0034, amended 2026-11-27).

    Voiding an earlier Game while a later one exists would change the Series'
    numbering and the Fearless Locks of the Game in progress.
    """
    current = current_game(games)
    if current is None or current.id != game.id:
        raise ValueError("void_not_current")
    return game.model_copy(update={"voided": True})


def create_replay(
    settings: RuleSnapshot,
    catalog: Sequence[Character],
    games: Sequence[Game],
    source: Game,
    identifier: str,
    choice: str,
    prefill: Game | None = None,
) -> Game:
    """Create a linked attempt; copied Game Rules flag, structural failures reject.

    The First Selection holder is left for the caller to record as the analyst
    sent it; a pre-fill is for display only and is never applied here.
    """
    error = replay_block(settings, games, source)
    if error is not None:
        raise ValueError(error)
    if choice not in {"copy_draft", "new_draft"}:
        raise ValueError("replay_choice_required")
    template = prefill or source
    replay = Game(
        id=identifier,
        number=source.number,
        replay_of=source.id,
        assignments=template.assignments,
        patch=template.patch,
        lineups=template.lineups,
    )
    if choice == "new_draft":
        return replay
    # Draft Positions are editable, but not together with a copied draft
    # (ADR-0034, amended 2026-11-27): the copied turns belong to the source's.
    if _draft_positions(replay) != _draft_positions(source):
        raise ValueError("copy_requires_same_draft_positions")
    for action in source.actions:
        error = structural_error(settings, catalog, replay, action)
        if error is not None:
            raise ValueError(error)
        original_prefix = source.model_copy(update={"actions": source.actions[: action.turn_index]})
        mapped_prefix = original_prefix.model_copy(update={"id": replay.id})
        acknowledgements = replay.acknowledgements
        for rule in _rules(settings, catalog, games, replay, action):
            original = next(
                (
                    a
                    for a in source.acknowledgements
                    if a.turn_index == action.turn_index
                    and a.rule == rule
                    and a.fingerprint
                    == _fingerprint(settings, rule, games, original_prefix, action)
                ),
                None,
            )
            fingerprint = _fingerprint(settings, rule, games, replay, action)
            if original is not None and fingerprint == _fingerprint(
                settings, rule, games, mapped_prefix, action
            ):
                acknowledgements += (
                    Acknowledgement(
                        turn_index=action.turn_index,
                        rule=rule,
                        fingerprint=fingerprint,
                        reason=original.reason,
                        carried_from=original.carried_from
                        + (
                            CarriedAcknowledgement(
                                game_id=source.id,
                                game_number=source.number,
                                fingerprint=original.fingerprint,
                            ),
                        ),
                    ),
                )
        replay = replay.model_copy(
            update={
                "actions": replay.actions + (action,),
                "acknowledgements": acknowledgements,
            }
        )
    return replay


def _draft_positions(game: Game) -> dict[TeamId, str]:
    return {a.team_id: a.position for a in game.assignments}
