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


@given(data=st.data())
def test_deterministic_and_locked_characters_are_never_available(
    profile, assignments, character_ids, data
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
    first = derive_state(profile.snapshot(), profile.catalog, [previous, current], current)
    second = derive_state(profile.snapshot(), profile.catalog, [previous, current], current)
    assert first == second
    assert before == (previous.model_dump(), current.model_dump(), profile.model_dump())
    for team in ["A", "B"]:
        assert not set(first.locks[team]).intersection(first.available[team])
