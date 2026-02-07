from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .constants import SEASONAL_PALETTES
from .services.asos_api import search_products
from .utils.color_engine import extract_dominant_color, is_seasonal_match


def index(request):
    seasons = sorted(SEASONAL_PALETTES.keys())
    return render(request, "matcher/index.html", {"seasons": seasons})


@require_http_methods(["GET", "POST"])
def search(request):
    query = (request.POST.get("query") or request.GET.get("query") or "").strip()
    season = (request.POST.get("season") or request.GET.get("season") or "").strip()

    seasons = sorted(SEASONAL_PALETTES.keys())
    results = []
    error = None

    if query and season in SEASONAL_PALETTES:
        try:
            products = search_products(query, limit=12)
        except Exception as exc:  # noqa: BLE001 - surfaces API errors to UI
            products = []
            error = f"ASOS API error: {exc}"

        palette = SEASONAL_PALETTES.get(season, [])

        for product in products[:15]:
            image_url = product.get("image_url")
            dominant_hex = None
            match = False
            if image_url:
                try:
                    dominant = extract_dominant_color(image_url)
                    dominant_hex = dominant.hex_value
                    match = is_seasonal_match(dominant_hex, palette)
                except Exception:
                    match = False

            results.append(
                {
                    "id": product.get("id"),
                    "name": product.get("name"),
                    "image_url": image_url,
                    "price": product.get("price"),
                    "dominant_hex": dominant_hex,
                    "is_match": match,
                }
            )
    elif query or season:
        error = "Please provide a search query and choose a season."

    context = {
        "query": query,
        "season": season,
        "seasons": seasons,
        "results": results,
        "error": error,
    }
    return render(request, "matcher/results.html", context)
