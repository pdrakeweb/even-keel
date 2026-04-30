Feature: Anchor drag alert (Phase 9)
  When the anchor is armed AND drift distance exceeds 30 m, the boat
  has dragged. The boat_alerts.yaml automation creates an
  anchor_drag persistent_notification. Recovery below 20 m or
  disarming the anchor clears it.

  Background:
    Given the boat is online

  @phase9 @alerts @critical @notification
  Scenario: Anchor armed with drift past 30m fires the anchor_drag alert
    When the anchor is armed at 45 m drift
    Then within 30 seconds HA entity "binary_sensor.boat_anchor_armed" equals "on"
    And within 30 seconds HA entity "sensor.boat_anchor_distance" equals "45.0"
    And within 15 seconds HA entity "persistent_notification.anchor_drag" is present

  @phase9 @alerts @recovery @notification
  Scenario: Drift recovering below 20m clears the alert
    Given the anchor is armed at 45 m drift
    And within 15 seconds HA entity "persistent_notification.anchor_drag" is present
    When the anchor is armed at 15 m drift
    Then within 30 seconds HA entity "sensor.boat_anchor_distance" equals "15.0"
    And within 60 seconds HA entity "persistent_notification.anchor_drag" is absent

  @phase9 @alerts @recovery @notification
  Scenario: Disarming the anchor clears any lingering drag alert
    Given the anchor is armed at 45 m drift
    And within 15 seconds HA entity "persistent_notification.anchor_drag" is present
    When the anchor is disarmed
    Then within 30 seconds HA entity "binary_sensor.boat_anchor_armed" equals "off"
    And within 60 seconds HA entity "persistent_notification.anchor_drag" is absent
