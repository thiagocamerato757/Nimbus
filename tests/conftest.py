import pytest
from hypothesis import settings

from nimbus.models import Assignment, DraftAction, Game
from nimbus.profiles import load_profiles

settings.register_profile("nimbus", derandomize=True, database=None, max_examples=80)
settings.load_profile("nimbus")


@pytest.fixture(params=["league-of-legends"])
def profile(request):
    # Add a future sequential Title profile here; engine cases consume only its values.
    return load_profiles()[request.param]


@pytest.fixture
def assignments():
    return (
        Assignment(team_id="A", side="red", position="first"),
        Assignment(team_id="B", side="blue", position="second"),
    )


@pytest.fixture
def previous_pick(assignments):
    return Game(
        id="earlier",
        number=1,
        assignments=assignments,
        actions=(DraftAction(turn_index=6, team_id="A", kind="pick", character_id="Orianna"),),
    )
