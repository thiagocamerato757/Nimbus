import pytest
from hypothesis import given
from hypothesis import strategies as st

from nimbus.engine import derive_state, validate_action
from nimbus.models import DraftAction, Game


def test_bs005_deriving_opening_bans_preserves_draft_position_turns(
    profile, assignments, character_ids, opening_ban_teams
):
    # BS-005: A, BB, AA, B are six sequential bans, including both B turns after A.
    current = Game(id="current", number=1, assignments=assignments)
    for index, team in enumerate(opening_ban_teams):
        state = derive_state(profile.snapshot(), profile.catalog, [current], current)
        assert state.next_turn.model_dump() == {"index": index, "team_id": team, "kind": "ban"}
        current = current.model_copy(
            update={
                "actions": current.actions
                + (
                    DraftAction(
                        turn_index=index,
                        team_id=team,
                        kind="ban",
                        character_id=character_ids[index],
                    ),
                )
            }
        )


def test_bs001_earlier_pick_locks_for_both_teams(
    profile, assignments, previous_pick, character_ids
):
    current = Game(id="current", number=2, assignments=assignments)
    state = derive_state(profile.snapshot(), profile.catalog, [previous_pick, current], current)
    assert state.locks == {"A": (character_ids[0],), "B": (character_ids[0],)}


def test_bs009_locked_pick_returns_fearless_lock(
    profile, assignments, previous_pick, character_ids, first_pick_index
):
    current = Game(id="current", number=2, assignments=assignments)
    action = DraftAction(
        turn_index=first_pick_index, team_id="A", kind="pick", character_id=character_ids[0]
    )
    assert (
        validate_action(
            profile.snapshot(), profile.catalog, [previous_pick, current], current, action
        )
        == "fearless_lock"
    )


def test_turn_uses_draft_position_even_when_first_pick_team_has_second_side(profile, assignments):
    current = Game(id="current", number=1, assignments=assignments)
    state = derive_state(profile.snapshot(), profile.catalog, [current], current)
    assert state.next_turn.team_id == "A"
    assert state.next_turn.kind == "ban"


def test_locks_exclude_bans_and_current_game_picks(
    profile, assignments, character_ids, first_pick_index
):
    earlier = Game(
        id="earlier",
        number=1,
        assignments=assignments,
        actions=(
            DraftAction(turn_index=0, team_id="A", kind="ban", character_id=character_ids[1]),
        ),
    )
    current = Game(
        id="current",
        number=2,
        assignments=assignments,
        actions=(
            DraftAction(
                turn_index=first_pick_index,
                team_id="A",
                kind="pick",
                character_id=character_ids[0],
            ),
        ),
    )
    state = derive_state(profile.snapshot(), profile.catalog, [earlier, current], current)
    assert state.locks == {"A": (), "B": ()}
    assert character_ids[0] not in state.available["A"]
    assert character_ids[1] in state.available["A"]


@pytest.mark.parametrize(
    "reach, sources",
    [
        ("none", "picks"),
        ("none", "picks_and_bans"),
        ("picking_team", "picks"),
        ("both_teams", "picks"),
        ("both_teams", "picks_and_bans"),
    ],
)
@given(data=st.data())
def test_deterministic_and_locked_characters_are_never_available(
    profile, assignments, character_ids, data, reach, sources
):
    # Both profiles use the same strategy, each drawing only from its own Catalog.
    identifiers = st.lists(
        st.sampled_from(character_ids), max_size=len(profile.snapshot().draft_order.turns)
    )

    def game(number, selected_ids):
        actions = tuple(
            DraftAction(
                turn_index=i,
                team_id="A" if turn.position == "first" else "B",
                kind=turn.kind,
                character_id=character,
            )
            for i, (turn, character) in enumerate(
                zip(profile.snapshot().draft_order.turns, selected_ids)
            )
        )
        return Game(id=str(number), number=number, assignments=assignments, actions=actions)

    previous = game(1, data.draw(identifiers, label="earlier Game Characters"))
    current = game(2, data.draw(identifiers, label="current Game Characters"))
    before = (previous.model_dump(), current.model_dump(), profile.model_dump())
    from nimbus.models import Fearless

    settings = profile.snapshot().model_copy(
        update={"fearless": Fearless(lock_reach=reach, lock_sources=sources)}
    )
    first = derive_state(settings, profile.catalog, [previous, current], current)
    second = derive_state(settings, profile.catalog, [previous, current], current)
    assert first == second
    assert before == (previous.model_dump(), current.model_dump(), profile.model_dump())
    for team in ["A", "B"]:
        assert not set(first.locks[team]).intersection(first.available[team])


def test_bs003_bs005_soft_fearless_ban_only_rejects_when_opponent_is_locked(
    profile, assignments, previous_pick, character_ids
):
    # Parent BS-003 / scoped BS-005: A picked earlier; only B's ban is wasted.
    from nimbus.models import Fearless

    settings = profile.snapshot().model_copy(
        update={"fearless": Fearless(id="soft", lock_reach="picking_team")}
    )
    current = Game(id="current", number=2, assignments=assignments)
    state = derive_state(settings, profile.catalog, [previous_pick, current], current)
    assert state.locks == {"A": (character_ids[0],), "B": ()}
    for team, expected in (("A", None), ("B", "wasted_ban")):
        ban = DraftAction(turn_index=0, team_id=team, kind="ban", character_id=character_ids[0])
        assert (
            validate_action(settings, profile.catalog, [previous_pick, current], current, ban)
            == expected
        )


def test_bs028_picking_team_with_bans_is_rejected(profile):
    # Parent BS-028: validation names the undefined combination.
    import pytest

    from nimbus.models import Fearless

    with pytest.raises(ValueError, match="picking_team.*picks_and_bans"):
        Fearless(id="custom", lock_reach="picking_team", lock_sources="picks_and_bans")


def test_bs028_bans_lock_both_teams_in_next_game(profile, assignments, character_ids):
    # Parent BS-028: picks and bans under both-Teams reach lock either Team.
    from nimbus.models import Fearless

    earlier = Game(
        id="earlier",
        number=1,
        assignments=assignments,
        actions=(
            DraftAction(turn_index=0, team_id="A", kind="ban", character_id=character_ids[0]),
        ),
    )
    current = Game(id="current", number=2, assignments=assignments)
    settings = profile.snapshot().model_copy(
        update={"fearless": Fearless(lock_sources="picks_and_bans")}
    )
    state = derive_state(settings, profile.catalog, [earlier, current], current)
    assert state.locks == {"A": (character_ids[0],), "B": (character_ids[0],)}


def test_bs009_skipped_ban_advances_but_pick_cannot_be_skipped(profile, assignments):
    # Parent BS-009 / US-003: a Skipped Ban fills only a ban turn.
    from nimbus.engine import check_entry

    current = Game(id="current", number=1, assignments=assignments)
    skipped = DraftAction(turn_index=0, team_id="A", kind="ban", character_id=None)
    assert check_entry(profile.snapshot(), profile.catalog, [current], current, skipped) is None
    current = current.model_copy(update={"actions": (skipped,)})
    assert (
        derive_state(profile.snapshot(), profile.catalog, [current], current).next_turn.index == 1
    )


def test_bs009_duplicate_reject_override_is_acknowledged(profile, assignments, character_ids):
    # Parent BS-009: a reason acknowledges the rule/action/cause, never structural errors.
    from nimbus.engine import record_entry
    from nimbus.models import OverrideReason

    current = Game(
        id="current",
        number=1,
        assignments=assignments,
        actions=(
            DraftAction(turn_index=0, team_id="A", kind="ban", character_id=character_ids[0]),
        ),
    )
    state = derive_state(profile.snapshot(), profile.catalog, [current], current)
    turn = state.next_turn
    action = DraftAction(
        turn_index=turn.index, team_id=turn.team_id, kind=turn.kind, character_id=character_ids[0]
    )
    assert (
        validate_action(profile.snapshot(), profile.catalog, [current], current, action)
        == "duplicate_character"
    )
    recorded = record_entry(
        profile.snapshot(),
        profile.catalog,
        [current],
        current,
        action,
        OverrideReason(category="official_ruling", note="Referee decision"),
    )
    violation = derive_state(profile.snapshot(), profile.catalog, [recorded], recorded).violations[
        0
    ]
    assert violation.rule == "duplicate_character"
    assert violation.status == "acknowledged"
    assert violation.reason.category == "official_ruling"
    assert violation.reason.note == "Referee decision"


@pytest.mark.parametrize("mode", ["allow", "warn", "reject"])
def test_bs009_locked_ban_settings_notice_or_violation(
    profile, assignments, previous_pick, character_ids, mode
):
    from nimbus.engine import record_entry
    from nimbus.models import OverrideReason

    settings = profile.snapshot().model_copy(
        update={"rule_settings": profile.rule_settings.model_copy(update={"banning_locked": mode})}
    )
    current = Game(id="current", number=2, assignments=assignments)
    action = DraftAction(turn_index=0, team_id="A", kind="ban", character_id=character_ids[0])
    if mode == "reject":
        with pytest.raises(ValueError, match="wasted_ban"):
            record_entry(settings, profile.catalog, [previous_pick, current], current, action)
    result = record_entry(
        settings,
        profile.catalog,
        [previous_pick, current],
        current,
        action,
        OverrideReason(category="official_ruling") if mode == "reject" else None,
    )
    state = derive_state(settings, profile.catalog, [previous_pick, result], result)
    assert [n.rule for n in state.notices] == (["wasted_ban"] if mode == "warn" else [])
    assert [v.status for v in state.violations] == (["acknowledged"] if mode == "reject" else [])


@pytest.mark.parametrize(
    "invalid", ["unknown", "retired", "turn", "team", "kind", "skip_pick", "complete"]
)
def test_bs009_structural_errors_cannot_be_overridden(profile, assignments, character_ids, invalid):
    from nimbus.engine import record_entry
    from nimbus.models import Character, OverrideReason

    settings = profile.snapshot()
    catalog = list(profile.catalog) + [Character(id="retired", name="Retired", retired=True)]
    current = Game(id="current", number=1, assignments=assignments)
    action = DraftAction(turn_index=0, team_id="A", kind="ban", character_id=character_ids[0])
    if invalid in ("unknown", "retired"):
        action = action.model_copy(update={"character_id": invalid})
    elif invalid in ("turn", "team", "kind"):
        action = action.model_copy(
            update={"turn_index": 99}
            if invalid == "turn"
            else {"team_id": "B"}
            if invalid == "team"
            else {"kind": "pick"}
        )
    else:
        count = (
            len(settings.draft_order.turns)
            if invalid == "complete"
            else next(i for i, t in enumerate(settings.draft_order.turns) if t.kind == "pick")
        )
        for i in range(count):
            turn = derive_state(settings, catalog, [current], current).next_turn
            entry = DraftAction(
                turn_index=i,
                team_id=turn.team_id,
                kind=turn.kind,
                character_id=None if turn.kind == "ban" else character_ids[i],
            )
            current = record_entry(settings, catalog, [current], current, entry)
        if invalid == "skip_pick":
            turn = derive_state(settings, catalog, [current], current).next_turn
            action = DraftAction(
                turn_index=turn.index, team_id=turn.team_id, kind="pick", character_id=None
            )
    with pytest.raises(ValueError):
        record_entry(
            settings,
            catalog,
            [current],
            current,
            action,
            OverrideReason(category="official_ruling"),
        )


def test_bs009_duplicate_allow_creates_no_violation(profile, assignments, character_ids):
    from nimbus.engine import record_entry

    settings = profile.snapshot().model_copy(
        update={
            "rule_settings": profile.rule_settings.model_copy(
                update={"same_character_twice": "allow"}
            )
        }
    )
    current = Game(id="current", number=1, assignments=assignments)
    for _ in range(2):
        turn = derive_state(settings, profile.catalog, [current], current).next_turn
        current = record_entry(
            settings,
            profile.catalog,
            [current],
            current,
            DraftAction(
                turn_index=turn.index,
                team_id=turn.team_id,
                kind=turn.kind,
                character_id=character_ids[0],
            ),
        )
    assert derive_state(settings, profile.catalog, [current], current).violations == ()


@given(data=st.data())
def test_bs009_skipped_and_overridden_actions_recompute_identically(
    profile, assignments, character_ids, data
):
    from nimbus.engine import record_entry
    from nimbus.models import OverrideReason

    settings = profile.snapshot()
    current = Game(id="current", number=1, assignments=assignments)
    choices = data.draw(
        st.lists(
            st.sampled_from(character_ids[:3]), min_size=1, max_size=len(settings.draft_order.turns)
        )
    )
    for character in choices:
        turn = derive_state(settings, profile.catalog, [current], current).next_turn
        skip = turn.kind == "ban" and data.draw(st.booleans())
        action = DraftAction(
            turn_index=turn.index,
            team_id=turn.team_id,
            kind=turn.kind,
            character_id=None if skip else character,
        )
        current = record_entry(
            settings,
            profile.catalog,
            [current],
            current,
            action,
            OverrideReason(category="official_ruling"),
        )
    restored = Game.model_validate_json(current.model_dump_json())
    state = derive_state(settings, profile.catalog, [current], current)
    assert state == derive_state(settings, profile.catalog, [restored], restored)
    assert all(v.status == "acknowledged" for v in state.violations)
    assert all(a.character_id is not None or a.kind == "ban" for a in current.actions)


def test_bs009_acknowledgement_matches_rule_action_and_cause(
    profile, assignments, previous_pick, character_ids, first_pick_index
):
    from nimbus.engine import record_entry
    from nimbus.models import OverrideReason

    current = Game(id="current", number=2, assignments=assignments)
    for _ in range(first_pick_index):
        turn = derive_state(
            profile.snapshot(), profile.catalog, [previous_pick, current], current
        ).next_turn
        current = record_entry(
            profile.snapshot(),
            profile.catalog,
            [previous_pick, current],
            current,
            DraftAction(turn_index=turn.index, team_id=turn.team_id, kind="ban", character_id=None),
        )
    turn = derive_state(
        profile.snapshot(), profile.catalog, [previous_pick, current], current
    ).next_turn
    current = record_entry(
        profile.snapshot(),
        profile.catalog,
        [previous_pick, current],
        current,
        DraftAction(
            turn_index=turn.index, team_id=turn.team_id, kind="pick", character_id=character_ids[0]
        ),
        OverrideReason(category="official_ruling"),
    )
    original = derive_state(profile.snapshot(), profile.catalog, [previous_pick, current], current)
    assert original.violations[0].status == "acknowledged"
    other_cause = previous_pick.model_copy(update={"id": "different-cause"})
    assert (
        derive_state(profile.snapshot(), profile.catalog, [other_cause, current], current)
        .violations[0]
        .status
        == "open"
    )
    assert (
        derive_state(profile.snapshot(), profile.catalog, [previous_pick, current], current)
        == original
    )
