from twitch_wap.infrastructure.config import MOBILE_DEVICE_PROFILES


def test_supported_device_profiles_cover_the_requested_iphone_and_samsung_viewports() -> None:
    profiles = {profile.identifier: profile for profile in MOBILE_DEVICE_PROFILES}

    assert profiles["pixel-7"].viewport == (412, 915)
    assert profiles["iphone"].viewport == (390, 844)
    assert profiles["samsung"].viewport == (360, 800)
    assert set(profiles) == {"pixel-7", "iphone", "samsung"}
    assert profiles["pixel-7"].user_agent
    assert profiles["iphone"].user_agent
    assert profiles["samsung"].user_agent
