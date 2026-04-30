Feature: Leak detection per zone publishes to canonical topics
  Three leak sensors (head, galley, engine bay) each publish to their
  own boat/hunter41/leak/<zone> topic. Like bilge, they're "1"/"0"
  booleans driven by GPIO contacts on the firmware side and equivalent
  payload bytes from the simulator.

  Background:
    Given the boat is online

  @phase6 @telemetry @critical
  Scenario: Head leak publishes "1" on the canonical head topic
    When the head reports a water leak
    Then within 5 seconds MQTT topic "boat/hunter41/leak/head" equals "1"

  @phase6 @telemetry @critical
  Scenario: Galley leak publishes "1" on the canonical galley topic
    When the galley reports a water leak
    Then within 5 seconds MQTT topic "boat/hunter41/leak/galley" equals "1"

  @phase6 @telemetry @critical
  Scenario: Engine bay leak publishes "1" on the canonical engine topic
    When the engine bay reports a water leak
    Then within 5 seconds MQTT topic "boat/hunter41/leak/engine" equals "1"

  @phase6 @telemetry
  Scenario: Cleared head leak publishes "0"
    Given the head reports a water leak
    And within 5 seconds MQTT topic "boat/hunter41/leak/head" equals "1"
    When the head leak clears
    Then within 5 seconds MQTT topic "boat/hunter41/leak/head" equals "0"
