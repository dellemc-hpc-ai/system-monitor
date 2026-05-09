#!/bin/bash
TOKEN="8699881677:AAEM_6K6G2JAI5HIlujPY515_o2zPo-a91U"
CHAT_ID="8670077590"
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
LOCKFILE="/tmp/pollen_report.lock"

# Ensure only one instance
exec 200>"$LOCKFILE"
flock -n 200 || { echo "Already running"; exit 0; }

# Kill stale scrape.py
pkill -f "python3.*scrape.py" 2>/dev/null
sleep 1

# Run scraper
cd "$SCRIPT_DIR"
python3 scrape.py

# Build Telegram HTML message from JSON
MSG=$(python3 - <<'PYEOF'
import json, html

with open("/home/frank/hermes/pollen-report/data/pollen-data.json") as f:
    d = json.load(f)

loc = d["location"]
ts = d["timestamp"][:16]
gps = d["gps"]
aqi = d["aqi"]
zip_ = d["zip"]
top = d["top_allergen"]
top_val = d["top_allergen_value"]
top_cat = d["top_allergen_category"]

# AQI color
aqi_cat = aqi["aqi"]
aqi_color = "🟢 Low" if aqi_cat <= 50 else "🟡 Moderate" if aqi_cat <= 100 else "🟠 Unhealthy for Sensitive" if aqi_cat <= 150 else "🔴 Unhealthy"

# GPS categories with emoji
def cat_emoji(cat):
    return {"Very High": "🔴", "High": "🟠", "Moderate": "🟡", "Low": "🟢", "Very Low": "⚪"}.get(cat, cat)

lines = []
lines.append(f"🌿 <b>Austin Pollen Report</b>")
lines.append(f"📍 {loc}  |  {ts}")
lines.append("")
lines.append(f"<b>⚠️ Top Allergen: {top} ({top_val}, {top_cat})</b>")
lines.append("")
lines.append("🌡️ <b>Key Allergens (AccuWeather)</b>")
lines.append(f"  Ragweed: {gps['ragweed']} {cat_emoji(gps['ragweed_category'])}")
lines.append(f"  Tree:    {gps['tree']} {cat_emoji(gps['tree_category'])}")
lines.append(f"  Mold:    {gps['mold']} {cat_emoji(gps['mold_category'])}")
lines.append(f"  Grass:   {gps['grass']} {cat_emoji(gps['grass_category'])}")
lines.append("")
lines.append("🌬️ <b>Air Quality</b>")
lines.append(f"  AQI {aqi['aqi']} ({aqi_cat} PM2.5) — {aqi_color}")
lines.append("")
lines.append("🌤️ <b>Weather</b>")
lines.append(f"  {gps['temp_high']}°F / {gps['temp_low']}°F  ☀️ {gps['hours_of_sun']}h sun")
lines.append("")
lines.append("📅 <b>5-Day Forecast</b>")
for f in gps["forecast"]:
    date = f["date"][5:]  # MM-DD
    hi, lo = f["temp_high"], f["temp_low"]
    tr, gr = f["tree"], f["grass"]
    lines.append(f"  {date}: {lo}°–{hi}°  🌳{tr}  🌾{gr}")
lines.append("")
lines.append("🗺️ <b>pollen.com (ZIP 78750)</b>")
zip_allergens = ", ".join([f"{a['name']} ({a['plantType']})" for a in zip_["top_allergens"]])
lines.append(f"  Overall: {zip_['overall_index']} ({zip_['overall_label']})")
lines.append(f"  Top: {zip_allergens}")

print("\n".join(lines))
PYEOF
)

# Send via Telegram
curl -s -X POST "https://api.telegram.org/bot${TOKEN}/sendMessage" \
  -d chat_id="$CHAT_ID" \
  -d text="$MSG" \
  -d parse_mode="HTML" \
  -d disable_web_page_preview="true"

echo ""
echo "Sent at $(date)"
