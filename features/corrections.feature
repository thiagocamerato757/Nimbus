# Parent: BS-010 / US-007; API seam with rule outcomes at the engine.
Feature: Corrections
  Late mistakes can be fixed without losing recorded information.

  Scenario: A correction that makes a later pick illegal flags it
    Given a legal pick in Game 3
    When the analyst corrects a Game 1 pick to the same Character under Hard Fearless
    Then the correction is saved, the Game 3 pick is unchanged and carries an Open Violation

  Scenario: A correction is kept in the edit history
    Given a recorded Draft Action
    When the analyst corrects it
    Then the edit history shows the change

  Scenario: An Open Violation can be acknowledged
    Given an Open Violation
    When the analyst acknowledges it with a reason
    Then it is an Acknowledged Violation carrying that reason

  Scenario: Removing the cause removes the Violation
    Given a Game 3 pick with a Violation caused by a Game 1 pick
    When the Game 1 pick is corrected to another Character
    Then the Violation no longer exists

  Scenario: An Acknowledged Violation reopens when its action or cause changes and it still breaks a rule
    Given an Acknowledged Violation
    When its cause changes and the action still breaks a rule
    Then the Violation is Open

  Scenario: Reversing a correction restores the acknowledgement
    Given a correction that reopened an Acknowledged Violation
    When the correction is reversed so that rule, action and cause match what was acknowledged
    Then the Violation is Acknowledged again with its original reason

  Scenario: The most recent Draft Action of the current Game can be cleared
    Given the current Game has recorded Draft Actions
    When the analyst clears the most recent one
    Then its turn is the current turn again and the edit history shows the clearing

  Scenario: An earlier Draft Action cannot be cleared
    Given the current Game has recorded Draft Actions
    When the analyst tries to clear one that is not the most recent
    Then nothing changes

  Scenario: Nothing can be cleared while the current Game has no actions
    Given Game 1 is Drafted and Game 2 is the current Game with no Draft Actions
    When the analyst tries to clear a Draft Action
    Then Game 1 is unchanged
