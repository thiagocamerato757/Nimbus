# Parent: BS-009 (US-003, US-006), issue #10
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
