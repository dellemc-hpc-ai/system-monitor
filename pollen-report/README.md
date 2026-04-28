# 🌿 Pollen Report Scraper

Austin, TX 78750 — Daily pollen allergy report with species-level breakdown.

**Sources:**
- **GPS/AccuWeather** (pollencount.app): tree/grass/ragweed/mold counts + categories
- **pollen.com** (via Chrome CDP): species-level allergen breakdown (Hickory, Willow, Oak, etc.)
- **WAQI**: Air Quality Index (PM2.5)

## Quick Start

```bash
cd pollen-report
pip install -r requirements.txt
python3 scrape.py
# Open data/today.html in browser
```

## Project Structure

```
pollen-report/
├── scrape.py           # Main scraper — generates JSON + HTML report
├── pollen_com_cdp.py   # Chrome CDP species fetcher
├── requirements.txt
├── data/
│   ├── pollen-data.json   # Structured output
│   └── today.html         # HTML report
└── run_daily.sh       # Cron wrapper
```

## Report Features

- **Key Allergens** — Tree 🌳 / Grass 🌾 / Ragweed 🌼 / Mold 🍄 sorted by severity
- **Species Breakdown** — Hickory / Willow / Oak from pollen.com (CDP)
- **AQI** — PM2.5 + Air Quality category
- **5-Day Forecast** — Tree + Grass counts

## Cron — Daily at 7 AM

```bash
crontab -e
0 7 * * * /home/frank/hermes/pollen-report/run_daily.sh >> /home/frank/hermes/pollen-report/data/cron.log 2>&1
```
