from io import BytesIO

from PIL import Image, ImageDraw

from twitch_wap.infrastructure.twitch_ui import TwitchWapUi


def _png_with_player_frame(black: bool) -> bytes:
    image = Image.new("RGB", (100, 100), "white")
    drawing = ImageDraw.Draw(image)
    drawing.rectangle((20, 20, 80, 80), fill="black" if black else "purple")
    if not black:
        drawing.line((20, 20, 80, 80), fill="white", width=3)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_black_player_region_is_not_a_visible_frame() -> None:
    has_pixels = TwitchWapUi._region_has_visible_pixels(
        _png_with_player_frame(black=True), 20, 20, 60, 60
    )

    assert has_pixels is False


def test_non_black_player_region_is_a_visible_frame() -> None:
    has_pixels = TwitchWapUi._region_has_visible_pixels(
        _png_with_player_frame(black=False), 20, 20, 60, 60
    )

    assert has_pixels is True
