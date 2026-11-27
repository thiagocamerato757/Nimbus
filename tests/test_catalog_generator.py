from scripts.generate_catalog import merge_catalog


def test_update_preserves_missing_characters_and_hand_edited_aliases():
    previous = {
        "data_dragon_version": "old",
        "characters": [
            {
                "id": "MonkeyKing",
                "name": "Wukong",
                "aliases": ["The Monkey King"],
                "retired": False,
            },
            {"id": "OldCharacter", "name": "Old Character", "aliases": [], "retired": True},
        ],
    }
    incoming = {
        "MonkeyKing": {"id": "MonkeyKing", "name": "Wukong", "image": {"full": "ignore.png"}}
    }
    updated = merge_catalog(previous, incoming, "16.23.1")
    assert updated["data_dragon_version"] == "16.23.1"
    assert updated["characters"] == [
        {
            "id": "MonkeyKing",
            "name": "Wukong",
            "aliases": ["The Monkey King", "MonkeyKing", "Wukong"],
            "retired": False,
        },
        {"id": "OldCharacter", "name": "Old Character", "aliases": [], "retired": True},
    ]
    assert previous["characters"][0]["aliases"] == ["The Monkey King"]
