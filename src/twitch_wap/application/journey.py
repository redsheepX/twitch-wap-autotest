from twitch_wap.application.ports import (
    ChannelObservationPort,
    EvidencePort,
    TwitchDiscoveryPort,
)
from twitch_wap.domain.models import ChannelReadiness, Evidence


class ChannelNotReady(RuntimeError):
    pass


class SearchJourney:
    """Application service for the business-level WAP discovery journey."""

    def __init__(
        self,
        discovery: TwitchDiscoveryPort,
        observation: ChannelObservationPort,
        evidence: EvidencePort,
    ) -> None:
        self._discovery = discovery
        self._observation = observation
        self._evidence = evidence

    def open_twitch(self) -> None:
        self._discovery.open_home()

    def open_search(self) -> None:
        self._discovery.open_search()

    def search(self, query: str) -> None:
        if not query.strip():
            raise ValueError("A search query is required.")
        self._discovery.search(query)

    def scroll_results(self, times: int) -> None:
        if times < 1:
            raise ValueError("Search results must be scrolled at least once.")
        for _ in range(times):
            self._discovery.scroll_results()

    def select_streamer(self) -> str:
        return self._discovery.select_streamer()

    def observe_channel(self, channel_url: str) -> ChannelReadiness:
        self._observation.dismiss_known_interruptions()
        readiness = self._observation.wait_until_ready(channel_url)
        if not readiness.observable:
            raise ChannelNotReady(
                f"Channel is not observable: {channel_url}. "
                f"main_content_visible={readiness.main_content_visible}, "
                f"blocking_interruption_present={readiness.blocking_interruption_present}, "
                f"streamer_name_visible={readiness.streamer_name_visible}"
            )
        return readiness

    def capture_channel_evidence(self, channel_url: str, label: str = "channel") -> Evidence:
        return self._evidence.capture(channel_url, label)
