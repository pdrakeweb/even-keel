Feature: AIS targets list publishes as canonical JSON
  The dashboard's iteration card subscribes to a single topic that
  carries the full target list as a JSON array. Each target has the
  same key shape regardless of source (firmware UART, simulator,
  cloud relay).

  Background:
    Given the boat is online

  @phase1 @ais @telemetry
  Scenario: No targets in range publishes an empty JSON array
    When zero AIS targets are reported
    Then within 5 seconds MQTT topic "boat/hunter41/ais/targets" parses as a JSON array of 0 items
    And within 5 seconds MQTT topic "boat/hunter41/ais/targets_in_range" equals "0"

  @phase1 @ais @telemetry
  Scenario: A single Class B target lands with the canonical key shape
    When a Class B target named "GULL" at 1.2 nm is reported
    Then within 5 seconds MQTT topic "boat/hunter41/ais/targets" parses as a JSON array of 1 items
    And the first AIS target on that topic has key "mmsi"
    And the first AIS target on that topic has key "name"
    And the first AIS target on that topic has key "range_nm"
    And within 5 seconds MQTT topic "boat/hunter41/ais/targets_in_range" equals "1"
    And within 5 seconds MQTT topic "boat/hunter41/ais/nearest_name" equals "GULL"

  @phase1 @ais @telemetry
  Scenario: Multiple targets nominate the closest as nearest
    When 3 AIS targets are reported at ranges 5.0 4.0 0.7 nm
    Then within 5 seconds MQTT topic "boat/hunter41/ais/targets" parses as a JSON array of 3 items
    And within 5 seconds MQTT topic "boat/hunter41/ais/targets_in_range" equals "3"
    And within 5 seconds MQTT topic "boat/hunter41/ais/nearest_range_nm" equals "0.70"
