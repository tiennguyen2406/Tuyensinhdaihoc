"""Synthetic image media checks; real official assets are inspected privately."""

from io import BytesIO

import pytest
from PIL import Image

from services.crawler.downloader import media_type
from services.crawler.images import image_info
from services.crawler.transport import Response
from services.data.parsers.registry import extract
from tests.parsers.helpers import profile, snapshot


def response(data, mime):
    return Response("https://example.test/table", 200, {"content-type": mime}, data, 1)


def image(fmt, size=(20, 10)):
    stream = BytesIO()
    Image.new("RGB", size, "white").save(stream, format=fmt)
    return stream.getvalue()


@pytest.mark.parametrize("fmt,mime", [("PNG", "image/png"), ("JPEG", "image/jpeg")])
def test_verified_png_jpeg_mime(fmt, mime):
    assert media_type(response(image(fmt), mime)) == mime


@pytest.mark.parametrize(
    "body,mime",
    [
        (b"<html>error</html>", "image/png"),
        (image("PNG"), "image/jpeg"),
        (image("JPEG")[:30], "image/jpeg"),
        (b"<svg/>", "image/svg+xml"),
    ],
)
def test_image_corruption_spoof_and_active_formats_rejected(body, mime):
    with pytest.raises(ValueError):
        media_type(response(body, mime))


def test_excessive_image_pixels_rejected(monkeypatch):
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 100)
    with pytest.raises(ValueError):
        media_type(response(image("PNG", (20, 20)), "image/png"))


def test_image_dimensions_and_no_html_parser_fallback():
    data = image("PNG", (32, 48))
    assert image_info(data, "image/png") == dict(format="PNG", width=32, height=48)
    out = extract(snapshot(data, "image/png"), profile(), data)
    assert not out.observations
    assert "unsupported_media_type" in {i.code for i in out.issues}


def test_animated_png_not_accepted_as_static_table():
    stream = BytesIO()
    Image.new("RGB", (10, 10), "white").save(
        stream, format="PNG", save_all=True, append_images=[Image.new("RGB", (10, 10), "black")]
    )
    with pytest.raises(ValueError, match="image_format_or_pixel_limit"):
        image_info(stream.getvalue(), "image/png")
