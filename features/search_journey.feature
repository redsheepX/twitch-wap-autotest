@e2e
Feature: Discover a StarCraft II streamer on Twitch WAP
  To prove that the mobile web journey remains usable
  As a test operator
  I want to search, scroll, open a streamer, and retain screenshot evidence

  Scenario Outline: Search and open an available StarCraft II streamer
    Given the "<device_identifier>" mobile profile is selected
    And the Chrome mobile-emulation session is ready
    When I open Twitch WAP
    And I open the search interface
    And I search for "StarCraft II"
    And I scroll the search results twice
    And I select an available streamer
    Then the channel page becomes observable
    And a streamer metadata screenshot is retained as evidence

    Examples:
      | device_identifier |
      | pixel-7           |
      | iphone            |
      | samsung           |
