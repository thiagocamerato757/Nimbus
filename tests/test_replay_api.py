"""BS-011 replay HTTP persistence and migration behavior."""

import pytest
from test_api import CurrentClient
from test_rosters import series

from nimbus.api import create_app


def post(client, path, payload):
    response = client.post(path, json=payload)
    assert response.status_code in (200, 201), response.text
    return response.json()


def voided(client):
    created = series(client, patch="26.1")
    base = f"/api/series/{created['id']}"
    saved = post(client, base + "/games", {"team_a_side": "blue", "first_pick_team": "A"})
    game = saved["games"][0]
    post(client, base + f"/games/{game['id']}/actions", {"character_id": "Ahri"})
    saved = post(client, base + f"/games/{game['id']}/void", {})
    return base, saved["games"][0]


# Parent: BS-011 confirmed creation choices. Given latest Voided Game, creating
# copy/new returns linked same-number independent identity and persists restart.
@pytest.mark.parametrize("choice,actions", [("copy_draft", 1), ("new_draft", 0)])
def test_bs011_replay_choice_saves_linked_attempt_and_survives_restart(tmp_path, choice, actions):
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        base, source = voided(client)
        path = base + f"/games/{source['id']}/replay"
        before = client.get(base)
        assert client.post(path, json={}).status_code == 422
        assert client.get(base).headers["x-nimbus-version"] == before.headers["x-nimbus-version"]
        saved = post(client, path, {"draft_choice": choice})
        replay = saved["games"][-1]
        assert replay["id"] != source["id"] and replay["replay_of"] == source["id"]
        assert [g["number"] for g in saved["games"]] == [1, 1]
        assert saved["games"][0] == source
        assert len(replay["actions"]) == actions
        assert replay["patch"] == "26.1" and replay["assignments"] == source["assignments"]
        assert replay["winner"] is None and replay["player_assignments"] == []
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        assert client.get(base).json() == saved


# Parent: BS-011 setup/copy preview shows violations without committing a Game;
# structural metadata mismatch rejects the complete request without silent drops.
def test_bs011_preview_prefill_violation_scope_and_structural_rejection(tmp_path):
    from test_rosters import player

    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        created = series(client, patch="26.1")
        person = player(client, created["teams"][0]["roster_id"])
        base = f"/api/series/{created['id']}"
        source = post(client, base + "/games", {"team_a_side": "blue", "first_pick_team": "A"})[
            "games"
        ][0]
        path = base + f"/games/{source['id']}"
        post(client, path + "/lineups", {"team_id": "A", "player_ids": [person["id"]]})
        post(client, path + "/actions", {"character_id": "Ahri"})
        post(
            client,
            path + "/actions",
            {
                "character_id": "Ahri",
                "override": {"category": "official_ruling", "note": "R" * 2000},
            },
        )
        post(client, path + "/actions", {"character_id": "Akali"})
        post(client, path + "/actions/2/correct", {"character_id": "Ahri"})
        post(client, path + "/void", {})
        before = client.get(base)
        preview = post(client, path + "/replay-preview", {"draft_choice": "copy_draft"})
        assert client.get(base).json() == before.json()
        assert client.get(base).headers["x-nimbus-version"] == before.headers["x-nimbus-version"]
        assert [(v["turn_index"], v["status"]) for v in preview["state"]["violations"]] == [
            (1, "acknowledged"),
            (2, "open"),
        ]
        inherited = preview["state"]["violations"][0]
        assert inherited["reason"]["note"] == "R" * 2000
        assert inherited["carried_from"][0]["game_id"] == source["id"]
        assert preview["lineups"]["A"] == [person["id"]]
        response = client.post(
            path + "/replay", json={"draft_choice": "copy_draft", "first_pick_team": "B"}
        )
        assert response.status_code == 409
        assert response.json()["detail"]["code"] == "copy_requires_same_draft_positions"
        assert client.get(base).json() == before.json()
        saved = post(
            client,
            path + "/replay",
            {
                "draft_choice": "copy_draft",
                "patch": "26.2",
                "team_a_side": "red",
                "lineups": {"A": [], "B": []},
            },
        )
        replay = saved["games"][-1]
        assert replay["patch"] == "26.2" and replay["assignments"][0]["side"] == "red"
        assert replay["lineups"] == {"A": [], "B": []}
        assert replay["winner"] is None and replay["player_assignments"] == []
        assert replay["state"]["violations"][0]["carried_from"] == inherited["carried_from"]


# Parent: BS-011 chains and eligibility. Replay only latest voided attempt;
# stale simultaneous writes cannot create two attempts, next Game advances once.
def test_bs011_chain_latest_guard_and_stale_write_are_atomic(tmp_path):
    from fastapi.testclient import TestClient

    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        base, source = voided(client)
        path = base + f"/games/{source['id']}/replay"
        stale = client.get(base).headers["x-nimbus-version"]
        first = post(client, path, {"draft_choice": "copy_draft"})["games"][-1]
        rejected = TestClient.post(
            client, path, json={"draft_choice": "copy_draft"}, headers={"x-nimbus-version": stale}
        )
        assert rejected.status_code == 409 and rejected.json()["detail"]["code"] == "stale_version"
        post(client, base + f"/games/{first['id']}/void", {})
        chain = post(
            client,
            base + f"/games/{first['id']}/replay",
            {"draft_choice": "new_draft", "first_pick_team": "B"},
        )["games"][-1]
        assert chain["number"] == 1 and chain["replay_of"] == first["id"]
        assert next(a for a in chain["assignments"] if a["position"] == "first")["team_id"] == "B"
        following = post(client, base + f"/games/{chain['id']}/void", {})
        # ADR-0034 (amended 2026-11-27): after a void, the next Game is its Replay.
        rejected = client.post(
            base + "/games", json={"team_a_side": "blue", "first_pick_team": "A"}
        )
        assert rejected.status_code == 409
        assert rejected.json()["detail"]["code"] == "replay_required"
        rejected = client.post(
            base + f"/games/{first['id']}/replay", json={"draft_choice": "new_draft"}
        )
        assert (
            rejected.status_code == 409
            and rejected.json()["detail"]["code"] == "replay_unavailable"
        )
        assert [g["number"] for g in following["games"]] == [1, 1, 1]
        assert client.get(base).json() == following


# Parent: BS-011 / ADR-0032 existing attempts, history and rulings survive real
# schema-7 migration, verified backup restoration and older additive restores.
@pytest.mark.parametrize("old_version", [1, 4, 5, 6, 7])
def test_bs011_migration_and_verified_restore_preserve_records(tmp_path, old_version):
    import shutil
    import sqlite3
    from pathlib import Path

    data = tmp_path / "data"
    # Fixture is an actual schema 7 with children; no internal state is asserted.
    data.mkdir()
    with sqlite3.connect(data / "nimbus.sqlite3") as db:
        for migration in sorted(Path("src/nimbus/migrations").glob("*.sql"))[:7]:
            db.executescript(migration.read_text())
    with CurrentClient(create_app(data_dir=data)) as client:
        from test_rosters import player

        created = series(client)
        person = player(client, created["teams"][0]["roster_id"])
        base = f"/api/series/{created['id']}"
        source = post(client, base + "/games", {"team_a_side": "blue", "first_pick_team": "A"})[
            "games"
        ][0]
        path = base + f"/games/{source['id']}"
        post(client, path + "/lineups", {"team_id": "A", "player_ids": [person["id"]]})
        post(client, path + "/actions", {"character_id": "Ahri"})
        post(
            client,
            path + "/actions",
            {
                "character_id": "Ahri",
                "override": {
                    "category": "official_ruling",
                    "note": "Migration ruling",
                },
            },
        )
        for _ in range(4):
            post(client, path + "/actions", {"character_id": None})
        post(client, path + "/actions", {"character_id": "Azir"})
        post(client, path + "/player-assignments", {"turn_index": 6, "player_id": person["id"]})
        post(client, path + "/actions/0/correct", {"character_id": "Akali"})
        post(client, path + "/actions/0/correct", {"character_id": "Ahri"})
        post(client, path + "/void", {})
        expected = client.get(base).json()
    # Rebuild schema-7 fixture, preserving all previous columns/children.
    with sqlite3.connect(data / "nimbus.sqlite3") as db:
        db.executescript("""PRAGMA foreign_keys=OFF;
        CREATE TABLE previous_games (id TEXT PRIMARY KEY, series_id TEXT NOT NULL REFERENCES series(id),
            number INTEGER NOT NULL, assignments TEXT NOT NULL, patch TEXT,
            acknowledgements TEXT NOT NULL DEFAULT '[]', edit_history TEXT NOT NULL DEFAULT '[]',
            winner TEXT, voided INTEGER NOT NULL DEFAULT 0, UNIQUE(series_id,number));
        INSERT INTO previous_games SELECT id,series_id,number,assignments,patch,acknowledgements,edit_history,winner,voided FROM games;
        DROP TABLE games; ALTER TABLE previous_games RENAME TO games;""")
        if old_version == 1:
            db.execute("DROP TABLE workspace_version")
        db.execute(f"PRAGMA user_version = {old_version}")
    previous_backups = {p.name for p in (data / "backups").glob("*")}
    with CurrentClient(create_app(data_dir=data)) as client:
        assert client.get(base).json() == expected
        backups = [
            b for b in client.get("/api/backups").json() if b["name"] not in previous_backups
        ]
        assert len(backups) == 1 and backups[0]["verified"]
        replay = post(client, path + "/replay", {"draft_choice": "copy_draft"})
        assert replay["games"][0]["edit_history"] == expected["games"][0]["edit_history"]
        manual = post(client, "/api/backups", {})
    for name in (backups[0]["name"], manual["name"]):
        restored = tmp_path / name
        restored.mkdir()
        shutil.copyfile(data / "backups" / name, restored / "nimbus.sqlite3")
        with CurrentClient(create_app(data_dir=restored)) as client:
            assert client.get(base).json() == (expected if name == backups[0]["name"] else replay)


# Parent BS-011 counted Voided Game/Azir example at the HTTP seam.
def test_bs011_azir_locks_game_four_but_never_its_same_number_replay(tmp_path):
    import shutil
    from pathlib import Path

    profiles = tmp_path / "profiles"
    shutil.copytree(Path("profiles"), profiles)
    rules = profiles / "league-of-legends.rules.yaml"
    rules.write_text(
        rules.read_text().replace("voided_games_count: false", "voided_games_count: true")
    )
    with CurrentClient(create_app(data_dir=tmp_path / "data", profile_dir=profiles)) as client:
        created = series(client)
        base = f"/api/series/{created['id']}"
        turns = created["rule_snapshot"]["draft_order"]["turns"]
        catalog = client.get("/api/profiles").json()[0]["catalog"]
        picks = iter(c["id"] for c in catalog if not c["retired"] and c["id"] != "Azir")

        def fill(game, azir=False):
            # Bans are skipped; each pick is a Character unused in this Series.
            for turn in turns[len(game["actions"]) :]:
                if turn["kind"] == "ban":
                    choice = None
                else:
                    choice = "Azir" if azir else next(picks)
                    azir = False
                post(client, base + f"/games/{game['id']}/actions", {"character_id": choice})

        setup = {"team_a_side": "blue", "first_pick_team": "A"}
        for _ in range(2):
            fill(post(client, base + "/games", setup)["games"][-1])
        source = post(client, base + "/games", setup)["games"][-1]
        assert source["number"] == 3
        path = base + f"/games/{source['id']}"
        for _ in range(6):
            post(client, path + "/actions", {"character_id": None})
        post(client, path + "/actions", {"character_id": "Azir"})
        post(client, path + "/void", {})
        copy = post(client, path + "/replay-preview", {"draft_choice": "copy_draft"})
        assert copy["number"] == 3
        assert copy["actions"][-1]["character_id"] == "Azir"
        assert "Azir" not in copy["state"]["locks"]["A"] + copy["state"]["locks"]["B"]
        assert copy["state"]["violations"] == []
        # ADR-0034 (amended 2026-11-27): Game 4 follows a non-voided Game 3. A new
        # draft without Azir isolates the counted voided attempt as the lock's cause.
        replay = post(client, path + "/replay", {"draft_choice": "new_draft"})["games"][-1]
        fill(replay)
        fourth = post(client, base + "/games", setup)["games"][-1]
        assert fourth["number"] == 4
        assert "Azir" in fourth["state"]["locks"]["A"]
        assert "Azir" in fourth["state"]["locks"]["B"]


# Parent ADR-0034 / #13 (amended 2026-11-27): Draft Positions are editable for a
# new draft, but copying the draft requires the same Draft Positions. Preview and
# creation reject the combination with a specific code and change nothing.
def test_copying_a_draft_requires_the_same_draft_positions(tmp_path):
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        base, source = voided(client)
        path = base + f"/games/{source['id']}"
        before = client.get(base)
        changed = {"draft_choice": "copy_draft", "first_pick_team": "B"}
        for endpoint in ("/replay-preview", "/replay"):
            response = client.post(path + endpoint, json=changed)
            assert response.status_code == 409, response.text
            assert response.json()["detail"] == {
                "code": "copy_requires_same_draft_positions",
                "message": "Copying the draft requires the same Draft Positions; "
                "keep them or choose new draft.",
            }
        assert client.get(base).json() == before.json()
        assert client.get(base).headers["x-nimbus-version"] == before.headers["x-nimbus-version"]
        sides = post(
            client, path + "/replay-preview", {"draft_choice": "copy_draft", "team_a_side": "red"}
        )
        assert len(sides["actions"]) == 1
        saved = post(
            client, path + "/replay", {"draft_choice": "new_draft", "first_pick_team": "B"}
        )
        replay = saved["games"][-1]
        assert replay["actions"] == []
        assert next(a for a in replay["assignments"] if a["position"] == "first")["team_id"] == "B"
