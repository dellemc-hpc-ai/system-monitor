"""
rule_builder.py — Build concrete custody rules from statute + distance + mode.
Produces custody_rules.json with resolved dad/mom labels (no abstract conservator roles).
"""
import json
import os
import sys
from datetime import date

# Add project root
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.geolocator import haversine_miles


def determine_distance_rule(distance_miles: float, statute: dict) -> str:
    """Select which distance rule applies based on miles."""
    dr = statute["distance_rules"]
    if distance_miles <= 50:
        return "under_50"
    elif distance_miles <= 100:
        return "50_to_100"
    else:
        return "over_100"


def resolve_alternation(alternation: dict, break_start_date: date) -> str:
    """
    Given an alternation block like:
      { "type": "odd_even_year", "base": "calendar_year_of_break_start" }
    Returns "dad" or "mom" for the given break_start_date.
    """
    if alternation.get("type") != "odd_even_year":
        raise ValueError(f"Unknown alternation type: {alternation.get('type')}")

    year = break_start_date.year
    is_odd = year % 2 == 1

    # In alternation, "odd_year" and "even_year" map to abstract roles (possessory/managing)
    # The caller must apply conservator_labels to convert to dad/mom
    return "odd" if is_odd else "even"


def build_custody_rules(
    statute: dict,
    distance_miles: float,
    mode: str,  # "spo" or "espo"
    dad_lat: float, dad_lon: float,
    mom_lat: float, mom_lon: float,
) -> dict:
    """
    Build concrete custody rules from statute template.

    Returns a dict like:
    {
      "state": "TX",
      "distance_miles": 12.4,
      "applicable_statute": "§153.312",
      "mode": "espo",
      "parents": { "possessory": "dad", "managing": "mom" },
      "weekend": { "pattern": "1st_3rd_5th_friday", "parent": "dad", ... },
      "thursday": { "parent": "dad", "overnight": true, ... },
      "holidays": {
        "thanksgiving": { "alternation": true, "odd_year": "dad", "even_year": "mom" },
        "christmas": { "split": true, "odd_year_first": "dad", "even_year_first": "mom" },
        "spring_break": { "alternation": true, "odd_year": "mom", "even_year": "dad" }
      },
      "summer": { "possessory_days": "july_1_30", "possessory_parent": "dad", "remainder_parent": "mom" },
      "fathers_day": { "parent": "dad" },
      "mothers_day": { "parent": "mom" }
    }
    """
    labels = statute.get("conservator_labels", {})
    possessory_label = labels.get("possessory", "dad")
    managing_label = labels.get("managing", "mom")
    father_label = labels.get("father", "dad")
    mother_label = labels.get("mother", "mom")

    distance_rule_key = determine_distance_rule(distance_miles, statute)
    distance_rule = statute["distance_rules"][distance_rule_key]
    statute_ref = distance_rule.get("statute", "unknown")

    mode_data = statute["modes"].get(mode)
    if not mode_data:
        raise ValueError(f"Unknown mode '{mode}'. Available: {list(statute['modes'].keys())}")

    rules = {
        "state": statute["state"],
        "distance_miles": round(distance_miles, 1),
        "applicable_statute": statute_ref,
        "distance_rule_key": distance_rule_key,
        "mode": mode,
        "parents": {
            "possessory": possessory_label,
            "managing": managing_label,
            "father": father_label,
            "mother": mother_label,
        },
        # Weekend rule
        "weekend": {
            "pattern": mode_data["weekend"].get("pattern", "1st_3rd_5th_friday"),
            "parent": possessory_label,
            "start_detail": mode_data["weekend"]["start"]["detail"],
            "end_detail": mode_data["weekend"]["end"]["detail"],
        },
        # Thursday rule
        "thursday": {
            "parent": possessory_label,
            "overnight": mode_data["thursday"].get("overnight", False),
            "start_detail": mode_data["thursday"]["start"]["detail"],
            "end_detail": mode_data["thursday"]["end"]["detail"],
            "description": mode_data["thursday"]["description"],
        },
        # Holidays
        "holidays": {},
        # Summer
        "summer": {
            "possessory_days": "july_1_30",
            "possessory_parent": possessory_label,
            "remainder_parent": managing_label,
        },
        # Parents day
        "fathers_day": { "parent": father_label },
        "mothers_day": { "parent": mother_label },
    }

    # Thanksgiving
    tg = statute["holidays"]["thanksgiving"]
    rules["holidays"]["thanksgiving"] = {
        "alternation": True,
        "odd_year": possessory_label,
        "even_year": managing_label,
        "whole_period": tg.get("whole_period", True),
        "start_detail": tg["start"]["detail"],
        "end_detail": tg["end"]["detail"],
    }

    # Christmas
    xm = statute["holidays"]["christmas"]
    rules["holidays"]["christmas"] = {
        "split": True,
        "split_detail": xm["split_point"]["detail"],
        "odd_year_first": possessory_label,
        "odd_year_second": managing_label,
        "even_year_first": managing_label,
        "even_year_second": possessory_label,
    }

    # Spring break
    sb = statute["holidays"]["spring_break"]
    rules["holidays"]["spring_break"] = {
        "alternation": True,
        "odd_year": managing_label,
        "even_year": possessory_label,
    }

    # Holiday weekend extension (§153.315)
    hw = statute["holidays"].get("holiday_weekend_extended", {})
    rules["holidays"]["holiday_extended"] = {
        "monday_holiday_extends_to_monday": True,
        "friday_holiday_extends_to_thursday": True,
        "applies_to": hw.get("friday_holiday", {}).get("applies_to", "both_spo_and_espo"),
    }

    return rules


def save_custody_rules(rules: dict, data_dir: str) -> None:
    os.makedirs(data_dir, exist_ok=True)
    path = os.path.join(data_dir, "custody_rules.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rules, f, indent=2, ensure_ascii=False)
    print(f"[rule_builder] Saved rules to {path}")


if __name__ == "__main__":
    import json
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from statute_loader import load_statute

    statute = load_statute("TX", "data/TX_TEST")
    rules = build_custody_rules(
        statute=statute,
        distance_miles=12.4,
        mode="espo",
        dad_lat=30.4425, dad_lon=-97.8134,
        mom_lat=30.4425, mom_lon=-97.8134,
    )
    print(json.dumps(rules, indent=2))
