Feature: Bilge water flips the HA binary_sensor through MQTT discovery
  When the simulator (or boat firmware) publishes "1" on the canonical
  bilge topic, HA's MQTT-discovery-registered binary_sensor must flip
  to "on" within seconds. This is the data plane → HA half of the full
  bilge-alarm critical path; the notification half lives in
  bilge_alarm.feature pending Pushover/Sonos test fixtures.

  Background:
    Given the boat is online

  @phase6 @alerts @critical
  Scenario: Bilge wet flips binary_sensor.boat_bilge_water_detected to on
    When the bilge float switch reports water
    Then within 5 seconds MQTT topic "boat/hunter41/bilge/water_detected" equals "1"
    And within 30 seconds HA entity "binary_sensor.boat_bilge_water_detected" equals "on"

  @phase6 @alerts @recovery
  Scenario: Clearing the bilge resets the HA binary_sensor to off
    Given the bilge float switch reports water
    And within 5 seconds MQTT topic "boat/hunter41/bilge/water_detected" equals "1"
    When the bilge float switch reports dry
    Then within 5 seconds MQTT topic "boat/hunter41/bilge/water_detected" equals "0"
    And within 30 seconds HA entity "binary_sensor.boat_bilge_water_detected" equals "off"

  @phase6 @alerts @critical @rollup
  Scenario: Bilge wet flips the boat_bilge_status template rollup to critical
    When the bilge float switch reports water
    Then within 30 seconds HA entity "binary_sensor.boat_bilge_water_detected" equals "on"
    And within 30 seconds HA entity "sensor.boat_bilge_status" equals "critical"

  @phase6 @alerts @rollup
  Scenario: Clearing the bilge restores boat_bilge_status to ok
    Given the bilge float switch reports water
    And within 30 seconds HA entity "sensor.boat_bilge_status" equals "critical"
    When the bilge float switch reports dry
    Then within 30 seconds HA entity "binary_sensor.boat_bilge_water_detected" equals "off"
    And within 30 seconds HA entity "sensor.boat_bilge_status" equals "ok"

  @phase6 @alerts @critical @notification
  Scenario: Bilge wet fires the boat_alerts automation that creates a persistent_notification
    When the bilge float switch reports water
    Then within 30 seconds HA entity "binary_sensor.boat_bilge_water_detected" equals "on"
    And within 15 seconds HA entity "persistent_notification.bilge_water" is present
