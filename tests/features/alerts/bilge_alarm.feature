Feature: Bilge water alarm
  As the boat owner, I want to be alerted whenever water is detected
  in the bilge so that I can respond before damage occurs.

  Background:
    Given the boat monitoring system is online
    And Kelly's "How's My Boat" card shows "Dry"

  @phase6 @critical @alerts
  Scenario: Bilge float switch triggers a notification
    When the bilge float switch reports water for 10 seconds
    Then within 30 seconds Home Assistant entity "binary_sensor.boatmon_bilge_water" should be "on"
    And Pete should receive a push notification containing "WATER DETECTED"
    And Kelly should receive a push notification containing "WATER DETECTED"
    And the home speakers should announce "Bilge water detected on the boat"
    And Kelly's "How's My Boat" card should show "WATER DETECTED" in red

  @phase6 @alerts
  Scenario: Brief float chatter does not trigger an alarm
    When the bilge float switch reports water for 2 seconds
    And the bilge float switch reports dry
    Then no bilge notification should be sent within 60 seconds
    And Kelly's "How's My Boat" card should still show "Dry"

  @phase6 @alerts @recovery
  Scenario: Bilge alarm clears when water recedes
    Given the bilge alarm is active
    When the bilge float switch reports dry for 5 minutes
    Then Home Assistant entity "binary_sensor.boatmon_bilge_water" should be "off"
    And Kelly's "How's My Boat" card should show "Dry"

  @phase6 @alerts @offline
  Scenario: Bilge alarm fires even if boat briefly disconnects
    Given the boat's MQTT connection has been offline for 2 minutes
    When the boat reconnects
    And the firmware replays a retained bilge-water event
    Then Pete should receive a push notification containing "WATER DETECTED"
