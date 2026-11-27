# Parent: BS-001
Feature: Fearless Locks across a Series
  Locks carry from earlier Games so the staff need not track them by hand.

  Scenario: Starting Game 2 locks Game 1's pick for both Teams under Hard Fearless
    Given a League of Legends Series under Hard Fearless
    And Team A picked Orianna in Game 1
    When the analyst starts Game 2
    Then Orianna is shown as locked for Team A and for Team B
