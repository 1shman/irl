from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .constants import SEASONAL_PALETTES
from .services.asos_api import search_products
from .utils.color_engine import extract_dominant_color, find_best_season


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

    debug = (request.GET.get("debug") or request.POST.get("debug") or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    if query:
        try:
            products = search_products(query, limit=5)
        except Exception as exc:  # noqa: BLE001 - surfaces API errors to UI
            products = []
            error = f"ASOS API error: {exc}"

        for product in products:
            image_url = product.get("image_url")
            dominant_hex = None
            best_season = None
            best_distance = None
            debug_error = None
            if image_url:
                try:
                    dominant = extract_dominant_color(image_url)
                    dominant_hex = dominant.hex_value
                    best_season, best_distance = find_best_season(dominant_hex, SEASONAL_PALETTES)
                except Exception as exc:
                    best_season = None
                    best_distance = None
                    if debug:
                        debug_error = f"Color extraction failed: {exc}"
            else:
                if debug:
                    debug_error = "Missing image URL"

            results.append(
                {
                    "id": product.get("id"),
                    "name": product.get("name"),
                    "image_url": image_url,
                    "price": product.get("price"),
                    "dominant_hex": dominant_hex,
                    "best_season": best_season,
                    "best_distance": best_distance,
                    "debug_error": debug_error if debug else None,
                }
            )
    else:
        error = "Please provide a search query."

    context = {
        "query": query,
        "season": season,
        "seasons": seasons,
        "results": results,
        "error": error,
    }
    return render(request, "matcher/results.html", context)
