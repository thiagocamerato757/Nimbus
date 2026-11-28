"""BS-011 confirmed extension at the shared pure-engine seam, both profiles."""

from nimbus.engine import derive_state
from nimbus.models import DraftAction, Game


# Parent: BS-011 replay copy. Given the latest Voided attempt, creating its copy
# returns a new linked same-number Game, editable prefill, without winner/Players.
def test_bs011_copy_replay_preserves_attempt_and_clears_result(profile, assignments, character_ids):
    from nimbus.engine import create_replay

    turn = profile.snapshot().draft_order.turns[0]
    source = Game(
        id="void",
        number=3,
        assignments=assignments,
        voided=True,
        winner="A",
        patch="26.1",
        lineups={"A": ("player",), "B": ()},
        actions=(
            DraftAction(turn_index=0, team_id="A", kind=turn.kind, character_id=character_ids[0]),
        ),
    )
    settings = profile.snapshot()
    replay = create_replay(settings, profile.catalog, (source,), source, "new", "copy_draft")
    assert replay.id == "new" and replay.number == 3
    assert replay.replay_of == source.id
    assert replay.actions == source.actions
    assert replay.assignments == assignments and replay.lineups == source.lineups
    assert replay.patch == "26.1"
    assert replay.winner is None and replay.player_assignments == () and not replay.voided
    assert source.voided and source.winner == "A"
    assert derive_state(settings, profile.catalog, (source, replay), replay).status == "Drafting"


# Parent: BS-011 copied Violations. Matching rule/action/cause carries its
# original reason and provenance; Open/new breaches stay Open; reversal restores.
def test_bs011_copied_violations_keep_scope_provenance_and_maximum_reason(
    profile, assignments, character_ids
):
    from nimbus.engine import acknowledge_violation, correct_action, create_replay
    from nimbus.models import OverrideReason

    settings = profile.snapshot()
    actions = tuple(
        DraftAction(
            turn_index=i,
            team_id="A" if t.position == "first" else "B",
            kind=t.kind,
            character_id=character_ids[0],
        )
        for i, t in enumerate(settings.draft_order.turns[:3])
    )
    source = Game(id="source", number=3, assignments=assignments, actions=actions, voided=True)
    reason = OverrideReason(category="official_ruling", note="R" * 2000)
    source = acknowledge_violation(
        settings, profile.catalog, (source,), source, 1, "duplicate_character", reason
    )
    replay = create_replay(settings, profile.catalog, (source,), source, "replay", "copy_draft")
    state = derive_state(settings, profile.catalog, (source, replay), replay)
    assert [(v.turn_index, v.status) for v in state.violations] == [
        (1, "acknowledged"),
        (2, "open"),
    ]
    assert state.violations[0].reason == reason
    assert state.violations[0].carried_from[0].game_id == "source"
    assert state.violations[0].carried_from[0].game_number == 3
    changed = correct_action(settings, profile.catalog, replay, 0, character_ids[1])
    assert [
        v.status
        for v in derive_state(settings, profile.catalog, (source, changed), changed).violations
    ] == ["open"]
    restored = correct_action(settings, profile.catalog, changed, 0, character_ids[0])
    assert derive_state(settings, profile.catalog, (source, restored), restored) == state
    replay = replay.model_copy(update={"voided": True})
    chain = create_replay(
        settings, profile.catalog, (source, replay), replay, "chain", "copy_draft"
    )
    v = derive_state(settings, profile.catalog, (source, replay, chain), chain).violations[0]
    assert v.reason.note == "R" * 2000
    assert [c.game_id for c in v.carried_from] == ["source", "replay"]


# Parent: BS-011 counted Voided attempt locks only higher numbers, never Replay.
def test_bs011_counted_voided_attempt_never_locks_same_number(
    profile, assignments, character_ids, first_pick_index
):
    from nimbus.models import Fearless

    settings = profile.snapshot()
    settings = settings.model_copy(
        update={
            "fearless": Fearless(lock_reach="both_teams", lock_sources="picks"),
            "rule_settings": settings.rule_settings.model_copy(update={"voided_games_count": True}),
        }
    )
    picked = "Azir" if profile.id == "league-of-legends" else character_ids[0]
    source = Game(
        id="void",
        number=3,
        assignments=assignments,
        voided=True,
        actions=(
            DraftAction(turn_index=first_pick_index, team_id="A", kind="pick", character_id=picked),
        ),
    )
    replay = Game(
        id="replay", replay_of="void", number=3, assignments=assignments, actions=source.actions
    )
    later = Game(id="four", number=4, assignments=assignments)
    state = derive_state(settings, profile.catalog, (source, replay, later), replay)
    assert state.locks == {"A": (), "B": ()} and state.violations == ()
    assert derive_state(settings, profile.catalog, (source, replay, later), later).locks == {
        "A": (picked,),
        "B": (picked,),
    }


# Parent: BS-011 replay eligibility and Structural Invariants reject atomically.
def test_bs011_only_latest_voided_attempt_replays_with_structural_actions(
    profile, assignments, character_ids
):
    import pytest

    from nimbus.engine import create_replay

    source = Game(
        id="void",
        number=1,
        voided=True,
        assignments=assignments,
        actions=(
            DraftAction(turn_index=0, team_id="A", kind="ban", character_id=character_ids[0]),
        ),
    )
    settings = profile.snapshot()
    replay = create_replay(settings, profile.catalog, (source,), source, "new", "new_draft")
    assert replay.actions == ()
    with pytest.raises(ValueError, match="replay_unavailable"):
        create_replay(settings, profile.catalog, (source, replay), source, "bad", "copy_draft")
    with pytest.raises(ValueError, match="replay_choice_required"):
        create_replay(settings, profile.catalog, (source,), source, "bad", "")
    swapped = source.model_copy(
        update={
            "assignments": tuple(
                a.model_copy(update={"position": "second" if a.position == "first" else "first"})
                for a in assignments
            )
        }
    )
    # ADR-0034 (amended 2026-11-27): a copied draft keeps the source Draft Positions.
    with pytest.raises(ValueError, match="copy_requires_same_draft_positions"):
        create_replay(settings, profile.catalog, (source,), source, "bad", "copy_draft", swapped)


# Parent ADR-0034 (amended 2026-11-27): Draft Positions are editable, but not
# together with a copied draft; Sides may still change, and new draft is free.
def test_copied_draft_requires_same_draft_positions(profile, assignments, character_ids):
    import pytest

    from nimbus.engine import create_replay

    turn = profile.snapshot().draft_order.turns[0]
    team = "A" if turn.position == "first" else "B"
    source = Game(
        id="void",
        number=2,
        voided=True,
        assignments=assignments,
        actions=(
            DraftAction(turn_index=0, team_id=team, kind=turn.kind, character_id=character_ids[0]),
        ),
    )
    settings = profile.snapshot()
    swapped = source.model_copy(
        update={
            "assignments": tuple(
                a.model_copy(update={"position": "second" if a.position == "first" else "first"})
                for a in assignments
            )
        }
    )
    new = create_replay(settings, profile.catalog, (source,), source, "new", "new_draft", swapped)
    assert new.assignments == swapped.assignments and new.actions == ()
    with pytest.raises(ValueError, match="copy_requires_same_draft_positions"):
        create_replay(settings, profile.catalog, (source,), source, "copy", "copy_draft", swapped)
    sides = source.model_copy(
        update={
            "assignments": tuple(
                a.model_copy(update={"side": b.side})
                for a, b in zip(assignments, reversed(assignments), strict=True)
            )
        }
    )
    copied = create_replay(
        settings, profile.catalog, (source,), source, "copy", "copy_draft", sides
    )
    assert copied.actions == source.actions and copied.assignments == sides.assignments


# Parent BS-012 / #14 (amended 2026-11-27): the engine never applies a pre-fill
# to a Replay; the holder is whatever the analyst's request carries.
def test_replay_never_applies_first_selection_prefill(profile, assignments, character_ids):
    from nimbus.engine import create_replay, first_selection_prefill

    settings = profile.snapshot().model_copy(update={"default_first_selection_holder": "loser"})
    previous = Game(id="one", number=1, assignments=assignments, winner="A")
    source = Game(id="void", number=2, voided=True, assignments=assignments)
    games = (previous, source)
    assert first_selection_prefill(settings, games, 2) == "B"
    replay = create_replay(settings, profile.catalog, games, source, "new", "new_draft")
    assert replay.first_selection_holder is None
