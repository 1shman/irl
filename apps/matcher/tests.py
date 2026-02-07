from unittest.mock import Mock, patch
import os

from django.test import Client, SimpleTestCase
from django.urls import reverse

from .services.asos_api import search_products
from .utils import color_engine
from .utils.color_engine import DominantColorResult, calculate_delta_e, find_best_season


class AsosApiTests(SimpleTestCase):
    def setUp(self):
        os.environ["RAPIDAPI_KEY"] = "test-key"

    def tearDown(self):
        os.environ.pop("RAPIDAPI_KEY", None)

    @patch("matcher.services.asos_api.requests.get")
    def test_search_products_success(self, mock_get: Mock):
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "products": [
                {"id": 1, "name": "Test Shirt", "imageUrl": "http://example.com/a.jpg"},
                {"id": 2, "productName": "Test Pants", "imageUrl": "http://example.com/b.jpg"},
            ]
        }
        mock_get.return_value = mock_response

        results = search_products("shirt", limit=2)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["id"], 1)
        self.assertEqual(results[0]["name"], "Test Shirt")
        self.assertEqual(results[0]["image_url"], "http://example.com/a.jpg")

    def test_search_products_missing_key(self):
        os.environ.pop("RAPIDAPI_KEY", None)
        with self.assertRaises(RuntimeError):
            search_products("shirt")


class ColorEngineTests(SimpleTestCase):
    def test_normalize_hex(self):
        self.assertEqual(color_engine._normalize_hex("#a1b2c3"), "#A1B2C3")
        self.assertEqual(color_engine._normalize_hex("A1B2C3"), "#A1B2C3")

    def test_calculate_delta_e_zero(self):
        self.assertEqual(calculate_delta_e("#112233", "#112233"), 0.0)

    def test_find_best_season(self):
        palettes = {
            "SeasonA": ["#112233"],
            "SeasonB": ["#FFFFFF"],
        }
        season, distance = find_best_season("#112233", palettes)
        self.assertEqual(season, "SeasonA")
        self.assertEqual(distance, 0.0)

    @patch("matcher.utils.color_engine._kmeans_primary_color")
    @patch("matcher.utils.color_engine._decode_image")
    @patch("matcher.utils.color_engine._download_image_bytes")
    def test_extract_dominant_color_flow(self, mock_download, mock_decode, mock_kmeans):
        color_engine.extract_dominant_color.cache_clear()
        color_engine._download_image_bytes.cache_clear()
        mock_download.return_value = b"fake"
        mock_decode.return_value = color_engine.np.zeros((200, 200, 3), dtype=color_engine.np.uint8)
        mock_kmeans.return_value = (10, 20, 30)

        result = color_engine.extract_dominant_color("http://example.com/image.jpg")

        self.assertIsInstance(result, DominantColorResult)
        self.assertEqual(result.hex_value, "#0A141E")
        self.assertEqual(result.rgb, (10, 20, 30))


class ViewsTests(SimpleTestCase):
    def setUp(self):
        self.client = Client()

    def test_index_ok(self):
        response = self.client.get(reverse("matcher:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Seasonal Color Matcher")

    @patch("matcher.views.search_products")
    def test_search_requires_params(self, mock_search):
        response = self.client.get(reverse("matcher:search"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please provide a search query.")
        mock_search.assert_not_called()

    @patch("matcher.views.find_best_season")
    @patch("matcher.views.extract_dominant_color")
    @patch("matcher.views.search_products")
    def test_search_success(self, mock_search, mock_extract, mock_best):
        mock_search.return_value = [
            {"id": 1, "name": "Blue Polo", "image_url": "http://example.com/a.jpg"}
        ]
        mock_extract.return_value = DominantColorResult(hex_value="#112233", rgb=(17, 34, 51))
        mock_best.return_value = ("Light Spring", 5.0)

        response = self.client.get(
            reverse("matcher:search"),
            {"query": "blue polo"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Closest Season")
        self.assertContains(response, "Blue Polo")

    @patch("matcher.views.search_products", side_effect=RuntimeError("boom"))
    def test_search_api_error(self, mock_search):
        response = self.client.get(
            reverse("matcher:search"),
            {"query": "blue", "season": "Light Spring"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ASOS API error")
        mock_search.assert_called_once()
