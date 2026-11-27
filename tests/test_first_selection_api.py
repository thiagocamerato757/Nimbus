"""BS-012 recording and ordinary corrections at the HTTP persistence seam."""

from test_api import CurrentClient
from test_replay_api import post
from test_rosters import series

from nimbus.api import create_app


# Parent BS-012: optional holder/choice record what happened, never turn order.
# Given independent Side/position, recording then correcting optional metadata
# persists across restart and does not create or change Draft Actions.
def test_bs012_record_and_correct_first_selection_without_changing_actions(tmp_path):
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        base = "/api/series/" + series(client)["id"]
        saved = post(
            client,
            base + "/games",
            {
                "team_a_side": "blue",
                "first_pick_team": "B",
                "first_selection_holder": "A",
                "first_selection_choice": "side",
            },
        )
        game = saved["games"][0]
        assert game["first_selection_holder"] == "A" and game["first_selection_choice"] == "side"
        assert game["state"]["next_turn"]["team_id"] == "B" and game["actions"] == []
        path = base + "/games/" + game["id"]
        saved = post(client, path + "/actions", {"character_id": "Ahri"})
        actions = saved["games"][0]["actions"]
        saved = post(
            client,
            path + "/first-selection",
            {
                "first_selection_holder": "B",
                "first_selection_choice": "draft_position",
            },
        )
        assert saved["games"][0]["first_selection_holder"] == "B"
        assert saved["games"][0]["first_selection_choice"] == "draft_position"
        assert saved["games"][0]["actions"] == actions
        saved = post(
            client,
            path + "/first-selection",
            {
                "first_selection_holder": None,
                "first_selection_choice": None,
            },
        )
        assert saved["games"][0]["first_selection_holder"] is None
        assert saved["games"][0]["first_selection_choice"] is None
        assert saved["games"][0]["actions"] == actions
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        assert client.get(base).json() == saved


def configured_profiles(tmp_path, extra):
    import shutil
    from pathlib import Path

    profiles = tmp_path / "profiles"
    shutil.copytree(Path("profiles"), profiles)
    rules = profiles / "league-of-legends.rules.yaml"
    import yaml

    configured = yaml.safe_load(rules.read_text())
    configured.update(yaml.safe_load(extra))
    rules.write_text(yaml.safe_dump(configured, sort_keys=False))
    return profiles, rules


# Parent BS-012 pending result: with a non-none loser default, pending stays
# empty; known winner prefill is editable, including an explicit empty record.
def test_bs012_loser_prefill_pending_override_and_snapshot_survive_profile_edits(tmp_path):
    profiles, rules = configured_profiles(tmp_path, "default_first_selection_holder: loser\n")
    data = tmp_path / "data"
    with CurrentClient(create_app(data_dir=data, profile_dir=profiles)) as client:
        created = series(client)
        base = "/api/series/" + created["id"]
        saved = post(client, base + "/games", {"team_a_side": "blue", "first_pick_team": "A"})
        game = saved["games"][0]
        path = base + "/games/" + game["id"]
        catalog = client.get("/api/profiles").json()[0]["catalog"]
        for i, _ in enumerate(created["rule_snapshot"]["draft_order"]["turns"]):
            saved = post(client, path + "/actions", {"character_id": catalog[i]["id"]})
        assert saved["next_first_selection_holder"] is None
        saved = post(client, path + "/winner", {"winner": "B"})
        assert saved["next_first_selection_holder"] == "A"
    rules.write_text(
        rules.read_text().replace(
            "default_first_selection_holder: loser", "default_first_selection_holder: winner"
        )
    )
    with CurrentClient(create_app(data_dir=data, profile_dir=profiles)) as client:
        assert client.get(base).json()["next_first_selection_holder"] == "A"
        saved = post(
            client,
            base + "/games",
            {
                "team_a_side": "blue",
                "first_pick_team": "B",
                "first_selection_holder": None,
            },
        )
        assert saved["games"][-1]["first_selection_holder"] is None
        # Pending Game 2 must not use known result from Game 1.
        assert saved["next_first_selection_holder"] is None


# Parent BS-012 coupled profile respected; snapshots keep the original explicit
# coupling map after a profile edit, and rejection saves no partial Game.
def test_bs012_explicit_coupling_map_is_snapshotted_and_replay_respects_it(tmp_path):
    profiles, rules = configured_profiles(tmp_path, "first_pick_side: red\n")
    rules.write_text(rules.read_text().replace("sides_coupled: false", "sides_coupled: true"))
    data = tmp_path / "data"
    with CurrentClient(create_app(data_dir=data, profile_dir=profiles)) as client:
        base = "/api/series/" + series(client)["id"]
        before = client.get(base)
        rejected = client.post(
            base + "/games", json={"team_a_side": "blue", "first_pick_team": "A"}
        )
        assert (
            rejected.status_code == 422 and rejected.json()["detail"]["code"] == "coupled_position"
        )
        assert client.get(base).json() == before.json()
        assert client.get(base).headers["x-nimbus-version"] == before.headers["x-nimbus-version"]
        saved = post(
            client,
            base + "/games",
            {
                "team_a_side": "blue",
                "first_pick_team": "B",
                "first_selection_holder": "A",
                "first_selection_choice": "draft_position",
            },
        )
        game = saved["games"][0]
        path = base + "/games/" + game["id"]
        saved = post(client, path + "/void", {})
    rules.write_text(rules.read_text().replace("first_pick_side: red", "first_pick_side: blue"))
    with CurrentClient(create_app(data_dir=data, profile_dir=profiles)) as client:
        rejected = client.post(
            path + "/replay",
            json={
                "draft_choice": "new_draft",
                "team_a_side": "blue",
                "first_pick_team": "A",
            },
        )
        assert rejected.status_code == 422
        assert client.get(base).json() == saved
        replay = post(client, path + "/replay", {"draft_choice": "new_draft"})["games"][-1]
        assert replay["first_selection_holder"] is None and replay["first_selection_choice"] is None
        assert replay["winner"] is None and replay["player_assignments"] == []
        assert replay["state"]["next_turn"]["team_id"] == "B"
        new = series(client)
        assert new["rule_snapshot"]["first_pick_side"] == "blue"
        assert client.get(base).json()["rule_snapshot"]["first_pick_side"] == "red"


# Parent BS-012 profile default: the pre-fill is computed for display only
# (#14, amended 2026-11-27). The request's holder is recorded as sent, and an
# omitted holder records none: the server never applies an unseen pre-fill.
def test_bs012_configured_holder_is_prefilled_but_never_enforced(tmp_path):
    from test_rosters import complete_draft, start

    profiles, _ = configured_profiles(tmp_path, "default_first_selection_holder: loser\n")
    with CurrentClient(create_app(data_dir=tmp_path / "data", profile_dir=profiles)) as client:
        for extra, expected in (
            ({}, None),
            ({"first_selection_holder": "B"}, "B"),
            ({"first_selection_holder": "A"}, "A"),
            ({"first_selection_holder": None}, None),
        ):
            created = series(client)
            base = "/api/series/" + created["id"]
            game = complete_draft(client, created, start(client, created))
            shown = post(client, base + "/games/" + game["id"] + "/winner", {"winner": "A"})
            assert shown["next_first_selection_holder"] == "B"
            saved = post(
                client,
                base + "/games",
                {
                    "team_a_side": "blue",
                    "first_pick_team": "B",
                    **extra,
                },
            )
            second = saved["games"][-1]
            assert second["first_selection_holder"] == expected
            assert second["first_selection_choice"] is None
            assert second["state"]["next_turn"]["team_id"] == "B"
            assert second["actions"] == []


# Parent BS-012 / ADR-0034: Replay is a new same-number Game. Its profile
# default uses the preceding lower-number nonvoid result, never its source.
def test_bs012_replay_default_uses_previous_logical_result_not_voided_source(tmp_path):
    from test_rosters import complete_draft, start

    profiles, _ = configured_profiles(tmp_path, "default_first_selection_holder: loser\n")
    with CurrentClient(create_app(data_dir=tmp_path / "data", profile_dir=profiles)) as client:
        created = series(client, fearless={"lock_reach": "none", "lock_sources": "picks"})
        base = "/api/series/" + created["id"]
        previous = complete_draft(client, created, start(client, created))
        previous_path = base + "/games/" + previous["id"]
        post(client, previous_path + "/winner", {"winner": "A"})
        source = post(
            client,
            base + "/games",
            {
                "team_a_side": "blue",
                "first_pick_team": "A",
                "first_selection_holder": "A",
                "first_selection_choice": "side",
            },
        )["games"][-1]
        path = base + "/games/" + source["id"]
        complete_draft(client, created, source)
        post(client, path + "/winner", {"winner": "B"})
        post(client, path + "/void", {})
        preview = post(client, path + "/replay-preview", {"draft_choice": "new_draft"})
        assert preview["first_selection_prefill"] == "B"
        assert preview["first_selection_holder"] is None
        assert preview["first_selection_choice"] is None
        shown = post(
            client,
            path + "/replay-preview",
            {"draft_choice": "new_draft", "first_selection_holder": "B"},
        )
        assert shown["first_selection_holder"] == "B"
        post(client, previous_path + "/winner", {"winner": None})
        preview = post(client, path + "/replay-preview", {"draft_choice": "new_draft"})
        assert preview["first_selection_prefill"] is None
        assert preview["first_selection_holder"] is None
        post(client, previous_path + "/winner", {"winner": "A"})
        saved = post(
            client,
            path + "/replay",
            {
                "draft_choice": "new_draft",
                "first_selection_holder": None,
            },
        )
        assert saved["games"][-1]["first_selection_holder"] is None
        assert saved["games"][-1]["first_selection_choice"] is None


# Parent BS-012 / ADR-0016: a coupled profile supplies its actual first-pick
# Side; a missing/unknown map or unknown default cannot silently become policy.
def test_bs012_malformed_coupled_profiles_fail_explicitly(tmp_path):
    import yaml

    profiles, rules = configured_profiles(tmp_path, "sides_coupled: true\n")
    base_rules = yaml.safe_load(rules.read_text())
    for index, extra in enumerate(
        (
            {},
            {"first_pick_side": "purple"},
            {"first_pick_side": "blue", "default_first_selection_holder": "seed"},
        )
    ):
        rules.write_text(yaml.safe_dump({**base_rules, **extra}, sort_keys=False))
        with CurrentClient(
            create_app(data_dir=tmp_path / str(index), profile_dir=profiles)
        ) as client:
            response = client.get("/api/profiles")
            assert response.status_code == 500
            assert response.json()["detail"]["code"] == "profile_load_failed"


# Parent BS-012 persistence / ADR-0032: existing schema-8 records retain all
# facts when optional First Selection fields are introduced, with verified backup.
def test_bs012_schema8_migration_and_backup_restore_keep_existing_game_facts(tmp_path):
    import shutil
    import sqlite3

    data = tmp_path / "data"
    with CurrentClient(create_app(data_dir=data)) as client:
        created = series(client)
        base = "/api/series/" + created["id"]
        game = post(client, base + "/games", {"team_a_side": "blue", "first_pick_team": "B"})[
            "games"
        ][0]
        path = base + "/games/" + game["id"]
        expected = post(client, path + "/actions", {"character_id": "Ahri"})
    with sqlite3.connect(data / "nimbus.sqlite3") as db:
        db.execute("ALTER TABLE games DROP COLUMN first_selection_holder")
        db.execute("ALTER TABLE games DROP COLUMN first_selection_choice")
        db.execute("PRAGMA user_version = 8")
    with CurrentClient(create_app(data_dir=data)) as client:
        assert client.get(base).json() == expected
        backups = client.get("/api/backups").json()
        assert len(backups) == 1 and backups[0]["verified"]
    restored = tmp_path / "restored"
    restored.mkdir()
    shutil.copyfile(data / "backups" / backups[0]["name"], restored / "nimbus.sqlite3")
    with CurrentClient(create_app(data_dir=restored)) as client:
        assert client.get(base).json() == expected


# Parent BS-012 / #14 (amended 2026-11-27): holder and choice go together. A
# save that keeps the holder keeps the stored choice; changing the holder clears
# the choice, which belonged to the other Team. Unsent fields are kept unless
# that would leave them inconsistent; sent fields are recorded as sent.
def test_bs012_first_selection_edit_keeps_holder_and_choice_consistent(tmp_path):
    with CurrentClient(create_app(data_dir=tmp_path)) as client:
        base = "/api/series/" + series(client)["id"]
        game = post(
            client,
            base + "/games",
            {
                "team_a_side": "blue",
                "first_pick_team": "A",
                "first_selection_holder": "A",
                "first_selection_choice": "side",
            },
        )["games"][0]
        path = base + "/games/" + game["id"] + "/first-selection"

        def edit(body):
            saved = post(client, path, body)["games"][0]
            return saved["first_selection_holder"], saved["first_selection_choice"]

        assert edit({"first_selection_holder": "A"}) == ("A", "side")
        assert edit({}) == ("A", "side")
        assert edit({"first_selection_holder": "B"}) == ("B", None)
        assert edit({"first_selection_choice": "draft_position"}) == ("B", "draft_position")
        assert edit({"first_selection_holder": None}) == (None, None)
        both = {"first_selection_holder": "A", "first_selection_choice": "side"}
        assert edit(both) == ("A", "side")
        assert edit({"first_selection_holder": "B", "first_selection_choice": "side"}) == (
            "B",
            "side",
        )
