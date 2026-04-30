Feature: Anchor watch publishes armed-state + drift distance
  When the user "drops the hook" they tap the anchor-armed switch in
  HA, which publishes the armed flag and the current GPS coordinates
  as the anchor reference. Subsequent telemetry publishes the live
  drift distance — drift past the alarm radius fires the Phase 9
  anchor-drag alert.

  Background:
    Given the boat is online

  @phase9 @telemetry
  Scenario: Disarmed anchor publishes "0" on the canonical armed topic
    When the anchor is disarmed
    Then within 5 seconds MQTT topic "boat/hunter41/anchor/armed" equals "0"
    And within 5 seconds MQTT topic "boat/hunter41/anchor/distance_m" equals "0.0"

  @phase9 @telemetry
  Scenario: Armed anchor at zero drift publishes "1"
    When the anchor is armed at 0 m drift
    Then within 5 seconds MQTT topic "boat/hunter41/anchor/armed" equals "1"
    And within 5 seconds MQTT topic "boat/hunter41/anchor/distance_m" equals "0.0"

  @phase9 @telemetry @critical
  Scenario: Drifting past the alarm radius publishes a non-zero distance
    When the anchor is armed at 45 m drift
    Then within 5 seconds MQTT topic "boat/hunter41/anchor/armed" equals "1"
    And within 5 seconds MQTT topic "boat/hunter41/anchor/distance_m" equals "45.0"

  @phase9 @telemetry @recovery
  Scenario: Disarming clears the drift distance
    Given the anchor is armed at 22 m drift
    And within 5 seconds MQTT topic "boat/hunter41/anchor/armed" equals "1"
    When the anchor is disarmed
    Then within 5 seconds MQTT topic "boat/hunter41/anchor/armed" equals "0"
    And within 5 seconds MQTT topic "boat/hunter41/anchor/distance_m" equals "0.0"
