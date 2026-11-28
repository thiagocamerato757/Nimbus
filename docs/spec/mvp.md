# Spec: Nimbus MVP (milestones 1–3): draft board, data and Copilot

> This file is the source of truth for the MVP specification. It moved here from [issue #2](https://github.com/thiagocamerato757/Nimbus/issues/2) on 2026-11-27, because the issue body was near GitHub's size limit. Record future amendments in this file as dated sections, and never rewrite a decision silently. Issue #2 keeps a short summary that links here. Tickets #4–#30 still name #2 as their parent.

Covers the MVP: milestones 1 to 3 of the first release, as defined in `docs/mvp-scope.md`. Milestones 4 to 6 are out. Sources: `CONTEXT.md` (vocabulary), `docs/adr/` (cited as ADR-NNNN), `docs/design-notes.md`, `docs/acceptance-examples.md`, `docs/open-questions.md`.

## Problem Statement

A coaching staff preparing and playing a Fearless Series tracks by hand, in spreadsheets, which Characters are locked, what each Player still has available, and what the opponent likes to pick and ban. Every pick narrows later Games for both Teams, the information is split across documents, and during a live draft there are only seconds to use it.

## Solution

A local web app in which the analyst records each Game's draft by hand and sees Fearless Locks, Violations and each Player's pool derived by a deterministic engine; imports match history, Rosters and Declared Pools from CSV and reads opponent statistics computed by code; and gets a Copilot that shows a code-ranked Shortlist at once and replaces it with a validated, explained AI Suggestion when one arrives.

Delivered in this order:

1. **Walking skeleton:** load the League of Legends Title profile, create a Series, enter one Game's draft by hand and see Fearless Locks applied in Game 2, through the real UI and API.
2. **Draft board and data:** the rest of the rules engine and draft board, CSV imports, Rosters, Character Pools and opponent statistics.
3. **Copilot:** code Shortlist and LLM enrichment. The core idea counts as proven here.

## Stories

### US-001 — Create a Series

**Type:** User Story

As an analyst, I want to create a Series between two Teams with its Series Format, Draft Order and Fearless Variant, optionally marking Our Team, so that the board follows the rules this Series is played under.

### US-002 — Record First Selection, Side and Draft Position

**Type:** User Story

As an analyst, I want to record before each Game who held First Selection, what they chose and each Team's Side and Draft Position, so that turn order is right without assuming blue picks first.

### US-003 — Enter a draft live

**Type:** User Story

As an analyst, I want to enter each ban and pick by hand, including a Skipped Ban, so that the board matches what happens on stage.

### US-004 — See locks and the Series timeline

**Type:** User Story

As a coach, I want to see Locked Characters and a Game-by-Game timeline with what each Game's record still lacks, so that I know what is left for both Teams.

### US-005 — Choose Fearless settings

**Type:** User Story

As an analyst, I want to choose a Preset or any valid combination of Lock Reach and Lock Sources, and see the impact before changing a rule setting on an existing Series, so that invented scrim formats work and changes hold no surprises.

### US-006 — Override a Game Rule

**Type:** User Story

As an analyst, I want a rule-breaking entry to be rejected with the reason, and to record it anyway with a reason, so that typos are caught and real rulings are still recorded.

### US-007 — Correct any Draft Action

**Type:** User Story

As an analyst, I want to correct any Draft Action, even in an earlier Game, undo the latest one in the current Game, keep an edit history and see new Violations flagged, so that mistakes found late can be fixed without losing information.

### US-008 — Never be blocked during a live Series

**Type:** User Story

As an analyst, I want to start the next Game without a winner or Player Assignments, so that I never miss entries while the next draft is on stage.

### US-009 — Close, void and replay Games

**Type:** User Story

As an analyst, I want to record winners and Player Assignments, and to void a Game, so that each Game's record is complete and abandoned Games do not distort it.

### US-010 — Manage Disabled Characters

**Type:** User Story

As an analyst, I want a Disabled List per Series, pre-filled from the Workspace list, so that Characters a league has switched off are treated as unavailable.

### US-011 — Manage Rosters, Lineups and Declared Pools

**Type:** User Story

As a coach, I want to keep Rosters and Declared Pools, and set each Game's Lineup, so that availability reflects who is actually playing.

### US-012 — See Remaining and Available Now

**Type:** User Story

As a coach, I want each Player's Remaining Pool and what is Available Now, with Observed Pools shown as estimates, so that I know what each Player can still play.

### US-013 — Import with a preview

**Type:** User Story

As an analyst, I want to preview an import, map unknown names, fix rejected Games from a small file and confirm before anything is written, so that bad data does not silently skew statistics.

### US-014 — Resolve duplicate Games

**Type:** User Story

As an analyst, I want probable duplicates found and linked, so that no Game is counted twice.

### US-015 — Remove a Source

**Type:** User Story

As an analyst, I want to remove a whole Source after seeing its impact, so that I can meet a deletion obligation.

### US-016 — Read opponent statistics

**Type:** User Story

As a coach, I want opponent statistics with sample sizes, scope filters and the Games behind each figure, so that I can trust and check them.

### US-017 — Get advice during a draft

**Type:** User Story

As a coach, I want up to three explained options for the Advised Team's turns, with something on screen at once, so that I can decide within the turn.

### US-018 — Tell the Copilot what the data does not know

**Type:** User Story

As a coach, I want Flags and short Notes, so that the advice reflects my plans, including saving Characters for later Games.

### US-019 — Control the AI

**Type:** User Story

As a coaching staff member, I want to choose providers and models, see whether data leaves the machine, set a cost limit and switch the LLM off, so that spend and secrets stay under our control.

### US-020 — Keep data safe on our machine

**Type:** User Story

As a coaching staff member, I want local-only access, consistent backups and protection from other websites, so that our data is not lost or exposed.

### US-021 — Add a Title by editing files

**Type:** User Story

As the person maintaining Title profiles, I want rules and Character Catalog as files checked when loaded, so that a new sequential-draft Title needs no engine change and a broken file never fails mid-Series.

### DS-001 — Match history

**Type:** Data Story

- Goal: past Games to compute statistics and Observed Pools from.
- Source: CSV files in Nimbus's two-file schema, plus Games recorded live. Unresolved: where the staff's files come from (no outside source is assumed).
- Data type: Games and their draft actions, with optional fields (ADR-0018).
- Approximate quantity: Unresolved: no volume was stated.

### DS-002 — Rosters and Declared Pools

**Type:** Data Story

- Goal: who is on each Team and what Our Team's Players can play.
- Source: `rosters` and `pools` CSV files, or in-app editing.
- Data type: Team, Player, optional usual Role; Team, Player, Character.
- Approximate quantity: Unresolved: not stated.

### DS-003 — League of Legends profile and Character Catalog

**Type:** Data Story

- Goal: the first Title profile, with its rules file and Character Catalog.
- Source: Unresolved: where the initial catalog comes from and how it is updated.
- Data type: YAML rules file and catalog file (ADR-0016).
- Approximate quantity: Unresolved: not stated.

### DS-004 — Test fixtures

**Type:** Data Story

- Goal: prove the game-agnostic promise and the correctness of statistics.
- Source: written by hand for the project.
- Data type: a synthetic Deadlock-style profile (6 Players per Team; ban sequence A, BB, AA, B as consecutive turns, then picks) and a fixed sample history with hand-computed expected results.
- Approximate quantity: one second profile; Unresolved: size of the sample history (a 10-Game history was only an example).

### AS-001 — Draft Copilot

**Type:** Agent Story

- **Agent goal:** advise one Team on its next ban or pick with legal, explained options.
- **Possible tasks:**
  - rerank eligible Characters and give one or two lines of reason each
  - propose combinations for consecutive turns
  - on request, say what the other Team might do
- **Available artifacts:**
  - **Tools:** rules engine (locks, availability, validation) and the statistics query layer, read only
  - **Skills:** none agreed
  - **Context / knowledge:** profile rules, computed statistics, Character Pools, Flags, Notes, draft state
  - **Memory:** none agreed; each Suggestion is recorded in the Suggestion Log
- **Autonomy:** advice only. It never writes draft state, never has an Override and cannot raise its own cost limit; only what the analyst records reaches the board.
- **Expected performance:** every Suggestion shown is validated by the engine. Unresolved: the turn budget it must answer within (the first milestone 3 ticket measures it) and any follow-rate target.

## Behavioral Specifications

### BS-001 — Walking skeleton: a pick locks in the next Game

**Stories:** US-001, US-003, US-004

```gherkin
Feature: Fearless Locks across a Series
  Locks carry from earlier Games so the staff need not track them by hand.

  Scenario: A pick in Game 1 is locked for both Teams in Game 2 under Hard Fearless
    Given a League of Legends Series under Hard Fearless
    And Team A picked Orianna in Game 1
    When the analyst starts Game 2
    Then Orianna is shown as locked for Team A and for Team B
```

### BS-002 — Remaining Pool counts availability, not personal use

**Stories:** US-012

```gherkin
Feature: Remaining Pool
  A Player's Remaining Pool reflects what the Team can still use.

  Scenario: An opponent's pick reduces a Player's Remaining Pool under Hard Fearless
    Given a Series under Hard Fearless
    And the mid Player of Team A has a Character Pool of 6 including Orianna
    And Team B picked Orianna in Game 1
    When the coach views that Player's pool in Game 2
    Then 5 Characters are Remaining, although the Player never played Orianna
```

### BS-003 — Banning a locked Character under Soft Fearless

**Stories:** US-005, US-006

```gherkin
Feature: Bans on locked Characters
  A ban is stopped only when it would be wasted.

  Background:
    Given a League of Legends Series under Soft Fearless
    And Team A picked Orianna in Game 1

  Scenario: The Team that picked the Character may ban it
    When Team A's ban of Orianna is entered in Game 2
    Then the ban is accepted with no Violation

  Scenario: The opposing Team's ban of the Character is rejected
    When Team B's ban of Orianna is entered in Game 2
    Then the ban is rejected because Team A cannot pick Orianna anyway
```

### BS-004 — Remaining versus Available Now

**Stories:** US-012

```gherkin
Feature: Available Now
  The coach sees both what is left for the Series and what is left in this draft.

  Scenario: Bans and teammate picks in this Game reduce Available Now but not Remaining
    Given a mid Player with 4 Remaining Characters at the start of a Game
    And one of the 4 has been banned in this Game
    And a teammate has picked another of the 4
    When the coach views that Player's pool
    Then 4 Characters are Remaining
    And 2 Characters are Available Now
```

### BS-005 — The same rules hold for a second Title profile

**Stories:** US-021, DS-004

**Audience:** developer-facing

```gherkin
# Parents: BS-002, BS-003, BS-004
Feature: Title-agnostic rules engine
  Any sequential draft is a Title profile edit.

  Scenario Outline: The engine reproduces an agreed outcome under the synthetic 6-player profile
    Given the synthetic Deadlock-style profile with its own Characters and sizes
    And the situation of <example> expressed with them
    When the engine derives the Series state
    Then the Locks, rejections and pool counts match those <example> states

    Examples:
      | example |
      | BS-002  |
      | BS-003  |
      | BS-004  |

  Scenario: The engine accepts consecutive turns for one Draft Position
    Given a Game under the synthetic profile with the ban sequence A, BB, AA, B
    When the engine derives the turn state after the first ban
    Then the next two turns are bans by Draft Position B
```

### BS-006 — Lineup pool match beats global Role Usage

**Stories:** US-016, US-017

```gherkin
Feature: Inferred Role of an unassigned pick
  A flex pick is read against the Players actually in the Lineup.

  Scenario: The only Lineup Player with the Character in their pool decides the Role
    Given Azir was played mostly mid across Match History
    And in the opponent's Lineup only the top Player has Azir in their Observed Pool
    And the opponent has picked Azir with no Player Assignment
    When the coach views that pick
    Then its Role is shown as top, inferred from the Lineup because only their top laner plays Azir
```

### BS-007 — Golden figures from the query layer

**Stories:** US-016, DS-004

**Audience:** developer-facing

```gherkin
Feature: Statistics query layer
  Every figure in Nimbus comes from one query layer, so it is checked against hand-computed results.

  Scenario: A ban rate matches the hand-computed value
    Given the fixed sample history, in which Azir is banned in 7 of 10 Games
    When Azir's ban rate is queried
    Then the result is 7 of 10 with a statistic id and the Games behind it

  Scenario: An opponent condition restricts a query to Games against that Team
    Given the fixed sample history
    When a Team's statistics are queried with the condition "Games against Team X"
    Then the result matches the hand-computed value over only the Games where Team X was the opponent
```

### Unresolved behavior

- The exact formulas, including whether "ban rate" counts bans by the Team, against it or both, were not decided; the hand-computed values depend on them.

### BS-008 — A contested pick ranks above an uncontested comfort pick

**Stories:** US-017

```gherkin
Feature: Pick Shortlist order
  Pick order follows contest, not only comfort.

  Scenario: A contested Character ranks above an uncontested one, which is explained as able to wait
    Given our mid Player's Declared Pool has Orianna and Azir
    And the opposing mid Player plays Azir often and Orianna never
    When the pick Shortlist is shown
    Then Azir ranks above Orianna
    And Orianna's reason says it is uncontested and can wait for a later turn
```

### BS-009 — Game Rules can be overridden, Structural Invariants cannot

**Stories:** US-006

```gherkin
Feature: Rule checks on entry
  Typos are caught while real rulings can still be recorded.

  Scenario: A live entry that breaks a Game Rule is rejected with its reason
    Given a Character is locked for Team A
    When Team A's pick of that Character is entered
    Then the entry is rejected and the Fearless Lock is given as the reason

  Scenario: An Override with a reason records the entry as an Acknowledged Violation
    Given a pick was rejected for a Fearless Lock
    When the analyst overrides it with a reason category
    Then the pick is recorded with an Acknowledged Violation carrying that reason

  Scenario: A Structural Invariant cannot be overridden
    Given a Character that is not in the Character Catalog
    When the analyst tries to record it with an Override
    Then nothing is recorded

  Scenario: A pick turn cannot be skipped
    Given the current turn is a pick
    When the analyst tries to skip it
    Then the turn stays unfilled

  Scenario: A "warn" rule setting accepts the entry with a notice
    Given the Series sets banning a locked Character to "warn"
    When a ban on a locked Character is entered
    Then the ban is recorded with a notice and no Violation
```

### BS-010 — Corrections save and flag, never change anything else

**Stories:** US-007

```gherkin
Feature: Corrections
  Late mistakes can be fixed without losing recorded information.

  Scenario: A correction that makes a later pick illegal flags it
    Given a legal pick in Game 3
    When the analyst corrects a Game 1 pick to the same Character under Hard Fearless
    Then the correction is saved, the Game 3 pick is unchanged and carries an Open Violation

  Scenario: A correction is kept in the edit history
    Given a recorded Draft Action
    When the analyst corrects it
    Then the edit history shows the change

  Scenario: An Open Violation can be acknowledged
    Given an Open Violation
    When the analyst acknowledges it with a reason
    Then it is an Acknowledged Violation carrying that reason

  Scenario: Removing the cause removes the Violation
    Given a Game 3 pick with a Violation caused by a Game 1 pick
    When the Game 1 pick is corrected to another Character
    Then the Violation no longer exists

  Scenario: An Acknowledged Violation reopens when its action or cause changes and it still breaks a rule
    Given an Acknowledged Violation
    When its cause changes and the action still breaks a rule
    Then the Violation is Open

  Scenario: Reversing a correction restores the acknowledgement
    Given a correction that reopened an Acknowledged Violation
    When the correction is reversed so that rule, action and cause match what was acknowledged
    Then the Violation is Acknowledged again with its original reason

  Scenario: The most recent Draft Action of the current Game can be cleared
    Given the current Game has recorded Draft Actions
    When the analyst clears the most recent one
    Then its turn is the current turn again and the edit history shows the clearing

  Scenario: An earlier Draft Action cannot be cleared
    Given the current Game has recorded Draft Actions
    When the analyst tries to clear one that is not the most recent
    Then nothing changes

  Scenario: Nothing can be cleared while the current Game has no actions
    Given Game 1 is Drafted and Game 2 is the current Game with no Draft Actions
    When the analyst tries to clear a Draft Action
    Then Game 1 is unchanged
```

### Unresolved behavior

- Which action carries the Violation when the same Character appears twice in a Game.

### BS-011 — Starting the next Game and closing a Game

**Stories:** US-008, US-009

```gherkin
Feature: Game lifecycle
  Live entry is never blocked by missing information.

  Scenario: The next Game starts from a Drafted Game with no winner
    Given Game 1 is Drafted with no winner and no Player Assignments
    When the analyst starts Game 2, choosing "later" at the winner prompt
    Then Game 2 starts and Game 1 shows its result as pending

  Scenario: The next Game cannot start while the previous one is Drafting
    Given Game 1 is Drafting
    When the analyst tries to start Game 2
    Then Game 2 does not start

  Scenario Outline: A Game is Closed only when fully recorded
    Given a Drafted Game with assignments <assignments> and winner <winner>
    When its status is read
    Then it is <status>

    Examples:
      | assignments | winner   | status  |
      | complete    | recorded | Closed  |
      | complete    | missing  | Drafted |
      | incomplete  | recorded | Drafted |

  Scenario: A Voided Game creates no Fearless Locks by default
    Given a Game with recorded picks, under the default profile setting
    When the analyst voids it
    Then its picks lock nothing in later Games
```

### BS-012 — First Selection is recorded, not enforced

**Stories:** US-002

```gherkin
Feature: First Selection
  Turn order comes from what actually happened.

  Scenario: Blue Side may be second pick
    Given a Series whose profile does not couple Side and Draft Position
    When the analyst records Team A on blue Side as the Second-pick Team
    Then the first turn belongs to Team B

  Scenario: The result is enough to start a draft
    Given a Game with both Teams' Side and Draft Position recorded
    When the analyst leaves the First Selection holder and choice empty
    Then the draft can be entered

  Scenario: No holder is pre-filled while the previous result is pending
    Given the previous Game has no winner
    When the next Game is set up
    Then no First Selection holder is pre-filled
```

### BS-013 — A Series keeps its own rule settings

**Stories:** US-001, US-005

```gherkin
Feature: Rule Snapshot
  Editing a profile never rewrites history.

  Scenario: Editing a profile leaves an existing Series unchanged
    Given a Series created from a profile
    When that Draft Order is edited in the profile and reloaded
    Then the Series still uses the order it was created with

  Scenario: A rule setting change shows its impact before saving
    Given a Series with recorded Draft Actions
    When the analyst proposes a different Fearless Variant
    Then the Violations created or cleared and the Players whose Remaining Pool changes are shown before anything is saved

  Scenario: A Draft Order that recorded actions do not fit is refused
    Given a Series with a recorded ban in a turn that another order defines as a pick
    When the analyst switches to that order
    Then the switch is refused
```

### BS-014 — Profiles are checked when loaded

**Stories:** US-021

```gherkin
Feature: Title profile validation
  A broken profile never fails mid-Series.

  Scenario Outline: A broken profile fails to load
    Given a Title profile with <defect>
    When the profile is loaded
    Then loading fails

    Examples:
      | defect                                                      |
      | a turn lacking a Draft Position or type                     |
      | picks per Draft Position not equal to the team size         |
      | duplicate Draft Order ids                                   |
      | a Character used by stored data missing from the catalog    |
```

### BS-015 — Disabled and Retired Characters

**Stories:** US-010

```gherkin
Feature: Unavailable Characters
  Temporary and permanent withdrawal behave differently.

  Scenario: A Disabled Character is not counted as Remaining
    Given a Player whose Character Pool includes a Character on the Series' Disabled List
    When the coach views that Player's pool
    Then that Character is not Remaining

  Scenario: Entering a Disabled Character needs an Override
    Given a Character on the Series' Disabled List
    When a pick of it is entered
    Then it is rejected as a Game Rule break

  Scenario: Editing the Workspace list leaves existing Series unchanged
    Given a Series created with a Disabled List
    When the Workspace list is edited
    Then the Series' Disabled List is unchanged

  Scenario: A Retired Character is not offered for a new entry
    Given a Retired Character
    When the analyst makes a new draft entry
    Then it is not offered, and past records still show it
```

### BS-016 — Import is previewed, atomic and idempotent

**Stories:** US-013, DS-001

```gherkin
Feature: Match history import
  Bad or repeated files never silently skew counts.

  Scenario: Nothing is written before confirmation
    Given a previewed import
    When the analyst cancels
    Then nothing is stored

  Scenario: One unreadable row rejects its whole Game only
    Given a file in which one row of one Game has an invalid value in an optional field
    When the import is previewed
    Then that Game is listed as rejected with the row and reason, and the other Games can be imported

  Scenario: Rejected Games can be downloaded for fixing
    Given an import that rejected some Games
    When the analyst downloads the rejected rows
    Then the file holds only those Games' rows, each with a reason

  Scenario: Re-importing the same file adds nothing
    Given a file that was already imported
    When it is imported again
    Then every Game is reported unchanged and no statistic changes

  Scenario: A changed Game replaces its draft actions as a set
    Given an imported Game
    When a file with the same Source and game reference but different actions is confirmed
    Then the Game is reported updated and holds only the new actions

  Scenario: Suspicious data warns without rejecting
    Given a Game with the same Character twice
    When the import is previewed
    Then a warning is listed for confirmation and the Game is not rejected
```

### BS-017 — Names and Player identity

**Stories:** US-011, US-013, DS-002

```gherkin
Feature: Name mapping and identity
  One entity stays one entity, and two people stay two.

  Scenario: A mapped unknown name is remembered
    Given the analyst mapped an unknown Team name to an existing Team
    When a later file uses that name
    Then it resolves to that Team without asking

  Scenario: A known Player name on another Team is questioned
    Given a Player on one Team
    When an import shows that name playing for another Team
    Then the analyst is asked whether it is the same Player

  Scenario: Removing a Player from a Roster keeps their history
    Given a Player with recorded Games
    When the coach removes them from the Roster
    Then their Games, Player Assignments and Observed Pool remain

  Scenario: A roster import never removes Players
    Given a Roster with a Player absent from a roster file
    When the file is imported
    Then that Player stays on the Roster

  Scenario: A pools import replaces only the named Players' Declared Pools
    Given two Players with Declared Pools
    When a pools file naming only one of them is confirmed
    Then that Player's pool matches the file and the other's is unchanged
```

### BS-018 — Duplicate Games and Sources

**Stories:** US-014, US-015

```gherkin
Feature: Duplicate Games and Source removal
  Each real Game counts once, and a Source can be withdrawn.

  Scenario: An exact match is pre-selected as the same Game
    Given a Game already in Nimbus
    When a record with the same Teams, a date within one day and identical picks is previewed
    Then it is pre-selected as "same Game"

  Scenario: A partial match needs an answer
    Given an unanswered probable duplicate with only some matching picks
    When the analyst tries to confirm the import
    Then the import is not confirmed

  Scenario: Linking keeps the existing record active
    Given a live Game and a matching imported record
    When the import is confirmed as the "same Game"
    Then the Game counts once, the live record is unchanged and active, and differing values were listed in the preview

  Scenario: Removing the active record's Source promotes another linked record
    Given a Game with linked records from two imported Sources
    When the Source of the active record is removed
    Then the earliest imported remaining record becomes active
```

### BS-019 — Which Games count

**Stories:** US-016

```gherkin
Feature: Statistic scope
  Every figure says what it was computed from.

  Scenario: Voided Games never count
    Given a Voided Game
    When statistics are computed
    Then it is not included

  Scenario: A Result Pending Game is left out of win rates only
    Given a Result Pending Game
    When statistics are computed
    Then it counts in every statistic except win rates

  Scenario: A Game missing a needed field is left out of that statistic
    Given an imported Game without Draft Position
    When a Draft Position split is computed
    Then that Game is left out and the number of Games used is reported

  Scenario: A small sample is flagged
    Given a statistic whose sample size is below the profile's minimum
    When it is shown
    Then it is marked low confidence

  Scenario: The default scope is the last 20 official Games
    Given a Team with more than 20 official Games and some scrims, and the default profile setting
    When its statistics are first opened
    Then they cover its last 20 official Games and state the count and date span
```

### BS-020 — Shortlist first, AI second

**Stories:** US-017, AS-001

```gherkin
Feature: Copilot responsiveness
  The board never shows an empty Copilot on a live turn.

  Scenario: A Shortlist appears on every state change
    Given a draft in progress
    When a Draft Action is recorded
    Then a Shortlist is shown without waiting for the AI

  Scenario: The AI's Suggestion replaces the Shortlist
    Given a shown Shortlist
    When a valid AI answer arrives for the current state
    Then up to three explained options replace it

  Scenario: A state change cancels the running request
    Given an AI request is in flight
    When another Draft Action is recorded
    Then the request is cancelled and its answer is never shown as current

  Scenario: Without an LLM the Shortlist remains
    Given the LLM is switched off
    When a Draft Action is recorded
    Then the Shortlist is still shown

  Scenario: Consecutive turns are suggested together
    Given the Advised Team has two consecutive picks
    When a Suggestion is made
    Then each option covers both turns
```

### Unresolved behavior

- LLM timeout, retry limit and what the coach sees when retries run out.
- Handling of a model refusal.

### BS-021 — Suggestions are validated

**Stories:** AS-001

**Audience:** developer-facing

```gherkin
# Parent: BS-020 (the AI's Suggestion replaces the Shortlist)
Feature: Suggestion validation
  Rules are code and numbers are code.

  Scenario Outline: A model answer that breaks a check is rejected and retried
    Given a model answer containing <fault>
    When the Copilot validates it
    Then it is not shown and a retry is requested

    Examples:
      | fault                                             |
      | a Character that is not eligible                  |
      | an unknown statistic id                           |
      | a digit outside a placeholder or the allowlist    |
      | a spelled-out number of two or more               |

  Scenario: General knowledge is labelled
    Given an eligible Character with no Nimbus data
    When it is suggested
    Then the reason says it rests on general knowledge and that there is no data

  Scenario: A reason taken from a Note is shown apart
    Given a Note influenced an option
    When the Suggestion is shown
    Then that reasoning appears as "per your note", separate from data reasons
```

### BS-022 — Eligibility never hides a valid option

**Stories:** US-017

```gherkin
Feature: Shortlist eligibility
  Thin data or an uncertain guess widens the choice.

  Scenario: No pool data falls back to all legal Characters
    Given the relevant Players have no pool data
    When the Shortlist is shown
    Then legal Characters are ranked by presence with a "no pool data" notice

  Scenario: An uncertain owner of an earlier pick does not narrow picks
    Given an earlier pick that could belong to either of two Players
    When the pick Shortlist is shown
    Then Characters either of those Players has Available Now are still offered

  Scenario: A Character known only from an Observed Pool says so
    Given a Character a Player has played 4 times that is not in their Declared Pool
    When it appears in the pick Shortlist
    Then its reason says "played 4 times; not in the declared pool"
```

### BS-023 — Flags steer the Shortlist

**Stories:** US-018

```gherkin
Feature: Coach Flags
  The coach's plans work without an LLM.

  Scenario: A saved Character sits low before its Game
    Given a "Save until Game 3" Flag on a legal Character
    When the Shortlist is shown in Game 2
    Then the Character is in the bottom band with "saved for Game 3" and is not hidden

  Scenario: A saved Character becomes a priority from its Game on
    Given a "Save until Game 3" Flag on a legal Character
    When the Shortlist is shown in Game 3
    Then the Character is treated as Priority

  Scenario: A Flag never makes a locked Character eligible
    Given a Priority Flag on a Character locked for the Advised Team
    When the pick Shortlist is shown
    Then the Character is not offered

  Scenario: An expired Workspace Flag stops applying
    Given a Workspace Flag whose expiry date has passed
    When the Shortlist is shown
    Then it has no effect and is listed for review
```

### Unresolved behavior

- Which Flag wins when several apply to one Character.
- Evaluating "until patch X" when the Series has no Patch.

### BS-024 — Cost limit per Series

**Stories:** US-019

```gherkin
Feature: LLM cost limit
  Spend is bounded without blocking the draft.

  Scenario: A warning appears at 80 percent
    Given a priced model and a Series limit of $10
    When reported usage brings the Series cost to $8
    Then a warning is shown

  Scenario: Reaching the limit stops enrichment only
    Given a Series at its limit
    When a Draft Action is recorded
    Then no LLM request is made and the Shortlist is still shown

  Scenario: The analyst raises the limit
    Given a Series at its limit
    When the analyst raises the limit
    Then LLM enrichment resumes

  Scenario: A cancelled request without final usage counts its output at the upper bound
    Given a streamed request to a priced model whose input usage was reported at the start
    When it is cancelled and no final usage is reported
    Then the Series cost includes that input and max_tokens of output, labelled as an upper bound

  Scenario: A request cancelled before any usage is reported counts both upper bounds
    Given a streamed request to a priced model with no usage reported yet
    When it is cancelled
    Then the Series cost includes the prompt's input upper bound and max_tokens of output, both labelled as upper bounds

  Scenario: Every attempt of a retried request is recorded
    Given a request whose first attempt fails
    When Nimbus retries it
    Then the cost ledger holds both attempts
```

### BS-025 — Providers, privacy and capabilities

**Stories:** US-019

```gherkin
Feature: LLM providers
  The staff know where data goes and the board survives a weak model.

  Scenario: A non-loopback endpoint is shown as leaving the machine
    Given an OpenAI-compatible provider whose base URL is not a loopback address
    When the coaching staff open settings
    Then it is shown that data leaves the machine, and what is sent

  Scenario: A model without reliable tool calling or structured output is not used for enrichment
    Given a configured model that fails its capability check
    When a Draft Action is recorded
    Then the Shortlist is shown without AI enrichment and the app keeps working

  Scenario: The API key is never shown
    Given a configured API key
    When settings are read
    Then they say only that a key is configured
```

### BS-026 — Local protection and concurrent tabs

**Stories:** US-020

```gherkin
Feature: Local access protection
  Other websites and stale tabs cannot change data.

  Scenario Outline: A state-changing request failing a check is rejected
    Given a state-changing request with <problem>
    When it reaches Nimbus
    Then it is rejected and nothing changes

    Examples:
      | problem                          |
      | an unexpected Host               |
      | a foreign Origin                 |
      | no custom application header     |

  Scenario: An edit from an outdated tab is rejected
    Given two tabs, one of which has not seen the latest change
    When that tab submits an edit to the same data
    Then the edit is rejected rather than overwriting
```

### BS-027 — Backups

**Stories:** US-020

```gherkin
Feature: Backups
  A backup that cannot be restored is worse than none.

  Scenario Outline: A backup is made before a risky operation
    Given existing data
    When <operation> is about to run
    Then a verified backup is made first

    Examples:
      | operation          |
      | a schema migration |
      | a Source removal   |
      | an import          |

  Scenario: A backup that fails verification is reported
    Given a new backup that fails its integrity check
    When it is verified
    Then the failure is reported at once

  Scenario: Retention spares manual backups
    Given more automatic backups than the retention number, and some manual ones
    When old backups are pruned
    Then only the oldest automatic ones are removed
```

### BS-028 — A picking-Team lock cannot come from bans

**Stories:** US-005

```gherkin
Feature: Custom Fearless Variant validation
  A combination whose meaning was never defined is refused rather than guessed.

  Scenario: Picking Team reach with bans as a Lock Source is rejected
    Given a Custom variant with Lock Reach "picking Team" and Lock Sources "picks and bans"
    When it is validated
    Then it is rejected with an error naming the combination

  Scenario: Both-Teams reach with bans locks the banned Character for both Teams
    Given a Series with Lock Reach "both Teams" and Lock Sources "picks and bans"
    And a Character was banned in Game 1
    When the analyst starts Game 2
    Then that Character is locked for both Teams
```

## Acceptance Criteria

The MVP is not done until each of these passes. They are the MVP acceptance examples from `docs/acceptance-examples.md`.

| ID | Acceptance example | Specified by | Verified at |
|---|---|---|---|
| AC-1 | Remaining Pool counts availability, not personal use | BS-002 | Engine, API |
| AC-2 | A ban on a locked Character under Soft Fearless | BS-003 | Engine, API |
| AC-3 | Remaining versus Available Now | BS-004 | Engine, API |
| AC-4 | The sequential-draft promise holds for a second profile | BS-005 | Engine |
| AC-5 | Lineup pool match beats global Role Usage | BS-006 | API, browser |
| AC-6 | Golden tests for the query layer | BS-007 | API |
| AC-7 | A contested pick ranks above an uncontested comfort pick | BS-008 | API, browser |

The remaining acceptance example (a one-Game swap in a ranking is not a material change) concerns saved Scouting Reports and belongs to milestone 4.

## Implementation Decisions

### Stack and shape

- FastAPI backend (Python 3.12+, managed with uv); React and TypeScript frontend; one local Workspace per data folder (ADR-0005).
- **Rules are code, judgment is AI** (ADR-0002). **Title-agnostic engine** (ADR-0001, partly superseded by ADR-0011 and ADR-0012).

### Modules

- **Title profile loader:** reads and validates the rules file and Character Catalog.
- **Rules engine:** pure, no I/O. Input: a Series' Rule Snapshot, the Character Catalog, Disabled List, Draft Actions, Game states and Character Pools. Output: Locks, turn state, Violations and availability (Remaining and Available Now). It also validates a proposed action. Nothing it derives is stored.
- **Series service:** Series, Games, Draft Actions, edit history, Overrides, Lineups, Player Assignments, impact preview.
- **Import pipeline and identity:** preview, rejection, warnings, name mapping, duplicate linking, Sources.
- **Statistics query layer:** the only source of figures.
- **Copilot:** eligibility, Shortlist ranking, prompt building, validation, Suggestion Log.
- **LLM interface:** Anthropic adapter, OpenAI-compatible adapter, fake model; cost ledger.
- **Storage and backups.**
- **Web API and frontend.**

### Title profiles (ADR-0014, 0015, 0016)

- Hand-edited YAML, validated at load; no profile editor. Rules file and catalog file are separate.
- Rules file: id, name, format version; display labels; team size; optional Roles; Side names, coupled flag and, if coupled, which Side picks first; default First Selection holder (loser, winner, alternate, none); named Draft Orders with stable ids and a default; allowed Series Formats (a fixed list; an entry may be "Fixed-length, any N") and a default; Fearless Presets and a default; rule settings (locked ban: allow, warn, reject; same Character twice in a Game: allow, reject; whether Voided Games count); report Game count; Role majority threshold; minimum sample size; digit allowlist; shortlist band thresholds; untranslated terms per language. Timer and material-change settings belong to later milestones.
- Catalog: stable id, display name, aliases, Retired flag. No Character roles or tags (ADR-0017). Characters are never deleted; the catalog is read live, not snapshotted.
- Sequential drafts only: one visible ban or pick per turn in a fixed order.

### Series, Games and draft rules (ADR-0003, 0006 to 0014)

- A Series snapshots its Draft Order (with its id) and rule settings.
- Fearless Variant is Lock Reach (none, picking Team, both) and Lock Sources (picks, picks and bans). Every combination is allowed except picking Team with picks and bans, which is rejected with a clear error (ADR-0011, amended); this applies wherever a variant is validated. Presets: Off, Soft, Hard.
- Picks in non-Voided earlier Games lock, including picks with Violations. Locks follow the Character, never the Player, apply as soon as recorded and never cross Series. Bans lock only if Lock Sources include them.
- The locked-ban rule applies only when the Character is already locked for the opponent of the banning Team.
- Draft Order turns are written by Draft Position, never Side. A ban turn may be skipped; a pick turn may not.
- Structural Invariants (one action per turn; the turn exists; the Character is in the catalog) are absolute. Game Rules reject a live entry, can be overridden with a category and optional note, and corrections always save. Violations are derived, Open or Acknowledged; nothing changes automatically. An acknowledgement stores a fingerprint of rule, action and cause and applies whenever all three match exactly (ADR-0009, amended).
- Only the most recent Draft Action of the current (latest non-voided) Game can be cleared; if it has none, there is nothing to clear. Others are corrected by replacement. Clearing goes into the edit history (ADR-0008, amended).
- Series Formats: Best-of (odd N, ends on a majority) or Fixed-length. Voided Games do not count. With results pending a Best-of Series is not declared over. A corrected winner never deletes Games; warn if Games exist past the deciding one.
- Game status: Drafting, Drafted, Closed (all Player Assignments and a winner); Voided from any status. The next Game needs the previous one Drafted, Closed or Voided.
- A Series may be between any two Teams, Our Team optionally marked; each live Series is marked official or scrim.
- Lineups are per Game, pre-filled from the previous one, and may be incomplete during the draft. Assignments go only to Lineup Players, one Character each.
- Patch is an optional Series field, overridable per Game, unused by MVP features.

### Data, import and identity (ADR-0018 to 0020, 0027)

- `games`: game reference, date and both Team names required; Series reference, Game number, Sides, Draft Positions, winner, patch, tournament and Fearless Variant optional.
- `draft_actions`: game reference, Team, ban or pick, Character required; order, Player, Role optional.
- Variant of an imported Game: row, else a Workspace tournament mapping, else unknown. Differing variants within one Series reference raise a warning.
- The unit of rejection is the Game. Missing optional fields are not errors; a Game with no actions is accepted. Game Rules are not enforced on history. Importing is idempotent per Source and game reference, previewed and atomic.
- Warnings needing confirmation: same Character twice in a Game; more picks than team size; differing variants in a Series reference; probable duplicates. Fewer picks than team size is not a warning.
- Duplicates: same Teams after aliases within one day. Exact (all picks identical) is pre-selected with confirm-all; partial has no default. "Different Games" is remembered. The existing record wins; dropped or contradicting values are listed, a contradicting winner as a warning.
- Every record keeps its Source and is official or scrim; live Games use a built-in live Source. Linked records are all kept, exactly one active. Removing a Source shows an impact preview; the new active record is live first, then earliest import.
- Imported values are kept as received beside their mapping.
- A Player is on at most one Roster; history never moves Rosters. Name mappings live in the Workspace; the app never rewrites catalog files.

### Statistics (ADR-0022, 0023, 0028)

- One parameterised query layer: Team, Side, Draft Position, scope filters and conditions, including opponent conditions such as "Games against Team X". Each result has a statistic id, value, sample size and Games.
- MVP statistics: bans by and against; presence; pick rate; win rate; pick priority; Role priority; splits by Draft Position and Game number in the Series; Observed Pools with counts and recency; Observed Role Usage.
- Scope: last 20 official Games by default (profile setting); filters for date range, patch, tournament, Source and scrim inclusion. Statistics below the minimum sample size are flagged low confidence.
- A pick's Role: recorded Role, else assigned Player's usual Role, else Lineup pool match, else Observed Role Usage majority (default 70%), else unknown. The last two inferred steps are labelled and counted.

### Copilot (ADR-0017, 0021, 0026, 0029)

- On every state change code produces a Shortlist; the AI result replaces it. Prepared suggestions start when the previous action is entered, can be switched off, and can be refreshed manually.
- Eligibility: picks are legal Characters a Lineup Player without a pick has Available Now; bans are legal Characters the opposing Lineup can play. Earlier pick ownership is inferred and widens when uncertain.
- Ranking is ordered factors with the first grouped into high, medium and low bands. Bans: opponent presence and pick priority; then fewest comparable options left for the likely Player; then recency. Picks: contest (opponent pool and priority); then Declared Pool; then the Advised Team's pick rate; then win rate. Every entry states why it sits there. The LLM may choose any eligible Character.
- Flags: Priority, Avoid, Ban Target, Save Until Game N; per Series or Workspace, Workspace ones with optional expiry. Notes: short free text per Series and per opponent Team, read only by the LLM.
- Advised Team is Our Team by default; ask if neither is marked. On-request "what might they do?". Warn about Open Violations only.
- Reasons cite statistic ids through placeholders; no digits or spelled-out numbers from two upwards in free text.
- Suggestion Log: state, what was actually recorded, latency, tokens, Flags and Notes in effect.

### LLM providers, cost and privacy (ADR-0030, 0031)

- Anthropic official Python SDK and an OpenAI-compatible HTTP adapter (Ollama, llama.cpp server, NVIDIA NIM) behind one interface.
- Model Roles per Workspace: prepared suggestions (default `claude-haiku-5-5`), manual refresh (default `claude-opus-5-5`, low effort). The reports role is unused in the MVP.
- Each model declares tool calling, structured output and context length, checked by a startup test call that never blocks the app.
- Only a loopback base URL counts as staying on the machine. Send only what the request needs. LLM off switch.
- Requests are streamed and cancellation is never delayed. Reported usage is used whenever it arrives. Before sending, a conservative input upper bound is computed from the prompt; a request cancelled (or failing after being sent) without reported usage is charged that bound for input and `max_tokens` for output, labelled as upper bounds, with the input bound priced at the highest input rate that could apply. The limit may overcount, never undercount.
- Client-library automatic retries are disabled; Nimbus retries itself and records every attempt in the cost ledger. `max_tokens` is set per Model Role and kept tight. The same rules hold for every provider; each adapter's actual reporting is checked in the adapter ticket (ADR-0031, amended).
- Price table in a configuration file; cost from reported usage including cache reads and writes. Priced models: $10 per Series by default, 80% warning, stop at 100%, one-click raise. Unpriced: optional token limit.
- Stable prompt content first and marked for caching; draft state last.

### Language (ADR-0024)

- The per-language mechanism (templates, number-word lists, digit check, untranslated terms) is built, shipping English only. All UI strings use translation keys.

### Storage, access and security (ADR-0032, 0033)

- SQLite, one file, WAL, schema migrations from milestone 1; default folder `~/.local/share/nimbus`; warn if under `/mnt/`. No encryption, stated to the user.
- Backups on demand and before migrations, Source removals and imports, via `VACUUM INTO` or the backup API, integrity-checked; keep the last 10 automatic ones (configurable). Restore replaces the file with the app closed and removes `-wal` and `-shm` files. Source removal compacts the database and offers to delete older backups.
- Bind `127.0.0.1` only; no login; Host and Origin checks; custom header on state-changing requests; no wildcard CORS; keys never reach the frontend.
- Multiple tabs: server is the truth, tabs update, stale edits are rejected.
- Run from source. Linux including WSL2 is supported; "open from the Windows browser" is documented and tested.

## Testing Decisions

A good test states behavior observable at a seam and survives internal redesign. Three seams are agreed.

**Seam 1 — Backend HTTP API (primary).** The real application with a temporary database, test Title profiles and a fake LLM model. No network, no spend. Covers persistence, import, identity, statistics, Copilot, cost, security and backups. The statistics query layer is tested here, golden tests included, because it depends on storage.

**Seam 2 — Rules engine interface.** Rule settings and catalog plus Draft Actions in; Locks, turn state, Violations and availability out. This is the most stable contract in the project. Rule combinations (Fearless Variants × Lock Sources × profiles × corrections × voids) are tested here, with property-based tests using Hypothesis, including at least:
- a Locked Character is never Available Now to a Team it is locked for;
- a correction followed by its reversal restores the same derived state, acknowledgements included (edit history excluded);
- every derived value is identical when recomputed from the same actions.

The same engine suite runs against the League of Legends profile and the synthetic 6-player profile, as the direct proof of ADR-0001.

**Seam 3 — Browser, with Playwright.** A few journeys only: the walking skeleton, and what exists only on screen (labels, reasons, notices).

**Outside the automated suite:** a small optional check of the real Anthropic and OpenAI-compatible adapters (integration test against a local OpenAI-compatible server in CI if feasible, otherwise manual), and the milestone 3 latency prototype.

| Behavior | Verified through |
|---|---|
| BS-001 | Browser (walking skeleton), API |
| BS-002, BS-003, BS-004 | Engine; API |
| BS-005 | Engine |
| BS-006, BS-008 | API; browser for the label and reason |
| BS-007 | API |
| BS-009, BS-010, BS-011, BS-013, BS-015 | API; their rule outcomes also at the engine |
| BS-012 | Engine for turn order; API |
| BS-014 | API (application loading profiles) |
| BS-016 to BS-019 | API |
| BS-020 to BS-025 | API with the fake model |
| BS-026, BS-027 | API |
| BS-028 | Engine; API for the validation error |

**Prior art:** none. The repository has no code yet.

## Out of Scope

- Milestone 4: Scouting Report, "Ask the report", saved-report snapshots, Side splits and the First Selection statistic.
- Countdown timer (milestone 4 or later).
- Brazilian Portuguese language data (follows right after the MVP).
- Milestone 5: opponent pool forecasting and forecast logging.
- Milestone 6: external data API.
- Deadlock profile, plan export, accounts and multiple users, access from the local network, encryption.
- Live capture of picks and bans, simultaneous or hidden drafts, transfer history, patch weighting, Copilot advice on First Selection, a profile editor, merging fields from duplicate records, converters from outside files, a translated interface, tuning the ranking from the Suggestion Log.

## Further Notes

### First ticket of milestone 3

Before building the Copilot, a prototype (`/prototype`) measures whether the prepared-suggestion model (`claude-haiku-5-5`, and a local model if one is available) answers within the turn budget with a realistic copilot prompt. The ticket states the budget; the result is recorded.

### Unresolved

To settle in the ticket that needs each one:

- **Rules:** Available Now when the same Character is allowed twice in a Game; which duplicate carries the Violation.
- **Workflow:** Override reason categories; pre-fill when replaying a Voided Game; changing a Series Format after Games exist; undoing a wrong alias, "same Player" or "same Game" answer; recording live a Game already imported; whether the live Source can be removed; whether Source removal also clears derived Suggestion Log entries.
- **Data:** CSV column names, date format, encoding, delimiter; origin and updating of the League of Legends catalog.
- **Figures:** exact formulas for presence, pick rate, win rate, pick priority, recency and "comparable options"; default thresholds; which Games (scrims or not) feed the Copilot for each Team.
- **AI:** turn budget; timeouts, retries, refusals; `max_tokens` per Model Role and how the input upper bound is computed; Flag precedence and patch expiry; English templates, number words and digit allowlist.

### Unverified

- The default First Selection holder has not been checked against league rulebooks.
- No model has been measured against a live pick turn.
- Minimum cacheable prompt length, cache prices and provider data retention terms need checking in the provider's documentation.




## Confirmed implementation amendments — 2026-11-27

## Confirmed decisions — 2026-11-27

The developer confirmed these outcomes in the grill-with-docs interview. No product questions remain for this slice.

- If the Series prohibits duplicate Characters, each occurrence after the first in Draft Order carries the duplicate Violation, regardless of which action was edited; the first does not.
- Saving a correction that creates a Violation on another action immediately explains the affected action, e.g. "This correction makes turn 10 a duplicate". Other actions remain unchanged.
- Source: ADR 0009 amendment and docs/acceptance-examples.md.

### BS-010 confirmed extension (US-007)

**Audience:** customer-facing

```gherkin
Feature: Correction impact
  Analysts can connect a correction to the other actions it affects.

  Scenario: An earlier correction flags and explains the later duplicate
    Given duplicate Characters are prohibited in the Game
    And turns 7 and 10 name different Characters
    When the analyst corrects turn 7 to the Character recorded on turn 10
    Then the correction saves and turn 10 is unchanged with a duplicate Violation
    And turn 7 does not carry that duplicate Violation
    And the analyst immediately sees "This correction makes turn 10 a duplicate"

  Scenario: Every duplicate after the first carries a Violation
    Given a correction has left three occurrences of the same Character in a Game that prohibits duplicates
    When the Game's Violations are read
    Then the second and third occurrences in Draft Order carry duplicate Violations
    And the first occurrence does not carry that duplicate Violation
```

Testing Decisions: retain BS-010 API and rule-engine seams (both profiles), plus the agreed browser seam for the immediately visible impact explanation. Existing BS-010 scenarios and acceptance criteria remain in scope.

## Confirmed decisions — 2026-11-27

The developer confirmed these outcomes in the grill-with-docs interview. No product questions remain for this slice.

- A Replay creates a new linked Game in the same Series and retains the Voided Game/history; both share a Game number. Only the latest voided attempt can be replayed, before a following Game starts. Replay chains retain that number.
- Editable prefill from the source: Lineups, Sides, Draft Positions, Patch. Explicit copy-draft/new-draft choice, with no default. Player Assignments and winner start empty.
- Copied Draft Actions are validated, editable prefill. Save immediately despite Game Rule Violations and show the Violations in the preview. Structural Invariants remain mandatory; no silent action drops.
- Open stays Open. Inherit an acknowledgement only for matching rule/action/cause, with provenance and reason "carried from voided Game N" plus the original reason. A different cause or new breach arrives Open without blocking. Subsequent changes/reversals follow ADR 0009.
- General rule: Fearless Locks apply only to higher Game numbers in the same Series. Same-number attempts cannot lock against each other, even when the snapshot counts Voided Games; such attempts still lock higher-numbered Games under that setting.
- Source: ADRs 0009, 0011 and 0034; docs/acceptance-examples.md (including Azir).

### BS-011 confirmed extension (US-004, US-008, US-009)

**Audience:** customer-facing

```gherkin
Feature: Replay of a Voided Game
  Analysts can record the repeated attempt without losing the abandoned one.

  Scenario: Replay setup requires an explicit draft choice
    Given the most recent attempt is Voided and no following Game has started
    When the analyst sets up its Replay
    Then Lineups, Sides, Draft Positions and Patch are pre-filled and editable
    And the analyst must choose "copy the voided Game's draft" or "new draft" with no default

  Scenario Outline: Creating a Replay preserves a linked attempt with the chosen draft
    Given the most recent attempt is Voided and no following Game has started
    When the analyst creates its Replay choosing <choice>
    Then a new Game is saved with the same Game number and linked to the preserved Voided Game
    And its Draft Actions are <actions> and remain editable
    And its Player Assignments and winner are empty
    And the timeline identifies it as a replay of the Voided Game

    Examples:
      | choice                       | actions                  |
      | copy the voided Game's draft  | copied from that attempt |
      | new draft                    | empty                    |

  Scenario: Copied Violations keep their scope and provenance without blocking
    Given a Voided Game has an Open Violation and an Acknowledged Violation
    When the analyst creates a Replay copying its draft
    Then the copy saves despite Game Rule Violations and shows those Violations in the preview
    And the Open Violation stays Open
    And the corresponding acknowledged rule, action and cause stay Acknowledged with "carried from voided Game N" plus the original reason and traceable provenance
    And any different cause or new breach arrives Open
    And Structural Invariants still hold and no actions are silently dropped

  Scenario: A voided Replay can itself be replayed
    Given the latest Replay is Voided and no following Game has started
    When the analyst creates another Replay
    Then the new attempt keeps the same Game number and links to the latest voided attempt

  Scenario: An older voided attempt cannot be replayed after a following Game starts
    Given a Voided Game has a following Game already started
    When the analyst tries to replay the older Voided Game
    Then no Replay is created and existing Games are unchanged

  Scenario: A counted Voided Game locks higher Game numbers but not its own Replay
    Given Hard Fearless with Voided Games counted and no earlier Azir Lock
    And Game 3 picked Azir and was Voided
    When the analyst reads the state of its draft-copy Replay and Game 4
    Then the Replay of Game 3 has no Fearless Violation from that voided attempt
    And Azir is locked for both Teams in Game 4
```

Testing Decisions: retain BS-011 API and rule-engine seams (both profiles), plus the agreed browser seam for the explicit draft choice, prefill, preview/provenance and replay timeline. Existing BS-011 scenarios and acceptance criteria remain in scope.


## First Selection profile clarification (#14)

## Default policy resolution — 2026-11-27

The generic League of Legends Title profile uses an explicit `default_first_selection_holder: none`; it does not claim a universal league policy. Official Riot NACL 2026 rulebook v26.6 (August 2026), sections 2.3.3.1 and 2.6.5.1, specifies random allocation for Game 1 and the previous loser for subsequent Games in that league. The configurable loser policy supports this documented case; winner/alternate/none are also configurable and always editable. A missing previous winner must not guess a holder, including for a Replay whose same-number voided source has a recorded winner.

Official source: https://cdn.sanity.io/files/dsfx7636/news_live/60f17a7a37ed1d1a380c80f78e029e636dca87e1.pdf via https://competitiveops.riotgames.com/en-US/library?GAME=lol . This is evidence for the scoped NACL rule, not for one rule across all leagues.

For coupled profiles, the profile explicitly declares `first_pick_side`; its mapping is not inferred from array order. Coupling and default settings are snapshotted with the Series (ADRs 0006, 0007, 0013).


## Confirmed amendments — 2026-11-27 (PR #34 review)

The developer settled these outcomes after the Claude Code review of PR #34. They amend the Implementation Decisions above; the original lines are kept for history.

- **Current Game** (amends "Only the most recent Draft Action of the current (latest non-voided) Game can be cleared"). The current Game is the last Game in the Series, voided or not, for clearing, live entry and starting the next Game. A Voided current Game has nothing to clear, and earlier Games are corrected by replacement (ADR 0008, amended).
- **Next Game** (amends "The next Game needs the previous one Drafted, Closed or Voided"). The next Game needs the previous one Drafted or Closed. After a Voided Game, the next Game is always its Replay under the same number, so a Best-of-3 goes 1, 2 (voided), 2, 3. The Series Format's maximum counts non-voided Games only (ADR 0034, amended).
- **Winner.** A winner can be set only for a Drafted or Closed Game, and cleared in any status. Series progress ignores a winner on a Game in any other status, and a Game sent back to Drafting can still have its stored winner cleared (refined later on 2026-11-27).
- **Replay gate.** A Replay is how the next Game starts after a void, so it follows the same gate as an ordinary next Game: it is rejected with `series_ended` while the Series has ended. "Ended" is derived from the current score, so a winner correction that un-decides the Series makes the Replay available again (ADR 0034, amended).
- **One ordered gate.** `can_start_next`, starting a Game and creating a Replay all use one engine gate. Its order is `series_ended`, then `replay_required`, then `draft_incomplete`, then `series_full`, so an ended Series is never told to replay. The engine also enforces the Replay gate, at the BS-011 engine seam.
- **What a record lacks** (refines #13 "what its record lacks"). The missing list shows everything still needed to reach Closed: a complete draft, a Player Assignment for every pick turn in the Draft Order, and the winner if absent. A stored winner that does not count yet is shown as a note, not as missing.
- **First Selection edits** (amends #14 "either can be corrected or cleared"). Holder and choice go together. A save that keeps the same holder keeps the stored choice. A save that changes the holder clears the stored choice, because it belonged to the other Team. Unsent fields are kept unless that would leave them inconsistent. A choice always belongs to a holder. A choice without a holder is rejected with `choice_without_holder` at Start Game, Replay and edits. One engine rule records First Selection for all three, and the UI disables the choice until a holder is selected and clears it when the holder changes. A choice without a holder is a Structural Invariant breach (ADR 0009, amended); an edit is rejected only when it would create one, and a database migration clears any stored one, logging each. The UI sends holder and choice exactly as displayed.
- **Voiding** (amends "Voided from any status"). A Game can still be Voided from any status, but only the current Game, the last one in the Series, can be voided. Voiding an earlier Game while a later one exists is rejected, because it would change the numbering and the Locks of the Game in progress (ADR 0034, amended).
- **Replay copy.** Copying a voided Game's draft requires the same Draft Positions. To change them, choose new draft (ADR 0034, amended; clarified in #13).
- **First Selection pre-fill (BS-012, #14).**
  - The pre-fill is computed for display only; the server never applies a holder the analyst has not seen.
  - Setup and Replay requests carry the holder the analyst saw, and an omitted holder records none.
  - After "Record winner and start", the setup form shows the First Selection pre-fill before the draft begins (as an offer; see below).
- **First Selection pre-fill while a form is open** (refines "The pre-fill is computed for display only"). The setup and Replay forms take the First Selection pre-fill once, when they open. Only the analyst's own change or Apply moves the holder. If the underlying result later changes, nothing on the form changes: the form offers the new pre-fill ("With the current result, the suggested holder would be B. Apply?"). Applying it changes the holder and clears the choice; ignoring it changes nothing. If "Record winner and start" produces a different pre-fill, the draft does not start: the form shows the offer, and the analyst applies it or presses Start again.

## Confirmed amendment — 2026-11-28 (PR #34 follow-up)

- **"A different pre-fill"** (refines "If \"Record winner and start\" produces a different pre-fill, the draft does not start"). "Different" means different from what is displayed, not different from the previous pre-fill. If the new pre-fill equals the holder already shown, the analyst has seen what will be recorded, so starting is fine. The draft therefore stops whenever the new pre-fill names a Team other than the holder shown, and the form offers it. If the new result gives no pre-fill and a holder is shown, the draft starts, because nothing unseen is applied.
- **The offer is derived** (amends "If the underlying result later changes, nothing on the form changes: the form offers the new pre-fill"). An offer is shown if and only if there is a current pre-fill and it names a Team other than the holder displayed. "Record winner and start" stops if and only if, after recording, that offer exists. No state remembers which pre-fill a form took (the principle of ADR 0008), so a result that gives no pre-fill offers nothing, and picking the offered Team by hand clears the offer and the notice.
- **No edits during a save** (refines "Setup and Replay requests carry the holder the analyst saw"). The next-Game setup cannot be edited while a save runs, so the holder and choice recorded are the ones shown.
