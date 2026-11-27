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

  # Parent: BS-005 (BS-003 example row), implemented in the same parameterized engine suite.
  Scenario: Deriving Soft Fearless under the synthetic profile preserves wasted-ban outcomes
    Given the synthetic 6-player profile under Soft Fearless
    And Team A picked Lantern in Game 1
    When the engine validates each Team's ban of Lantern in Game 2
    Then Team A's ban has no rejection
    And Team B's ban is rejected as wasted

  # BS-002 and BS-004 rows remain deferred to issue #15.
