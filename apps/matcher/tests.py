from django.test import SimpleTestCase
from unittest.mock import Mock, patch
import os

from .services.asos_api import search_products


class AsosApiTests(SimpleTestCase):
    def setUp(self):
        os.environ["RAPIDAPI_KEY"] = "test-key"

    def tearDown(self):
        os.environ.pop("RAPIDAPI_KEY", None)

    @patch("apps.matcher.services.asos_api.requests.get")
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
