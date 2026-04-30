Feature: Engine telemetry publishes to canonical MQTT topics
  Engine running state, RPM, oil pressure, and coolant temp drive the
  underway dashboard tile and the runtime hour accumulator. The
  numeric topics use one-decimal formatting; engine_running is the
  same "1"/"0" boolean contract as shore power.

  Background:
    Given the boat is online

  @phase5 @telemetry
  Scenario: Engine off publishes "0" on the canonical running topic
    When the engine is reported off
    Then within 5 seconds MQTT topic "boat/hunter41/engine/running" equals "0"

  @phase5 @telemetry
  Scenario: Engine on publishes "1" on the canonical running topic
    When the engine is reported running
    Then within 5 seconds MQTT topic "boat/hunter41/engine/running" equals "1"

  @phase5 @telemetry
  Scenario: Idle RPM publishes the integer reading
    When the engine reports 850 RPM
    Then within 5 seconds MQTT topic "boat/hunter41/engine/rpm" equals "850"

  @phase5 @telemetry
  Scenario: Cruising RPM publishes the integer reading
    When the engine reports 2400 RPM
    Then within 5 seconds MQTT topic "boat/hunter41/engine/rpm" equals "2400"

  @phase5 @telemetry @critical
  Scenario: Hot coolant publishes a one-decimal reading
    When the engine coolant reports 95.5 C
    Then within 5 seconds MQTT topic "boat/hunter41/engine/coolant" equals "95.5"
