"""BS-013 through the agreed API seam."""

from test_player_pools_api import save_pool, set_lineup, start_pool_game

pytest_plugins = ["test_player_pools_api"]


# Parent BS-013 + Disabled List AC: preview before saving, cancellation preserves data/version.
def test_bs013_disabled_preview_shows_created_cleared_violations_and_remaining(pool_workspace):
    client, created, profile, person, ids = pool_workspace
    save_pool(client, created, person, ids[:2])
    game = set_lineup(client, created, start_pool_game(client, created, profile), person)
    base = f"/api/series/{created['id']}"
    assert (
        client.post(f"{base}/games/{game['id']}/actions", json={"character_id": ids[0]}).status_code
        == 201
    )
    original = client.get(base)
    proposal = {"disabled_characters": [ids[0]]}
    preview = client.post(base + "/settings-preview", json=proposal)
    assert preview.status_code == 200, preview.text
    assert preview.headers["x-nimbus-version"] == original.headers["x-nimbus-version"]
    before, after = preview.json()["before"], preview.json()["after"]
    assert before["games"][0]["state"]["violations"] == []
    assert after["games"][0]["state"]["violations"][0]["rule"] == "disabled_character"
    assert after["games"][0]["player_pools"][person["id"]]["remaining"] == [ids[1]]
    assert client.get(base).json() == original.json()  # Cancel means discard the preview.
    saved = client.post(base + "/settings", json=proposal)
    assert saved.status_code == 200, saved.text
    assert saved.json() == after
    cleared = client.post(base + "/settings-preview", json={"disabled_characters": []}).json()
    assert cleared["before"]["games"][0]["state"]["violations"]
    assert cleared["after"]["games"][0]["state"]["violations"] == []
    assert cleared["after"]["games"][0]["player_pools"][person["id"]]["remaining"] == sorted(
        ids[:2]
    )


# Parent BS-013: changing Fearless shows created/cleared Violations and Players affected.
def test_bs013_fearless_preview_then_explicit_save(pool_workspace):
    from test_lifecycle import fill

    client, created, profile, person, ids = pool_workspace
    base = f"/api/series/{created['id']}"
    off = {"fearless": {"lock_reach": "none", "lock_sources": "picks"}}
    assert client.post(base + "/settings", json=off).status_code == 200
    save_pool(client, created, person, ids[:2])
    first = start_pool_game(client, created, profile)
    fill(client, created, first, iter(ids))
    second = set_lineup(client, created, start_pool_game(client, created, profile), person)
    actions = base + f"/games/{second['id']}/actions"
    for turn in created["rule_snapshot"]["draft_order"]["turns"]:
        assert (
            client.post(
                actions, json={"character_id": ids[0] if turn["kind"] == "pick" else None}
            ).status_code
            == 201
        )
        if turn["kind"] == "pick":
            break
    original = client.get(base).json()
    hard = {"fearless": {"lock_reach": "both_teams", "lock_sources": "picks"}}
    preview = client.post(base + "/settings-preview", json=hard)
    assert preview.status_code == 200, preview.text
    after = preview.json()["after"]
    assert after["games"][-1]["state"]["violations"][0]["rule"] == "fearless_lock"
    assert after["games"][-1]["player_pools"][person["id"]]["remaining"] == []
    assert client.get(base).json() == original
    assert client.post(base + "/settings", json=hard).json() == after
    cleared = client.post(base + "/settings-preview", json=off).json()["after"]
    assert cleared["games"][-1]["state"]["violations"] == []
    assert cleared["games"][-1]["player_pools"][person["id"]]["remaining"] == sorted(ids[:2])


# Parent BS-013: updated profile order is opt-in, incompatible history refuses preview/save.
def test_bs013_reloaded_profile_keeps_snapshot_and_refuses_incompatible_order(tmp_path):
    import shutil

    import yaml
    from test_api import CurrentClient
    from test_rosters import series, start

    from nimbus.api import create_app
    from nimbus.profiles import DEFAULT_PROFILE_DIR

    directory = tmp_path / "profiles"
    shutil.copytree(DEFAULT_PROFILE_DIR, directory)
    data = tmp_path / "data"
    with CurrentClient(create_app(data_dir=data, profile_dir=directory)) as client:
        created = series(client)
        base = f"/api/series/{created['id']}"
        game = start(client, created)
        assert (
            client.post(
                base + f"/games/{game['id']}/actions", json={"character_id": "Ahri"}
            ).status_code
            == 201
        )
        original = client.get(base).json()
    path = directory / "league-of-legends.rules.yaml"
    rules = yaml.safe_load(path.read_text())
    turns = rules["draft_orders"][0]["turns"]
    pick = next(
        i
        for i, t in enumerate(turns)
        if t["kind"] == "pick" and t["position"] == turns[0]["position"]
    )
    turns[0], turns[pick] = turns[pick], turns[0]
    path.write_text(yaml.safe_dump(rules))
    with CurrentClient(create_app(data_dir=data, profile_dir=directory)) as client:
        assert client.get(base).json() == original
        assert (
            client.get("/api/profiles").json()[0]["draft_orders"][0]["turns"][0]["kind"] == "pick"
        )
        for endpoint in ("settings-preview", "settings"):
            result = client.post(
                base + "/" + endpoint,
                json={"draft_order_id": created["rule_snapshot"]["draft_order"]["id"]},
            )
            assert result.status_code == 409, result.text
            assert result.json()["detail"]["code"] == "incompatible_draft_order"
        assert client.get(base).json() == original


# Parent #17 format decision: preview ended/past decision and reject too-small format.
def test_bs013_format_preview_and_refusal(pool_workspace):
    from test_lifecycle import fill

    client, created, profile, _person, ids = pool_workspace
    base = f"/api/series/{created['id']}"
    assert (
        client.post(
            base + "/settings", json={"fearless": {"lock_reach": "none", "lock_sources": "picks"}}
        ).status_code
        == 200
    )
    for _ in range(2):
        game = start_pool_game(client, created, profile)
        fill(client, created, game, iter(ids))
        assert (
            client.post(base + f"/games/{game['id']}/winner", json={"winner": "A"}).status_code
            == 200
        )
    proposal = {"series_format": {"kind": "best_of", "games": 3}}
    preview = client.post(base + "/settings-preview", json=proposal).json()
    assert preview["before"]["progress"]["ended"] is False
    assert preview["after"]["progress"]["ended"] is True
    assert client.get(base).json()["progress"]["ended"] is False
    third = start_pool_game(client, created, profile)
    preview = client.post(base + "/settings-preview", json=proposal).json()
    assert preview["after"]["progress"]["games_past_decision"] == [3]
    # A fourth started, unfinished Game still counts towards the maximum.
    fill(client, created, third, iter(ids))
    start_pool_game(client, created, profile)
    for endpoint in ("settings-preview", "settings"):
        result = client.post(base + "/" + endpoint, json=proposal)
        assert result.status_code == 409, result.text
        assert result.json()["detail"]["code"] == "series_format_too_small"


# Parent BS-013: explicit save must not overwrite edits made since its preview.
def test_bs013_preview_version_guards_save(pool_workspace):
    from fastapi.testclient import TestClient

    client, created, _profile, _person, ids = pool_workspace
    base = f"/api/series/{created['id']}"
    proposal = {"disabled_characters": [ids[0]]}
    preview = client.post(base + "/settings-preview", json=proposal)
    assert client.post(base + "/disabled", json={"character_ids": [ids[1]]}).status_code == 200
    result = TestClient.post(
        client,
        base + "/settings",
        json=proposal,
        headers={"x-nimbus-version": preview.headers["x-nimbus-version"]},
    )
    assert result.status_code == 409
    assert result.json()["detail"]["code"] == "stale_version"
    assert client.get(base).json()["rule_snapshot"]["disabled_characters"] == [ids[1]]
