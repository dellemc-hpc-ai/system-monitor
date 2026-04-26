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

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")


def load_default_address():
    path = os.path.join(CONFIG_DIR, "default_address.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["address"]


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


def build_calendar_for_district(district: str, calendar_page_url: str = "", force: bool = False):
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
             "thanksgiving": {"start": "2026-11-23", "end": "2026-11-27",
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

    custody_rules = {
        "espo": {
            "weekend": {"pattern": "1st_3rd_5th_friday", "parent": "dad"},
            "thursday": {"parent": "dad"},
            "holidays": {
                "thanksgiving": {"odd_year_parent": "dad", "even_year_parent": "mom"},
                "christmas":    {"split": "first_second_half",
                                 "odd_year_parent": "dad", "even_year_parent": "mom",
                                 "split_day": 28},
                "spring_break": {"odd_year_parent": "mom", "even_year_parent": "dad"},
            },
            "summer": {"parent": "dad", "default_30_days": "july_1_30"},
            "noschool_days": {"default_parent": "dad"},
        },
        "spo": {
            "weekend": {"pattern": "1st_3rd_5th_friday", "parent": "dad"},
            "thursday": {"parent": "dad"},
            "holidays": {
                "thanksgiving": {"odd_year_parent": "dad", "even_year_parent": "mom"},
                "christmas":    {"split": "first_second_half",
                                 "odd_year_parent": "dad", "even_year_parent": "mom",
                                 "split_day": 28},
                "spring_break": {"odd_year_parent": "mom", "even_year_parent": "dad"},
            },
            "summer": {"parent": "dad", "default_30_days": "july_1_30"},
            "noschool_days": {"default_parent": "dad"},
        },
    }
    with open(saved, "r+", encoding="utf-8") as f:
        data = json.load(f)
        data["custody_rules"] = custody_rules
        f.seek(0)
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.truncate()

    return saved


def main():
    parser = argparse.ArgumentParser(description="Custody calendar pipeline")
    parser.add_argument("--address", default=None)
    parser.add_argument("--district", default=None)
    parser.add_argument("--mode", default="espo", choices=["espo", "spo"])
    parser.add_argument("--debug", action="store_true",
                        help="Force recalculation and show sample intervals (for verification)")
    args = parser.parse_args()

    address = args.address or load_default_address()
    print(f"[1] Address: {address}")

    print("[2] Geocoding...")
    geo = geocode(address)
    if geo:
        print(f"    lat={geo.lat:.4f} lon={geo.lon:.4f} city={geo.city}")
    else:
        print("    (geocoding failed)")

    district = args.district
    cal_url = ""
    if geo:
        found, cal_url = search_district(address, geo.city, geo.state, geo.county)
        district = found
        print(f"[3] District: {district} | calendar: {cal_url or 'N/A'}")
        if cal_url:
            cache_district(address, district, cal_url)
    else:
        print(f"[3] District: {district}")

    if not district:
        print("[ERROR] No district found. Exiting.")
        return

    ics_url = get_ics_url(district) if district else None
    if ics_url:
        print(f"[ICS] Using registry ICS URL for '{district}'")
    elif cal_url:
        print(f"[ICS] Will scrape ICS from: {cal_url}")
    else:
        print("[WARN] No ICS URL known. Will attempt scraping.")

    cal_path = find_existing_calendar(district)
    if not cal_path:
        print(f"[4] Building calendar for {district}...")
        cal_path = build_calendar_for_district(district, cal_url)
    else:
        print(f"[4] Using existing: {cal_path}")

    calendar = load_calendar(cal_path)

    # ── Interval generation ──────────────────────────────────────────────────
    # Default: load cached intervals (fast, no re-parse needed)
    # --debug: force recalculate and show sample intervals (for verification)
    # Recalculation is only needed when school calendar/ICS changes or new school year starts.
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for mode in ["espo", "spo"]:
        cached_path = os.path.join(DATA_DIR, "processed", f"{mode}_intervals.json")
        if os.path.exists(cached_path) and not args.debug:
            print(f"[{mode.upper()}] Loading cached intervals: {cached_path}")
        else:
            recalc = "Force recalculating" if args.debug else "No cache, calculating"
            print(f"[{mode.upper()}] {recalc}...")
            gen = CustodyIntervalGenerator(calendar, mode=mode)
            ivs = gen.generate()
            errors = ivs.verify_no_overlaps()
            print(f"    {mode.upper()}: {len(ivs)} intervals, "
                  f"{'OVERLAPS: ' + str(errors) if errors else 'OK'}")
            save_intervals(ivs, cached_path)
            print(f"    Saved to {cached_path}")

    if args.debug:
        print("\n[DEBUG] Showing sample intervals around Jan 2026:")
        from datetime import date
        for mode in ["espo", "spo"]:
            cached_path = os.path.join(DATA_DIR, "processed", f"{mode}_intervals.json")
            with open(cached_path, encoding="utf-8") as f:
                ivs_data = json.load(f)
            print(f"\n  === {mode.upper()} Jan 15-22 2026 ===")
            for iv in ivs_data.get("intervals", ivs_data):
                sd = iv["start"]
                if "2026-01-15" <= sd <= "2026-01-22":
                    print(f"    {iv['start']} - {iv['end']}  {iv['custodian']}  {iv['reason']}")

    print("[6] Generating HTML...")
    html_dest = os.path.join(OUTPUT_DIR, "custody_school_calendar.html")
    HTMLBuilder(district,
                _load_intervals("espo"),
                _load_intervals("spo")).build(html_dest)
    print(f"[DONE] {html_dest}")


def _load_intervals(mode: str):
    path = os.path.join(DATA_DIR, "processed", f"{mode}_intervals.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    return data.get("intervals", data)


if __name__ == "__main__":
    main()
