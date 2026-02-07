# Seasonal Color Matcher 🎨👗

A Django-powered web application that helps users find clothing that matches their personal "Color Seasonality." By extracting dominant colors from retail product images and comparing them to curated seasonal palettes, the app provides a personalized shopping experience.

## 🌟 Key Features

- **12-Season Identification:** Supports standard color theory (e.g., Deep Winter, Soft Summer, Light Spring).
- **Dominant Color Extraction:** Uses **OpenCV** and **K-Means Clustering** to isolate the primary color of a garment from an image URL.
- **Fuzzy Matching Logic:** Implements **Delta E ($\Delta E$)** distance calculations in the CIE Lab color space to ensure matches are perceptually accurate, accounting for lighting and shadows.
- **ASOS Integration:** Fetches real-time product data using the ASOS API (via RapidAPI).
- **Mobile-First Design:** Fully responsive UI built with **Tailwind CSS**.

## 🛠️ Tech Stack

- **Backend:** Python / Django
- **Computer Vision:** OpenCV, NumPy, Scikit-learn
- **Color Science:** Colormath / SciPy
- **Frontend:** Tailwind CSS, JavaScript (Fetch API)
- **Data Source:** ASOS API (RapidAPI)

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- A RapidAPI account (for ASOS API access)

### Environment Variables
Set these in `.env` (do not commit the file):
- `DJANGO_SECRET_KEY` (required)
- `DJANGO_DEBUG` (`true` or `false`)
- `DJANGO_ALLOWED_HOSTS` (comma-separated, e.g. `localhost,127.0.0.1`)
- `DJANGO_SECURE_SSL_REDIRECT` (`true` or `false`, production)
- `DJANGO_SECURE_HSTS_SECONDS` (integer, production)
