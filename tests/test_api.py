from fastapi.testclient import TestClient

from nimbus.api import create_app


class CurrentClient(TestClient):
    """Existing sequential scenarios submit each edit from their latest API state."""

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args, base_url="http://127.0.0.1:8000", headers={"x-nimbus-app": "1"}, **kwargs
        )

    def post(self, url, **kwargs):
        version = self.get("/api/series").headers["x-nimbus-version"]
        return super().post(url, headers={"x-nimbus-version": version}, **kwargs)


def test_bs001_starting_next_game_locks_previous_pick_for_both_teams(tmp_path):
    # Parent BS-001, API seam: starting Game 2 exposes Game 1 picks as locked for both Teams.
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        created = client.post(
            "/api/series",
            json={
                "team_a": "Team A",
                "team_b": "Team B",
                "our_team": "A",
                "profile_id": "league-of-legends",
            },
        )
        assert created.status_code == 201, created.text
        series = created.json()
        game = client.post(
            f"/api/series/{series['id']}/games",
            json={
                "team_a_side": "red",
                "first_pick_team": "A",
            },
        ).json()["games"][0]
        catalog = client.get("/api/profiles").json()[0]["catalog"]
        others = [c["id"] for c in catalog if c["id"] != "Orianna"]
        for index, turn in enumerate(series["rule_snapshot"]["draft_order"]["turns"]):
            character = "Orianna" if index == 6 else others[index]
            result = client.post(
                f"/api/series/{series['id']}/games/{game['id']}/actions",
                json={"character_id": character},
            )
            assert result.status_code == 201, result.text
        started = client.post(
            f"/api/series/{series['id']}/games",
            json={"team_a_side": "blue", "first_pick_team": "B"},
        )
        assert started.status_code == 201, started.text
        second = started.json()["games"][1]
        assert "Orianna" in second["state"]["locks"]["A"]
        assert "Orianna" in second["state"]["locks"]["B"]


def test_bs009_locked_pick_is_rejected_without_advancing_turn(tmp_path):
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        series = client.post(
            "/api/series",
            json={
                "team_a": "Team A",
                "team_b": "Team B",
                "profile_id": "league-of-legends",
            },
        ).json()
        base = f"/api/series/{series['id']}"
        game = client.post(
            f"{base}/games",
            json={
                "team_a_side": "red",
                "first_pick_team": "A",
            },
        ).json()["games"][0]
        catalog = [
            c["id"]
            for c in client.get("/api/profiles").json()[0]["catalog"]
            if not c["retired"] and c["id"] != "Orianna"
        ]
        for i, _ in enumerate(series["rule_snapshot"]["draft_order"]["turns"]):
            assert (
                client.post(
                    f"{base}/games/{game['id']}/actions",
                    json={"character_id": "Orianna" if i == 6 else catalog[i]},
                ).status_code
                == 201
            )
        second = client.post(
            f"{base}/games",
            json={
                "team_a_side": "red",
                "first_pick_team": "A",
            },
        ).json()["games"][1]
        for _ in range(6):
            client.post(f"{base}/games/{second['id']}/actions", json={"character_id": None})
        rejected = client.post(
            f"{base}/games/{second['id']}/actions", json={"character_id": "Orianna"}
        )
        assert rejected.status_code == 409
        assert rejected.json()["detail"] == {
            "code": "fearless_lock",
            "message": "Fearless Lock: this Character was picked in an earlier Game.",
        }
        current = client.get(base).json()["games"][1]
        assert len(current["actions"]) == 6
        assert current["state"]["next_turn"] == {"index": 6, "team_id": "A", "kind": "pick"}


def test_incomplete_draft_prevents_next_game_and_tracks_side_independently(tmp_path):
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        series = client.post(
            "/api/series",
            json={
                "team_a": "Team A",
                "team_b": "Team B",
                "profile_id": "league-of-legends",
            },
        ).json()
        base = f"/api/series/{series['id']}"
        first = client.post(
            f"{base}/games",
            json={
                "team_a_side": "red",
                "first_pick_team": "A",
            },
        ).json()["games"][0]
        assert first["assignments"] == [
            {"team_id": "A", "side": "red", "position": "first"},
            {"team_id": "B", "side": "blue", "position": "second"},
        ]
        assert first["state"]["next_turn"]["team_id"] == "A"
        blocked = client.post(f"{base}/games", json={"team_a_side": "blue", "first_pick_team": "B"})
        assert blocked.status_code == 409
        assert blocked.json()["detail"]["code"] == "draft_incomplete"
        assert len(client.get(base).json()["games"]) == 1


def test_series_snapshot_and_actions_survive_restart_and_profile_edits(tmp_path):
    import shutil

    import yaml

    from nimbus.profiles import DEFAULT_PROFILE_DIR

    profile_dir = tmp_path / "profiles"
    shutil.copytree(DEFAULT_PROFILE_DIR, profile_dir)
    data = tmp_path / "data"
    with CurrentClient(create_app(data_dir=data, profile_dir=profile_dir)) as client:
        series = client.post(
            "/api/series",
            json={
                "team_a": "Team A",
                "team_b": "Team B",
                "profile_id": "league-of-legends",
                "our_team": "B",
            },
        ).json()
        base = f"/api/series/{series['id']}"
        game = client.post(
            f"{base}/games",
            json={
                "team_a_side": "red",
                "first_pick_team": "A",
            },
        ).json()["games"][0]
        client.post(f"{base}/games/{game['id']}/actions", json={"character_id": "Ahri"})
    path = profile_dir / "league-of-legends.rules.yaml"
    rules = yaml.safe_load(path.read_text())
    rules["draft_orders"][0]["id"] = rules["default_draft_order"] = "edited-order"
    rules["draft_orders"][0]["turns"][0]["position"] = "second"
    rules["rule_settings"]["banning_locked"] = "allow"
    path.write_text(yaml.safe_dump(rules))
    with CurrentClient(create_app(data_dir=data, profile_dir=profile_dir)) as restarted:
        restored = restarted.get(base).json()
        assert restored["rule_snapshot"] == series["rule_snapshot"]
        assert restored["our_team"] == "B"
        assert restored["games"][0]["actions"] == [
            {"turn_index": 0, "team_id": "A", "kind": "ban", "character_id": "Ahri"},
        ]
        assert restarted.get("/api/series").json()[0]["id"] == series["id"]
        fresh = restarted.post(
            "/api/series",
            json={
                "team_a": "C",
                "team_b": "D",
                "profile_id": "league-of-legends",
            },
        ).json()
        assert fresh["rule_snapshot"]["draft_order"]["id"] == "edited-order"
        assert fresh["rule_snapshot"]["rule_settings"]["banning_locked"] == "allow"


def test_issue9_creation_choices_are_snapshotted_and_persisted(tmp_path):
    # US-001/US-005: creation chooses profile settings and optional Series/Game Patch.
    body = {
        "profile_id": "league-of-legends",
        "team_a": "Visitors",
        "team_b": "Guests",
        "draft_order_id": "lol-pro-2026",
        "series_format": {"kind": "fixed_length", "games": 4},
        "fearless": {"lock_reach": "none", "lock_sources": "picks_and_bans"},
        "patch": "26.23",
        "record_type": "scrim",
    }
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        response = client.post("/api/series", json=body)
        assert response.status_code == 201, response.text
        series = response.json()
        assert series["our_team"] is None
        assert series["record_type"] == "scrim"
        assert series["patch"] == "26.23"
        assert series["rule_snapshot"]["series_format"] == {"kind": "fixed_length", "games": 4}
        assert series["rule_snapshot"]["fearless"] == {
            "id": "custom",
            "lock_reach": "none",
            "lock_sources": "picks_and_bans",
        }
        base = f"/api/series/{series['id']}"
        response = client.post(
            f"{base}/games", json={"team_a_side": "blue", "first_pick_team": "A", "patch": "26.24"}
        )
        assert response.status_code == 201, response.text
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        stored = client.get(base).json()
        assert stored["rule_snapshot"] == series["rule_snapshot"]
        assert stored["games"][0]["patch"] == "26.24"
        assert stored["patch"] == "26.23"


def test_bs028_api_names_rejected_combination(tmp_path):
    # Parent BS-028: the API exposes the same validation error as the engine.
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        response = client.post(
            "/api/series",
            json={
                "profile_id": "league-of-legends",
                "team_a": "A",
                "team_b": "B",
                "fearless": {"lock_reach": "picking_team", "lock_sources": "picks_and_bans"},
            },
        )
        assert response.status_code == 422, response.text
        assert "picking_team" in response.text and "picks_and_bans" in response.text


import pytest


@pytest.mark.parametrize("ban_team, expected_status", [("A", 201), ("B", 409)])
def test_bs003_soft_fearless_ban_is_rejected_only_for_opponent(tmp_path, ban_team, expected_status):
    # Parent BS-003: A may ban its own previous pick; B's ban would be wasted.
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        series = client.post(
            "/api/series",
            json={
                "profile_id": "league-of-legends",
                "team_a": "A",
                "team_b": "B",
                "fearless": {"lock_reach": "picking_team", "lock_sources": "picks"},
            },
        ).json()
        base = f"/api/series/{series['id']}"
        game = client.post(
            f"{base}/games", json={"team_a_side": "blue", "first_pick_team": "A"}
        ).json()["games"][0]
        catalog = [
            c["id"]
            for c in client.get("/api/profiles").json()[0]["catalog"]
            if c["id"] != "Orianna"
        ]
        for i, _ in enumerate(series["rule_snapshot"]["draft_order"]["turns"]):
            response = client.post(
                f"{base}/games/{game['id']}/actions",
                json={"character_id": "Orianna" if i == 6 else catalog[i]},
            )
            assert response.status_code == 201, response.text
        second = client.post(
            f"{base}/games", json={"team_a_side": "blue", "first_pick_team": ban_team}
        ).json()["games"][-1]
        response = client.post(
            f"{base}/games/{second['id']}/actions", json={"character_id": "Orianna"}
        )
        assert response.status_code == expected_status, response.text
        if expected_status == 201:
            assert response.json()["games"][-1]["actions"][0]["character_id"] == "Orianna"
        else:
            assert response.json()["detail"]["code"] == "wasted_ban"
            unchanged = client.get(base).json()["games"][-1]
            assert unchanged["actions"] == []
            assert unchanged["state"]["next_turn"]["index"] == 0


@pytest.mark.parametrize("schema_version", [1, 2])
def test_issue9_migration_preserves_old_series_and_verified_backup(tmp_path, schema_version):
    # US-001 / ADR-0032: legacy persisted facts survive additive settings migration.
    import json
    import shutil
    import sqlite3
    from pathlib import Path

    from nimbus.profiles import load_profiles

    data = tmp_path / "data"
    data.mkdir()
    migrations = Path(__file__).parents[1] / "src/nimbus/migrations"
    with sqlite3.connect(data / "nimbus.sqlite3") as old:
        old.executescript((migrations / "001_initial.sql").read_text())
        if schema_version == 2:
            old.executescript((migrations / "002_workspace_version.sql").read_text())
        old.execute(
            "INSERT INTO series VALUES (?, ?, ?, ?, ?)",
            (
                "legacy",
                "league-of-legends",
                json.dumps([{"id": "A", "name": "Old A"}, {"id": "B", "name": "Old B"}]),
                None,
                load_profiles()["league-of-legends"].snapshot().model_dump_json(),
            ),
        )
        old.execute(
            "INSERT INTO games VALUES (?, ?, ?, ?)",
            (
                "old-game",
                "legacy",
                1,
                json.dumps(
                    [
                        {"team_id": "A", "side": "blue", "position": "first"},
                        {"team_id": "B", "side": "red", "position": "second"},
                    ]
                ),
            ),
        )
        old.execute(
            "INSERT INTO draft_actions VALUES (?, ?, ?, ?, ?)",
            ("old-game", 0, "A", "ban", "Orianna"),
        )
    with CurrentClient(create_app(data_dir=data)) as client:
        series = client.get("/api/series/legacy").json()
        assert series["teams"][0]["name"] == "Old A"
        assert series["games"][0]["actions"] == [
            {"turn_index": 0, "team_id": "A", "kind": "ban", "character_id": "Orianna"}
        ]
        assert series["patch"] is None
        assert series["record_type"] == "official"
        backup = client.get("/api/backups").json()[0]
        assert backup["verified"] is True
    restored = tmp_path / "restored"
    restored.mkdir()
    shutil.copyfile(data / "backups" / backup["name"], restored / "nimbus.sqlite3")
    with CurrentClient(create_app(data_dir=restored)) as client:
        assert client.get("/api/series/legacy").json() == series


@pytest.mark.parametrize(
    "setting",
    [
        {"series_format": {"kind": "best_of", "games": 2}},
        {"series_format": {"kind": "fixed_length", "games": 99}},
        {"draft_order_id": "missing"},
    ],
)
def test_issue9_creation_rejects_invalid_or_unavailable_format_and_order(tmp_path, setting):
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        response = client.post(
            "/api/series",
            json={"profile_id": "league-of-legends", "team_a": "A", "team_b": "B", **setting},
        )
        assert response.status_code == 422
        assert client.get("/api/series").json() == []


@pytest.mark.parametrize(
    "reach, sources, label",
    [
        ("none", "picks", "off"),
        ("none", "picks_and_bans", "custom"),
        ("picking_team", "picks", "soft"),
        ("both_teams", "picks", "hard"),
        ("both_teams", "picks_and_bans", "custom"),
    ],
)
def test_issue9_all_defined_fearless_combinations_are_accepted(tmp_path, reach, sources, label):
    # ADR-0011: all combinations except BS-028's undefined one are accepted.
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        response = client.post(
            "/api/series",
            json={
                "profile_id": "league-of-legends",
                "team_a": "A",
                "team_b": "B",
                "fearless": {"lock_reach": reach, "lock_sources": sources},
            },
        )
        assert response.status_code == 201, response.text
        assert response.json()["rule_snapshot"]["fearless"] == {
            "id": label,
            "lock_reach": reach,
            "lock_sources": sources,
        }


def test_bs009_skip_and_override_persist_with_reason(tmp_path):
    # Parent BS-009 / US-003: skipped ban, rejected duplicate, acknowledged Override.
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        series = client.post(
            "/api/series", json={"profile_id": "league-of-legends", "team_a": "A", "team_b": "B"}
        ).json()
        base = f"/api/series/{series['id']}"
        game = client.post(
            base + "/games", json={"team_a_side": "blue", "first_pick_team": "A"}
        ).json()["games"][0]
        path = f"{base}/games/{game['id']}/actions"
        response = client.post(path, json={"character_id": None})
        assert response.status_code == 201, response.text
        assert client.post(path, json={"character_id": "Ahri"}).status_code == 201
        assert (
            client.post(path, json={"character_id": "Ahri"}).json()["detail"]["code"]
            == "duplicate_character"
        )
        response = client.post(
            path,
            json={
                "character_id": "Ahri",
                "override": {"category": "official_ruling", "note": "Referee"},
            },
        )
        assert response.status_code == 201, response.text
        state = response.json()["games"][0]["state"]
        assert state["violations"] == [
            {
                "turn_index": 2,
                "rule": "duplicate_character",
                "status": "acknowledged",
                "reason": {"category": "official_ruling", "note": "Referee"},
            }
        ]
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        assert client.get(base).json()["games"][0]["state"] == state


@pytest.mark.parametrize("mode", ["allow", "warn", "reject"])
def test_bs009_api_rules_skipped_completion_and_fearless_override(tmp_path, mode):
    import shutil

    import yaml

    from nimbus.profiles import DEFAULT_PROFILE_DIR

    directory = tmp_path / "profiles"
    shutil.copytree(DEFAULT_PROFILE_DIR, directory)
    path = directory / "league-of-legends.rules.yaml"
    rules = yaml.safe_load(path.read_text())
    rules["rule_settings"]["banning_locked"] = mode
    path.write_text(yaml.safe_dump(rules))
    with CurrentClient(create_app(data_dir=tmp_path / "data", profile_dir=directory)) as client:
        series = client.post(
            "/api/series", json={"profile_id": "league-of-legends", "team_a": "A", "team_b": "B"}
        ).json()
        base = f"/api/series/{series['id']}"
        game = client.post(
            base + "/games", json={"team_a_side": "blue", "first_pick_team": "A"}
        ).json()["games"][0]
        path = f"{base}/games/{game['id']}/actions"
        catalog = [
            c["id"] for c in client.get("/api/profiles").json()[0]["catalog"] if not c["retired"]
        ]
        for index, turn in enumerate(series["rule_snapshot"]["draft_order"]["turns"]):
            entry = None if turn["kind"] == "ban" else catalog[index]
            response = client.post(path, json={"character_id": entry})
            assert response.status_code == 201, response.text
        assert response.json()["games"][0]["state"]["complete"] is True
        second = client.post(base + "/games", json={"team_a_side": "blue", "first_pick_team": "A"})
        assert second.status_code == 201
        game = second.json()["games"][1]
        path = f"{base}/games/{game['id']}/actions"
        body = {"character_id": catalog[6]}
        response = client.post(path, json=body)
        if mode == "reject":
            assert response.status_code == 409
            body["override"] = {"category": "official_ruling"}
            response = client.post(path, json=body)
        assert response.status_code == 201, response.text
        state = response.json()["games"][1]["state"]
        assert len(state["notices"]) == (1 if mode == "warn" else 0)
        assert len(state["violations"]) == (1 if mode == "reject" else 0)
        for _ in range(5):
            assert client.post(path, json={"character_id": None}).status_code == 201
        before = client.get(base).json()
        for invalid in (
            {"character_id": "unknown", "override": {"category": "official_ruling"}},
            {"character_id": None, "override": {"category": "official_ruling"}},
            {"character_id": catalog[6], "override": {"category": "other", "note": "  "}},
            {"character_id": catalog[6], "override": {"category": "not-a-category"}},
            {
                "character_id": catalog[6],
                "kind": "ban",
                "override": {"category": "official_ruling"},
            },
        ):
            assert client.post(path, json=invalid).status_code in (409, 422)
            assert client.get(base).json() == before
        rejected = client.post(path, json={"character_id": catalog[6]})
        assert rejected.status_code == 409
        assert rejected.json()["detail"]["code"] == "fearless_lock"
        response = client.post(
            path, json={"character_id": catalog[6], "override": {"category": "earlier_entry_wrong"}}
        )
        assert response.status_code == 201
        violation = response.json()["games"][1]["state"]["violations"][-1]
        assert violation["status"] == "acknowledged"
        assert violation["reason"] == {"category": "earlier_entry_wrong", "note": None}


def test_issue10_schema3_migration_preserves_facts_and_backup(tmp_path):
    import json
    import sqlite3
    from pathlib import Path

    from nimbus.profiles import load_profiles

    migrations = Path(__file__).parents[1] / "src/nimbus/migrations"
    with sqlite3.connect(tmp_path / "nimbus.sqlite3") as old:
        for name in ("001_initial.sql", "002_workspace_version.sql", "003_series_settings.sql"):
            old.executescript((migrations / name).read_text())
        old.execute(
            "INSERT INTO series VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                "legacy",
                "league-of-legends",
                json.dumps([{"id": "A", "name": "A"}, {"id": "B", "name": "B"}]),
                None,
                load_profiles()["league-of-legends"].snapshot().model_dump_json(),
                None,
                "official",
            ),
        )
        old.execute(
            "INSERT INTO games VALUES (?, ?, ?, ?, ?)",
            (
                "game",
                "legacy",
                1,
                json.dumps(
                    [
                        {"team_id": "A", "side": "blue", "position": "first"},
                        {"team_id": "B", "side": "red", "position": "second"},
                    ]
                ),
                None,
            ),
        )
        old.execute(
            "INSERT INTO draft_actions VALUES (?, ?, ?, ?, ?)", ("game", 0, "A", "ban", "Ahri")
        )
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        game = client.get("/api/series/legacy").json()["games"][0]
        assert game["actions"] == [
            {"turn_index": 0, "team_id": "A", "kind": "ban", "character_id": "Ahri"}
        ]
        assert game["acknowledgements"] == []
        backup = client.get("/api/backups").json()[0]
        assert backup["verified"] is True
        assert (
            client.post(
                "/api/series/legacy/games/game/actions", json={"character_id": None}
            ).status_code
            == 201
        )
    with sqlite3.connect(tmp_path / "backups" / backup["name"]) as saved:
        assert saved.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        assert saved.execute("PRAGMA user_version").fetchone() == (3,)
        assert saved.execute("SELECT character_id FROM draft_actions").fetchall() == [("Ahri",)]
