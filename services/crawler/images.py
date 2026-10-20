"""Bounded static PNG/JPEG validation; no OCR, rendering or source interpretation."""

import warnings
from io import BytesIO

from PIL import Image


def image_info(data: bytes, mime: str) -> dict[str, int | str]:
    formats = {"image/png": "PNG", "image/jpeg": "JPEG"}
    if mime not in formats or len(data) > 25 * 1024 * 1024:
        raise ValueError("image_type_or_size_limit")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as image:
                width, height = image.size
                if (
                    image.format != formats[mime]
                    or width * height > min(40_000_000, Image.MAX_IMAGE_PIXELS or 40_000_000)
                    or width > 16_384
                    or height > 16_384
                    or getattr(image, "n_frames", 1) != 1
                ):
                    raise ValueError("image_format_or_pixel_limit")
                image.verify()
            with Image.open(BytesIO(data)) as image:
                image.load()
        return dict(format=formats[mime], width=width, height=height)
    except (
        OSError,
        SyntaxError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as e:
        raise ValueError("invalid_or_oversized_image") from e
