"""BS-015: Workspace and Series Disabled Lists through HTTP."""

from test_player_pools_api import (
    save_pool,
    set_lineup,
    start_pool_game,
)
from test_rosters import series

pytest_plugins = ["test_player_pools_api"]


# Parent: BS-015 (Workspace edits leave existing Series unchanged), #16 AC.
# Given a Workspace list, creating a Series copies it; editing either list later
# leaves the other unchanged, and the Series list persists across reads.
def test_bs015_workspace_list_is_copied_and_series_is_editable(pool_workspace):
    client, _created, profile, _person, ids = pool_workspace
    endpoint = f"/api/workspace/disabled/{profile['id']}"
    assert client.post(endpoint, json={"character_ids": [ids[0]]}).status_code == 200
    first = series(client, profile_id=profile["id"])
    assert first["rule_snapshot"]["disabled_characters"] == [ids[0]]
    assert client.post(endpoint, json={"character_ids": [ids[1]]}).status_code == 200
    assert client.get(f"/api/series/{first['id']}").json()["rule_snapshot"]["disabled_characters"] == [ids[0]]
    second = series(client, profile_id=profile["id"])
    assert second["rule_snapshot"]["disabled_characters"] == [ids[1]]
    edited = client.post(f"/api/series/{first['id']}/disabled", json={"character_ids": []})
    assert edited.status_code == 200, edited.text
    assert edited.json()["rule_snapshot"]["disabled_characters"] == []
    assert client.get(endpoint).json() == [ids[1]]


# Parent: BS-015 (Disabled pool exclusion and Game Rule Override).
# Given a Disabled Character in a Declared Pool, the API omits it from Remaining
# and Available Now and rejects its entry until an Override reason is supplied.
def test_bs015_disabled_pool_and_entry_override(pool_workspace):
    client, created, profile, person, ids = pool_workspace
    save_pool(client, created, person, ids[:2])
    assert client.post(f"/api/series/{created['id']}/disabled",
                       json={"character_ids": [ids[0]]}).status_code == 200
    game = start_pool_game(client, created, profile)
    game = set_lineup(client, created, game, person)
    assert game["player_pools"][person["id"]] == {
        "remaining": [ids[1]], "available_now": [ids[1]]
    }
    base = f"/api/series/{created['id']}/games/{game['id']}/actions"
    for turn in created["rule_snapshot"]["draft_order"]["turns"]:
        if turn["kind"] == "pick":
            break
        assert client.post(base, json={"character_id": None}).status_code == 201
    rejected = client.post(base, json={"character_id": ids[0]})
    assert rejected.status_code == 409
    assert rejected.json()["detail"]["code"] == "disabled_character"
    accepted = client.post(base, json={"character_id": ids[0],
                                      "override": {"category": "official_ruling"}})
    assert accepted.status_code == 201, accepted.text
    assert accepted.json()["games"][-1]["state"]["violations"][0]["status"] == "acknowledged"


# Parent: BS-015 (Retired Character not offered; historical records retain it), ADR-0014.
# Given a recorded Character, retiring it in the live catalog removes entry
# availability while preserving the recorded action and current catalog name.
def test_bs015_catalog_retirement_is_live_and_preserves_history(tmp_path):
    import shutil

    import yaml
    from test_api import CurrentClient

    from nimbus.api import create_app
    from nimbus.profiles import DEFAULT_PROFILE_DIR

    directory = tmp_path / "profiles"
    shutil.copytree(DEFAULT_PROFILE_DIR, directory)
    catalog_path = directory / "league-of-legends.catalog.yaml"
    with CurrentClient(create_app(data_dir=tmp_path / "data", profile_dir=directory)) as client:
        created = series(client)
        profile = client.get("/api/profiles").json()[0]
        game = start_pool_game(client, created, profile)
        base = f"/api/series/{created['id']}/games/{game['id']}/actions"
        assert client.post(base, json={"character_id": "Ahri"}).status_code == 201
        catalog = yaml.safe_load(catalog_path.read_text())
        next(c for c in catalog["characters"] if c["id"] == "Ahri")["retired"] = True
        catalog_path.write_text(yaml.safe_dump(catalog))
        fetched = client.get(f"/api/series/{created['id']}").json()["games"][-1]
        assert fetched["actions"][0]["character_id"] == "Ahri"
        assert "Ahri" not in fetched["state"]["available"]["A"]
        assert next(c for c in client.get("/api/profiles").json()[0]["catalog"] if c["id"] == "Ahri")["retired"]
        result = client.post(base, json={"character_id": "Ahri", "override": {"category": "official_ruling"}})
        assert result.status_code == 422
        assert result.json()["detail"]["code"] == "unknown_character"
