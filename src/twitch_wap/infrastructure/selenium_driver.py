from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from .config import RuntimeSettings


class ChromeDriverFactory:
    """Creates Chrome drivers; Selenium Manager resolves a compatible driver."""

    def __init__(self, settings: RuntimeSettings) -> None:
        self._settings = settings

    def create(self) -> webdriver.Chrome:
        options = Options()
        profile = self._settings.device_profile
        width, height = profile.viewport
        options.add_experimental_option(
            "mobileEmulation",
            {
                "deviceMetrics": {
                    "width": width,
                    "height": height,
                    "pixelRatio": profile.pixel_ratio,
                    "mobile": True,
                },
                "userAgent": profile.user_agent,
            },
        )
        options.add_argument(f"--window-size={width},{height}")
        options.add_argument("--disable-notifications")
        options.add_argument("--autoplay-policy=no-user-gesture-required")
        if self._settings.headless:
            options.add_argument("--headless=new")
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(self._settings.timeout_seconds)
        return driver
