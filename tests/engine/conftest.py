from pathlib import Path

import pytest

from nimbus.models import Assignment, DraftAction, Game
from nimbus.profiles import DEFAULT_PROFILE_DIR, load_profiles

TEST_PROFILE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "profiles"


@pytest.fixture(
    scope="session",
    autouse=True,
    params=[
        pytest.param((DEFAULT_PROFILE_DIR, "league-of-legends"), id="league-of-legends"),
        pytest.param((TEST_PROFILE_DIR, "synthetic-deadlock"), id="synthetic-deadlock"),
    ],
)
def profile(request):
    directory, identifier = request.param
    return load_profiles(directory)[identifier]


@pytest.fixture(scope="session")
def opening_ban_teams(profile):
    # Independent worked examples: LoL alternates, DS-004 groups A, BB, AA, B.
    return {
        "league-of-legends": ("A", "B", "A", "B", "A", "B"),
        "synthetic-deadlock": ("A", "B", "B", "A", "A", "B"),
    }[profile.id]


@pytest.fixture(scope="session")
def assignments(profile):
    return (
        Assignment(team_id="A", side=profile.sides[1], position="first"),
        Assignment(team_id="B", side=profile.sides[0], position="second"),
    )


@pytest.fixture(scope="session")
def character_ids(profile):
    return tuple(character.id for character in profile.catalog if not character.retired)


@pytest.fixture(scope="session")
def first_pick_index(profile):
    return next(
        i for i, turn in enumerate(profile.snapshot().draft_order.turns) if turn.kind == "pick"
    )


@pytest.fixture(scope="session")
def previous_pick(assignments, character_ids, first_pick_index):
    return Game(
        id="earlier",
        number=1,
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
