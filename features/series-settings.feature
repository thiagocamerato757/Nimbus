# Parents: BS-003, BS-028; US-001, US-005. Developer-facing engine/API seam.
Feature: Series Fearless settings
  A Series snapshot determines which earlier Draft Actions make a pick or ban unavailable.

  # Parent: BS-003, scoped BS-005. Same engine suite covers both Title profiles.
  Scenario Outline: Validating a Soft Fearless ban rejects only a wasted ban
    Given Soft Fearless with picking Team reach and picks as Lock Sources
    And Team A picked a Character in Game 1
    When the engine validates Team <team>'s ban of that Character in Game 2
    Then the result is <result>

    Examples:
      | team | result            |
      | A    | no rejection      |
      | B    | wasted ban        |

  # Parent: BS-028
  Scenario: Validating picking Team reach with bans rejects the combination
    Given Custom Fearless with picking Team reach and picks and bans as Lock Sources
    When the variant is validated
    Then validation rejects picking Team reach with picks and bans

  # Parent: BS-028
  Scenario: Deriving both Teams reach with bans locks the banned Character for both Teams
    Given both Teams reach with picks and bans as Lock Sources
    And Team A banned a Character in Game 1
    When the engine derives Game 2
    Then the Character is locked for Team A and Team B
