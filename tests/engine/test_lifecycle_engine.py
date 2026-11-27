"""BS-011 and #13 lifecycle outcomes at the shared engine seam."""

from nimbus.engine import derive_state
from nimbus.models import DraftAction, Game, PlayerAssignment


def drafted(profile, assignments, character_ids, **extra):
    actions = tuple(
        DraftAction(
            turn_index=i,
            team_id="A" if t.position == "first" else "B",
            kind=t.kind,
            character_id=character_ids[i] if t.kind == "pick" else None,
        )
        for i, t in enumerate(profile.snapshot().draft_order.turns)
    )
    return Game(id="one", number=1, assignments=assignments, actions=actions, **extra)


# Parent: BS-011: Given complete draft without assignments/winner, deriving status
# yields Drafted and Result Pending; only a fully recorded Game is Closed.
def test_bs011_derived_status_requires_draft_assignments_and_winner(
    profile, assignments, character_ids
):
    settings = profile.snapshot()
    game = drafted(profile, assignments, character_ids)
    state = derive_state(settings, profile.catalog, (game,), game)
    assert state.status == "Drafted"
    assert state.result_pending is True
    assigned = tuple(
        PlayerAssignment(turn_index=a.turn_index, player_id=f"player-{a.turn_index}")
        for a in game.actions
        if a.kind == "pick"
    )
    for players, winner, expected in [
        (assigned, None, "Drafted"),
        ((), "A", "Drafted"),
        (assigned, "A", "Closed"),
    ]:
        recorded = game.model_copy(update={"player_assignments": players, "winner": winner})
        assert derive_state(settings, profile.catalog, (recorded,), recorded).status == expected
    incomplete = game.model_copy(update={"actions": game.actions[:-1]})
    assert derive_state(settings, profile.catalog, (incomplete,), incomplete).status == "Drafting"


# Parent: BS-011: Given recorded picks, voiding makes no later Locks by default;
# ADR-0013 preserves the Series snapshot's voided_games_count exception.
def test_bs011_void_excludes_locks_unless_snapshot_counts_voided_games(
    profile, assignments, character_ids
):
    game = drafted(profile, assignments, character_ids, voided=True)
    later = Game(id="later", number=2, assignments=assignments)
    settings = profile.snapshot()
    state = derive_state(settings, profile.catalog, (game, later), later)
    assert state.locks == {"A": (), "B": ()}
    assert derive_state(settings, profile.catalog, (game,), game).status == "Voided"
    counting = settings.model_copy(
        update={
            "rule_settings": settings.rule_settings.model_copy(update={"voided_games_count": True})
        }
    )
    picks = tuple(sorted(a.character_id for a in game.actions if a.kind == "pick"))
    assert derive_state(counting, profile.catalog, (game, later), later).locks == {
        "A": picks,
        "B": picks,
    }


# Parent: #13 acceptance / US-009: Best-of ends at majority only without
# pending results; corrections retain later Games and expose their warning.
def test_best_of_majority_pending_and_corrected_decision(profile, assignments, character_ids):
    from nimbus.engine import derive_progress
    from nimbus.models import SeriesFormat

    settings = profile.snapshot().model_copy(
        update={"series_format": SeriesFormat(kind="best_of", games=5)}
    )
    base = drafted(profile, assignments, character_ids)
    games = tuple(
        base.model_copy(update={"id": str(i), "number": i, "winner": winner})
        for i, winner in enumerate(("A", "A", "B", "A"), 1)
    )
    progress = derive_progress(settings, games)
    assert progress.score == {"A": 3, "B": 1}
    assert progress.ended is True
    assert progress.deciding_game == 4
    corrected = games[:2] + (games[2].model_copy(update={"winner": "A"}), games[3])
    progress = derive_progress(settings, corrected)
    assert progress.deciding_game == 3
    assert progress.games_past_decision == (4,)
    assert len(corrected) == 4
    pending = games[:2] + (games[2].model_copy(update={"winner": None}), games[3])
    progress = derive_progress(settings, pending)
    assert progress.ended is False
    assert progress.pending_results == (3,)
    assert progress.can_start_next is True
    voided = games[:2] + (games[2], games[3].model_copy(update={"voided": True}))
    assert derive_progress(settings, voided).score == {"A": 2, "B": 1}


# Parent: #13 acceptance: Fixed-length counts non-voided Games regardless of score.
def test_fixed_length_excludes_voided_games(profile, assignments, character_ids):
    from nimbus.engine import derive_progress
    from nimbus.models import SeriesFormat

    settings = profile.snapshot().model_copy(
        update={"series_format": SeriesFormat(kind="fixed_length", games=2)}
    )
    base = drafted(profile, assignments, character_ids, winner="A")
    games = (
        base.model_copy(update={"voided": True}),
        base.model_copy(update={"id": "two", "number": 2}),
    )
    assert derive_progress(settings, games).can_start_next is True
    games += (base.model_copy(update={"id": "three", "number": 3}),)
    progress = derive_progress(settings, games)
    assert progress.ended is True
    assert progress.can_start_next is False
    assert progress.score == {"A": 2, "B": 0}


# Parent #13 acceptance "A Best-of Series ends on a majority and is not declared
# over while results are pending": only Drafted or Closed Games count a winner,
# so a winner left on a Drafting Game (for example after clearing) is ignored.
def test_progress_counts_winners_only_on_drafted_or_closed_games(
    profile, assignments, character_ids
):
    from nimbus.engine import derive_progress
    from nimbus.models import SeriesFormat

    settings = profile.snapshot().model_copy(
        update={"series_format": SeriesFormat(kind="best_of", games=3)}
    )
    one = drafted(profile, assignments, character_ids, winner="A")
    two = one.model_copy(update={"id": "two", "number": 2, "actions": one.actions[:1]})
    progress = derive_progress(settings, (one, two))
    assert progress.score == {"A": 1, "B": 0}
    assert progress.ended is False and progress.deciding_game is None
    assert progress.pending_results == ()
    complete = two.model_copy(update={"actions": one.actions})
    assert derive_progress(settings, (one, complete)).score == {"A": 2, "B": 0}
    assert derive_progress(settings, (one, complete)).ended is True


# Parent ADR-0034 (amended 2026-11-27): after a Voided Game the next Game is
# always its Replay, so no ordinary next Game can start.
def test_no_ordinary_next_game_after_a_voided_game(profile, assignments, character_ids):
    from nimbus.engine import derive_progress

    settings = profile.snapshot()
    one = drafted(profile, assignments, character_ids)
    assert derive_progress(settings, (one,)).can_start_next is True
    voided = one.model_copy(update={"voided": True})
    assert derive_progress(settings, (voided,)).can_start_next is False


# Parent ADR-0034 (amended 2026-11-27): only the current Game, the last one in
# the Series, can be voided; voiding an earlier Game would renumber the Series
# and change the Locks of the Game in progress.
def test_only_the_current_game_can_be_voided(profile, assignments, character_ids):
    import pytest

    from nimbus.engine import void_game

    one = drafted(profile, assignments, character_ids)
    two = Game(id="two", number=2, assignments=assignments)
    with pytest.raises(ValueError, match="void_not_current"):
        void_game((one, two), one)
    assert void_game((one, two), two).voided is True
    assert void_game((one,), one).voided is True


# Parent #13 (Q11) / ADR-0034: one "Drafted or Closed" rule serves winners,
# Series progress and the next-Game gate, and it agrees with the derived status.
def test_drafted_or_closed_matches_the_derived_status(profile, assignments, character_ids):
    from nimbus.engine import is_drafted_or_closed
    from nimbus.models import PlayerAssignment

    settings = profile.snapshot()
    complete = drafted(profile, assignments, character_ids)
    closed = complete.model_copy(
        update={
            "winner": "A",
            "player_assignments": tuple(
                PlayerAssignment(turn_index=a.turn_index, player_id=f"p{a.turn_index}")
                for a in complete.actions
                if a.kind == "pick"
            ),
        }
    )
    for game in (
        complete,
        closed,
        complete.model_copy(update={"actions": complete.actions[:-1], "winner": "A"}),
        complete.model_copy(update={"voided": True, "winner": "A"}),
    ):
        status = derive_state(settings, profile.catalog, (game,), game).status
        assert is_drafted_or_closed(settings, game) is (status in ("Drafted", "Closed"))


# Parent ADR-0034 (amended 2026-11-27): a Voided current Game takes no live entry.
def test_live_entry_on_a_voided_game_is_rejected_as_voided(profile, assignments, opening_ban_teams):
    from nimbus.engine import check_entry

    settings = profile.snapshot()
    game = Game(id="one", number=1, assignments=assignments, voided=True)
    ban = DraftAction(turn_index=0, team_id=opening_ban_teams[0], kind="ban", character_id=None)
    assert check_entry(settings, profile.catalog, (game,), game, ban) == "game_voided"
