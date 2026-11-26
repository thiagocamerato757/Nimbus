# Acceptance examples

Concrete cases agreed during design, to be turned into tests.

## Remaining pool counts availability, not personal use

- Hard Fearless. The mid Player of Team A has a Character Pool of 6, including Orianna.
- In Game 1 the opponent (Team B) picks Orianna.
- In Game 2 Team A's mid Player has 5 remaining, without having played Orianna.

## A ban on a locked Character under Soft Fearless

- Soft Fearless. In Game 1, Team A picks Orianna.
- In Game 2, a ban on Orianna by Team A is valid and useful, because it denies her to Team B.
- In Game 2, a ban on Orianna by Team B triggers the locked-ban rule (reject for the League of Legends default), because Team A cannot pick her anyway.

## Remaining versus Available Now

- A mid Player has 4 Remaining Characters at the start of a Game.
- During that Game's draft, one of the 4 is banned and a teammate picks another.
- The mid Player still has 4 Remaining and has 2 Available Now.

## The sequential-draft promise holds for a second profile

- A synthetic, test-only Deadlock-style profile: 6 Players per Team, a ban sequence A, BB, AA, B written as consecutive turns, then picks.
- The examples above pass against this profile (with its own Characters and sizes) with no engine changes.

## Lineup pool match beats global Role Usage

- Azir is played mostly mid across all imported history.
- In the opponent's current Lineup, only the top Player has Azir in their Observed Pool.
- The opponent picks Azir and has no Player Assignment yet: the Role is top, labelled as inferred from the Lineup ("only their top laner plays Azir"), not mid.

## A one-Game swap in a ranking is not a material change

- A saved report cites Azir as the most-banned Character, with 7 bans; Ahri has 6.
- Newer data puts Ahri one Game ahead of Azir, so Azir is now second.
- The Interpretation is not marked "data has changed materially".

## Golden tests for the query layer (MVP test plan)

- A fixed sample history with expected results computed by hand, for example: in a 10-Game history, Azir's ban rate is 7/10.
- Every statistic and condition, including "Games against Team X", is checked against it.

## A contested pick ranks above an uncontested comfort pick

- Our mid Player's Declared Pool has Orianna and Azir. The opposing mid Player plays Azir often and Orianna never.
- The pick Shortlist ranks Azir above Orianna.
- Orianna's reason reads as "uncontested: can wait for a later turn", not as a rejection.
