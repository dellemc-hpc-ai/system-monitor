import os, sys, json, argparse
from datetime import date as date_cls

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from geocode_district import geocode, search_district, cache_district
from calendar_fetcher_parser import DataNormalizer
from calendar_fetcher_parser.fetch_district_ics import (
    fetch_noschool_events, build_noschool_labels, NoCalendarSourceError,
)
from calendar_fetcher_parser.district_ics_registry import get_ics_url
from custody_interval_calculator import (
    CustodyIntervalGenerator, load_calendar, save_intervals,
)
from static_web_generator import HTMLBuilder
from statute_loader import load_statute
from rule_builder import build_custody_rules
from geolocator import haversine_miles

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
BASE_DIR = PROJECT_ROOT
DATA_DIR = os.path.join(BASE_DIR, "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
CONFIG_DIR = os.path.join(BASE_DIR, "config")


# ─── rule_builder output → CustodyIntervalGenerator format ────────────────────
# rule_builder produces rules using:
#   "odd_year": "dad", "even_year": "dad"   (top-level keys, singular)
#   "possessory_parent"/"remainder_parent"  (summer)
# CustodyIntervalGenerator (StandardCalendar.custody_rules) expects:
#   "odd_year_parent": "dad", "even_year_parent": "mom"  (nested under each holiday)
#   "default_30_days": "july_1_30"           (summer, under noschool_days)
# This adapter converts between the two formats.

def convert_rules_to_standard_format(rules: dict, mode: str) -> dict:
    """
    Convert rule_builder output to the StandardCalendar custody_rules format
    expected by CustodyIntervalGenerator.
    """
    holidays = rules.get("holidays", {})
    summer = rules.get("summer", {})
    noschool = {"default_parent": summer.get("possessory_parent", "dad")}

    return {
        "espo": {
            "weekend": dict(rules.get("weekend", {})),
            "thursday": dict(rules.get("thursday", {})),
            "holidays": {
                "thanksgiving": {
                    "odd_year_parent": holidays.get("thanksgiving", {}).get("odd_year"),
                    "even_year_parent": holidays.get("thanksgiving", {}).get("even_year"),
                },
                "christmas": {
                    "split": "first_second_half",
                    "odd_year_parent": holidays.get("christmas", {}).get("odd_year_first"),
                    "even_year_parent": holidays.get("christmas", {}).get("even_year_first"),
                    "split_day": 28,
                },
                "spring_break": {
                    "odd_year_parent": holidays.get("spring_break", {}).get("odd_year"),
                    "even_year_parent": holidays.get("spring_break", {}).get("even_year"),
                    "whole_period": holidays.get("spring_break", {}).get("whole_period", True),
                },
            },
            "summer": {
                "parent": summer.get("possessory_parent", "dad"),
                "default_30_days": summer.get("possessory_days", "july_1_30"),
            },
            "noschool_days": noschool,
        },
        "spo": {
            # SPO weekend/thursday are identical to ESPO for our purposes;
            # CustodyIntervalGenerator uses the same rules for both modes
            # when rules are provided via calendar.custody_rules.
            # The statute differences (ESPO Thu overnight) are handled by
            # CustodyIntervalGenerator internally based on mode.
            "weekend": dict(rules.get("weekend", {})),
            "thursday": dict(rules.get("thursday", {})),
            "holidays": {
                "thanksgiving": {
                    "odd_year_parent": holidays.get("thanksgiving", {}).get("odd_year"),
                    "even_year_parent": holidays.get("thanksgiving", {}).get("even_year"),
                },
                "christmas": {
                    "split": "first_second_half",
                    "odd_year_parent": holidays.get("christmas", {}).get("odd_year_first"),
                    "even_year_parent": holidays.get("christmas", {}).get("even_year_first"),
                    "split_day": 28,
                },
                "spring_break": {
                    "odd_year_parent": holidays.get("spring_break", {}).get("odd_year"),
                    "even_year_parent": holidays.get("spring_break", {}).get("even_year"),
                    "whole_period": holidays.get("spring_break", {}).get("whole_period", True),
                },
            },
            "summer": {
                "parent": summer.get("possessory_parent", "dad"),
                "default_30_days": summer.get("possessory_days", "july_1_30"),
            },
            "noschool_days": noschool,
        },
    }


# ─── Address loading ───────────────────────────────────────────────────────────

def load_addresses():
    """Load dad and mom addresses from inputs/ directory."""
    dad_file = os.path.join(BASE_DIR, "inputs", "dad_addr.txt")
    mom_file = os.path.join(BASE_DIR, "inputs", "mom_addr.txt")

    with open(dad_file, encoding="utf-8") as f:
        dad_addr = f.read().strip()
    if not dad_addr:
        raise ValueError("inputs/dad_addr.txt is empty — please fill in the dad's address")

    mom_addr = ""
    if os.path.exists(mom_file):
        with open(mom_file, encoding="utf-8") as f:
            mom_addr = f.read().strip()

    return dad_addr, mom_addr


def find_existing_calendar(district):
    processed = os.path.join(DATA_DIR, "processed")
    if not os.path.exists(processed):
        return None
    dl = district.lower().replace(" ", "_")
    for fname in os.listdir(processed):
        if dl in fname.lower() and fname.endswith(".json") and "interval" not in fname:
            return os.path.join(processed, fname)
    return None


def _school_year_dates(sy_label: str):
    start_year = int(sy_label.split("-")[0])
    end_year = start_year + 1
    sy_start = date_cls(start_year, 8, 1)
    sy_end = date_cls(end_year, 8, 31)
    return sy_start, sy_end


# ─── Calendar building ────────────────────────────────────────────────────────

def build_calendar_for_district(district: str, calendar_page_url: str = ""):
    """Fetch ICS calendar from the district and normalize into StandardCalendar JSON."""
    normalizer = DataNormalizer(district)
    normalizer.set_source(f"{district} official calendar (Google Calendar ICS)")

    school_years = [
        {"label": "2025-2026", "start": "2025-08-13", "end": "2026-05-21",
         "breaks": {
             "thanksgiving": {"start": "2025-11-24", "end": "2025-11-30",
                              "label": {"en": "Thanksgiving Break", "cn": "感恩节假期"}},
             "christmas":    {"start": "2025-12-19", "end": "2026-01-05",
                              "label": {"en": "Christmas Break",  "cn": "圣诞假期"}},
             "spring":       {"start": "2026-03-16", "end": "2026-03-20",
                              "label": {"en": "Spring Break",    "cn": "春假"}},
             "summer":       {"start": "2026-05-22", "end": "2026-08-12",
                              "label": {"en": "Summer Break",    "cn": "暑假"}},
         }},
        {"label": "2026-2027", "start": "2026-08-18", "end": "2027-05-27",
         "breaks": {
             "thanksgiving": {"start": "2026-11-21", "end": "2026-11-27",
                              "label": {"en": "Thanksgiving Break", "cn": "感恩节假期"}},
             "christmas":    {"start": "2026-12-18", "end": "2027-01-05",
                              "label": {"en": "Christmas Break",   "cn": "圣诞假期"}},
             "spring":       {"start": "2027-03-15", "end": "2027-03-19",
                              "label": {"en": "Spring Break",     "cn": "春假"}},
             "summer":       {"start": "2027-05-28", "end": "2027-08-16",
                              "label": {"en": "Summer Break",      "cn": "暑假"}},
         }},
    ]

    for sy in school_years:
        label = sy["label"]
        sy_start, sy_end = _school_year_dates(label)
        print(f"[ICS] Fetching noschool days for {label} ({sy_start} -> {sy_end})...")
        try:
            events = fetch_noschool_events(
                district=district,
                school_year_start=sy_start,
                school_year_end=sy_end,
                calendar_page_url=calendar_page_url,
            )
            sy["noschool_days"] = build_noschool_labels(events)
            print(f"[ICS] Found {len(events)} noschool days for {label}")
        except NoCalendarSourceError as e:
            print(f"[WARN] Could not fetch ICS for {label}: {e}")
            sy["noschool_days"] = []

    for sy in school_years:
        normalizer.add_school_year(
            year=sy["label"], start=sy["start"], end=sy["end"],
            breaks=sy["breaks"], noschool_days=sy["noschool_days"],
        )

    errors = normalizer.validate()
    if errors:
        print("Validation errors:", errors)
    else:
        print("[OK] Calendar data valid")

    saved = normalizer.save()
    return saved


# ─── Interval helpers ─────────────────────────────────────────────────────────

def _load_intervals(mode: str):
    path = os.path.join(DATA_DIR, "processed", f"{mode}_intervals.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    return data.get("intervals", data)


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Custody calendar pipeline")
    parser.add_argument("--address", default=None,
                        help="Override dad address (default: read from inputs/dad_addr.txt)")
    parser.add_argument("--district", default=None,
                        help="Override district name (default: auto-detect from address)")
    parser.add_argument("--debug", action="store_true",
                        help="Force recalculate intervals and show sample output")
    args = parser.parse_args()

    # ── 1. Load addresses ─────────────────────────────────────────────────────
    dad_addr, mom_addr = load_addresses()
    dad_addr = args.address or dad_addr
    print(f"[1] Dad address: {dad_addr}")
    if mom_addr:
        print(f"    Mom address: {mom_addr}")

    # ── 2. Geocode ───────────────────────────────────────────────────────────
    print("[2] Geocoding dad...")
    dad_loc = geocode(dad_addr)
    if dad_loc is None:
        print("[ERROR] Geocoding dad address failed.")
        sys.exit(1)
    print(f"    Dad lat/lon: {dad_loc.lat:.4f}, {dad_loc.lon:.4f}")

    mom_loc = dad_loc
    if mom_addr:
        print("[2b] Geocoding mom...")
        mom_loc = geocode(mom_addr)
        if mom_loc:
            print(f"    Mom lat/lon: {mom_loc.lat:.4f}, {mom_loc.lon:.4f}")
        else:
            print("    [WARN] Mom geocoding failed, using dad's location")

    # ── 3. Distance & district ────────────────────────────────────────────────
    distance = haversine_miles(dad_loc.lat, dad_loc.lon, mom_loc.lat, mom_loc.lon)
    print(f"[3] Distance between parents: {distance:.1f} miles")

    district = args.district
    cal_url = ""
    if dad_loc.city:
        found, cal_url = search_district(dad_addr, dad_loc.city, dad_loc.state, dad_loc.county)
        district = found or district
        print(f"[3] District: {district} | calendar: {cal_url or 'N/A'}")
        if cal_url:
            cache_district(dad_addr, district, cal_url)
    else:
        print(f"[3] District: {district or '(unknown)'}")

    if not district:
        print("[ERROR] No district found. Exiting.")
        sys.exit(1)

    # ── 4. Statute ────────────────────────────────────────────────────────────
    print("[4] Loading TX statute...")
    statute = load_statute("TX", PROCESSED_DIR)
    print(f"    {statute['state_name']} ({statute['state']}) — "
          f"modes: {list(statute['modes'].keys())}, "
          f"distance rule: {distance:.1f}mi → "
          f"{'under_50' if distance<=50 else '50_to_100' if distance<=100 else 'over_100'}")

    # ── 5. Calendar ───────────────────────────────────────────────────────────
    ics_url = get_ics_url(district) if district else None
    if ics_url:
        print(f"[ICS] Registry ICS URL for '{district}'")
    elif cal_url:
        print(f"[ICS] Scraping ICS from: {cal_url}")
    else:
        print("[ICS] Will attempt scraping.")

    cal_path = find_existing_calendar(district)
    if not cal_path:
        print(f"[5] Building calendar for {district}...")
        cal_path = build_calendar_for_district(district, cal_url)
    else:
        print(f"[5] Using existing: {cal_path}")

    calendar = load_calendar(cal_path)

    # ── 6. Build & attach rules (from statute, not hardcoded) ─────────────────
    print("[6] Building custody rules from TX statute...")
    # Build rules for both modes using rule_builder (dynamic, statute-based)
    for mode in ["espo", "spo"]:
        raw_rules = build_custody_rules(
            statute=statute,
            distance_miles=distance,
            mode=mode,
            dad_lat=dad_loc.lat,
            dad_lon=dad_loc.lon,
            mom_lat=mom_loc.lat,
            mom_lon=mom_loc.lon,
        )
        # Convert to StandardCalendar format expected by CustodyIntervalGenerator
        standard_rules = convert_rules_to_standard_format(raw_rules, mode)
        if not hasattr(calendar, 'custody_rules'):
            calendar.custody_rules = {}
        calendar.custody_rules[mode] = standard_rules[mode]

        # Save both formats for reference
        rules_path = os.path.join(PROCESSED_DIR, f"{mode}_rules.json")
        with open(rules_path, "w", encoding="utf-8") as f:
            json.dump(raw_rules, f, indent=2, ensure_ascii=False)
        print(f"    [{mode.upper()}] statute-based rules -> {rules_path}")

    # ── 7. Generate intervals ─────────────────────────────────────────────────
    for mode in ["espo", "spo"]:
        cached_path = os.path.join(DATA_DIR, "processed", f"{mode}_intervals.json")
        if os.path.exists(cached_path) and not args.debug:
            print(f"[{mode.upper()}] Loading cached: {cached_path}")
        else:
            recalc = "Force recalculating" if args.debug else "Calculating"
            print(f"[{mode.upper()}] {recalc}...")
            gen = CustodyIntervalGenerator(calendar, mode=mode)
            ivs = gen.generate()
            errors = ivs.verify_no_overlaps()
            print(f"    {mode.upper()}: {len(ivs)} intervals, "
                  f"{'OVERLAPS: ' + str(errors) if errors else 'OK'}")
            save_intervals(ivs, cached_path)

    if args.debug:
        print("\n[DEBUG] Sample intervals Jan 15-22 2026:")
        for mode in ["espo", "spo"]:
            print(f"\n  === {mode.upper()} Jan 15-22 2026 ===")
            for iv in _load_intervals(mode):
                sd = iv["start"]
                if "2026-01-15" <= sd <= "2026-01-22":
                    print(f"    {iv['start']} - {iv['end']}  {iv['custodian']}  {iv['reason']}")

    # ── 8. Generate HTML (repo root for GitHub Pages) ─────────────────────────
    print("\n[8] Generating HTML...")
    ROOT_HTML = os.path.join(BASE_DIR, "index.html")
    HTMLBuilder(
        district=district,
        espo_intervals=_load_intervals("espo"),
        spo_intervals=_load_intervals("spo"),
    ).build(ROOT_HTML)
    print(f"[DONE] {ROOT_HTML}")


if __name__ == "__main__":
    main()
