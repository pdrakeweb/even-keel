Feature: Shore power loss alert (Phase 6)
  Shore power dropping while at the slip is the early warning that
  charging has stopped — battery bank goes from "trickling up
  forever" to "draining on its own clock." The boat_alerts.yaml
  automation creates a persistent_notification on cross-down and
  dismisses on restoration.

  Background:
    Given the boat is online

  @phase6 @alerts @critical @notification
  Scenario: Shore power dropping fires the shore_power_lost alert
    Given shore power is connected
    And within 30 seconds HA entity "binary_sensor.boat_shore_power" equals "on"
    When shore power is disconnected
    Then within 30 seconds HA entity "binary_sensor.boat_shore_power" equals "off"
    And within 15 seconds HA entity "persistent_notification.shore_power_lost" is present

  @phase6 @alerts @recovery @notification
  Scenario: Shore power restoration clears the alert
    Given shore power is disconnected
    And within 15 seconds HA entity "persistent_notification.shore_power_lost" is present
    When shore power is connected
    Then within 30 seconds HA entity "binary_sensor.boat_shore_power" equals "on"
    And within 60 seconds HA entity "persistent_notification.shore_power_lost" is absent
