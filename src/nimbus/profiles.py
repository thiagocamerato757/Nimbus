"""Read independent YAML rules and live Character Catalog files."""

import os
from pathlib import Path

import yaml
from pydantic import BaseModel

from nimbus.models import Character, DraftOrder, RuleSettings, RuleSnapshot

DEFAULT_PROFILE_DIR = Path(__file__).resolve().parents[2] / "profiles"


class TitleProfile(BaseModel):
    id: str
    name: str
    format_version: int
    team_size: int
    character_label: str
    character_pool_label: str
    sides: tuple[str, str]
    sides_coupled: bool
    draft_orders: tuple[DraftOrder, ...]
    default_draft_order: str
    rule_settings: RuleSettings
    catalog: tuple[Character, ...]
    data_dragon_version: str

    def snapshot(self) -> RuleSnapshot:
        order = next(order for order in self.draft_orders if order.id == self.default_draft_order)
        return RuleSnapshot(draft_order=order, rule_settings=self.rule_settings)


def load_profiles(directory: Path | None = None) -> dict[str, TitleProfile]:
    root = directory or Path(os.environ.get("NIMBUS_PROFILE_DIR", DEFAULT_PROFILE_DIR))
    result = {}
    for path in sorted(root.glob("*.rules.yaml")):
        rules = yaml.safe_load(path.read_text())
        catalog = yaml.safe_load((root / rules.pop("catalog_file")).read_text())
        profile = TitleProfile(
            **rules,
            catalog=catalog["characters"],
            data_dragon_version=catalog["data_dragon_version"],
        )
        result[profile.id] = profile
    return result
