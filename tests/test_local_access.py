"""BS-026 through the real HTTP API and temporary SQLite Workspace."""

import pytest
from fastapi.testclient import TestClient

from nimbus.api import create_app

CREATE = {"profile_id": "league-of-legends", "team_a": "North", "team_b": "South"}


# Parent BS-026: a request failing any local-access check cannot change data.
@pytest.mark.parametrize(
    "headers",
    [
        {"host": "attacker.example", "origin": "http://127.0.0.1:5173", "x-nimbus-app": "1"},
        {"origin": "https://attacker.example", "x-nimbus-app": "1"},
        {"origin": "http://127.0.0.1:5173"},
    ],
)
def test_bs026_failed_local_check_rejects_write_without_changes(tmp_path, headers):
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1:8000") as client:
        before = client.get("/api/series")
        response = client.post("/api/series", json=CREATE, headers=headers)
        assert response.status_code == 403
        after = client.get("/api/series")
        assert after.json() == before.json() == []
        assert after.headers["x-nimbus-version"] == before.headers["x-nimbus-version"]


# Parent BS-026: only the first edit based on a Workspace version may be accepted.
def test_bs026_stale_edit_is_rejected_without_overwriting(tmp_path):
    with TestClient(
        create_app(tmp_path), base_url="http://127.0.0.1:8000", headers={"x-nimbus-app": "1"}
    ) as client:
        version = client.get("/api/series").headers.get("x-nimbus-version", "0")
        accepted = client.post("/api/series", json=CREATE, headers={"x-nimbus-version": version})
        assert accepted.status_code == 201
        before = client.get("/api/series")
        stale = client.post("/api/series", json=CREATE, headers={"x-nimbus-version": version})
        assert stale.status_code == 409
        assert stale.json()["detail"]["code"] == "stale_version"
        after = client.get("/api/series")
        assert after.json() == before.json()
        assert after.headers["x-nimbus-version"] == before.headers["x-nimbus-version"]


# Parent BS-026: simultaneous outdated edits cannot both advance the draft.
def test_bs026_simultaneous_edits_accept_one_and_preserve_it(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    # Separate app instances share only SQLite: no in-process lock can make this pass.
    with (
        TestClient(
            create_app(tmp_path), base_url="http://127.0.0.1:8000", headers={"x-nimbus-app": "1"}
        ) as first,
        TestClient(
            create_app(tmp_path), base_url="http://127.0.0.1:8000", headers={"x-nimbus-app": "1"}
        ) as second,
    ):
        created = first.post("/api/series", json=CREATE, headers={"x-nimbus-version": "0"})
        base = f"/api/series/{created.json()['id']}"
        started = first.post(
            f"{base}/games",
            json={"team_a_side": "blue", "first_pick_team": "A"},
            headers={"x-nimbus-version": created.headers["x-nimbus-version"]},
        )
        path = f"{base}/games/{started.json()['games'][0]['id']}/actions"
        version = started.headers["x-nimbus-version"]
        barrier = Barrier(2)

        def edit(client, character):
            barrier.wait()
            return client.post(
                path, json={"character_id": character}, headers={"x-nimbus-version": version}
            )

        with ThreadPoolExecutor(2) as executor:
            futures = [executor.submit(edit, first, "Ahri"), executor.submit(edit, second, "Akali")]
            responses = [future.result(timeout=15) for future in futures]
        assert sorted(r.status_code for r in responses) == [201, 409]
        accepted = next(r for r in responses if r.status_code == 201).json()
        rejected = next(r for r in responses if r.status_code == 409)
        assert rejected.json()["detail"]["code"] == "stale_version"
        final = first.get(base)
        assert final.json() == accepted
        assert len(final.json()["games"][0]["actions"]) == 1
        assert final.json()["games"][0]["state"]["next_turn"]["index"] == 1


# Parent BS-026/ADR0033: browser preflight does not authorize another website.
def test_bs026_foreign_preflight_is_not_authorized(tmp_path):
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1:8000") as client:
        response = client.options(
            "/api/series",
            headers={
                "origin": "https://attacker.example",
                "access-control-request-method": "POST",
                "access-control-request-headers": "x-nimbus-app,x-nimbus-version",
            },
        )
        assert response.status_code == 403
        assert "access-control-allow-origin" not in response.headers
        assert client.get("/api/series").json() == []


# Parent BS-026: new writes must supply the version they were based on.
@pytest.mark.parametrize("version", [None, "invalid", "-1"])
def test_bs026_missing_or_invalid_version_cannot_change_data(tmp_path, version):
    with TestClient(
        create_app(tmp_path), base_url="http://localhost:8000", headers={"x-nimbus-app": "1"}
    ) as client:
        headers = {} if version is None else {"x-nimbus-version": version}
        response = client.post("/api/series", json=CREATE, headers=headers)
        assert response.status_code == 409
        assert client.get("/api/series").json() == []


# ADR-0032: introducing version checks preserves and backs up existing Workspace facts.
def test_version_migration_preserves_records_and_a_restorable_backup(tmp_path):
    import sqlite3

    data = tmp_path / "existing"
    with TestClient(
        create_app(data),
        base_url="http://127.0.0.1:8000",
        headers={"x-nimbus-app": "1", "x-nimbus-version": "0"},
    ) as client:
        created = client.post("/api/series", json=CREATE)
        base = f"/api/series/{created.json()['id']}"
        started = client.post(
            f"{base}/games",
            json={"team_a_side": "blue", "first_pick_team": "A"},
            headers={"x-nimbus-version": created.headers["x-nimbus-version"]},
        )
        game = started.json()["games"][0]
        recorded = client.post(
            f"{base}/games/{game['id']}/actions",
            json={"character_id": "Ahri"},
            headers={"x-nimbus-version": started.headers["x-nimbus-version"]},
        )
        expected = recorded.json()
    # Fixture precondition: the original schema has facts but no workspace revision.
    with sqlite3.connect(data / "nimbus.sqlite3") as old:
        old.executescript("DROP TABLE workspace_version; PRAGMA user_version = 1;")
    with TestClient(create_app(data), base_url="http://127.0.0.1:8000") as migrated:
        assert migrated.get(base).json() == expected
    backups = list((data / "backups").glob("automatic-migration-*.sqlite3"))
    assert len(backups) == 1
    restored = tmp_path / "restored"
    restored.mkdir()
    # Restore via SQLite itself; prove backup usability through the API, not its rows.
    with (
        sqlite3.connect(backups[0]) as source,
        sqlite3.connect(restored / "nimbus.sqlite3") as target,
    ):
        source.backup(target)
    with TestClient(create_app(restored), base_url="http://127.0.0.1:8000") as recovered:
        assert recovered.get(base).json() == expected
