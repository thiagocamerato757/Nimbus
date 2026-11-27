# Parent: BS-009 (only the live-entry rejection scenario belongs to issue #4)
Feature: Rule checks on entry
  Typos are caught while real rulings can still be recorded.

  Scenario: Entering a pick of a locked Character rejects the entry with its reason
    Given a Character is locked for Team A
    When Team A's pick of that Character is entered
    Then the entry is rejected and the Fearless Lock is given as the reason
