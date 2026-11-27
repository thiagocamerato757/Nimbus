"""#13 lifecycle: BS-011 / US-004, US-008, US-009 at the HTTP seam."""

from test_api import CurrentClient
from test_rosters import complete_draft, player, series, start

from nimbus.api import create_app


# Parent: BS-011: Given Drafting, starting another Game is rejected; Given
# Drafted without result/assignments, starting succeeds and result stays pending.
def test_bs011_next_game_requires_only_complete_draft_and_status_is_derived(tmp_path):
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        created = series(client)
        base = f"/api/series/{created['id']}"
        game = start(client, created)
        assert game["state"]["status"] == "Drafting"
        assert (
            client.post(
                base + "/games", json={"team_a_side": "blue", "first_pick_team": "A"}
            ).status_code
            == 409
        )
        game = complete_draft(client, created, game)
        assert game["state"]["status"] == "Drafted"
        assert game["state"]["result_pending"] is True
        second = start(client, created)
        assert second["number"] == 2
        path = base + f"/games/{game['id']}"
        response = client.post(path + "/winner", json={"winner": "A"})
        assert response.status_code == 200, response.text
        assert response.json()["games"][0]["state"]["status"] == "Drafted"
        for team in created["teams"]:
            picks = [
                a for a in game["actions"] if a["kind"] == "pick" and a["team_id"] == team["id"]
            ]
            members = [
                player(client, team["roster_id"], name=f"Player {i}") for i in range(len(picks))
            ]
            assert (
                client.post(
                    path + "/lineups",
                    json={"team_id": team["id"], "player_ids": [p["id"] for p in members]},
                ).status_code
                == 200
            )
            for pick, person in zip(picks, members, strict=True):
                response = client.post(
                    path + "/player-assignments",
                    json={"turn_index": pick["turn_index"], "player_id": person["id"]},
                )
                assert response.status_code == 200
        assert response.json()["games"][0]["state"]["status"] == "Closed"
        response = client.post(path + "/winner", json={"winner": None})
        assert response.status_code == 200
        assert response.json()["games"][0]["state"]["status"] == "Drafted"
        assert response.json()["games"][0]["state"]["missing"] == ["winner"]
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        stored = client.get(base).json()["games"][0]
        assert stored["winner"] is None
        assert stored["state"]["result_pending"] is True
        assert stored["state"]["missing"] == ["winner"]


# Parent: BS-011: Given a drafted Game, voiding it removes later Fearless Locks;
# Given an abandoned draft, voiding permits the next draft without a result.
def test_bs011_voided_games_do_not_lock_or_block_next_draft_and_persist(tmp_path):
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        created = series(client, series_format={"kind": "fixed_length", "games": 4})
        base = f"/api/series/{created['id']}"
        game = complete_draft(client, created, start(client, created))
        second = start(client, created)
        response = client.post(base + f"/games/{game['id']}/void", json={})
        assert response.status_code == 200, response.text
        games = response.json()["games"]
        assert games[0]["state"]["status"] == "Voided"
        assert games[1]["state"]["locks"] == {"A": [], "B": []}
        response = client.post(base + f"/games/{second['id']}/void", json={})
        assert response.status_code == 200
        assert response.json()["games"][1]["state"]["next_turn"] is None
        assert (
            client.post(
                base + f"/games/{second['id']}/actions", json={"character_id": None}
            ).status_code
            == 409
        )
        third = start(client, created)
        assert third["number"] == 3
        assert third["state"]["status"] == "Drafting"
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        games = client.get(base).json()["games"]
        assert [g["state"]["status"] for g in games] == ["Voided", "Voided", "Drafting"]


# Parent: #13 acceptance: correcting a winner can move the deciding Game;
# existing Games remain and are warned about, while pending results defer ending.
def test_best_of_score_pending_results_and_correction_warning(tmp_path):
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        created = series(
            client,
            series_format={"kind": "best_of", "games": 3},
            fearless={"lock_reach": "none", "lock_sources": "picks"},
        )
        base = f"/api/series/{created['id']}"
        games = [complete_draft(client, created, start(client, created)) for _ in range(3)]
        assert client.get(base).json()["progress"]["ended"] is False
        for game, winner in zip(games, ("A", "B", "A"), strict=True):
            response = client.post(base + f"/games/{game['id']}/winner", json={"winner": winner})
            assert response.status_code == 200
        assert response.json()["progress"]["score"] == {"A": 2, "B": 1}
        assert response.json()["progress"]["ended"] is True
        response = client.post(base + f"/games/{games[1]['id']}/winner", json={"winner": "A"})
        assert [g["id"] for g in response.json()["games"]] == [g["id"] for g in games]
        assert response.json()["progress"]["deciding_game"] == 2
        assert response.json()["progress"]["games_past_decision"] == [3]
        response = client.post(base + f"/games/{games[0]['id']}/winner", json={"winner": None})
        assert response.json()["progress"]["pending_results"] == [1]
        assert response.json()["progress"]["ended"] is False


# Parent: #13 acceptance: a Best-of majority ends the Series before the maximum;
# voiding a deciding Game removes its result and permits play to continue.
def test_majority_stops_starting_and_voiding_decision_reopens_series(tmp_path):
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        created = series(
            client,
            series_format={"kind": "best_of", "games": 3},
            fearless={"lock_reach": "none", "lock_sources": "picks"},
        )
        base = f"/api/series/{created['id']}"
        for _ in range(2):
            game = complete_draft(client, created, start(client, created))
            response = client.post(base + f"/games/{game['id']}/winner", json={"winner": "A"})
            assert response.status_code == 200
        assert response.json()["progress"]["ended"] is True
        assert response.json()["progress"]["can_start_next"] is False
        response = client.post(
            base + "/games", json={"team_a_side": "blue", "first_pick_team": "A"}
        )
        assert response.status_code == 409
        assert response.json()["detail"]["code"] == "series_ended"
        response = client.post(base + f"/games/{game['id']}/void", json={})
        assert response.json()["progress"]["score"] == {"A": 1, "B": 0}
        assert start(client, created)["number"] == 3


# Parent: #13 acceptance: Fixed-length ends after the set number of non-voided
# Games, irrespective of the score or missing winners.
def test_fixed_length_plays_set_count_excluding_voided_games(tmp_path):
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        created = series(
            client,
            series_format={"kind": "fixed_length", "games": 4},
            fearless={"lock_reach": "none", "lock_sources": "picks"},
        )
        base = f"/api/series/{created['id']}"
        first = start(client, created)
        assert client.post(base + f"/games/{first['id']}/void", json={}).status_code == 200
        for _ in range(4):
            complete_draft(client, created, start(client, created))
        saved = client.get(base).json()
        assert len(saved["games"]) == 5
        assert saved["progress"]["ended"] is True
        assert saved["progress"]["score"] == {"A": 0, "B": 0}
        assert saved["progress"]["can_start_next"] is False
        assert (
            client.post(
                base + "/games", json={"team_a_side": "blue", "first_pick_team": "A"}
            ).status_code
            == 409
        )
