"""BS-027 at the agreed HTTP API seam with real temporary SQLite databases."""

import shutil

import pytest
from fastapi.testclient import TestClient

from nimbus.api import create_app

CREATE = {"profile_id": "league-of-legends", "team_a": "North", "team_b": "South"}
HEADERS = {"x-nimbus-app": "1", "x-nimbus-version": "0"}


def client_for(path):
    return TestClient(create_app(path), base_url="http://127.0.0.1:8000", headers=HEADERS)


# Parent: BS-027 / US-020: on-demand backups must be verified and restorable (ADR-0032).
def test_bs027_manual_backup_restores_workspace_through_api(tmp_path):
    data = tmp_path / "data"
    with client_for(data) as client:
        created = client.post("/api/series", json=CREATE)
        expected = created.json()
        response = client.post(
            "/api/backups",
            json={},
            headers={"x-nimbus-version": created.headers["x-nimbus-version"]},
        )
        assert response.status_code == 201
        backup = response.json()
        assert backup["kind"] == "manual"
        assert backup["verified"] is True
        assert backup in client.get("/api/backups").json()
    restored = tmp_path / "restored"
    restored.mkdir()
    # Restoration is test setup; the actual restored facts are observed only via HTTP.
    shutil.copyfile(data / "backups" / backup["name"], restored / "nimbus.sqlite3")
    with client_for(restored) as recovered:
        assert recovered.get(f"/api/series/{expected['id']}").json() == expected


# Parent: BS-027: retention spares manual backups; migration makes a verified backup first.
@pytest.mark.parametrize("retention", [2, None])
def test_bs027_migration_retention_spares_manual_backups(tmp_path, monkeypatch, retention):
    import sqlite3

    if retention is None:
        monkeypatch.delenv("NIMBUS_BACKUP_RETENTION", raising=False)
    else:
        monkeypatch.setenv("NIMBUS_BACKUP_RETENTION", str(retention))
    kept = retention if retention is not None else 10
    with client_for(tmp_path) as client:
        created = client.post("/api/series", json=CREATE)
        expected = created.json()
        manual = client.post(
            "/api/backups",
            json={},
            headers={"x-nimbus-version": created.headers["x-nimbus-version"]},
        ).json()["name"]
    automatic_names = []
    for _ in range(kept + 1):
        # Fixture: pre-existing facts are on the previous supported schema.
        with sqlite3.connect(tmp_path / "nimbus.sqlite3") as old:
            old.executescript("DROP TABLE workspace_version; PRAGMA user_version = 1;")
        with client_for(tmp_path) as migrated:
            assert migrated.get(f"/api/series/{expected['id']}").json() == expected
            backups = migrated.get("/api/backups").json()
            names = {backup["name"] for backup in backups}
            new = names - set(automatic_names) - {manual}
            assert len(new) == 1
            automatic_names.extend(new)
    assert names == {manual, *automatic_names[-kept:]}
    for name in automatic_names[-kept:]:
        restored = tmp_path / name
        restored.mkdir()
        shutil.copyfile(tmp_path / "backups" / name, restored / "nimbus.sqlite3")
        with client_for(restored) as recovered:
            assert recovered.get(f"/api/series/{expected['id']}").json() == expected


# Parent: BS-027: a backup that fails verification is reported at once.
def test_bs027_integrity_failure_is_reported_and_not_offered(tmp_path, monkeypatch):
    import sqlite3

    original_connect = sqlite3.connect

    class RejectedBackup(sqlite3.Connection):
        def execute(self, sql, *args, **kwargs):
            if sql == "PRAGMA integrity_check":
                return super().execute("SELECT 'integrity check rejected backup'")
            return super().execute(sql, *args, **kwargs)

    def connect(database, *args, **kwargs):
        # Only the external SQLite integrity-check result is controlled, not app internals.
        if "/backups/" in str(database):
            kwargs["factory"] = RejectedBackup
        return original_connect(database, *args, **kwargs)

    with client_for(tmp_path) as client:
        before = client.get("/api/series")
        monkeypatch.setattr(sqlite3, "connect", connect)
        response = client.post("/api/backups", json={})
        assert response.status_code == 500
        assert response.json()["detail"]["code"] == "backup_failed"
        assert "integrity check" in response.json()["detail"]["message"]
        assert client.get("/api/backups").json() == []
        after = client.get("/api/series")
        assert after.json() == before.json()
        assert after.headers["x-nimbus-version"] == before.headers["x-nimbus-version"]


# Parent: BS-027: only a verified backup can be offered for restoration.
def test_bs027_backup_is_not_listed_until_verification_succeeds(tmp_path, monkeypatch):
    import sqlite3

    original_connect = sqlite3.connect
    offered_during_verification = []

    class ObservedBackup(sqlite3.Connection):
        def execute(self, sql, *args, **kwargs):
            if sql == "PRAGMA integrity_check":
                offered_during_verification.extend(client.get("/api/backups").json())
            return super().execute(sql, *args, **kwargs)

    def connect(database, *args, **kwargs):
        if "/backups/" in str(database):
            kwargs["factory"] = ObservedBackup
        return original_connect(database, *args, **kwargs)

    with client_for(tmp_path) as client:
        monkeypatch.setattr(sqlite3, "connect", connect)
        response = client.post("/api/backups", json={})
        assert response.status_code == 201
        assert offered_during_verification == []
        assert client.get("/api/backups").json() == [response.json()]
