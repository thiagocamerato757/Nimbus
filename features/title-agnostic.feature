# Parent: BS-005; stories US-021 and DS-004, issue #5
Feature: Title-agnostic rules engine
  A sequential Title profile supplies its own Characters and Draft Order,
  so adding a Title does not require an engine change.

  Scenario Outline: Deriving the next turn preserves consecutive bans for Draft Position B
    Given a Game under the synthetic 6-player profile with ban turns A, B, B, A, A, B followed by picks
    And the first <recorded_bans> bans have been recorded
    When the rules engine derives the next turn
    Then the next turn is a ban by Draft Position B

    Examples:
      | recorded_bans |
      | 1             |
      | 2             |

  # The BS-005 Scenario Outline examples remain deferred until their behavior exists:
  # BS-003 in issue #9; BS-002 and BS-004 in issue #15.
