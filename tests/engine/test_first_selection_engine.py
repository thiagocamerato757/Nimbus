"""BS-012 at the agreed pure engine seam, shared by both Title profiles."""

from nimbus.engine import derive_state, record_entry
from nimbus.models import Assignment, DraftAction, Game


# Parent: BS-012 blue may pick second / result enough to draft.
# Given Team A on the first Side but second Draft Position, when an entry is
# recorded without First Selection metadata, Team B owns the opening turn.
def test_bs012_draft_positions_alone_choose_turn_owner(profile, character_ids):
    game = Game(
        id="first-selection",
        number=1,
        assignments=(
            Assignment(team_id="A", side=profile.sides[0], position="second"),
            Assignment(team_id="B", side=profile.sides[1], position="first"),
        ),
    )
    assert game.first_selection_holder is None and game.first_selection_choice is None
    settings = profile.snapshot()
    before = derive_state(settings, profile.catalog, (game,), game)
    assert before.next_turn.team_id == "B"
    recorded = record_entry(
        settings,
        profile.catalog,
        (game,),
        game,
        DraftAction(turn_index=0, team_id="B", kind="ban", character_id=character_ids[0]),
    )
    assert recorded.actions[0].team_id == "B"


# Parent BS-012 pending predecessor / profile default editable (ADR-0006).
# Given configured defaults and a preceding logical Game (with a voided source),
# prefill follows only that Game's nonvoid result; pending never guesses.
def test_bs012_prefill_uses_nonvoid_previous_logical_game(profile, assignments):
    from nimbus.engine import first_selection_prefill

    source = Game(id="void", number=1, assignments=assignments, voided=True, winner="A")
    previous = Game(
        id="replay",
        number=1,
        replay_of="void",
        assignments=assignments,
        winner="B",
        first_selection_holder="A",
    )
    for policy, expected in (("loser", "A"), ("winner", "B"), ("alternate", "B"), ("none", None)):
        settings = profile.snapshot().model_copy(update={"default_first_selection_holder": policy})
        assert first_selection_prefill(settings, (source, previous), 2) == expected
        assert first_selection_prefill(settings, (source,), 2) is None
        pending = previous.model_copy(update={"winner": None})
        assert first_selection_prefill(settings, (source, pending), 2) is None
        assert first_selection_prefill(settings, (source, previous), 1) is None
        assert first_selection_prefill(settings, (source, previous), 3) is None


# Parent BS-012 coupled profile respected (ADR-0007 / ADR-0016).
# Given an explicit first-pick Side, recording the opposite Draft Position
# rejects; the matching result still starts turns from Draft Position.
def test_bs012_coupled_side_uses_explicit_mapping(profile):
    import pytest

    from nimbus.engine import game_assignments

    settings = profile.snapshot().model_copy(
        update={
            "sides_coupled": True,
            "first_pick_side": profile.sides[1],
        }
    )
    with pytest.raises(ValueError, match="coupled_position"):
        game_assignments(settings, profile.sides[0], "A")
    assignments = game_assignments(settings, profile.sides[0], "B")
    assert assignments[0].side == profile.sides[0] and assignments[0].position == "second"
    game = Game(id="coupled", number=1, assignments=assignments)
    assert derive_state(settings, profile.catalog, (game,), game).next_turn.team_id == "B"
