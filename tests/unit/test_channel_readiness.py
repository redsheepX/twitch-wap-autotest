from twitch_wap.domain import ChannelReadiness


def test_channel_is_observable_only_when_main_content_is_visible_and_unblocked() -> None:
    ready = ChannelReadiness(
        channel_url="https://www.twitch.tv/example",
        main_content_visible=True,
        blocking_interruption_present=False,
        streamer_name_visible=True,
    )
    blocked = ChannelReadiness(
        channel_url="https://www.twitch.tv/example",
        main_content_visible=True,
        blocking_interruption_present=True,
        streamer_name_visible=True,
    )

    assert ready.observable is True
    assert blocked.observable is False
