"""ASOS API wrapper for RapidAPI ASOS endpoints."""

from __future__ import annotations

from typing import Any, Dict, List
import os
import requests
import re

ASOS_API_HOST = os.getenv("RAPIDAPI_HOST", "asos2.p.rapidapi.com")
ASOS_SEARCH_URL = os.getenv(
    "RAPIDAPI_ASOS_BASE_URL",
    f"https://{ASOS_API_HOST}/products/v2/list",
)
DEFAULT_TIMEOUT = 10


_ASOS_SIZE_TOKEN_RE = re.compile(r"\$n_\d+w\$")
_ASOS_WID_RE = re.compile(r"([?&])wid=\d+")


def _force_small_asos_image(url: str, target_width: int = 320) -> str:
    if "images.asos-media.com" not in url:
        return url

    if "?" not in url:
        return f"{url}?$n_{target_width}w$&wid={target_width}&fit=constrain"

    updated = _ASOS_SIZE_TOKEN_RE.sub(f"$n_{target_width}w$", url)
    if updated == url and f"$n_{target_width}w$" not in updated:
        updated = f"{updated}&$n_{target_width}w$"

    if _ASOS_WID_RE.search(updated):
        updated = _ASOS_WID_RE.sub(rf"\\1wid={target_width}", updated)
    else:
        updated = f"{updated}&wid={target_width}"

    if "fit=" not in updated:
        updated = f"{updated}&fit=constrain"

    return updated


def _normalize_product(product: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize an ASOS product payload to the fields we care about.
    """
    image_url = (
        product.get("imageUrl")
        or product.get("image_url")
        or product.get("image")
        or None
    )
    image_template = product.get("imageUrlTemplate")
    if image_template and image_url:
        if "{imageUrl}" in image_template:
            image_url = image_template.replace("{imageUrl}", image_url)
        elif "{0}" in image_template:
            image_url = image_template.replace("{0}", image_url)
    elif image_template and not image_url:
        image_url = image_template

    if image_url:
        if image_url.startswith("//"):
            image_url = f"https:{image_url}"
        elif image_url.startswith("images.asos-media.com"):
            image_url = f"https://{image_url}"
        image_url = _force_small_asos_image(image_url)
    return {
        "id": product.get("id"),
        "name": product.get("name") or product.get("productName"),
        "image_url": image_url,
        "price": product.get("price"),
        "raw": product,
    }


def search_products(query: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Fetch products from ASOS via RapidAPI.
    Returns normalized product dictionaries.
    """
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        raise RuntimeError("RAPIDAPI_KEY is not set.")
    if "your_actual_rapidapi_key_here" in api_key:
        raise RuntimeError("RAPIDAPI_KEY is still a placeholder.")

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": ASOS_API_HOST,
        "User-Agent": "seasonal-color-matcher/0.1",
    }

    params = {
        "q": query,
        "store": "US",
        "country": "US",
        "lang": "en-US",
        "currency": "USD",
        "limit": str(limit),
        "offset": str(offset),
    }

    response = requests.get(
        ASOS_SEARCH_URL,
        headers=headers,
        params=params,
        timeout=DEFAULT_TIMEOUT,
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        status = response.status_code
        body = response.text[:500] if response.text else ""
        if status == 403:
            raise RuntimeError(
                "ASOS API 403 Forbidden. Verify your RapidAPI subscription, key, and host."
            ) from exc
        raise RuntimeError(f"ASOS API error {status}: {body}") from exc

    data = response.json()
    products = data.get("products", [])
    return [_normalize_product(product) for product in products]
