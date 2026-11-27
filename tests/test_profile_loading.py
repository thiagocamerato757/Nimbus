"""BS-014 at the agreed API seam, with files and a temporary SQLite workspace."""

import shutil

import pytest
import yaml
from fastapi.testclient import TestClient

from nimbus.api import create_app
from nimbus.profiles import DEFAULT_PROFILE_DIR


@pytest.fixture
def profile_files(tmp_path):
    directory = tmp_path / "profiles"
    shutil.copytree(DEFAULT_PROFILE_DIR, directory)
    return directory


def edit_yaml(path, change):
    document = yaml.safe_load(path.read_text())
    change(document)
    path.write_text(yaml.safe_dump(document))


def api(data, profiles):
    return TestClient(
        create_app(data_dir=data, profile_dir=profiles),
        base_url="http://127.0.0.1:8000",
        headers={"x-nimbus-app": "1"},
    )


# Parent: BS-014; issue #7 requires the file and defect in the load error.
@pytest.mark.parametrize("missing", ["position", "kind"])
def test_bs014_loading_turn_without_position_or_type_names_file_and_defect(
    tmp_path, profile_files, missing
):
    path = profile_files / "league-of-legends.rules.yaml"
    edit_yaml(path, lambda rules: rules["draft_orders"][0]["turns"][0].pop(missing))
    with api(tmp_path / "data", profile_files) as client:
        response = client.get("/api/profiles")
    assert response.status_code == 500
    assert response.json()["detail"]["code"] == "profile_load_failed"
    assert path.name in response.json()["detail"]["message"]
    assert missing in response.json()["detail"]["message"]


# Parent: BS-014, picks per Draft Position must equal team size.
@pytest.mark.parametrize("position", ["first", "second"])
def test_bs014_loading_unequal_pick_count_names_file_and_defect(tmp_path, profile_files, position):
    path = profile_files / "league-of-legends.rules.yaml"

    def remove_pick(rules):
        turns = rules["draft_orders"][0]["turns"]
        turns.remove(next(t for t in turns if t == {"kind": "pick", "position": position}))

    edit_yaml(path, remove_pick)
    with api(tmp_path / "data", profile_files) as client:
        response = client.get("/api/profiles")
    assert response.status_code == 500
    message = response.json()["detail"]["message"]
    assert path.name in message
    assert "pick" in message and position in message and "5" in message


# Parent: BS-014, duplicate Draft Order ids.
def test_bs014_loading_duplicate_draft_order_ids_names_file_and_defect(tmp_path, profile_files):
    path = profile_files / "league-of-legends.rules.yaml"
    edit_yaml(path, lambda rules: rules["draft_orders"].append(rules["draft_orders"][0]))
    with api(tmp_path / "data", profile_files) as client:
        response = client.get("/api/profiles")
    assert response.status_code == 500
    message = response.json()["detail"]["message"]
    assert path.name in message
    assert "duplicate Draft Order id" in message


def post(client, url, document):
    version = client.get("/api/series").headers["x-nimbus-version"]
    response = client.post(url, json=document, headers={"x-nimbus-version": version})
    assert response.status_code == 201, response.text
    return response.json()


def recorded_series(client):
    series = post(
        client,
        "/api/series",
        {"profile_id": "league-of-legends", "team_a": "North", "team_b": "South"},
    )
    base = f"/api/series/{series['id']}"
    game = post(client, f"{base}/games", {"team_a_side": "blue", "first_pick_team": "A"})
    post(client, f"{base}/games/{game['games'][0]['id']}/actions", {"character_id": "Orianna"})
    return base


# Parent: BS-014; ADR-0014 requires references in stored data to survive catalog edits.
def test_bs014_loading_catalog_missing_stored_character_names_file_and_defect(
    tmp_path,
    profile_files,
):
    data = tmp_path / "data"
    with api(data, profile_files) as client:
        base = recorded_series(client)
    path = profile_files / "league-of-legends.catalog.yaml"
    edit_yaml(
        path,
        lambda catalog: catalog.update(
            characters=[c for c in catalog["characters"] if c["id"] != "Orianna"]
        ),
    )
    with api(data, profile_files) as restarted:
        response = restarted.get("/api/profiles")
        assert response.status_code == 500
        message = response.json()["detail"]["message"]
        assert path.name in message and "Orianna" in message and "missing" in message
        # The profile load error is already exposed before a Series is resumed.
        assert restarted.get(base).json()["detail"]["code"] == "profile_load_failed"


# Parent: BS-014; issue #7 acceptance validates the MVP-used ADR-0016 metadata.
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("id", ""),
        ("name", " "),
        ("format_version", 2),
        ("team_size", 0),
        ("team_size", "5"),
        ("character_label", ""),
        ("character_pool_label", ""),
        ("sides", ["blue", "blue"]),
        ("sides", ["", "red"]),
        ("sides_coupled", "false"),
    ],
)
def test_bs014_loading_malformed_rules_metadata_names_file_and_field(
    tmp_path,
    profile_files,
    field,
    value,
):
    path = profile_files / "league-of-legends.rules.yaml"
    edit_yaml(path, lambda rules: rules.update({field: value}))
    with api(tmp_path / "data", profile_files) as client:
        response = client.get("/api/profiles")
    assert response.status_code == 500
    message = response.json()["detail"]["message"]
    assert path.name in message and field in message


# Parent: BS-014; issue #7 acceptance validates used Draft Order and Rule Settings fields.
@pytest.mark.parametrize(
    ("fields", "value"),
    [
        (("draft_orders",), []),
        (("default_draft_order",), "missing-order"),
        (("draft_orders", 0, "id"), ""),
        (("draft_orders", 0, "name"), ""),
        (("rule_settings", "banning_locked"), "unknown"),
        (("rule_settings", "same_character_twice"), "unknown"),
        (("rule_settings", "voided_games_count"), "false"),
    ],
)
def test_bs014_loading_malformed_orders_or_settings_names_file_and_field(
    tmp_path,
    profile_files,
    fields,
    value,
):
    path = profile_files / "league-of-legends.rules.yaml"

    def change(rules):
        target = rules
        for field in fields[:-1]:
            target = target[field]
        target[fields[-1]] = value

    edit_yaml(path, change)
    with api(tmp_path / "data", profile_files) as client:
        response = client.get("/api/profiles")
    assert response.status_code == 500
    message = response.json()["detail"]["message"]
    assert path.name in message and fields[-1] in message


# Parent: BS-014; issue #7 acceptance validates ADR-0016 Character Catalog fields.
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("id", ""),
        ("name", ""),
        ("aliases", [12]),
        ("retired", "false"),
    ],
)
def test_bs014_loading_malformed_catalog_names_file_and_field(
    tmp_path,
    profile_files,
    field,
    value,
):
    path = profile_files / "league-of-legends.catalog.yaml"
    edit_yaml(path, lambda catalog: catalog["characters"][0].update({field: value}))
    with api(tmp_path / "data", profile_files) as client:
        response = client.get("/api/profiles")
    assert response.status_code == 500
    message = response.json()["detail"]["message"]
    assert path.name in message and field in message


# Parent: BS-014; stable Character ids (ADR-0016) cannot identify two Characters.
def test_bs014_loading_duplicate_character_ids_names_file_and_defect(tmp_path, profile_files):
    path = profile_files / "league-of-legends.catalog.yaml"
    edit_yaml(path, lambda catalog: catalog["characters"].append(catalog["characters"][0]))
    with api(tmp_path / "data", profile_files) as client:
        response = client.get("/api/profiles")
    assert response.status_code == 500
    message = response.json()["detail"]["message"]
    assert path.name in message and "duplicate Character id" in message


# Parent: BS-014, a broken profile never fails mid-Series.
def test_bs014_file_edit_does_not_break_an_already_loaded_series(tmp_path, profile_files):
    with api(tmp_path / "data", profile_files) as client:
        base = recorded_series(client)
        path = profile_files / "league-of-legends.rules.yaml"
        edit_yaml(path, lambda rules: rules["draft_orders"][0]["turns"][0].pop("kind"))
        assert client.get(base).status_code == 200


# Parent: BS-014; ADR-0014 retains Retired Characters in stored records.
def test_bs014_retired_stored_character_remains_loadable(tmp_path, profile_files):
    data = tmp_path / "data"
    with api(data, profile_files) as client:
        base = recorded_series(client)
    path = profile_files / "league-of-legends.catalog.yaml"
    edit_yaml(
        path,
        lambda catalog: next(
            character for character in catalog["characters"] if character["id"] == "Orianna"
        ).update(retired=True),
    )
    with api(data, profile_files) as restarted:
        assert restarted.get("/api/profiles").status_code == 200
        assert restarted.get(base).status_code == 200


@pytest.mark.parametrize(
    "change, defect",
    [
        (lambda r: r["series_formats"].append({"kind": "best_of", "games": 2}), "odd"),
        (
            lambda r: r.update(default_series_format={"kind": "fixed_length", "games": 99}),
            "default_series_format",
        ),
        (lambda r: r.update(default_fearless="missing"), "default_fearless"),
        (
            lambda r: r["fearless_presets"].append(
                {"lock_reach": "picking_team", "lock_sources": "picks_and_bans"}
            ),
            "picking_team",
        ),
    ],
)
def test_bs014_issue9_invalid_profile_settings_name_file_and_defect(
    tmp_path, profile_files, change, defect
):
    # Parent BS-014 / #9: newly added profile settings fail at load, never mid-Series.
    path = profile_files / "league-of-legends.rules.yaml"
    edit_yaml(path, change)
    with api(tmp_path / "data", profile_files) as client:
        response = client.get("/api/profiles")
    assert response.status_code == 500
    assert path.name in response.text
    assert defect in response.text


@pytest.mark.parametrize("change", ["remove", "rename_id", "duplicate_id"])
def test_stored_profile_identity_must_resolve_unambiguously(tmp_path, profile_files, change):
    data = tmp_path / "data"
    with api(data, profile_files) as client:
        base = recorded_series(client)
    path = profile_files / "league-of-legends.rules.yaml"
    if change == "remove":
        path.unlink()
    elif change == "rename_id":
        edit_yaml(path, lambda rules: rules.update(id="renamed"))
    else:
        shutil.copyfile(path, profile_files / "duplicate.rules.yaml")
    with api(data, profile_files) as restarted:
        response = restarted.get("/api/profiles")
        assert response.status_code == 500
        assert response.json()["detail"]["code"] == "profile_load_failed"
        message = response.json()["detail"]["message"]
        assert str(profile_files) in message
        assert "league-of-legends" in message
        assert restarted.get(base).json()["detail"]["code"] == "profile_load_failed"
