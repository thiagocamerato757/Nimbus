# Parent: BS-001 (locks from earlier Games)
Feature: Derived Fearless state
  The rules engine exposes earlier picks as locks for both Teams.

  Scenario: Deriving Game 2 state locks Game 1's pick for both Teams
    Given a Hard Fearless Rule Snapshot
    And Game 1 contains Team A's pick of Orianna
    When the rules engine derives Game 2 state
    Then Orianna is locked for Team A and Team B

# Parent: BS-009 (rejected pick gives the Fearless Lock reason)
Feature: Validate manual picks
  Callers can report why a locked pick cannot be recorded.

  Scenario: Validating a locked pick returns the Fearless Lock reason
    Given Orianna is locked for Team A
    When the rules engine validates Team A's pick of Orianna
    Then the reason is Fearless Lock
