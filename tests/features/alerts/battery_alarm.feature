Feature: Low house-battery state-of-charge fires the boat_alerts notification
  When the house battery drops below 20% SoC, the production
  boat_alerts.yaml automation creates a persistent_notification.
  Recovery above 30% (5% hysteresis) clears it. This exercises the
  same MQTT → HA discovery → automation pipeline as bilge, against a
  numeric threshold rather than a binary state.

  Background:
    Given the boat is online

  @phase6 @alerts @critical @notification
  Scenario: SoC dropping under 20% creates the battery_low notification
    When the house battery reports 18% state of charge
    Then within 30 seconds HA entity "sensor.boat_house_battery_soc" equals "18.0"
    And within 15 seconds HA entity "persistent_notification.battery_low" is present

  @phase6 @alerts @recovery @notification
  Scenario: SoC recovering above 30% dismisses the battery_low notification
    Given the house battery reports 18% state of charge
    And within 15 seconds HA entity "persistent_notification.battery_low" is present
    When the house battery reports 35% state of charge
    Then within 30 seconds HA entity "sensor.boat_house_battery_soc" equals "35.0"
    And within 60 seconds HA entity "persistent_notification.battery_low" is absent
