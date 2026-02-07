# AGENTS.md: Seasonal Color Matcher (PoC)

## 1. Project Overview
**Goal:** A Django-based mobile-first web app that fetches clothing from the ASOS API, extracts the dominant color via OpenCV, and matches it against a user's 12-season color palette using fuzzy logic ($\Delta E$).

## 2. Technical Stack
* **Framework:** Django (Python 3.10+)
* **Image Processing:** `opencv-python`, `numpy`, `scikit-learn` (K-Means)
* **Color Science:** `colormath` (for Lab space conversions)
* **Frontend:** Tailwind CSS via CDN (Mobile-first)
* **API:** ASOS (via RapidAPI)

## 3. Core Modules & Logic

### A. The Color Engine (`utils/color_engine.py`)
1.  **Extraction:**
    * **Input:** Image URL.
    * **Process:** Download image $\rightarrow$ Resize to 200x200 $\rightarrow$ Center-crop 50% (to isolate garment) $\rightarrow$ Apply K-Means (k=3) to find the primary cluster.
2.  **Conversion:** Convert RGB/Hex to **CIE Lab** color space for accurate perceptual matching.
3.  **Matching:** * Calculate the Euclidean distance ($\Delta E$) between the extracted color and the user's seasonal palette.
    * **Logic:** `is_match = True` if $\Delta E < 10$ (Standard threshold for "close enough").

### B. Seasonal Palettes (`constants.py`)
Hard-code a dictionary containing the 12 standard seasons:
* **Spring:** Light Spring, Clear Spring, Warm Spring.
* **Summer:** Soft Summer, Light Summer, Cool Summer.
* **Autumn:** Deep Autumn, Soft Autumn, Warm Autumn.
* **Winter:** Deep Winter, Clear Winter, Cool Winter.
* *Note: Each season should contain ~20 representative HEX codes.*

### C. The Search Workflow (`views.py`)
1.  Receive search query from frontend (e.g., "blue polo").
2.  Query ASOS API and retrieve product list (image URLs and metadata).
3.  **Processing Loop:** * Iterate through the first 10-15 results.
    * Run `color_engine.py` on each image.
    * Tag products with `is_seasonal_match: true/false`.
4.  Return results to the mobile-responsive grid.

## 4. Implementation Roadmap

### Phase 1: Environment & Utils
- [x] Initialize Django project and app structure.
- [x] Create `constants.py` with 12-season HEX dictionaries.
- [x] Develop `extract_dominant_color(url)` utility using OpenCV/KMeans.
- [x] Develop `calculate_delta_e(hex1, hex2)` utility.

### Phase 2: API & Integration
- [x] Configure RapidAPI credentials for ASOS.
- [x] Create `services/asos_service.py` to handle API requests.
- [x] Build the main search view that combines API data with the color engine.

### Phase 3: Frontend Development
- [ ] Design "Season Selection" landing page (Mobile-first).
- [ ] Create search results page with "Seasonal Match" badges using Tailwind CSS.

---

## 5. Instructions for AI Coding Agents
* **Accuracy:** Prioritize Delta E calculations over simple RGB comparisons.
* **Performance:** Implement basic caching for image processing results to avoid redundant downloads of the same product image.
* **UI:** Use a clean, minimalist aesthetic. Ensure the "Match" indicator is highly visible on mobile.

---

## 6. Project Directory Structure
```text
irl/
├── manage.py
├── .env                    # API keys and secret variables
├── .gitignore              # To ignore venv, __pycache__, and .env
├── AGENTS.md               # The development spec for AI agents
├── README.md               # Project documentation
├── requirements.txt        # List of dependencies
│
├── core/                   # Project configuration
│   ├── __init__.py
│   ├── settings.py         
│   ├── urls.py             
│   └── wsgi.py
│
├── apps/                   
│   └── matcher/            # Main application logic
│       ├── migrations/
│       ├── static/         
│       │   └── css/
│       │       └── styles.css
│       ├── templates/      
│       │   └── matcher/
│       │       ├── base.html
│       │       ├── index.html
│       │       └── results.html
│       ├── __init__.py
│       ├── constants.py    # 12-Season HEX Dictionary
│       ├── models.py       
│       ├── services/       
│       │   ├── __init__.py
│       │   └── asos_api.py # ASOS API wrapper
│       ├── utils/          
│       │   ├── __init__.py
│       │   └── color_engine.py  # OpenCV & K-Means logic
│       ├── urls.py         
│       └── views.py        
└── venv/
```
