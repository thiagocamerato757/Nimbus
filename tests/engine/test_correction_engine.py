"""BS-010 corrections through the title-agnostic engine interface."""

from nimbus.engine import derive_state
from nimbus.models import DraftAction, Game


def recorded_pick(profile, first_pick_index, character_id):
    """Skipped bans up to the first pick, then that pick: a contiguous record
    (one Draft Action per turn, ADR-0009), as live entry always produces."""
    turns = profile.snapshot().draft_order.turns
    bans = tuple(
        DraftAction(
            turn_index=i,
            team_id="A" if turns[i].position == "first" else "B",
            kind=turns[i].kind,
            character_id=None,
        )
        for i in range(first_pick_index)
    )
    pick = DraftAction(
        turn_index=first_pick_index, team_id="A", kind="pick", character_id=character_id
    )
    return (*bans, pick)


def test_bs010_correcting_earlier_pick_flags_unchanged_later_pick(
    profile, assignments, character_ids, first_pick_index
):
    # Parent BS-010: Given different Game 1/Game 3 picks, replacing Game 1's
    # Character with Game 3's saves it and exposes an Open Fearless Violation.
    from nimbus.engine import correct_action

    earlier = Game(
        id="one",
        number=1,
        assignments=assignments,
        actions=recorded_pick(profile, first_pick_index, character_ids[0]),
    )
    later = Game(
        id="three",
        number=3,
        assignments=assignments,
        actions=(
            DraftAction(
                turn_index=first_pick_index, team_id="A", kind="pick", character_id=character_ids[1]
            ),
        ),
    )
    corrected = correct_action(
        profile.snapshot(), profile.catalog, earlier, first_pick_index, character_ids[1]
    )
    state = derive_state(profile.snapshot(), profile.catalog, [corrected, later], later)
    assert corrected.actions[-1].character_id == character_ids[1]
    assert later.actions[0].character_id == character_ids[1]
    assert [(v.turn_index, v.rule, v.status) for v in state.violations] == [
        (first_pick_index, "fearless_lock", "open")
    ]


def test_bs010_acknowledging_open_violation_keeps_reason(
    profile, assignments, previous_pick, character_ids, first_pick_index
):
    # Parent BS-010: an Open rule/action/cause is acknowledged with its reason.
    from nimbus.engine import acknowledge_violation
    from nimbus.models import OverrideReason

    current = Game(
        id="three",
        number=3,
        assignments=assignments,
        actions=(
            DraftAction(
                turn_index=first_pick_index, team_id="A", kind="pick", character_id=character_ids[0]
            ),
        ),
    )
    reason = OverrideReason(category="official_ruling", note="Referee confirmed")
    acknowledged = acknowledge_violation(
        profile.snapshot(),
        profile.catalog,
        [previous_pick, current],
        current,
        first_pick_index,
        "fearless_lock",
        reason,
    )
    violation = derive_state(
        profile.snapshot(), profile.catalog, [previous_pick, acknowledged], acknowledged
    ).violations[0]
    assert (violation.status, violation.reason) == ("acknowledged", reason)


def test_bs010_clearing_latest_current_action_restores_its_turn(
    profile, assignments, character_ids
):
    # Parent BS-010: clearing only the current Game's latest action returns that turn.
    from nimbus.engine import clear_action

    current = Game(
        id="current",
        number=1,
        assignments=assignments,
        actions=(
            DraftAction(turn_index=0, team_id="A", kind="ban", character_id=character_ids[0]),
        ),
    )
    cleared = clear_action([current], current, 0)
    assert cleared.actions == ()
    assert (
        derive_state(profile.snapshot(), profile.catalog, [cleared], cleared).next_turn.index == 0
    )


import pytest
from hypothesis import given
from hypothesis import strategies as st


@pytest.mark.parametrize(
    "reach,sources",
    [
        ("none", "picks"),
        ("none", "picks_and_bans"),
        ("picking_team", "picks"),
        ("both_teams", "picks"),
        ("both_teams", "picks_and_bans"),
    ],
)
@given(data=st.data())
def test_bs010_correction_reversal_restores_derived_state_including_acknowledgements(
    profile,
    assignments,
    character_ids,
    reach,
    sources,
    data,
):
    # Parent BS-010 / ADR-0009: any correction and its reversal restore all
    # derived values, including previously acknowledged rule/action/cause.
    from nimbus.engine import correct_action, record_entry
    from nimbus.models import Fearless, OverrideReason

    settings = profile.snapshot().model_copy(
        update={
            "fearless": Fearless(lock_reach=reach, lock_sources=sources),
        }
    )
    chosen = data.draw(
        st.lists(st.sampled_from(character_ids), min_size=3, max_size=3, unique=True),
        label="original and replacement Characters",
    )
    games = []
    reason = OverrideReason(category="official_ruling", note="Acknowledged before correction")
    for number in (1, 2):
        game = Game(id=str(number), number=number, assignments=assignments)
        for _ in range(7):
            turn = derive_state(settings, profile.catalog, games + [game], game).next_turn
            action = DraftAction(
                turn_index=turn.index,
                team_id=turn.team_id,
                kind=turn.kind,
                character_id=None if turn.kind == "ban" else chosen[0],
            )
            game = record_entry(settings, profile.catalog, games + [game], game, action, reason)
        games.append(game)
    before = tuple(derive_state(settings, profile.catalog, games, g) for g in games)
    target = data.draw(st.integers(min_value=0, max_value=1), label="Game to correct")
    turn_index = data.draw(st.integers(min_value=0, max_value=6), label="turn to correct")
    original = games[target].actions[turn_index].character_id
    changed = correct_action(settings, profile.catalog, games[target], turn_index, chosen[1])
    changed_games = [changed if i == target else g for i, g in enumerate(games)]
    assert changed.actions[turn_index].character_id == chosen[1]
    restored = correct_action(settings, profile.catalog, changed, turn_index, original)
    restored_games = [restored if i == target else g for i, g in enumerate(changed_games)]
    assert (
        tuple(derive_state(settings, profile.catalog, restored_games, g) for g in restored_games)
        == before
    )
    if reach != "none":
        assert before[1].violations[0].status == "acknowledged"


def test_bs010_correction_can_choose_retired_character(profile, assignments, character_ids):
    from nimbus.engine import correct_action
    from nimbus.models import Character

    # Parent issue #11 acceptance: a correction can deliberately choose Retired.
    current = Game(
        id="current",
        number=1,
        assignments=assignments,
        actions=(
            DraftAction(turn_index=0, team_id="A", kind="ban", character_id=character_ids[0]),
        ),
    )
    catalog = (*profile.catalog, Character(id="retired", name="Retired", retired=True))
    corrected = correct_action(profile.snapshot(), catalog, current, 0, "retired")
    assert corrected.actions[0].character_id == "retired"


@pytest.mark.parametrize(
    "turn,character,error",
    [
        (99, "known", "action_not_found"),
        (0, "unknown", "unknown_character"),
        (6, None, "cannot_skip_pick"),
    ],
)
def test_bs010_structural_invariants_still_apply(
    profile,
    assignments,
    character_ids,
    turn,
    character,
    error,
):
    from nimbus.engine import correct_action

    # Parent BS-010 acceptance: replacement may break Game Rules, never structure.
    # The recorded turns are contiguous (one Draft Action per turn, ADR-0009).
    settings = profile.snapshot()
    turns = settings.draft_order.turns
    pick = next(i for i, t in enumerate(turns) if t.kind == "pick")
    game = Game(
        id="current",
        number=1,
        assignments=assignments,
        actions=tuple(
            DraftAction(
                turn_index=i,
                team_id="A" if turns[i].position == "first" else "B",
                kind=turns[i].kind,
                character_id=character_ids[i],
            )
            for i in range(pick + 1)
        ),
    )
    with pytest.raises(ValueError, match=error):
        correct_action(
            settings,
            profile.catalog,
            game,
            pick if turn == 6 else turn,
            character_ids[0] if character == "known" else character,
        )
    # A recorded gap breaks "one Draft Action per turn" and cannot be corrected.
    gapped = game.model_copy(update={"actions": game.actions[:1] + game.actions[pick:]})
    with pytest.raises(ValueError, match="invalid_turn"):
        correct_action(settings, profile.catalog, gapped, pick, character_ids[-1])


@pytest.mark.parametrize("empty,earlier", [(False, False), (True, False), (True, True)])
def test_bs010_clear_rejects_earlier_turn_or_game_and_empty_current(
    profile,
    assignments,
    character_ids,
    empty,
    earlier,
):
    from nimbus.engine import clear_action

    # Parent BS-010: earlier turns/Games and an empty current Game cannot be cleared.
    game = Game(
        id="one",
        number=1,
        assignments=assignments,
        actions=(
            DraftAction(turn_index=0, team_id="A", kind="ban", character_id=character_ids[0]),
            DraftAction(turn_index=1, team_id="B", kind="ban", character_id=character_ids[1]),
        ),
    )
    current = Game(id="two", number=2, assignments=assignments) if empty else game
    with pytest.raises(ValueError, match="cannot_clear_action"):
        clear_action([game, current] if empty else [game], game if earlier else current, 0)


def test_bs010_changed_cause_reopens_and_reversal_restores_original_reason(
    profile,
    assignments,
    character_ids,
    first_pick_index,
):
    from nimbus.engine import acknowledge_violation, correct_action
    from nimbus.models import OverrideReason

    # Parent BS-010: adding another matching earlier cause reopens a still-broken
    # rule; restoring that cause restores its original acknowledgement.
    earlier = Game(
        id="one",
        number=1,
        assignments=assignments,
        actions=recorded_pick(profile, first_pick_index, character_ids[0]),
    )
    other = Game(
        id="two",
        number=2,
        assignments=assignments,
        actions=recorded_pick(profile, first_pick_index, character_ids[1]),
    )
    later = Game(id="three", number=3, assignments=assignments, actions=earlier.actions)
    reason = OverrideReason(category="earlier_entry_wrong", note="Verified original cause")
    later = acknowledge_violation(
        profile.snapshot(),
        profile.catalog,
        [earlier, other, later],
        later,
        first_pick_index,
        "fearless_lock",
        reason,
    )
    changed = correct_action(
        profile.snapshot(), profile.catalog, other, first_pick_index, character_ids[0]
    )
    reopened = derive_state(profile.snapshot(), profile.catalog, [earlier, changed, later], later)
    assert reopened.violations[0].status == "open"
    restored = correct_action(
        profile.snapshot(), profile.catalog, changed, first_pick_index, character_ids[1]
    )
    acknowledged = derive_state(
        profile.snapshot(), profile.catalog, [earlier, restored, later], later
    )
    assert (acknowledged.violations[0].status, acknowledged.violations[0].reason) == (
        "acknowledged",
        reason,
    )
    removed = correct_action(
        profile.snapshot(), profile.catalog, earlier, first_pick_index, character_ids[2]
    )
    assert (
        derive_state(
            profile.snapshot(), profile.catalog, [removed, restored, later], later
        ).violations
        == ()
    )


@pytest.mark.parametrize("turn_indices", [(0, 1, 6), (0, 6, 7), (6, 7, 8)])
@pytest.mark.parametrize("edited_occurrence", [0, 1, 2])
def test_bs010_correction_flags_every_duplicate_after_first_in_draft_order(
    profile, assignments, character_ids, turn_indices, edited_occurrence
):
    # Parent BS-010 confirmed extension: ban/ban/pick, ban/pick/pick and
    # pick/pick/pick occurrences obey Draft Order regardless of the edited action.
    from nimbus.engine import correct_action

    turns = profile.snapshot().draft_order.turns
    edited_turn = turn_indices[edited_occurrence]
    actions = tuple(
        DraftAction(
            turn_index=index,
            team_id=next(a.team_id for a in assignments if a.position == turns[index].position),
            kind=turns[index].kind,
            character_id=(
                character_ids[1]
                if index == edited_turn
                else character_ids[0]
                if index in turn_indices
                else character_ids[index + 3]
            ),
        )
        for index in range(max(turn_indices) + 1)
    )
    game = Game(id="current", number=1, assignments=assignments, actions=actions)
    corrected = correct_action(
        profile.snapshot(), profile.catalog, game, edited_turn, character_ids[0]
    )
    state = derive_state(profile.snapshot(), profile.catalog, [corrected], corrected)
    assert [(v.turn_index, v.rule, v.status) for v in state.violations] == [
        (turn_indices[1], "duplicate_character", "open"),
        (turn_indices[2], "duplicate_character", "open"),
    ]
    assert tuple(a for a in corrected.actions if a.turn_index != edited_turn) == tuple(
        a for a in actions if a.turn_index != edited_turn
    )


# Parent BS-010 / ADR-0008 (amended 2026-11-27): the current Game is the last
# Game, voided or not. Given Game 1 Drafted and Game 2 Voided, nothing can be
# cleared: Game 2 is voided and Game 1 is fixed only by replacement.
def test_bs010_current_game_is_last_game_even_when_voided(profile, assignments, opening_ban_teams):
    from nimbus.engine import clear_action, current_game

    def bans(count):
        return tuple(
            DraftAction(turn_index=i, team_id=opening_ban_teams[i], kind="ban", character_id=None)
            for i in range(count)
        )

    first = Game(id="one", number=1, assignments=assignments, actions=bans(2))
    voided = Game(id="two", number=2, assignments=assignments, voided=True, actions=bans(1))
    games = (first, voided)
    assert current_game(games) == voided
    assert current_game(()) is None
    for game in games:
        with pytest.raises(ValueError, match="cannot_clear_action"):
            clear_action(games, game, game.actions[-1].turn_index)
    live = voided.model_copy(update={"voided": False})
    assert clear_action((first, live), live, 0).actions == ()


# Parent ADR-0009: one Structural Invariant check serves live entry, correction
# and a copied Replay draft, so the three paths cannot drift apart.
@pytest.mark.parametrize(
    "character,error", [("missing-character", "unknown_character"), (None, "cannot_skip_pick")]
)
def test_structural_invariants_reject_entry_correction_and_copy_alike(
    profile, assignments, character_ids, first_pick_index, character, error
):
    from nimbus.engine import check_entry, correct_action, create_replay

    settings = profile.snapshot()
    turns = settings.draft_order.turns
    before = tuple(
        DraftAction(
            turn_index=i,
            team_id="A" if turns[i].position == "first" else "B",
            kind=turns[i].kind,
            character_id=None,
        )
        for i in range(first_pick_index)
    )
    team = "A" if turns[first_pick_index].position == "first" else "B"
    pick = DraftAction(
        turn_index=first_pick_index, team_id=team, kind="pick", character_id=character
    )
    game = Game(id="game", number=1, assignments=assignments, actions=before)
    assert check_entry(settings, profile.catalog, (game,), game, pick) == error
    recorded = game.model_copy(
        update={"actions": before + (pick.model_copy(update={"character_id": character_ids[0]}),)}
    )
    with pytest.raises(ValueError, match=error):
        correct_action(settings, profile.catalog, recorded, first_pick_index, character)
    source = game.model_copy(update={"voided": True, "actions": before + (pick,)})
    with pytest.raises(ValueError, match=error):
        create_replay(settings, profile.catalog, (source,), source, "copy", "copy_draft")


# Parent BS-015 / CONTEXT "Retired Character": past records still show it, but
# it is not offered for new entries. A Retired Character is in the Catalog, so it
# is structurally valid; only live entry refuses it. #11: a correction can
# deliberately choose it, and a copied Replay draft keeps the recorded fact.
def test_retired_character_is_refused_only_for_new_entries(profile, assignments, first_pick_index):
    from nimbus.engine import check_entry, correct_action, create_replay
    from nimbus.models import Character

    catalog = (*profile.catalog, Character(id="retired-x", name="Retired X", retired=True))
    settings = profile.snapshot()
    turns = settings.draft_order.turns
    ban = DraftAction(
        turn_index=0,
        team_id="A" if turns[0].position == "first" else "B",
        kind=turns[0].kind,
        character_id="retired-x",
    )
    empty = Game(id="game", number=1, assignments=assignments)
    assert check_entry(settings, catalog, (empty,), empty, ban) == "unknown_character"
    recorded = empty.model_copy(
        update={"actions": (ban.model_copy(update={"character_id": None}),)}
    )
    corrected = correct_action(settings, catalog, recorded, 0, "retired-x")
    assert corrected.actions[0].character_id == "retired-x"
    source = recorded.model_copy(update={"voided": True, "actions": (ban,)})
    replay = create_replay(settings, catalog, (source,), source, "copy", "copy_draft")
    assert replay.actions == (ban,)
