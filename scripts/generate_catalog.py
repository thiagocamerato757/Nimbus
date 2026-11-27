"""Merge text fields from one explicit Data Dragon version; never remove Characters."""

from __future__ import annotations

import argparse
import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any
from urllib.request import urlopen

import yaml


def merge_catalog(
    previous: dict[str, Any], incoming: dict[str, Any], version: str
) -> dict[str, Any]:
    result = deepcopy(previous)
    characters = {character["id"]: character for character in result.get("characters", [])}
    for entry in incoming.values():
        identifier, name = entry["id"], entry["name"]
        character = characters.setdefault(
            identifier,
            {
                "id": identifier,
                "name": name,
                "aliases": [],
                "retired": False,
            },
        )
        # Preserve manual names, retirement decisions and aliases. Absence from a
        # release is not evidence of retirement: leave missing records untouched.
        if identifier != name:
            character["aliases"] = list(
                dict.fromkeys(
                    [
                        *character.get("aliases", []),
                        identifier,
                        name,
                    ]
                )
            )
    result["data_dragon_version"] = version
    result["source"] = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion.json"
    result["characters"] = sorted(characters.values(), key=lambda character: character["id"])
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--version", required=True, help="Explicit Data Dragon version, e.g. 16.23.1"
    )
    parser.add_argument(
        "--output", type=Path, default=Path("profiles/league-of-legends.catalog.yaml")
    )
    args = parser.parse_args()
    if not re.fullmatch(r"\d+\.\d+\.\d+", args.version):
        parser.error("version must be three dot-separated numbers")
    url = f"https://ddragon.leagueoflegends.com/cdn/{args.version}/data/en_US/champion.json"
    with urlopen(url, timeout=30) as response:
        payload = json.load(response)
    if payload.get("version") != args.version or not payload.get("data"):
        raise ValueError("Data Dragon returned an unexpected version or empty catalog")
    previous = yaml.safe_load(args.output.read_text()) if args.output.exists() else {}
    merged = merge_catalog(previous, payload["data"], args.version)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(yaml.safe_dump(merged, sort_keys=False, allow_unicode=True))
    print(f"Wrote {len(merged['characters'])} Characters from Data Dragon {args.version}")


if __name__ == "__main__":
    main()
