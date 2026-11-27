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
        for _ in series["rule_snapshot"]["draft_order"]["turns"]:
            # Duplicate entries remain deliberately accepted until issue #10.
            assert (
                client.post(
                    f"{base}/games/{game['id']}/actions", json={"character_id": "Orianna"}
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
            client.post(f"{base}/games/{second['id']}/actions", json={"character_id": "Ahri"})
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
