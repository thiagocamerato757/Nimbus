# Parent: BS-013 and #17 format decision; developer-facing engine seam
Feature: Pure rule proposal outcomes
  Callers can validate a proposed Rule Snapshot and derive its consequences without changing the original Series.

  Scenario: Fearless proposal derives changed locks, Violations and Remaining
    Given an Off Rule Snapshot and the same picked Character in Game 1 and Game 2
    When the caller proposes Hard Fearless
    Then Game 2 derives a Fearless Lock Violation and excludes the Character from Remaining
    And the original Rule Snapshot remains Off

  Scenario: A Voided Game still retains its turn meaning
    Given a Voided Game with a recorded ban
    When the caller proposes a Draft Order making that turn a pick
    Then the proposal is refused as incompatible

  Scenario: Voided Games do not consume places in the new Series Format
    Given three non-voided Games and one Voided Game
    When the caller proposes Best-of-3
    Then the proposal is accepted with all four records retained
