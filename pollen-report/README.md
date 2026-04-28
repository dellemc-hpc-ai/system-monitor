# 🌿 Pollen Report Scraper

Daily pollen allergy report — auto-detects your location via IP geolocation.

**Sources:**
- **AccuWeather** (pollencount.app): tree/grass/ragweed/mold counts + categories
- **pollen.com** (via Chrome CDP): species-level allergen breakdown (Hickory, Willow, Oak, etc.)
- **WAQI**: Air Quality Index (PM2.5)

## Quick Start

```bash
pip install -r requirements.txt
python3 scrape.py
# Open data/today.html in browser
```

## How It Works

1. **Auto-detect location** via ip-api.com (no API key needed)
2. **GPS data** from AccuWeather using detected lat/lng
3. **Species data** from pollen.com using detected ZIP code (via headless Chrome CDP)
4. **AQI** from WAQI using detected coordinates
5. Falls back to Austin TX 78750 defaults if location detection fails

## Report Features

- **Key Allergens** — Tree / Grass / Ragweed / Mold sorted by severity
- **Species Breakdown** — Hickory / Willow / Oak from pollen.com (CDP)
- **AQI** — PM2.5 + Air Quality category
- **5-Day Forecast** — Tree + Grass counts

## Project Structure

```
pollen-report/
├── scrape.py           # Main scraper — auto-detects location, generates JSON + HTML
├── pollen_com_cdp.py   # Chrome CDP species fetcher (takes ZIP code as arg)
├── requirements.txt    # requests + websockets
├── data/
│   ├── pollen-data.json   # Structured output
│   └── today.html         # HTML report
└── README.md
```

## Cron — Daily at 7 AM (OpenClaw)

Managed by OpenClaw cron job — no crontab entry needed.
