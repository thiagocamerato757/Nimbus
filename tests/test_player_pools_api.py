"""BS-002 and BS-004 through the agreed HTTP seam."""

from pathlib import Path

import pytest
from test_api import CurrentClient
from test_rosters import player, series

from nimbus.api import create_app
from nimbus.profiles import DEFAULT_PROFILE_DIR


@pytest.fixture(
    params=[
        (DEFAULT_PROFILE_DIR, "league-of-legends"),
        (Path(__file__).parent / "fixtures" / "profiles", "synthetic-deadlock"),
    ]
)
def pool_workspace(request, tmp_path):
    directory, profile_id = request.param
    with CurrentClient(create_app(data_dir=tmp_path, profile_dir=directory)) as client:
        created = series(client, profile_id=profile_id)
        profile = next(p for p in client.get("/api/profiles").json() if p["id"] == profile_id)
        person = player(client, created["teams"][0]["roster_id"], name="Mid", role="mid")
        ids = [c["id"] for c in profile["catalog"] if not c["retired"]]
        yield client, created, profile, person, ids


def save_pool(client, created, person, ids):
    response = client.post(
        f"/api/series/{created['id']}/teams/A/players/{person['id']}/pool",
        json={"character_ids": ids},
    )
    assert response.status_code == 200, response.text


def start_pool_game(client, created, profile):
    response = client.post(
        f"/api/series/{created['id']}/games",
        json={"team_a_side": profile["sides"][0], "first_pick_team": "A"},
    )
    assert response.status_code == 201, response.text
    return response.json()["games"][-1]


def set_lineup(client, created, game, person):
    response = client.post(
        f"/api/series/{created['id']}/games/{game['id']}/lineups",
        json={"team_id": "A", "player_ids": [person["id"]]},
    )
    assert response.status_code == 200, response.text
    return response.json()["games"][-1]


# Parent: BS-002: the HTTP response exposes five Remaining Characters after an
# opponent picked one of a Player's six Declared Characters in the earlier Game.
def test_bs002_viewing_game_two_returns_five_remaining(pool_workspace):
    client, created, profile, person, ids = pool_workspace
    pool = ids[:6]
    save_pool(client, created, person, pool)
    first = start_pool_game(client, created, profile)
    base = f"/api/series/{created['id']}/games/{first['id']}"
    opponent_picked = False
    others = iter(ids[6:])
    for turn in created["rule_snapshot"]["draft_order"]["turns"]:
        character = None
        if turn["kind"] == "pick":
            if turn["position"] == "second" and not opponent_picked:
                character, opponent_picked = pool[0], True
            else:
                character = next(others)
        response = client.post(base + "/actions", json={"character_id": character})
        assert response.status_code == 201, response.text
    second = start_pool_game(client, created, profile)
    second = set_lineup(client, created, second, person)
    result = second["player_pools"][person["id"]]
    assert result["remaining"] == sorted(pool[1:])
    assert len(result["remaining"]) == 5


# Parent: BS-004: reading the Lineup's pools after one ban and a teammate pick
# exposes four Remaining and two Available Now, without a Player Assignment.
def test_bs004_viewing_pool_returns_four_remaining_and_two_available(pool_workspace):
    client, created, profile, person, ids = pool_workspace
    pool = ids[:4]
    save_pool(client, created, person, pool)
    game = start_pool_game(client, created, profile)
    set_lineup(client, created, game, person)
    base = f"/api/series/{created['id']}/games/{game['id']}"
    for index, turn in enumerate(created["rule_snapshot"]["draft_order"]["turns"]):
        character = pool[0] if index == 0 else pool[1] if turn["kind"] == "pick" else None
        response = client.post(base + "/actions", json={"character_id": character})
        assert response.status_code == 201, response.text
        if turn["kind"] == "pick":
            break
    fetched = client.get(f"/api/series/{created['id']}").json()["games"][-1]
    result = fetched["player_pools"][person["id"]]
    assert result == {"remaining": sorted(pool), "available_now": sorted(pool[2:])}
    assert len(result["remaining"]) == 4
    assert len(result["available_now"]) == 2
