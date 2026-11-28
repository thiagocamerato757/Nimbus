# Parent: BS-010 / US-007; API seam with rule outcomes at the engine.
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

# Parent: BS-010 / US-007 confirmed extension (ADR-0009, 2026-11-27).
# Customer-facing; API and engine, browser for the immediate explanation.
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

# Parent: BS-010, every duplicate after the first carries a Violation.
# Developer-facing; rules engine seam, both Title profiles.
Feature: Derive duplicate occurrences after correction
  Engine callers can identify the unchanged actions that break the duplicate rule.

  Scenario: Correcting any occurrence leaves only later occurrences flagged
    Given a Rule Snapshot prohibiting duplicate Characters
    And three ban or pick turns with two occurrences of one Character
    When the engine corrects the remaining turn to that Character
    Then only the second and third occurrences in Draft Order have duplicate Violations
    And every other Draft Action is unchanged

# Parent: BS-010 confirmed extension, duplicate occurrence ownership.
# Developer-facing; HTTP API seam.
Feature: Save corrections with derived duplicate outcomes
  API callers receive the saved correction and the untouched actions' Violations.

  Scenario: Saving a correction returns later duplicate carriers
    Given a Series prohibiting duplicates with two or three recorded ban or pick occurrences
    When a correction makes those occurrences name the same Character
    Then the response and a subsequent read flag every occurrence after the first
    And the other recorded actions and their edit history are unchanged

# Parent: BS-010 confirmed extension, immediate explanation on another action.
# Developer-facing; browser seam.
Feature: Explain correction impact on screen
  The saved correction identifies affected actions while their records stay unchanged.

  Scenario: Saving turn 7's correction immediately identifies turn 10's duplicate
    Given a Game prohibiting duplicates with different Characters on turns 7 and 10
    When the analyst saves turn 7 with turn 10's Character
    Then the screen immediately says "This correction makes turn 10 a duplicate"
    And turn 10's Character is unchanged

  # Parent: BS-010 correction creates a Violation on another action, including another Game.
  Scenario: Saving an earlier Game correction identifies every newly affected later action
    Given later Games contain picks or bans that are legal under Hard Fearless
    When an earlier pick is corrected to their Character
    Then the screen immediately identifies each affected Game and turn with its Fearless Lock or wasted ban
    And the later Games' Draft Actions and edit history are unchanged
