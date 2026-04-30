Feature: Bilge water publishes to canonical MQTT topic
  As the EvenKeel platform, I need the bilge wet/dry signal to land on
  exactly the topic the dashboards and alert engine subscribe to. This
  is the data-plane contract the simulator and the boat firmware both
  honour.

  Background:
    Given the boat is online

  @phase1 @telemetry @critical
  Scenario: Bilge wet publishes "1" on the canonical topic
    When the bilge float switch reports water
    Then within 5 seconds MQTT topic "boat/hunter41/bilge/water_detected" equals "1"

  @phase1 @telemetry
  Scenario: Bilge dry publishes "0" on the canonical topic
    When the bilge float switch reports dry
    Then within 5 seconds MQTT topic "boat/hunter41/bilge/water_detected" equals "0"

  @phase1 @telemetry
  Scenario: Bilge wet→dry round-trip lands on the wire
    Given the bilge float switch reports water
    And within 5 seconds MQTT topic "boat/hunter41/bilge/water_detected" equals "1"
    When the bilge float switch reports dry
    Then within 5 seconds MQTT topic "boat/hunter41/bilge/water_detected" equals "0"
