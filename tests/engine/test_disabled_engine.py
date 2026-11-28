"""BS-015 at the agreed pure engine seam, on both Title profiles."""

import pytest

from nimbus.engine import derive_player_pool, derive_state, record_entry
from nimbus.models import DraftAction, Game, OverrideReason


# Parent: BS-015 (Disabled Character is not Remaining).
# Given a two-Character Declared Pool including a Disabled Character,
# when the engine derives its pools, only the other Character is Remaining/Available Now.
def test_bs015_disabled_character_is_neither_remaining_nor_available(
    profile, assignments, character_ids
):
    pool = character_ids[:2]
    settings = profile.snapshot().model_copy(update={"disabled_characters": (pool[0],)})
    game = Game(id="current", number=1, assignments=assignments)
    state = derive_state(settings, profile.catalog, [game], game)
    result = derive_player_pool(state, "A", pool)
    assert result.remaining == (pool[1],)
    assert result.available_now == (pool[1],)


# Parent: BS-015 (entering a Disabled Character needs an Override).
# Given a Disabled Character, recording its ban or pick rejects a Game Rule break;
# supplying an Override records the same action as an Acknowledged Violation.
@pytest.mark.parametrize("kind", ["pick", "ban"])
def test_bs015_disabled_entry_needs_override(profile, assignments, character_ids, kind):
    settings = profile.snapshot().model_copy(update={"disabled_characters": (character_ids[0],)})
    turn_index = next(i for i, t in enumerate(settings.draft_order.turns) if t.kind == kind)
    prior = tuple(
        DraftAction(turn_index=i, team_id="A" if turn.position == "first" else "B",
                    kind=turn.kind, character_id=None)
        for i, turn in enumerate(settings.draft_order.turns[:turn_index])
    )
    game = Game(id="current", number=1, assignments=assignments, actions=prior)
    turn = settings.draft_order.turns[turn_index]
    action = DraftAction(turn_index=turn_index,
                         team_id="A" if turn.position == "first" else "B",
                         kind=kind, character_id=character_ids[0])
    with pytest.raises(ValueError, match="disabled_character"):
        record_entry(settings, profile.catalog, [game], game, action)
    recorded = record_entry(settings, profile.catalog, [game], game, action,
                            OverrideReason(category="official_ruling"))
    state = derive_state(settings, profile.catalog, [recorded], recorded)
    assert [(v.rule, v.status) for v in state.violations] == [
        ("disabled_character", "acknowledged")
    ]
