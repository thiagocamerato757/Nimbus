# Parent: BS-013
Feature: Preview deliberate Series rule amendments
  Analysts can see the consequences of a rule amendment before changing recorded history.

  Scenario: Editing a profile leaves an existing Series Rule Snapshot unchanged
    Given a Series with recorded Draft Actions created from a Title profile
    When that profile's Draft Order is edited and reloaded
    Then the Series still uses its own original Draft Order

  Scenario Outline: Changing Fearless shows the changed rule outcomes before saving
    Given a Series with a Character picked in two Games and a Player with that Character in their Declared Pool
    And Fearless is <before>
    When the analyst previews Fearless <after>
    Then the preview shows the repeated pick's Violation <outcome>
    And the Player's Remaining Pool changes to <remaining>
    And the saved Series is unchanged
    Examples:
      | before | after | outcome | remaining |
      | Off | Hard | created | exclude that Character |
      | Hard | Off | cleared | include that Character |

  Scenario: Incompatible recorded turns refuse a Draft Order amendment
    Given a Series with a recorded ban in a turn that another Draft Order defines as a pick
    When the analyst proposes that Draft Order
    Then the amendment is refused

  Scenario Outline: The Disabled List uses the rule amendment preview
    Given a Series with a recorded Character in a Player's Declared Pool
    When the analyst previews <amendment> that Character on the Disabled List
    Then the preview shows its Violation <outcome>
    And the Player's Remaining Pool changes to <remaining>
    And the saved Series is unchanged
    Examples:
      | amendment | outcome | remaining |
      | adding | created | exclude that Character |
      | removing | cleared | include that Character |

  Scenario: Cancelling a preview leaves the Series unchanged
    Given an unsaved Disabled List amendment preview
    When the analyst cancels the preview
    Then the Series retains its original Disabled List and recorded Games

  Scenario: Explicitly saving applies the previewed amendment
    Given an unsaved rule amendment preview and an unchanged Workspace version
    When the analyst explicitly saves the amendment
    Then the Series uses the previewed rule settings and derived outcomes

  Scenario: An outdated preview cannot overwrite a newer edit
    Given a rule amendment preview followed by a saved Workspace edit
    When the analyst saves the outdated amendment
    Then the save is refused as outdated
    And the newer edit is retained

  Scenario: Reducing Best-of-5 to Best-of-3 at 2–0 previews an ended Series
    Given a Best-of-5 Series with two drafted Games won by Team A
    When the analyst previews Best-of-3
    Then the preview shows Series ended changing from no to yes
    And the saved Series remains Best-of-5

  Scenario: A format amendment keeps Games past the deciding Game
    Given a Best-of-5 Series with the first two Games won by Team A and a third Game started
    When the analyst previews Best-of-3
    Then the existing warning identifies Game 3 past deciding Game 2
    And all recorded Games are retained

  Scenario: A format with too few places is refused
    Given a Series with four non-voided Games including an unfinished draft
    When the analyst proposes Best-of-3
    Then the amendment is refused with the non-voided Game maximum error

