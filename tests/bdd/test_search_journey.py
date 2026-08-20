from pytest_bdd import given, parsers, scenarios, then, when

from twitch_wap.infrastructure import MOBILE_DEVICE_PROFILES

scenarios("../../features/search_journey.feature")


@given(
    parsers.parse('the "{device_identifier}" mobile profile is selected'),
    target_fixture="device_identifier",
)
def select_mobile_profile(device_identifier: str) -> str:
    supported_profiles = {profile.identifier for profile in MOBILE_DEVICE_PROFILES}
    if device_identifier not in supported_profiles:
        raise ValueError(f"Unsupported mobile profile: {device_identifier}")
    return device_identifier


@given("the Chrome mobile-emulation session is ready")
def chrome_mobile_session_is_ready(journey):
    return journey


@when("I open Twitch WAP")
def open_twitch_wap(journey):
    journey.open_twitch()


@when("I open the search interface")
def open_search_interface(journey):
    journey.open_search()


@when(parsers.parse('I search for "{query}"'))
def search_for_query(journey, query: str):
    journey.search(query)


@when("I scroll the search results twice")
def scroll_search_results(journey):
    journey.scroll_results(2)


@when("I select an available streamer", target_fixture="channel_url")
def select_streamer(journey) -> str:
    return journey.select_streamer()


@then("the channel page becomes observable", target_fixture="channel_readiness")
def channel_page_becomes_observable(journey, channel_url: str):
    return journey.observe_channel(channel_url)


@then("a streamer metadata screenshot is retained as evidence")
def retain_streamer_metadata_screenshot(journey, channel_url: str, channel_readiness):
    assert channel_readiness.streamer_name_visible
    evidence = journey.capture_channel_evidence(channel_url, "channel-metadata")

    assert evidence.screenshot_path.exists()
    assert evidence.screenshot_path.stat().st_size > 0
