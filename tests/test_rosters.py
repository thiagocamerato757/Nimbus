"""US-011 / DS-002 through the agreed HTTP seam (no BS IDs for #12)."""

from test_api import CurrentClient

from nimbus.api import create_app


def series(client, **extra):
    response = client.post(
        "/api/series",
        json={
            "profile_id": "league-of-legends",
            "team_a": "Our Team",
            "team_b": "Visitors",
            "our_team": "A",
            **extra,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def player(client, team, name="Alex", role=None):
    response = client.post(
        "/api/players",
        json={
            "name": name,
            "current_team_id": team,
            "usual_role": role,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_same_named_players_are_distinct_and_current_roster_survives_restart(tmp_path):
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        created = series(client)
        team_a, team_b = [t["roster_id"] for t in created["teams"]]
        first = player(client, team_a, role="mid")
        second = player(client, team_b)
        assert first["id"] != second["id"]
        assert first["name"] == second["name"] == "Alex"
        response = client.post(
            f"/api/players/{first['id']}",
            json={
                "name": "Alex",
                "usual_role": "support",
                "current_team_id": team_b,
            },
        )
        assert response.status_code == 200, response.text
        assert response.json()["current_team_id"] == team_b
        assert (
            client.post(
                f"/api/players/{first['id']}",
                json={
                    "name": "Alex",
                    "current_team_id": "missing",
                },
            ).status_code
            == 404
        )
        reused = series(client, team_a_id=team_a, team_b_id=team_b)
        assert [t["roster_id"] for t in reused["teams"]] == [team_a, team_b]
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        people = {p["id"]: p for p in client.get("/api/players").json()}
        assert people[first["id"]]["current_team_id"] == team_b
        assert people[first["id"]]["usual_role"] == "support"
        assert people[second["id"]]["current_team_id"] == team_b
        assert {t["id"] for t in client.get("/api/teams").json()} == {team_a, team_b}


def test_declared_pools_are_owned_by_our_team_and_persist_per_title(tmp_path):
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        created = series(client)
        ours, theirs = [t["roster_id"] for t in created["teams"]]
        person, opponent = player(client, ours), player(client, theirs)
        path = f"/api/series/{created['id']}/teams/A/players/{person['id']}/pool"
        response = client.post(path, json={"character_ids": ["Ahri", "Orianna"]})
        assert response.status_code == 200, response.text
        assert response.json()["declared_pools"]["league-of-legends"] == ["Ahri", "Orianna"]
        rejected = client.post(path, json={"character_ids": ["missing"]})
        assert rejected.status_code == 422
        assert (
            client.post(
                f"/api/series/{created['id']}/teams/B/players/{opponent['id']}/pool",
                json={"character_ids": ["Ahri"]},
            ).status_code
            == 409
        )
        assert client.post(path, json={"character_ids": ["Orianna"]}).status_code == 200
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        people = {p["id"]: p for p in client.get("/api/players").json()}
        assert people[person["id"]]["declared_pools"] == {"league-of-legends": ["Orianna"]}
        assert people[opponent["id"]]["declared_pools"] == {}


def start(client, created):
    response = client.post(
        f"/api/series/{created['id']}/games",
        json={
            "team_a_side": "blue",
            "first_pick_team": "A",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["games"][-1]


def complete_draft(client, created, game):
    catalog = next(
        p for p in client.get("/api/profiles").json() if p["id"] == created["profile_id"]
    )["catalog"]
    choices = [c["id"] for c in catalog if not c["retired"]]
    for i, turn in enumerate(created["rule_snapshot"]["draft_order"]["turns"]):
        response = client.post(
            f"/api/series/{created['id']}/games/{game['id']}/actions",
            json={"character_id": choices[i] if turn["kind"] == "pick" else None},
        )
        assert response.status_code == 201, response.text
    return response.json()["games"][-1]


def test_each_game_lineup_is_independent_prefilled_and_can_be_incomplete(tmp_path):
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        created = series(client)
        ours, theirs = [t["roster_id"] for t in created["teams"]]
        first, substitute, opponent = (
            player(client, ours),
            player(client, ours),
            player(client, theirs),
        )
        game = start(client, created)
        path = f"/api/series/{created['id']}/games/{game['id']}/lineups"
        response = client.post(path, json={"team_id": "A", "player_ids": [first["id"]]})
        assert response.status_code == 200, response.text
        assert response.json()["games"][0]["lineups"] == {"A": [first["id"]], "B": []}
        assert (
            client.post(path, json={"team_id": "A", "player_ids": [opponent["id"]]}).status_code
            == 409
        )
        assert (
            client.post(
                path, json={"team_id": "A", "player_ids": [first["id"], first["id"]]}
            ).status_code
            == 422
        )
        complete_draft(client, created, game)
        second = start(client, created)  # no Player Assignments needed to continue drafting
        assert second["lineups"] == {"A": [first["id"]], "B": []}
        response = client.post(
            f"/api/series/{created['id']}/games/{second['id']}/lineups",
            json={"team_id": "A", "player_ids": [substitute["id"]]},
        )
        assert response.status_code == 200, response.text
        assert response.json()["games"][0]["lineups"]["A"] == [first["id"]]
        assert response.json()["games"][1]["lineups"]["A"] == [substitute["id"]]
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        games = client.get(f"/api/series/{created['id']}").json()["games"]
        assert games[0]["lineups"]["A"] == [first["id"]]
        assert games[1]["lineups"]["A"] == [substitute["id"]]


def test_assign_only_lineup_players_once_and_roster_removal_preserves_history(tmp_path):
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        created = series(client)
        ours, theirs = [t["roster_id"] for t in created["teams"]]
        first, second, bench = [player(client, ours) for _ in range(3)]
        opponent = player(client, theirs)
        game = start(client, created)
        base = f"/api/series/{created['id']}/games/{game['id']}"
        assert (
            client.post(
                base + "/lineups", json={"team_id": "A", "player_ids": [first["id"], second["id"]]}
            ).status_code
            == 200
        )
        assert (
            client.post(
                base + "/lineups", json={"team_id": "B", "player_ids": [opponent["id"]]}
            ).status_code
            == 200
        )
        game = complete_draft(client, created, game)
        picks = [
            a["turn_index"] for a in game["actions"] if a["kind"] == "pick" and a["team_id"] == "A"
        ]
        path = base + "/player-assignments"
        response = client.post(path, json={"turn_index": picks[0], "player_id": first["id"]})
        assert response.status_code == 200, response.text
        expected = [{"turn_index": picks[0], "player_id": first["id"]}]
        assert response.json()["games"][0]["player_assignments"] == expected
        for turn, who in [
            (picks[1], first),
            (picks[1], bench),
            (picks[1], opponent),
            (0, second),
            (99, second),
        ]:
            assert (
                client.post(path, json={"turn_index": turn, "player_id": who["id"]}).status_code
                == 409
            )
        assert (
            client.post(
                base + "/lineups", json={"team_id": "A", "player_ids": [second["id"]]}
            ).status_code
            == 409
        )
        removed = client.post(
            f"/api/players/{first['id']}", json={"name": "Alex", "current_team_id": None}
        )
        assert removed.status_code == 200
        assert (
            client.get(f"/api/series/{created['id']}").json()["games"][0]["player_assignments"]
            == expected
        )
        response = client.post(path, json={"turn_index": picks[0], "player_id": second["id"]})
        assert response.status_code == 200
        assert response.json()["games"][0]["player_assignments"] == [
            {"turn_index": picks[0], "player_id": second["id"]}
        ]
        assert (
            client.post(path, json={"turn_index": picks[0], "player_id": None}).status_code == 200
        )
        assert (
            client.post(path, json={"turn_index": picks[0], "player_id": first["id"]}).status_code
            == 200
        )
        # Current Roster membership never rewrites the previous Game's Lineup.
        next_game = start(client, created)
        assert next_game["lineups"]["A"] == [first["id"], second["id"]]
        assert next_game["player_assignments"] == []
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        stored = client.get(f"/api/series/{created['id']}").json()["games"][0]
        assert stored["player_assignments"] == expected
        assert first["id"] in stored["lineups"]["A"]
        assert (
            next(p for p in client.get("/api/players").json() if p["id"] == first["id"])[
                "current_team_id"
            ]
            is None
        )


def test_synthetic_six_player_lineups_and_pick_corrections_keep_assignments_coherent(tmp_path):
    from pathlib import Path

    with CurrentClient(
        create_app(data_dir=tmp_path, profile_dir=Path("tests/fixtures/profiles"))
    ) as client:
        created = series(client, profile_id="synthetic-deadlock")
        team_id = created["teams"][0]["roster_id"]
        members = [player(client, team_id, name=f"Player {i}") for i in range(7)]
        # This profile uses amber/sapphire Sides, keeping Lineups independent of Side Assignment.
        response = client.post(
            f"/api/series/{created['id']}/games",
            json={
                "team_a_side": "amber",
                "first_pick_team": "A",
            },
        )
        assert response.status_code == 201, response.text
        game = response.json()["games"][0]
        base = f"/api/series/{created['id']}/games/{game['id']}"
        assert (
            client.post(
                base + "/lineups", json={"team_id": "A", "player_ids": [p["id"] for p in members]}
            ).status_code
            == 422
        )
        response = client.post(
            base + "/lineups", json={"team_id": "A", "player_ids": [p["id"] for p in members[:6]]}
        )
        assert response.status_code == 200, response.text
        game = complete_draft(client, created, game)
        pick = next(a for a in reversed(game["actions"]) if a["kind"] == "pick")
        # The final pick belongs to Team B: set that Team's own Player and Lineup.
        other_team = created["teams"][1]["roster_id"]
        person = player(client, other_team, name="Opponent")
        assert pick["team_id"] == "B"
        assert (
            client.post(
                base + "/lineups", json={"team_id": "B", "player_ids": [person["id"]]}
            ).status_code
            == 200
        )
        expected = [{"turn_index": pick["turn_index"], "player_id": person["id"]}]
        assert client.post(base + "/player-assignments", json=expected[0]).status_code == 200
        catalog = client.get("/api/profiles").json()[0]["catalog"]
        replacement = next(c["id"] for c in catalog if c["id"] != pick["character_id"])
        response = client.post(
            base + f"/actions/{pick['turn_index']}/correct", json={"character_id": replacement}
        )
        assert response.status_code == 200, response.text
        assert response.json()["games"][0]["player_assignments"] == expected
        response = client.post(base + f"/actions/{pick['turn_index']}/clear", json={})
        assert response.status_code == 200, response.text
        assert response.json()["games"][0]["player_assignments"] == []


def test_declared_pool_characters_cannot_disappear_when_profiles_reload(tmp_path):
    import shutil

    import yaml

    from nimbus.profiles import DEFAULT_PROFILE_DIR

    profiles = tmp_path / "profiles"
    shutil.copytree(DEFAULT_PROFILE_DIR, profiles)
    data = tmp_path / "data"
    with CurrentClient(create_app(data_dir=data, profile_dir=profiles)) as client:
        created = series(client)
        person = player(client, created["teams"][0]["roster_id"])
        response = client.post(
            f"/api/series/{created['id']}/teams/A/players/{person['id']}/pool",
            json={"character_ids": ["Orianna"]},
        )
        assert response.status_code == 200
    catalog_file = profiles / "league-of-legends.catalog.yaml"
    catalog = yaml.safe_load(catalog_file.read_text())
    catalog["characters"] = [c for c in catalog["characters"] if c["id"] != "Orianna"]
    catalog_file.write_text(yaml.safe_dump(catalog))
    with CurrentClient(create_app(data_dir=data, profile_dir=profiles)) as client:
        response = client.get("/api/profiles")
        assert response.status_code == 500, response.text
        assert response.json()["detail"]["code"] == "profile_load_failed"
        assert "Orianna" in response.json()["detail"]["message"]
