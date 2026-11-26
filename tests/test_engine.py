from hypothesis import given
from hypothesis import strategies as st

from nimbus.engine import derive_state, validate_action
from nimbus.models import DraftAction, Game


def test_bs001_earlier_pick_locks_for_both_teams(profile, assignments, previous_pick):
    current = Game(id="current", number=2, assignments=assignments)
    state = derive_state(profile.snapshot(), profile.catalog, [previous_pick, current], current)
    assert state.locks == {"A": ("Orianna",), "B": ("Orianna",)}


def test_bs009_locked_pick_returns_fearless_lock(profile, assignments, previous_pick):
    current = Game(id="current", number=2, assignments=assignments)
    action = DraftAction(turn_index=6, team_id="A", kind="pick", character_id="Orianna")
    assert (
        validate_action(
            profile.snapshot(), profile.catalog, [previous_pick, current], current, action
        )
        == "fearless_lock"
    )


def test_turn_uses_draft_position_even_when_first_pick_team_is_red(profile, assignments):
    current = Game(id="current", number=1, assignments=assignments)
    state = derive_state(profile.snapshot(), profile.catalog, [current], current)
    assert state.next_turn.team_id == "A"
    assert state.next_turn.kind == "ban"


def test_locks_exclude_bans_and_current_game_picks(profile, assignments):
    earlier = Game(
        id="earlier",
        number=1,
        assignments=assignments,
        actions=(DraftAction(turn_index=0, team_id="A", kind="ban", character_id="Ahri"),),
    )
    current = Game(
        id="current",
        number=2,
        assignments=assignments,
        actions=(DraftAction(turn_index=6, team_id="A", kind="pick", character_id="Orianna"),),
    )
    state = derive_state(profile.snapshot(), profile.catalog, [earlier, current], current)
    assert state.locks == {"A": (), "B": ()}
    assert "Orianna" not in state.available["A"]
    assert "Ahri" in state.available["A"]


@given(
    st.lists(st.sampled_from(["Ahri", "Orianna", "Ashe"]), max_size=20),
    st.lists(st.sampled_from(["Ahri", "Orianna", "Ashe"]), max_size=20),
)
def test_deterministic_and_locked_characters_are_never_available(previous_ids, current_ids):
    # The public seam remains parameterizable through a Title profile; no engine globals.
    from nimbus.models import Assignment
    from nimbus.profiles import load_profiles

    for profile in load_profiles().values():
        assignments = (
            Assignment(team_id="A", side=profile.sides[1], position="first"),
            Assignment(team_id="B", side=profile.sides[0], position="second"),
        )

        def game(number, identifiers, profile=profile, assignments=assignments):
            actions = tuple(
                DraftAction(
                    turn_index=i,
                    team_id="A" if turn.position == "first" else "B",
                    kind=turn.kind,
                    character_id=character,
                )
                for i, (turn, character) in enumerate(
                    zip(profile.snapshot().draft_order.turns, identifiers)
                )
            )
            return Game(id=str(number), number=number, assignments=assignments, actions=actions)

        previous, current = game(1, previous_ids), game(2, current_ids)
        before = (previous.model_dump(), current.model_dump(), profile.model_dump())
        first = derive_state(profile.snapshot(), profile.catalog, [previous, current], current)
        second = derive_state(profile.snapshot(), profile.catalog, [previous, current], current)
        assert first == second
        assert before == (previous.model_dump(), current.model_dump(), profile.model_dump())
        for team in ["A", "B"]:
            assert not set(first.locks[team]).intersection(first.available[team])
