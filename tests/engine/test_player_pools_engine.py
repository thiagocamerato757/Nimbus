"""US-012: Declared Pool availability through the pure engine seam."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from nimbus.engine import derive_player_pool, derive_state, validate_action
from nimbus.models import DraftAction, Fearless, Game


# Parent: BS-002; BS-005 repeats this state with the synthetic Title profile.
# Given a six-Character Declared Pool and an opponent's earlier pick under Hard Fearless,
# when the engine derives that Player's pool in Game 2, five Characters are Remaining.
def test_bs002_bs005_opponent_pick_leaves_five_remaining(
    profile, assignments, character_ids, first_pick_index
):
    pool = character_ids[:6]
    earlier = Game(
        id="earlier",
        number=1,
        assignments=assignments,
        actions=(
            DraftAction(
                turn_index=first_pick_index + 1, team_id="B", kind="pick", character_id=pool[0]
            ),
        ),
    )
    current = Game(id="current", number=2, assignments=assignments)
    state = derive_state(profile.snapshot(), profile.catalog, [earlier, current], current)
    result = derive_player_pool(state, "A", pool)
    assert result.remaining == tuple(sorted(pool[1:]))
    assert len(result.remaining) == 5


# Parent: BS-004; BS-005 repeats this state with the synthetic Title profile.
# Given four Remaining Characters, a current ban and a teammate's current pick,
# when the engine derives the pool, four remain and two are Available Now.
def test_bs004_bs005_current_ban_and_teammate_pick_leave_two_available(
    profile, assignments, character_ids, first_pick_index
):
    pool = character_ids[:4]
    current = Game(
        id="current",
        number=1,
        assignments=assignments,
        actions=(
            DraftAction(turn_index=0, team_id="B", kind="ban", character_id=pool[0]),
            DraftAction(
                turn_index=first_pick_index, team_id="A", kind="pick", character_id=pool[1]
            ),
        ),
    )
    state = derive_state(profile.snapshot(), profile.catalog, [current], current)
    result = derive_player_pool(state, "A", pool)
    assert result.remaining == tuple(sorted(pool))
    assert len(result.remaining) == 4
    assert result.available_now == tuple(sorted(pool[2:]))
    assert len(result.available_now) == 2


# Parent: #15 acceptance criterion extends #10's Locked-never-Available property
# to each Player, with both Title profiles and every defined Fearless Variant.
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
@pytest.mark.parametrize("same_character_twice", ["reject", "allow"])
@given(data=st.data())
def test_locked_character_is_never_available_now_for_any_player(
    profile, assignments, character_ids, reach, sources, same_character_twice, data
):
    settings = profile.snapshot().model_copy(
        update={
            "fearless": Fearless(lock_reach=reach, lock_sources=sources),
            "rule_settings": profile.rule_settings.model_copy(
                update={"same_character_twice": same_character_twice}
            ),
        }
    )
    games = []
    for number in (1, 2):
        selected = data.draw(
            st.lists(st.sampled_from(character_ids), max_size=len(settings.draft_order.turns)),
            label=f"Game {number} Characters",
        )
        actions = tuple(
            DraftAction(
                turn_index=index,
                team_id="A" if turn.position == "first" else "B",
                kind=turn.kind,
                character_id=character,
            )
            for index, (turn, character) in enumerate(zip(settings.draft_order.turns, selected))
        )
        games.append(Game(id=str(number), number=number, assignments=assignments, actions=actions))
    state = derive_state(settings, profile.catalog, games, games[-1])
    for team in ("A", "B"):
        for _ in range(profile.team_size):
            declared = data.draw(
                st.lists(st.sampled_from(character_ids), unique=True, max_size=12),
                label=f"Team {team} Player pool",
            )
            result = derive_player_pool(state, team, declared)
            assert set(state.locks[team]).isdisjoint(result.available_now)


# Parent: #15 domain decision (2026-11-28): allowing the same Character twice
# permits opposing Teams to mirror; the picking Team loses it Available Now.
@pytest.mark.parametrize("picking_team,opponent", [("A", "B"), ("B", "A")])
def test_mirroring_pick_is_available_only_to_opponent(
    profile, assignments, character_ids, first_pick_index, picking_team, opponent
):
    settings = profile.snapshot().model_copy(
        update={
            "rule_settings": profile.rule_settings.model_copy(
                update={"same_character_twice": "allow"}
            )
        }
    )
    character = character_ids[0]
    current = Game(
        id="current",
        number=1,
        assignments=assignments,
        actions=(
            DraftAction(
                turn_index=first_pick_index,
                team_id=picking_team,
                kind="pick",
                character_id=character,
            ),
        ),
    )
    state = derive_state(settings, profile.catalog, [current], current)
    picking_pool = derive_player_pool(state, picking_team, [character])
    opposing_pool = derive_player_pool(state, opponent, [character])
    assert picking_pool.remaining == opposing_pool.remaining == (character,)
    assert picking_pool.available_now == ()
    assert opposing_pool.available_now == (character,)
    assert character not in state.available[picking_team]
    assert character in state.available[opponent]
    mirror = DraftAction(
        turn_index=first_pick_index + 1, team_id=opponent, kind="pick", character_id=character
    )
    assert validate_action(settings, profile.catalog, [current], current, mirror) is None


# Parent: #15 domain decision: a Team cannot pick a Character twice;
# allowing same-Team duplicates would require a different future setting.
@pytest.mark.parametrize("team", ["A", "B"])
def test_mirroring_rejects_a_second_pick_for_the_same_team(
    profile, assignments, character_ids, first_pick_index, team
):
    settings = profile.snapshot().model_copy(
        update={
            "rule_settings": profile.rule_settings.model_copy(
                update={"same_character_twice": "allow"}
            )
        }
    )
    character = character_ids[0]
    current = Game(
        id="current",
        number=1,
        assignments=assignments,
        actions=(
            DraftAction(
                turn_index=first_pick_index, team_id=team, kind="pick", character_id=character
            ),
        ),
    )
    repeat = DraftAction(
        turn_index=first_pick_index + 2, team_id=team, kind="pick", character_id=character
    )
    assert (
        validate_action(settings, profile.catalog, [current], current, repeat)
        == "duplicate_character"
    )


# Parent: #15 domain decision: bans remove Available Now for both Teams even
# with mirroring enabled, and a banned Character cannot be picked normally.
@pytest.mark.parametrize("banning_team", ["A", "B"])
def test_mirroring_ban_removes_character_for_both_teams(
    profile, assignments, character_ids, first_pick_index, banning_team
):
    settings = profile.snapshot().model_copy(
        update={
            "rule_settings": profile.rule_settings.model_copy(
                update={"same_character_twice": "allow"}
            )
        }
    )
    character = character_ids[0]
    current = Game(
        id="current",
        number=1,
        assignments=assignments,
        actions=(
            DraftAction(turn_index=0, team_id=banning_team, kind="ban", character_id=character),
        ),
    )
    state = derive_state(settings, profile.catalog, [current], current)
    for team in ("A", "B"):
        result = derive_player_pool(state, team, [character])
        assert result.remaining == (character,)
        assert result.available_now == ()
        pick = DraftAction(
            turn_index=first_pick_index, team_id=team, kind="pick", character_id=character
        )
        assert (
            validate_action(settings, profile.catalog, [current], current, pick)
            == "duplicate_character"
        )


# Parents: BS-002 / BS-005 and #15's mirroring decision: mirrored picks are
# ordinary earlier picks, so Hard Fearless still locks them for both Teams.
def test_mirrored_earlier_picks_are_locked_for_both_teams_next_game(
    profile, assignments, character_ids, first_pick_index
):
    settings = profile.snapshot().model_copy(
        update={
            "rule_settings": profile.rule_settings.model_copy(
                update={"same_character_twice": "allow"}
            )
        }
    )
    character = character_ids[0]
    earlier = Game(
        id="earlier",
        number=1,
        assignments=assignments,
        actions=(
            DraftAction(
                turn_index=first_pick_index, team_id="A", kind="pick", character_id=character
            ),
            DraftAction(
                turn_index=first_pick_index + 1, team_id="B", kind="pick", character_id=character
            ),
        ),
    )
    current = Game(id="current", number=2, assignments=assignments)
    state = derive_state(settings, profile.catalog, [earlier, current], current)
    for team in ("A", "B"):
        assert state.locks[team] == (character,)
        result = derive_player_pool(state, team, [character])
        assert result.remaining == result.available_now == ()
        pick = DraftAction(
            turn_index=first_pick_index, team_id=team, kind="pick", character_id=character
        )
        assert (
            validate_action(settings, profile.catalog, [earlier, current], current, pick)
            == "fearless_lock"
        )
