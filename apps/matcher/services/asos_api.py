"""ASOS API wrapper for RapidAPI ASOS endpoints."""

from __future__ import annotations

from typing import Any, Dict, List
import os
import requests

ASOS_API_HOST = "asos2.p.rapidapi.com"
ASOS_SEARCH_URL = f"https://{ASOS_API_HOST}/products/v2/list"
DEFAULT_TIMEOUT = 10


def _normalize_product(product: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize an ASOS product payload to the fields we care about.
    """
    image_url = (
        product.get("imageUrl")
        or product.get("image_url")
        or product.get("image")
        or product.get("imageUrlTemplate")
    )
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

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": ASOS_API_HOST,
    }

    params = {
        "q": query,
        "store": "US",
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
    response.raise_for_status()
    data = response.json()
    products = data.get("products", [])
    return [_normalize_product(product) for product in products]
