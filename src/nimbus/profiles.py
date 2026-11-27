"""Read independent YAML rules and live Character Catalog files."""

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Annotated

import yaml
from pydantic import (
    BaseModel,
    Field,
    StrictBool,
    StringConstraints,
    ValidationError,
    model_validator,
)

from nimbus.models import Character, DraftOrder, Fearless, RuleSettings, RuleSnapshot, SeriesFormat

Name = Annotated[str, StringConstraints(strict=True, strip_whitespace=True, min_length=1)]

DEFAULT_PROFILE_DIR = Path(__file__).resolve().parents[2] / "profiles"


class ProfileCharacter(Character):
    id: Name
    name: Name
    aliases: tuple[Name, ...] = ()
    retired: StrictBool = False


class CatalogFile(BaseModel):
    characters: tuple[ProfileCharacter, ...]
    data_dragon_version: Name

    @model_validator(mode="after")
    def check_character_ids(self) -> "CatalogFile":
        ids = [character.id for character in self.characters]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate Character id")
        return self


class ProfileDraftOrder(DraftOrder):
    id: Name
    name: Name


class ProfileRuleSettings(RuleSettings):
    voided_games_count: StrictBool


class TitleProfile(BaseModel):
    id: Name
    name: Name
    format_version: Annotated[int, Field(strict=True, ge=1, le=1)]
    team_size: Annotated[int, Field(strict=True, gt=0)]
    character_label: Name
    character_pool_label: Name
    sides: tuple[Name, Name]
    sides_coupled: StrictBool
    draft_orders: Annotated[tuple[ProfileDraftOrder, ...], Field(min_length=1)]
    default_draft_order: Name
    rule_settings: ProfileRuleSettings
    series_formats: Annotated[tuple[SeriesFormat, ...], Field(min_length=1)]
    default_series_format: SeriesFormat
    fearless_presets: Annotated[tuple[Fearless, ...], Field(min_length=1)]
    default_fearless: Name
    catalog: tuple[Character, ...]
    data_dragon_version: str

    @model_validator(mode="after")
    def check_pick_counts(self) -> "TitleProfile":
        if self.default_series_format not in self.series_formats:
            raise ValueError("default_series_format must be in series_formats")
        preset_ids = [preset.id for preset in self.fearless_presets]
        if len(preset_ids) != len(set(preset_ids)):
            raise ValueError("duplicate Fearless preset id")
        if self.default_fearless not in preset_ids:
            raise ValueError("default_fearless must name a Fearless preset")
        if self.sides[0] == self.sides[1]:
            raise ValueError("sides must have two distinct names")
        ids = [order.id for order in self.draft_orders]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate Draft Order id")
        if self.default_draft_order not in ids:
            raise ValueError("default_draft_order must name a Draft Order in draft_orders")
        for order in self.draft_orders:
            for position in ("first", "second"):
                picks = sum(t.kind == "pick" and t.position == position for t in order.turns)
                if picks != self.team_size:
                    raise ValueError(
                        f"Draft Order {order.id}: {position} picks must equal team size "
                        f"{self.team_size}, found {picks}"
                    )
        return self

    def snapshot(self) -> RuleSnapshot:
        order = next(order for order in self.draft_orders if order.id == self.default_draft_order)
        return RuleSnapshot(
            draft_order=order,
            rule_settings=self.rule_settings,
            series_format=self.default_series_format,
            fearless=next(p for p in self.fearless_presets if p.id == self.default_fearless),
        )


class ProfileLoadError(ValueError):
    """A profile file cannot safely be used by the application."""


def load_profiles(
    directory: Path | None = None,
    referenced_characters: Mapping[str, set[str]] | None = None,
) -> dict[str, TitleProfile]:
    root = directory or Path(os.environ.get("NIMBUS_PROFILE_DIR", DEFAULT_PROFILE_DIR))
    result = {}
    for path in sorted(root.glob("*.rules.yaml")):
        try:
            rules = yaml.safe_load(path.read_text())
            catalog_path = root / rules.pop("catalog_file")
        except (OSError, yaml.YAMLError, KeyError, TypeError, AttributeError) as error:
            raise ProfileLoadError(f"{path}: {error}") from error
        try:
            catalog = yaml.safe_load(catalog_path.read_text())
            checked_catalog = CatalogFile.model_validate(catalog)
            characters = checked_catalog.characters
            version = checked_catalog.data_dragon_version
        except (OSError, yaml.YAMLError, KeyError, TypeError, ValidationError) as error:
            raise ProfileLoadError(f"{catalog_path}: {error}") from error
        try:
            profile = TitleProfile(**rules, catalog=characters, data_dragon_version=version)
        except ValidationError as error:
            source = catalog_path if error.errors()[0]["loc"][:1] == ("catalog",) else path
            raise ProfileLoadError(f"{source}: {error}") from error
        used = (referenced_characters or {}).get(profile.id, set())
        missing = used - {character.id for character in profile.catalog}
        if missing:
            raise ProfileLoadError(
                f"{catalog_path}: Character used by stored data missing from catalog: "
                + ", ".join(sorted(missing))
            )
        result[profile.id] = profile
    return result
