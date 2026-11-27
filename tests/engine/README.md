# Shared engine suite

Run `uv run pytest tests/engine -v`. Every test in this directory inherits the
automatic `profile` fixture and runs once for League of Legends and once for
the test-only synthetic Deadlock-style Title profile. Add engine cases here,
with the parent BS id in the test name or comment; do not copy a test per Title.

The agreed seam is `derive_state` / `validate_action`: Rule Snapshot, Character
Catalog and recorded Games/Draft Actions in; Locks, availability, turn state and
rejections out. Use `profile`, `assignments`, `character_ids`, `first_pick_index`
and `previous_pick` for inputs. Character names, Side names, turn offsets and
team sizes must come from the profile. Independent expected outcomes belong
in assertions or worked-example fixtures (such as `opening_ban_teams`), not a
second implementation of the rules.

Property cases use this same fixture and draw from its own Catalog; they must
not iterate over production profiles themselves. Hypothesis runs 80 repeatable
examples per profile and checks determinism, unchanged inputs and that locked
Characters are unavailable.

The synthetic YAML files in `tests/fixtures/profiles` describe six Players per
Team, six bans A, BB, AA, B, then twelve picks (six per Draft Position). Their
24 Characters are invented. They use the ordinary checked profile loader but
are not shipped in `profiles/` or exposed by the application. The existing
loader's `data_dragon_version` field holds a synthetic version marker; no
external Character data is used.

Issue #5 covers BS-005's consecutive-turn scenario and runs the existing #4
engine cases under both profiles. BS-003's shared cases arrive in #9; BS-002
and BS-004 arrive in #15. Their deferred Scenario Outline rows are not marked
as passing here. API and browser tests remain separate from this pure seam.
