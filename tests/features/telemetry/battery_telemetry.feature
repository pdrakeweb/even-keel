Feature: Battery + shore-power state publishes to canonical MQTT topics
  As the EvenKeel platform, the house battery's voltage / state of charge
  and the shore-power presence flag are the single most-watched values
  on the boat. The simulator and the boat firmware must both produce
  byte-identical payloads on the canonical topics so HA's rollup
  templates can't tell them apart.

  Background:
    Given the boat is online

  @phase4 @telemetry @critical
  Scenario: Healthy SoC publishes a numeric percentage with one decimal
    When the house battery reports 75% state of charge
    Then within 5 seconds MQTT topic "boat/hunter41/power/battery/house/soc" equals "75.0"

  @phase4 @telemetry @critical
  Scenario: Critical-low SoC fires the canonical low value
    When the house battery reports 18% state of charge
    Then within 5 seconds MQTT topic "boat/hunter41/power/battery/house/soc" equals "18.0"

  @phase4 @telemetry
  Scenario: House voltage publishes with two decimals
    When the house battery reports 12.45 volts
    Then within 5 seconds MQTT topic "boat/hunter41/power/battery/house/v" equals "12.45"

  @phase4 @telemetry
  Scenario: Shore power loss flips the canonical topic to 0
    Given shore power is connected
    And within 5 seconds MQTT topic "boat/hunter41/power/shore" equals "1"
    When shore power is disconnected
    Then within 5 seconds MQTT topic "boat/hunter41/power/shore" equals "0"
