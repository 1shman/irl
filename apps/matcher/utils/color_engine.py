"""Color extraction and matching utilities."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable, Tuple

import cv2
import numpy as np
import requests
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie1976
from colormath.color_objects import LabColor, sRGBColor
from sklearn.cluster import KMeans


@dataclass(frozen=True)
class DominantColorResult:
    hex_value: str
    rgb: Tuple[int, int, int]


def _normalize_hex(value: str) -> str:
    value = value.strip().lstrip("#")
    if len(value) != 6:
        raise ValueError(f"Invalid hex color: {value!r}")
    return f"#{value.upper()}"


def _rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def _hex_to_rgb(hex_value: str) -> Tuple[int, int, int]:
    normalized = _normalize_hex(hex_value)
    return tuple(int(normalized[i : i + 2], 16) for i in (1, 3, 5))


@lru_cache(maxsize=256)
def _download_image_bytes(url: str) -> bytes:
    response = requests.get(
        url,
        timeout=10,
        headers={"User-Agent": "seasonal-color-matcher/0.1"},
    )
    response.raise_for_status()
    return response.content


def _decode_image(image_bytes: bytes) -> np.ndarray:
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Unable to decode image bytes")
    return image


def _center_crop(image: np.ndarray, crop_ratio: float = 0.5) -> np.ndarray:
    height, width = image.shape[:2]
    crop_h = int(height * crop_ratio)
    crop_w = int(width * crop_ratio)
    start_y = (height - crop_h) // 2
    start_x = (width - crop_w) // 2
    return image[start_y : start_y + crop_h, start_x : start_x + crop_w]


def _kmeans_primary_color(pixels: np.ndarray, k: int = 3) -> Tuple[int, int, int]:
    kmeans = KMeans(n_clusters=k, n_init="auto", random_state=42)
    labels = kmeans.fit_predict(pixels)
    counts = np.bincount(labels)
    dominant_index = int(np.argmax(counts))
    dominant_color = kmeans.cluster_centers_[dominant_index]
    rgb = tuple(int(round(c)) for c in dominant_color)
    return rgb


@lru_cache(maxsize=256)
def extract_dominant_color(url: str) -> DominantColorResult:
    image_bytes = _download_image_bytes(url)
    image = _decode_image(image_bytes)

    resized = cv2.resize(image, (200, 200), interpolation=cv2.INTER_AREA)
    cropped = _center_crop(resized, crop_ratio=0.5)

    # OpenCV loads as BGR; convert to RGB for consistency
    rgb_image = cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB)
    pixels = rgb_image.reshape((-1, 3))

    dominant_rgb = _kmeans_primary_color(pixels, k=3)
    dominant_hex = _rgb_to_hex(dominant_rgb)
    return DominantColorResult(hex_value=dominant_hex, rgb=dominant_rgb)


def calculate_delta_e(hex1: str, hex2: str) -> float:
    rgb1 = _hex_to_rgb(hex1)
    rgb2 = _hex_to_rgb(hex2)

    lab1 = convert_color(sRGBColor(*rgb1, is_upscaled=True), LabColor)
    lab2 = convert_color(sRGBColor(*rgb2, is_upscaled=True), LabColor)

    return float(delta_e_cie1976(lab1, lab2))


def is_seasonal_match(extracted_hex: str, palette_hexes: Iterable[str], threshold: float = 10.0) -> bool:
    extracted_hex = _normalize_hex(extracted_hex)
    for palette_hex in palette_hexes:
        if calculate_delta_e(extracted_hex, palette_hex) < threshold:
            return True
    return False
