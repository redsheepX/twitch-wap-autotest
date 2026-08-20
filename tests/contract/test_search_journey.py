from pathlib import Path

import pytest

from twitch_wap.application import ChannelNotReady, SearchJourney
from twitch_wap.domain import ChannelReadiness, Evidence


class FakeTwitchUi:
    def __init__(self, observable: bool = True) -> None:
        self.calls: list[str] = []
        self._observable = observable
        self.channel_url = "https://www.twitch.tv/example_streamer"

    def open_home(self) -> None:
        self.calls.append("open_home")

    def open_search(self) -> None:
        self.calls.append("open_search")

    def search(self, query: str) -> None:
        self.calls.append(f"search:{query}")

    def scroll_results(self) -> None:
        self.calls.append("scroll_results")

    def select_streamer(self) -> str:
        self.calls.append("select_streamer")
        return self.channel_url

    def dismiss_known_interruptions(self) -> tuple[str, ...]:
        self.calls.append("dismiss_known_interruptions")
        return ()

    def wait_until_ready(self, channel_url: str) -> ChannelReadiness:
        self.calls.append(f"wait_until_ready:{channel_url}")
        return ChannelReadiness(channel_url, self._observable, False, True)


class FakeEvidence:
    def __init__(self) -> None:
        self.captured_urls: list[str] = []

    def capture(self, channel_url: str, label: str = "channel") -> Evidence:
        self.captured_urls.append(channel_url)
        return Evidence(Path(f"artifacts/{label}.png"), channel_url)

    def capture_failure(self, label: str, error: str) -> Path:
        return Path(f"artifacts/failure-{label}.png")


def test_journey_orchestrates_search_scroll_observation_and_evidence() -> None:
    ui = FakeTwitchUi()
    evidence = FakeEvidence()
    journey = SearchJourney(ui, ui, evidence)

    journey.open_twitch()
    journey.open_search()
    journey.search("StarCraft II")
    journey.scroll_results(2)
    channel_url = journey.select_streamer()
    journey.observe_channel(channel_url)
    result = journey.capture_channel_evidence(channel_url, "channel-metadata")

    assert ui.calls == [
        "open_home",
        "open_search",
        "search:StarCraft II",
        "scroll_results",
        "scroll_results",
        "select_streamer",
        "dismiss_known_interruptions",
        "wait_until_ready:https://www.twitch.tv/example_streamer",
    ]
    assert evidence.captured_urls == [channel_url]
    assert result.screenshot_path == Path("artifacts/channel-metadata.png")


def test_journey_refuses_to_capture_when_channel_is_not_observable() -> None:
    ui = FakeTwitchUi(observable=False)
    journey = SearchJourney(ui, ui, FakeEvidence())

    with pytest.raises(ChannelNotReady):
        journey.observe_channel(ui.channel_url)



@pytest.mark.parametrize("query", ["", "   "])
def test_journey_rejects_blank_search_terms(query: str) -> None:
    ui = FakeTwitchUi()
    journey = SearchJourney(ui, ui, FakeEvidence())

    with pytest.raises(ValueError, match="search query"):
        journey.search(query)
