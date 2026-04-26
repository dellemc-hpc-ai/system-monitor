"""
main.py — Custody Calendar Generator
=====================================
End-to-end pipeline:
  1. Load statute (TX)
  2. Load standard school calendar
  3. Geolocate parents via Nominatim
  4. Build custody rules (SPO + ESPO)
  5. Compute custody intervals
  6. Generate HTML calendar
"""
import os, sys, json

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── 1. Load statute ───────────────────────────────────────────────────────────
from src.statute_loader import load_statute

statute = load_statute("TX", PROCESSED_DIR)
print(f"[main] Loaded statute: {statute['state']} {statute['state_name']}")

# ── 2. Load standard calendar ─────────────────────────────────────────────────
from src.custody_calculator import load_standard_calendar

cal_path = os.path.join(PROCESSED_DIR, "rrisd_standard_calendar.json")
if not os.path.exists(cal_path):
    print(f"[main] ERROR: {cal_path} not found.")
    print("         Run the calendar fetcher first, or place standard_calendar.json there.")
    sys.exit(1)

cal = load_standard_calendar(cal_path)
district_name = cal.get("district", "Round Rock ISD")
print(f"[main] Calendar district: {district_name}")
print(f"       School years: {[sy['year'] for sy in cal.get('schoolYears', [])]}")

# ── 3. Geolocate parents ─────────────────────────────────────────────────────
from src.geolocator import geocode

dad_file = os.path.join(BASE_DIR, "inputs", "dad_addr.txt")
mom_file = os.path.join(BASE_DIR, "inputs", "mom_addr.txt")

with open(dad_file, encoding="utf-8") as f:
    dad_addr = f.read().strip()
print(f"[main] Dad address: {dad_addr}")

dad_loc = geocode(dad_addr)
if dad_loc is None:
    print("[main] ERROR: geocoding dad address failed")
    sys.exit(1)
print(f"[main] Dad lat/lon: {dad_loc.lat:.4f}, {dad_loc.lon:.4f}")

mom_loc = dad_loc
if os.path.exists(mom_file):
    with open(mom_file, encoding="utf-8") as f:
        mom_addr = f.read().strip()
    if mom_addr:
        mom_loc = geocode(mom_addr)
        if mom_loc:
            print(f"[main] Mom lat/lon: {mom_loc.lat:.4f}, {mom_loc.lon:.4f}")
        else:
            print("[main] WARNING: mom geocoding failed, using dad's location")
            mom_loc = dad_loc
else:
    print("[main] Mom address file empty → distance = 0")

# ── 4. Compute distance ──────────────────────────────────────────────────────
from math import radians, cos, sin, sqrt, atan2

def haversine(lat1, lon1, lat2, lon2):
    R = 3958.8
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))

distance = haversine(dad_loc.lat, dad_loc.lon, mom_loc.lat, mom_loc.lon)
print(f"[main] Distance between parents: {distance:.1f} miles")

# ── 5. Build rules & compute intervals ──────────────────────────────────────
from src.rule_builder import build_custody_rules
from src.custody_calculator import CustodyCalculator

def build_and_compute(mode):
    rules = build_custody_rules(
        statute=statute,
        distance_miles=distance,
        mode=mode,
        dad_lat=dad_loc.lat,
        dad_lon=dad_loc.lon,
        mom_lat=mom_loc.lat,
        mom_lon=mom_loc.lon,
    )
    calc = CustodyCalculator(rules, cal)
    intervals = calc.compute_intervals()
    return rules, intervals

print("\n[main] Computing ESPO intervals...")
espo_rules, espo_intervals = build_and_compute("espo")
print(f"      ESPO: {len(espo_intervals)} intervals")

print("[main] Computing SPO intervals...")
spo_rules, spo_intervals = build_and_compute("spo")
print(f"      SPO:  {len(spo_intervals)} intervals")

# ── 6. Save intervals ────────────────────────────────────────────────────────
espo_iv_list = [iv.to_dict() for iv in espo_intervals]
spo_iv_list = [iv.to_dict() for iv in spo_intervals]

espo_path = os.path.join(PROCESSED_DIR, "espo_intervals.json")
spo_path = os.path.join(PROCESSED_DIR, "spo_intervals.json")

with open(espo_path, "w", encoding="utf-8") as f:
    json.dump({"count": len(espo_intervals), "intervals": espo_iv_list}, f, indent=2)
print(f"[main] Saved ESPO intervals -> {espo_path}")

with open(spo_path, "w", encoding="utf-8") as f:
    json.dump({"count": len(spo_intervals), "intervals": spo_iv_list}, f, indent=2)
print(f"[main] Saved SPO intervals  -> {spo_path}")

# ── 7. Generate HTML ─────────────────────────────────────────────────────────
from src.static_web_generator.html_builder import HTMLBuilder

builder = HTMLBuilder(
    district=district_name,
    espo_intervals=espo_iv_list,
    spo_intervals=spo_iv_list,
)
html_path = os.path.join(OUTPUT_DIR, "custody_school_calendar.html")
builder.build(html_path)
print(f"[main] Generated HTML -> {html_path}")
print(f"Done! Open: {html_path}")
