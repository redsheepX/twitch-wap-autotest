import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageStat
from selenium.webdriver.remote.webdriver import WebDriver

from twitch_wap.domain.models import Evidence


class SeleniumEvidenceWriter:
    def __init__(self, driver: WebDriver, artifacts_dir: Path) -> None:
        self._driver = driver
        self._artifacts_dir = artifacts_dir

    def capture(self, channel_url: str, label: str = "channel") -> Evidence:
        path = self._save_png(label, require_content=True)
        return Evidence(screenshot_path=path, channel_url=channel_url)

    def capture_failure(self, label: str, error: str) -> Path:
        screenshot_path = self._save_png(f"failure-{label}", require_content=False)
        metadata_path = screenshot_path.with_suffix(".json")
        metadata_path.write_text(
            json.dumps(
                {
                    "captured_at": datetime.now(UTC).isoformat(),
                    "current_url": self._driver.current_url,
                    "error": error,
                    "screenshot": screenshot_path.name,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return screenshot_path

    def _save_png(self, prefix: str, require_content: bool) -> Path:
        self._artifacts_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        path = self._artifacts_dir / f"{prefix}-{timestamp}-{uuid4().hex[:8]}.png"
        if not self._driver.save_screenshot(str(path)) or not path.exists() or path.stat().st_size == 0:
            raise RuntimeError(f"Unable to save screenshot evidence: {path}")
        if require_content and self._is_visually_blank(path):
            path.unlink(missing_ok=True)
            raise RuntimeError("Channel screenshot is visually blank.")
        return path

    @staticmethod
    def _is_visually_blank(path: Path) -> bool:
        with Image.open(path) as image:
            variance = max(ImageStat.Stat(image.convert("RGB")).var)
        return variance < 3
