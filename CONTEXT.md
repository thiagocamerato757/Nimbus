# Nimbus

A scouting and drafting workspace for esports coaching staffs preparing for and playing a Series.

## Language

**Title**:
The video game Nimbus is being used for, such as League of Legends or Deadlock.
_Avoid_: Game

**Title profile**:
The description of one Title's draft rules and Characters.
_Avoid_: Game profile

**Player**:
A person who plays Characters. A Player is on at most one Roster, and two people with the same name are different Players.

**Roster**:
All the Players currently on a Team, possibly more than play in any one Game. Never means a Title's Characters.

**Lineup**:
The Players of one Team who play a given Game, as many as the Title's team size. A substitution is a different Lineup.

**Role**:
A Player's usual position, such as top or mid, where a Title has them. It never affects what is legal.

**Statistic**:
A figure computed from Match History, with an id, a value, a sample size and the Games behind it.

**Low-confidence Statistic**:
A Statistic whose sample size is below the Title profile's minimum.

**Scouting Report**:
A written account of one Team, made of Observations and Interpretations. A saved one keeps the Statistics it was written from.

**Outdated Report**:
A saved Scouting Report whose Report Scope no longer yields the same Games or versions of them.

**Materially Changed Interpretation**:
An Interpretation whose cited Statistics now differ materially from the saved values. It is not necessarily wrong.
_Avoid_: Contradicted

**Report Scope**:
Which Games a Scouting Report's Statistics are computed over.

**Pick Priority**:
In which pick turns a Team takes a Character, across the Games in scope.

**Role Priority**:
In which pick turns a Team takes each Role, across the Games in scope.

**Observation**:
A part of a Scouting Report that states Statistics in fixed wording, with nothing written by the AI.

**Interpretation**:
A part of a Scouting Report where the AI reads meaning into Statistics it cites. It is always shown as a reading, not as data.

**Inferred Role**:
The Role given to a pick from Character Pools or Observed Role Usage because none was recorded or assigned. It is always labelled as inferred.

**Observed Role Usage**:
How often each Character was played by Players of each Role in Match History. It exists only for Titles with Roles.
_Avoid_: Character role, tag

**Character Pool**:
The Characters a Player can play, either Declared or Observed. The League of Legends profile displays it as "Champion Pool".

**Declared Pool**:
A Character Pool entered by the coach for a Player of Our Team. It is a fact the coach owns.

**Observed Pool**:
A Character Pool estimated from a Player's match history, with how often and how recently each Character was played. It is always presented as an estimate.

**Remaining Pool**:
A Player's Character Pool minus every Character unavailable to their Team for the rest of the Series, through a Fearless Lock or the Disabled List, whoever played it.

**Available Now**:
A Player's Remaining Pool minus the current Game's bans and both Teams' picks so far.

**Team**:
A competing side of players. A Series has two, and at most one is marked as Our Team.

**Our Team**:
The Team whose coaching staff is using Nimbus, when it is playing in the Series.

**Series**:
An ordered set of Games between the same two Teams, across which Fearless locks accumulate. It is either Best-of or Fixed-length, and locks never carry into another Series.
_Avoid_: Match, Bo5

**Series Format**:
How many Games a Series plays and when it ends: Best-of or Fixed-length, with a number of Games.

**Best-of Series**:
A Series that ends as soon as one Team wins a majority of an odd number of Games.

**Fixed-length Series**:
A Series that plays a set number of Games whatever the score, as is common in scrims.

**Game**:
One played contest between two Teams, with its own draft and one winner, normally part of a Series. Never means the video game.
_Avoid_: Match, map

**Imported Game**:
A past Game brought in from match history rather than recorded live. It may be incomplete and belong to no known Series.

**Match History**:
Every past Game Nimbus knows about, imported or recorded live.

**Source**:
The named origin of Game records, within which each game reference identifies one Game. Games recorded in Nimbus belong to the built-in live Source. A record is either official or scrim, for live ones according to its Series.

**Active Record**:
Among linked records of the same real Game, the one that counts. The others are kept.

**Alias**:
Another name under which a Team, Player or Character is known.

**Current Game**:
The last Game in the Series, voided or not.

**Game Status**:
Where a Game stands: Drafting, Drafted, Closed or Voided.

**Drafting**:
A Game whose draft still has turns to be filled.

**Drafted**:
A Game whose draft is complete but which still lacks a Player Assignment or a winner.

**Closed**:
A Game that is fully recorded: every pick has a Player Assignment and the winner is known.

**Result Pending**:
A Game whose draft is complete but whose winner has not been recorded.

**Voided Game**:
A Game that was abandoned or remade. By default its Draft Actions do not count for Fearless.

**Replay**:
A new Game in the same Series that repeats a Voided Game, shares its Game number and remains linked to it. The Voided Game keeps its own record.

**Side**:
The half of the map a Team plays on in a Game, such as blue or red in League of Legends. It does not determine Draft Position.
_Avoid_: Draft side

**Draft Position**:
Whether a Team is the First-pick Team or the Second-pick Team in a Game's draft.
_Avoid_: Pick side, pick order

**First Selection**:
The right, held by one Team before a Game's draft, to choose either its Side or its Draft Position, leaving the other choice to the opponent.
_Avoid_: Side selection

**Draft Order**:
A named list of turns for a Game's draft, each belonging to a Draft Position and being either a ban or a pick. A Title profile defines one or more, and each Series uses one.

**Rule Snapshot**:
The copy of its Draft Order and other rule settings that a Series keeps from when it was created or last deliberately changed.

**Draft Action**:
What fills one turn of the Draft Order: a ban or pick of one Character by a Team. A pick belongs to the Team, not to a Player.

**Skipped Ban**:
A ban turn that passed with no Character. Pick turns cannot be skipped.

**Player Assignment**:
The record of which Player actually played a picked Character in a Game, after any swaps.
_Avoid_: Swap

**Fearless Lock**:
The unavailability of a Character to a Team in a Game because of Draft Actions in earlier Games of the same Series.

**Fearless Variant**:
The Fearless rule a Series plays under, made of a Lock Reach and Lock Sources. The picking Team reach cannot be combined with bans as a Lock Source.

**Lock Reach**:
Which Teams a Fearless Lock applies to: none, the picking Team, or both Teams.

**Lock Sources**:
Which earlier Draft Actions create Fearless Locks: picks, or picks and bans.

**Preset**:
A named Fearless Variant offered by a Title profile: Off (no reach), Soft (picking Team, picks) or Hard (both Teams, picks). Any other combination is Custom.

**Structural Invariant**:
A condition recorded draft data must always satisfy to make sense at all. It can never be overridden.

**Game Rule**:
A restriction on Draft Actions that comes from the Series' rule settings, such as a Fearless Lock or its Disabled List. It can be overridden by the analyst.
_Avoid_: Constraint, invariant

**Override**:
The analyst's deliberate recording of a Draft Action that breaks a Game Rule, with a reason.

**Violation**:
A recorded Draft Action that breaks a Game Rule.
_Avoid_: Conflict, error

**Open Violation**:
A Violation nobody has confirmed yet, typically one that appeared after a correction.

**Acknowledged Violation**:
A Violation the analyst has confirmed with a reason, either by Override or afterwards. The confirmation covers that rule, action and cause.

**Copilot**:
The assistant that advises one Team on its bans and picks during a Game's draft.

**Advised Team**:
The Team the Copilot is advising, Our Team unless changed.

**Suggestion**:
Up to three ranked options the Copilot offers for the current turn, or for consecutive turns together. It is advice and never a Draft Action.

**Shortlist**:
The ranking of options computed by code, shown until the AI's Suggestion arrives or when no AI is available.

**Suggestion Log**:
The record of each Suggestion beside what was actually recorded on that turn.

**Flag**:
The coach's mark on a Character that steers the Shortlist: Priority, Avoid, Ban Target or Save Until Game N.
_Avoid_: Tag

**Note**:
The coach's short free text about a Series or an opponent Team, read only by the AI.

**Model Role**:
A job an AI model is chosen for: prepared suggestions, manual refresh or reports.
_Avoid_: Role (which means a Player's position)

**Character**:
Anything that can be picked or banned in a Title.
_Avoid_: Champion, hero

**Character Catalog**:
Every Character in a Title, including Retired ones.
_Avoid_: Roster

**Retired Character**:
A Character permanently withdrawn from a Title. Past records still show it, but it is not offered for new entries.
_Avoid_: Removed, deleted

**Disabled Character**:
A Character temporarily barred from one Series, as when a league switches off a new or bugged one. Picking or banning it breaks a Game Rule.
_Avoid_: Retired

**Disabled List**:
The Disabled Characters of one Series.

**Workspace**:
Everything one coaching staff keeps in Nimbus, including the list of currently disabled Characters that pre-fills each new Series and the Fearless Variant of each tournament in Match History.

**Patch**:
The Title version a Series or Game was played on, when known.
