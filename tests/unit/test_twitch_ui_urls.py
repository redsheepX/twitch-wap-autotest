from twitch_wap.infrastructure.twitch_ui import TwitchWapUi


def test_mobile_streamer_path_is_a_channel_url() -> None:
    ui = object.__new__(TwitchWapUi)

    assert ui._is_channel_url("https://m.twitch.tv/example_streamer") is True


def test_mobile_navigation_path_is_not_a_channel_url() -> None:
    ui = object.__new__(TwitchWapUi)

    assert ui._is_channel_url("https://m.twitch.tv/activity") is False
