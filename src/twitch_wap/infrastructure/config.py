from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DeviceProfile:
    identifier: str
    viewport: tuple[int, int]
    pixel_ratio: float
    user_agent: str


MOBILE_DEVICE_PROFILES = (
    DeviceProfile(
        identifier="pixel-7",
        viewport=(412, 915),
        pixel_ratio=2.625,
        user_agent=(
            "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        ),
    ),
    DeviceProfile(
        identifier="iphone",
        viewport=(390, 844),
        pixel_ratio=3,
        user_agent=(
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 "
            "Mobile/15E148 Safari/604.1"
        ),
    ),
    DeviceProfile(
        identifier="samsung",
        viewport=(360, 800),
        pixel_ratio=3,
        user_agent=(
            "Mozilla/5.0 (Linux; Android 13; SM-S901B) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        ),
    ),
)


@dataclass(frozen=True)
class RuntimeSettings:
    base_url: str = "https://m.twitch.tv/?desktop-redirect=true"
    device_profile: DeviceProfile = MOBILE_DEVICE_PROFILES[0]
    timeout_seconds: int = 20
    artifacts_dir: Path = Path("artifacts")
    headless: bool = False
