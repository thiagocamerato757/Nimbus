"""BS-013: rule proposal behavior at the agreed engine seam, both Titles."""

import pytest

from nimbus.engine import propose_settings
from nimbus.models import Fearless, Series, Team


# Parent BS-013: proposing Fearless derives changed rule outcomes without editing history.
def test_bs013_fearless_proposal_changes_locks_without_mutation(
    profile, previous_pick, assignments, character_ids
):
    from nimbus.engine import derive_state
    from nimbus.models import Game

    series = Series(
        id="s",
        profile_id=profile.id,
        teams=(Team(id="A", name="A"), Team(id="B", name="B")),
        our_team="A",
        rule_snapshot=profile.snapshot(),
        games=(previous_pick, Game(id="next", number=2, assignments=assignments)),
    )
    updated = propose_settings(
        series, series.rule_snapshot.model_copy(update={"fearless": Fearless(lock_reach="none")})
    )
    assert (
        character_ids[0]
        in derive_state(
            series.rule_snapshot, profile.catalog, series.games, series.games[-1]
        ).locks["A"]
    )
    assert (
        derive_state(
            updated.rule_snapshot, profile.catalog, updated.games, updated.games[-1]
        ).locks["A"]
        == ()
    )
    assert series.rule_snapshot.fearless.id == "hard"


# Parent BS-013: recorded ban turns cannot become picks, even on Voided Games.
def test_bs013_incompatible_order_is_refused(profile, assignments, character_ids):
    from nimbus.models import DraftAction, Game

    settings = profile.snapshot()
    game = Game(
        id="g",
        number=1,
        assignments=assignments,
        voided=True,
        actions=(
            DraftAction(turn_index=0, team_id="A", kind="ban", character_id=character_ids[0]),
        ),
    )
    series = Series(
        id="s",
        profile_id=profile.id,
        teams=(),
        our_team=None,
        rule_snapshot=settings,
        games=(game,),
    )
    turns = list(settings.draft_order.turns)
    turns[0] = turns[0].model_copy(update={"kind": "pick"})
    proposed = settings.model_copy(
        update={"draft_order": settings.draft_order.model_copy(update={"turns": tuple(turns)})}
    )
    with pytest.raises(ValueError, match="incompatible_draft_order"):
        propose_settings(series, proposed)


# Parent #17 format decision: Bo5 2–0 becomes ended in Bo3; past-decision records retained.
@pytest.mark.parametrize("count,past", [(2, ()), (3, (3,))])
def test_bs013_format_change_recomputes_ended_and_past_decision(
    profile, assignments, character_ids, count, past
):
    from nimbus.engine import derive_progress
    from nimbus.models import DraftAction, Game, SeriesFormat

    settings = profile.snapshot().model_copy(update={"series_format": SeriesFormat(games=5)})
    actions = tuple(
        DraftAction(
            turn_index=i,
            team_id="A" if turn.position == "first" else "B",
            kind=turn.kind,
            character_id=character_ids[i],
        )
        for i, turn in enumerate(settings.draft_order.turns)
    )
    games = tuple(
        Game(id=str(i), number=i, assignments=assignments, actions=actions, winner="A")
        for i in range(1, count + 1)
    )
    series = Series(
        id="s", profile_id=profile.id, teams=(), our_team=None, rule_snapshot=settings, games=games
    )
    if count == 2:
        assert not derive_progress(settings, games).ended
    updated = propose_settings(
        series, settings.model_copy(update={"series_format": SeriesFormat(games=3)})
    )
    progress = derive_progress(updated.rule_snapshot, updated.games)
    assert progress.ended
    assert progress.deciding_game == 2
    assert progress.games_past_decision == past
    assert updated.games == games


# Parent #17 format decision: count all non-voided Games, including unfinished drafts.
def test_bs013_format_too_small_counts_pending_but_excludes_voided(profile, assignments):
    from nimbus.models import Game, SeriesFormat

    settings = profile.snapshot()
    games = tuple(Game(id=str(i), number=i, assignments=assignments) for i in range(1, 5))
    series = Series(
        id="s", profile_id=profile.id, teams=(), our_team=None, rule_snapshot=settings, games=games
    )
    proposed = settings.model_copy(update={"series_format": SeriesFormat(games=3)})
    with pytest.raises(ValueError, match="series_format_too_small"):
        propose_settings(series, proposed)
    series = series.model_copy(
        update={"games": (*games[:3], games[3].model_copy(update={"voided": True}))}
    )
    assert propose_settings(series, proposed).rule_snapshot.series_format.games == 3


# Parent BS-013: Fearless proposals create/clear Violations and change Remaining.
def test_bs013_fearless_proposal_violations_and_player_remaining(
    profile, previous_pick, assignments, character_ids, first_pick_index
):
    from nimbus.engine import derive_player_pool, derive_state
    from nimbus.models import DraftAction, Game

    off = profile.snapshot().model_copy(update={"fearless": Fearless(lock_reach="none")})
    second = Game(
        id="next",
        number=2,
        assignments=assignments,
        actions=(
            DraftAction(
                turn_index=first_pick_index, team_id="A", kind="pick", character_id=character_ids[0]
            ),
        ),
    )
    series = Series(
        id="s",
        profile_id=profile.id,
        teams=(),
        our_team=None,
        rule_snapshot=off,
        games=(previous_pick, second),
    )
    before = derive_state(off, profile.catalog, series.games, second)
    proposed = propose_settings(series, off.model_copy(update={"fearless": Fearless()}))
    after = derive_state(proposed.rule_snapshot, profile.catalog, proposed.games, second)
    assert before.violations == ()
    assert [v.rule for v in after.violations] == ["fearless_lock"]
    assert derive_player_pool(before, "A", character_ids[:2]).remaining == tuple(
        sorted(character_ids[:2])
    )
    assert derive_player_pool(after, "A", character_ids[:2]).remaining == (character_ids[1],)
    reverted = propose_settings(proposed, off)
    assert (
        derive_state(reverted.rule_snapshot, profile.catalog, reverted.games, second).violations
        == ()
    )
