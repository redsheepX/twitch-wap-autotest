from collections.abc import Iterable
from io import BytesIO
from typing import ClassVar
from urllib.parse import urlparse

from PIL import Image, ImageStat
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait

from twitch_wap.domain.models import ChannelReadiness

from .config import RuntimeSettings


class TwitchWapUi:
    """Selenium adapter for Twitch WAP. Locators live only in this adapter."""

    _SEARCH_BUTTONS = (
        "button[data-a-target='search-button']",
        "button[aria-label*='Search']",
        "button[aria-label*='搜尋']",
    )
    _SEARCH_INPUTS = (
        "input[data-a-target='search-input']",
        "input[role='searchbox']",
        "input[type='search']",
        "input[aria-label*='Search']",
        "input[aria-label*='搜尋']",
    )
    _KNOWN_INTERRUPTION_CLOSES: ClassVar[dict[str, tuple[str, ...]]] = {
        "cookie-consent": (
            "button[data-a-target='consent-banner-accept']",
            "button[data-a-target='consent-banner-close']",
        ),
        "generic-modal": (
            "button[data-a-target='modal-close-button']",
            "[role='dialog'] button[aria-label='Close']",
            "[role='dialog'] button[aria-label='關閉']",
        ),
        "app-redirect": (
            "button[data-a-target='mweb-continue-in-browser']",
            "button[data-a-target='continue-in-browser']",
        ),
    }
    _READY_SELECTORS = ("main",)
    _CHANNEL_METADATA_BUTTONS = (
        "button[data-a-target='channel-metadata-button']",
        "button[aria-label*='channel metadata']",
        "button[aria-label*='頻道中繼資料']",
    )
    _NON_CHANNEL_PATHS = frozenset(
        {
            "",
            "activity",
            "creatorcamp",
            "directory",
            "downloads",
            "home",
            "login",
            "p",
            "search",
            "settings",
            "signup",
            "turbo",
            "wallet",
        }
    )

    def __init__(self, driver: WebDriver, settings: RuntimeSettings) -> None:
        self._driver = driver
        self._settings = settings
        self._wait = WebDriverWait(driver, settings.timeout_seconds)

    def open_home(self) -> None:
        self._driver.get(self._settings.base_url)
        self._wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")

    def open_search(self) -> None:
        self.dismiss_known_interruptions()
        button = self._first_visible(self._SEARCH_BUTTONS)
        if button is not None:
            button.click()
        if self._wait_for_search_input(seconds=3):
            return
        self._open_mobile_browse_page()
        self._wait.until(lambda _: self._first_visible(self._SEARCH_INPUTS) is not None)

    def search(self, query: str) -> None:
        input_element = self._wait.until(lambda _: self._first_visible(self._SEARCH_INPUTS))
        input_element.clear()
        input_element.send_keys(query, Keys.ENTER)
        self._wait.until(lambda driver: "search" in driver.current_url.lower())

    def scroll_results(self) -> None:
        before, after, maximum = self._driver.execute_script(
            """
            const before = window.pageYOffset;
            const maximum = Math.max(0, document.documentElement.scrollHeight - window.innerHeight);
            window.scrollBy(0, Math.max(1, window.innerHeight * 0.3));
            return [before, window.pageYOffset, maximum];
            """
        )
        if before < maximum and after <= before:
            raise RuntimeError("Search results did not move while scrollable content remained.")

    def select_streamer(self) -> str:
        streamer = self._wait.until(lambda _: self._first_streamer_link())
        previous_url = self._driver.current_url
        try:
            streamer.click()
        except ElementClickInterceptedException as error:
            raise RuntimeError("A UI overlay blocked streamer selection.") from error
        self._wait.until(lambda driver: driver.current_url != previous_url)
        return self._driver.current_url

    def dismiss_known_interruptions(self) -> tuple[str, ...]:
        dismissed: list[str] = []
        for name, selectors in self._KNOWN_INTERRUPTION_CLOSES.items():
            element = self._first_visible(selectors)
            if element is None:
                continue
            try:
                self._click(element)
                dismissed.append(name)
            except ElementClickInterceptedException:
                continue
        browser_continue = self._first_visible_xpath(
            "//*[self::button or self::a][contains(normalize-space(), 'Continue using browser') "
            "or contains(normalize-space(), '繼續使用網頁版')]"
        )
        if browser_continue is not None:
            self._click(browser_continue)
            dismissed.append("app-redirect")
        return tuple(dismissed)

    def wait_until_ready(self, channel_url: str) -> ChannelReadiness:
        if not self._is_channel_url(channel_url):
            return ChannelReadiness(
                channel_url=channel_url,
                main_content_visible=False,
                blocking_interruption_present=True,
                streamer_name_visible=False,
            )
        self._wait.until(lambda driver: driver.current_url == channel_url)
        channel_name = urlparse(channel_url).path.strip("/").lower()
        self._wait.until(
            lambda driver: self._first_visible(self._READY_SELECTORS) is not None
            and channel_name in driver.execute_script(
                "return (document.body?.innerText || '').toLowerCase();"
            )
            and self._player_has_visible_frame()
        )
        self._reveal_channel_metadata()
        self._wait.until(lambda _: self._streamer_name_is_visible(channel_name))
        self._neutralize_metadata_backdrop()
        self._wait.until(lambda _: self._metadata_backdrops_are_transparent())
        blocking = any(
            self._first_visible(selectors) is not None
            for selectors in self._KNOWN_INTERRUPTION_CLOSES.values()
        )
        return ChannelReadiness(
            channel_url=channel_url,
            main_content_visible=True,
            blocking_interruption_present=blocking,
            streamer_name_visible=self._streamer_name_is_visible(channel_name),
        )

    def _first_visible(self, selectors: Iterable[str]) -> WebElement | None:
        for selector in selectors:
            try:
                element = self._driver.find_element(By.CSS_SELECTOR, selector)
            except NoSuchElementException:
                continue
            if element.is_displayed():
                return element
        return None

    def _first_visible_xpath(self, selector: str) -> WebElement | None:
        try:
            element = self._driver.find_element(By.XPATH, selector)
        except NoSuchElementException:
            return None
        return element if element.is_displayed() else None

    def _click(self, element: WebElement) -> None:
        try:
            element.click()
        except ElementClickInterceptedException:
            self._driver.execute_script("arguments[0].click();", element)

    def _wait_for_search_input(self, seconds: int) -> bool:
        short_wait = WebDriverWait(self._driver, seconds)
        try:
            short_wait.until(lambda _: self._first_visible(self._SEARCH_INPUTS) is not None)
        except TimeoutException:
            return False
        return True

    def _open_mobile_browse_page(self) -> None:
        browse_link = self._first_visible(("a[href='/directory']",))
        if browse_link is not None:
            self._click(browse_link)
        else:
            self._driver.get("https://m.twitch.tv/directory")
        self._wait.until(lambda driver: "/directory" in urlparse(driver.current_url).path)

    def _reveal_channel_metadata(self) -> None:
        metadata_button = self._first_visible(self._CHANNEL_METADATA_BUTTONS)
        if metadata_button is not None:
            self._click(metadata_button)

    def _neutralize_metadata_backdrop(self) -> None:
        """Keeps Twitch metadata intact while making only its visual scrim transparent."""
        self._driver.execute_script(
            """
            for (const backdrop of document.querySelectorAll("[class*='ModalBackdrop']")) {
                const rect = backdrop.getBoundingClientRect();
                const color = getComputedStyle(backdrop).backgroundColor;
                if (rect.width >= innerWidth * 0.95 && rect.height >= innerHeight * 0.95
                    && color !== 'rgba(0, 0, 0, 0)') {
                    backdrop.style.setProperty('background-color', 'transparent', 'important');
                }
            }
            """
        )

    def _metadata_backdrops_are_transparent(self) -> bool:
        return self._driver.execute_script(
            """
            const fullScreenBackdrops = Array.from(
                document.querySelectorAll("[class*='ModalBackdrop']")
            ).filter((backdrop) => {
                const rect = backdrop.getBoundingClientRect();
                return rect.width >= innerWidth * 0.95 && rect.height >= innerHeight * 0.95;
            });
            return fullScreenBackdrops.every(
                (backdrop) => getComputedStyle(backdrop).backgroundColor === 'rgba(0, 0, 0, 0)'
            );
            """
        )

    def _streamer_name_is_visible(self, channel_name: str) -> bool:
        return self._driver.execute_script(
            """
            const channelName = arguments[0];
            return Array.from(document.querySelectorAll('button')).some((button) => {
                const rect = button.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0
                    && rect.top >= 0 && rect.bottom <= window.innerHeight
                    && button.innerText.toLowerCase().includes(channelName);
            });
            """,
            channel_name,
        )

    def _player_has_visible_frame(self) -> bool:
        state = self._driver.execute_script(
            """
            const video = document.querySelector('video');
            if (!video) return null;
            const rect = video.getBoundingClientRect();
            return {
                hasFrame: video.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA
                    && !video.paused
                    && video.currentTime > 0
                    && video.videoWidth > 0
                    && video.videoHeight > 0,
                x: rect.x,
                y: rect.y,
                width: rect.width,
                height: rect.height,
            };
            """
        )
        if not state or not state["hasFrame"]:
            return False
        return self._region_has_visible_pixels(
            self._driver.get_screenshot_as_png(),
            state["x"],
            state["y"],
            state["width"],
            state["height"],
        )

    @staticmethod
    def _region_has_visible_pixels(
        screenshot: bytes, x: float, y: float, width: float, height: float
    ) -> bool:
        with Image.open(BytesIO(screenshot)).convert("RGB") as image:
            left = max(0, int(x))
            top = max(0, int(y))
            right = min(image.width, int(x + width))
            bottom = min(image.height, int(y + height))
            if right <= left or bottom <= top:
                return False
            statistics = ImageStat.Stat(image.crop((left, top, right, bottom)))
            brightness = max(statistics.mean)
            variance = max(statistics.var)
        return brightness >= 8 and variance >= 3

    def _first_streamer_link(self) -> WebElement | None:
        for element in self._driver.find_elements(By.CSS_SELECTOR, "main button"):
            if not element.is_displayed():
                continue
            if element.find_elements(By.CSS_SELECTOR, "h2"):
                return element
        return None

    def _is_channel_url(self, href: str) -> bool:
        parsed = urlparse(href)
        if parsed.netloc not in {"www.twitch.tv", "twitch.tv", "m.twitch.tv"}:
            return False
        path_parts = [part for part in parsed.path.split("/") if part]
        return len(path_parts) == 1 and path_parts[0].lower() not in self._NON_CHANNEL_PATHS
