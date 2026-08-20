import json

import pytest
from PIL import Image

from twitch_wap.infrastructure.evidence import SeleniumEvidenceWriter


class FakeDriver:
    current_url = "https://www.twitch.tv/example"

    def __init__(self, color: str = "purple") -> None:
        self._color = color

    def save_screenshot(self, path: str) -> bool:
        Image.new("RGB", (10, 10), self._color).save(path)
        return True


def test_failure_evidence_includes_screenshot_and_diagnostic_metadata(tmp_path) -> None:
    writer = SeleniumEvidenceWriter(FakeDriver(), tmp_path)

    screenshot = writer.capture_failure("search", "expected search results")
    metadata = json.loads(screenshot.with_suffix(".json").read_text(encoding="utf-8"))

    assert screenshot.exists()
    assert screenshot.stat().st_size > 0
    assert metadata["current_url"] == "https://www.twitch.tv/example"
    assert metadata["error"] == "expected search results"
    assert metadata["screenshot"] == screenshot.name


def test_channel_evidence_rejects_a_visually_blank_screenshot(tmp_path) -> None:
    writer = SeleniumEvidenceWriter(FakeDriver("white"), tmp_path)

    with pytest.raises(RuntimeError, match="visually blank"):
        writer.capture("https://www.twitch.tv/example")
