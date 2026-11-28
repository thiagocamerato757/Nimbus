# Parent: BS-015 / US-010, issue #16; ADR-0014.
Feature: Disabled Lists and live Character Catalogs
  The analyst can manage temporary Series withdrawals without rewriting other
  Series, while permanently withdrawn Characters remain in historical records.

  Scenario: Viewing a pool excludes its Disabled Character
    Given a Player's Declared Pool contains Ahri and Akali
    And Ahri is on the Series Disabled List
    When the coach views that Player's pool
    Then only Akali is Remaining and Available Now

  Scenario: Entering a Disabled pick rejects a Game Rule break
    Given Ahri is on the Series Disabled List
    When the analyst enters a pick of Ahri without an Override
    Then the entry is rejected as a Game Rule break

  Scenario: Entering a Disabled pick with an Override acknowledges its Violation
    Given Ahri is on the Series Disabled List
    When the analyst enters a pick of Ahri with an official ruling Override
    Then the pick is recorded with an Acknowledged Violation

  Scenario: Creating a Series copies the Workspace Disabled List
    Given Ahri is on the Workspace Disabled List
    When the analyst creates a Series
    Then its Disabled List contains Ahri

  Scenario: Editing the Workspace Disabled List preserves an existing Series
    Given a Series was created with Ahri on its Disabled List
    When the analyst replaces the Workspace Disabled List with Akali
    Then the Series Disabled List still contains only Ahri

  Scenario: Editing the Series Disabled List changes its own list
    Given a Series has Ahri on its Disabled List
    When the analyst clears the Series Disabled List
    Then the Series Disabled List is empty

  Scenario: Retiring a Character preserves its historical entry
    Given a Game contains a recorded entry of Ahri
    When Ahri is marked Retired in the live Character Catalog
    Then the recorded entry still shows Ahri
    And Ahri is not offered for a new draft entry
