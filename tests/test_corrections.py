"""BS-010 corrections are saved and visible through the real HTTP application."""

from test_api import CurrentClient

from nimbus.api import create_app


def start(client):
    series = client.post(
        "/api/series",
        json={
            "profile_id": "league-of-legends",
            "team_a": "A",
            "team_b": "B",
        },
    ).json()
    base = f"/api/series/{series['id']}"
    game = client.post(
        base + "/games",
        json={
            "team_a_side": "blue",
            "first_pick_team": "A",
        },
    ).json()["games"][0]
    return base, f"{base}/games/{game['id']}/actions"


def test_bs010_correction_is_saved_with_history_across_restart(tmp_path):
    # Parent BS-010: Given a recorded ban, replacing it saves the Character
    # and exposes the before/after edit through the API after restarting.
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        base, actions = start(client)
        client.post(actions, json={"character_id": "Ahri"})
        result = client.post(actions + "/0/correct", json={"character_id": "Akali"})
        assert result.status_code == 200, result.text
        game = result.json()["games"][0]
        assert game["actions"][0]["character_id"] == "Akali"
        edit = game["edit_history"][0]
        assert edit["before"]["character_id"] == "Ahri"
        assert edit["after"]["character_id"] == "Akali"
        assert edit["recorded_at"].endswith("+00:00")
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        assert client.get(base).json()["games"][0] == game


def three_games(client):
    base, actions = start(client)
    catalogs = client.get("/api/profiles").json()[0]["catalog"]
    characters = [c["id"] for c in catalogs if not c["retired"]]
    paths = []
    picks = []
    offset = 0
    for number in range(3):
        if number:
            game = client.post(
                base + "/games",
                json={
                    "team_a_side": "blue",
                    "first_pick_team": "A",
                },
            ).json()["games"][-1]
            actions = f"{base}/games/{game['id']}/actions"
        paths.append(actions)
        for index, turn in enumerate(
            client.get(base).json()["rule_snapshot"]["draft_order"]["turns"]
        ):
            character = None if turn["kind"] == "ban" else characters[offset]
            if character:
                offset += 1
                if index == 6:
                    picks.append(character)
            result = client.post(actions, json={"character_id": character})
            assert result.status_code == 201, result.text
    return base, paths, picks


def test_bs010_acknowledgement_reopens_and_returns_when_cause_is_reversed(tmp_path):
    # Parent BS-010: Game 1 correction creates Game 3's Open Violation;
    # acknowledgement survives restart, reopens on changed cause and returns on reversal.
    reason = {"category": "official_ruling", "note": "Stage ruling"}
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        base, paths, picks = three_games(client)
        original_third_actions = client.get(base).json()["games"][2]["actions"]
        corrected = client.post(paths[0] + "/6/correct", json={"character_id": picks[2]})
        assert corrected.status_code == 200, corrected.text
        third = corrected.json()["games"][2]
        assert third["actions"] == original_third_actions
        assert third["state"]["violations"] == [
            {"turn_index": 6, "rule": "fearless_lock", "status": "open", "reason": None},
        ]
        result = client.post(
            paths[2] + "/6/acknowledge",
            json={
                "rule": "fearless_lock",
                "reason": reason,
            },
        )
        assert result.status_code == 200, result.text
        assert result.json()["games"][2]["state"]["violations"][0]["reason"] == reason
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        assert (
            client.get(base).json()["games"][2]["state"]["violations"][0]["status"]
            == "acknowledged"
        )
        changed = client.post(paths[1] + "/6/correct", json={"character_id": picks[2]}).json()
        assert changed["games"][2]["state"]["violations"][0]["status"] == "open"
        reversed_ = client.post(paths[1] + "/6/correct", json={"character_id": picks[1]}).json()
        assert reversed_["games"][2]["state"]["violations"][0] == {
            "turn_index": 6,
            "rule": "fearless_lock",
            "status": "acknowledged",
            "reason": reason,
        }
        removed = client.post(paths[0] + "/6/correct", json={"character_id": picks[0]}).json()
        assert removed["games"][2]["state"]["violations"] == []


def test_bs010_only_latest_current_action_can_be_cleared_with_history(tmp_path):
    # Parent BS-010: clearing the most recent current action restores its turn;
    # attempting an earlier turn leaves facts, history and workspace version alone.
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        base, actions = start(client)
        client.post(actions, json={"character_id": "Ahri"})
        original = client.post(actions, json={"character_id": "Akali"})
        rejected = client.post(actions + "/0/clear", json={})
        assert rejected.status_code == 409, rejected.text
        assert rejected.headers["x-nimbus-version"] == original.headers["x-nimbus-version"]
        assert client.get(base).json() == original.json()
        cleared = client.post(actions + "/1/clear", json={})
        assert cleared.status_code == 200, cleared.text
        game = cleared.json()["games"][0]
        assert game["state"]["next_turn"] == {"index": 1, "team_id": "B", "kind": "ban"}
        assert [a["character_id"] for a in game["actions"]] == ["Ahri"]
        assert game["edit_history"][0]["before"]["character_id"] == "Akali"
        assert game["edit_history"][0]["after"] is None


def test_bs010_empty_current_game_cannot_clear_earlier_game(tmp_path):
    # Parent BS-010: with an empty Game 2, no Game 1 action can be cleared.
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        base, actions = start(client)
        catalog = client.get("/api/profiles").json()[0]["catalog"]
        characters = iter(c["id"] for c in catalog if not c["retired"])
        for turn in client.get(base).json()["rule_snapshot"]["draft_order"]["turns"]:
            result = client.post(
                actions,
                json={
                    "character_id": None if turn["kind"] == "ban" else next(characters),
                },
            )
            assert result.status_code == 201, result.text
        started = client.post(
            base + "/games",
            json={
                "team_a_side": "blue",
                "first_pick_team": "A",
            },
        )
        current_actions = f"{base}/games/{started.json()['games'][1]['id']}/actions"
        for path in (actions + "/19/clear", current_actions + "/0/clear"):
            rejected = client.post(path, json={})
            assert rejected.status_code == 409, rejected.text
            assert rejected.json()["detail"]["code"] == "cannot_clear_action"
            assert rejected.headers["x-nimbus-version"] == started.headers["x-nimbus-version"]
            assert client.get(base).json() == started.json()


import pytest


@pytest.mark.parametrize(
    "turn,character,error",
    [
        (99, "Ahri", "action_not_found"),
        (0, "missing", "unknown_character"),
        (6, None, "cannot_skip_pick"),
    ],
)
def test_bs010_structural_rejection_keeps_facts_and_history(tmp_path, turn, character, error):
    # Parent BS-010: corrections retain Structural Invariants and reject atomically.
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        base, actions = start(client)
        for _ in range(6):
            client.post(actions, json={"character_id": None})
        recorded = client.post(actions, json={"character_id": "Ahri"})
        rejected = client.post(actions + f"/{turn}/correct", json={"character_id": character})
        assert rejected.status_code == 422, rejected.text
        assert rejected.json()["detail"]["code"] == error
        assert rejected.headers["x-nimbus-version"] == recorded.headers["x-nimbus-version"]
        assert client.get(base).json() == recorded.json()


def test_bs010_retired_correction_is_deliberate_and_persists(tmp_path):
    import shutil

    import yaml

    from nimbus.profiles import DEFAULT_PROFILE_DIR

    # Issue #11 acceptance: correction can select a Retired Character.
    directory = tmp_path / "profiles"
    shutil.copytree(DEFAULT_PROFILE_DIR, directory)
    catalog_path = directory / "league-of-legends.catalog.yaml"
    catalog = yaml.safe_load(catalog_path.read_text())
    next(c for c in catalog["characters"] if c["id"] == "Akali")["retired"] = True
    catalog_path.write_text(yaml.safe_dump(catalog))
    with CurrentClient(create_app(data_dir=tmp_path / "data", profile_dir=directory)) as client:
        base, actions = start(client)
        client.post(actions, json={"character_id": "Ahri"})
        result = client.post(actions + "/0/correct", json={"character_id": "Akali"})
        assert result.status_code == 200, result.text
        assert result.json()["games"][0]["actions"][0]["character_id"] == "Akali"
        assert (
            client.get(base).json()["games"][0]["edit_history"][0]["after"]["character_id"]
            == "Akali"
        )


def test_bs010_history_keeps_character_catalog_references(tmp_path):
    import shutil

    import yaml

    from nimbus.profiles import DEFAULT_PROFILE_DIR

    # Parent BS-010 history + ADR-0014: the original Character remains a stored
    # record after correction and must still exist in the Character Catalog.
    directory = tmp_path / "profiles"
    shutil.copytree(DEFAULT_PROFILE_DIR, directory)
    data = tmp_path / "data"
    with CurrentClient(create_app(data_dir=data, profile_dir=directory)) as client:
        _, actions = start(client)
        client.post(actions, json={"character_id": "Ahri"})
        client.post(actions + "/0/correct", json={"character_id": "Akali"})
    path = directory / "league-of-legends.catalog.yaml"
    catalog = yaml.safe_load(path.read_text())
    catalog["characters"] = [c for c in catalog["characters"] if c["id"] != "Ahri"]
    path.write_text(yaml.safe_dump(catalog))
    with CurrentClient(create_app(data_dir=data, profile_dir=directory)) as client:
        result = client.get("/api/profiles")
        assert result.status_code == 500, result.text
        assert result.json()["detail"]["code"] == "profile_load_failed"
        assert "Ahri" in result.json()["detail"]["message"]


def test_bs010_schema4_migration_preserves_actions_acknowledgements_and_backup(tmp_path):
    import shutil
    import sqlite3

    # Parent BS-010 / ADR-0032: adding edit history preserves existing facts and
    # acknowledgements, and an automatic pre-migration backup can be restored.
    data = tmp_path / "data"
    with CurrentClient(create_app(data_dir=data)) as client:
        base, actions = start(client)
        client.post(actions, json={"character_id": "Ahri"})
        previous = client.post(
            actions,
            json={
                "character_id": "Ahri",
                "override": {"category": "official_ruling", "note": "Existing ruling"},
            },
        ).json()
    # Fixture: the immediately preceding supported schema has no history column.
    with sqlite3.connect(data / "nimbus.sqlite3") as old:
        old.execute("ALTER TABLE games DROP COLUMN edit_history")
        old.execute("PRAGMA user_version = 4")
    with CurrentClient(create_app(data_dir=data)) as client:
        migrated = client.get(base).json()
        assert migrated == previous
        assert migrated["games"][0]["edit_history"] == []
        assert migrated["games"][0]["state"]["violations"][0]["reason"]["note"] == "Existing ruling"
        backups = client.get("/api/backups").json()
        assert len(backups) == 1
        assert backups[0]["verified"] is True
    restored = tmp_path / "restored"
    restored.mkdir()
    shutil.copyfile(data / "backups" / backups[0]["name"], restored / "nimbus.sqlite3")
    with CurrentClient(create_app(data_dir=restored)) as client:
        assert client.get(base).json() == previous
