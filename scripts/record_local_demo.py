"""Record the Pixel 7 Twitch WAP journey as the GIF embedded in the README."""

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw

from twitch_wap.infrastructure import (
    MOBILE_DEVICE_PROFILES,
    ChromeDriverFactory,
    RuntimeSettings,
    TwitchWapUi,
)


def _pixel_7_settings(project_root: Path) -> RuntimeSettings:
    profile = next(profile for profile in MOBILE_DEVICE_PROFILES if profile.identifier == "pixel-7")
    return RuntimeSettings(
        device_profile=profile,
        artifacts_dir=project_root / "artifacts",
        headless=False,
    )


def _capture_frame(driver, label: str) -> Image.Image:
    with Image.open(BytesIO(driver.get_screenshot_as_png())).convert("RGB") as screenshot:
        frame = Image.new("RGB", (screenshot.width, screenshot.height + 96), "white")
        frame.paste(screenshot, (0, 96))
    ImageDraw.Draw(frame).text((32, 28), label, fill="black", font_size=36)
    frame.thumbnail((360, 800), Image.Resampling.LANCZOS)
    return frame


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    output_path = project_root / "docs" / "local-e2e-demo.gif"
    output_path.parent.mkdir(exist_ok=True)

    settings = _pixel_7_settings(project_root)
    driver = ChromeDriverFactory(settings).create()
    ui = TwitchWapUi(driver, settings)
    frames: list[Image.Image] = []
    try:
        ui.open_home()
        frames.append(_capture_frame(driver, "1. Open Twitch WAP"))
        ui.open_search()
        frames.append(_capture_frame(driver, "2. Open search"))
        ui.search("StarCraft II")
        frames.append(_capture_frame(driver, "3. Search StarCraft II"))
        ui.scroll_results()
        ui.scroll_results()
        frames.append(_capture_frame(driver, "4. Scroll results twice"))
        channel_url = ui.select_streamer()
        ui.wait_until_ready(channel_url)
        frames.append(_capture_frame(driver, "5. Open streamer and retain evidence"))
    finally:
        driver.quit()

    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=1200,
        loop=0,
        optimize=True,
    )
    print(f"Recorded local demo: {output_path}")


if __name__ == "__main__":
    main()
