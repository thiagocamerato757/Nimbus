# Parent: BS-026, US-020; issue #6 and ADR-0033.
Feature: Local access protection and truthful tabs
  Other websites cannot change the Workspace, and outdated edits cannot overwrite
  the server's state while open tabs keep showing its latest changes.

  Scenario Outline: A request failing a local check is rejected without changes
    Given a state-changing request with <problem>
    When it reaches Nimbus
    Then the request is rejected
    And the Workspace remains unchanged

    Examples:
      | problem                      |
      | an unexpected Host           |
      | a foreign Origin             |
      | no custom application header |

  Scenario: An outdated edit is rejected without overwriting the Workspace
    Given two tabs based on the same Workspace version
    And one tab has saved a change
    When the other tab submits an edit based on the earlier version
    Then the edit is rejected
    And the saved change remains unchanged

  Scenario: Simultaneous edits based on one version accept only one change
    Given two tabs based on the same Workspace version
    When both tabs submit a Draft Action for the same Game simultaneously
    Then exactly one Draft Action is recorded
    And the other edit is rejected as outdated

  # Issue #6 acceptance: automatic updates and an analyst-visible stale notice.
  Scenario: A change in one tab appears automatically in another tab
    Given two tabs showing the same Series
    When one tab records a Draft Action
    Then the other tab shows the new Draft Action without a manual reload

  Scenario: An outdated prepared edit tells the analyst why it was rejected
    Given an analyst prepared a Draft Action before another tab saved a change
    When the analyst submits that prepared Draft Action
    Then Nimbus tells the analyst that the edit is outdated
    And the draft still shows only the saved change
