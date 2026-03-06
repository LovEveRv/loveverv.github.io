#!/usr/bin/env python3
"""Convert PNG/JPEG image from local file or URL to WebP with optional resize limits."""

from __future__ import annotations

import argparse
from io import BytesIO
from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import urlopen

from PIL import Image


SUPPORTED_FORMATS = {"PNG", "JPEG"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read a local image or image URL, optionally resize, then convert to WebP."
    )

    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("-f", "--file", dest="file_path", help="Input local image file")
    source_group.add_argument("-w", "--web", dest="url", help="Input image URL")

    parser.add_argument(
        "-o",
        "--output",
        dest="output_name",
        default=None,
        help="Output filename (default: inferred from source name)",
    )
    parser.add_argument("--max-width", type=int, default=None, help="Maximum output width")
    parser.add_argument("--max-height", type=int, default=None, help="Maximum output height")

    args = parser.parse_args()

    if args.max_width is not None and args.max_width <= 0:
        parser.error("--max-width must be a positive integer")
    if args.max_height is not None and args.max_height <= 0:
        parser.error("--max-height must be a positive integer")

    return args


def infer_stem_from_url(url: str) -> str:
    parsed = urlparse(url)
    name = Path(unquote(parsed.path)).name
    if not name:
        return "output"
    stem = Path(name).stem
    return stem or "output"


def infer_output_path(output_name: str | None, file_path: str | None, url: str | None) -> Path:
    if output_name:
        out = Path(output_name)
    elif file_path:
        out = Path(file_path).name
        out = Path(out).with_suffix(".webp")
    elif url:
        out = Path(infer_stem_from_url(url)).with_suffix(".webp")
    else:
        raise ValueError("Either file path or URL must be provided")

    if out.suffix.lower() != ".webp":
        out = out.with_suffix(".webp")

    return out


def open_image_from_file(file_path: str) -> Image.Image:
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")
    return Image.open(path)


def open_image_from_url(url: str) -> Image.Image:
    with urlopen(url, timeout=15) as response:
        image_bytes = response.read()
    return Image.open(BytesIO(image_bytes))


def validate_image_format(image: Image.Image) -> None:
    if image.format not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported input format: {image.format}. Only PNG and JPEG are supported."
        )


def resize_image(image: Image.Image, max_width: int | None, max_height: int | None) -> Image.Image:
    width, height = image.size

    scale_factors = [1.0]
    if max_width is not None:
        scale_factors.append(max_width / width)
    if max_height is not None:
        scale_factors.append(max_height / height)

    scale = min(scale_factors)

    # Keep aspect ratio and avoid enlarging image.
    if scale < 1.0:
        new_width = max(1, int(width * scale))
        new_height = max(1, int(height * scale))
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    return image


def convert_to_webp(image: Image.Image, output_path: Path) -> None:
    # Convert to RGB if needed for WebP output consistency.
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGB")
    image.save(output_path, format="WEBP")


def main() -> None:
    args = parse_args()

    output_path = infer_output_path(args.output_name, args.file_path, args.url)

    if args.file_path:
        image = open_image_from_file(args.file_path)
    else:
        image = open_image_from_url(args.url)

    with image:
        validate_image_format(image)
        resized = resize_image(image, args.max_width, args.max_height)
        convert_to_webp(resized, output_path)

    print(f"Saved: {output_path.resolve()}")


if __name__ == "__main__":
    main()
