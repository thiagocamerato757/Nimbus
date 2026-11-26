# Opponent reports cover the last 20 official Games by default

Teams play at very different rates, so the default scope is a count of Games, not days: the Team's last 20 official Games (a profile setting). Every Source of imported history, and every Series recorded live, is marked official or scrim. Opponent reports default to official only, because opponent scrim data is rare and unreliable, with a filter to include scrims; our own scrims matter for our pools and testing rather than for scouting. Reports can also be filtered by date range, patch, tournament and Source, and state the number of Games and the date span they covered.

The MVP computes only what the Shortlist and the Copilot use. Per Team: bans by and against it; presence; pick rate and win rate; pick priority; Role priority; splits by Draft Position and Game number in the Series. Per Player: the Observed Pool with counts and recency, plus Observed Role Usage.

Side splits and the First Selection choices statistic come with the Scouting Report in milestone 4. Side and First Selection are still recorded from the start, and the query layer stays generic ([ADR 0028](0028-one-parameterised-query-layer.md)), so adding them later is cheap.

Voided Games never count. Result Pending Games are left out of win rates only. Games with Violations count, because they happened. A Game missing a field is left out of just the statistics that need it.

## Considered Options

- Last 90 days: sample size would swing widely between Teams.
- All Sources by default: mixes unreliable scrim data into opponent scouting.
