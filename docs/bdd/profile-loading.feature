# Parent: BS-014 (US-021), issue #7 acceptance criteria
Feature: Title profile validation at application loading
  The application rejects broken Title profiles before they can break a Series.

  Scenario Outline: Loading a turn without its Draft Position or type reports the file and defect
    Given a Title rules file whose first turn lacks <field>
    When the application loads its Title profiles
    Then loading fails with the rules file name and the missing <field>

    Examples:
      | field    |
      | position |
      | kind     |

  Scenario: Loading a Draft Order with too few picks reports the file and defect
    Given a team size of 5 and a rules file with only 4 first-position picks
    When the application loads its Title profiles
    Then loading fails with the rules file name and a picks-per-Draft-Position defect

  Scenario: Loading duplicate Draft Order ids reports the file and defect
    Given a rules file with two Draft Orders sharing an id
    When the application loads its Title profiles
    Then loading fails with the rules file name and a duplicate Draft Order id defect

  Scenario: Loading a catalog missing a stored Character reports the file and defect
    Given a stored Series with a Draft Action using Orianna
    And its Title catalog no longer contains Orianna
    When the application loads its Title profiles
    Then loading fails with the catalog file name and the missing Character id Orianna

  # Issue #7 acceptance: validate MVP-used ADR-0016 fields.
  Scenario Outline: Loading malformed rules metadata reports the file and field
    Given a Title rules file with <defect>
    When the application loads its Title profiles
    Then loading fails with the rules file name and <field>

    Examples:
      | defect                       | field                |
      | an empty id                  | id                   |
      | an empty display name        | name                 |
      | unsupported format version 2 | format_version       |
      | team size 0                  | team_size            |
      | a string team size           | team_size            |
      | an empty Character label     | character_label      |
      | an empty Character Pool label| character_pool_label |
      | repeated Side names          | sides                |
      | an empty Side name           | sides                |
      | a string coupled flag        | sides_coupled        |

  Scenario Outline: Loading malformed Draft Orders or rule settings reports the file and field
    Given a Title rules file with <defect>
    When the application loads its Title profiles
    Then loading fails with the rules file name and <field>

    Examples:
      | defect                          | field                |
      | no Draft Orders                 | draft_orders         |
      | an unknown default Draft Order  | default_draft_order  |
      | an empty Draft Order id         | id                   |
      | an empty Draft Order name       | name                 |
      | unknown banning-locked policy   | banning_locked       |
      | unknown duplicate-character rule| same_character_twice |
      | a string Voided Games flag      | voided_games_count   |

  Scenario Outline: Loading malformed Character Catalog fields reports the file and defect
    Given a Character Catalog with <defect>
    When the application loads its Title profiles
    Then loading fails with the catalog file name and <field>

    Examples:
      | defect                     | field   |
      | an empty Character id      | id      |
      | an empty Character name    | name    |
      | an alias that is a number  | aliases |
      | a string Retired flag      | retired |
      | duplicate Character ids    | id      |

  Scenario: Editing files after loading leaves an active Series usable
    Given an application that has loaded its Title profile and recorded a Series
    And its rules file has since lost a turn's type
    When the application resumes the Series
    Then the Series remains readable using the already loaded profile

  Scenario: Loading a catalog with a Retired stored Character succeeds
    Given a stored Series with a Draft Action using Orianna
    And Orianna remains in the catalog marked Retired
    When the application loads its Title profiles
    Then the stored Series remains readable
