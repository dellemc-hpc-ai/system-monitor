#!/usr/bin/env python3
"""
Pollen Report Scraper - Linux Version
Auto-detects location via IP geolocation, falls back to Austin TX defaults.

Data sources:
  1. GPS (pollencount.app / AccuWeather): lat/lng based
  2. ZIP  (pollen.com via CDP): species-level data for detected or default ZIP

Usage:
  python3 scrape.py [--output FILE] [--html FILE]
  python3 scrape.py --test
"""

import argparse
import json
import os
import subprocess
import sys
import urllib.request
from datetime import datetime

# ─── Defaults (Austin TX 78750) ─────────────────────────────────────────────────
DEFAULT_LAT = 30.4403525
DEFAULT_LNG = -97.81407276
DEFAULT_ZIP = "78750"
DEFAULT_CITY = "Austin, TX 78750"
DEFAULT_SOURCE_NAME = "pollencount.app (10625 Glass Mountain)"

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
OUTPUT_JSON = os.path.join(DATA_DIR, "pollen-data.json")
DEFAULT_HTML = os.path.join(DATA_DIR, "today.html")
ZIP_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pollen_com_cdp.py")

AQI_API = "https://api.waqi.info/feed/geo:30.4403;-97.814/?token=demo"


# ─── Location Detection ──────────────────────────────────────────────────────────

def detect_location():
    """Detect lat/lng/zip from current IP via ip-api.com (free, no key needed).
    Returns (lat, lng, zip, city) on success, None on failure.
    Falls back to defaults silently.
    """
    try:
        req = urllib.request.Request(
            "http://ip-api.com/json/?fields=status,country,region,regionName,city,zip,lat,lon",
            headers={"User-Agent": "Mozilla/5.0 (PollenReport/1.0)"}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
        if data.get("status") != "success":
            return None
        lat = data.get("lat")
        lng = data.get("lon")
        zip_code = data.get("zip") or ""
        city = f"{data.get('city', '')}, {data.get('regionName', '')} {zip_code}".strip()
        if lat and lng:
            print(f"[Location] Detected: {city} ({lat}, {lng})")
            return {
                "lat": lat, "lng": lng,
                "zip": zip_code or DEFAULT_ZIP,
                "city": city,
            }
    except Exception as e:
        print(f"[Location] Detection failed: {e}, using defaults")
    return None


# ─── GPS source: AccuWeather via pollencount.app ──────────────────────────────────

def fetch_gps_data(lat, lng):
    """Fetch pollen/weather data from AccuWeather (GPS-based)."""
    url = f"https://pollencount.app/api/getForecast?lat={lat}&lng={lng}"
    print(f"Fetching GPS data from pollencount.app...")
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; PollenReport/1.0)"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"GPS fetch failed: {e}", file=sys.stderr)
        return None


def parse_gps_data(raw, source_name):
    """Parse AccuWeather getForecast response into structured dict."""
    result = {
        "source": "GPS (AccuWeather)",
        "source_name": source_name,
    }
    forecasts = raw.get("DailyForecasts", [])
    if not forecasts:
        return result
    today = forecasts[0]
    for item in today.get("AirAndPollen", []):
        name = item.get("Name", "")
        val = item.get("Value")
        cat = item.get("Category", "")
        if name == "Tree":
            result["tree"] = val
            result["tree_category"] = cat
        elif name == "Grass":
            result["grass"] = val
            result["grass_category"] = cat
        elif name == "Ragweed":
            result["ragweed"] = val
            result["ragweed_category"] = cat
        elif name == "Mold":
            result["mold"] = val
            result["mold_category"] = cat
        elif name == "AirQuality":
            result["air_quality"] = val
        elif name == "UVIndex":
            result["uv_index"] = val
    if "Headline" in today:
        result["headline"] = today["Headline"]
    result["temp_high"] = today.get("Temperature", {}).get("Maximum", {}).get("Value")
    result["temp_low"] = today.get("Temperature", {}).get("Minimum", {}).get("Value")
    result["hours_of_sun"] = today.get("HoursOfSun", "?")
    fc = []
    for day in forecasts[:6]:
        fc.append({
            "date": day.get("Date", "")[:10],
            "temp_high": day.get("Temperature", {}).get("Maximum", {}).get("Value"),
            "temp_low": day.get("Temperature", {}).get("Minimum", {}).get("Value"),
            "tree": next((i.get("Value") for i in day.get("AirAndPollen", []) if i.get("Name") == "Tree"), None),
            "grass": next((i.get("Value") for i in day.get("AirAndPollen", []) if i.get("Name") == "Grass"), None),
        })
    result["forecast"] = fc
    return result


# ─── ZIP source: pollen.com via Chrome CDP ────────────────────────────────────────

def fetch_zip_data(zip_code):
    """Fetch species-level pollen data from pollen.com via Chrome CDP.
    Falls back to None if CDP fails or script not found.
    """
    print(f"Fetching ZIP data from pollen.com ({zip_code}) via CDP...")
    if not os.path.exists(ZIP_SCRIPT):
        print(f"  CDP script not found: {ZIP_SCRIPT}")
        return None
    try:
        result = subprocess.run(
            [sys.executable, ZIP_SCRIPT, zip_code],
            capture_output=True, text=True, timeout=90
        )
        if result.returncode == 0 and result.stdout.strip() and result.stdout.strip() != "null":
            data = json.loads(result.stdout.strip())
            print("  -> pollen.com CDP: success")
            return data
        else:
            print("  -> pollen.com CDP returned null or failed")
            return None
    except subprocess.TimeoutExpired:
        print("  -> CDP timed out (90s)")
        return None
    except Exception as e:
        print(f"  -> CDP failed: {e}")
        return None


def parse_zip_data(raw, zip_code):
    """Parse pollen.com data into unified structure."""
    if raw is None:
        return {}
    result = {
        "source": "ZIP (pollen.com)",
        "source_name": f"pollen.com ({zip_code})",
    }
    if "overall_index" in raw or "top_allergens" in raw:
        result["overall_index"] = raw.get("overall_index")
        result["overall_label"] = raw.get("overall_label", "")
        result["top_allergens"] = raw.get("top_allergens", [])
        result["yesterday"] = raw.get("yesterday", {})
        result["tomorrow"] = raw.get("tomorrow", {})
        return result
    # Old API format
    try:
        fc = raw.get("forecast", {})
        today = fc.get("today", fc.get("current", fc))
        if isinstance(today, list):
            today = today[0] if today else {}
        result["tree"] = today.get("Tree", today.get("tree", today.get("TreePollen")))
        result["grass"] = today.get("Grass", today.get("grass", today.get("GrassPollen")))
        result["ragweed"] = today.get("Ragweed", today.get("ragweed"))
        result["mold"] = today.get("Mold", today.get("mold"))
        for k in ["tree_category", "grass_category", "ragweed_category", "mold_category"]:
            v = today.get(k.title().replace("_", ""), today.get(k))
            if v is not None:
                result[k] = v
        result["forecast"] = []
        for day in fc.get("extended", [])[:5]:
            result["forecast"].append({
                "date": day.get("date", day.get("Date", ""))[:10],
                "tree": day.get("Tree", day.get("tree")),
                "grass": day.get("Grass", day.get("grass")),
            })
    except Exception as e:
        print(f"ZIP parse error: {e}", file=sys.stderr)
    return result


# ─── AQI from WAQI ───────────────────────────────────────────────────────────────

def fetch_aqi(lat, lng):
    url = f"https://api.waqi.info/feed/geo:{lat:.4f};{lng:.4f}/?token=demo"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            if data.get("status") == "ok":
                iaqi = data["data"].get("iaqi", {})
                return {
                    "pm25": iaqi.get("pm25", {}).get("v"),
                    "aqi": data["data"].get("aqi"),
                    "source": "WAQI (World Air Quality Index)",
                }
    except Exception as e:
        print(f"AQI fetch failed: {e}", file=sys.stderr)
    return {"pm25": None, "aqi": None, "source": "unavailable"}


# ─── Report Generation ────────────────────────────────────────────────────────────

CAT_ORDER = {"very high": 0, "high": 1, "moderate": 2, "low": 3, "very low": 4, "": 5}

def severity_pollen(value, category):
    if value is None:
        return "-", "gray"
    cat = (category or "").lower()
    color_map = {
        "very low": "lightgreen",
        "low": "green",
        "moderate": "yellow",
        "high": "orange",
        "very high": "red",
    }
    return category or "-", color_map.get(cat, "gray")


def top_allergens(gps):
    allergens = []
    for key, label in [
        ("tree", "Tree"),
        ("grass", "Grass"),
        ("ragweed", "Ragweed"),
        ("mold", "Mold"),
    ]:
        val = gps.get(key)
        cat = gps.get(f"{key}_category", "")
        if val is not None:
            _, col = severity_pollen(val, cat)
            allergens.append((label, val, cat, col))
    allergens.sort(key=lambda x: (CAT_ORDER.get(x[2].lower(), 99), -(x[1] or 0)))
    return allergens


def severity_aqi(aqi):
    if aqi is None:
        return "-", "gray"
    if aqi <= 50:
        return "Good", "green"
    elif aqi <= 100:
        return "Moderate", "yellow"
    elif aqi <= 150:
        return "Unhealthy for Sensitive", "orange"
    elif aqi <= 200:
        return "Unhealthy", "red"
    elif aqi <= 300:
        return "Very Unhealthy", "purple"
    return "Hazardous", "maroon"


def source_block(data, is_gps=True):
    tag = "GPS" if is_gps else "ZIP"
    tag_class = "gps" if is_gps else "zip"
    loc = data.get("source_name", "Unknown location")
    src = "AccuWeather (pollencount.app)" if is_gps else "pollen.com"
    allergen_vals = {k: data.get(k, 0) or 0 for k in ["tree", "grass", "ragweed", "mold"]}
    top_key = max(allergen_vals, key=allergen_vals.get) if any(allergen_vals.values()) else None
    rows_html = ""
    for key, icon in [("tree", "🌳"), ("grass", "🌾"), ("ragweed", "🌼"), ("mold", "🍄")]:
        val = data.get(key)
        cat = data.get(f"{key}_category", "")
        cat_disp, col = severity_pollen(val, cat)
        v = val if val is not None else "-"
        star = " ⭐" if key == top_key and val is not None else ""
        rows_html += f"""
            <div class="pollen-row">
                <span class="pollen-name">{icon} {key.title()}{star}</span>
                <div class="pollen-right">
                    <span class="pollen-num">{v}</span>
                    <span class="badge {col}">{cat_disp}</span>
                </div>
            </div>"""
    return f"""
        <div class="source-card">
            <div class="source-header">
                <span class="source-tag {tag_class}">{tag}</span>
                <span class="source-name">{src}</span>
                <span class="source-loc">{loc}</span>
            </div>
            <div class="pollen-rows">{rows_html}
            </div>
        </div>"""


def zip_species_block(zipd):
    if not zipd or not zipd.get("top_allergens"):
        return ""
    allergens = zipd.get("top_allergens", [])
    overall_idx = zipd.get("overall_index")
    overall_lbl = zipd.get("overall_label", "")
    pt_colors = {"Tree": "#1f6feb", "Grass": "#238636", "Weed": "#d29922", "": "#484f58"}
    allergen_rows = ""
    for t in allergens:
        pt = t.get("plantType", "")
        pt_col = pt_colors.get(pt, "#484f58")
        genus = t.get("genus", "")
        allergen_rows += f"""
            <div class="pollen-row">
                <span class="pollen-name">🌿 {t['name']} <span class="species-genus">({genus})</span></span>
                <span class="badge" style="background:{pt_col}">{pt}</span>
            </div>"""
    idx_str = f"{overall_idx}" if overall_idx is not None else "—"
    return f"""
        <div class="source-card">
            <div class="source-header">
                <span class="source-tag zip">ZIP</span>
                <span class="source-name">pollen.com ({zipd.get('source_name', '').split('(')[-1].rstrip(')')})</span>
            </div>
            <div class="pollen-rows">{allergen_rows}
            </div>
            <div class="zip-overall">
                <span class="zip-idx">{idx_str}</span>
                <span class="zip-lbl">{overall_lbl}</span>
            </div>
            <div class="zip-note">Species breakdown via pollen.com &middot; Today's top allergens</div>
        </div>"""


def generate_html(gps_data, zip_data, aqi, location):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M %Z")
    loc_display = location.get("city", DEFAULT_CITY)
    aqi_val = aqi.get("aqi")
    aqi_cat, aqi_col = severity_aqi(aqi_val)

    allergens = top_allergens(gps_data)
    allergen_rows = ""
    for label, val, cat, col in allergens:
        v = val if val is not None else "-"
        allergen_rows += f"""
            <div class="pollen-row">
                <span class="pollen-name">{label}</span>
                <div class="pollen-right">
                    <span class="pollen-num">{v}</span>
                    <span class="badge {col}">{cat}</span>
                </div>
            </div>"""

    gps_block = source_block(gps_data, is_gps=True)

    if zip_data and zip_data.get("top_allergens"):
        zip_block = zip_species_block(zip_data)
    elif zip_data and zip_data.get("tree") is not None:
        zip_block = source_block(zip_data, is_gps=False)
    else:
        zip_block = """
        <div class="source-card">
            <div class="source-header">
                <span class="source-tag zip">ZIP</span>
                <span class="source-name">pollen.com</span>
                <span class="source-loc">Species data unavailable</span>
            </div>
            <div class="pollen-unavailable">
                <p>pollen.com species data currently unavailable.</p>
            </div>
        </div>"""

    weather = ""
    if gps_data.get("temp_high"):
        weather = f"""
        <div class="card">
            <h2>Today's Weather</h2>
            <div class="weather-row">
                <span class="temp-big">{gps_data["temp_high"]}°F</span>
                <span class="temp-range">/ {gps_data.get("temp_low","?")}°F</span>
                <span class="sun-info">☀️ {gps_data.get("hours_of_sun","?")}h sun</span>
            </div>
            {('<p class="headline">' + gps_data["headline"] + '</p>') if gps_data.get("headline") else ''}
        </div>"""

    fc_rows = ""
    for day in gps_data.get("forecast", []):
        fc_rows += f"""
        <div class="forecast-row">
            <span class="forecast-date">{day.get("date","?")[5:]}</span>
            <span class="forecast-temps">{day.get("temp_low","?")}°–{day.get("temp_high","?")}°F</span>
            <span>🌳 {day.get("tree","?")}</span>
            <span>🌾 {day.get("grass","?")}</span>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🌿 Pollen Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0d1117; color: #e6edf3; line-height: 1.6; }}
        .container {{ max-width: 640px; margin: 0 auto; padding: 30px 16px; }}
        h1 {{ font-size: 1.6rem; color: #58a6ff; margin-bottom: 4px; }}
        .timestamp {{ color: #8b949e; font-size: 0.85rem; }}
        .location {{ color: #8b949e; font-size: 0.9rem; margin: 8px 0 24px; }}
        .card {{ background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 20px; margin-bottom: 16px; }}
        .card h2 {{ font-size: 0.85rem; color: #8b949e; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 14px; border-bottom: 1px solid #21262d; padding-bottom: 8px; }}
        .source-card {{ background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 20px; margin-bottom: 12px; }}
        .source-header {{ display: flex; align-items: center; gap: 8px; margin-bottom: 14px; border-bottom: 1px solid #21262d; padding-bottom: 10px; }}
        .source-tag {{ font-size: 0.7rem; padding: 2px 8px; border-radius: 8px; font-weight: 700; }}
        .source-tag.gps {{ background: #1f6feb; }} .source-tag.zip {{ background: #238636; }}
        .source-name {{ font-weight: 700; font-size: 0.95rem; }}
        .source-loc {{ color: #8b949e; font-size: 0.8rem; margin-left: auto; }}
        .pollen-row {{ display: flex; justify-content: space-between; align-items: center; padding: 9px 0; border-bottom: 1px solid #21262d; }}
        .pollen-row:last-child {{ border-bottom: none; }}
        .pollen-name {{ font-size: 0.95rem; }}
        .pollen-right {{ display: flex; align-items: center; gap: 8px; }}
        .pollen-num {{ font-size: 1.2rem; font-weight: 700; min-width: 36px; text-align: right; }}
        .pollen-unavailable {{ padding: 12px 0; color: #8b949e; font-size: 0.88rem; }}
        .species-genus {{ color: #8b949e; font-size: 0.8rem; font-weight: 400; }}
        .zip-overall {{ display: flex; align-items: center; gap: 12px; margin-top: 14px; padding-top: 12px; border-top: 1px solid #21262d; }}
        .zip-idx {{ font-size: 1.5rem; font-weight: 800; }}
        .zip-lbl {{ color: #8b949e; font-size: 0.85rem; }}
        .zip-note {{ color: #484f58; font-size: 0.75rem; margin-top: 8px; }}
        .badge {{ font-size: 0.68rem; padding: 2px 7px; border-radius: 10px; color: #fff; font-weight: 600; }}
        .lightgreen {{ background: #3fb950; }} .green {{ background: #238636; }}
        .yellow {{ background: #d29922; }} .orange {{ background: #db6d28; }}
        .red {{ background: #da3633; }} .purple {{ background: #8957e5; }}
        .maroon {{ background: #b62324; }} .gray {{ background: #484f58; }}
        .aqi-section {{ display: flex; align-items: center; gap: 16px; }}
        .aqi-num {{ font-size: 2.5rem; font-weight: 800; }}
        .weather-row {{ display: flex; align-items: baseline; gap: 12px; }}
        .temp-big {{ font-size: 2rem; font-weight: 800; }}
        .temp-range {{ color: #8b949e; }}
        .sun-info {{ color: #8b949e; font-size: 0.85rem; }}
        .headline {{ margin-top: 10px; color: #d29922; font-size: 0.9rem; }}
        .forecast-row {{ display: grid; grid-template-columns: 60px 1fr 50px 50px; gap: 8px; align-items: center; padding: 8px 0; border-bottom: 1px solid #21262d; font-size: 0.9rem; }}
        .forecast-row:last-child {{ border-bottom: none; }}
        .forecast-date {{ color: #8b949e; }}
        .forecast-temps {{ color: #8b949e; }}
        .footer {{ text-align: center; color: #484f58; font-size: 0.8rem; margin-top: 24px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🌿 Pollen Report</h1>
        <p class="timestamp">{ts}</p>
        <p class="location">📍 {loc_display}</p>

        <div class="card">
            <h2>🌡️ Key Allergens Today</h2>
            <p style="color:#8b949e;font-size:0.82rem;margin-bottom:12px">Primary outdoor allergens - sorted by severity &nbsp;⭐ = top contributor</p>
            <div class="pollen-rows">{allergen_rows}
            </div>
        </div>

{gps_block}
{zip_block}

        <div class="card">
            <h2>🌬️ Air Quality</h2>
            <div class="aqi-section">
                <span class="aqi-num">{aqi.get("aqi") or "—"}</span>
                <span class="badge {aqi_col}">{aqi_cat}</span>
                {('<span style="color:#8b949e">PM2.5: ' + str(aqi.get("pm25") or "—") + '</span>') if aqi.get("pm25") else ''}
            </div>
        </div>

{weather}

        <div class="card">
            <h2>📅 5-Day Forecast</h2>
            <div class="forecast-row header">
                <span></span><span></span><span>🌳</span><span>🌾</span>
            </div>{fc_rows}
        </div>

        <p class="footer">Sources: AccuWeather (GPS) + pollen.com (ZIP)</p>
    </div>
</body>
</html>"""


# ─── Main ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Pollen Report Scraper")
    parser.add_argument("--output", default=OUTPUT_JSON, help="Output JSON path")
    parser.add_argument("--html", default=DEFAULT_HTML, help="Output HTML path")
    parser.add_argument("--test", action="store_true", help="Print outputs to stdout")
    args = parser.parse_args()

    # 1. Detect location (falls back to Austin TX defaults)
    detected = detect_location()
    if detected:
        location = detected
    else:
        location = {
            "lat": DEFAULT_LAT, "lng": DEFAULT_LNG,
            "zip": DEFAULT_ZIP, "city": DEFAULT_CITY,
        }
        print("[Location] Using default: Austin TX 78750")

    lat = location["lat"]
    lng = location["lng"]
    zip_code = location["zip"]

    # 2. Fetch data
    gps_raw = fetch_gps_data(lat, lng)
    gps_data = parse_gps_data(gps_raw, location.get("city", DEFAULT_CITY)) if gps_raw else {}
    zip_raw = fetch_zip_data(zip_code)
    zip_data = parse_zip_data(zip_raw, zip_code)
    aqi = fetch_aqi(lat, lng)

    # 3. Build output
    allergens = top_allergens(gps_data)
    top = allergens[0] if allergens else None

    output = {
        "timestamp": datetime.now().isoformat(),
        "location": location.get("city", DEFAULT_CITY),
        "lat": lat, "lng": lng, "zip": zip_code,
        "gps": gps_data,
        "zip": zip_data,
        "aqi": aqi,
        "top_allergen": top[0] if top else None,
        "top_allergen_value": top[1] if top else None,
        "top_allergen_category": top[2] if top else None,
    }

    html = generate_html(gps_data, zip_data, aqi, location)

    if args.test:
        print(json.dumps(output, indent=2))
        print(html)
    else:
        with open(args.output, "w") as f:
            json.dump(output, f, indent=2)
        with open(args.html, "w") as f:
            f.write(html)
        print(f"JSON: {args.output}")
        print(f"HTML: {args.html}")


if __name__ == "__main__":
    main()
