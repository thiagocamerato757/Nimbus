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


def fill(client, created, game, picks):
    """Enter every remaining turn: skipped bans and the given picks in order."""
    for turn in created["rule_snapshot"]["draft_order"]["turns"][len(game["actions"]) :]:
        response = client.post(
            f"/api/series/{created['id']}/games/{game['id']}/actions",
            json={"character_id": next(picks) if turn["kind"] == "pick" else None},
        )
        assert response.status_code == 201, response.text
    return response.json()["games"][-1]


# Parent: BS-011 "A Voided Game creates no Fearless Locks by default": Given a
# Game with recorded picks under the default setting, When it is voided, Then its
# picks lock nothing in later Games, while its Replay's picks do lock Game 2.
# ADR-0034 (amended 2026-11-27): only the current Game is voided; its Replay follows.
def test_bs011_voided_games_do_not_lock_or_block_next_draft_and_persist(tmp_path):
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        created = series(client, series_format={"kind": "fixed_length", "games": 4})
        assert created["rule_snapshot"]["rule_settings"]["voided_games_count"] is False
        base = f"/api/series/{created['id']}"
        catalog = [c["id"] for c in client.get("/api/profiles").json()[0]["catalog"]]
        voided_picks, replay_picks = catalog[:10], catalog[10:20]
        game = fill(client, created, start(client, created), iter(voided_picks))
        response = client.post(base + f"/games/{game['id']}/void", json={})
        assert response.status_code == 200, response.text
        assert response.json()["games"][0]["state"]["status"] == "Voided"
        response = client.post(
            base + f"/games/{game['id']}/replay", json={"draft_choice": "new_draft"}
        )
        assert response.status_code == 201, response.text
        replay = response.json()["games"][-1]
        assert replay["state"]["locks"] == {"A": [], "B": []}
        fill(client, created, replay, iter(replay_picks))
        later = start(client, created)
        assert later["number"] == 2
        for team in ("A", "B"):
            assert later["state"]["locks"][team] == sorted(replay_picks)
            assert not set(voided_picks) & set(later["state"]["locks"][team])
        response = client.post(base + f"/games/{later['id']}/void", json={})
        assert response.json()["games"][-1]["state"]["next_turn"] is None
        response = client.post(base + f"/games/{later['id']}/actions", json={"character_id": None})
        assert response.status_code == 409
        assert response.json()["detail"]["code"] == "game_voided"
        saved = client.get(base).json()
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        games = client.get(base).json()["games"]
        assert games == saved["games"]
        assert [g["state"]["status"] for g in games] == ["Voided", "Drafted", "Voided"]


# Parent ADR-0034 (amended 2026-11-27): voiding an earlier Game while a later
# one exists is rejected and changes nothing; the current Game can be voided.
def test_only_the_current_game_can_be_voided(tmp_path):
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        created = series(client)
        base = f"/api/series/{created['id']}"
        first = complete_draft(client, created, start(client, created))
        second = start(client, created)
        before = client.get(base)
        response = client.post(base + f"/games/{first['id']}/void", json={})
        assert response.status_code == 409, response.text
        assert response.json()["detail"] == {
            "code": "void_not_current",
            "message": "Only the current Game can be voided; correct earlier Games by replacement.",
        }
        after = client.get(base)
        assert after.json() == before.json()
        assert after.headers["x-nimbus-version"] == before.headers["x-nimbus-version"]
        response = client.post(base + f"/games/{second['id']}/void", json={})
        assert response.status_code == 200, response.text
        assert [g["voided"] for g in response.json()["games"]] == [False, True]


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
        response = client.post(
            base + f"/games/{game['id']}/replay", json={"draft_choice": "new_draft"}
        )
        assert response.status_code == 201, response.text
        assert response.json()["games"][-1]["number"] == 2


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
        response = client.post(
            base + f"/games/{first['id']}/replay", json={"draft_choice": "new_draft"}
        )
        assert response.status_code == 201, response.text
        complete_draft(client, created, response.json()["games"][-1])
        for _ in range(3):
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


# Parent #13 decision (Q11, 2026-11-27): a winner is set only for a Drafted or
# Closed Game; Drafting and Voided Games reject it and change nothing. Clearing a
# winner is allowed in any status.
def test_winner_is_accepted_only_for_drafted_or_closed_games(tmp_path):
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        created = series(
            client,
            series_format={"kind": "best_of", "games": 3},
            fearless={"lock_reach": "none", "lock_sources": "picks"},
        )
        base = f"/api/series/{created['id']}"
        first = complete_draft(client, created, start(client, created))
        assert client.post(base + f"/games/{first['id']}/winner", json={"winner": "A"}).is_success
        second = start(client, created)
        client.post(base + f"/games/{second['id']}/actions", json={"character_id": None})
        before = client.get(base)
        response = client.post(base + f"/games/{second['id']}/winner", json={"winner": "A"})
        assert response.status_code == 409, response.text
        assert response.json()["detail"]["code"] == "winner_not_allowed"
        assert client.get(base).json() == before.json()
        assert before.json()["progress"]["ended"] is False
        response = client.post(base + f"/games/{second['id']}/winner", json={"winner": None})
        assert response.status_code == 200, response.text
        client.post(base + f"/games/{second['id']}/void", json={})
        response = client.post(base + f"/games/{second['id']}/winner", json={"winner": "A"})
        assert response.status_code == 409
        assert response.json()["detail"]["code"] == "winner_not_allowed"
        response = client.post(base + f"/games/{second['id']}/winner", json={"winner": None})
        assert response.status_code == 200, response.text


# Parent #13 acceptance "not declared over while results are pending": clearing
# the last action of a Drafted Game that has a winner returns it to Drafting,
# and its stored winner stops counting until the draft is complete again.
def test_winner_on_a_game_returned_to_drafting_does_not_count(tmp_path):
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
        assert response.json()["progress"]["ended"] is True
        last = game["actions"][-1]["turn_index"]
        response = client.post(base + f"/games/{game['id']}/actions/{last}/clear", json={})
        assert response.status_code == 200, response.text
        progress = response.json()["progress"]
        assert progress["score"] == {"A": 1, "B": 0}
        assert progress["ended"] is False and progress["deciding_game"] is None
        # The stored winner of a Game back in Drafting can still be removed.
        path = base + f"/games/{game['id']}/winner"
        assert response.json()["games"][-1]["winner"] == "A"
        response = client.post(path, json={"winner": None})
        assert response.status_code == 200, response.text
        assert response.json()["games"][-1]["winner"] is None
        assert response.json()["games"][-1]["state"]["status"] == "Drafting"
        assert client.post(path, json={"winner": "A"}).status_code == 409


# Parent ADR-0034 (amended 2026-11-27): after a Voided Game the next Game is
# always its Replay, so a Bo3 goes 1, 2 (voided), 2, 3; the maximum counts
# non-voided Games only.
def test_after_a_void_the_next_game_is_its_replay(tmp_path):
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        created = series(
            client,
            series_format={"kind": "best_of", "games": 3},
            fearless={"lock_reach": "none", "lock_sources": "picks"},
        )
        base = f"/api/series/{created['id']}"
        first = complete_draft(client, created, start(client, created))
        client.post(base + f"/games/{first['id']}/winner", json={"winner": "A"})
        second = complete_draft(client, created, start(client, created))
        saved = client.post(base + f"/games/{second['id']}/void", json={}).json()
        assert saved["progress"]["can_start_next"] is False
        before = client.get(base)
        response = client.post(
            base + "/games", json={"team_a_side": "blue", "first_pick_team": "A"}
        )
        assert response.status_code == 409, response.text
        assert response.json()["detail"]["code"] == "replay_required"
        assert client.get(base).json() == before.json()
        response = client.post(
            base + f"/games/{second['id']}/replay", json={"draft_choice": "new_draft"}
        )
        assert response.status_code == 201, response.text
        replay = complete_draft(client, created, response.json()["games"][-1])
        saved = client.post(base + f"/games/{replay['id']}/winner", json={"winner": "B"}).json()
        assert saved["progress"]["can_start_next"] is True
        third = complete_draft(client, created, start(client, created))
        saved = client.post(base + f"/games/{third['id']}/winner", json={"winner": "A"}).json()
        assert [g["number"] for g in saved["games"]] == [1, 2, 2, 3]
        assert [g["voided"] for g in saved["games"]] == [False, True, False, False]
        assert saved["progress"]["ended"] is True
        assert saved["progress"]["score"] == {"A": 2, "B": 1}


# Parent ADR-0034 (amended 2026-11-27): a Replay is how the next Game starts
# after a void, so it follows the same gate as an ordinary next Game. Given a
# decided Bo3, replaying a voided Game past the decision is rejected with
# series_ended; a winner correction that un-decides the Series makes it available.
def test_replay_follows_the_series_ended_gate_in_both_directions(tmp_path):
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        created = series(
            client,
            series_format={"kind": "best_of", "games": 3},
            fearless={"lock_reach": "none", "lock_sources": "picks"},
        )
        base = f"/api/series/{created['id']}"
        first = complete_draft(client, created, start(client, created))
        client.post(base + f"/games/{first['id']}/winner", json={"winner": "A"})
        second = complete_draft(client, created, start(client, created))
        third = start(client, created)
        decided = client.post(base + f"/games/{second['id']}/winner", json={"winner": "A"})
        assert decided.json()["progress"]["ended"] is True
        assert decided.json()["progress"]["games_past_decision"] == [3]
        client.post(base + f"/games/{third['id']}/void", json={})
        before = client.get(base)
        for endpoint in ("/replay-preview", "/replay"):
            response = client.post(
                base + f"/games/{third['id']}{endpoint}", json={"draft_choice": "new_draft"}
            )
            assert response.status_code == 409, response.text
            assert response.json()["detail"]["code"] == "series_ended"
        assert client.get(base).json() == before.json()
        undecided = client.post(base + f"/games/{second['id']}/winner", json={"winner": "B"})
        assert undecided.json()["progress"]["ended"] is False
        response = client.post(
            base + f"/games/{third['id']}/replay", json={"draft_choice": "new_draft"}
        )
        assert response.status_code == 201, response.text
        assert [g["number"] for g in response.json()["games"]] == [1, 2, 3, 3]
